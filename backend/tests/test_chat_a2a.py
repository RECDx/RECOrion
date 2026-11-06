"""
#611: Ajanlar arası konuşmalar (AGENT_TO_AGENT) yalnız "Ajanlar Arası Konuşmaları İzleme" (chat:view_a2a) izni olana görünür.

- Görev ve proje sohbet geçmişinde izni olmayan ekip üyesi A2A mesajını görmez, olağan mesajları görür.
- Proje geneli A2A süzgeci izinsiz 403; şirket yöneticisi (müşteri izinlerinin tamamı) görür.
"""
from tests.test_workflow import _exec, _ready_project, world  # noqa: F401  (fikstür)


def test_agent_to_agent_messages_need_permission(client, world, db):
    w = world
    admin, member = w["admin"]["h"], w["member"]["h"]
    pid, human_id, _ = _ready_project(client, w, "A2A Görünürlüğü")
    try:
        for kind, text in (("AGENT_TO_AGENT", "Kodcu → Kontrolcu: kapsamı daraltalım"), ("CHAT", "Olağan görev mesajı")):
            _exec(db, "INSERT INTO chat_messages (tenant_id, project_id, task_id, sender_actor_id, role, content, message_type, is_private) "
                      "VALUES (%s, %s, %s, %s, 'assistant', %s, %s, FALSE) RETURNING id", w["tenant"], pid, human_id, w["agent"], text, kind)
        texts = lambda h, url: [m["content"] for m in client.get(url, headers=h).json()]  # noqa: E731
        hist, proj = f"/api/v1/chat/history/{human_id}", f"/api/v1/chat/project/{pid}"
        assert "Olağan görev mesajı" in texts(member, hist) and not any("Kodcu →" in t for t in texts(member, hist))
        assert not any("Kodcu →" in t for t in texts(member, proj))
        assert client.get(proj, headers=member, params={"message_type": "AGENT_TO_AGENT"}).status_code == 403
        assert any("Kodcu →" in t for t in texts(admin, hist))
        r = client.get(proj, headers=admin, params={"message_type": "AGENT_TO_AGENT"})
        assert r.status_code == 200 and [m["content"] for m in r.json()] == ["Kodcu → Kontrolcu: kapsamı daraltalım"]
    finally:
        client.post(f"/api/v1/projects/{pid}/status", headers=admin, json={"action": "cancel"})
