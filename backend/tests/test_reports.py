"""
İSTEK #744: Beyin AI ile rapor (tablo/grafik/pivot) + Merkez k ayarı ve baskınlık kuralı.

- Şirket raporu kullanıcının rolüyle süzülür: üye yalnız ekibindeki projeyi görür; kredi raporu billing:view ister.
- Zaman serisi sütun grafik, iki boyut pivot; katalog dışı rapor reddedilir; RECDx şirket raporunu çalıştıramaz (KVKK).
- Beyin yanıtındaki ```rapor``` bloğu ayıklanır; Beyin istemine yalnız kullanıcının yetkisindeki raporlar yazılır.
- Merkez: k eşiği ayarlanır; k'dan az şirket ya da tek şirket baskınsa satır gizlenir.
"""
import uuid

from app.services import reports as rs
from tests.test_integrations import _super
from tests.test_workflow import _exec, world  # noqa: F401  (fikstür)


def _run(client, w, h, **spec):
    return client.post(f"/api/v1/company/{w['tenant']}/reports/run", headers=h, json=spec)


def test_company_reports_role_scoped(client, db, world):
    w = world
    admin, member = w["admin"]["h"], w["member"]["h"]
    mine = client.post("/api/v1/projects", headers=admin, json={"tenant_id": w["tenant"], "name": "Rapor A"}).json()["id"]
    other = client.post("/api/v1/projects", headers=admin, json={"tenant_id": w["tenant"], "name": "Rapor B"}).json()["id"]
    _exec(db, "INSERT INTO project_members (id, project_id, actor_id, role, created_at) VALUES (gen_random_uuid(), %s, %s, 'MEMBER', now())",
          mine, w["member"]["id"])
    for pid, title in ((mine, "A1"), (mine, "A2"), (other, "B1")):
        assert client.post(f"/api/v1/projects/{pid}/tasks", headers=admin, json={"title": title, "assignee_actor_id": w["agent"]}).status_code in (200, 201)

    r = _run(client, w, admin, report="tasks", dims=["project"], measure="count")
    assert r.status_code == 200, r.text
    got = {x["keys"][0]: x["value"] for x in r.json()["rows"]}
    assert got["Rapor A"] == 2 and got["Rapor B"] == 1 and r.json()["chart"] == "bar"
    m = _run(client, w, member, report="tasks", dims=["project"]).json()
    assert {x["keys"][0] for x in m["rows"]} == {"Rapor A"}  # üye yalnız ekibindeki proje

    pv = _run(client, w, admin, report="tasks", dims=["project", "assignee_type"], chart="bar").json()
    assert pv["chart"] == "pivot" and pv["dim_labels"] == ["Proje", "Atanan türü"]

    _exec(db, "INSERT INTO llm_calls (id, tenant_id, purpose, credits_cost, latency_ms, status, created_at) "
              "VALUES (gen_random_uuid(), %s, 'TASK', 12.5, 900, 'SUCCESS', now())", w["tenant"])
    assert _run(client, w, member, report="ai_usage", dims=["month"]).status_code == 403  # kredi yetkisi yok
    u = _run(client, w, admin, report="ai_usage", dims=["month"], measure="credits").json()
    assert u["chart"] == "column" and sum(x["value"] for x in u["rows"]) >= 12.5
    assert _run(client, w, admin, report="uydurma").status_code == 422
    assert _run(client, w, _super(client, db), report="tasks").status_code == 403  # RECDx şirket içeriğini göremez
    cat = client.get(f"/api/v1/company/{w['tenant']}/reports/catalog", headers=member).json()
    assert "tasks" in {c["code"] for c in cat} and "ai_usage" not in {c["code"] for c in cat}


def test_report_block_extraction():
    text = 'İşte rapor.\n```rapor\n{"report": "tasks", "dims": ["status"], "chart": "bar"}\n```'
    assert rs.extract(text) == {"report": "tasks", "dims": ["status"], "chart": "bar"}
    assert rs.extract("rapor yok") is None
    assert rs.extract("```rapor\n{bozuk}\n```") is None
    assert "{" in rs.PROMPT.format(catalog="- x")  # biçim süslü parantezleri bozulmaz


def test_platform_k_and_dominance(client, db, world):
    sa = _super(client, db)
    assert client.get("/api/v1/system/privacy-settings", headers=sa).json()["k_min"] == 5
    assert client.put("/api/v1/system/privacy-settings", headers=sa, json={"k_min": 2, "dominance_pct": 60}).status_code == 422
    assert client.put("/api/v1/system/privacy-settings", headers=world["admin"]["h"], json={"k_min": 5, "dominance_pct": 60}).status_code == 403
    tenants = [str(_exec(db, "INSERT INTO tenants (id, slug, name, is_active) VALUES (gen_random_uuid(), %s, %s, TRUE) RETURNING id",
                         f"r_{uuid.uuid4().hex[:8]}", f"R Şirketi {i}")[0]) for i in range(5)]
    even, heavy, few = (f"{n} {uuid.uuid4().hex[:5]}" for n in ("Dengeli", "Baskın", "Az"))
    ins = ("INSERT INTO learning_records (id, tenant_id, source, label, job_title, data, lesson_status) "
           "VALUES (gen_random_uuid(), %s, 'APPROVAL', 'DOGRU', %s, '{}', 'NONE')")
    for t in tenants:
        _exec(db, ins, t, even)
        _exec(db, ins, t, heavy)
    for _ in range(10):
        _exec(db, ins, tenants[0], heavy)  # tek şirket %73 → baskın
    for t in tenants[:3]:
        _exec(db, ins, t, few)
    r = client.post("/api/v1/system/reports/run", headers=sa, json={"report": "platform_titles", "dims": ["job_title"]}).json()
    titles = {x["keys"][0] for x in r["rows"]}
    assert even in titles and heavy not in titles and few not in titles and r["hidden_groups"] >= 2
    assert client.put("/api/v1/system/privacy-settings", headers=sa, json={"k_min": 3, "dominance_pct": 80}).status_code == 200
    r = client.post("/api/v1/system/reports/run", headers=sa, json={"report": "platform_titles", "dims": ["job_title"]}).json()
    titles = {x["keys"][0] for x in r["rows"]}
    assert few in titles and heavy in titles  # k=3 → 3 şirketli görünür; baskın şirket payı 11/15=%73 < %80 → görünür
    client.put("/api/v1/system/privacy-settings", headers=sa, json={"k_min": 5, "dominance_pct": 60})
