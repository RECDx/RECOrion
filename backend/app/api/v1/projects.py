from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from app.db.session import get_db
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


@router.get("", response_model=List[ProjectResponse])
@router.get("/", response_model=List[ProjectResponse])
async def list_projects(tenant_id: Optional[uuid.UUID] = Query(None), db: AsyncSession = Depends(get_db)):
    stmt = select(Project)
    if tenant_id:
        stmt = stmt.where(Project.tenant_id == tenant_id)
    stmt = stmt.order_by(Project.created_at.desc())
    result = await db.execute(stmt)
    return result.scalars().all()


@router.post("", response_model=ProjectResponse)
@router.post("/", response_model=ProjectResponse)
async def create_project(payload: ProjectCreate, db: AsyncSession = Depends(get_db)):
    existing = await db.execute(select(Project).where(Project.tenant_id == payload.tenant_id, Project.slug == payload.slug))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Bu proje kodu (slug) şirketinizde zaten kullanımda.")

    project = Project(
        tenant_id=payload.tenant_id,
        slug=payload.slug,
        name=payload.name,
        description=payload.description,
        field_package=payload.field_package,
        status="ACTIVE"
    )
    db.add(project)
    await db.commit()
    await db.refresh(project)
    return project


@router.get("/{project_id}/tasks", response_model=List[TaskResponse])
async def list_tasks(project_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Task).where(Task.project_id == project_id).order_by(Task.created_at))
    return result.scalars().all()


@router.post("/{project_id}/tasks", response_model=TaskResponse)
async def create_task(project_id: uuid.UUID, payload: TaskCreate, db: AsyncSession = Depends(get_db)):
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
