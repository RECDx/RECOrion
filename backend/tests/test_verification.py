"""
İSTEK #752: Teslimata göre doğrulama, kapsam raporu ve kalite kapısı.

- Plan adımı teslimat + doğrulama (tür, yöntem) taşır; plan onayında göreve geçer (kontrol listesi maddeleri yöntemden çıkar).
- Doğrulaması eksik adım onaya gelince uyarı görünür, onay 409 TEST_GATE (needs_reason) döner; eksikle onay ancak gerekçeyle,
  VERIFICATION_WAIVED olarak kayda geçer. Kontrol listesi işaretlenince onay doğrudan geçer.
- Kapsam raporu "N teslimattan M tanesi doğrulandı"; tamamlanan adımda doğrulama eksikse proje kabulü gerekçe ister.
- Yazılım: ana daldaki denetimlerin dalda silinmesi/gevşetilmesi tespit edilir.
"""
from datetime import date, timedelta

from app.services import verification
from app.services.project_planning import validate_plan
from tests.test_workflow import _wait, ai, world  # noqa: F401  (fikstür)


def test_plan_fields_checklist_and_loosening():
    plan = validate_plan({"summary": "s", "steps": [
        {"key": "S1", "title": "İç denetim", "deliverable": "ISO 9001 iç denetimi", "verification_type": "checklist",
         "verification": "Denetim kontrol listesi tamam; uygunsuzluk kapanış kanıtları; yönetim gözden geçirmesi"},
        {"key": "S2", "title": "Saha ölçümü", "verification_type": "BILINMEYEN", "verification": "OEE ölçülür"}]}, set())
    s1, s2 = plan["steps"]
    assert s1["deliverable"] == "ISO 9001 iç denetimi" and s1["verification_type"] == "CHECKLIST"
    assert s2["verification_type"] == "EVIDENCE"  # bilinmeyen tür kanıta düşer
    v = verification.init_for_task(s1, human=False)
    assert [i["item"] for i in v["checklist"]] == ["Denetim kontrol listesi tamam", "uygunsuzluk kapanış kanıtları", "yönetim gözden geçirmesi"]
    assert verification.init_for_task({"title": "eski plan"}, False) is None

    # otomatik test türündeki teslimatın kodu teslimde sistemce çalıştırılır ("verify"); çıktı istemine teslimat girer
    from app.db.models import Actor, Task
    from app.services import agent_work, sandbox
    import pytest
    mp = pytest.MonkeyPatch()
    mp.setattr(sandbox, "enabled", lambda: True)
    mp.setattr(agent_work.code_repo, "active", lambda p: True)
    try:
        dev = Actor(role="Yazılım Geliştirici")
        t = Task(title="Turlar sayfası filtresi", deliverable="Bölge/fiyat filtresi",
                 verification={"type": "TEST", "method": "'Yurt dışı' seçilince yalnız yurt dışı turları görünür"})
        assert agent_work._runs_tests(None, dev, t) == "verify"
        assert agent_work._runs_tests(None, dev, Task(title="Analiz", verification={"type": "EVIDENCE"})) is False
        assert "Doğrulama (Otomatik test): 'Yurt dışı'" in agent_work._deliverable_lines(t)
    finally:
        mp.undo()

    base = '{"checks": [{"name": "Giriş", "type": "http", "expect_status": 200, "expect_text": "token"},' \
           ' {"name": "Filtre", "type": "browser", "steps": [{"click": "#f"}, {"expect_text": "Yurt dışı"}]}, {"name": "Sağlık", "type": "http"}]}'
    ref = '{"checks": [{"name": "Giriş", "type": "http", "expect_status": 200}, {"name": "Sağlık", "type": "http"}]}'
    assert verification.loosened_checks(base, ref) == [{"name": "Giriş", "change": "beklenti 2 → 1"}, {"name": "Filtre", "change": "silindi"}]
    assert verification.loosened_checks(base, base) == [] and verification.loosened_checks(None, ref) == []


def _project(client, w, name, steps):
    h = w["admin"]["h"]
    pid = client.post("/api/v1/projects", headers=h, json={"tenant_id": w["tenant"], "name": name, "requirements": "Doğrulama"}).json()["id"]
    assert client.put(f"/api/v1/projects/{pid}/plan", headers=h, json={"summary": "s", "steps": steps}).status_code == 200
    assert client.post(f"/api/v1/projects/{pid}/plan/approve", headers=h).status_code == 200
    start = date.today()
    client.put(f"/api/v1/projects/{pid}", headers=h, json={"start_date": start.isoformat(), "end_date": (start + timedelta(days=10)).isoformat()})
    assert client.post(f"/api/v1/projects/{pid}/status", headers=h, json={"action": "mark_ready"}).status_code == 200
    return pid


def test_verification_gate_coverage_and_acceptance(client, world, ai):  # noqa: F811
    w = world
    h, member = w["admin"]["h"], w["member"]["h"]
    pid = _project(client, w, "Doğrulama Projesi", [
        {"key": "S1", "title": "İç denetim raporu", "estimated_days": 1, "agent_id": w["agent"], "deliverable": "İç denetim raporu",
         "verification_type": "CHECKLIST", "verification": "Tüm maddeler denetlendi; uygunsuzluklar kapatıldı"},
        {"key": "S2", "title": "OEE ölçümü", "estimated_days": 1, "agent_id": w["agent"], "deliverable": "Pilot hat OEE değeri",
         "verification_type": "MEASURE", "verification": "OEE ölçülür, hedef %65", "requires_approval": False, "depends_on": ["S1"]}])
    cov = client.get(f"/api/v1/projects/{pid}/verification", headers=h).json()
    assert cov["total"] == 2 and cov["summary"].startswith("2 teslimattan 0 tanesi doğrulandı"), cov["summary"]
    assert {r["type"] for r in cov["rows"]} == {"CHECKLIST", "MEASURE"}
    client.post(f"/api/v1/projects/{pid}/status", headers=h, json={"action": "start"})

    t, f = _wait(client, h, pid, lambda t, f: t["İç denetim raporu"]["status"] == "WAITING_APPROVAL", "S1 onaya gelmeli", 60)
    s1 = t["İç denetim raporu"]
    assert s1["verification"]["status"] == "MISSING" and "Teslimat doğrulanmadı (Kontrol listesi" in s1["acceptance_warning"]
    r = client.post(f"/api/v1/tasks/{s1['id']}/decision", headers=h, json={"approve": True})
    assert r.status_code == 409 and r.json()["detail"]["code"] == "TEST_GATE" and r.json()["detail"]["needs_reason"] is True
    assert client.post(f"/api/v1/tasks/{s1['id']}/decision", headers=h, json={"approve": True, "force": True}).status_code == 422
    # kontrol listesini yetkisiz üye işaretleyemez; yönetici işaretler, onay doğrudan geçer
    url = f"/api/v1/tasks/{s1['id']}/verification/checklist"
    assert client.put(url, headers=member, json={"items": [True, True]}).status_code == 403
    assert client.put(url, headers=h, json={"items": [True, False]}).json()["status"] == "MISSING"
    assert client.put(f"/api/v1/tasks/{s1['id']}/verification/measure", headers=h, json={"value": "5"}).status_code == 409  # tür uyumsuz
    assert client.put(url, headers=h, json={"items": [True, True]}).json()["status"] == "VERIFIED"
    assert client.post(f"/api/v1/tasks/{s1['id']}/decision", headers=h, json={"approve": True}).status_code == 200

    # S2 onay gerektirmez: ölçüm girilmeden tamamlanır → kapsamda eksik kalır
    t, f = _wait(client, h, pid, lambda t, f: t["OEE ölçümü"]["status"] == "DONE", "S2 tamamlanmalı", 60)
    cov = client.get(f"/api/v1/projects/{pid}/verification", headers=h).json()
    by = {r["title"]: r for r in cov["rows"]}
    assert by["İç denetim raporu"]["status"] == "VERIFIED" and by["OEE ölçümü"]["status"] == "MISSING"
    assert cov["summary"] == "2 teslimattan 1 tanesi doğrulandı, 1 tanesinde doğrulama eksik"
    assert client.put(f"/api/v1/tasks/{by['OEE ölçümü']['task_id']}/verification/measure", headers=h, json={"value": "61"}).status_code == 409  # kapandı

    # proje kabulü: eksik teslimat varsa gerekçe gerekir ve kayda geçer
    st = f"/api/v1/projects/{pid}/status"
    r = client.post(st, headers=h, json={"action": "complete", "summary": "bitti"})
    assert r.status_code == 409 and r.json()["detail"]["code"] == "COVERAGE_GATE" and "OEE ölçümü" in r.json()["detail"]["message"]
    assert client.post(st, headers=h, json={"action": "complete", "summary": "kısa", "accept_gaps": True}).status_code == 422
    r = client.post(st, headers=h, json={"action": "complete", "summary": "Ölçüm cihazı arızalı; OEE bir sonraki ay ölçülecek.", "accept_gaps": True})
    assert r.status_code == 200, r.text
    events = client.get(f"/api/v1/projects/{pid}/workflow", headers=h).json()["events"]
    assert any(e["kind"] == "ACCEPTED_WITH_GAPS" for e in events)


def test_waive_with_reason_is_recorded(client, world, ai):  # noqa: F811
    w = world
    h = w["admin"]["h"]
    pid = _project(client, w, "Gerekçeli Kabul", [
        {"key": "S1", "title": "Pilot ölçüm", "estimated_days": 1, "agent_id": w["agent"], "deliverable": "Çevrim süresi",
         "verification_type": "MEASURE", "verification": "Çevrim süresi ölçülür"}])
    client.post(f"/api/v1/projects/{pid}/status", headers=h, json={"action": "start"})
    t, _ = _wait(client, h, pid, lambda t, f: t["Pilot ölçüm"]["status"] == "WAITING_APPROVAL", "onaya gelmeli", 60)
    tid = t["Pilot ölçüm"]["id"]
    r = client.post(f"/api/v1/tasks/{tid}/decision", headers=h, json={"approve": True, "force": True, "note": "Cihaz yok, tahmini değer kabul"})
    assert r.status_code == 200, r.text
    _, f = _wait(client, h, pid, lambda t, f: t["Pilot ölçüm"]["status"] == "DONE", "tamamlanmalı", 30)
    assert any(e["kind"] == "VERIFICATION_WAIVED" and "Cihaz yok" in (e["note"] or "") for e in f["events"])
    row = client.get(f"/api/v1/projects/{pid}/verification", headers=h).json()["rows"][0]
    assert row["status"] == "WAIVED" and row["waived"]["reason"] == "Cihaz yok, tahmini değer kabul"
    # gerekçeyle kabul edilen adım proje kabulünü engellemez
    assert client.post(f"/api/v1/projects/{pid}/status", headers=h, json={"action": "complete", "summary": "tamam"}).status_code == 200
