"""
İSTEK #754: Beyin AI deneme seti.

- Yalnız Süper Admin koşturur/görür; aynı anda tek koşu.
- Brif test şirketinde projeye dönüşür; keşif turlarında yöneticiyi RECAi cevap anahtarıyla oynar; tanım onaylanır, plan
  önerilir, değerlendirilir ve proje gerekçeyle iptal edilir. Deneme projeleri öğrenme kaydı üretmez.
- Puan: keşif (ortaya çıkan + belgeye giren anahtar maddeleri), tanım, plan yapısı, doğrulama; önceki koşuyla fark.
"""
import json

from tests.test_integrations import _super
from tests.test_workflow import _exec, world  # noqa: F401  (fikstür)

CASE = {"code": "t1", "title": "Deneme tur sitesi", "sector": "Turizm", "brief": "Tur sitesi istiyoruz.",
        "expect": {"software": True, "human": True},
        "key": [{"id": "k1", "topic": "Kapsam", "fact": "Bölgeye göre süzgeç"}, {"id": "k2", "topic": "Kısıt", "fact": "Sahte ödeme"},
                {"id": "k3", "topic": "Paydaş", "fact": "Yönetim paneli"}, {"id": "k4", "topic": "Akış", "fact": "Sol menü"}]}


def _fake_llm(monkeypatch, human_id):
    from app.services.evren_client import ChatResult, evren_client

    calls = {"discovery": 0, "manager": 0, "plan": 0, "judge": 0}

    async def chat(model_code, messages, **kw):
        p = messages[-1]["content"]
        if "canlandırıyorsun" in p:
            calls["manager"] += 1
            ids = [ln.split(":")[0].strip("- ").strip() for ln in p.split("# Sorular")[1].strip().splitlines() if ln.startswith("- ")]
            out = {"answers": [{"id": i, "answer": "Bölgeye göre süzgeç olmalı.", "facts": ["k1", "k9"]} for i in ids]}
        elif "değerlendiriyorsun" in p:
            calls["judge"] += 1
            out = {"in_charter": ["k2", "kx"], "in_plan": ["k1", "k2"], "structure": 8, "note": "Menü eksik"}
        elif "keşif görüşmesi" in p:
            calls["discovery"] += 1
            out = {"charter": {"goal": "Tur satışı", "success_criteria": ["aylık 50 rezervasyon"], "scope_in": ["katalog"], "scope_out": ["gerçek ödeme"],
                               "users_roles": ["ziyaretçi"], "deliverables": [{"name": "Site", "acceptance": "süzgeç çalışır", "verification": "tarayıcı testi"}],
                               "workflows": ["ziyaretçi süzer → rezervasyon"], "risks": ["kontenjan"]},
                   "maturity": {"score": 60 + 10 * calls["discovery"], "missing": []},
                   "questions": [{"topic": "Kapsam", "text": "Turlar nasıl süzülecek?", "why": "liste"}], "reminders": [], "research_suggestions": []}
        elif "planlıyorsun" in p:
            calls["plan"] += 1
            out = {"summary": "plan", "steps": [
                {"key": "S1", "title": "Arayüz ve kullanım tasarımı", "deliverable": "Ekran haritası", "verification": "Menüden tüm sayfalara iki tıkla gidilir", "verification_type": "TEST", "estimated_days": 2},
                {"key": "S2", "title": "Backend", "deliverable": "API", "verification": "kod var", "estimated_days": 2},
                {"key": "S3", "title": "Kullanıcı kabul testi", "deliverable": "Kabul raporu", "verification": "Tanım belgesindeki akışlar tarayıcıda denenir",
                 "verification_type": "HUMAN", "assignee_human_id": human_id, "estimated_days": 1, "depends_on": ["S1", "S2"]}],
                   "hire_suggestions": [], "risks": [], "questions": []}
        else:  # önceki testlerden kalan arka plan çağrıları (ör. ders çıkarma) sayılmaz
            out = {}
        return ChatResult(json.dumps(out, ensure_ascii=False), None, 100, 50, {})
    monkeypatch.setattr(evren_client, "chat", chat)
    return calls


def test_brain_bench_run_scores_and_cleans_up(client, db, world, monkeypatch):  # noqa: F811
    from app.services import brain_bench as bb

    w = world
    slug = _exec(db, "SELECT slug FROM tenants WHERE id = %s", w["tenant"])[0]
    human_id = _exec(db, "SELECT id::text FROM actors WHERE tenant_id = %s AND actor_type = 'HUMAN' ORDER BY created_at LIMIT 1", w["tenant"])[0]
    monkeypatch.setattr(bb, "TEST_TENANT_SLUG", slug)
    _exec(db, "UPDATE brain_bench_runs SET status = 'FAILED' WHERE status = 'RUNNING'")  # önceki yarım test koşusu engellemesin
    monkeypatch.setattr(bb, "cases", lambda: [CASE])
    calls = _fake_llm(monkeypatch, human_id)
    spawned = []
    monkeypatch.setattr(bb, "spawn", lambda rid: spawned.append(rid))
    sa = _super(client, db)

    # yetki: şirket yöneticisi göremez ve koşturamaz
    assert client.get("/api/v1/system/brain-bench/cases", headers=w["admin"]["h"]).status_code == 403
    assert client.post("/api/v1/system/brain-bench/runs", headers=w["admin"]["h"], json={}).status_code == 403
    assert client.get("/api/v1/system/brain-bench/cases", headers=sa).json()["cases"][0]["code"] == "t1"

    r = client.post("/api/v1/system/brain-bench/runs", headers=sa, json={"label": "ilk"})
    assert r.status_code == 202 and r.json()["status"] == "RUNNING" and r.json()["case_codes"] == ["t1"]
    # aynı anda ikinci koşu yok
    assert client.post("/api/v1/system/brain-bench/runs", headers=sa, json={}).status_code == 409

    client.portal.call(bb.execute, spawned[0])
    assert calls == {"discovery": 3, "manager": 2, "plan": 1, "judge": 1}  # 3 keşif turu, aradaki 2 yanıt
    run = client.get(f"/api/v1/system/brain-bench/runs/{r.json()['id']}", headers=sa).json()
    assert run["status"] == "DONE", run
    res = run["results"][0]
    assert "error" not in res, res
    s, d = res["scores"], res["details"]
    # keşif: k1 (yöneticiden; k9 anahtarda yok) + k2 (belgede; kx yok) → 2/4
    assert d["found"] == ["k1", "k2"] and s["discovery"] == 15.0
    assert d["plan_checks"] == {"ui_step": True, "acceptance_step": True, "human_step": True, "not_layered": True}
    assert s["plan"] == 22.0  # 15 × 8/10 + 10
    assert d["verified_steps"] == 2 and s["verification"] == round(10 * 2 / 3 + 15 * 2 / 4, 1)
    assert s["charter"] == round(12 + 8 * 0.9, 1)  # tüm bölümler + olgunluk %90
    assert run["total"] == s["total"] and res["rounds"] == 3
    assert any("Sol menü" in m for m in d["missed"])

    # proje gerekçeyle iptal edildi, öğrenme kaydı yok
    pid = res["project_id"]
    assert _exec(db, "SELECT status, close_summary FROM projects WHERE id = %s", pid)[0] == "CANCELLED"
    assert _exec(db, "SELECT count(*) FROM learning_records WHERE project_id = %s", pid)[0] == 0

    # ikinci koşu: önceki tamamlanmış koşuyla fark
    r2 = client.post("/api/v1/system/brain-bench/runs", headers=sa, json={"codes": ["t1", "yok"]})
    assert r2.json()["case_codes"] == ["t1"]
    client.portal.call(bb.execute, spawned[1])
    runs = client.get("/api/v1/system/brain-bench/runs", headers=sa).json()
    assert runs[0]["id"] == r2.json()["id"] and runs[0]["previous_id"] == run["id"]
    assert set(runs[0]["delta"]["t1"]) == {"discovery", "charter", "plan", "verification", "total"}


def test_brain_bench_failure_is_recorded_per_case(client, db, world, monkeypatch):  # noqa: F811
    """EVREN yanıt veremezse brif hata gerekçesiyle kalır, proje yine kapatılır, koşu FAILED olur."""
    from app.services import brain_bench as bb
    from app.services.evren_client import evren_client

    w = world
    monkeypatch.setattr(bb, "TEST_TENANT_SLUG", _exec(db, "SELECT slug FROM tenants WHERE id = %s", w["tenant"])[0])
    monkeypatch.setattr(bb, "cases", lambda: [CASE])
    spawned = []
    monkeypatch.setattr(bb, "spawn", lambda rid: spawned.append(rid))
    _exec(db, "UPDATE brain_bench_runs SET status = 'FAILED' WHERE status = 'RUNNING'")

    async def broken(model_code, messages, **kw):
        raise RuntimeError("EVREN yanıtsız")
    monkeypatch.setattr(evren_client, "chat", broken)
    sa = _super(client, db)
    rid = client.post("/api/v1/system/brain-bench/runs", headers=sa, json={}).json()["id"]
    client.portal.call(bb.execute, spawned[0])
    run = client.get(f"/api/v1/system/brain-bench/runs/{rid}", headers=sa).json()
    assert run["status"] == "FAILED" and run["results"][0]["error"].startswith("keşif")
    assert _exec(db, "SELECT status FROM projects WHERE id = %s", run["results"][0]["project_id"])[0] == "CANCELLED"
