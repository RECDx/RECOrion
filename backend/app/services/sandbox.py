"""
Kod Çalıştırma Ortamı (ADIM 16.2): AI personelin yazdığı kodun RECOrion içinde denenmesi.

- Projenin Gitea deposundan istenen dalın arşivi alınır, iç ağdaki sandbox servisine gönderilir. Servis her koşu için yeni,
  sınırlı, root olmayan bir kap açar; bağımlılıkları kurar, ağı keser, testleri (pytest / npm test / scripts/recorion_test.sh)
  çalıştırır, kabı siler. Kod ne RECOrion veritabanına ne gizli bilgilere erişir.
- Koşu `test_runs` tablosuna yazılır; proje geçmişine TEST_RUN olayı düşer. Work Area'da projenin "Testler" sekmesinde ve
  Test Uzmanı'nın adım çıktısında görünür.
- AI Test Uzmanı (unvanında "test", "QA" veya "kalite güvence" geçen AI personel) deposu olan projede çıktısını ürettiğinde
  koşu kendiliğinden yapılır; AI gerçek sonuçları okuyup test raporunu bu sonuçlara göre tamamlar (agent_work).
"""
import logging
import re
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.models import Project, Task, TestRun
from app.services import code_repo, task_flow

logger = logging.getLogger("recorion.sandbox")

RUN_TIMEOUT = 900  # kurulum + test üst süresi (servis kendi içinde aşama başına 300 sn sınırlar)
MAX_ARCHIVE = 25 * 1024 * 1024
TEST_ROLE = re.compile(r"test|\bqa\b|kalite güvence", re.I)
STATUS_TR = {"RUNNING": "Çalışıyor", "PASSED": "Geçti", "FAILED": "Kaldı", "NO_TESTS": "Test bulunamadı", "ERROR": "Çalıştırılamadı"}


class SandboxError(Exception):
    pass


def enabled() -> bool:
    return bool(settings.SANDBOX_URL) and code_repo.enabled()


def is_test_role(role: Optional[str]) -> bool:
    return bool(role and TEST_ROLE.search(role))


def now() -> datetime:
    return datetime.now(timezone.utc)


async def _archive(project: Project, ref: str) -> bytes:
    base = settings.GITEA_URL.rstrip("/") + "/api/v1"
    try:
        async with httpx.AsyncClient(timeout=60, headers={"Authorization": f"token {settings.GITEA_TOKEN}"}) as c:
            r = await c.get(f"{base}/repos/{project.repo_owner}/{project.repo_name}/archive/{ref}.zip")
    except httpx.HTTPError as exc:
        raise SandboxError(f"Kod deposuna ulaşılamadı ({exc.__class__.__name__}).")
    if r.status_code == 404:
        raise SandboxError(f"'{ref}' dalı depoda bulunamadı.")
    if r.status_code != 200:
        raise SandboxError(f"Depo arşivi alınamadı ({r.status_code}).")
    if len(r.content) > MAX_ARCHIVE:
        raise SandboxError("Depo çalıştırma ortamı için çok büyük (25 MB üstü).")
    return r.content


async def _sha(project: Project, ref: str) -> Optional[str]:
    try:
        data = await code_repo._exists(f"/repos/{project.repo_owner}/{project.repo_name}/branches/{ref}")
        return ((data or {}).get("commit") or {}).get("id")
    except code_repo.RepoError:
        return None


async def execute(archive: bytes) -> Dict[str, Any]:
    """Arşivi sandbox servisine gönderir, sonucu döner (testlerde taklit edilir)."""
    try:
        async with httpx.AsyncClient(timeout=RUN_TIMEOUT) as c:
            r = await c.post(settings.SANDBOX_URL.rstrip("/") + "/run", content=archive, headers={"Content-Type": "application/zip"})
    except httpx.HTTPError as exc:
        raise SandboxError(f"Kod çalıştırma ortamına ulaşılamadı ({exc.__class__.__name__}).")
    if r.status_code != 200:
        try:
            detail = r.json().get("detail")
        except ValueError:
            detail = r.text[:200]
        raise SandboxError(f"Kod çalıştırma ortamı hata verdi ({r.status_code}): {detail}")
    return r.json()


def _totals(result: Dict[str, Any]) -> Dict[str, int]:
    t = {"passed": 0, "failed": 0, "skipped": 0}
    for p in result.get("projects") or []:
        test = p.get("test") or {}
        t["passed"] += int(test.get("passed") or 0)
        t["failed"] += int(test.get("failed") or 0) + int(test.get("errors") or 0)
        t["skipped"] += int(test.get("skipped") or 0)
    return t


async def start(db: AsyncSession, project: Project, ref: str, actor_id=None, task: Optional[Task] = None) -> TestRun:
    run = TestRun(tenant_id=project.tenant_id, project_id=project.id, task_id=task.id if task else None, ref=ref,
                  status="RUNNING", started_by_actor_id=actor_id, created_at=now())
    db.add(run)
    await db.flush()
    return run


async def finish(db: AsyncSession, project: Project, run: TestRun, task: Optional[Task] = None) -> TestRun:
    """Koşuyu yapar ve sonucu kaydeder. Hata akışı durdurmaz: koşu ERROR olarak kaydedilir."""
    try:
        if not code_repo.active(project):
            raise SandboxError("Bu projenin kod deposu açık değil.")
        run.commit_sha = await _sha(project, run.ref)
        result = await execute(await _archive(project, run.ref))
        run.result, run.status = result, result.get("status") if result.get("status") in STATUS_TR else "ERROR"
        t = _totals(result)
        run.passed, run.failed, run.skipped = t["passed"], t["failed"], t["skipped"]
    except SandboxError as exc:
        run.status, run.error = "ERROR", str(exc)
    except Exception as exc:  # beklenmeyen: koşu kaydı açık kalmasın
        logger.exception("Test koşusu başarısız")
        run.status, run.error = "ERROR", f"Beklenmeyen hata: {exc.__class__.__name__}"
    run.finished_at = now()
    note = f"{run.ref}: {STATUS_TR.get(run.status, run.status)} · {run.passed} geçti, {run.failed} kaldı" + (f" · {run.error}" if run.error else "")
    await task_flow.log(db, project, task, "TEST_RUN", run.started_by_actor_id, note,
                        {"test_run_id": str(run.id), "status": run.status, "passed": run.passed, "failed": run.failed})
    return run


def report_md(run: TestRun) -> str:
    """Koşunun sistem tarafından yazılan (AI'ın değiştiremediği) özeti: adım çıktısına eklenir."""
    lines = ["## Gerçek test koşusu (RECOrion Kod Çalıştırma Ortamı)", "",
             f"- Dal: `{run.ref}`" + (f" · commit `{run.commit_sha[:10]}`" if run.commit_sha else ""),
             f"- Sonuç: **{STATUS_TR.get(run.status, run.status)}** · {run.passed} geçti · {run.failed} kaldı · {run.skipped} atlandı"]
    if run.error:
        lines.append(f"- Hata: {run.error}")
    res = run.result or {}
    if res.get("note"):
        lines.append(f"- Not: {res['note']}")
    for p in res.get("projects") or []:
        test, inst = p.get("test") or {}, p.get("install") or {}
        lines.append(f"\n### `{p.get('dir')}` ({p.get('kind')}) — {STATUS_TR.get(test.get('status'), test.get('status') or '-')}")
        if inst and not inst.get("ok"):
            lines += ["Bağımlılık kurulumu başarısız:", "```text", (inst.get("log") or "")[-1500:], "```"]
        for f in (test.get("failures") or [])[:10]:
            lines.append(f"- ✗ `{f.get('name')}`: {(f.get('message') or '').strip()[:300]}")
        if test.get("status") in ("FAILED", "TIMEOUT") and not test.get("failures"):
            lines += ["```text", (test.get("log") or "")[-2000:], "```"]
    return "\n".join(lines)


def view(run: TestRun) -> Dict[str, Any]:
    return {"id": str(run.id), "task_id": str(run.task_id) if run.task_id else None, "ref": run.ref, "commit_sha": run.commit_sha,
            "status": run.status, "status_label": STATUS_TR.get(run.status, run.status), "passed": run.passed, "failed": run.failed,
            "skipped": run.skipped, "error": run.error, "result": run.result, "started_by_actor_id": str(run.started_by_actor_id) if run.started_by_actor_id else None,
            "created_at": run.created_at, "finished_at": run.finished_at}
