from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
from app.config import settings
from app.api.router import api_router
from app.core.audit import AuditMiddleware

logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("recorion_app")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("=" * 60)
    logger.info("🚀 RECOrion FastAPI Backend Çekirdeği Başlatılıyor...")
    logger.info(f"   Ortam: {settings.ENVIRONMENT}")
    logger.info(f"   Dark DB: {settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}")
    logger.info(f"   Qdrant Vektör: {settings.QDRANT_HOST}:{settings.QDRANT_PORT}")
    logger.info(f"   Redis Stream: {settings.REDIS_HOST}:{settings.REDIS_PORT}")
    logger.info("=" * 60)
    scheduler_task = None
    if settings.SCHEDULER_ENABLED:
        import asyncio
        from app.services.scheduler_service import scheduler_loop
        scheduler_task = asyncio.create_task(scheduler_loop())
    yield
    if scheduler_task:
        scheduler_task.cancel()
    logger.info("🛑 RECOrion Backend Durduruluyor...")


app = FastAPI(
    title="RECOrion API",
    description="Operational Reasoning & Intelligence Orchestration Network - Çekirdek Backend API",
    version="3.0.0",
    lifespan=lifespan
)

# Denetim kaydı: tüm değişiklik istekleri ve giriş denemeleri
app.add_middleware(AuditMiddleware)

# CORS Middleware (yalnızca izinli frontend adresleri, .env: CORS_ORIGINS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

# Yapay zeka hataları: sahte yanıt yerine anlaşılır hata (503 servis yok, 402 kredi, 403 model izni)
from fastapi import Request as _Request
from fastapi.responses import JSONResponse
from app.services.llm_gateway import LLMError


@app.exception_handler(LLMError)
async def llm_error_handler(request: _Request, exc: LLMError):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})


# API Rotaları
app.include_router(api_router)


@app.get("/", tags=["Root"])
async def root():
    return {
        "project": "RECOrion",
        "description": "Operational Reasoning & Intelligence Orchestration Network",
        "version": "3.0.0",
        "docs_url": "/docs",
        "api_v1_health": "/api/v1/health"
    }
