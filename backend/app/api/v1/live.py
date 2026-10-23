"""
Canlı akış uçları (ADIM 8.2).

- POST /api/v1/live/ticket: proje ekibindeki kullanıcıya 60 sn geçerli, tek kullanımlık WebSocket bileti verir.
- WS /ws/projects/{project_id}?ticket=...: proje kanalındaki olaylar (mesaj, iş akışı olayı, AI düşünce adımı).
  Erişim politikası HTTP isteklerine uygulandığı için WebSocket ucu api_router dışındadır; denetimi bilet ve
  bağlantı anındaki proje üyeliği kontrolü yapar. Özel mesajlar yalnızca gönderenine iletilir.
"""
import asyncio
import json
import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import CurrentUser, get_current_user, load_current_user
from app.core.tokens import redis_client
from app.db.models import Actor
from app.db.session import AsyncSessionLocal, get_db
from app.services import live
from app.services import projects as psvc

logger = logging.getLogger("recorion.live")

router = APIRouter(prefix="/live", tags=["Canlı Akış"])
ws_router = APIRouter()

HEARTBEAT_SECONDS = 25


class TicketIn(BaseModel):
    project_id: uuid.UUID


@router.post("/ticket")
async def create_ticket(payload: TicketIn, user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    await psvc.load(db, user, payload.project_id)
    return {"ticket": await live.issue_ticket(user.actor_id, payload.project_id), "expires_in": live.TICKET_TTL_SECONDS}


async def _authorize(project_id: uuid.UUID, ticket: str) -> uuid.UUID:
    actor_id = await live.redeem_ticket(ticket, project_id)
    if not actor_id:
        raise PermissionError("Bilet geçersiz veya süresi dolmuş.")
    async with AsyncSessionLocal() as db:
        actor = await db.get(Actor, actor_id)
        if not actor or actor.actor_type != "HUMAN" or actor.status == "DISABLED":
            raise PermissionError("Kullanıcı etkin değil.")
        try:
            await psvc.load(db, await load_current_user(db, actor), project_id)
        except HTTPException as exc:
            raise PermissionError(exc.detail)
    return actor_id


@ws_router.websocket("/ws/projects/{project_id}")
async def project_stream(websocket: WebSocket, project_id: uuid.UUID, ticket: str = ""):
    try:
        actor_id = await _authorize(project_id, ticket)
    except PermissionError as exc:
        await websocket.close(code=4403, reason=str(exc)[:120])
        return
    await websocket.accept()
    me = str(actor_id)
    client = redis_client()
    pubsub = client.pubsub()
    await pubsub.subscribe(live.channel(project_id))

    async def pump():
        async for msg in pubsub.listen():
            if msg.get("type") != "message":
                continue
            data = json.loads(msg["data"])
            m = data.get("message") or {}
            if m.get("is_private") and m.get("visible_to_actor_id") != me:  # özel yazışma yalnızca soran kişiye
                continue
            await websocket.send_text(msg["data"] if isinstance(msg["data"], str) else json.dumps(data))

    async def reader():
        while True:
            if (await websocket.receive_text()) == "ping":
                await websocket.send_text('{"type":"pong"}')

    async def heartbeat():
        while True:
            await asyncio.sleep(HEARTBEAT_SECONDS)
            await websocket.send_text('{"type":"ping"}')

    await websocket.send_text(json.dumps({"type": "ready", "project_id": str(project_id)}))
    tasks = [asyncio.create_task(c()) for c in (pump, reader, heartbeat)]
    try:
        done, _ = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
        for t in done:
            if t.exception() and not isinstance(t.exception(), (WebSocketDisconnect, RuntimeError)):
                logger.warning("Canlı akış bağlantısı kapandı: %s", t.exception())
    finally:
        for t in tasks:
            t.cancel()
        try:
            await pubsub.unsubscribe()
            await pubsub.aclose()
            await client.aclose()
        except Exception:
            pass
