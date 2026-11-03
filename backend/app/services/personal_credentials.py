"""
Kişisel bağlantı anahtarları (ADIM 14.2): kişi, şirketin bir bağlantısında (ör. RECSlip.App v2 kurulu Odoo) kendi kullanıcı
anahtarını tanımlar; kişinin AI personeli o kişinin adına yalnızca bu anahtarla işlem yapar (ör. masraf onayı). Odoo'da
kişinin kendi yetkileri ve kayıt izi geçerlidir; RECOrion bağlantının ortak anahtarını bu işler için kullanmaz.

- Anahtar kasada şifreli, bağlantıya ve kişiye bağlı (binding); API'de, kayıtta ve hata mesajında asla yer almaz.
- Kaydederken denenir: Odoo kullanıcısı (uid, giriş adı, ad) okunur; geçersizse kaydedilmez.
- Süresi dolmuş veya denemesi başarısız anahtar işlem için kullanılmaz; kişi Bağlantılarım'dan yeniler.
"""
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import vault
from app.db.models import Actor, IntegrationConnection, PersonalCredential
from app.integrations.base import Context, ToolError

SUPPORTED = ("odoo",)


def now() -> datetime:
    return datetime.now(timezone.utc)


def binding(cred: PersonalCredential) -> str:
    return f"{cred.tenant_id}:{cred.connection_id}:{cred.actor_id}"


def context(conn: IntegrationConnection, cred: PersonalCredential) -> Context:
    """Kişinin anahtarıyla çalışan bağlantı bağlamı (bağlantının adresi/veritabanı + kişinin anahtarı)."""
    secrets = vault.unseal(cred.secret, binding(cred)) if cred.secret else {}
    return Context(config=dict(conn.config or {}), secrets={"api_key": secrets.get("api_key") or ""},
                   tenant_id=str(conn.tenant_id), connection_id=str(conn.id))


def usable(cred: Optional[PersonalCredential]) -> bool:
    return bool(cred and cred.status == "ACTIVE" and cred.secret and (not cred.expires_at or cred.expires_at > now()))


async def whoami(ctx: Context) -> Dict[str, object]:
    """Anahtarın Odoo kullanıcısı: {uid, login, name}. Anahtar geçersizse ToolError."""
    from app.integrations import odoo

    info = await odoo._kw(ctx, "res.users", "context_get", [])
    uid = (info or {}).get("uid")
    if not uid:
        raise ToolError("Odoo kullanıcısı okunamadı.")
    rows = await odoo._kw(ctx, "res.users", "read", [[uid]], {"fields": ["login", "name"]}) or []
    row = rows[0] if rows else {}
    return {"uid": uid, "login": row.get("login"), "name": row.get("name")}


async def _connection(db: AsyncSession, tenant_id, connection_id) -> IntegrationConnection:
    conn = await db.get(IntegrationConnection, connection_id)
    if not conn or conn.tenant_id != tenant_id or conn.status != "ACTIVE":
        raise HTTPException(status_code=404, detail="Bağlantı bulunamadı veya etkin değil.")
    if conn.connector not in SUPPORTED:
        raise HTTPException(status_code=400, detail="Bu bağlantı türünde kişisel anahtar kullanılmıyor.")
    return conn


async def _agent(db: AsyncSession, tenant_id, agent_actor_id) -> Optional[uuid.UUID]:
    if not agent_actor_id:
        return None
    agent = await db.get(Actor, agent_actor_id)
    if not agent or agent.tenant_id != tenant_id or agent.actor_type != "AI_AGENT":
        raise HTTPException(status_code=400, detail="Seçilen AI personel bu şirkette yok.")
    return agent.id


async def save(db: AsyncSession, actor: Actor, connection_id, api_key: Optional[str], agent_actor_id=None,
               expires_at: Optional[datetime] = None) -> PersonalCredential:
    """Kişinin anahtarını kaydeder (yeni veya yenileme). Anahtar verilirse önce denenir."""
    conn = await _connection(db, actor.tenant_id, connection_id)
    cred = (await db.execute(select(PersonalCredential).where(
        PersonalCredential.actor_id == actor.id, PersonalCredential.connection_id == conn.id))).scalar_one_or_none()
    if not cred:
        if not (api_key or "").strip():
            raise HTTPException(status_code=400, detail="API anahtarını girin.")
        cred = PersonalCredential(tenant_id=actor.tenant_id, actor_id=actor.id, connection_id=conn.id)
        db.add(cred)
    cred.agent_actor_id = await _agent(db, actor.tenant_id, agent_actor_id)
    if expires_at is not None:
        cred.expires_at = expires_at
    if (api_key or "").strip():
        probe = Context(config=dict(conn.config or {}), secrets={"api_key": api_key.strip()})
        try:
            who = await whoami(probe)
        except ToolError as exc:
            raise HTTPException(status_code=400, detail=f"Anahtar denenemedi: {exc}")
        await db.flush()  # kimlik (binding) için
        cred.secret = vault.seal({"api_key": api_key.strip()}, binding(cred))
        cred.external_uid, cred.external_login, cred.external_name = who["uid"], who["login"], who["name"]
        cred.status, cred.last_test_at, cred.last_test_ok, cred.last_error = "ACTIVE", now(), True, None
    await db.commit()
    await db.refresh(cred)
    return cred


async def test(db: AsyncSession, cred: PersonalCredential) -> PersonalCredential:
    conn = await db.get(IntegrationConnection, cred.connection_id)
    cred.last_test_at = now()
    try:
        who = await whoami(context(conn, cred))
        cred.external_uid, cred.external_login, cred.external_name = who["uid"], who["login"], who["name"]
        cred.status, cred.last_test_ok, cred.last_error = "ACTIVE", True, None
    except ToolError as exc:
        cred.status, cred.last_test_ok, cred.last_error = "INVALID", False, str(exc)[:500]
    await db.commit()
    await db.refresh(cred)
    return cred


async def mark_invalid(db: AsyncSession, cred: PersonalCredential, error: str) -> None:
    """İşlem sırasında anahtar reddedildi (401): bir daha kullanılmaz, kişi yeniler."""
    cred.status, cred.last_test_ok, cred.last_error, cred.last_test_at = "INVALID", False, error[:500], now()
    await db.commit()


async def by_external_uids(db: AsyncSession, connection_id, uids: List[int]) -> List[PersonalCredential]:
    if not uids:
        return []
    rows = (await db.execute(select(PersonalCredential).where(
        PersonalCredential.connection_id == connection_id, PersonalCredential.external_uid.in_(uids)))).scalars().all()
    return [c for c in rows if usable(c)]


def out(cred: PersonalCredential, conn: Optional[IntegrationConnection] = None, agent: Optional[Actor] = None,
        owner: Optional[Actor] = None) -> Dict[str, object]:
    days_left = (cred.expires_at - now()).days if cred.expires_at else None
    return {"id": str(cred.id), "connection_id": str(cred.connection_id), "connection_name": conn.name if conn else None,
            "external_login": cred.external_login, "external_name": cred.external_name, "external_uid": cred.external_uid,
            "agent_actor_id": str(cred.agent_actor_id) if cred.agent_actor_id else None,
            "agent_name": agent.display_name if agent else None,
            "owner_actor_id": str(cred.actor_id), "owner_name": owner.display_name if owner else None,
            "expires_at": cred.expires_at, "days_left": days_left, "status": cred.status, "usable": usable(cred),
            "last_test_at": cred.last_test_at, "last_test_ok": cred.last_test_ok, "last_error": cred.last_error,
            "has_key": bool(cred.secret)}
