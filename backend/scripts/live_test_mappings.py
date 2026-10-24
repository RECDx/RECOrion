"""Canlı deneme (ADIM 12.3): RECDx hazır eşlemeleri test Odoo'sunun (Odoo.sh, recdx-recorion-test) alan tanımlarıyla doğrulanır
ve örnek nesnelerle YAZMADAN denenir (yalnızca alan tanımı okuma ve arama). Bağlantı bilgileri ortam değişkenlerinden okunur,
ekrana basılmaz. Gerçek RECDx Odoo'su ile KULLANILMAZ.
"""
import asyncio
import json
import os
import sys

sys.path.insert(0, "/app")
from app.db.models import IntegrationMapping  # noqa: E402
from app.integrations.base import Context  # noqa: E402
from app.services import business_objects as bo  # noqa: E402
from app.services import mappings as ms  # noqa: E402


async def main() -> None:
    ctx = Context({"url": os.environ["ODOO_TEST_URL"], "db": os.environ["ODOO_TEST_DB"]}, {"api_key": os.environ["ODOO_TEST_API_KEY"]})
    tgt = ms.OdooTarget(None, ctx)
    for t in json.loads(ms.SEED_FILE.read_text(encoding="utf-8")):
        m = IntegrationMapping(connector="odoo", object_type=t["object_type"], name=t["name"], target=t["target"],
                               rules=ms.clean_rules(t["rules"]), match=t.get("match"), when=t.get("when"), version=1)
        fields = await tgt.fields(m.target)
        errors, warnings = ms.check(m.object_type, m.rules, fields, "odoo", m.match)
        for r in m.rules:
            if r["transform"] == "lines":
                lf = await tgt.fields({"model": fields[r["target"]]["relation"]})
                errors += [f"Kalem: {e}" for e in ms.check(m.object_type, r["params"]["rules"], lf, "odoo", nested=True)[0]]
        sample = dict(ms.SAMPLES[m.object_type])
        if m.object_type == "ORDER" and m.when:
            sample["direction"] = m.when["equals"]
        built = await ms.build(m, sample, tgt)
        print(f"\n== {t['code']} → {m.target['model']}: denetim hata {len(errors)}, uyarı {len(warnings)}")
        for e in errors + warnings:
            print("   !", e)
        print("   değerler:", json.dumps(built.values, ensure_ascii=False, default=str)[:400])
        for e in built.errors + built.warnings:
            print("   deneme:", e)
    print("\nörnek cari VKN geçerli mi:", bo.vkn_ok(ms.SAMPLES["PARTNER"]["tax_number"]))


asyncio.run(main())
