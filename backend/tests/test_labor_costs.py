"""
ADIM 7.5.2: Personel maliyeti ve proje maliyet ucu (gerçek Temporal; EVREN ve nesne deposu sahte).

- Günlük maliyet: insan personelde kişisel veri; listede yalnızca kullanıcı yönetme yetkisi olana görünür.
- Adım tamamlanınca ücret ve gerçekleşen iş günü kayda geçer; ücret sonradan değişse de geçmiş adımın maliyeti değişmez.
- Token maliyeti: AI personel çağrılarının TL maliyeti (LLM fiyatı) adım bazında toplanır; fiyatsız çağrılar ayrıca sayılır.
- Maliyet raporu proje yöneticisine açıktır, ekip üyesine kapalıdır.
"""
from tests.test_workflow import _exec, _ready_project, _wait, ai, world  # noqa: F401  (fikstürler)


def test_labor_and_token_costs(client, db, world, ai):
    w = world
    admin, member = w["admin"]["h"], w["member"]["h"]
    tid = w["tenant"]

    # Günlük maliyetler: insan (kişisel veri) ve AI (isteğe bağlı sabit)
    r = client.put(f"/api/v1/company/{tid}/users/{w['member']['id']}", headers=admin, json={"daily_cost_try": 2500})
    assert r.status_code == 200 and r.json()["daily_cost_try"] == 2500, r.text
    assert client.put(f"/api/v1/company/{tid}/users/{w['member']['id']}", headers=member, json={"daily_cost_try": 1}).status_code == 403
    admin_view = {u["id"]: u for u in client.get(f"/api/v1/company/{tid}/users", headers=admin).json()}
    member_view = {u["id"]: u for u in client.get(f"/api/v1/company/{tid}/users", headers=member).json()}
    assert admin_view[w["member"]["id"]]["daily_cost_try"] == 2500
    assert member_view[w["member"]["id"]]["daily_cost_try"] is None  # KVKK: üye başkasının ücretini görmez
    r = client.put(f"/api/v1/company/{tid}/ai-agents/{w['agent']}", headers=admin, json={"daily_cost_try": 100})
    assert r.status_code == 200 and r.json()["daily_cost_try"] == 100, r.text

    # AI personel modelinin TL fiyatı (1M girdi 10 ₺, 1M çıktı 40 ₺)
    model_id = _exec(db, "SELECT preferred_model_id FROM actors WHERE id = %s", w["agent"])[0]
    _exec(db, "DELETE FROM llm_model_prices WHERE model_id = %s", model_id)
    _exec(db, "INSERT INTO llm_model_prices (model_id, price_in_per_1m_try, price_out_per_1m_try, valid_from) VALUES (%s, 10, 40, now() - interval '1 day')", model_id)
    try:
        pid, human_id, dep_id = _ready_project(client, w, "Maliyet Projesi")
        before = client.get(f"/api/v1/projects/{pid}/costs", headers=admin).json()
        assert all(t["labor"]["basis"] == "PLANNED" for t in before["tasks"])
        human_plan = next(t for t in before["tasks"] if t["title"] == "İnsan adımı")
        assert human_plan["labor"]["cost"] == 2500.0 and before["totals"]["labor"] == 0  # tahmin gerçekleşene sayılmaz

        assert client.post(f"/api/v1/projects/{pid}/status", headers=admin, json={"action": "start"}).status_code == 200
        _wait(client, admin, pid, lambda t, f: t["AI adımı"]["status"] == "WAITING_APPROVAL" and t["İnsan adımı"]["status"] == "IN_PROGRESS", "başlamalı")
        ai_id = next(t["task_id"] for t in before["tasks"] if t["title"] == "AI adımı")
        assert client.post(f"/api/v1/tasks/{ai_id}/decision", headers=admin, json={"approve": True}).status_code == 200
        client.post(f"/api/v1/tasks/{human_id}/submit", headers=member, json={"note": "bitti"})
        _wait(client, admin, pid, lambda t, f: t["İnsan adımı"]["status"] == "WAITING_APPROVAL", "insan teslimi")
        assert client.post(f"/api/v1/tasks/{human_id}/decision", headers=admin, json={"approve": True}).status_code == 200
        _wait(client, admin, pid, lambda t, f: t["İnsan adımı"]["status"] == "DONE" and t["AI adımı"]["status"] == "DONE", "iki adım tamamlanmalı")

        # Ücret sonradan değişir: tamamlanan adımın maliyeti değişmez
        client.put(f"/api/v1/company/{tid}/users/{w['member']['id']}", headers=admin, json={"daily_cost_try": 9999})
        assert client.get(f"/api/v1/projects/{pid}/costs", headers=member).status_code == 403  # rapor yöneticide
        c = client.get(f"/api/v1/projects/{pid}/costs", headers=admin).json()
        rows = {t["title"]: t for t in c["tasks"]}
        human, ai_row = rows["İnsan adımı"], rows["AI adımı"]
        assert human["labor"]["basis"] == "ACTUAL" and human["labor"]["days"] == 1 and human["labor"]["cost"] == 2500.0
        assert ai_row["labor"]["cost"] == 100.0  # AI günlük sabit maliyet × 1 gün
        # FakeAI çağrısı: 1200 girdi × 10/1M + 300 çıktı × 40/1M = 0,024 ₺
        assert ai_row["tokens"]["calls"] == 1 and abs(ai_row["tokens"]["cost"] - 0.024) < 1e-9 and ai_row["tokens"]["unpriced_calls"] == 0
        # İnsan adımı bitince bağımlı AI adımı başladı: süren adım da gerçekleşen maliyet biriktirir (1 gün × 100 ₺)
        dep = rows["Bağımlı adım"]
        assert dep["labor"]["basis"] == "RUNNING" and dep["labor"]["cost"] == 100.0
        tokens = sum(t["tokens"]["cost"] for t in c["tasks"])
        assert c["totals"]["labor"] == 2700.0 and abs(c["totals"]["actual"] - (2700 + tokens)) < 1e-6
        assert c["by_model"] and c["by_model"][0]["calls"] >= 1 and c["currency"] == "TRY" and c["vat_included"] is False
        client.post(f"/api/v1/projects/{pid}/status", headers=admin, json={"action": "cancel"})

        # Fiyatı tanımsız modelle yapılan çağrı fiyatsız sayılır
        _exec(db, "DELETE FROM llm_model_prices WHERE model_id = %s", model_id)
        pid2, _, _ = _ready_project(client, w, "Fiyatsız Proje")
        client.post(f"/api/v1/projects/{pid2}/status", headers=admin, json={"action": "start"})
        _wait(client, admin, pid2, lambda t, f: t["AI adımı"]["status"] == "WAITING_APPROVAL", "AI çıktısı")
        c2 = client.get(f"/api/v1/projects/{pid2}/costs", headers=admin).json()
        assert c2["totals"]["unpriced_calls"] >= 1 and c2["totals"]["token"] == 0
        client.post(f"/api/v1/projects/{pid2}/status", headers=admin, json={"action": "cancel"})
    finally:
        _exec(db, "DELETE FROM llm_model_prices WHERE model_id = %s", model_id)
        _exec(db, "UPDATE actors SET daily_cost_try = NULL WHERE id IN (%s, %s)", w["member"]["id"], w["agent"])
