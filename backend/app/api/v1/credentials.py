"""
Kişisel bağlantı anahtarları (ADIM 14.2) — Bağlantılarım.

- /me/credentials: kişinin şirket bağlantılarındaki kendi anahtarları (ör. RECSlip v2 Odoo kullanıcısı) ve bu anahtarla
  onun adına çalışacak AI personel. Anahtar bir kez girilir, denenir, kasada saklanır; asla geri dönmez.
- /company/{tenant_id}/credentials: şirket yöneticisinin görünümü — kimin anahtarı var, süresi ne zaman doluyor (anahtar yok).
"""
import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import write_audit_event
from app.core.security import CurrentUser, ensure_tenant_content, forbidden, get_current_user
from app.db.models import Actor, IntegrationConnection, PersonalCredential
from app.db.session import get_db
from app.services import personal_credentials as pcs

router = APIRouter(tags=["Bağlantılarım"])


class CredentialIn(BaseModel):
    connection_id: uuid.UUID
    api_key: Optional[str] = Field(None, max_length=500)
    agent_actor_id: Optional[uuid.UUID] = None
    expires_at: Optional[datetime] = None


class CredentialUpdate(BaseModel):
    api_key: Optional[str] = Field(None, max_length=500)
    agent_actor_id: Optional[uuid.UUID] = None
    expires_at: Optional[datetime] = None


async def _own(db: AsyncSession, user: CurrentUser, cid: uuid.UUID) -> PersonalCredential:
    cred = await db.get(PersonalCredential, cid)
    if not cred or cred.actor_id != user.actor_id:
        raise HTTPException(status_code=404, detail="Anahtar bulunamadı.")
    return cred


async def _out(db: AsyncSession, cred: PersonalCredential):
    conn = await db.get(IntegrationConnection, cred.connection_id)
    agent = await db.get(Actor, cred.agent_actor_id) if cred.agent_actor_id else None
    owner = await db.get(Actor, cred.actor_id)
    return pcs.out(cred, conn, agent, owner)


def _no_staff(user: CurrentUser) -> None:
    if user.is_platform_staff:
        raise forbidden("KVKK gereği RECDx personeli müşteri sistemine kişisel anahtar tanımlayamaz.")


@router.get("/me/credentials")
async def my_credentials(user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    rows = (await db.execute(select(PersonalCredential).where(PersonalCredential.actor_id == user.actor_id)
                             .order_by(PersonalCredential.created_at))).scalars().all()
    conns = (await db.execute(select(IntegrationConnection).where(
        IntegrationConnection.tenant_id == user.tenant_id, IntegrationConnection.status == "ACTIVE",
        IntegrationConnection.connector.in_(pcs.SUPPORTED)).order_by(IntegrationConnection.name))).scalars().all()
    agents = (await db.execute(select(Actor).where(Actor.tenant_id == user.tenant_id, Actor.actor_type == "AI_AGENT",
                                                   Actor.status != "DISABLED").order_by(Actor.display_name))).scalars().all()
    return {"credentials": [await _out(db, c) for c in rows],
            "connections": [{"id": str(c.id), "name": c.name, "connector": c.connector} for c in conns],
            "agents": [{"id": str(a.id), "name": a.display_name} for a in agents]}


@router.post("/me/credentials", status_code=201)
async def add_credential(payload: CredentialIn, user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    _no_staff(user)
    actor = await db.get(Actor, user.actor_id)
    cred = await pcs.save(db, actor, payload.connection_id, payload.api_key, payload.agent_actor_id, payload.expires_at)
    await write_audit_event(action="PERSONAL_CREDENTIAL_SAVED", actor_id=user.actor_id, tenant_id=user.tenant_id,
                            target_type="personal_credential", target_id=str(cred.id),
                            payload={"connection_id": str(cred.connection_id), "external_login": cred.external_login})
    return await _out(db, cred)


@router.put("/me/credentials/{cid}")
async def update_credential(cid: uuid.UUID, payload: CredentialUpdate, user: CurrentUser = Depends(get_current_user),
                            db: AsyncSession = Depends(get_db)):
    _no_staff(user)
    cred = await _own(db, user, cid)
    actor = await db.get(Actor, user.actor_id)
    cred = await pcs.save(db, actor, cred.connection_id, payload.api_key, payload.agent_actor_id, payload.expires_at)
    return await _out(db, cred)


@router.post("/me/credentials/{cid}/test")
async def test_credential(cid: uuid.UUID, user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await _out(db, await pcs.test(db, await _own(db, user, cid)))


@router.delete("/me/credentials/{cid}")
async def delete_credential(cid: uuid.UUID, user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    cred = await _own(db, user, cid)
    await db.delete(cred)
    await db.commit()
    await write_audit_event(action="PERSONAL_CREDENTIAL_DELETED", actor_id=user.actor_id, tenant_id=user.tenant_id,
                            target_type="personal_credential", target_id=str(cid))
    return {"deleted": True}


@router.get("/company/{tenant_id}/credentials")
async def company_credentials(tenant_id: uuid.UUID, user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    ensure_tenant_content(user, tenant_id)
    if not any(user.has(p) for p in ("integration:manage", "integration:approve", "user:manage")):
        raise forbidden("Kişisel anahtarların listesini entegrasyon veya kullanıcı yöneticisi görür.")
    rows = (await db.execute(select(PersonalCredential).where(PersonalCredential.tenant_id == tenant_id)
                             .order_by(PersonalCredential.expires_at.asc().nullslast()))).scalars().all()
    return [await _out(db, c) for c in rows]
