"""
Proje planlama (ADIM 6.3) ve simülasyon (ADIM 6.4).

Plan (projects.plan): Beyin AI'nın önerdiği, yöneticinin düzenleyip onayladığı iş adımları.
  {"summary", "steps": [{key, title, description, acceptance_criteria, department, job_title, agent_id,
   estimated_days, depends_on: [key], priority}], "hire_suggestions": [{job_title, department, reason}],
   "risks": [...], "questions": [...], "model_code", "generated_at"}
Onayda adımlar görevlere (tasks) dönüşür; bağımlılıklar görev kimliklerine çevrilir; AI personel ekibe eklenir.

Simülasyon: iş günü takvimi (hafta sonu hariç), bağımlılık ve personel kapasitesi (bir personel aynı anda tek iş)
ile adım tarihleri, toplam süre, tahmini kredi ve riskler.
"""
import json
import logging
import re
import uuid
from datetime import date, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Actor, ChatMessage, Department, JobTitle, LLMModel, Project, Task, Tenant
from app.services import credits, knowledge, llm_gateway
from app.services import projects as psvc
from app.services.llm_gateway import LLMContext

logger = logging.getLogger("recorion.planning")

MAX_STEPS = 40
# Bir iş günü için tahmini model kullanımı (kredi tahmini; gerçek kullanım ölçülür)
TOKENS_IN_PER_DAY = 40_000
TOKENS_OUT_PER_DAY = 10_000


# ---------------------------------------------------------------- bağlam
async def _team_pool(db: AsyncSession, tenant_id: uuid.UUID) -> List[Dict[str, Any]]:
    agents = (await db.execute(select(Actor).where(Actor.tenant_id == tenant_id, Actor.actor_type == "AI_AGENT",
                                                   Actor.dismissed_at.is_(None), Actor.status != "DISABLED"))).scalars().all()
    titles = {t.id: t for t in (await db.execute(select(JobTitle).where(JobTitle.id.in_([a.job_title_id for a in agents if a.job_title_id] or [uuid.uuid4()])))).scalars()}
    depts = {d.id: d.name for d in (await db.execute(select(Department).where(Department.tenant_id == tenant_id))).scalars()}
    busy = dict((await db.execute(select(Task.assignee_actor_id, func.count()).join(Project, Project.id == Task.project_id).where(
        Project.tenant_id == tenant_id, Project.status.in_(("READY", "ACTIVE")), Task.status.notin_(("DONE", "CANCELLED")))
        .group_by(Task.assignee_actor_id))).all())
    return [{"agent_id": str(a.id), "name": a.display_name, "title": titles[a.job_title_id].title if a.job_title_id in titles else a.role,
             "department": depts.get(a.department_id), "open_tasks_elsewhere": busy.get(a.id, 0)} for a in agents]


async def _context(db: AsyncSession, project: Project) -> Dict[str, Any]:
    tenant = await db.get(Tenant, project.tenant_id)
    pool = await _team_pool(db, tenant.id)
    depts = [d.name for d in (await db.execute(select(Department).where(Department.tenant_id == tenant.id).order_by(Department.name))).scalars()]
    hits = await knowledge.retrieve(knowledge.Scope(tenant_id=tenant.id, project_id=project.id),
                                    (project.requirements or project.name)[:2000], limit=6, layers=["PROJECT", "GLOBAL"])
    return {"tenant": tenant, "pool": pool, "departments": depts, "knowledge": knowledge.format_context(hits, max_chars=5000)}


def _parse(text: str) -> Dict[str, Any]:
    text = text.strip()
    if "```" in text:
        text = text.split("```")[1].removeprefix("json").strip()
    return json.loads(text[text.find("{"): text.rfind("}") + 1])


# ---------------------------------------------------------------- doğrulama
def _pos(value) -> Optional[Dict[str, float]]:
    """Akış şemasındaki konum (ADIM 7.4)."""
    try:
        return {"x": round(float(value["x"]), 1), "y": round(float(value["y"]), 1)} if value else None
    except (KeyError, TypeError, ValueError):
        return None


def _rejections(value) -> int:
    try:
        return max(1, min(int(value), 5))
    except (TypeError, ValueError):
        return 3


def validate_plan(plan: Dict[str, Any], pool_ids: set, human_ids: Optional[set] = None) -> Dict[str, Any]:
    """Adımları temizler; geçersiz personel/bağımlılıkları düşürür; döngü varsa hata verir.
    human_ids: onaylayıcı olabilecek insan personel (verilmezse onaylayıcı alanı korunmaz)."""
    steps, keys = [], set()
    for i, s in enumerate((plan.get("steps") or [])[:MAX_STEPS], 1):
        title = str(s.get("title") or "").strip()[:255]
        if not title:
            continue
        key = str(s.get("key") or f"S{i}").strip()[:16] or f"S{i}"
        while key in keys:
            key = f"{key}_{i}"
        keys.add(key)
        try:
            days = float(s.get("estimated_days") or 1)
        except (TypeError, ValueError):
            days = 1.0
        agent = str(s.get("agent_id") or "") or None
        reviewer = str(s.get("reviewer_agent_id") or "") or None
        steps.append({
            "key": key, "title": title, "description": str(s.get("description") or "").strip()[:4000],
            "acceptance_criteria": str(s.get("acceptance_criteria") or "").strip()[:2000],
            "department": (str(s.get("department") or "").strip() or None), "job_title": (str(s.get("job_title") or "").strip() or None),
            "agent_id": agent if agent in pool_ids else None, "estimated_days": max(0.5, min(days, 60.0)),
            # Kontrol personeli (ADIM 7.2): havuzdan, işi yapan personelden farklı bir AI personel
            "reviewer_agent_id": reviewer if reviewer in pool_ids and reviewer != agent else None,
            # Akış ayarları (ADIM 7.4): onaylayıcı (boş: proje yöneticisi), onay gerekliliği, ret sınırı, şema konumu
            "approver_actor_id": (str(s.get("approver_actor_id")) if human_ids is not None and str(s.get("approver_actor_id") or "") in human_ids else None),
            "requires_approval": s.get("requires_approval") is not False,
            "max_rejections": _rejections(s.get("max_rejections", 3)),
            "pos": _pos(s.get("pos")),
            "depends_on": [str(d) for d in (s.get("depends_on") or [])],
            "priority": s.get("priority") if s.get("priority") in ("HIGH", "MEDIUM", "LOW") else "MEDIUM",
        })
    for s in steps:
        s["depends_on"] = [d for d in dict.fromkeys(s["depends_on"]) if d in keys and d != s["key"]]
    # Döngü kontrolü (iş akışı döngüsüz olmalı; ret/revizyon döngüleri adım özelliğidir)
    graph = {s["key"]: s["depends_on"] for s in steps}
    state: Dict[str, int] = {}

    def visit(k: str) -> None:
        if state.get(k) == 1:
            raise HTTPException(status_code=422, detail=f"İş adımlarında döngüsel bağımlılık var ({k}). Bir adım kendisine dolaylı olarak bağlı olamaz.")
        if state.get(k) == 2:
            return
        state[k] = 1
        for d in graph[k]:
            visit(d)
        state[k] = 2
    for k in graph:
        visit(k)
    hires = [{"job_title": str(h.get("job_title") or "").strip()[:128], "department": (str(h.get("department") or "").strip() or None),
              "reason": str(h.get("reason") or "").strip()[:500]} for h in (plan.get("hire_suggestions") or []) if h.get("job_title")]
    return {"summary": str(plan.get("summary") or "").strip()[:3000], "steps": steps, "hire_suggestions": hires[:10],
            "risks": [str(r)[:300] for r in (plan.get("risks") or [])][:10],
            "questions": [str(q)[:300] for q in (plan.get("questions") or [])][:8]}


# ---------------------------------------------------------------- Beyin AI önerisi
async def suggest_plan(db: AsyncSession, project: Project, feedback: Optional[str] = None) -> Dict[str, Any]:
    ctx = await _context(db, project)
    pool_text = "\n".join(f"- agent_id={p['agent_id']} | {p['name']} | {p['title']} | {p['department'] or '-'} | başka projelerde açık iş: {p['open_tasks_elsewhere']}"
                          for p in ctx["pool"]) or "- (şirkette henüz AI personel yok)"
    current = json.dumps({"steps": (project.plan or {}).get("steps", [])}, ensure_ascii=False)[:6000] if project.plan else "yok"
    prompt = f"""Sen {ctx['tenant'].name} şirketinin Beyin AI'sısın ve proje yöneticisiyle birlikte bir {'Case' if project.kind == 'CASE' else 'proje'} planlıyorsun.
Görevin: isterlere göre uygulanabilir iş adımlarını çıkarmak ve her adım için departman + unvan bazında şirketin AI personel
havuzundan en uygun personeli önermek. Havuzda uygun personel yoksa agent_id boş bırak ve hire_suggestions'a gereken unvanı yaz.
Bir personele aynı anda çok iş yığma; başka projelerdeki açık işleri dikkate al. Bağımlılıklar döngüsüz olmalı.
Kalite gerektiren adımlara, işi yapandan farklı ve konuya uygun bir kontrol personeli (reviewer_agent_id) öner.
Bilmediğin bilgiyi uydurma; eksikleri "questions" içinde yöneticiye sor.

# Proje
Adı: {project.name}
Açıklama: {(project.description or '-')[:2000]}
İsterler:
{(project.requirements or '-')[:8000]}
Hedef tarihler: {project.start_date or 'belirlenmedi'} - {project.end_date or 'belirlenmedi'}

# Şirketin departmanları
{', '.join(ctx['departments']) or '-'}

# AI personel havuzu
{pool_text}
{ctx['knowledge']}

# Mevcut plan taslağı
{current}

# Yöneticinin geri bildirimi
{(feedback or 'yok')[:4000]}

Sadece şu JSON'u döndür:
{{"summary": "planın 3-5 cümlelik özeti",
  "steps": [{{"key": "S1", "title": "adım adı", "description": "ne yapılacak", "acceptance_criteria": "tamam sayılma ölçütü",
             "department": "departman", "job_title": "gereken unvan", "agent_id": "havuzdan agent_id veya boş",
             "reviewer_agent_id": "çıktıyı kontrol edecek, işi yapandan farklı havuz agent_id'si veya boş",
             "estimated_days": 2, "depends_on": ["önceki adım key"], "priority": "HIGH|MEDIUM|LOW"}}],
  "hire_suggestions": [{{"job_title": "unvan", "department": "departman", "reason": "neden gerekli"}}],
  "risks": ["risk"], "questions": ["yöneticiye soru"]}}"""
    llm_ctx = LLMContext(tenant_id=project.tenant_id, purpose="BRAIN", project_id=project.id)
    # Beyin AI modeli meşgul/yanıtsızsa paketteki yedek modelle önerir
    result = await llm_gateway.chat(llm_ctx, [{"role": "user", "content": prompt}], temperature=0.3, max_tokens=6000, timeout=300, fallback=True)
    try:
        plan = validate_plan(_parse(result.content), {p["agent_id"] for p in ctx["pool"]})
    except (ValueError, KeyError) as exc:
        raise HTTPException(status_code=502, detail="Beyin AI geçerli bir plan üretemedi; lütfen tekrar deneyin.") from exc
    if not plan["steps"]:
        raise HTTPException(status_code=502, detail="Beyin AI iş adımı üretemedi; isterleri biraz daha ayrıntılandırıp tekrar deneyin.")
    plan.update({"model_code": result.model_code, "generated_at": psvc.now().isoformat(), "approved": False})
    await _attach_hire_matches(db, project, plan)
    project.plan = plan
    project.planning_approved_at = None
    if project.status == "DRAFT":
        project.status = "PLANNING"
    await db.commit()
    return plan


async def _attach_hire_matches(db: AsyncSession, project: Project, plan: Dict[str, Any]) -> None:
    """İşe alım önerilerini katalog unvanlarıyla eşleştirir (işe alım sihirbazında doğrudan seçilebilsin)."""
    tenant = await db.get(Tenant, project.tenant_id)
    sectors = [str(s) for s in (tenant.sectors or [])]
    for h in plan["hire_suggestions"]:
        words = [w for w in re.split(r"\W+", h["job_title"]) if len(w) > 3][:3]
        stmt = select(JobTitle).where(JobTitle.tenant_id.is_(None), JobTitle.is_active,
                                      (JobTitle.sector_code.is_(None)) | (JobTitle.sector_code.in_(sectors or ["-"])))
        for w in words:
            stmt = stmt.where(JobTitle.title.ilike(f"%{w}%"))
        match = (await db.execute(stmt.limit(1))).scalars().first()
        h["catalog_title_id"] = str(match.id) if match else None
        h["catalog_title"] = match.title if match else None


# ---------------------------------------------------------------- planlama sohbeti
async def plan_chat(db: AsyncSession, project: Project, actor_id: uuid.UUID, content: str) -> Dict[str, Any]:
    ctx = await _context(db, project)
    history = list(reversed((await db.execute(select(ChatMessage).where(
        ChatMessage.project_id == project.id, ChatMessage.message_type == "PLAN_CHAT")
        .order_by(ChatMessage.created_at.desc()).limit(12))).scalars().all()))
    plan_text = "\n".join(f"{s['key']}. {s['title']} ({s['estimated_days']} gün, {s.get('job_title') or '-'})"
                          for s in (project.plan or {}).get("steps", [])) or "henüz plan yok"
    system = f"""Sen {ctx['tenant'].name} şirketinin Beyin AI'sısın. Proje yöneticisiyle "{project.name}" projesini planlıyorsun.
İsterleri netleştir, eksikleri sor, iş adımları ve AI personel seçimi hakkında öneri yap. Kısa ve uygulanabilir yanıt ver.
Planı değiştirmek gerekiyorsa yöneticiye "Planı bu konuşmaya göre güncelle" butonunu kullanmasını öner.

İsterler: {(project.requirements or '-')[:5000]}
Mevcut plan: {plan_text}
AI personel: {', '.join(f"{p['name']} ({p['title']})" for p in ctx['pool']) or 'yok'}
{ctx['knowledge']}"""
    messages = [{"role": "system", "content": system}] + [{"role": m.role, "content": m.content} for m in history]
    messages.append({"role": "user", "content": content})
    result = await llm_gateway.chat(LLMContext(tenant_id=project.tenant_id, purpose="BRAIN", project_id=project.id),
                                    messages, temperature=0.4, max_tokens=2500, timeout=150)
    for role, text in (("user", content), ("assistant", result.content.strip())):
        db.add(ChatMessage(tenant_id=project.tenant_id, project_id=project.id, sender_actor_id=actor_id, role=role,
                           content=text, message_type="PLAN_CHAT"))
    await db.commit()
    return {"content": result.content.strip(), "model_code": result.model_code, "credits": result.credits}


async def plan_feedback_from_chat(db: AsyncSession, project: Project) -> str:
    rows = (await db.execute(select(ChatMessage).where(ChatMessage.project_id == project.id, ChatMessage.message_type == "PLAN_CHAT")
                             .order_by(ChatMessage.created_at.desc()).limit(12))).scalars().all()
    return "\n".join(f"{'Yönetici' if m.role == 'user' else 'Beyin AI'}: {m.content[:800]}" for m in reversed(rows))


# ---------------------------------------------------------------- onay
async def approve_plan(db: AsyncSession, project: Project, actor_id: uuid.UUID) -> List[Task]:
    if project.status not in ("DRAFT", "PLANNING"):
        raise HTTPException(status_code=409, detail="Plan yalnızca planlama aşamasında onaylanabilir.")
    steps = (project.plan or {}).get("steps") or []
    if not steps:
        raise HTTPException(status_code=409, detail="Onaylanacak iş adımı yok.")
    # Önceki onaydan kalan, henüz başlamamış adımlar yeniden oluşturulur
    for t in (await db.execute(select(Task).where(Task.project_id == project.id))).scalars():
        if t.status not in ("BACKLOG", "READY"):
            raise HTTPException(status_code=409, detail="Başlamış iş adımları olan projede plan yeniden onaylanamaz.")
        await db.delete(t)
    await db.flush()
    depts = {d.name.lower(): d.id for d in (await db.execute(select(Department).where(Department.tenant_id == project.tenant_id))).scalars()}
    key_to_task: Dict[str, Task] = {}
    for i, s in enumerate(steps, 1):
        agent = await db.get(Actor, uuid.UUID(s["agent_id"])) if s.get("agent_id") else None
        if agent and agent.tenant_id != project.tenant_id:
            agent = None
        approver = await db.get(Actor, uuid.UUID(s["approver_actor_id"])) if s.get("approver_actor_id") else None
        if approver and (approver.tenant_id != project.tenant_id or approver.actor_type != "HUMAN"):
            approver = None
        reviewer = await db.get(Actor, uuid.UUID(s["reviewer_agent_id"])) if s.get("reviewer_agent_id") else None
        if reviewer and (reviewer.tenant_id != project.tenant_id or (agent and reviewer.id == agent.id)):
            reviewer = None
        task = Task(project_id=project.id, title=s["title"], description=s.get("description"),
                    acceptance_criteria=s.get("acceptance_criteria"), priority=s.get("priority", "MEDIUM"),
                    assignee_actor_id=agent.id if agent else None, estimated_effort=s.get("estimated_days", 1),
                    department_id=depts.get((s.get("department") or "").lower()), job_title_id=agent.job_title_id if agent else None,
                    order_index=i, status="BACKLOG", depends_on=[], reviewer_actor_id=reviewer.id if reviewer else None,
                    approver_actor_id=approver.id if approver else None, requires_approval=s.get("requires_approval", True) is not False,
                    max_rejections=_rejections(s.get("max_rejections", 3)))
        db.add(task)
        key_to_task[s["key"]] = task
        for member in (agent, reviewer, approver):
            if member:
                await psvc.set_member(db, project, member, None, actor_id)
    await db.flush()
    for s in steps:
        key_to_task[s["key"]].depends_on = [str(key_to_task[d].id) for d in s.get("depends_on", []) if d in key_to_task]
    project.plan = {**project.plan, "approved": True}
    project.planning_approved_at = psvc.now()
    if project.status == "DRAFT":
        project.status = "PLANNING"
    await db.commit()
    return list(key_to_task.values())


# ---------------------------------------------------------------- simülasyon
def _add_workdays(d: date, days: float) -> date:
    """d gününden başlayıp 'days' iş günü süren işin son günü (hafta sonu hariç)."""
    while d.weekday() >= 5:
        d += timedelta(days=1)
    remaining = max(1, round(days + 0.49))
    while remaining > 1:
        d += timedelta(days=1)
        if d.weekday() < 5:
            remaining -= 1
    return d


def _next_workday(d: date) -> date:
    d += timedelta(days=1)
    while d.weekday() >= 5:
        d += timedelta(days=1)
    return d


def workdays_between(a: date, b: date) -> int:
    n, d = 0, a
    while d <= b:
        n += d.weekday() < 5
        d += timedelta(days=1)
    return n


async def simulate(db: AsyncSession, project: Project, start: Optional[date] = None) -> Dict[str, Any]:
    tasks = (await db.execute(select(Task).where(Task.project_id == project.id).order_by(Task.order_index))).scalars().all()
    if not tasks:
        raise HTTPException(status_code=409, detail="Simülasyon için önce iş adımlarını onaylayın.")
    start = start or project.start_date or date.today()
    by_id = {str(t.id): t for t in tasks}
    agent_free: Dict[str, date] = {}
    finish: Dict[str, date] = {}
    order: List[Task] = []
    pending = list(tasks)
    while pending:  # bağımlılık sırasıyla (topolojik) yerleştir
        ready = [t for t in pending if all(d in finish or d not in by_id for d in (t.depends_on or []))]
        if not ready:
            raise HTTPException(status_code=422, detail="İş adımlarında döngüsel bağımlılık var.")
        for t in ready:
            earliest = start
            for d in t.depends_on or []:
                if d in finish:
                    earliest = max(earliest, _next_workday(finish[d]))
            who = str(t.assignee_actor_id) if t.assignee_actor_id else None
            if who and who in agent_free:
                earliest = max(earliest, _next_workday(agent_free[who]))
            while earliest.weekday() >= 5:
                earliest += timedelta(days=1)
            end = _add_workdays(earliest, float(t.estimated_effort or 1))
            t.start_date, t.due_date = earliest, end
            finish[str(t.id)] = end
            if who:
                agent_free[who] = end
            order.append(t)
            pending.remove(t)

    # Kredi tahmini: AI personelin model katsayısıyla
    agents = {a.id: a for a in (await db.execute(select(Actor).where(Actor.id.in_([t.assignee_actor_id for t in tasks if t.assignee_actor_id] or [uuid.uuid4()])))).scalars()}
    model_coef = {m.id: m.effort_coefficient for m in (await db.execute(select(LLMModel))).scalars()}
    total_credits = Decimal(0)
    for t in tasks:
        agent = agents.get(t.assignee_actor_id)
        coef = model_coef.get(agent.preferred_model_id, 1) if agent and agent.actor_type == "AI_AGENT" else 0
        days = Decimal(str(t.estimated_effort or 1))
        c = credits.credit_cost(coef, int(TOKENS_IN_PER_DAY * days), int(TOKENS_OUT_PER_DAY * days)) if coef else Decimal(0)
        t.estimated_credits = c
        total_credits += c

    tenant = await db.get(Tenant, project.tenant_id)
    end = max(finish.values())
    risks = []
    unassigned = [t.title for t in tasks if not t.assignee_actor_id]
    if unassigned:
        risks.append({"level": "high", "text": f"{len(unassigned)} iş adımına personel atanmamış: {', '.join(unassigned[:4])}."})
    if project.end_date and end > project.end_date:
        late = workdays_between(project.end_date, end) - 1
        risks.append({"level": "high", "text": f"Tahmini bitiş ({end.isoformat()}) hedef tarihten {late} iş günü sonra."})
    if tenant.slug != "recdx_hq":
        await credits.ensure_period_grant(db, tenant)
        summary = await credits.summary(db, tenant)
        if total_credits > summary.balance:
            risks.append({"level": "high", "text": f"Tahmini kredi ({float(total_credits):,.0f}) kalan krediden ({float(summary.balance):,.0f}) fazla."})
        elif summary.monthly_grant and total_credits > summary.monthly_grant * Decimal("0.5"):
            risks.append({"level": "medium", "text": "Proje aylık kredinizin yarısından fazlasını kullanabilir."})
    load: Dict[Any, int] = {}
    for t in tasks:
        if t.assignee_actor_id:
            load[t.assignee_actor_id] = load.get(t.assignee_actor_id, 0) + 1
    if tasks and load and max(load.values()) > max(3, len(tasks) * 0.6):
        heavy = agents.get(max(load, key=load.get))
        risks.append({"level": "medium", "text": f"İşlerin çoğu tek personelde ({heavy.display_name if heavy else '-'}); süre uzayabilir."})
    if (project.plan or {}).get("hire_suggestions"):
        risks.append({"level": "medium", "text": "Beyin AI işe alınması gereken unvan(lar) önerdi; ekip eksik olabilir."})

    sim = {"start_date": start.isoformat(), "end_date": end.isoformat(), "workdays": workdays_between(start, end),
           "estimated_credits": float(total_credits), "task_count": len(tasks), "risks": risks,
           "simulated_at": psvc.now().isoformat(),
           "timeline": [{"task_id": str(t.id), "title": t.title, "start": t.start_date.isoformat(), "end": t.due_date.isoformat(),
                         "assignee": agents[t.assignee_actor_id].display_name if t.assignee_actor_id in agents else None,
                         "credits": float(t.estimated_credits or 0)} for t in order]}
    project.simulation = sim
    if not project.start_date:
        project.start_date = start
    await db.commit()
    return sim
