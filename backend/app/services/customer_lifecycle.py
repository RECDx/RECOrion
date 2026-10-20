"""
Müşteri yaşam döngüsü: başvuru → Odoo siparişi → RECDx onayı/reddi → aktivasyon e-postası.

Başvuru (tenant_leads) ile şirket (tenants) arasındaki bağ lead.tenant_id ile kurulur;
isim veya slug benzerliğiyle eşleştirme yapılmaz.
Odoo çağrıları senkron XML-RPC olduğundan arka planda (thread) çalıştırılır ve API'yi bekletmez.
"""
import asyncio
import logging
import re
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.tokens import issue_link_token
from app.db.models import Actor, NotificationSchedule, Plan, Tenant, TenantLead
from app.db.session import AsyncSessionLocal
from app.services.notification_service import NotificationService
from app.services.odoo_service import OdooService

logger = logging.getLogger("recorion.lifecycle")

PACKAGE_DAYS = 365
SET_PASSWORD_PURPOSE = "set_password"
ACTIVATION_LINK_HOURS = 72
RESET_LINK_HOURS = 1


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def app_url(path: str = "") -> str:
    return settings.PUBLIC_APP_URL.rstrip("/") + "/" + path.lstrip("/")


async def unique_slug(db: AsyncSession, name: str) -> str:
    base = re.sub(r"[^a-z0-9]", "", (name or "").lower().translate(str.maketrans("çğıöşüâî", "cgiosuai")))[:16] or "sirket"
    while True:
        candidate = f"{base}_{uuid.uuid4().hex[:6]}"
        if not (await db.execute(select(Tenant.id).where(Tenant.slug == candidate))).first():
            return candidate


async def company_admin(db: AsyncSession, tenant_id: uuid.UUID) -> Optional[Actor]:
    return (await db.execute(
        select(Actor).where(Actor.tenant_id == tenant_id, Actor.role == "COMPANY_ADMIN").order_by(Actor.created_at)
    )).scalars().first()


async def set_password_link(actor: Actor, hours: int = ACTIVATION_LINK_HOURS) -> str:
    token = await issue_link_token(SET_PASSWORD_PURPOSE, str(actor.id), hours * 3600)
    return app_url(f"#/reset-password?token={token}")


# ---------------------------------------------------------------- Odoo
async def sync_lead_to_odoo(lead_id: uuid.UUID) -> None:
    """Başvuru için Odoo müşteri kaydı ve satış teklifi açar (arka plan görevi)."""
    async with AsyncSessionLocal() as db:
        lead = await db.get(TenantLead, lead_id)
        if not lead:
            return
        if not settings.ODOO_SYNC_ENABLED:
            lead.odoo_sync_status = "SKIPPED"
            await db.commit()
            return
        plan = await db.get(Plan, lead.plan_id) if lead.plan_id else None
        if not plan or not plan.odoo_product_id:
            lead.odoo_sync_status = "FAILED"
            lead.odoo_sync_error = "Paketin Odoo ürün eşleşmesi (odoo_product_id) tanımlı değil."
            await db.commit()
            return
        try:
            partner_id = lead.odoo_partner_id
            if not partner_id:
                partner = await asyncio.to_thread(
                    OdooService.get_or_create_partner,
                    lead.company_name, lead.contact_email, lead.phone or "", lead.address, lead.website, lead.tax_id,
                )
                if not partner:
                    raise RuntimeError("Odoo müşteri kaydı oluşturulamadı.")
                partner_id = partner["id"]
                lead.odoo_partner_id = partner_id
                lead.odoo_partner_name = partner["name"]
            if not lead.odoo_order_id:
                res = await asyncio.to_thread(
                    OdooService.create_sale_order, partner_id, plan.odoo_product_id, float(plan.monthly_price or 0),
                    f"RECOrion - {plan.name} (aylık kiralama)",
                )
                if not res.get("success"):
                    raise RuntimeError(res.get("error") or "Satış teklifi oluşturulamadı.")
                lead.odoo_order_id = res["order_id"]
                lead.odoo_order_name = res["order_name"]
            lead.odoo_sync_status = "SYNCED"
            lead.odoo_sync_error = None
        except Exception as exc:
            logger.error("Odoo senkronizasyonu başarısız (lead=%s): %s", lead_id, exc)
            lead.odoo_sync_status = "FAILED"
            lead.odoo_sync_error = str(exc)[:500]
        await db.commit()


async def _odoo_order_action(order_id: Optional[int], action: str) -> None:
    if not order_id or not settings.ODOO_SYNC_ENABLED:
        return
    fn = OdooService.confirm_sale_order if action == "confirm" else OdooService.cancel_sale_order
    try:
        await asyncio.to_thread(fn, order_id)
    except Exception as exc:
        logger.warning("Odoo sipariş işlemi (%s, %s) başarısız: %s", action, order_id, exc)


# ---------------------------------------------------------------- e-postalar
async def activation_email_enabled(db: AsyncSession) -> bool:
    """'Müşteri Kayıt Olduğunda' zamanlaması pasife alınmışsa aktivasyon e-postası gönderilmez."""
    sched = (await db.execute(
        select(NotificationSchedule).where(NotificationSchedule.trigger_type == "ON_REGISTRATION")
    )).scalars().first()
    return sched is None or bool(sched.is_active)


async def send_activation_email(db: AsyncSession, tenant: Tenant, admin: Optional[Actor], has_known_password: bool) -> bool:
    if not admin or not (admin.email or tenant.contact_email):
        return False
    plan = await db.get(Plan, tenant.plan_id) if tenant.plan_id else None
    link = await set_password_link(admin)
    if has_known_password:
        instruction = ("Kayıt sırasında belirlediğiniz şifre ile giriş yapabilirsiniz. Şifrenizi hatırlamıyorsanız "
                       f"aşağıdaki düğmeden {ACTIVATION_LINK_HOURS} saat içinde yeni şifre belirleyebilirsiniz.")
    else:
        instruction = f"Güvenliğiniz için şifreniz e-postayla gönderilmez. Aşağıdaki düğmeden {ACTIVATION_LINK_HOURS} saat içinde şifrenizi belirleyin."
    return await NotificationService.send_by_code(db, "ACCOUNT_ACTIVATED", admin.email or tenant.contact_email, {
        "company_name": tenant.name,
        "contact_name": admin.display_name,
        "plan_name": plan.name if plan else "RECOrion Paketi",
        "package_expiry_date": tenant.package_expiry_date.strftime("%d.%m.%Y") if tenant.package_expiry_date else "-",
        "login_email": admin.email,
        "password_instruction": instruction,
        "action_label": "Şifremi Belirle / Giriş Yap",
        "action_url": link,
        "login_url": app_url(),
    })


# ---------------------------------------------------------------- onay / ret
async def activate_tenant(db: AsyncSession, tenant: Tenant, reviewer_id: Optional[uuid.UUID], lead: Optional[TenantLead] = None) -> dict:
    """Şirketi ve paketini aktifleştirir, başvuruyu onaylar, Odoo siparişini onaylar, e-posta gönderir."""
    now = now_utc()
    tenant.is_active = True
    tenant.package_start_date = tenant.package_start_date or now
    expiry = tenant.package_expiry_date
    if not expiry or expiry < now:
        tenant.package_expiry_date = now + timedelta(days=PACKAGE_DAYS)

    if lead is None:
        lead = (await db.execute(
            select(TenantLead).where(TenantLead.tenant_id == tenant.id).order_by(TenantLead.created_at.desc())
        )).scalars().first()

    admin = await company_admin(db, tenant.id)
    has_known_password = False
    if admin:
        if admin.status == "DISABLED":
            admin.status = "IDLE"
        if not admin.password_hash and lead and lead.password_hash:
            admin.password_hash = lead.password_hash
        has_known_password = bool(lead and lead.password_hash and admin.password_hash == lead.password_hash)

    if lead:
        lead.status = "APPROVED"
        lead.reviewed_by_actor_id = reviewer_id
        lead.reviewed_at = now
        lead.rejection_reason = None
        lead.password_hash = None  # artık yöneticinin hesabında; başvuruda tutulmaz

    await db.commit()
    await db.refresh(tenant)

    await _odoo_order_action(lead.odoo_order_id if lead else None, "confirm")
    email_sent = False
    if await activation_email_enabled(db):
        email_sent = await send_activation_email(db, tenant, admin, has_known_password)
    return {"email_sent": email_sent, "package_expiry_date": tenant.package_expiry_date}


async def reject_lead(db: AsyncSession, lead: TenantLead, reviewer_id: Optional[uuid.UUID], reason: str) -> bool:
    lead.status = "REJECTED"
    lead.rejection_reason = reason
    lead.reviewed_by_actor_id = reviewer_id
    lead.reviewed_at = now_utc()
    lead.password_hash = None
    if lead.tenant_id:
        tenant = await db.get(Tenant, lead.tenant_id)
        if tenant:
            tenant.is_active = False
    await db.commit()
    await _odoo_order_action(lead.odoo_order_id, "cancel")
    return await NotificationService.send_by_code(db, "LEAD_REJECTED", lead.contact_email, {
        "contact_name": lead.contact_name or "Yetkili",
        "company_name": lead.company_name,
        "reason": reason,
    })


async def process_new_lead(lead_id: uuid.UUID) -> None:
    """Yeni başvuru sonrası arka plan işi: Odoo teklifi, ardından müşteri ve RECDx bildirimleri."""
    await sync_lead_to_odoo(lead_id)
    async with AsyncSessionLocal() as db:
        lead = await db.get(TenantLead, lead_id)
        if not lead:
            return
        plan = await db.get(Plan, lead.plan_id) if lead.plan_id else None
        ctx = {
            "company_name": lead.company_name,
            "contact_name": lead.contact_name or "Yetkili",
            "contact_email": lead.contact_email,
            "phone": lead.phone or "-",
            "plan_name": plan.name if plan else "-",
            "order_ref": lead.odoo_order_name or "işleniyor",
            "review_url": app_url("#/super-admin/leads"),
        }
        await NotificationService.send_by_code(db, "LEAD_RECEIVED", lead.contact_email, ctx)
        await NotificationService.send_by_code(db, "ADMIN_NEW_LEAD", settings.ADMIN_NOTIFICATION_EMAIL, ctx)
