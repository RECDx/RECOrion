"""
#349: müşteriye EVREN model adları yerine RECAi adları.

- AI personel RECAi adı seçer (Mergen/Hızlı/Derin); arkasındaki model gateway'de çözülür; Süper Admin modeli değiştirince
  personel kendiliğinden yeni modele geçer, müşteride ad değişmez.
- Paketinde olmayan ad seçilemez; Görsel/Ses/Okur paket ve personel bazında açılır-kapanır (kapalıysa çağrı reddedilir).
- Müşteri yanıtlarında (AI personel, seçenekler, raporlar) gerçek model adı yok; yalnızca Süper Admin görür.
"""
import uuid

import pytest

from app.services import llm_gateway
from tests.test_integrations import _super
from tests.test_workflow import _exec, world  # noqa: F401  (fikstür)

REAL = ("deepseek", "mimo", "qwen", "gemma", "glm")


def _resolve(client, tenant_id, actor_id, purpose="AGENT_CHAT"):
    from app.db.models import Tenant
    from app.db.session import AsyncSessionLocal

    async def go():
        async with AsyncSessionLocal() as s:
            t = await s.get(Tenant, uuid.UUID(tenant_id))
            return (await llm_gateway.resolve_model(s, t, purpose, None, uuid.UUID(actor_id) if actor_id else None)).model_code
    return client.portal.call(go)


def test_agent_tier_resolves_and_follows_super_admin_change(client, db, world):
    w = world
    h = w["admin"]["h"]
    title = _exec(db, "INSERT INTO job_titles (tenant_id, code, title, category, base_role_prompt, is_active, source) "
                      "VALUES (%s, %s, 'Analist', 'GENEL', 'Sen bir analistsin.', TRUE, 'COMPANY') RETURNING id::text",
                  w["tenant"], f"ANALIST_{uuid.uuid4().hex[:6].upper()}")[0]
    r = client.post(f"/api/v1/company/{w['tenant']}/ai-agents", headers=h, json={
        "display_name": f"Derin Analist {uuid.uuid4().hex[:4]}", "job_title_id": title, "model_code": "DERIN",
        "recai_capabilities": {"GORSEL": False}})
    assert r.status_code in (200, 201), r.text
    agent = r.json()
    assert agent["recai_tier"] == "DERIN" and agent["model_display_name"] == "RECAi Derin" and agent["recai_capabilities"] == {"GORSEL": False}
    assert not any(x in r.text for x in REAL)  # yanıtta gerçek model adı yok
    assert _resolve(client, w["tenant"], agent["id"]) == "mimo-v2.6-pro"

    listed = client.get(f"/api/v1/company/{w['tenant']}/ai-agents", headers=h)
    assert not any(x in listed.text for x in REAL)

    sa = _super(client, db)
    tiers = {t["code"]: t for t in client.get("/api/v1/system/recai-tiers", headers=sa).json()}
    assert tiers["DERIN"]["model_code"] == "mimo-v2.6-pro" and tiers["GORSEL"]["purpose"] == "VISION"
    assert client.get("/api/v1/system/recai-tiers", headers=h).status_code == 403
    assert client.put("/api/v1/system/recai-tiers/DERIN", headers=sa, json={"model_code": "qwen3-vl-30b"}).status_code == 422  # tür uymaz
    assert client.put("/api/v1/system/recai-tiers/DERIN", headers=sa, json={"model_code": "yok-model"}).status_code == 422
    try:
        r = client.put("/api/v1/system/recai-tiers/DERIN", headers=sa, json={"model_code": "glm-5.3", "fallback_model_code": "mimo-v2.6-pro"})
        assert r.status_code == 200
        assert _resolve(client, w["tenant"], agent["id"]) == "glm-5.3"  # personel kendiliğinden yeni modele geçti
        again = client.get(f"/api/v1/company/{w['tenant']}/ai-agents", headers=h).json()
        assert next(a for a in again if a["id"] == agent["id"])["model_display_name"] == "RECAi Derin"  # ad değişmedi
    finally:
        client.put("/api/v1/system/recai-tiers/DERIN", headers=sa, json={"model_code": "mimo-v2.6-pro", "fallback_model_code": "deepseek-v4.1-flash"})


def test_package_tiers_and_capabilities(client, db, world):
    w = world
    h = w["admin"]["h"]
    opts = client.get(f"/api/v1/company/{w['tenant']}/recai", headers=h).json()
    assert {t["code"]: t["available"] for t in opts["tiers"]} == {"MERGEN": True, "HIZLI": True, "DERIN": True}  # PRO
    assert {c["code"]: c["in_plan"] for c in opts["capabilities"]} == {"GORSEL": True, "SES": True, "OKUR": True}
    assert "EVREN" in opts["infra_note"] and not any(x in str(opts) for x in REAL)

    # STARTER: Derin ve Görsel yok
    _exec(db, "UPDATE tenants SET plan_id = (SELECT id FROM plans WHERE code = 'STARTER') WHERE id = %s", w["tenant"])
    try:
        opts = client.get(f"/api/v1/company/{w['tenant']}/recai", headers=h).json()
        assert {t["code"]: t["available"] for t in opts["tiers"]}["DERIN"] is False
        assert {c["code"]: c["in_plan"] for c in opts["capabilities"]}["GORSEL"] is False
        r = client.put(f"/api/v1/company/{w['tenant']}/ai-agents/{w['agent']}", headers=h, json={"model_code": "DERIN"})
        assert r.status_code == 403 and ("RECAi Derin" in r.json()["detail"] or "değiştirmeye izin vermiyor" in r.json()["detail"])
        r = client.put(f"/api/v1/company/{w['tenant']}/ai-agents/{w['agent']}", headers=h, json={"recai_capabilities": {"GORSEL": True, "OKUR": True}})
        assert r.json()["recai_capabilities"] == {"GORSEL": False, "OKUR": False}  # paketinde yoksa açılamaz

        from app.services.llm_gateway import LLMContext, ModelNotAllowed

        with pytest.raises(ModelNotAllowed, match="RECAi Görsel paketinizde yer almıyor"):
            client.portal.call(llm_gateway.describe_image, LLMContext(tenant_id=uuid.UUID(w["tenant"])), b"png", "açıkla")
    finally:
        _exec(db, "UPDATE tenants SET plan_id = (SELECT id FROM plans WHERE code = 'PRO') WHERE id = %s", w["tenant"])

    # PRO'da Görsel açık ama personel için kapatılabilir
    client.put(f"/api/v1/company/{w['tenant']}/ai-agents/{w['agent']}", headers=h, json={"recai_capabilities": {"GORSEL": False}})
    from app.services.llm_gateway import LLMContext, ModelNotAllowed

    with pytest.raises(ModelNotAllowed, match="bu AI personel için kapalı"):
        client.portal.call(llm_gateway.describe_image, LLMContext(tenant_id=uuid.UUID(w["tenant"]), actor_id=uuid.UUID(w["agent"])), b"png", "açıkla")


def test_public_plans_hide_real_models(client, db):
    plans = client.get("/api/v1/tenants/plans?active_only=true").json()
    pro = next(p for p in plans if p["code"] == "PRO")
    assert pro["allowed_models"] == [] and pro["recai_tiers"] == ["MERGEN", "HIZLI", "DERIN"]
    sa = _super(client, db)
    assert next(p for p in client.get("/api/v1/tenants/plans", headers=sa).json() if p["code"] == "PRO")["allowed_models"]
