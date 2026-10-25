"""
ADIM 13.1: Odoo ve RECDx uygulamaları (RECQmind, RECSlip) tercihi.

- Web satın almada isteğe bağlı tercih başvuruya ve şirkete yazılır; Odoo yoksa "kullanıyorum" seçilemez (ilgiye döner).
- Şirket yöneticisi tercihi değiştirir; ekip üyesi değiştiremez; yeni ilgi RECDx'e e-postayla bildirilir, denetim kaydına düşer.
- RECQmind/RECSlip katalog kartları yalnızca o uygulamayı kullanan ve Odoo'su olan şirkete görünür; Odoo bağlanınca durum "açık".
"""
import uuid

from app.services import notification_service as ns
from app.services import recdx_apps
from tests.test_integration_catalog import _seed as _seed_catalog
from tests.test_lifecycle import code_from_outbox, purchase_payload
from tests.test_workflow import _exec, world  # noqa: F401  (fikstür)


def test_clean_rules():
    assert recdx_apps.clean({"has_odoo": False, "apps": {"recqmind": "using", "recslip": "NO", "baska": "USING"}}) == \
        {"has_odoo": False, "apps": {"recqmind": "INTERESTED", "recslip": "NO"}}
    assert recdx_apps.clean({"has_odoo": True, "apps": {"recqmind": "USING", "recslip": "uydurma"}}) == \
        {"has_odoo": True, "apps": {"recqmind": "USING"}}
    assert recdx_apps.clean("bozuk") == {"has_odoo": None, "apps": {}}


def test_purchase_request_stores_preferences(client, db):
    pub = client.get("/api/v1/recdx-apps")
    assert pub.status_code == 200 and {a["code"] for a in pub.json()["apps"]} == {"recqmind", "recslip"}
    email = f"tercih_{uuid.uuid4().hex[:6]}@firma-test.com.tr"
    assert client.post("/api/v1/tenants/purchase-request/send-code", json={"email": email}).status_code == 200
    r = client.post("/api/v1/tenants/purchase-request", json=purchase_payload(email, code_from_outbox(email), recdx_apps={
        "has_odoo": True, "apps": {"recqmind": "USING", "recslip": "INTERESTED"}}))
    assert r.status_code == 200, r.text
    prefs = _exec(db, "SELECT preferences FROM tenant_leads WHERE id = %s", r.json()["lead_id"])[0]
    assert prefs["recdx_apps"]["apps"] == {"recqmind": "USING", "recslip": "INTERESTED"} and prefs["recdx_apps"]["has_odoo"] is True
    settings = _exec(db, "SELECT t.settings FROM tenants t JOIN tenant_leads l ON l.tenant_id = t.id WHERE l.id = %s", r.json()["lead_id"])[0]
    assert settings["recdx_apps"]["apps"]["recqmind"] == "USING"


def test_company_preference_and_catalog_visibility(client, db, world):
    w = world
    _seed_catalog(client)
    url = f"/api/v1/company/{w['tenant']}/recdx-apps"
    codes = lambda h: {e["code"] for e in client.get("/api/v1/integrations/catalog", headers=h).json()["entries"]}  # noqa: E731
    assert not {"recqmind", "recslip"} & codes(w["member"]["h"])  # tercih yokken kartlar görünmez

    d = client.get(url, headers=w["admin"]["h"]).json()
    assert {a["code"]: a["state"] for a in d["apps"]} == {"recqmind": "OFF", "recslip": "OFF"}
    assert client.put(url, headers=w["member"]["h"], json={"has_odoo": True, "apps": {"recqmind": "USING"}}).status_code == 403
    before = len(ns.OUTBOX)
    r = client.put(url, headers=w["admin"]["h"], json={"has_odoo": True, "apps": {"recqmind": "USING", "recslip": "INTERESTED"}})
    assert r.status_code == 200, r.text
    states = {a["code"]: a["state"] for a in r.json()["apps"]}
    assert states == {"recqmind": "NEEDS_ODOO", "recslip": "INTERESTED"}
    assert any("RECSlip ile ilgileniyor" in m["subject"] for m in ns.OUTBOX[before:])  # satışa bilgi
    assert "recqmind" in codes(w["member"]["h"]) and "recslip" not in codes(w["member"]["h"])
    audit = _exec(db, "SELECT count(*) FROM audit_events WHERE action = 'RECDX_APPS_UPDATED' AND tenant_id = %s", w["tenant"])[0]
    assert audit >= 1

    # Odoo bağlanınca entegrasyon açık
    client.post(f"/api/v1/company/{w['tenant']}/integrations", headers=w["admin"]["h"], json={
        "connector": "odoo", "name": f"Odoo {uuid.uuid4().hex[:4]}", "config": {"url": "https://odoo.example", "db": "x"},
        "secrets": {"api_key": "k"}})
    states = {a["code"]: a["state"] for a in client.get(url, headers=w["admin"]["h"]).json()["apps"]}
    assert states["recqmind"] == "ACTIVE"
    # Odoo yok denirse "kullanıyorum" ilgiye döner, kart gizlenir; aynı ilgi tekrar bildirilmez
    before = len(ns.OUTBOX)
    r = client.put(url, headers=w["admin"]["h"], json={"has_odoo": False, "apps": {"recqmind": "USING", "recslip": "INTERESTED"}})
    assert {a["code"]: a["choice"] for a in r.json()["apps"]}["recqmind"] == "INTERESTED"
    assert "recqmind" not in codes(w["member"]["h"])
    assert [m for m in ns.OUTBOX[before:] if "RECSlip" in m["subject"]] == []
