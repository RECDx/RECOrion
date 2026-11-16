"""
Temporal aktiviteleri (ADIM 7.1): akışların veritabanına dokunan tek yeri.

Her aktivite kendi oturumunu açar; bağlantı havuzu kullanılmaz (NullPool), böylece worker hangi olay döngüsünde
çalışırsa çalışsın bağlantılar o döngüye bağlı kalmaz.
"""
from typing import Any, Dict, List

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool
from temporalio import activity

from app.config import settings
from app.services import agent_work, task_flow

_session = None


def session() -> AsyncSession:
    global _session
    if _session is None:
        engine = create_async_engine(settings.get_database_url(), poolclass=NullPool)
        _session = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False, autoflush=False)
    return _session()


@activity.defn
async def next_ready_tasks(project_id: str, running: List[str]) -> Dict[str, Any]:
    async with session() as db:
        return await task_flow.next_ready(db, project_id, running)


@activity.defn
async def project_started(project_id: str, actor_id: str = "") -> None:
    async with session() as db:
        await task_flow.project_started(db, project_id, actor_id or None)


@activity.defn
async def project_finished(project_id: str) -> None:
    async with session() as db:
        await task_flow.project_finished(db, project_id)


@activity.defn
async def cancel_remaining(project_id: str, payload: Dict[str, Any]) -> None:
    async with session() as db:
        await task_flow.cancel_remaining(db, project_id, payload)


@activity.defn
async def start_task(task_id: str) -> Dict[str, Any]:
    async with session() as db:
        return await task_flow.start_task(db, task_id)


@activity.defn
async def submit_task(task_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    async with session() as db:
        return await task_flow.submit(db, task_id, payload)


@activity.defn
async def approve_task(task_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    async with session() as db:
        return await task_flow.approve(db, task_id, payload)


@activity.defn
async def reject_task(task_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    async with session() as db:
        return await task_flow.reject(db, task_id, payload)


@activity.defn
async def release_task(task_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    async with session() as db:
        return await task_flow.release(db, task_id, payload)


@activity.defn
async def cancel_task(task_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    async with session() as db:
        return await task_flow.cancel(db, task_id, payload)


@activity.defn
async def block_task(task_id: str, error: str) -> Dict[str, Any]:
    async with session() as db:
        return await task_flow.block(db, task_id, error)


@activity.defn
async def ai_work(task_id: str, feedback: str = "") -> Dict[str, Any]:
    """AI personel iş adımının çıktısını üretir (ADIM 7.2). #746: şirketin eş zamanlı AI sınırı doluysa iş başlamaz
    ({"queued": True}; akış bekleyip yeniden dener, kredi düşmez)."""
    from app.db.models import Project, Task, Tenant
    from app.services import credit_control

    async with session() as db:
        task = await db.get(Task, credit_control.uuid_of(task_id))
        project = await db.get(Project, task.project_id) if task else None
        tenant = await db.get(Tenant, project.tenant_id) if project else None
        if tenant and not await credit_control.acquire_slot(db, tenant, task_id):
            limit = await credit_control.parallel_limit(db, tenant)
            return {"ok": False, "queued": True,
                    "error": f"Şirketin eş zamanlı AI çalışması sınırı ({limit}) dolu; adım sırada bekliyor (kredi düşmez)."}
        try:
            return await agent_work.produce(db, task_id, feedback or None)
        finally:
            if tenant:
                await credit_control.release_slot(tenant.id, task_id)


@activity.defn
async def credit_pause(task_id: str, reason: str, detail: str = "") -> Dict[str, Any]:
    """#746: kredi bitti / haftalık sınır doldu → şirketin aktif proje ve Case'leri duraklatılır (adım karantinaya düşmez)."""
    from app.db.models import Project, Task
    from app.services import credit_control

    async with session() as db:
        task = await db.get(Task, credit_control.uuid_of(task_id))
        project = await db.get(Project, task.project_id) if task else None
        paused = await credit_control.pause_tenant(db, project.tenant_id, reason, detail) if project else []
        return {"paused": paused}


@activity.defn
async def ai_review(task_id: str) -> Dict[str, Any]:
    """Kontrol personeli son çıktıyı değerlendirir (ADIM 7.2)."""
    async with session() as db:
        return await agent_work.review(db, task_id)


@activity.defn
async def run_transfer(transfer_id: str) -> Dict[str, Any]:
    """Onaylı aktarımı dış sisteme yazar (ADIM 12.4). İş mantığı hatası TransferFailed (yeniden denenmez)."""
    from temporalio.exceptions import ApplicationError

    from app.services import transfers

    try:
        return await transfers.execute(transfer_id)
    except transfers.TransferFailed as exc:
        raise ApplicationError(str(exc), type="TransferFailed", non_retryable=True)


@activity.defn
async def fail_transfer(transfer_id: str, reason: str) -> None:
    from app.services import transfers

    await transfers.mark_failed(transfer_id, reason)


ALL = [run_transfer, fail_transfer, ai_work, ai_review, block_task, next_ready_tasks, project_started, project_finished, cancel_remaining, start_task, submit_task, approve_task, reject_task,
       release_task, cancel_task, credit_pause]
