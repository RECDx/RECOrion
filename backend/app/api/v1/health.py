from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.db.session import get_db
from app.config import settings
import httpx

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("")
@router.get("/")
async def health_check(db: AsyncSession = Depends(get_db)):
    """
    Sistem bileşenlerinin (PostgreSQL, Qdrant, Redis) anlık sağlık durumunu döndürür.
    """
    status = {
        "status": "healthy",
        "project": settings.PROJECT_NAME,
        "environment": settings.ENVIRONMENT,
        "services": {}
    }

    # 1. PostgreSQL Kontrolü
    try:
        res = await db.execute(text("SELECT 1"))
        status["services"]["postgres"] = "healthy" if res.scalar() == 1 else "unhealthy"
    except Exception as e:
        status["services"]["postgres"] = f"error: {str(e)}"
        status["status"] = "degraded"

    # 2. Qdrant Kontrolü
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.get(f"http://{settings.QDRANT_HOST}:{settings.QDRANT_PORT}/healthz")
            status["services"]["qdrant"] = "healthy" if resp.status_code == 200 else "unhealthy"
    except Exception as e:
        status["services"]["qdrant"] = f"error: {str(e)}"
        status["status"] = "degraded"

    # 3. Redis Kontrolü
    try:
        import redis.asyncio as aioredis
        r = aioredis.from_url(f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}", password=settings.REDIS_PASSWORD or None)
        pong = await r.ping()
        status["services"]["redis"] = "healthy" if pong else "unhealthy"
        await r.aclose()
    except Exception as e:
        status["services"]["redis"] = f"error: {str(e)}"
        status["status"] = "degraded"

    return status
