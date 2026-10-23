"""
ADIM 9.1: Şirket dashboard'u.

- Proje/adım durumları, günlük kredi ve TL maliyet serisi, LLM bazında maliyet, proje bazında bütçe/gerçekleşen.
- Yalnızca şirket yöneticisi; platform personeli müşteri içeriğini göremez (KVKK); dönem doğrulanır.
- KVKK: personel maliyeti yalnızca toplam/proje düzeyinde; kişi adı veya kişi başı günlük ücret dönmez.
"""
import json
import uuid

from tests.test_workflow import PASSWORD, _exec, _login, _ready_project, world  # noqa: F401  (fikstür)
from app.core.security import hash_password


def _call(db, w, pid, task_id, model, credits, cost_try, days_ago=0):
    _exec(db, "INSERT INTO llm_calls (id, tenant_id, project_id, task_id, purpose, model_code, tokens_in, tokens_out, credits_cost, "
              "latency_ms, status, cost_try, created_at) VALUES (gen_random_uuid(), %s, %s, %s, 'AGENT_CHAT', %s, 1000, 500, %s, 900, "
              "'SUCCESS', %s, now() - make_interval(days => %s))", w["tenant"], pid, task_id, model, credits, cost_try, days_ago)


def test_company_dashboard(client, db, world):
    w = world
    admin = w["admin"]["h"]
    pid, human_id, _ = _ready_project(client, w, "Pano Projesi")
    _exec(db, "UPDATE projects SET budget_try = 10000 WHERE id = %s", pid)
    _exec(db, "UPDATE actors SET daily_cost_try = 4321 WHERE id = %s", w["member"]["id"])
    client.post(f"/api/v1/projects/{pid}/cost-items", headers=admin,
                json={"category": "LISANS", "description": "Lisans", "quantity": 1, "unit_price_try": 750})
    _call(db, w, pid, human_id, "pano-model-a", 12.5, 3.25)
    _call(db, w, pid, human_id, "pano-model-a", 7.5, None, days_ago=2)
    _call(db, w, pid, None, "pano-model-b", 4.0, 1.0, days_ago=40)  # 30 günlük dönemin dışında

    r = client.get(f"/api/v1/company/{w['tenant']}/dashboard?days=30", headers=admin)
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["projects"]["by_status"].get("READY", 0) >= 1 and d["tasks"]["total"] >= 3
    assert len(d["series"]) == 30 and d["series"][-1]["cost"] >= 3.25
    a = next(m for m in d["by_model"] if m["model_code"] == "pano-model-a")
    assert a["calls"] == 2 and a["credits"] == 20.0 and a["cost"] == 3.25 and a["unpriced_calls"] == 1
    assert not any(m["model_code"] == "pano-model-b" for m in d["by_model"])
    row = next(p for p in d["costs"]["projects"] if p["project_id"] == pid)
    assert row["budget"] == 10000 and row["other"] == 750 and row["token"] >= 4.25 and row["tasks_total"] == 3
    assert any(c["category"] == "LISANS" and c["amount"] >= 750 for c in d["costs"]["by_category"])
    assert d["credits"] and "monthly_grant" in d["credits"]
    # KVKK: kişi adı ve kişi başı günlük ücret yok
    text = json.dumps(d, ensure_ascii=False)
    assert "Uzman" not in text and "4321" not in text

    r90 = client.get(f"/api/v1/company/{w['tenant']}/dashboard?days=90", headers=admin).json()
    assert len(r90["series"]) == 90 and any(m["model_code"] == "pano-model-b" for m in r90["by_model"])
    assert client.get(f"/api/v1/company/{w['tenant']}/dashboard?days=12", headers=admin).status_code == 422


def test_company_dashboard_access(client, db, world):
    w = world
    url = f"/api/v1/company/{w['tenant']}/dashboard"
    assert client.get(url, headers=w["member"]["h"]).status_code == 403  # ekip üyesi şirket panosunu görmez
    tag = uuid.uuid4().hex[:6]
    hq = _exec(db, "SELECT id FROM tenants WHERE slug = 'recdx_hq'")[0]
    email = f"pano_super_{tag}@recdx.com"
    _exec(db, "INSERT INTO actors (tenant_id, actor_type, display_name, email, role, password_hash, status) "
              "VALUES (%s, 'HUMAN', 'Süper', %s, 'SUPER_ADMIN', %s, 'IDLE')", hq, email, hash_password(PASSWORD))
    assert client.get(url, headers=_login(client, email)).status_code == 403  # KVKK: platform personeli müşteri içeriğini görmez
    other_dept = _exec(db, "INSERT INTO departments (id, tenant_id, name) VALUES (gen_random_uuid(), %s, 'Başka') RETURNING id", hq)[0]
    assert client.get(f"{url}?department_id={other_dept}", headers=w["admin"]["h"]).status_code == 404
