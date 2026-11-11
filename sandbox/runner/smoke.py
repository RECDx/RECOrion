"""
RECOrion Kod Çalıştırma Ortamı — duman testi (İSTEK #734). İş kabının İÇİNDE, ağ kesildikten sonra çalışır.

Deponun kökündeki `recorion.json` ("uygulama nasıl açılır, neyle denenir") okunur:
  {"services": [{"name": "api", "dir": ".", "start": "uvicorn src.main:app --host 127.0.0.1 --port 8000",
                 "port": 8000, "ready": "/docs"}, ...],
   "checks":   [{"name": "Giriş", "type": "http", "service": "api", "method": "POST", "path": "/token",
                 "form": {...} | "json": {...}, "bearer": "{token}", "expect_status": 200, "expect_text": "...",
                 "save": {"token": "access_token"}},
                {"name": "Arayüzden giriş", "type": "browser", "service": "web", "path": "/",
                 "steps": [{"fill": "#username", "value": "secretary"}, {"click": "button[type=submit]"},
                           {"expect_text": "Hastalar"}]}]}
Servisler sırayla başlatılır (Python projesinde .rx-venv-N, Node'da node_modules/.bin yolda), port açılana ve "ready"
adresi 5xx dışı yanıt verene kadar beklenir; denetimler sırayla koşar; servisler kapatılır. Sonuç /work/.rx-smoke.json'a yazılır.
Yalnız standart kütüphane (+ varsa Playwright). Uygulamanın kendi kodu bu betiği değiştiremez: betik koşudan hemen önce kaba konur.
"""
import json
import os
import re
import signal
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

WORK = "/work"
OUT = "/work/.rx-smoke.json"
READY_TIMEOUT = int(os.environ.get("SMOKE_READY_TIMEOUT", "60"))
CHECK_TIMEOUT = 20
MAX_CHECKS = 30
LOG_TAIL = 2500


def _venv_for(service_dir: str) -> list:
    """Hizmetin klasörüne en yakın Python projesinin venv'i ve Node bin klasörü yola eklenir."""
    paths = []
    try:
        projects = json.load(open("/work/.rx-projects.json", encoding="utf-8"))
    except Exception:
        projects = []
    sd = os.path.normpath(service_dir)
    best = None
    for i, p in enumerate(projects):
        pd = os.path.normpath(p.get("dir") or ".")
        if p.get("kind") == "python" and (sd == pd or sd.startswith(pd + "/") or pd == "."):
            if best is None or len(pd) > len(best[1]):
                best = (i, pd)
    if best is not None:
        paths.append(f"/work/.rx-venv-{best[0]}/bin")
    nb = os.path.join(WORK, sd, "node_modules", ".bin")
    if os.path.isdir(nb):
        paths.append(nb)
    return paths


def _tail(path: str) -> str:
    try:
        text = open(path, encoding="utf-8", errors="replace").read()
    except Exception:
        return ""
    return text if len(text) <= LOG_TAIL else "…\n" + text[-LOG_TAIL:]


def _port_open(port: int) -> bool:
    with socket.socket() as s:
        s.settimeout(1)
        return s.connect_ex(("127.0.0.1", port)) == 0


def _http(method, url, headers=None, data=None, timeout=CHECK_TIMEOUT):
    req = urllib.request.Request(url, data=data, headers=headers or {}, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read(200_000).decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read(20_000).decode("utf-8", "replace")


def _fmt(value, saved):
    if isinstance(value, str):
        return re.sub(r"\{(\w+)\}", lambda m: str(saved.get(m[1], m[0])), value)
    if isinstance(value, dict):
        return {k: _fmt(v, saved) for k, v in value.items()}
    if isinstance(value, list):
        return [_fmt(v, saved) for v in value]
    return value


def _dig(data, path):
    for part in str(path).split("."):
        if isinstance(data, list) and part.isdigit():
            data = data[int(part)] if int(part) < len(data) else None
        elif isinstance(data, dict):
            data = data.get(part)
        else:
            return None
    return data


def start_services(spec):
    procs, out = [], []
    for i, s in enumerate((spec.get("services") or [])[:5]):
        name, port = str(s.get("name") or f"servis{i + 1}"), int(s.get("port") or 0)
        sdir = os.path.normpath(str(s.get("dir") or "."))
        cwd = os.path.join(WORK, sdir)
        log = f"/work/.rx-smoke-{i}.log"
        item = {"name": name, "dir": sdir, "port": port, "command": s.get("start"), "started": False, "ready": False}
        if not s.get("start") or not port or ".." in sdir.split("/") or not os.path.isdir(cwd):
            item["error"] = "Başlatma komutu, port veya klasör eksik/geçersiz."
            out.append(item)
            continue
        env = dict(os.environ, PATH=":".join(_venv_for(sdir) + [os.environ.get("PATH", "")]), PORT=str(port), PYTHONUNBUFFERED="1")
        env.update({str(k): str(v) for k, v in (s.get("env") or {}).items()})
        p = subprocess.Popen(["sh", "-c", str(s["start"])], cwd=cwd, env=env, stdout=open(log, "w"), stderr=subprocess.STDOUT,
                             start_new_session=True)
        procs.append(p)
        item["started"] = True
        deadline, ready_path = time.time() + READY_TIMEOUT, str(s.get("ready") or "/")
        while time.time() < deadline:
            if p.poll() is not None:
                item["error"] = f"Uygulama açılırken kapandı (çıkış kodu {p.returncode})."
                break
            if _port_open(port):
                try:
                    code, _ = _http("GET", f"http://127.0.0.1:{port}{ready_path}", timeout=5)
                    if code < 500:
                        item["ready"], item["ready_status"] = True, code
                        break
                except Exception:
                    pass
            time.sleep(1)
        else:
            item["error"] = f"{READY_TIMEOUT} sn içinde {port} portunda yanıt vermedi."
        item["log"] = _tail(log)
        out.append(item)
    return procs, out


def run_http(c, services, saved):
    svc = services.get(c.get("service")) or next(iter(services.values()), None)
    if not svc or not svc.get("ready"):
        return False, "Hizmet açılmadığı için denenemedi."
    url = f"http://127.0.0.1:{svc['port']}{_fmt(c.get('path') or '/', saved)}"
    headers, data = {str(k): str(v) for k, v in (_fmt(c.get("headers") or {}, saved)).items()}, None
    if c.get("bearer"):
        headers["Authorization"] = "Bearer " + _fmt(c["bearer"], saved)
    if c.get("form") is not None:
        data = urllib.parse.urlencode(_fmt(c["form"], saved)).encode()
        headers.setdefault("Content-Type", "application/x-www-form-urlencoded")
    elif c.get("json") is not None:
        data = json.dumps(_fmt(c["json"], saved)).encode()
        headers.setdefault("Content-Type", "application/json")
    code, body = _http(str(c.get("method") or "GET").upper(), url, headers, data)
    want = c.get("expect_status", 200)
    want = want if isinstance(want, list) else [want]
    if code not in [int(w) for w in want]:
        return False, f"HTTP {code} (beklenen {', '.join(map(str, want))}): {body[:300]}"
    if c.get("expect_text") and str(c["expect_text"]) not in body:
        return False, f"Yanıtta '{c['expect_text']}' yok: {body[:300]}"
    for key, path in (c.get("save") or {}).items():
        try:
            saved[key] = _dig(json.loads(body), path)
        except ValueError:
            return False, f"Yanıt JSON değil; '{path}' alınamadı."
        if saved[key] in (None, ""):
            return False, f"Yanıtta '{path}' yok."
    return True, f"HTTP {code}"


def run_browser(c, services, saved, browser):
    if browser is None:
        return None, "Tarayıcı denetimi bu ortamda yok (Playwright kurulu değil)."
    svc = services.get(c.get("service")) or next(iter(services.values()), None)
    if not svc or not svc.get("ready"):
        return False, "Hizmet açılmadığı için denenemedi."
    page = browser.new_page()
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)[:200]))
    page.on("response", lambda r: errors.append(f"{r.request.method} {r.url.split('127.0.0.1')[-1]} → {r.status}") if r.status >= 400 else None)
    page.set_default_timeout(10_000)
    try:
        page.goto(f"http://127.0.0.1:{svc['port']}{_fmt(c.get('path') or '/', saved)}")
        for st in (c.get("steps") or [])[:25]:
            st = _fmt(st, saved)
            if "fill" in st:
                page.fill(st["fill"], str(st.get("value", "")))
            elif "click" in st:
                page.click(st["click"])
            elif "select" in st:
                page.select_option(st["select"], str(st.get("value", "")))
            elif "goto" in st:
                page.goto(f"http://127.0.0.1:{svc['port']}{st['goto']}")
            elif "expect_text" in st:
                page.get_by_text(str(st["expect_text"])).first.wait_for(state="visible")
            elif "expect_selector" in st:
                page.wait_for_selector(st["expect_selector"], state="visible")
            elif "wait_ms" in st:
                page.wait_for_timeout(min(int(st["wait_ms"]), 5000))
        return True, "Adımlar tamamlandı" + (f" (uyarılar: {'; '.join(errors[:3])})" if errors else "")
    except Exception as exc:
        msg = str(exc).split("\n")[0][:300]
        return False, msg + (f" · Sayfa hataları/başarısız istekler: {'; '.join(errors[:5])}" if errors else "")
    finally:
        page.close()


def main():
    result = {"status": "NO_SMOKE", "services": [], "checks": [], "readme": None}
    readme = next((n for n in ("README.md", "readme.md", "README.MD", "README.txt", "README") if os.path.isfile(os.path.join(WORK, n))), None)
    size = len(open(os.path.join(WORK, readme), encoding="utf-8", errors="replace").read().strip()) if readme else 0
    result["readme"] = {"file": readme, "chars": size, "ok": size >= 300}
    path = os.path.join(WORK, "recorion.json")
    if not os.path.isfile(path):
        result["note"] = "Depoda recorion.json yok: uygulamanın nasıl açılıp deneneceği tanımlı değil; duman testi yapılmadı."
        json.dump(result, open(OUT, "w", encoding="utf-8"), ensure_ascii=False)
        return
    try:
        spec = json.load(open(path, encoding="utf-8"))
        assert isinstance(spec, dict)
    except Exception as exc:
        result.update(status="FAILED", note=f"recorion.json okunamadı: {exc.__class__.__name__}")
        json.dump(result, open(OUT, "w", encoding="utf-8"), ensure_ascii=False)
        return
    procs, svcs = start_services(spec)
    result["services"] = svcs
    services = {s["name"]: s for s in svcs}
    saved, browser, pw = {}, None, None
    checks = (spec.get("checks") or [])[:MAX_CHECKS]
    try:
        if any(c.get("type") == "browser" for c in checks):
            try:
                from playwright.sync_api import sync_playwright
                pw = sync_playwright().start()
                exe = os.environ.get("SMOKE_CHROMIUM")
                browser = pw.chromium.launch(executable_path=exe if exe and os.path.exists(exe) else None,
                                             args=["--no-sandbox", "--disable-dev-shm-usage"])
            except Exception:
                browser = None
        for i, c in enumerate(checks):
            name = str(c.get("name") or f"Denetim {i + 1}")
            t0 = time.time()
            try:
                ok, detail = (run_browser if c.get("type") == "browser" else run_http)(c, services, saved, *(
                    [browser] if c.get("type") == "browser" else []))
            except Exception as exc:
                ok, detail = False, f"{exc.__class__.__name__}: {str(exc)[:200]}"
            result["checks"].append({"name": name, "type": c.get("type") or "http", "ok": ok, "detail": detail,
                                     "seconds": round(time.time() - t0, 1)})
    finally:
        try:
            if browser:
                browser.close()
            if pw:
                pw.stop()
        except Exception:
            pass
        for p in procs:
            try:
                os.killpg(p.pid, signal.SIGTERM)
            except Exception:
                pass
        time.sleep(1)
        for p in procs:
            try:
                os.killpg(p.pid, signal.SIGKILL)
            except Exception:
                pass
    for s in result["services"]:
        s["log"] = s.get("log") or ""
    bad_svc = [s for s in svcs if not s.get("ready")]
    bad = [c for c in result["checks"] if c["ok"] is False]
    if bad_svc or bad:
        result["status"] = "FAILED"
    elif not checks:
        result.update(status="FAILED" if not svcs else "PASSED", note="recorion.json'da denetim (checks) yok; yalnız açılış denendi.")
    else:
        result["status"] = "PASSED"
    json.dump(result, open(OUT, "w", encoding="utf-8"), ensure_ascii=False)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # betik hatası koşuyu bozmasın
        json.dump({"status": "ERROR", "note": f"Duman testi betiği hata verdi: {exc.__class__.__name__}: {exc}"[:500]},
                  open(OUT, "w", encoding="utf-8"), ensure_ascii=False)
        sys.exit(0)
