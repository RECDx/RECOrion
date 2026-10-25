"""
Bağlantı kataloğu uçları (ADIM 12.1).

Herkes (giriş yapmış):
- GET  /integrations/catalog                       etkin kartlar (kimlik bilgisi yok)
- GET  /integrations/objects                       ortak iş nesneleri ve alanları (ADIM 12.2)
- POST /integrations/objects/{type}/validate       nesneyi doğrular (hatalar Türkçe, alan etiketli)
Şirket (integration:manage):
- POST /company/{tid}/integrations/advise          RECAi bağlanma rehberi (şirketin kredisinden)
Süper Admin (RECDx):
- GET  /system/integration-catalog                 tüm kartlar (arşivliler dahil)
- POST /system/integration-catalog                 yeni kart
- PUT  /system/integration-catalog/{id}            kartı düzenle / arşivle
"""
import uuid
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import CurrentUser, ensure_tenant_content, forbidden, get_current_user
from app.db.models import IntegrationCatalogEntry
from app.db.session import get_db
from app.integrations import oauth
from app.services import business_objects
from app.services import integration_catalog as cat
from app.services.llm_gateway import LLMError

router = APIRouter(tags=["Bağlantı Kataloğu"])


def _super(user: CurrentUser) -> None:
    if not user.is_super_admin:
        raise HTTPException(status_code=403, detail="Bu işlem yalnızca RECDx Süper Admin içindir.")


@router.get("/integrations/catalog")
async def catalog(user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    from app.db.models import Tenant

    tenant = None if user.is_platform_staff else await db.get(Tenant, user.tenant_id)
    return {"entries": [cat.out(e) for e in await cat.active(db, tenant)], "categories": list(cat.CATEGORIES),
            "methods": cat.METHOD_LABEL, "redirect_uri": oauth.redirect_uri()}


@router.get("/integrations/objects")
async def objects(user: CurrentUser = Depends(get_current_user)):
    return {"version": business_objects.VERSION, "objects": business_objects.catalog()}


@router.post("/integrations/objects/{object_type}/validate")
async def validate_object(object_type: str, payload: Dict[str, Any], user: CurrentUser = Depends(get_current_user)):
    if object_type not in business_objects.OBJECTS:
        raise HTTPException(status_code=404, detail="Bilinmeyen nesne türü.")
    clean, errors = business_objects.validate(object_type, payload)
    return {"ok": not errors, "object": clean, "errors": errors}


class AdviseIn(BaseModel):
    text: str = Field(..., min_length=3, max_length=1500)


@router.post("/company/{tenant_id}/integrations/advise")
async def advise(tenant_id: uuid.UUID, payload: AdviseIn, user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    ensure_tenant_content(user, tenant_id)
    if not user.has("integration:manage"):
        raise forbidden("Entegrasyonları yalnızca entegrasyon yönetimi yetkisi olanlar yönetebilir.")
    try:
        return await cat.advise(db, tenant_id, user.actor_id, payload.text)
    except LLMError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message)
    except ValueError as exc:
        raise HTTPException(status_code=503, detail=str(exc))


class EntryIn(BaseModel):
    code: Optional[str] = Field(None, max_length=64)
    title: str = Field(..., min_length=2, max_length=120)
    vendor: Optional[str] = Field(None, max_length=120)
    category: str
    method: str
    connector: Optional[str] = None
    preset: Dict[str, Any] = Field(default_factory=dict)
    description: Optional[str] = Field(None, max_length=2000)
    setup_steps: List[str] = Field(default_factory=list, max_length=12)
    keywords: Optional[str] = Field(None, max_length=500)
    sort: int = 100
    requires_app: Optional[str] = None
    status: Optional[str] = Field(None, pattern="^(ACTIVE|ARCHIVED)$")


@router.get("/system/integration-catalog")
async def admin_list(user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    _super(user)
    rows = (await db.execute(select(IntegrationCatalogEntry).order_by(IntegrationCatalogEntry.sort, IntegrationCatalogEntry.title))).scalars()
    return {"entries": [cat.out(e) for e in rows], "categories": list(cat.CATEGORIES), "methods": cat.METHOD_LABEL}


@router.post("/system/integration-catalog", status_code=201)
async def admin_create(payload: EntryIn, user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    _super(user)
    code = (payload.code or "").strip()
    if not cat.CODE.match(code):
        raise HTTPException(status_code=422, detail="Kod küçük harf, rakam ve alt çizgiden oluşmalı (ör. logo_tiger).")
    if (await db.execute(select(IntegrationCatalogEntry.id).where(IntegrationCatalogEntry.code == code))).first():
        raise HTTPException(status_code=409, detail="Bu kodla bir kart zaten var.")
    try:
        data = cat.validate(payload.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    e = IntegrationCatalogEntry(code=code, **data)
    db.add(e)
    await db.commit()
    return cat.out(e)


@router.put("/system/integration-catalog/{entry_id}")
async def admin_update(entry_id: uuid.UUID, payload: EntryIn, user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    _super(user)
    e = await db.get(IntegrationCatalogEntry, entry_id)
    if not e:
        raise HTTPException(status_code=404, detail="Kart bulunamadı.")
    try:
        data = cat.validate(payload.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    for k, v in data.items():
        setattr(e, k, v)
    if payload.status:
        e.status = payload.status
    await db.commit()
    return cat.out(e)
