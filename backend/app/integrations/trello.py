"""Trello bağlayıcısı (ADIM 10.3): pano/liste/kart okuma; kart açma, taşıma ve yorum (yazma = insan onayı).

Kimlik: müşterinin kendi API anahtarı ve token'ı (trello.com/app-key), kasada şifreli. Anahtar ve token istek adresinde
gittiği için hata mesajlarına adres yazılmaz.
"""
from typing import Any, Dict

import httpx

from app.integrations.base import READ, WRITE, Connector, Context, Field, Tool, ToolError, http_client, require

API = "https://api.trello.com/1"


async def _call(ctx: Context, method: str, path: str, params: Dict[str, Any] = None) -> Any:
    key, token = ctx.secrets.get("api_key"), ctx.secrets.get("token")
    if not key or not token:
        raise ToolError("Trello API anahtarı ve token tanımlı değil.")
    q = {**(params or {}), "key": key, "token": token}
    try:
        async with http_client() as c:
            r = await c.request(method, f"{API}{path}", params=q)
    except httpx.HTTPError as exc:
        raise ToolError(f"Trello'ya ulaşılamadı ({exc.__class__.__name__}).")
    if r.status_code >= 400:
        detail = r.text[:150].strip().replace(key, "***").replace(token, "***")
        raise ToolError(f"Trello hata döndürdü: {r.status_code} {detail}")
    return r.json() if r.content else {}


def _board(ctx: Context, args: Dict[str, Any]) -> str:
    board = args.get("board_id") or ctx.config.get("default_board_id")
    if not board:
        raise ToolError("Pano (board_id) yok; önce list_boards ile seçin veya bağlantıda varsayılan pano tanımlayın.")
    return str(board)


async def _boards(ctx: Context, args: Dict[str, Any]):
    rows = await _call(ctx, "GET", "/members/me/boards", {"filter": "open", "fields": "name,url"})
    return [{"id": b["id"], "name": b["name"], "url": b.get("url")} for b in rows]


async def _lists(ctx: Context, args: Dict[str, Any]):
    rows = await _call(ctx, "GET", f"/boards/{_board(ctx, args)}/lists", {"filter": "open", "fields": "name"})
    return [{"id": x["id"], "name": x["name"]} for x in rows]


async def _cards(ctx: Context, args: Dict[str, Any]):
    path = f"/lists/{args['list_id']}/cards" if args.get("list_id") else f"/boards/{_board(ctx, args)}/cards"
    rows = await _call(ctx, "GET", path, {"fields": "name,desc,idList,due,url,closed"})
    return [{"id": c["id"], "name": c["name"], "list_id": c.get("idList"), "due": c.get("due"), "url": c.get("url"),
             "desc": (c.get("desc") or "")[:300]} for c in rows[:100] if not c.get("closed")]


async def _create(ctx: Context, args: Dict[str, Any]):
    require(args, "list_id", "name")
    card = await _call(ctx, "POST", "/cards", {"idList": args["list_id"], "name": str(args["name"])[:500],
                                               "desc": str(args.get("desc") or "")[:5000], **({"due": args["due"]} if args.get("due") else {})})
    return {"id": card.get("id"), "url": card.get("url")}


async def _move(ctx: Context, args: Dict[str, Any]):
    require(args, "card_id", "list_id")
    card = await _call(ctx, "PUT", f"/cards/{args['card_id']}", {"idList": args["list_id"]})
    return {"id": card.get("id"), "list_id": card.get("idList")}


async def _comment(ctx: Context, args: Dict[str, Any]):
    require(args, "card_id", "text")
    act = await _call(ctx, "POST", f"/cards/{args['card_id']}/actions/comments", {"text": str(args["text"])[:5000]})
    return {"comment_id": act.get("id")}


async def _test(ctx: Context) -> str:
    me = await _call(ctx, "GET", "/members/me", {"fields": "username,fullName"})
    return f"{me.get('fullName') or me.get('username')} hesabına bağlanıldı"


_BOARD = {"type": "string", "description": "Pano kimliği (boşsa varsayılan pano)"}

CONNECTOR = Connector(
    code="trello", title="Trello",
    description="Trello panolarındaki listeleri ve kartları okur; onayla kart açar, taşır, yorum yazar.",
    config_fields=[Field("default_board_id", "Varsayılan pano kimliği", required=False, placeholder="ör. 5f1a2b3c...",
                         help="Boşsa AI personel önce panoları listeler.")],
    secret_fields=[Field("api_key", "API anahtarı", help="trello.com/app-key adresinden alınır. Kasada şifreli saklanır."),
                   Field("token", "Token", help="Aynı sayfadaki 'Token' bağlantısıyla üretilir. Kasada şifreli saklanır.")],
    static_tools=[
        Tool("list_boards", "Hesabın açık Trello panolarını listeler.", {"type": "object", "properties": {}}, READ, _boards),
        Tool("list_lists", "Panodaki listeleri (sütunları) döner.", {"type": "object", "properties": {"board_id": _BOARD}}, READ, _lists),
        Tool("list_cards", "Panodaki veya bir listedeki açık kartları döner (en fazla 100).",
             {"type": "object", "properties": {"board_id": _BOARD, "list_id": {"type": "string"}}}, READ, _cards),
        Tool("create_card", "Listeye yeni kart açar.",
             {"type": "object", "properties": {"list_id": {"type": "string"}, "name": {"type": "string"}, "desc": {"type": "string"},
                                               "due": {"type": "string", "description": "Bitiş tarihi (ISO 8601)"}},
              "required": ["list_id", "name"]}, WRITE, _create),
        Tool("move_card", "Kartı başka listeye taşır.",
             {"type": "object", "properties": {"card_id": {"type": "string"}, "list_id": {"type": "string"}},
              "required": ["card_id", "list_id"]}, WRITE, _move),
        Tool("comment_card", "Karta yorum yazar.",
             {"type": "object", "properties": {"card_id": {"type": "string"}, "text": {"type": "string"}},
              "required": ["card_id", "text"]}, WRITE, _comment),
    ],
    test_fn=_test,
)
