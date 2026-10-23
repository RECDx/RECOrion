"""
Canlı akış (ADIM 8.2): proje kanalına anlık olaylar (Redis pub/sub → WebSocket).

- Yeni mesaj (chat_messages) ve iş akışı olayı (task_events) veritabanına yazılıp işlem tamamlandığında kendiliğinden
  yayınlanır: SQLAlchemy oturum kancaları eklenen kayıtları toplar, commit sonrası gönderir (geri alınan işlem yayınlanmaz).
- AI düşünce adımları (`thought`) doğrudan yayınlanır; kalıcı değildir.
- Abone olmak için kısa ömürlü, tek kullanımlık bilet gerekir (tarayıcı WebSocket'e Authorization başlığı ekleyemez).
"""
import asyncio
import json
import logging
import secrets
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import event
from sqlalchemy.orm import Session

from app.core.tokens import _digest, redis_client
from app.db.models import ChatMessage, TaskEvent

logger = logging.getLogger("recorion.live")

TICKET_TTL_SECONDS = 60
CONTENT_PREVIEW = 20000  # tek olayda gönderilen en fazla mesaj metni (tamamı geçmişten okunabilir)


def channel(project_id) -> str:
    return f"live:project:{project_id}"


def _iso(v) -> Optional[str]:
    return v.isoformat() if isinstance(v, datetime) else v


def message_event(m: ChatMessage) -> Dict[str, Any]:
    return {"type": "message", "project_id": str(m.project_id), "task_id": str(m.task_id) if m.task_id else None, "message": {
        "id": str(m.id), "task_id": str(m.task_id) if m.task_id else None, "project_id": str(m.project_id),
        "sender_actor_id": str(m.sender_actor_id) if m.sender_actor_id else None, "sender_name": m.sender_name,
        "role": m.role, "content": (m.content or "")[:CONTENT_PREVIEW], "thought_process": m.thought_process,
        "attachments": m.attachments or [], "is_private": bool(m.is_private),
        "visible_to_actor_id": str(m.visible_to_actor_id) if m.visible_to_actor_id else None, "message_type": m.message_type or "CHAT",
        "created_at": _iso(m.created_at)}}


def task_event(e: TaskEvent) -> Dict[str, Any]:
    return {"type": "task_event", "project_id": str(e.project_id), "task_id": str(e.task_id) if e.task_id else None,
            "kind": e.kind, "note": (e.note or "")[:500] or None, "actor_id": str(e.actor_id) if e.actor_id else None,
            "created_at": _iso(e.created_at) or datetime.now(timezone.utc).isoformat()}


async def publish(project_id, payload: Dict[str, Any]) -> None:
    """Yayın hatası işi durdurmaz (canlı akış yardımcıdır; kayıt veritabanındadır)."""
    try:
        client = redis_client()
        try:
            await client.publish(channel(project_id), json.dumps(payload, ensure_ascii=False, default=str))
        finally:
            await client.aclose()
    except Exception as exc:
        logger.warning("Canlı olay yayınlanamadı (%s): %s", project_id, exc)


async def thought(project_id, task_id, step: str, text: str) -> None:
    """AI'ın o an ne yaptığı (Bilgi taranıyor, Çıktı yazılıyor, Kontrol ediliyor...)."""
    if project_id:
        await publish(project_id, {"type": "thought", "project_id": str(project_id), "task_id": str(task_id) if task_id else None,
                                   "step": step, "text": text[:500], "created_at": datetime.now(timezone.utc).isoformat()})


# ---------------------------------------------------------------- commit sonrası otomatik yayın
@event.listens_for(Session, "after_flush")
def _collect(session: Session, flush_context) -> None:
    """Olay, kayıt yazıldığı anda hazırlanır (commit sonrası nesne alanlarına dokunulmaz)."""
    new = [o for o in session.new if isinstance(o, (ChatMessage, TaskEvent)) and o.project_id]
    if not new:
        return
    # sender_name veritabanı tetikleyicisinde dolar: aynı işlem içinden okunur
    missing = {o.sender_actor_id for o in new if isinstance(o, ChatMessage) and not o.sender_name and o.sender_actor_id}
    names: Dict[Any, str] = {}
    if missing:
        from app.db.models import Actor
        from sqlalchemy import select
        names = dict(session.connection().execute(select(Actor.id, Actor.display_name).where(Actor.id.in_(missing))).all())
    pending = session.info.setdefault("live_pending", [])
    for o in new:
        if isinstance(o, ChatMessage):
            payload = message_event(o)
            payload["message"]["sender_name"] = payload["message"]["sender_name"] or names.get(o.sender_actor_id)
        else:
            payload = task_event(o)
        pending.append((o.project_id, payload))


@event.listens_for(Session, "after_commit")
def _send(session: Session) -> None:
    pending: List[Any] = session.info.pop("live_pending", [])
    if not pending:
        return
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:  # eşzamanlı betik/test oturumu: canlı yayın yok
        return
    # Sıra korunur (mesajlar yazıldığı sırayla gelir); göreve referans tutulur, yoksa bitmeden çöpe gidebilir
    task = loop.create_task(_publish_all(pending))
    _background.add(task)
    task.add_done_callback(_background.discard)


_background: set = set()


async def _publish_all(pending: List[Any]) -> None:
    for pid, payload in pending:
        await publish(pid, payload)


@event.listens_for(Session, "after_rollback")
def _drop(session: Session) -> None:
    session.info.pop("live_pending", None)


# ---------------------------------------------------------------- bilet
async def issue_ticket(actor_id, project_id) -> str:
    ticket = secrets.token_urlsafe(24)
    client = redis_client()
    try:
        await client.set(f"liveticket:{_digest(ticket)}", json.dumps({"actor_id": str(actor_id), "project_id": str(project_id)}),
                         ex=TICKET_TTL_SECONDS)
    finally:
        await client.aclose()
    return ticket


async def redeem_ticket(ticket: str, project_id: uuid.UUID) -> Optional[uuid.UUID]:
    """Bileti tüketir; geçerliyse ve aynı proje içinse kişinin kimliğini döner."""
    if not ticket or len(ticket) > 100:
        return None
    client = redis_client()
    try:
        raw = await client.getdel(f"liveticket:{_digest(ticket)}")
    finally:
        await client.aclose()
    if not raw:
        return None
    data = json.loads(raw)
    if data.get("project_id") != str(project_id):
        return None
    return uuid.UUID(data["actor_id"])
