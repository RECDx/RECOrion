"""
Çıktıdan kayda aktarım uçları (ADIM 12.4). Aktarımlar şirketin içeriğidir (KVKK: RECDx platform personeli göremez).

Proje (yönetici: proje yöneticisi veya project:manage; görüntüleme: proje ekibi):
- GET  /projects/{pid}/transfer-options            kullanılabilir onaylı eşlemeler (ad, nesne, hedef, bağlantı)
- GET  /projects/{pid}/transfers                   projenin aktarımları
- POST /tasks/{task_id}/transfers                  adım çıktısından aktarım önerisi (RECAi çıkarır; onaya düşer)
- POST /projects/{pid}/transfers                   proje çıktısından (tüm adımlar) aktarım önerisi
- PUT  /tasks/{task_id}/transfer-rules             adım bitince önerilecek eşlemeler
- PUT  /projects/{pid}/transfer-on-close           proje kapanınca önerilecek eşlemeler
Aktarım:
- GET  /transfers/{id} · PUT /transfers/{id} (nesneyi düzelt → önizleme yenilenir, onaylar sıfırlanır)
- POST /transfers/{id}/decision (onayla/reddet) · /rollback (geri al) · /retry (başarısızı yeniden kuyruğa al)
Şirket (integration:manage): GET /company/{tid}/transfers (günlük) · GET/PUT /company/{tid}/transfer-policy
Kişi: GET /me/transfer-approvals (Onaylarım)
"""
import uuid
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import CurrentUser, ensure_tenant_content, forbidden, get_current_user
from app.db.models import IntegrationConnection, IntegrationMapping, IntegrationTransfer, Project, Task, Tenant
from app.db.session import get_db
from app.services import business_objects as bo
from app.services import projects as psvc
from app.services import transfers as tsvc

router = APIRouter(tags=["Aktarımlar"])


async def _transfer(db: AsyncSession, user: CurrentUser, tid: uuid.UUID, manage: bool = False) -> IntegrationTransfer:
    tr = await db.get(IntegrationTransfer, tid)
    if not tr:
        raise HTTPException(status_code=404, detail="Aktarım bulunamadı.")
    ensure_tenant_content(user, tr.tenant_id)
    if user.has("integration:manage"):
        return tr
    if not tr.project_id:
        raise forbidden("Bu aktarımı yalnızca entegrasyon yöneticisi görebilir.")
    await psvc.load(db, user, tr.project_id, manage=manage)
    return tr


async def _active_mappings(db: AsyncSession, tenant_id: uuid.UUID, ids: Optional[List[str]] = None) -> List[IntegrationMapping]:
    stmt = (select(IntegrationMapping).join(IntegrationConnection, IntegrationConnection.id == IntegrationMapping.connection_id)
            .where(IntegrationMapping.tenant_id == tenant_id, IntegrationMapping.status == "ACTIVE", IntegrationConnection.status == "ACTIVE"))
    rows = list((await db.execute(stmt.order_by(IntegrationMapping.name))).scalars())
    if ids is not None:
        want = {str(i) for i in ids}
        found = [m for m in rows if str(m.id) in want]
        if len(found) != len(want):
            raise HTTPException(status_code=422, detail="Seçilen eşlemelerden biri onaylı değil veya bağlantısı etkin değil.")
        return found
    return rows


def _option(m: IntegrationMapping, conn_names: Dict[uuid.UUID, str]) -> Dict[str, Any]:
    return {"id": str(m.id), "name": m.name, "object_type": m.object_type, "object_label": bo.OBJECTS[m.object_type]["label"],
            "target": m.target.get("model") or m.target.get("tool"), "connection_name": conn_names.get(m.connection_id), "connector": m.connector}


@router.get("/projects/{project_id}/transfer-options")
async def transfer_options(project_id: uuid.UUID, user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    project = await psvc.load(db, user, project_id)
    rows = await _active_mappings(db, project.tenant_id)
    names = {c.id: c.name for c in (await db.execute(select(IntegrationConnection).where(IntegrationConnection.tenant_id == project.tenant_id))).scalars()}
    return [_option(m, names) for m in rows]


@router.get("/projects/{project_id}/transfers")
async def project_transfers(project_id: uuid.UUID, user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    await psvc.load(db, user, project_id)
    rows = (await db.execute(select(IntegrationTransfer).where(IntegrationTransfer.project_id == project_id)
                             .order_by(IntegrationTransfer.created_at.desc()))).scalars()
    return [tsvc.out(t) for t in rows]


class ProposeIn(BaseModel):
    mapping_id: uuid.UUID


async def _start(db: AsyncSession, user: CurrentUser, project: Project, task: Optional[Task], mapping_id: uuid.UUID) -> Dict[str, Any]:
    m = (await _active_mappings(db, project.tenant_id, [str(mapping_id)]))[0]
    if project.status not in ("ACTIVE", "PAUSED", "COMPLETED"):
        raise HTTPException(status_code=409, detail="Aktarım yalnızca başlamış veya tamamlanmış projelerde yapılabilir.")
    tr = IntegrationTransfer(tenant_id=project.tenant_id, project_id=project.id, task_id=task.id if task else None, mapping_id=m.id,
                             object_type=m.object_type, trigger="MANUAL", status="EXTRACTING", connection_id=m.connection_id,
                             created_by_actor_id=user.actor_id, created_by_name=user.actor.display_name)
    conn = await db.get(IntegrationConnection, m.connection_id)
    tr.connection_name = conn.name if conn else None
    db.add(tr)
    await db.commit()
    tsvc.spawn(tsvc.fill_background(tr.id, "TASK" if task else "PROJECT"))
    return tsvc.out(tr)


@router.post("/tasks/{task_id}/transfers", status_code=202)
async def propose_from_task(task_id: uuid.UUID, payload: ProposeIn, user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    task = await db.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="İş adımı bulunamadı.")
    project = await psvc.load(db, user, task.project_id, manage=True)
    if task.status not in ("DONE", "WAITING_APPROVAL", "IN_REVIEW"):
        raise HTTPException(status_code=409, detail="Bu adımın aktarılacak çıktısı henüz yok.")
    return await _start(db, user, project, task, payload.mapping_id)


@router.post("/projects/{project_id}/transfers", status_code=202)
async def propose_from_project(project_id: uuid.UUID, payload: ProposeIn, user: CurrentUser = Depends(get_current_user),
                               db: AsyncSession = Depends(get_db)):
    project = await psvc.load(db, user, project_id, manage=True)
    return await _start(db, user, project, None, payload.mapping_id)


class RulesIn(BaseModel):
    mapping_ids: List[uuid.UUID] = Field(default_factory=list, max_length=10)


@router.put("/tasks/{task_id}/transfer-rules")
async def task_rules(task_id: uuid.UUID, payload: RulesIn, user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    task = await db.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="İş adımı bulunamadı.")
    project = await psvc.load(db, user, task.project_id, manage=True)
    await _active_mappings(db, project.tenant_id, [str(i) for i in payload.mapping_ids])
    task.transfer_mapping_ids = [str(i) for i in payload.mapping_ids]
    await db.commit()
    return {"task_id": str(task.id), "mapping_ids": task.transfer_mapping_ids}


@router.put("/projects/{project_id}/transfer-on-close")
async def close_rules(project_id: uuid.UUID, payload: RulesIn, user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    project = await psvc.load(db, user, project_id, manage=True)
    await _active_mappings(db, project.tenant_id, [str(i) for i in payload.mapping_ids])
    project.transfer_on_close = [str(i) for i in payload.mapping_ids]
    await db.commit()
    return {"project_id": str(project.id), "mapping_ids": project.transfer_on_close}


@router.get("/transfers/{transfer_id}")
async def get_transfer(transfer_id: uuid.UUID, user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    tr = await _transfer(db, user, transfer_id)
    return {**tsvc.out(tr), "can_decide": await tsvc.can_decide(db, user, tr)}


class FixIn(BaseModel):
    object: Dict[str, Any]


@router.put("/transfers/{transfer_id}")
async def fix_transfer(transfer_id: uuid.UUID, payload: FixIn, user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Önerinin nesnesini düzeltir; önizleme yeniden üretilir ve önceki onaylar düşer (değişen kayıt yeniden onaylanır)."""
    tr = await _transfer(db, user, transfer_id, manage=True)
    if tr.status not in ("NEEDS_FIX", "PENDING_APPROVAL"):
        raise HTTPException(status_code=409, detail="Bu aktarım artık düzenlenemez.")
    if tr.object_type == "PARTNER" and str((payload.object or {}).get("tax_number") or "").count("*"):
        payload.object["tax_number"] = (tr.object or {}).get("tax_number")  # maskeli TCKN geri geldiyse asıl değer korunur
    try:
        await tsvc.prepare(db, tr, payload.object)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    await db.commit()
    await tsvc.notify_pending(db, tr)
    return tsvc.out(tr)


class DecisionIn(BaseModel):
    approve: bool
    note: Optional[str] = Field(None, max_length=2000)


@router.post("/transfers/{transfer_id}/decision")
async def decide(transfer_id: uuid.UUID, payload: DecisionIn, user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    tr = await db.get(IntegrationTransfer, transfer_id)
    if not tr:
        raise HTTPException(status_code=404, detail="Aktarım bulunamadı.")
    ensure_tenant_content(user, tr.tenant_id)
    await tsvc.decide(db, tr, user, payload.approve, payload.note)
    await db.commit()
    if tr.status == "APPROVED":
        await tsvc.enqueue(str(tr.id))
    elif tr.status == "PENDING_APPROVAL":
        await tsvc.notify_pending(db, tr)  # ikinci onaylayıcıya
    return tsvc.out(tr)


@router.post("/transfers/{transfer_id}/rollback")
async def rollback(transfer_id: uuid.UUID, user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    tr = await _transfer(db, user, transfer_id, manage=True)
    await tsvc.rollback(db, tr, user)
    await db.commit()
    return tsvc.out(tr)


@router.post("/transfers/{transfer_id}/retry")
async def retry(transfer_id: uuid.UUID, user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    tr = await _transfer(db, user, transfer_id)
    if not user.has("integration:manage"):
        raise forbidden("Başarısız aktarımı yalnızca entegrasyon yöneticisi yeniden deneyebilir.")
    if tr.status != "FAILED" or not tr.approvals or len([a for a in tr.approvals if a.get("approve")]) < tr.required_approvals:
        raise HTTPException(status_code=409, detail="Yalnızca onaylanmış ama yazılamamış aktarım yeniden denenebilir.")
    tr.status, tr.error = "APPROVED", None
    await db.commit()
    await tsvc.enqueue(str(tr.id))
    return tsvc.out(tr)


@router.get("/company/{tenant_id}/transfers")
async def company_transfers(tenant_id: uuid.UUID, status: Optional[str] = None, limit: int = Query(100, le=500),
                            user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    ensure_tenant_content(user, tenant_id)
    if not user.has("integration:manage"):
        raise forbidden("Aktarım günlüğünü yalnızca entegrasyon yöneticisi görebilir.")
    stmt = select(IntegrationTransfer).where(IntegrationTransfer.tenant_id == tenant_id)
    if status:
        stmt = stmt.where(IntegrationTransfer.status == status.upper())
    return [tsvc.out(t) for t in (await db.execute(stmt.order_by(IntegrationTransfer.created_at.desc()).limit(limit))).scalars()]


@router.get("/me/transfer-approvals")
async def my_transfer_approvals(user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if user.is_platform_staff:
        return []
    rows = (await db.execute(select(IntegrationTransfer).where(IntegrationTransfer.tenant_id == user.tenant_id,
                                                               IntegrationTransfer.status == "PENDING_APPROVAL")
                             .order_by(IntegrationTransfer.created_at))).scalars().all()
    return [tsvc.out(t) for t in rows if await tsvc.can_decide(db, user, t)]


class PolicyIn(BaseModel):
    double_approval_objects: List[str] = Field(default_factory=list)
    amount_threshold: Optional[float] = Field(None, ge=0)


@router.get("/company/{tenant_id}/transfer-policy")
async def get_policy(tenant_id: uuid.UUID, user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    ensure_tenant_content(user, tenant_id)
    if not user.has("integration:manage"):
        raise forbidden("Aktarım kurallarını yalnızca entegrasyon yöneticisi görebilir.")
    return tsvc.policy(await db.get(Tenant, tenant_id))


@router.put("/company/{tenant_id}/transfer-policy")
async def set_policy(tenant_id: uuid.UUID, payload: PolicyIn, user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    ensure_tenant_content(user, tenant_id)
    if not user.has("integration:manage"):
        raise forbidden("Aktarım kurallarını yalnızca entegrasyon yöneticisi değiştirebilir.")
    bad = [o for o in payload.double_approval_objects if o not in bo.OBJECTS]
    if bad:
        raise HTTPException(status_code=422, detail=f"Bilinmeyen nesne türü: {', '.join(bad)}")
    tenant = await db.get(Tenant, tenant_id)
    tenant.settings = {**(tenant.settings or {}), "transfer": {"double_approval_objects": payload.double_approval_objects,
                                                              "amount_threshold": payload.amount_threshold}}
    await db.commit()
    return tsvc.policy(tenant)
