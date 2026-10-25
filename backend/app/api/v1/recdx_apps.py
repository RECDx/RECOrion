"""
RECDx uygulamaları tercihi uçları (ADIM 13.1).

- GET /recdx-apps                         uygulama tanıtımı (herkese açık: web satın alma formu)
- GET /company/{tid}/recdx-apps           şirketin tercihi ve her uygulamanın durumu
- PUT /company/{tid}/recdx-apps           tercihi değiştir (tenant:manage veya integration:manage); yeni ilgi RECDx'e bildirilir
"""
import logging
import uuid
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import write_audit_event
from app.core.security import CurrentUser, ensure_tenant_management, forbidden, get_current_user
from app.db.models import IntegrationConnection, Tenant
from app.db.session import get_db
from app.services import recdx_apps

router = APIRouter(tags=["RECDx Uygulamaları"])
logger = logging.getLogger("recorion.recdx_apps")


@router.get("/recdx-apps")
async def public_apps():
    return recdx_apps.describe(None)


async def _describe(db: AsyncSession, tenant: Tenant) -> Dict[str, Any]:
    conns = (await db.execute(select(IntegrationConnection).where(IntegrationConnection.tenant_id == tenant.id))).scalars().all()
    return recdx_apps.describe(tenant, conns)


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
    before = set(recdx_apps.interests(recdx_apps.get(tenant)))
    data = recdx_apps.store(tenant, payload.model_dump(), user.actor_id)
    await db.commit()
    new_interest = sorted(set(recdx_apps.interests(data)) - before)
    await write_audit_event(action="RECDX_APPS_UPDATED", actor_id=user.actor_id, tenant_id=tenant_id, target_type="tenant",
                            target_id=str(tenant_id), payload={"has_odoo": data["has_odoo"], "apps": data["apps"], "new_interest": new_interest})
    if new_interest:
        await _notify_sales(db, tenant, new_interest)
    return await _describe(db, tenant)


async def _notify_sales(db: AsyncSession, tenant: Tenant, apps: list) -> None:
    """Yeni ilgi: RECDx satış ekibine e-posta (yönetici bildirim adresi). Gönderilemezse kayıt yine denetim günlüğünde."""
    import asyncio
    import html

    from app.config import settings
    from app.services.notification_service import NotificationService

    subject = f"RECOrion: {tenant.name} {', '.join(apps)} ile ilgileniyor"
    text = f"{tenant.name} Şirket Yönetimi'nden {', '.join(apps)} uygulamasını kullanmak istediğini belirtti."
    try:
        await asyncio.to_thread(NotificationService._send_email, settings.ADMIN_NOTIFICATION_EMAIL, subject, f"<p>{html.escape(text)}</p>", text)
    except Exception as exc:  # e-posta altyapısı yoksa iş durmaz
        logger.warning("RECDx uygulama ilgisi bildirilemedi: %s", exc)
