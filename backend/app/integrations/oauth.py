"""MCP sunucularına tek tık giriş (ADIM 12.1): MCP yetkilendirme belirtimi (2025-06-18) = OAuth 2.1 + PKCE.

Akış:
1. Keşif: MCP adresine kimliksiz istek → 401 + WWW-Authenticate resource_metadata (RFC 9728) → korunan kaynak bilgisi →
   yetkilendirme sunucusu bilgisi (RFC 8414 / OpenID). Kaynak bilgisi yoksa (eski sunucular) MCP adresinin kökü denenir.
2. İstemci: şirketin girdiği istemci kimliği; yoksa dinamik istemci kaydı (RFC 7591) — RECOrion kendini kaydeder.
3. Kullanıcı tarayıcıda servisin kendi giriş ekranında izin verir (PKCE S256, state, resource = RFC 8707).
4. Geri dönüş: kod → erişim + yenileme token'ı; kimlik kasasında şifreli (bağlantının gizli alanlarında "_" önekli).
5. Erişim token'ının süresi dolmadan (veya 401'de) yenileme token'ıyla tazelenir ve kasaya yazılır.

Keşfedilen her adres SSRF korumasından geçer (yetkilendirme adresine kullanıcının tarayıcısı gider; diğerlerine backend).
Token'lar, istemci gizli anahtarı ve PKCE doğrulayıcısı kayıtlara, hata iletilerine ve API yanıtlarına yazılmaz.
"""
import base64
import hashlib
import json
import re
import secrets
import time
from typing import Any, Dict, List, Optional
from urllib.parse import urlencode, urlsplit

import httpx

from app.integrations.base import Context, ToolError, guard_url, http_client

CALLBACK_PATH = "/api/v1/integrations/oauth/callback"
STATE_TTL = 600  # giriş penceresi 10 dk
REFRESH_MARGIN = 60  # süresinin dolmasına bu kadar saniye kala tazelenir
TOKEN_KEYS = ("_access_token", "_refresh_token", "_expires_at")
CLIENT_KEYS = ("_client_id", "_client_secret", "_client_issuer", "_client_redirect")
INIT = {"jsonrpc": "2.0", "id": 1, "method": "initialize",
        "params": {"protocolVersion": "2025-06-18", "capabilities": {}, "clientInfo": {"name": "RECOrion", "version": "1.0"}}}


def redirect_uri() -> str:
    from app.config import settings

    return settings.PUBLIC_APP_URL.rstrip("/") + CALLBACK_PATH


def enabled(config: Dict[str, Any]) -> bool:
    return (config or {}).get("auth_mode") == "oauth"


def _b64url(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode().rstrip("=")


def pkce() -> Dict[str, str]:
    verifier = _b64url(secrets.token_bytes(48))
    return {"verifier": verifier, "challenge": _b64url(hashlib.sha256(verifier.encode()).digest())}


def _www_auth(header: str) -> Dict[str, str]:
    return {k.lower(): v for k, v in re.findall(r'([A-Za-z_]+)="([^"]*)"', header or "")}


def _well_known(base: str, name: str) -> List[str]:
    """RFC 8414/9728 adresleri: yol varsa önce araya eklenmiş biçim (/.well-known/x/yol), sonra kök."""
    p = urlsplit(base)
    root = f"{p.scheme}://{p.netloc}"
    path = p.path.rstrip("/")
    out = [f"{root}/.well-known/{name}{path}"] if path else []
    return out + [f"{root}/.well-known/{name}"]


async def _get_json(client: httpx.AsyncClient, url: str) -> Optional[Dict[str, Any]]:
    try:
        r = await client.get(await guard_url(url), headers={"Accept": "application/json"})
    except (httpx.HTTPError, ToolError):
        return None
    if r.status_code != 200:
        return None
    try:
        data = r.json()
    except ValueError:
        return None
    return data if isinstance(data, dict) else None


def _https(url: str, what: str) -> str:
    from app.config import settings

    if not isinstance(url, str) or not url.startswith(("https://", "http://")):
        raise ToolError(f"Yetkilendirme sunucusu geçersiz {what} bildirdi.")
    if url.startswith("http://") and not settings.INTEGRATIONS_ALLOW_PRIVATE_NETWORK:
        raise ToolError(f"Yetkilendirme sunucusunun {what} adresi https değil; güvenli olmayan girişe izin verilmez.")
    return url


async def discover(mcp_url: str) -> Dict[str, Any]:
    """MCP sunucusunun yetkilendirme bilgisini bulur. Kimlik gerekmiyorsa {"auth_required": False}."""
    url = await guard_url((mcp_url or "").strip())
    async with http_client(timeout=15) as c:
        try:
            r = await c.post(url, json=INIT, headers={"Accept": "application/json, text/event-stream", "Content-Type": "application/json"})
        except httpx.HTTPError as exc:
            raise ToolError(f"MCP sunucusuna ulaşılamadı ({exc.__class__.__name__}).")
        if r.status_code < 400:
            return {"auth_required": False}
        if r.status_code not in (401, 403):
            raise ToolError(f"MCP sunucusu HTTP {r.status_code} döndürdü.")
        hint = _www_auth(r.headers.get("www-authenticate", ""))
        prm = await _get_json(c, hint["resource_metadata"]) if hint.get("resource_metadata") else None
        if not prm:
            for cand in _well_known(url, "oauth-protected-resource"):
                prm = await _get_json(c, cand)
                if prm:
                    break
        p = urlsplit(url)
        issuer = ((prm or {}).get("authorization_servers") or [f"{p.scheme}://{p.netloc}"])[0]
        asm = None
        for cand in _well_known(issuer, "oauth-authorization-server") + _well_known(issuer, "openid-configuration"):
            asm = await _get_json(c, cand)
            if asm and asm.get("authorization_endpoint") and asm.get("token_endpoint"):
                break
            asm = None
    if not asm:
        raise ToolError("Bu MCP sunucusunun yetkilendirme sunucusu bulunamadı; sunucu tek tık girişi desteklemiyor olabilir "
                        "(erişim anahtarı yöntemini deneyin).")
    methods = asm.get("code_challenge_methods_supported")
    if methods and "S256" not in methods:
        raise ToolError("Yetkilendirme sunucusu PKCE (S256) desteklemiyor; güvenli giriş yapılamaz.")
    scope = hint.get("scope") or " ".join((prm or {}).get("scopes_supported") or [])
    return {"auth_required": True, "issuer": str(issuer),
            "authorization_endpoint": _https(asm["authorization_endpoint"], "giriş"),
            "token_endpoint": _https(asm["token_endpoint"], "token"),
            "registration_endpoint": _https(asm["registration_endpoint"], "kayıt") if asm.get("registration_endpoint") else None,
            "auth_methods": asm.get("token_endpoint_auth_methods_supported") or [],
            "resource": (prm or {}).get("resource") or url, "scope": scope.strip()}


async def register(meta: Dict[str, Any]) -> Dict[str, str]:
    """Dinamik istemci kaydı: RECOrion bu yetkilendirme sunucusuna kendini istemci olarak kaydeder."""
    body = {"client_name": "RECOrion", "redirect_uris": [redirect_uri()], "grant_types": ["authorization_code", "refresh_token"],
            "response_types": ["code"], "token_endpoint_auth_method": "none"}
    try:
        async with http_client(timeout=15) as c:
            r = await c.post(await guard_url(meta["registration_endpoint"]), json=body, headers={"Accept": "application/json"})
    except httpx.HTTPError as exc:
        raise ToolError(f"İstemci kaydı yapılamadı ({exc.__class__.__name__}).")
    if r.status_code not in (200, 201):
        raise ToolError(f"Yetkilendirme sunucusu istemci kaydını reddetti (HTTP {r.status_code}); istemci kimliğini elle girin.")
    data = r.json()
    if not data.get("client_id"):
        raise ToolError("Yetkilendirme sunucusu istemci kimliği vermedi.")
    return {"_client_id": str(data["client_id"]), "_client_secret": str(data.get("client_secret") or ""),
            "_client_issuer": meta["issuer"], "_client_redirect": redirect_uri()}


def client_of(secrets_: Dict[str, Any], meta: Dict[str, Any]) -> Optional[Dict[str, str]]:
    """Kullanılacak istemci: şirketin girdiği kimlik önceliklidir; yoksa bu sunucu ve yönlendirme adresi için kaydedilmiş olan."""
    if secrets_.get("client_id"):
        return {"id": secrets_["client_id"], "secret": secrets_.get("client_secret") or ""}
    if secrets_.get("_client_id") and secrets_.get("_client_issuer") == meta["issuer"] and secrets_.get("_client_redirect") == redirect_uri():
        return {"id": secrets_["_client_id"], "secret": secrets_.get("_client_secret") or ""}
    return None


def authorize_url(meta: Dict[str, Any], client_id: str, state: str, challenge: str) -> str:
    q = {"response_type": "code", "client_id": client_id, "redirect_uri": redirect_uri(), "code_challenge": challenge,
         "code_challenge_method": "S256", "state": state, "resource": meta["resource"]}
    if meta.get("scope"):
        q["scope"] = meta["scope"]
    ep = meta["authorization_endpoint"]
    return ep + ("&" if "?" in ep else "?") + urlencode(q)


async def _token_request(token_endpoint: str, client: Dict[str, str], auth_methods: List[str], data: Dict[str, str]) -> Dict[str, Any]:
    auth = None
    data = dict(data)
    if client.get("secret") and "client_secret_basic" in auth_methods and "client_secret_post" not in auth_methods:
        auth = httpx.BasicAuth(client["id"], client["secret"])
    else:
        data["client_id"] = client["id"]
        if client.get("secret"):
            data["client_secret"] = client["secret"]
    try:
        async with http_client(timeout=20) as c:
            r = await c.post(await guard_url(token_endpoint), data=data, auth=auth, headers={"Accept": "application/json"})
    except httpx.HTTPError as exc:
        raise ToolError(f"Yetkilendirme sunucusuna ulaşılamadı ({exc.__class__.__name__}).")
    try:
        body = r.json()
    except ValueError:
        body = {}
    if r.status_code != 200 or not body.get("access_token"):
        reason = body.get("error_description") or body.get("error") or f"HTTP {r.status_code}"
        raise ToolError(f"Yetkilendirme sunucusu token vermedi: {str(reason)[:200]}")
    expires = body.get("expires_in")
    return {"_access_token": str(body["access_token"]), "_refresh_token": str(body.get("refresh_token") or ""),
            "_expires_at": int(time.time()) + int(expires) if isinstance(expires, (int, float)) or str(expires or "").isdigit() else None}


async def exchange(pending: Dict[str, Any], client: Dict[str, str], code: str) -> Dict[str, Any]:
    tokens = await _token_request(pending["token_endpoint"], client, pending.get("auth_methods") or [], {
        "grant_type": "authorization_code", "code": code, "redirect_uri": redirect_uri(),
        "code_verifier": pending["verifier"], "resource": pending["resource"]})
    return {**tokens, "_token_endpoint": pending["token_endpoint"], "_resource": pending["resource"],
            "_auth_methods": pending.get("auth_methods") or []}


def _client_from(secrets_: Dict[str, Any]) -> Dict[str, str]:
    if secrets_.get("client_id"):
        return {"id": secrets_["client_id"], "secret": secrets_.get("client_secret") or ""}
    return {"id": secrets_.get("_client_id") or "", "secret": secrets_.get("_client_secret") or ""}


async def refresh(ctx: Context) -> None:
    """Yenileme token'ıyla yeni erişim token'ı alır; bağlamı ve kasayı günceller."""
    s = ctx.secrets
    if not s.get("_refresh_token") or not s.get("_token_endpoint"):
        raise ToolError("Oturum süresi doldu; Entegrasyonlar ekranında yeniden 'Giriş yap'a basın.")
    data = {"grant_type": "refresh_token", "refresh_token": s["_refresh_token"]}
    if s.get("_resource"):
        data["resource"] = s["_resource"]
    try:
        tokens = await _token_request(s["_token_endpoint"], _client_from(s), s.get("_auth_methods") or [], data)
    except ToolError:
        raise ToolError("Oturum yenilenemedi; Entegrasyonlar ekranında yeniden 'Giriş yap'a basın.")
    if not tokens["_refresh_token"]:
        tokens["_refresh_token"] = s["_refresh_token"]  # sunucu yenisini vermediyse eskisi geçerli
    await persist(ctx, tokens)


async def access_token(ctx: Context) -> str:
    """Geçerli erişim token'ı (süresi dolmak üzereyse önce tazelenir)."""
    if not ctx.secrets.get("_access_token"):
        raise ToolError("Bu MCP sunucusu için henüz giriş yapılmadı; Entegrasyonlar ekranında 'Giriş yap'a basın.")
    exp = ctx.secrets.get("_expires_at")
    if exp and int(exp) - REFRESH_MARGIN < time.time():
        await refresh(ctx)
    return ctx.secrets["_access_token"]


async def persist(ctx: Context, updates: Dict[str, Any]) -> None:
    """Bağlamdaki gizli bilgileri günceller ve bağlantının kasa kaydına yazar."""
    ctx.secrets.update(updates)
    if not ctx.connection_id:
        return
    import uuid

    from app.core import vault
    from app.db.models import IntegrationConnection
    from app.db.session import AsyncSessionLocal

    async with AsyncSessionLocal() as db:
        conn = await db.get(IntegrationConnection, uuid.UUID(ctx.connection_id))
        if not conn:
            return
        binding = f"{conn.tenant_id}:{conn.id}"
        current = vault.unseal(conn.secret, binding) if conn.secret else {}
        current.update(updates)
        conn.secret = vault.seal(current, binding)
        await db.commit()


# Bekleyen giriş (state → bağlantı, PKCE doğrulayıcısı, uç noktalar): Redis'te 10 dk, tek kullanımlık, özetle anahtarlanır
def _state_key(state: str) -> str:
    return "oauth:" + hashlib.sha256(state.encode()).hexdigest()


async def save_pending(state: str, data: Dict[str, Any]) -> None:
    from app.core.tokens import redis_client

    await redis_client().set(_state_key(state), json.dumps(data), ex=STATE_TTL)


async def pop_pending(state: str) -> Optional[Dict[str, Any]]:
    from app.core.tokens import redis_client

    if not state or len(state) > 200:
        return None
    raw = await redis_client().getdel(_state_key(state))
    return json.loads(raw) if raw else None
