"""
Adım 4: LLM Gateway, kredi defteri, model senkronu, Beyin AI ve Süper Yönetici asistanı.
EVREN'e gerçek çağrı yapılmaz; evren_client metotları sahte yanıtlarla değiştirilir.
"""
import uuid
from decimal import Decimal

import psycopg2
import pytest

from app.core.security import hash_password
from app.services import credits
from app.services.evren_client import ChatResult, EmbeddingResult, EvrenError, RerankResult, evren_client

PASSWORD = "Kredi-Testi-Sifresi-2026"


def _exec(db, sql, *params):
    with db.cursor() as cur:
        cur.execute(sql, params)
        return cur.fetchone() if cur.description else None


def _all(db, sql, *params):
    with db.cursor() as cur:
        cur.execute(sql, params)
        return cur.fetchall()


def _login(client, email):
    r = client.post("/api/v1/auth/login", json={"email": email, "password": PASSWORD})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


class FakeEvren:
    def __init__(self):
        self.chat_calls = []
        self.fail = False

    async def chat(self, model_code, messages, **kwargs):
        self.chat_calls.append((model_code, messages))
        if self.fail:
            raise EvrenError("bağlantı hatası")
        return ChatResult(content="Beyin yanıtı", thought=None, tokens_in=1000, tokens_out=500,
                          raw={"usage": {"evren": {"credits_held_cr": 0.5, "credits_remaining_cr": 999.5}}})

    async def embed(self, text, model_code):
        return EmbeddingResult(vector=[0.0] * 8, tokens_in=10)

    async def rerank(self, query, documents, model_code, top_n=5):
        return RerankResult(results=[], tokens_in=10)

    async def list_models(self):
        return [
            {"id": "glm-5.3", "task": "chat", "context_length": 524288, "default_max_output_tokens": 16384,
             "modalities": ["text"], "pricing": {"prompt_token_price": 0, "completion_token_price": 0,
                                                 "currency": "CR", "free_until": "2026-11-01"}},
            {"id": "voxcpm2", "task": "tts", "context_length": 4096, "modalities": ["text", "audio"],
             "pricing": {"prompt_token_price": 0, "completion_token_price": 0, "currency": "CR"}},
        ]


@pytest.fixture
def fake_evren(monkeypatch):
    fake = FakeEvren()
    for name in ("chat", "embed", "rerank", "list_models"):
        monkeypatch.setattr(evren_client, name, getattr(fake, name))
    return fake


@pytest.fixture(scope="module")
def tag():
    return uuid.uuid4().hex[:8]


def _make_tenant(db, tag, suffix, plan="STARTER"):
    tid = _exec(db, "INSERT INTO tenants (id, slug, name, plan_id, is_active) "
                    "VALUES (gen_random_uuid(), %s, %s, (SELECT id FROM plans WHERE code = %s), TRUE) RETURNING id",
                f"kredi_{suffix}_{tag}", f"Kredi {suffix} A.Ş.", plan)[0]
    email = f"kredi_{suffix}_{tag}@kredi-test.com.tr"
    _exec(db, "INSERT INTO actors (tenant_id, actor_type, display_name, email, role, password_hash, status) "
              "VALUES (%s, 'HUMAN', 'Kredi Yönetici', %s, 'COMPANY_ADMIN', %s, 'IDLE')", tid, email, hash_password(PASSWORD))
    return str(tid), email


@pytest.fixture(scope="module")
def company(db, client, tag):
    tid, email = _make_tenant(db, tag, "a")
    return {"id": tid, "headers": _login(client, email)}


@pytest.fixture(scope="module")
def super_headers(client, db, tag):
    hq = _exec(db, "SELECT id FROM tenants WHERE slug = 'recdx_hq'")[0]
    email = f"kredi_super_{tag}@recdx.com"
    _exec(db, "INSERT INTO actors (tenant_id, actor_type, display_name, email, role, password_hash, status) "
              "VALUES (%s, 'HUMAN', 'Kredi Super', %s, 'SUPER_ADMIN', %s, 'IDLE')", hq, email, hash_password(PASSWORD))
    return _login(client, email)


# ---------------------------------------------------------------------------
def test_credit_cost_formula():
    # katsayı × (giriş/1000 × 1 + çıkış/1000 × 2)
    assert credits.credit_cost(2, 1000, 500) == Decimal("4.0000")
    assert credits.credit_cost(None, 1000, 0) == Decimal("1.0000")


def test_brain_chat_charges_credits_and_uses_package_model(client, db, company, fake_evren):
    r = client.post(f"/api/v1/company/{company['id']}/brain/chat", json={"content": "Bu ay ne yapmalıyız?"},
                    headers=company["headers"])
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["message"]["content"] == "Beyin yanıtı"
    # Varsayılan Beyin modeli (glm-5.3) STARTER paketinde yok: paketin izin verdiği ilk sohbet modeli kullanılır
    assert body["model_code"] == "deepseek-v4-flash"
    assert body["credits"] == pytest.approx(0.8 * 2.0)  # katsayı 0.8 × (1 + 1)
    system_prompt = fake_evren.chat_calls[-1][1][0]["content"]
    assert "Kredi a A.Ş." in system_prompt

    rows = dict(_all(db, "SELECT entry_type, SUM(amount) FROM credit_ledger WHERE tenant_id = %s GROUP BY 1", company["id"]))
    assert rows["MONTHLY_GRANT"] == 5000
    assert rows["USAGE"] < 0
    call = _exec(db, "SELECT purpose, model_code, status, evren_balance_after FROM llm_calls "
                     "WHERE tenant_id = %s AND purpose = 'BRAIN'", company["id"])
    assert call[:3] == ("BRAIN", "deepseek-v4-flash", "SUCCESS") and call[3] == Decimal("999.5")

    history = client.get(f"/api/v1/company/{company['id']}/brain/history", headers=company["headers"]).json()
    assert [m["role"] for m in history] == ["user", "assistant"]

    summary = client.get(f"/api/v1/company/{company['id']}/credits", headers=company["headers"]).json()
    assert summary["summary"]["used_this_period"] > 0
    assert any(row["key"] == "BRAIN" for row in summary["by_purpose"])


def test_credit_ledger_is_append_only(db, company):
    with pytest.raises(psycopg2.Error):
        _exec(db, "UPDATE credit_ledger SET amount = 999999 WHERE tenant_id = %s", company["id"])
    with pytest.raises(psycopg2.Error):
        _exec(db, "DELETE FROM credit_ledger WHERE tenant_id = %s", company["id"])


def test_model_outside_package_is_rejected(client, company):
    r = client.put(f"/api/v1/company/{company['id']}/brain/settings", json={"brain_model_code": "glm-5.3"},
                   headers=company["headers"])
    assert r.status_code == 403
    r = client.put(f"/api/v1/company/{company['id']}/brain/settings", json={"brain_model_code": "gemma-4-31b"},
                   headers=company["headers"])
    assert r.status_code == 200 and r.json()["brain_model_code"] == "gemma-4-31b"


def test_evren_failure_returns_503_without_charge(client, db, company, fake_evren):
    before = _exec(db, "SELECT COUNT(*) FROM credit_ledger WHERE tenant_id = %s AND entry_type = 'USAGE'", company["id"])[0]
    fake_evren.fail = True
    r = client.post(f"/api/v1/company/{company['id']}/brain/chat", json={"content": "merhaba"}, headers=company["headers"])
    assert r.status_code == 503
    after = _exec(db, "SELECT COUNT(*) FROM credit_ledger WHERE tenant_id = %s AND entry_type = 'USAGE'", company["id"])[0]
    assert after == before + 1  # yalnızca vektörleme (hafıza araması) ücretlendi, sohbet değil
    assert _exec(db, "SELECT COUNT(*) FROM llm_calls WHERE tenant_id = %s AND status = 'FAILED'", company["id"])[0] == 1


def test_exhausted_credits_return_402(client, db, tag, fake_evren):
    tid, email = _make_tenant(db, tag, "b")
    headers = _login(client, email)
    client.get(f"/api/v1/company/{tid}/credits", headers=headers)  # aylık hak eklenir
    _exec(db, "INSERT INTO credit_ledger (tenant_id, entry_type, amount, period, note) VALUES (%s, 'ADJUSTMENT', -5000, %s, 'test')",
          tid, credits.current_period())
    r = client.post(f"/api/v1/company/{tid}/brain/chat", json={"content": "merhaba"}, headers=headers)
    assert r.status_code == 402
    assert fake_evren.chat_calls == []


def test_unused_monthly_credits_expire_topups_carry_over(client, db, tag, super_headers):
    tid, email = _make_tenant(db, tag, "c")
    _exec(db, "INSERT INTO credit_ledger (tenant_id, entry_type, amount, period) VALUES (%s, 'MONTHLY_GRANT', 5000, '2000-01')", tid)
    _exec(db, "INSERT INTO credit_ledger (tenant_id, entry_type, amount, period) VALUES (%s, 'USAGE', -1000, '2000-01')", tid)
    _exec(db, "INSERT INTO credit_ledger (tenant_id, entry_type, amount, period) VALUES (%s, 'TOPUP', 300, '2000-01')", tid)
    summary = client.get(f"/api/v1/company/{tid}/credits", headers=_login(client, email)).json()["summary"]
    assert _exec(db, "SELECT amount FROM credit_ledger WHERE tenant_id = %s AND entry_type = 'EXPIRE'", tid)[0] == -4000
    assert summary["balance"] == 5300 and summary["topup_balance"] == 300

    r = client.post(f"/api/v1/tenants/{tid}/credits/topup", json={"amount": 200, "note": "kampanya"}, headers=super_headers)
    assert r.status_code == 200 and r.json()["summary"]["balance"] == 5500


def test_credit_permissions(client, company, super_headers):
    # Kredi durumu yönetim verisidir: süper admin görebilir; Beyin AI içeriktir: göremez (KVKK)
    assert client.get(f"/api/v1/company/{company['id']}/credits", headers=super_headers).status_code == 200
    assert client.get(f"/api/v1/company/{company['id']}/brain/history", headers=super_headers).status_code == 403
    assert client.post(f"/api/v1/tenants/{company['id']}/credits/topup", json={"amount": 10},
                       headers=company["headers"]).status_code == 403
    assert client.get("/api/v1/system/llm/usage", headers=company["headers"]).status_code == 403
    assert client.post("/api/v1/system/assistant/chat", json={"content": "x"}, headers=company["headers"]).status_code == 403


def test_platform_assistant_uses_aggregate_data(client, super_headers, fake_evren):
    r = client.post("/api/v1/system/assistant/chat", json={"content": "Kaç müşterimiz var?"}, headers=super_headers)
    assert r.status_code == 200, r.text
    prompt = fake_evren.chat_calls[-1][1][0]["content"]
    assert "Kredi a A.Ş." in prompt and "KVKK" in prompt
    history = client.get("/api/v1/system/assistant/history", headers=super_headers).json()
    assert history[-1]["content"] == "Beyin yanıtı"
    usage = client.get("/api/v1/system/llm/usage", headers=super_headers).json()
    assert usage["evren_balance"]["credits_remaining"] == 999.5


def test_sync_evren_adds_new_models_inactive(client, db, super_headers, fake_evren):
    r = client.post("/api/v1/models/sync-evren", headers=super_headers)
    assert r.status_code == 200, r.text
    try:
        assert r.json()["added"] == ["voxcpm2"]
        assert _exec(db, "SELECT model_type, status FROM llm_models WHERE model_code = 'voxcpm2'") == ("TTS", "INACTIVE")
    finally:  # diğer testler başlangıç kataloğunu (15 model) bekliyor
        _exec(db, "DELETE FROM llm_models WHERE model_code = 'voxcpm2'")
    assert _exec(db, "SELECT context_window, evren_task, free_until::text FROM llm_models WHERE model_code = 'glm-5.3'") == \
        (524288, "chat", "2026-11-01")


def test_model_settings_validate_type(client, super_headers):
    r = client.put("/api/v1/system/settings/models", json={"settings": {"model.default.embedding": "glm-5.3"}},
                   headers=super_headers)
    assert r.status_code == 400
    r = client.put("/api/v1/system/settings/models", json={"settings": {"model.default.brain": "gemma-4-31b"}},
                   headers=super_headers)
    assert r.status_code == 200
    assert next(s for s in r.json() if s["key"] == "model.default.brain")["model_code"] == "gemma-4-31b"
