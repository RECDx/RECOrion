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

from app.db.models import Actor, LLMCall, Project, ProjectCostItem, Task

CATEGORIES = {"MATERYAL": "Materyal", "DANISMANLIK": "Danışmanlık", "EGITIM": "Eğitim", "LISANS": "Lisans / yazılım",
              "SEYAHAT": "Seyahat", "DONANIM": "Donanım", "DIGER": "Diğer"}

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

    # Diğer maliyet kalemleri (ADIM 7.5.3)
    items = (await db.execute(select(ProjectCostItem).where(ProjectCostItem.project_id == project.id)
                              .order_by(ProjectCostItem.incurred_on, ProjectCostItem.created_at))).scalars().all()
    by_category: Dict[str, Decimal] = {}
    items_by_task: Dict[Any, Decimal] = {}
    for it in items:
        by_category[it.category] = by_category.get(it.category, ZERO) + _d(it.amount_try)
        items_by_task[it.task_id] = items_by_task.get(it.task_id, ZERO) + _d(it.amount_try)
    other = sum(by_category.values(), ZERO)
    for row in rows:
        row["other"] = float(items_by_task.get(uuid_of(row["task_id"]), ZERO))
    planned = await planned_costs(db, project, tasks, actors)
    return {
        "project_id": str(project.id), "currency": "TRY", "vat_included": False,
        "tasks": rows,
        "project_level_tokens": {**general, "cost": float(general["cost"]), "credits": float(general["credits"])} if general else None,
        "by_model": [{"model_code": m, **v, "cost": float(v["cost"]), "credits": float(v["credits"])} for m, v in sorted(by_model.items())],
        "items": [item_out(it) for it in items],
        "by_category": [{"category": k, "label": CATEGORIES.get(k, k), "amount": float(v)} for k, v in sorted(by_category.items())],
        "planned": planned,
        "budget": {"amount": float(project.budget_try) if project.budget_try is not None else None, "note": project.budget_note,
                   "suggested": planned["total"]},
        "totals": {"labor": float(totals["labor"]), "labor_planned": float(totals["labor_planned"]), "token": float(totals["token"]),
                   "other": float(other), "actual": float(totals["labor"] + totals["token"] + other),
                   "unpriced_calls": totals["unpriced_calls"], "credits": float(totals["credits"]),
                   "budget_variance": (float(project.budget_try - (totals["labor"] + totals["token"] + other))
                                       if project.budget_try is not None else None)},
    }


def uuid_of(v):
    import uuid as _uuid

    return _uuid.UUID(v) if v else None


def item_out(it: ProjectCostItem) -> Dict[str, Any]:
    return {"id": str(it.id), "task_id": str(it.task_id) if it.task_id else None, "category": it.category,
            "category_label": CATEGORIES.get(it.category, it.category), "description": it.description, "quantity": float(it.quantity),
            "unit": it.unit, "unit_price_try": float(it.unit_price_try), "amount_try": float(it.amount_try), "incurred_on": it.incurred_on,
            "attachment_name": it.attachment_name, "has_attachment": bool(it.attachment_path), "created_at": it.created_at}


async def planned_costs(db: AsyncSession, project: Project, tasks, actors) -> Dict[str, Any]:
    """Plana göre tahmini maliyet: personel (günlük maliyet × planlanan gün) + token (simülasyon varsayımı × LLM fiyatı).
    Bütçe önerisi olarak kullanılır. Fiyatı veya günlük maliyeti olmayan kalemler eksik sayılır (missing)."""
    from app.services import pricing
    from app.services.project_planning import TOKENS_IN_PER_DAY, TOKENS_OUT_PER_DAY

    labor_total, token_total, missing_rate, missing_price = ZERO, ZERO, 0, 0
    for t in tasks:
        days = Decimal(str(t.estimated_effort or 1))
        a = actors.get(t.assignee_actor_id)
        if a and a.daily_cost_try is not None:
            labor_total += _d(a.daily_cost_try) * days
        elif a and a.actor_type == "HUMAN":
            missing_rate += 1
        if a and a.actor_type == "AI_AGENT":
            price = await pricing.price_at(db, a.preferred_model_id)
            if price:
                token_total += pricing.call_cost(price, int(TOKENS_IN_PER_DAY * days), int(TOKENS_OUT_PER_DAY * days))
            else:
                missing_price += 1
    return {"labor": float(labor_total.quantize(Decimal("0.01"))), "token": float(token_total.quantize(Decimal("0.01"))),
            "total": float((labor_total + token_total).quantize(Decimal("0.01"))),
            "missing_daily_cost": missing_rate, "missing_llm_price": missing_price}
