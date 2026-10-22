"""
Bildirim kanalı altyapısı (ADIM 7.3).

Akış olayları kişiye tek noktadan bildirilir; kişinin tercihine göre her kanaldan gönderilir. Kanallar: e-posta (şablonlu)
ve Telegram (isteğe bağlı butonlarla). Yeni kanal (ör. WhatsApp) CHANNELS'a eklenir.
Tercih: actors.notification_prefs {"email": bool, "telegram": bool}; belirtilmemişse açık.
Bildirim hatası akışı durdurmaz.
"""
import logging
import uuid
from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.models import Actor

logger = logging.getLogger("recorion.notify")

CHANNELS = ("email", "telegram")


def prefs(actor: Actor) -> Dict[str, bool]:
    raw = actor.notification_prefs or {}
    return {c: raw.get(c, True) is not False for c in CHANNELS}


def project_url(project_id) -> str:
    return f"{settings.PUBLIC_APP_URL.rstrip('/')}/#/workspace?project={project_id}"


async def send(db: AsyncSession, actor_id, text: str, email_code: Optional[str] = None,
               email_context: Optional[Dict[str, Any]] = None, buttons: Optional[List[List[Dict[str, str]]]] = None,
               telegram_text: Optional[str] = None) -> Dict[str, bool]:
    """
    Kişiye bildirim. text: kısa düz metin (Telegram); email_code verilirse şablonlu e-posta da gönderilir.
    buttons: Telegram satır içi butonları [[{"text", "callback_data"}]]. Dönüş: kanal -> gönderildi mi.
    """
    from app.services import telegram_service
    from app.services.notification_service import NotificationService

    actor = await db.get(Actor, uuid.UUID(str(actor_id))) if actor_id else None
    sent = {c: False for c in CHANNELS}
    if not actor or actor.actor_type != "HUMAN":
        return sent
    p = prefs(actor)
    if p["email"] and email_code and actor.email:
        try:
            sent["email"] = await NotificationService.send_by_code(db, email_code, actor.email,
                                                                   {"contact_name": actor.display_name, **(email_context or {})})
        except Exception as exc:
            logger.warning("E-posta bildirimi gönderilemedi (%s): %s", email_code, exc)
    if p["telegram"] and actor.telegram_chat_id:
        markup = {"inline_keyboard": buttons} if buttons else None
        try:
            sent["telegram"] = await telegram_service.send_message(actor.telegram_chat_id, telegram_text or text, reply_markup=markup)
        except Exception as exc:
            logger.warning("Telegram bildirimi gönderilemedi: %s", exc)
    return sent
