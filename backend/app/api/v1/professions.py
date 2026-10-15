"""
Türkiye Ticaret Bakanlığı Meslek Tanımı Modülü (Madde 1).
- Meslek Kodu (code: örn: A.01, A.02...)
- Sektör Kodu (sector_code: örn: A)
- Meslek Tanım Adı (name: örn: Kerestecilik)
"""
import logging
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select, or_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.db.models import Profession, Sector

logger = logging.getLogger("professions_api")

router = APIRouter(prefix="/professions", tags=["Meslek Tanımı Modülü"])


class ProfessionCreate(BaseModel):
    code: str = Field(..., description="Meslek Kodu (örn: A.01, A.02)")
    sector_code: str = Field(..., description="Bağlı Olduğu Sektör Kodu (örn: A)")
    name: str = Field(..., description="Meslek Tanım Adı (örn: Kerestecilik)")
    description: Optional[str] = None
    is_active: bool = True


class ProfessionUpdate(BaseModel):
    sector_code: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class ProfessionOut(BaseModel):
    code: str
    sector_code: str
    sector_name: Optional[str] = None
    name: str
    description: Optional[str] = None
    is_active: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


@router.get("/", response_model=List[ProfessionOut])
async def list_professions(
    sector_code: Optional[str] = Query(None, description="Sektör koduna göre filtrele (örn: A)"),
    q: Optional[str] = Query(None, description="Meslek kodu veya adında arama"),
    is_active: Optional[bool] = Query(None, description="Aktiflik filtresi"),
    limit: int = Query(500, description="Maksimum kayıt sayısı"),
    offset: int = Query(0, description="Öteleme"),
    db: AsyncSession = Depends(get_db)
):
    """
    Meslek Tanımlarını listeler.
    """
    stmt = select(Profession, Sector.name.label("sec_name")).outerjoin(
        Sector, Profession.sector_code == Sector.code
    )

    if sector_code and sector_code.strip():
        stmt = stmt.where(Profession.sector_code == sector_code.strip().upper())

    if q and q.strip():
        term = f"%{q.strip().lower()}%"
        stmt = stmt.where(
            or_(
                func.lower(Profession.code).ilike(term),
                func.lower(Profession.name).ilike(term)
            )
        )

    if is_active is not None:
        stmt = stmt.where(Profession.is_active == is_active)

    stmt = stmt.order_by(Profession.code.asc()).limit(limit).offset(offset)
    res = await db.execute(stmt)
    rows = res.all()

    result = []
    for prof, sec_name in rows:
        result.append(ProfessionOut(
            code=prof.code,
            sector_code=prof.sector_code,
            sector_name=sec_name,
            name=prof.name,
            description=prof.description,
            is_active=prof.is_active,
            created_at=prof.created_at,
            updated_at=prof.updated_at
        ))
    return result


@router.get("/{code}", response_model=ProfessionOut)
async def get_profession(code: str, db: AsyncSession = Depends(get_db)):
    """
    Belirli bir meslek tanımının detaylarını döndürür.
    """
    clean_code = code.strip()
    prof = await db.get(Profession, clean_code)
    if not prof:
        raise HTTPException(status_code=404, detail=f"'{clean_code}' kodlu meslek tanımı bulunamadı.")

    sector = await db.get(Sector, prof.sector_code) if prof.sector_code else None

    return ProfessionOut(
        code=prof.code,
        sector_code=prof.sector_code,
        sector_name=sector.name if sector else None,
        name=prof.name,
        description=prof.description,
        is_active=prof.is_active,
        created_at=prof.created_at,
        updated_at=prof.updated_at
    )


@router.post("/", response_model=ProfessionOut, status_code=201)
async def create_profession(payload: ProfessionCreate, db: AsyncSession = Depends(get_db)):
    """
    Yeni Meslek Tanımı oluşturur.
    """
    clean_code = payload.code.strip()
    clean_sec_code = payload.sector_code.strip().upper()
    clean_name = payload.name.strip()

    if not clean_code:
        raise HTTPException(status_code=400, detail="Meslek kodu zorunludur.")
    if not clean_sec_code:
        raise HTTPException(status_code=400, detail="Bağlı olacağı sektör kodu zorunludur.")
    if not clean_name:
        raise HTTPException(status_code=400, detail="Meslek tanım adı zorunludur.")

    sector = await db.get(Sector, clean_sec_code)
    if not sector:
        raise HTTPException(status_code=400, detail=f"'{clean_sec_code}' kodlu ana sektör bulunamadı.")

    existing = await db.get(Profession, clean_code)
    if existing:
        raise HTTPException(status_code=400, detail=f"'{clean_code}' kodlu meslek tanımı zaten mevcuttur.")

    prof = Profession(
        code=clean_code,
        sector_code=clean_sec_code,
        name=clean_name,
        description=payload.description.strip() if payload.description else None,
        is_active=payload.is_active
    )
    db.add(prof)
    await db.commit()
    await db.refresh(prof)

    return ProfessionOut(
        code=prof.code,
        sector_code=prof.sector_code,
        sector_name=sector.name,
        name=prof.name,
        description=prof.description,
        is_active=prof.is_active,
        created_at=prof.created_at,
        updated_at=prof.updated_at
    )


@router.put("/{code}", response_model=ProfessionOut)
async def update_profession(code: str, payload: ProfessionUpdate, db: AsyncSession = Depends(get_db)):
    """
    Mevcut Meslek Tanımını günceller.
    """
    clean_code = code.strip()
    prof = await db.get(Profession, clean_code)
    if not prof:
        raise HTTPException(status_code=404, detail=f"'{clean_code}' kodlu meslek tanımı bulunamadı.")

    if payload.sector_code is not None:
        clean_sec_code = payload.sector_code.strip().upper()
        sector = await db.get(Sector, clean_sec_code)
        if not sector:
            raise HTTPException(status_code=400, detail=f"'{clean_sec_code}' kodlu ana sektör bulunamadı.")
        prof.sector_code = clean_sec_code

    if payload.name is not None:
        if not payload.name.strip():
            raise HTTPException(status_code=400, detail="Meslek tanım adı boş bırakılamaz.")
        prof.name = payload.name.strip()

    if payload.description is not None:
        prof.description = payload.description.strip() if payload.description else None

    if payload.is_active is not None:
        prof.is_active = payload.is_active

    prof.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(prof)

    sector = await db.get(Sector, prof.sector_code) if prof.sector_code else None

    return ProfessionOut(
        code=prof.code,
        sector_code=prof.sector_code,
        sector_name=sector.name if sector else None,
        name=prof.name,
        description=prof.description,
        is_active=prof.is_active,
        created_at=prof.created_at,
        updated_at=prof.updated_at
    )


@router.delete("/{code}")
async def delete_profession(code: str, db: AsyncSession = Depends(get_db)):
    """
    Meslek Tanımını siler.
    """
    clean_code = code.strip()
    prof = await db.get(Profession, clean_code)
    if not prof:
        raise HTTPException(status_code=404, detail=f"'{clean_code}' kodlu meslek tanımı bulunamadı.")

    prof_name = prof.name
    await db.delete(prof)
    await db.commit()

    return {
        "success": True,
        "message": f"'{prof_name}' ({clean_code}) meslek tanımı başarıyla silindi."
    }
