"""
Her yerden onay (ADIM 7.3): e-posta bağlantısı ve Telegram butonları için tek kullanımlık belirteçler.

- Belirteç yalnızca onaylayıcıya gönderilir; veritabanında SHA-256 özeti tutulur.
- Belirteç belirli bir teslime bağlıdır (tasks.submitted_at). Adım artık onay beklemiyorsa, yeni bir teslim yapılmışsa,
  onaylayıcı değişmişse, süresi dolmuşsa veya kullanılmışsa geçersizdir.
- Karar web'deki onayla aynı yoldan (Temporal sinyali) yürür; kanal akış geçmişine yazılır.
"""
import hashlib
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.models import Actor, ApprovalToken, Project, Task

TOKEN_DAYS = 7


def _hash(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()


def _now() -> datetime:
    return datetime.now(timezone.utc)


def public_url() -> bool:
    url = settings.PUBLIC_APP_URL.lower()
    return url.startswith("https://") and "localhost" not in url and "127.0.0.1" not in url


def approve_url(raw: str) -> str:
    return f"{settings.PUBLIC_APP_URL.rstrip('/')}/#/approve?token={raw}"


async def create(db: AsyncSession, task: Task, actor_id, channel: str) -> Tuple[str, ApprovalToken]:
    raw = secrets.token_urlsafe(24)  # 32 karakter; Telegram callback_data sınırına (64 bayt) sığar
    tok = ApprovalToken(token_hash=_hash(raw), task_id=task.id, actor_id=uuid.UUID(str(actor_id)), channel=channel,
                        submitted_at=task.submitted_at, expires_at=_now() + timedelta(days=TOKEN_DAYS))
    db.add(tok)
    await db.flush()
    return raw, tok


async def resolve(db: AsyncSession, raw: str) -> Tuple[ApprovalToken, Task, Project, Actor]:
    """Geçerli belirteci çözer; geçersizse kullanıcıya anlaşılır bir hata verir."""
    tok = (await db.execute(select(ApprovalToken).where(ApprovalToken.token_hash == _hash(raw or "")))).scalars().first()
    if not tok:
        raise HTTPException(status_code=404, detail="Onay bağlantısı geçersiz.")
    task = await db.get(Task, tok.task_id)
    project = await db.get(Project, task.project_id) if task else None
    actor = await db.get(Actor, tok.actor_id)
    if tok.used_at:
        raise HTTPException(status_code=410, detail="Bu onay bağlantısı daha önce kullanıldı.")
    expires = tok.expires_at if tok.expires_at.tzinfo else tok.expires_at.replace(tzinfo=timezone.utc)
    if expires < _now():
        raise HTTPException(status_code=410, detail="Onay bağlantısının süresi doldu. Kararı RECOrion Work Space'ten verebilirsiniz.")
    if not task or not project or project.status not in ("ACTIVE", "PAUSED"):
        raise HTTPException(status_code=410, detail="Bu iş adımı artık karar beklemiyor.")
    if task.status != "WAITING_APPROVAL" or task.submitted_at != tok.submitted_at:
        raise HTTPException(status_code=410, detail="Bu iş adımı için karar zaten verilmiş veya yeni bir teslim yapılmış.")
    if (task.approver_actor_id or project.manager_actor_id) != tok.actor_id or not actor or actor.status == "DISABLED":
        raise HTTPException(status_code=403, detail="Bu iş adımının onaylayıcısı değişti; bağlantı geçersiz.")
    return tok, task, project, actor


async def decide(db: AsyncSession, raw: str, approve: bool, note: Optional[str], channel: str) -> Dict[str, Any]:
    from app.workflows import engine

    tok, task, project, actor = await resolve(db, raw)
    note = (note or "").strip()
    if not approve and not note:
        raise HTTPException(status_code=422, detail="Revizyon isterken gerekçeyi yazın; personel buna göre düzeltecek.")
    await engine.signal_task(str(task.id), "decide", {"actor_id": str(actor.id), "approve": approve, "note": note, "channel": channel})
    tok.used_at = _now()
    await db.commit()
    return {"accepted": True, "task_id": str(task.id), "approve": approve}


async def pending_for(db: AsyncSession, actor_id, tenant_id) -> List[Dict[str, Any]]:
    """Kişinin kararını bekleyen işler: onaylayıcısı olduğu onaylar ve yöneticisi olduğu projelerde karantinadaki adımlar."""
    rows = (await db.execute(select(Task, Project).join(Project, Project.id == Task.project_id).where(
        Project.tenant_id == tenant_id, Project.status.in_(("ACTIVE", "PAUSED")),
        Task.status.in_(("WAITING_APPROVAL", "QUARANTINED"))).order_by(Task.submitted_at))).all()
    actor_ids = {t.assignee_actor_id for t, _ in rows if t.assignee_actor_id}
    names = {a.id: a.display_name for a in (await db.execute(select(Actor).where(Actor.id.in_(actor_ids or {uuid.uuid4()})))).scalars()}
    out = []
    for t, p in rows:
        approver = t.approver_actor_id or p.manager_actor_id
        if (t.status == "WAITING_APPROVAL" and approver == actor_id) or (t.status == "QUARANTINED" and p.manager_actor_id == actor_id):
            out.append({"task_id": str(t.id), "title": t.title, "status": t.status, "project_id": str(p.id), "project_name": p.name,
                        "assignee": names.get(t.assignee_actor_id), "submitted_at": t.submitted_at,
                        "rejection_count": t.rejection_count or 0, "kind": "APPROVAL" if t.status == "WAITING_APPROVAL" else "QUARANTINE"})
    return out

