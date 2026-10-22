"""
ADIM 7.4: Akış editörü ayarları plan adımında saklanır, onayda iş adımına aktarılır ve iş akışı bunlara uyar
(gerçek Temporal; EVREN ve nesne deposu sahte).

- Onaylayıcı: proje yöneticisi yerine seçilen insan personel; onay isteği ona gider, kararı o verir.
- "Onay gerekmez": AI çıktısı doğrudan tamamlanır.
- Ret sınırı: 1 seçildiyse ilk retle karantina.
- Şema konumu (pos) ve geçersiz değerlerin temizlenmesi.
"""
import re

from app.services import notification_service as ns
from tests.test_approvals import _until
from tests.test_workflow import _exec, _wait, ai, world  # noqa: F401  (fikstürler)


def test_flow_settings_applied(client, db, world, ai):
    w = world
    admin, member = w["admin"]["h"], w["member"]["h"]
    pid = client.post("/api/v1/projects", headers=admin, json={"tenant_id": w["tenant"], "name": "Akış Ayarları", "requirements": "x"}).json()["id"]
    steps = [
        {"key": "A", "title": "Uzman onaylı adım", "agent_id": w["agent"], "approver_actor_id": w["member"]["id"], "max_rejections": 1,
         "pos": {"x": 10.123, "y": 20}},
        {"key": "B", "title": "Onaysız adım", "agent_id": w["agent"], "requires_approval": False, "depends_on": ["A"]},
        {"key": "C", "title": "Geçersiz ayarlı adım", "agent_id": w["agent"], "approver_actor_id": w["agent"],  # AI onaylayıcı olamaz
         "max_rejections": 99, "pos": {"x": "a"}},
    ]
    r = client.put(f"/api/v1/projects/{pid}/plan", headers=admin, json={"summary": "s", "steps": steps})
    assert r.status_code == 200, r.text
    saved = {s["key"]: s for s in r.json()["steps"]}
    assert saved["A"]["approver_actor_id"] == w["member"]["id"] and saved["A"]["max_rejections"] == 1 and saved["A"]["pos"] == {"x": 10.1, "y": 20.0}
    assert saved["B"]["requires_approval"] is False and saved["B"]["max_rejections"] == 3
    assert saved["C"]["approver_actor_id"] is None and saved["C"]["max_rejections"] == 5 and saved["C"]["pos"] is None

    assert client.post(f"/api/v1/projects/{pid}/plan/approve", headers=admin).status_code == 200
    tasks = {t["title"]: t for t in client.get(f"/api/v1/projects/{pid}/tasks", headers=admin).json()}
    assert tasks["Uzman onaylı adım"]["approver_actor_id"] == w["member"]["id"] and tasks["Uzman onaylı adım"]["max_rejections"] == 1
    assert tasks["Onaysız adım"]["requires_approval"] is False
    members = {m["actor_id"]: m["role"] for m in client.get(f"/api/v1/projects/{pid}", headers=admin).json()["members"]}
    assert w["member"]["id"] in members  # onaylayıcı ekibe eklendi

    start = "2026-11-02"
    client.put(f"/api/v1/projects/{pid}", headers=admin, json={"start_date": start, "end_date": "2026-11-30"})
    assert client.post(f"/api/v1/projects/{pid}/status", headers=admin, json={"action": "mark_ready"}).status_code == 200
    assert client.post(f"/api/v1/projects/{pid}/status", headers=admin, json={"action": "start"}).status_code == 200

    # Onay isteği seçilen onaylayıcıya (uzman) gider; karar onun
    flow_tasks, _ = _wait(client, admin, pid, lambda t, f: t["Uzman onaylı adım"]["status"] == "WAITING_APPROVAL", "A onaya gelmeli")
    a = flow_tasks["Uzman onaylı adım"]
    assert a["approver"]["id"] == w["member"]["id"]
    member_email = _exec(db, "SELECT email FROM actors WHERE id = %s", w["member"]["id"])[0]
    _until(lambda: any(m["to"] == member_email and "Uzman onaylı adım" in m["subject"] for m in ns.OUTBOX), "uzmana onay e-postası")
    member_view = {t["title"]: t for t in client.get(f"/api/v1/projects/{pid}/workflow", headers=member).json()["tasks"]}
    assert member_view["Uzman onaylı adım"]["can_decide"]
    queue = client.get("/api/v1/me/approvals", headers=member).json()
    assert any(q["task_id"] == a["id"] for q in queue)

    # Ret sınırı 1: ilk retle karantina
    assert client.post(f"/api/v1/tasks/{a['id']}/decision", headers=member, json={"approve": False, "note": "Eksik"}).status_code == 200
    _wait(client, admin, pid, lambda t, f: t["Uzman onaylı adım"]["status"] == "QUARANTINED", "tek retle karantina")
    def approval_mails():
        return [m for m in ns.OUTBOX if m["to"] == member_email and "Uzman onaylı adım" in m["subject"]]
    sent_before = len(approval_mails())  # yeniden denemeden önce
    assert client.post(f"/api/v1/tasks/{a['id']}/release", headers=admin, json={"action": "retry"}).status_code == 200
    _wait(client, admin, pid, lambda t, f: t["Uzman onaylı adım"]["status"] == "WAITING_APPROVAL", "yeniden onaya gelmeli")
    _until(lambda: len(approval_mails()) > sent_before, "yeni teslim için yeni onay e-postası")
    link = [m for m in ns.OUTBOX if m["to"] == member_email and "Uzman onaylı adım" in m["subject"]][-1]
    raw = re.search(r"#/approve\?token=([A-Za-z0-9_-]+)", link["html"]).group(1)
    assert client.post(f"/api/v1/approvals/{raw}", json={"approve": True}).status_code == 200

    # Onaysız adım: AI çıktısı doğrudan tamamlanır (onay isteği yok)
    flow_tasks, flow = _wait(client, admin, pid, lambda t, f: t["Onaysız adım"]["status"] == "DONE", "B onaysız tamamlanmalı")
    b_events = [e["kind"] for e in flow["events"] if e["task_id"] == flow_tasks["Onaysız adım"]["id"]]
    assert "AI_OUTPUT" in b_events and "APPROVED" not in b_events and "DONE" in b_events
    client.post(f"/api/v1/projects/{pid}/status", headers=admin, json={"action": "cancel"})
