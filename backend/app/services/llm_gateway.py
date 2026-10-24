"""
RECOrion LLM Gateway: tüm yapay zeka çağrılarının tek kapısı.

Her çağrıda:
1. Model çözülür (açık seçim → AI personelin modeli → şirketin Beyin AI modeli →
   platform varsayılanı) ve şirket paketinin izin verdiği modeller arasında olduğu doğrulanır.
2. Kredi ön kontrolü yapılır (RECDx platform kullanımı sınırlanmaz, yalnızca ölçülür).
3. EVREN çağrılır; token kullanımı yanıttaki usage alanından okunur.
4. llm_calls (ölçüm) ve credit_ledger (kredi düşümü) kaydedilir; eşik aşıldıysa uyarı gider.

Hata durumunda sahte yanıt üretilmez: LLMError (503 / 402 / 403) fırlatılır.
Ölçüm kayıtları çağıranın veritabanı oturumundan bağımsız, kendi oturumunda tutulur.
"""
import logging
import time
import uuid
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any, Dict, List, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Actor, LLMCall, LLMModel, Plan, SystemSetting, Tenant
from app.db.session import AsyncSessionLocal
from app.services import credits
from app.services.evren_client import EvrenError, estimate_tokens, evren_client

logger = logging.getLogger("recorion.llm")

HQ_SLUG = "recdx_hq"

# Amaç → varsayılan model ayarı (system_settings)
PURPOSE_SETTING = {
    "BRAIN": "model.default.brain",
    "AGENT_CHAT": "model.default.agent",
    "PLATFORM_ASSISTANT": "model.platform_assistant",
    "MANIFESTO": "default_manifesto_model",
    "ROLE_PROMPT": "default_manifesto_model",
    "TITLE_REVIEW": "default_manifesto_model",
    "EMBEDDING": "model.default.embedding",
    "RERANK": "model.default.rerank",
    "OCR": "model.default.ocr",
    "TRANSCRIPTION": "model.default.transcription",
    "GUARD": "model.guard",
    "VISION": "model.default.vision",
    "LEARNING_CARD": "default_manifesto_model",
}
INFRA_PURPOSES = {"EMBEDDING", "RERANK", "OCR", "GUARD", "VISION", "TRANSCRIPTION"}  # paket model listesinden bağımsız altyapı modelleri
AUDIO_TOKENS_PER_SECOND = 25  # yazıya çevirme ucu kullanım bildirmez: ses saniyesi başına tahmini giriş tokenı
OCR_PAGE_TOKENS = 1000  # OCR ucu kullanım bildirmez: sayfa başına tahmini giriş tokenı
IMAGE_TOKENS = 1200  # görsel başına tahmini giriş tokenı (kredi ön kontrolü için)
DEFAULT_CHAT_SETTING = "model.default.chat"
DEFAULT_AGENT_SETTING = "model.default.agent"
FALLBACK_SETTING = "model.fallback"  # meşgul/yanıtsız modelde ilk yedek (kullanıcı kararı 23.10.2026)
CHAT_TYPES = {"CHAT", "VISION", "DECISION"}


class LLMError(Exception):
    status_code = 503

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class LLMUnavailable(LLMError):
    status_code = 503

    def __init__(self, message: str, model_code: Optional[str] = None):
        super().__init__(message)
        self.model_code = model_code  # yanıt vermeyen model (yedek model seçiminde dışlanır)


class CreditExhausted(LLMError):
    status_code = 402


class ModelNotAllowed(LLMError):
    status_code = 403


@dataclass
class LLMContext:
    """Çağrının kime ve neye ait olduğu (ölçüm, kredi ve model seçimi için)."""
    tenant_id: Optional[uuid.UUID]  # None: RECDx platformu
    purpose: str = "CHAT"
    actor_id: Optional[uuid.UUID] = None  # AI personel (modeli buradan da çözülebilir)
    task_id: Optional[uuid.UUID] = None
    project_id: Optional[uuid.UUID] = None
    task_type: Optional[str] = None  # ADIM 11.4: iş türü (CODE, ANALYSIS, SUMMARY, WRITING, STRUCTURED) → onaylı yönlendirme


@dataclass
class GatewayChatResult:
    content: str
    thought: Optional[str]
    model_code: str
    tokens_in: int
    tokens_out: int
    credits: float
    raw: Dict[str, Any] = field(default_factory=dict)
    fallback_from: Optional[str] = None  # asıl model yanıt vermediyse onun kodu (yedek modelle üretildi)
    tool_calls: List[Dict[str, Any]] = field(default_factory=list)  # ADIM 10.2


async def _setting(db: AsyncSession, key: str) -> Optional[str]:
    row = await db.get(SystemSetting, key)
    return str(row.value) if row and row.value else None


async def _tenant(db: AsyncSession, tenant_id: Optional[uuid.UUID]) -> Tenant:
    if tenant_id:
        tenant = await db.get(Tenant, tenant_id)
        if tenant:
            return tenant
    tenant = (await db.execute(select(Tenant).where(Tenant.slug == HQ_SLUG))).scalar_one_or_none()
    if not tenant:
        raise LLMError("Şirket bulunamadı.")
    return tenant


async def allowed_model_codes(db: AsyncSession, tenant: Tenant) -> Optional[set]:
    """Paketin izin verdiği modeller; None = sınırsız (platform veya listesiz paket)."""
    if tenant.slug == HQ_SLUG or not tenant.plan_id:
        return None
    plan = await db.get(Plan, tenant.plan_id)
    codes = {str(m).lower() for m in (plan.allowed_models or [])} if plan else set()
    return codes or None


async def resolve_model(db: AsyncSession, tenant: Tenant, purpose: str, requested: Optional[str],
                        actor_id: Optional[uuid.UUID], task_type: Optional[str] = None) -> LLMModel:
    allowed = await allowed_model_codes(db, tenant)
    infra = purpose in INFRA_PURPOSES

    candidates: List[str] = []
    if requested:
        candidates.append(requested)
    if actor_id and not infra:
        actor = await db.get(Actor, actor_id)
        if actor and actor.preferred_model_id:
            m = await db.get(LLMModel, actor.preferred_model_id)
            if m:
                candidates.append(m.model_code)
    if purpose == "BRAIN" and tenant.brain_model_code:
        candidates.append(tenant.brain_model_code)
    # Model yönlendirici (ADIM 11.4): Süper Admin'in iş türü için onayladığı model, platform varsayılanından önce gelir
    # (açık seçim, AI personelin modeli ve şirketin Beyin modeli her zaman önce)
    route_type = task_type or ("STRUCTURED" if purpose == "BRAIN" else None)
    if route_type and not infra and purpose != "QUALITY_TEST" and (routed := await _setting(db, f"model.route.{route_type}")):
        candidates.append(routed)
    for key in (PURPOSE_SETTING.get(purpose), DEFAULT_CHAT_SETTING if not infra else None):
        if key and (value := await _setting(db, key)):
            candidates.append(value)

    for i, code in enumerate(candidates):
        model = (await db.execute(select(LLMModel).where(func.lower(LLMModel.model_code) == code.lower()))).scalar_one_or_none()
        if not model or model.status != "ACTIVE":
            continue
        # Altyapı modelleri (embedding/rerank/OCR/guard) paket listesinden bağımsızdır; sohbet modelleri pakete bağlıdır
        if allowed is not None and not infra and model.model_code.lower() not in allowed:
            if i == 0 and requested:
                raise ModelNotAllowed(f"'{model.model_code}' modeli şirketinizin paketinde yer almıyor.")
            continue
        return model

    # Son çare: paketin izin verdiği ilk aktif sohbet modeli
    if not infra:
        stmt = select(LLMModel).where(LLMModel.status == "ACTIVE", LLMModel.model_type.in_(CHAT_TYPES)).order_by(LLMModel.model_code)
        for model in (await db.execute(stmt)).scalars():
            if allowed is None or model.model_code.lower() in allowed:
                return model
    raise LLMError("Bu işlem için kullanılabilir bir yapay zeka modeli bulunamadı.")


async def _preflight(db: AsyncSession, tenant: Tenant, model: LLMModel, est_in: int, est_out: int) -> None:
    if tenant.slug == HQ_SLUG:
        return
    await credits.ensure_period_grant(db, tenant)
    bal = await credits.balance(db, tenant.id)
    if bal <= 0 or bal < credits.credit_cost(model.effort_coefficient, est_in, est_out):
        raise CreditExhausted("Şirketinizin RECOrion kredisi bu işlem için yetersiz. Yeni dönemi bekleyebilir veya ek kredi için RECDx ile iletişime geçebilirsiniz.")


async def _record(db: AsyncSession, tenant: Tenant, model: LLMModel, ctx: LLMContext, tokens_in: int, tokens_out: int,
                  started: float, error: Optional[str] = None, raw: Optional[Dict[str, Any]] = None) -> Decimal:
    cost = Decimal(0) if error else credits.credit_cost(model.effort_coefficient, tokens_in, tokens_out)
    evren = ((raw or {}).get("usage") or {}).get("evren") or {}
    call = LLMCall(
        id=uuid.uuid4(), tenant_id=tenant.id, task_id=ctx.task_id, actor_id=ctx.actor_id, project_id=ctx.project_id,
        model_id=model.id, model_code=model.model_code, purpose=ctx.purpose, tokens_in=tokens_in, tokens_out=tokens_out,
        credits_cost=cost, latency_ms=int((time.monotonic() - started) * 1000),
        status="FAILED" if error else "SUCCESS", error=(error or None) and error[:500],
        evren_credits=_num(evren.get("credits_charged_cr") or evren.get("credits_held_cr")),
        evren_balance_after=_num(evren.get("credits_remaining_cr")),
    )
    if not error:
        # TL maliyet: çağrı anında geçerli LLM fiyatı (ADIM 7.5.1); fiyat tanımlı değilse boş kalır
        from app.services import pricing

        price = await pricing.price_at(db, model.id)
        if price:
            call.cost_try = pricing.call_cost(price, tokens_in, tokens_out)
    db.add(call)
    if not error and tenant.slug != HQ_SLUG:
        await credits.record_usage(db, tenant.id, cost, call.id, f"{ctx.purpose} · {model.model_code}")
    await db.commit()
    if not error and tenant.slug != HQ_SLUG:
        try:
            await credits.check_alerts(db, tenant)
        except Exception as exc:
            logger.warning("Kredi uyarısı gönderilemedi: %s", exc)
    return cost


def _num(value) -> Optional[Decimal]:
    try:
        return Decimal(str(value)) if value is not None else None
    except Exception:
        return None


async def fallback_model(db: AsyncSession, tenant: Tenant, exclude: str) -> Optional[LLMModel]:
    """Asıl model meşgul/yanıtsızken kullanılacak yedek: önce model.fallback (23.10.2026: mimo-v2.6-pro), AI personel
    varsayılanı, genel varsayılan, sonra paketteki ilk sohbet modeli."""
    allowed = await allowed_model_codes(db, tenant)
    codes = [c for c in [await _setting(db, FALLBACK_SETTING), await _setting(db, DEFAULT_AGENT_SETTING),
                         await _setting(db, DEFAULT_CHAT_SETTING)] if c]
    stmt = select(LLMModel).where(LLMModel.status == "ACTIVE", LLMModel.model_type.in_(CHAT_TYPES)).order_by(LLMModel.model_code)
    codes += [m.model_code for m in (await db.execute(stmt)).scalars()]
    for code in codes:
        if code.lower() == exclude.lower() or (allowed is not None and code.lower() not in allowed):
            continue
        model = (await db.execute(select(LLMModel).where(func.lower(LLMModel.model_code) == code.lower()))).scalar_one_or_none()
        if model and model.status == "ACTIVE" and model.model_type in CHAT_TYPES:
            return model
    return None


# ---------------------------------------------------------------- genel arayüz
async def chat(ctx: LLMContext, messages: List[Dict[str, str]], model_code: Optional[str] = None,
               temperature: float = 0.7, max_tokens: int = 4096, timeout: Optional[float] = None,
               fallback: bool = False, tools: Optional[List[Dict[str, Any]]] = None) -> GatewayChatResult:
    """fallback=True: model meşgul/yanıtsız (EVREN hatası veya boş yanıt) ise paketteki yedek modelle bir kez daha dener."""
    try:
        return await _chat_once(ctx, messages, model_code, temperature, max_tokens, timeout, tools)
    except LLMUnavailable as exc:
        if not fallback:
            raise
        failed = exc.model_code
        async with AsyncSessionLocal() as db:
            tenant = await _tenant(db, ctx.tenant_id)
            backup = await fallback_model(db, tenant, failed or "")
        if not backup or not failed:
            raise
        logger.warning("%s yanıt vermedi; yedek model %s ile deneniyor (%s).", failed, backup.model_code, ctx.purpose)
        result = await _chat_once(ctx, messages, backup.model_code, temperature, max_tokens, timeout, tools)
        result.fallback_from = failed
        return result


async def _chat_once(ctx: LLMContext, messages: List[Dict[str, str]], model_code: Optional[str],
                     temperature: float, max_tokens: int, timeout: Optional[float],
                     tools: Optional[List[Dict[str, Any]]] = None) -> GatewayChatResult:
    async with AsyncSessionLocal() as db:
        tenant = await _tenant(db, ctx.tenant_id)
        model = await resolve_model(db, tenant, ctx.purpose, model_code, ctx.actor_id, ctx.task_type)
        if model.max_output_tokens:
            max_tokens = min(max_tokens, model.max_output_tokens)
        est_in = estimate_tokens(" ".join(str(m.get("content", "")) for m in messages))
        await _preflight(db, tenant, model, est_in, min(max_tokens, 512))
        started = time.monotonic()
        try:
            extra = {"tools": tools} if tools else {}
            result = await evren_client.chat(model.model_code, messages, temperature=temperature, max_tokens=max_tokens,
                                             timeout=timeout, **extra)
        except EvrenError as exc:
            await _record(db, tenant, model, ctx, 0, 0, started, error=str(exc))
            logger.error("LLM çağrısı başarısız (%s, %s): %s", ctx.purpose, model.model_code, exc)
            raise LLMUnavailable(f"Yapay zeka servisi şu anda yanıt veremiyor ({model.model_code}). Lütfen biraz sonra tekrar deneyin.",
                                 model_code=model.model_code) from exc
        tool_calls = list(getattr(result, "tool_calls", None) or [])
        if not result.content.strip() and not tool_calls:  # yalnızca araç çağrısı içeren yanıt boş sayılmaz
            await _record(db, tenant, model, ctx, result.tokens_in, result.tokens_out, started, raw=result.raw)
            raise LLMUnavailable("Model bir yanıt üretemedi (düşünme bütçesi doldu). Lütfen isteği kısaltıp tekrar deneyin.",
                                 model_code=model.model_code)
        cost = await _record(db, tenant, model, ctx, result.tokens_in, result.tokens_out, started, raw=result.raw)
        return GatewayChatResult(content=result.content, thought=result.thought, model_code=model.model_code,
                                 tokens_in=result.tokens_in, tokens_out=result.tokens_out, credits=float(cost), raw=result.raw,
                                 tool_calls=tool_calls)


async def embed(ctx: LLMContext, text: str) -> List[float]:
    ctx.purpose = "EMBEDDING"
    async with AsyncSessionLocal() as db:
        tenant = await _tenant(db, ctx.tenant_id)
        model = await resolve_model(db, tenant, "EMBEDDING", None, None)
        await _preflight(db, tenant, model, estimate_tokens(text), 0)
        started = time.monotonic()
        try:
            result = await evren_client.embed(text, model.model_code)
        except EvrenError as exc:
            await _record(db, tenant, model, ctx, 0, 0, started, error=str(exc))
            raise LLMUnavailable("Hafıza vektörleme servisi şu anda yanıt veremiyor. Lütfen biraz sonra tekrar deneyin.") from exc
        await _record(db, tenant, model, ctx, result.tokens_in, 0, started)
        return result.vector


async def rerank(ctx: LLMContext, query: str, documents: List[str], top_n: int = 5) -> List[Dict[str, Any]]:
    ctx.purpose = "RERANK"
    async with AsyncSessionLocal() as db:
        tenant = await _tenant(db, ctx.tenant_id)
        model = await resolve_model(db, tenant, "RERANK", None, None)
        await _preflight(db, tenant, model, estimate_tokens(query + " ".join(documents)), 0)
        started = time.monotonic()
        try:
            result = await evren_client.rerank(query, documents, model.model_code, top_n=top_n)
        except EvrenError as exc:
            await _record(db, tenant, model, ctx, 0, 0, started, error=str(exc))
            raise LLMUnavailable("Yeniden sıralama servisi yanıt vermedi.") from exc
        await _record(db, tenant, model, ctx, result.tokens_in, 0, started)
        return result.results


async def ocr(ctx: LLMContext, png_bytes: bytes) -> str:
    """Bir sayfa/görsel için OCR. Kredi: sayfa başına tahmini giriş + okunan metin kadar çıkış tokenı."""
    ctx.purpose = "OCR"
    async with AsyncSessionLocal() as db:
        tenant = await _tenant(db, ctx.tenant_id)
        model = await resolve_model(db, tenant, "OCR", None, None)
        await _preflight(db, tenant, model, OCR_PAGE_TOKENS, 500)
        started = time.monotonic()
        try:
            text = await evren_client.ocr(png_bytes, model.model_code)
        except EvrenError as exc:
            await _record(db, tenant, model, ctx, 0, 0, started, error=str(exc))
            raise LLMUnavailable("Belge okuma (OCR) servisi şu anda yanıt veremiyor. Lütfen biraz sonra tekrar deneyin.") from exc
        await _record(db, tenant, model, ctx, OCR_PAGE_TOKENS, estimate_tokens(text), started)
        return text


async def transcribe(ctx: LLMContext, audio: bytes, filename: str, mime: str, seconds: float) -> str:
    """Ses parçasını yazıya çevirir (ADIM 11.3). Kredi: saniye başına tahmini giriş + okunan metin kadar çıkış tokenı."""
    ctx.purpose = "TRANSCRIPTION"
    async with AsyncSessionLocal() as db:
        tenant = await _tenant(db, ctx.tenant_id)
        model = await resolve_model(db, tenant, "TRANSCRIPTION", None, None)
        est_in = int(seconds * AUDIO_TOKENS_PER_SECOND)
        await _preflight(db, tenant, model, est_in, 2000)
        started = time.monotonic()
        try:
            text = await evren_client.transcribe(audio, filename, mime, model.model_code)
        except EvrenError as exc:
            await _record(db, tenant, model, ctx, 0, 0, started, error=str(exc))
            raise LLMUnavailable("Ses yazıya çevirme servisi şu anda yanıt veremiyor. Lütfen biraz sonra tekrar deneyin.") from exc
        await _record(db, tenant, model, ctx, est_in, estimate_tokens(text), started)
        return text


async def guard(ctx: LLMContext, text: str) -> Dict[str, Any]:
    """İçerik güvenliği: {"safe": bool, "level": "Safe|Unsafe|Controversial", "categories": [...]}"""
    import re

    ctx.purpose = "GUARD"
    result = await chat(ctx, [{"role": "user", "content": text[:6000]}], temperature=0, max_tokens=64, timeout=60)
    level = (re.search(r"Safety:\s*(\w+)", result.content) or [None, "Safe"])[1]
    cats = (re.search(r"Categories:\s*(.+)", result.content) or [None, "None"])[1].strip()
    return {"safe": level.lower() != "unsafe", "level": level,
            "categories": [] if cats.lower() == "none" else [c.strip() for c in cats.split(",")]}


async def describe_image(ctx: LLMContext, png_bytes: bytes, instruction: str) -> str:
    """Görseli görsel-dil modeliyle açıklar (fotoğraf, şema, çizim). Görsel verisi token tahminine katılmaz."""
    import base64

    ctx.purpose = "VISION"
    async with AsyncSessionLocal() as db:
        tenant = await _tenant(db, ctx.tenant_id)
        model = await resolve_model(db, tenant, "VISION", None, None)
        await _preflight(db, tenant, model, IMAGE_TOKENS + estimate_tokens(instruction), 600)
        messages = [{"role": "user", "content": [
            {"type": "text", "text": instruction},
            {"type": "image_url", "image_url": {"url": "data:image/png;base64," + base64.b64encode(png_bytes).decode()}},
        ]}]
        started = time.monotonic()
        try:
            result = await evren_client.chat(model.model_code, messages, temperature=0.2, max_tokens=1200, timeout=120)
        except EvrenError as exc:
            await _record(db, tenant, model, ctx, 0, 0, started, error=str(exc))
            raise LLMUnavailable("Görsel açıklama servisi şu anda yanıt veremiyor. Lütfen biraz sonra tekrar deneyin.") from exc
        usage = (result.raw or {}).get("usage") or {}
        tokens_in = int(usage.get("prompt_tokens") or IMAGE_TOKENS)
        await _record(db, tenant, model, ctx, tokens_in, result.tokens_out, started, raw=result.raw)
        return result.content.strip()
