"""
Bağlayıcı çerçevesi (ADIM 10.1).

Bir bağlayıcı (Connector) bir dış sistem türüdür (Odoo, Telegram, Trello...). Her bağlayıcı:
- config_fields: düz ayarlar (adres, veritabanı adı, varsayılan sohbet...) — ekranda gösterilir;
- secret_fields: kimlik bilgileri (token, parola) — kimlik kasasında şifreli saklanır, asla geri dönmez;
- tools(): araçlar, MCP araç şemasıyla (name, description, inputSchema) + tür: READ (anında) / WRITE (insan onayı);
- test(): bağlantıyı dener (yalnızca okuma).
Araç sonuçları kısa ve JSON olarak döner; büyük sonuçlar kırpılır (LLM bağlamı ve kayıt şişmesin).
"""
import json
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, Dict, List, Optional

READ, WRITE = "READ", "WRITE"
RESULT_LIMIT = 8000


class ToolError(Exception):
    """Araç çalıştı ama dış sistem hata verdi veya girdi geçersiz; mesaj kullanıcıya/AI'a gösterilebilir (gizli bilgi içermez)."""


@dataclass
class Field:
    key: str
    label: str
    required: bool = True
    placeholder: str = ""
    help: str = ""


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

    async def tools(self, ctx: Context) -> List[Tool]:
        """Araç listesi: çoğu bağlayıcıda sabit; dış MCP sunucusunda tools/list ile keşfedilir."""
        return await self.tools_fn(ctx) if self.tools_fn else list(self.static_tools)

    async def test(self, ctx: Context) -> str:
        return await self.test_fn(ctx) if self.test_fn else "Tanımlı"

    def describe(self) -> Dict[str, Any]:
        return {"code": self.code, "title": self.title, "description": self.description,
                "config_fields": [f.__dict__ for f in self.config_fields],
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
