"""
RECOrion Edge ajanı (ADIM 10.5, 12.5) — müşterinin kendi sunucusunda çalışır (Logo, Mikro vb. veritabanının yanında).

Güvenlik modeli:
- Yalnızca DIŞA bağlanır: RECOrion'a yoklama yapar (HTTPS), iş alır, sonucu gönderir. Müşteri ağına port açılmaz.
- Yalnızca bu sunucudaki şablon dosyasında (templates.json) tanımlı İZİNLİ SORGULARI çalıştırır. RECOrion'dan SQL gelmez;
  yalnızca şablon adı ve parametre değerleri gelir. Parametreler türüne, uzunluğuna göre denetlenir ve sorguya bağlanır
  (birleştirme yapılmaz → SQL enjeksiyonu yok). Dönen satır sayısı sınırlıdır.
- Okuma şablonları salt okunur bağlantıda / geri alınan işlemde çalışır. Yazma şablonları varsayılan KAPALIDIR
  (allow_write: true gerekir) ve RECOrion'da da her biri insan onayından geçer.
- Her iş yerel denetim kaydına yazılır (şablon, parametreler, satır sayısı, süre; sonuç verisi yazılmaz).
- REST şablonları (ADIM 12.5): şirket ağındaki bir programlama arayüzünü (ör. Logo REST servisi) çağırır — Logo'nun
  tablolarına doğrudan yazmak yerine Logo'nun kendi kurallarıyla kayıt açılır. Adres ve kimlik bilgisi YALNIZCA bu
  sunucudaki yapılandırmadadır (http_api; parolalar ortam değişkeninde). Şablon yolu ve gövdesi burada sabittir;
  RECOrion'dan yalnızca türü denetlenmiş parametre değerleri gelir ve tam alan değeri olarak yerleşir (metin birleştirme yok).

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
from urllib.parse import quote

import httpx

VERSION = "0.2.0"
NAME = re.compile(r"^[a-z][a-z0-9_]{1,59}$")
PARAM = re.compile(r"(?<![:\w]):([a-z][a-z0-9_]*)")
DEFAULT_MAX_ROWS, HARD_MAX_ROWS, DEFAULT_MAX_LEN = 100, 1000, 200
HTTP_METHODS = ("GET", "POST", "PUT", "PATCH")
PATH_PARAM = re.compile(r"\{([a-z][a-z0-9_]*)\}")
RESULT_LIMIT = 20000
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
        if not NAME.match(t.get("name", "")) or not ((t.get("sql") or "").strip() or isinstance(t.get("http"), dict)):
            raise SystemExit(f"Geçersiz şablon: {t.get('name')!r} (ad küçük harf/rakam/_; sql veya http zorunlu)")
        declared = {p["name"] for p in t.get("params", [])}
        if t.get("http"):
            used = http_placeholders(t)
            if not cfg.get("http_api", {}).get("base_url"):
                raise SystemExit(f"Şablon {t['name']}: REST şablonu için yapılandırmada http_api.base_url gerekli")
        else:
            used = set(PARAM.findall(t["sql"]))
        if used != declared:
            raise SystemExit(f"Şablon {t['name']}: kullanılan parametreler {sorted(used)} ile tanımlı parametreler {sorted(declared)} aynı olmalı")
        t.setdefault("kind", "READ")
        by_name[t["name"]] = t
    cfg["templates"] = by_name
    cfg.setdefault("allow_write", False)
    return cfg


def _walk_placeholders(v: Any, out: set) -> None:
    if isinstance(v, str) and PARAM.fullmatch(v):
        out.add(v[1:])
    elif isinstance(v, dict):
        for x in v.values():
            _walk_placeholders(x, out)
    elif isinstance(v, list):
        for x in v:
            _walk_placeholders(x, out)


def http_placeholders(t: Dict[str, Any]) -> set:
    """REST şablonunu doğrular; kullanılan parametre adlarını döner (yol: {ad}, sorgu/gövde: tam değer ":ad")."""
    h = t["http"]
    if h.get("method", "GET") not in HTTP_METHODS:
        raise SystemExit(f"Şablon {t['name']}: yöntem {HTTP_METHODS} olmalı")
    path = str(h.get("path") or "")
    if not path.startswith("/") or "://" in path or ".." in path or "?" in path:
        raise SystemExit(f"Şablon {t['name']}: yol '/' ile başlamalı; adres, '..' ve '?' içeremez (sorgu için query kullanın)")
    used = set(PATH_PARAM.findall(path))
    _walk_placeholders(h.get("query") or {}, used)
    _walk_placeholders(h.get("body"), used)
    if h.get("method", "GET") == "GET" and t.get("kind") == "WRITE" or h.get("method", "GET") != "GET" and t.get("kind", "READ") == "READ":
        raise SystemExit(f"Şablon {t['name']}: okuma şablonu GET, yazma şablonu POST/PUT/PATCH olmalı")
    return used


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


def _fill(v: Any, values: Dict[str, Any]) -> Any:
    """Gövde/sorgu kalıbına parametreleri yerleştirir: yalnızca tam değer ":ad" yer tutucuları (değer türüyle). Boş isteğe bağlı
    parametrenin alanı gövdeden çıkarılır."""
    if isinstance(v, str) and PARAM.fullmatch(v):
        return values.get(v[1:])
    if isinstance(v, dict):
        out = {}
        for k, x in v.items():
            y = _fill(x, values)
            if y is not None:
                out[k] = y
        return out
    if isinstance(v, list):
        return [_fill(x, values) for x in v]
    return v


def _clip(data: Any) -> Any:
    text = json.dumps(data, ensure_ascii=False, default=str)
    return data if len(text) <= RESULT_LIMIT else {"truncated": True, "preview": text[:RESULT_LIMIT]}


def _pick_id(data: Any, key: Optional[str]) -> Any:
    item = data[0] if isinstance(data, list) and data else data
    if isinstance(item, dict):
        for k in ([key] if key else []) + ["id", "ID", "INTERNAL_REFERENCE", "LOGICALREF"]:
            if item.get(k) not in (None, ""):
                return item[k]
    return None


class HTTPApi:
    """Şirket ağındaki REST arayüzü (ör. Logo REST servisi). Adres ve kimlik yalnızca bu yapılandırmada; parolalar ortam değişkeninde.
    auth.type: none | bearer (token_env) | basic (username_env, password_env) |
               oauth_password (token_path, username_env, password_env, isteğe bağlı client_id_env/client_secret_env, form)."""

    def __init__(self, conf: Dict[str, Any], client: Optional[httpx.Client] = None):
        self.conf, self.auth = conf, conf.get("auth") or {"type": "none"}
        self.client = client or httpx.Client(base_url=conf["base_url"].rstrip("/"), timeout=float(conf.get("timeout") or 20),
                                             verify=conf.get("verify_tls", True), follow_redirects=False)
        self._token, self._exp = None, 0.0

    @staticmethod
    def _env(name: Optional[str]) -> str:
        v = os.environ.get(name or "", "")
        if not v:
            raise TemplateError(f"Hedef sistem kimlik bilgisi ortam değişkeninde yok ({name}).")
        return v

    def _oauth(self, force: bool = False) -> str:
        if self._token and not force and time.time() < self._exp - 30:
            return self._token
        a = self.auth
        form = {"grant_type": "password", "username": self._env(a.get("username_env")), "password": self._env(a.get("password_env")),
                **{k: str(v) for k, v in (a.get("form") or {}).items()}}
        basic = (self._env(a["client_id_env"]), os.environ.get(a.get("client_secret_env") or "", "")) if a.get("client_id_env") else None
        r = self.client.post(a.get("token_path") or "/api/v1/token", data=form, auth=basic)
        if r.status_code != 200 or not r.json().get("access_token"):
            raise TemplateError(f"Hedef sistem girişi reddedildi (HTTP {r.status_code}).")
        body = r.json()
        self._token, self._exp = body["access_token"], time.time() + float(body.get("expires_in") or 600)
        return self._token

    def _headers(self, force: bool = False) -> Dict[str, str]:
        typ = self.auth.get("type", "none")
        if typ == "bearer":
            return {"Authorization": f"Bearer {self._env(self.auth.get('token_env'))}"}
        if typ == "basic":
            import base64
            raw = f"{self._env(self.auth.get('username_env'))}:{self._env(self.auth.get('password_env'))}".encode()
            return {"Authorization": "Basic " + base64.b64encode(raw).decode()}
        if typ == "oauth_password":
            return {"Authorization": f"Bearer {self._oauth(force)}"}
        return {}

    def call(self, method: str, path: str, query: Dict[str, Any], body: Any) -> Tuple[int, Any]:
        for attempt in (1, 2):
            r = self.client.request(method, path, params={k: v for k, v in (query or {}).items() if v is not None},
                                    json=body if method != "GET" else None, headers=self._headers(force=attempt == 2))
            if r.status_code == 401 and attempt == 1 and self.auth.get("type") == "oauth_password":
                continue  # oturum düşmüş olabilir: bir kez yeniden giriş
            break
        try:
            data = r.json()
        except ValueError:
            data = {"text": r.text[:500]}
        if r.status_code >= 400:
            msg = ""
            if isinstance(data, dict):
                msg = str(data.get("Message") or data.get("message") or data.get("error_description") or data.get("error") or "")[:200]
            raise TemplateError(f"Hedef sistem HTTP {r.status_code}{': ' + msg if msg else ''}")
        return r.status_code, data


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
def execute(cfg: Dict[str, Any], driver, job: Dict[str, Any], http: Optional[HTTPApi] = None) -> Dict[str, Any]:
    t = cfg["templates"].get(job.get("template"))
    if not t:
        raise TemplateError("Bu şablon ajanda tanımlı değil.")
    write = t["kind"] == "WRITE"
    if write and not cfg["allow_write"]:
        raise TemplateError("Bu ajanda yazma şablonları kapalı (allow_write).")
    values = check_params(t, job.get("params") or {})
    if t.get("http"):
        if not http:
            raise TemplateError("Bu ajanda REST arayüzü yapılandırılmamış (http_api).")
        h = t["http"]
        path = PATH_PARAM.sub(lambda m: quote(str(values.get(m.group(1)) or ""), safe=""), h["path"])
        status, data = http.call(h.get("method", "GET"), path, _fill(h.get("query") or {}, values), _fill(h.get("body"), values))
        if isinstance(data, dict) and h.get("result_list") and isinstance(data.get(h["result_list"]), list):
            data = data[h["result_list"]]
        out = {"status": status, "data": _clip(data), "id": _pick_id(data, t.get("result_id"))}
        if isinstance(data, list):
            out["row_count"] = len(data)
        return out
    if driver is None:
        raise TemplateError("Bu ajanda veritabanı yapılandırılmamış.")
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
        self.driver = make_driver(cfg["database"]) if cfg.get("database") else None
        self.http = HTTPApi(cfg["http_api"]) if cfg.get("http_api") else None
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
                result, ok, err = execute(self.cfg, self.driver, job, self.http), True, None
                info = f"HTTP {result['status']}" if "status" in result else f"{result.get('row_count', result.get('affected_rows'))} satır"
            except TemplateError as exc:
                result, ok, err, info = None, False, str(exc), str(exc)
            except httpx.HTTPError as exc:  # şirket ağındaki arayüze ulaşılamadı: RECOrion geçici hata sayar, yeniden dener
                log.warning("Hedef sisteme ulaşılamadı: %s", exc)
                result, ok, err, info = None, False, f"Hedef sisteme ulaşılamadı ({exc.__class__.__name__})", repr(exc)[:300]
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
