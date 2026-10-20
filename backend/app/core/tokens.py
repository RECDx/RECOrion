"""
Redis tabanlı kısa ömürlü güvenlik yardımcıları:
- İstek sınırı (rate limit)
- E-posta doğrulama kodu (6 hane, 10 dk, en fazla 5 deneme)
- Tek kullanımlık bağlantı token'ları (şifre belirleme / sıfırlama)

Redis'te kodların ve token'ların yalnızca SHA-256 özeti tutulur.
"""
import hashlib
import hmac
import logging
import secrets
from typing import Optional

import redis.asyncio as aioredis

from app.config import settings

logger = logging.getLogger("recorion.tokens")

EMAIL_CODE_TTL_MINUTES = 10
EMAIL_CODE_MAX_ATTEMPTS = 5


def _digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def redis_client() -> aioredis.Redis:
    return aioredis.from_url(
        f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB}",
        password=settings.REDIS_PASSWORD or None,
        decode_responses=True,
    )


async def hit_rate_limit(key: str, limit: int, window_seconds: int) -> bool:
    """Sınır aşıldıysa True döner. Redis erişilemezse istek engellenmez (loglanır)."""
    try:
        client = redis_client()
        try:
            full = f"ratelimit:{key}"
            count = await client.incr(full)
            if count == 1:
                await client.expire(full, window_seconds)
            return count > limit
        finally:
            await client.aclose()
    except Exception as exc:
        logger.warning("İstek sınırı kontrol edilemedi (%s): %s", key, exc)
        return False


# ---------------------------------------------------------------- e-posta doğrulama kodu
async def issue_email_code(email: str) -> str:
    code = f"{secrets.randbelow(1_000_000):06d}"
    client = redis_client()
    try:
        await client.set(f"emailcode:{email}", _digest(code), ex=EMAIL_CODE_TTL_MINUTES * 60)
        await client.delete(f"emailcode:attempts:{email}")
    finally:
        await client.aclose()
    return code


async def verify_email_code(email: str, code: str) -> bool:
    """Doğruysa kodu tüketir. Fazla deneme kodu geçersiz kılar."""
    client = redis_client()
    try:
        stored = await client.get(f"emailcode:{email}")
        if not stored:
            return False
        attempts = await client.incr(f"emailcode:attempts:{email}")
        await client.expire(f"emailcode:attempts:{email}", EMAIL_CODE_TTL_MINUTES * 60)
        if attempts > EMAIL_CODE_MAX_ATTEMPTS:
            await client.delete(f"emailcode:{email}")
            return False
        if hmac.compare_digest(stored, _digest((code or "").strip())):
            await client.delete(f"emailcode:{email}", f"emailcode:attempts:{email}")
            return True
        return False
    finally:
        await client.aclose()


# ---------------------------------------------------------------- tek kullanımlık bağlantılar
async def issue_link_token(purpose: str, subject_id: str, ttl_seconds: int) -> str:
    token = secrets.token_urlsafe(32)
    client = redis_client()
    try:
        await client.set(f"linktoken:{purpose}:{_digest(token)}", subject_id, ex=ttl_seconds)
    finally:
        await client.aclose()
    return token


async def consume_link_token(purpose: str, token: str) -> Optional[str]:
    if not token:
        return None
    client = redis_client()
    try:
        key = f"linktoken:{purpose}:{_digest(token)}"
        subject_id = await client.get(key)
        if subject_id:
            await client.delete(key)
        return subject_id
    finally:
        await client.aclose()
