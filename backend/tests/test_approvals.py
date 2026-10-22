"""
ADIM 7.3: Her yerden onay ve bildirim kanalları (gerçek Temporal; EVREN, nesne deposu ve Telegram sahte).

- Onay isteği onaylayıcıya e-postada tek kullanımlık bağlantıyla gider; bağlantıdan giriş yapmadan karar verilir,
  bağlantı ikinci kez kullanılamaz.
- Telegram'daki Onayla / Revizyon iste butonları; revizyonda gerekçe sonraki mesajla alınır; başka sohbetten gelen karar
  reddedilir.
- Onay kuyruğu (/me/approvals) ve bildirim tercihleri (e-posta kapatılınca e-posta gitmez).
"""
import re

import pytest

from app.services import notification_service as ns
from app.services import telegram_service
from tests.test_workflow import _exec, _ready_project, _wait, ai, world  # noqa: F401  (fikstürler)


@pytest.fixture
def telegram(monkeypatch):
    sent = []

    async def fake_call(method, payload, timeout=15):
        sent.append((method, payload))
        return {"ok": True, "result": []}

    monkeypatch.setattr(telegram_service.settings, "TELEGRAM_BOT_TOKEN", "test-token")
    monkeypatch.setattr(telegram_service, "_call", fake_call)
    return sent


def _email_of(db, actor_id):
    return _exec(db, "SELECT email FROM actors WHERE id = %s", actor_id)[0]


def _approval_link(email, title):
    mails = [m for m in ns.OUTBOX if m["to"] == email and title in m["subject"]]
    assert mails, f"{email} için '{title}' onay e-postası yok"
    return re.search(r"#/approve\?token=([A-Za-z0-9_-]+)", mails[-1]["html"]).group(1)


def test_email_link_decision_and_queue(client, db, world, ai, telegram):
    w = world
    admin, member = w["admin"]["h"], w["member"]["h"]
    pid, human_id, _ = _ready_project(client, w, "E-posta Onay Projesi")
    assert client.post(f"/api/v1/projects/{pid}/status", headers=admin, json={"action": "start"}).status_code == 200
    _wait(client, admin, pid, lambda t, f: t["İnsan adımı"]["status"] == "IN_PROGRESS", "insan adımı başlamalı")
    assert client.post(f"/api/v1/tasks/{human_id}/submit", headers=member, json={"note": "Rapor ekte"}).status_code == 200
    _wait(client, admin, pid, lambda t, f: t["İnsan adımı"]["status"] == "WAITING_APPROVAL", "onay beklemeli")

    # Onay kuyruğu: onaylayıcıda görünür, üyede görünmez
    queue = client.get("/api/v1/me/approvals", headers=admin).json()
    assert any(q["task_id"] == human_id and q["kind"] == "APPROVAL" for q in queue)
    assert not any(q["task_id"] == human_id for q in client.get("/api/v1/me/approvals", headers=member).json())

    raw = _approval_link(_email_of(db, w["admin"]["id"]), "İnsan adımı")
    assert client.get("/api/v1/approvals/gecersiz-belirtec").status_code == 404
    summary = client.get(f"/api/v1/approvals/{raw}")  # giriş yok
    assert summary.status_code == 200 and summary.json()["task_title"] == "İnsan adımı"
    assert client.post(f"/api/v1/approvals/{raw}", json={"approve": False}).status_code == 422  # gerekçe şart
    assert client.post(f"/api/v1/approvals/{raw}", json={"approve": True, "note": "E-postadan onay"}).status_code == 200
    _, flow = _wait(client, admin, pid, lambda t, f: t["İnsan adımı"]["status"] == "DONE", "e-postadan onaylanmalı")
    approved = next(e for e in flow["events"] if e["kind"] == "APPROVED" and e["task_id"] == human_id)
    assert approved["data"]["channel"] == "EMAIL" and approved["actor"]["id"] == w["admin"]["id"]
    assert client.post(f"/api/v1/approvals/{raw}", json={"approve": True}).status_code == 410  # tek kullanımlık
    assert client.get(f"/api/v1/approvals/{raw}").status_code == 410
    client.post(f"/api/v1/projects/{pid}/status", headers=admin, json={"action": "cancel"})


def test_telegram_buttons_and_prefs(client, db, world, ai, telegram):
    w = world
    admin = w["admin"]["h"]
    _exec(db, "UPDATE actors SET telegram_chat_id = '777', notification_prefs = '{}'::jsonb WHERE id = %s", w["admin"]["id"])
    pid, _, _ = _ready_project(client, w, "Telegram Onay Projesi")
    assert client.post(f"/api/v1/projects/{pid}/status", headers=admin, json={"action": "start"}).status_code == 200
    tasks, _ = _wait(client, admin, pid, lambda t, f: t["AI adımı"]["status"] == "WAITING_APPROVAL", "AI adımı onaya gelmeli")
    ai_id = tasks["AI adımı"]["id"]

    msg = next(p for m, p in reversed(telegram) if m == "sendMessage" and p.get("reply_markup") and "AI adımı" in p["text"])
    assert msg["chat_id"] == "777"
    buttons = msg["reply_markup"]["inline_keyboard"][0]
    assert buttons[0]["callback_data"].startswith("a:") and buttons[1]["callback_data"].startswith("r:")
    raw = buttons[1]["callback_data"][2:]

    # Başka sohbetten karar kabul edilmez
    client.portal.call(telegram_service.handle_update, {"callback_query": {"id": "1", "data": f"a:{raw}", "message": {"chat": {"id": 999}}}})
    assert any("bu Telegram hesabına ait değil" in p.get("text", "") for m, p in telegram if m == "sendMessage")
    # Revizyon: buton > gerekçe mesajı > geri bildirimle yeniden çalışma
    client.portal.call(telegram_service.handle_update, {"callback_query": {"id": "2", "data": f"r:{raw}", "message": {"chat": {"id": 777}}}})
    client.portal.call(telegram_service.handle_update, {"message": {"chat": {"id": 777}, "text": "Telegram'dan: tabloyu ekle"}})
    _, flow = _wait(client, admin, pid, lambda t, f: any(e["kind"] == "REJECTED" and e["task_id"] == ai_id for e in f["events"]),
                        "Telegram'dan revizyon istenmeli")
    rejected = next(e for e in flow["events"] if e["kind"] == "REJECTED" and e["task_id"] == ai_id)
    assert rejected["data"]["channel"] == "TELEGRAM" and rejected["note"] == "Telegram'dan: tabloyu ekle"
    _wait(client, admin, pid, lambda t, f: "Telegram'dan: tabloyu ekle" in ai.work_prompts[-1], "AI geri bildirimi almalı")

    # Yeni teslimde onay; eski belirteç geçersiz, yeni butonla onay
    _wait(client, admin, pid, lambda t, f: t["AI adımı"]["status"] == "WAITING_APPROVAL" and t["AI adımı"]["artifact"]["version"] == 2,
          "AI sürüm 2 ile onaya gelmeli")
    assert client.get(f"/api/v1/approvals/{raw}").status_code == 410
    msg = next(p for m, p in reversed(telegram) if m == "sendMessage" and p.get("reply_markup") and "AI adımı" in p["text"])
    client.portal.call(telegram_service.handle_update,
                       {"callback_query": {"id": "3", "data": msg["reply_markup"]["inline_keyboard"][0][0]["callback_data"], "message": {"chat": {"id": 777}}}})
    _wait(client, admin, pid, lambda t, f: t["AI adımı"]["status"] == "DONE", "Telegram'dan onaylanmalı")

    # Tercih: e-posta kapalıyken e-posta gitmez, Telegram gider
    assert client.put("/api/v1/auth/notification-prefs", headers=admin, json={"email": False, "telegram": True}).json() == {"email": False, "telegram": True}
    admin_email = _email_of(db, w["admin"]["id"])
    before = len([m for m in ns.OUTBOX if m["to"] == admin_email])
    tg_before = len(telegram)
    client.post(f"/api/v1/projects/{pid}/status", headers=admin, json={"action": "cancel"})
    pid2, _, _ = _ready_project(client, w, "Tercih Projesi")
    client.post(f"/api/v1/projects/{pid2}/status", headers=admin, json={"action": "start"})
    _wait(client, admin, pid2, lambda t, f: t["AI adımı"]["status"] == "WAITING_APPROVAL", "onaya gelmeli")
    assert len([m for m in ns.OUTBOX if m["to"] == admin_email]) == before
    assert any(m == "sendMessage" for m, _ in telegram[tg_before:])
    client.put("/api/v1/auth/notification-prefs", headers=admin, json={"email": True, "telegram": True})
    client.post(f"/api/v1/projects/{pid2}/status", headers=admin, json={"action": "cancel"})
