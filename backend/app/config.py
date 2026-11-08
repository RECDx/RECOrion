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
    # Telegram bildirimleri (ADIM 6.5): BotFather'dan alınan token ve botun kullanıcı adı (@ olmadan)
    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_BOT_USERNAME: str = ""
    # İş akışı motoru (ADIM 7): Temporal sunucusu; worker backend sürecinde çalışır
    WORKFLOW_ENABLED: bool = True
    TEMPORAL_HOST: str = "temporal"
    TEMPORAL_PORT: int = 7233
    TEMPORAL_NAMESPACE: str = "default"
    TEMPORAL_TASK_QUEUE: str = "recorion-main"
    # Web başvurusu kötüye kullanım sınırları (IP başına, saatlik)
    PURCHASE_IP_LIMIT_PER_HOUR: int = 5
    # Ücretsiz e-posta (gmail vb.) ile başvuru: yalnız yerel canlı test için .env ile açılır; varsayılan kapalı (kurumsal e-posta zorunlu)
    ALLOW_FREE_EMAIL_SIGNUP: bool = False
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

    # Gitea: proje kod depoları (ADIM 8.5). GITEA_URL backend'in eriştiği iç adres, GITEA_PUBLIC_URL kullanıcıya gösterilen
    GITEA_URL: str = "http://gitea:3000"
    GITEA_PUBLIC_URL: str = "http://localhost:3000"
    GITEA_TOKEN: str = ""  # .env üzerinden verilir; boşsa kod deposu özelliği kapalıdır
    # Kod Çalıştırma Ortamı (ADIM 16.2): yalnız iç ağdaki sandbox servisi; boşsa AI test koşusu kapalıdır
    SANDBOX_URL: str = ""

    # Entegrasyon kimlik kasası (ADIM 10.1): base64 32 bayt AES-256-GCM anahtarı. Boşsa bağlantı eklenemez.
    RECORION_VAULT_KEY: str = ""
    # Müşterinin girdiği dış adresler (Odoo, Gitea, MCP sunucusu) özel/yerel ağa gidemez (SSRF koruması, ADIM 10.4).
    # Yalnızca geliştirme/canlı testte açılır.
    INTEGRATIONS_ALLOW_PRIVATE_NETWORK: bool = False

    # EVREN LLM Gateway (TÜBİTAK BİLGEM & SSB SAYZEK EVREN)
    EVREN_API_BASE_URL: str = "https://evren-llmapi.ssyz.org.tr/v1"
    EVREN_API_KEY: str = ""  # .env üzerinden verilir
    LLM_TIMEOUT_SECONDS: int = 120
    # 08.11.2026 (EVREN yanıtı, #666): sohbet çağrıları akışlı; ilk token (düşünme dahil) bu sürede gelmezse model
    # meşgul sayılır ve çağrı kesilir (llm_gateway fallback=True ise yedek modele geçer). Kuyruktaki keep-alive sayılmaz.
    LLM_FIRST_TOKEN_TIMEOUT_SECONDS: int = 60
    # Düşünme modu kapatılan modeller (virgülle; chat_template_kwargs.enable_thinking=false). EVREN'de tüm sohbet
    # modelleri varsayılan olarak düşünür; düşünen modellerde max_tokens en az LLM_THINKING_MIN_TOKENS tutulur.
    EVREN_NO_THINKING_MODELS: str = "qwen3.8-flash-next"
    LLM_THINKING_MIN_TOKENS: int = 4096
    # 429 + Retry-After: en çok bu kadar saniye beklenip bir kez yeniden denenir; daha uzunsa hata döner.
    EVREN_RETRY_AFTER_MAX_SECONDS: int = 60

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
