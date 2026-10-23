"""Telegram bağlayıcısı (ADIM 10.1/10.3): şirketin kendi botuyla bir gruba/kanala mesaj (yazma = insan onayı)."""
from typing import Any, Dict

import httpx

from app.integrations.base import READ, WRITE, Connector, Context, Field, Tool, ToolError, require

API = "https://api.telegram.org"


async def _call(ctx: Context, method: str, payload: Dict[str, Any] = None) -> Dict[str, Any]:
    token = ctx.secrets.get("bot_token")
    if not token:
        raise ToolError("Bot token tanımlı değil.")
    try:
        async with httpx.AsyncClient(timeout=15) as c:
            r = await c.post(f"{API}/bot{token}/{method}", json=payload or {})
    except httpx.HTTPError as exc:
        raise ToolError(f"Telegram'a ulaşılamadı ({exc.__class__.__name__}).")  # adres (token içerir) yazılmaz
    data = r.json() if r.content else {}
    if not data.get("ok"):
        raise ToolError(f"Telegram hata döndürdü: {data.get('description') or r.status_code}")
    return data.get("result") or {}


async def _get_bot(ctx: Context, args: Dict[str, Any]):
    me = await _call(ctx, "getMe")
    return {"username": me.get("username"), "name": me.get("first_name")}


async def _send(ctx: Context, args: Dict[str, Any]):
    require(args, "text")
    chat_id = args.get("chat_id") or ctx.config.get("default_chat_id")
    if not chat_id:
        raise ToolError("Hedef sohbet (chat_id) yok; bağlantıda varsayılan sohbet tanımlayın.")
    msg = await _call(ctx, "sendMessage", {"chat_id": chat_id, "text": str(args["text"])[:4000]})
    return {"message_id": msg.get("message_id"), "chat_id": chat_id}


async def _test(ctx: Context) -> str:
    me = await _call(ctx, "getMe")
    return f"@{me.get('username')} botuna bağlanıldı"


CONNECTOR = Connector(
    code="telegram", title="Telegram",
    description="Şirketin kendi Telegram botuyla bir gruba veya kanala bilgilendirme mesajı gönderir.",
    config_fields=[Field("default_chat_id", "Varsayılan sohbet / grup kimliği", required=False, placeholder="-1001234567890",
                         help="Mesajın gideceği grup veya kanal; botun o gruba ekli olması gerekir.")],
    secret_fields=[Field("bot_token", "Bot token", help="@BotFather'dan alınır. Kasada şifreli saklanır.")],
    static_tools=[
        Tool("get_bot", "Bağlı Telegram botunun adını döner.", {"type": "object", "properties": {}}, READ, _get_bot),
        Tool("send_message", "Telegram grubuna/kanalına mesaj gönderir.",
             {"type": "object", "properties": {"text": {"type": "string", "description": "Mesaj metni"},
                                               "chat_id": {"type": "string", "description": "Hedef sohbet (boşsa varsayılan)"}},
              "required": ["text"]}, WRITE, _send),
    ],
    test_fn=_test,
)
