"""
Model yönlendirici uçları (ADIM 11.4) — yalnızca RECDx Süper Admin (platform ayarı; müşteri içeriği yok).

- GET  /system/model-router                 iş türleri, onaylı yönler, canlı ölçümler, son koşu ve öneri, karar geçmişi
- POST /system/model-router/runs            kalite test setini seçilen modellerde koştur (arka planda)
- GET  /system/model-router/runs/{id}       koşu durumu, vaka sonuçları, öneri
- POST /system/model-router/routes          iş türü için modeli onayla (veya yönlendirmeyi kaldır); iz tutulur
"""
import uuid
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import CurrentUser, get_current_user
from app.db.models import LLMModel, ModelRouteDecision, QualityResult, QualityRun
from app.db.session import get_db
from app.services import model_router as rsvc

router = APIRouter(tags=["Model Yönlendirici"])


def _super(user: CurrentUser) -> None:
    if not user.is_super_admin:
        raise HTTPException(status_code=403, detail="Bu işlem yalnızca RECDx Süper Admin içindir.")


def _run_out(r: QualityRun) -> Dict[str, Any]:
    return {"id": str(r.id), "models": r.models, "suite_version": r.suite_version, "status": r.status, "progress": r.progress,
            "error": r.error, "started_at": r.started_at, "finished_at": r.finished_at}


@router.get("/system/model-router")
async def overview(user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    _super(user)
    suite = rsvc.load_suite()
    models = (await db.execute(select(LLMModel.model_code, LLMModel.display_name).where(LLMModel.status == "ACTIVE", LLMModel.model_type == "CHAT")
                               .order_by(LLMModel.model_code))).all()
    last = (await db.execute(select(QualityRun).order_by(QualityRun.started_at.desc()).limit(1))).scalar_one_or_none()
    last_done = (await db.execute(select(QualityRun).where(QualityRun.status == "DONE").order_by(QualityRun.started_at.desc()).limit(1))).scalar_one_or_none()
    decisions = (await db.execute(select(ModelRouteDecision).order_by(ModelRouteDecision.decided_at.desc()).limit(20))).scalars().all()
    return {
        "task_types": rsvc.TASK_TYPES, "weights": rsvc.WEIGHTS, "quality_min": rsvc.QUALITY_MIN,
        "suite": {"version": suite["version"], "cases": {tt: sum(1 for c in suite["cases"] if c["task_type"] == tt) for tt in rsvc.TASK_TYPES}},
        "models": [{"model_code": m, "name": n} for m, n in models], "routes": await rsvc.current_routes(db),
        "live": await rsvc.live_metrics(db), "last_run": _run_out(last) if last else None,
        "recommendation": await rsvc.recommend(db, last_done.id) if last_done else None, "recommendation_run_id": str(last_done.id) if last_done else None,
        "decisions": [{"task_type": d.task_type, "model_code": d.model_code, "previous_model_code": d.previous_model_code, "note": d.note,
                       "decided_at": d.decided_at, "run_id": str(d.run_id) if d.run_id else None} for d in decisions],
    }


class RunIn(BaseModel):
    models: List[str] = Field(..., min_length=1, max_length=12)


@router.post("/system/model-router/runs", status_code=202)
async def start_run(payload: RunIn, user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    _super(user)
    if (await db.execute(select(QualityRun.id).where(QualityRun.status == "RUNNING"))).first():
        raise HTTPException(status_code=409, detail="Süren bir kalite testi var; bitmesini bekleyin.")
    wanted = {m.lower() for m in payload.models}
    rows = (await db.execute(select(LLMModel.model_code).where(func.lower(LLMModel.model_code).in_(wanted), LLMModel.status == "ACTIVE",
                                                               LLMModel.model_type == "CHAT"))).scalars().all()
    if len(rows) != len(wanted):
        raise HTTPException(status_code=422, detail="Yalnızca etkin sohbet modelleri sınanabilir.")
    run = QualityRun(started_by_actor_id=user.actor_id, models=sorted(rows), suite_version=rsvc.load_suite()["version"], status="RUNNING",
                     progress="Başlıyor…")
    db.add(run)
    await db.commit()
    rsvc.start(run.id, sorted(rows))
    return _run_out(run)


@router.get("/system/model-router/runs/{run_id}")
async def get_run(run_id: uuid.UUID, user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    _super(user)
    run = await db.get(QualityRun, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Koşu bulunamadı.")
    rows = (await db.execute(select(QualityResult).where(QualityResult.run_id == run_id).order_by(QualityResult.model_code, QualityResult.case_code))).scalars().all()
    return {**_run_out(run), "results": [{"model_code": r.model_code, "case_code": r.case_code, "task_type": r.task_type, "score": float(r.score),
                                          "checks": r.checks, "latency_ms": r.latency_ms, "error": r.error, "output_excerpt": r.output_excerpt}
                                         for r in rows],
            "recommendation": await rsvc.recommend(db, run_id) if run.status == "DONE" else None}


class RouteIn(BaseModel):
    task_type: str
    model_code: Optional[str] = None  # boş: yönlendirmeyi kaldır (platform varsayılanı)
    run_id: Optional[uuid.UUID] = None
    note: Optional[str] = Field(None, max_length=1000)


@router.post("/system/model-router/routes")
async def set_route(payload: RouteIn, user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    _super(user)
    evidence = None
    if payload.run_id and payload.model_code:
        rec = (await rsvc.recommend(db, payload.run_id)).get(payload.task_type) or {}
        evidence = next((c for c in rec.get("candidates", []) if c["model_code"].lower() == payload.model_code.lower()), None)
        if evidence and not evidence["eligible"] and not (payload.note or "").strip():
            raise HTTPException(status_code=422, detail="Bu model kalite eşiğinin altında; yine de onaylamak için gerekçe yazın.")
    d = await rsvc.approve(db, payload.task_type, payload.model_code, user.actor_id, payload.run_id, payload.note, evidence)
    return {"task_type": d.task_type, "model_code": d.model_code, "previous_model_code": d.previous_model_code, "routes": await rsvc.current_routes(db)}
