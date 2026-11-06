"""
ADIM 16.2 (#610): Kod Çalıştırma Ortamı ve AI Test Uzmanı (gerçek Gitea; sandbox servisi taklit, ayrıca varsa gerçek).

- Testleri yalnız proje yöneticisi elle başlatır; ekip sonuçları görür, ekip dışı göremez; deposuz projede çalışmaz.
- AI Test Uzmanı deposu olan projede çıktısını teslim edince dalı gerçekten çalıştırılır; sistemin yazdığı sonuç ve AI'ın bu
  sonuca göre değerlendirmesi adım çıktısına eklenir; koşu Testler listesinde adıma bağlı görünür.
- Gerçek sandbox servisi erişilebilirse: geçen ve kalan pytest testleri doğru sayılır, kod internetsiz çalışır.
"""
import io
import json
import zipfile

import httpx
import pytest

from app.config import settings
from app.db.models import TestRun
from app.services import sandbox
from tests.test_code_repo import _gitea, coder  # noqa: F401  (fikstür)
from tests.test_workflow import _ready_project, _wait, world  # noqa: F401  (fikstür)

pytestmark = pytest.mark.skipif(not settings.GITEA_TOKEN, reason="GITEA_TOKEN yok (kod deposu sunucusu yapılandırılmamış)")

FAKE = {"status": "FAILED", "seconds": 12.5, "projects": [
    {"dir": ".", "kind": "python", "install": {"ok": True, "exit_code": 0, "seconds": 8.0, "log": ""},
     "test": {"passed": 3, "failed": 1, "errors": 0, "skipped": 0, "exit_code": 1, "status": "FAILED", "seconds": 1.2, "log": "1 failed",
              "failures": [{"name": "tests.test_app.test_randevu_cakisma", "message": "AssertionError: çakışan randevu kabul edildi"}]}}]}


def test_role_and_report():
    assert sandbox.is_test_role("Test Uzmanı") and sandbox.is_test_role("QA Engineer") and sandbox.is_test_role("Kalite Güvence Uzmanı")
    assert not sandbox.is_test_role("Yazılım Geliştirici (Backend)") and not sandbox.is_test_role(None)
    run = TestRun(ref="adim-3-test", commit_sha="abcdef1234567890", status="FAILED", passed=3, failed=1, skipped=0, result=FAKE)
    md = sandbox.report_md(run)
    assert "Gerçek test koşusu" in md and "**Kaldı**" in md and "3 geçti · 1 kaldı" in md
    assert "test_randevu_cakisma" in md and "abcdef1234" in md
    assert sandbox._totals(FAKE) == {"passed": 3, "failed": 1, "skipped": 0}


@pytest.fixture
def fake_sandbox(monkeypatch):
    calls = []

    async def execute(archive):
        calls.append(archive)
        assert archive[:2] == b"PK"  # depodan gerçek zip arşivi gelir
        return FAKE
    monkeypatch.setattr(settings, "SANDBOX_URL", "http://sandbox:8100")
    monkeypatch.setattr(sandbox, "execute", execute)
    return calls


def _cleanup(client, admin, pid, base):
    client.post(f"/api/v1/projects/{pid}/status", headers=admin, json={"action": "cancel"})
    info = client.get(base, headers=admin).json()
    if info.get("url"):
        owner, repo = info["url"].rstrip("/").split("/")[-2:]
        _gitea("DELETE", f"/repos/{owner}/{repo}")
        if not _gitea("GET", f"/orgs/{owner}/repos").json():
            _gitea("DELETE", f"/orgs/{owner}")


def test_manual_run_permissions_and_results(client, world, coder, fake_sandbox):  # noqa: F811
    w = world
    admin, member, outsider = w["admin"]["h"], w["member"]["h"], w["outsider"]["h"]
    pid, _, _ = _ready_project(client, w, "Test Koşusu Projesi")
    base, runs = f"/api/v1/projects/{pid}/repository", f"/api/v1/projects/{pid}/test-runs"
    try:
        assert client.post(runs, headers=admin, json={"ref": "main"}).status_code == 409  # depo yok
        assert client.put(base, headers=admin, json={"mode": "RECORION"}).status_code == 200
        assert client.get(runs, headers=member).json()["enabled"] is True
        assert client.post(runs, headers=member, json={"ref": "main"}).status_code == 403
        assert client.post(runs, headers=admin, json={"ref": "../main"}).status_code == 422
        r = client.post(runs, headers=admin, json={"ref": "main"})
        assert r.status_code == 200 and r.json()["status"] == "RUNNING", r.text
        listed = client.get(runs, headers=member).json()
        run = listed["runs"][0]
        assert run["status"] == "FAILED" and run["passed"] == 3 and run["failed"] == 1 and run["commit_sha"]
        assert run["result"]["projects"][0]["test"]["failures"][0]["name"].endswith("test_randevu_cakisma")
        assert listed["can_run"] is False and client.get(runs, headers=admin).json()["can_run"] is True
        assert client.get(f"{runs}/{run['id']}", headers=member).json()["id"] == run["id"]
        assert client.get(runs, headers=outsider).status_code == 403
        assert client.get(f"{runs}/{run['id']}", headers=outsider).status_code == 403
        # Olmayan dal: koşu "Çalıştırılamadı" olarak kaydedilir, sandbox'a gidilmez
        n = len(fake_sandbox)
        client.post(runs, headers=admin, json={"ref": "olmayan-dal"})
        bad = client.get(runs, headers=admin).json()["runs"][0]
        assert bad["status"] == "ERROR" and "bulunamadı" in bad["error"] and len(fake_sandbox) == n
        flow = client.get(f"/api/v1/projects/{pid}/workflow", headers=admin).json()
        assert sum(e["kind"] == "TEST_RUN" for e in flow["events"]) == 2
    finally:
        _cleanup(client, admin, pid, base)


def test_ai_test_specialist_step_runs_tests(client, world, coder, fake_sandbox, monkeypatch):  # noqa: F811
    """AI adımının sahibi test uzmanıysa çıktı teslim edilince dal çalıştırılır ve sonuç çıktıya eklenir."""
    monkeypatch.setattr(sandbox, "is_test_role", lambda role: True)
    w = world
    admin, member = w["admin"]["h"], w["member"]["h"]
    pid, _, _ = _ready_project(client, w, "AI Test Uzmanı Projesi")
    base = f"/api/v1/projects/{pid}/repository"
    try:
        assert client.put(base, headers=admin, json={"mode": "RECORION"}).status_code == 200
        client.post(f"/api/v1/projects/{pid}/status", headers=admin, json={"action": "start"})
        tasks, flow = _wait(client, admin, pid, lambda t, f: t["AI adımı"]["status"] == "WAITING_APPROVAL", "AI adımı onaya gelmeli", 90)
        ai_id = tasks["AI adımı"]["id"]
        run = client.get(f"/api/v1/projects/{pid}/test-runs", headers=member).json()["runs"][0]
        assert run["task_id"] == ai_id and run["ref"] == "adim-1-ai-adimi" and run["status"] == "FAILED"
        assert any(e["kind"] == "TEST_RUN" and e["task_id"] == ai_id for e in flow["events"])
        msgs = client.get(f"/api/v1/chat/history/{ai_id}", headers=admin)
        assert msgs.status_code == 200, msgs.text
        # Görev sohbeti (Work Area): çıktıdan sonra sistemin yazdığı gerçek sonuç + AI değerlendirmesi ayrı mesaj
        text = json.dumps(msgs.json(), ensure_ascii=False)
        assert "Gerçek test koşusu" in text and "Test Uzmanı değerlendirmesi" in text and "test_randevu_cakisma" in text
    finally:
        _cleanup(client, admin, pid, base)


def test_failed_tests_send_back_to_developer(client, world, db, coder, fake_sandbox):  # noqa: F811
    """Testler kalınca: geliştiriciye 'Test düzeltmesi 1' (test adımı onaylanınca başlar) + test uzmanına 'Yeniden test 1';
    yeniden test de kalırsa 2. tur açılır; akış yeni adımları kendiliğinden yürütür."""
    from datetime import date, timedelta

    from tests.test_workflow import _exec
    w = world
    admin = w["admin"]["h"]
    _exec(db, "UPDATE actors SET role = 'Test Uzmanı' WHERE id = %s", w["reviewer"])
    pid = client.post("/api/v1/projects", headers=admin, json={"tenant_id": w["tenant"], "name": "Düzeltme Döngüsü", "requirements": "Kod + test"}).json()["id"]
    base = f"/api/v1/projects/{pid}/repository"
    try:
        steps = [{"key": "S1", "title": "Randevu modülü", "estimated_days": 1, "agent_id": w["agent"]},
                 {"key": "S2", "title": "Testler", "estimated_days": 1, "agent_id": w["reviewer"], "depends_on": ["S1"]}]
        assert client.put(f"/api/v1/projects/{pid}/plan", headers=admin, json={"summary": "s", "steps": steps}).status_code == 200
        assert client.post(f"/api/v1/projects/{pid}/plan/approve", headers=admin).status_code == 200
        start = date.today()
        client.put(f"/api/v1/projects/{pid}", headers=admin, json={"start_date": start.isoformat(), "end_date": (start + timedelta(days=10)).isoformat()})
        assert client.post(f"/api/v1/projects/{pid}/status", headers=admin, json={"action": "mark_ready"}).status_code == 200
        assert client.put(base, headers=admin, json={"mode": "RECORION"}).status_code == 200
        client.post(f"/api/v1/projects/{pid}/status", headers=admin, json={"action": "start"})
        approve = lambda tid: client.post(f"/api/v1/tasks/{tid}/decision", headers=admin, json={"approve": True})  # noqa: E731

        t, _ = _wait(client, admin, pid, lambda t, f: t["Randevu modülü"]["status"] == "WAITING_APPROVAL", "geliştirici adımı onaya gelmeli", 90)
        assert approve(t["Randevu modülü"]["id"]).status_code == 200
        t, f = _wait(client, admin, pid, lambda t, f: t["Testler"]["status"] == "WAITING_APPROVAL", "test adımı onaya gelmeli", 90)
        fix, retest = t.get("Test düzeltmesi 1: Randevu modülü"), t.get("Yeniden test 1: Testler")
        assert fix and retest, list(t)
        assert fix["assignee"]["id"] == w["agent"] and fix["depends_on"] == [t["Testler"]["id"]] and fix["status"] in ("BACKLOG", "READY")
        assert retest["assignee"]["id"] == w["reviewer"] and retest["depends_on"] == [fix["id"]]
        assert any(e["kind"] == "TEST_FIX_LOOP" for e in f["events"])
        # Test adımı onaylanınca düzeltme kendiliğinden başlar, ardından yeniden test; o da kalınca 2. tur açılır
        assert approve(t["Testler"]["id"]).status_code == 200
        t, _ = _wait(client, admin, pid, lambda t, f: t["Test düzeltmesi 1: Randevu modülü"]["status"] == "WAITING_APPROVAL", "düzeltme adımı çalışmalı", 90)
        assert approve(t["Test düzeltmesi 1: Randevu modülü"]["id"]).status_code == 200
        t, _ = _wait(client, admin, pid, lambda t, f: "Test düzeltmesi 2: Randevu modülü" in t, "2. düzeltme turu açılmalı", 90)
        assert t["Yeniden test 2: Testler"]["assignee"]["id"] == w["reviewer"]
        assert len([r for r in client.get(f"/api/v1/projects/{pid}/test-runs", headers=admin).json()["runs"]]) == 2
    finally:
        _exec(db, "UPDATE actors SET role = 'Uzman' WHERE id = %s", w["reviewer"])
        _cleanup(client, admin, pid, base)


def _sandbox_up() -> bool:
    try:
        return httpx.get(settings.SANDBOX_URL.rstrip("/") + "/health", timeout=5).json().get("ok") is True
    except Exception:
        return False


@pytest.mark.skipif(not settings.SANDBOX_URL or not _sandbox_up(), reason="Sandbox servisi erişilemiyor")
def test_real_sandbox_runs_pytest_offline():
    import asyncio
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("proje/requirements.txt", "")
        z.writestr("proje/app.py", "def topla(a, b):\n    return a + b\n")
        z.writestr("proje/tests/test_app.py",
                   "import socket\nfrom app import topla\n\n"
                   "def test_topla():\n    assert topla(2, 3) == 5\n\n"
                   "def test_hatali():\n    assert topla(2, 2) == 5\n\n"
                   "def test_internet_yok():\n    try:\n        socket.create_connection(('1.1.1.1', 53), timeout=3)\n"
                   "        assert False, 'internet açık'\n    except OSError:\n        pass\n")
        z.writestr("proje/conftest.py", "import sys, os\nsys.path.insert(0, os.path.dirname(__file__))\n")
    res = asyncio.run(sandbox.execute(buf.getvalue()))
    t = res["projects"][0]["test"]
    assert res["status"] == "FAILED" and t["passed"] == 2 and t["failed"] == 1, res
    assert t["failures"][0]["name"].endswith("test_hatali")
