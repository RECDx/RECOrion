"""İSTEK #750: Beyin AI web derin araştırması uçları (proje) ve şirket ayarı (aç/kapa, izinli/yasaklı siteler)."""
import uuid
from typing import List, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import CurrentUser, get_current_user
from app.db.models import Tenant
from app.db.session import get_db
from app.services import projects as svc
from app.services import web_research as wr

router = APIRouter(tags=["Web derin araştırma (#750)"])
Depth = Literal["QUICK", "STANDARD", "DEEP"]


class EstimateIn(BaseModel):
    depth: Depth = "STANDARD"


class StartIn(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)
    depth: Depth = "STANDARD"
    max_credits: Optional[float] = Field(None, gt=0, le=100000)
    origin: Literal["MANAGER", "BRAIN_SUGGESTION"] = "MANAGER"


class SettingsIn(BaseModel):
    enabled: bool = True
    allow_domains: List[str] = []
    deny_domains: List[str] = []


@router.post("/projects/{project_id}/research/estimate")
async def estimate(project_id: uuid.UUID, payload: EstimateIn, user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Araştırma başlamadan önce tahmini ve en fazla kredi (yönetici onayı için)."""
    project = await svc.load(db, user, project_id, manage=True)
    return await wr.estimate(db, project, payload.depth)


@router.get("/projects/{project_id}/research")
async def list_research(project_id: uuid.UUID, user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    project = await svc.load(db, user, project_id)
    tenant = await db.get(Tenant, project.tenant_id)
    return {"enabled": wr.settings_of(tenant)["enabled"], "depths": {k: v["label"] for k, v in wr.DEPTHS.items()},
            "items": [wr.out(r) for r in await wr.list_for(db, project)]}


@router.post("/projects/{project_id}/research")
async def start_research(project_id: uuid.UUID, payload: StartIn, user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Yönetici onayıyla araştırmayı başlatır; arka planda sürer, ilerleme liste ucundan izlenir."""
    project = await svc.load(db, user, project_id, manage=True)
    r = await wr.start(db, project, user.actor_id, payload.question, payload.depth, payload.max_credits, payload.origin)
    return wr.out(r)


@router.post("/projects/{project_id}/research/{research_id}/cancel")
async def cancel_research(project_id: uuid.UUID, research_id: uuid.UUID, user: CurrentUser = Depends(get_current_user),
                          db: AsyncSession = Depends(get_db)):
    """Süren araştırmayı durdurur; o ana kadar harcanan kredi geri gelmez."""
    project = await svc.load(db, user, project_id, manage=True)
    return wr.out(await wr.cancel(db, project, research_id))


class RatingIn(BaseModel):
    rating: Literal["USEFUL", "PARTIAL", "USELESS"]


@router.post("/projects/{project_id}/research/{research_id}/rating")
async def rate_research(project_id: uuid.UUID, research_id: uuid.UUID, payload: RatingIn,
                        user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """#753: yönetici araştırmanın faydasını tek tıkla değerlendirir (Beyin öğrenme kaydı; yeniden değerlendirilebilir)."""
    from app.db.models import WebResearch
    from app.services import brain_learning, task_flow

    project = await svc.load(db, user, project_id, manage=True)
    r = await db.get(WebResearch, research_id)
    if r is None or r.project_id != project.id:
        raise HTTPException(status_code=404, detail="Araştırma bulunamadı.")
    if r.status != "DONE":
        raise HTTPException(status_code=409, detail="Yalnız tamamlanan araştırma değerlendirilebilir.")
    r.rating, r.rated_by, r.rated_at = payload.rating, user.actor_id, svc.now()
    label = brain_learning.RATINGS[payload.rating][1]
    await task_flow.log(db, project, None, "WEB_RESEARCH_RATED", user.actor_id, f"Web araştırması değerlendirildi: {label}",
                        {"research_id": str(r.id), "rating": payload.rating})
    await db.commit()
    await brain_learning.on_research_rated(project, r, user.actor_id)
    return wr.out(r)


@router.get("/company/{tenant_id}/web-research/settings")
async def get_settings(tenant_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    tenant = await db.get(Tenant, tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Şirket bulunamadı.")
    return wr.settings_of(tenant)


@router.put("/company/{tenant_id}/web-research/settings")
async def put_settings(tenant_id: uuid.UUID, payload: SettingsIn, db: AsyncSession = Depends(get_db)):
    """Şirket yöneticisi web araştırmasını kapatabilir, izinli (yalnız bunlar) ve yasaklı site listesi tanımlayabilir."""
    tenant = await db.get(Tenant, tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Şirket bulunamadı.")
    return await wr.save_settings(db, tenant, payload.enabled, payload.allow_domains, payload.deny_domains)
