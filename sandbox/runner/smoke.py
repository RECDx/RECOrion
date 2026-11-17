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


SKIP_UI = {"node_modules", ".git", "docs", "tests", "test", "__tests__", "coverage", "dist", "build", ".venv", "venv"}


def _has_web_ui() -> bool:
    """Depoda (doküman/test/derleme klasörleri dışında) HTML ya da JSX/Vue arayüz dosyası var mı."""
    for root, dirs, files in os.walk(WORK):
        dirs[:] = [d for d in dirs if d not in SKIP_UI and not d.startswith(".rx-")]
        if any(f.endswith((".html", ".jsx", ".tsx", ".vue")) for f in files):
            return True
    return False


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


STEP_KINDS = ("fill", "click", "select", "check", "uncheck", "press", "goto", "expect_text", "expect_selector",
              "wait_for_selector", "wait_ms")


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
    steps = (c.get("steps") or [])[:25]
    where = "sayfa açılışı"
    try:
        page.goto(f"http://127.0.0.1:{svc['port']}{_fmt(c.get('path') or '/', saved)}")
        for i, st in enumerate(steps, 1):
            st = _fmt(st, saved)
            kind = next((k for k in STEP_KINDS if k in st), None)
            where = f"adım {i}/{len(steps)} ({kind or '?'}: {str(st.get(kind, ''))[:60] if kind else json.dumps(st, ensure_ascii=False)[:80]})"
            # C3-60: tanınmayan adım sessizce atlanmaz (atlanırsa sonraki adım yanıltıcı biçimde zaman aşımına düşer)
            if kind is None:
                raise ValueError(f"Bilinmeyen adım türü; desteklenenler: {', '.join(STEP_KINDS)}")
            to = min(int(st.get("timeout") or 10_000), 30_000)
            if kind == "fill":
                page.fill(st["fill"], str(st.get("value", "")), timeout=to)
            elif kind == "click":
                page.click(st["click"], timeout=to)
            elif kind == "select":
                page.select_option(st["select"], str(st.get("value", "")), timeout=to)
            elif kind == "check":
                page.check(st["check"], timeout=to)
            elif kind == "uncheck":
                page.uncheck(st["uncheck"], timeout=to)
            elif kind == "press":
                page.press(st.get("selector") or "body", str(st["press"]), timeout=to)
            elif kind == "goto":
                page.goto(f"http://127.0.0.1:{svc['port']}{st['goto']}", timeout=to)
            elif kind == "expect_text":
                page.get_by_text(str(st["expect_text"])).first.wait_for(state="visible", timeout=to)
            elif kind in ("expect_selector", "wait_for_selector"):
                state = st.get("state") if st.get("state") in ("attached", "detached", "visible", "hidden") else "visible"
                page.wait_for_selector(st[kind], state=state, timeout=to)
            elif kind == "wait_ms":
                page.wait_for_timeout(min(int(st["wait_ms"]), 5000))
        return True, "Adımlar tamamlandı" + (f" (uyarılar: {'; '.join(errors[:3])})" if errors else "")
    except Exception as exc:
        msg = str(exc).split("\n")[0][:300]
        return False, f"{where}: {msg}" + (f" · Sayfa hataları/başarısız istekler: {'; '.join(errors[:5])}" if errors else "")
    finally:
        page.close()


CRAWL_PAGES, CRAWL_BUTTONS, CRAWL_BUDGET = 6, 12, 120  # sayfa, sayfa başına düğme, saniye
_MUT_JS = """() => { window.__rxMut = 0; if (window.__rxObs) window.__rxObs.disconnect();
  window.__rxObs = new MutationObserver((m) => { window.__rxMut += m.length; });
  window.__rxObs.observe(document.documentElement, {subtree: true, childList: true, attributes: true, characterData: true});
  document.addEventListener('invalid', () => { window.__rxMut += 1; }, true); }"""
_BTN_JS = """(max) => [...document.querySelectorAll('button, [role=button], input[type=button], input[type=submit]')]
  .filter((b) => !b.disabled && b.getAttribute('aria-disabled') !== 'true' && b.offsetParent !== null)
  .slice(0, max).map((b, i) => { b.setAttribute('data-rx-btn', String(i)); return b; })
  .map((b, i) => ({i, label: (b.innerText || b.value || b.getAttribute('aria-label') || b.title || '').trim().slice(0, 50)}))"""
_LINK_JS = """() => [...document.querySelectorAll('a[href]')].map((a) => ({href: a.getAttribute('href'), text: (a.innerText || '').trim().slice(0, 50)}))"""


def _same_origin_path(href: str, port: int):
    """Uygulama içi bağlantı mı; öyleyse yol (+sorgu) döner. Çapa, mailto, javascript ve dış adresler atlanır."""
    if not href or href.startswith(("#", "mailto:", "tel:", "javascript:")):
        return None
    u = urllib.parse.urlparse(href)
    if u.scheme and u.scheme not in ("http", "https"):
        return None
    if u.netloc and u.netloc not in (f"127.0.0.1:{port}", f"localhost:{port}"):
        return None
    path = u.path or "/"
    return path + (f"?{u.query}" if u.query else "")


def crawl(services, browser, login_check, saved):
    """İSTEK #752 tıklama taraması: uygulama içi sayfaları gezer; her görünür düğmeye taze sayfada tıklar ve hiçbir şey
    yapmayan düğmeyi (DOM, adres, ağ isteği, pencere değişmiyor), JS hatasını ve ölü bağlantıyı (4xx/5xx) raporlar.
    Giriş gerekiyorsa ilk başarılı arayüz denetiminin adımları önce tekrarlanır (aynı oturum)."""
    svc = services.get((login_check or {}).get("service")) or next((s for s in services.values() if s.get("ready")), None)
    if not svc or not svc.get("ready") or browser is None:
        return None
    port, base, t0 = svc["port"], f"http://127.0.0.1:{svc['port']}", time.time()
    ctx = browser.new_context()
    page = ctx.new_page()
    page.set_default_timeout(8_000)
    js_errors, net, dialogs = [], {"n": 0}, {"n": 0}
    page.on("pageerror", lambda e: js_errors.append(str(e).split("\n")[0][:160]))
    page.on("request", lambda r: net.__setitem__("n", net["n"] + 1) if r.resource_type in ("xhr", "fetch", "document") else None)
    page.on("dialog", lambda d: (dialogs.__setitem__("n", dialogs["n"] + 1), d.dismiss()))
    ctx.on("page", lambda p: (dialogs.__setitem__("n", dialogs["n"] + 1), p.close()))
    out = {"pages": [], "dead_buttons": [], "dead_links": [], "js_errors": [], "texts": [], "login": None}
    start = "/"
    try:
        if login_check:
            try:
                page.goto(base + _fmt(login_check.get("path") or "/", saved))
                for st in (login_check.get("steps") or [])[:25]:
                    st = _fmt(st, saved)
                    if "fill" in st:
                        page.fill(st["fill"], str(st.get("value", "")))
                    elif "click" in st:
                        page.click(st["click"])
                    elif "select" in st:
                        page.select_option(st["select"], str(st.get("value", "")))
                    elif "press" in st:
                        page.press(st.get("selector") or "body", str(st["press"]))
                    elif "goto" in st:
                        page.goto(base + st["goto"])
                    elif "expect_text" in st:
                        page.get_by_text(str(st["expect_text"])).first.wait_for(state="visible")
                page.wait_for_timeout(500)
                start = _same_origin_path(page.url, port) or "/"
                out["login"] = login_check.get("name")
            except Exception as exc:
                out["login_error"] = str(exc).split("\n")[0][:200]
        queue, seen, checked = [start], set(), {}
        while queue and len(seen) < CRAWL_PAGES and time.time() - t0 < CRAWL_BUDGET:
            path = queue.pop(0)
            if path in seen:
                continue
            seen.add(path)
            n_err = len(js_errors)
            resp = page.goto(base + path, wait_until="networkidle")
            page.wait_for_timeout(300)
            info = {"path": path, "status": resp.status if resp else None, "buttons": 0, "dead": 0}
            out["texts"].append(page.inner_text("body")[:6000])
            for ln in page.evaluate(_LINK_JS)[:60]:
                p2 = _same_origin_path(ln["href"], port)
                if p2 is None:
                    continue
                if p2 not in checked:
                    try:
                        checked[p2] = _http("GET", base + p2, timeout=8)[0]
                    except Exception as exc:
                        checked[p2] = f"{exc.__class__.__name__}"
                code = checked[p2]
                if not isinstance(code, int) or code >= 400:
                    out["dead_links"].append({"page": path, "text": ln["text"], "href": p2, "status": code})
                elif p2 not in seen and p2 not in queue and p2.split("?")[0] != path.split("?")[0]:
                    queue.append(p2)
            buttons = page.evaluate(_BTN_JS, CRAWL_BUTTONS)
            info["buttons"] = len(buttons)
            for b in buttons:
                if time.time() - t0 > CRAWL_BUDGET:
                    break
                try:
                    page.goto(base + path, wait_until="networkidle")
                    page.wait_for_timeout(200)
                    page.evaluate(_BTN_JS, CRAWL_BUTTONS)  # yeniden yüklemede işaretler kaybolur
                    page.evaluate(_MUT_JS)
                    url0, net0, dlg0 = page.url, net["n"], dialogs["n"]
                    page.click(f'[data-rx-btn="{b["i"]}"]', timeout=3000)
                    page.wait_for_timeout(700)
                    moved = page.url != url0
                    mut = 0 if moved else page.evaluate("() => window.__rxMut || 0")
                    if not (moved or mut or net["n"] > net0 or dialogs["n"] > dlg0):
                        info["dead"] += 1
                        out["dead_buttons"].append({"page": path, "label": b["label"] or f"düğme {b['i'] + 1}"})
                except Exception:
                    info["skipped"] = info.get("skipped", 0) + 1  # görünmez/kapanan öğe: tarama hatası ölü düğme sayılmaz
            out["pages"].append(info)
            for e in dict.fromkeys(js_errors[n_err:]):  # aynı hata her yeniden yüklemede tekrarlanır: bir kez yazılır
                if len(out["js_errors"]) < 8:
                    out["js_errors"].append({"page": path, "error": e})
            del js_errors[:]
    except Exception as exc:
        out["error"] = f"{exc.__class__.__name__}: {str(exc).split(chr(10))[0][:200]}"
    finally:
        try:
            ctx.close()
        except Exception:
            pass
    out["seconds"] = round(time.time() - t0, 1)
    return out


def crawl_check(cr):
    """Tarama sonucunu denetim satırına çevirir: ölü düğme, JS hatası ve ölü bağlantı duman testini düşürür."""
    probs = []
    if cr.get("dead_buttons"):
        probs.append("tepkisiz düğme: " + ", ".join(f"'{d['label']}' ({d['page']})" for d in cr["dead_buttons"][:6]))
    if cr.get("js_errors"):
        probs.append("JS hatası: " + "; ".join(f"{e['page']}: {e['error']}" for e in cr["js_errors"][:4]))
    if cr.get("dead_links"):
        probs.append("ölü bağlantı: " + ", ".join(f"'{d['text'] or d['href']}' → {d['href']} ({d['status']})" for d in cr["dead_links"][:6]))
    n_btn = sum(p["buttons"] for p in cr.get("pages") or [])
    head = f"{len(cr.get('pages') or [])} sayfa, {n_btn} düğme tıklandı"
    if cr.get("login_error"):
        head += f" (giriş tekrarlanamadı: {cr['login_error'][:80]})"
    if cr.get("error") and not cr.get("pages"):
        return {"name": "Tıklama taraması", "type": "crawl", "ok": None, "detail": f"Tarama yapılamadı: {cr['error']}", "seconds": cr.get("seconds")}
    return {"name": "Tıklama taraması", "type": "crawl", "ok": not probs, "seconds": cr.get("seconds"),
            "detail": head + (" · " + " · ".join(probs) if probs else " · sorun yok")}


CLAIM_RE = re.compile(r"[\"“«]([^\"”»\n]{3,40})[\"”»]|\*\*([^*\n]{3,40})\*\*")


def doc_claims(texts):
    """README'deki tırnaklı/kalın kısa ifadeler (ör. "sol menü", **Sepete ekle**) taranan sayfaların metninde aranır."""
    readme = next((n for n in ("README.md", "readme.md") if os.path.isfile(os.path.join(WORK, n))), None)
    if not readme or not texts:
        return None
    body = open(os.path.join(WORK, readme), encoding="utf-8", errors="replace").read()
    body = re.sub(r"```.*?```|`[^`]*`", " ", body, flags=re.S)  # kod blokları komut/örnek: iddia değil
    claims = []
    for m in CLAIM_RE.finditer(body):
        c = (m.group(1) or m.group(2)).strip()
        if c and not re.search(r"[/\\:=<>{}$]|https?|\.\w{2,4}$", c) and c.lower() not in (x.lower() for x in claims):
            claims.append(c)
    claims = claims[:25]
    if not claims:
        return None
    page = " ".join(texts).casefold()
    missing = [c for c in claims if c.casefold() not in page]
    return {"claims": len(claims), "missing": missing}


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
        web_ui = _has_web_ui()
        if web_ui or any(c.get("type") == "browser" for c in checks):
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
        # İSTEK #752: arayüzlü uygulamada tıklama taraması + README iddialarının sayfada aranması
        if web_ui and browser is not None:
            login = next((c for c, r in zip(checks, result["checks"]) if c.get("type") == "browser" and r["ok"] is True), None)
            try:
                cr = crawl(services, browser, login, saved)
            except Exception as exc:
                cr = {"error": f"{exc.__class__.__name__}: {str(exc)[:200]}"}
            if cr is not None:
                result["crawl"] = {k: v for k, v in cr.items() if k != "texts"}
                result["checks"].append(crawl_check(cr))
                claims = doc_claims(cr.get("texts") or [])
                if claims:
                    result["doc_claims"] = claims
                    miss = claims["missing"]
                    result["checks"].append({"name": "Belge iddiaları sayfada", "type": "claims", "ok": not miss, "seconds": 0,
                                             "detail": f"README'deki {claims['claims']} ifadeden {claims['claims'] - len(miss)} tanesi sayfalarda bulundu"
                                                       + (" · bulunamayan: " + ", ".join(f"'{m}'" for m in miss[:8]) if miss else "")})
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
    # Depoda web arayüzü varsa arayüzden deneme zorunlu: yalnız API denemek arayüzün çalıştığını göstermez
    if web_ui and not any(c.get("type") == "browser" for c in checks):
        result["checks"].append({"name": "Arayüzden deneme", "type": "browser", "ok": False, "seconds": 0,
                                 "detail": "Depoda web arayüzü (HTML) var ama recorion.json'da arayüzden deneme (type: browser) yok; "
                                           "arayüzün gerçek API'ye bağlanıp çalıştığı doğrulanmadı."})
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
