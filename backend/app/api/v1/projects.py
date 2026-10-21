"""
Proje/Case API (ADIM 6). Yetki ve durum kuralları: app/services/projects.py
"""
import uuid
from datetime import date, datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import CurrentUser, ensure_tenant_content, get_current_user
from app.db.models import Actor, AgentDocument, Department, JobTitle, Project, ProjectMember, Task, Tenant
from app.db.session import get_db
from app.services import projects as svc

router = APIRouter(prefix="/projects", tags=["Projects & Tasks (İş Akışları)"])


class ProjectCreate(BaseModel):
    tenant_id: uuid.UUID
    name: str = Field(min_length=2, max_length=255)
    slug: Optional[str] = Field(None, max_length=64)
    kind: str = "PROJECT"  # PROJECT, CASE
    description: Optional[str] = None
    requirements: Optional[str] = None
    field_package: str = "GENEL"  # YAZILIM, GENEL
    manager_actor_id: Optional[uuid.UUID] = None  # boş: oluşturan kişi
    department_id: Optional[uuid.UUID] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None


class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    kind: Optional[str] = None
    description: Optional[str] = None
    requirements: Optional[str] = None
    field_package: Optional[str] = None
    manager_actor_id: Optional[uuid.UUID] = None
    department_id: Optional[uuid.UUID] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None


class ProjectResponse(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    slug: str
    name: str
    kind: str = "PROJECT"
    description: Optional[str] = None
    requirements: Optional[str] = None
    field_package: str
    status: str
    repo_url: Optional[str] = None
    manager_actor_id: Optional[uuid.UUID] = None
    department_id: Optional[uuid.UUID] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    planning_approved_at: Optional[datetime] = None
    ready_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    acceptance_criteria: Optional[str] = None
    priority: str = "MEDIUM"
    assignee_actor_id: Optional[uuid.UUID] = None
    estimated_effort: float = 1.0
    department_id: Optional[uuid.UUID] = None
    job_title_id: Optional[uuid.UUID] = None
    depends_on: List[uuid.UUID] = []
    order_index: Optional[int] = None


class TaskResponse(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    title: str
    description: Optional[str] = None
    acceptance_criteria: Optional[str] = None
    priority: str
    status: str
    assignee_actor_id: Optional[uuid.UUID] = None
    estimated_effort: float
    order_index: int = 0
    department_id: Optional[uuid.UUID] = None
    job_title_id: Optional[uuid.UUID] = None
    depends_on: List[Any] = []
    start_date: Optional[date] = None
    due_date: Optional[date] = None
    estimated_credits: Optional[float] = None
    reviewer_actor_id: Optional[uuid.UUID] = None
    approver_actor_id: Optional[uuid.UUID] = None
    requires_approval: bool = True
    max_rejections: int = 3
    rejection_count: int = 0
    started_at: Optional[datetime] = None
    submitted_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


def _out(p: Project) -> Dict[str, Any]:
    return {**ProjectResponse.model_validate(p).model_dump(), "status_label": svc.STATUS_LABELS.get(p.status, p.status)}


@router.get("")
@router.get("/")
async def list_projects(tenant_id: Optional[uuid.UUID] = Query(None),
                        scope: str = Query("mine", description="mine: üyesi olduğum projeler; all: şirketin tüm projeleri (project:manage)"),
                        user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    tenant_id = tenant_id or user.tenant_id
    ensure_tenant_content(user, tenant_id)
    stmt = select(Project).where(Project.tenant_id == tenant_id)
    if scope != "all" or not user.has("project:manage"):
        member_of = select(ProjectMember.project_id).where(ProjectMember.actor_id == user.actor_id)
        stmt = stmt.where(or_(Project.id.in_(member_of), Project.manager_actor_id == user.actor_id))
    rows = (await db.execute(stmt.order_by(Project.created_at.desc()))).scalars().all()
    counts = dict((await db.execute(select(Task.project_id, func.count()).where(Task.project_id.in_([p.id for p in rows] or [uuid.uuid4()]))
                                    .group_by(Task.project_id))).all())
    return [{**_out(p), "task_count": counts.get(p.id, 0)} for p in rows]


@router.post("")
@router.post("/")
async def create_project(payload: ProjectCreate, user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    ensure_tenant_content(user, payload.tenant_id, "project:create")
    tenant = await db.get(Tenant, payload.tenant_id)
    await svc.ensure_project_quota(db, tenant)
    manager = await svc.check_manager(db, tenant.id, payload.manager_actor_id or user.actor_id)
    if payload.department_id:
        dept = await db.get(Department, payload.department_id)
        if not dept or dept.tenant_id != tenant.id:
            raise HTTPException(status_code=422, detail="Departman bulunamadı.")
    if payload.slug and (await db.execute(select(Project.id).where(Project.tenant_id == tenant.id, Project.slug == payload.slug))).first():
        raise HTTPException(status_code=400, detail="Bu proje kodu (slug) şirketinizde zaten kullanımda.")
    project = Project(
        tenant_id=tenant.id, slug=payload.slug or await svc.unique_slug(db, tenant.id, payload.name), name=payload.name.strip(),
        kind=payload.kind if payload.kind in ("PROJECT", "CASE") else "PROJECT", description=payload.description,
        requirements=payload.requirements, field_package=payload.field_package, status="DRAFT",
        manager_actor_id=manager.id, department_id=payload.department_id, start_date=payload.start_date,
        end_date=payload.end_date, created_by_actor_id=user.actor_id,
    )
    db.add(project)
    await db.flush()
    await svc.set_member(db, project, manager, "MANAGER", user.actor_id)
    await db.commit()
    await db.refresh(project)
    return _out(project)


@router.get("/{project_id}")
async def get_project(project_id: uuid.UUID, user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    project = await svc.load(db, user, project_id)
    tasks = (await db.execute(select(Task).where(Task.project_id == project.id).order_by(Task.order_index, Task.created_at))).scalars().all()
    docs = (await db.execute(select(func.count()).select_from(AgentDocument).where(
        AgentDocument.project_id == project.id, AgentDocument.status.notin_(("DELETED",))))).scalar() or 0
    can_manage = user.has("project:manage") or project.manager_actor_id == user.actor_id
    return {**_out(project), "plan": project.plan, "simulation": project.simulation, "close_summary": project.close_summary,
            "members": await svc.members_out(db, project.id), "tasks": [TaskResponse.model_validate(t).model_dump() for t in tasks],
            "document_count": docs, "can_manage": can_manage}


@router.put("/{project_id}")
async def update_project(project_id: uuid.UUID, payload: ProjectUpdate, user: CurrentUser = Depends(get_current_user),
                         db: AsyncSession = Depends(get_db)):
    project = await svc.load(db, user, project_id, manage=True)
    if project.status not in svc.EDITABLE_STATUSES:
        raise HTTPException(status_code=409, detail="Başlamış veya kapanmış projenin temel bilgileri değiştirilemez.")
    data = payload.model_dump(exclude_unset=True)
    if "manager_actor_id" in data and data["manager_actor_id"]:
        manager = await svc.check_manager(db, project.tenant_id, data["manager_actor_id"])
        await svc.set_member(db, project, manager, "MANAGER", user.actor_id)
    if data.get("department_id"):
        dept = await db.get(Department, data["department_id"])
        if not dept or dept.tenant_id != project.tenant_id:
            raise HTTPException(status_code=422, detail="Departman bulunamadı.")
    if data.get("kind") and data["kind"] not in ("PROJECT", "CASE"):
        raise HTTPException(status_code=422, detail="Geçersiz tür.")
    for key, value in data.items():
        setattr(project, key, value.strip() if isinstance(value, str) else value)
    if project.start_date and project.end_date and project.end_date < project.start_date:
        raise HTTPException(status_code=422, detail="Bitiş tarihi başlangıçtan önce olamaz.")
    await db.commit()
    await db.refresh(project)
    return _out(project)


class StatusIn(BaseModel):
    action: str  # start_planning, mark_ready, reopen_planning, start, pause, resume, complete, cancel
    summary: Optional[str] = Field(None, max_length=4000)


@router.post("/{project_id}/status")
async def change_status(project_id: uuid.UUID, payload: StatusIn, user: CurrentUser = Depends(get_current_user),
                        db: AsyncSession = Depends(get_db)):
    project = await svc.load(db, user, project_id, manage=True)
    previous = project.status
    await svc.transition(db, project, payload.action, payload.summary)
    try:
        await _sync_workflow(project, payload.action, user)
    except HTTPException:
        # Akış motoruna ulaşılamadıysa durum geri alınır; kullanıcı tekrar dener
        project.status = previous
        if payload.action == "start":
            project.started_at = None
        if payload.action in ("complete", "cancel"):
            project.closed_at = None
        await db.commit()
        raise
    await db.commit()
    return _out(project)


async def _sync_workflow(project: Project, action: str, user: CurrentUser) -> None:
    """Proje durum geçişlerini Temporal proje akışına yansıtır (ADIM 7.1)."""
    from app.config import settings
    from app.workflows import engine

    if not settings.WORKFLOW_ENABLED:
        return
    if action == "start":
        project.workflow_id = await engine.start_project(str(project.id), str(user.actor_id))
    elif project.workflow_id and action in ("pause", "resume"):
        await engine.signal_project(str(project.id), action)
    elif project.workflow_id and action in ("complete", "cancel"):
        await engine.signal_project(str(project.id), "cancel", {"actor_id": str(user.actor_id), "note": "Proje kapatıldı."})


# ---------------------------------------------------------------- ekip
class MemberIn(BaseModel):
    actor_id: uuid.UUID
    role: Optional[str] = None  # insanlar için MEMBER veya MANAGER; AI personel her zaman AGENT


@router.post("/{project_id}/members")
async def add_member(project_id: uuid.UUID, payload: MemberIn, user: CurrentUser = Depends(get_current_user),
                     db: AsyncSession = Depends(get_db)):
    project = await svc.load(db, user, project_id, manage=True)
    actor = await db.get(Actor, payload.actor_id)
    if not actor:
        raise HTTPException(status_code=404, detail="Personel bulunamadı.")
    if actor.actor_type == "AI_AGENT" and actor.dismissed_at:
        raise HTTPException(status_code=422, detail="İşten çıkarılmış AI personel projeye eklenemez.")
    await svc.set_member(db, project, actor, payload.role, user.actor_id)
    await db.commit()
    return await svc.members_out(db, project.id)


@router.delete("/{project_id}/members/{actor_id}")
async def remove_member(project_id: uuid.UUID, actor_id: uuid.UUID, user: CurrentUser = Depends(get_current_user),
                        db: AsyncSession = Depends(get_db)):
    project = await svc.load(db, user, project_id, manage=True)
    if actor_id == project.manager_actor_id:
        raise HTTPException(status_code=409, detail="Proje yöneticisi ekipten çıkarılamaz; önce başka bir yönetici atayın.")
    if (await db.execute(select(Task.id).where(Task.project_id == project.id, Task.assignee_actor_id == actor_id,
                                                Task.status.notin_(("DONE", "CANCELLED"))))).first():
        raise HTTPException(status_code=409, detail="Bu personele atanmış açık iş adımları var; önce başka birine atayın.")
    member = await svc.membership(db, project.id, actor_id)
    if member:
        await db.delete(member)
        await db.commit()
    return await svc.members_out(db, project.id)


# ---------------------------------------------------------------- iş adımları
async def _check_task_refs(db: AsyncSession, project: Project, payload) -> None:
    if payload.assignee_actor_id:
        assignee = await db.get(Actor, payload.assignee_actor_id)
        if not assignee or assignee.tenant_id != project.tenant_id:
            raise HTTPException(status_code=400, detail="Görev yalnızca aynı şirketteki bir personele atanabilir.")
    if payload.job_title_id:
        title = await db.get(JobTitle, payload.job_title_id)
        if not title or title.tenant_id not in (None, project.tenant_id):
            raise HTTPException(status_code=400, detail="Unvan bulunamadı.")


@router.get("/{project_id}/tasks", response_model=List[TaskResponse])
async def list_tasks(project_id: uuid.UUID, user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    await svc.load(db, user, project_id)
    result = await db.execute(select(Task).where(Task.project_id == project_id).order_by(Task.order_index, Task.created_at))
    return result.scalars().all()


@router.post("/{project_id}/tasks", response_model=TaskResponse)
async def create_task(project_id: uuid.UUID, payload: TaskCreate, user: CurrentUser = Depends(get_current_user),
                      db: AsyncSession = Depends(get_db)):
    project = await svc.load(db, user, project_id)
    ensure_tenant_content(user, project.tenant_id, "task:create")
    await _check_task_refs(db, project, payload)
    last = (await db.execute(select(func.coalesce(func.max(Task.order_index), 0)).where(Task.project_id == project.id))).scalar()
    task = Task(
        project_id=project_id, title=payload.title, description=payload.description,
        acceptance_criteria=payload.acceptance_criteria, priority=payload.priority,
        assignee_actor_id=payload.assignee_actor_id, estimated_effort=payload.estimated_effort,
        department_id=payload.department_id, job_title_id=payload.job_title_id,
        depends_on=[str(d) for d in payload.depends_on], order_index=payload.order_index if payload.order_index is not None else last + 1,
        status="BACKLOG",
    )
    db.add(task)
    if payload.assignee_actor_id:
        await svc.set_member(db, project, await db.get(Actor, payload.assignee_actor_id), None, user.actor_id)
    await db.commit()
    await db.refresh(task)
    return task


# ---------------------------------------------------------------- Beyin AI planlama (ADIM 6.3) ve simülasyon (ADIM 6.4)
from app.services import project_planning as planning  # noqa: E402


class SuggestIn(BaseModel):
    feedback: Optional[str] = Field(None, max_length=4000)
    use_chat: bool = False  # planlama sohbetindeki konuşmayı geri bildirim olarak kullan


@router.post("/{project_id}/plan/suggest")
async def suggest_plan(project_id: uuid.UUID, payload: SuggestIn, user: CurrentUser = Depends(get_current_user),
                       db: AsyncSession = Depends(get_db)):
    """Beyin AI isterlerden iş adımlarını ve departman+unvan bazında personel önerisini çıkarır (taslak)."""
    project = await svc.load(db, user, project_id, manage=True)
    if project.status not in ("DRAFT", "PLANNING"):
        raise HTTPException(status_code=409, detail="Plan yalnızca taslak veya planlama aşamasında oluşturulabilir.")
    if not (project.requirements or "").strip():
        raise HTTPException(status_code=422, detail="Önce projenin isterlerini yazın.")
    feedback = payload.feedback
    if payload.use_chat:
        feedback = "\n".join(filter(None, [feedback, await planning.plan_feedback_from_chat(db, project)]))
    return await planning.suggest_plan(db, project, feedback)


class PlanIn(BaseModel):
    summary: Optional[str] = None
    steps: List[Dict[str, Any]]
    hire_suggestions: List[Dict[str, Any]] = []
    risks: List[str] = []
    questions: List[str] = []


@router.put("/{project_id}/plan")
async def update_plan(project_id: uuid.UUID, payload: PlanIn, user: CurrentUser = Depends(get_current_user),
                      db: AsyncSession = Depends(get_db)):
    """Yöneticinin düzenlediği plan taslağı (onay kaldırılır, yeniden onay gerekir)."""
    project = await svc.load(db, user, project_id, manage=True)
    if project.status not in ("DRAFT", "PLANNING"):
        raise HTTPException(status_code=409, detail="Plan yalnızca planlama aşamasında düzenlenebilir.")
    pool = {p["agent_id"] for p in await planning._team_pool(db, project.tenant_id)}
    plan = planning.validate_plan(payload.model_dump(), pool)
    old = project.plan or {}
    project.plan = {**plan, "model_code": old.get("model_code"), "generated_at": old.get("generated_at"),
                    "edited_at": svc.now().isoformat(), "approved": False,
                    "hire_suggestions": plan["hire_suggestions"] or old.get("hire_suggestions", [])}
    project.planning_approved_at = None
    if project.status == "DRAFT":
        project.status = "PLANNING"
    await db.commit()
    return project.plan


@router.post("/{project_id}/plan/approve")
async def approve_plan(project_id: uuid.UUID, user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Planı onaylar: adımlar iş adımlarına (görevlere) dönüşür, önerilen AI personel ekibe eklenir."""
    project = await svc.load(db, user, project_id, manage=True)
    tasks = await planning.approve_plan(db, project, user.actor_id)
    return {"success": True, "task_count": len(tasks), "unassigned": sum(1 for t in tasks if not t.assignee_actor_id)}


@router.get("/{project_id}/plan/chat")
async def plan_chat_history(project_id: uuid.UUID, user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    from app.db.models import ChatMessage

    project = await svc.load(db, user, project_id)
    rows = (await db.execute(select(ChatMessage).where(ChatMessage.project_id == project.id, ChatMessage.message_type == "PLAN_CHAT")
                             .order_by(ChatMessage.created_at))).scalars().all()
    return [{"id": str(m.id), "role": m.role, "content": m.content, "created_at": m.created_at} for m in rows]


class PlanChatIn(BaseModel):
    content: str = Field(min_length=1, max_length=8000)


@router.post("/{project_id}/plan/chat")
async def plan_chat(project_id: uuid.UUID, payload: PlanChatIn, user: CurrentUser = Depends(get_current_user),
                    db: AsyncSession = Depends(get_db)):
    project = await svc.load(db, user, project_id, manage=True)
    return await planning.plan_chat(db, project, user.actor_id, payload.content.strip())


class SimulateIn(BaseModel):
    start_date: Optional[date] = None


@router.post("/{project_id}/simulate")
async def simulate(project_id: uuid.UUID, payload: SimulateIn, user: CurrentUser = Depends(get_current_user),
                   db: AsyncSession = Depends(get_db)):
    """Tarihleri, süreyi, tahmini krediyi ve riskleri hesaplar; iş adımlarının tarihlerini günceller."""
    project = await svc.load(db, user, project_id, manage=True)
    if project.status not in ("DRAFT", "PLANNING", "READY"):
        raise HTTPException(status_code=409, detail="Simülasyon yalnızca proje başlamadan önce yapılabilir.")
    return await planning.simulate(db, project, payload.start_date)
