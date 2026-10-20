"""
Adım 3: Web satın alma ve müşteri yaşam döngüsü testleri.
E-postalar EMAIL_DELIVERY=log ile OUTBOX'a yazılır; Odoo çağrılmaz.
"""
import re
import uuid
from datetime import datetime, timedelta, timezone

import pytest

from app.core.security import hash_password
from app.services import notification_service as ns

PASSWORD = "Web-Kayit-Sifresi-2026"


def outbox_for(email, subject_part=None):
    mails = [m for m in ns.OUTBOX if m["to"] == email]
    if subject_part:
        mails = [m for m in mails if subject_part.lower() in m["subject"].lower()]
    return mails


def code_from_outbox(email):
    mail = outbox_for(email, "doğrulama kodunuz")[-1]
    return re.search(r"kodunuz: (\d{6})", mail["subject"]).group(1)


def token_from_mail(mail):
    return re.search(r"reset-password\?token=([A-Za-z0-9_\-]+)", mail["html"]).group(1)


def _exec(db, sql, *params):
    with db.cursor() as cur:
        cur.execute(sql, params)
        return cur.fetchone() if cur.description else None


@pytest.fixture(scope="module")
def tag():
    return uuid.uuid4().hex[:8]


@pytest.fixture(scope="module")
def super_headers(client, db, tag):
    hq = _exec(db, "SELECT id FROM tenants WHERE slug = 'recdx_hq'")[0]
    email = f"lc_super_{tag}@recdx.com"
    _exec(db, "INSERT INTO actors (tenant_id, actor_type, display_name, email, role, password_hash, status) "
              "VALUES (%s, 'HUMAN', 'LC Super', %s, 'SUPER_ADMIN', %s, 'IDLE') RETURNING id", hq, email, hash_password(PASSWORD))
    r = client.post("/api/v1/auth/login", json={"email": email, "password": PASSWORD})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def purchase_payload(email, code, **extra):
    return {
        "plan_code": "STARTER", "company_name": f"Deneme Ltd {email[:6]}", "phone": "+90 212 000 00 00",
        "contact_name": "Ayşe Yılmaz", "contact_email": email, "password": PASSWORD, "email_code": code,
        "sectors": ["C"], "professions": ["C.01"], **extra,
    }


def register(client, email):
    assert client.post("/api/v1/tenants/purchase-request/send-code", json={"email": email}).status_code == 200
    r = client.post("/api/v1/tenants/purchase-request", json=purchase_payload(email, code_from_outbox(email)))
    assert r.status_code == 200, r.text
    return r.json()["lead_id"]


# ---------------------------------------------------------------------------
# Web başvurusu
# ---------------------------------------------------------------------------
def test_send_code_rejects_public_email(client):
    assert client.post("/api/v1/tenants/purchase-request/send-code", json={"email": "biri@gmail.com"}).status_code == 400


def test_send_code_is_rate_limited_per_email(client, tag):
    email = f"limit_{tag}@deneme-sirket.com.tr"
    assert client.post("/api/v1/tenants/purchase-request/send-code", json={"email": email}).status_code == 200
    assert client.post("/api/v1/tenants/purchase-request/send-code", json={"email": email}).status_code == 429


def test_purchase_requires_valid_code(client, tag):
    email = f"kod_{tag}@deneme-sirket.com.tr"
    client.post("/api/v1/tenants/purchase-request/send-code", json={"email": email})
    r = client.post("/api/v1/tenants/purchase-request", json=purchase_payload(email, "000000"))
    assert r.status_code == 400 and "doğrulama kodu" in r.json()["detail"].lower()


def test_purchase_honeypot_blocks_bots(client, tag):
    email = f"bot_{tag}@deneme-sirket.com.tr"
    client.post("/api/v1/tenants/purchase-request/send-code", json={"email": email})
    r = client.post("/api/v1/tenants/purchase-request", json=purchase_payload(email, code_from_outbox(email), company_fax="spam"))
    assert r.status_code == 400


def test_purchase_creates_linked_pending_records(client, db, super_headers, tag):
    email = f"basvuru_{tag}@deneme-sirket.com.tr"
    lead_id = register(client, email)

    tenant_id, status, odoo = _exec(db, "SELECT tenant_id, status, odoo_sync_status FROM tenant_leads WHERE id = %s", lead_id)
    assert status == "PENDING" and odoo == "SKIPPED"
    assert _exec(db, "SELECT is_active FROM tenants WHERE id = %s", tenant_id)[0] is False
    assert _exec(db, "SELECT count(*) FROM actors WHERE tenant_id = %s AND role = 'COMPANY_ADMIN'", tenant_id)[0] == 1

    # Kod tek kullanımlık
    r = client.post("/api/v1/tenants/purchase-request", json=purchase_payload(f"x{email}", code_from_outbox(email)))
    assert r.status_code == 400

    # Müşteriye ve RECDx'e bildirim gitti
    assert outbox_for(email, "başvurunuz alındı")
    # Onay beklerken giriş yapılamaz
    login = client.post("/api/v1/auth/login", json={"email": email, "password": PASSWORD})
    assert login.status_code == 403

    # Başvuru listesi şifre bilgisi döndürmez
    leads = client.get("/api/v1/tenants/leads", headers=super_headers).json()
    mine = next(l for l in leads if l["id"] == lead_id)
    assert "password_hash" not in mine and "notes" not in mine


def test_approve_activates_and_sends_mail_without_password(client, db, super_headers, tag):
    email = f"onay_{tag}@deneme-sirket.com.tr"
    lead_id = register(client, email)
    r = client.post(f"/api/v1/tenants/leads/{lead_id}/approve", headers=super_headers)
    assert r.status_code == 200 and r.json()["activation_email_sent"] is True

    tenant_id = _exec(db, "SELECT tenant_id FROM tenant_leads WHERE id = %s", lead_id)[0]
    active, expiry = _exec(db, "SELECT is_active, package_expiry_date FROM tenants WHERE id = %s", tenant_id)
    assert active is True and expiry > datetime.now(timezone.utc) + timedelta(days=360)
    assert _exec(db, "SELECT password_hash FROM tenant_leads WHERE id = %s", lead_id)[0] is None

    mail = outbox_for(email, "hesabınız aktif")[-1]
    assert PASSWORD not in mail["html"] and PASSWORD not in mail["text"]
    assert "reset-password?token=" in mail["html"]

    assert client.post("/api/v1/auth/login", json={"email": email, "password": PASSWORD}).status_code == 200


def test_reject_lead(client, super_headers, tag):
    email = f"ret_{tag}@deneme-sirket.com.tr"
    lead_id = register(client, email)
    assert client.post(f"/api/v1/tenants/leads/{lead_id}/reject", headers=super_headers, json={"reason": "x"}).status_code == 400
    r = client.post(f"/api/v1/tenants/leads/{lead_id}/reject", headers=super_headers,
                    json={"reason": "Vergi bilgileri doğrulanamadı."})
    assert r.status_code == 200
    assert "Vergi bilgileri doğrulanamadı." in outbox_for(email, "başvurunuz hakkında")[-1]["html"]
    login = client.post("/api/v1/auth/login", json={"email": email, "password": PASSWORD})
    assert login.status_code == 403


# ---------------------------------------------------------------------------
# Şifre belirleme / sıfırlama
# ---------------------------------------------------------------------------
def test_password_reset_flow(client, super_headers, tag):
    email = f"sifre_{tag}@deneme-sirket.com.tr"
    lead_id = register(client, email)
    client.post(f"/api/v1/tenants/leads/{lead_id}/approve", headers=super_headers)

    r = client.post("/api/v1/auth/password-reset/request", json={"email": email})
    assert r.status_code == 200
    token = token_from_mail(outbox_for(email, "şifre belirleme")[-1])

    assert client.post("/api/v1/auth/password-reset/confirm", json={"token": token, "new_password": "kisa"}).status_code == 400
    new_password = "Yeni-Guclu-Sifre-2026"
    assert client.post("/api/v1/auth/password-reset/confirm", json={"token": token, "new_password": new_password}).status_code == 200
    assert client.post("/api/v1/auth/password-reset/confirm", json={"token": token, "new_password": new_password}).status_code == 400  # tek kullanımlık
    assert client.post("/api/v1/auth/login", json={"email": email, "password": new_password}).status_code == 200


def test_password_reset_does_not_reveal_accounts(client):
    before = len(ns.OUTBOX)
    r = client.post("/api/v1/auth/password-reset/request", json={"email": "olmayan-hesap@deneme-sirket.com.tr"})
    assert r.status_code == 200 and len(ns.OUTBOX) == before


def test_admin_create_without_password_uses_set_password_link(client, db, super_headers, tag):
    email = f"admin_{tag}@deneme-sirket.com.tr"
    plan_id = _exec(db, "SELECT id FROM plans WHERE code = 'PRO'")[0]
    r = client.post("/api/v1/tenants/admin-create", headers=super_headers, json={
        "name": f"Manuel Kurum {tag}", "contact_email": email, "plan_id": str(plan_id),
        "admin_name": "Mehmet Demir", "activate_package": True, "send_welcome_email": True,
    })
    assert r.status_code == 200, r.text
    assert "admin_password" not in r.json()
    assert _exec(db, "SELECT password_hash FROM actors WHERE email = %s", email)[0] is None

    token = token_from_mail(outbox_for(email, "hesabınız aktif")[-1])
    assert client.post("/api/v1/auth/password-reset/confirm", json={"token": token, "new_password": PASSWORD}).status_code == 200
    assert client.post("/api/v1/auth/login", json={"email": email, "password": PASSWORD}).status_code == 200


# ---------------------------------------------------------------------------
# Paket hakları (#241)
# ---------------------------------------------------------------------------
@pytest.fixture(scope="module")
def starter_company(client, db, super_headers, tag):
    email = f"paket_{tag}@deneme-sirket.com.tr"
    lead_id = register(client, email)
    client.post(f"/api/v1/tenants/leads/{lead_id}/approve", headers=super_headers)
    tenant_id = _exec(db, "SELECT tenant_id FROM tenant_leads WHERE id = %s", lead_id)[0]
    title_id = _exec(db, "INSERT INTO job_titles (tenant_id, code, title, category, base_role_prompt, recommended_model_code) "
                         "VALUES (NULL, %s, 'Test Analisti', 'GENEL', 'Sen bir analistsin.', 'gemma-4-31b') RETURNING id",
                     f"TEST_ANALIST_{tag}")[0]
    token = client.post("/api/v1/auth/login", json={"email": email, "password": PASSWORD}).json()["access_token"]
    return {"tenant_id": tenant_id, "title_id": title_id, "headers": {"Authorization": f"Bearer {token}"}}


def test_entitlements_endpoint(client, starter_company):
    r = client.get(f"/api/v1/company/{starter_company['tenant_id']}/entitlements", headers=starter_company["headers"])
    assert r.status_code == 200
    e = r.json()
    assert e["plan_code"] == "STARTER" and e["can_change_llm"] is False and e["can_create_custom_titles"] is False


def test_starter_cannot_change_llm_or_prompt(client, starter_company):
    url = f"/api/v1/company/{starter_company['tenant_id']}/ai-agents"
    base = {"display_name": "Ajan", "job_title_id": str(starter_company["title_id"])}
    h = starter_company["headers"]
    assert client.post(url, headers=h, json={**base, "model_code": "deepseek-v4-flash"}).status_code == 403
    assert client.post(url, headers=h, json={**base, "model_code": "gemma-4-31b", "system_prompt": "Başka bir prompt"}).status_code == 403
    ok = client.post(url, headers=h, json={**base, "model_code": "gemma-4-31b"})
    assert ok.status_code == 201, ok.text
    assert ok.json()["model_code"] == "gemma-4-31b"


def test_starter_cannot_create_custom_titles(client, starter_company):
    r = client.post(f"/api/v1/company/{starter_company['tenant_id']}/job-titles", headers=starter_company["headers"],
                    json={"title": "Özel Ünvan", "category": "GENEL", "base_role_prompt": "x"})
    assert r.status_code == 403


# ---------------------------------------------------------------------------
# Zamanlayıcı ve şablonlar
# ---------------------------------------------------------------------------
def test_expiration_reminder_schedule(db, tag):
    import asyncio
    from app.db.session import engine
    from app.services.scheduler_service import run_due_schedules

    email = f"hatirlat_{tag}@deneme-sirket.com.tr"
    _exec(db, "INSERT INTO tenants (slug, name, contact_email, is_active, package_expiry_date) VALUES (%s, %s, %s, TRUE, %s) RETURNING id",
          f"hatirlat_{tag}", f"Hatırlatma {tag}", email, datetime.now(timezone.utc) + timedelta(days=30))
    _exec(db, "UPDATE notification_schedules SET next_run_at = NULL WHERE trigger_type = 'BEFORE_EXPIRATION_INTERVAL' RETURNING id")

    async def run_twice():
        await engine.dispose(close=False)
        await run_due_schedules()
        await run_due_schedules()  # ikinci çalıştırma vadesi gelmediği için bir şey göndermez
        await engine.dispose()

    asyncio.run(run_twice())
    assert len(outbox_for(email)) == 1


def test_template_values_are_html_escaped():
    from app.services.notification_service import render_template_text
    out = render_template_text("<p>{{company_name}}</p>", {"company_name": "<script>alert(1)</script>"}, escape=True)
    assert "<script>" not in out and "&lt;script&gt;" in out


def test_public_stats(client):
    r = client.get("/api/v1/public/stats")
    assert r.status_code == 200 and r.json()["sectors"] == 11 and r.json()["llm_models"] >= 13


def test_invalid_tax_id_rejected(client, tag):
    """'123456' gibi geçersiz vergi numaraları Odoo'da başka bir şirketle eşleşebiliyordu."""
    email = f"vkn_{tag}@deneme-sirket.com.tr"
    client.post("/api/v1/tenants/purchase-request/send-code", json={"email": email})
    r = client.post("/api/v1/tenants/purchase-request", json=purchase_payload(email, code_from_outbox(email), tax_id="123456"))
    assert r.status_code == 400 and "VKN" in r.json()["detail"]


def test_odoo_mail_fallback_treats_none_marshal_fault_as_sent(monkeypatch):
    """Odoo mail.mail.send None döndürür; XML-RPC hatası gönderimin başarısız olduğu anlamına gelmez."""
    import xmlrpc.client
    from app.services.notification_service import NotificationService
    from app.services.odoo_service import OdooService

    class FakeModels:
        def execute_kw(self, db, uid, pw, model, method, args, *rest):
            if method == "create":
                return 7
            raise xmlrpc.client.Fault(1, "TypeError: cannot marshal None unless allow_none is enabled")

    monkeypatch.setattr(OdooService, "_get_connection", classmethod(lambda cls: (2, FakeModels(), {"db": "d", "password": "p"})))
    assert NotificationService._send_via_odoo({"from_email": "a@b.c"}, "x@y.z", "Konu", "<p>x</p>") is True


@pytest.mark.parametrize("tax_id", ["1234567890", "1111111111", "1222222223"])
def test_fake_tax_ids_rejected(client, tag, tax_id):
    """Ardışık/tekrarlı veya kontrol hanesi tutmayan vergi numaraları reddedilir."""
    email = f"vkn{tax_id[-3:]}_{tag}@deneme-sirket.com.tr"
    client.post("/api/v1/tenants/purchase-request/send-code", json={"email": email})
    r = client.post("/api/v1/tenants/purchase-request", json=purchase_payload(email, code_from_outbox(email), tax_id=tax_id))
    assert r.status_code == 400


def test_valid_tckn_accepted():
    from app.api.v1.tenants import validate_tax_id
    assert validate_tax_id("100 000 001 46") == "10000000146"


def test_odoo_partner_matching_requires_same_company():
    """Aynı vergi numaralı ama başka şirkete ait Odoo kaydı kullanılmaz (S00061/S00062 hatası)."""
    from app.services.odoo_service import partner_matches
    assert not partner_matches("SIRIUS MES", "a@siriusmes.com", {"name": "Antigravity Odoo Test A.Ş.", "email": "t@antigravity-corp.com"})
    assert not partner_matches("SIRIUS MES", "a@siriusmes.com", {"name": "KRT İnşaat A.Ş.", "email": "info@krt.com"})
    assert partner_matches("SIRIUSMES", "x@baska.com", {"name": "SİRİUS MES Mühendislik Ltd. Şti.", "email": ""})
    assert partner_matches("Yeni Ünvan A.Ş.", "a@siriusmes.com", {"name": "Eski Ünvan", "email": "b@siriusmes.com"})
