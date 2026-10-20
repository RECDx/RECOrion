"""
ADIM 5.1: Platform departman/unvan kataloğu, yükleyici, yetkiler ve şirkete öneri.
"""
import asyncio
import json
import uuid

import pytest

from app.core.security import hash_password

PASSWORD = "Katalog-Testi-Sifresi-2026"


def _exec(db, sql, *params):
    with db.cursor() as cur:
        cur.execute(sql, params)
        return cur.fetchone() if cur.description else None


def _login(client, email):
    r = client.post("/api/v1/auth/login", json={"email": email, "password": PASSWORD})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def run_loader(db_url, directory):
    """Yükleyiciyi uygulamanın bağlantı havuzundan bağımsız, kendi event loop'unda çalıştırır."""
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
    from sqlalchemy.pool import NullPool
    from app.services.catalog_seed import load_catalog

    async def go():
        engine = create_async_engine(db_url, poolclass=NullPool)
        try:
            async with async_sessionmaker(engine)() as session:
                return await load_catalog(session, directory)
        finally:
            await engine.dispose()
    return asyncio.run(go())


def _title(code, **extra):
    return {"code": code, "title": f"{code} Unvanı", "seniority": "MID", "description": "İş tanımı.",
            "responsibilities": ["a"], "skills": ["b"], "kpis": ["c"], "professions": [],
            "recommended_model_code": "mimo-v2.6-pro", "autonomy_level": "L1",
            "role_prompt": "Sen {{company_name}} şirketinde çalışan bir test unvanısın.", **extra}


@pytest.fixture(scope="module")
def tag():
    return uuid.uuid4().hex[:6].upper()


@pytest.fixture(scope="module")
def seeded(test_db_url, tmp_path_factory, tag):
    """Geçici bir katalog klasörünü yükler: 1 genel departman + A sektörü departmanı ve GEN_ eki."""
    d = tmp_path_factory.mktemp("catalog")
    gen = f"GEN_T{tag}"
    (d / "general.json").write_text(json.dumps({"scope": "GENERAL", "sector_code": None, "departments": [
        {"code": gen, "name": f"Test Genel {tag}", "description": "x", "professions": [], "titles": [_title(f"GEN_T{tag}_UZMAN")]},
    ]}), encoding="utf-8")
    (d / "sector_A.json").write_text(json.dumps({"scope": "SECTOR", "sector_code": "A", "departments": [
        {"code": f"A_T{tag}", "name": f"Test Atölye {tag}", "description": "y", "professions": ["A.03", "X.99"],
         "titles": [_title(f"A_T{tag}_MARANGOZ", professions=["A.03"]), _title(f"A_T{tag}_KERESTE", professions=["A.02"])]},
        {"code": gen, "titles": [_title(f"A_T{tag}_SATIS")]},
    ]}), encoding="utf-8")

    first, second = run_loader(test_db_url, d), run_loader(test_db_url, d)
    return {"first": first, "second": second, "gen": gen}


@pytest.fixture(scope="module")
def super_headers(client, db, tag):
    hq = _exec(db, "SELECT id FROM tenants WHERE slug = 'recdx_hq'")[0]
    email = f"kat_super_{tag.lower()}@recdx.com"
    _exec(db, "INSERT INTO actors (tenant_id, actor_type, display_name, email, role, password_hash, status) "
              "VALUES (%s, 'HUMAN', 'Kat Super', %s, 'SUPER_ADMIN', %s, 'IDLE')", hq, email, hash_password(PASSWORD))
    return _login(client, email)


@pytest.fixture(scope="module")
def company(client, db, tag):
    tid = _exec(db, "INSERT INTO tenants (id, slug, name, is_active, sectors, professions) VALUES "
                    "(gen_random_uuid(), %s, 'Katalog Mobilya', TRUE, '[\"A\"]'::jsonb, '[\"A.03\"]'::jsonb) RETURNING id",
                f"kat_{tag.lower()}")[0]
    email = f"kat_admin_{tag.lower()}@kat-test.com.tr"
    _exec(db, "INSERT INTO actors (tenant_id, actor_type, display_name, email, role, password_hash, status) "
              "VALUES (%s, 'HUMAN', 'Kat Admin', %s, 'COMPANY_ADMIN', %s, 'IDLE')", tid, email, hash_password(PASSWORD))
    return {"id": str(tid), "headers": _login(client, email)}


def test_loader_adds_once_and_validates(db, seeded, tag):
    assert seeded["first"] == {"departments": 2, "titles": 4, "skipped_files": 0}
    assert seeded["second"] == {"departments": 0, "titles": 0, "skipped_files": 0}
    # Geçersiz meslek kodu atılır; GEN_ ekindeki sektör unvanı genel departmana sektör etiketiyle eklenir
    assert _exec(db, "SELECT profession_codes FROM catalog_departments WHERE code = %s", f"A_T{tag}")[0] == ["A.03"]
    assert _exec(db, "SELECT scope, sector_code, category FROM job_titles WHERE code = %s", f"A_T{tag}_SATIS") == \
        ("SECTOR", "A", f"Test Genel {tag}")


def test_admin_edits_survive_reload(db, seeded, tag, test_db_url, tmp_path):
    _exec(db, "UPDATE job_titles SET title = 'Düzenlenmiş' WHERE code = %s", f"GEN_T{tag}_UZMAN")
    (tmp_path / "general.json").write_text(json.dumps({"scope": "GENERAL", "departments": [
        {"code": seeded["gen"], "name": "x", "titles": [_title(f"GEN_T{tag}_UZMAN")]}]}), encoding="utf-8")
    assert run_loader(test_db_url, tmp_path)["titles"] == 0
    assert _exec(db, "SELECT title FROM job_titles WHERE code = %s", f"GEN_T{tag}_UZMAN")[0] == "Düzenlenmiş"


def test_catalog_read_and_filters(client, company, seeded, tag):
    h = company["headers"]
    titles = client.get(f"/api/v1/catalog/titles?sector_code=A&profession_code=A.03&search=T{tag}", headers=h).json()
    codes = {t["code"] for t in titles["items"]}
    assert f"A_T{tag}_MARANGOZ" in codes and f"A_T{tag}_KERESTE" not in codes and f"A_T{tag}_SATIS" in codes
    detail = client.get(f"/api/v1/catalog/titles/{titles['items'][0]['id']}", headers=h).json()
    assert detail["base_role_prompt"].startswith("Sen")
    summary = client.get("/api/v1/catalog/summary", headers=h).json()
    assert summary["total_titles"] >= 4


def test_catalog_write_requires_super_admin(client, company, super_headers, seeded, tag):
    dept = {"code": f"A_NEW{tag}", "name": f"Yeni {tag}", "sector_code": "A", "profession_codes": ["A.06"]}
    assert client.post("/api/v1/catalog/departments", json=dept, headers=company["headers"]).status_code == 403
    r = client.post("/api/v1/catalog/departments", json=dept, headers=super_headers)
    assert r.status_code == 201, r.text
    dept_id = r.json()["id"]
    title = {"code": f"A_NEW{tag}_UZMAN", "title": "Yeni Uzman", "catalog_department_id": dept_id,
             "base_role_prompt": "Sen yeni bir uzmansın, görevin test etmektir.", "seniority": "SENIOR"}
    r = client.post("/api/v1/catalog/titles", json=title, headers=super_headers)
    assert r.status_code == 201 and r.json()["sector_code"] == "A" and r.json()["category"] == f"Yeni {tag}"
    assert client.post("/api/v1/catalog/titles", json=title, headers=super_headers).status_code == 409
    assert client.delete(f"/api/v1/catalog/departments/{dept_id}", headers=super_headers).status_code == 409
    assert client.delete(f"/api/v1/catalog/titles/{r.json()['id']}", headers=super_headers).json()["deactivated"] is False
    assert client.delete(f"/api/v1/catalog/departments/{dept_id}", headers=super_headers).status_code == 200


def test_company_recommendation_and_import(client, db, company, seeded, tag):
    h = company["headers"]
    rec = client.get(f"/api/v1/company/{company['id']}/catalog/recommended", headers=h).json()
    by_code = {d["code"]: d for d in rec["departments"]}
    assert by_code[f"A_T{tag}"]["profession_match"] is True and by_code[f"A_T{tag}"]["title_count"] == 1  # A.02 unvanı elenir
    assert rec["departments"][0]["rank"] == 0
    ids = [by_code[f"A_T{tag}"]["id"], by_code[seeded["gen"]]["id"]]
    r = client.post(f"/api/v1/company/{company['id']}/departments/from-catalog", json={"catalog_department_ids": ids}, headers=h)
    assert sorted(r.json()["created"]) == sorted([f"Test Atölye {tag}", f"Test Genel {tag}"])
    r = client.post(f"/api/v1/company/{company['id']}/departments/from-catalog", json={"catalog_department_ids": ids}, headers=h)
    assert r.json()["created"] == []
    rec = client.get(f"/api/v1/company/{company['id']}/catalog/recommended", headers=h).json()
    assert {d["code"]: d for d in rec["departments"]}[f"A_T{tag}"]["imported"] is True
