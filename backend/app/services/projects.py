"""
Proje/Case çekirdeği (ADIM 6): yetki, ekip ve durum geçişleri.

Durumlar: DRAFT > PLANNING > READY > ACTIVE > (PAUSED) > COMPLETED | CANCELLED
- Proje yöneticisi şirketin insan kullanıcısıdır (kullanıcı kararı); AI personel ekipte AGENT rolüyle yer alır.
- Proje içeriği şirket içeriğidir (KVKK): RECDx yöneticileri erişemez.
- Projeyi görme: ekip üyeleri ve project:manage yetkisi olanlar. Düzenleme: proje yöneticisi veya project:manage.
"""
import re
import unicodedata
import uuid
from datetime import date, datetime, timezone
from typing import Dict, List, Optional

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import CurrentUser, ensure_tenant_content, forbidden
from app.db.models import Actor, Plan, Project, ProjectMember, Task, Tenant

OPEN_STATUSES = ("DRAFT", "PLANNING", "READY", "ACTIVE", "PAUSED")
EDITABLE_STATUSES = ("DRAFT", "PLANNING", "READY")
STATUS_LABELS = {"DRAFT": "Taslak", "PLANNING": "Planlama", "READY": "Başlamaya hazır", "ACTIVE": "Aktif",
                 "PAUSED": "Duraklatıldı", "COMPLETED": "Tamamlandı", "CANCELLED": "İptal edildi"}


def now() -> datetime:
    return datetime.now(timezone.utc)


def slugify(text: str) -> str:
    text = unicodedata.normalize("NFKD", text.replace("ı", "i").replace("İ", "I")).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:48] or "proje"


async def unique_slug(db: AsyncSession, tenant_id: uuid.UUID, name: str) -> str:
    base = slugify(name)
    slug, n = base, 1
    while (await db.execute(select(Project.id).where(Project.tenant_id == tenant_id, Project.slug == slug))).first():
        n += 1
        slug = f"{base}-{n}"
    return slug


async def membership(db: AsyncSession, project_id: uuid.UUID, actor_id: uuid.UUID) -> Optional[ProjectMember]:
    return (await db.execute(select(ProjectMember).where(
        ProjectMember.project_id == project_id, ProjectMember.actor_id == actor_id))).scalars().first()


async def load(db: AsyncSession, user: CurrentUser, project_id: uuid.UUID, manage: bool = False) -> Project:
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Proje bulunamadı.")
    ensure_tenant_content(user, project.tenant_id)
    if user.has("project:manage") or project.manager_actor_id == user.actor_id:
        return project
    if manage:
        raise forbidden("Bu projeyi yalnızca proje yöneticisi veya proje yönetim yetkisi olanlar düzenleyebilir.")
    if not await membership(db, project.id, user.actor_id):
        raise forbidden("Bu projenin ekibinde değilsiniz.")
    return project


async def ensure_project_quota(db: AsyncSession, tenant: Tenant) -> None:
    plan = await db.get(Plan, tenant.plan_id) if tenant.plan_id else None
    if not plan or plan.max_projects is None or tenant.slug == "recdx_hq":
        return
    open_count = (await db.execute(select(func.count()).select_from(Project).where(
        Project.tenant_id == tenant.id, Project.status.in_(OPEN_STATUSES)))).scalar() or 0
    if open_count >= plan.max_projects:
        raise HTTPException(status_code=403, detail=f"'{plan.name}' paketinizde aynı anda en fazla {plan.max_projects} açık proje "
                                                    "olabilir. Tamamlanan veya iptal edilen projeler sayılmaz.")


async def check_manager(db: AsyncSession, tenant_id: uuid.UUID, actor_id: uuid.UUID) -> Actor:
    actor = await db.get(Actor, actor_id)
    if not actor or actor.tenant_id != tenant_id or actor.actor_type != "HUMAN":
        raise HTTPException(status_code=422, detail="Proje yöneticisi şirketinizin insan kullanıcılarından biri olmalıdır.")
    return actor


async def set_member(db: AsyncSession, project: Project, actor: Actor, role: Optional[str], added_by: uuid.UUID) -> ProjectMember:
    if actor.tenant_id != project.tenant_id:
        raise HTTPException(status_code=422, detail="Projeye yalnızca aynı şirketin personeli eklenebilir.")
    role = "AGENT" if actor.actor_type == "AI_AGENT" else (role if role in ("MANAGER", "MEMBER") else "MEMBER")
    # Oturumda henüz yazılmamış (aynı işlemde eklenmiş) üyelik de dikkate alınır
    member = next((o for o in db.new if isinstance(o, ProjectMember) and o.project_id == project.id and o.actor_id == actor.id), None)         or await membership(db, project.id, actor.id)
    if member:
        member.role = role if member.role != "MANAGER" else member.role
    else:
        member = ProjectMember(project_id=project.id, actor_id=actor.id, role=role, added_by_actor_id=added_by)
        db.add(member)
    return member


async def transition(db: AsyncSession, project: Project, action: str, summary: Optional[str] = None) -> Project:
    """Durum geçişleri; her geçişin önkoşulları burada denetlenir."""
    s = project.status
    tasks = (await db.execute(select(Task).where(Task.project_id == project.id))).scalars().all()

    def need(cond: bool, msg: str):
        if not cond:
            raise HTTPException(status_code=409, detail=msg)

    if action == "start_planning":
        need(s == "DRAFT", "Yalnızca taslak projeler planlamaya alınabilir.")
        need(bool((project.requirements or "").strip()), "Planlamaya geçmeden önce projenin isterlerini yazın.")
        project.status = "PLANNING"
    elif action == "mark_ready":
        need(s == "PLANNING", "Yalnızca planlamadaki projeler hazır yapılabilir.")
        need(bool(project.planning_approved_at) and bool(tasks), "Önce iş adımlarını onaylayın.")
        need(bool(project.start_date and project.end_date), "Başlangıç ve bitiş tarihlerini belirleyin.")
        need(project.end_date >= project.start_date, "Bitiş tarihi başlangıçtan önce olamaz.")
        unassigned = [t.title for t in tasks if not t.assignee_actor_id]
        need(not unassigned, "Atanmamış iş adımları var: " + ", ".join(unassigned[:5]))
        project.status, project.ready_at = "READY", now()
    elif action == "reopen_planning":
        need(s == "READY", "Yalnızca hazır projeler yeniden planlamaya alınabilir.")
        project.status, project.ready_at = "PLANNING", None
    elif action == "start":
        need(s == "READY", "Yalnızca başlamaya hazır projeler başlatılabilir.")
        project.status, project.started_at = "ACTIVE", now()
        for t in tasks:  # bağımlılığı olmayan adımlar başlayabilir
            if t.status == "BACKLOG" and not (t.depends_on or []):
                t.status = "READY"
    elif action == "pause":
        need(s == "ACTIVE", "Yalnızca aktif projeler duraklatılabilir.")
        project.status = "PAUSED"
    elif action == "resume":
        need(s == "PAUSED", "Yalnızca duraklatılmış projeler devam ettirilebilir.")
        project.status = "ACTIVE"
    elif action == "complete":
        need(s in ("ACTIVE", "PAUSED"), "Yalnızca aktif veya duraklatılmış projeler tamamlanabilir.")
        project.status, project.closed_at, project.close_summary = "COMPLETED", now(), (summary or "").strip() or None
    elif action == "cancel":
        need(s not in ("COMPLETED", "CANCELLED"), "Bu proje zaten kapanmış.")
        project.status, project.closed_at, project.close_summary = "CANCELLED", now(), (summary or "").strip() or None
    else:
        raise HTTPException(status_code=400, detail="Bilinmeyen işlem.")
    await db.commit()
    return project


def to_date(v) -> Optional[date]:
    if v in (None, ""):
        return None
    return v if isinstance(v, date) else date.fromisoformat(str(v)[:10])


async def members_out(db: AsyncSession, project_id: uuid.UUID) -> List[Dict]:
    rows = (await db.execute(select(ProjectMember, Actor).join(Actor, Actor.id == ProjectMember.actor_id)
                             .where(ProjectMember.project_id == project_id).order_by(ProjectMember.role, Actor.display_name))).all()
    return [{"actor_id": str(a.id), "display_name": a.display_name, "actor_type": a.actor_type, "role": m.role,
             "email": a.email if a.actor_type == "HUMAN" else None, "status": a.status} for m, a in rows]


SOURCE_MODELS = {"helpdesk.ticket": "destek bileti", "sale.order": "satış siparişi", "project.task": "görev", "hr.expense": "masraf"}


def source_label(ref: Optional[str]) -> Optional[str]:
    """Dış kayıt bağı (ADIM 13.3) ekranda: "odoo:helpdesk.ticket:42" → "Odoo destek bileti #42"."""
    parts = (ref or "").split(":")
    if len(parts) != 3 or not parts[2]:
        return ref or None
    connector, model, rid = parts
    return f"{connector.capitalize()} {SOURCE_MODELS.get(model, model)} #{rid}"
