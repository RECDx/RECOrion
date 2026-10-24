"""Dış MCP sunucusu bağlayıcısı (ADIM 10.4): Streamable HTTP taşıması (MCP 2025-06-18).

- Araçlar sunucudan tools/list ile keşfedilir (sayfalı, en fazla MAX_TOOLS); şirket yöneticisi hangi AI personelin hangi aracı
  kullanacağını yetkiyle açar (ADIM 10.1). Liste kısa süre önbellekte tutulur (her sohbet mesajında sunucuya gidilmez).
- Tür: yalnızca sunucunun readOnlyHint=true dediği araçlar OKUMA'dır; diğer her şey YAZMA sayılır ve insan onayına düşer.
- Her işlem kendi oturumunu açar: initialize → notifications/initialized → istek (Mcp-Session-Id varsa taşınır).
- Yanıt application/json veya text/event-stream (SSE) olabilir; SSE'de isteğin kimliğine ait JSON-RPC yanıtı alınır.
- Adres SSRF korumasından geçer; yönlendirme izlenmez. Kimlik bilgisi (token) kasada; hata mesajlarına yazılmaz.
- Kimlik (ADIM 12.1): erişim anahtarı (token), tek tık giriş (OAuth 2.1, app/integrations/oauth.py) veya kimliksiz.
  OAuth'ta erişim token'ı süresi dolmadan tazelenir; sunucu 401 dönerse bir kez yenilenip yeniden denenir.
"""
import hashlib
import json
import time
from typing import Any, Dict, List, Optional, Tuple

import httpx

from app.integrations import oauth
from app.integrations.base import READ, WRITE, Connector, Context, Field, Tool, ToolError, guard_url, http_client

PROTOCOL_VERSION = "2025-06-18"
MAX_TOOLS = 100
MAX_PAGES = 5
CACHE_SECONDS = 120
CLIENT_INFO = {"name": "RECOrion", "version": "1.0"}
_cache: Dict[str, Tuple[float, List[Tool]]] = {}


class _Unauthorized(ToolError):
    pass


def _headers(ctx: Context, session: Optional[str] = None) -> Dict[str, str]:
    h = {"Accept": "application/json, text/event-stream", "Content-Type": "application/json", "MCP-Protocol-Version": PROTOCOL_VERSION}
    mode = ctx.config.get("auth_mode")
    if oauth.enabled(ctx.config):
        h["Authorization"] = f"Bearer {ctx.secrets.get('_access_token') or ''}"
        token = None
    else:
        token = ctx.secrets.get("token") if mode != "none" else None
    if token:
        name = (ctx.config.get("auth_header") or "Authorization").strip()
        h[name] = f"Bearer {token}" if name.lower() == "authorization" else token
    if session:
        h["Mcp-Session-Id"] = session
    return h


def _parse(r: httpx.Response, req_id: int) -> Dict[str, Any]:
    """JSON veya SSE gövdesinden bu isteğin JSON-RPC yanıtını çıkarır."""
    ctype = r.headers.get("content-type", "")
    messages: List[Any] = []
    if "text/event-stream" in ctype:
        data: List[str] = []
        for line in r.text.splitlines() + [""]:
            if line.startswith("data:"):
                data.append(line[5:].lstrip())
            elif not line.strip() and data:  # olay sonu
                try:
                    messages.append(json.loads("\n".join(data)))
                except ValueError:
                    pass
                data = []
    else:
        try:
            body = r.json()
        except ValueError:
            raise ToolError("MCP sunucusu geçersiz yanıt döndürdü.")
        messages = body if isinstance(body, list) else [body]
    for m in messages:
        if isinstance(m, dict) and m.get("id") == req_id and ("result" in m or "error" in m):
            if m.get("error"):
                raise ToolError(f"MCP sunucusu hata döndürdü: {str(m['error'].get('message') or m['error'])[:300]}")
            return m["result"]
    raise ToolError("MCP sunucusundan bu isteğin yanıtı gelmedi.")


class _Session:
    def __init__(self, ctx: Context, client: httpx.AsyncClient, url: str):
        self.ctx, self.client, self.url, self.session, self.next_id, self.server = ctx, client, url, None, 1, {}

    async def _post(self, payload: Dict[str, Any]) -> httpx.Response:
        try:
            r = await self.client.post(self.url, json=payload, headers=_headers(self.ctx, self.session))
        except httpx.HTTPError as exc:
            raise ToolError(f"MCP sunucusuna ulaşılamadı ({exc.__class__.__name__}).")
        if r.status_code in (401, 403):
            if oauth.enabled(self.ctx.config):
                raise _Unauthorized("MCP sunucusu oturumu kabul etmedi; Entegrasyonlar ekranında yeniden 'Giriş yap'a basın.")
            raise ToolError(f"MCP sunucusu erişimi reddetti ({r.status_code}); token'ı kontrol edin.")
        if r.status_code >= 400:
            raise ToolError(f"MCP sunucusu HTTP {r.status_code} döndürdü.")
        return r

    async def request(self, method: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        req_id, self.next_id = self.next_id, self.next_id + 1
        r = await self._post({"jsonrpc": "2.0", "id": req_id, "method": method, "params": params or {}})
        return _parse(r, req_id)

    async def open(self) -> "_Session":
        req_id, self.next_id = self.next_id, self.next_id + 1
        r = await self._post({"jsonrpc": "2.0", "id": req_id, "method": "initialize", "params": {
            "protocolVersion": PROTOCOL_VERSION, "capabilities": {}, "clientInfo": CLIENT_INFO}})
        self.session = r.headers.get("mcp-session-id")
        self.server = _parse(r, req_id)
        await self._post({"jsonrpc": "2.0", "method": "notifications/initialized"})
        return self

    async def close(self) -> None:
        if self.session:  # oturumu sunucuda kapat (desteklemiyorsa önemsiz)
            try:
                await self.client.delete(self.url, headers=_headers(self.ctx, self.session))
            except httpx.HTTPError:
                pass


async def _with_session(ctx: Context, fn, timeout: float = 30):
    url = await guard_url((ctx.config.get("url") or "").strip())
    if oauth.enabled(ctx.config):
        await oauth.access_token(ctx)  # giriş yapılmamışsa anlaşılır hata; süresi dolmak üzereyse tazeler
    for attempt in (1, 2):
        async with http_client(timeout=timeout) as client:
            try:
                s = await _Session(ctx, client, url).open()
                try:
                    return await fn(s)
                finally:
                    await s.close()
            except _Unauthorized:
                if attempt == 2 or not ctx.secrets.get("_refresh_token"):
                    raise
                await oauth.refresh(ctx)  # token sunucuda geçersiz kılınmış olabilir: bir kez yenile, yeniden dene


def _cache_key(ctx: Context) -> str:
    raw = json.dumps([ctx.config.get("url"), ctx.config.get("auth_header"), ctx.config.get("read_tools"), ctx.config.get("auth_mode"),
                      ctx.secrets.get("token"), ctx.secrets.get("_access_token")], sort_keys=True)
    return hashlib.sha256(raw.encode()).hexdigest()


def _text(result: Dict[str, Any]) -> str:
    parts = []
    for c in result.get("content") or []:
        if c.get("type") == "text":
            parts.append(c.get("text") or "")
        elif c.get("type") == "resource" and isinstance(c.get("resource"), dict):
            parts.append(c["resource"].get("text") or f"[kaynak: {c['resource'].get('uri')}]")
        else:
            parts.append(f"[{c.get('type')} içerik]")
    return "\n".join(parts)


def _runner(name: str):
    async def run(ctx: Context, args: Dict[str, Any]):
        result = await _with_session(ctx, lambda s: s.request("tools/call", {"name": name, "arguments": args or {}}), timeout=30)
        if result.get("isError"):
            raise ToolError(f"Araç hata döndürdü: {_text(result)[:500]}")
        out: Dict[str, Any] = {"text": _text(result)}
        if result.get("structuredContent") is not None:
            out["data"] = result["structuredContent"]
        return out
    return run


def _declared_reads(ctx: Context) -> set:
    return {n.strip() for n in (ctx.config.get("read_tools") or "").split(",") if n.strip()}


def _to_tool(t: Dict[str, Any], declared_reads: set) -> Optional[Tool]:
    name = str(t.get("name") or "").strip()
    if not name:
        return None
    schema = t.get("inputSchema") if isinstance(t.get("inputSchema"), dict) else {}
    schema = {**schema, "type": "object"} if schema else {"type": "object", "properties": {}}
    # Sunucu readOnlyHint vermiyorsa şirket yöneticisi aracı açıkça "okuma" diye tanımlayabilir (sorumluluk yöneticide)
    read_only = bool((t.get("annotations") or {}).get("readOnlyHint")) or name in declared_reads
    desc = str(t.get("description") or t.get("title") or name)[:1000]
    return Tool(name, desc, schema, READ if read_only else WRITE, _runner(name))


async def _list(ctx: Context) -> List[Tool]:
    key = _cache_key(ctx)
    hit = _cache.get(key)
    if hit and hit[0] > time.monotonic():
        return hit[1]

    async def fetch(s: _Session):
        tools, cursor = [], None
        for _ in range(MAX_PAGES):
            page = await s.request("tools/list", {"cursor": cursor} if cursor else {})
            tools += [x for x in (_to_tool(t, _declared_reads(ctx)) for t in page.get("tools") or []) if x]
            cursor = page.get("nextCursor")
            if not cursor or len(tools) >= MAX_TOOLS:
                break
        return tools[:MAX_TOOLS]
    tools = await _with_session(ctx, fetch)
    _cache[key] = (time.monotonic() + CACHE_SECONDS, tools)
    return tools


async def _test(ctx: Context) -> str:
    _cache.pop(_cache_key(ctx), None)  # deneme her zaman tazeler
    tools = await _list(ctx)
    info = await _with_session(ctx, lambda s: _server_info(s))
    reads = sum(1 for t in tools if t.kind == READ)
    return f"{info} · {len(tools)} araç ({reads} okuma, {len(tools) - reads} yazma/onaylı)"


async def _server_info(s: _Session) -> str:
    si = s.server.get("serverInfo") or {}
    return f"{si.get('name') or 'MCP sunucusu'} {si.get('version') or ''}".strip()


CONNECTOR = Connector(
    code="mcp", title="MCP sunucusu",
    description="Şirketin kullandığı herhangi bir MCP sunucusunu (Streamable HTTP) bağlar; araçları otomatik keşfedilir.",
    config_fields=[
        Field("url", "Sunucu adresi (MCP uç noktası)", placeholder="https://mcp.sirket.com/mcp"),
        Field("auth_mode", "Kimlik yöntemi", required=False,
              help="Tek tık giriş: bağlantıyı kaydedip 'Giriş yap'a basın; servisin kendi ekranında izin verirsiniz, anahtar kopyalanmaz.",
              options=[["token", "Erişim anahtarı (token)"], ["oauth", "Tek tık giriş (OAuth)"], ["none", "Kimlik gerekmez"]]),
        Field("auth_header", "Kimlik başlığı", required=False, placeholder="Authorization",
              help="Boşsa token 'Authorization: Bearer …' olarak gönderilir; sunucu başka başlık istiyorsa adını yazın (ör. X-API-Key)."),
        Field("read_tools", "Okuma sayılacak araçlar", required=False, placeholder="read_wiki_structure, read_wiki_contents",
              help="Sunucunun salt okunur diye işaretlemediği ama yalnızca bilgi getiren araçlar (virgülle). Listede olmayan "
                   "işaretsiz araçlar yazma sayılır ve her kullanımda insan onayı ister."),
    ],
    secret_fields=[Field("token", "Erişim token'ı", required=False, help="Yalnızca 'Erişim anahtarı' yönteminde. Kasada şifreli saklanır."),
                   Field("client_id", "OAuth istemci kimliği", required=False,
                         help="Yalnızca tek tık girişte ve sunucu otomatik kaydı desteklemiyorsa (ör. HubSpot, Box): servisin geliştirici "
                              "konsolunda uygulama oluşturup kimliği buraya yazın. Boşsa RECOrion kendini otomatik kaydeder."),
                   Field("client_secret", "OAuth istemci gizli anahtarı", required=False, help="İstemci kimliğiyle birlikte verildiyse.")],
    tools_fn=_list,
    test_fn=_test,
)
