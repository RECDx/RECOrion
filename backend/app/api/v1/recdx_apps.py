"""
RECDx uygulamaları uçları (ADIM 13.1).

- GET /recdx-apps?plan_code=PRO            uygulama tanıtımı ve paketin teklifi (herkese açık: web satın alma formu)
- GET /company/{tid}/recdx-apps            şirketin seçimi, paketinin teklifi, durum ve son talep
- PUT /company/{tid}/recdx-apps            seçimi değiştir (tenant:manage / integration:manage): yeni 'paketime ekle' Odoo teklifi,
                                           yeni 'teklif istiyorum' Odoo CRM fırsatı açar (arka planda); RECDx'e e-posta
- GET /system/recdx-app-requests           Genel Merkez: tüm talepler (şirket adı, seçim, fiyat, Odoo sipariş/fırsat, durum)
- PUT /system/recdx-app-requests/{id}      Genel Merkez: durum/not (kuruldu, iptal...)
- POST /system/recdx-app-requests/{id}/retry  Odoo işlemini yeniden dene
"""
import logging
import uuid
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import write_audit_event
from app.core.security import CurrentUser, ensure_tenant_management, forbidden, get_current_user
from app.db.models import IntegrationConnection, Plan, RecdxAppRequest, Tenant
from app.db.session import get_db
from app.services import recdx_apps

router = APIRouter(tags=["RECDx Uygulamaları"])
logger = logging.getLogger("recorion.recdx_apps")


@router.get("/recdx-apps")
async def public_apps(plan_code: Optional[str] = None, db: AsyncSession = Depends(get_db)):
    plan = (await db.execute(select(Plan).where(Plan.code == plan_code.upper()))).scalar_one_or_none() if plan_code else None
    return recdx_apps.describe(None, plan=plan)


async def _describe(db: AsyncSession, tenant: Tenant) -> Dict[str, Any]:
    conns = (await db.execute(select(IntegrationConnection).where(IntegrationConnection.tenant_id == tenant.id))).scalars().all()
    reqs = (await db.execute(select(RecdxAppRequest).where(RecdxAppRequest.tenant_id == tenant.id))).scalars().all()
    plan = await db.get(Plan, tenant.plan_id) if tenant.plan_id else None
    return {**recdx_apps.describe(tenant, conns, plan, reqs), "plan_name": plan.name if plan else None}


@router.get("/company/{tenant_id}/recdx-apps")
async def company_apps(tenant_id: uuid.UUID, user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    ensure_tenant_management(user, tenant_id)
    return await _describe(db, await db.get(Tenant, tenant_id))


class PrefIn(BaseModel):
    has_odoo: Optional[bool] = None
    apps: Dict[str, str] = {}


@router.put("/company/{tenant_id}/recdx-apps")
async def set_company_apps(tenant_id: uuid.UUID, payload: PrefIn, user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    ensure_tenant_management(user, tenant_id)
    if not (user.has("tenant:manage") or user.has("integration:manage")):
        raise forbidden("Bu tercihi yalnızca şirket yöneticisi değiştirebilir.")
    tenant = await db.get(Tenant, tenant_id)
    plan = await db.get(Plan, tenant.plan_id) if tenant.plan_id else None
    data = recdx_apps.store(tenant, payload.model_dump(), user.actor_id, plan)
    made = await recdx_apps.create_requests(db, tenant, plan, data["apps"], "COMPANY", actor_id=user.actor_id)
    await db.commit()
    await write_audit_event(action="RECDX_APPS_UPDATED", actor_id=user.actor_id, tenant_id=tenant_id, target_type="tenant",
                            target_id=str(tenant_id), payload={"has_odoo": data["has_odoo"], "apps": data["apps"],
                                                               "requests": [f"{r.app}:{r.choice}" for r in made]})
    sales = [r for r in made if r.choice in ("ADD", "QUOTE")]
    if sales:
        await _notify_sales(tenant, sales)
        recdx_apps.spawn(recdx_apps.process_company_requests([r.id for r in sales]))
    return await _describe(db, tenant)


async def _notify_sales(tenant: Tenant, reqs: list) -> None:
    """Yeni talep: RECDx satış ekibine e-posta (yönetici bildirim adresi). Gönderilemezse kayıt Genel Merkez ekranında."""
    import asyncio
    import html

    from app.config import settings
    from app.services.notification_service import NotificationService

    items = ", ".join(f"{recdx_apps.APPS[r.app]['title']} ({recdx_apps.CHOICE_LABELS[r.choice].lower()})" for r in reqs)
    subject = f"RECOrion: {tenant.name} RECDx uygulama talebi: {items}"
    text = f"{tenant.name} Şirket Yönetimi'nden talep iletti: {items}. Ayrıntı: Genel Merkez > Uygulama Talepleri."
    try:
        await asyncio.to_thread(NotificationService._send_email, settings.ADMIN_NOTIFICATION_EMAIL, subject, f"<p>{html.escape(text)}</p>", text)
    except Exception as exc:  # e-posta altyapısı yoksa iş durmaz
        logger.warning("RECDx uygulama talebi bildirilemedi: %s", exc)


# --- Genel Merkez ---

def _super(user: CurrentUser) -> None:
    if not user.is_super_admin:
        raise HTTPException(status_code=403, detail="Bu işlem yalnızca RECDx Süper Admin içindir.")


@router.get("/system/recdx-app-requests")
async def list_requests(status: Optional[str] = None, user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    _super(user)
    stmt = select(RecdxAppRequest, Tenant.name).join(Tenant, Tenant.id == RecdxAppRequest.tenant_id)
    if status:
        stmt = stmt.where(RecdxAppRequest.status == status.upper())
    rows = (await db.execute(stmt.order_by(RecdxAppRequest.created_at.desc()).limit(500))).all()
    return [recdx_apps.request_out(r, name) for r, name in rows]


class RequestUpdate(BaseModel):
    status: Optional[str] = Field(None, pattern="^(NEW|ORDERED|OPPORTUNITY|IN_USE|DONE|CANCELLED)$")
    note: Optional[str] = Field(None, max_length=2000)


@router.put("/system/recdx-app-requests/{request_id}")
async def update_request(request_id: uuid.UUID, payload: RequestUpdate, user: CurrentUser = Depends(get_current_user),
                         db: AsyncSession = Depends(get_db)):
    _super(user)
    r = await db.get(RecdxAppRequest, request_id)
    if not r:
        raise HTTPException(status_code=404, detail="Talep bulunamadı.")
    if payload.status:
        r.status = payload.status
    if payload.note is not None:
        r.note = payload.note.strip() or None
    await db.commit()
    return recdx_apps.request_out(r, (await db.get(Tenant, r.tenant_id)).name)


@router.post("/system/recdx-app-requests/{request_id}/retry")
async def retry_request(request_id: uuid.UUID, user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    _super(user)
    r = await db.get(RecdxAppRequest, request_id)
    if not r or r.choice not in ("ADD", "QUOTE"):
        raise HTTPException(status_code=404, detail="Yeniden denenebilecek talep bulunamadı.")
    if r.status not in ("FAILED", "SKIPPED"):
        raise HTTPException(status_code=409, detail="Yalnızca başarısız veya atlanmış talep yeniden denenir.")
    plan = await db.get(Plan, r.plan_id) if r.plan_id else None
    if r.choice == "ADD" and not r.odoo_product_id:  # Süper Admin ürünü sonradan seçtiyse teklif yenilenir
        o = recdx_apps.offer(plan, r.app)
        r.odoo_product_id, r.list_price, r.price = o.get("odoo_product_id"), o.get("list_price"), o["price"]
    r.status, r.error = "NEW", None
    await db.commit()
    await recdx_apps.process_company_requests([r.id])
    await db.refresh(r)
    return recdx_apps.request_out(r, (await db.get(Tenant, r.tenant_id)).name)
