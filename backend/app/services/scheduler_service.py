"""
Otomatik e-posta zamanlayıcısı.

- Backend açıkken her SCHEDULER_INTERVAL_MINUTES dakikada bir vadesi gelen zamanlamaları çalıştırır.
- Birden fazla backend süreci çalışsa bile Redis kilidi ile aynı anda tek süreç işler.
- BEFORE_EXPIRATION_INTERVAL: paket bitişine target_lead_days gün kalan şirketlere, her
  frequency_days günde en fazla bir kez hatırlatma gönderir. Kural günlük çalışır; böylece
  pencereye yeni giren şirketler en geç bir gün içinde ilk hatırlatmayı alır.
- ON_REGISTRATION: zamanlanmış değildir; şirket aktivasyonunda kullanılır (customer_lifecycle).
"""
import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Tuple

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.tokens import redis_client
from app.db.models import NotificationSchedule, Plan, Tenant
from app.db.session import AsyncSessionLocal
from app.services.notification_service import NotificationService

logger = logging.getLogger("recorion.scheduler")

LOCK_KEY = "scheduler:lock"
RUN_EVERY = timedelta(days=1)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _aware(dt: datetime) -> datetime:
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


async def send_expiration_reminder(db: AsyncSession, tenant: Tenant, template_code: str = "PACKAGE_EXPIRATION_REMINDER") -> Tuple[bool, int]:
    from app.services.customer_lifecycle import app_url

    days_remaining = (_aware(tenant.package_expiry_date) - _now()).days if tenant.package_expiry_date else 0
    plan = await db.get(Plan, tenant.plan_id) if tenant.plan_id else None
    sent = await NotificationService.send_by_code(db, template_code, tenant.contact_email, {
        "company_name": tenant.name,
        "plan_name": plan.name if plan else "Kurumsal Paket",
        "expiry_date": tenant.package_expiry_date.strftime("%d.%m.%Y") if tenant.package_expiry_date else "-",
        "days_remaining": max(0, days_remaining),
        "renewal_url": app_url(""),
    })
    if sent:
        tenant.last_reminder_sent_at = _now()
    return sent, days_remaining


async def run_schedule(db: AsyncSession, sched: NotificationSchedule) -> int:
    """Zamanlamayı bir kez çalıştırır; gönderilen e-posta sayısını döner."""
    processed = 0
    now = _now()
    if sched.trigger_type == "BEFORE_EXPIRATION_INTERVAL":
        tenants = (await db.execute(select(Tenant).where(Tenant.is_active == True))).scalars().all()
        for t in tenants:
            if not t.package_expiry_date or not t.contact_email:
                continue
            days_remaining = (_aware(t.package_expiry_date) - now).days
            if not (0 <= days_remaining <= (sched.target_lead_days or 90)):
                continue
            if t.last_reminder_sent_at and (now - _aware(t.last_reminder_sent_at)).days < (sched.frequency_days or 15):
                continue
            sent, _ = await send_expiration_reminder(db, t, sched.template_code)
            processed += int(sent)
    sched.last_run_at = now
    sched.next_run_at = now + RUN_EVERY
    await db.commit()
    return processed


async def run_due_schedules() -> int:
    total = 0
    async with AsyncSessionLocal() as db:
        due = (await db.execute(
            select(NotificationSchedule).where(
                NotificationSchedule.is_active == True,
                NotificationSchedule.trigger_type == "BEFORE_EXPIRATION_INTERVAL",
                or_(NotificationSchedule.next_run_at == None, NotificationSchedule.next_run_at <= _now()),
            )
        )).scalars().all()
        for sched in due:
            try:
                total += await run_schedule(db, sched)
            except Exception as exc:
                await db.rollback()
                logger.error("Zamanlama çalıştırılamadı (%s): %s", sched.name, exc)
    return total


async def scheduler_loop() -> None:
    interval = max(1, settings.SCHEDULER_INTERVAL_MINUTES) * 60
    logger.info("Otomatik zamanlayıcı başladı (her %s dakikada bir kontrol).", interval // 60)
    while True:
        try:
            client = redis_client()
            try:
                acquired = await client.set(LOCK_KEY, "1", nx=True, ex=interval - 5 if interval > 10 else interval)
            finally:
                await client.aclose()
            if acquired:
                sent = await run_due_schedules()
                if sent:
                    logger.info("Zamanlayıcı %s hatırlatma e-postası gönderdi.", sent)
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            logger.error("Zamanlayıcı döngüsü hatası: %s", exc)
        await asyncio.sleep(interval)
