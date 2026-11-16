"""İSTEK #747: ek kredi satın alma — Merkez paket tanımı, sipariş (Odoo satış siparişi), havale/EFT onayıyla tek TOPUP,
iptal, süre dolunca otomatik iptal, yetkiler. Odoo sahte bağlantıyla (gerçek RECDx Odoo'suna yazılmaz)."""
import asyncio
from datetime import datetime, timedelta, timezone

import pytest

from app.services import credit_store
from app.services.odoo_service import OdooService
from tests.test_lifecycle import super_headers, tag  # noqa: F401  (fikstür)
from tests.test_workflow import _exec, world  # noqa: F401  (fikstür)


class FakeOdoo:
    def __init__(self):
        self.orders, self.confirmed, self.cancelled, self.invoiced = [], [], [], []

    def install(self, monkeypatch):
        n = {"i": 100}

        def create_sale_order(partner_id, product_id, price, description, extra_lines=None):
            n["i"] += 1
            self.orders.append((partner_id, product_id, price, description))
            return {"success": True, "order_id": n["i"], "order_name": f"S{n['i']:05d}", "partner_id": partner_id}
        monkeypatch.setattr(OdooService, "create_sale_order", staticmethod(create_sale_order))
        monkeypatch.setattr(OdooService, "get_or_create_partner", staticmethod(lambda *a, **k: {"id": 77, "name": "Test"}))
        monkeypatch.setattr(OdooService, "confirm_sale_order", staticmethod(lambda oid: self.confirmed.append(oid) or True))
        monkeypatch.setattr(OdooService, "cancel_sale_order", staticmethod(lambda oid: self.cancelled.append(oid) or True))
        monkeypatch.setattr(OdooService, "create_invoice_draft",
                            staticmethod(lambda oid: self.invoiced.append(oid) or {"success": True, "invoice_ids": [500 + oid]}))
        monkeypatch.setattr(OdooService, "list_products", staticmethod(lambda search=None, ids=None, limit=200: [{"id": 9}]))
        return self


@pytest.fixture
def odoo(monkeypatch):
    return FakeOdoo().install(monkeypatch)


def test_credit_purchase_flow(client, db, world, odoo, super_headers):  # noqa: F811
    w, admin, member = world, world["admin"]["h"], world["member"]["h"]
    sa = super_headers
    tid = w["tenant"]
    # Merkez: satışa açmak için fiyat + Odoo ürünü şart; geçerli paketler (PRO)
    packs = client.get("/api/v1/system/credit-packs", headers=sa).json()
    p5 = next(p for p in packs if p["code"] == "KREDI-5K")
    body = {"code": "KREDI-5K", "name": "5.000 Kredi", "credits": 5000, "price_try": None, "odoo_product_id": None,
            "plan_codes": [], "sort_order": 1, "is_active": True}
    assert client.put(f"/api/v1/system/credit-packs/{p5['id']}", headers=sa, json=body).status_code == 422
    body.update(price_try=2500, odoo_product_id=9, plan_codes=["PRO"])
    r = client.put(f"/api/v1/system/credit-packs/{p5['id']}", headers=sa, json=body)
    assert r.status_code == 200 and r.json()["sellable"], r.text
    assert client.get("/api/v1/system/credit-packs", headers=admin).status_code == 403  # yalnız Merkez
    client.put("/api/v1/system/billing-settings", headers=sa, json={"bank_info": "RECDx · TR00 TEST IBAN"})

    store = client.get(f"/api/v1/company/{tid}/credit-store", headers=admin).json()
    assert [p["code"] for p in store["packs"]] == ["KREDI-5K"] and store["card_enabled"] is False and "TEST IBAN" in store["bank_info"]
    assert client.post(f"/api/v1/company/{tid}/credit-orders", headers=member, json={"pack_id": p5["id"]}).status_code == 403
    assert client.post(f"/api/v1/company/{tid}/credit-orders", headers=admin,
                       json={"pack_id": p5["id"], "payment_method": "CARD"}).status_code == 409  # kart henüz kapalı
    o = client.post(f"/api/v1/company/{tid}/credit-orders", headers=admin, json={"pack_id": p5["id"]})
    assert o.status_code == 201, o.text
    o = o.json()
    assert o["status"] == "PENDING" and o["odoo_order_name"].startswith("S") and o["price_try"] == 2500
    assert odoo.orders[-1][1:3] == (9, 2500.0)  # Odoo satış siparişi kredi paketinin ürünü ve fiyatıyla

    before = client.get(f"/api/v1/company/{tid}/credits", headers=admin).json()["summary"]["balance"]
    r = client.post(f"/api/v1/system/credit-orders/{o['id']}/load", headers=sa)
    assert r.status_code == 200 and r.json()["status"] == "LOADED" and r.json()["invoice_drafted"]
    after = client.get(f"/api/v1/company/{tid}/credits", headers=admin).json()["summary"]["balance"]
    assert abs(after - before - 5000) < 0.01  # bakiye defterdeki TOPUP ile arttı
    assert client.post(f"/api/v1/system/credit-orders/{o['id']}/load", headers=sa).status_code == 409  # ikinci kez yüklenmez
    assert odoo.confirmed and odoo.invoiced
    led = _exec(db, "SELECT count(*) FROM credit_ledger WHERE tenant_id = %s AND entry_type = 'TOPUP' AND note LIKE %s", tid, f"%{o['odoo_order_name']}%")
    assert led[0] == 1

    # müşteri iptali ve süre dolması
    o2 = client.post(f"/api/v1/company/{tid}/credit-orders", headers=admin, json={"pack_id": p5["id"]}).json()
    assert client.post(f"/api/v1/company/{tid}/credit-orders/{o2['id']}/cancel", headers=admin).json()["status"] == "CANCELLED"
    o3 = client.post(f"/api/v1/company/{tid}/credit-orders", headers=admin, json={"pack_id": p5["id"]}).json()
    _exec(db, "UPDATE credit_orders SET expires_at = %s WHERE id = %s RETURNING id", datetime.now(timezone.utc) - timedelta(minutes=1), o3["id"])

    async def run():  # kendi döngüsünde ayrı bağlantı (uygulamanın havuzu başka döngüye bağlı)
        from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

        from app.config import settings
        engine = create_async_engine(settings.DATABASE_URL)
        try:
            async with async_sessionmaker(engine, expire_on_commit=False)() as s:
                return await credit_store.expire_due(s)
        finally:
            await engine.dispose()
    assert asyncio.run(run()) >= 1
    orders = {x["id"]: x for x in client.get("/api/v1/system/credit-orders", headers=sa).json()}
    assert orders[o3["id"]]["status"] == "EXPIRED" and len(odoo.cancelled) >= 2
    client.put(f"/api/v1/system/credit-packs/{p5['id']}", headers=sa, json={**body, "is_active": False})


def test_plan_upgrade_prorated(client, db, world, odoo, super_headers):  # noqa: F811
    """Paket yükseltme: yalnız üst paketler; ayın kalan günleri için oransal fark; onayda paket hemen değişir ve kredi farkı yüklenir."""
    w, admin, sa = world, world["admin"]["h"], super_headers
    tid = w["tenant"]
    old_product = _exec(db, "SELECT odoo_product_id FROM plans WHERE code = 'ENTERPRISE'")[0]
    _exec(db, "UPDATE plans SET odoo_product_id = 9 WHERE code = 'ENTERPRISE' RETURNING id")
    try:
        frac = credit_store._month_fraction()
        store = client.get(f"/api/v1/company/{tid}/credit-store", headers=admin).json()
        assert store["current_plan"]["code"] == "PRO"
        opt = next(o for o in store["upgrade_options"] if o["code"] == "ENTERPRISE")
        assert all(o["code"] != "STARTER" for o in store["upgrade_options"])  # alt paket yükseltme seçeneği değil
        expected = round((opt["monthly_price"] - float(_exec(db, "SELECT monthly_price FROM plans WHERE code = 'PRO'")[0])) * float(frac["fraction"]), 2)
        assert abs(opt["prorated_price_try"] - float(expected)) < 0.02 and opt["days_left"] == frac["days_left"]
        r = client.post(f"/api/v1/company/{tid}/plan-upgrade-orders", headers=admin, json={"plan_id": opt["plan_id"]})
        assert r.status_code == 201, r.text
        o = r.json()
        assert o["kind"] == "PLAN_UPGRADE" and o["credits"] == opt["prorated_credits"]
        assert client.post(f"/api/v1/company/{tid}/plan-upgrade-orders", headers=admin, json={"plan_id": opt["plan_id"]}).status_code == 409
        before = client.get(f"/api/v1/company/{tid}/credits", headers=admin).json()["summary"]["balance"]
        assert client.post(f"/api/v1/system/credit-orders/{o['id']}/load", headers=sa).json()["status"] == "LOADED"
        after = client.get(f"/api/v1/company/{tid}/credits", headers=admin).json()["summary"]["balance"]
        assert abs(after - before - opt["prorated_credits"]) < 0.01
        assert _exec(db, "SELECT p.code FROM tenants t JOIN plans p ON p.id = t.plan_id WHERE t.id = %s", tid)[0] == "ENTERPRISE"
    finally:
        _exec(db, "UPDATE tenants SET plan_id = (SELECT id FROM plans WHERE code = 'PRO') WHERE id = %s RETURNING id", tid)
        _exec(db, "UPDATE plans SET odoo_product_id = %s WHERE code = 'ENTERPRISE' RETURNING id", old_product)
