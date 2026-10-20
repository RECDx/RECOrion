"""
RECOrion kredi muhasebesi.

Kurallar
- Dönem: İstanbul saatine göre takvim ayı (YYYY-MM).
- Her dönemin ilk kullanımında paketin aylık kredisi (plans.monthly_credits) deftere eklenir.
- Kullanım önce aylık krediden düşer; aylık kredinin kullanılmayan kısmı dönem sonunda
  süresi dolar (EXPIRE kaydı). Ek yüklenen krediler (TOPUP) devreder.
- Kredi maliyeti (V3 formülü): katsayı × (giriş_token/1000 × 1 + çıkış_token/1000 × 2)
- Bakiye = defterdeki tutarların toplamı. Defter değiştirilemez (veritabanı tetikleyicisi).
- RECDx ana şirketinin (platform) kullanımı ölçülür ama sınırlanmaz.
"""
import logging
import uuid
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Optional
from zoneinfo import ZoneInfo

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Actor, CreditLedgerEntry, Plan, Tenant

logger = logging.getLogger("recorion.credits")

TZ = ZoneInfo("Europe/Istanbul")
INPUT_WEIGHT = Decimal("1.0")
OUTPUT_WEIGHT = Decimal("2.0")


def current_period(now: Optional[datetime] = None) -> str:
    return (now or datetime.now(TZ)).astimezone(TZ).strftime("%Y-%m")


def credit_cost(effort_coefficient, tokens_in: int, tokens_out: int) -> Decimal:
    coef = Decimal(str(effort_coefficient or 1))
    cost = coef * (Decimal(tokens_in) / 1000 * INPUT_WEIGHT + Decimal(tokens_out) / 1000 * OUTPUT_WEIGHT)
    return cost.quantize(Decimal("0.0001"))


async def _sum(db: AsyncSession, *conditions) -> Decimal:
    value = (await db.execute(select(func.coalesce(func.sum(CreditLedgerEntry.amount), 0)).where(*conditions))).scalar()
    return Decimal(str(value or 0))


async def balance(db: AsyncSession, tenant_id: uuid.UUID) -> Decimal:
    return await _sum(db, CreditLedgerEntry.tenant_id == tenant_id)


async def ensure_period_grant(db: AsyncSession, tenant: Tenant) -> None:
    """Bu dönemin aylık kredisini (gerekirse önceki dönemin süresi dolan kısmıyla) deftere ekler."""
    period = current_period()
    exists = (await db.execute(select(CreditLedgerEntry.id).where(
        CreditLedgerEntry.tenant_id == tenant.id, CreditLedgerEntry.period == period,
        CreditLedgerEntry.entry_type == "MONTHLY_GRANT",
    ))).first()
    if exists:
        return

    last_grant = (await db.execute(select(CreditLedgerEntry).where(
        CreditLedgerEntry.tenant_id == tenant.id, CreditLedgerEntry.entry_type == "MONTHLY_GRANT",
    ).order_by(CreditLedgerEntry.period.desc()).limit(1))).scalar_one_or_none()
    try:
        if last_grant and last_grant.period < period:
            used = -await _sum(db, CreditLedgerEntry.tenant_id == tenant.id, CreditLedgerEntry.period == last_grant.period,
                               CreditLedgerEntry.entry_type == "USAGE")
            remainder = max(Decimal(0), Decimal(str(last_grant.amount)) - used)
            if remainder > 0:
                db.add(CreditLedgerEntry(tenant_id=tenant.id, entry_type="EXPIRE", amount=-remainder,
                                         period=last_grant.period, note="Kullanılmayan aylık kredinin süresi doldu"))
        plan = await db.get(Plan, tenant.plan_id) if tenant.plan_id else None
        monthly = Decimal(str(plan.monthly_credits or 0)) if plan else Decimal(0)
        db.add(CreditLedgerEntry(tenant_id=tenant.id, entry_type="MONTHLY_GRANT", amount=monthly, period=period,
                                 note=f"{plan.name if plan else 'Paketsiz'} aylık kredi hakkı"))
        await db.commit()
    except IntegrityError:
        await db.rollback()  # aynı anda başka bir istek eklemiş


@dataclass
class CreditSummary:
    period: str
    monthly_grant: Decimal
    used_this_period: Decimal
    monthly_remaining: Decimal
    topup_balance: Decimal
    balance: Decimal
    percent_used: float
    unlimited: bool = False

    def as_dict(self) -> dict:
        return {k: (float(v) if isinstance(v, Decimal) else v) for k, v in self.__dict__.items()}


async def summary(db: AsyncSession, tenant: Tenant, unlimited: bool = False) -> CreditSummary:
    period = current_period()
    grant = await _sum(db, CreditLedgerEntry.tenant_id == tenant.id, CreditLedgerEntry.period == period,
                       CreditLedgerEntry.entry_type == "MONTHLY_GRANT")
    used = -await _sum(db, CreditLedgerEntry.tenant_id == tenant.id, CreditLedgerEntry.period == period,
                       CreditLedgerEntry.entry_type == "USAGE")
    total = await balance(db, tenant.id)
    monthly_remaining = max(Decimal(0), grant - used)
    return CreditSummary(
        period=period, monthly_grant=grant, used_this_period=used, monthly_remaining=monthly_remaining,
        topup_balance=max(Decimal(0), total - monthly_remaining), balance=total,
        percent_used=round(float(used / grant * 100), 1) if grant > 0 else 0.0, unlimited=unlimited,
    )


async def record_usage(db: AsyncSession, tenant_id: uuid.UUID, amount: Decimal, llm_call_id: uuid.UUID, note: str) -> None:
    if amount <= 0:
        return
    db.add(CreditLedgerEntry(tenant_id=tenant_id, entry_type="USAGE", amount=-amount, period=current_period(),
                             llm_call_id=llm_call_id, note=note[:200]))


async def topup(db: AsyncSession, tenant: Tenant, amount: Decimal, actor_id: Optional[uuid.UUID], note: str) -> None:
    db.add(CreditLedgerEntry(tenant_id=tenant.id, entry_type="TOPUP", amount=amount, period=current_period(),
                             created_by_actor_id=actor_id, note=note or "Ek kredi yüklemesi"))
    await db.commit()


async def check_alerts(db: AsyncSession, tenant: Tenant) -> None:
    """%80 ve tükenme uyarılarını dönem başına bir kez şirket yöneticisine e-postayla bildirir."""
    from app.core.tokens import redis_client
    from app.services.notification_service import NotificationService

    s = await summary(db, tenant)
    if s.monthly_grant <= 0:
        return
    if s.balance <= 0:
        level, code = "100", "CREDIT_EXHAUSTED"
    elif s.percent_used >= 80:
        level, code = "80", "CREDIT_LOW"
    else:
        return
    client = redis_client()
    try:
        first = await client.set(f"credit_alert:{tenant.id}:{s.period}:{level}", "1", nx=True, ex=40 * 86400)
    except Exception as exc:
        logger.warning("Kredi uyarısı kilidi alınamadı: %s", exc)
        first = False
    finally:
        await client.aclose()
    if not first:
        return
    admin = (await db.execute(select(Actor).where(Actor.tenant_id == tenant.id, Actor.role == "COMPANY_ADMIN")
                              .order_by(Actor.created_at))).scalars().first()
    await NotificationService.send_by_code(db, code, (admin.email if admin else None) or tenant.contact_email, {
        "contact_name": admin.display_name if admin else "Yetkili",
        "company_name": tenant.name, "period": s.period,
        "percent": int(s.percent_used), "remaining": f"{float(s.balance):,.0f}".replace(",", "."),
    })
