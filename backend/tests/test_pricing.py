"""
ADIM 7.5.1: LLM bazında TL fiyat listesi.

- Fiyat geçmişi: yeni fiyat yeni satırdır; her çağrı çağrı anındaki fiyatla TL maliyet alır, eski çağrılar değişmez.
- Geriye dönük fiyat girilince o aralıktaki fiyatlanmamış çağrılar hesaplanır.
- EVREN fiyatı (CR/token) ve CR>TL kuruyla TL fiyat önerisi; yalnızca Süper Admin.
"""
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from app.core.security import hash_password
from app.services import llm_gateway
from app.services.evren_client import ChatResult, evren_client
from app.services.llm_gateway import LLMContext

PASSWORD = "Fiyat-Testi-Sifresi-2026"
MODEL = "gemma-4-31b"


def _exec(db, sql, *params):
    with db.cursor() as cur:
        cur.execute(sql, params)
        return cur.fetchone() if cur.description else None


@pytest.fixture(scope="module")
def admins(client, db):
    tag = uuid.uuid4().hex[:6]
    hq = _exec(db, "SELECT id FROM tenants WHERE slug = 'recdx_hq'")[0]
    sa = f"fiyat_super_{tag}@recdx.com"
    _exec(db, "INSERT INTO actors (tenant_id, actor_type, display_name, email, role, password_hash, status) "
              "VALUES (%s, 'HUMAN', 'Süper', %s, 'SUPER_ADMIN', %s, 'IDLE')", hq, sa, hash_password(PASSWORD))
    tid = _exec(db, "INSERT INTO tenants (id, slug, name, plan_id, is_active) VALUES (gen_random_uuid(), %s, 'Fiyat Ltd', "
                    "(SELECT id FROM plans WHERE code = 'PRO'), TRUE) RETURNING id", f"fiyat_{tag}")[0]
    ca = f"fiyat_admin_{tag}@fiyat-test.com.tr"
    _exec(db, "INSERT INTO actors (tenant_id, actor_type, display_name, email, role, password_hash, status) "
              "VALUES (%s, 'HUMAN', 'Yönetici', %s, 'COMPANY_ADMIN', %s, 'IDLE')", tid, ca, hash_password(PASSWORD))

    def login(email):
        return {"Authorization": f"Bearer {client.post('/api/v1/auth/login', json={'email': email, 'password': PASSWORD}).json()['access_token']}"}
    return {"super": login(sa), "company": login(ca)}


def test_price_history_and_call_costs(client, db, admins, monkeypatch):
    model_id = _exec(db, "SELECT id FROM llm_models WHERE model_code = %s", MODEL)[0]
    _exec(db, "DELETE FROM llm_model_prices WHERE model_id = %s", model_id)
    t0 = datetime.now(timezone.utc) - timedelta(days=2)
    # Fiyat girilmeden önce yapılmış (fiyatlanmamış) çağrı
    old_call = _exec(db, "INSERT INTO llm_calls (id, model_id, model_code, purpose, tokens_in, tokens_out, status, created_at) "
                         "VALUES (gen_random_uuid(), %s, %s, 'CHAT', 1000, 500, 'SUCCESS', %s) RETURNING id", model_id, MODEL, t0 + timedelta(hours=1))[0]

    assert client.get("/api/v1/system/llm-prices", headers=admins["company"]).status_code == 403
    r = client.post("/api/v1/system/llm-prices", headers=admins["super"], json={
        "model_code": MODEL, "price_in_per_1m_try": 10, "price_out_per_1m_try": 40, "valid_from": t0.isoformat(), "note": "İlk fiyat"})
    assert r.status_code == 200, r.text
    assert r.json()["backfilled_calls"] >= 1
    assert _exec(db, "SELECT cost_try FROM llm_calls WHERE id = %s", old_call)[0] == Decimal("0.030000")  # 1000×10/1M + 500×40/1M
    dup = client.post("/api/v1/system/llm-prices", headers=admins["super"], json={
        "model_code": MODEL, "price_in_per_1m_try": 1, "price_out_per_1m_try": 1, "valid_from": t0.isoformat()})
    assert dup.status_code == 409

    # Yeni fiyat: sonraki çağrılar yeni fiyatla; eski çağrı değişmez
    assert client.post("/api/v1/system/llm-prices", headers=admins["super"], json={
        "model_code": MODEL, "price_in_per_1m_try": 20, "price_out_per_1m_try": 80}).status_code == 200

    async def chat(model_code, messages, **kw):
        return ChatResult("Tamam", None, 2000, 1000, {})
    monkeypatch.setattr(evren_client, "chat", chat)
    result = client.portal.call(llm_gateway.chat, LLMContext(tenant_id=None, purpose="CHAT"), [{"role": "user", "content": "x"}], MODEL)
    assert result.model_code == MODEL
    new_cost = _exec(db, "SELECT cost_try FROM llm_calls WHERE model_code = %s ORDER BY created_at DESC LIMIT 1", MODEL)[0]
    assert new_cost == Decimal("0.120000")  # 2000×20/1M + 1000×80/1M
    assert _exec(db, "SELECT cost_try FROM llm_calls WHERE id = %s", old_call)[0] == Decimal("0.030000")

    listing = client.get("/api/v1/system/llm-prices", headers=admins["super"]).json()
    row = next(m for m in listing["models"] if m["model_code"] == MODEL)
    assert row["current"]["price_in_per_1m_try"] == 20 and len(row["history"]) == 2


def test_cr_rate_suggestion(client, db, admins):
    _exec(db, "UPDATE llm_models SET prompt_token_price = 0.000002, completion_token_price = 0.000008, pricing_currency = 'CR' "
              "WHERE model_code = 'qwen3.8-flash-next'")
    try:
        assert client.put("/api/v1/system/llm-prices/cr-rate", headers=admins["company"], json={"cr_to_try": 2.5}).status_code == 403
        assert client.put("/api/v1/system/llm-prices/cr-rate", headers=admins["super"], json={"cr_to_try": 2.5}).json() == {"cr_to_try": 2.5}
        listing = client.get("/api/v1/system/llm-prices", headers=admins["super"]).json()
        assert listing["cr_to_try"] == 2.5
        row = next(m for m in listing["models"] if m["model_code"] == "qwen3.8-flash-next")
        assert row["suggestion"] == {"price_in_per_1m_try": 5.0, "price_out_per_1m_try": 20.0}  # CR/token × 1M × 2,5
        free = next(m for m in listing["models"] if m["model_code"] == "deepseek-v4-flash")
        assert free["suggestion"] is None  # EVREN fiyatı 0 (ücretsiz dönem)
    finally:
        _exec(db, "UPDATE llm_models SET prompt_token_price = 0, completion_token_price = 0 WHERE model_code = 'qwen3.8-flash-next'")
        client.put("/api/v1/system/llm-prices/cr-rate", headers=admins["super"], json={"cr_to_try": None})
