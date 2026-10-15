"""
Türkiye Ticaret Bakanlığı Sektör Tanımlama Modülü (Madde 1).
- Sektör Kodu (code: örn: A, B, C...)
- Sektör Adı (name: örn: AĞAÇ İŞLERİ)
"""
import logging
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.db.models import Sector, Profession

logger = logging.getLogger("sectors_api")

router = APIRouter(prefix="/sectors", tags=["Sektör Tanımlama Modülü"])


class SectorCreate(BaseModel):
    code: str = Field(..., description="Sektör Kodu (örn: A, B, C)")
    name: str = Field(..., description="Sektör Adı (örn: AĞAÇ İŞLERİ)")
    description: Optional[str] = None
    icon: Optional[str] = None
    image_url: Optional[str] = None
    is_active: bool = True


class SectorUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    icon: Optional[str] = None
    image_url: Optional[str] = None
    is_active: Optional[bool] = None


class SectorOut(BaseModel):
    code: str
    name: str
    description: Optional[str] = None
    icon: Optional[str] = None
    image_url: Optional[str] = None
    is_active: bool
    professions_count: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


@router.get("/", response_model=List[SectorOut])
async def list_sectors(
    q: Optional[str] = Query(None, description="Sektör kodu veya adında arama"),
    is_active: Optional[bool] = Query(None, description="Aktiflik filtresi"),
    db: AsyncSession = Depends(get_db)
):
    """
    Tüm sektörleri listeler.
    """
    stmt = select(
        Sector,
        func.count(Profession.code).label("prof_count")
    ).outerjoin(
        Profession, Sector.code == Profession.sector_code
    ).group_by(Sector.code)

    if q and q.strip():
        term = f"%{q.strip().lower()}%"
        stmt = stmt.where(
            or_(
                func.lower(Sector.code).ilike(term),
                func.lower(Sector.name).ilike(term)
            )
        )

    if is_active is not None:
        stmt = stmt.where(Sector.is_active == is_active)

    stmt = stmt.order_by(Sector.code.asc())
    res = await db.execute(stmt)
    rows = res.all()

    result = []
    for sector_obj, prof_cnt in rows:
        result.append(SectorOut(
            code=sector_obj.code,
            name=sector_obj.name,
            description=sector_obj.description,
            icon=sector_obj.icon,
            image_url=sector_obj.image_url,
            is_active=sector_obj.is_active,
            professions_count=prof_cnt or 0,
            created_at=sector_obj.created_at,
            updated_at=sector_obj.updated_at
        ))
    return result


@router.get("/{code}")
async def get_sector(code: str, db: AsyncSession = Depends(get_db)):
    """
    Belirli bir sektörün detaylarını ve altındaki meslek tanımlarını döndürür.
    """
    clean_code = code.strip().upper()
    sector = await db.get(Sector, clean_code)
    if not sector:
        raise HTTPException(status_code=404, detail=f"'{clean_code}' kodlu sektör bulunamadı.")

    p_stmt = select(Profession).where(Profession.sector_code == clean_code).order_by(Profession.code.asc())
    p_res = await db.execute(p_stmt)
    professions = p_res.scalars().all()

    return {
        "code": sector.code,
        "name": sector.name,
        "description": sector.description,
        "icon": sector.icon,
        "image_url": sector.image_url,
        "is_active": sector.is_active,
        "created_at": sector.created_at,
        "updated_at": sector.updated_at,
        "professions": [
            {
                "code": p.code,
                "name": p.name,
                "description": p.description,
                "is_active": p.is_active
            }
            for p in professions
        ]
    }


@router.post("/", response_model=SectorOut, status_code=201)
async def create_sector(payload: SectorCreate, db: AsyncSession = Depends(get_db)):
    """
    Yeni Sektör Tanımı oluşturur.
    """
    clean_code = payload.code.strip().upper()
    clean_name = payload.name.strip()

    if not clean_code:
        raise HTTPException(status_code=400, detail="Sektör kodu zorunludur.")
    if not clean_name:
        raise HTTPException(status_code=400, detail="Sektör adı zorunludur.")

    existing = await db.get(Sector, clean_code)
    if existing:
        raise HTTPException(status_code=400, detail=f"'{clean_code}' kodlu sektör zaten tanımlıdır.")

    sector = Sector(
        code=clean_code,
        name=clean_name,
        description=payload.description.strip() if payload.description else None,
        icon=payload.icon.strip() if payload.icon else None,
        image_url=payload.image_url.strip() if payload.image_url else None,
        is_active=payload.is_active
    )
    db.add(sector)
    await db.commit()
    await db.refresh(sector)

    return SectorOut(
        code=sector.code,
        name=sector.name,
        description=sector.description,
        icon=sector.icon,
        image_url=sector.image_url,
        is_active=sector.is_active,
        professions_count=0,
        created_at=sector.created_at,
        updated_at=sector.updated_at
    )


@router.put("/{code}", response_model=SectorOut)
async def update_sector(code: str, payload: SectorUpdate, db: AsyncSession = Depends(get_db)):
    """
    Mevcut Sektör Tanımını günceller.
    """
    clean_code = code.strip().upper()
    sector = await db.get(Sector, clean_code)
    if not sector:
        raise HTTPException(status_code=404, detail=f"'{clean_code}' kodlu sektör bulunamadı.")

    if payload.name is not None:
        if not payload.name.strip():
            raise HTTPException(status_code=400, detail="Sektör adı boş bırakılamaz.")
        sector.name = payload.name.strip()

    if payload.description is not None:
        sector.description = payload.description.strip() if payload.description else None

    if payload.icon is not None:
        sector.icon = payload.icon.strip() if payload.icon else None

    if payload.image_url is not None:
        sector.image_url = payload.image_url.strip() if payload.image_url else None

    if payload.is_active is not None:
        sector.is_active = payload.is_active

    sector.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(sector)

    prof_cnt = await db.scalar(
        select(func.count(Profession.code)).where(Profession.sector_code == clean_code)
    ) or 0

    return SectorOut(
        code=sector.code,
        name=sector.name,
        description=sector.description,
        icon=sector.icon,
        image_url=sector.image_url,
        is_active=sector.is_active,
        professions_count=prof_cnt,
        created_at=sector.created_at,
        updated_at=sector.updated_at
    )


@router.delete("/{code}")
async def delete_sector(code: str, db: AsyncSession = Depends(get_db)):
    """
    Sektör Tanımını ve altındaki meslek tanımlarını siler.
    """
    clean_code = code.strip().upper()
    sector = await db.get(Sector, clean_code)
    if not sector:
        raise HTTPException(status_code=404, detail=f"'{clean_code}' kodlu sektör bulunamadı.")

    sec_name = sector.name
    await db.delete(sector)
    await db.commit()

    return {
        "success": True,
        "message": f"'{sec_name}' ({clean_code}) sektörü ve ilişkili meslek tanımları başarıyla silindi."
    }
