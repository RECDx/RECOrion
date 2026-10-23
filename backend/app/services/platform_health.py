"""
Platform sağlık kontrolü (ADIM 9.4): Süper Admin panosundaki sabit "Aktif / Bağlı" rozetleri yerine gerçek ölçüm.

Her bileşen kısa zaman aşımıyla paralel denetlenir; sonuç 30 sn önbellekte tutulur (pano her açılışta servisleri yormasın).
Durumlar: OK, SLOW (yanıt yavaş), DOWN (erişilemiyor), OFF (bu kurulumda kapalı/yapılandırılmamış).
Yanıta anahtar, şifre veya bağlantı dizesi yazılmaz.
"""
import asyncio
import time
from typing import Any, Awaitable, Callable, Dict, List, Optional

import httpx
from sqlalchemy import text

from app.config import settings
from app.db.session import AsyncSessionLocal

TIMEOUT = 5.0
SLOW_MS = 2000
REMOTE_SLOW_MS = 4000  # internet üzerindeki servisler (EVREN, Odoo)
CACHE_SECONDS = 30
_cache: Dict[str, Any] = {"at": 0.0, "data": None}


async def _postgres() -> Optional[str]:
    async with AsyncSessionLocal() as db:
        await db.execute(text("SELECT 1"))
    return None


async def _redis() -> Optional[str]:
    from app.core.tokens import redis_client

    c = redis_client()
    try:
        await c.ping()
    finally:
        await c.aclose()
    return None


async def _qdrant() -> Optional[str]:
    async with httpx.AsyncClient(timeout=TIMEOUT) as c:
        r = await c.get(f"http://{settings.QDRANT_HOST}:{settings.QDRANT_PORT}/healthz")
    r.raise_for_status()
    return None


async def _minio() -> Optional[str]:
    from app.services import storage

    exists = await asyncio.to_thread(storage._get_client().bucket_exists, settings.MINIO_DOCUMENTS_BUCKET)
    return None if exists else "Belge kovası henüz oluşturulmamış (ilk yüklemede oluşur)."


async def _temporal() -> Optional[str]:
    if not settings.WORKFLOW_ENABLED:
        raise _Off("İş akışı motoru bu kurulumda kapalı.")
    from temporalio.client import Client

    client = await Client.connect(f"{settings.TEMPORAL_HOST}:{settings.TEMPORAL_PORT}", namespace=settings.TEMPORAL_NAMESPACE)
    await client.service_client.check_health()
    return None


async def _gitea() -> Optional[str]:
    if not settings.GITEA_TOKEN:
        raise _Off("Kod deposu sunucusu yapılandırılmamış.")
    async with httpx.AsyncClient(timeout=TIMEOUT) as c:
        r = await c.get(settings.GITEA_URL.rstrip("/") + "/api/v1/version")
    r.raise_for_status()
    return f"Gitea {r.json().get('version', '')}".strip()


async def _evren() -> Optional[str]:
    from app.services.evren_client import evren_client

    models = await asyncio.wait_for(evren_client.list_models(), timeout=TIMEOUT)
    return f"{len(models)} model listelendi"


async def _odoo() -> Optional[str]:
    import os
    import xmlrpc.client

    url = (os.getenv("ODOO_URL") or "").rstrip("/")  # odoo_service ile aynı kaynak
    if not settings.ODOO_SYNC_ENABLED or not url:
        raise _Off("Odoo eşitlemesi kapalı.")

    def version():
        return xmlrpc.client.ServerProxy(url + "/xmlrpc/2/common").version()

    v = await asyncio.wait_for(asyncio.to_thread(version), timeout=TIMEOUT)
    return f"Odoo {v.get('server_version', '')}".strip()


class _Off(Exception):
    pass


CHECKS: List[tuple] = [
    ("postgres", "PostgreSQL (veritabanı)", _postgres),
    ("redis", "Redis (canlı akış, oturum güvenliği)", _redis),
    ("qdrant", "Qdrant (hafıza vektörleri)", _qdrant),
    ("minio", "MinIO (belge ve çıktı deposu)", _minio),
    ("temporal", "Temporal (iş akışı motoru)", _temporal),
    ("gitea", "Gitea (proje kod depoları)", _gitea),
    ("evren", "EVREN LLM Gateway", _evren),
    ("odoo", "Odoo ERP", _odoo),
]
REMOTE = {"evren", "odoo"}


async def _run(key: str, name: str, fn: Callable[[], Awaitable[Optional[str]]]) -> Dict[str, Any]:
    start = time.monotonic()
    try:
        detail = await asyncio.wait_for(fn(), timeout=TIMEOUT + 1)
        ms = int((time.monotonic() - start) * 1000)
        slow = ms > (REMOTE_SLOW_MS if key in REMOTE else SLOW_MS)
        return {"key": key, "name": name, "status": "SLOW" if slow else "OK", "latency_ms": ms, "detail": detail}
    except _Off as exc:
        return {"key": key, "name": name, "status": "OFF", "latency_ms": None, "detail": str(exc)}
    except Exception as exc:  # erişilemiyor: yalnızca hata türü (bağlantı ayrıntısı/gizli bilgi yazılmaz)
        ms = int((time.monotonic() - start) * 1000)
        reason = "zaman aşımı" if isinstance(exc, asyncio.TimeoutError) else exc.__class__.__name__
        return {"key": key, "name": name, "status": "DOWN", "latency_ms": ms, "detail": f"Erişilemiyor ({reason})."}


async def check_all(force: bool = False) -> Dict[str, Any]:
    now = time.monotonic()
    if not force and _cache["data"] and now - _cache["at"] < CACHE_SECONDS:
        return _cache["data"]
    results = await asyncio.gather(*(_run(k, n, f) for k, n, f in CHECKS))
    down = [r for r in results if r["status"] == "DOWN"]
    overall = "DOWN" if any(r["key"] in ("postgres", "redis") for r in down) else ("DEGRADED" if down or any(r["status"] == "SLOW" for r in results) else "OK")
    data = {"status": overall, "checked_at": time.time(), "services": results}
    _cache.update(at=now, data=data)
    return data
