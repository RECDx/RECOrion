"""
İş akışı adımlarının veritabanı tarafı (ADIM 7.1).

Temporal akışları (app/workflows) karar verir ve bekler; durum değişiklikleri, olay geçmişi (task_events) ve
bildirimler burada yapılır. Akış aktiviteleri bu fonksiyonları kendi oturumlarıyla çağırır.

İş adımı durumları:
  BACKLOG/READY > IN_PROGRESS > (teslim) WAITING_APPROVAL > onay: DONE | ret: REVISION > ... > 3. ret: QUARANTINED
  QUARANTINED: proje yöneticisi yeniden dener (ret sayacı sıfırlanır) veya adımı iptal eder.
"""
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Actor, Project, Task, TaskEvent

logger = logging.getLogger("recorion.task_flow")

CLOSED = ("DONE", "CANCELLED")
WORKING = ("IN_PROGRESS", "REVISION")
STATUS_LABELS = {"BACKLOG": "Sırada", "READY": "Başlayabilir", "IN_PROGRESS": "Çalışılıyor", "WAITING_APPROVAL": "Onay bekliyor",
                 "REVISION": "Revizyonda", "QUARANTINED": "Karantinada", "DONE": "Tamamlandı", "CANCELLED": "İptal edildi"}


def now() -> datetime:
    return datetime.now(timezone.utc)


def _uuid(v) -> Optional[uuid.UUID]:
    return uuid.UUID(str(v)) if v else None


async def log(db: AsyncSession, project: Project, task: Optional[Task], kind: str, actor_id=None,
              note: Optional[str] = None, data: Optional[Dict[str, Any]] = None) -> None:
    db.add(TaskEvent(tenant_id=project.tenant_id, project_id=project.id, task_id=task.id if task else None, kind=kind,
                     actor_id=_uuid(actor_id), note=(note or None) and note[:4000], data=data or {}))


async def approver_of(db: AsyncSession, task: Task, project: Project) -> Optional[Actor]:
    return await db.get(Actor, task.approver_actor_id or project.manager_actor_id) if (task.approver_actor_id or project.manager_actor_id) else None


async def notify(db: AsyncSession, actor_id, text: str) -> None:
    """Kişiye bildirim (şimdilik Telegram; e-posta ve diğer kanallar ADIM 7.3'te ortak kanal altyapısına bağlanır)."""
    from app.services import telegram_service

    actor = await db.get(Actor, _uuid(actor_id)) if actor_id else None
    if actor and actor.actor_type == "HUMAN" and actor.telegram_chat_id:
        try:
            await telegram_service.send_message(actor.telegram_chat_id, text)
        except Exception as exc:  # bildirim hatası akışı durdurmaz
            logger.warning("Bildirim gönderilemedi: %s", exc)


async def _load(db: AsyncSession, task_id) -> tuple:
    task = await db.get(Task, _uuid(task_id))
    project = await db.get(Project, task.project_id) if task else None
    return task, project


# ---------------------------------------------------------------- proje akışı
async def next_ready(db: AsyncSession, project_id, running: List[str]) -> Dict[str, Any]:
    """Bağımlılıkları kapanmış ve henüz başlamamış adımlar; açık adım sayısı."""
    tasks = (await db.execute(select(Task).where(Task.project_id == _uuid(project_id)).order_by(Task.order_index))).scalars().all()
    ids = {str(t.id) for t in tasks}
    closed = {str(t.id) for t in tasks if t.status in CLOSED}
    ready = [str(t.id) for t in tasks if t.status in ("BACKLOG", "READY") and str(t.id) not in running
             and all(str(d) in closed or str(d) not in ids for d in (t.depends_on or []))]
    for t in tasks:  # kullanıcıya "başlayabilir" olarak görünsün
        if str(t.id) in ready and t.status == "BACKLOG":
            t.status = "READY"
    await db.commit()
    return {"ready": ready, "remaining": sum(1 for t in tasks if t.status not in CLOSED)}


async def project_started(db: AsyncSession, project_id, actor_id=None) -> None:
    project = await db.get(Project, _uuid(project_id))
    await log(db, project, None, "PROJECT_STARTED", actor_id)
    await db.commit()


async def cancel_remaining(db: AsyncSession, project_id, payload: Optional[Dict[str, Any]] = None) -> None:
    """Proje kapatılınca henüz başlamamış adımlar da iptal edilir."""
    project = await db.get(Project, _uuid(project_id))
    for t in (await db.execute(select(Task).where(Task.project_id == project.id, Task.status.notin_(CLOSED)))).scalars():
        t.status = "CANCELLED"
        await log(db, project, t, "CANCELLED", (payload or {}).get("actor_id"), (payload or {}).get("note"))
    await db.commit()


async def project_finished(db: AsyncSession, project_id) -> None:
    project = await db.get(Project, _uuid(project_id))
    await log(db, project, None, "PROJECT_FINISHED", note="Tüm iş adımları kapandı.")
    await db.commit()
    await notify(db, project.manager_actor_id,
                 f"RECOrion: '{project.name}' projesinin tüm iş adımları tamamlandı. Kapanış özetini yazıp projeyi kapatabilirsiniz.")


# ---------------------------------------------------------------- iş adımı akışı
async def start_task(db: AsyncSession, task_id) -> Dict[str, Any]:
    task, project = await _load(db, task_id)
    if task.status in ("BACKLOG", "READY"):
        task.status, task.started_at = "IN_PROGRESS", now()
        await log(db, project, task, "TASK_STARTED", data={"assignee": str(task.assignee_actor_id) if task.assignee_actor_id else None})
    await db.commit()
    assignee = await db.get(Actor, task.assignee_actor_id) if task.assignee_actor_id else None
    if assignee and assignee.actor_type == "HUMAN":
        await notify(db, assignee.id, f"RECOrion: '{project.name}' projesinde size yeni bir iş adımı açıldı: {task.title}")
    return {"status": task.status, "requires_approval": bool(task.requires_approval), "max_rejections": int(task.max_rejections or 3),
            "assignee_type": assignee.actor_type if assignee else None, "rejection_count": int(task.rejection_count or 0)}


async def submit(db: AsyncSession, task_id, payload: Dict[str, Any]) -> Dict[str, Any]:
    task, project = await _load(db, task_id)
    task.submitted_at = now()
    await log(db, project, task, "SUBMITTED", payload.get("actor_id"), payload.get("note"))
    if task.requires_approval:
        task.status = "WAITING_APPROVAL"
        await db.commit()
        approver = await approver_of(db, task, project)
        if approver:
            await notify(db, approver.id, f"RECOrion: '{project.name}' projesinde '{task.title}' iş adımı onayınızı bekliyor.")
    else:
        task.status, task.completed_at = "DONE", now()
        await log(db, project, task, "DONE")
        await db.commit()
    return {"status": task.status}


async def approve(db: AsyncSession, task_id, payload: Dict[str, Any]) -> Dict[str, Any]:
    task, project = await _load(db, task_id)
    task.status, task.completed_at = "DONE", now()
    await log(db, project, task, "APPROVED", payload.get("actor_id"), payload.get("note"))
    await log(db, project, task, "DONE")
    await db.commit()
    if task.assignee_actor_id:
        await notify(db, task.assignee_actor_id, f"RECOrion: '{task.title}' iş adımınız onaylandı.")
    return {"status": task.status}


async def reject(db: AsyncSession, task_id, payload: Dict[str, Any]) -> Dict[str, Any]:
    task, project = await _load(db, task_id)
    task.rejection_count = int(task.rejection_count or 0) + 1
    await log(db, project, task, "REJECTED", payload.get("actor_id"), payload.get("note"), {"count": task.rejection_count})
    quarantined = task.rejection_count >= int(task.max_rejections or 3)
    if quarantined:
        task.status = "QUARANTINED"
        await log(db, project, task, "QUARANTINED", note=f"{task.rejection_count} kez reddedildi; proje yöneticisinin kararı bekleniyor.")
    else:
        task.status = "REVISION"
    await db.commit()
    if quarantined:
        await notify(db, project.manager_actor_id, f"RECOrion: '{task.title}' iş adımı {task.rejection_count} kez reddedildi ve karantinaya alındı. "
                                                  "Yeniden denemeye veya iptal etmeye siz karar verin.")
    elif task.assignee_actor_id:
        await notify(db, task.assignee_actor_id, f"RECOrion: '{task.title}' iş adımı revizyona gönderildi: {payload.get('note') or '-'}")
    return {"status": task.status, "quarantined": quarantined}


async def release(db: AsyncSession, task_id, payload: Dict[str, Any]) -> Dict[str, Any]:
    """Karantinadaki adım: retry (ret sayacı sıfırlanır, yeniden çalışılır) veya cancel."""
    task, project = await _load(db, task_id)
    if payload.get("action") == "cancel":
        task.status = "CANCELLED"
        await log(db, project, task, "CANCELLED", payload.get("actor_id"), payload.get("note"))
    else:
        task.status, task.rejection_count = "IN_PROGRESS", 0
        if payload.get("assignee_actor_id"):
            task.assignee_actor_id = _uuid(payload["assignee_actor_id"])
        await log(db, project, task, "RELEASED", payload.get("actor_id"), payload.get("note"),
                  {"assignee": str(task.assignee_actor_id) if task.assignee_actor_id else None})
    await db.commit()
    return {"status": task.status}


async def cancel(db: AsyncSession, task_id, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    task, project = await _load(db, task_id)
    if task.status not in CLOSED:
        task.status = "CANCELLED"
        await log(db, project, task, "CANCELLED", (payload or {}).get("actor_id"), (payload or {}).get("note"))
        await db.commit()
    return {"status": task.status}
