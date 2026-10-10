from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
from app.config import settings
from app.api.router import api_router

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
    yield
    logger.info("🛑 RECOrion Backend Durduruluyor...")


app = FastAPI(
    title="RECOrion API",
    description="Operational Reasoning & Intelligence Orchestration Network - Çekirdek Backend API",
    version="3.0.0",
    lifespan=lifespan
)

# CORS Middleware (Frontend Work Area Bağlantısı)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
