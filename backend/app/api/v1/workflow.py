"""
İş akışı uçları (ADIM 7.1): akış görünümü, teslim, onay/ret ve karantina kararı.

Uçlar önce veritabanındaki durumu ve yetkiyi denetler, sonra Temporal akışına sinyal gönderir; durum değişikliğini
akış aktiviteleri yazar (birkaç saniye içinde görünür).
"""
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import CurrentUser, forbidden, get_current_user
from app.db.models import Actor, Project, Task, TaskEvent
from app.db.session import get_db
from app.services import projects as psvc
from app.services import task_flow
from app.workflows import engine

router = APIRouter(tags=["İş Akışı (Workflow)"])


def _manages(user: CurrentUser, project: Project) -> bool:
    return user.has("project:manage") or project.manager_actor_id == user.actor_id


async def _task(db: AsyncSession, user: CurrentUser, task_id: uuid.UUID):
    task = await db.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="İş adımı bulunamadı.")
    project = await psvc.load(db, user, task.project_id)
    if project.status not in ("ACTIVE", "PAUSED"):
        raise HTTPException(status_code=409, detail="İş akışı yalnızca aktif projelerde yürür.")
    return task, project


@router.get("/projects/{project_id}/workflow")
async def project_workflow(project_id: uuid.UUID, user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    project = await psvc.load(db, user, project_id)
    tasks = (await db.execute(select(Task).where(Task.project_id == project.id).order_by(Task.order_index))).scalars().all()
    events = (await db.execute(select(TaskEvent).where(TaskEvent.project_id == project.id)
                               .order_by(TaskEvent.created_at.desc()).limit(300))).scalars().all()
    ids = {t.assignee_actor_id for t in tasks} | {t.approver_actor_id for t in tasks} | {e.actor_id for e in events} | {project.manager_actor_id}
    names = {a.id: a for a in (await db.execute(select(Actor).where(Actor.id.in_([i for i in ids if i] or [uuid.uuid4()])))).scalars()}
    manages = _manages(user, project)

    def who(aid):
        a = names.get(aid)
        return {"id": str(a.id), "name": a.display_name, "type": a.actor_type} if a else None

    out = []
    for t in tasks:
        approver_id = t.approver_actor_id or project.manager_actor_id
        is_assignee = t.assignee_actor_id == user.actor_id
        out.append({
            "id": str(t.id), "title": t.title, "status": t.status, "status_label": task_flow.STATUS_LABELS.get(t.status, t.status),
            "order_index": t.order_index, "priority": t.priority, "depends_on": t.depends_on or [],
            "assignee": who(t.assignee_actor_id), "approver": who(approver_id), "requires_approval": t.requires_approval,
            "rejection_count": t.rejection_count or 0, "max_rejections": t.max_rejections or 3,
            "started_at": t.started_at, "submitted_at": t.submitted_at, "completed_at": t.completed_at,
            "can_submit": t.status in task_flow.WORKING and (is_assignee or manages),
            "can_decide": t.status == "WAITING_APPROVAL" and (approver_id == user.actor_id or user.has("project:manage")),
            "can_release": t.status == "QUARANTINED" and manages,
        })
    return {"project_id": str(project.id), "status": project.status, "workflow_id": project.workflow_id, "tasks": out,
            "events": [{"id": str(e.id), "task_id": str(e.task_id) if e.task_id else None, "kind": e.kind, "actor": who(e.actor_id),
                        "note": e.note, "data": e.data, "created_at": e.created_at} for e in events]}


class SubmitIn(BaseModel):
    note: Optional[str] = Field(None, max_length=4000)


@router.post("/tasks/{task_id}/submit")
async def submit_task(task_id: uuid.UUID, payload: SubmitIn, user: CurrentUser = Depends(get_current_user),
                      db: AsyncSession = Depends(get_db)):
    """İş adımının çıktısını teslim eder (atanan insan personel veya AI personel adına proje yöneticisi)."""
    task, project = await _task(db, user, task_id)
    if task.status not in task_flow.WORKING:
        raise HTTPException(status_code=409, detail="Bu iş adımı şu an teslim edilebilir durumda değil.")
    if task.assignee_actor_id != user.actor_id and not _manages(user, project):
        raise forbidden("Bu iş adımını yalnızca atanan personel veya proje yöneticisi teslim edebilir.")
    await engine.signal_task(str(task.id), "submit", {"actor_id": str(user.actor_id), "note": (payload.note or "").strip()})
    return {"accepted": True}


class DecisionIn(BaseModel):
    approve: bool
    note: Optional[str] = Field(None, max_length=4000)


@router.post("/tasks/{task_id}/decision")
async def decide_task(task_id: uuid.UUID, payload: DecisionIn, user: CurrentUser = Depends(get_current_user),
                      db: AsyncSession = Depends(get_db)):
    """Onay veya ret (ret gerekçesi zorunlu). Onaylayıcı: adımın onaylayıcısı, yoksa proje yöneticisi."""
    task, project = await _task(db, user, task_id)
    if task.status != "WAITING_APPROVAL":
        raise HTTPException(status_code=409, detail="Bu iş adımı onay beklemiyor.")
    if (task.approver_actor_id or project.manager_actor_id) != user.actor_id and not user.has("project:manage"):
        raise forbidden("Bu iş adımını yalnızca onaylayıcısı onaylayabilir.")
    note = (payload.note or "").strip()
    if not payload.approve and not note:
        raise HTTPException(status_code=422, detail="Revizyon isterken gerekçeyi yazın; personel buna göre düzeltecek.")
    await engine.signal_task(str(task.id), "decide", {"actor_id": str(user.actor_id), "approve": payload.approve, "note": note})
    return {"accepted": True}


class ReleaseIn(BaseModel):
    action: str = Field(pattern="^(retry|cancel)$")
    note: Optional[str] = Field(None, max_length=4000)
    assignee_actor_id: Optional[uuid.UUID] = None  # yeniden denemede başka personele atama


@router.post("/tasks/{task_id}/release")
async def release_task(task_id: uuid.UUID, payload: ReleaseIn, user: CurrentUser = Depends(get_current_user),
                       db: AsyncSession = Depends(get_db)):
    """Karantinadaki iş adımı için proje yöneticisinin kararı: yeniden dene (isteğe bağlı başka personelle) veya iptal et."""
    task, project = await _task(db, user, task_id)
    if task.status != "QUARANTINED":
        raise HTTPException(status_code=409, detail="Bu iş adımı karantinada değil.")
    if not _manages(user, project):
        raise forbidden("Karantina kararını proje yöneticisi verir.")
    if payload.assignee_actor_id:
        actor = await db.get(Actor, payload.assignee_actor_id)
        if not actor or actor.tenant_id != project.tenant_id:
            raise HTTPException(status_code=422, detail="Personel bulunamadı.")
        await psvc.set_member(db, project, actor, None, user.actor_id)
        await db.commit()
    await engine.signal_task(str(task.id), "release", {
        "actor_id": str(user.actor_id), "action": payload.action, "note": (payload.note or "").strip(),
        "assignee_actor_id": str(payload.assignee_actor_id) if payload.assignee_actor_id else None})
    return {"accepted": True}
