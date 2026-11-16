"""
İSTEK #747 — Ek kredi satın alma uçları.

Merkez (Süper Admin): kredi paketleri tanımı (Odoo ürünü seçimi), kredi siparişleri (havale/EFT onayı = kredi yükleme, iptal),
ödeme ayarları (banka bilgisi). Şirket: satın alınabilir paketler + siparişlerim, sipariş verme (yalnız şirket yöneticisi),
ödemesi beklenen siparişi iptal.
"""
import uuid
from decimal import Decimal
from typing import List, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import CurrentUser, get_current_user
from app.db.models import CreditOrder, CreditPack, Tenant
from app.db.session import get_db
from app.services import credit_store as cs

router = APIRouter(tags=["Ek kredi satın alma (#747)"])


# ---------------------------------------------------------------- Merkez
class PackIn(BaseModel):
    code: str = Field(..., min_length=2, max_length=32)
    name: str = Field(..., min_length=2, max_length=128)
    credits: int = Field(..., ge=100, le=10_000_000)
    price_try: Optional[Decimal] = Field(None, ge=0, le=100_000_000)
    odoo_product_id: Optional[int] = None
    plan_codes: List[str] = Field(default_factory=list)
    sort_order: int = 0
    is_active: bool = False


async def _check_pack(payload: PackIn) -> None:
    if payload.is_active and (not payload.price_try or not payload.odoo_product_id):
        raise HTTPException(status_code=422, detail="Satışa açmak için fiyat ve Odoo ürünü girilmeli.")
    from app.api.v1.tenants import _validate_odoo_product

    await _validate_odoo_product(payload.odoo_product_id)


@router.get("/system/credit-packs")
async def list_packs(db: AsyncSession = Depends(get_db)):
    rows = (await db.execute(select(CreditPack).order_by(CreditPack.sort_order, CreditPack.credits))).scalars().all()
    return [cs.pack_out(p, admin=True) for p in rows]


@router.post("/system/credit-packs", status_code=201)
async def create_pack(payload: PackIn, db: AsyncSession = Depends(get_db)):
    await _check_pack(payload)
    if (await db.execute(select(CreditPack).where(CreditPack.code == payload.code.strip().upper()))).scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Bu kodla bir kredi paketi zaten var.")
    p = CreditPack(**{**payload.model_dump(), "code": payload.code.strip().upper()})
    db.add(p)
    await db.commit()
    return cs.pack_out(p, admin=True)


@router.put("/system/credit-packs/{pack_id}")
async def update_pack(pack_id: uuid.UUID, payload: PackIn, db: AsyncSession = Depends(get_db)):
    p = await db.get(CreditPack, pack_id)
    if not p:
        raise HTTPException(status_code=404, detail="Kredi paketi bulunamadı.")
    await _check_pack(payload)
    for k, v in payload.model_dump().items():
        setattr(p, k, v.strip().upper() if k == "code" else v)
    await db.commit()
    return cs.pack_out(p, admin=True)


@router.get("/system/credit-orders")
async def list_orders(status: Optional[str] = Query(None, max_length=16), db: AsyncSession = Depends(get_db)):
    q = select(CreditOrder).order_by(CreditOrder.created_at.desc()).limit(300)
    if status:
        q = q.where(CreditOrder.status == status)
    rows = (await db.execute(q)).scalars().all()
    names = dict((await db.execute(select(Tenant.id, Tenant.name).where(Tenant.id.in_([o.tenant_id for o in rows] or [uuid.uuid4()])))).all())
    return [cs.order_out(o, names.get(o.tenant_id)) for o in rows]


@router.post("/system/credit-orders/{order_id}/load")
async def load_order(order_id: uuid.UUID, user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Havale/EFT ödemesi alındı: Odoo siparişi onaylanır, taslak fatura oluşur, kredi yüklenir."""
    o = await db.get(CreditOrder, order_id)
    if not o:
        raise HTTPException(status_code=404, detail="Sipariş bulunamadı.")
    return cs.order_out(await cs.load(db, o, user.actor_id))


class CancelIn(BaseModel):
    reason: Optional[str] = Field(None, max_length=500)


@router.post("/system/credit-orders/{order_id}/cancel")
async def cancel_order_hq(order_id: uuid.UUID, payload: CancelIn, user: CurrentUser = Depends(get_current_user),
                          db: AsyncSession = Depends(get_db)):
    o = await db.get(CreditOrder, order_id)
    if not o:
        raise HTTPException(status_code=404, detail="Sipariş bulunamadı.")
    return cs.order_out(await cs.cancel(db, o, user.actor_id, payload.reason or "RECDx tarafından iptal edildi."))


class BillingIn(BaseModel):
    bank_info: str = Field("", max_length=2000)


@router.get("/system/billing-settings")
async def get_billing(db: AsyncSession = Depends(get_db)):
    return await cs.billing_settings(db)


@router.put("/system/billing-settings")
async def put_billing(payload: BillingIn, db: AsyncSession = Depends(get_db)):
    return await cs.set_billing_settings(db, payload.bank_info.strip())


# ---------------------------------------------------------------- Şirket
async def _tenant(db: AsyncSession, tenant_id: uuid.UUID) -> Tenant:
    t = await db.get(Tenant, tenant_id)
    if not t:
        raise HTTPException(status_code=404, detail="Şirket bulunamadı.")
    return t


@router.get("/company/{tenant_id}/credit-store")
async def credit_store(tenant_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Satın alınabilir kredi paketleri, ödeme bilgileri ve şirketin kredi siparişleri."""
    t = await _tenant(db, tenant_id)
    orders = (await db.execute(select(CreditOrder).where(CreditOrder.tenant_id == t.id).order_by(CreditOrder.created_at.desc()).limit(50))).scalars().all()
    from app.db.models import Plan

    plan = await db.get(Plan, t.plan_id) if t.plan_id else None
    return {"packs": [cs.pack_out(p) for p in await cs.packs_for(db, t)], **await cs.billing_settings(db),
            "orders": [cs.order_out(o) for o in orders], "upgrade_options": await cs.upgrade_options(db, t),
            "current_plan": {"code": plan.code, "name": plan.name, "monthly_credits": plan.monthly_credits} if plan else None}


class UpgradeIn(BaseModel):
    plan_id: uuid.UUID


@router.post("/company/{tenant_id}/plan-upgrade-orders", status_code=201)
async def place_upgrade(tenant_id: uuid.UUID, payload: UpgradeIn, user: CurrentUser = Depends(get_current_user),
                        db: AsyncSession = Depends(get_db)):
    """#747 ek: paket yükseltme siparişi (hemen geçerli; bu ayın kalan günleri için oransal fiyat ve kredi farkı)."""
    t = await _tenant(db, tenant_id)
    return cs.order_out(await cs.create_upgrade_order(db, t, payload.plan_id, user.actor_id))


class OrderIn(BaseModel):
    pack_id: uuid.UUID
    payment_method: Literal["TRANSFER", "CARD"] = "TRANSFER"


@router.post("/company/{tenant_id}/credit-orders", status_code=201)
async def place_order(tenant_id: uuid.UUID, payload: OrderIn, user: CurrentUser = Depends(get_current_user),
                      db: AsyncSession = Depends(get_db)):
    t = await _tenant(db, tenant_id)
    return cs.order_out(await cs.create_order(db, t, payload.pack_id, payload.payment_method, user.actor_id))


@router.post("/company/{tenant_id}/credit-orders/{order_id}/cancel")
async def cancel_order(tenant_id: uuid.UUID, order_id: uuid.UUID, user: CurrentUser = Depends(get_current_user),
                       db: AsyncSession = Depends(get_db)):
    o = await db.get(CreditOrder, order_id)
    if not o or o.tenant_id != tenant_id:
        raise HTTPException(status_code=404, detail="Sipariş bulunamadı.")
    return cs.order_out(await cs.cancel(db, o, user.actor_id, "Müşteri iptal etti."))
