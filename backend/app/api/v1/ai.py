"""
Yapay zeka kullanımı: kredi durumu, platform model ayarları, Beyin AI ve Süper Yönetici asistanı.

KVKK
- Kredi ve kullanım ekranları yalnızca ölçüm verisi gösterir (model, amaç, token, kredi); içerik yoktur.
- Beyin AI şirket içeriğidir (manifesto, hafıza, sohbet): yalnızca şirketin kendi kullanıcıları erişir.
- Süper Yönetici asistanı yalnızca yönetim ve toplu veriyle çalışır; müşteri içeriğine erişmez.
"""
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import CurrentUser, get_current_user, get_hq_tenant_id
from app.db.models import (
    Actor, ChatMessage, CreditLedgerEntry, Department, JobTitle, LLMCall, LLMModel, Plan, SystemSetting,
    Tenant, TenantLead,
)
from app.db.session import get_db
from app.services import credits, llm_gateway
from app.services.llm_gateway import CHAT_TYPES, HQ_SLUG, LLMContext, ModelNotAllowed

router = APIRouter(tags=["AI & Kredi"])

HISTORY_TURNS = 10  # modele gönderilen önceki mesaj sayısı


async def _get_tenant(db: AsyncSession, tenant_id: uuid.UUID) -> Tenant:
    tenant = await db.get(Tenant, tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Şirket bulunamadı.")
    return tenant


def _f(value) -> float:
    return float(value or 0)


# ---------------------------------------------------------------- kredi durumu
@router.get("/company/{tenant_id}/credits")
async def company_credits(tenant_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Bu dönemin kredi özeti ve model / AI personel / işlem türü kırılımı."""
    tenant = await _get_tenant(db, tenant_id)
    unlimited = tenant.slug == HQ_SLUG
    if not unlimited:
        await credits.ensure_period_grant(db, tenant)
    summary = await credits.summary(db, tenant, unlimited=unlimited)

    start = datetime.strptime(summary.period + "-01", "%Y-%m-%d").replace(tzinfo=credits.TZ)
    period_calls = (LLMCall.tenant_id == tenant.id, LLMCall.created_at >= start)

    async def breakdown(column):
        rows = await db.execute(
            select(column, func.count(), func.coalesce(func.sum(LLMCall.tokens_in), 0),
                   func.coalesce(func.sum(LLMCall.tokens_out), 0), func.coalesce(func.sum(LLMCall.credits_cost), 0))
            .where(*period_calls, LLMCall.status == "SUCCESS").group_by(column)
            .order_by(desc(func.coalesce(func.sum(LLMCall.credits_cost), 0)))
        )
        return [{"key": k, "calls": c, "tokens_in": int(ti), "tokens_out": int(to), "credits": _f(cr)} for k, c, ti, to, cr in rows]

    by_actor = await breakdown(LLMCall.actor_id)
    names = {a.id: a.display_name for a in (await db.execute(
        select(Actor).where(Actor.id.in_([r["key"] for r in by_actor if r["key"]])))).scalars()}
    for row in by_actor:
        row["name"] = names.get(row["key"], "Silinmiş personel") if row["key"] else "Şirket geneli"
        row["key"] = str(row["key"]) if row["key"] else None

    recent = (await db.execute(select(LLMCall).where(LLMCall.tenant_id == tenant.id)
                               .order_by(LLMCall.created_at.desc()).limit(20))).scalars().all()
    ledger = (await db.execute(select(CreditLedgerEntry).where(CreditLedgerEntry.tenant_id == tenant.id,
                                                               CreditLedgerEntry.entry_type != "USAGE")
                               .order_by(CreditLedgerEntry.created_at.desc()).limit(20))).scalars().all()
    failed = (await db.execute(select(func.count()).where(*period_calls, LLMCall.status == "FAILED"))).scalar()
    return {
        "summary": summary.as_dict(),
        "by_model": await breakdown(LLMCall.model_code),
        "by_purpose": await breakdown(LLMCall.purpose),
        "by_actor": by_actor,
        "failed_calls": failed,
        "recent_calls": [{
            "created_at": c.created_at, "model_code": c.model_code, "purpose": c.purpose,
            "actor_name": names.get(c.actor_id) if c.actor_id else None, "tokens_in": c.tokens_in,
            "tokens_out": c.tokens_out, "credits": _f(c.credits_cost), "status": c.status, "latency_ms": c.latency_ms,
        } for c in recent],
        "ledger": [{"created_at": e.created_at, "entry_type": e.entry_type, "amount": _f(e.amount),
                    "period": e.period, "note": e.note} for e in ledger],
    }


class TopupPayload(BaseModel):
    amount: Decimal = Field(gt=0, le=10_000_000)
    note: Optional[str] = Field(default=None, max_length=200)


@router.post("/tenants/{tenant_id}/credits/topup")
async def topup_credits(tenant_id: uuid.UUID, payload: TopupPayload,
                        current: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Süper Admin: şirkete ek kredi yükler (ek krediler dönem sonunda silinmez)."""
    tenant = await _get_tenant(db, tenant_id)
    if tenant.slug == HQ_SLUG:
        raise HTTPException(status_code=400, detail="RECDx ana şirketinin kullanımı sınırsızdır; kredi yüklenmez.")
    await credits.ensure_period_grant(db, tenant)
    await credits.topup(db, tenant, payload.amount, current.actor_id, (payload.note or "").strip())
    return {"success": True, "summary": (await credits.summary(db, tenant)).as_dict()}


@router.get("/system/llm/usage")
async def platform_usage(db: AsyncSession = Depends(get_db)):
    """Süper Admin: bu dönem şirket ve model bazında kullanım, EVREN maliyeti ve kalan EVREN kredisi."""
    period = credits.current_period()
    start = datetime.strptime(period + "-01", "%Y-%m-%d").replace(tzinfo=credits.TZ)
    agg = (func.count(), func.coalesce(func.sum(LLMCall.tokens_in), 0), func.coalesce(func.sum(LLMCall.tokens_out), 0),
           func.coalesce(func.sum(LLMCall.credits_cost), 0), func.coalesce(func.sum(LLMCall.evren_credits), 0))

    def row(key, c, ti, to, cr, ev):
        return {"key": key, "calls": c, "tokens_in": int(ti), "tokens_out": int(to), "credits": _f(cr), "evren_credits": _f(ev)}

    tenants = {t.id: t for t in (await db.execute(select(Tenant))).scalars()}
    by_tenant = []
    for tid, *vals in await db.execute(select(LLMCall.tenant_id, *agg).where(LLMCall.created_at >= start,
                                                                              LLMCall.status == "SUCCESS").group_by(LLMCall.tenant_id)):
        item = row(str(tid) if tid else None, *vals)
        item["name"] = tenants[tid].name if tid in tenants else "Silinmiş şirket"
        item["is_platform"] = tid in tenants and tenants[tid].slug == HQ_SLUG
        by_tenant.append(item)
    by_tenant.sort(key=lambda r: r["credits"], reverse=True)
    by_model = [row(k, *v) for k, *v in await db.execute(
        select(LLMCall.model_code, *agg).where(LLMCall.created_at >= start, LLMCall.status == "SUCCESS").group_by(LLMCall.model_code))]
    by_model.sort(key=lambda r: r["calls"], reverse=True)
    failed = (await db.execute(select(func.count()).where(LLMCall.created_at >= start, LLMCall.status == "FAILED"))).scalar()
    last = (await db.execute(select(LLMCall.evren_balance_after, LLMCall.created_at).where(LLMCall.evren_balance_after.isnot(None))
                             .order_by(LLMCall.created_at.desc()).limit(1))).first()
    return {
        "period": period, "by_tenant": by_tenant, "by_model": by_model, "failed_calls": failed,
        "evren_balance": {"credits_remaining": _f(last[0]), "as_of": last[1]} if last else None,
    }


# ---------------------------------------------------------------- platform model ayarları
MODEL_SETTINGS = {
    "model.default.chat": ("Varsayılan sohbet modeli", CHAT_TYPES),
    "model.default.brain": ("Varsayılan Beyin AI modeli", CHAT_TYPES),
    "model.platform_assistant": ("Süper Yönetici asistanı modeli", CHAT_TYPES),
    "default_manifesto_model": ("Manifesto, rol promptu ve ünvan inceleme modeli", CHAT_TYPES),
    "model.default.embedding": ("Hafıza vektörleme modeli", {"EMBEDDING"}),
    "model.default.rerank": ("Hafıza yeniden sıralama modeli", {"RERANKER"}),
}


@router.get("/system/settings/models")
async def get_model_settings(db: AsyncSession = Depends(get_db)):
    values = {s.key: s.value for s in (await db.execute(select(SystemSetting).where(SystemSetting.key.in_(MODEL_SETTINGS)))).scalars()}
    return [{"key": k, "label": label, "model_types": sorted(types), "model_code": values.get(k)}
            for k, (label, types) in MODEL_SETTINGS.items()]


class ModelSettingsPayload(BaseModel):
    settings: Dict[str, str]


@router.put("/system/settings/models")
async def put_model_settings(payload: ModelSettingsPayload, db: AsyncSession = Depends(get_db)):
    for key, code in payload.settings.items():
        if key not in MODEL_SETTINGS:
            raise HTTPException(status_code=400, detail=f"Bilinmeyen ayar: {key}")
        label, types = MODEL_SETTINGS[key]
        model = (await db.execute(select(LLMModel).where(func.lower(LLMModel.model_code) == code.strip().lower()))).scalar_one_or_none()
        if not model or model.status != "ACTIVE":
            raise HTTPException(status_code=400, detail=f"{label}: '{code}' aktif bir model değil.")
        if model.model_type not in types:
            raise HTTPException(status_code=400, detail=f"{label}: '{code}' bu amaç için uygun bir model türü değil ({model.model_type}).")
        setting = await db.get(SystemSetting, key)
        if setting:
            setting.value = model.model_code
        else:
            db.add(SystemSetting(key=key, value=model.model_code, description=label))
    await db.commit()
    return await get_model_settings(db)


# ---------------------------------------------------------------- Beyin AI
async def _chat_models_for(db: AsyncSession, tenant: Tenant) -> List[LLMModel]:
    allowed = await llm_gateway.allowed_model_codes(db, tenant)
    models = (await db.execute(select(LLMModel).where(LLMModel.status == "ACTIVE", LLMModel.model_type.in_(CHAT_TYPES))
                               .order_by(LLMModel.model_code))).scalars().all()
    return [m for m in models if allowed is None or m.model_code.lower() in allowed]


@router.get("/company/{tenant_id}/brain/settings")
async def get_brain_settings(tenant_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    tenant = await _get_tenant(db, tenant_id)
    default = await db.get(SystemSetting, "model.default.brain")
    return {
        "brain_model_code": tenant.brain_model_code,
        "platform_default": default.value if default else None,
        "available_models": [{"model_code": m.model_code, "display_name": m.display_name, "model_type": m.model_type,
                              "effort_coefficient": _f(m.effort_coefficient)} for m in await _chat_models_for(db, tenant)],
    }


class BrainSettingsPayload(BaseModel):
    brain_model_code: Optional[str] = None  # boş: platform varsayılanı


@router.put("/company/{tenant_id}/brain/settings")
async def put_brain_settings(tenant_id: uuid.UUID, payload: BrainSettingsPayload, db: AsyncSession = Depends(get_db)):
    tenant = await _get_tenant(db, tenant_id)
    code = (payload.brain_model_code or "").strip().lower() or None
    if code and code not in {m.model_code.lower() for m in await _chat_models_for(db, tenant)}:
        raise ModelNotAllowed(f"'{code}' modeli Beyin AI için kullanılamaz veya şirketinizin paketinde yer almıyor.")
    tenant.brain_model_code = code
    await db.commit()
    return await get_brain_settings(tenant_id, db)


class ChatPayload(BaseModel):
    content: str = Field(min_length=1, max_length=8000)


def _message_out(m: ChatMessage) -> dict:
    created = m.created_at.replace(tzinfo=timezone.utc) if m.created_at and m.created_at.tzinfo is None else m.created_at
    return {"id": str(m.id), "role": m.role, "content": m.content, "created_at": created, "tokens": m.tokens}


async def _history(db: AsyncSession, tenant_id: uuid.UUID, actor_id: uuid.UUID, message_type: str, limit: int) -> List[ChatMessage]:
    rows = (await db.execute(select(ChatMessage).where(
        ChatMessage.tenant_id == tenant_id, ChatMessage.sender_actor_id == actor_id, ChatMessage.message_type == message_type,
    ).order_by(ChatMessage.created_at.desc()).limit(limit))).scalars().all()
    return list(reversed(rows))


async def _converse(db: AsyncSession, ctx: LLMContext, tenant_id: uuid.UUID, actor_id: uuid.UUID, message_type: str,
                    system_prompt: str, content: str) -> dict:
    """Önceki konuşmayla birlikte modeli çağırır; başarılı olursa soru ve cevabı kaydeder."""
    previous = await _history(db, tenant_id, actor_id, message_type, HISTORY_TURNS)
    messages = [{"role": "system", "content": system_prompt}]
    messages += [{"role": m.role, "content": m.content} for m in previous]
    messages.append({"role": "user", "content": content})
    result = await llm_gateway.chat(ctx, messages, temperature=0.4, max_tokens=4096, timeout=120)

    now = datetime.utcnow()
    question = ChatMessage(tenant_id=tenant_id, sender_actor_id=actor_id, role="user", content=content,
                           message_type=message_type, is_private=True, tokens=result.tokens_in, created_at=now)
    answer = ChatMessage(tenant_id=tenant_id, sender_actor_id=actor_id, role="assistant", content=result.content.strip(),
                         message_type=message_type, is_private=True, tokens=result.tokens_out,
                         created_at=now.replace(microsecond=min(now.microsecond + 1, 999999)))
    db.add_all([question, answer])
    await db.commit()
    return {"message": _message_out(answer), "model_code": result.model_code, "credits": result.credits}


async def _brain_prompt(db: AsyncSession, tenant: Tenant, query: str) -> str:
    from app.services.collective_memory import collective_memory

    departments = (await db.execute(select(Department).where(Department.tenant_id == tenant.id).order_by(Department.name))).scalars().all()
    titles = (await db.execute(select(JobTitle).where(JobTitle.tenant_id == tenant.id).order_by(JobTitle.title))).scalars().all()
    agents = (await db.execute(select(Actor).where(Actor.tenant_id == tenant.id, Actor.actor_type == "AI_AGENT",
                                                   Actor.dismissed_at.is_(None)).order_by(Actor.display_name))).scalars().all()
    dept_names = {d.id: d.name for d in departments}
    title_names = {t.id: t.title for t in titles}
    memories = await collective_memory.search_memory(str(tenant.id), query, limit=5)

    def lines(items):
        return "\n".join(f"- {i}" for i in items) or "- (henüz tanımlı değil)"

    return f"""Sen {tenant.name} şirketinin Beyin AI'sısın: şirketin organizatör yapay zekasısın.
Görevin şirket yöneticilerine ve çalışanlarına yardımcı olmak: işleri planlamak, hangi AI personelin hangi işe uygun
olduğunu önermek, eksik departman veya ünvanları fark etmek, kurum hafızasındaki bilgileri kullanarak yanıt vermek.
Bilmediğin bir şeyi uydurma; bilgi eksikse bunu söyle ve neye ihtiyaç olduğunu belirt. Yanıtların Türkçe, açık ve
uygulanabilir olsun; tablo kullanma, gerekirse başlık, kısa maddeler ve **kalın** vurgu kullan.

# Kurumsal manifesto
{(tenant.sector_manifesto or "(manifesto henüz yazılmadı)")[:6000]}

# Departmanlar
{lines(d.name for d in departments)}

# Ünvanlar
{lines(f"{t.title}" + (f" ({dept_names[t.department_id]})" if t.department_id in dept_names else "") for t in titles)}

# AI personel
{lines(f"{a.display_name} - {title_names.get(a.job_title_id, a.role)}" + (f", {dept_names[a.department_id]}" if a.department_id in dept_names else "") + f" [{a.status}]" for a in agents)}

# Kurum hafızasından ilgili bilgiler
{lines(m["content"][:800] for m in memories)}
"""


@router.post("/company/{tenant_id}/brain/chat")
async def brain_chat(tenant_id: uuid.UUID, payload: ChatPayload,
                     current: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    tenant = await _get_tenant(db, tenant_id)
    system_prompt = await _brain_prompt(db, tenant, payload.content)
    return await _converse(db, LLMContext(tenant_id=tenant.id, purpose="BRAIN"), tenant.id, current.actor_id,
                           "BRAIN", system_prompt, payload.content.strip())


@router.get("/company/{tenant_id}/brain/history")
async def brain_history(tenant_id: uuid.UUID, limit: int = Query(50, ge=1, le=200),
                        current: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return [_message_out(m) for m in await _history(db, tenant_id, current.actor_id, "BRAIN", limit)]


# ---------------------------------------------------------------- Süper Yönetici asistanı
async def _platform_prompt(db: AsyncSession) -> str:
    """Yalnızca yönetim ve toplu veri: şirket, paket, başvuru ve kredi bilgisi. Müşteri içeriği yoktur."""
    plans = {p.id: p for p in (await db.execute(select(Plan))).scalars()}
    tenants = (await db.execute(select(Tenant).order_by(Tenant.created_at.desc()).limit(60))).scalars().all()
    counts = dict((await db.execute(select(Actor.tenant_id, func.count()).where(Actor.dismissed_at.is_(None))
                                    .group_by(Actor.tenant_id))).all())
    agent_counts = dict((await db.execute(select(Actor.tenant_id, func.count()).where(
        Actor.actor_type == "AI_AGENT", Actor.dismissed_at.is_(None)).group_by(Actor.tenant_id))).all())
    leads = dict((await db.execute(select(TenantLead.status, func.count()).group_by(TenantLead.status))).all())
    period = credits.current_period()
    used = dict((await db.execute(select(CreditLedgerEntry.tenant_id, func.sum(CreditLedgerEntry.amount)).where(
        CreditLedgerEntry.period == period, CreditLedgerEntry.entry_type == "USAGE").group_by(CreditLedgerEntry.tenant_id))).all())
    models = (await db.execute(select(LLMModel).where(LLMModel.status == "ACTIVE").order_by(LLMModel.model_type))).scalars().all()

    rows = []
    for t in tenants:
        plan = plans.get(t.plan_id)
        expiry = t.package_expiry_date.date().isoformat() if t.package_expiry_date else "-"
        owner = " (RECDx ana şirketi: platform sahibi, müşteri değil)" if t.slug == HQ_SLUG else ""
        rows.append(f"- {t.name}{owner} | paket: {plan.name if plan else '-'} | {'aktif' if t.is_active else 'pasif'} | "
                    f"bitiş: {expiry} | kullanıcı+AI: {counts.get(t.id, 0)} (AI: {agent_counts.get(t.id, 0)}) | "
                    f"{period} kredi kullanımı: {abs(_f(used.get(t.id))):.0f} / {plan.monthly_credits if plan else 0}")
    return f"""Sen RECOrion platformunun Süper Yönetici asistanısın (RECDx). RECDx yöneticilerine müşteri şirketler,
paketler, başvurular, kredi kullanımı ve platform modelleri hakkında yardımcı olursun.
KVKK gereği müşteri şirketlerin proje, sohbet, hafıza ve doküman içeriklerine erişimin yoktur; sorulursa bunu belirt.
Yalnızca aşağıdaki verilere dayan, sayı uydurma. Müşteri sayısına RECDx ana şirketini katma.
Yanıtların Türkçe ve kısa olsun; tablo kullanma, gerekirse kısa maddeler ve **kalın** vurgu kullan.

Bugün: {datetime.now(credits.TZ).date().isoformat()} (dönem {period})

# Şirketler (son 60)
{chr(10).join(rows) or "- yok"}

# Başvurular (durum: adet)
{", ".join(f"{k}: {v}" for k, v in leads.items()) or "yok"}

# Paketler
{chr(10).join(f"- {p.name} ({p.code}): {_f(p.monthly_price):.0f} {p.currency}/ay, {p.monthly_credits} kredi, {p.max_agents} AI personel" for p in plans.values()) or "- yok"}

# Aktif modeller
{", ".join(f"{m.model_code} ({m.model_type}, katsayı {_f(m.effort_coefficient)})" for m in models)}
"""


@router.post("/system/assistant/chat")
async def assistant_chat(payload: ChatPayload, current: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    hq_id = await get_hq_tenant_id(db)
    return await _converse(db, LLMContext(tenant_id=None, purpose="PLATFORM_ASSISTANT"), hq_id, current.actor_id,
                           "PLATFORM_ASSISTANT", await _platform_prompt(db), payload.content.strip())


@router.get("/system/assistant/history")
async def assistant_history(limit: int = Query(50, ge=1, le=200),
                            current: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    hq_id = await get_hq_tenant_id(db)
    return [_message_out(m) for m in await _history(db, hq_id, current.actor_id, "PLATFORM_ASSISTANT", limit)]
