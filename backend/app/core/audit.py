"""
Değiştirilemez denetim kaydı (audit log).

Tüm değişiklik istekleri (POST/PUT/PATCH/DELETE) ve giriş denemeleri `audit_events`
tablosuna yazılır. Tablo veritabanı tetikleyicisiyle yalnızca eklemeye açıktır
(UPDATE/DELETE engellenir). KVKK gereği istek gövdesi kaydedilmez; yalnızca kim,
hangi şirket, hangi uç, sonuç kodu ve kaynak IP tutulur.
"""
import logging
import uuid
from typing import Optional

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.db.session import AsyncSessionLocal

logger = logging.getLogger("recorion.audit")

AUDITED_METHODS = {"POST", "PUT", "PATCH", "DELETE"}


def _client_ip(request: Request) -> Optional[str]:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else None


async def write_audit_event(
    *,
    action: str,
    actor_id: Optional[uuid.UUID] = None,
    tenant_id: Optional[uuid.UUID] = None,
    target_type: Optional[str] = None,
    target_id: Optional[str] = None,
    payload: Optional[dict] = None,
) -> None:
    from app.db.models import AuditEvent

    try:
        async with AsyncSessionLocal() as db:
            db.add(AuditEvent(
                action=action[:128],
                actor_id=actor_id,
                tenant_id=tenant_id,
                target_type=(target_type or "")[:64] or None,
                target_id=(target_id or "")[:64] or None,
                payload=payload or {},
            ))
            await db.commit()
    except Exception as exc:  # denetim kaydı yazılamazsa isteği bozma, ama logla
        logger.error("Denetim kaydı yazılamadı (%s): %s", action, exc)


class AuditMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        if request.method not in AUDITED_METHODS or not request.url.path.startswith("/api/v1/"):
            return response

        user = getattr(request.state, "user", None)
        route_path = getattr(request.state, "route_path", request.url.path)
        params = getattr(request.state, "path_params", None) or {}
        target_id = next((str(v) for k, v in reversed(list(params.items())) if k != "tenant_id"), None)
        tenant_id = getattr(request.state, "tenant_id", None) or (user.tenant_id if user else None)

        await write_audit_event(
            action=f"{request.method} {route_path}",
            actor_id=user.actor_id if user else getattr(request.state, "audit_actor_id", None),
            tenant_id=tenant_id,
            target_type=route_path.removeprefix("/api/v1/").split("/")[0],
            target_id=target_id,
            payload={
                "status": response.status_code,
                "ip": _client_ip(request),
                "cross_tenant": bool(user and tenant_id and user.tenant_id != tenant_id),
            },
        )
        return response
