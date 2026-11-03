"""
Şirketin resmi logosu (İSTEK: kayıt, Şirket Yönetimi ve Ana Merkez'den eklenir).

- Kabul: PNG, JPG, WEBP (en fazla 2 MB). SVG kabul edilmez (betik taşıyabilir).
- Görsel sunucuda yeniden çizilir: en uzun kenar 512 px, PNG (saydamlık korunur); EXIF/meta veri atılır.
- Depo: MinIO "{tenant_id}/logo/logo.png". Adres sürümlü olduğundan tarayıcı önbelleği güvenle kullanılır.
- Logo şirketin kamuya açık kimliğidir (kişisel/şirket içeriği değil); ekranlarda oturum belirteci olmadan gösterilir.
"""
import base64
import binascii
import io
from datetime import datetime, timezone
from typing import Optional

from fastapi import HTTPException

from app.db.models import Tenant
from app.services import storage

MAX_BYTES = 2 * 1024 * 1024
MAX_SIDE = 512
MIN_SIDE = 16
FORMATS = {"PNG", "JPEG", "WEBP"}


def key_of(tenant_id) -> str:
    return f"{tenant_id}/logo/logo.png"


def normalize(data: bytes) -> bytes:
    """Yüklenen görseli denetler ve 512 px PNG'ye çevirir; uygun değilse 400."""
    from PIL import Image, UnidentifiedImageError

    if not data:
        raise HTTPException(status_code=400, detail="Logo dosyası boş.")
    if len(data) > MAX_BYTES:
        raise HTTPException(status_code=400, detail="Logo en fazla 2 MB olabilir.")
    Image.MAX_IMAGE_PIXELS = 40_000_000  # sıkıştırma bombasına karşı
    try:
        img = Image.open(io.BytesIO(data))
        fmt = img.format
        img.load()
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError, ValueError):
        raise HTTPException(status_code=400, detail="Logo PNG, JPG veya WEBP biçiminde bir görsel olmalı.")
    if fmt not in FORMATS:
        raise HTTPException(status_code=400, detail="Logo PNG, JPG veya WEBP biçiminde olmalı (SVG ve diğerleri kabul edilmez).")
    if min(img.size) < MIN_SIDE:
        raise HTTPException(status_code=400, detail=f"Logo çok küçük (en az {MIN_SIDE}×{MIN_SIDE} piksel).")
    img = img.convert("RGBA")
    img.thumbnail((MAX_SIDE, MAX_SIDE))
    out = io.BytesIO()
    img.save(out, format="PNG", optimize=True)
    return out.getvalue()


def decode_data_url(value: Optional[str]) -> Optional[bytes]:
    """Kayıt formundan gelen "data:image/...;base64,..." değerini çözer (boşsa None)."""
    if not value:
        return None
    head, _, body = value.partition(",")
    if not head.startswith("data:image/") or ";base64" not in head or not body:
        raise HTTPException(status_code=400, detail="Logo görseli okunamadı.")
    try:
        return base64.b64decode(body, validate=True)
    except (binascii.Error, ValueError):
        raise HTTPException(status_code=400, detail="Logo görseli okunamadı.")


async def save(tenant: Tenant, png: bytes) -> None:
    """Normalize edilmiş PNG'yi depoya yazar; çağıran commit eder."""
    try:
        await storage.put_object(key_of(tenant.id), png, "image/png")
    except storage.StorageError:
        raise HTTPException(status_code=503, detail="Logo şu anda kaydedilemedi. Lütfen biraz sonra tekrar deneyin.")
    tenant.logo_key = key_of(tenant.id)
    tenant.logo_updated_at = datetime.now(timezone.utc)


async def remove(tenant: Tenant) -> None:
    if tenant.logo_key:
        await storage.delete_object(tenant.logo_key)
    tenant.logo_key, tenant.logo_updated_at = None, None


def url_of(tenant: Optional[Tenant]) -> Optional[str]:
    if not tenant or not tenant.logo_key:
        return None
    v = int(tenant.logo_updated_at.timestamp()) if tenant.logo_updated_at else 0
    return f"/api/v1/public/tenant-logo/{tenant.id}?v={v}"

