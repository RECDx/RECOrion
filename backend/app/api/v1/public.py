"""Resmi web sitesi için herkese açık, kişisel veri içermeyen istatistikler."""
from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import LLMModel, Profession, Sector
from app.db.session import get_db

router = APIRouter(prefix="/public", tags=["Herkese Açık"])


@router.get("/stats")
async def public_stats(db: AsyncSession = Depends(get_db)):
    async def count(stmt):
        return (await db.execute(stmt)).scalar() or 0

    return {
        "llm_models": await count(select(func.count(LLMModel.id)).where(LLMModel.status == "ACTIVE")),
        "sectors": await count(select(func.count(Sector.code)).where(Sector.is_active == True)),
        "professions": await count(select(func.count(Profession.code)).where(Profession.is_active == True)),
    }
