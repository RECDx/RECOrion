"""
RECSlip.App v2 aylık masraf süreci (ADIM 14) uçları.

- /company/{tenant_id}/recslip: paket durumu (Odoo bağlantıları, Case'ler, kişisel anahtarlar, aktarımlar); /setup ile bu ayın
  Case'i açılır; /run ile takip hemen çalıştırılır (entegrasyon yöneticisi).
- /projects/{project_id}/recslip: Case'in ayarları/kriterleri (Case yöneticisi değiştirir), AI kararları, aktarım.
- /me/recslip-decisions ve /recslip-decisions/{id}/decide: kişinin Onaylarım'ındaki fişler; karar kişinin kendi anahtarıyla.
"""
import uuid
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import write_audit_event
from app.core.security import CurrentUser, ensure_tenant_content, forbidden, get_current_user
from app.db.models import Actor, IntegrationConnection, PersonalCredential, Project, RecslipDecision, RecslipExport
from app.db.session import get_db
from app.services import personal_credentials as pcs
from app.services import projects as psvc
from app.services import recslip as rs
from app.services import recslip_case as rc

router = APIRouter(tags=["RECSlip"])


def _manage(user: CurrentUser, tenant_id: uuid.UUID) -> None:
    ensure_tenant_content(user, tenant_id)
    if not user.has("integration:manage"):
        raise forbidden("RECSlip sürecini entegrasyon yöneticisi kurar.")


class SetupIn(BaseModel):
    connection_id: uuid.UUID
    manager_actor_id: uuid.UUID
    report_agent_id: uuid.UUID
    report_approver_id: uuid.UUID
    settings: Optional[Dict[str, Any]] = None


class SettingsIn(BaseModel):
    settings: Dict[str, Any]


class DecideIn(BaseModel):
    approve: bool
    note: Optional[str] = Field(None, max_length=2000)
    apply_corrections: bool = True


def _export_out(e: RecslipExport, odoo_url: Optional[str] = None) -> Dict[str, Any]:
    # #658: dosya RECSlip'te (v2) kalır; Case adını, v2 kaydının bağlantısını ve (varsa) bilgisayardaki yolunu gösterir
    link = f"{odoo_url.rstrip('/')}/odoo/recslip.export/{e.odoo_export_id}" if (odoo_url and e.odoo_export_id) else None
    return {"id": str(e.id), "period": e.period, "name": e.name, "software": e.software, "receipt_count": e.receipt_count,
            "total": float(e.total or 0), "not_exported": e.not_exported, "status": e.status, "attempts": e.attempts,
            "next_attempt_at": e.next_attempt_at, "last_error": e.last_error, "posted_at": e.posted_at,
            "artifact_id": str(e.artifact_id) if e.artifact_id else None, "odoo_export_id": e.odoo_export_id,
            "odoo_link": link, "local_path": e.local_path}


async def _case_out(db: AsyncSession, p: Project) -> Dict[str, Any]:
    s = rs.settings_of(p)
    period = (p.settings or {}).get("period")
    cal = rs.calendar_of(period, s) if period else {}
    exp = (await db.execute(select(RecslipExport).where(RecslipExport.project_id == p.id))).scalars().first()
    conn = await db.get(IntegrationConnection, uuid.UUID(p.settings["connection_id"])) if (p.settings or {}).get("connection_id") else None
    odoo_url = ((conn.config or {}).get("url") if conn else None)
    return {"project_id": str(p.id), "name": p.name, "status": p.status, "period": period, "settings": s,
            "state": (p.settings or {}).get("state") or {}, "calendar": cal, "counts": await rc.decision_counts(db, p),
            "agreement": await rc.agreement(db, p), "export": _export_out(exp, odoo_url) if exp else None,
            "connection_id": (p.settings or {}).get("connection_id"), "manager_actor_id": str(p.manager_actor_id)}


@router.get("/company/{tenant_id}/recslip")
async def recslip_status(tenant_id: uuid.UUID, user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    ensure_tenant_content(user, tenant_id)
    conns = (await db.execute(select(IntegrationConnection).where(IntegrationConnection.tenant_id == tenant_id,
                                                                  IntegrationConnection.connector == "odoo"))).scalars().all()
    cases = (await db.execute(select(Project).where(Project.tenant_id == tenant_id, Project.source_ref.like(f"{rc.SOURCE}:%"))
                              .order_by(Project.created_at.desc()).limit(24))).scalars().all()
    creds = (await db.execute(select(PersonalCredential).where(PersonalCredential.tenant_id == tenant_id))).scalars().all()
    owners = {a.id: a for a in (await db.execute(select(Actor).where(Actor.id.in_([c.actor_id for c in creds] or [uuid.uuid4()])))).scalars()}
    return {"connections": [{"id": str(c.id), "name": c.name, "status": c.status} for c in conns],
            "cases": [await _case_out(db, p) for p in cases], "defaults": rs.DEFAULT_SETTINGS,
            "credentials": [pcs.out(c, owner=owners.get(c.actor_id)) for c in creds]}


@router.post("/company/{tenant_id}/recslip/setup", status_code=201)
async def recslip_setup(tenant_id: uuid.UUID, payload: SetupIn, user: CurrentUser = Depends(get_current_user),
                        db: AsyncSession = Depends(get_db)):
    _manage(user, tenant_id)
    p = await rc.setup(db, tenant_id, payload.connection_id, payload.manager_actor_id, payload.report_agent_id,
                       payload.report_approver_id, payload.settings)
    await write_audit_event(action="RECSLIP_SETUP", actor_id=user.actor_id, tenant_id=tenant_id, target_type="project", target_id=str(p.id),
                            payload={"connection_id": str(payload.connection_id)})
    return await _case_out(db, p)


@router.post("/company/{tenant_id}/recslip/run")
async def recslip_run(tenant_id: uuid.UUID, user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Takibi beklemeden hemen çalıştırır (bu şirketin RECSlip bağlantıları)."""
    _manage(user, tenant_id)
    cases = (await db.execute(select(Project).where(Project.tenant_id == tenant_id, Project.source_ref.like(f"{rc.SOURCE}:%"),
                                                    Project.status == "ACTIVE").order_by(Project.created_at.desc()))).scalars().all()
    if not cases:
        raise HTTPException(status_code=404, detail="Etkin RECSlip Case'i yok; önce süreci kurun.")
    out = {}
    for p in cases[:1]:
        conn = await db.get(IntegrationConnection, uuid.UUID(p.settings["connection_id"]))
        out = await rs.run_connection(db, conn, p)
        await rc.advance(db, conn, p)
    return out


async def _case(db: AsyncSession, user: CurrentUser, project_id: uuid.UUID) -> Project:
    p = await psvc.load(db, user, project_id)
    if not (p.source_ref or "").startswith(f"{rc.SOURCE}:"):
        raise HTTPException(status_code=404, detail="Bu bir RECSlip Case'i değil.")
    return p


@router.get("/projects/{project_id}/recslip")
async def case_detail(project_id: uuid.UUID, user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    p = await _case(db, user, project_id)
    rows = (await db.execute(select(RecslipDecision).where(RecslipDecision.project_id == p.id)
                             .order_by(RecslipDecision.created_at.desc()).limit(500))).scalars().all()
    actors = {a.id: a for a in (await db.execute(select(Actor).where(
        Actor.id.in_({r.approver_actor_id for r in rows if r.approver_actor_id} | {r.agent_actor_id for r in rows if r.agent_actor_id} or {uuid.uuid4()})))).scalars()}
    return {**await _case_out(db, p), "decisions": [rs.decision_out(r, actors.get(r.approver_actor_id), actors.get(r.agent_actor_id)) for r in rows],
            "can_edit": user.has("project:manage") or p.manager_actor_id == user.actor_id}


class ExportPathIn(BaseModel):
    local_path: str = Field("", max_length=500)


@router.put("/projects/{project_id}/recslip/export-path")
async def case_export_path(project_id: uuid.UUID, payload: ExportPathIn, user: CurrentUser = Depends(get_current_user),
                           db: AsyncSession = Depends(get_db)):
    """Muhasebecinin aktarım dosyasını bilgisayarına indirdiği yol (#658): dosya RECOrion'a alınmaz, yalnız yolu not edilir."""
    p = await _case(db, user, project_id)
    if not (user.has("project:manage") or p.manager_actor_id == user.actor_id):
        raise forbidden("Aktarım dosyası yolunu Case yöneticisi yazar.")
    exp = (await db.execute(select(RecslipExport).where(RecslipExport.project_id == p.id))).scalars().first()
    if not exp or not exp.name:
        raise HTTPException(status_code=409, detail="Bu dönemin aktarım dosyası henüz oluşmadı.")
    exp.local_path = payload.local_path.strip() or None
    await db.commit()
    return await _case_out(db, p)


@router.put("/projects/{project_id}/recslip")
async def case_settings(project_id: uuid.UUID, payload: SettingsIn, user: CurrentUser = Depends(get_current_user),
                        db: AsyncSession = Depends(get_db)):
    p = await _case(db, user, project_id)
    if not (user.has("project:manage") or p.manager_actor_id == user.actor_id):
        raise forbidden("RECSlip ayarlarını Case yöneticisi değiştirir.")
    keep = {k: v for k, v in (p.settings or {}).items() if k not in rs.DEFAULT_SETTINGS}
    p.settings = {**keep, **rs.validate_settings(payload.settings)}
    await db.commit()
    await write_audit_event(action="RECSLIP_SETTINGS", actor_id=user.actor_id, tenant_id=p.tenant_id, target_type="project", target_id=str(p.id),
                            payload={"criteria": p.settings.get("criteria")})
    return await _case_out(db, p)


@router.get("/me/recslip-decisions")
async def my_decisions(user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    rows = (await db.execute(select(RecslipDecision).where(RecslipDecision.approver_actor_id == user.actor_id,
                                                           RecslipDecision.status == "PENDING")
                             .order_by(RecslipDecision.created_at))).scalars().all()
    agents = {a.id: a for a in (await db.execute(select(Actor).where(Actor.id.in_({r.agent_actor_id for r in rows if r.agent_actor_id} or {uuid.uuid4()})))).scalars()}
    return [rs.decision_out(r, agent=agents.get(r.agent_actor_id)) for r in rows]


@router.post("/recslip-decisions/{decision_id}/decide")
async def decide(decision_id: uuid.UUID, payload: DecideIn, user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    dec = await db.get(RecslipDecision, decision_id)
    if not dec or dec.tenant_id != user.tenant_id:
        raise HTTPException(status_code=404, detail="Karar bulunamadı.")
    actor = await db.get(Actor, user.actor_id)
    dec = await rs.decide(db, dec, actor, payload.approve, payload.note, payload.apply_corrections)
    await write_audit_event(action="RECSLIP_DECISION", actor_id=user.actor_id, tenant_id=user.tenant_id, target_type="recslip_decision",
                            target_id=str(dec.id), payload={"approve": payload.approve, "expense_id": dec.expense_id})
    return rs.decision_out(dec)
