import os
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    PROJECT_NAME: str = "RECOrion"
    ENVIRONMENT: str = "local_dev"
    DEBUG: bool = True
    SECRET_KEY: str = ""  # .env üzerinden verilir

    # Kimlik doğrulama (JWT)
    ACCESS_TOKEN_HOURS: int = 12
    REMEMBER_ME_DAYS: int = 30
    LOGIN_MAX_FAILED_ATTEMPTS: int = 5
    LOGIN_LOCK_MINUTES: int = 15

    # Virgülle ayrılmış izinli frontend adresleri
    CORS_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173"

    # SQL sorgularını loglar (parametreler dahil); yalnızca yerel hata ayıklamada açın
    DB_ECHO: bool = False

    # Müşterilere giden e-postalardaki bağlantıların kök adresi
    PUBLIC_APP_URL: str = "http://localhost:5173"
    # RECDx'e yeni başvuru bildirimlerinin gideceği adres
    ADMIN_NOTIFICATION_EMAIL: str = "info@recdx.com"
    # smtp: gerçek gönderim · log: göndermeden bellekte tut (test/geliştirme)
    EMAIL_DELIVERY: str = "smtp"
    # SMTP sunucusunun TLS sertifikası doğrulansın mı (kendinden imzalı sertifikalı sunucularda false; bağlantı yine şifrelidir)
    SMTP_TLS_VERIFY: bool = True
    # Odoo satış siparişi senkronizasyonu (testlerde kapalı)
    ODOO_SYNC_ENABLED: bool = True
    ODOO_PRICELIST_ID: int = 1
    # Otomatik zamanlayıcı (mail hatırlatmaları)
    SCHEDULER_ENABLED: bool = True
    SCHEDULER_INTERVAL_MINUTES: int = 60
    # Web başvurusu kötüye kullanım sınırları (IP başına, saatlik)
    PURCHASE_IP_LIMIT_PER_HOUR: int = 5
    EMAIL_CODE_IP_LIMIT_PER_HOUR: int = 20

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
    REDIS_DB: int = 0  # testler ayrı veritabanı kullanır

    # MinIO
    MINIO_ROOT_USER: str = "minio_admin"
    MINIO_ROOT_PASSWORD: str = ""  # .env üzerinden verilir
    MINIO_ENDPOINT: str = "minio:9000"
    MINIO_BUCKET_NAME: str = "recorion-artifacts"
    MINIO_USE_SSL: bool = False
    MINIO_DOCUMENTS_BUCKET: str = "recorion-documents"  # öğrenme dokümanları (ADIM 5.4)

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
