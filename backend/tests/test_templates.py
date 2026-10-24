"""
ADIM 11.1: proje şablonları (şirket içi + RECDx platform şablonları).

- RECDx şablonları açılışta yüklenir, herkes görür; Süper Admin yayımlar/arşivler, şirket düzenleyemez.
- Projeden şirket şablonu: yalnızca proje yöneticisi; kişi kimlikleri (AI/insan/kontrol/onaylayıcı) şablona girmez.
- Şirket şablonu KVKK gereği RECDx'e görünmez.
- Şablondan proje: plan taslak, unvanı uyan AI personel eşleşir, eşleşmeyen rol için işe alım önerisi; kullanım sayılır.
- Arşivlenen şablon listelenmez ve kullanılamaz.
"""
import json

from tests.test_integrations import _super
from tests.test_workflow import _exec, world  # noqa: F401  (fikstür)


def _seed(client):
    from app.db.session import AsyncSessionLocal
    from app.services.project_templates import ensure_platform_templates

    async def go():
        async with AsyncSessionLocal() as s:
            return await ensure_platform_templates(s)
    return client.portal.call(go)


def test_platform_templates_seeded_and_managed(client, db, world):
    w = world
    member = w["member"]["h"]
    first = _seed(client)
    assert _seed(client) == 0  # yalnızca eksikler eklenir (ikinci açılışta hiçbir şey)
    assert first in (0, 6)
    lst = client.get("/api/v1/project-templates", headers=member).json()
    codes = {t["name"] for t in lst if t["scope"] == "PLATFORM"}
    assert {"KVKK uyum projesi", "Müşteri şikâyeti vakası"} <= codes
    kvkk = next(t for t in lst if t["name"] == "KVKK uyum projesi")
    assert kvkk["step_count"] == 6 and kvkk["total_days"] > 0 and "Uyum Uzmanı" in kvkk["roles"]
    full = client.get(f"/api/v1/project-templates/{kvkk['id']}", headers=member).json()
    assert all("agent_id" not in s for s in full["plan"]["steps"])
    assert client.put(f"/api/v1/project-templates/{kvkk['id']}", headers=w["admin"]["h"], json={"name": "Benim"}).status_code == 403

    sa = _super(client, db)
    assert client.get("/api/v1/system/project-templates", headers=member).status_code == 403
    plan = {"summary": "Deneme", "steps": [{"key": "A", "title": "Analiz", "job_title": "Analist", "estimated_days": 2},
                                           {"key": "B", "title": "Uygulama", "depends_on": ["A"], "agent_id": "kimse"}]}
    r = client.post("/api/v1/system/project-templates", headers=sa, json={"name": "Deneme şablonu", "category": "Test", "plan": plan})
    assert r.status_code == 201, r.text
    t = r.json()
    assert t["scope"] == "PLATFORM" and t["total_days"] == 3.0 and "agent_id" not in json.dumps(t["plan"])
    assert any(x["id"] == t["id"] for x in client.get("/api/v1/project-templates", headers=member).json())
    assert client.put(f"/api/v1/system/project-templates/{t['id']}", headers=sa, json={"status": "ARCHIVED"}).status_code == 200
    assert not any(x["id"] == t["id"] for x in client.get("/api/v1/project-templates", headers=member).json())
    assert client.post(f"/api/v1/project-templates/{t['id']}/use", headers=w["admin"]["h"], json={"name": "Arşivden"}).status_code == 409


def test_company_template_from_project_and_reuse(client, db, world):
    w = world
    admin, member = w["admin"]["h"], w["member"]["h"]
    title = _exec(db, "SELECT role FROM actors WHERE id = %s", w["agent"])[0]
    pid = client.post("/api/v1/projects", headers=admin, json={"tenant_id": w["tenant"], "name": "Kaynak proje"}).json()["id"]
    assert client.post(f"/api/v1/projects/{pid}/save-as-template", headers=admin, json={"name": "Boş"}).status_code == 409  # plan yok
    steps = [{"key": "S1", "title": "Analiz", "job_title": title, "agent_id": w["agent"], "reviewer_agent_id": w["reviewer"],
              "approver_actor_id": w["admin"]["id"], "estimated_days": 2, "description": "ACME müşterisine özel not"},
             {"key": "S2", "title": "Hukuk kontrolü", "job_title": "Hukuk Müşaviri", "depends_on": ["S1"], "estimated_days": 1,
              "requires_approval": False}]
    assert client.put(f"/api/v1/projects/{pid}/plan", headers=admin, json={"summary": "Özet", "steps": steps}).status_code == 200
    assert client.post(f"/api/v1/projects/{pid}/save-as-template", headers=member, json={"name": "Yetkisiz kayıt"}).status_code in (403, 404)
    r = client.post(f"/api/v1/projects/{pid}/save-as-template", headers=admin,
                    json={"name": "Analiz + hukuk", "category": "Danışmanlık", "keep_descriptions": False})
    assert r.status_code == 201, r.text
    tpl = r.json()
    dumped = json.dumps(tpl["plan"])
    assert tpl["scope"] == "COMPANY" and w["agent"] not in dumped and w["reviewer"] not in dumped and w["admin"]["id"] not in dumped
    assert "ACME" not in dumped  # açıklamalar alınmadı
    assert tpl["plan"]["steps"][1]["requires_approval"] is False and tpl["plan"]["steps"][1]["depends_on"] == ["S1"]

    # Şirket içinde görünür; RECDx'e görünmez (KVKK)
    assert any(t["id"] == tpl["id"] for t in client.get("/api/v1/project-templates", headers=member).json())
    sa = _super(client, db)
    assert not any(t["id"] == tpl["id"] for t in client.get("/api/v1/project-templates", headers=sa).json())
    assert client.get(f"/api/v1/project-templates/{tpl['id']}", headers=sa).status_code == 404
    assert client.put(f"/api/v1/system/project-templates/{tpl['id']}", headers=sa, json={"status": "ARCHIVED"}).status_code == 404

    # Şablondan yeni proje: plan taslak, unvanı uyan AI personel eşleşir, eşleşmeyen rol işe alım önerisi
    assert client.post(f"/api/v1/project-templates/{tpl['id']}/use", headers=member, json={"name": "Yetkisiz"}).status_code == 403
    r = client.post(f"/api/v1/project-templates/{tpl['id']}/use", headers=admin, json={"name": "Şablondan proje"})
    assert r.status_code == 200, r.text
    new = r.json()
    assert new["matched_steps"] == 1 and new["unmatched_roles"] == ["Hukuk Müşaviri"]
    p = client.get(f"/api/v1/projects/{new['id']}", headers=admin).json()
    assert p["plan"]["approved"] is False and p["plan"]["from_template"]["name"] == "Analiz + hukuk"
    assert p["plan"]["steps"][0]["agent_id"] == w["agent"] and p["plan"]["steps"][1]["agent_id"] is None
    assert p["plan"]["hire_suggestions"][0]["job_title"] == "Hukuk Müşaviri"
    assert client.post(f"/api/v1/projects/{new['id']}/plan/approve", headers=admin).status_code == 200
    assert next(t for t in client.get("/api/v1/project-templates", headers=admin).json() if t["id"] == tpl["id"])["use_count"] == 1

    assert client.put(f"/api/v1/project-templates/{tpl['id']}", headers=member, json={"status": "ARCHIVED"}).status_code == 403
    assert client.put(f"/api/v1/project-templates/{tpl['id']}", headers=admin, json={"status": "ARCHIVED"}).status_code == 200
    assert not any(t["id"] == tpl["id"] for t in client.get("/api/v1/project-templates", headers=admin).json())
