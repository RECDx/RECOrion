"""
Telegram bildirimleri (ADIM 6.5).

Bağlama: kullanıcı profilinden tek kullanımlık kod alır, botu açıp "/start KOD" gönderir; bot dinleyicisi
(getUpdates uzun yoklama) kodu eşleştirip kullanıcının telegram_chat_id değerini kaydeder.
TELEGRAM_BOT_TOKEN tanımlı değilse Telegram kapalıdır; bildirimler yalnızca e-postayla gider.
"""
import asyncio
import logging
import secrets
from datetime import datetime, timezone
from typing import Optional

import httpx
from sqlalchemy import select

from app.config import settings
from app.db.models import Actor
from app.db.session import AsyncSessionLocal

logger = logging.getLogger("recorion.telegram")


class _MaskBotToken(logging.Filter):
    """İstek adresindeki (/bot<TOKEN>/...) bot token'ını loglarda gizler."""

    def filter(self, record: logging.LogRecord) -> bool:
        token = settings.TELEGRAM_BOT_TOKEN
        if token:
            msg = record.getMessage()
            if token in msg:
                record.msg, record.args = msg.replace(token, "***"), None
        return True


for _name in ("httpx", "httpcore.connection", "httpcore.http11", "recorion.telegram"):
    logging.getLogger(_name).addFilter(_MaskBotToken())

API = "https://api.telegram.org/bot{token}/{method}"
OFFSET_KEY = "recorion:telegram:offset"
LOCK_KEY = "recorion:telegram:poller"


def enabled() -> bool:
    return bool(settings.TELEGRAM_BOT_TOKEN)


def deep_link(code: str) -> Optional[str]:
    return f"https://t.me/{settings.TELEGRAM_BOT_USERNAME}?start={code}" if settings.TELEGRAM_BOT_USERNAME else None


def new_link_code() -> str:
    return secrets.token_hex(4).upper()  # 8 karakter


async def _call(method: str, payload: dict, timeout: float = 15) -> Optional[dict]:
    if not enabled():
        return None
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.post(API.format(token=settings.TELEGRAM_BOT_TOKEN, method=method), json=payload)
        data = resp.json()
        if not data.get("ok"):
            logger.warning("Telegram %s hatası: %s", method, data.get("description"))
            return None
        return data
    except (httpx.HTTPError, ValueError) as exc:
        logger.warning("Telegram %s çağrısı başarısız: %s", method, exc)
        return None


async def send_message(chat_id: Optional[str], text: str, reply_markup: Optional[dict] = None) -> bool:
    if not chat_id:
        return False
    payload = {"chat_id": chat_id, "text": text, "disable_web_page_preview": True}
    if reply_markup:
        payload["reply_markup"] = reply_markup
    return bool(await _call("sendMessage", payload))


REVISE_KEY = "recorion:telegram:revise:{chat}"


async def _decide(chat_id: str, raw: str, approve: bool, note: Optional[str]) -> str:
    """Telegram'dan gelen karar: belirtecin sahibi bu sohbetin bağlı olduğu kişi olmalı."""
    from fastapi import HTTPException

    from app.services import approvals

    async with AsyncSessionLocal() as db:
        try:
            tok, task, project, actor = await approvals.resolve(db, raw)
            if actor.telegram_chat_id != chat_id:
                return "Bu onay isteği bu Telegram hesabına ait değil."
            await approvals.decide(db, raw, approve, note, "TELEGRAM")
        except HTTPException as exc:
            return f"İşlem yapılamadı: {exc.detail}"
    return f"'{task.title}' onaylandı." if approve else f"'{task.title}' revizyona gönderildi."


async def handle_callback(cb: dict) -> None:
    """Onay mesajındaki butonlar: a:<belirteç> onayla, r:<belirteç> revizyon (gerekçe istenir)."""
    from app.core.tokens import redis_client

    data = cb.get("data") or ""
    chat_id = str(((cb.get("message") or {}).get("chat") or {}).get("id") or (cb.get("from") or {}).get("id") or "")
    await _call("answerCallbackQuery", {"callback_query_id": cb.get("id")})
    if not chat_id or ":" not in data:
        return
    action, raw = data.split(":", 1)
    if action == "a":
        await send_message(chat_id, await _decide(chat_id, raw, True, None))
    elif action == "r":
        client = redis_client()
        try:
            await client.set(REVISE_KEY.format(chat=chat_id), raw, ex=3600)
        finally:
            await client.aclose()
        await send_message(chat_id, "Revizyon gerekçesini yazın (personel buna göre düzeltecek):", reply_markup={"force_reply": True})


async def _pending_revision(chat_id: str) -> Optional[str]:
    from app.core.tokens import redis_client

    client = redis_client()
    try:
        raw = await client.getdel(REVISE_KEY.format(chat=chat_id))
    finally:
        await client.aclose()
    return raw.decode() if isinstance(raw, bytes) else raw


async def handle_update(update: dict) -> None:
    if update.get("callback_query"):
        await handle_callback(update["callback_query"])
        return
    msg = update.get("message") or {}
    text = (msg.get("text") or "").strip()
    chat_id = str((msg.get("chat") or {}).get("id") or "")
    if chat_id and text and not text.startswith("/"):
        raw = await _pending_revision(chat_id)  # revizyon butonundan sonra yazılan gerekçe
        if raw:
            await send_message(chat_id, await _decide(chat_id, raw, False, text))
        return
    if not chat_id or not text.startswith("/start"):
        return
    code = text.removeprefix("/start").strip().upper()
    if not code:
        await send_message(chat_id, "RECOrion bildirimlerini almak için profilinizdeki bağlantı koduyla /start KOD yazın.")
        return
    async with AsyncSessionLocal() as db:
        actor = (await db.execute(select(Actor).where(Actor.telegram_link_code == code))).scalars().first()
        if not actor:
            await send_message(chat_id, "Kod geçersiz veya süresi dolmuş. RECOrion profilinizden yeni kod alın.")
            return
        actor.telegram_chat_id, actor.telegram_link_code = chat_id, None
        actor.telegram_linked_at = datetime.now(timezone.utc)
        await db.commit()
        name = actor.display_name
    await send_message(chat_id, f"Merhaba {name}, Telegram hesabınız RECOrion'a bağlandı. Proje bildirimleri artık buraya da gelecek.")


async def poll_loop() -> None:
    """Bot mesajlarını uzun yoklamayla dinler (tek örnek: Redis kilidi)."""
    from app.core.tokens import redis_client

    logger.info("Telegram bot dinleyicisi başladı.")
    while True:
        try:
            client = redis_client()
            try:
                if not await client.set(LOCK_KEY, "1", nx=True, ex=60):
                    await asyncio.sleep(30)
                    continue
                offset = int(await client.get(OFFSET_KEY) or 0)
                data = await _call("getUpdates", {"offset": offset, "timeout": 25}, timeout=35)
                for update in (data or {}).get("result", []):
                    offset = max(offset, int(update["update_id"]) + 1)
                    await handle_update(update)
                await client.set(OFFSET_KEY, str(offset))
                await client.delete(LOCK_KEY)
            finally:
                await client.aclose()
            if data is None:
                await asyncio.sleep(10)
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            logger.error("Telegram dinleyici hatası: %s", exc)
            await asyncio.sleep(10)
