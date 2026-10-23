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


def files_from_output(task: Task, content: str) -> Dict[str, str]:
    """Adım çıktısı her zaman `docs/adimlar/` altına; yolu belirtilmiş kod blokları ayrı dosya olarak."""
    files: Dict[str, str] = {f"docs/adimlar/{task.order_index or 0:02d}-{slug(task.title, 60)}.md": content}
    found = [(m.group(2), m.group(3)) for m in CODE_BLOCK.finditer(content)] + \
            [(m.group(1), m.group(2)) for m in PATH_ONLY_BLOCK.finditer(content)]
    for raw, body in found:
        path = _safe_path(raw)
        if path and not path.startswith("docs/adimlar/") and len(files) < MAX_FILES and len(body.encode()) <= MAX_FILE_BYTES:
            files[path] = body if body.endswith("\n") else body + "\n"
    return files


async def commit_step(project: Project, task: Task, version: int, content: str, author: str) -> Dict[str, Any]:
    """Çıktıyı adımın dalına commit eder; dal yoksa main'den açılır; ana dala birleştirme isteği yoksa açılır."""
    owner, repo = project.repo_owner, project.repo_name
    branch = task.repo_branch or branch_name(task)
    branch_exists = bool(await _exists(f"/repos/{owner}/{repo}/branches/{branch}"))
    ref = branch if branch_exists else BASE_BRANCH
    ops = []
    files = files_from_output(task, content)
    for path, body in files.items():
        current = await _exists(f"/repos/{owner}/{repo}/contents/{path}?ref={ref}")
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
    return {"branch": branch, "commit": sha, "pr": pr, "files": list(files)}


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
async def after_output(db: AsyncSession, project: Project, task: Task, version: int, content: str, author: str) -> None:
    from app.services import task_flow

    if not active(project):
        return
    try:
        r = await commit_step(project, task, version, content, author)
        await task_flow.log(db, project, task, "REPO_COMMIT", task.assignee_actor_id,
                            f"{r['branch']} dalına {len(r['files'])} dosya commit edildi.", r)
    except RepoError as exc:
        logger.warning("Depo commit hatası (%s): %s", task.id, exc.message)
        await task_flow.log(db, project, task, "REPO_ERROR", note=exc.message)


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
    out = {"mode": project.repo_mode or "NONE", "enabled": enabled(), "url": public_url(project), "base": BASE_BRANCH, "steps": []}
    if not active(project):
        return out
    owner, repo = project.repo_owner, project.repo_name
    for t in tasks:
        step = {"task_id": str(t.id), "title": t.title, "order_index": t.order_index, "status": t.status, "branch": t.repo_branch,
                "pr": t.repo_pr_number, "merged_at": t.repo_merged_at, "state": None, "files": []}
        if t.repo_pr_number:
            try:
                _, pr = await _call("GET", f"/repos/{owner}/{repo}/pulls/{t.repo_pr_number}")
                step["state"] = "MERGED" if pr.get("merged") else ("OPEN" if pr.get("state") == "open" else "CLOSED")
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
