"""
ADIM 7.1: Temporal iş akışı (gerçek Temporal sunucusu, test kuyruğu). Proje başlayınca akış başlar; bağımlılık sırası,
teslim, onay/ret, 3 ret sonrası karantina, yeniden deneme, iptal ve değiştirilemez olay geçmişi.
"""
import json
import time
import uuid
from datetime import date, timedelta

import psycopg2
import pytest

from app.core.security import hash_password

PASSWORD = "Akis-Testi-Sifresi-2026"


def _exec(db, sql, *params):
    with db.cursor() as cur:
        cur.execute(sql, params)
        return cur.fetchone() if cur.description else None


def _login(client, email):
    r = client.post("/api/v1/auth/login", json={"email": email, "password": PASSWORD})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.fixture(scope="module")
def world(client, db):
    tag = uuid.uuid4().hex[:6]
    tid = _exec(db, "INSERT INTO tenants (id, slug, name, plan_id, is_active) VALUES (gen_random_uuid(), %s, 'Akış Ltd', "
                    "(SELECT id FROM plans WHERE code = 'STARTER'), TRUE) RETURNING id", f"akis_{tag}")[0]

    def human(name, role):
        email = f"akis_{name}_{tag}@akis-test.com.tr"
        aid = _exec(db, "INSERT INTO actors (tenant_id, actor_type, display_name, email, role, password_hash, status) "
                        "VALUES (%s, 'HUMAN', %s, %s, %s, %s, 'IDLE') RETURNING id", tid, name, email, role, hash_password(PASSWORD))[0]
        return {"id": str(aid), "h": _login(client, email)}

    model = _exec(db, "SELECT id FROM llm_models WHERE model_code = 'deepseek-v4-flash'")[0]
    agent = str(_exec(db, "INSERT INTO actors (tenant_id, actor_type, display_name, role, status, preferred_model_id) "
                          "VALUES (%s, 'AI_AGENT', 'Kodcu', 'X', 'IDLE', %s) RETURNING id", tid, model)[0])
    return {"tenant": str(tid), "admin": human("Yonetici", "COMPANY_ADMIN"), "member": human("Uzman", "USER"),
            "outsider": human("Diger", "USER"), "agent": agent}


def _ready_project(client, w, name):
    """Plan onaylı (1 AI adımı) + insan adımı + bağımlı adım; başlamaya hazır proje."""
    h = w["admin"]["h"]
    pid = client.post("/api/v1/projects", headers=h, json={"tenant_id": w["tenant"], "name": name, "requirements": "Test isterleri"}).json()["id"]
    plan = {"summary": "s", "steps": [{"key": "S1", "title": "AI adımı", "estimated_days": 1, "agent_id": w["agent"]}]}
    assert client.put(f"/api/v1/projects/{pid}/plan", headers=h, json=plan).status_code == 200
    assert client.post(f"/api/v1/projects/{pid}/plan/approve", headers=h).status_code == 200
    human_task = client.post(f"/api/v1/projects/{pid}/tasks", headers=h, json={"title": "İnsan adımı", "assignee_actor_id": w["member"]["id"]}).json()
    dep_task = client.post(f"/api/v1/projects/{pid}/tasks", headers=h, json={
        "title": "Bağımlı adım", "assignee_actor_id": w["agent"], "depends_on": [human_task["id"]]}).json()
    start = date.today()
    assert client.put(f"/api/v1/projects/{pid}", headers=h, json={"start_date": start.isoformat(), "end_date": (start + timedelta(days=10)).isoformat()}).status_code == 200
    r = client.post(f"/api/v1/projects/{pid}/status", headers=h, json={"action": "mark_ready"})
    assert r.status_code == 200, r.text
    return pid, human_task["id"], dep_task["id"]


def _flow(client, h, pid):
    r = client.get(f"/api/v1/projects/{pid}/workflow", headers=h)
    assert r.status_code == 200, r.text
    return r.json()


def _wait(client, h, pid, cond, what, timeout=30):
    deadline = time.time() + timeout
    while time.time() < deadline:
        flow = _flow(client, h, pid)
        by_title = {t["title"]: t for t in flow["tasks"]}
        if cond(by_title, flow):
            return by_title, flow
        time.sleep(0.4)
    raise AssertionError(f"Beklenen akış durumu oluşmadı: {what}\n{json.dumps(_flow(client, h, pid)['tasks'], default=str, ensure_ascii=False)}")


def test_workflow_full_cycle(client, world):
    w = world
    admin, member, outsider = w["admin"]["h"], w["member"]["h"], w["outsider"]["h"]
    pid, human_id, dep_id = _ready_project(client, w, "Akış Projesi")

    assert client.post(f"/api/v1/projects/{pid}/status", headers=admin, json={"action": "start"}).status_code == 200
    tasks, flow = _wait(client, admin, pid, lambda t, f: t["AI adımı"]["status"] == "IN_PROGRESS" and t["İnsan adımı"]["status"] == "IN_PROGRESS",
                        "bağımsız iki adım başlamalı")
    assert flow["workflow_id"] == f"project-{pid}"
    assert tasks["Bağımlı adım"]["status"] in ("BACKLOG", "READY") and tasks["Bağımlı adım"]["status"] != "IN_PROGRESS"
    assert tasks["İnsan adımı"]["approver"]["id"] == w["admin"]["id"]  # onaylayıcı varsayılan: proje yöneticisi

    # Yetki: ekip dışı göremez; üye yalnızca kendi adımını teslim eder; onay yöneticide
    assert client.get(f"/api/v1/projects/{pid}/workflow", headers=outsider).status_code == 403
    ai_task_id = tasks["AI adımı"]["id"]
    assert client.post(f"/api/v1/tasks/{ai_task_id}/submit", headers=member, json={}).status_code == 403

    # 3 ret > karantina
    for i in range(1, 4):
        r = client.post(f"/api/v1/tasks/{human_id}/submit", headers=member, json={"note": f"Teslim {i}"})
        assert r.status_code == 200, r.text
        _wait(client, admin, pid, lambda t, f: t["İnsan adımı"]["status"] == "WAITING_APPROVAL", f"teslim {i} onay beklemeli")
        assert client.post(f"/api/v1/tasks/{human_id}/decision", headers=member, json={"approve": True}).status_code == 403
        assert client.post(f"/api/v1/tasks/{human_id}/decision", headers=admin, json={"approve": False}).status_code == 422  # gerekçe şart
        assert client.post(f"/api/v1/tasks/{human_id}/decision", headers=admin, json={"approve": False, "note": f"Eksik {i}"}).status_code == 200
        expected = "QUARANTINED" if i == 3 else "REVISION"
        tasks, _ = _wait(client, admin, pid, lambda t, f: t["İnsan adımı"]["status"] == expected, f"ret {i} sonrası {expected}")
    assert tasks["İnsan adımı"]["rejection_count"] == 3 and tasks["İnsan adımı"]["can_release"]
    assert client.post(f"/api/v1/tasks/{human_id}/submit", headers=member, json={}).status_code == 409
    assert client.post(f"/api/v1/tasks/{human_id}/release", headers=member, json={"action": "retry"}).status_code == 403

    # Yönetici yeniden dener > teslim > onay; bağımlı adım açılır
    assert client.post(f"/api/v1/tasks/{human_id}/release", headers=admin, json={"action": "retry", "note": "Bir kez daha"}).status_code == 200
    tasks, _ = _wait(client, admin, pid, lambda t, f: t["İnsan adımı"]["status"] == "IN_PROGRESS", "yeniden deneme")
    assert tasks["İnsan adımı"]["rejection_count"] == 0
    client.post(f"/api/v1/tasks/{human_id}/submit", headers=member, json={"note": "Son hali"})
    _wait(client, admin, pid, lambda t, f: t["İnsan adımı"]["status"] == "WAITING_APPROVAL", "son teslim")
    assert client.post(f"/api/v1/tasks/{human_id}/decision", headers=admin, json={"approve": True, "note": "Tamam"}).status_code == 200
    _wait(client, admin, pid, lambda t, f: t["İnsan adımı"]["status"] == "DONE" and t["Bağımlı adım"]["status"] == "IN_PROGRESS",
          "onaydan sonra bağımlı adım başlamalı")

    # AI adımlarını yönetici teslim eder (otomatik çalışma ADIM 7.2), onaylar > proje akışı biter
    for title in ("AI adımı", "Bağımlı adım"):
        tid = tasks[title]["id"]
        assert client.post(f"/api/v1/tasks/{tid}/submit", headers=admin, json={"note": "AI çıktısı"}).status_code == 200
        _wait(client, admin, pid, lambda t, f, x=title: t[x]["status"] == "WAITING_APPROVAL", f"{title} onay bekler")
        assert client.post(f"/api/v1/tasks/{tid}/decision", headers=admin, json={"approve": True}).status_code == 200
    _, flow = _wait(client, admin, pid, lambda t, f: any(e["kind"] == "PROJECT_FINISHED" for e in f["events"]), "proje akışı bitmeli")
    kinds = [e["kind"] for e in reversed(flow["events"])]
    assert kinds[0] == "PROJECT_STARTED" and kinds.count("REJECTED") == 3 and "QUARANTINED" in kinds and "RELEASED" in kinds
    assert kinds.count("DONE") == 3


def test_workflow_pause_and_cancel(client, world, db):
    w = world
    admin = w["admin"]["h"]
    pid, human_id, _ = _ready_project(client, w, "İptal Projesi")
    assert client.post(f"/api/v1/projects/{pid}/status", headers=admin, json={"action": "start"}).status_code == 200
    _wait(client, admin, pid, lambda t, f: t["İnsan adımı"]["status"] == "IN_PROGRESS", "başlamalı")
    assert client.post(f"/api/v1/projects/{pid}/status", headers=admin, json={"action": "pause"}).status_code == 200
    assert client.post(f"/api/v1/projects/{pid}/status", headers=admin, json={"action": "resume"}).status_code == 200
    assert client.post(f"/api/v1/projects/{pid}/status", headers=admin, json={"action": "cancel", "summary": "Vazgeçildi"}).status_code == 200
    tasks, _ = _wait(client, admin, pid, lambda t, f: all(x["status"] == "CANCELLED" for x in t.values()), "tüm adımlar iptal olmalı")
    # Kapanmış projede akış komutu yok
    assert client.post(f"/api/v1/tasks/{human_id}/submit", headers=w["member"]["h"], json={}).status_code == 409

    # Olay geçmişi değiştirilemez
    with pytest.raises(psycopg2.Error):
        _exec(db, "UPDATE task_events SET note = 'değişti' WHERE project_id = %s", pid)
