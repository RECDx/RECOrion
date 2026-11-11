"""
Aşama 2 Tur 2 (maliyet tutarlılığı): F69, F71, F74, F112, F113.

- Simülasyonun adım kredisi tahmini Maliyet'e taşınır (plan kredisi, adım plan kredisi); geçmiş başlangıç tarihi risk olarak uyarılır.
- Proje tamamlanınca açık kalan adımlar iptal edilir; maliyette "İptal" görünür, insan eşdeğerine girmez.
- Fark = bütçe − gerçekleşen.
"""
from datetime import date, timedelta

from tests.test_workflow import _ready_project, _wait, world  # noqa: F401  (fikstür)


def test_cost_consistency(client, world):  # noqa: F811
    w = world
    admin = w["admin"]["h"]
    pid, human_id, dep_id = _ready_project(client, w, "Maliyet Tutarlılığı")
    try:
        past = (date.today() - timedelta(days=20)).isoformat()
        sim = client.post(f"/api/v1/projects/{pid}/simulate", headers=admin, json={"start_date": past})
        assert sim.status_code == 200, sim.text
        assert any("geçmişte" in r["text"] for r in sim.json()["risks"]), sim.json()["risks"]
        sim = client.post(f"/api/v1/projects/{pid}/simulate", headers=admin, json={"start_date": date.today().isoformat()}).json()
        assert not any("geçmişte" in r["text"] for r in sim["risks"])
        c = client.get(f"/api/v1/projects/{pid}/costs", headers=admin).json()
        assert c["totals"]["planned_credits"] > 0 and abs(c["totals"]["planned_credits"] - sim["estimated_credits"]) < 0.01
        assert all(r["estimated_credits"] is not None for r in c["tasks"])
        if c["totals"]["credit_unit_try"] is not None:
            assert c["totals"]["planned_ai_try"] > 0 and c["planned"]["credits"] > 0

        assert client.post(f"/api/v1/projects/{pid}/status", headers=admin, json={"action": "start"}).status_code == 200
        _wait(client, admin, pid, lambda t, f: t["İnsan adımı"]["status"] == "IN_PROGRESS", "başlamalı")
        assert client.put(f"/api/v1/projects/{pid}/budget", headers=admin, json={"budget_try": -5}).status_code == 422
        r = client.put(f"/api/v1/projects/{pid}/budget", headers=admin, json={"budget_try": -5})
        assert "eksi olamaz" in r.text
        assert client.put(f"/api/v1/projects/{pid}/budget", headers=admin, json={"budget_try": 5000}).status_code == 200
        r = client.post(f"/api/v1/projects/{pid}/status", headers=admin, json={"action": "complete", "summary": "Erken kapanış"})
        assert r.status_code == 200, r.text
        c = client.get(f"/api/v1/projects/{pid}/costs", headers=admin).json()
        rows = {x["title"]: x for x in c["tasks"]}
        assert rows["Bağımlı adım"]["status"] == "CANCELLED" and rows["Bağımlı adım"]["labor"]["basis"] == "CANCELLED"
        assert rows["İnsan adımı"]["status"] == "CANCELLED" and rows["İnsan adımı"]["in_scope"] is False
        assert all(x["labor"]["basis"] not in ("RUNNING", "PLANNED") for x in c["tasks"] if x["status"] == "CANCELLED")
        assert c["totals"]["human_days"] == sum(x["human"]["days"] for x in c["tasks"] if x["in_scope"])
        t = c["totals"]
        assert abs(t["budget_variance"] - (5000 - t["actual"])) < 0.011
    finally:
        client.post(f"/api/v1/projects/{pid}/status", headers=admin, json={"action": "cancel"})
