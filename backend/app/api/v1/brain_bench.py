"""
Beyin AI deneme seti uçları (İSTEK #754) — yalnız RECDx Süper Admin (Merkez).

- GET  /system/brain-bench/cases        brifler (kısa brif + gizli cevap anahtarı; sentetik, müşteri verisi değil)
- GET  /system/brain-bench/runs         koşular (son 20) ve önceki koşuyla karşılaştırma
- POST /system/brain-bench/runs         yeni koşu (canlı test şirketinde arka planda; aynı anda tek koşu)
- GET  /system/brain-bench/runs/{id}    koşu ayrıntısı
"""
import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import CurrentUser, get_current_user
from app.db.models import BrainBenchRun
from app.db.session import get_db
from app.services import brain_bench as bsvc

router = APIRouter(tags=["Beyin Deneme Seti"])


def _super(user: CurrentUser) -> None:
    if not user.is_super_admin:
        raise HTTPException(status_code=403, detail="Bu işlem yalnızca RECDx Süper Admin içindir.")


class RunIn(BaseModel):
    codes: Optional[List[str]] = None
    label: Optional[str] = Field(None, max_length=200)


@router.get("/system/brain-bench/cases")
async def list_cases(user: CurrentUser = Depends(get_current_user)):
    _super(user)
    return {"cases": bsvc.cases(), "weights": bsvc.WEIGHTS, "rounds": bsvc.ROUNDS}


@router.get("/system/brain-bench/runs")
async def list_runs(user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    _super(user)
    await bsvc.expire_stale(db)
    runs = [bsvc.out(r) for r in (await db.execute(select(BrainBenchRun).order_by(BrainBenchRun.started_at.desc()).limit(20))).scalars()]
    for i, r in enumerate(runs):  # her koşu, kendinden önceki tamamlanmış koşuyla karşılaştırılır
        prev = next((p for p in runs[i + 1:] if p["status"] == "DONE"), None)
        r["previous_id"] = prev and prev["id"]
        r["delta"] = bsvc.compare(r, prev)
    return runs


@router.post("/system/brain-bench/runs", status_code=202)
async def start_run(payload: RunIn, user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    _super(user)
    run = await bsvc.create_run(db, payload.codes, payload.label, user.actor_id)
    bsvc.spawn(run.id)
    return bsvc.out(run)


@router.get("/system/brain-bench/runs/{run_id}")
async def get_run(run_id: uuid.UUID, user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    _super(user)
    run = await db.get(BrainBenchRun, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Koşu bulunamadı.")
    return bsvc.out(run)
