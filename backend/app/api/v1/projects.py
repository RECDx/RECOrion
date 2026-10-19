from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from app.db.session import get_db
from app.core.security import CurrentUser, ensure_tenant_content, get_current_user
from app.db.models import Project, Task, Actor
from pydantic import BaseModel
import uuid

router = APIRouter(prefix="/projects", tags=["Projects & Tasks (İş Akışları)"])


class ProjectCreate(BaseModel):
    tenant_id: uuid.UUID
    slug: str
    name: str
    description: Optional[str] = None
    field_package: str = "GENEL"  # YAZILIM, GENEL


class ProjectResponse(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    slug: str
    name: str
    description: Optional[str] = None
    field_package: str
    status: str
    repo_url: Optional[str] = None

    class Config:
        from_attributes = True


class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    acceptance_criteria: Optional[str] = None
    priority: str = "MEDIUM"
    assignee_actor_id: Optional[uuid.UUID] = None
    estimated_effort: float = 1.0


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

    class Config:
        from_attributes = True


async def _get_project_for(db: AsyncSession, user: CurrentUser, project_id: uuid.UUID, permission: Optional[str] = None) -> Project:
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Proje bulunamadı.")
    ensure_tenant_content(user, project.tenant_id, permission)
    return project


@router.get("", response_model=List[ProjectResponse])
@router.get("/", response_model=List[ProjectResponse])
async def list_projects(
    tenant_id: Optional[uuid.UUID] = Query(None),
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    tenant_id = tenant_id or user.tenant_id
    ensure_tenant_content(user, tenant_id)
    stmt = select(Project).where(Project.tenant_id == tenant_id)
    stmt = stmt.order_by(Project.created_at.desc())
    result = await db.execute(stmt)
    return result.scalars().all()


@router.post("", response_model=ProjectResponse)
@router.post("/", response_model=ProjectResponse)
async def create_project(payload: ProjectCreate, user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    ensure_tenant_content(user, payload.tenant_id, "project:create")
    existing = await db.execute(select(Project).where(Project.tenant_id == payload.tenant_id, Project.slug == payload.slug))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Bu proje kodu (slug) şirketinizde zaten kullanımda.")

    project = Project(
        tenant_id=payload.tenant_id,
        slug=payload.slug,
        name=payload.name,
        description=payload.description,
        field_package=payload.field_package,
        status="ACTIVE",
        created_by_actor_id=user.actor_id,
    )
    db.add(project)
    await db.commit()
    await db.refresh(project)
    return project


@router.get("/{project_id}/tasks", response_model=List[TaskResponse])
async def list_tasks(project_id: uuid.UUID, user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    await _get_project_for(db, user, project_id)
    result = await db.execute(select(Task).where(Task.project_id == project_id).order_by(Task.created_at))
    return result.scalars().all()


@router.post("/{project_id}/tasks", response_model=TaskResponse)
async def create_task(project_id: uuid.UUID, payload: TaskCreate, user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    project = await _get_project_for(db, user, project_id, "task:create")
    if payload.assignee_actor_id:
        assignee = await db.get(Actor, payload.assignee_actor_id)
        if not assignee or assignee.tenant_id != project.tenant_id:
            raise HTTPException(status_code=400, detail="Görev yalnızca aynı şirketteki bir personele atanabilir.")
    task = Task(
        project_id=project_id,
        title=payload.title,
        description=payload.description,
        acceptance_criteria=payload.acceptance_criteria,
        priority=payload.priority,
        assignee_actor_id=payload.assignee_actor_id,
        estimated_effort=payload.estimated_effort,
        status="BACKLOG"
    )
    db.add(task)
    await db.commit()
    await db.refresh(task)
    return task
