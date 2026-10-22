"""
LLM bazında TL fiyatlandırma (ADIM 7.5.1).

- Model başına 1 milyon girdi ve 1 milyon çıktı token'ının TL fiyatı (KDV hariç), geçerlilik başlangıcıyla.
  Fiyatlar değiştirilmez; yeni fiyat yeni satırdır.
- Her LLM çağrısının TL maliyeti çağrı anında geçerli fiyatla hesaplanıp llm_calls.cost_try'ye yazılır.
- Geriye dönük bir fiyat girilirse, o fiyatın geçerli olduğu aralıktaki henüz fiyatlanmamış çağrılar hesaplanır
  (daha önce fiyatlanmış çağrılar değişmez).
- EVREN fiyatı (CR/token) ve CR>TL kuru varsa TL fiyat önerisi üretilir; karar Süper Admin'indir.
"""
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import LLMCall, LLMModel, LLMModelPrice, SystemSetting

CR_RATE_KEY = "pricing.evren_cr_to_try"
MILLION = Decimal(1_000_000)


def now() -> datetime:
    return datetime.now(timezone.utc)


def call_cost(price: LLMModelPrice, tokens_in: int, tokens_out: int) -> Decimal:
    return ((Decimal(tokens_in or 0) * Decimal(price.price_in_per_1m_try) + Decimal(tokens_out or 0) * Decimal(price.price_out_per_1m_try))
            / MILLION).quantize(Decimal("0.000001"))


async def price_at(db: AsyncSession, model_id, at: Optional[datetime] = None) -> Optional[LLMModelPrice]:
    if not model_id:
        return None
    return (await db.execute(select(LLMModelPrice).where(LLMModelPrice.model_id == model_id, LLMModelPrice.valid_from <= (at or now()))
                             .order_by(LLMModelPrice.valid_from.desc()).limit(1))).scalars().first()


async def cr_rate(db: AsyncSession) -> Optional[Decimal]:
    row = await db.get(SystemSetting, CR_RATE_KEY)
    try:
        return Decimal(str(row.value)) if row and row.value not in (None, "", "null") else None
    except Exception:
        return None


def suggestion(model: LLMModel, rate: Optional[Decimal]) -> Optional[Dict[str, float]]:
    """EVREN fiyatı (CR/token) × 1M × kur. EVREN ücretsiz dönemdeyse veya kur yoksa öneri yok."""
    if not rate or model.pricing_currency != "CR":
        return None
    p_in, p_out = Decimal(str(model.prompt_token_price or 0)), Decimal(str(model.completion_token_price or 0))
    if p_in <= 0 and p_out <= 0:
        return None
    return {"price_in_per_1m_try": float((p_in * MILLION * rate).quantize(Decimal("0.0001"))),
            "price_out_per_1m_try": float((p_out * MILLION * rate).quantize(Decimal("0.0001")))}


async def add_price(db: AsyncSession, model: LLMModel, price_in: Decimal, price_out: Decimal, valid_from: Optional[datetime],
                    note: Optional[str], actor_id) -> Dict[str, Any]:
    valid_from = valid_from or now()
    if valid_from.tzinfo is None:
        valid_from = valid_from.replace(tzinfo=timezone.utc)
    price = LLMModelPrice(model_id=model.id, price_in_per_1m_try=price_in, price_out_per_1m_try=price_out, valid_from=valid_from,
                          note=(note or None), created_by_actor_id=uuid.UUID(str(actor_id)) if actor_id else None)
    db.add(price)
    await db.flush()
    priced = await backfill(db, model, price)
    await db.commit()
    return {"price": price, "backfilled_calls": priced}


async def backfill(db: AsyncSession, model: LLMModel, price: LLMModelPrice) -> int:
    """Fiyatın geçerli olduğu aralıktaki (bir sonraki fiyata kadar) fiyatlanmamış başarılı çağrıları hesaplar."""
    nxt = (await db.execute(select(LLMModelPrice.valid_from).where(LLMModelPrice.model_id == model.id,
                                                                   LLMModelPrice.valid_from > price.valid_from)
                            .order_by(LLMModelPrice.valid_from).limit(1))).scalar()
    cond = [LLMCall.model_id == model.id, LLMCall.cost_try.is_(None), LLMCall.status == "SUCCESS", LLMCall.created_at >= price.valid_from]
    if nxt:
        cond.append(LLMCall.created_at < nxt)
    rows = (await db.execute(select(LLMCall.id, LLMCall.tokens_in, LLMCall.tokens_out).where(and_(*cond)))).all()
    for cid, t_in, t_out in rows:
        await db.execute(update(LLMCall).where(LLMCall.id == cid).values(cost_try=call_cost(price, t_in, t_out)))
    return len(rows)


async def price_list(db: AsyncSession) -> List[Dict[str, Any]]:
    rate = await cr_rate(db)
    models = (await db.execute(select(LLMModel).order_by(LLMModel.model_type, LLMModel.model_code))).scalars().all()
    out = []
    for m in models:
        current = await price_at(db, m.id)
        history = (await db.execute(select(LLMModelPrice).where(LLMModelPrice.model_id == m.id)
                                    .order_by(LLMModelPrice.valid_from.desc()))).scalars().all()
        out.append({
            "model_code": m.model_code, "display_name": m.display_name, "model_type": m.model_type, "status": m.status,
            "effort_coefficient": float(m.effort_coefficient or 1),
            "evren": {"prompt_token_price": float(m.prompt_token_price or 0), "completion_token_price": float(m.completion_token_price or 0),
                      "currency": m.pricing_currency, "free_until": m.free_until},
            "current": _out(current), "suggestion": suggestion(m, rate),
            "history": [_out(h) for h in history],
        })
    return out


def _out(p: Optional[LLMModelPrice]) -> Optional[Dict[str, Any]]:
    if not p:
        return None
    return {"id": str(p.id), "price_in_per_1m_try": float(p.price_in_per_1m_try), "price_out_per_1m_try": float(p.price_out_per_1m_try),
            "valid_from": p.valid_from, "note": p.note, "created_at": p.created_at}
