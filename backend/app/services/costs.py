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

from app.db.models import Actor, JobTitle, LLMCall, Project, ProjectCostItem, Task, Tenant

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
    if task.status == "CANCELLED":  # F112: iptal edilen adım "sürüyor"/"plan" sayılmaz
        if not task.started_at:
            return {"days": 0.0, "cost": ZERO, "basis": "CANCELLED", "rated": rate is not None}
        end = (task.completed_at or task.updated_at or datetime.now(timezone.utc)).date()
        days = workdays(task.started_at.date(), end)
        cost = (_d(rate) * Decimal(str(days))).quantize(Decimal("0.01")) if rate is not None else ZERO
        return {"days": float(days), "cost": cost, "basis": "CANCELLED", "rated": rate is not None}
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
        select(LLMCall.task_id, LLMCall.model_code, LLMCall.purpose, func.count(), func.sum(LLMCall.tokens_in), func.sum(LLMCall.tokens_out),
               func.sum(LLMCall.cost_try), func.count().filter(LLMCall.cost_try.is_(None)), func.sum(LLMCall.credits_cost), LLMCall.actor_id)
        .where(LLMCall.project_id == project.id, LLMCall.status == "SUCCESS")
        .group_by(LLMCall.task_id, LLMCall.model_code, LLMCall.purpose, LLMCall.actor_id))).all()
    from app.services import recai

    all_tiers = await recai.tiers(db)
    by_task: Dict[Any, Dict[str, Any]] = {}
    by_model: Dict[str, Dict[str, Any]] = {}  # #349: müşteriye RECAi adına göre
    actor_credits: Dict[Any, Dict[Any, Decimal]] = {}  # F115: adımda işi yapan / kontrol eden ayrımı
    for task_id, model, purpose, calls, t_in, t_out, cost, unpriced, credits, actor_id in token_rows:
        per = actor_credits.setdefault(task_id, {})
        per[actor_id] = per.get(actor_id, ZERO) + _d(credits)
        for bucket, key in ((by_task, task_id), (by_model, recai.public_name(model, all_tiers, purpose))):
            b = bucket.setdefault(key, {"calls": 0, "tokens_in": 0, "tokens_out": 0, "cost": ZERO, "unpriced_calls": 0, "credits": ZERO})
            b["calls"] += calls
            b["tokens_in"] += int(t_in or 0)
            b["tokens_out"] += int(t_out or 0)
            b["cost"] += _d(cost)
            b["unpriced_calls"] += unpriced
            b["credits"] += _d(credits)

    # #664: kredinin TL karşılığı (paket bazlı) ve insan eşdeğeri (ünvan referans maaşı × planlanan iş günü)
    from app.services import human_equivalent as he

    cfg = await he.settings(db)
    tenant = await db.get(Tenant, project.tenant_id)
    unit = await he.tenant_credit_unit(db, tenant) if tenant else None
    # F70/F76/F114: müşteriye gösterilen AI (token) maliyeti her yerde tek kaynaktan: kredi × paket kredi birim fiyatı.
    # LLM TL fiyatı RECDx'in iç maliyetidir (llm_cost olarak ayrı kalır); kredi birimi varken "fiyatsız" çağrı yoktur.
    if unit is not None:
        for bucket in (*by_task.values(), *by_model.values()):
            bucket["llm_cost"], bucket["cost"], bucket["unpriced_calls"] = bucket["cost"], _ai_try(bucket["credits"], unit), 0
    jt_ids = {t.job_title_id or (actors[t.assignee_actor_id].job_title_id if t.assignee_actor_id in actors else None) for t in tasks}
    titles = {j.id: j for j in (await db.execute(select(JobTitle).where(JobTitle.id.in_([i for i in jt_ids if i] or [project.id])))).scalars()}
    rows, totals = [], {"labor": ZERO, "labor_planned": ZERO, "token": ZERO, "unpriced_calls": 0, "credits": ZERO}
    he_tot = {"human_days": ZERO, "human_cost": ZERO}
    planned_credits = ZERO
    starts, ends = [], []
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
        human = he.human_for(titles.get(t.job_title_id or (assignee.job_title_id if assignee else None)), float(t.estimated_effort or 1), cfg)
        # F113: iptal edilen (hiç yapılmamış) adım insan eşdeğerine girmez; satırda "kapsam dışı" işaretlenir. AI'ın iptalden önce
        # harcadığı kredi ise gerçek harcamadır, AI tarafında kalır.
        in_scope = t.status != "CANCELLED"
        if in_scope:
            he_tot["human_days"] += Decimal(str(human["days"]))
            he_tot["human_cost"] += Decimal(str(human["cost"]))
            planned_credits += _d(t.estimated_credits)
        review_credits = sum((c for a, c in actor_credits.get(t.id, {}).items() if a and a != t.assignee_actor_id), ZERO)
        end = t.completed_at or t.submitted_at
        if t.started_at:
            starts.append(t.started_at)
            ends.append(end or datetime.now(timezone.utc))
        rows.append({"task_id": str(t.id), "title": t.title, "status": t.status, "order_index": t.order_index,
                     "assignee": assignee.display_name if assignee else None, "assignee_type": assignee.actor_type if assignee else None,
                     "labor": {**lab, "cost": float(lab["cost"])},
                     "tokens": {**tok, "cost": float(tok["cost"]), "credits": float(tok["credits"])},
                     "ai_credit_try": float((tok["credits"] * unit).quantize(Decimal("0.01"))) if unit is not None else None,
                     "ai_hours": round((end - t.started_at).total_seconds() / 3600, 2) if (t.started_at and end) else None,
                     "human": human, "in_scope": in_scope,
                     # F71: adımın plan kredisi (simülasyon) ve TL karşılığı; F115: kredinin kontrol personeline düşen kısmı
                     "estimated_credits": float(t.estimated_credits) if t.estimated_credits is not None else None,
                     "estimated_try": float(_ai_try(_d(t.estimated_credits), unit)) if (unit is not None and t.estimated_credits is not None) else None,
                     "review_credits": float(review_credits)})
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
    planned = await planned_costs(db, project, tasks, actors, unit)
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
                   # #664: müşteri gözüyle AI maliyeti kredi × paket kredi birim fiyatı (LLM TL fiyatı RECDx'in iç maliyetidir)
                   "other": float(other), "actual": float(totals["labor"] + totals["token"] + other),
                   "ai_cost_basis": "KREDI" if unit is not None else "LLM_FIYATI",
                   "unpriced_calls": totals["unpriced_calls"], "credits": float(totals["credits"]),
                   # F74: fark = bütçe − gerçekleşen (gerçekleşenle aynı kaynak)
                   "budget_variance": (float(project.budget_try - (totals["labor"] + totals["token"] + other))
                                       if project.budget_try is not None else None),
                   "planned_credits": float(planned_credits), "planned_ai_try": float(_ai_try(planned_credits, unit)) if unit is not None else None,
                   "effort_days_note": "Toplam efor: adımların planlanan iş günlerinin toplamı (adam-gün); takvim süresi paralel adımlarla daha kısadır.",
                   **_comparison(totals["credits"], unit, he_tot, starts, ends, cfg)},
    }


def _ai_try(credits: Decimal, unit: Decimal) -> Decimal:
    return (credits * unit).quantize(Decimal("0.01"))


def _comparison(credits: Decimal, unit: Optional[Decimal], he_tot: Dict[str, Decimal], starts, ends, cfg) -> Dict[str, Any]:
    """#664: AI ile insan karşılaştırması (müşteri gözü). AI maliyeti = kredi × paket kredi birim fiyatı."""
    ai_try = (credits * unit).quantize(Decimal("0.01")) if unit is not None else None
    cal_days = round((max(ends) - min(starts)).total_seconds() / 86400, 2) if starts else None
    return {"credit_unit_try": float(unit) if unit is not None else None, "ai_credit_try": float(ai_try) if ai_try is not None else None,
            "human_days": float(he_tot["human_days"]), "human_cost": float(he_tot["human_cost"].quantize(Decimal("0.01"))),
            "ai_calendar_days": cal_days,
            "saving": float((he_tot["human_cost"] - ai_try).quantize(Decimal("0.01"))) if ai_try is not None else None,
            "cost_basis_note": (f"İnsan eşdeğeri: ünvan referans aylık brüt maaşı × {cfg.get('employer_factor')} ÷ {cfg.get('work_days_month')} "
                                f"iş günü × planlanan gün. AI: kredi × paket kredi birim fiyatı.")}


def uuid_of(v):
    import uuid as _uuid

    return _uuid.UUID(v) if v else None


def item_out(it: ProjectCostItem) -> Dict[str, Any]:
    return {"id": str(it.id), "task_id": str(it.task_id) if it.task_id else None, "category": it.category,
            "category_label": CATEGORIES.get(it.category, it.category), "description": it.description, "quantity": float(it.quantity),
            "unit": it.unit, "unit_price_try": float(it.unit_price_try), "amount_try": float(it.amount_try), "incurred_on": it.incurred_on,
            "attachment_name": it.attachment_name, "has_attachment": bool(it.attachment_path), "created_at": it.created_at}


async def planned_costs(db: AsyncSession, project: Project, tasks, actors, unit: Optional[Decimal] = None) -> Dict[str, Any]:
    """Plana göre tahmini maliyet: personel (günlük maliyet × planlanan gün) + token (simülasyon varsayımı × LLM fiyatı).
    Bütçe önerisi olarak kullanılır. Fiyatı veya günlük maliyeti olmayan kalemler eksik sayılır (missing)."""
    from app.services import pricing
    from app.services.project_planning import TOKENS_IN_PER_DAY, TOKENS_OUT_PER_DAY

    labor_total, token_total, missing_rate, missing_price, credits = ZERO, ZERO, 0, 0, ZERO
    for t in tasks:
        if t.status == "CANCELLED":
            continue
        days = Decimal(str(t.estimated_effort or 1))
        a = actors.get(t.assignee_actor_id)
        if a and a.daily_cost_try is not None:
            labor_total += _d(a.daily_cost_try) * days
        elif a and a.actor_type == "HUMAN":
            missing_rate += 1
        if a and a.actor_type == "AI_AGENT" and unit is not None and t.estimated_credits is not None:
            # F71/F76: plan (öneri) AI tutarı simülasyonun kredi tahmini × paket kredi birim fiyatı
            credits += _d(t.estimated_credits)
            token_total += _ai_try(_d(t.estimated_credits), unit)
        elif a and a.actor_type == "AI_AGENT":
            price = await pricing.price_at(db, a.preferred_model_id)
            if price:
                token_total += pricing.call_cost(price, int(TOKENS_IN_PER_DAY * days), int(TOKENS_OUT_PER_DAY * days))
            else:
                missing_price += 1
    return {"labor": float(labor_total.quantize(Decimal("0.01"))), "token": float(token_total.quantize(Decimal("0.01"))),
            "total": float((labor_total + token_total).quantize(Decimal("0.01"))),
            "missing_daily_cost": missing_rate, "missing_llm_price": missing_price, "credits": float(credits)}
