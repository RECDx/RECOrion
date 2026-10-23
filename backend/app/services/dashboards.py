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

from app.db.models import Actor, LLMCall, Project, Task, TaskEvent, Tenant
from app.services import costs, credits
from app.services import projects as psvc

PERIODS = (7, 30, 90, 365)
ROI_MIN_RATED_HUMANS = 3  # KVKK: ortalama tek kişinin ücretini ele vermesin
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
    agents, roi = await agent_scorecards(db, tenant, since, department_id)
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
        "agents": agents,
        "roi": roi,
    }


async def agent_scorecards(db: AsyncSession, tenant: Tenant, since: datetime, department_id: Optional[uuid.UUID] = None):
    """AI personel karnesi (ADIM 9.2) ve tahmini tasarruf.

    - İlk seferde onay: tamamlanan adımlardan kontrol personeli veya insan revizyonu istenmeyenlerin payı.
    - Otonomi: insan revizyonu istenmeden tamamlanan adımların payı (insan onayı tasarım gereği her zaman vardır).
    - Süre: adımın başlaması ile teslim arası (saat). Maliyet: kredi, TL token maliyeti, AI sabit günlük maliyeti.
    - Tasarruf: AI'ın tamamladığı iş günü x şirketin ortalama insan günlük maliyeti - AI maliyeti (token + sabit).
      Ortalama, en az ROI_MIN_RATED_HUMANS insan personelin günlük maliyeti tanımlıysa hesaplanır (KVKK).
    """
    stmt = select(Actor).where(Actor.tenant_id == tenant.id, Actor.actor_type == "AI_AGENT")
    if department_id:
        stmt = stmt.where(Actor.department_id == department_id)
    agents = (await db.execute(stmt.order_by(Actor.display_name))).scalars().all()
    ids = [a.id for a in agents] or [uuid.uuid4()]
    done = (await db.execute(select(Task).where(Task.assignee_actor_id.in_(ids), Task.status == "DONE",
                                                Task.completed_at >= since))).scalars().all()
    task_ids = [t.id for t in done] or [uuid.uuid4()]
    # Adım başına revizyon olayları (tamamlanan adımların tüm geçmişi) ve dönem içindeki karantinalar
    ev = {}
    for tid, kind, n in (await db.execute(select(TaskEvent.task_id, TaskEvent.kind, func.count())
                                          .where(TaskEvent.task_id.in_(task_ids), TaskEvent.kind.in_(("REJECTED", "REVIEW_FAILED")))
                                          .group_by(TaskEvent.task_id, TaskEvent.kind))).all():
        ev.setdefault(tid, {})[kind] = n
    assigned = dict((await db.execute(select(Task.assignee_actor_id, func.count()).where(Task.assignee_actor_id.in_(ids))
                                      .group_by(Task.assignee_actor_id))).all())
    quarantined = dict((await db.execute(
        select(Task.assignee_actor_id, func.count()).join(TaskEvent, TaskEvent.task_id == Task.id)
        .where(Task.assignee_actor_id.in_(ids), TaskEvent.kind == "QUARANTINED", TaskEvent.created_at >= since)
        .group_by(Task.assignee_actor_id))).all())
    spend = {a: (c, cr, tl, u) for a, c, cr, tl, u in (await db.execute(
        select(LLMCall.actor_id, func.count(), func.sum(LLMCall.credits_cost), func.sum(LLMCall.cost_try),
               func.count().filter(LLMCall.cost_try.is_(None)))
        .where(LLMCall.actor_id.in_(ids), LLMCall.status == "SUCCESS", LLMCall.created_at >= since)
        .group_by(LLMCall.actor_id))).all()}

    rates = [Decimal(str(r)) for (r,) in (await db.execute(select(Actor.daily_cost_try).where(
        Actor.tenant_id == tenant.id, Actor.actor_type == "HUMAN", Actor.daily_cost_try.isnot(None), Actor.daily_cost_try > 0))).all()]
    avg_rate = (sum(rates) / len(rates)) if len(rates) >= ROI_MIN_RATED_HUMANS else None

    cards, total_days, total_ai_cost, total_unpriced = [], Decimal(0), Decimal(0), 0
    for a in agents:
        mine = [t for t in done if t.assignee_actor_id == a.id]
        first_pass = sum(1 for t in mine if not ev.get(t.id))
        autonomous = sum(1 for t in mine if not ev.get(t.id, {}).get("REJECTED"))
        revisions = sum(sum(ev.get(t.id, {}).values()) for t in mine)
        hours = [(t.submitted_at - t.started_at).total_seconds() / 3600 for t in mine if t.started_at and t.submitted_at]
        days = sum((Decimal(str(t.labor_days)) if t.labor_days is not None else
                    Decimal(costs.workdays(t.started_at.date(), t.completed_at.date())) if t.started_at else Decimal(1)) for t in mine)
        fixed = sum((Decimal(str(t.labor_cost_try)) for t in mine if t.labor_cost_try is not None), Decimal(0))
        calls, cr, tl, unpriced = spend.get(a.id, (0, 0, 0, 0))
        ai_cost = Decimal(str(tl or 0)) + fixed
        total_days += days
        total_ai_cost += ai_cost
        total_unpriced += unpriced
        if not (assigned.get(a.id) or calls):
            continue  # hiç işi olmayan personel karnede gösterilmez
        cards.append({
            "actor_id": str(a.id), "name": a.display_name, "title": a.role, "status": a.status, "autonomy_level": a.autonomy_level,
            "assigned": assigned.get(a.id, 0), "completed": len(mine),
            "first_pass_rate": round(first_pass / len(mine), 3) if mine else None,
            "autonomy_rate": round(autonomous / len(mine), 3) if mine else None,
            "revisions": revisions, "quarantined": quarantined.get(a.id, 0),
            "avg_hours": round(sum(hours) / len(hours), 1) if hours else None,
            "work_days": float(days), "calls": calls, "credits": round(_f(cr), 2), "cost": round(float(ai_cost), 2), "unpriced_calls": unpriced,
        })
    if avg_rate is None:
        roi = {"available": False, "reason": f"Tahmini tasarruf için en az {ROI_MIN_RATED_HUMANS} insan personelin günlük maliyeti "
                                              "tanımlı olmalı (ortalama kişi ücretini ele vermesin diye; KVKK).",
               "rated_humans": len(rates), "work_days": float(total_days), "ai_cost": round(float(total_ai_cost), 2)}
    else:
        human_equivalent = total_days * avg_rate
        roi = {"available": True, "work_days": float(total_days), "human_equivalent": round(float(human_equivalent), 2),
               "ai_cost": round(float(total_ai_cost), 2), "saving": round(float(human_equivalent - total_ai_cost), 2),
               "rated_humans": len(rates), "unpriced_calls": total_unpriced,
               "assumption": "AI personelin tamamladığı adımların iş günü, şirketin ortalama insan günlük maliyetiyle yapılsaydı "
                             "oluşacak tutardan AI'ın token ve sabit maliyeti düşülerek bulunur."}
    return cards, roi
