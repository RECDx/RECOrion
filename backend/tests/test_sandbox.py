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


def test_failed_tests_send_back_to_developer(client, world, db, coder, fake_sandbox, monkeypatch):  # noqa: F811
    """Testler kalınca (Aşama 2 bulgularıyla yeniden: F100/F103/F105/F109):
    - geliştiriciye 'Test düzeltmesi 1' HEMEN başlar (test adımının onayını beklemez), 'Yeniden test 1' düzeltme + test adımı
      bitince çalışır; yeni adımlarda kontrol personeli yoktur;
    - açık tur varken test adımı yeniden koşup yine kalırsa yeni tur AÇILMAZ (TEST_FIX_UPDATED);
    - yeniden test de kalınca 2. tur açılır; ardından testler geçince açık tur kendiliğinden kapanır."""
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
        decide = lambda tid, ok=True, note=None: client.post(f"/api/v1/tasks/{tid}/decision", headers=admin,  # noqa: E731
                                                             json={"approve": ok, "note": note, "force": True})
        F1, R1 = "Test düzeltmesi 1: Randevu modülü", "Yeniden test 1: Testler"

        t, _ = _wait(client, admin, pid, lambda t, f: t["Randevu modülü"]["status"] == "WAITING_APPROVAL", "geliştirici adımı onaya gelmeli", 90)
        assert decide(t["Randevu modülü"]["id"]).status_code == 200
        # Test adımı onaylanmadan düzeltme kendiliğinden başlar ve onaya gelir (F103)
        t, f = _wait(client, admin, pid, lambda t, f: t["Testler"]["status"] == "WAITING_APPROVAL" and F1 in t
                     and t[F1]["status"] == "WAITING_APPROVAL", "düzeltme test onayını beklemeden çalışmalı", 120)
        fix, retest = t[F1], t[R1]
        assert fix["assignee"]["id"] == w["agent"] and fix["depends_on"] == [] and fix["fix_kind"] == "FIX" and fix["reviewer"] is None
        assert retest["assignee"]["id"] == w["reviewer"] and set(retest["depends_on"]) == {fix["id"], t["Testler"]["id"]}
        assert retest["fix_of_task_id"] == t["Testler"]["id"] and retest["status"] in ("BACKLOG", "READY")
        assert any(e["kind"] == "TEST_FIX_LOOP" for e in f["events"])
        # Açık tur varken test adımı revizyonla yeniden koşup yine kalır: yeni tur açılmaz (F100)
        assert decide(t["Testler"]["id"], False, "Bir test daha ekle").status_code == 200
        t, f = _wait(client, admin, pid, lambda t, f: any(e["kind"] == "TEST_FIX_UPDATED" for e in f["events"])
                     and t["Testler"]["status"] == "WAITING_APPROVAL", "açık tur güncellenmeli", 120)
        assert "Test düzeltmesi 2: Randevu modülü" not in t
        # Düzeltme + test adımı onaylanınca yeniden test çalışır; o da kalınca 2. tur açılır
        assert decide(t[F1]["id"]).status_code == 200
        assert decide(t["Testler"]["id"]).status_code == 200
        t, _ = _wait(client, admin, pid, lambda t, f: "Test düzeltmesi 2: Randevu modülü" in t and t[R1]["status"] == "WAITING_APPROVAL",
                     "2. düzeltme turu açılmalı", 120)
        assert t["Yeniden test 2: Testler"]["assignee"]["id"] == w["reviewer"]
        assert len(client.get(f"/api/v1/projects/{pid}/test-runs", headers=admin).json()["runs"]) == 3
        # Yeniden test 1 revizyonla tekrar koşar ve bu kez geçer: açık 2. tur kendiliğinden kapanır (F105)
        passed = {**FAKE, "status": "PASSED", "projects": [{**FAKE["projects"][0], "test": {**FAKE["projects"][0]["test"],
                                                                                          "passed": 4, "failed": 0, "status": "PASSED", "failures": []}}]}

        async def execute(archive):
            return passed
        monkeypatch.setattr(sandbox, "execute", execute)
        assert decide(t[R1]["id"], False, "Yeniden çalıştır").status_code == 200
        t, f = _wait(client, admin, pid, lambda t, f: t["Test düzeltmesi 2: Randevu modülü"]["status"] == "CANCELLED"
                     and t["Yeniden test 2: Testler"]["status"] == "CANCELLED", "testler geçince açık tur kapanmalı", 120)
        assert any(e["kind"] == "TEST_FIX_CLOSED" for e in f["events"])
    finally:
        _exec(db, "UPDATE actors SET role = 'Uzman' WHERE id = %s", w["reviewer"])
        _cleanup(client, admin, pid, base)


def test_pick_developer_scoring():
    """F99: kalan testlerde geçen dosyaları yazan geliştirici seçilir; test/doküman dosyaları puan almaz."""
    text = "FAILED tests/test_api.py::test_login - File \"/work/src/auth.py\", line 12 in verify_password"
    backend = ["src/auth.py", "src/main.py", "docs/adimlar/02-backend.md"]
    frontend = ["src/frontend/js/api.js", "src/frontend/index.html"]
    assert sandbox._score(backend, text) > 0 and sandbox._score(frontend, text) == 0
    assert sandbox._score(["tests/test_api.py", "docs/adimlar/04-test.md"], text) == 0


def test_test_specialist_paths():
    """F104: test uzmanı yalnız test dosyalarını, test yapılandırmasını, recorion.json ve README'yi depoya yazar."""
    from app.services.code_repo import is_test_path
    for ok in ("tests/test_api.py", "conftest.py", "src/frontend/tests/frontend.test.js", "requirements.txt", "recorion.json",
               "README.md", "docs/adimlar/04-test.md", "scripts/recorion_test.sh", "app/user_test.py", "web/login.spec.ts"):
        assert is_test_path(ok), ok
    for bad in ("src/auth.py", "src/main.py", "src/frontend/js/api.js", "src/db/seed.py", "main.py"):
        assert not is_test_path(bad), bad


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
