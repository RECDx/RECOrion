"""
ADIM 12.1: bağlantı kataloğu, RECAi bağlanma rehberi ve MCP tek tık girişi (sahte OAuth + MCP sunucusu; gerçek ağa çıkılmaz).

- Katalog: tohumdan yüklenir, herkes görür (kimlik bilgisi yok); yalnızca RECDx Süper Admin düzenler; arşivlenen kart gizlenir.
- OAuth: keşif (401 → korunan kaynak → yetkilendirme sunucusu), dinamik istemci kaydı, PKCE S256, state tek kullanımlık,
  resource gönderilir; token'lar kasada şifreli, yanıtta ve veritabanında açık görünmez; süresi dolunca / 401'de yenilenir.
- Otomatik kayıt olmayan sunucuda istemci kimliği istenir; eski sunucularda (kaynak bilgisi yok) kök adres denenir.
- Yetki: yalnızca integration:manage; ekip üyesi ve RECDx platform personeli (KVKK) erişemez; "_" alanları gönderilemez.
"""
import asyncio
import base64
import hashlib
import json
import time
import uuid
from urllib.parse import parse_qs, urlsplit

import httpx
import pytest

from app.config import settings
from app.core import vault
from app.integrations import base, mcp, oauth
from tests.test_integrations import _super
from tests.test_workflow import _exec, world  # noqa: F401  (fikstür)

MCP_URL = "https://mcp.example/mcp"
LEGACY_URL = "https://eski.example/mcp"
NODCR_URL = "https://kayitsiz.example/mcp"


def _seed(client):
    from app.db.session import AsyncSessionLocal
    from app.services.integration_catalog import ensure_catalog

    async def go():
        async with AsyncSessionLocal() as s:
            return await ensure_catalog(s)
    return client.portal.call(go)


@pytest.fixture
def fake_oauth(monkeypatch):
    st = {"valid": {"erisim-1"}, "challenge": None, "token_requests": [], "registered": 0, "refreshes": 0}

    def mcp_reply(req, msg):
        if msg["method"] == "initialize":
            return httpx.Response(200, headers={"mcp-session-id": "s1"}, json={"jsonrpc": "2.0", "id": msg["id"], "result": {
                "protocolVersion": "2025-06-18", "capabilities": {"tools": {}}, "serverInfo": {"name": "Sahte İş Takibi", "version": "2"}}})
        if msg["method"] == "notifications/initialized":
            return httpx.Response(202)
        if msg["method"] == "tools/list":
            return httpx.Response(200, json={"jsonrpc": "2.0", "id": msg["id"], "result": {"tools": [
                {"name": "list_issues", "description": "Kayıtları listeler", "annotations": {"readOnlyHint": True}},
                {"name": "create_issue", "description": "Kayıt açar"}]}})
        return httpx.Response(200, json={"jsonrpc": "2.0", "id": msg["id"], "result": {"content": [{"type": "text", "text": "3 kayıt"}]}})

    def handler(req: httpx.Request) -> httpx.Response:
        u = str(req.url)
        if req.method == "DELETE":
            return httpx.Response(200)
        if any(u.startswith(x) for x in (MCP_URL, LEGACY_URL, NODCR_URL, "https://bilinmez.example/mcp")):
            auth = req.headers.get("authorization", "")
            if auth.removeprefix("Bearer ") not in st["valid"]:
                hdr = 'Bearer realm="OAuth", scope="issues:read issues:write"'
                if u.startswith(MCP_URL):
                    hdr += ', resource_metadata="https://mcp.example/.well-known/oauth-protected-resource/mcp"'
                return httpx.Response(401, headers={"www-authenticate": hdr})
            return mcp_reply(req, json.loads(req.content))
        if u == "https://mcp.example/.well-known/oauth-protected-resource/mcp":
            return httpx.Response(200, json={"resource": MCP_URL, "authorization_servers": ["https://auth.example"]})
        if u == "https://kayitsiz.example/.well-known/oauth-protected-resource/mcp":
            return httpx.Response(200, json={"resource": NODCR_URL, "authorization_servers": ["https://kayitsiz.example"]})
        if u in ("https://auth.example/.well-known/oauth-authorization-server", "https://eski.example/.well-known/oauth-authorization-server"):
            root = "https://" + urlsplit(u).netloc
            return httpx.Response(200, json={"issuer": root, "authorization_endpoint": f"{root}/authorize",
                                             "token_endpoint": f"{root}/token", "registration_endpoint": f"{root}/register",
                                             "code_challenge_methods_supported": ["S256"]})
        if u == "https://kayitsiz.example/.well-known/oauth-authorization-server":
            return httpx.Response(200, json={"issuer": "https://kayitsiz.example", "authorization_endpoint": "https://kayitsiz.example/authorize",
                                             "token_endpoint": "https://kayitsiz.example/token", "code_challenge_methods_supported": ["S256"],
                                             "token_endpoint_auth_methods_supported": ["client_secret_basic"]})
        if u.endswith("/register") and req.method == "POST":
            body = json.loads(req.content)
            assert body["redirect_uris"] == [oauth.redirect_uri()] and body["token_endpoint_auth_method"] == "none"
            st["registered"] += 1
            return httpx.Response(201, json={"client_id": f"rec-{st['registered']}"})
        if u.endswith("/token") and req.method == "POST":
            form = {k: v[0] for k, v in parse_qs(req.content.decode()).items()}
            st["token_requests"].append({**form, "_basic": req.headers.get("authorization")})
            if form["grant_type"] == "authorization_code":
                digest = base64.urlsafe_b64encode(hashlib.sha256(form["code_verifier"].encode()).digest()).decode().rstrip("=")
                if form.get("code") != "kod-1" or digest != st["challenge"] or form.get("redirect_uri") != oauth.redirect_uri():
                    return httpx.Response(400, json={"error": "invalid_grant", "error_description": "kod veya doğrulayıcı hatalı"})
                return httpx.Response(200, json={"access_token": "erisim-1", "refresh_token": "yenile-1", "expires_in": 3600, "token_type": "Bearer"})
            if form["grant_type"] == "refresh_token" and form.get("refresh_token") == "yenile-1":
                st["refreshes"] += 1
                st["valid"].add("erisim-2")
                return httpx.Response(200, json={"access_token": "erisim-2", "expires_in": 3600})
            return httpx.Response(400, json={"error": "invalid_grant"})
        return httpx.Response(404)
    monkeypatch.setattr(base, "TRANSPORT", httpx.MockTransport(handler))
    mcp._cache.clear()
    return st


def _start(client, h, base_url, cid, st):
    r = client.post(f"{base_url}/{cid}/oauth/start", headers=h)
    assert r.status_code == 200, r.text
    q = {k: v[0] for k, v in parse_qs(urlsplit(r.json()["authorize_url"]).query).items()}
    st["challenge"] = q.get("code_challenge")
    return r.json(), q


def _callback(client, **params):
    r = client.get("/api/v1/integrations/oauth/callback", params=params, follow_redirects=False)
    assert r.status_code == 302
    loc = r.headers["location"]
    assert loc.startswith(settings.PUBLIC_APP_URL.rstrip("/") + "/?") and loc.endswith("#/company-admin")
    return {k: v[0] for k, v in parse_qs(urlsplit(loc.split("#")[0]).query).items()}


def _secrets(db, cid):
    row = _exec(db, "SELECT secret, tenant_id FROM integration_connections WHERE id = %s", cid)
    return row[0], vault.unseal(row[0], f"{row[1]}:{cid}")


def test_catalog_visible_and_managed_by_super_admin_only(client, db, world):
    w = world
    _seed(client)
    r = client.get("/api/v1/integrations/catalog", headers=w["member"]["h"])
    assert r.status_code == 200
    by = {e["code"]: e for e in r.json()["entries"]}
    assert {"odoo", "logo", "linear", "notion", "custom_mcp"} <= set(by)
    assert by["linear"]["method"] == "MCP_OAUTH" and by["linear"]["preset"] == {"url": "https://mcp.linear.app/mcp", "auth_mode": "oauth"}
    assert by["logo"]["method"] == "EDGE" and by["sap_b1"]["method"] == "PLANNED" and by["sap_b1"]["connector"] is None
    assert r.json()["redirect_uri"].endswith("/api/v1/integrations/oauth/callback")

    sa = _super(client, db)
    assert client.get("/api/v1/system/integration-catalog", headers=w["admin"]["h"]).status_code == 403
    card = {"code": f"test_{uuid.uuid4().hex[:6]}", "title": "Test ERP", "category": "ERP", "method": "MCP_OAUTH", "connector": "mcp",
            "preset": {"url": "https://mcp.testerp.example/mcp"}, "setup_steps": ["Giriş yapın"], "keywords": "test"}
    assert client.post("/api/v1/system/integration-catalog", headers=w["admin"]["h"], json=card).status_code == 403
    assert client.post("/api/v1/system/integration-catalog", headers=sa, json={**card, "method": "BILINMEZ"}).status_code == 422
    assert client.post("/api/v1/system/integration-catalog", headers=sa, json={**card, "preset": {"sifre": "x"}}).status_code == 422
    assert client.post("/api/v1/system/integration-catalog", headers=sa, json={**card, "connector": "edge"}).status_code == 422
    assert client.post("/api/v1/system/integration-catalog", headers=sa, json={**card, "code": "Büyük Harf"}).status_code == 422
    r = client.post("/api/v1/system/integration-catalog", headers=sa, json=card)
    assert r.status_code == 201, r.text
    assert r.json()["preset"]["auth_mode"] == "oauth"  # tek tık giriş kartında kimlik yöntemi zorunlu oauth
    assert client.post("/api/v1/system/integration-catalog", headers=sa, json=card).status_code == 409
    eid = r.json()["id"]
    assert client.put(f"/api/v1/system/integration-catalog/{eid}", headers=sa, json={**card, "status": "ARCHIVED"}).status_code == 200
    codes = {e["code"] for e in client.get("/api/v1/integrations/catalog", headers=w["member"]["h"]).json()["entries"]}
    assert card["code"] not in codes
    assert _seed(client) == 0  # tohum yeniden çalışınca kopya eklenmez


def test_mcp_oauth_login_refresh_and_logout(client, db, world, fake_oauth):
    w = world
    _seed(client)
    h = w["admin"]["h"]
    base_url = f"/api/v1/company/{w['tenant']}/integrations"
    body = {"connector": "mcp", "catalog_code": "custom_mcp", "name": f"İş takibi {uuid.uuid4().hex[:4]}",
            "config": {"url": MCP_URL, "auth_mode": "oauth"}}
    assert client.post(base_url, headers=h, json={**body, "catalog_code": "odoo"}).status_code == 422  # kart başka sistemin
    assert client.post(base_url, headers=h, json={**body, "secrets": {"_access_token": "sahte"}}).status_code == 422
    r = client.post(base_url, headers=h, json=body)
    assert r.status_code == 201, r.text
    conn = r.json()
    cid = conn["id"]
    assert conn["catalog_code"] == "custom_mcp" and conn["oauth"]["connected"] is False
    r = client.get(f"{base_url}/{cid}/tools", headers=h)
    assert r.status_code == 502 and "Giriş yap" in r.json()["detail"]

    # Yetki: ekip üyesi ve RECDx personeli giriş başlatamaz
    assert client.post(f"{base_url}/{cid}/oauth/start", headers=w["member"]["h"]).status_code == 403
    assert client.post(f"{base_url}/{cid}/oauth/start", headers=_super(client, db)).status_code == 403

    started, q = _start(client, h, base_url, cid, fake_oauth)
    assert started["authorize_url"].startswith("https://auth.example/authorize?")
    assert q["client_id"] == "rec-1" and q["code_challenge_method"] == "S256" and q["resource"] == MCP_URL
    assert q["redirect_uri"] == oauth.redirect_uri() and q["scope"] == "issues:read issues:write" and len(q["state"]) >= 32
    assert _callback(client, state="uydurma", code="kod-1")["oauth"] == "error"
    back = _callback(client, state=q["state"], code="kod-1")
    assert back == {"oauth": "ok", "conn": cid}
    assert _callback(client, state=q["state"], code="kod-1")["oauth"] == "error"  # state tek kullanımlık
    tr = fake_oauth["token_requests"][-1]
    assert tr["resource"] == MCP_URL and tr["client_id"] == "rec-1"

    r = client.get(base_url, headers=h)
    me = next(c for c in r.json() if c["id"] == cid)
    assert me["oauth"]["connected"] is True and me["oauth"]["can_refresh"] is True and me["last_test_ok"] is True
    assert "erisim-1" not in r.text and "yenile-1" not in r.text and not any(k.startswith("_") for k in me["secrets_set"])
    raw, sec = _secrets(db, cid)
    assert "erisim-1" not in raw and sec["_access_token"] == "erisim-1" and sec["_client_id"] == "rec-1"

    tools = client.get(f"{base_url}/{cid}/tools", headers=h).json()
    assert {t["name"]: t["kind"] for t in tools} == {"list_issues": "READ", "create_issue": "WRITE"}
    assert client.post(f"{base_url}/{cid}/test", headers=h).json()["detail"].startswith("Sahte İş Takibi 2")

    # Sunucu token'ı geçersiz kıldı: bir kez yenilenir, yeni token kasaya yazılır
    fake_oauth["valid"].discard("erisim-1")
    mcp._cache.clear()
    tools = client.get(f"{base_url}/{cid}/tools", headers=h)
    assert tools.status_code == 200, tools.text
    assert fake_oauth["refreshes"] == 1 and _secrets(db, cid)[1]["_access_token"] == "erisim-2"
    assert _secrets(db, cid)[1]["_refresh_token"] == "yenile-1"  # sunucu yenisini vermedi: eskisi korunur

    # Süresi dolmak üzere: istekten önce tazelenir
    _, sec = _secrets(db, cid)
    from app.integrations.base import Context
    ctx = Context(config={"url": MCP_URL, "auth_mode": "oauth"}, secrets={**sec, "_expires_at": int(time.time()) + 10}, connection_id=None)
    assert asyncio.run(oauth.access_token(ctx)) == "erisim-2" and fake_oauth["refreshes"] == 2

    # Kullanıcı izin vermedi
    _, q2 = _start(client, h, base_url, cid, fake_oauth)
    assert fake_oauth["registered"] == 1  # kayıtlı istemci yeniden kullanıldı
    back = _callback(client, state=q2["state"], error="access_denied")
    assert back["oauth"] == "error" and "izin verilmedi" in back["msg"]

    r = client.post(f"{base_url}/{cid}/oauth/disconnect", headers=h)
    assert r.status_code == 200 and r.json()["oauth"]["connected"] is False
    assert "_access_token" not in _secrets(db, cid)[1] and _secrets(db, cid)[1]["_client_id"] == "rec-1"

    # Adres değişince eski oturum ve kayıtlı istemci silinir
    _start(client, h, base_url, cid, fake_oauth)
    client.put(f"{base_url}/{cid}", headers=h, json={"config": {"url": LEGACY_URL, "auth_mode": "oauth"}})
    assert "_client_id" not in _secrets(db, cid)[1]


def test_oauth_legacy_discovery_and_manual_client(client, db, world, fake_oauth):
    w = world
    h = w["admin"]["h"]
    base_url = f"/api/v1/company/{w['tenant']}/integrations"
    # Kaynak bilgisi olmayan eski sunucu: MCP adresinin kökündeki yetkilendirme sunucusu bulunur
    legacy = client.post(base_url, headers=h, json={"connector": "mcp", "name": f"Eski {uuid.uuid4().hex[:4]}",
                                                    "config": {"url": LEGACY_URL, "auth_mode": "oauth"}}).json()
    _, q = _start(client, h, base_url, legacy["id"], fake_oauth)
    assert q["resource"] == LEGACY_URL and "scope" in q

    # Otomatik kayıt yok: istemci kimliği istenir; girilince temel kimlik doğrulamayla token alınır
    nodcr = client.post(base_url, headers=h, json={"connector": "mcp", "name": f"Kayıtsız {uuid.uuid4().hex[:4]}",
                                                   "config": {"url": NODCR_URL, "auth_mode": "oauth"}}).json()
    r = client.post(f"{base_url}/{nodcr['id']}/oauth/start", headers=h)
    assert r.status_code == 422 and oauth.redirect_uri() in r.json()["detail"]
    client.put(f"{base_url}/{nodcr['id']}", headers=h, json={"secrets": {"client_id": "sirket-uyg", "client_secret": "gizli-anahtar"}})
    _, q = _start(client, h, base_url, nodcr["id"], fake_oauth)
    assert q["client_id"] == "sirket-uyg"
    assert _callback(client, state=q["state"], code="kod-1")["oauth"] == "ok"
    tr = fake_oauth["token_requests"][-1]
    assert tr["_basic"].startswith("Basic ") and "client_secret" not in tr  # sunucu yalnızca basic destekliyor
    listed = next(c for c in client.get(base_url, headers=h).json() if c["id"] == nodcr["id"])
    assert listed["secrets_set"] == {"client_id": True, "client_secret": True} and "gizli-anahtar" not in json.dumps(listed)


def test_oauth_start_requires_oauth_mode_and_no_auth_server(client, world, fake_oauth, monkeypatch):
    w = world
    h = w["admin"]["h"]
    base_url = f"/api/v1/company/{w['tenant']}/integrations"
    tok = client.post(base_url, headers=h, json={"connector": "mcp", "name": f"Anahtarlı {uuid.uuid4().hex[:4]}",
                                                 "config": {"url": MCP_URL}, "secrets": {"token": "erisim-1"}}).json()
    assert client.post(f"{base_url}/{tok['id']}/oauth/start", headers=h).status_code == 409
    assert "oauth" not in tok
    # Yetkilendirme sunucusu bulunamayan adres
    bad = client.post(base_url, headers=h, json={"connector": "mcp", "name": f"Yok {uuid.uuid4().hex[:4]}",
                                                 "config": {"url": "https://bilinmez.example/mcp", "auth_mode": "oauth"}}).json()
    r = client.post(f"{base_url}/{bad['id']}/oauth/start", headers=h)
    assert r.status_code == 502 and "yetkilendirme sunucusu bulunamadı" in r.json()["detail"]


def test_oauth_rejects_insecure_endpoints(fake_oauth, monkeypatch):
    monkeypatch.setattr(settings, "INTEGRATIONS_ALLOW_PRIVATE_NETWORK", False)
    with pytest.raises(Exception, match="https değil"):
        oauth._https("http://auth.example/token", "token")
    assert oauth._https("https://auth.example/token", "token")


def test_recai_connection_advisor(client, world, monkeypatch):
    from app.services.evren_client import ChatResult, evren_client

    w = world
    _seed(client)
    answers = [json.dumps({"code": "logo", "summary": "Logo Tiger 3 şirket sunucusunda; Edge ajanıyla bağlanılır.",
                           "steps": ["Ajan anahtarı oluşturun", "Ajanı Logo sunucusuna kurun"], "notes": "Logo SQL kullanıcısı salt okunur olsun."}),
               json.dumps({"code": "uydurma_kart", "summary": "x", "steps": []})]
    seen = []

    async def chat(model_code, messages, **kw):
        seen.append(messages)
        return ChatResult(answers.pop(0), None, 500, 120, {})
    monkeypatch.setattr(evren_client, "chat", chat)
    url = f"/api/v1/company/{w['tenant']}/integrations/advise"
    assert client.post(url, headers=w["member"]["h"], json={"text": "Logo Tiger 3"}).status_code == 403
    r = client.post(url, headers=w["admin"]["h"], json={"text": "Logo Tiger 3 kullanıyoruz, sunucu şirkette"})
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["entry"]["code"] == "logo" and d["entry"]["method"] == "EDGE" and len(d["steps"]) == 2
    assert "logo: Logo" in seen[0][0]["content"] and "RECAi" in seen[0][0]["content"]
    d = client.post(url, headers=w["admin"]["h"], json={"text": "Bilinmeyen bir sistem"}).json()
    assert d["entry"] is None  # katalogda olmayan kart gösterilmez
