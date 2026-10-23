"""
ADIM 8.2: Canlı akış (Redis pub/sub → WebSocket).

- Bilet yalnızca proje ekibine verilir; tek kullanımlıktır, başka projede geçmez; biletsiz bağlantı kapatılır.
- Kaydedilen her mesaj ve iş akışı olayı proje kanalına kendiliğinden düşer; AI düşünce adımları anlık gelir.
- Özel mesaj yalnızca gönderenine iletilir.
"""
import concurrent.futures

import pytest
from starlette.websockets import WebSocketDisconnect

from app.services.evren_client import ChatResult, evren_client
from tests.test_workflow import _ready_project, ai, world  # noqa: F401  (fikstür)

POOL = concurrent.futures.ThreadPoolExecutor(max_workers=4)


def _recv(ws, timeout=20):
    """Zaman aşımlı okuma (olay gelmezse test asılı kalmaz, başarısız olur)."""
    return POOL.submit(ws.receive_json).result(timeout=timeout)


def _until(ws, cond, what, limit=30):
    seen = []
    for _ in range(limit):
        e = _recv(ws)
        seen.append(e.get("type") + ":" + str(e.get("kind") or e.get("step") or (e.get("message") or {}).get("role")))
        if cond(e):
            return e
    raise AssertionError(f"{what} gelmedi; gelenler: {seen}")


def _ticket(client, h, pid):
    r = client.post("/api/v1/live/ticket", headers=h, json={"project_id": pid})
    return r


@pytest.fixture
def replies(monkeypatch):
    async def chat(model_code, messages, **kw):
        return ChatResult(f"Yanıt: {messages[-1]['content'][:40]}", "kısa düşünce", 100, 20, {})
    monkeypatch.setattr(evren_client, "chat", chat)


def test_ticket_rules(client, world):
    w = world
    pid, _, _ = _ready_project(client, w, "Canlı Bilet")
    other, _, _ = _ready_project(client, w, "Başka Canlı")
    assert _ticket(client, w["outsider"]["h"], pid).status_code == 403
    r = _ticket(client, w["member"]["h"], pid)
    assert r.status_code == 200 and r.json()["expires_in"] == 60
    ticket = r.json()["ticket"]

    with pytest.raises(WebSocketDisconnect) as exc:  # başka projenin kanalına bu biletle girilemez
        with client.websocket_connect(f"/ws/projects/{other}?ticket={ticket}") as ws:
            ws.receive_json()
    assert exc.value.code == 4403
    with pytest.raises(WebSocketDisconnect):  # bilet (yanlış denemede bile) tüketildi
        with client.websocket_connect(f"/ws/projects/{pid}?ticket={ticket}") as ws:
            ws.receive_json()
    with pytest.raises(WebSocketDisconnect):
        with client.websocket_connect(f"/ws/projects/{pid}") as ws:
            ws.receive_json()

    ticket = _ticket(client, w["member"]["h"], pid).json()["ticket"]
    with client.websocket_connect(f"/ws/projects/{pid}?ticket={ticket}") as ws:
        assert _recv(ws) == {"type": "ready", "project_id": pid}
        ws.send_text("ping")
        assert _recv(ws) == {"type": "pong"}
    with pytest.raises(WebSocketDisconnect):  # aynı bilet ikinci kez kullanılamaz
        with client.websocket_connect(f"/ws/projects/{pid}?ticket={ticket}") as ws:
            ws.receive_json()


def test_messages_and_thoughts_stream_live(client, world, replies):
    w = world
    pid, human_id, _ = _ready_project(client, w, "Canlı Sohbet")
    ticket = _ticket(client, w["member"]["h"], pid).json()["ticket"]
    with client.websocket_connect(f"/ws/projects/{pid}?ticket={ticket}") as ws:
        assert _recv(ws)["type"] == "ready"
        r = client.post("/api/v1/chat/send", headers=w["admin"]["h"], json={"task_id": human_id, "content": "Durum nedir?"})
        assert r.status_code == 200, r.text
        events = []
        _until(ws, lambda e: events.append(e) or (e["type"] == "message" and e["message"]["role"] == "assistant"), "AI yanıtı")
        kinds = [e["type"] + ":" + (e.get("step") or e.get("message", {}).get("role", "")) for e in events]
        # Kullanıcı mesajı yanıt beklenmeden görünür; ardından AI'ın o an ne yaptığı, en sonda yanıt
        assert kinds.index("message:user") < kinds.index("message:assistant") and "thought:ANALYSIS" in kinds and "thought:WRITING" in kinds
        user_msg, answer = events[kinds.index("message:user")], events[-1]
        assert user_msg["message"]["content"] == "Durum nedir?" and user_msg["message"]["sender_name"] == "Yonetici"
        assert user_msg["message"]["id"] == r.json()["user_message"]["id"]
        assert answer["message"]["content"].startswith("Yanıt: Durum nedir?") and answer["task_id"] == human_id
        # İnsan adımında yanıtı RECAi verir; yanıt adıma atanmış insanın adına yazılmaz
        assert answer["message"]["sender_name"] == "RECAi" and answer["message"]["sender_actor_id"] is None
        assert "Bilgi katmanları" in events[kinds.index("thought:ANALYSIS")]["text"]

        # Özel mesaj başkasına gitmez: üyenin akışında sıradaki mesaj herkese açık olandır
        client.post("/api/v1/chat/send", headers=w["admin"]["h"], json={"task_id": human_id, "content": "Gizli not", "is_private": True})
        client.post("/api/v1/chat/send", headers=w["admin"]["h"], json={"task_id": human_id, "content": "Açık not"})
        nxt = _until(ws, lambda e: e["type"] == "message", "sonraki mesaj")
        assert nxt["message"]["content"] == "Açık not"

    ticket = _ticket(client, w["admin"]["h"], pid).json()["ticket"]
    with client.websocket_connect(f"/ws/projects/{pid}?ticket={ticket}") as ws:  # gönderen kendi özel mesajını görür
        assert _recv(ws)["type"] == "ready"
        client.post("/api/v1/chat/send", headers=w["admin"]["h"], json={"task_id": human_id, "content": "Kendime not", "is_private": True})
        mine = _until(ws, lambda e: e["type"] == "message", "kendi özel mesajı")
        assert mine["message"]["content"] == "Kendime not" and mine["message"]["is_private"] is True
        reply = _until(ws, lambda e: e["type"] == "message", "özel soruya yanıt")
        assert reply["message"]["content"].startswith("Yanıt: Kendime not") and reply["message"]["is_private"] is True

    # Geçmiş: soran kişi özel sorusunu ve yanıtını görür; diğer ekip üyesi ikisini de görmez
    url = f"/api/v1/chat/history/{human_id}?include_private=true"
    own = [m["content"] for m in client.get(url, headers=w["admin"]["h"]).json()]
    other = [m["content"] for m in client.get(url, headers=w["member"]["h"]).json()]
    assert "Gizli not" in own and "Yanıt: Gizli not" in own
    assert not any("Gizli not" in c or "Kendime not" in c for c in other) and "Açık not" in other


def test_workflow_events_stream_live(client, world, ai):
    w = world
    pid, _, _ = _ready_project(client, w, "Canlı Akış Olayları")
    ticket = _ticket(client, w["admin"]["h"], pid).json()["ticket"]
    with client.websocket_connect(f"/ws/projects/{pid}?ticket={ticket}") as ws:
        assert _recv(ws)["type"] == "ready"
        assert client.post(f"/api/v1/projects/{pid}/status", headers=w["admin"]["h"], json={"action": "start"}).status_code == 200
        _until(ws, lambda e: e["type"] == "task_event" and e["kind"] == "TASK_STARTED", "adım başladı olayı", limit=40)
        _until(ws, lambda e: e["type"] == "thought" and e["step"] == "WRITING", "AI yazıyor düşüncesi", limit=40)
        out = _until(ws, lambda e: e["type"] == "message" and e["message"]["role"] == "assistant", "AI çıktısı", limit=40)
        assert out["message"]["sender_name"] == "Kodcu" and "AI adımı çıktısı" in out["message"]["content"]
        _until(ws, lambda e: e["type"] == "task_event" and e["kind"] == "AI_OUTPUT", "AI çıktı olayı", limit=40)
    client.post(f"/api/v1/projects/{pid}/status", headers=w["admin"]["h"], json={"action": "cancel"})
