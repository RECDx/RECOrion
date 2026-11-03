"""Şirketin resmi logosu: gösterme (herkese açık), yükleme ve kaldırma (şirket yöneticisi veya RECDx süper yönetici)."""
import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Tenant
from app.db.session import get_db
from app.services import storage, tenant_logo

router = APIRouter(tags=["Şirket Logosu"])


async def _tenant(db: AsyncSession, tenant_id: uuid.UUID) -> Tenant:
    tenant = await db.get(Tenant, tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Şirket bulunamadı.")
    return tenant


@router.get("/public/tenant-logo/{tenant_id}")
async def get_logo(tenant_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Logo görseli (PNG). Adres sürümlü (?v=) olduğundan uzun süre önbelleğe alınabilir."""
    tenant = await db.get(Tenant, tenant_id)
    if not tenant or not tenant.logo_key:
        raise HTTPException(status_code=404, detail="Logo bulunamadı.")
    try:
        data = await storage.get_object(tenant.logo_key)
    except storage.StorageError:
        raise HTTPException(status_code=404, detail="Logo bulunamadı.")
    return Response(content=data, media_type="image/png", headers={
        "Cache-Control": "public, max-age=31536000, immutable", "X-Content-Type-Options": "nosniff",
        "Content-Security-Policy": "default-src 'none'"})


@router.put("/company/{tenant_id}/logo")
async def upload_logo(tenant_id: uuid.UUID, file: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    tenant = await _tenant(db, tenant_id)
    data = await file.read(tenant_logo.MAX_BYTES + 1)
    await tenant_logo.save(tenant, tenant_logo.normalize(data))
    await db.commit()
    return {"success": True, "message": "Şirket logosu kaydedildi.", "logo_url": tenant_logo.url_of(tenant)}


@router.delete("/company/{tenant_id}/logo")
async def delete_logo(tenant_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    tenant = await _tenant(db, tenant_id)
    await tenant_logo.remove(tenant)
    await db.commit()
    return {"success": True, "message": "Şirket logosu kaldırıldı.", "logo_url": None}
