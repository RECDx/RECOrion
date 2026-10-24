"""
RECOrion Edge ajanı (ADIM 10.5) — müşterinin kendi sunucusunda çalışır (Logo, Mikro vb. veritabanının yanında).

Güvenlik modeli:
- Yalnızca DIŞA bağlanır: RECOrion'a yoklama yapar (HTTPS), iş alır, sonucu gönderir. Müşteri ağına port açılmaz.
- Yalnızca bu sunucudaki şablon dosyasında (templates.json) tanımlı İZİNLİ SORGULARI çalıştırır. RECOrion'dan SQL gelmez;
  yalnızca şablon adı ve parametre değerleri gelir. Parametreler türüne, uzunluğuna göre denetlenir ve sorguya bağlanır
  (birleştirme yapılmaz → SQL enjeksiyonu yok). Dönen satır sayısı sınırlıdır.
- Okuma şablonları salt okunur bağlantıda / geri alınan işlemde çalışır. Yazma şablonları varsayılan KAPALIDIR
  (allow_write: true gerekir) ve RECOrion'da da her biri insan onayından geçer.
- Her iş yerel denetim kaydına yazılır (şablon, parametreler, satır sayısı, süre; sonuç verisi yazılmaz).

Çalıştırma:
    pip install httpx            (SQL Server için ayrıca: pip install pyodbc + Microsoft ODBC Driver 18)
    set RECORION_URL=https://app.recorion.com
    set RECORION_EDGE_TOKEN=rxe_...      (Şirket Yönetimi › Entegrasyonlar › Edge Connector › Ajan anahtarı)
    python recorion_edge.py --config edge_config.json
"""
import argparse
import datetime as dt
import decimal
import json
import logging
import os
import platform
import re
import sqlite3
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import httpx

VERSION = "0.1.0"
NAME = re.compile(r"^[a-z][a-z0-9_]{1,59}$")
PARAM = re.compile(r"(?<![:\w]):([a-z][a-z0-9_]*)")
DEFAULT_MAX_ROWS, HARD_MAX_ROWS, DEFAULT_MAX_LEN = 100, 1000, 200
log = logging.getLogger("recorion_edge")


class TemplateError(Exception):
    """Şablon/parametre hatası: RECOrion'a anlaşılır mesajla döner (iç ayrıntı içermez)."""


# ---------------------------------------------------------------- şablonlar
def load_config(path: Path) -> Dict[str, Any]:
    cfg = json.loads(path.read_text(encoding="utf-8"))
    tpath = Path(cfg.get("templates_file") or "templates.json")
    if not tpath.is_absolute():
        tpath = path.parent / tpath
    templates = json.loads(tpath.read_text(encoding="utf-8"))
    by_name = {}
    for t in templates:
        if not NAME.match(t.get("name", "")) or not (t.get("sql") or "").strip():
            raise SystemExit(f"Geçersiz şablon: {t.get('name')!r} (ad küçük harf/rakam/_; sql zorunlu)")
        names_in_sql = set(PARAM.findall(t["sql"]))
        declared = {p["name"] for p in t.get("params", [])}
        if names_in_sql != declared:
            raise SystemExit(f"Şablon {t['name']}: sql parametreleri {sorted(names_in_sql)} ile tanımlı parametreler {sorted(declared)} aynı olmalı")
        t.setdefault("kind", "READ")
        by_name[t["name"]] = t
    cfg["templates"] = by_name
    cfg.setdefault("allow_write", False)
    return cfg


def catalog(cfg: Dict[str, Any]) -> List[Dict[str, Any]]:
    """RECOrion'a bildirilen katalog: SQL GÖNDERİLMEZ. Yazmaya izin yoksa yazma şablonları hiç bildirilmez."""
    out = []
    for t in cfg["templates"].values():
        if t["kind"] == "WRITE" and not cfg["allow_write"]:
            continue
        out.append({"name": t["name"], "description": t.get("description", ""), "kind": t["kind"],
                    "params": [{k: p[k] for k in ("name", "type", "required", "description", "max_length") if k in p}
                               for p in t.get("params", [])]})
    return out


def check_params(t: Dict[str, Any], values: Dict[str, Any]) -> Dict[str, Any]:
    values = values or {}
    declared = {p["name"]: p for p in t.get("params", [])}
    unknown = set(values) - set(declared)
    if unknown:
        raise TemplateError(f"Bilinmeyen parametre: {', '.join(sorted(unknown))}")
    out = {}
    for name, p in declared.items():
        v = values.get(name)
        if v is None or v == "":
            if p.get("required", True):
                raise TemplateError(f"Eksik parametre: {name}")
            out[name] = None
            continue
        typ = p.get("type", "string")
        if typ == "integer":
            if isinstance(v, bool) or not isinstance(v, int):
                raise TemplateError(f"{name} tam sayı olmalı")
        elif typ == "number":
            if isinstance(v, bool) or not isinstance(v, (int, float)):
                raise TemplateError(f"{name} sayı olmalı")
        elif typ == "boolean":
            if not isinstance(v, bool):
                raise TemplateError(f"{name} doğru/yanlış olmalı")
        elif typ == "date":
            try:
                dt.date.fromisoformat(str(v))
            except ValueError:
                raise TemplateError(f"{name} YYYY-AA-GG biçiminde tarih olmalı")
            v = str(v)
        else:
            if not isinstance(v, str):
                raise TemplateError(f"{name} metin olmalı")
            if len(v) > int(p.get("max_length") or DEFAULT_MAX_LEN):
                raise TemplateError(f"{name} en fazla {p.get('max_length') or DEFAULT_MAX_LEN} karakter olabilir")
            if p.get("like"):  # içerir araması: joker karakterler kaçırılır, kalıp ajan tarafında kurulur
                v = "%" + v.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%"
        out[name] = v
    return out


def compile_sql(sql: str, values: Dict[str, Any], style: str) -> Tuple[str, Any]:
    if style == "named":  # sqlite: :ad
        return sql, values
    order = PARAM.findall(sql)  # pyodbc: ? sırasıyla
    return PARAM.sub("?", sql), [values[n] for n in order]


def _jsonable(v: Any) -> Any:
    if isinstance(v, decimal.Decimal):
        return float(v)
    if isinstance(v, (dt.date, dt.datetime, dt.time)):
        return v.isoformat()
    if isinstance(v, (bytes, bytearray)):
        return f"<{len(v)} bayt>"
    return v


# ---------------------------------------------------------------- veritabanı sürücüleri
class SQLiteDriver:
    """Deneme ve test için (sahte Logo veritabanı). Okuma bağlantısı salt okunur açılır."""
    style = "named"

    def __init__(self, path: str):
        self.path = path

    def run(self, sql: str, params: Any, write: bool, max_rows: int):
        uri = f"file:{self.path}?mode={'rw' if write else 'ro'}"
        con = sqlite3.connect(uri, uri=True, timeout=10)
        try:
            cur = con.execute(sql, params)
            if write:
                con.commit()
                return [], [], cur.rowcount, False
            cols = [d[0] for d in cur.description or []]
            rows = cur.fetchmany(max_rows + 1)
            return cols, rows[:max_rows], len(rows[:max_rows]), len(rows) > max_rows
        finally:
            con.close()


class ODBCDriver:
    """SQL Server (Logo Tiger/GO, Mikro). Okuma işlemi her zaman geri alınır; salt okunur bir veritabanı kullanıcısı önerilir."""
    style = "qmark"

    def __init__(self, conn_str: str):
        import pyodbc  # noqa: F401 (yalnızca bu sürücüde gerekir)
        self.conn_str = conn_str

    def run(self, sql: str, params: Any, write: bool, max_rows: int):
        import pyodbc
        con = pyodbc.connect(self.conn_str, autocommit=False, timeout=15)
        try:
            cur = con.cursor()
            cur.execute(sql, params)
            if write:
                con.commit()
                return [], [], cur.rowcount, False
            cols = [d[0] for d in cur.description or []]
            rows = cur.fetchmany(max_rows + 1)
            con.rollback()
            return cols, [list(r) for r in rows[:max_rows]], len(rows[:max_rows]), len(rows) > max_rows
        finally:
            con.close()


def make_driver(db: Dict[str, Any]):
    if db.get("driver") == "sqlite":
        return SQLiteDriver(db["path"])
    if db.get("driver") == "odbc":
        conn_str = os.environ.get(db.get("connection_string_env") or "RECORION_EDGE_DB", "")
        if not conn_str:
            raise SystemExit("ODBC bağlantı dizesi ortam değişkeninde yok (connection_string_env).")
        return ODBCDriver(conn_str)
    raise SystemExit("database.driver: sqlite veya odbc olmalı")


# ---------------------------------------------------------------- işler
def execute(cfg: Dict[str, Any], driver, job: Dict[str, Any]) -> Dict[str, Any]:
    t = cfg["templates"].get(job.get("template"))
    if not t:
        raise TemplateError("Bu şablon ajanda tanımlı değil.")
    write = t["kind"] == "WRITE"
    if write and not cfg["allow_write"]:
        raise TemplateError("Bu ajanda yazma şablonları kapalı (allow_write).")
    values = check_params(t, job.get("params") or {})
    sql, params = compile_sql(t["sql"], values, driver.style)
    max_rows = min(int(t.get("max_rows") or DEFAULT_MAX_ROWS), HARD_MAX_ROWS)
    cols, rows, count, truncated = driver.run(sql, params, write, max_rows)
    if write:
        return {"affected_rows": count}
    return {"columns": cols, "rows": [[_jsonable(v) for v in r] for r in rows], "row_count": count, "truncated": truncated}


def audit(cfg: Dict[str, Any], job: Dict[str, Any], ok: bool, info: str, ms: int) -> None:
    path = cfg.get("audit_log") or "edge_audit.log"
    line = {"at": dt.datetime.now().isoformat(timespec="seconds"), "job": job.get("id"), "template": job.get("template"),
            "params": job.get("params"), "ok": ok, "info": info, "ms": ms}
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(line, ensure_ascii=False) + "\n")


class Agent:
    def __init__(self, cfg: Dict[str, Any], url: str, token: str, client: Optional[httpx.Client] = None, wait: int = 25):
        self.cfg, self.url, self.wait = cfg, url.rstrip("/"), wait
        self.driver = make_driver(cfg["database"])
        self.client = client or httpx.Client(timeout=wait + 15, follow_redirects=False)
        self.headers = {"X-RECOrion-Edge-Token": token, "User-Agent": f"RECOrion-Edge/{VERSION}"}

    def poll_once(self) -> int:
        r = self.client.post(f"{self.url}/api/v1/edge/poll", headers=self.headers, json={
            "version": VERSION, "hostname": self.cfg.get("hostname") or platform.node(), "templates": catalog(self.cfg), "wait": self.wait})
        if r.status_code in (401, 403):
            raise SystemExit(f"RECOrion ajanı kabul etmedi ({r.status_code}): {r.json().get('detail')}")
        r.raise_for_status()
        jobs = r.json().get("jobs") or []
        for job in jobs:
            start = time.monotonic()
            try:
                result, ok, err = execute(self.cfg, self.driver, job), True, None
                info = f"{result.get('row_count', result.get('affected_rows'))} satır"
            except TemplateError as exc:
                result, ok, err, info = None, False, str(exc), str(exc)
            except Exception as exc:  # veritabanı hatası: ayrıntı yerelde, RECOrion'a yalnızca tür
                log.exception("Şablon çalıştırılamadı: %s", job.get("template"))
                result, ok, err, info = None, False, f"Veritabanı hatası ({exc.__class__.__name__})", repr(exc)[:300]
            ms = int((time.monotonic() - start) * 1000)
            audit(self.cfg, job, ok, info, ms)
            self.client.post(f"{self.url}/api/v1/edge/jobs/{job['id']}/result", headers=self.headers,
                             json={"ok": ok, "result": result, "error": err})
        return len(jobs)

    def run_forever(self) -> None:
        backoff = 1
        log.info("RECOrion Edge %s başladı · %s · %d şablon", VERSION, self.url, len(catalog(self.cfg)))
        while True:
            try:
                self.poll_once()
                backoff = 1
            except httpx.HTTPError as exc:
                log.warning("RECOrion'a ulaşılamadı (%s); %d sn sonra yeniden denenecek", exc.__class__.__name__, backoff)
                time.sleep(backoff)
                backoff = min(backoff * 2, 60)


def main() -> None:
    ap = argparse.ArgumentParser(description="RECOrion Edge ajanı")
    ap.add_argument("--config", default="edge_config.json")
    ap.add_argument("--once", action="store_true", help="bir yoklama yap ve çık (kurulum denemesi)")
    args = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    url, token = os.environ.get("RECORION_URL", ""), os.environ.get("RECORION_EDGE_TOKEN", "")
    if not url or not token:
        raise SystemExit("RECORION_URL ve RECORION_EDGE_TOKEN ortam değişkenleri gerekli.")
    if url.startswith("http://") and not re.match(r"http://(localhost|127\.0\.0\.1)(:\d+)?(/|$)", url) and os.environ.get("RECORION_EDGE_ALLOW_HTTP") != "1":
        raise SystemExit("RECOrion adresi https:// olmalı (anahtar ve veriler şifresiz gitmesin).")
    agent = Agent(load_config(Path(args.config)), url, token, wait=0 if args.once else 25)
    if args.once:
        print(f"Bağlantı başarılı; {agent.poll_once()} iş işlendi.")
        return
    agent.run_forever()


if __name__ == "__main__":
    sys.exit(main())
