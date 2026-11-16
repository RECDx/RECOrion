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
# #746: bakiye bunun altındaysa "kredi bitti" sayılır (bir AI adımı tipik olarak onlarca–yüzlerce kredi harcar)
EXHAUSTED_BELOW = Decimal(50)
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


# ---------------------------------------------------------------- #746: harcama ayarları, haftalık sınır, tahmin
def week_key(now: Optional[datetime] = None) -> str:
    """ISO hafta anahtarı (İstanbul saati), ör. 2026-W47."""
    y, w, _ = (now or datetime.now(TZ)).astimezone(TZ).isocalendar()
    return f"{y}-W{w:02d}"


def week_start(now: Optional[datetime] = None) -> datetime:
    from datetime import timedelta

    n = (now or datetime.now(TZ)).astimezone(TZ)
    return (n - timedelta(days=n.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)


def spend_settings(tenant: Tenant) -> dict:
    """Şirketin harcama ayarları (tenant.settings['credit']): haftalık sınır (aylık hakkın %'si; None = kapalı, varsayılan),
    kredi yüklenince duraklayan işlerin kendiliğinden devam etmesi, bu hafta için sınırın kaldırılması."""
    c = ((tenant.settings or {}).get("credit") or {})
    cap = c.get("weekly_cap_pct")
    return {"weekly_cap_pct": int(cap) if cap not in (None, "", 0) else None,
            "auto_resume_after_topup": bool(c.get("auto_resume_after_topup", False)),
            "weekly_cap_lifted_week": c.get("weekly_cap_lifted_week")}


async def week_used(db: AsyncSession, tenant_id: uuid.UUID, now: Optional[datetime] = None) -> Decimal:
    return -await _sum(db, CreditLedgerEntry.tenant_id == tenant_id, CreditLedgerEntry.entry_type == "USAGE",
                       CreditLedgerEntry.created_at >= week_start(now))


async def weekly_cap_block(db: AsyncSession, tenant: Tenant, estimate: Decimal = Decimal(0)) -> Optional[str]:
    """Haftalık harcama sınırı açık ve bu hafta doluysa kullanıcıya gösterilecek metin; değilse None."""
    s = spend_settings(tenant)
    if not s["weekly_cap_pct"] or s["weekly_cap_lifted_week"] == week_key():
        return None
    grant = await _sum(db, CreditLedgerEntry.tenant_id == tenant.id, CreditLedgerEntry.period == current_period(),
                       CreditLedgerEntry.entry_type == "MONTHLY_GRANT")
    if grant <= 0:
        return None
    cap = grant * Decimal(s["weekly_cap_pct"]) / 100
    used = await week_used(db, tenant.id)
    if used + estimate <= cap:
        return None
    return (f"Şirketin haftalık harcama sınırına ulaşıldı (aylık hakkın %{s['weekly_cap_pct']}'i, {float(cap):,.0f} kredi). "
            "Yeni AI işleri bu hafta başlamaz; şirket yöneticisi Kredi ve Kullanım ekranından sınırı bu hafta için kaldırabilir.").replace(",", ".")


def forecast_depletion(used: Decimal, balance_: Decimal, now: Optional[datetime] = None) -> Optional[str]:
    """Bu dönemki harcama hızıyla bakiyenin biteceği gün (YYYY-MM-DD); hız yoksa None."""
    from datetime import timedelta

    n = (now or datetime.now(TZ)).astimezone(TZ)
    elapsed_days = max((n - n.replace(day=1, hour=0, minute=0, second=0, microsecond=0)).total_seconds() / 86400, 0.25)
    rate = used / Decimal(str(elapsed_days))
    if rate <= 0 or balance_ <= 0:
        return None
    days = float(balance_ / rate)
    if days > 366:
        return None
    return (n + timedelta(days=days)).date().isoformat()


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
    # #746: kullanım göstergesi
    depletes_on: Optional[str] = None
    level: str = "OK"  # OK, WARN80, WARN95, EXHAUSTED
    week_used: Decimal = Decimal(0)
    settings: Optional[dict] = None
    weekly_cap_reached: bool = False

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
    pct = round(float(used / grant * 100), 1) if grant > 0 else 0.0
    level = "EXHAUSTED" if (not unlimited and total < EXHAUSTED_BELOW) else ("WARN95" if pct >= 95 else ("WARN80" if pct >= 80 else "OK"))
    return CreditSummary(
        period=period, monthly_grant=grant, used_this_period=used, monthly_remaining=monthly_remaining,
        topup_balance=max(Decimal(0), total - monthly_remaining), balance=total,
        percent_used=pct, unlimited=unlimited,
        depletes_on=None if unlimited else forecast_depletion(used, total), level="OK" if unlimited else level,
        week_used=await week_used(db, tenant.id), settings=spend_settings(tenant),
        weekly_cap_reached=False if unlimited else bool(await weekly_cap_block(db, tenant)),
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
    # #746: şirket ayarı açıksa kredi nedeniyle duraklayan işler yüklemeden sonra kendiliğinden devam eder
    if spend_settings(tenant)["auto_resume_after_topup"]:
        from app.services import credit_control

        await credit_control.resume_credit_paused(db, tenant, actor_id)


async def check_alerts(db: AsyncSession, tenant: Tenant) -> None:
    """%80 ve tükenme uyarılarını dönem başına bir kez şirket yöneticisine e-postayla bildirir."""
    from app.core.tokens import redis_client
    from app.services.notification_service import NotificationService

    s = await summary(db, tenant)
    if s.monthly_grant <= 0:
        return
    if s.balance <= 0:
        level, code = "100", "CREDIT_EXHAUSTED"
    elif s.percent_used >= 95:  # #746
        level, code = "95", "CREDIT_LOW"
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
    # #746: aktif projesi olan proje yöneticilerine de kısa bildirim (tercih ettikleri kanaldan)
    from app.db.models import Project
    from app.services import task_flow

    pms = {pm for (pm,) in (await db.execute(select(Project.manager_actor_id).where(
        Project.tenant_id == tenant.id, Project.status.in_(("ACTIVE", "PAUSED")), Project.manager_actor_id.isnot(None)))).all()}
    pms.discard(admin.id if admin else None)
    text = (f"RECOrion: {tenant.name} kredisi bitti; projeler duraklatılır. Ek kredi için şirket yöneticinize başvurun."
            if level == "100" else
            f"RECOrion: {tenant.name} bu ayın kredi hakkının %{int(s.percent_used)}'ini kullandı"
            + (f"; bu hızla {s.depletes_on} tarihinde biter." if s.depletes_on else "."))
    for pm in pms:
        try:
            await task_flow.notify(db, pm, text)
        except Exception as exc:  # bildirim hatası kullanımı engellemez
            logger.warning("Kredi bildirimi gönderilemedi (%s): %s", pm, exc)
