"""
Bağlayıcı çerçevesi (ADIM 10.1).

Bir bağlayıcı (Connector) bir dış sistem türüdür (Odoo, Telegram, Trello...). Her bağlayıcı:
- config_fields: düz ayarlar (adres, veritabanı adı, varsayılan sohbet...) — ekranda gösterilir;
- secret_fields: kimlik bilgileri (token, parola) — kimlik kasasında şifreli saklanır, asla geri dönmez;
- tools(): araçlar, MCP araç şemasıyla (name, description, inputSchema) + tür: READ (anında) / WRITE (insan onayı);
- test(): bağlantıyı dener (yalnızca okuma).
Araç sonuçları kısa ve JSON olarak döner; büyük sonuçlar kırpılır (LLM bağlamı ve kayıt şişmesin).
"""
import asyncio
import ipaddress
import json
import socket
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, Dict, List, Optional
from urllib.parse import urlsplit

import httpx

READ, WRITE = "READ", "WRITE"
RESULT_LIMIT = 8000
# Testlerde sahte dış sistem: httpx.MockTransport atanır (gerçek ağa çıkılmaz)
TRANSPORT: Optional[httpx.AsyncBaseTransport] = None


def http_client(timeout: float = 15, **kw) -> httpx.AsyncClient:
    # Yönlendirme izlenmez (follow_redirects=False): dış sunucu isteği iç ağa yönlendiremez
    return httpx.AsyncClient(timeout=timeout, transport=TRANSPORT, follow_redirects=False, **kw)


async def guard_url(url: str) -> str:
    """Müşterinin girdiği adres: yalnızca http(s), kimlik bilgisi gömülmemiş ve özel/yerel ağa çözülmeyen ana bilgisayar
    (SSRF koruması: veritabanı, backend, bulut meta veri adresi vb. hedeflenemez). Geliştirmede ayarla açılır."""
    from app.config import settings

    parts = urlsplit((url or "").strip())
    if parts.scheme not in ("http", "https") or not parts.hostname:
        raise ToolError("Adres http(s):// ile başlamalı.")
    if parts.username or parts.password:
        raise ToolError("Adrese kullanıcı adı/parola yazmayın; kimlik bilgisi ayrı alana girilir.")
    if settings.INTEGRATIONS_ALLOW_PRIVATE_NETWORK:
        return url
    try:
        infos = await asyncio.get_running_loop().getaddrinfo(parts.hostname, parts.port or (443 if parts.scheme == "https" else 80))
    except socket.gaierror:
        return url  # çözülemeyen ad: istek zaten başarısız olur
    for info in infos:
        ip = ipaddress.ip_address(info[4][0])
        if not ip.is_global or ip.is_multicast:
            raise ToolError("Bu adres özel/yerel ağa çıkıyor; yalnızca internetten erişilebilen sunucular bağlanabilir.")
    return url


class ToolError(Exception):
    """Araç çalıştı ama dış sistem hata verdi veya girdi geçersiz; mesaj kullanıcıya/AI'a gösterilebilir (gizli bilgi içermez)."""


@dataclass
class Field:
    key: str
    label: str
    required: bool = True
    placeholder: str = ""
    help: str = ""
    options: List[List[str]] = field(default_factory=list)  # [[değer, etiket]]: ekranda seçim kutusu


# Her bağlantıda ortak: yalnızca okuma seçilirse yazma araçları AI personele hiç sunulmaz
ACCESS_FIELD = Field("access", "Erişim", required=False,
                     help="Yalnızca okuma: AI personel bu sistemde hiçbir şey değiştiremez (yazma araçları gizlenir).",
                     options=[["READ_WRITE", "Okuma ve yazma (yazmalar insan onayıyla)"], ["READ_ONLY", "Yalnızca okuma"]])


def read_only(config: Dict[str, Any]) -> bool:
    return (config or {}).get("access") == "READ_ONLY"


@dataclass
class Tool:
    name: str
    description: str
    input_schema: Dict[str, Any]
    kind: str
    run: Callable[["Context", Dict[str, Any]], Awaitable[Any]]

    def mcp(self) -> Dict[str, Any]:
        return {"name": self.name, "description": self.description, "inputSchema": self.input_schema,
                "annotations": {"readOnlyHint": self.kind == READ}}


@dataclass
class Context:
    """Aracın çalıştığı bağlantı: düz ayarlar ve çözülmüş kimlik bilgileri (yalnızca bellek içinde)."""
    config: Dict[str, Any]
    secrets: Dict[str, Any]
    tenant_id: Optional[str] = None
    connection_id: Optional[str] = None
    state: Dict[str, Any] = field(default_factory=dict)  # bağlayıcının çalışma durumu (Edge: ajanın şablon kataloğu, son görülme)


@dataclass
class Connector:
    code: str
    title: str
    description: str
    config_fields: List[Field] = field(default_factory=list)
    secret_fields: List[Field] = field(default_factory=list)
    tools_fn: Optional[Callable[[Context], Awaitable[List[Tool]]]] = None
    static_tools: List[Tool] = field(default_factory=list)
    test_fn: Optional[Callable[[Context], Awaitable[str]]] = None

    @property
    def all_config_fields(self) -> List[Field]:
        return self.config_fields + [ACCESS_FIELD]

    async def tools(self, ctx: Context) -> List[Tool]:
        """Araç listesi: çoğu bağlayıcıda sabit; dış MCP sunucusunda tools/list ile keşfedilir.
        Yalnızca okuma bağlantısında yazma araçları listelenmez."""
        tools = await self.tools_fn(ctx) if self.tools_fn else list(self.static_tools)
        return [t for t in tools if t.kind == READ] if read_only(ctx.config) else tools

    async def test(self, ctx: Context) -> str:
        return await self.test_fn(ctx) if self.test_fn else "Tanımlı"

    def describe(self) -> Dict[str, Any]:
        return {"code": self.code, "title": self.title, "description": self.description,
                "config_fields": [f.__dict__ for f in self.all_config_fields],
                "secret_fields": [f.__dict__ for f in self.secret_fields],
                "tools": [{"name": t.name, "description": t.description, "kind": t.kind} for t in self.static_tools],
                "dynamic_tools": self.tools_fn is not None}


def clip(result: Any) -> Any:
    """Büyük sonuçları kırpar; JSON'a çevrilemeyeni metne çevirir."""
    try:
        text = json.dumps(result, ensure_ascii=False, default=str)
    except (TypeError, ValueError):
        text = str(result)
        result = text
    if len(text) <= RESULT_LIMIT:
        return result
    return {"truncated": True, "preview": text[:RESULT_LIMIT]}


def require(args: Dict[str, Any], *keys: str) -> None:
    missing = [k for k in keys if args.get(k) in (None, "")]
    if missing:
        raise ToolError(f"Eksik alan: {', '.join(missing)}")
