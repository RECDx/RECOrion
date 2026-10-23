"""
Dashboard ve raporlar (ADIM 9).

company_overview(): şirket (veya bir departman) için proje/adım durumları, kredi ve TL maliyet zaman serisi, LLM bazında
token maliyeti, proje bazında bütçe/gerçekleşen ve maliyet kalemleri. KVKK: personel maliyeti yalnızca toplam ve proje
düzeyinde döner; kişi adı veya kişi başı ücret dönmez.
"""
import uuid
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, cast, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.types import Date

from app.db.models import LLMCall, Project, Task, Tenant
from app.services import costs, credits
from app.services import projects as psvc

PERIODS = (7, 30, 90, 365)
MAX_PROJECTS = 60  # maliyet tablosundaki en fazla proje (en son güncellenenler)
TZ = credits.TZ


def _f(v) -> float:
    return float(v or 0)


async def scope_projects(db: AsyncSession, tenant_id: uuid.UUID, department_id: Optional[uuid.UUID]) -> List[Project]:
    stmt = select(Project).where(Project.tenant_id == tenant_id)
    if department_id:
        stmt = stmt.where(Project.department_id == department_id)
    return (await db.execute(stmt.order_by(Project.created_at.desc()))).scalars().all()


async def company_overview(db: AsyncSession, tenant: Tenant, days: int = 30, department_id: Optional[uuid.UUID] = None) -> Dict[str, Any]:
    days = days if days in PERIODS else 30
    since = datetime.now(TZ).replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=days - 1)
    projects = await scope_projects(db, tenant.id, department_id)
    pids = [p.id for p in projects]
    no_projects = [uuid.uuid4()]

    # Proje ve adım durumları; zamanında biten = hedef bitiş tarihinden önce/aynı gün kapanan
    status_counts: Dict[str, int] = {}
    on_time = late = 0
    for p in projects:
        status_counts[p.status] = status_counts.get(p.status, 0) + 1
        if p.status == "COMPLETED" and p.end_date and p.closed_at:
            if p.closed_at.astimezone(TZ).date() <= p.end_date:
                on_time += 1
            else:
                late += 1
    task_counts = dict((await db.execute(select(Task.status, func.count()).where(Task.project_id.in_(pids or no_projects))
                                         .group_by(Task.status))).all())

    # Zaman serisi: günlük kredi ve TL token maliyeti (kapsam: şirket ya da departmanın projeleri)
    call_scope = [LLMCall.tenant_id == tenant.id, LLMCall.status == "SUCCESS", LLMCall.created_at >= since]
    if department_id:
        call_scope.append(LLMCall.project_id.in_(pids or no_projects))
    day = cast(func.timezone("Europe/Istanbul", LLMCall.created_at), Date)
    rows = (await db.execute(select(day, func.count(), func.sum(LLMCall.credits_cost), func.sum(LLMCall.cost_try))
                             .where(*call_scope).group_by(day).order_by(day))).all()
    by_day = {d: (c, cr, tl) for d, c, cr, tl in rows}
    series = []
    for i in range(days):
        d = (since + timedelta(days=i)).date()
        c, cr, tl = by_day.get(d, (0, 0, 0))
        series.append({"date": d.isoformat(), "calls": c, "credits": round(_f(cr), 2), "cost": round(_f(tl), 2)})
    by_model = [{"model_code": m, "calls": c, "credits": round(_f(cr), 2), "cost": round(_f(tl), 2), "unpriced_calls": u}
                for m, c, cr, tl, u in (await db.execute(
                    select(LLMCall.model_code, func.count(), func.sum(LLMCall.credits_cost), func.sum(LLMCall.cost_try),
                           func.count().filter(LLMCall.cost_try.is_(None)))
                    .where(*call_scope).group_by(LLMCall.model_code).order_by(func.sum(LLMCall.credits_cost).desc()))).all()]

    # Proje maliyetleri (ADIM 7.5 hesabıyla aynı): bütçe / gerçekleşen; personel yalnızca proje toplamı
    totals = {"labor": 0.0, "token": 0.0, "other": 0.0, "actual": 0.0, "budget": 0.0, "budget_projects": 0, "unpriced_calls": 0}
    by_category: Dict[str, Dict[str, Any]] = {}
    table = []
    for p in [p for p in projects if p.status != "DRAFT"][:MAX_PROJECTS]:
        c = await costs.project_costs(db, p)
        t = c["totals"]
        for k in ("labor", "token", "other", "actual"):
            totals[k] += t[k]
        totals["unpriced_calls"] += t["unpriced_calls"]
        if c["budget"]["amount"] is not None:
            totals["budget"] += c["budget"]["amount"]
            totals["budget_projects"] += 1
        for cat in c["by_category"]:
            b = by_category.setdefault(cat["category"], {"category": cat["category"], "label": cat["label"], "amount": 0.0})
            b["amount"] += cat["amount"]
        done = sum(1 for x in c["tasks"] if x["status"] == "DONE")
        table.append({"project_id": str(p.id), "name": p.name, "status": p.status, "status_label": psvc.STATUS_LABELS.get(p.status, p.status),
                      "budget": c["budget"]["amount"], "actual": t["actual"], "labor": t["labor"], "token": t["token"], "other": t["other"],
                      "variance": t["budget_variance"], "credits": t["credits"], "tasks_done": done, "tasks_total": len(c["tasks"])})
    credit_summary = None
    if not department_id:  # kredi hakkı şirket düzeyindedir
        unlimited = tenant.slug == "recdx_hq"
        if not unlimited:
            await credits.ensure_period_grant(db, tenant)
        credit_summary = (await credits.summary(db, tenant, unlimited=unlimited)).as_dict()
    return {
        "days": days, "since": since.date().isoformat(), "department_id": str(department_id) if department_id else None,
        "currency": "TRY", "vat_included": False,
        "projects": {"total": len(projects), "by_status": status_counts, "on_time": on_time, "late": late},
        "tasks": {"total": sum(task_counts.values()), "by_status": task_counts},
        "credits": credit_summary,
        "series": series,
        "by_model": by_model,
        "costs": {"totals": {k: (round(v, 2) if isinstance(v, float) else v) for k, v in totals.items()},
                  "by_category": sorted(by_category.values(), key=lambda x: -x["amount"]),
                  "projects": table},
    }
