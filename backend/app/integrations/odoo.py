"""Odoo bağlayıcısı (ADIM 10.3): JSON-RPC (/jsonrpc) ile kayıt arama/sayma (okuma), oluşturma/güncelleme (yazma = insan onayı).

Erişim Odoo'daki kullanıcının kendi yetkileriyle sınırlıdır; ek olarak bağlantıda izinli modeller listesi verilebilir.
Silme aracı bilerek yoktur. Kimlik bilgisi (parola / API anahtarı) kasada şifreli saklanır, hata mesajlarına yazılmaz.
"""
from typing import Any, Dict, List

import httpx

from app.integrations.base import READ, WRITE, Connector, Context, Field, Tool, ToolError, guard_url, http_client, require

MAX_LIMIT = 100


def _url(ctx: Context) -> str:
    url = (ctx.config.get("url") or "").strip().rstrip("/")
    if not url.startswith(("https://", "http://")):
        raise ToolError("Odoo adresi http(s):// ile başlamalı.")
    return url


async def _rpc(ctx: Context, service: str, method: str, *args) -> Any:
    body = {"jsonrpc": "2.0", "method": "call", "params": {"service": service, "method": method, "args": list(args)}, "id": 1}
    url = await guard_url(_url(ctx))
    try:
        async with http_client(timeout=20) as c:
            r = await c.post(f"{url}/jsonrpc", json=body)
    except httpx.HTTPError as exc:
        raise ToolError(f"Odoo'ya ulaşılamadı ({exc.__class__.__name__}).")
    if r.status_code != 200:
        raise ToolError(f"Odoo HTTP {r.status_code} döndürdü.")
    data = r.json()
    if data.get("error"):
        err = data["error"].get("data") or {}
        # Odoo hata mesajı kullanıcıya gösterilebilir; iz (traceback) gösterilmez
        raise ToolError(f"Odoo: {(err.get('message') or data['error'].get('message') or 'hata')[:300]}")
    return data.get("result")


async def _uid(ctx: Context) -> int:
    uid = await _rpc(ctx, "common", "login", ctx.config.get("db"), ctx.config.get("username"), ctx.secrets.get("api_key"))
    if not uid:
        raise ToolError("Odoo girişi reddedildi (veritabanı, kullanıcı veya API anahtarı hatalı).")
    return uid


def _allowed(ctx: Context) -> List[str]:
    return [m.strip() for m in (ctx.config.get("allowed_models") or "").split(",") if m.strip()]


def _model(ctx: Context, args: Dict[str, Any]) -> str:
    require(args, "model")
    model = str(args["model"]).strip()
    allowed = _allowed(ctx)
    if allowed and model not in allowed:
        raise ToolError(f"'{model}' modeli bu bağlantıda izinli değil. İzinli: {', '.join(allowed)}")
    return model


async def _kw(ctx: Context, model: str, method: str, args: list, kw: Dict[str, Any] = None) -> Any:
    uid = await _uid(ctx)
    return await _rpc(ctx, "object", "execute_kw", ctx.config.get("db"), uid, ctx.secrets.get("api_key"), model, method, args, kw or {})


def _domain(args: Dict[str, Any]) -> list:
    d = args.get("domain") or []
    if not isinstance(d, list):
        raise ToolError("domain bir liste olmalı, ör. [[\"state\", \"=\", \"sale\"]]")
    return d


async def _search(ctx: Context, args: Dict[str, Any]):
    model = _model(ctx, args)
    limit = max(1, min(int(args.get("limit") or 20), MAX_LIMIT))
    kw = {"fields": args.get("fields") or ["display_name"], "limit": limit}
    if args.get("order"):
        kw["order"] = str(args["order"])
    rows = await _kw(ctx, model, "search_read", [_domain(args)], kw)
    return {"model": model, "count": len(rows), "records": rows}


async def _count(ctx: Context, args: Dict[str, Any]):
    model = _model(ctx, args)
    return {"model": model, "count": await _kw(ctx, model, "search_count", [_domain(args)])}


async def _find_models(ctx: Context, args: Dict[str, Any]):
    q = str(args.get("keyword") or "").strip()
    domain = ["|", ["model", "ilike", q], ["name", "ilike", q]] if q else []
    allowed = _allowed(ctx)
    if allowed:  # Odoo önek gösterimi: & A (| B C)
        domain = ["&", ["model", "in", allowed], *domain] if domain else [["model", "in", allowed]]
    rows = await _kw(ctx, "ir.model", "search_read", [domain], {"fields": ["model", "name"], "limit": 30})
    return [{"model": r["model"], "name": r["name"]} for r in rows]


async def _create(ctx: Context, args: Dict[str, Any]):
    model = _model(ctx, args)
    if not isinstance(args.get("values"), dict) or not args["values"]:
        raise ToolError("values alan-değer nesnesi olmalı.")
    rid = await _kw(ctx, model, "create", [args["values"]])
    return {"model": model, "id": rid[0] if isinstance(rid, list) else rid}


async def _update(ctx: Context, args: Dict[str, Any]):
    model = _model(ctx, args)
    ids = args.get("ids")
    if not isinstance(ids, list) or not ids or not all(isinstance(i, int) for i in ids):
        raise ToolError("ids tam sayı listesi olmalı.")
    if len(ids) > 50:
        raise ToolError("Tek seferde en fazla 50 kayıt güncellenebilir.")
    if not isinstance(args.get("values"), dict) or not args["values"]:
        raise ToolError("values alan-değer nesnesi olmalı.")
    await _kw(ctx, model, "write", [ids, args["values"]])
    return {"model": model, "updated": ids}


async def _test(ctx: Context) -> str:
    version = await _rpc(ctx, "common", "version")
    uid = await _uid(ctx)
    return f"Odoo {(version or {}).get('server_version', '?')} · kullanıcı #{uid} ile bağlanıldı"


_MODEL = {"type": "string", "description": "Odoo modeli, ör. res.partner, sale.order, project.task"}
_DOMAIN = {"type": "array", "description": "Odoo arama filtresi, ör. [[\"is_company\", \"=\", true]]", "items": {}}
_VALUES = {"type": "object", "description": "Alan-değer çiftleri"}

CONNECTOR = Connector(
    code="odoo", title="Odoo",
    description="Şirketin Odoo ERP'sinde kayıt arar ve sayar; onayla kayıt oluşturur veya günceller (silme yok).",
    config_fields=[
        Field("url", "Odoo adresi", placeholder="https://sirket.odoo.com"),
        Field("db", "Veritabanı adı", placeholder="sirket"),
        Field("username", "Kullanıcı (e-posta)", placeholder="entegrasyon@sirket.com",
              help="AI personel bu kullanıcının Odoo yetkileriyle çalışır; ayrı, kısıtlı bir entegrasyon kullanıcısı önerilir."),
        Field("allowed_models", "İzinli modeller", required=False, placeholder="res.partner, sale.order, project.task",
              help="Virgülle ayırın. Boşsa kullanıcının Odoo'da erişebildiği tüm modeller."),
    ],
    secret_fields=[Field("api_key", "API anahtarı veya parola", help="Odoo > Tercihler > Hesap Güvenliği > API Anahtarları. Kasada şifreli saklanır.")],
    static_tools=[
        Tool("find_models", "Odoo'da adı veya teknik adı anahtar kelimeyle eşleşen modelleri listeler.",
             {"type": "object", "properties": {"keyword": {"type": "string", "description": "ör. sipariş, partner, task"}}}, READ, _find_models),
        Tool("search_records", "Odoo modelinde kayıt arar (en fazla 100).",
             {"type": "object", "properties": {"model": _MODEL, "domain": _DOMAIN,
                                               "fields": {"type": "array", "items": {"type": "string"}, "description": "Dönecek alanlar"},
                                               "limit": {"type": "integer", "description": "En fazla 100 (varsayılan 20)"},
                                               "order": {"type": "string", "description": "ör. create_date desc"}},
              "required": ["model"]}, READ, _search),
        Tool("count_records", "Odoo modelinde filtreye uyan kayıt sayısını döner.",
             {"type": "object", "properties": {"model": _MODEL, "domain": _DOMAIN}, "required": ["model"]}, READ, _count),
        Tool("create_record", "Odoo modelinde yeni kayıt oluşturur.",
             {"type": "object", "properties": {"model": _MODEL, "values": _VALUES}, "required": ["model", "values"]}, WRITE, _create),
        Tool("update_record", "Odoo kayıtlarını günceller (en fazla 50).",
             {"type": "object", "properties": {"model": _MODEL, "ids": {"type": "array", "items": {"type": "integer"}}, "values": _VALUES},
              "required": ["model", "ids", "values"]}, WRITE, _update),
    ],
    test_fn=_test,
)
