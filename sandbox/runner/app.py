"""
RECOrion Kod Çalıştırma Ortamı — yönetici servis (ADIM 16.2).

POST /run (gövde: deponun zip arşivi) → her koşu için yeni bir iş kabı:
  1. Kod kaba konur (root olmayan kullanıcı, yetkiler düşürülmüş, bellek/işlemci/süreç sınırlı).
  2. Alt projeler bulunur: requirements.txt / pyproject.toml → Python, package.json → Node. Bağımlılıklar kurulur
     (yalnız bu aşamada internet açık).
  3. Ağ kesilir; testler çalışır: pytest (junit raporu) / npm test. Kökte scripts/recorion_test.sh varsa o çalışır.
  3b. Duman testi (#734): kökte recorion.json varsa uygulama kendi komutuyla açılır, adresler ve (Playwright ile) arayüz
      akışı denenir (smoke.py); README de bakılır.
  4. Sonuç (geçen/kalan/hata sayıları, kalan testlerin adı ve mesajı, kayıt sonları) döner; kap silinir.
Kodun kendisi bu servise ya da RECOrion ağına erişemez; bu servis yalnız backend ile ortak iç ağdadır.
"""
import io
import json
import os
import re
import tarfile
import threading
import time
import uuid
import xml.etree.ElementTree as ET
import zipfile
from typing import Any, Dict, List, Optional, Tuple

import docker
from docker.errors import ImageNotFound
from fastapi import FastAPI, HTTPException, Request

RUNTIME_IMAGE = os.environ.get("SANDBOX_RUNTIME_IMAGE", "recorion-sandbox-runtime:2")
RUNTIME_DIR = "/srv/runtime"
MAX_ZIP = 25 * 1024 * 1024
MAX_FILES = 3000
INSTALL_TIMEOUT = int(os.environ.get("SANDBOX_INSTALL_TIMEOUT", "300"))
TEST_TIMEOUT = int(os.environ.get("SANDBOX_TEST_TIMEOUT", "300"))
SMOKE_TIMEOUT = int(os.environ.get("SANDBOX_SMOKE_TIMEOUT", "300"))
SMOKE_SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "smoke.py")
LOG_TAIL = 6000
SKIP_DIRS = {"node_modules", ".git", ".venv", "venv", "__pycache__", "dist", "build", ".next"}

app = FastAPI(title="RECOrion Sandbox", docs_url=None, redoc_url=None)
_client = None
_slots = threading.Semaphore(int(os.environ.get("SANDBOX_PARALLEL", "2")))
_build_lock = threading.Lock()


def client():
    global _client
    if _client is None:
        _client = docker.from_env(timeout=120)
    return _client


def ensure_image() -> None:
    with _build_lock:
        try:
            client().images.get(RUNTIME_IMAGE)
        except ImageNotFound:
            client().images.build(path=RUNTIME_DIR, tag=RUNTIME_IMAGE, rm=True, pull=True)


@app.get("/health")
def health():
    try:
        client().ping()
        try:
            client().images.get(RUNTIME_IMAGE)
            image = True
        except ImageNotFound:
            image = False
        return {"ok": True, "image": image}
    except Exception as exc:  # docker soketi yok
        return {"ok": False, "error": exc.__class__.__name__}


# ---------------------------------------------------------------- arşiv
def _tar_from_zip(data: bytes) -> Tuple[bytes, List[str]]:
    """Zip'i (Gitea arşivi: tek üst klasör) üst klasörsüz, runner (1000) sahipli bir tar'a çevirir."""
    try:
        zf = zipfile.ZipFile(io.BytesIO(data))
    except zipfile.BadZipFile:
        raise HTTPException(status_code=422, detail="Geçersiz arşiv.")
    names = [n for n in zf.namelist() if not n.endswith("/")]
    if len(names) > MAX_FILES:
        raise HTTPException(status_code=413, detail="Depoda çok fazla dosya var.")
    tops = {n.split("/", 1)[0] for n in zf.namelist()}
    strip = len(tops) == 1 and all("/" in n for n in names)
    buf, paths = io.BytesIO(), []
    with tarfile.open(fileobj=buf, mode="w") as tar:
        for n in names:
            rel = n.split("/", 1)[1] if strip else n
            if not rel or rel.startswith("/") or ".." in rel.split("/"):
                continue
            body = zf.read(n)
            ti = tarfile.TarInfo(rel)
            ti.size, ti.mode, ti.uid, ti.gid, ti.mtime = len(body), 0o644, 1000, 1000, int(time.time())
            if rel.endswith(".sh"):
                ti.mode = 0o755
            tar.addfile(ti, io.BytesIO(body))
            paths.append(rel)
    return buf.getvalue(), paths


def _projects(paths: List[str]) -> List[Dict[str, str]]:
    """Kökte ve en fazla 2 alt klasör derinlikte Python/Node projelerini bulur."""
    out, seen = [], set()
    for p in sorted(paths, key=lambda x: (x.count("/"), x)):
        parts = p.split("/")
        if len(parts) > 3 or any(d in SKIP_DIRS for d in parts[:-1]):
            continue
        d, f = "/".join(parts[:-1]), parts[-1]
        kind = "python" if f in ("requirements.txt", "pyproject.toml") else "node" if f == "package.json" else None
        if kind and (d, kind) not in seen:
            seen.add((d, kind))
            out.append({"dir": d or ".", "kind": kind})
    return out


# ---------------------------------------------------------------- kap içi komut
def _exec(box, cmd: str, workdir: str, timeout: int) -> Tuple[int, str, float]:
    t0 = time.time()
    code, out = box.exec_run(["timeout", "-k", "5", str(timeout), "sh", "-c", cmd], workdir=workdir, user="runner",
                             environment={"CI": "true", "HOME": "/home/runner"})
    text = (out or b"").decode("utf-8", "replace")
    return code, text, round(time.time() - t0, 1)


def _tail(text: str) -> str:
    return text if len(text) <= LOG_TAIL else "…\n" + text[-LOG_TAIL:]


def _read_file(box, path: str) -> Optional[str]:
    try:
        stream, _ = box.get_archive(path)
        raw = b"".join(stream)
        with tarfile.open(fileobj=io.BytesIO(raw)) as tar:
            m = tar.next()
            return tar.extractfile(m).read().decode("utf-8", "replace") if m else None
    except Exception:
        return None


def _junit(xml: Optional[str]) -> Dict[str, Any]:
    res = {"passed": 0, "failed": 0, "errors": 0, "skipped": 0, "failures": []}
    if not xml:
        return res
    try:
        root = ET.fromstring(xml)
    except ET.ParseError:
        return res
    for tc in root.iter("testcase"):
        name = ".".join(x for x in (tc.get("classname"), tc.get("name")) if x)
        bad = next((c for c in tc if c.tag in ("failure", "error")), None)
        if bad is not None:
            res["failed" if bad.tag == "failure" else "errors"] += 1
            if len(res["failures"]) < 30:
                res["failures"].append({"name": name[:300], "message": (bad.get("message") or (bad.text or ""))[:800]})
        elif any(c.tag == "skipped" for c in tc):
            res["skipped"] += 1
        else:
            res["passed"] += 1
    return res


NODE_PATTERNS = [
    (re.compile(r"Tests:\s+(?:(\d+) failed, )?(?:(\d+) skipped, )?(?:(\d+) passed, )?(\d+) total"), "jest"),
    (re.compile(r"Tests\s+(?:(\d+) failed \| )?(?:(\d+) passed)?(?: \| (\d+) skipped)?"), "vitest"),
]


def _node_counts(text: str) -> Dict[str, int]:
    m = NODE_PATTERNS[0][0].search(text)
    if m:
        return {"failed": int(m[1] or 0), "skipped": int(m[2] or 0), "passed": int(m[3] or 0)}
    m = NODE_PATTERNS[1][0].search(text)
    if m and (m[1] or m[2]):
        return {"failed": int(m[1] or 0), "passed": int(m[2] or 0), "skipped": int(m[3] or 0)}
    p, f = re.search(r"^# pass (\d+)", text, re.M), re.search(r"^# fail (\d+)", text, re.M)  # node --test
    if p or f:
        return {"passed": int(p[1]) if p else 0, "failed": int(f[1]) if f else 0, "skipped": 0}
    return {}


# ---------------------------------------------------------------- koşu
def _install(box, proj: Dict[str, str], i: int) -> Tuple[int, str, float]:
    wd = f"/work/{proj['dir']}".rstrip("/.") or "/work"
    if proj["kind"] == "python":
        venv = f"/work/.rx-venv-{i}"
        req = "-r requirements.txt" if _exists(box, f"{wd}/requirements.txt") else ""
        cmd = (f"python -m venv {venv} && {venv}/bin/pip install -q pytest {req}"
               + (f" && ({venv}/bin/pip install -q -e . || true)" if _exists(box, f"{wd}/pyproject.toml") else ""))
        return _exec(box, cmd, wd, INSTALL_TIMEOUT)
    return _exec(box, "npm install --no-audit --no-fund --loglevel=error", wd, INSTALL_TIMEOUT)


def _put_file(box, path: str, body: bytes) -> None:
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w") as tar:
        ti = tarfile.TarInfo(os.path.basename(path))
        ti.size, ti.mode, ti.uid, ti.gid, ti.mtime = len(body), 0o644, 1000, 1000, int(time.time())
        tar.addfile(ti, io.BytesIO(body))
    box.put_archive(os.path.dirname(path), buf.getvalue())


def _smoke(box, projects: List[Dict[str, str]]) -> Dict[str, Any]:
    """Duman testi: betik koşu anında kaba konur (uygulama kodu değiştiremez), sonucu JSON olarak okunur."""
    _put_file(box, "/work/.rx-projects.json", json.dumps(projects).encode())
    _put_file(box, "/work/.rx-smoke.py", open(SMOKE_SCRIPT, "rb").read())
    code, out, sec = _exec(box, "python /work/.rx-smoke.py", "/work", SMOKE_TIMEOUT)
    raw = _read_file(box, "/work/.rx-smoke.json")
    try:
        res = json.loads(raw) if raw else None
    except ValueError:
        res = None
    if not isinstance(res, dict):
        res = {"status": "ERROR", "note": "Duman testi sonucu okunamadı" + (" (süre doldu)." if code == 124 else "."), "log": _tail(out)}
    res["seconds"] = sec
    return res


def _exists(box, path: str) -> bool:
    return box.exec_run(["test", "-e", path], user="runner")[0] == 0


def _test(box, proj: Dict[str, str], i: int) -> Dict[str, Any]:
    wd = f"/work/{proj['dir']}".rstrip("/.") or "/work"
    if proj["kind"] == "python":
        junit = f"/work/.rx-junit-{i}.xml"
        code, out, sec = _exec(box, f"/work/.rx-venv-{i}/bin/python -m pytest -q -p no:cacheprovider --junitxml={junit}", wd, TEST_TIMEOUT)
        counts = _junit(_read_file(box, junit))
        status = "NO_TESTS" if code == 5 else "TIMEOUT" if code == 124 else "PASSED" if code == 0 else "FAILED"
        return {**counts, "exit_code": code, "status": status, "seconds": sec, "log": _tail(out), "command": "pytest"}
    pkg = json.loads(_read_file(box, f"{wd}/package.json") or "{}")
    script = ((pkg.get("scripts") or {}).get("test") or "").strip()
    if not script or "no test specified" in script:
        return {"passed": 0, "failed": 0, "errors": 0, "skipped": 0, "failures": [], "exit_code": None, "status": "NO_TESTS",
                "seconds": 0, "log": "package.json içinde test betiği yok.", "command": "npm test"}
    code, out, sec = _exec(box, "npm test --silent", wd, TEST_TIMEOUT)
    counts = {"passed": 0, "failed": 0, "errors": 0, "skipped": 0, "failures": [], **_node_counts(out)}
    status = "TIMEOUT" if code == 124 else "PASSED" if code == 0 else "FAILED"
    return {**counts, "exit_code": code, "status": status, "seconds": sec, "log": _tail(out), "command": "npm test"}


@app.post("/run")
async def run(request: Request):
    data = await request.body()
    if not data or len(data) > MAX_ZIP:
        raise HTTPException(status_code=413, detail="Arşiv boş veya çok büyük.")
    import anyio
    return await anyio.to_thread.run_sync(_run_sync, data)


def _run_sync(data: bytes) -> Dict[str, Any]:
    tar, paths = _tar_from_zip(data)
    projects = _projects(paths)
    custom = "scripts/recorion_test.sh" in paths
    if not projects and not custom and "recorion.json" not in paths:
        return {"status": "NO_TESTS", "projects": [], "seconds": 0,
                "note": "Depoda çalıştırılabilir proje bulunamadı (requirements.txt, pyproject.toml veya package.json yok)."}
    started = time.time()
    with _slots:
        ensure_image()
        box = client().containers.run(
            RUNTIME_IMAGE, ["sleep", "infinity"], detach=True, name=f"rx-sandbox-{uuid.uuid4().hex[:10]}",
            user="runner", working_dir="/work", network_mode="bridge", mem_limit="1536m", memswap_limit="1536m",
            nano_cpus=1_500_000_000, pids_limit=512, cap_drop=["ALL"], security_opt=["no-new-privileges"],
            labels={"recorion.sandbox": "1"}, environment={"CI": "true", "HOME": "/home/runner"})
        try:
            box.put_archive("/work", tar)
            results = []
            for i, proj in enumerate(projects):
                code, out, sec = _install(box, proj, i)
                results.append({**proj, "install": {"ok": code == 0, "exit_code": code, "seconds": sec, "log": _tail(out)}})
            # Kurulum bitti: testler internetsiz çalışır
            try:
                client().networks.get("bridge").disconnect(box, force=True)
            except Exception:
                pass
            if custom:
                code, out, sec = _exec(box, "sh scripts/recorion_test.sh", "/work", TEST_TIMEOUT)
                results.append({"dir": ".", "kind": "script", "install": None,
                                "test": {"passed": 0, "failed": 0, "errors": 0, "skipped": 0, "failures": [], "exit_code": code,
                                         "status": "TIMEOUT" if code == 124 else "PASSED" if code == 0 else "FAILED",
                                         "seconds": sec, "log": _tail(out), "command": "scripts/recorion_test.sh"}})
            for i, r in enumerate(results):
                if r["kind"] in ("python", "node"):
                    r["test"] = _test(box, r, i) if r["install"]["ok"] else {
                        "passed": 0, "failed": 0, "errors": 0, "skipped": 0, "failures": [], "exit_code": None, "status": "INSTALL_FAILED",
                        "seconds": 0, "log": "", "command": ""}
            try:
                smoke = _smoke(box, projects)
            except Exception as exc:  # duman testi koşuyu bozmasın
                smoke = {"status": "ERROR", "note": f"Duman testi çalıştırılamadı: {exc.__class__.__name__}"}
        finally:
            try:
                box.remove(force=True)
            except Exception:
                pass
    states = [r["test"]["status"] for r in results]
    if any(s in ("FAILED", "TIMEOUT", "INSTALL_FAILED") for s in states) or smoke.get("status") in ("FAILED", "ERROR"):
        status = "FAILED"
    elif any(s == "PASSED" for s in states) or smoke.get("status") == "PASSED":
        status = "PASSED"
    else:
        status = "NO_TESTS"
    return {"status": status, "projects": results, "smoke": smoke, "seconds": round(time.time() - started, 1)}
