"""
İSTEK #746 — Kredi denetimi: kredi bitince / haftalık sınır dolunca şirketin projelerini ve Case'lerini duraklatma, kredi
yüklenince (ya da sınır kaldırılınca) kaldığı yerden devam ettirme ve EVREN koruma sınırı (eş zamanlı AI adımı).

- Kredi biten şirkette adım karantinaya düşmez: tüm aktif proje/Case'ler "kredi bitti" nedeniyle duraklar (akış kaydı).
- Kredi nedeniyle duraklayan proje, kredi yüklenmeden (ya da sınır kaldırılmadan) devam ettirilemez.
- Yükleme sonrası şirket ayarı açıksa kendiliğinden devam eder; değilse yönetici tek tıkla devam ettirir.
- Eş zamanlı AI adımı paket başına sınırlıdır (Başlangıç 2, Profesyonel 5, Kurumsal 10); sınırdaki iş sırada bekler, kredi
  düşmez. Sınır Merkez'de paket özelliği (features.max_parallel_ai) ile değiştirilebilir.
"""
import logging
import time
import uuid
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Actor, Plan, Project, TaskEvent, Tenant

logger = logging.getLogger("recorion.credit_control")

CREDIT_REASONS = ("CREDIT", "WEEKLY_CAP")
REASON_TEXT = {"CREDIT": "Şirketin kredisi bittiği için duraklatıldı. Kredi yüklenince kaldığı yerden sürer.",
               "WEEKLY_CAP": "Şirketin haftalık harcama sınırı dolduğu için duraklatıldı. Sınır kaldırılınca ya da yeni haftada sürer."}
DEFAULT_PARALLEL = {"STARTER": 2, "PRO": 5, "ENTERPRISE": 10}
SLOT_TTL = 60 * 60  # bir AI çalışması en fazla 45 dk sürer; takılı kalan yer 1 saatte düşer


async def pause_reason(db: AsyncSession, project: Project) -> Optional[str]:
    """Duraklatılmış projenin son duraklatma nedeni (MANAGER, CREDIT, WEEKLY_CAP) ya da None."""
    if project.status != "PAUSED":
        return None
    ev = (await db.execute(select(TaskEvent).where(TaskEvent.project_id == project.id, TaskEvent.kind == "PROJECT_PAUSED")
                           .order_by(TaskEvent.created_at.desc()).limit(1))).scalar_one_or_none()
    return ((ev.data or {}).get("reason") if ev else None) or "MANAGER"


async def blocker(db: AsyncSession, tenant: Tenant, reason: Optional[str]) -> Optional[str]:
    """Kredi nedeniyle duraklamış iş için engel sürüyorsa kullanıcıya gösterilecek metin."""
    from app.services import credits

    if reason == "CREDIT" and await credits.balance(db, tenant.id) < credits.EXHAUSTED_BELOW:
        return "Şirketin kredisi bitti; kredi yüklenmeden proje devam ettirilemez. Şirket yöneticisi Kredi ve Kullanım ekranından ek kredi alabilir."
    if reason == "WEEKLY_CAP":
        return await credits.weekly_cap_block(db, tenant)
    return None


async def _signal(project: Project, name: str) -> None:
    from app.config import settings
    from app.workflows import engine

    if settings.WORKFLOW_ENABLED and project.workflow_id:
        try:
            await engine.signal_project(str(project.id), name)
        except Exception as exc:  # akış motoru yoksa durum yine değişir; devamda proje akışı yenilenir
            logger.warning("Proje akışına %s sinyali gönderilemedi (%s): %s", name, project.id, exc)


async def pause_tenant(db: AsyncSession, tenant_id, reason: str, detail: str = "") -> List[str]:
    """Şirketin tüm aktif proje ve Case'lerini kredi nedeniyle duraklatır; yöneticilere bir kez bildirir."""
    from app.services import task_flow

    projects = (await db.execute(select(Project).where(Project.tenant_id == tenant_id, Project.status == "ACTIVE"))).scalars().all()
    if not projects:
        return []
    for p in projects:
        p.status = "PAUSED"
        await task_flow.log(db, p, None, "PROJECT_PAUSED", None, REASON_TEXT.get(reason, detail), {"reason": reason, "detail": detail[:500]})
    await db.commit()
    for p in projects:
        await _signal(p, "pause")
    tenant = await db.get(Tenant, tenant_id)
    admins = (await db.execute(select(Actor.id).where(Actor.tenant_id == tenant_id, Actor.role == "COMPANY_ADMIN",
                                                      Actor.status != "DISABLED"))).scalars().all()
    people = set(admins) | {p.manager_actor_id for p in projects if p.manager_actor_id}
    what = "kredisi bitti" if reason == "CREDIT" else "haftalık harcama sınırı doldu"
    text = (f"RECOrion: {tenant.name if tenant else 'Şirket'} {what}; {len(projects)} proje/Case duraklatıldı. "
            "Kredi ve Kullanım ekranından ek kredi alınabilir ya da paket yükseltilebilir; işler kaldığı yerden sürer.")
    for actor_id in people:
        try:
            await task_flow.notify(db, actor_id, text)
        except Exception as exc:
            logger.warning("Kredi duraklatma bildirimi gönderilemedi (%s): %s", actor_id, exc)
    return [str(p.id) for p in projects]


async def credit_paused(db: AsyncSession, tenant_id) -> List[Project]:
    rows = (await db.execute(select(Project).where(Project.tenant_id == tenant_id, Project.status == "PAUSED"))).scalars().all()
    return [p for p in rows if await pause_reason(db, p) in CREDIT_REASONS]


async def resume_credit_paused(db: AsyncSession, tenant: Tenant, actor_id=None) -> Dict[str, Any]:
    """Kredi nedeniyle duraklayan ve engeli kalkmış işleri devam ettirir."""
    from app.services import task_flow

    resumed, blocked = [], []
    for p in await credit_paused(db, tenant.id):
        reason = await pause_reason(db, p)
        msg = await blocker(db, tenant, reason)
        if msg:
            blocked.append({"project": p.name, "reason": msg})
            continue
        p.status = "ACTIVE"
        await task_flow.log(db, p, None, "PROJECT_RESUMED", actor_id,
                            "Kredi yüklendi; proje kaldığı yerden sürüyor." if reason == "CREDIT" else "Haftalık sınır kalktı; proje kaldığı yerden sürüyor.",
                            {"reason": reason})
        resumed.append(p)
    await db.commit()
    for p in resumed:
        await _signal(p, "resume")
    return {"resumed": [p.name for p in resumed], "blocked": blocked}


# ---------------------------------------------------------------- EVREN koruma sınırı (eş zamanlı AI adımı)
async def parallel_limit(db: AsyncSession, tenant: Tenant) -> Optional[int]:
    from app.services.llm_gateway import HQ_SLUG

    if tenant.slug == HQ_SLUG:
        return None
    plan = await db.get(Plan, tenant.plan_id) if tenant.plan_id else None
    configured = ((plan.features or {}).get("max_parallel_ai") if plan else None)
    try:
        return int(configured) if configured else DEFAULT_PARALLEL.get(plan.code if plan else "", 5)
    except (TypeError, ValueError):
        return DEFAULT_PARALLEL.get(plan.code if plan else "", 5)


async def acquire_slot(db: AsyncSession, tenant: Tenant, task_id: str) -> bool:
    """Şirketin eş zamanlı AI çalışması sınırında yer ayırır; sınır doluysa False (iş sırada bekler, kredi düşmez)."""
    limit = await parallel_limit(db, tenant)
    if limit is None:
        return True
    from app.core.tokens import redis_client

    key, now = f"ai_slots:{tenant.id}", time.time()
    client = redis_client()
    try:
        slots = await client.hgetall(key)
        stale = [k for k, v in slots.items() if now - float(v) > SLOT_TTL]
        if stale:
            await client.hdel(key, *stale)
        live = {(k.decode() if isinstance(k, bytes) else k) for k in slots if k not in stale}
        if task_id in live:
            await client.hset(key, task_id, str(now))
            return True
        if len(live) >= limit:
            return False
        await client.hset(key, task_id, str(now))
        await client.expire(key, SLOT_TTL)
        return True
    except Exception as exc:  # Redis yoksa sınır uygulanmaz (iş durmaz)
        logger.warning("EVREN koruma sınırı denetlenemedi: %s", exc)
        return True
    finally:
        await client.aclose()


async def release_slot(tenant_id, task_id: str) -> None:
    from app.core.tokens import redis_client

    client = redis_client()
    try:
        await client.hdel(f"ai_slots:{tenant_id}", task_id)
    except Exception:
        pass
    finally:
        await client.aclose()


def uuid_of(v) -> uuid.UUID:
    return v if isinstance(v, uuid.UUID) else uuid.UUID(str(v))
