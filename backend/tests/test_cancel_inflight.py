"""
HATA #760: Proje kapanınca / adım iptal edilince, o sırada LLM yanıtı bekleyen AI çalışması sonucu yazmamalı.

e2e753'te proje gerekçeyle kabul edilip kapatıldıktan sonra iptal edilmiş adımlara çıktı yazıldı, depoya commit edildi, test
koşturuldu ve yeni düzeltme turu açıldı. Artık produce() yanıttan sonra veritabanındaki güncel duruma bakar ve hiçbir şey yazmaz.
"""
from types import SimpleNamespace

from app.db.session import AsyncSessionLocal
from app.services import agent_work
from tests.test_workflow import _exec, _ready_project, ai, world  # noqa: F401  (fikstür)


def _produce(client, task_id):
    async def go():
        async with AsyncSessionLocal() as s:
            return await agent_work.produce(s, task_id)
    return client.portal.call(go)


def test_cancelled_while_generating_writes_nothing(client, world, db, ai, monkeypatch):  # noqa: F811
    w = world
    pid, _, dep_id = _ready_project(client, w, "Uçuştaki iptal")
    ai_id = _exec(db, "SELECT id FROM tasks WHERE project_id = %s AND title = 'AI adımı'", pid)[0]

    def fake_generate(cancel_sql):
        async def gen(ctx, messages, tooling=None):
            if cancel_sql:  # yanıt beklenirken yönetici projeyi kapattı / adım iptal edildi
                _exec(db, *cancel_sql)
            return "## Çıktı\nTamam", SimpleNamespace(thought=None, public_model="RECAi Mergen"), 1, 0, None, []
        return gen

    def counts(tid):
        return (_exec(db, "SELECT count(*) FROM artifacts WHERE task_id = %s", tid)[0],
                _exec(db, "SELECT count(*) FROM task_events WHERE task_id = %s AND kind = 'AI_OUTPUT'", tid)[0])

    # Adım iptal edildi → çıktı yazılmaz, iş akışı "iptal" olarak biter
    monkeypatch.setattr(agent_work, "_generate", fake_generate(("UPDATE tasks SET status = 'CANCELLED' WHERE id = %s", ai_id)))
    out = _produce(client, ai_id)
    assert out["ok"] is False and out["cancelled"] is True
    assert counts(ai_id) == (0, 0)

    # Proje kapandı → bağımlı adımın çıktısı da yazılmaz
    before = _exec(db, "SELECT status FROM projects WHERE id = %s", pid)[0]
    monkeypatch.setattr(agent_work, "_generate", fake_generate(("UPDATE projects SET status = 'COMPLETED' WHERE id = %s", pid)))
    out = _produce(client, dep_id)
    assert out["cancelled"] is True and counts(dep_id) == (0, 0)

    # Açık projede normal yazılır (kontrol, işi engellemiyor)
    _exec(db, "UPDATE projects SET status = %s WHERE id = %s", before, pid)
    monkeypatch.setattr(agent_work, "_generate", fake_generate(None))
    out = _produce(client, dep_id)
    assert out["ok"] is True and counts(dep_id) == (1, 1)


def test_reasoned_approval_cancels_unstarted_fix_rounds(client, world, db, ai):  # noqa: F811
    """Kullanıcı kararı (18.11.2026): doğrulaması eksik adım gerekçeyle onaylanınca aynı adımın başlamamış düzeltme/yeniden test
    turları iptal edilir (kredi harcamasın); çalışmakta olan tur ve başka adımın turları dokunulmaz."""
    from app.db.models import Project, Task
    from app.services import sandbox

    w = world
    h = w["admin"]["h"]
    pid, human_id, _ = _ready_project(client, w, "Gerekçeli onay turları")
    root = _exec(db, "SELECT id FROM tasks WHERE project_id = %s AND title = 'AI adımı'", pid)[0]

    def fix(title, status, of):
        tid = client.post(f"/api/v1/projects/{pid}/tasks", headers=h, json={"title": title, "assignee_actor_id": w["agent"]}).json()["id"]
        _exec(db, "UPDATE tasks SET fix_of_task_id = %s, fix_kind = 'FIX', status = %s WHERE id = %s", of, status, tid)
        return tid
    waiting, running, other = fix("Yeniden test 1: AI adımı", "BACKLOG", root), fix("Test düzeltmesi 1: x", "IN_PROGRESS", root), \
        fix("Yeniden test 1: başka", "BACKLOG", human_id)

    async def go():
        async with AsyncSessionLocal() as s:
            closed = await sandbox.cancel_pending_rounds(s, await s.get(Project, pid), await s.get(Task, root))
            await s.commit()  # onay ucunda olduğu gibi
            return closed
    assert client.portal.call(go) == ["Yeniden test 1: AI adımı"]
    st = lambda tid: _exec(db, "SELECT status FROM tasks WHERE id = %s", tid)[0]  # noqa: E731
    assert (st(waiting), st(running), st(other)) == ("CANCELLED", "IN_PROGRESS", "BACKLOG")
    assert _exec(db, "SELECT count(*) FROM task_events WHERE task_id = %s AND kind = 'TEST_FIX_CLOSED'", root)[0] == 1
