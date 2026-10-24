"""
Proje şablonları uçları (ADIM 11.1).

Work Space (giriş yapmış kullanıcı):
- GET  /project-templates                     şirketin + RECDx'in etkin şablonları (RECDx personeli yalnızca platform şablonlarını görür)
- GET  /project-templates/{id}                şablon ve plan iskeleti
- POST /project-templates/{id}/use            şablondan yeni proje (project:create); plan taslak, AI personel unvanla eşleşir
- POST /projects/{id}/save-as-template        projeden şirket şablonu (proje yöneticisi); kişi kimliği şablona girmez
- PUT  /project-templates/{id}                şirket şablonunu düzenle/arşivle (oluşturan veya project:manage)
Süper Admin:
- GET  /system/project-templates              platform şablonları (arşivdekiler dahil)
- POST /system/project-templates              platform şablonu yayımla
- PUT  /system/project-templates/{id}         platform şablonunu düzenle/arşivle
"""
import uuid
from datetime import date
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import CurrentUser, ensure_tenant_content, get_current_user
from app.db.models import Project, ProjectTemplate
from app.db.session import get_db
from app.services import project_templates as tsvc
from app.services import projects as psvc

router = APIRouter(tags=["Proje Şablonları"])


def _super(user: CurrentUser) -> None:
    if not user.is_super_admin:
        raise HTTPException(status_code=403, detail="Bu işlem yalnızca RECDx Süper Admin içindir.")


async def _get(db: AsyncSession, user: CurrentUser, tid: uuid.UUID) -> ProjectTemplate:
    t = await db.get(ProjectTemplate, tid)
    if not tsvc.visible(user, t):
        raise HTTPException(status_code=404, detail="Şablon bulunamadı.")
    return t


@router.get("/project-templates")
async def list_templates(user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    cond = ProjectTemplate.tenant_id.is_(None)
    if not user.is_platform_staff:
        cond = or_(cond, ProjectTemplate.tenant_id == user.tenant_id)
    rows = (await db.execute(select(ProjectTemplate).where(cond, ProjectTemplate.status == "ACTIVE")
                             .order_by(ProjectTemplate.tenant_id.is_(None), ProjectTemplate.name))).scalars().all()
    return [tsvc.out(t) for t in rows]


@router.get("/project-templates/{template_id}")
async def get_template(template_id: uuid.UUID, user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return tsvc.out(await _get(db, user, template_id), full=True)


class UseIn(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    description: Optional[str] = None
    manager_actor_id: Optional[uuid.UUID] = None
    department_id: Optional[uuid.UUID] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None


@router.post("/project-templates/{template_id}/use")
async def use_template(template_id: uuid.UUID, payload: UseIn, user: CurrentUser = Depends(get_current_user),
                       db: AsyncSession = Depends(get_db)):
    from app.api.v1.projects import ProjectCreate, create_project

    t = await _get(db, user, template_id)
    if t.status != "ACTIVE":
        raise HTTPException(status_code=409, detail="Bu şablon arşivde.")
    created = await create_project(ProjectCreate(
        tenant_id=user.tenant_id, name=payload.name, kind=t.kind, field_package=t.field_package,
        description=payload.description or t.description, manager_actor_id=payload.manager_actor_id,
        department_id=payload.department_id, start_date=payload.start_date, end_date=payload.end_date), user, db)
    project = await db.get(Project, uuid.UUID(str(created["id"])))
    t = await db.get(ProjectTemplate, template_id)
    result = await tsvc.apply(db, t, project)
    await db.commit()
    return {**created, **result, "template": {"id": str(t.id), "name": t.name}}


class SaveIn(BaseModel):
    name: str = Field(..., min_length=2, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    category: Optional[str] = Field(None, max_length=80)
    keep_descriptions: bool = True


@router.post("/projects/{project_id}/save-as-template", status_code=201)
async def save_as_template(project_id: uuid.UUID, payload: SaveIn, user: CurrentUser = Depends(get_current_user),
                           db: AsyncSession = Depends(get_db)):
    project = await psvc.load(db, user, project_id, manage=True)
    ensure_tenant_content(user, project.tenant_id)
    if not (project.plan or {}).get("steps"):
        raise HTTPException(status_code=409, detail="Şablon için projenin planında en az bir iş adımı olmalı.")
    t = ProjectTemplate(tenant_id=project.tenant_id, name=payload.name.strip(), description=payload.description,
                        category=payload.category, kind=project.kind, field_package=project.field_package,
                        plan=tsvc.skeleton(project.plan, payload.keep_descriptions), source_project_id=project.id,
                        created_by_actor_id=user.actor_id)
    db.add(t)
    await db.commit()
    return tsvc.out(t, full=True)


class TemplateUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    category: Optional[str] = Field(None, max_length=80)
    status: Optional[str] = Field(None, pattern="^(ACTIVE|ARCHIVED)$")
    plan: Optional[Dict[str, Any]] = None


def _update(t: ProjectTemplate, payload: TemplateUpdate) -> None:
    for k in ("name", "description", "category", "status"):
        v = getattr(payload, k)
        if v is not None:
            setattr(t, k, v.strip() if isinstance(v, str) and k == "name" else v)
    if payload.plan is not None:
        plan = tsvc.skeleton(payload.plan)
        if not plan["steps"]:
            raise HTTPException(status_code=422, detail="Şablonda en az bir iş adımı olmalı.")
        t.plan = plan


@router.put("/project-templates/{template_id}")
async def update_template(template_id: uuid.UUID, payload: TemplateUpdate, user: CurrentUser = Depends(get_current_user),
                          db: AsyncSession = Depends(get_db)):
    t = await _get(db, user, template_id)
    if t.tenant_id is None:
        raise HTTPException(status_code=403, detail="RECDx şablonları yalnızca Süper Admin tarafından düzenlenir.")
    if not (t.created_by_actor_id == user.actor_id or user.has("project:manage")):
        raise HTTPException(status_code=403, detail="Şablonu yalnızca oluşturan veya proje yönetim yetkisi olan düzenler.")
    _update(t, payload)
    await db.commit()
    return tsvc.out(t, full=True)


# ---------------------------------------------------------------- Süper Admin: platform şablonları
@router.get("/system/project-templates")
async def platform_templates(user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    _super(user)
    rows = (await db.execute(select(ProjectTemplate).where(ProjectTemplate.tenant_id.is_(None))
                             .order_by(ProjectTemplate.status, ProjectTemplate.name))).scalars().all()
    return [tsvc.out(t, full=True) for t in rows]


class PlatformIn(BaseModel):
    name: str = Field(..., min_length=2, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    category: Optional[str] = Field(None, max_length=80)
    kind: str = Field("PROJECT", pattern="^(PROJECT|CASE)$")
    plan: Dict[str, Any]


@router.post("/system/project-templates", status_code=201)
async def create_platform_template(payload: PlatformIn, user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    _super(user)
    plan = tsvc.skeleton(payload.plan)
    if not plan["steps"]:
        raise HTTPException(status_code=422, detail="Şablonda en az bir iş adımı olmalı.")
    t = ProjectTemplate(tenant_id=None, name=payload.name.strip(), description=payload.description, category=payload.category,
                        kind=payload.kind, plan=plan, created_by_actor_id=user.actor_id)
    db.add(t)
    await db.commit()
    return tsvc.out(t, full=True)


@router.put("/system/project-templates/{template_id}")
async def update_platform_template(template_id: uuid.UUID, payload: TemplateUpdate, user: CurrentUser = Depends(get_current_user),
                                   db: AsyncSession = Depends(get_db)):
    _super(user)
    t = await db.get(ProjectTemplate, template_id)
    if not t or t.tenant_id is not None:  # şirket şablonu RECDx'e görünmez (KVKK)
        raise HTTPException(status_code=404, detail="Şablon bulunamadı.")
    _update(t, payload)
    await db.commit()
    return tsvc.out(t, full=True)
