"""
Entegrasyon (MCP) uçları (ADIM 10.1).

Bağlantılar, araç yetkileri ve çağrı kaydı şirketin içeriğidir: yalnızca o şirketin integration:manage yetkisi olanları
(KVKK: RECDx platform personeli göremez). Şifreler yalnızca yazılır; yanıtlarda "dolu/boş" olarak döner.
Gizli alanlarda "_" önekli anahtarlar RECOrion'un kendi yönettiği değerlerdir (OAuth token'ları, kayıtlı istemci; ADIM 12.1):
kullanıcı bunları gönderemez, yanıtlarda yalnızca "giriş yapıldı/yapılmadı" olarak görünür.
"""
import logging
import secrets as pysecrets
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app import integrations
from app.core import vault
from app.core.security import CurrentUser, ensure_tenant_content, forbidden, get_current_user
from app.db.models import Actor, AgentToolGrant, IntegrationCatalogEntry, IntegrationConnection, Project, ToolCall
from app.db.session import get_db
from app.integrations import oauth
from app.integrations.base import READ, Context, ToolError
from app.services import code_repo, tool_gateway

router = APIRouter(tags=["Entegrasyonlar (MCP)"])
logger = logging.getLogger("recorion.integrations")


def _manage(user: CurrentUser, tenant_id: uuid.UUID) -> None:
    ensure_tenant_content(user, tenant_id)
    if not user.has("integration:manage"):
        raise forbidden("Entegrasyonları yalnızca entegrasyon yönetimi yetkisi olanlar yönetebilir.")


async def _conn(db: AsyncSession, user: CurrentUser, tenant_id: uuid.UUID, cid: uuid.UUID) -> IntegrationConnection:
    _manage(user, tenant_id)
    conn = await db.get(IntegrationConnection, cid)
    if not conn or conn.tenant_id != tenant_id:
        raise HTTPException(status_code=404, detail="Bağlantı bulunamadı.")
    return conn


def conn_out(c: IntegrationConnection) -> Dict[str, Any]:
    try:
        secrets = tool_gateway.context(c).secrets
    except vault.VaultError:
        secrets = {}
    secrets_set = vault.mask({k: v for k, v in secrets.items() if not k.startswith("_")})
    connector = integrations.REGISTRY.get(c.connector)
    out = {"id": str(c.id), "connector": c.connector, "connector_title": connector.title if connector else c.connector,
           "catalog_code": c.catalog_code, "name": c.name, "config": c.config or {}, "secrets_set": secrets_set, "status": c.status,
           "last_test_at": c.last_test_at, "last_test_ok": c.last_test_ok, "last_error": c.last_error, "created_at": c.created_at,
           **({"agent": _agent_out(c)} if c.connector == "edge" else {})}
    if oauth.enabled(c.config):
        exp = secrets.get("_expires_at")
        out["oauth"] = {"connected": bool(secrets.get("_access_token")), "can_refresh": bool(secrets.get("_refresh_token")),
                        "expires_at": datetime.fromtimestamp(int(exp), timezone.utc) if exp else None,
                        "redirect_uri": oauth.redirect_uri()}
    return out


def _agent_out(c: IntegrationConnection) -> Dict[str, Any]:
    """Edge ajanı durumu (anahtar asla dönmez; yalnızca tanımlı olup olmadığı)."""
    from app.integrations import edge

    info = c.agent_info or {}
    return {"has_token": bool(c.agent_token_hash), "online": edge.online(c.agent_seen_at), "seen_at": c.agent_seen_at,
            "hostname": info.get("hostname"), "version": info.get("version"), "templates": len(info.get("templates") or [])}


@router.get("/integrations/connectors")
async def connectors(user: CurrentUser = Depends(get_current_user)):
    """Bağlayıcı kataloğu (alanlar ve araçlar; gizli bilgi yok)."""
    return {"vault_ready": vault.enabled(), "connectors": [c.describe() for c in integrations.REGISTRY.values()]}


class ConnectionIn(BaseModel):
    connector: str
    catalog_code: Optional[str] = Field(None, max_length=64)
    name: str = Field(..., min_length=2, max_length=120)
    config: Dict[str, Any] = Field(default_factory=dict)
    secrets: Dict[str, str] = Field(default_factory=dict)


class ConnectionUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=120)
    config: Optional[Dict[str, Any]] = None
    secrets: Optional[Dict[str, str]] = None  # boş değer = mevcut şifreyi koru
    status: Optional[str] = Field(None, pattern="^(ACTIVE|DISABLED)$")


def _no_managed(secrets: Dict[str, Any]) -> None:
    if any(k.startswith("_") for k in secrets):
        raise HTTPException(status_code=422, detail="Bu alanlar RECOrion tarafından yönetilir; gönderilemez.")


def _check_fields(connector, config: Dict[str, Any], secrets: Dict[str, Any]) -> None:
    cfg_keys = {f.key for f in connector.all_config_fields}
    sec_keys = {f.key for f in connector.secret_fields}
    unknown = (set(config) - cfg_keys) | ({k for k in secrets if not k.startswith("_")} - sec_keys)
    if unknown:
        raise HTTPException(status_code=422, detail=f"Bilinmeyen alan: {', '.join(sorted(unknown))}")
    missing = [f.label for f in connector.all_config_fields if f.required and not config.get(f.key)] + \
              [f.label for f in connector.secret_fields if f.required and not secrets.get(f.key)]
    if missing:
        raise HTTPException(status_code=422, detail=f"Zorunlu alan: {', '.join(missing)}")
    bad = [f.label for f in connector.all_config_fields
           if f.options and config.get(f.key) not in (None, "", *[v for v, _ in f.options])]
    if bad:
        raise HTTPException(status_code=422, detail=f"Geçersiz seçim: {', '.join(bad)}")


@router.get("/company/{tenant_id}/integrations")
async def list_connections(tenant_id: uuid.UUID, user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    _manage(user, tenant_id)
    rows = (await db.execute(select(IntegrationConnection).where(IntegrationConnection.tenant_id == tenant_id)
                             .order_by(IntegrationConnection.created_at))).scalars().all()
    return [conn_out(c) for c in rows]


@router.post("/company/{tenant_id}/integrations", status_code=201)
async def create_connection(tenant_id: uuid.UUID, payload: ConnectionIn, user: CurrentUser = Depends(get_current_user),
                            db: AsyncSession = Depends(get_db)):
    _manage(user, tenant_id)
    connector = integrations.REGISTRY.get(payload.connector)
    if not connector:
        raise HTTPException(status_code=422, detail="Bilinmeyen bağlayıcı.")
    if not vault.enabled():
        raise HTTPException(status_code=503, detail="Kimlik kasası yapılandırılmamış; RECDx ile iletişime geçin.")
    _no_managed(payload.secrets)
    _check_fields(connector, payload.config, payload.secrets)
    if payload.catalog_code:
        entry = (await db.execute(select(IntegrationCatalogEntry).where(IntegrationCatalogEntry.code == payload.catalog_code))).scalar_one_or_none()
        if not entry or entry.connector != connector.code or entry.status != "ACTIVE":
            raise HTTPException(status_code=422, detail="Katalog kartı bu sistemle eşleşmiyor.")
    if (await db.execute(select(IntegrationConnection.id).where(IntegrationConnection.tenant_id == tenant_id,
                                                                IntegrationConnection.name == payload.name.strip()))).first():
        raise HTTPException(status_code=409, detail="Bu adla bir bağlantı zaten var.")
    conn = IntegrationConnection(id=uuid.uuid4(), tenant_id=tenant_id, connector=connector.code, name=payload.name.strip(),
                                 config=payload.config, catalog_code=payload.catalog_code, created_by_actor_id=user.actor_id)
    conn.secret = vault.seal({k: v for k, v in payload.secrets.items() if v}, tool_gateway.binding(conn))
    db.add(conn)
    await db.commit()
    return conn_out(conn)


@router.put("/company/{tenant_id}/integrations/{cid}")
async def update_connection(tenant_id: uuid.UUID, cid: uuid.UUID, payload: ConnectionUpdate, user: CurrentUser = Depends(get_current_user),
                            db: AsyncSession = Depends(get_db)):
    conn = await _conn(db, user, tenant_id, cid)
    connector = integrations.get(conn.connector)
    secrets = tool_gateway.context(conn).secrets
    _no_managed(payload.secrets or {})
    if payload.secrets:
        secrets.update({k: v for k, v in payload.secrets.items() if v})  # boş gönderilen alan korunur
    config = payload.config if payload.config is not None else (conn.config or {})
    old = conn.config or {}
    if (config.get("url"), config.get("auth_mode")) != (old.get("url"), old.get("auth_mode")) or             (payload.secrets or {}).get("client_id"):
        # Sunucu, kimlik yöntemi veya istemci değişti: eski oturum ve kayıtlı istemci geçersiz (yeniden 'Giriş yap')
        secrets = {k: v for k, v in secrets.items() if k not in oauth.TOKEN_KEYS + oauth.CLIENT_KEYS}
    _check_fields(connector, config, secrets)
    if payload.name:
        conn.name = payload.name.strip()
    conn.config, conn.secret = config, vault.seal(secrets, tool_gateway.binding(conn))
    if payload.status:
        conn.status = payload.status
    # Bu hesaba yansıtılan proje depoları (#297): Gitea'daki yansıtma eski token'la kalmasın
    if conn.connector in code_repo.MIRROR_CONNECTORS and (payload.status or payload.secrets or payload.config is not None):
        for project in (await db.execute(select(Project).where(Project.mirror_connection_id == conn.id))).scalars().all():
            try:
                if conn.status != "ACTIVE":
                    await code_repo.clear_mirror(project)
                else:
                    await code_repo.set_mirror(project, conn, project.mirror_repo)
            except code_repo.RepoError as exc:
                raise HTTPException(status_code=502, detail=f"'{project.name}' projesinin yansıtması güncellenemedi: {exc.message}")
    await db.commit()
    return conn_out(conn)


@router.post("/company/{tenant_id}/integrations/{cid}/test")
async def test_connection(tenant_id: uuid.UUID, cid: uuid.UUID, user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    from datetime import datetime, timezone

    conn = await _conn(db, user, tenant_id, cid)
    try:
        detail = await integrations.get(conn.connector).test(tool_gateway.context(conn))
        conn.last_test_ok, conn.last_error = True, None
    except (ToolError, vault.VaultError) as exc:
        detail, conn.last_test_ok, conn.last_error = str(exc), False, str(exc)[:1000]
    except Exception as exc:
        detail, conn.last_test_ok, conn.last_error = f"Bağlantı denenemedi ({exc.__class__.__name__}).", False, f"{exc.__class__.__name__}"
    conn.last_test_at = datetime.now(timezone.utc)
    await db.commit()
    return {"ok": conn.last_test_ok, "detail": detail}


@router.get("/company/{tenant_id}/integrations/{cid}/tools")
async def connection_tools(tenant_id: uuid.UUID, cid: uuid.UUID, user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    conn = await _conn(db, user, tenant_id, cid)
    try:
        tools = await tool_gateway.connection_tools(conn)
    except (ToolError, vault.VaultError) as exc:
        raise HTTPException(status_code=502, detail=str(exc))
    return [{"name": t.name, "description": t.description, "kind": t.kind, "input_schema": t.input_schema} for t in tools]


class GrantsIn(BaseModel):
    grants: List[Dict[str, str]] = Field(default_factory=list, max_length=500)  # [{"actor_id", "tool"}]


@router.get("/company/{tenant_id}/integrations/{cid}/grants")
async def get_grants(tenant_id: uuid.UUID, cid: uuid.UUID, user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    await _conn(db, user, tenant_id, cid)
    rows = (await db.execute(select(AgentToolGrant).where(AgentToolGrant.connection_id == cid))).scalars().all()
    return [{"actor_id": str(g.actor_id), "tool": g.tool} for g in rows]


@router.put("/company/{tenant_id}/integrations/{cid}/grants")
async def set_grants(tenant_id: uuid.UUID, cid: uuid.UUID, payload: GrantsIn, user: CurrentUser = Depends(get_current_user),
                     db: AsyncSession = Depends(get_db)):
    """Bağlantının AI personel araç yetkilerini topluca belirler (yalnızca bu şirketin AI personeli)."""
    conn = await _conn(db, user, tenant_id, cid)
    names = {t.name for t in await tool_gateway.connection_tools(conn)} | {"*"}
    wanted = set()
    for g in payload.grants:
        try:
            aid = uuid.UUID(g.get("actor_id", ""))
        except ValueError:
            raise HTTPException(status_code=422, detail="Geçersiz AI personel.")
        if g.get("tool") not in names:
            raise HTTPException(status_code=422, detail=f"Bu bağlantıda '{g.get('tool')}' aracı yok.")
        wanted.add((aid, g["tool"]))
    agents = {a.id for a in (await db.execute(select(Actor).where(Actor.id.in_([a for a, _ in wanted] or [uuid.uuid4()]),
                                                                  Actor.tenant_id == tenant_id, Actor.actor_type == "AI_AGENT"))).scalars()}
    if any(a not in agents for a, _ in wanted):
        raise HTTPException(status_code=422, detail="Araç yetkisi yalnızca bu şirketin AI personeline verilebilir.")
    existing = {(g.actor_id, g.tool): g for g in (await db.execute(select(AgentToolGrant).where(AgentToolGrant.connection_id == cid))).scalars()}
    for key, g in existing.items():
        if key not in wanted:
            await db.delete(g)
    for aid, tool in wanted - set(existing):
        db.add(AgentToolGrant(tenant_id=tenant_id, connection_id=cid, actor_id=aid, tool=tool, created_by_actor_id=user.actor_id))
    await db.commit()
    return [{"actor_id": str(a), "tool": t} for a, t in sorted(wanted, key=lambda x: (str(x[0]), x[1]))]


class TryIn(BaseModel):
    tool: str
    arguments: Dict[str, Any] = Field(default_factory=dict)


@router.post("/company/{tenant_id}/integrations/{cid}/try")
async def try_tool(tenant_id: uuid.UUID, cid: uuid.UUID, payload: TryIn, user: CurrentUser = Depends(get_current_user),
                   db: AsyncSession = Depends(get_db)):
    """Yöneticinin bir OKUMA aracını denemesi (kurulumu doğrulamak için); kayda yönetici adına yazılır."""
    conn = await _conn(db, user, tenant_id, cid)
    tool = next((t for t in await tool_gateway.connection_tools(conn) if t.name == payload.tool), None)
    if not tool:
        raise HTTPException(status_code=404, detail="Araç bulunamadı.")
    if tool.kind != READ:
        raise HTTPException(status_code=409, detail="Yazma araçları elle denenemez; AI personel kullandığında onaya düşer.")
    call = ToolCall(tenant_id=tenant_id, connection_id=conn.id, connection_name=conn.name, actor_id=user.actor_id,
                    actor_name=user.actor.display_name, tool=tool.name, kind=READ, arguments=payload.arguments, status="EXECUTED")
    db.add(call)
    await tool_gateway._execute(conn, tool, payload.arguments, call)
    await db.commit()
    return tool_gateway.call_out(call)


@router.get("/company/{tenant_id}/tool-calls")
async def list_calls(tenant_id: uuid.UUID, status: Optional[str] = None, limit: int = Query(100, le=500),
                     user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    _manage(user, tenant_id)
    stmt = select(ToolCall).where(ToolCall.tenant_id == tenant_id)
    if status:
        stmt = stmt.where(ToolCall.status == status.upper())
    rows = (await db.execute(stmt.order_by(ToolCall.created_at.desc()).limit(limit))).scalars().all()
    return [tool_gateway.call_out(c) for c in rows]


@router.get("/me/tool-approvals")
async def my_tool_approvals(user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Onayımı bekleyen yazma işlemleri (Onaylarım ekranı)."""
    if user.is_platform_staff:
        return []
    rows = (await db.execute(select(ToolCall).where(ToolCall.tenant_id == user.tenant_id, ToolCall.status == "PENDING_APPROVAL")
                             .order_by(ToolCall.created_at))).scalars().all()
    return [tool_gateway.call_out(c) for c in rows if tool_gateway.can_decide(user, c)]


class DecisionIn(BaseModel):
    approve: bool
    note: Optional[str] = Field(None, max_length=2000)


@router.post("/tool-calls/{call_id}/decision")
async def decide(call_id: uuid.UUID, payload: DecisionIn, user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    call = await db.get(ToolCall, call_id)
    if not call:
        raise HTTPException(status_code=404, detail="Araç çağrısı bulunamadı.")
    ensure_tenant_content(user, call.tenant_id)
    await tool_gateway.decide(db, call, user, payload.approve, payload.note)
    await db.commit()
    return tool_gateway.call_out(call)


# --- Tek tık giriş (OAuth) — ADIM 12.1 ---

@router.post("/company/{tenant_id}/integrations/{cid}/oauth/start")
async def oauth_start(tenant_id: uuid.UUID, cid: uuid.UUID, user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Servisin giriş ekranına gidecek adresi üretir (PKCE + state). İstemci yoksa RECOrion kendini otomatik kaydeder."""
    conn = await _conn(db, user, tenant_id, cid)
    if conn.connector != "mcp" or not oauth.enabled(conn.config):
        raise HTTPException(status_code=409, detail="Bu bağlantının kimlik yöntemi tek tık giriş değil.")
    if conn.status != "ACTIVE":
        raise HTTPException(status_code=409, detail="Bağlantı devre dışı.")
    ctx = tool_gateway.context(conn)
    try:
        meta = await oauth.discover(conn.config.get("url"))
        if not meta["auth_required"]:
            raise HTTPException(status_code=409, detail="Bu MCP sunucusu kimlik istemiyor; kimlik yöntemini 'Kimlik gerekmez' seçin.")
        client = oauth.client_of(ctx.secrets, meta)
        if not client:
            if not meta.get("registration_endpoint"):
                raise HTTPException(status_code=422, detail="Bu sunucu otomatik istemci kaydını desteklemiyor. Servisin geliştirici "
                                    f"konsolunda uygulama oluşturun (yönlendirme adresi: {oauth.redirect_uri()}) ve istemci kimliğini girin.")
            registered = await oauth.register(meta)
            await oauth.persist(ctx, registered)
            client = oauth.client_of(ctx.secrets, meta)
    except ToolError as exc:
        raise HTTPException(status_code=502, detail=str(exc))
    state, codes = pysecrets.token_urlsafe(32), oauth.pkce()
    await oauth.save_pending(state, {"tenant_id": str(tenant_id), "connection_id": str(cid), "actor_id": str(user.actor_id),
                                     "verifier": codes["verifier"], "token_endpoint": meta["token_endpoint"],
                                     "auth_methods": meta["auth_methods"], "resource": meta["resource"], "issuer": meta["issuer"]})
    return {"authorize_url": oauth.authorize_url(meta, client["id"], state, codes["challenge"]), "redirect_uri": oauth.redirect_uri()}


def _back(ok: bool, cid: Optional[str], message: str = "") -> RedirectResponse:
    from app.config import settings

    q = f"oauth={'ok' if ok else 'error'}" + (f"&conn={cid}" if cid else "") + (f"&msg={quote(message[:300])}" if message else "")
    return RedirectResponse(f"{settings.PUBLIC_APP_URL.rstrip('/')}/?{q}#/company-admin", status_code=302)


@router.get("/integrations/oauth/callback")
async def oauth_callback(state: str = "", code: str = "", error: str = "", error_description: str = "", db: AsyncSession = Depends(get_db)):
    """Servisin giriş ekranından dönüş (herkese açık uç; yetki tek kullanımlık state ile doğrulanır)."""
    pending = await oauth.pop_pending(state)
    if not pending:
        return _back(False, None, "Giriş oturumu bulunamadı veya süresi doldu; yeniden 'Giriş yap'a basın.")
    cid = pending["connection_id"]
    if error:
        return _back(False, cid, "Giriş iptal edildi veya izin verilmedi." if error == "access_denied" else f"Servis girişi reddetti: {(error_description or error)[:200]}")
    conn = await db.get(IntegrationConnection, uuid.UUID(cid))
    if not conn or str(conn.tenant_id) != pending["tenant_id"] or conn.connector != "mcp" or not oauth.enabled(conn.config):
        return _back(False, None, "Bağlantı bulunamadı veya değişti.")
    ctx = tool_gateway.context(conn)
    client = oauth.client_of(ctx.secrets, {"issuer": pending["issuer"]})
    try:
        if not client or not code:
            raise ToolError("Giriş tamamlanamadı (istemci veya kod eksik).")
        tokens = await oauth.exchange(pending, client, code)
    except ToolError as exc:
        conn.last_test_at, conn.last_test_ok, conn.last_error = datetime.now(timezone.utc), False, str(exc)[:1000]
        await db.commit()
        return _back(False, cid, str(exc))
    secrets = {**ctx.secrets, **tokens}
    conn.secret = vault.seal(secrets, tool_gateway.binding(conn))
    conn.last_test_at, conn.last_test_ok, conn.last_error = datetime.now(timezone.utc), True, None
    await db.commit()
    logger.info("MCP OAuth girişi tamamlandı (bağlantı %s)", cid)
    return _back(True, cid)


@router.post("/company/{tenant_id}/integrations/{cid}/oauth/disconnect")
async def oauth_disconnect(tenant_id: uuid.UUID, cid: uuid.UUID, user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Oturumu kapatır: RECOrion'daki token'lar silinir (serviste verilen izni ayrıca servisin ayarlarından kaldırabilirsiniz)."""
    conn = await _conn(db, user, tenant_id, cid)
    secrets = {k: v for k, v in tool_gateway.context(conn).secrets.items() if k not in oauth.TOKEN_KEYS}
    conn.secret = vault.seal(secrets, tool_gateway.binding(conn))
    await db.commit()
    return conn_out(conn)
