"""İSTEK #745: proje/Case gerçek duraklatma (süren AI çağrısından sonra yeni çalışma/teslim başlamaz), devam ve iptalde kayıp
maliyet (gerekçe zorunlu, akışa ve rapora düşer)."""
import asyncio
import time

from tests.test_workflow import _flow, _ready_project, _wait, ai, world  # noqa: F401  (fikstürler)


def test_pause_holds_step_and_resume_continues(client, world, ai):
    w, h = world, world["admin"]["h"]
    slow = ai.chat

    async def slow_chat(model_code, messages, **kw):  # süren AI çağrısı sırasında duraklatma gelsin
        await asyncio.sleep(3)
        return await slow(model_code, messages, **kw)
    ai.chat = slow_chat
    from app.services import evren_client
    evren_client.chat = slow_chat

    pid, _, _ = _ready_project(client, w, "Duraklatma Projesi")
    try:
        assert client.post(f"/api/v1/projects/{pid}/status", headers=h, json={"action": "start"}).status_code == 200
        _wait(client, h, pid, lambda t, f: t["AI adımı"]["status"] == "IN_PROGRESS", "AI adımı başlamalı")
        r = client.post(f"/api/v1/projects/{pid}/status", headers=h, json={"action": "pause", "summary": "Müşteri toplantısı bekleniyor"})
        assert r.status_code == 200 and r.json()["status"] == "PAUSED"
        # süren çağrı tamamlanır (sürüm üretilir) ama adım teslim/onaya geçmez
        _wait(client, h, pid, lambda t, f: any(e["kind"] == "AI_OUTPUT" for e in f["events"]), "süren çağrı tamamlanmalı", 40)
        time.sleep(4)
        tasks = {t["title"]: t for t in _flow(client, h, pid)["tasks"]}
        assert tasks["AI adımı"]["status"] == "IN_PROGRESS", tasks["AI adımı"]["status"]
        flow = _flow(client, h, pid)
        paused = [e for e in flow["events"] if e["kind"] == "PROJECT_PAUSED"]
        assert paused and paused[0]["note"] == "Müşteri toplantısı bekleniyor"

        assert client.post(f"/api/v1/projects/{pid}/status", headers=h, json={"action": "resume"}).status_code == 200
        _wait(client, h, pid, lambda t, f: t["AI adımı"]["status"] == "WAITING_APPROVAL", "devamda kaldığı yerden onaya gelmeli", 40)
        assert any(e["kind"] == "PROJECT_RESUMED" for e in _flow(client, h, pid)["events"])
    finally:
        client.post(f"/api/v1/projects/{pid}/status", headers=h, json={"action": "cancel", "summary": "Test temizliği"})


def test_cancel_requires_reason_and_records_lost_cost(client, world, ai):
    w, h, member = world, world["admin"]["h"], world["member"]["h"]
    pid, _, _ = _ready_project(client, w, "İptal Projesi")
    assert client.post(f"/api/v1/projects/{pid}/status", headers=h, json={"action": "start"}).status_code == 200
    _wait(client, h, pid, lambda t, f: t["AI adımı"]["status"] == "WAITING_APPROVAL", "AI adımı onaya gelmeli", 40)

    pv = client.get(f"/api/v1/projects/{pid}/cancel-preview", headers=h)
    assert pv.status_code == 200, pv.text
    pv = pv.json()
    assert pv["spent"]["credits"] > 0 and pv["delivered"]["credits"] == 0
    assert abs(pv["lost"]["credits"] - pv["spent"]["credits"]) < 1e-6  # onaylanmış adım yok: harcananın tamamı kayıp
    assert any(s["title"] == "AI adımı" for s in pv["open_steps"])
    assert client.get(f"/api/v1/projects/{pid}/cancel-preview", headers=member).status_code == 403  # yalnız yönetim

    r = client.post(f"/api/v1/projects/{pid}/status", headers=h, json={"action": "cancel"})
    assert r.status_code == 409 and "gerekçe" in r.json()["detail"].lower()
    r = client.post(f"/api/v1/projects/{pid}/status", headers=h, json={"action": "cancel", "summary": "Müşteri vazgeçti"})
    assert r.status_code == 200 and r.json()["status"] == "CANCELLED"
    flow = _flow(client, h, pid)
    ev = next(e for e in flow["events"] if e["kind"] == "PROJECT_CANCELLED")
    assert ev["note"] == "Müşteri vazgeçti"
    assert client.get(f"/api/v1/projects/{pid}/cancel-preview", headers=h).status_code == 409  # kapanmış

    rep = client.post(f"/api/v1/company/{w['tenant']}/reports/run", headers=h,
                      json={"report": "cancellations", "dims": ["project"], "measure": "lost_credits"})
    assert rep.status_code == 200, rep.text
    body = rep.json()
    assert "İptal Projesi" in str(body) and body.get("rows") is not None
