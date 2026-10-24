"""Canlı deneme (ADIM 12.2): Odoo bağlayıcısı test Odoo'suna (Odoo.sh, recdx-recorion-test) JSON-2 ile bağlanır.

Yalnızca okuma ve alan tanımları; kayıt yazmaz. Bağlantı bilgileri ortam değişkenlerinden (ODOO_TEST_URL, ODOO_TEST_DB,
ODOO_TEST_API_KEY) okunur, ekrana basılmaz. Gerçek RECDx Odoo'su ile KULLANILMAZ.
"""
import asyncio
import os
import sys

sys.path.insert(0, "/app")
from app.integrations import get  # noqa: E402
from app.integrations.base import Context  # noqa: E402


async def main() -> None:
    cfg = {"url": os.environ["ODOO_TEST_URL"], "db": os.environ["ODOO_TEST_DB"]}
    sec = {"api_key": os.environ["ODOO_TEST_API_KEY"]}
    conn = get("odoo")
    print("deneme:", await conn.test(Context(cfg, sec)))
    tools = {t.name: t for t in await conn.tools(Context(cfg, sec))}
    ctx = Context(cfg, sec)
    print("cari sayısı:", (await tools["count_records"].run(ctx, {"model": "res.partner"}))["count"])
    d = await tools["describe_model"].run(ctx, {"model": "product.template"})
    req = [f["name"] for f in d["fields"] if f["required"]]
    print("ürün kartı yazılabilir alan:", len(d["fields"]), "· zorunlu:", ", ".join(req))
    print("birimler:", [r["display_name"] for r in (await tools["search_records"].run(ctx, {"model": "uom.uom", "limit": 30}))["records"]])


asyncio.run(main())
