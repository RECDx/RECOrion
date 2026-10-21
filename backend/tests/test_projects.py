"""
ADIM 6: Proje/Case çekirdeği, Beyin AI planlama, simülasyon, durumlar, başlangıç bildirimi ve Telegram bağlama.
EVREN ve Telegram sahte nesnelerle değiştirilir.
"""
import asyncio
import json
import uuid
from datetime import date, timedelta

import pytest

from app.core.security import hash_password
from app.services import notification_service as ns
from app.services import telegram_service
from app.services.evren_client import ChatResult, EmbeddingResult, evren_client

PASSWORD = "Proje-Testi-Sifresi-2026"


def _exec(db, sql, *params):
    with db.cursor() as cur:
        cur.execute(sql, params)
        return cur.fetchone() if cur.description else None


def _all(db, sql, *params):
    with db.cursor() as cur:
        cur.execute(sql, params)
        return cur.fetchall()


def _login(client, email):
    r = client.post("/api/v1/auth/login", json={"email": email, "password": PASSWORD})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.fixture(scope="module")
def world(client, db):
    tag = uuid.uuid4().hex[:6]
    tid = _exec(db, "INSERT INTO tenants (id, slug, name, plan_id, is_active) VALUES (gen_random_uuid(), %s, 'Proje Ltd', "
                    "(SELECT id FROM plans WHERE code = 'STARTER'), TRUE) RETURNING id", f"prj_{tag}")[0]

    def human(name, role):
        email = f"prj_{name}_{tag}@prj-test.com.tr"
        aid = _exec(db, "INSERT INTO actors (tenant_id, actor_type, display_name, email, role, password_hash, status) "
                        "VALUES (%s, 'HUMAN', %s, %s, %s, %s, 'IDLE') RETURNING id", tid, name, email, role, hash_password(PASSWORD))[0]
        return {"id": str(aid), "email": email, "h": _login(client, email)}

    admin, member, outsider = human("Yönetici", "COMPANY_ADMIN"), human("Uzman", "USER"), human("Diğer", "USER")
    model = _exec(db, "SELECT id FROM llm_models WHERE model_code = 'deepseek-v4-flash'")[0]
    agents = [str(_exec(db, "INSERT INTO actors (tenant_id, actor_type, display_name, role, status, preferred_model_id) "
                            "VALUES (%s, 'AI_AGENT', %s, 'X', 'IDLE', %s) RETURNING id", tid, n, model)[0]) for n in ("Analist", "Kodcu")]
    hq = _exec(db, "SELECT id FROM tenants WHERE slug = 'recdx_hq'")[0]
    sa_email = f"prj_super_{tag}@recdx.com"
    _exec(db, "INSERT INTO actors (tenant_id, actor_type, display_name, email, role, password_hash, status) "
              "VALUES (%s, 'HUMAN', 'Süper', %s, 'SUPER_ADMIN', %s, 'IDLE')", hq, sa_email, hash_password(PASSWORD))
    return {"tenant": str(tid), "admin": admin, "member": member, "outsider": outsider, "agents": agents, "super": _login(client, sa_email)}


@pytest.fixture
def brain(monkeypatch, world):
    calls = []

    async def chat(model_code, messages, **kw):
        content = messages[-1]["content"]
        calls.append(content)
        if "Sadece şu JSON" in content:
            a1, a2 = world["agents"]
            return ChatResult(json.dumps({"summary": "Plan özeti.", "steps": [
                {"key": "S1", "title": "Analiz", "estimated_days": 2, "agent_id": a1, "department": "BT", "job_title": "İş Analisti"},
                {"key": "S2", "title": "Kodlama", "estimated_days": 3, "agent_id": a2, "depends_on": ["S1"]},
                {"key": "S3", "title": "Test", "estimated_days": 1, "agent_id": "uydurma-id", "depends_on": ["S2", "S9"]},
                {"key": "S4", "title": "Dokümantasyon", "estimated_days": 1, "agent_id": a1, "depends_on": ["S1"]},
            ], "hire_suggestions": [{"job_title": "Yazılım Test Uzmanı", "reason": "Test için personel yok"}],
                "risks": ["Test personeli yok"], "questions": ["Canlıya çıkış tarihi nedir?"]}), None, 1000, 400, {})
        return ChatResult("Planlama önerim: önce analiz.", None, 300, 50, {})

    async def embed(text, model_code):
        return EmbeddingResult([0.1] * 8, 10)

    monkeypatch.setattr(evren_client, "chat", chat)
    monkeypatch.setattr(evren_client, "embed", embed)
    return calls


def test_project_create_visibility_and_kvkk(client, world):
    w = world
    r = client.post("/api/v1/projects", headers=w["admin"]["h"], json={"tenant_id": w["tenant"], "name": "Müşteri Portalı", "kind": "PROJECT"})
    assert r.status_code == 200, r.text
    p = r.json()
    assert p["status"] == "DRAFT" and p["manager_actor_id"] == w["admin"]["id"] and p["slug"] == "musteri-portali"
    w["project"] = p["id"]
    assert client.get(f"/api/v1/projects/{p['id']}", headers=w["outsider"]["h"]).status_code == 403  # ekipte değil
    assert client.get(f"/api/v1/projects/{p['id']}", headers=w["super"]).status_code == 403  # KVKK
    assert all(x["id"] != p["id"] for x in client.get(f"/api/v1/projects?tenant_id={w['tenant']}", headers=w["outsider"]["h"]).json())
    # Ekibe eklenen insan personel projeyi görür ama düzenleyemez
    client.post(f"/api/v1/projects/{p['id']}/members", headers=w["admin"]["h"], json={"actor_id": w["member"]["id"]})
    assert client.get(f"/api/v1/projects/{p['id']}", headers=w["member"]["h"]).status_code == 200
    assert client.put(f"/api/v1/projects/{p['id']}", headers=w["member"]["h"], json={"name": "X Y"}).status_code == 403
    # AI personel proje yöneticisi olamaz
    assert client.put(f"/api/v1/projects/{p['id']}", headers=w["admin"]["h"], json={"manager_actor_id": w["agents"][0]}).status_code == 422
    # Planlamaya geçmek için isterler zorunlu
    assert client.post(f"/api/v1/projects/{p['id']}/status", headers=w["admin"]["h"], json={"action": "start_planning"}).status_code == 409


def test_project_quota(client, world):
    for i in range(2):  # STARTER: en fazla 3 açık proje (biri önceki testte açıldı)
        assert client.post("/api/v1/projects", headers=world["admin"]["h"], json={"tenant_id": world["tenant"], "name": f"Ek {i}"}).status_code == 200
    r = client.post("/api/v1/projects", headers=world["admin"]["h"], json={"tenant_id": world["tenant"], "name": "Fazla"})
    assert r.status_code == 403 and "3 açık proje" in r.json()["detail"]
    for p in client.get(f"/api/v1/projects?tenant_id={world['tenant']}", headers=world["admin"]["h"]).json():
        if p["name"].startswith("Ek "):
            client.post(f"/api/v1/projects/{p['id']}/status", headers=world["admin"]["h"], json={"action": "cancel"})


def test_plan_suggest_approve_simulate_and_start(client, db, world, brain):
    w, h = world, world["admin"]["h"]
    pid = w["project"]
    client.put(f"/api/v1/projects/{pid}", headers=h, json={"requirements": "Müşteriler sipariş durumunu görebilmeli."})
    plan = client.post(f"/api/v1/projects/{pid}/plan/suggest", headers=h, json={}).json()
    steps = {s["key"]: s for s in plan["steps"]}
    assert steps["S3"]["agent_id"] is None and steps["S3"]["depends_on"] == ["S2"]  # uydurma personel ve bağımlılık düşer
    assert plan["hire_suggestions"][0]["job_title"] == "Yazılım Test Uzmanı"
    assert client.get(f"/api/v1/projects/{pid}", headers=h).json()["status"] == "PLANNING"

    # Döngüsel bağımlılık reddedilir
    bad = {"steps": [{"key": "A", "title": "A", "depends_on": ["B"]}, {"key": "B", "title": "B", "depends_on": ["A"]}]}
    assert client.put(f"/api/v1/projects/{pid}/plan", headers=h, json=bad).status_code == 422

    # Yönetici test adımını kodcuya atar ve onaylar
    plan["steps"][2]["agent_id"] = w["agents"][1]
    assert client.put(f"/api/v1/projects/{pid}/plan", headers=h, json=plan).status_code == 200
    r = client.post(f"/api/v1/projects/{pid}/plan/approve", headers=h)
    assert r.json() == {"success": True, "task_count": 4, "unassigned": 0}
    tasks = {t["title"]: t for t in client.get(f"/api/v1/projects/{pid}/tasks", headers=h).json()}
    assert tasks["Kodlama"]["depends_on"] == [tasks["Analiz"]["id"]]
    members = client.get(f"/api/v1/projects/{pid}", headers=h).json()["members"]
    assert {m["actor_id"] for m in members if m["role"] == "AGENT"} == set(w["agents"])

    # Simülasyon: pazartesi başlangıç, hafta sonu atlanır, aynı personelin işleri üst üste binmez
    monday = date.today() + timedelta(days=(7 - date.today().weekday()))
    sim = client.post(f"/api/v1/projects/{pid}/simulate", headers=h, json={"start_date": monday.isoformat()}).json()
    tl = {x["title"]: x for x in sim["timeline"]}
    assert tl["Analiz"]["start"] == monday.isoformat() and tl["Analiz"]["end"] == (monday + timedelta(days=1)).isoformat()
    assert tl["Dokümantasyon"]["start"] == (monday + timedelta(days=2)).isoformat()  # analist önce analizi bitirir
    assert tl["Kodlama"]["start"] == (monday + timedelta(days=2)).isoformat()
    assert tl["Test"]["start"] == (monday + timedelta(days=7)).isoformat()  # kodlama 3 gün (hafta sonu atlanır)
    assert sim["estimated_credits"] > 0 and sim["workdays"] == 6
    assert any("işe alınması" in r["text"] for r in sim["risks"])

    # Hazır yapmak için tarihler gerekir; sonra başlatılır ve bağımlılığı olmayan adım READY olur
    assert client.post(f"/api/v1/projects/{pid}/status", headers=h, json={"action": "mark_ready"}).status_code == 409
    client.put(f"/api/v1/projects/{pid}", headers=h, json={"start_date": monday.isoformat(), "end_date": (monday + timedelta(days=14)).isoformat()})
    assert client.post(f"/api/v1/projects/{pid}/status", headers=h, json={"action": "mark_ready"}).json()["status"] == "READY"
    assert client.post(f"/api/v1/projects/{pid}/status", headers=w["member"]["h"], json={"action": "start"}).status_code == 403
    assert client.post(f"/api/v1/projects/{pid}/status", headers=h, json={"action": "start"}).json()["status"] == "ACTIVE"
    statuses = {t["title"]: t["status"] for t in client.get(f"/api/v1/projects/{pid}/tasks", headers=h).json()}
    assert statuses == {"Analiz": "READY", "Kodlama": "BACKLOG", "Test": "BACKLOG", "Dokümantasyon": "BACKLOG"}
    assert client.post(f"/api/v1/projects/{pid}/plan/approve", headers=h).status_code == 409  # başlamış projede plan değişmez


def test_plan_chat(client, world, brain):
    h = world["admin"]["h"]
    r = client.post("/api/v1/projects", headers=h, json={"tenant_id": world["tenant"], "name": "Sohbet Projesi", "requirements": "Rapor ekranı"})
    pid = r.json()["id"]
    assert client.post(f"/api/v1/projects/{pid}/plan/chat", headers=h, json={"content": "Nereden başlayalım?"}).json()["content"].startswith("Planlama")
    hist = client.get(f"/api/v1/projects/{pid}/plan/chat", headers=h).json()
    assert [m["role"] for m in hist] == ["user", "assistant"]
    client.post(f"/api/v1/projects/{pid}/plan/suggest", headers=h, json={"use_chat": True})
    assert "Nereden başlayalım?" in brain[-1]  # konuşma plana geri bildirim olarak girer
    client.post(f"/api/v1/projects/{pid}/status", headers=h, json={"action": "cancel"})


def test_start_reminder_email_and_telegram(client, db, world, monkeypatch):
    from app.services.scheduler_service import send_project_start_reminders

    sent = []
    monkeypatch.setattr(telegram_service, "send_message", lambda chat_id, text: _fake_send(sent, chat_id, text))
    pid = _exec(db, "INSERT INTO projects (id, tenant_id, slug, name, status, manager_actor_id, start_date) VALUES "
                    "(gen_random_uuid(), %s, %s, 'Hatırlatma Projesi', 'READY', %s, %s) RETURNING id",
                world["tenant"], f"hat-{uuid.uuid4().hex[:4]}", world["admin"]["id"], date.today())[0]
    _exec(db, "UPDATE actors SET telegram_chat_id = '12345' WHERE id = %s", world["admin"]["id"])
    before = len(ns.OUTBOX)
    assert asyncio.run(_run(send_project_start_reminders)) >= 1
    mails = [m for m in ns.OUTBOX[before:] if m["to"] == world["admin"]["email"]]
    assert mails and "Hatırlatma Projesi" in mails[-1]["subject"]
    assert any(c == "12345" and "Hatırlatma Projesi" in t for c, t in sent)
    assert asyncio.run(_run(send_project_start_reminders)) == 0  # ikinci kez gönderilmez
    _exec(db, "UPDATE projects SET status = 'CANCELLED' WHERE id = %s", pid)


async def _fake_send(sent, chat_id, text):
    sent.append((chat_id, text))
    return True


async def _run(fn):
    """Uygulamanın bağlantı havuzundan bağımsız çalıştırmak için kısa ömürlü motor kullanılır."""
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
    from sqlalchemy.pool import NullPool
    from app.config import settings
    from app.services import scheduler_service

    engine = create_async_engine(settings.DATABASE_URL, poolclass=NullPool)
    original = scheduler_service.AsyncSessionLocal
    scheduler_service.AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)
    try:
        return await fn()
    finally:
        scheduler_service.AsyncSessionLocal = original
        await engine.dispose()


def test_telegram_linking(client, db, world, monkeypatch):
    h = world["member"]["h"]
    monkeypatch.setattr(telegram_service.settings, "TELEGRAM_BOT_TOKEN", "")
    assert client.post("/api/v1/auth/telegram/link", headers=h).status_code == 503
    monkeypatch.setattr(telegram_service.settings, "TELEGRAM_BOT_TOKEN", "test-token")
    monkeypatch.setattr(telegram_service.settings, "TELEGRAM_BOT_USERNAME", "RecOrionBot")
    r = client.post("/api/v1/auth/telegram/link", headers=h).json()
    assert r["deep_link"] == f"https://t.me/RecOrionBot?start={r['code']}"

    replies = []
    monkeypatch.setattr(telegram_service, "send_message", lambda chat_id, text: _fake_send(replies, chat_id, text))
    from app.services import telegram_service as ts
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
    from sqlalchemy.pool import NullPool
    from app.config import settings

    async def link():
        engine = create_async_engine(settings.DATABASE_URL, poolclass=NullPool)
        original = ts.AsyncSessionLocal
        ts.AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)
        try:
            await ts.handle_update({"message": {"text": f"/start {r['code']}", "chat": {"id": 777}}})
            await ts.handle_update({"message": {"text": "/start YANLIS", "chat": {"id": 888}}})
        finally:
            ts.AsyncSessionLocal = original
            await engine.dispose()
    asyncio.run(link())
    assert _exec(db, "SELECT telegram_chat_id, telegram_link_code FROM actors WHERE id = %s", world["member"]["id"]) == ("777", None)
    assert "bağlandı" in replies[0][1] and "geçersiz" in replies[1][1]
    assert client.get("/api/v1/auth/telegram", headers=h).json()["linked"] is True


def test_project_documents_follow_project_membership(client, world, monkeypatch):
    """Proje ekleri: ekip üyeleri görür ve yükler (sohbet ekleri), ekip dışı göremez, onay proje yöneticisindedir."""
    from app.services.documents import pipeline

    async def _noop(*a, **kw):
        return None
    monkeypatch.setattr(pipeline, "process_document", _noop)
    w = world
    pid = client.post("/api/v1/projects", headers=w["admin"]["h"], json={"tenant_id": w["tenant"], "name": "Ekli Proje"}).json()["id"]
    assert client.post(f"/api/v1/projects/{pid}/members", headers=w["admin"]["h"], json={"actor_id": w["member"]["id"]}).status_code == 200

    files = {"file": ("not.txt", b"Proje notu: teslim cuma.", "text/plain")}
    r = client.post(f"/api/v1/projects/{pid}/documents", headers=w["member"]["h"], files=files)
    assert r.status_code == 201, r.text
    doc_id = r.json()["id"]
    assert [d["id"] for d in client.get(f"/api/v1/projects/{pid}/documents", headers=w["member"]["h"]).json()] == [doc_id]
    assert client.get(f"/api/v1/projects/{pid}/documents", headers=w["outsider"]["h"]).status_code == 403
    assert client.get(f"/api/v1/documents/{doc_id}", headers=w["outsider"]["h"]).status_code == 403
    assert client.get(f"/api/v1/documents/{doc_id}", headers=w["member"]["h"]).status_code == 200
    # Üye onaylayamaz/silemez; KVKK: süper admin içeriği göremez
    assert client.delete(f"/api/v1/documents/{doc_id}", headers=w["member"]["h"]).status_code == 403
    assert client.get(f"/api/v1/projects/{pid}/documents", headers=w["super"]).status_code == 403
    assert client.delete(f"/api/v1/documents/{doc_id}", headers=w["admin"]["h"]).status_code == 200
