"""Canlı deneme (ADIM 12.6): RECOrion'un MCP istemcisi (app/integrations/mcp.py) RECOrion'un kendi MCP sunucusuna gerçek HTTP ile
bağlanır. Canlı test şirketinin ("RECOrion Canlı Test A.Ş.") yöneticisi adına geçici okuma anahtarı açılır, kullanılır, iptal edilir.
Anahtar ekrana basılmaz. Gerçek müşteri şirketlerine dokunulmaz.
"""
import asyncio
import hashlib
import secrets
import sys
from datetime import datetime, timedelta, timezone

sys.path.insert(0, "/app")
from sqlalchemy import select  # noqa: E402

from app.config import settings  # noqa: E402
from app.db.models import Actor, PersonalToken, Tenant  # noqa: E402
from app.db.session import AsyncSessionLocal  # noqa: E402
from app.integrations import get, mcp  # noqa: E402
from app.integrations.base import Context  # noqa: E402


async def main() -> None:
    settings.INTEGRATIONS_ALLOW_PRIVATE_NETWORK = True  # yalnızca bu deneme: sunucu aynı makinede
    async with AsyncSessionLocal() as db:
        tenant = (await db.execute(select(Tenant).where(Tenant.slug == "recorion_canli_test"))).scalar_one()
        admin = (await db.execute(select(Actor).where(Actor.tenant_id == tenant.id, Actor.role == "COMPANY_ADMIN",
                                                      Actor.actor_type == "HUMAN"))).scalars().first()
        raw = "rxp_" + secrets.token_urlsafe(32)
        tok = PersonalToken(tenant_id=tenant.id, actor_id=admin.id, name="Canlı deneme (MCP istemcisi)", token_hash=hashlib.sha256(raw.encode()).hexdigest(),
                            prefix=raw[:10], scopes=["READ"], expires_at=datetime.now(timezone.utc) + timedelta(minutes=10))
        db.add(tok)
        await db.commit()
        tid = tok.id
    try:
        ctx = Context({"url": "http://localhost:8000/api/v1/mcp"}, {"token": raw})
        mcp._cache.clear()
        print("deneme:", await get("mcp").test(ctx))
        tools = {t.name: t for t in await get("mcp").tools(ctx)}
        print("araçlar:", sorted(tools), "· türler:", sorted({t.kind for t in tools.values()}))
        r = await tools["list_projects"].run(ctx, {})
        projects = (r.get("data") or {}).get("projects") or []
        print("proje sayısı:", len(projects), "· ilk:", projects[0]["name"] if projects else "-")
    finally:
        async with AsyncSessionLocal() as db:
            t = await db.get(PersonalToken, tid)
            t.revoked_at = datetime.now(timezone.utc)
            await db.commit()
        print("geçici anahtar iptal edildi")


asyncio.run(main())
