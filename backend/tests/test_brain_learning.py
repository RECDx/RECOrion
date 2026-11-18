"""
İSTEK #753: Beyin AI öğrenme etiketleri (#742 kayıtları üzerinde).

- Keşif: tanım belgesi onayında sorulan sorular ve yanıtlanıp belgeye girenler kaydedilir (eşik altı onay BELIRSIZ).
- Plan: önerilen planın kopyası saklanır; geri bildirimle yeniden istenen öneri YANLIS (ret) olur; onayda yöneticinin değişikliği
  ölçülür, onaylanan plan DOGRU, belirgin değiştirilen öneri YANLIS ve ikisi tercih çifti olarak eşlenir; aynı öneri yeniden
  onaylanınca ikinci kayıt yazılmaz.
- Web araştırması: tek tık fayda değerlendirmesi (yeniden değerlendirmede aynı kayıt güncellenir; yalnız yönetici, yalnız biten).
- Proje sonucu: kapanışta kapsam uyumu; eksikle kapanışta onaylı plan kaydı BELIRSIZ'e çekilir (ilk etiket sonuçla güncellenir).
- Sektör paketi önerileri: şirketler arası, k-anonim (eşik altı gizli); yalnız Merkez.
- RECAi veri seti: Beyin kayıtları "Beyin AI" sistem istemiyle girer; dersleri şirket hafızasına aday düşer.
"""
import json
import uuid

from app.services import brain_learning as bl
from tests.test_integrations import _super
from tests.test_sector_packs import _publish_all, _seed
from tests.test_workflow import _exec, world  # noqa: F401  (fikstür)


def test_plan_diff_and_snapshot():
    sugg = {"summary": "s", "steps": [{"key": "S1", "title": "Saha keşfi", "estimated_days": 2}, {"key": "S2", "title": "Pilot hat", "agent_id": "a"},
                                      {"key": "S3", "title": "Eğitim planı", "estimated_days": 1}]}
    snap = bl.plan_snapshot({**sugg, "model_code": "m", "generated_at": "t"})
    assert snap["steps"][0]["title"] == "Saha keşfi" and snap["generated_at"] == "t"
    same = bl.plan_diff(snap, {"steps": [dict(s) for s in sugg["steps"]]})
    assert same["ratio"] == 0 and same["verdict"] == "KABUL"
    final = {"steps": [{"title": "saha  keşfi!", "estimated_days": 2}, {"title": "Pilot hat", "agent_id": "b"}, {"title": "Kullanıcı eğitimi"}]}
    d = bl.plan_diff(snap, final)
    assert d["added"] == ["Kullanıcı eğitimi"] and d["removed"] == ["Eğitim planı"] and d["changed"] == ["Pilot hat"]
    assert d["ratio"] == round(2.5 / 3, 2) and d["verdict"] == "DEGISTIRILEREK_KABUL"


def _records(db, pid, source):
    rows = []
    with db.cursor() as cur:
        cur.execute("SELECT id, label, data, pair_id, output, feedback, job_title, agent_id FROM learning_records "
                    "WHERE project_id = %s AND source = %s ORDER BY created_at", (pid, source))
        for r in cur.fetchall():
            rows.append(dict(zip(("id", "label", "data", "pair_id", "output", "feedback", "job_title", "agent_id"), r)))
    return rows


def test_brain_learning_labels_end_to_end(client, db, world, monkeypatch):  # noqa: F811
    from app.services import reports
    from app.services.evren_client import ChatResult, evren_client

    w = world
    h, member = w["admin"]["h"], w["member"]["h"]
    _seed(client)
    sa = _super(client, db)
    packs = _publish_all(client, sa)
    pid = client.post("/api/v1/projects", headers=h, json={
        "tenant_id": w["tenant"], "name": f"Beyin {uuid.uuid4().hex[:4]}",
        "requirements": "Fabrikadaki makinelerin duruşlarını ve OEE değerini izleyen üretim takip sistemi."}).json()["id"]

    calls = {"discovery": 0}

    async def chat(model_code, messages, **kw):
        text = messages[-1]["content"]
        if "keşif görüşmesi" in text:
            calls["discovery"] += 1
            qs = [{"topic": "Kapsam", "text": "Kaç makine izlenecek?", "why": "kapsam"},
                  {"topic": "Kısıtlar", "text": "PLC erişimi var mı?", "why": "veri"}] if calls["discovery"] == 1 else []
            out = {"charter": {"goal": "OEE izleme", "deliverables": [{"name": "Pilot hat OEE panosu", "acceptance": "veri", "verification": "ölçüm"},
                                                                       {"name": "Vardiya raporu", "acceptance": "rapor", "verification": "kanıt"}]},
                   "maturity": {"score": 80, "missing": []}, "questions": qs, "reminders": [], "research_suggestions": []}
        elif "RECAi" in text or "öğrenme motoru" in (messages[0].get("content") or ""):
            out = {"neden": "DEGERLENDIRICI", "neden_gerekce": "zevk", "ders": "", "kapsam": "AGENT"}
        else:
            out = {"summary": "plan", "steps": [
                {"key": "S1", "title": "Saha keşfi", "acceptance_criteria": "envanter raporu", "agent_id": "", "estimated_days": 2, "depends_on": [],
                 "deliverable": "Makine envanteri", "verification_type": "EVIDENCE", "verification": "Envanter tablosu"},
                {"key": "S2", "title": "Pilot hat kurulumu", "acceptance_criteria": "veri geliyor", "agent_id": "", "estimated_days": 3,
                 "depends_on": ["S1"], "deliverable": "Pilot hat OEE panosu", "verification_type": "MEASURE", "verification": "OEE ölçülür"}],
                   "hire_suggestions": [], "risks": [], "questions": []}
        return ChatResult(json.dumps(out, ensure_ascii=False), None, 100, 50, {})
    monkeypatch.setattr(evren_client, "chat", chat)

    # --- keşif: 2 soru soruldu, biri yanıtlandı; onayda kayıt
    r1 = client.post(f"/api/v1/projects/{pid}/discovery/round", headers=h, json={"answers": []}).json()
    q1, q2 = r1["pending"]
    assert client.post(f"/api/v1/projects/{pid}/discovery/round", headers=h,
                       json={"answers": [{"id": q1["id"], "answer": "12 makine"}, {"id": q2["id"], "answer": ""}]}).status_code == 200
    assert client.post(f"/api/v1/projects/{pid}/discovery/approve", headers=h, json={}).status_code == 200
    (disc,) = _records(db, pid, "BRAIN_DISCOVERY")
    assert disc["label"] == "DOGRU" and disc["data"]["asked"] == 2 and disc["data"]["answered"] == 1
    assert disc["job_title"] == "Beyin AI" and disc["agent_id"] is None and "OEE izleme" in disc["output"]

    # --- plan: ilk öneri; geri bildirimle yeniden istenince önceki öneri ret kaydı olur
    assert client.post(f"/api/v1/projects/{pid}/plan/suggest", headers=h, json={}).status_code == 200
    assert _records(db, pid, "BRAIN_PLAN") == []
    assert client.post(f"/api/v1/projects/{pid}/plan/suggest", headers=h, json={"feedback": "Eğitim adımı unutulmuş"}).status_code == 200
    (rej,) = _records(db, pid, "BRAIN_PLAN")
    assert rej["label"] == "YANLIS" and "Eğitim adımı unutulmuş" in rej["feedback"] and rej["data"]["verdict"] == "RET"

    # yönetici planı düzenler (adım ekler, birini değiştirir); öneri kopyası korunur
    plan = client.get(f"/api/v1/projects/{pid}", headers=h).json()["plan"]
    steps = plan["steps"]
    steps[1]["estimated_days"] = 5
    steps.append({"key": "S3", "title": "Operatör eğitimi", "estimated_days": 1, "depends_on": ["S2"]})
    assert client.put(f"/api/v1/projects/{pid}/plan", headers=h, json={"summary": "plan", "steps": steps}).status_code == 200
    assert client.get(f"/api/v1/projects/{pid}", headers=h).json()["plan"]["suggested"]["steps"][0]["title"] == "Saha keşfi"
    assert client.post(f"/api/v1/projects/{pid}/plan/approve", headers=h).status_code == 200
    recs = _records(db, pid, "BRAIN_PLAN")
    good = next(r for r in recs if r["label"] == "DOGRU")
    bad = [r for r in recs if r["label"] == "YANLIS"]
    assert good["data"]["added"] == ["Operatör eğitimi"] and good["data"]["changed"] == ["Pilot hat kurulumu"]
    assert good["data"]["verdict"] == "DEGISTIRILEREK_KABUL" and good["data"]["pack_code"] == "uretim-mes"
    assert "Operatör eğitimi" in good["output"] and len(bad) == 2 and all(b["pair_id"] == good["id"] for b in bad)
    assert any("Eklenen adımlar: Operatör eğitimi" in (b["feedback"] or "") for b in bad)
    # aynı öneri yeniden onaylanınca ikinci kayıt yazılmaz
    assert client.post(f"/api/v1/projects/{pid}/plan/approve", headers=h).status_code == 200
    assert len(_records(db, pid, "BRAIN_PLAN")) == 3

    # --- web araştırması: yalnız biten, yalnız yönetici; yeniden değerlendirme aynı kaydı günceller
    rid = str(uuid.uuid4())
    _exec(db, "INSERT INTO web_research (id, tenant_id, project_id, question, masked_question, depth, origin, status, max_credits, spent_credits, result) "
              "VALUES (%s, %s, %s, 'OEE standartları', 'OEE standartları', 'QUICK', 'BRAIN_SUGGESTION', 'DONE', 30, 12.5, %s)",
          rid, w["tenant"], pid, json.dumps({"summary": "OEE = kullanılabilirlik × performans × kalite", "findings": [{"text": "ISO 22400"}], "sources": []}))
    url = f"/api/v1/projects/{pid}/research/{rid}/rating"
    assert client.post(url, headers=member, json={"rating": "USEFUL"}).status_code in (403, 404)
    assert client.post(url, headers=h, json={"rating": "BAŞKA"}).status_code == 422
    assert client.post(url, headers=h, json={"rating": "USELESS"}).json()["rating"] == "USELESS"
    (res,) = _records(db, pid, "BRAIN_RESEARCH")
    assert res["label"] == "YANLIS" and res["data"]["spent_credits"] == 12.5 and "ISO 22400" in res["output"]
    assert client.post(url, headers=h, json={"rating": "USEFUL"}).status_code == 200
    (res,) = _records(db, pid, "BRAIN_RESEARCH")
    assert res["label"] == "DOGRU" and res["data"]["rating"] == "USEFUL"
    _exec(db, "UPDATE web_research SET status = 'RUNNING' WHERE id = %s", rid)
    assert client.post(url, headers=h, json={"rating": "USEFUL"}).status_code == 409

    # --- şirket ekranı: Beyin kayıtları "Beyin AI" adıyla ve kaynak etiketiyle görünür; RECDx göremez (KVKK)
    lst = client.get(f"/api/v1/company/{w['tenant']}/learning/records?source=BRAIN_PLAN", headers=h).json()
    assert lst and all(x["agent_name"] == "Beyin AI" and x["source_label"] == "Beyin · Plan önerisi" for x in lst)
    assert client.get(f"/api/v1/company/{w['tenant']}/learning/records", headers=sa).status_code == 403

    # --- sektör paketi önerileri: k-anonim (tek şirket eşiğin altında gizli), yalnız Merkez
    sug = f"/api/v1/system/sector-packs/{packs['uretim-mes']['id']}/suggestions"
    assert client.get(sug, headers=h).status_code == 403
    hidden = client.get(sug, headers=sa).json()
    assert hidden["added"] == [] and hidden["hidden"] >= 1

    async def loose(db_):
        return {"k_min": 1, "dominance_pct": 100}
    monkeypatch.setattr(reports, "privacy", loose)
    shown = client.get(sug, headers=sa).json()
    assert shown["added"][0]["title"] == "Operatör eğitimi" and shown["added"][0]["companies"] == 1

    # --- proje sonucu: eksik doğrulamayla kapanış → sonuç kaydı BELIRSIZ, onaylı plan kaydı sonradan BELIRSIZ
    _exec(db, "UPDATE projects SET status = 'ACTIVE' WHERE id = %s", pid)
    _exec(db, "UPDATE tasks SET status = 'DONE' WHERE project_id = %s", pid)
    r = client.post(f"/api/v1/projects/{pid}/status", headers=h,
                    json={"action": "complete", "summary": "Pano ölçümü sonraki ay yapılacak.", "accept_gaps": True})
    assert r.status_code == 200, r.text
    (out,) = _records(db, pid, "BRAIN_OUTCOME")
    assert out["label"] == "BELIRSIZ" and "Pilot hat OEE panosu" in out["data"]["missing"]
    assert "Vardiya raporu" in out["data"]["skipped_requirements"]
    good = next(r for r in _records(db, pid, "BRAIN_PLAN") if r["id"] == good["id"])
    assert good["label"] == "BELIRSIZ" and good["data"]["original_label"] == "DOGRU" and good["data"]["relabel_reason"]


def test_brain_records_in_dataset_and_lessons_go_to_company_memory():
    from app.db.models import LearningRecord
    from app.services import training_data

    rec = LearningRecord(source="BRAIN_PLAN", label="DOGRU", sector="Üretim", job_title="Beyin AI")
    assert "Beyin AI'sısın" in training_data._system(rec) and "Üretim" in training_data._system(rec)
    assert "AI personelsin" in training_data._system(LearningRecord(source="APPROVAL", label="DOGRU", job_title="Analist"))
    assert bl.lesson_scope(LearningRecord(agent_id=None), "AGENT") == "GLOBAL"
    assert bl.lesson_scope(LearningRecord(agent_id=uuid.uuid4()), "AGENT") == "AGENT"
