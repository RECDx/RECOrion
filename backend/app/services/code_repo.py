"""
Proje kod deposu (ADIM 8.5): RECOrion Gitea deposu.

- Her şirket Gitea'da bir organizasyondur (rx-<şirket kısa adı>); her proje özel (private) bir depodur, ana dal `main`.
- AI personel her iş adımında kendi dalına (adim-<sıra>-<başlık>) çalışır: çıktı `docs/adimlar/` altına, çıktıdaki yol
  belirtilmiş kod blokları (```python src/app.py) dosya olarak commit edilir; ana dala birleştirme isteği (PR) açılır.
- Ana dala birleştirme yalnızca insan onayıyla olur: adım onaylanınca PR birleştirilir; onay gerektirmeyen adımı proje
  yöneticisi Kod Deposu ekranından birleştirir. İptal edilen adımın PR'ı kapatılır.
- Depo işlemleri iş akışını durdurmaz: hata olay geçmişine (REPO_ERROR) yazılır, iş sürer.
"""
import asyncio
import base64
import difflib
import logging
import re
import unicodedata
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

import httpx
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.models import Project, Task, Tenant

logger = logging.getLogger("recorion.code_repo")

BASE_BRANCH = "main"
MERGE_ATTEMPTS = 8
MERGE_RETRY_SECONDS = 2
MERGE_TOTAL_SECONDS = 60
MAX_FILES = 40
MAX_FILE_BYTES = 200_000
CODE_BLOCK = re.compile(r"^```[ \t]*([\w+#.-]*)[ \t]+([\w./-]+\.[\w]+)[ \t]*\n(.*?)^```[ \t]*$", re.M | re.S)
PATH_ONLY_BLOCK = re.compile(r"^```[ \t]*((?:[\w.-]+/)+[\w.-]+\.[\w]+)[ \t]*\n(.*?)^```[ \t]*$", re.M | re.S)
# Senaryo F81 (08.11.2026): model yolu açılış satırına değil bloğun ilk satırına yorum olarak yazıyor
# (```sql\n-- src/db/schema.sql). Yorum satırı dosyaya yazılmaz (JSON gibi yorumsuz dosyalar bozulmasın).
COMMENT_PATH_BLOCK = re.compile(
    r"^```[ \t]*[\w+#-]*[ \t]*\n[ \t]*(?:#|//|--|;|/\*|<!--)[ \t]*(?:(?:dosya|file|path|yol)[ \t]*:[ \t]*)?"
    r"((?:[\w.-]+/)*[\w.-]+\.[A-Za-z][A-Za-z0-9]{0,7})[ \t]*(?:\*/|-->)?[ \t]*\n(.*?)^```[ \t]*$", re.M | re.S | re.I)


# Senaryo C3-21 (12.11.2026): model yolu bloğun İLK satırına ÇIPLAK yazıyor (```python\nsrc/app/main.py\n...). Tek "kelime",
# uzantılı ya da bilinen dosya adı, boşluksuz; yol satırı dosyaya yazılmaz.
BARE_PATH_BLOCK = re.compile(
    r"^```[ \t]*[\w+#-]*[ \t]*\n[ \t]*((?:[\w.-]+/)*(?:[\w.-]+\.[A-Za-z][A-Za-z0-9]{0,7}|Dockerfile|Makefile|Procfile))[ \t]*\n(.*?)^```[ \t]*$",
    re.M | re.S)

# Senaryo C3-27 (12.11.2026): model yolu bloğun ÜSTÜNDEKİ başlık satırına yazıyor (### `src/web/index.html`, **src/x.py**,
# "Dosya: src/x.py"); araya boş satır girebilir. Satırda yoldan başka söz olmamalı (yanlış eşleşme olmasın).
HEADING_PATH_BLOCK = re.compile(
    r"^[ \t]*(?:#{1,6}[ \t]*|[-*][ \t]+)?(?:\*\*|__)?(?:(?:dosya|file|path|yol)[ \t]*:[ \t]*)?`?"
    r"((?:[\w.-]+/)*(?:[\w.-]+\.[A-Za-z][A-Za-z0-9]{0,7}|Dockerfile|Makefile|Procfile))`?(?:\*\*|__)?[ \t]*:?[ \t]*\n"
    r"(?:[ \t]*\n){0,2}```[ \t]*[\w+#-]*[ \t]*\n(.*?)^```[ \t]*$",
    re.M | re.S | re.I)

# Senaryo C3-29: başlık yol ile başlar (### `src/web/admin.js` (açıklama)), altında ≤3 açıklama satırı, sonra kod bloğu.
HEADING_DESC_PATH_BLOCK = re.compile(
    r"^[ \t]*#{1,6}[ \t]*`((?:[\w.-]+/)*(?:[\w.-]+\.[A-Za-z][A-Za-z0-9]{0,7}|Dockerfile|Makefile|Procfile))`[^\n]*\n"
    r"(?:(?![ \t]*```)[^\n]*\n){0,3}```[ \t]*[\w+#-]*[ \t]*\n(.*?)^```[ \t]*$",
    re.M | re.S)
# Kısmi blok: "// ...", "# ...", "<!-- ... -->", "/* ... */" yer tutucusu → tam dosya değil; yazılmaz.
PARTIAL_MARK = re.compile(r"^[ \t]*(?://|#|<!--|/\*|--)[ \t]*(?:\.\.\.|…)", re.M)

# Senaryo C3-33 (13.11.2026): genel geri arama. Yolu yukarıdaki desenlerle bulunamayan blok için üstteki ≤4 satıra bakılır;
# en yakın dosya adı, uzantısı bloğun diliyle uyumluysa kullanılır ("## 3. Duman Testi (recorion.json)" + açıklama + blok).
NEAR_PATH = re.compile(r"(?<![\w/.-])((?:[\w.-]+/)*(?:[\w-][\w.-]*\.[A-Za-z][A-Za-z0-9]{0,7}|Dockerfile|Makefile|Procfile))(?![\w/-])")
LANG_EXT = {"python": {"py"}, "py": {"py"}, "json": {"json"}, "markdown": {"md"}, "md": {"md"}, "bash": {"sh"}, "sh": {"sh"},
            "shell": {"sh"}, "javascript": {"js", "mjs"}, "js": {"js", "mjs"}, "typescript": {"ts"}, "ts": {"ts"},
            "html": {"html", "htm"}, "css": {"css"}, "toml": {"toml"}, "yaml": {"yml", "yaml"}, "yml": {"yml", "yaml"},
            "ini": {"ini", "cfg"}, "text": {"txt", "cfg", "ini"}, "txt": {"txt"}, "sql": {"sql"}, "dockerfile": {"Dockerfile"}}
KNOWN_EXT = set().union(*LANG_EXT.values())


FENCE_OPEN = re.compile(r"^ {0,3}(`{3,})[ \t]*([\w+#.-]*)")
FENCE_LINE = re.compile(r"^\s*(`{3,})[ \t]*([\w+#.-]*)[^\n]*$")


def fenced_blocks(content: str) -> List[Tuple[str, int, str]]:
    """(dil, açılış satırının konumu, tam gövde). Markdown bloğunun içindeki dilli açılışlar iç blok sayılır ve yalın ``` ile
    kapanır; dış blok ancak derinlik sıfırken gelen yalın ``` ile biter (C3-33: README içinde ```bash)."""
    out: List[Tuple[str, int, str]] = []
    lines = content.split("\n")
    offsets, pos = [], 0
    for ln in lines:
        offsets.append(pos)
        pos += len(ln) + 1
    i, n = 0, len(lines)
    while i < n:
        m = FENCE_OPEN.match(lines[i])
        if not m:
            i += 1
            continue
        ticks, lang = len(m.group(1)), m.group(2)
        nested = lang.lower() in ("markdown", "md")
        depth, j = 0, i + 1
        while j < n:
            f = FENCE_LINE.match(lines[j])
            if f and len(f.group(1)) >= 3:
                if f.group(2):  # dilli açılış
                    if nested:
                        depth += 1
                elif depth > 0:
                    depth -= 1
                elif len(f.group(1)) >= ticks:
                    break
            j += 1
        if j >= n:
            break  # kapanmamış blok: yazılmaz
        out.append((lang, offsets[i], "\n".join(lines[i + 1:j]) + "\n"))
        i = j + 1
    return out


def _near_path(content: str, start: int, lang: str):
    lines = content[:start].rstrip("\n").split("\n")[-4:]
    want = LANG_EXT.get((lang or "").lower())
    for line in reversed(lines):
        if line.strip().startswith("```"):
            return None  # önceki bloğun içine/sonuna taşma yok
        for cand in reversed(NEAR_PATH.findall(line)):
            ext = cand.rsplit(".", 1)[-1] if "." in cand.rsplit("/", 1)[-1] else cand.rsplit("/", 1)[-1]
            if (want and ext in want) or (not want and ext in KNOWN_EXT):  # dil yoksa yalnız bilinen uzantı (alan adı değil)
                return cand
    return None

class RepoError(Exception):
    def __init__(self, message: str, status: int = 502):
        super().__init__(message)
        self.message, self.status = message, status


def enabled() -> bool:
    return bool(settings.GITEA_TOKEN)


def slug(text: str, limit: int = 40) -> str:
    text = unicodedata.normalize("NFKD", (text or "").replace("ı", "i").replace("İ", "I")).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:limit].strip("-") or "x"


# ---------------------------------------------------------------- Gitea HTTP
async def _call(method: str, path: str, json: Optional[Dict[str, Any]] = None, ok=(200, 201, 204), params=None) -> Tuple[int, Any]:
    if not enabled():
        raise RepoError("Kod deposu sunucusu yapılandırılmamış (GITEA_TOKEN).", 503)
    try:
        async with httpx.AsyncClient(base_url=settings.GITEA_URL.rstrip("/") + "/api/v1", timeout=15,
                                     headers={"Authorization": f"token {settings.GITEA_TOKEN}"}) as c:
            r = await c.request(method, path, json=json, params=params)
    except httpx.HTTPError as exc:
        raise RepoError(f"Kod deposu sunucusuna ulaşılamadı ({exc.__class__.__name__}).", 503)
    if r.status_code not in ok:
        detail = ""
        try:
            detail = (r.json() or {}).get("message") or ""
        except ValueError:
            detail = r.text[:200]
        raise RepoError(f"Kod deposu işlemi başarısız ({r.status_code}): {detail}".strip(), r.status_code)
    try:
        return r.status_code, (r.json() if r.content else None)
    except ValueError:
        return r.status_code, None


async def _exists(path: str) -> Optional[Any]:
    try:
        return (await _call("GET", path, ok=(200,)))[1]
    except RepoError as exc:
        if exc.status == 404:
            return None
        raise


def public_url(project: Project) -> Optional[str]:
    if not project.repo_owner or not project.repo_name:
        return None
    return f"{settings.GITEA_PUBLIC_URL.rstrip('/')}/{project.repo_owner}/{project.repo_name}"


# ---------------------------------------------------------------- depo açma
async def enable(db: AsyncSession, project: Project) -> Project:
    """Projeye depo açar (yoksa şirket organizasyonu da). Zaten varsa olduğu gibi kullanılır."""
    tenant = await db.get(Tenant, project.tenant_id)
    owner = project.repo_owner or f"rx-{slug(tenant.slug, 36)}"
    name = project.repo_name or slug(project.slug or project.name, 90)
    if not await _exists(f"/orgs/{owner}"):
        await _call("POST", "/orgs", {"username": owner, "full_name": tenant.name[:100], "visibility": "private",
                                      "description": f"{tenant.name} — RECOrion proje kod depoları"})
    if not await _exists(f"/repos/{owner}/{name}"):
        await _call("POST", f"/orgs/{owner}/repos", {
            "name": name, "description": f"{project.name} (RECOrion)"[:255], "private": True, "auto_init": True,
            "default_branch": BASE_BRANCH, "readme": "Default"})
    project.repo_mode, project.repo_owner, project.repo_name = "RECORION", owner, name
    project.repo_url = public_url(project)
    return project


def active(project: Project) -> bool:
    return enabled() and project.repo_mode == "RECORION" and bool(project.repo_owner and project.repo_name)


SEED_MAX_FILES = 400
SEED_MAX_BYTES = 8_000_000


async def seed_from(project: Project, source: Project) -> Dict[str, Any]:
    """C3-67: bakım/düzeltme projesi, kapanmış bir projenin ana dalındaki kodla başlar (kapalı projeye adım eklenemez).
    Kaynağın main dalındaki dosyalar yeni deponun main dalına tek commit olarak kopyalanır; kaynak depo değişmez."""
    src = await tree(source, BASE_BRANCH)
    blobs = [e for e in src["entries"] if e["type"] == "blob"][:SEED_MAX_FILES]
    owner, repo = project.repo_owner, project.repo_name
    ops, total = [], 0
    for e in blobs:
        _, f = await _call("GET", f"/repos/{source.repo_owner}/{source.repo_name}/contents/{e['path']}",
                           params={"ref": src["sha"] or BASE_BRANCH})
        content = (f or {}).get("content") or ""
        total += len(content) * 3 // 4
        if total > SEED_MAX_BYTES:
            raise RepoError("Kaynak projenin kodu kopyalamak için çok büyük.", 413)
        current = await _exists(f"/repos/{owner}/{repo}/contents/{e['path']}?ref={BASE_BRANCH}")
        op = {"path": e["path"], "content": content.replace("\n", "")}
        if isinstance(current, dict) and current.get("sha"):
            op.update(operation="update", sha=current["sha"])
        else:
            op["operation"] = "create"
        ops.append(op)
    if not ops:
        return {"files": 0, "source_sha": src["sha"]}
    await _call("POST", f"/repos/{owner}/{repo}/contents", {
        "files": ops, "branch": BASE_BRANCH, "author": {"name": "RECOrion", "email": "ai@recorion.local"},
        "message": f"Başlangıç kodu: '{source.name}' projesinin ana dalı ({(src['sha'] or '')[:10]})"})
    return {"files": len(ops), "source_sha": src["sha"]}


# ---------------------------------------------------------------- iş adımının dosyaları
def branch_name(task: Task) -> str:
    return f"adim-{task.order_index or 0}-{slug(task.title, 50)}"


def _safe_path(path: str) -> Optional[str]:
    """Depo içinde kalan göreli yol; '..', mutlak yol, boş/nokta parça ve .git reddedilir (ör. ../../etc/x)."""
    path = (path or "").strip().replace("\\", "/")
    while path.startswith("./"):
        path = path[2:]
    parts = path.split("/")
    if not path or len(path) > 200 or path.startswith("/") or any(p in ("", ".", "..") for p in parts) or parts[0] == ".git":
        return None
    return path


def files_from_output(task: Task, content: str, partials: Optional[List[str]] = None) -> Dict[str, str]:
    """Adım çıktısı her zaman `docs/adimlar/` altına; yolu belirtilmiş kod blokları ayrı dosya olarak.
    partials verilirse '...' ile kısaltıldığı için yazılmayan dosya yolları buna eklenir (C3-59)."""
    files: Dict[str, str] = {f"docs/adimlar/{task.order_index or 0:02d}-{slug(task.title, 60)}.md": content}
    found = [(m.group(1), m.group(2)) for m in HEADING_DESC_PATH_BLOCK.finditer(content)] + \
            [(m.group(1), m.group(2)) for m in HEADING_PATH_BLOCK.finditer(content)] + \
            [(m.group(2), m.group(3)) for m in CODE_BLOCK.finditer(content)] + \
            [(m.group(1), m.group(2)) for m in PATH_ONLY_BLOCK.finditer(content)] + \
            [(m.group(1), m.group(2)) for m in COMMENT_PATH_BLOCK.finditer(content)] + \
            [(m.group(1), m.group(2)) for m in BARE_PATH_BLOCK.finditer(content)]
    blocks = fenced_blocks(content)
    # C3-33: düz desenler iç içe blokta gövdeyi yarıda keser → aynı bloğun tarayıcıdaki TAM gövdesi kullanılır
    full = []
    for raw, body in found:
        for _lang, _off, whole in blocks:
            k = whole.find(body[:400]) if body else -1
            if 0 <= k <= 300 and len(whole) - k > len(body):
                body = whole[k:]
                break
        full.append((raw, body))
    found = full
    seen = {b[:400] for _, b in found}
    for lang, off, whole in blocks:  # yolu hiçbir desenle bulunamayan blok: üst satırlara bak
        if not any(x and x in whole for x in seen):
            near = _near_path(content, off, lang)
            if near:
                found.append((near, whole))
    for raw, body in found:
        path = _safe_path(raw)
        if PARTIAL_MARK.search(body):  # C3-29: kısmi parça tam dosyanın yerine geçmesin
            if partials is not None and path and not path.startswith("docs/adimlar/") and path not in partials:
                partials.append(path)
            continue
        if path and not path.startswith("docs/adimlar/") and len(files) < MAX_FILES and len(body.encode()) <= MAX_FILE_BYTES:
            files[path] = body if body.endswith("\n") else body + "\n"
    return files


TEST_PATH = re.compile(r"(^|/)(tests?|__tests__|spec)/|(^|/)(test_[^/]+|[^/]+_test\.py|[^/]+\.(test|spec)\.[cm]?[jt]sx?|conftest\.py|"
                       r"pytest\.ini|requirements[^/]*\.txt|package\.json|recorion\.json|README(\.md)?)$|^scripts/recorion_test\.sh$|^docs/", re.I)


def is_test_path(path: str) -> bool:
    """Test uzmanının depoya yazabileceği dosyalar (F104): testler, test yapılandırması/bağımlılıkları, recorion.json, README, dokümanlar."""
    return bool(TEST_PATH.search(path or ""))


def merge3(base: str, ours: str, theirs: str) -> Tuple[Optional[str], int]:
    """C4-22: satır bazlı üç yollu birleştirme (git merge-file benzeri). base: AI'nın bu dosyanın önceki kendi sürümü, ours: AI'nın
    yeni sürümü, theirs: daldaki güncel hâl (başka adımların ana daldan gelen onaylı değişiklikleri dahil). Dönen (metin, çakışma);
    çakışma varsa metin None — başka adımın onaylı değişikliği sessizce silinmez."""
    b, a, t = base.splitlines(True), ours.splitlines(True), theirs.splitlines(True)
    am = difflib.SequenceMatcher(None, b, a, autojunk=False).get_matching_blocks()
    tm = difflib.SequenceMatcher(None, b, t, autojunk=False).get_matching_blocks()
    sync, ia, it = [], 0, 0
    while ia < len(am) and it < len(tm):
        ab, aa, al = am[ia]
        tb, tt, tl = tm[it]
        i, j = max(ab, tb), min(ab + al, tb + tl)
        if i < j:
            sync.append((i, j, aa + (i - ab), tt + (i - tb)))
        if ab + al < tb + tl:
            ia += 1
        else:
            it += 1
    sync.append((len(b), len(b), len(a), len(t)))
    out: List[str] = []
    conflicts, zb, za, zt = 0, 0, 0, 0
    for i, j, sa, st in sync:
        zs, as_, ts = b[zb:i], a[za:sa], t[zt:st]
        if as_ == ts or ts == zs:
            out += as_
        elif as_ == zs:
            out += ts
        else:
            conflicts += 1
        out += b[i:j]
        zb, za, zt = j, sa + (j - i), st + (j - i)
    return (None if conflicts else "".join(out)), conflicts


async def commit_step(project: Project, task: Task, version: int, content: str, author: str, keep=None,
                      previous: Optional[str] = None) -> Dict[str, Any]:
    """Çıktıyı adımın dalına commit eder; dal yoksa main'den açılır; ana dala birleştirme isteği yoksa açılır.
    keep: dosya yolu süzgeci (ör. test uzmanı yalnız test dosyaları); süzülenler "dropped" olarak döner.
    previous: adımın bir önceki çıktısı (C4-22): daldaki dosya bu adımın önceki sürümünden farklıysa (başka bir adımın onaylı
    değişikliği ana daldan gelmiş) üç yollu birleştirilir; çakışan dosya yazılmaz, "conflicts" olarak döner."""
    owner, repo = project.repo_owner, project.repo_name
    branch = task.repo_branch or branch_name(task)
    branch_exists = bool(await _exists(f"/repos/{owner}/{repo}/branches/{branch}"))
    ref = branch if branch_exists else BASE_BRANCH
    ops = []
    partial: List[str] = []
    files = files_from_output(task, content, partial)
    partial = [p for p in partial if p not in files]  # aynı dosyanın tam hâli de verildiyse uyarı yok
    dropped = [p for p in files if keep and not keep(p)]
    files = {p: b for p, b in files.items() if p not in dropped}
    before = files_from_output(task, previous) if previous else {}
    conflicts: List[str] = []
    merged: List[str] = []
    for path, body in list(files.items()):
        current = await _exists(f"/repos/{owner}/{repo}/contents/{path}?ref={ref}")
        if path in before and isinstance(current, dict) and current.get("content") is not None and not path.startswith("docs/adimlar/"):
            try:
                theirs = base64.b64decode(current["content"]).decode("utf-8")
            except (ValueError, UnicodeDecodeError):
                theirs = None
            if theirs is not None and theirs != before[path] and theirs != body:
                text, _n = merge3(before[path], body, theirs)
                if text is None:
                    conflicts.append(path)
                    del files[path]
                    continue
                body = files[path] = text
                merged.append(path)
        op = {"path": path, "content": base64.b64encode(body.encode("utf-8")).decode()}
        if isinstance(current, dict) and current.get("sha"):
            op.update(operation="update", sha=current["sha"])
        else:
            op["operation"] = "create"
        ops.append(op)
    payload = {"files": ops, "message": f"{task.title}: sürüm {version} ({author})", "author": {"name": author, "email": "ai@recorion.local"}}
    payload.update({"branch": branch} if branch_exists else {"branch": BASE_BRANCH, "new_branch": branch})
    _, res = await _call("POST", f"/repos/{owner}/{repo}/contents", payload)
    sha = ((res or {}).get("commit") or {}).get("sha")
    pr = task.repo_pr_number
    if not pr:
        _, opened = await _call("POST", f"/repos/{owner}/{repo}/pulls", {
            "head": branch, "base": BASE_BRANCH, "title": f"{task.order_index or ''}. {task.title}".strip(". "),
            "body": f"RECOrion iş adımı: **{task.title}**\n\nAna dala birleştirme insan onayıyla yapılır (adım onaylanınca)."})
        pr = opened["number"]
    task.repo_branch, task.repo_pr_number = branch, pr
    return {"branch": branch, "commit": sha, "pr": pr, "files": list(files), "dropped": dropped, "partial": partial,
            "conflicts": conflicts, "merged": merged}


async def update_from_base(project: Project, task: Task) -> str:
    """C3-42: adımın dalını ana daldaki son değişikliklerle günceller (Gitea "PR'ı güncelle", birleştirme). Test koşusundan önce
    çağrılır: dal düzeltmeler ana dala birleşmeden önce açıldıysa testler eski kodla koşmasın. Dönen: UPDATED | CONFLICT | SKIPPED."""
    if not active(project) or not task.repo_pr_number or task.repo_merged_at:
        return "SKIPPED"
    try:
        code, _ = await _call("POST", f"/repos/{project.repo_owner}/{project.repo_name}/pulls/{task.repo_pr_number}/update",
                              ok=(200, 204, 409), params={"style": "merge"})
    except RepoError:
        return "SKIPPED"
    return "CONFLICT" if code == 409 else "UPDATED"



async def rebranch(project: Project, task: Task, version: int, content: str, author: str, keep=None,
                   previous: Optional[str] = None) -> Dict[str, Any]:
    """C3-42: dal ana dalla çakışıyor → eski PR kapatılır, çıktı ana daldan açılan YENİ dala (…-r<sürüm>) yazılır, yeni PR açılır.
    C4-22: çıktılar tam dosya olduğu için ana daldaki başka adımların onaylı değişiklikleri üzerine yazılabilirdi; artık
    previous (adımın bir önceki çıktısı) tabanıyla üç yollu birleştirilir, çakışan dosya yazılmaz."""
    if task.repo_pr_number and not task.repo_merged_at:
        try:
            await _call("PATCH", f"/repos/{project.repo_owner}/{project.repo_name}/pulls/{task.repo_pr_number}", {"state": "closed"})
        except RepoError:
            pass
    task.repo_branch, task.repo_pr_number = f"{branch_name(task)}-r{version}", None
    return await commit_step(project, task, version, content, author, keep, previous)

async def merge_step(project: Project, task: Task, approver: str) -> Dict[str, Any]:
    if not task.repo_pr_number or task.repo_merged_at:
        return {"merged": bool(task.repo_merged_at), "skipped": True}
    owner, repo = project.repo_owner, project.repo_name
    path = f"/repos/{owner}/{repo}/pulls/{task.repo_pr_number}"
    body = {"Do": "merge", "MergeTitleField": f"{task.title} (onaylayan: {approver})",
            "MergeMessageField": "RECOrion: iş adımı insan onayıyla ana dala birleştirildi."}
    # Yeni açılan istekte Gitea birleştirilebilirliği arka planda hesaplar; o sırada 405 "try again later" döner
    for attempt in range(MERGE_ATTEMPTS):
        _, pr = await _call("GET", path)
        if pr.get("merged"):
            break
        try:
            await _call("POST", f"{path}/merge", body, ok=(200, 204))
            break
        except RepoError as exc:
            if exc.status != 405 or attempt == MERGE_ATTEMPTS - 1:
                raise
            await asyncio.sleep(MERGE_RETRY_SECONDS)
    task.repo_merged_at = datetime.now(timezone.utc)
    return {"merged": True, "pr": task.repo_pr_number}


async def close_step(project: Project, task: Task) -> None:
    if task.repo_pr_number and not task.repo_merged_at:
        await _call("PATCH", f"/repos/{project.repo_owner}/{project.repo_name}/pulls/{task.repo_pr_number}", {"state": "closed"})


# ---------------------------------------------------------------- akış kancaları (hata akışı durdurmaz)
async def after_output(db: AsyncSession, project: Project, task: Task, version: int, content: str, author: str,
                       keep=None, previous: Optional[str] = None) -> Dict[str, List[str]]:
    """Depo varsa çıktıyı adımın dalına commit eder. Dönen: {"dropped": süzgece takılanlar, "partial": '...' ile kısaltıldığı
    için yazılmayanlar (C3-59)}."""
    from app.services import task_flow

    if not active(project):
        return {"dropped": [], "partial": [], "conflicts": []}
    try:
        r = await commit_step(project, task, version, content, author, keep, previous)
        await task_flow.log(db, project, task, "REPO_COMMIT", task.assignee_actor_id,
                            f"{r['branch']} dalına {len(r['files'])} dosya commit edildi."
                            + (f" Yazılmayan (test uzmanı kapsamı dışı): {', '.join(r['dropped'])}." if r["dropped"] else "")
                            + (f" Yazılmayan (kısaltılmış, '...' içeriyor; tam dosya gerekli): {', '.join(r['partial'])}."
                               if r["partial"] else "")
                            + (f" Başka adımın ana daldaki değişiklikleriyle birleştirildi: {', '.join(r['merged'])}." if r["merged"] else "")
                            + (f" Yazılmayan (başka adımın ana daldaki onaylı değişiklikleriyle çakışıyor): {', '.join(r['conflicts'])}."
                               if r["conflicts"] else ""), r)
        return {"dropped": r["dropped"], "partial": r["partial"], "conflicts": r["conflicts"]}
    except RepoError as exc:
        logger.warning("Depo commit hatası (%s): %s", task.id, exc.message)
        await task_flow.log(db, project, task, "REPO_ERROR", note=exc.message)
        return {"dropped": [], "partial": [], "conflicts": []}


async def after_approval(db: AsyncSession, project: Project, task: Task, actor_id, approver: str) -> None:
    from app.services import task_flow

    if not active(project) or not task.repo_pr_number:
        return
    try:
        # Onay aktivitesi (2 dk) aşılmasın: depo yavaşsa birleştirme yöneticiye bırakılır, onay yine bir kez işlenir
        r = await asyncio.wait_for(merge_step(project, task, approver), timeout=MERGE_TOTAL_SECONDS)
        if not r.get("skipped"):
            await task_flow.log(db, project, task, "REPO_MERGED", actor_id, f"#{task.repo_pr_number} ana dala birleştirildi.", r)
    except (RepoError, asyncio.TimeoutError) as exc:
        message = getattr(exc, "message", None) or "kod deposu zamanında yanıt vermedi"
        logger.warning("Depo birleştirme hatası (%s): %s", task.id, message)
        await task_flow.log(db, project, task, "REPO_ERROR", note=f"Birleştirilemedi: {message}. Proje yöneticisi Kod Deposu ekranından birleştirebilir.")


async def after_cancel(db: AsyncSession, project: Project, task: Task) -> None:
    if not active(project):
        return
    try:
        await close_step(project, task)
    except RepoError as exc:
        logger.warning("Depo PR kapatma hatası (%s): %s", task.id, exc.message)


# ---------------------------------------------------------------- ekran
async def overview(project: Project, tasks: List[Task]) -> Dict[str, Any]:
    out = {"mode": project.repo_mode or "NONE", "enabled": enabled(), "url": public_url(project), "base": BASE_BRANCH, "steps": [],
           "mirror": None}
    if not active(project):
        return out
    owner, repo = project.repo_owner, project.repo_name
    if project.mirror_repo:
        out["mirror"] = {"repo": project.mirror_repo, "connection_id": str(project.mirror_connection_id) if project.mirror_connection_id else None}
        try:
            state = await mirrors(project)
            out["mirror"].update(state[0] if state else {"last_error": "Yansıtma sunucuda bulunamadı; yeniden kurun."})
        except RepoError as exc:
            out["mirror"]["last_error"] = exc.message
    for t in tasks:
        step = {"task_id": str(t.id), "title": t.title, "order_index": t.order_index, "status": t.status, "branch": t.repo_branch,
                "pr": t.repo_pr_number, "merged_at": t.repo_merged_at, "state": None, "files": []}
        if t.repo_pr_number:
            try:
                _, pr = await _call("GET", f"/repos/{owner}/{repo}/pulls/{t.repo_pr_number}")
                step["state"] = "MERGED" if pr.get("merged") else ("OPEN" if pr.get("state") == "open" else "CLOSED")
                # Fark görünümü (ADIM 16.1): adımın ayrıldığı nokta ve dalın son hâli
                step["base_sha"], step["head_sha"] = pr.get("merge_base"), (pr.get("head") or {}).get("sha")
                _, files = await _call("GET", f"/repos/{owner}/{repo}/pulls/{t.repo_pr_number}/files")
                step["files"] = [{"path": f.get("filename"), "status": f.get("status"), "additions": f.get("additions")} for f in files or []]
            except RepoError as exc:
                step["error"] = exc.message
        out["steps"].append(step)
    return out


async def read_file(project: Project, ref: str, path: str) -> Dict[str, Any]:
    path = _safe_path(path)
    if not path or not re.fullmatch(r"[\w./-]{1,120}", ref or ""):
        raise HTTPException(status_code=422, detail="Geçersiz dosya yolu veya dal.")
    data = await _exists(f"/repos/{project.repo_owner}/{project.repo_name}/contents/{path}?ref={ref}")
    if not isinstance(data, dict) or data.get("type") != "file":
        raise HTTPException(status_code=404, detail="Dosya bulunamadı.")
    raw = base64.b64decode(data.get("content") or "")
    if len(raw) > MAX_FILE_BYTES:
        raise HTTPException(status_code=413, detail="Dosya ekranda gösterilemeyecek kadar büyük.")
    return {"path": path, "ref": ref, "size": len(raw), "content": raw.decode("utf-8", "replace")}


# ---------------------------------------------------------------- Kod Gezgini (ADIM 16.1, #609): salt okuma
TREE_LIMIT = 2000
ARCHIVE_MAX_BYTES = 25 * 1024 * 1024
SEARCH_LIMIT = 200
REF_RE = re.compile(r"[\w./-]{1,120}")


def _ref(ref: str) -> str:
    if not ref or not REF_RE.fullmatch(ref) or ".." in ref:
        raise HTTPException(status_code=422, detail="Geçersiz dal.")
    return ref


async def refs(project: Project, tasks: List[Task]) -> List[Dict[str, Any]]:
    """Depo dalları; adım dalları görev başlığıyla eşlenir. main önce, sonra adım sırası."""
    _, branches = await _call("GET", f"/repos/{project.repo_owner}/{project.repo_name}/branches", params={"limit": 100})
    by_branch = {t.repo_branch: t for t in tasks if t.repo_branch}
    out = []
    for b in branches or []:
        c, t = b.get("commit") or {}, by_branch.get(b.get("name"))
        out.append({"name": b.get("name"), "sha": c.get("id"), "date": c.get("timestamp"), "message": (c.get("message") or "").strip()[:200],
                    "task_id": str(t.id) if t else None, "task_title": t.title if t else None, "order_index": t.order_index if t else None})
    out.sort(key=lambda r: (r["name"] != BASE_BRANCH, r["order_index"] if r["order_index"] is not None else 10 ** 6, r["name"]))
    return out


async def tree(project: Project, ref: str) -> Dict[str, Any]:
    ref = _ref(ref)
    # F88: Gitea'nın git/trees ucu bazı dal adlarını çözemiyor ("sha not found"); dal önce commit SHA'sına çevrilir
    target = ref
    if not re.fullmatch(r"[0-9a-f]{40}", ref):
        branch = await _exists(f"/repos/{project.repo_owner}/{project.repo_name}/branches/{ref}")
        target = ((branch or {}).get("commit") or {}).get("id") or ref
    entries, page = [], 1
    while True:
        try:
            _, data = await _call("GET", f"/repos/{project.repo_owner}/{project.repo_name}/git/trees/{target}",
                                  params={"recursive": "true", "per_page": 1000, "page": page})
        except RepoError as exc:
            if exc.status in (400, 404):
                raise HTTPException(status_code=404, detail="Dal bulunamadı.")
            raise
        for e in (data or {}).get("tree") or []:
            entries.append({"path": e.get("path"), "type": "tree" if e.get("type") == "tree" else "blob", "size": e.get("size") or 0})
        if not (data or {}).get("truncated") or len(entries) >= TREE_LIMIT:
            break
        page += 1
    return {"ref": ref, "sha": (data or {}).get("sha"), "entries": entries[:TREE_LIMIT], "truncated": len(entries) > TREE_LIMIT}


# AI personelin gördüğü depo kodu (senaryo F98, 08.11.2026)
REPO_CONTEXT_CHARS = 30000
REPO_FILE_CHARS = 9000
REPO_PRIORITY_CHARS = 30000  # C4-22: adımın kendi dosyaları ve recorion.json için ek bağlam
REPO_PRIORITY_FILE_CHARS = 30000
REPO_LISTING_MAX = 300
CONTEXT_EXT = {".py", ".js", ".mjs", ".ts", ".html", ".css", ".sql", ".yaml", ".yml", ".json", ".toml", ".txt", ".cfg", ".ini", ".sh"}
CODE_EXT = {".py", ".js", ".mjs", ".ts"}


def _ext(path: str) -> str:
    name = path.rsplit("/", 1)[-1]
    return ("." + name.rsplit(".", 1)[-1].lower()) if "." in name else ""


async def context_for_ai(project: Project, ref: str = BASE_BRANCH, limit: int = REPO_CONTEXT_CHARS,
                         priority: Optional[List[str]] = None) -> str:
    """Dalın dosya listesi + kaynak dosyaların içeriği (önce uygulama kodu, sonra testler ve yapılandırma), sınır içinde.
    Depoya ulaşılamazsa boş döner; iş durmaz."""
    try:
        files = [e for e in (await tree(project, ref))["entries"] if e["type"] == "blob"]
    except Exception as exc:  # noqa: BLE001 — bağlam eksik kalır, iş sürer
        logger.warning("Depo bağlamı alınamadı (%s, %s): %s", project.id, ref, exc)
        return ""
    if not files:
        return ""
    listing = "\n".join(f"- {e['path']}" for e in files[:REPO_LISTING_MAX])
    def rank(e):
        p = e["path"].lower()
        return ("test" in p, _ext(p) not in CODE_EXT, p.count("/"), e["size"])
    # C4-22: adımın yazacağı dosyalar (önceki sürümünde yazdıkları) ve paylaşılan recorion.json önce ve TAM verilir; aksi hâlde AI
    # ana daldaki başka adımın onaylı değişikliğini görmeden dosyayı baştan yazıp siliyordu
    first = set(priority or []) | {"recorion.json"}
    picks = sorted((e for e in files if _ext(e["path"]) in CONTEXT_EXT and not e["path"].startswith("docs/")
                    and 0 < e["size"] <= MAX_FILE_BYTES), key=lambda e: (e["path"] not in first, rank(e)))
    parts, used = [], len(listing)
    limit += REPO_PRIORITY_CHARS if priority else 0
    for e in picks:
        if used >= limit:
            break
        try:
            body = (await read_file(project, ref, e["path"]))["content"]
        except Exception:  # noqa: BLE001
            continue
        cap = REPO_PRIORITY_FILE_CHARS if e["path"] in first else REPO_FILE_CHARS
        if len(body) > cap:
            body = body[:cap] + "\n… (dosyanın devamı kısaltıldı)"
        block = f"\n### {e['path']}\n{body}\n"
        if used + len(block) > limit:
            continue
        parts.append(block)
        used += len(block)
    return (f"# Depodaki kod (dal: {ref})\nBu, projenin şu anki gerçek kodudur; önceki adım özetleriyle çelişirse depodakini esas al "
            f"(uç nokta adları, alan adları, giriş yöntemi). Var olan bir dosyayı değiştirirken buradaki GÜNCEL hâlini temel al: "
            f"başka adımların eklediği bölümleri (menü, bağlantı, recorion.json denetimleri vb.) koru, yalnız kendi değişikliğini ekle."
            f"\nDosyalar:\n{listing}\n" + "".join(parts) + "\n")


async def archive(project: Project, ref: str) -> bytes:
    """Dalın zip arşivi (Gitea); sınırı aşan arşiv indirilmez."""
    ref = _ref(ref)
    if not enabled():
        raise RepoError("Kod deposu sunucusu yapılandırılmamış (GITEA_TOKEN).", 503)
    url = f"/repos/{project.repo_owner}/{project.repo_name}/archive/{ref}.zip"
    try:
        async with httpx.AsyncClient(base_url=settings.GITEA_URL.rstrip("/") + "/api/v1", timeout=60,
                                     headers={"Authorization": f"token {settings.GITEA_TOKEN}"}) as c:
            async with c.stream("GET", url) as r:
                if r.status_code == 404:
                    raise HTTPException(status_code=404, detail="Dal bulunamadı.")
                if r.status_code != 200:
                    raise RepoError(f"Arşiv alınamadı ({r.status_code}).", r.status_code)
                buf = bytearray()
                async for chunk in r.aiter_bytes():
                    buf.extend(chunk)
                    if len(buf) > ARCHIVE_MAX_BYTES:
                        raise HTTPException(status_code=413, detail="Depo arşivi indirilemeyecek kadar büyük (25 MB üstü).")
                return bytes(buf)
    except httpx.HTTPError as exc:
        raise RepoError(f"Kod deposu sunucusuna ulaşılamadı ({exc.__class__.__name__}).", 503)


async def search(project: Project, ref: str, q: str) -> Dict[str, Any]:
    """Dosya adı ve içerik araması (büyük/küçük harf duyarsız); arşiv bellekte açılır, ikili ve büyük dosyalar atlanır."""
    import io
    import zipfile

    needle = (q or "").strip().casefold()
    if not 2 <= len(needle) <= 100:
        raise HTTPException(status_code=422, detail="Arama 2–100 karakter olmalı.")
    data = await archive(project, ref)
    files, hits = [], []
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        for info in z.infolist():
            if info.is_dir():
                continue
            path = info.filename.split("/", 1)[1] if "/" in info.filename else info.filename  # kök klasör (<repo>/) atılır
            if not path:
                continue
            if needle in path.casefold():
                files.append(path)
            if len(hits) >= SEARCH_LIMIT or info.file_size > MAX_FILE_BYTES:
                continue
            raw = z.read(info)
            if b"\x00" in raw[:8000]:
                continue
            for no, line in enumerate(raw.decode("utf-8", "replace").splitlines(), 1):
                if needle in line.casefold():
                    hits.append({"path": path, "line": no, "text": line.strip()[:240]})
                    if len(hits) >= SEARCH_LIMIT:
                        break
    return {"ref": ref, "q": q, "files": files[:SEARCH_LIMIT], "matches": hits, "truncated": len(hits) >= SEARCH_LIMIT}


# ---------------------------------------------------------------- müşterinin hesabına yansıtma (ADIM 10.3, #297)
MIRROR_INTERVAL = "8h0m0s"  # her commit'te de gönderilir (sync_on_commit); aralık yedek
MIRROR_CONNECTORS = ("github", "gitea")


def _clean_remote(address: str) -> str:
    """Yansıtma adresinden kullanıcı/parola kısmını atar (ekranda ve kayıtta kimlik bilgisi görünmez)."""
    return re.sub(r"//[^/@]+@", "//", address or "")


async def mirrors(project: Project) -> List[Dict[str, Any]]:
    if not active(project):
        return []
    _, rows = await _call("GET", f"/repos/{project.repo_owner}/{project.repo_name}/push_mirrors")
    return [{"remote": _clean_remote(m.get("remote_address")), "last_update": m.get("last_update"),
             "last_error": (m.get("last_error") or "")[:300] or None, "sync_on_commit": m.get("sync_on_commit")} for m in rows or []]


async def _drop_mirrors(project: Project) -> None:
    _, rows = await _call("GET", f"/repos/{project.repo_owner}/{project.repo_name}/push_mirrors")
    for m in rows or []:
        await _call("DELETE", f"/repos/{project.repo_owner}/{project.repo_name}/push_mirrors/{m['remote_name']}")


async def set_mirror(project: Project, conn, target: str) -> None:
    """Gitea push mirror kurar: hedef müşterinin bağlantısındaki hesap; token bağlantının kasasından çözülür.
    Önceki yansıtmalar kaldırılır (projede tek hedef). Kurulunca hemen bir gönderim tetiklenir."""
    from app.integrations import git_hosting
    from app.integrations.base import ToolError
    from app.services import tool_gateway

    if not active(project):
        raise RepoError("Önce projenin RECOrion kod deposunu açın.", 409)
    ctx = tool_gateway.context(conn)
    try:
        owner, name = git_hosting.split_repo(target)
        web = git_hosting.web_base(conn.connector, ctx)
        username = ctx.config.get("username") or (await git_hosting.call(conn.connector, ctx, "GET", "/user")).get("login")
    except ToolError as exc:
        raise RepoError(str(exc), 422)
    if not web.startswith(("https://", "http://")):
        raise RepoError("Bağlantının sunucu adresi geçersiz.", 422)
    await _drop_mirrors(project)
    await _call("POST", f"/repos/{project.repo_owner}/{project.repo_name}/push_mirrors", {
        "remote_address": f"{web}/{owner}/{name}.git", "remote_username": username or "oauth2",
        "remote_password": ctx.secrets.get("token") or "", "interval": MIRROR_INTERVAL, "sync_on_commit": True})
    try:
        await _call("POST", f"/repos/{project.repo_owner}/{project.repo_name}/push_mirrors-sync")
    except RepoError as exc:  # ilk gönderim gecikirse aralıkla/sonraki commit'te yapılır
        logger.warning("Yansıtma ilk gönderimi tetiklenemedi (%s): %s", project.id, exc.message)
    project.mirror_connection_id, project.mirror_repo = conn.id, f"{owner}/{name}"


async def clear_mirror(project: Project) -> None:
    if active(project):
        await _drop_mirrors(project)
    project.mirror_connection_id, project.mirror_repo = None, None
