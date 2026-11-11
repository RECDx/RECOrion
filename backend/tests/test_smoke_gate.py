"""
İSTEK #734: yazılım projelerinde kurulum ve duman testi.

- Kod Çalıştırma Ortamı sonucundaki duman testi (uygulama açıldı mı, API/arayüz denetimleri, README) rapora ve sayılara girer.
- Kabul/teslim adımı teslim edilince kod gerçekten çalıştırılır (test uzmanı olmasa da).
- Kabul kapısı: deposu olan projede kabul adımı ya da son açık adım, son koşu + duman testi geçmeden onaylanmak istenirse 409
  TEST_GATE döner, iş akışında uyarı görünür; "yine de onayla" (force) geçmişe TEST_GATE_OVERRIDE olarak yazılır.
"""
import copy
from datetime import date, timedelta

import pytest

from app.config import settings
from app.db.models import Actor, Task, TestRun
from app.services import agent_work, sandbox
from tests.test_code_repo import _gitea, coder  # noqa: F401  (fikstür)
from tests.test_sandbox import _cleanup
from tests.test_workflow import _wait, world  # noqa: F401  (fikstür)

pytestmark = pytest.mark.skipif(not settings.GITEA_TOKEN, reason="GITEA_TOKEN yok (kod deposu sunucusu yapılandırılmamış)")

SMOKE_FAILED = {
    "status": "FAILED", "seconds": 20.1,
    "services": [{"name": "api", "dir": ".", "port": 8000, "started": True, "ready": False,
                  "error": "Uygulama açılırken kapandı (çıkış kodu 3).", "log": "sqlite3.OperationalError: unable to open database file"},
                 {"name": "web", "dir": "src/frontend", "port": 3000, "started": True, "ready": True, "ready_status": 200, "log": ""}],
    "checks": [{"name": "Giriş (API)", "type": "http", "ok": False, "detail": "Hizmet açılmadığı için denenemedi."},
               {"name": "Arayüzden giriş", "type": "browser", "ok": False, "detail": "Timeout · POST :3000/token → 501"}],
    "readme": {"file": "README.md", "chars": 87, "ok": False}}
RESULT_FAILED = {"status": "FAILED", "seconds": 70.0, "smoke": SMOKE_FAILED, "projects": [
    {"dir": ".", "kind": "python", "install": {"ok": True, "exit_code": 0, "seconds": 8.0, "log": ""},
     "test": {"passed": 6, "failed": 0, "errors": 0, "skipped": 0, "exit_code": 0, "status": "PASSED", "seconds": 2.0, "log": "", "failures": []}}]}
RESULT_PASSED = copy.deepcopy(RESULT_FAILED)
RESULT_PASSED.update(status="PASSED", smoke={
    "status": "PASSED", "seconds": 9.0,
    "services": [{"name": "api", "dir": ".", "port": 8000, "started": True, "ready": True, "ready_status": 200, "log": ""}],
    "checks": [{"name": "Giriş (API)", "type": "http", "ok": True, "detail": "HTTP 200"},
               {"name": "Arayüzden giriş", "type": "browser", "ok": True, "detail": "Adımlar tamamlandı"}],
    "readme": {"file": "README.md", "chars": 900, "ok": True}})


def test_smoke_report_and_totals():
    run = TestRun(ref="main", status="FAILED", passed=6, failed=4, skipped=0, result=RESULT_FAILED)
    md = sandbox.report_md(run)
    assert "Duman testi (uygulamayı açıp deneme) — Kaldı" in md
    assert "AÇILMADI" in md and "unable to open database file" in md and "POST :3000/token → 501" in md
    assert "README: var, 87 karakter — kurulum talimatı eksik/yetersiz" in md
    # 6 pytest + 2 kalan denetim + açılmayan 1 hizmet
    assert sandbox._totals(RESULT_FAILED) == {"passed": 6, "failed": 3, "skipped": 0}
    assert sandbox._totals(RESULT_PASSED) == {"passed": 8, "failed": 0, "skipped": 0}
    assert sandbox.smoke_status(run) == "FAILED" and sandbox.smoke_status(None) is None


def test_acceptance_step_runs_code(monkeypatch):
    monkeypatch.setattr(sandbox, "enabled", lambda: True)
    monkeypatch.setattr(agent_work.code_repo, "active", lambda p: True)
    dev = Actor(role="Yazılım Geliştirici (Backend)")
    assert agent_work._runs_tests(None, Actor(role="Test Uzmanı")) == "test"
    assert agent_work._runs_tests(None, dev, Task(title="Kabul, kurulum talimatı ve teslim")) == "accept"
    assert agent_work._runs_tests(None, dev, Task(title="Kurulum ve duman testi")) == "accept"
    assert agent_work._runs_tests(None, dev, Task(title="Backend geliştirme")) is False
    tenant = type("T", (), {"name": "Deneme A.Ş."})()
    text = agent_work._system(dev, tenant, True, "accept")
    assert "DUMAN TESTİ" in text and "recorion.json" in text and "pytest dosyaları" not in text
    assert "pytest dosyaları" in agent_work._system(dev, tenant, True, "test")
    assert "DUMAN TESTİ" not in agent_work._system(dev, tenant, True, False)


def _fake(monkeypatch, result):
    async def execute(archive):
        assert archive[:2] == b"PK"
        return copy.deepcopy(result)
    monkeypatch.setattr(settings, "SANDBOX_URL", "http://sandbox:8100")
    monkeypatch.setattr(sandbox, "execute", execute)


def _acceptance_project(client, w, name):
    admin = w["admin"]["h"]
    pid = client.post("/api/v1/projects", headers=admin, json={"tenant_id": w["tenant"], "name": name, "requirements": "Kod + kabul"}).json()["id"]
    steps = [{"key": "S1", "title": "Kabul ve teslim", "estimated_days": 1, "agent_id": w["agent"]}]
    assert client.put(f"/api/v1/projects/{pid}/plan", headers=admin, json={"summary": "s", "steps": steps}).status_code == 200
    assert client.post(f"/api/v1/projects/{pid}/plan/approve", headers=admin).status_code == 200
    start = date.today()
    client.put(f"/api/v1/projects/{pid}", headers=admin, json={"start_date": start.isoformat(), "end_date": (start + timedelta(days=10)).isoformat()})
    assert client.post(f"/api/v1/projects/{pid}/status", headers=admin, json={"action": "mark_ready"}).status_code == 200
    base = f"/api/v1/projects/{pid}/repository"
    assert client.put(base, headers=admin, json={"mode": "RECORION"}).status_code == 200
    client.post(f"/api/v1/projects/{pid}/status", headers=admin, json={"action": "start"})
    return pid, base


def test_acceptance_gate_blocks_until_override(client, world, coder, monkeypatch):  # noqa: F811
    w = world
    admin = w["admin"]["h"]
    _fake(monkeypatch, RESULT_FAILED)
    pid, base = _acceptance_project(client, w, "Kabul Kapısı Projesi")
    try:
        t, f = _wait(client, admin, pid, lambda t, f: t["Kabul ve teslim"]["status"] == "WAITING_APPROVAL", "kabul adımı onaya gelmeli", 90)
        step = t["Kabul ve teslim"]
        run = client.get(f"/api/v1/projects/{pid}/test-runs", headers=admin).json()["runs"][0]
        assert run["task_id"] == step["id"] and run["status"] == "FAILED" and run["result"]["smoke"]["status"] == "FAILED"
        warn = step["acceptance_warning"]
        assert warn and "duman testi kaldı" in warn and "README" in warn, warn
        r = client.post(f"/api/v1/tasks/{step['id']}/decision", headers=admin, json={"approve": True})
        assert r.status_code == 409 and r.json()["detail"]["code"] == "TEST_GATE", r.text
        # Revizyon istemek kapıya takılmaz
        assert "TEST_GATE" not in client.post(f"/api/v1/tasks/{step['id']}/decision", headers=admin,
                                              json={"approve": False, "note": ""}).text
        r = client.post(f"/api/v1/tasks/{step['id']}/decision", headers=admin, json={"approve": True, "force": True})
        assert r.status_code == 200, r.text
        _, f = _wait(client, admin, pid, lambda t, f: t["Kabul ve teslim"]["status"] == "DONE", "zorla onay geçmeli", 60)
        assert any(e["kind"] == "TEST_GATE_OVERRIDE" for e in f["events"])
    finally:
        _cleanup(client, admin, pid, base)


def test_acceptance_gate_passes_when_app_runs(client, world, coder, monkeypatch):  # noqa: F811
    w = world
    admin = w["admin"]["h"]
    _fake(monkeypatch, RESULT_PASSED)
    pid, base = _acceptance_project(client, w, "Kabul Geçen Proje")
    try:
        t, _ = _wait(client, admin, pid, lambda t, f: t["Kabul ve teslim"]["status"] == "WAITING_APPROVAL", "kabul adımı onaya gelmeli", 90)
        assert t["Kabul ve teslim"]["acceptance_warning"] is None
        r = client.post(f"/api/v1/tasks/{t['Kabul ve teslim']['id']}/decision", headers=admin, json={"approve": True})
        assert r.status_code == 200, r.text
    finally:
        _cleanup(client, admin, pid, base)
