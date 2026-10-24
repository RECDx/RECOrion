"""
RECOrion ilk açılış hazırlığı (her başlangıçta çalışır, idempotent).

`alembic upgrade head` sonrasında çalıştırılır:
1. Qdrant kolektif hafıza koleksiyonu yoksa oluşturulur (4096 boyut, Cosine).
2. RECORION_SUPERADMIN_EMAILS içindeki süper adminler yoksa RECDx ana şirketine
   eklenir. İlk şifre RECORION_SUPERADMIN_INITIAL_PASSWORD'dan okunur; şifre
   repoda tutulmaz. Mevcut kullanıcılara dokunulmaz.
3. Platform departman/unvan kataloğundaki eksik kayıtlar app/seed/catalog/*.json'dan eklenir.

Kullanım: python -m app.bootstrap
"""
import asyncio
import logging
import os

from qdrant_client import AsyncQdrantClient
from qdrant_client.http import models as qmodels
from sqlalchemy import select

from app.api.v1.auth import hash_password
from app.config import settings
from app.db.models import Actor, Tenant
from app.db.session import AsyncSessionLocal

logging.basicConfig(level=logging.INFO, format="%(levelname)s [bootstrap] %(message)s")
logger = logging.getLogger("recorion.bootstrap")

HQ_SLUG = "recdx_hq"
EMBEDDING_DIM = 4096


async def ensure_qdrant_collection() -> None:
    client = AsyncQdrantClient(host=settings.QDRANT_HOST, port=settings.QDRANT_PORT, check_compatibility=False)
    try:
        if await client.collection_exists(settings.QDRANT_COLLECTION_NAME):
            return
        await client.create_collection(
            collection_name=settings.QDRANT_COLLECTION_NAME,
            vectors_config=qmodels.VectorParams(size=EMBEDDING_DIM, distance=qmodels.Distance.COSINE),
        )
        logger.info("Qdrant koleksiyonu oluşturuldu: %s", settings.QDRANT_COLLECTION_NAME)
    finally:
        await client.close()


async def ensure_super_admins() -> None:
    emails = [e.strip().lower() for e in os.getenv("RECORION_SUPERADMIN_EMAILS", "").split(",") if e.strip()]
    if not emails:
        return
    initial_password = os.getenv("RECORION_SUPERADMIN_INITIAL_PASSWORD", "")

    async with AsyncSessionLocal() as db:
        hq = (await db.execute(select(Tenant).where(Tenant.slug == HQ_SLUG))).scalar_one_or_none()
        if not hq:
            logger.warning("'%s' ana şirketi bulunamadı; süper admin oluşturulmadı.", HQ_SLUG)
            return

        existing = set(
            (await db.execute(select(Actor.email).where(Actor.email.in_(emails)))).scalars().all()
        )
        missing = [e for e in emails if e not in existing]
        if not missing:
            return
        if not initial_password:
            logger.warning("Eksik süper adminler var (%s) ama RECORION_SUPERADMIN_INITIAL_PASSWORD tanımlı değil.", ", ".join(missing))
            return

        for email in missing:
            db.add(Actor(
                tenant_id=hq.id,
                actor_type="HUMAN",
                display_name=email.split("@")[0],
                email=email,
                role="SUPER_ADMIN",
                password_hash=hash_password(initial_password),
                autonomy_level="L3",
                status="IDLE",
            ))
        await db.commit()
        logger.info("Süper admin oluşturuldu: %s (ilk girişte şifreyi değiştirin)", ", ".join(missing))


async def ensure_catalog() -> None:
    from app.services.catalog_seed import load_catalog

    async with AsyncSessionLocal() as db:
        added = await load_catalog(db)
    if added["departments"] or added["titles"]:
        logger.info("Platform kataloğu yüklendi: %s departman, %s unvan", added["departments"], added["titles"])
    from app.services.project_templates import ensure_platform_templates

    async with AsyncSessionLocal() as db:
        n = await ensure_platform_templates(db)
    if n:
        logger.info("RECDx proje şablonları yüklendi: %s", n)


async def main() -> None:
    try:
        await ensure_qdrant_collection()
    except Exception as exc:  # Qdrant geçici olarak erişilemezse API yine de açılsın
        logger.warning("Qdrant koleksiyonu kontrol edilemedi: %s", exc)
    await ensure_super_admins()
    try:
        await ensure_catalog()
    except Exception as exc:  # katalog yüklenemese de API açılsın; hata loglanır
        logger.error("Platform kataloğu yüklenemedi: %s", exc)


if __name__ == "__main__":
    asyncio.run(main())
