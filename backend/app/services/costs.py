"""
Proje/Case maliyet hesabı (ADIM 7.5). Tutarlar TL, KDV hariç.

- Token maliyeti: llm_calls.cost_try (çağrı anındaki LLM fiyatı, ADIM 7.5.1); fiyatı tanımsız çağrılar "fiyatsız" sayılır.
- Personel maliyeti (ADIM 7.5.2): atanan personelin günlük maliyeti × gerçekleşen iş günü (hafta sonu hariç; başlangıçtan
  tamamlanmaya, sürüyorsa bugüne). Tamamlanan adımda ücret ve gün kayda geçer (snapshot), sonradan değişmez.
  Başlamamış adımda tahmin: günlük maliyet × planlanan süre (estimated_effort).
  AI personel için günlük maliyet isteğe bağlı sabit maliyettir; AI'nın asıl maliyeti token maliyetidir.
- Kişi bazında günlük ücret kişisel veridir (KVKK): bu servis adım bazında toplam döner, ücreti ayrıca göstermez.
"""
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Any, Dict, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Actor, LLMCall, Project, Task

ZERO = Decimal("0")


def _d(v) -> Decimal:
    return Decimal(str(v)) if v is not None else ZERO


def workdays(a: date, b: date) -> int:
    """a ve b dahil, hafta sonu hariç iş günü (en az 1)."""
    if b < a:
        return 1
    n, d = 0, a
    while d <= b:
        n += d.weekday() < 5
        d = date.fromordinal(d.toordinal() + 1)
    return max(1, n)


def _today() -> date:
    return datetime.now(timezone.utc).date()


def labor(task: Task, assignee: Optional[Actor]) -> Dict[str, Any]:
    """Adımın personel maliyeti: kayda geçmişse onu, değilse gerçekleşen/planlanan güne göre hesaplananı döner."""
    if task.labor_cost_try is not None:
        return {"days": float(task.labor_days or 0), "cost": _d(task.labor_cost_try), "basis": "ACTUAL", "rated": task.labor_rate_try is not None}
    rate = assignee.daily_cost_try if assignee else None
    if task.started_at:
        start = task.started_at.date()
        end = (task.completed_at.date() if task.completed_at else _today())
        days, basis = workdays(start, end), "ACTUAL" if task.completed_at else "RUNNING"
    else:
        days, basis = float(task.estimated_effort or 1), "PLANNED"
    cost = (_d(rate) * Decimal(str(days))).quantize(Decimal("0.01")) if rate is not None else ZERO
    return {"days": float(days), "cost": cost, "basis": basis, "rated": rate is not None}


async def snapshot_labor(db: AsyncSession, task: Task) -> None:
    """Adım tamamlanınca personel maliyetini kayda geçir (çağıran commit eder)."""
    assignee = await db.get(Actor, task.assignee_actor_id) if task.assignee_actor_id else None
    if task.labor_cost_try is not None:
        return
    rate = assignee.daily_cost_try if assignee else None
    start = task.started_at.date() if task.started_at else _today()
    end = task.completed_at.date() if task.completed_at else _today()
    days = workdays(start, end)
    task.labor_days = Decimal(days)
    task.labor_rate_try = rate
    task.labor_cost_try = (_d(rate) * Decimal(days)).quantize(Decimal("0.01")) if rate is not None else ZERO


async def project_costs(db: AsyncSession, project: Project) -> Dict[str, Any]:
    tasks = (await db.execute(select(Task).where(Task.project_id == project.id).order_by(Task.order_index))).scalars().all()
    actors = {a.id: a for a in (await db.execute(select(Actor).where(
        Actor.id.in_([t.assignee_actor_id for t in tasks if t.assignee_actor_id] or [project.manager_actor_id])))).scalars()}
    # Token maliyeti: adım bazında ve adıma bağlı olmayan proje çağrıları (Beyin AI planlama, planlama sohbeti)
    token_rows = (await db.execute(
        select(LLMCall.task_id, LLMCall.model_code, func.count(), func.sum(LLMCall.tokens_in), func.sum(LLMCall.tokens_out),
               func.sum(LLMCall.cost_try), func.count().filter(LLMCall.cost_try.is_(None)), func.sum(LLMCall.credits_cost))
        .where(LLMCall.project_id == project.id, LLMCall.status == "SUCCESS")
        .group_by(LLMCall.task_id, LLMCall.model_code))).all()
    by_task: Dict[Any, Dict[str, Any]] = {}
    by_model: Dict[str, Dict[str, Any]] = {}
    for task_id, model, calls, t_in, t_out, cost, unpriced, credits in token_rows:
        for bucket, key in ((by_task, task_id), (by_model, model)):
            b = bucket.setdefault(key, {"calls": 0, "tokens_in": 0, "tokens_out": 0, "cost": ZERO, "unpriced_calls": 0, "credits": ZERO})
            b["calls"] += calls
            b["tokens_in"] += int(t_in or 0)
            b["tokens_out"] += int(t_out or 0)
            b["cost"] += _d(cost)
            b["unpriced_calls"] += unpriced
            b["credits"] += _d(credits)

    rows, totals = [], {"labor": ZERO, "labor_planned": ZERO, "token": ZERO, "unpriced_calls": 0, "credits": ZERO}
    for t in tasks:
        assignee = actors.get(t.assignee_actor_id)
        lab = labor(t, assignee)
        tok = by_task.get(t.id, {"calls": 0, "tokens_in": 0, "tokens_out": 0, "cost": ZERO, "unpriced_calls": 0, "credits": ZERO})
        if lab["basis"] == "PLANNED":
            totals["labor_planned"] += lab["cost"]
        else:
            totals["labor"] += lab["cost"]
        totals["token"] += tok["cost"]
        totals["unpriced_calls"] += tok["unpriced_calls"]
        totals["credits"] += tok["credits"]
        rows.append({"task_id": str(t.id), "title": t.title, "status": t.status, "order_index": t.order_index,
                     "assignee": assignee.display_name if assignee else None, "assignee_type": assignee.actor_type if assignee else None,
                     "labor": {**lab, "cost": float(lab["cost"])},
                     "tokens": {**tok, "cost": float(tok["cost"]), "credits": float(tok["credits"])}})
    general = by_task.get(None)
    if general:
        totals["token"] += general["cost"]
        totals["unpriced_calls"] += general["unpriced_calls"]
        totals["credits"] += general["credits"]
    return {
        "project_id": str(project.id), "currency": "TRY", "vat_included": False,
        "tasks": rows,
        "project_level_tokens": {**general, "cost": float(general["cost"]), "credits": float(general["credits"])} if general else None,
        "by_model": [{"model_code": m, **v, "cost": float(v["cost"]), "credits": float(v["credits"])} for m, v in sorted(by_model.items())],
        "totals": {"labor": float(totals["labor"]), "labor_planned": float(totals["labor_planned"]), "token": float(totals["token"]),
                   "actual": float(totals["labor"] + totals["token"]), "unpriced_calls": totals["unpriced_calls"],
                   "credits": float(totals["credits"])},
    }
