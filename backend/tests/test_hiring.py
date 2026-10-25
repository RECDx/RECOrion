"""
ADIM 5.3: AI personel işe alım akışı (Sektör > Departman > Unvan > LLM > Rol promptu).
"""
import json
import uuid

import pytest

from app.core.security import hash_password
from tests.test_catalog import _title, run_loader

PASSWORD = "Ise-Alim-Testi-2026"


def _exec(db, sql, *params):
    with db.cursor() as cur:
        cur.execute(sql, params)
        return cur.fetchone() if cur.description else None


@pytest.fixture(scope="module")
def tag():
    return uuid.uuid4().hex[:6].upper()


@pytest.fixture(scope="module")
def catalog(test_db_url, tmp_path_factory, tag):
    d = tmp_path_factory.mktemp("hire_catalog")
    prompt = "Sen {{company_name}} şirketinin {{department_name}} biriminde çalışan bir test uzmanısın."
    (d / "sector_A.json").write_text(json.dumps({"scope": "SECTOR", "sector_code": "A", "departments": [
        {"code": f"A_H{tag}", "name": f"Mobilya Üretim {tag}", "description": "x", "professions": ["A.06"], "titles": [
            _title(f"A_H{tag}_PLAN", professions=["A.06"], recommended_model_code="mimo-v2.6-pro", role_prompt=prompt),
            _title(f"A_H{tag}_STOK", professions=["A.06"], recommended_model_code="deepseek-v4-flash", role_prompt=prompt),
            _title(f"A_H{tag}_KERESTE", professions=["A.02"], role_prompt=prompt),
        ]},
    ]}), encoding="utf-8")
    (d / "sector_B.json").write_text(json.dumps({"scope": "SECTOR", "sector_code": "B", "departments": [
        {"code": f"B_H{tag}", "name": f"Otel {tag}", "description": "y", "professions": [], "titles": [_title(f"B_H{tag}_OTEL")]},
    ]}), encoding="utf-8")
    run_loader(test_db_url, d)
    return d


@pytest.fixture(scope="module")
def company(client, db, tag, catalog):
    tid = _exec(db, "INSERT INTO tenants (id, slug, name, plan_id, is_active, sectors, professions) VALUES "
                    "(gen_random_uuid(), %s, %s, (SELECT id FROM plans WHERE code = 'STARTER'), TRUE, "
                    "'[\"A\"]'::jsonb, '[\"A.06\"]'::jsonb) RETURNING id", f"hire_{tag.lower()}", f"Ahşap {tag} Ltd")[0]
    email = f"hire_{tag.lower()}@hire-test.com.tr"
    _exec(db, "INSERT INTO actors (tenant_id, actor_type, display_name, email, role, password_hash, status) "
              "VALUES (%s, 'HUMAN', 'İK', %s, 'COMPANY_ADMIN', %s, 'IDLE')", tid, email, hash_password(PASSWORD))
    r = client.post("/api/v1/auth/login", json={"email": email, "password": PASSWORD})
    return {"id": str(tid), "headers": {"Authorization": f"Bearer {r.json()['access_token']}"}, "name": f"Ahşap {tag} Ltd"}


def _catalog_dept(client, company, tag):
    opts = client.get(f"/api/v1/company/{company['id']}/hire/options", headers=company["headers"]).json()
    return opts, next(d for d in opts["departments"] if d["name"] == f"Mobilya Üretim {tag}")


def test_options_and_titles(client, company, tag):
    opts, dept = _catalog_dept(client, company, tag)
    assert opts["sectors"][0]["code"] == "A" and dept["source"] == "CATALOG" and dept["profession_match"]
    assert opts["entitlements"]["can_change_llm"] is False
    assert all(not d["name"].startswith("Otel") for d in opts["departments"])  # başka sektör önerilmez
    titles = client.get(f"/api/v1/company/{company['id']}/hire/titles?catalog_department_id={dept['catalog_department_id']}",
                        headers=company["headers"]).json()
    assert sorted(t["title"] for t in titles) == sorted([f"A_H{tag}_PLAN Unvanı", f"A_H{tag}_STOK Unvanı"])  # A.02 elenir
    assert all(t["kind"] == "CATALOG" for t in titles)


def test_preview_renders_prompt_and_forced_model(client, company, tag):
    _, dept = _catalog_dept(client, company, tag)
    titles = client.get(f"/api/v1/company/{company['id']}/hire/titles?catalog_department_id={dept['catalog_department_id']}",
                        headers=company["headers"]).json()
    plan = next(t for t in titles if t["title"].startswith(f"A_H{tag}_PLAN"))
    p = client.get(f"/api/v1/company/{company['id']}/hire/preview?title_id={plan['id']}&department_name=Üretim",
                   headers=company["headers"]).json()
    assert p["role_prompt"] == f"Sen {company['name']} şirketinin Üretim biriminde çalışan bir test uzmanısın."
    # #349: unvanın önerisi (RECAi Derin) STARTER paketinde yok: RECAi Mergen kullanılır
    assert p["recommended_model_code"] is None and p["model_code"] == "MERGEN"


def test_hire_from_catalog_adopts_department_and_title(client, db, company, tag):
    _, dept = _catalog_dept(client, company, tag)
    titles = client.get(f"/api/v1/company/{company['id']}/hire/titles?catalog_department_id={dept['catalog_department_id']}",
                        headers=company["headers"]).json()
    stok = next(t for t in titles if t["title"].startswith(f"A_H{tag}_STOK"))
    body = {"display_name": "Stok Asistanı", "catalog_title_id": stok["id"], "catalog_department_id": dept["catalog_department_id"]}
    r = client.post(f"/api/v1/company/{company['id']}/ai-agents", json=body, headers=company["headers"])
    assert r.status_code in (200, 201), r.text
    agent = r.json()
    assert agent["department_name"] == f"Mobilya Üretim {tag}" and agent["model_code"] == "MERGEN" and agent["model_display_name"] == "RECAi Mergen"
    assert agent["system_prompt"] == f"Sen {company['name']} şirketinin Mobilya Üretim {tag} biriminde çalışan bir test uzmanısın."
    src = _exec(db, "SELECT source, source_title_id::text, tenant_id::text FROM job_titles WHERE id = %s", agent["job_title_id"])
    assert src == ("CATALOG", stok["id"], company["id"])

    # İkinci işe alım aynı şirket unvanını ve departmanını kullanır; sihirbaz artık bunları şirket kaydı olarak gösterir
    r = client.post(f"/api/v1/company/{company['id']}/ai-agents", json={**body, "display_name": "Stok Asistanı 2"}, headers=company["headers"])
    assert r.json()["job_title_id"] == agent["job_title_id"] and r.json()["department_id"] == agent["department_id"]
    assert _exec(db, "SELECT count(*) FROM departments WHERE tenant_id = %s", company["id"])[0] == 1
    opts = client.get(f"/api/v1/company/{company['id']}/hire/options", headers=company["headers"]).json()
    mine = [d for d in opts["departments"] if d["name"] == f"Mobilya Üretim {tag}"]
    assert len(mine) == 1 and mine[0]["source"] == "COMPANY"
    titles = client.get(f"/api/v1/company/{company['id']}/hire/titles?department_id={mine[0]['department_id']}",
                        headers=company["headers"]).json()
    assert [t["kind"] for t in titles].count("COMPANY") == 1 and len(titles) == 2


def test_package_rules_enforced(client, company, tag, db):
    _, dept = _catalog_dept(client, company, tag)
    other = _exec(db, "SELECT id::text FROM job_titles WHERE code = %s AND tenant_id IS NULL", f"B_H{tag}_OTEL")[0]
    r = client.post(f"/api/v1/company/{company['id']}/ai-agents", json={"display_name": "Otelci", "catalog_title_id": other},
                    headers=company["headers"])
    assert r.status_code == 422  # şirketin sektörü dışında
    plan = _exec(db, "SELECT id::text FROM job_titles WHERE code = %s AND tenant_id IS NULL", f"A_H{tag}_PLAN")[0]
    base = {"display_name": "Planlamacı", "catalog_title_id": plan}
    assert client.post(f"/api/v1/company/{company['id']}/ai-agents", json={**base, "model_code": "gemma-4-31b"},
                       headers=company["headers"]).status_code == 403  # LLM değiştirme izni yok
    assert client.post(f"/api/v1/company/{company['id']}/ai-agents", json={**base, "system_prompt": "Sen başka bir şeysin."},
                       headers=company["headers"]).status_code == 403  # rol promptu değiştirme izni yok
