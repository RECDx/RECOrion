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
from app.db.models import Actor, Artifact, Project, Task, TaskEvent
from app.db.session import get_db
from app.services import projects as psvc
from app.services import agent_work, task_flow
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
    ids = ({t.assignee_actor_id for t in tasks} | {t.approver_actor_id for t in tasks} | {t.reviewer_actor_id for t in tasks}
           | {e.actor_id for e in events} | {project.manager_actor_id})
    latest = {}
    for art in (await db.execute(select(Artifact).where(Artifact.task_id.in_([t.id for t in tasks] or [uuid.uuid4()]))
                                 .order_by(Artifact.version))).scalars():
        latest[art.task_id] = art
    names = {a.id: a for a in (await db.execute(select(Actor).where(Actor.id.in_([i for i in ids if i] or [uuid.uuid4()])))).scalars()}
    manages = _manages(user, project)

    def who(aid):
        a = names.get(aid)
        return {"id": str(a.id), "name": a.display_name, "type": a.actor_type} if a else None

    from app.services import sandbox
    gates = {t.id: await sandbox.acceptance_gate(db, project, t) for t in tasks if t.status in ("WAITING_APPROVAL", "QUARANTINED")}
    # F86: duran adımın nedeni kartta görünsün (son "yeniden dene"den sonraki en son BLOCKED kaydı)
    blocked, unreviewed = {}, {}
    for e in events:  # en yeniden eskiye
        if e.task_id and e.task_id not in blocked and e.kind in ("BLOCKED", "RELEASED"):
            blocked[e.task_id] = e.note if e.kind == "BLOCKED" else None
        # F89: son sürüm kontrol personelinden geçmeden onaya geldiyse kartta uyarı
        if e.task_id and e.task_id not in unreviewed and e.kind in ("REVIEW_SKIPPED", "REVIEW_PASSED", "REVIEW_FAILED", "AI_OUTPUT"):
            unreviewed[e.task_id] = e.note if (e.kind == "REVIEW_SKIPPED" and (e.data or {}).get("unreviewed")) else None
    # F82: yönetici revizyonları kontrol retlerinden ayrı sayılır; bu revizyon karantinaya götürecekse önceden söylenir
    revision_left = {}
    for t in tasks:
        if t.status == "WAITING_APPROVAL":
            used = await task_flow.rejections_since_release(db, t, "REJECTED")
            revision_left[t.id] = {"used": used, "max": int(t.max_rejections or 3)}
    out = []
    for t in tasks:
        approver_id = t.approver_actor_id or project.manager_actor_id
        is_assignee = t.assignee_actor_id == user.actor_id
        assignee = names.get(t.assignee_actor_id)
        art = latest.get(t.id)
        out.append({
            "id": str(t.id), "title": t.title, "status": t.status, "status_label": task_flow.STATUS_LABELS.get(t.status, t.status),
            "order_index": t.order_index, "priority": t.priority, "depends_on": t.depends_on or [],
            "assignee": who(t.assignee_actor_id), "approver": who(approver_id), "reviewer": who(t.reviewer_actor_id),
            "requires_approval": t.requires_approval,
            "artifact": {"id": str(art.id), "version": art.version, "name": art.name, "created_at": art.created_at} if art else None,
            "ai_working": bool(assignee and assignee.actor_type == "AI_AGENT" and t.status in task_flow.WORKING),
            "rejection_count": t.rejection_count or 0, "max_rejections": t.max_rejections or 3,
            "started_at": t.started_at, "submitted_at": t.submitted_at, "completed_at": t.completed_at,
            # AI personel kendi teslim eder; insan personeli yerine yönetici de teslim edebilir
            "can_submit": t.status in task_flow.WORKING and (assignee is None or assignee.actor_type == "HUMAN") and (is_assignee or manages),
            "can_decide": t.status == "WAITING_APPROVAL" and (approver_id == user.actor_id or user.has("project:manage")
                                                              or user.has("task:approve") or user.has("task:reject")),
            "can_release": t.status == "QUARANTINED" and manages,
            "can_cancel": manages and t.status not in task_flow.CLOSED and t.status != "QUARANTINED" and project.status in ("ACTIVE", "PAUSED"),
            "can_edit_people": manages and t.status not in task_flow.CLOSED,  # F92
            "fix_kind": t.fix_kind, "fix_of_task_id": str(t.fix_of_task_id) if t.fix_of_task_id else None,
            "acceptance_warning": gates.get(t.id),  # kabul kapısı (#734): onaydan önce gösterilir
            "manager_revisions": revision_left.get(t.id),  # F82: {used, max}
            "blocked_reason": blocked.get(t.id) if t.status == "QUARANTINED" else None,  # F86
            "unreviewed_warning": unreviewed.get(t.id) if t.status == "WAITING_APPROVAL" else None,  # F89
            "can_accept_last": t.status == "QUARANTINED" and manages and bool(latest.get(t.id)),  # F90
            # ADIM 12.4: çıktıyı dış sisteme aktarma (proje yöneticisi) ve adım bitince önerilecek eşlemeler
            "can_transfer": manages and t.status in ("DONE", "WAITING_APPROVAL") and bool(art),
            "transfer_mapping_ids": t.transfer_mapping_ids or [],
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
    assignee = await db.get(Actor, task.assignee_actor_id) if task.assignee_actor_id else None
    if assignee and assignee.actor_type == "AI_AGENT":
        raise HTTPException(status_code=409, detail="Bu adımı AI personel yürütüyor; çıktısını kendisi teslim eder.")
    await engine.signal_task(str(task.id), "submit", {"actor_id": str(user.actor_id), "note": (payload.note or "").strip()})
    return {"accepted": True}


class DecisionIn(BaseModel):
    approve: bool
    note: Optional[str] = Field(None, max_length=4000)
    force: bool = False  # kabul kapısı uyarısına rağmen onay (#734); geçmişe yazılır


@router.post("/tasks/{task_id}/decision")
async def decide_task(task_id: uuid.UUID, payload: DecisionIn, user: CurrentUser = Depends(get_current_user),
                      db: AsyncSession = Depends(get_db)):
    """Onay veya ret (ret gerekçesi zorunlu). Onaylayıcı: adımın onaylayıcısı, yoksa proje yöneticisi."""
    task, project = await _task(db, user, task_id)
    if task.status != "WAITING_APPROVAL":
        raise HTTPException(status_code=409, detail="Bu iş adımı onay beklemiyor.")
    deputy = user.has("task:approve" if payload.approve else "task:reject")  # vekâleten karar (Kalite ve Onay Sorumlusu)
    if (task.approver_actor_id or project.manager_actor_id) != user.actor_id and not (user.has("project:manage") or deputy):
        raise forbidden("Bu iş adımını yalnızca onaylayıcısı onaylayabilir.")
    note = (payload.note or "").strip()
    if not payload.approve and not note:
        raise HTTPException(status_code=422, detail="Revizyon isterken gerekçeyi yazın; personel buna göre düzeltecek.")
    if payload.approve:
        from app.services import sandbox
        gate = await sandbox.acceptance_gate(db, project, task)
        if gate and not payload.force:
            raise HTTPException(status_code=409, detail={"code": "TEST_GATE", "message": gate})
        if gate:
            await task_flow.log(db, project, task, "TEST_GATE_OVERRIDE", user.actor_id, gate)
            await db.commit()
    await engine.signal_task(str(task.id), "decide", {"actor_id": str(user.actor_id), "approve": payload.approve, "note": note})
    return {"accepted": True}


class ReleaseIn(BaseModel):
    action: str = Field(pattern="^(retry|cancel|approve)$")  # approve: son sürümü gerekçeyle kabul (F90)
    note: Optional[str] = Field(None, max_length=4000)
    assignee_actor_id: Optional[uuid.UUID] = None  # yeniden denemede başka personele atama
    force: bool = False  # kabul kapısı uyarısına rağmen (#734)


@router.post("/tasks/{task_id}/release")
async def release_task(task_id: uuid.UUID, payload: ReleaseIn, user: CurrentUser = Depends(get_current_user),
                       db: AsyncSession = Depends(get_db)):
    """Karantinadaki iş adımı için proje yöneticisinin kararı: yeniden dene (isteğe bağlı başka personelle) veya iptal et."""
    task, project = await _task(db, user, task_id)
    if task.status != "QUARANTINED":
        raise HTTPException(status_code=409, detail="Bu iş adımı karantinada değil.")
    if not _manages(user, project):
        raise forbidden("Karantina kararını proje yöneticisi verir.")
    if payload.action == "approve":
        if not (payload.note or "").strip():
            raise HTTPException(status_code=422, detail="Son sürümü kabul ederken gerekçeyi yazın; akış geçmişine kaydedilir.")
        if not (await db.execute(select(Artifact.id).where(Artifact.task_id == task.id).limit(1))).scalar():
            raise HTTPException(status_code=409, detail="Bu adımın kabul edilecek bir çıktısı yok; yeniden deneyin veya iptal edin.")
        from app.services import sandbox
        gate = await sandbox.acceptance_gate(db, project, task)
        if gate and not payload.force:
            raise HTTPException(status_code=409, detail={"code": "TEST_GATE", "message": gate})
        if gate:
            await task_flow.log(db, project, task, "TEST_GATE_OVERRIDE", user.actor_id, gate)
            await db.commit()
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


@router.get("/tasks/{task_id}/people")
async def task_people(task_id: uuid.UUID, user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """F92: adımın kişileri ve seçenekler (proje yöneticisi): kontrol personeli = şirketin AI personeli; onaylayıcı = insan personel."""
    task, project = await _task(db, user, task_id)
    if not _manages(user, project):
        raise forbidden("Adımın kişilerini proje yöneticisi değiştirir.")
    actors = (await db.execute(select(Actor).where(Actor.tenant_id == project.tenant_id, Actor.status != "DISABLED")
                               .order_by(Actor.display_name))).scalars().all()
    pick = lambda a: {"id": str(a.id), "name": a.display_name, "role": a.role}  # noqa: E731
    return {"reviewer_actor_id": str(task.reviewer_actor_id) if task.reviewer_actor_id else None,
            "approver_actor_id": str(task.approver_actor_id) if task.approver_actor_id else None,
            "assignee_actor_id": str(task.assignee_actor_id) if task.assignee_actor_id else None,
            "manager_actor_id": str(project.manager_actor_id) if project.manager_actor_id else None,
            "can_change_assignee": task.status in ("BACKLOG", "READY"),
            "reviewers": [pick(a) for a in actors if a.actor_type == "AI_AGENT" and a.id != task.assignee_actor_id],
            "approvers": [pick(a) for a in actors if a.actor_type == "HUMAN"],
            "assignees": [pick(a) for a in actors if a.actor_type == "AI_AGENT"]}


class PeopleIn(BaseModel):
    reviewer_actor_id: Optional[uuid.UUID] = None  # boş: kontrol personeli yok
    approver_actor_id: Optional[uuid.UUID] = None  # boş: proje yöneticisi onaylar
    assignee_actor_id: Optional[uuid.UUID] = None  # yalnız başlamamış adımda; boş: değişmez
    note: Optional[str] = Field(None, max_length=1000)


@router.put("/tasks/{task_id}/people")
async def set_task_people(task_id: uuid.UUID, payload: PeopleIn, user: CurrentUser = Depends(get_current_user),
                          db: AsyncSession = Depends(get_db)):
    """F92: plan onaylandıktan sonra da adımın kontrol personeli / onaylayıcısı (başlamamışsa personeli) değiştirilir veya
    kontrol personeli kaldırılır. Değişiklik akış geçmişine yazılır; çalışan adımda bir sonraki teslimde geçerli olur."""
    task, project = await _task(db, user, task_id)
    if not _manages(user, project):
        raise forbidden("Adımın kişilerini proje yöneticisi değiştirir.")
    if task.status in task_flow.CLOSED:
        raise HTTPException(status_code=409, detail="Kapanmış adımın kişileri değiştirilemez.")

    async def own(aid, kind, label):
        if not aid:
            return None
        a = await db.get(Actor, aid)
        if not a or a.tenant_id != project.tenant_id or a.actor_type != kind or a.status == "DISABLED":
            raise HTTPException(status_code=422, detail=f"{label} bulunamadı.")
        return a
    reviewer = await own(payload.reviewer_actor_id, "AI_AGENT", "Kontrol personeli")
    approver = await own(payload.approver_actor_id, "HUMAN", "Onaylayıcı")
    assignee = await own(payload.assignee_actor_id, "AI_AGENT", "AI personel")
    if assignee and assignee.id != task.assignee_actor_id and task.status not in ("BACKLOG", "READY"):
        raise HTTPException(status_code=409, detail="Başlamış adımın personeli buradan değiştirilemez; karantinada 'Yeniden dene' ile başka personel seçin.")
    new_assignee = assignee.id if assignee else task.assignee_actor_id
    if reviewer and reviewer.id == new_assignee:
        raise HTTPException(status_code=422, detail="Kontrol personeli işi yapan personelden farklı olmalı.")
    before = {"reviewer": str(task.reviewer_actor_id or ""), "approver": str(task.approver_actor_id or ""), "assignee": str(task.assignee_actor_id or "")}
    task.reviewer_actor_id = reviewer.id if reviewer else None
    task.approver_actor_id = approver.id if approver else None
    task.assignee_actor_id = new_assignee
    for a in (reviewer, approver, assignee):
        if a:
            await psvc.set_member(db, project, a, None, user.actor_id)
    after = {"reviewer": str(task.reviewer_actor_id or ""), "approver": str(task.approver_actor_id or ""), "assignee": str(task.assignee_actor_id or "")}
    if before != after:
        names = []
        if before["reviewer"] != after["reviewer"]:
            names.append(f"kontrol personeli: {reviewer.display_name if reviewer else 'yok'}")
        if before["approver"] != after["approver"]:
            names.append(f"onaylayıcı: {approver.display_name if approver else 'proje yöneticisi'}")
        if before["assignee"] != after["assignee"]:
            names.append(f"personel: {assignee.display_name}")
        await task_flow.log(db, project, task, "PEOPLE_CHANGED", user.actor_id,
                            "; ".join(names) + (f" — {payload.note.strip()}" if (payload.note or "").strip() else ""), {"before": before, "after": after})
    await db.commit()
    return {"ok": True, "changed": before != after}


class CancelIn(BaseModel):
    note: Optional[str] = Field(None, max_length=4000)


@router.post("/tasks/{task_id}/cancel")
async def cancel_task(task_id: uuid.UUID, payload: CancelIn, user: CurrentUser = Depends(get_current_user),
                      db: AsyncSession = Depends(get_db)):
    """F110: proje yöneticisi sıradaki, çalışan, onay bekleyen veya revizyondaki gereksiz adımı iptal eder (gerekçe zorunlu).
    Başlamamış adım hemen kapanır; çalışan AI adımı elindeki iş bitince kapanır. Bu adıma bağlı adımlar beklemeden devam eder."""
    task, project = await _task(db, user, task_id)
    if not _manages(user, project):
        raise forbidden("Adımı proje yöneticisi iptal eder.")
    if task.status in task_flow.CLOSED:
        raise HTTPException(status_code=409, detail="Bu iş adımı zaten kapalı.")
    if task.status == "QUARANTINED":
        raise HTTPException(status_code=409, detail="Karantinadaki adım için 'Adımı iptal et' kararını kullanın.")
    note = (payload.note or "").strip()
    if not note:
        raise HTTPException(status_code=422, detail="İptal gerekçesini yazın; akış geçmişine kaydedilir.")
    state = await task_flow.request_cancel(db, task, project, user.actor_id, note)
    return {"accepted": True, "state": state}


@router.get("/tasks/{task_id}/artifacts/{artifact_id}")
async def artifact_content(task_id: uuid.UUID, artifact_id: uuid.UUID, user: CurrentUser = Depends(get_current_user),
                           db: AsyncSession = Depends(get_db)):
    """İş adımı çıktısının (artefakt) içeriği; proje ekibi görür."""
    task = await db.get(Task, task_id)
    art = await db.get(Artifact, artifact_id)
    if not task or not art or art.task_id != task.id:
        raise HTTPException(status_code=404, detail="Çıktı bulunamadı.")
    await psvc.load(db, user, task.project_id)
    versions = (await db.execute(select(Artifact.id, Artifact.version, Artifact.created_at).where(Artifact.task_id == task.id)
                                 .order_by(Artifact.version.desc()))).all()
    return {"id": str(art.id), "name": art.name, "version": art.version, "created_at": art.created_at,
            "content": await agent_work.artifact_text(art, 200_000),
            "versions": [{"id": str(v.id), "version": v.version, "created_at": v.created_at} for v in versions]}
