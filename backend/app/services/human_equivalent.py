"""
Kredinin TL karşılığı ve insan eşdeğeri (#664, kullanıcı kararı 07.11.2026).

- Kredi birim fiyatı (müşteri gözü): paketin `credit_unit_price_try` değeri; boşsa aylık ücret ÷ aylık kredi
  (2026: Başlangıç 2,98 · PRO 1,60 · Kurumsal 0,99 TL/kredi). RECDx'in gerçek maliyeti (EVREN/GPU) ayrıdır
  (`cost.real_credit_cost_try`), yalnız Merkez'de kullanılır.
- İnsan eşdeğeri: adımı yapacak ünvanın referans aylık brüt maaşı × işveren maliyet katsayısı ÷ aylık iş günü ×
  planlanan iş günü (Beyin AI'nın adım için önerdiği süre). Maaş: ünvana özel değer, yoksa aile (Yazılım/BT, Genel)
  ve kıdeme göre referans bandı; ünvan yoksa Genel/MID varsayılanı. Referans bantları kişisel veri değildir.
"""
import re
from decimal import Decimal
from typing import Any, Dict, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import JobTitle, Plan, SystemSetting, Tenant

DEFAULT_BANDS = {"IT": {"JUNIOR": 85000, "MID": 140000, "SENIOR": 210000, "LEAD": 240000, "MANAGER": 260000},
                 "GENERAL": {"JUNIOR": 50000, "MID": 75000, "SENIOR": 110000, "LEAD": 135000, "MANAGER": 190000}}
DEFAULTS = {"salary_bands": DEFAULT_BANDS, "employer_factor": 1.25, "work_days_month": 22, "real_credit_cost_try": None}
KEYS = {"salary_bands": "cost.salary_bands", "employer_factor": "cost.employer_factor", "work_days_month": "cost.work_days_month",
        "real_credit_cost_try": "cost.real_credit_cost_try"}
SENIORITIES = ("JUNIOR", "MID", "SENIOR", "LEAD", "MANAGER")
IT_PATTERN = re.compile(r"yazılım|geliştirici|developer|\btest|\bqa\b|bilgi teknoloj|\bbt\b|sistem ve ağ|veri analist|veri bilim|"
                        r"siber|bilgi güvenli|devops|yapay zeka|bilişim", re.I)
D2 = Decimal("0.01")


async def settings(db: AsyncSession) -> Dict[str, Any]:
    out = dict(DEFAULTS)
    for name, key in KEYS.items():
        row = await db.get(SystemSetting, key)
        if row is not None:
            out[name] = row.value
    return out


def validate(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Merkez'den gelen ayarları sınırlar içine alır (bilinmeyen anahtar atılır)."""
    bands = payload.get("salary_bands") or DEFAULT_BANDS
    clean = {fam: {s: max(0, min(10_000_000, int(float((bands.get(fam) or {}).get(s) or DEFAULT_BANDS[fam][s])))) for s in SENIORITIES}
             for fam in ("IT", "GENERAL")}
    factor = max(1.0, min(3.0, float(payload.get("employer_factor") or 1.25)))
    days = max(15, min(31, int(payload.get("work_days_month") or 22)))
    real = payload.get("real_credit_cost_try")
    real = None if real in (None, "") else max(0.0, min(1000.0, float(real)))
    return {"salary_bands": clean, "employer_factor": factor, "work_days_month": days, "real_credit_cost_try": real}


async def save(db: AsyncSession, payload: Dict[str, Any]) -> Dict[str, Any]:
    clean = validate(payload)
    for name, key in KEYS.items():
        row = await db.get(SystemSetting, key)
        if row is None:
            db.add(SystemSetting(key=key, value=clean[name]))
        else:
            row.value = clean[name]
    await db.commit()
    return clean


def credit_unit(plan: Optional[Plan]) -> Optional[Decimal]:
    """Kredi birim fiyatı (TL): paketteki değer, yoksa aylık ücret ÷ aylık kredi."""
    if not plan:
        return None
    if plan.credit_unit_price_try is not None:
        return Decimal(str(plan.credit_unit_price_try))
    if plan.monthly_price and plan.monthly_credits:
        return (Decimal(str(plan.monthly_price)) / Decimal(int(plan.monthly_credits))).quantize(Decimal("0.0001"))
    return None


async def tenant_credit_unit(db: AsyncSession, tenant: Tenant) -> Optional[Decimal]:
    return credit_unit(await db.get(Plan, tenant.plan_id) if tenant.plan_id else None)


def family(jt: Optional[JobTitle]) -> str:
    if not jt:
        return "GENERAL"
    return "IT" if IT_PATTERN.search(f"{jt.title} {jt.category or ''}") else "GENERAL"


def human_for(jt: Optional[JobTitle], days: float, cfg: Dict[str, Any]) -> Dict[str, Any]:
    """Bir adımın insan eşdeğeri: gün × günlük maliyet."""
    fam = family(jt)
    seniority = (jt.seniority if jt and jt.seniority in SENIORITIES else "MID")
    if jt and jt.reference_salary_try is not None:
        monthly, basis = Decimal(str(jt.reference_salary_try)), "UNVAN"
    else:
        bands = cfg.get("salary_bands") or DEFAULT_BANDS
        monthly = Decimal(str((bands.get(fam) or DEFAULT_BANDS[fam]).get(seniority) or DEFAULT_BANDS[fam][seniority]))
        basis = "REFERANS" if jt else "VARSAYILAN"
    daily = (monthly * Decimal(str(cfg.get("employer_factor") or 1.25)) / Decimal(int(cfg.get("work_days_month") or 22))).quantize(D2)
    d = Decimal(str(days or 1))
    return {"job_title": jt.title if jt else None, "family": fam, "seniority": seniority, "monthly_salary": float(monthly),
            "daily_cost": float(daily), "days": float(d), "cost": float((daily * d).quantize(D2)), "basis": basis}
