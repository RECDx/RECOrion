"""
#664: kredinin TL karşılığı ve insan eşdeğeri.

- Paketlerin kredi birim fiyatı: değer girilmemişse aylık ücret ÷ aylık kredi (PRO 39.900 ÷ 25.000 ≈ 1,596 TL); girilirse o.
- Maliyet ayarları (maaş bantları, katsayı, iş günü, RECDx gerçek kredi maliyeti) yalnız süper admin; sınırlar içine alınır.
- Proje maliyetinde adım bazında: AI kredisi × birim fiyat = TL; insan eşdeğeri = ünvan bandı × katsayı ÷ iş günü × planlanan gün.
"""
from tests.test_lifecycle import super_headers, tag  # noqa: F401  (fikstür)
from tests.test_workflow import _exec, _ready_project, world  # noqa: F401  (fikstür)


def test_plan_credit_unit_and_cost_settings(client, super_headers, world):  # noqa: F811
    plans = {p["code"]: p for p in client.get("/api/v1/tenants/plans").json()}
    assert abs(plans["PRO"]["effective_credit_unit_try"] - 1.596) < 0.001
    assert abs(plans["ENTERPRISE"]["effective_credit_unit_try"] - 0.99) < 0.001
    assert client.get("/api/v1/system/cost-settings", headers=world["admin"]["h"]).status_code == 403
    cfg = client.get("/api/v1/system/cost-settings", headers=super_headers).json()
    assert cfg["salary_bands"]["IT"]["MID"] == 140000 and cfg["employer_factor"] == 1.25 and cfg["work_days_month"] == 22
    r = client.put("/api/v1/system/cost-settings", headers=super_headers, json={**cfg, "employer_factor": 9, "work_days_month": 3})
    assert r.status_code == 200 and r.json()["employer_factor"] == 3.0 and r.json()["work_days_month"] == 15  # sınırlar
    assert client.put("/api/v1/system/cost-settings", headers=super_headers, json=cfg).json()["employer_factor"] == 1.25


def test_project_costs_show_ai_credit_try_and_human_equivalent(client, db, world):  # noqa: F811
    w = world
    admin = w["admin"]["h"]
    pid, human_id, dep_id = _ready_project(client, w, "İnsan Eşdeğeri")
    jt = _exec(db, "INSERT INTO job_titles (tenant_id, code, title, category, base_role_prompt, seniority) VALUES (NULL, %s, "
                   "'Yazılım Geliştirici (Backend)', 'Bilişim', 'x', 'MID') RETURNING id", f"HE_BACKEND_{pid[:8]}")[0]
    ai_task = _exec(db, "SELECT id FROM tasks WHERE project_id = %s AND title = 'AI adımı'", pid)[0]
    _exec(db, "UPDATE tasks SET job_title_id = %s, estimated_effort = 2 WHERE id = %s RETURNING id", jt, ai_task)
    _exec(db, "INSERT INTO llm_calls (id, tenant_id, project_id, task_id, model_code, purpose, status, tokens_in, tokens_out, credits_cost, latency_ms) "
              "VALUES (gen_random_uuid(), %s, %s, %s, 'deepseek-v4-flash', 'AGENT_CHAT', 'SUCCESS', 3000, 2000, 10, 1000) RETURNING id",
          w["tenant"], pid, ai_task)
    c = client.get(f"/api/v1/projects/{pid}/costs", headers=admin).json()
    row = next(r for r in c["tasks"] if r["title"] == "AI adımı")
    assert row["human"]["family"] == "IT" and row["human"]["basis"] == "REFERANS" and row["human"]["seniority"] == "MID"
    assert abs(row["human"]["daily_cost"] - 7954.55) < 0.01 and abs(row["human"]["cost"] - 15909.10) < 0.02
    assert abs(row["ai_credit_try"] - 15.96) < 0.01  # 10 kredi × 1,596 TL (PRO)
    other = next(r for r in c["tasks"] if r["title"] == "İnsan adımı")
    assert other["human"]["basis"] in ("VARSAYILAN", "REFERANS")
    t = c["totals"]
    assert abs(t["credit_unit_try"] - 1.596) < 0.001 and t["human_cost"] > t["ai_credit_try"] and t["saving"] > 0
    assert "iş günü" in t["cost_basis_note"]
    client.post(f"/api/v1/projects/{pid}/status", headers=admin, json={"action": "cancel"})
