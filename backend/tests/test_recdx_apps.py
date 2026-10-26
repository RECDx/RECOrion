"""
ADIM 13.1: Odoo ve RECDx uygulamaları (RECQmind, RECSlip) — tercih, paket teklifi ve satış (kullanıcı kararı 25.10.2026, karma model).

- Paket teklifi Süper Admin'de: yok / indirimli (%) / dahil + Odoo'dan seçilen ürün (ad ve liste fiyatı Odoo'dan).
- Müşteri seçimi: zaten kullanıyorum (yalnızca entegrasyon), paketime ekle (Odoo siparişine indirimli/0 fiyatlı satır),
  teklif istiyorum (Odoo CRM fırsatı), hayır. Odoo yoksa veya paketin teklifi yoksa "paketime ekle" teklife döner.
- Talepler Genel Merkez'de (Süper Admin) görünür; ürün seçilmemişse hata görünür ve ürün seçildikten sonra yeniden denenir.
- RECQmind/RECSlip katalog kartları yalnızca kullanan/ekleyen ve Odoo'su olan şirkete görünür. Gerçek Odoo çağrılmaz (sahte).
"""
import time
import uuid

import pytest

from app.config import settings
from app.services import notification_service as ns
from app.services import recdx_apps
from app.services.odoo_service import OdooService
from tests.test_integration_catalog import _seed as _seed_catalog
from tests.test_integrations import _super
from tests.test_lifecycle import code_from_outbox, purchase_payload
from tests.test_workflow import _exec, world  # noqa: F401  (fikstür)

PRODUCTS = {501: {"id": 501, "name": "RECQmind 4 RECOrion", "list_price": 1000.0}, 502: {"id": 502, "name": "RECSlip.App 4 RECOrion", "list_price": 0.0}}


@pytest.fixture
def fake_odoo(monkeypatch):
    log = {"orders": [], "quotes": [], "crm": []}
    monkeypatch.setattr(settings, "ODOO_SYNC_ENABLED", True)
    monkeypatch.setattr(OdooService, "list_products", classmethod(lambda cls, search=None, ids=None, limit=200: [PRODUCTS[i] for i in (ids or []) if i in PRODUCTS]))
    monkeypatch.setattr(OdooService, "get_or_create_partner", classmethod(lambda cls, *a, **k: {"id": 77, "name": "Deneme"}))

    def order(cls, partner_id, product_id, price, description, extra_lines=None):
        log["orders"].append({"partner": partner_id, "lines": extra_lines or []})
        return {"success": True, "order_id": 900 + len(log["orders"]), "order_name": f"S{900 + len(log['orders'])}"}

    def quote(cls, partner_id, lines, note):
        log["quotes"].append({"partner": partner_id, "lines": [{k: v for k, v in ln.items() if k != "request"} for ln in lines]})
        return {"success": True, "order_id": 950, "order_name": "S950"}

    def crm(cls, partner_id, name, description, revenue, email, phone):
        log["crm"].append({"partner": partner_id, "name": name, "revenue": revenue})
        return {"success": True, "lead_id": 4200 + len(log["crm"])}
    monkeypatch.setattr(OdooService, "create_sale_order", classmethod(order))
    monkeypatch.setattr(OdooService, "create_quotation", classmethod(quote))
    monkeypatch.setattr(OdooService, "create_crm_lead", classmethod(crm))
    return log


def _plan(db, code):
    return _exec(db, "SELECT id FROM plans WHERE code = %s", code)[0]


def test_offer_and_choice_rules():
    from app.db.models import Plan

    pro = Plan(recdx_apps={"recqmind": {"mode": "DISCOUNT", "discount": 50, "list_price": 1000}, "recslip": {"mode": "INCLUDED", "list_price": 300}})
    assert recdx_apps.offer(pro, "recqmind")["price"] == 500.0 and recdx_apps.offer(pro, "recslip")["price"] == 0.0
    starter = Plan(recdx_apps={})
    assert recdx_apps.offer(starter, "recqmind") == {"mode": "NONE", "price": None, "available": False}
    assert recdx_apps.clean({"has_odoo": True, "apps": {"recqmind": "ADD", "recslip": "add"}}, starter)["apps"] == {"recqmind": "QUOTE", "recslip": "QUOTE"}
    assert recdx_apps.clean({"has_odoo": False, "apps": {"recqmind": "USING", "recslip": "ADD"}}, pro)["apps"] == {"recqmind": "QUOTE", "recslip": "QUOTE"}
    assert recdx_apps.clean({"has_odoo": True, "apps": {"recqmind": "interested", "recslip": "uydurma"}}, pro)["apps"] == {"recqmind": "QUOTE"}
    with pytest.raises(ValueError, match="indirim"):
        recdx_apps.clean_offer({"recqmind": {"mode": "DISCOUNT", "discount": 120}})
    with pytest.raises(ValueError, match="teklif türü"):
        recdx_apps.clean_offer({"recqmind": {"mode": "BEDAVA"}})


def test_describe_sorts_new_and_stored_requests():
    """Kayıt yeni eklenmiş talep (bellekte saat dilimsiz) ile veritabanından gelen talebi birlikte sıralar (13.4'te bulunan 500)."""
    from datetime import datetime, timedelta, timezone

    from app.db.models import RecdxAppRequest

    old = RecdxAppRequest(id=uuid.uuid4(), tenant_id=uuid.uuid4(), app="recslip", choice="QUOTE", status="NEW",
                          created_at=datetime.now(timezone.utc) - timedelta(days=1))
    new = RecdxAppRequest(id=uuid.uuid4(), tenant_id=old.tenant_id, app="recslip", choice="USING", status="NEW", created_at=datetime.utcnow())
    apps = {a["code"]: a for a in recdx_apps.describe(requests=[new, old])["apps"]}
    assert apps["recslip"]["request"]["choice"] == "USING"


def test_plan_offer_editable_by_super_admin(client, db, fake_odoo):
    sa = _super(client, db)
    pid = _plan(db, "STARTER")
    plan = client.get(f"/api/v1/tenants/plans/{pid}", headers=sa).json()
    body = {k: plan[k] for k in ("name", "description", "monthly_price", "currency", "max_humans", "max_agents", "max_projects",
                                 "monthly_credits", "storage_gb", "allowed_models", "features", "odoo_product_id", "is_active")}
    r = client.put(f"/api/v1/tenants/plans/{pid}", headers=sa, json={**body, "recdx_apps": {
        "recqmind": {"mode": "DISCOUNT", "discount": 25, "odoo_product_id": 501, "list_price": 1}, "recslip": {"mode": "NONE"}}})
    assert r.status_code == 200, r.text
    assert r.json()["recdx_apps"]["recqmind"] == {"mode": "DISCOUNT", "discount": 25.0, "odoo_product_id": 501,
                                                  "odoo_product_name": "RECQmind 4 RECOrion", "list_price": 1000.0}  # fiyat Odoo'dan
    r = client.put(f"/api/v1/tenants/plans/{pid}", headers=sa, json={**body, "recdx_apps": {"recqmind": {"mode": "DISCOUNT", "odoo_product_id": 999}}})
    assert r.status_code == 422
    r = client.put(f"/api/v1/tenants/plans/{pid}", headers=sa, json={**body, "recdx_apps": {"recqmind": {"mode": "INCLUDED", "odoo_product_id": 999}}})
    assert r.status_code == 400  # Odoo'da yok
    client.put(f"/api/v1/tenants/plans/{pid}", headers=sa, json={**body, "recdx_apps": {}})  # STARTER eski haline


def test_purchase_adds_order_lines_and_crm(client, db, fake_odoo):
    from app.services import customer_lifecycle

    _exec(db, """UPDATE plans SET recdx_apps = '{"recqmind": {"mode": "DISCOUNT", "discount": 50, "odoo_product_id": 501, "list_price": 1000},
                                                 "recslip": {"mode": "INCLUDED"}}'::jsonb WHERE code = 'STARTER'""")
    try:
        pub = client.get("/api/v1/recdx-apps?plan_code=STARTER").json()
        offers = {a["code"]: a["offer"] for a in pub["apps"]}
        assert offers["recqmind"]["price"] == 500.0 and offers["recslip"]["mode"] == "INCLUDED"
        email = f"tercih_{uuid.uuid4().hex[:6]}@firma-test.com.tr"
        client.post("/api/v1/tenants/purchase-request/send-code", json={"email": email})
        r = client.post("/api/v1/tenants/purchase-request", json=purchase_payload(email, code_from_outbox(email), recdx_apps={
            "has_odoo": True, "apps": {"recqmind": "ADD", "recslip": "ADD"}}))
        assert r.status_code == 200, r.text
        lead_id = r.json()["lead_id"]
        client.portal.call(customer_lifecycle.sync_lead_to_odoo, uuid.UUID(lead_id))
        line = fake_odoo["orders"][-1]["lines"]
        assert line == [{"product_id": 501, "price": 500.0, "name": "RECQmind 4 RECOrion (%50 indirimli)"}]  # RECSlip ürünü seçilmemiş
        reqs = {r[0]: r[1:] for r in _exec_all(db, "SELECT app, status, odoo_order_name, error FROM recdx_app_requests WHERE lead_id = %s", lead_id)}
        assert reqs["recqmind"][0] == "ORDERED" and reqs["recqmind"][1].startswith("S9")
        assert reqs["recslip"][0] == "FAILED" and "ürünü seçilmemiş" in reqs["recslip"][2]
        tenant_settings = _exec(db, "SELECT t.settings FROM tenants t JOIN tenant_leads l ON l.tenant_id = t.id WHERE l.id = %s", lead_id)[0]
        assert tenant_settings["recdx_apps"]["apps"] == {"recqmind": "ADD", "recslip": "ADD"}

        # Genel Merkez: talepler görünür; ürün sonradan seçilince yeniden denenir (0 fiyatla ek teklif)
        sa = _super(client, db)
        rows = client.get("/api/v1/system/recdx-app-requests", headers=sa).json()
        failed = next(x for x in rows if x["app"] == "recslip" and x["status"] == "FAILED" and x["tenant_name"].startswith("Deneme Ltd"))
        _exec(db, """UPDATE plans SET recdx_apps = jsonb_set(recdx_apps, '{recslip}', '{"mode": "INCLUDED", "odoo_product_id": 502, "list_price": 0}')
                     WHERE code = 'STARTER'""")
        again = client.post(f"/api/v1/system/recdx-app-requests/{failed['id']}/retry", headers=sa).json()
        assert again["status"] == "ORDERED" and fake_odoo["quotes"][-1]["lines"] == [{"product_id": 502, "price": 0.0, "name": "RECSlip 4 RECOrion (dahil)"}]
        done = client.put(f"/api/v1/system/recdx-app-requests/{failed['id']}", headers=sa, json={"status": "DONE", "note": "Odoo.sh'a kuruldu"}).json()
        assert done["status"] == "DONE" and done["note"] == "Odoo.sh'a kuruldu"
    finally:
        _exec(db, "UPDATE plans SET recdx_apps = '{}'::jsonb WHERE code = 'STARTER'")


def _exec_all(db, sql, *params):
    with db.cursor() as cur:
        cur.execute(sql, params)
        return cur.fetchall()


def test_company_preference_requests_and_catalog(client, db, world, fake_odoo):
    w = world
    _seed_catalog(client)
    url = f"/api/v1/company/{w['tenant']}/recdx-apps"
    codes = lambda h: {e["code"] for e in client.get("/api/v1/integrations/catalog", headers=h).json()["entries"]}  # noqa: E731
    assert not {"recqmind", "recslip"} & codes(w["member"]["h"])
    assert {a["code"]: a["state"] for a in client.get(url, headers=w["admin"]["h"]).json()["apps"]} == {"recqmind": "OFF", "recslip": "OFF"}
    assert client.put(url, headers=w["member"]["h"], json={"has_odoo": True, "apps": {"recqmind": "USING"}}).status_code == 403
    assert client.get("/api/v1/system/recdx-app-requests", headers=w["admin"]["h"]).status_code == 403

    before = len(ns.OUTBOX)
    r = client.put(url, headers=w["admin"]["h"], json={"has_odoo": True, "apps": {"recqmind": "USING", "recslip": "QUOTE"}})
    assert r.status_code == 200, r.text
    d = {a["code"]: a for a in r.json()["apps"]}
    assert d["recqmind"]["state"] == "NEEDS_ODOO" and d["recqmind"]["request"]["status"] == "IN_USE"  # yalnızca entegrasyon
    assert d["recslip"]["state"] == "QUOTE"
    assert any("RECSlip (teklif istiyorum)" in m["subject"] for m in ns.OUTBOX[before:])
    end = time.time() + 10
    while time.time() < end and not fake_odoo["crm"]:
        time.sleep(0.2)
    assert fake_odoo["crm"] and fake_odoo["crm"][-1]["name"].startswith("RECSlip 4 RECOrion - ")
    assert "recqmind" in codes(w["member"]["h"]) and "recslip" not in codes(w["member"]["h"])

    # Aynı seçim tekrar gönderilince yeni talep/fırsat açılmaz
    n = len(fake_odoo["crm"])
    client.put(url, headers=w["admin"]["h"], json={"has_odoo": True, "apps": {"recqmind": "USING", "recslip": "QUOTE"}})
    time.sleep(1)
    assert len(fake_odoo["crm"]) == n

    client.post(f"/api/v1/company/{w['tenant']}/integrations", headers=w["admin"]["h"], json={
        "connector": "odoo", "name": f"Odoo {uuid.uuid4().hex[:4]}", "config": {"url": "https://odoo.example", "db": "x"}, "secrets": {"api_key": "k"}})
    assert {a["code"]: a["state"] for a in client.get(url, headers=w["admin"]["h"]).json()["apps"]}["recqmind"] == "ACTIVE"
    rows = client.get("/api/v1/system/recdx-app-requests", headers=_super(client, db)).json()
    mine = [x for x in rows if x["tenant_id"] == w["tenant"]]
    assert {(x["app"], x["choice"], x["status"]) for x in mine} >= {("recqmind", "USING", "IN_USE"), ("recslip", "QUOTE", "OPPORTUNITY")}
    assert _exec(db, "SELECT count(*) FROM audit_events WHERE action = 'RECDX_APPS_UPDATED' AND tenant_id = %s", w["tenant"])[0] >= 2
