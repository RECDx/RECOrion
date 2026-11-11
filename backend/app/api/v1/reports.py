"""
İSTEK #744 — Rapor uçları (Beyin AI raporları ve Merkez toplu raporları).

- GET  /company/{tid}/reports/catalog     kullanıcının yetkisine göre rapor kataloğu
- POST /company/{tid}/reports/run         raporu çalıştırır (rol sınırlı; şirket içeriği — RECDx göremez)
- GET  /system/reports/catalog            Merkez toplu rapor kataloğu
- POST /system/reports/run                Merkez raporu (k-anonimlik + baskınlık kuralı)
- GET/PUT /system/privacy-settings        k eşiği ve baskınlık sınırı (Merkez ayarı)
"""
import uuid
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import CurrentUser, get_current_user
from app.db.session import get_db
from app.services import reports as rs

router = APIRouter(tags=["Raporlar (#744)"])


class RunIn(BaseModel):
    report: str = Field(..., max_length=40)
    dims: List[str] = Field(default_factory=list, max_length=2)
    measure: Optional[str] = Field(None, max_length=40)
    filters: Dict[str, Any] = Field(default_factory=dict)
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    chart: Optional[str] = Field(None, max_length=10)
    title: Optional[str] = Field(None, max_length=200)


async def _run(db, spec: RunIn, **kw):
    try:
        return await rs.run(db, spec.model_dump(), **kw)
    except rs.ReportError as exc:
        raise HTTPException(status_code=exc.status, detail=str(exc))


@router.get("/company/{tenant_id}/reports/catalog")
async def company_report_catalog(tenant_id: uuid.UUID, user: CurrentUser = Depends(get_current_user)):
    return rs.catalog_out(user)


@router.post("/company/{tenant_id}/reports/run")
async def company_report_run(tenant_id: uuid.UUID, payload: RunIn, user: CurrentUser = Depends(get_current_user),
                             db: AsyncSession = Depends(get_db)):
    return await _run(db, payload, tenant_id=tenant_id, user=user)


@router.get("/system/reports/catalog")
async def platform_report_catalog():
    return rs.catalog_out(None, platform=True)


@router.post("/system/reports/run")
async def platform_report_run(payload: RunIn, db: AsyncSession = Depends(get_db)):
    return await _run(db, payload, platform=True)


class PrivacyIn(BaseModel):
    k_min: int = Field(..., ge=3, le=50)
    dominance_pct: int = Field(..., ge=30, le=100)


@router.get("/system/privacy-settings")
async def get_privacy(db: AsyncSession = Depends(get_db)):
    return {**await rs.privacy(db), "default": rs.PRIVACY_DEFAULT}


@router.put("/system/privacy-settings")
async def put_privacy(payload: PrivacyIn, db: AsyncSession = Depends(get_db)):
    try:
        return await rs.set_privacy(db, payload.k_min, payload.dominance_pct)
    except rs.ReportError as exc:
        raise HTTPException(status_code=exc.status, detail=str(exc))
