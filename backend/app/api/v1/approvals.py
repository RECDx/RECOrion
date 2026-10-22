"""
Her yerden onay uçları (ADIM 7.3).

- /approvals/{token}: e-posta veya Telegram'daki tek kullanımlık bağlantı; giriş gerektirmez, belirteç kimlik yerine geçer
  (yalnızca onaylayıcıya gönderilir, süreli, teslime bağlı). Yalnızca o iş adımının özeti ve son çıktısı gösterilir.
- /me/approvals: kişinin kararını bekleyen işler (onay kuyruğu).
- /auth/notification-prefs: kişinin bildirim kanalı tercihleri.
"""
from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import CurrentUser, get_current_user
from app.db.models import Actor
from app.db.session import get_db
from app.services import agent_work, approvals, notify

router = APIRouter(tags=["Onaylar ve Bildirimler"])


@router.get("/approvals/{token}")
async def approval_summary(token: str, db: AsyncSession = Depends(get_db)):
    tok, task, project, actor = await approvals.resolve(db, token)
    art = await agent_work.latest_artifact(db, task.id)
    assignee = await db.get(Actor, task.assignee_actor_id) if task.assignee_actor_id else None
    return {"project_name": project.name, "task_title": task.title, "description": task.description,
            "acceptance_criteria": task.acceptance_criteria, "approver": actor.display_name,
            "assignee": assignee.display_name if assignee else None, "submitted_at": task.submitted_at,
            "rejection_count": task.rejection_count or 0, "max_rejections": task.max_rejections or 3, "expires_at": tok.expires_at,
            "artifact": {"name": art.name, "version": art.version, "content": await agent_work.artifact_text(art, 100_000)} if art else None}


class TokenDecisionIn(BaseModel):
    approve: bool
    note: Optional[str] = Field(None, max_length=4000)


@router.post("/approvals/{token}")
async def approval_decide(token: str, payload: TokenDecisionIn, db: AsyncSession = Depends(get_db)):
    return await approvals.decide(db, token, payload.approve, payload.note, "EMAIL")


@router.get("/me/approvals")
async def my_approvals(user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await approvals.pending_for(db, user.actor_id, user.tenant_id)


class PrefsIn(BaseModel):
    email: bool = True
    telegram: bool = True


@router.get("/auth/notification-prefs")
async def get_prefs(user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return notify.prefs(await db.get(Actor, user.actor_id))


@router.put("/auth/notification-prefs")
async def set_prefs(payload: PrefsIn, user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    actor = await db.get(Actor, user.actor_id)
    actor.notification_prefs = {**(actor.notification_prefs or {}), "email": payload.email, "telegram": payload.telegram}
    await db.commit()
    return notify.prefs(actor)
