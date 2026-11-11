"""
Aşama 2 bulguları F92 ve F110: proje yöneticisinin plan onayından sonra adım üzerindeki denetimi.

- F92: adımın kontrol personeli değiştirilir/kaldırılır, onaylayıcı değiştirilir, başlamamış adımın AI personeli değişir;
  kontrol personeli işi yapanla aynı olamaz; yalnız proje yöneticisi; geçmişe PEOPLE_CHANGED yazılır.
- F110: sıradaki ya da çalışan gereksiz adım gerekçeyle iptal edilir (yalnız karantinada değil); başlamamış adım hemen kapanır,
  çalışan adım akışına iptal sinyali gider.
"""
from tests.test_workflow import _flow, _ready_project, _wait, world  # noqa: F401  (fikstür)


def test_people_and_cancel(client, world):  # noqa: F811
    w = world
    admin, member = w["admin"]["h"], w["member"]["h"]
    pid, human_id, dep_id = _ready_project(client, w, "Adım Denetimi Projesi")
    try:
        assert client.post(f"/api/v1/projects/{pid}/status", headers=admin, json={"action": "start"}).status_code == 200
        _wait(client, admin, pid, lambda t, f: t["İnsan adımı"]["status"] == "IN_PROGRESS", "insan adımı başlamalı")
        # F92: kişiler
        assert client.get(f"/api/v1/tasks/{dep_id}/people", headers=member).status_code == 403
        opts = client.get(f"/api/v1/tasks/{dep_id}/people", headers=admin).json()
        assert "reviewers" in opts, opts
        assert opts["can_change_assignee"] is True and any(a["id"] == w["reviewer"] for a in opts["reviewers"])
        assert all(a["id"] != w["agent"] for a in opts["reviewers"])  # işi yapan kendini kontrol edemez
        put = lambda tid, body, h=admin: client.put(f"/api/v1/tasks/{tid}/people", headers=h, json=body)  # noqa: E731
        assert put(dep_id, {"reviewer_actor_id": w["reviewer"]}, member).status_code == 403
        assert put(dep_id, {"reviewer_actor_id": w["agent"]}).status_code == 422
        r = put(dep_id, {"reviewer_actor_id": w["reviewer"], "note": "BT Müdürü kontrol etsin"})
        assert r.status_code == 200 and r.json()["changed"] is True, r.text
        flow = _flow(client, admin, pid)
        dep = next(t for t in flow["tasks"] if t["id"] == dep_id)
        assert dep["reviewer"]["id"] == w["reviewer"] and dep["can_edit_people"] and dep["can_cancel"]
        assert any(e["kind"] == "PEOPLE_CHANGED" and e["task_id"] == dep_id and "BT Müdürü" in (e["note"] or "") for e in flow["events"])
        assert put(dep_id, {"reviewer_actor_id": None}).json()["changed"] is True  # kontrol personeli kaldırılır
        # Başlamış adımın personeli buradan değişmez
        assert put(human_id, {"assignee_actor_id": w["agent"]}).status_code in (409, 422)
        # F110: gerekçesiz iptal yok; sıradaki adım hemen kapanır; çalışan adıma iptal iletilir
        assert client.post(f"/api/v1/tasks/{dep_id}/cancel", headers=admin, json={"note": ""}).status_code == 422
        assert client.post(f"/api/v1/tasks/{dep_id}/cancel", headers=member, json={"note": "gereksiz"}).status_code == 403
        r = client.post(f"/api/v1/tasks/{dep_id}/cancel", headers=admin, json={"note": "Testler geçti, gereksiz"})
        assert r.status_code == 200 and r.json()["state"] == "CANCELLED", r.text
        r = client.post(f"/api/v1/tasks/{human_id}/cancel", headers=admin, json={"note": "Bu iş dışarıda yapıldı"})
        assert r.status_code == 200 and r.json()["state"] == "REQUESTED", r.text
        t, f = _wait(client, admin, pid, lambda t, f: t["İnsan adımı"]["status"] == "CANCELLED", "çalışan adım iptal olmalı")
        assert t["Bağımlı adım"]["status"] == "CANCELLED"
        assert client.post(f"/api/v1/tasks/{dep_id}/cancel", headers=admin, json={"note": "x"}).status_code == 409
    finally:
        client.post(f"/api/v1/projects/{pid}/status", headers=admin, json={"action": "cancel"})
