"""
LLM TL fiyat listesi uçları (ADIM 7.5.1, yalnızca RECDx Süper Admin).
"""
from datetime import datetime
from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import CurrentUser, get_current_user
from app.db.models import LLMModel, SystemSetting
from app.db.session import get_db
from app.services import pricing

router = APIRouter(prefix="/system/llm-prices", tags=["LLM TL Fiyatları"])


@router.get("")
async def list_prices(db: AsyncSession = Depends(get_db)):
    return {"cr_to_try": float(r) if (r := await pricing.cr_rate(db)) else None, "models": await pricing.price_list(db)}


class PriceIn(BaseModel):
    model_code: str
    price_in_per_1m_try: Decimal = Field(ge=0, le=1_000_000)
    price_out_per_1m_try: Decimal = Field(ge=0, le=1_000_000)
    valid_from: Optional[datetime] = None  # boş: şimdi; geçmiş tarih verilirse o aralıktaki fiyatlanmamış çağrılar hesaplanır
    note: Optional[str] = Field(None, max_length=500)


@router.post("")
async def add_price(payload: PriceIn, user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    model = (await db.execute(select(LLMModel).where(func.lower(LLMModel.model_code) == payload.model_code.lower()))).scalar_one_or_none()
    if not model:
        raise HTTPException(status_code=404, detail="Model bulunamadı.")
    try:
        result = await pricing.add_price(db, model, payload.price_in_per_1m_try, payload.price_out_per_1m_try, payload.valid_from,
                                         payload.note, user.actor_id)
    except Exception as exc:
        if "uq" in str(exc).lower() or "unique" in str(exc).lower():
            raise HTTPException(status_code=409, detail="Bu model için aynı başlangıç zamanlı bir fiyat zaten var.") from exc
        raise
    return {"price": pricing._out(result["price"]), "backfilled_calls": result["backfilled_calls"]}


class RateIn(BaseModel):
    cr_to_try: Optional[Decimal] = Field(None, gt=0, le=1_000_000)


@router.put("/cr-rate")
async def set_cr_rate(payload: RateIn, db: AsyncSession = Depends(get_db)):
    row = await db.get(SystemSetting, pricing.CR_RATE_KEY)
    value = float(payload.cr_to_try) if payload.cr_to_try is not None else None
    if row:
        row.value = value
    else:
        db.add(SystemSetting(key=pricing.CR_RATE_KEY, value=value, description="EVREN 1 CR'nin TL karşılığı"))
    await db.commit()
    return {"cr_to_try": value}
