import os
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    PROJECT_NAME: str = "RECOrion"
    ENVIRONMENT: str = "local_dev"
    DEBUG: bool = True
    SECRET_KEY: str = ""  # .env üzerinden verilir

    # PostgreSQL
    POSTGRES_USER: str = "recorion_admin"
    POSTGRES_PASSWORD: str = ""  # .env üzerinden verilir
    POSTGRES_DB: str = "recorion_db"
    POSTGRES_HOST: str = "postgres"
    POSTGRES_PORT: int = 5432
    DATABASE_URL: Optional[str] = None

    # Qdrant
    QDRANT_HOST: str = "qdrant"
    QDRANT_PORT: int = 6333
    QDRANT_COLLECTION_NAME: str = "recorion_collective_memory"

    # Redis
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: Optional[str] = None

    # MinIO
    MINIO_ROOT_USER: str = "minio_admin"
    MINIO_ROOT_PASSWORD: str = ""  # .env üzerinden verilir
    MINIO_ENDPOINT: str = "minio:9000"
    MINIO_BUCKET_NAME: str = "recorion-artifacts"
    MINIO_USE_SSL: bool = False

    # EVREN LLM Gateway (TÜBİTAK BİLGEM & SSB SAYZEK EVREN)
    EVREN_API_BASE_URL: str = "https://evren-llmapi.ssyz.org.tr/v1"
    EVREN_API_KEY: str = ""  # .env üzerinden verilir
    LLM_TIMEOUT_SECONDS: int = 120

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

    def get_database_url(self) -> str:
        if self.DATABASE_URL:
            # asyncpg protokolü kontrolü
            if self.DATABASE_URL.startswith("postgresql://"):
                return self.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)
            return self.DATABASE_URL
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"


settings = Settings()
