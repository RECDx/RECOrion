"""
ADIM 10.4: dış MCP sunucusu bağlama (Streamable HTTP; sahte sunucu, gerçek ağa çıkılmaz).

- initialize → notifications/initialized → istek; Mcp-Session-Id taşınır; yanıt JSON veya SSE.
- tools/list sayfalı; readOnlyHint=true OKUMA, diğerleri YAZMA (insan onayı); yalnızca okuma bağlantısında yazmalar gizli.
- Araç adı LLM için güvenli biçime çevrilir (nokta/uzun ad), çakışmaz. Araç listesi önbellekte.
- isError ve 401 anlaşılır hata; token mesajda görünmez.
- SSRF: özel/yerel/meta veri adresleri ve adrese gömülü parola reddedilir.
"""
import asyncio
import json
import uuid

import httpx
import pytest

from app.config import settings
from app.db.models import IntegrationConnection
from app.integrations import base, get, mcp
from app.integrations.base import READ, WRITE, Context, ToolError, guard_url
from app.services import tool_gateway

TOKEN = "mcp-sahte-token-42"
URL = "https://mcp.example/mcp"
LONG = "sirket.depo.stok_hareketleri_ayrintili_raporu_olustur_ve_ozetle_v2"


def _sse(obj):
    return httpx.Response(200, headers={"content-type": "text/event-stream"},
                          text=f"event: message\ndata: {json.dumps(obj)}\n\n")


@pytest.fixture
def fake_mcp(monkeypatch):
    log = {"methods": [], "sessions": set(), "calls": []}

    def handler(req: httpx.Request) -> httpx.Response:
        if req.method == "DELETE":
            return httpx.Response(200)
        if req.headers.get("authorization") != f"Bearer {TOKEN}":
            return httpx.Response(401, text=f"bad token {req.headers.get('authorization')}")
        msg = json.loads(req.content)
        log["methods"].append(msg["method"])
        if msg["method"] == "initialize":
            assert msg["params"]["clientInfo"]["name"] == "RECOrion"
            return httpx.Response(200, headers={"mcp-session-id": "oturum-1"},
                                  json={"jsonrpc": "2.0", "id": msg["id"], "result": {
                                      "protocolVersion": "2025-06-18", "capabilities": {"tools": {}},
                                      "serverInfo": {"name": "Sahte ERP MCP", "version": "0.9"}}})
        log["sessions"].add(req.headers.get("mcp-session-id"))
        if msg["method"] == "notifications/initialized":
            return httpx.Response(202)
        if msg["method"] == "tools/list":
            if not msg["params"].get("cursor"):
                return _sse({"jsonrpc": "2.0", "id": msg["id"], "result": {"nextCursor": "s2", "tools": [
                    {"name": "stok.sorgula", "description": "Stok miktarı", "annotations": {"readOnlyHint": True},
                     "inputSchema": {"type": "object", "properties": {"sku": {"type": "string"}}, "required": ["sku"]}}]}})
            return httpx.Response(200, json={"jsonrpc": "2.0", "id": msg["id"], "result": {"tools": [
                {"name": "siparis_olustur", "description": "Sipariş açar", "inputSchema": {"type": "object", "properties": {}}},
                {"name": LONG, "description": "Uzun adlı araç", "annotations": {"readOnlyHint": True}},
                {"name": "hata_veren", "annotations": {"readOnlyHint": True}}]}})
        if msg["method"] == "tools/call":
            log["calls"].append(msg["params"])
            name = msg["params"]["name"]
            if name == "hata_veren":
                return _sse({"jsonrpc": "2.0", "id": msg["id"], "result": {"isError": True, "content": [{"type": "text", "text": "Depo kapalı"}]}})
            if name == "yok":
                return httpx.Response(200, json={"jsonrpc": "2.0", "id": msg["id"], "error": {"code": -32602, "message": "Bilinmeyen araç"}})
            return _sse({"jsonrpc": "2.0", "id": msg["id"], "result": {
                "content": [{"type": "text", "text": f"{msg['params']['arguments'].get('sku')}: 12 adet"}], "structuredContent": {"qty": 12}}})
        return httpx.Response(400)
    monkeypatch.setattr(base, "TRANSPORT", httpx.MockTransport(handler))
    mcp._cache.clear()
    return log


def _ctx(**cfg):
    return Context(config={"url": URL, **cfg}, secrets={"token": TOKEN})


def test_mcp_discovery_and_calls(fake_mcp):
    ctx = _ctx()
    tools = {t.name: t for t in asyncio.run(get("mcp").tools(ctx))}
    assert set(tools) == {"stok.sorgula", "siparis_olustur", LONG, "hata_veren"}  # iki sayfa birleşti
    assert tools["stok.sorgula"].kind == READ and tools["siparis_olustur"].kind == WRITE  # ipucu yoksa yazma (onaylı)
    assert fake_mcp["methods"][:3] == ["initialize", "notifications/initialized", "tools/list"]
    assert fake_mcp["sessions"] == {"oturum-1"}

    n = len(fake_mcp["methods"])
    asyncio.run(get("mcp").tools(ctx))
    assert len(fake_mcp["methods"]) == n  # önbellekten

    r = asyncio.run(tools["stok.sorgula"].run(ctx, {"sku": "A-1"}))
    assert r == {"text": "A-1: 12 adet", "data": {"qty": 12}}
    with pytest.raises(ToolError, match="Depo kapalı"):
        asyncio.run(tools["hata_veren"].run(ctx, {}))
    with pytest.raises(ToolError, match="Bilinmeyen araç"):
        asyncio.run(mcp._runner("yok")(ctx, {}))

    ro = {t.name for t in asyncio.run(get("mcp").tools(_ctx(access="READ_ONLY")))}
    assert "siparis_olustur" not in ro and "stok.sorgula" in ro
    info = asyncio.run(get("mcp").test(ctx))
    assert info.startswith("Sahte ERP MCP 0.9 · 4 araç (3 okuma, 1 yazma")


def test_admin_can_declare_unmarked_tools_as_read(fake_mcp):
    kinds = {t.name: t.kind for t in asyncio.run(get("mcp").tools(_ctx(read_tools="siparis_olustur_degil, hata_veren")))}
    assert kinds["siparis_olustur"] == WRITE  # listede yok: işaretsiz araç yazma kalır
    kinds = {t.name: t.kind for t in asyncio.run(get("mcp").tools(_ctx(read_tools=" siparis_olustur ")))}
    assert kinds["siparis_olustur"] == READ


def test_mcp_auth_error_hides_token(fake_mcp):
    with pytest.raises(ToolError, match="401") as e:
        asyncio.run(get("mcp").tools(Context({"url": URL}, {"token": "yanlis-gizli-token"})))
    assert "yanlis-gizli-token" not in str(e.value)


def test_llm_function_names_are_safe_and_unique():
    conn = IntegrationConnection(id=uuid.uuid4())
    names = [tool_gateway.fn_name(conn, t) for t in ("stok.sorgula", "stok_sorgula", LONG, LONG + "_baska", "get_bot")]
    import re
    assert all(re.fullmatch(r"[a-zA-Z0-9_-]{1,64}", n) for n in names)
    assert len(set(names)) == len(names)
    assert names[-1].endswith("__get_bot")  # sade adlar değişmez (önceki kayıtlarla uyumlu)


@pytest.mark.parametrize("url", ["http://127.0.0.1:8000/mcp", "http://localhost/mcp", "http://10.1.2.3/mcp", "http://169.254.169.254/latest",
                                 "http://[::1]/mcp", "http://postgres:5432/", "ftp://mcp.example/", "https://kullanici:parola@mcp.example/mcp"])
def test_ssrf_guard_blocks_private_targets(url, monkeypatch):
    monkeypatch.setattr(settings, "INTEGRATIONS_ALLOW_PRIVATE_NETWORK", False)
    with pytest.raises(ToolError):
        asyncio.run(guard_url(url))


def test_ssrf_guard_allows_public_and_dev_override(monkeypatch):
    monkeypatch.setattr(settings, "INTEGRATIONS_ALLOW_PRIVATE_NETWORK", False)
    assert asyncio.run(guard_url("https://8.8.8.8/mcp")) == "https://8.8.8.8/mcp"
    monkeypatch.setattr(settings, "INTEGRATIONS_ALLOW_PRIVATE_NETWORK", True)
    assert asyncio.run(guard_url("http://127.0.0.1:9000/mcp"))
    with pytest.raises(ToolError):  # gömülü parola her durumda reddedilir
        asyncio.run(guard_url("https://a:b@mcp.example/"))
