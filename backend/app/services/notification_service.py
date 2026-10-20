"""
RECOrion e-posta gönderim servisi.

- Tüm müşteri e-postaları veritabanındaki şablonlardan (email_templates) üretilir;
  Süper Admin şablonları editörden düzenleyebilir.
- {{degisken}} değerleri HTML'e kaçışlanarak (escape) yerleştirilir.
- SMTP bağlantısı STARTTLS/SSL olmadan kimlik bilgisi göndermez.
- EMAIL_DELIVERY=log iken e-posta gönderilmez, OUTBOX'a yazılır (test/geliştirme).
- Gönderim kaydı (SENT_EMAILS_LOG) yalnızca üst veriyi tutar; içerik (şifre, kod) tutulmaz.
"""
import asyncio
import html as html_lib
import logging
import re
import smtplib
import ssl
from collections import deque
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any, Deque, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings

logger = logging.getLogger("recorion_notification")

# Son gönderimlerin üst verisi (alıcı, konu, sonuç) - içerik tutulmaz
SENT_EMAILS_LOG: Deque[Dict[str, Any]] = deque(maxlen=200)
# EMAIL_DELIVERY=log modunda gönderilmeyen e-postalar (yalnızca test/geliştirme)
OUTBOX: List[Dict[str, Any]] = []

_PLACEHOLDER = re.compile(r"\{\{\s*([a-zA-Z0-9_]+)\s*\}\}")


def render_template_text(text: str, context: Dict[str, Any], escape: bool) -> str:
    def sub(m):
        if m.group(1) not in context:
            return m.group(0)
        v = context[m.group(1)]
        s = "" if v is None else str(v)
        return html_lib.escape(s) if escape else s
    return _PLACEHOLDER.sub(sub, text or "")


class NotificationService:
    ADMIN_NOTIFICATION_EMAIL = settings.ADMIN_NOTIFICATION_EMAIL

    @classmethod
    def get_smtp_config(cls) -> Dict[str, Any]:
        import os
        return {
            "host": os.getenv("SMTP_HOST") or "mail.recdx.com",
            "port": int(os.getenv("SMTP_PORT") or "587"),
            "user": os.getenv("SMTP_USER") or "info@recdx.com",
            "password": os.getenv("SMTP_PASSWORD") or "",
            "from_email": os.getenv("FROM_EMAIL") or "info@recdx.com",
        }

    @classmethod
    def _send_smtp(cls, cfg: Dict[str, Any], to_email: str, subject: str, html_body: str, text_body: str) -> None:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"RECOrion <{cfg['from_email']}>"
        msg["To"] = to_email
        msg.attach(MIMEText(text_body, "plain", "utf-8"))
        msg.attach(MIMEText(html_body, "html", "utf-8"))
        context = ssl.create_default_context()
        if cfg["port"] == 465:
            with smtplib.SMTP_SSL(cfg["host"], cfg["port"], timeout=15, context=context) as server:
                server.login(cfg["user"], cfg["password"])
                server.sendmail(cfg["from_email"], [to_email], msg.as_string())
        else:
            with smtplib.SMTP(cfg["host"], cfg["port"], timeout=15) as server:
                server.starttls(context=context)  # başarısız olursa istisna: şifre açık metin gönderilmez
                server.login(cfg["user"], cfg["password"])
                server.sendmail(cfg["from_email"], [to_email], msg.as_string())

    @classmethod
    def _send_via_odoo(cls, cfg: Dict[str, Any], to_email: str, subject: str, html_body: str) -> bool:
        from app.services.odoo_service import OdooService
        uid, models, odoo_cfg = OdooService._get_connection()
        if not uid or not models:
            return False
        mail_id = models.execute_kw(odoo_cfg["db"], uid, odoo_cfg["password"], "mail.mail", "create",
                                    [{"email_from": cfg["from_email"], "email_to": to_email, "subject": subject, "body_html": html_body}])
        models.execute_kw(odoo_cfg["db"], uid, odoo_cfg["password"], "mail.mail", "send", [[mail_id]])
        return True

    @classmethod
    def _send_email(cls, to_email: str, subject: str, html_body: str, text_body: str) -> bool:
        record = {"timestamp": datetime.utcnow().isoformat(), "to": to_email, "subject": subject, "delivered": False}

        if settings.EMAIL_DELIVERY == "log":
            OUTBOX.append({**record, "html": html_body, "text": text_body})
            record["delivered"] = True
            SENT_EMAILS_LOG.append(record)
            logger.info("E-posta (log modu, gönderilmedi): %s - %s", to_email, subject)
            return True

        cfg = cls.get_smtp_config()
        if cfg["host"] and cfg["user"] and cfg["password"]:
            try:
                cls._send_smtp(cfg, to_email, subject, html_body, text_body)
                record["delivered"] = True
                SENT_EMAILS_LOG.append(record)
                logger.info("E-posta SMTP ile gönderildi: %s - %s", to_email, subject)
                return True
            except Exception as exc:
                record["smtp_error"] = str(exc)[:300]
                logger.error("SMTP gönderim hatası (%s): %s. Odoo yedek kanalı deneniyor.", to_email, exc)

        try:
            if cls._send_via_odoo(cfg, to_email, subject, html_body):
                record["delivered"] = True
                record["channel"] = "odoo"
                SENT_EMAILS_LOG.append(record)
                logger.info("E-posta Odoo yedek kanalı ile gönderildi: %s", to_email)
                return True
        except Exception as exc:
            record["odoo_error"] = str(exc)[:300]
            logger.error("Odoo e-posta gönderim hatası: %s", exc)

        SENT_EMAILS_LOG.append(record)
        return False

    @classmethod
    def render_and_send_template(cls, to_email: str, template: Any, context: Dict[str, Any]) -> bool:
        """Şablondaki {{degisken}} alanlarını doldurup gönderir (senkron)."""
        if not to_email:
            return False
        get = (lambda k: getattr(template, k, None)) if not isinstance(template, dict) else template.get
        subject = render_template_text(get("subject") or "", context, escape=False)
        html_body = render_template_text(get("html_content") or "", context, escape=True)
        text_body = render_template_text(get("text_content") or "", context, escape=False)
        if not text_body:
            text_body = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html_body)).strip()
            text_body = html_lib.unescape(text_body)
        return cls._send_email(to_email, subject, html_body, text_body)

    @classmethod
    async def send_by_code(cls, db: AsyncSession, code: str, to_email: Optional[str], context: Dict[str, Any]) -> bool:
        """Kodu verilen aktif şablonla e-posta gönderir; SMTP çağrısı olay döngüsünü bloklamaz."""
        from app.db.models import EmailTemplate

        if not to_email:
            return False
        tmpl = (await db.execute(
            select(EmailTemplate).where(EmailTemplate.code == code).order_by(EmailTemplate.created_at.desc())
        )).scalars().first()
        if not tmpl or not tmpl.is_active:
            logger.warning("'%s' e-posta şablonu bulunamadı veya pasif; e-posta gönderilmedi (%s).", code, to_email)
            return False
        snapshot = {"subject": tmpl.subject, "html_content": tmpl.html_content, "text_content": tmpl.text_content}
        return await asyncio.to_thread(cls.render_and_send_template, to_email, snapshot, context)
