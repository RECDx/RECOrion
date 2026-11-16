"""
İSTEK #747 — Ek kredi satın alma.

- Kredi paketleri Merkez'de tanımlanır (kredi miktarı, KDV hariç fiyat, Odoo ürünü, geçerli abonelik paketleri).
- Şirket yöneticisi paket ve ödeme yöntemi seçer; her sipariş için Odoo'da satış siparişi (teklif) açılır.
- Havale/EFT: Merkez "Ödeme alındı, krediyi yükle" der → Odoo siparişi onaylanır, taslak fatura oluşur (muhasebe keser),
  kredi defterine tek bir TOPUP yazılır, müşteriye bildirim gider. Ödeme 7 gün içinde gelmezse sipariş kendiliğinden iptal.
- Kart (sanal POS): altyapı kapalı gelir (system setting billing.card_enabled); sağlayıcı seçilince ödeme bildirimi
  `load()` ile aynı yoldan kredi yükler.
- Bakiye şirket kartında tutulmaz; kredi yüklemek = credit_ledger'a TOPUP kaydı. Bir sipariş yalnız bir kez yükler.
"""
import asyncio
import logging
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Actor, CreditLedgerEntry, CreditOrder, CreditPack, Plan, SystemSetting, Tenant, TenantLead

logger = logging.getLogger("recorion.credit_store")

VALID_DAYS = 7
BANK_SETTING = "billing.bank_info"
CARD_SETTING = "billing.card_enabled"
MAX_PENDING = 3
STATUS_TR = {"PENDING": "Ödeme bekleniyor", "LOADED": "Kredi yüklendi", "CANCELLED": "İptal edildi", "EXPIRED": "Süresi doldu"}


def _now() -> datetime:
    return datetime.now(timezone.utc)


async def _setting(db: AsyncSession, key: str, default=None):
    row = await db.get(SystemSetting, key)
    return row.value if row else default


async def billing_settings(db: AsyncSession) -> Dict[str, Any]:
    bank = await _setting(db, BANK_SETTING, {}) or {}
    card = await _setting(db, CARD_SETTING, {}) or {}
    return {"bank_info": bank.get("text") or "", "card_enabled": bool(card.get("enabled")), "valid_days": VALID_DAYS}


async def set_billing_settings(db: AsyncSession, bank_info: str) -> Dict[str, Any]:
    row = await db.get(SystemSetting, BANK_SETTING)
    if row:
        row.value = {"text": bank_info}
    else:
        db.add(SystemSetting(key=BANK_SETTING, value={"text": bank_info}, description="Ek kredi havale/EFT banka bilgileri (#747)"))
    await db.commit()
    return await billing_settings(db)


def pack_out(p: CreditPack, admin: bool = False) -> Dict[str, Any]:
    out = {"id": str(p.id), "code": p.code, "name": p.name, "credits": p.credits,
           "price_try": float(p.price_try) if p.price_try is not None else None,
           "unit_price_try": float((p.price_try / p.credits).quantize(Decimal("0.0001"))) if p.price_try and p.credits else None}
    if admin:
        out.update(odoo_product_id=p.odoo_product_id, plan_codes=p.plan_codes or [], sort_order=p.sort_order, is_active=p.is_active,
                   sellable=bool(p.is_active and p.price_try and p.odoo_product_id))
    return out


def order_out(o: CreditOrder, tenant_name: Optional[str] = None) -> Dict[str, Any]:
    return {"id": str(o.id), "tenant_id": str(o.tenant_id), "tenant_name": tenant_name, "pack_name": o.pack_name, "credits": o.credits,
            "price_try": float(o.price_try), "payment_method": o.payment_method, "status": o.status,
            "status_label": STATUS_TR.get(o.status, o.status), "odoo_order_name": o.odoo_order_name, "created_at": o.created_at,
            "expires_at": o.expires_at, "decided_at": o.decided_at, "note": o.note,
            "invoice_drafted": bool(o.odoo_invoice_ids), "kind": o.kind or "CREDIT"}


async def packs_for(db: AsyncSession, tenant: Tenant) -> List[CreditPack]:
    """Şirketin satın alabileceği paketler: etkin, fiyatı ve Odoo ürünü tanımlı, şirketin abonelik paketine açık."""
    plan = await db.get(Plan, tenant.plan_id) if tenant.plan_id else None
    rows = (await db.execute(select(CreditPack).where(CreditPack.is_active.is_(True)).order_by(CreditPack.sort_order, CreditPack.credits))).scalars().all()
    return [p for p in rows if p.price_try and p.odoo_product_id and (not p.plan_codes or (plan and plan.code in p.plan_codes))]


async def _partner_id(db: AsyncSession, tenant: Tenant) -> int:
    from app.services.odoo_service import OdooService

    lead = (await db.execute(select(TenantLead).where(TenantLead.tenant_id == tenant.id, TenantLead.odoo_partner_id.isnot(None))
                             .order_by(TenantLead.created_at.desc()).limit(1))).scalar_one_or_none()
    if lead:
        return lead.odoo_partner_id
    partner = await asyncio.to_thread(OdooService.get_or_create_partner, tenant.name, tenant.contact_email or "", tenant.phone or "",
                                      tenant.address, tenant.website, tenant.tax_id)
    if not partner:
        raise HTTPException(status_code=503, detail="Odoo müşteri kaydına ulaşılamadı; sipariş oluşturulamadı. Lütfen biraz sonra tekrar deneyin.")
    return partner["id"]


async def _admins(db: AsyncSession, tenant_id) -> List[Actor]:
    return (await db.execute(select(Actor).where(Actor.tenant_id == tenant_id, Actor.role == "COMPANY_ADMIN", Actor.status != "DISABLED")
                             .order_by(Actor.created_at))).scalars().all()


async def _mail(db: AsyncSession, tenant: Tenant, code: str, ctx: Dict[str, Any]) -> None:
    from app.services.notification_service import NotificationService

    admins = await _admins(db, tenant.id)
    to = (admins[0].email if admins else None) or tenant.contact_email
    if not to:
        return
    try:
        await NotificationService.send_by_code(db, code, to, {"contact_name": admins[0].display_name if admins else "Yetkili",
                                                              "company_name": tenant.name, **ctx})
    except Exception as exc:  # e-posta hatası siparişi bozmaz
        logger.warning("Kredi siparişi e-postası gönderilemedi (%s): %s", code, exc)


async def create_order(db: AsyncSession, tenant: Tenant, pack_id, method: str, actor_id) -> CreditOrder:
    from app.services.llm_gateway import HQ_SLUG
    from app.services.odoo_service import OdooService

    if tenant.slug == HQ_SLUG:
        raise HTTPException(status_code=400, detail="RECDx ana şirketinin kullanımı sınırsızdır; kredi satın alınmaz.")
    pack = next((p for p in await packs_for(db, tenant) if str(p.id) == str(pack_id)), None)
    if not pack:
        raise HTTPException(status_code=404, detail="Bu kredi paketi şirketiniz için satışta değil.")
    if method not in ("TRANSFER", "CARD"):
        raise HTTPException(status_code=422, detail="Ödeme yöntemi havale/EFT ya da kart olmalı.")
    if method == "CARD" and not (await billing_settings(db))["card_enabled"]:
        raise HTTPException(status_code=409, detail="Kartla ödeme henüz etkin değil; havale/EFT ile sipariş verebilirsiniz.")
    pending = (await db.execute(select(CreditOrder).where(CreditOrder.tenant_id == tenant.id, CreditOrder.status == "PENDING"))).scalars().all()
    if len(pending) >= MAX_PENDING:
        raise HTTPException(status_code=409, detail=f"Ödemesi beklenen {len(pending)} siparişiniz var; yenisini vermeden önce ödeyin ya da iptal edin.")
    partner = await _partner_id(db, tenant)
    res = await asyncio.to_thread(OdooService.create_sale_order, partner, pack.odoo_product_id, float(pack.price_try),
                                  f"RECOrion ek kredi — {pack.name} ({pack.credits} kredi)")
    if not res.get("success"):
        raise HTTPException(status_code=503, detail="Odoo'da satış siparişi oluşturulamadı; lütfen biraz sonra tekrar deneyin.")
    order = CreditOrder(tenant_id=tenant.id, pack_id=pack.id, pack_name=pack.name, credits=pack.credits, price_try=pack.price_try,
                        payment_method=method, status="PENDING", odoo_order_id=res["order_id"], odoo_order_name=res["order_name"],
                        created_by_actor_id=actor_id, expires_at=_now() + timedelta(days=VALID_DAYS))
    db.add(order)
    await db.commit()
    await db.refresh(order)
    bs = await billing_settings(db)
    await _mail(db, tenant, "CREDIT_ORDER_CREATED", {
        "credits": f"{pack.credits:,}".replace(",", "."), "order_name": order.odoo_order_name,
        "amount": f"{float(pack.price_try):,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
        "bank_info": bs["bank_info"] or "Banka bilgileri için RECDx ile iletişime geçin.", "valid_days": VALID_DAYS})
    return order


# ---------------------------------------------------------------- paket yükseltme (hemen geçerli, oransal)
def _month_fraction(now: Optional[datetime] = None) -> Dict[str, Any]:
    """Ayın kalan gün oranı (İstanbul takvimi; bugün dahil)."""
    import calendar

    from app.services.credits import TZ

    n = (now or datetime.now(TZ)).astimezone(TZ)
    days = calendar.monthrange(n.year, n.month)[1]
    left = days - n.day + 1
    return {"days_in_month": days, "days_left": left, "fraction": Decimal(left) / Decimal(days)}


async def upgrade_options(db: AsyncSession, tenant: Tenant, now: Optional[datetime] = None) -> List[Dict[str, Any]]:
    """Şirketin geçebileceği üst paketler ve bu ay için oransal fiyat / kredi farkı."""
    cur = await db.get(Plan, tenant.plan_id) if tenant.plan_id else None
    cur_price, cur_credits = Decimal(str(cur.monthly_price or 0)) if cur else Decimal(0), (cur.monthly_credits or 0) if cur else 0
    mf = _month_fraction(now)
    plans = (await db.execute(select(Plan).where(Plan.is_active.is_(True)).order_by(Plan.monthly_price))).scalars().all()
    out = []
    for p in plans:
        price = Decimal(str(p.monthly_price or 0))
        if (cur and p.id == cur.id) or price <= cur_price or not p.odoo_product_id:
            continue
        out.append({"plan_id": str(p.id), "code": p.code, "name": p.name, "monthly_price": float(price), "monthly_credits": p.monthly_credits,
                    "prorated_price_try": float(((price - cur_price) * mf["fraction"]).quantize(Decimal("0.01"))),
                    "prorated_credits": int(((p.monthly_credits or 0) - cur_credits) * mf["fraction"]),
                    "days_left": mf["days_left"], "days_in_month": mf["days_in_month"]})
    return out


async def create_upgrade_order(db: AsyncSession, tenant: Tenant, plan_id, actor_id) -> CreditOrder:
    from app.services.llm_gateway import HQ_SLUG
    from app.services.odoo_service import OdooService

    if tenant.slug == HQ_SLUG:
        raise HTTPException(status_code=400, detail="RECDx ana şirketinin paketi değiştirilmez.")
    opt = next((o for o in await upgrade_options(db, tenant) if o["plan_id"] == str(plan_id)), None)
    if not opt:
        raise HTTPException(status_code=404, detail="Bu paket şirketiniz için yükseltme seçeneği değil.")
    if (await db.execute(select(CreditOrder).where(CreditOrder.tenant_id == tenant.id, CreditOrder.kind == "PLAN_UPGRADE",
                                                   CreditOrder.status == "PENDING"))).scalars().first():
        raise HTTPException(status_code=409, detail="Ödemesi beklenen bir paket yükseltme siparişiniz var.")
    plan = await db.get(Plan, uuid_of(plan_id))
    partner = await _partner_id(db, tenant)
    desc = f"RECOrion paket yükseltme — {plan.name} (bu ayın kalan {opt['days_left']}/{opt['days_in_month']} günü, oransal fark)"
    res = await asyncio.to_thread(OdooService.create_sale_order, partner, plan.odoo_product_id, opt["prorated_price_try"], desc)
    if not res.get("success"):
        raise HTTPException(status_code=503, detail="Odoo'da satış siparişi oluşturulamadı; lütfen biraz sonra tekrar deneyin.")
    order = CreditOrder(tenant_id=tenant.id, kind="PLAN_UPGRADE", target_plan_id=plan.id, from_plan_id=tenant.plan_id,
                        pack_name=f"Paket yükseltme: {plan.name}", credits=max(0, opt["prorated_credits"]),
                        price_try=Decimal(str(opt["prorated_price_try"])), payment_method="TRANSFER", status="PENDING",
                        odoo_order_id=res["order_id"], odoo_order_name=res["order_name"], created_by_actor_id=actor_id,
                        expires_at=_now() + timedelta(days=VALID_DAYS))
    db.add(order)
    await db.commit()
    await db.refresh(order)
    bs = await billing_settings(db)
    await _mail(db, tenant, "CREDIT_ORDER_CREATED", {
        "credits": f"{order.credits:,}".replace(",", "."), "order_name": order.odoo_order_name,
        "amount": f"{float(order.price_try):,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
        "bank_info": bs["bank_info"] or "Banka bilgileri için RECDx ile iletişime geçin.", "valid_days": VALID_DAYS})
    return order


def uuid_of(v):
    import uuid as _uuid

    return v if isinstance(v, _uuid.UUID) else _uuid.UUID(str(v))


async def load(db: AsyncSession, order: CreditOrder, actor_id=None, source: str = "TRANSFER") -> CreditOrder:
    """Ödeme alındı: Odoo siparişi onaylanır, taslak fatura oluşur, deftere tek bir TOPUP yazılır, müşteri bilgilendirilir."""
    from app.services import credit_control, credits
    from app.services.odoo_service import OdooService

    if order.status != "PENDING":
        raise HTTPException(status_code=409, detail=f"Bu sipariş '{STATUS_TR.get(order.status, order.status)}' durumunda; kredi yüklenemez.")
    tenant = await db.get(Tenant, order.tenant_id)
    if order.odoo_order_id:
        if not await asyncio.to_thread(OdooService.confirm_sale_order, order.odoo_order_id):
            logger.warning("Odoo siparişi onaylanamadı (%s); kredi yine yüklenir, Odoo'da elle onaylanmalı.", order.odoo_order_name)
        inv = await asyncio.to_thread(OdooService.create_invoice_draft, order.odoo_order_id)
        order.odoo_invoice_ids = inv.get("invoice_ids") if inv.get("success") else None
    await credits.ensure_period_grant(db, tenant)
    upgrade = order.kind == "PLAN_UPGRADE"
    if upgrade and order.target_plan_id:  # paket hemen değişir; bu ayın oransal kredi farkı yüklenir, gelecek ay yeni paketin hakkı gelir
        tenant.plan_id = order.target_plan_id
    what = "Paket yükseltme farkı" if upgrade else "Ek kredi siparişi"
    entry = CreditLedgerEntry(tenant_id=tenant.id, entry_type="TOPUP", amount=Decimal(order.credits), period=credits.current_period(),
                              created_by_actor_id=actor_id, note=f"{what} {order.odoo_order_name or order.id} ({'kart' if source == 'CARD' else 'havale/EFT'})")
    db.add(entry)
    await db.flush()
    order.ledger_entry_id, order.status, order.decided_by_actor_id, order.decided_at = entry.id, "LOADED", actor_id, _now()
    await db.commit()
    await _mail(db, tenant, "CREDIT_ORDER_LOADED", {"credits": f"{order.credits:,}".replace(",", "."), "order_name": order.odoo_order_name or ""})
    if credits.spend_settings(tenant)["auto_resume_after_topup"]:  # #746: duraklayan işler kendiliğinden sürer
        await credit_control.resume_credit_paused(db, tenant, actor_id)
    return order


async def cancel(db: AsyncSession, order: CreditOrder, actor_id=None, reason: str = "", expired: bool = False) -> CreditOrder:
    from app.services.odoo_service import OdooService

    if order.status != "PENDING":
        raise HTTPException(status_code=409, detail="Yalnız ödemesi beklenen sipariş iptal edilebilir.")
    if order.odoo_order_id:
        await asyncio.to_thread(OdooService.cancel_sale_order, order.odoo_order_id)
    order.status = "EXPIRED" if expired else "CANCELLED"
    order.decided_by_actor_id, order.decided_at = actor_id, _now()
    order.note = (reason or ("Ödeme süresi doldu." if expired else "")).strip()[:500] or None
    await db.commit()
    return order


async def expire_due(db: AsyncSession) -> int:
    """Ödeme süresi dolan siparişleri iptal eder (zamanlayıcı)."""
    rows = (await db.execute(select(CreditOrder).where(CreditOrder.status == "PENDING", CreditOrder.expires_at < _now()))).scalars().all()
    for o in rows:
        try:
            await cancel(db, o, None, expired=True)
        except Exception as exc:
            logger.warning("Süresi dolan kredi siparişi iptal edilemedi (%s): %s", o.id, exc)
    return len(rows)
