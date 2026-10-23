"""
ADIM 9.1: Şirket dashboard'u.

- Proje/adım durumları, günlük kredi ve TL maliyet serisi, LLM bazında maliyet, proje bazında bütçe/gerçekleşen.
- Yalnızca şirket yöneticisi; platform personeli müşteri içeriğini göremez (KVKK); dönem doğrulanır.
- KVKK: personel maliyeti yalnızca toplam/proje düzeyinde; kişi adı veya kişi başı günlük ücret dönmez.
"""
import json
import uuid

from tests.test_workflow import PASSWORD, _exec, _login, _ready_project, ai, world  # noqa: F401  (fikstür)
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
    # KVKK: kişi başı günlük ücret hiçbir yerde yok; ekip iş durumu yalnızca iş sayıları içerir
    text = json.dumps(d, ensure_ascii=False)
    assert "4321" not in text and "daily_cost" not in text
    assert all(set(p) <= {"actor_id", "name", "title", "open", "working", "waiting_approval", "done", "overdue"} for p in d["people"])

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


def test_agent_scorecard_and_roi(client, db, world, ai):
    """ADIM 9.2: kontrol personeli bir kez reddeder, yönetici onaylar: karne ve tahmini tasarruf."""
    from tests.test_workflow import _wait
    w = world
    admin = w["admin"]["h"]
    ai.fail_reviews = 1
    pid, _, _ = _ready_project(client, w, "Karne Projesi", reviewer=True)
    client.post(f"/api/v1/projects/{pid}/status", headers=admin, json={"action": "start"})
    tasks, _ = _wait(client, admin, pid, lambda t, f: t["AI adımı"]["status"] == "WAITING_APPROVAL", "AI adımı onaya gelmeli", 60)
    assert client.post(f"/api/v1/tasks/{tasks['AI adımı']['id']}/decision", headers=admin, json={"approve": True}).status_code == 200
    _wait(client, admin, pid, lambda t, f: t["AI adımı"]["status"] == "DONE", "AI adımı tamamlanmalı", 30)

    url = f"/api/v1/company/{w['tenant']}/dashboard?days=30"
    d = client.get(url, headers=admin).json()
    card = next(a for a in d["agents"] if a["name"] == "Kodcu")
    assert card["completed"] >= 1 and card["revisions"] >= 1 and card["first_pass_rate"] < 1
    assert card["autonomy_rate"] == 1.0  # insan revizyon istemedi (yalnızca kontrol personeli)
    assert card["credits"] > 0 and card["avg_hours"] is not None
    assert not any(a["name"] == "Kontrolcu" and a["completed"] for a in d["agents"])  # kontrol personelinin kendi adımı yok

    # ROI: en az 3 insanın günlük maliyeti tanımlı değilse gösterilmez (KVKK)
    _exec(db, "UPDATE actors SET daily_cost_try = NULL WHERE tenant_id = %s", w["tenant"])
    _exec(db, "UPDATE actors SET daily_cost_try = 3000 WHERE id = %s", w["admin"]["id"])
    roi = client.get(url, headers=admin).json()["roi"]
    assert roi["available"] is False and "KVKK" in roi["reason"]
    _exec(db, "UPDATE actors SET daily_cost_try = 2000 WHERE id IN (%s, %s)", w["member"]["id"], w["outsider"]["id"])
    d = client.get(url, headers=admin).json()
    roi = d["roi"]
    expected = round(roi["work_days"] * (7000 / 3) - roi["ai_cost"], 2)
    assert roi["available"] is True and abs(roi["saving"] - expected) < 0.05 and roi["rated_humans"] == 3
    text = json.dumps(d)
    # Kişi başı ücret alanı dönmez; ortalama yalnızca en az 3 kişiden hesaplanır (tutarlar toplam/proje/adım düzeyinde)
    assert "daily_cost" not in text and "labor_rate" not in text and "avg_rate" not in text
    _exec(db, "UPDATE actors SET daily_cost_try = NULL WHERE tenant_id = %s", w["tenant"])
    client.post(f"/api/v1/projects/{pid}/status", headers=admin, json={"action": "cancel"})


def test_department_dashboard(client, db, world):
    """ADIM 9.3: departman panosu yetkisi kendi departmanıyla sınırlı; parasal bilgi ayrıca billing:view ister."""
    w = world
    tid = w["tenant"]
    url = f"/api/v1/company/{tid}/dashboard"
    dept_a = str(_exec(db, "INSERT INTO departments (id, tenant_id, name) VALUES (gen_random_uuid(), %s, 'Satış') RETURNING id", tid)[0])
    dept_b = str(_exec(db, "INSERT INTO departments (id, tenant_id, name) VALUES (gen_random_uuid(), %s, 'Üretim') RETURNING id", tid)[0])
    pid, human_id, _ = _ready_project(client, w, "Satış Projesi")
    other, _, _ = _ready_project(client, w, "Üretim Projesi")
    _exec(db, "UPDATE projects SET department_id = %s WHERE id = %s", dept_a, pid)
    _exec(db, "UPDATE projects SET department_id = %s WHERE id = %s", dept_b, other)
    member = w["member"]
    try:
        assert client.get(url, headers=member["h"]).status_code == 403  # yetki yok
        _exec(db, "UPDATE actors SET extra_permissions = '[\"department:dashboard\"]'::jsonb, department_id = NULL WHERE id = %s", member["id"])
        r = client.get(url, headers=member["h"])
        assert r.status_code == 403 and "Departmanınız tanımlı değil" in r.json()["detail"]
        _exec(db, "UPDATE actors SET department_id = %s WHERE id = %s", dept_a, member["id"])
        r = client.get(url, headers=member["h"])
        assert r.status_code == 200, r.text
        d = r.json()
        names = {p["name"] for p in (d.get("costs") or {}).get("projects", [])}
        assert d["department_locked"] is True and d["department_name"] == "Satış" and d["can_view_costs"] is False
        assert d["costs"] is None and d["roi"] is None and d["credits"] is None and not names
        assert all("cost" not in x for x in d["series"]) and all("cost" not in a for a in d["agents"])
        assert d["projects"]["total"] == 1  # yalnızca Satış projesi
        me = next(p for p in d["people"] if p["actor_id"] == member["id"])
        assert me["open"] >= 1  # Satış projesindeki insan adımı
        assert client.get(f"{url}?department_id={dept_b}", headers=member["h"]).status_code == 403
        # billing:view ile parasal bilgi de görünür
        _exec(db, "UPDATE actors SET extra_permissions = '[\"department:dashboard\", \"billing:view\"]'::jsonb WHERE id = %s", member["id"])
        d = client.get(url, headers=member["h"]).json()
        assert d["can_view_costs"] is True and {p["name"] for p in d["costs"]["projects"]} == {"Satış Projesi"}
        # Şirket yöneticisi istediği departmanı seçer
        d = client.get(f"{url}?department_id={dept_b}", headers=w["admin"]["h"]).json()
        assert d["department_locked"] is False and {p["name"] for p in d["costs"]["projects"]} == {"Üretim Projesi"}
    finally:
        _exec(db, "UPDATE actors SET extra_permissions = '[]'::jsonb, department_id = NULL WHERE id = %s", member["id"])


def _super(client, db):
    tag = uuid.uuid4().hex[:6]
    hq = _exec(db, "SELECT id FROM tenants WHERE slug = 'recdx_hq'")[0]
    email = f"plat_super_{tag}@recdx.com"
    _exec(db, "INSERT INTO actors (tenant_id, actor_type, display_name, email, role, password_hash, status) "
              "VALUES (%s, 'HUMAN', 'Süper', %s, 'SUPER_ADMIN', %s, 'IDLE')", hq, email, hash_password(PASSWORD))
    return _login(client, email)


def test_platform_dashboard_and_health(client, db, world, monkeypatch):
    """ADIM 9.4: Süper Admin panosu (platform sayıları, LLM sağlığı) ve gerçek sağlık kontrolü; şirket yöneticisine kapalı."""
    from app.config import settings
    from app.services import platform_health
    from app.services.evren_client import evren_client
    w = world
    sa = _super(client, db)
    for status, latency, out in (("SUCCESS", 1000, 100), ("SUCCESS", 3000, 300), ("FAILED", 5000, 0)):
        _exec(db, "INSERT INTO llm_calls (id, tenant_id, purpose, model_code, tokens_in, tokens_out, credits_cost, latency_ms, status, created_at) "
                  "VALUES (gen_random_uuid(), %s, 'AGENT_CHAT', 'saglik-model', 100, %s, 1, %s, %s, now())", w["tenant"], out, latency, status)
    r = client.get("/api/v1/system/dashboard?days=7", headers=sa)
    assert r.status_code == 200, r.text
    d = r.json()
    m = next(x for x in d["llm"]["models"] if x["model_code"] == "saglik-model")
    assert m["calls"] == 3 and m["failed"] == 1 and abs(m["fail_rate"] - 0.333) < 0.01
    assert m["p50_ms"] == 2000 and m["tokens_per_sec"] == 100.0
    assert len(d["llm"]["series"]) == 7 and d["tenants"]["total"] >= 1
    assert any(u["tenant_id"] == w["tenant"] for u in d["usage_by_tenant"])
    assert client.get("/api/v1/system/dashboard", headers=w["admin"]["h"]).status_code == 403  # yalnızca Süper Admin

    async def models():
        return [{"id": "x"}]
    monkeypatch.setattr(evren_client, "list_models", models)
    h = client.get("/api/v1/system/health?refresh=true", headers=sa)
    assert h.status_code == 200
    services = {s["key"]: s for s in h.json()["services"]}
    assert services["postgres"]["status"] in ("OK", "SLOW") and services["redis"]["status"] in ("OK", "SLOW")
    assert services["odoo"]["status"] == "OFF"  # testlerde Odoo eşitlemesi kapalı
    text = h.text
    for secret in (settings.SECRET_KEY, settings.GITEA_TOKEN, settings.EVREN_API_KEY, settings.MINIO_ROOT_PASSWORD):
        assert not secret or secret not in text
    assert client.get("/api/v1/system/health", headers=w["admin"]["h"]).status_code == 403
    platform_health._cache.update(at=0.0, data=None)
