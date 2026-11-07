"""
Senaryolu canlı test (ADIM 17, ORN Soft) Aşama 1 düzeltmeleri.

- #636/#654 (F22/F41): paket API'si "şirkete özel ünvan" iznini döndürür; PRO ve Kurumsal'da açık, Başlangıç'ta kapalı.
  Merkez bir şirkete paketten bağımsız istisna verir (ON/OFF), "Paket ayarı"na (PLAN) dönerek geri alır; yalnız süper admin.
- #635 (F21): şirket kullanıcı eklediğinde kişiye şifre belirleme bağlantılı davet e-postası gider.
- #633 (F19): satın almada şirket e-postası yönetici e-postasıyla ezilmez.
"""
from app.services import notification_service as ns
from tests.test_lifecycle import (PASSWORD, _exec, code_from_outbox, outbox_for, purchase_payload, starter_company,  # noqa: F401
                                  super_headers, tag)


def test_plan_api_returns_custom_title_flag(client, super_headers):  # noqa: F811
    plans = {p["code"]: p for p in client.get("/api/v1/tenants/plans").json()}
    assert plans["PRO"]["can_create_custom_titles"] is True and plans["ENTERPRISE"]["can_create_custom_titles"] is True
    assert plans["STARTER"]["can_create_custom_titles"] is False


def test_central_override_for_one_company_is_optional_and_reversible(client, starter_company, super_headers):  # noqa: F811
    tid, h = starter_company["tenant_id"], starter_company["headers"]
    ent = lambda: client.get(f"/api/v1/company/{tid}/entitlements", headers=h).json()["can_create_custom_titles"]  # noqa: E731
    new_title = lambda n: client.post(f"/api/v1/company/{tid}/job-titles", headers=h,  # noqa: E731
                                      json={"title": f"Özel Ünvan {n}", "category": "GENEL", "base_role_prompt": "x"})
    url = f"/api/v1/tenants/{tid}/custom-titles"
    assert ent() is False and new_title(1).status_code == 403  # Başlangıç paketi: kapalı
    assert client.put(url, headers=h, json={"mode": "ON"}).status_code == 403  # müşteri kendine istisna veremez
    r = client.put(url, headers=super_headers, json={"mode": "ON"})
    assert r.status_code == 200 and r.json()["effective"] is True
    assert ent() is True and new_title(2).status_code in (200, 201)
    assert client.get(f"/api/v1/tenants/{tid}/details", headers=super_headers).json()["tenant"]["custom_titles_override"] is True
    assert client.put(url, headers=super_headers, json={"mode": "PLAN"}).json()["effective"] is False  # geri alındı
    assert ent() is False and new_title(3).status_code == 403
    assert client.put(url, headers=super_headers, json={"mode": "BASKA"}).status_code == 422


def test_new_user_gets_invitation_email(client, starter_company, tag):  # noqa: F811
    tid, h = starter_company["tenant_id"], starter_company["headers"]
    email = f"yeni_{tag}@deneme-sirket.com.tr"
    r = client.post(f"/api/v1/company/{tid}/users", headers=h, json={"display_name": "Yeni Kişi", "email": email, "password": PASSWORD})
    assert r.status_code in (200, 201), r.text
    mail = outbox_for(email, "hesabınız oluşturuldu")
    assert mail and "reset-password?token=" in mail[-1]["html"] and email in mail[-1]["html"]
    assert len([m for m in ns.OUTBOX if m["to"] == email]) == 1


def test_purchase_keeps_company_email_separate(client, db, tag):  # noqa: F811
    email = f"yonetici_{tag}@deneme-sirket.com.tr"
    assert client.post("/api/v1/tenants/purchase-request/send-code", json={"email": email}).status_code == 200
    r = client.post("/api/v1/tenants/purchase-request", json=purchase_payload(
        email, code_from_outbox(email), company_email=f"info_{tag}@deneme-sirket.com.tr"))
    assert r.status_code == 200, r.text
    tenant_email, admin_email = _exec(db, "SELECT t.contact_email, a.email FROM tenant_leads l JOIN tenants t ON t.id = l.tenant_id "
                                          "JOIN actors a ON a.tenant_id = t.id AND a.role = 'COMPANY_ADMIN' WHERE l.id = %s", r.json()["lead_id"])
    assert tenant_email == f"info_{tag}@deneme-sirket.com.tr" and admin_email == email
