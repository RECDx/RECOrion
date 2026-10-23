"""
ADIM 8.1: Silinemez mesaj kaydı ve sohbet uçlarında proje üyeliği.

- chat_messages UPDATE/DELETE/TRUNCATE engellenir; yalnızca şirket kaydı silinirken (o şirket için) silinebilir.
- Gönderen personel silinse de mesaj ve gönderenin adı kalır; yazışma olan adım plan yeniden onaylanırken silinmez.
- Sohbet geçmişi ve gönderme yalnızca proje ekibine açık; mesaj türü/uzunluğu doğrulanır; kapanmış projeye yazılamaz.
"""
import uuid

import psycopg2
import pytest

from app.core.security import hash_password
from tests.test_workflow import PASSWORD, _exec, _login, _ready_project, world  # noqa: F401  (fikstür)


def _msg(db, w, pid, task_id, sender, content="Merhaba"):
    return str(_exec(db, "INSERT INTO chat_messages (tenant_id, project_id, task_id, sender_actor_id, role, content) "
                         "VALUES (%s, %s, %s, %s, 'user', %s) RETURNING id", w["tenant"], pid, task_id, sender, content)[0])


def test_chat_messages_are_append_only(client, db, world):
    w = world
    pid, human_id, _ = _ready_project(client, w, "Kayıt Projesi")
    mid = _msg(db, w, pid, human_id, w["member"]["id"])
    assert _exec(db, "SELECT sender_name FROM chat_messages WHERE id = %s", mid)[0] == "Uzman"  # ad yazıldığı anda saklanır

    for sql in ("UPDATE chat_messages SET content = 'değişti' WHERE id = %s", "DELETE FROM chat_messages WHERE id = %s"):
        with pytest.raises(psycopg2.Error, match="değiştirilemez"):
            _exec(db, sql, mid)
    with pytest.raises(psycopg2.Error):
        _exec(db, "TRUNCATE chat_messages")
    # Başka şirketin silme izni bu şirketin mesajını silmez
    with pytest.raises(psycopg2.Error):
        with db.cursor() as cur:
            cur.execute("BEGIN; SELECT set_config('recorion.purge_tenant', %s, true); DELETE FROM chat_messages WHERE id = %s; COMMIT",
                        (str(uuid.uuid4()), mid))
    _exec(db, "ROLLBACK")
    # Yazışma olan iş adımı silinemez (mesajlar sessizce kaybolmaz)
    with pytest.raises(psycopg2.Error):
        _exec(db, "DELETE FROM tasks WHERE id = %s", human_id)
    assert _exec(db, "SELECT content FROM chat_messages WHERE id = %s", mid)[0] == "Merhaba"


def test_sender_deleted_message_kept(client, db, world):
    w = world
    pid, human_id, _ = _ready_project(client, w, "Ayrılan Personel")
    gone = str(_exec(db, "INSERT INTO actors (tenant_id, actor_type, display_name, role, status) VALUES (%s, 'AI_AGENT', "
                         "'Geçici Ajan', 'Uzman', 'IDLE') RETURNING id", w["tenant"])[0])
    mid = _msg(db, w, pid, human_id, gone, "Ayrılmadan önce yazdım")
    r = client.delete(f"/api/v1/company/{w['tenant']}/ai-agents/{gone}", headers=w["admin"]["h"])
    assert r.status_code == 200, r.text
    assert _exec(db, "SELECT sender_actor_id::text, sender_name FROM chat_messages WHERE id = %s", mid) == (gone, "Geçici Ajan")


def test_tenant_purge_removes_only_its_messages(client, db):
    """KVKK: şirket kaydı silinirken o şirketin (projesiz) asistan yazışmaları da silinir."""
    tag = uuid.uuid4().hex[:6]
    tid = str(_exec(db, "INSERT INTO tenants (id, slug, name, is_active) VALUES (gen_random_uuid(), %s, 'Silinecek Ltd', TRUE) RETURNING id",
                    f"silinecek_{tag}")[0])
    aid = _exec(db, "INSERT INTO actors (tenant_id, actor_type, display_name, role, status) VALUES (%s, 'HUMAN', 'Kişi', 'USER', 'IDLE') "
                    "RETURNING id", tid)[0]
    _exec(db, "INSERT INTO chat_messages (tenant_id, sender_actor_id, role, content, message_type) VALUES (%s, %s, 'user', 'soru', 'BRAIN')",
          tid, aid)
    with pytest.raises(psycopg2.Error):
        _exec(db, "DELETE FROM tenants WHERE id = %s", tid)  # izin olmadan değil
    hq = _exec(db, "SELECT id FROM tenants WHERE slug = 'recdx_hq'")[0]
    email = f"kayit_super_{tag}@recdx.com"
    _exec(db, "INSERT INTO actors (tenant_id, actor_type, display_name, email, role, password_hash, status) "
              "VALUES (%s, 'HUMAN', 'Süper', %s, 'SUPER_ADMIN', %s, 'IDLE')", hq, email, hash_password(PASSWORD))
    r = client.delete(f"/api/v1/tenants/{tid}", headers=_login(client, email))
    assert r.status_code == 200, r.text
    assert _exec(db, "SELECT count(*) FROM chat_messages WHERE tenant_id = %s", tid)[0] == 0


def test_chat_access_requires_project_membership(client, db, world):
    w = world
    pid, human_id, _ = _ready_project(client, w, "Ekip Sohbeti")
    _msg(db, w, pid, human_id, w["admin"]["id"], "Ekip içi not")
    admin, member, outsider = w["admin"]["h"], w["member"]["h"], w["outsider"]["h"]

    r = client.get(f"/api/v1/chat/history/{human_id}", headers=member)  # insan adımına atanmış = ekip üyesi
    assert r.status_code == 200 and r.json()[0]["sender_name"] == "Yonetici"
    assert client.get(f"/api/v1/chat/history/{human_id}", headers=outsider).status_code == 403
    assert client.get(f"/api/v1/chat/project/{pid}", headers=outsider).status_code == 403
    assert client.post("/api/v1/chat/learn/" + human_id, headers=outsider).status_code == 403
    send = {"task_id": human_id, "content": "Bu adım ne durumda?"}
    assert client.post("/api/v1/chat/send", headers=outsider, json=send).status_code == 403
    assert client.post("/api/v1/chat/send", headers=member, json={**send, "message_type": "AGENT_TO_AGENT"}).status_code == 422
    assert client.post("/api/v1/chat/send", headers=member, json={**send, "content": ""}).status_code == 422
    assert client.post("/api/v1/chat/send", headers=member, json={**send, "content": "x" * 20001}).status_code == 422

    assert client.post(f"/api/v1/projects/{pid}/status", headers=admin, json={"action": "cancel"}).status_code == 200
    r = client.post("/api/v1/chat/send", headers=admin, json=send)
    assert r.status_code == 409 and "salt okunur" in r.json()["detail"]
    assert client.get(f"/api/v1/chat/history/{human_id}", headers=member).status_code == 200  # kayıt okunabilir kalır


def test_plan_reapproval_keeps_chatted_tasks(client, db, world):
    w = world
    h = w["admin"]["h"]
    pid = client.post("/api/v1/projects", headers=h, json={"tenant_id": w["tenant"], "name": "Yeniden Onay", "requirements": "İster"}).json()["id"]
    step = {"key": "S1", "title": "Analiz", "estimated_days": 1, "agent_id": w["agent"]}
    assert client.put(f"/api/v1/projects/{pid}/plan", headers=h, json={"summary": "s", "steps": [step]}).status_code == 200
    assert client.post(f"/api/v1/projects/{pid}/plan/approve", headers=h).status_code == 200
    assert client.post(f"/api/v1/projects/{pid}/plan/approve", headers=h).status_code == 200  # yazışma yokken yeniden onay serbest
    task_id = str(_exec(db, "SELECT id FROM tasks WHERE project_id = %s", pid)[0])
    _msg(db, w, pid, task_id, w["admin"]["id"], "Analize şunu da ekleyelim")
    r = client.post(f"/api/v1/projects/{pid}/plan/approve", headers=h)
    assert r.status_code == 409 and "yazışma var" in r.json()["detail"]
