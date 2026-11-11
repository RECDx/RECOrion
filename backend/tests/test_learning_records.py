"""
İSTEK #742: tek etiketli öğrenme kaydı (sohbet + iş akışı; sektörden bağımsız).

- Kontrol personeli reti ve yönetici reti YANLIS, onay DOGRU kaydı olur; reddedilen sürümler onaylanan sürüme bağlanır (tercih çifti).
- İnsanın işi kaydedilmez (AI öğrenmesi değildir).
- Ders: RECAi nedeni MODEL_HATASI derse AI personelin hafızasına yazılır; DEGERLENDIRICI/ORTAM/KAPSAM ise ders yazılmaz.
- GLOBAL ders kurumsal aday olur (yönetici onayı).
- Yönetici nedeni düzeltir: AI hatası değilse dersi hafızadan geri alınır.
- Şirket içeriği: süper admin ve yetkisiz üye göremez (KVKK).
- Test koşusu: ortam belirtisi ORTAM sayılır.
"""
import json
import time

from app.services import learning_records as lr
from app.services import llm_gateway
from tests.test_integrations import _super
from tests.test_workflow import _ready_project, _wait, ai, world  # noqa: F401  (fikstür)


def _records(client, w, **params):
    r = client.get(f"/api/v1/company/{w['tenant']}/learning/records", headers=w["admin"]["h"], params=params)
    assert r.status_code == 200, r.text
    return r.json()


def _until(fn, what, timeout=20):
    end = time.time() + timeout
    while time.time() < end:
        v = fn()
        if v:
            return v
        time.sleep(0.4)
    raise AssertionError(what)


class _R:
    def __init__(self, content):
        self.content, self.credits, self.public_model = content, 0.1, "RECAi"


def _lesson(client, monkeypatch, record_id, answer):
    async def chat(ctx, messages, **k):
        assert "öğrenme motoru" in messages[0]["content"]
        return _R(json.dumps(answer, ensure_ascii=False))
    monkeypatch.setattr(llm_gateway, "chat", chat)

    async def go():
        from app.db.session import AsyncSessionLocal
        async with AsyncSessionLocal() as s:
            rec = await lr.extract_lesson(s, record_id)
            return {"status": rec.lesson_status, "cause": rec.cause, "cause_by": rec.cause_by, "memory": str(rec.lesson_memory_id or ""),
                    "scope": rec.lesson_scope}
    return client.portal.call(go)


def test_workflow_decisions_become_labeled_records(client, db, world, ai, monkeypatch):
    w = world
    admin = w["admin"]["h"]
    ai.fail_reviews = 1
    pid, human_id, _ = _ready_project(client, w, "Öğrenme Projesi", reviewer=True)
    assert client.post(f"/api/v1/projects/{pid}/status", headers=admin, json={"action": "start"}).status_code == 200
    tasks, _ = _wait(client, admin, pid, lambda t, f: t["AI adımı"]["status"] == "WAITING_APPROVAL", "kontrolden sonra onayda", timeout=45)
    tid = tasks["AI adımı"]["id"]
    assert client.post(f"/api/v1/tasks/{tid}/decision", headers=admin, json={"approve": False, "note": "Fiyat tablosu eksik"}).status_code == 200
    _wait(client, admin, pid, lambda t, f: t["AI adımı"]["status"] == "WAITING_APPROVAL" and t["AI adımı"]["artifact"]["version"] == 3,
          "revizyondan sonra onayda", timeout=45)
    assert client.post(f"/api/v1/tasks/{tid}/decision", headers=admin, json={"approve": True, "note": "Tamam, tablo eklendi"}).status_code == 200

    recs = _until(lambda: (lambda r: r if any(x["source"] == "APPROVAL" for x in r) else None)(_records(client, w)), "onay kaydı oluşmalı")
    by = {x["source"]: x for x in recs}
    assert by["REVIEW"]["label"] == "YANLIS" and "Eksik bölüm 1" in (by["REVIEW"]["feedback"] or "")
    assert by["REJECTION"]["label"] == "YANLIS" and by["REJECTION"]["feedback"] == "Fiyat tablosu eksik"
    ok = by["APPROVAL"]
    assert ok["label"] == "DOGRU" and ok["paired"] and ok["lesson_status"] == "PENDING"  # çift var → ders çıkarılacak
    assert by["REVIEW"]["paired"] and by["REJECTION"]["paired"]
    assert all(x["task_id"] == tid for x in recs)  # insan adımı kaydedilmez
    full = client.get(f"/api/v1/company/{w['tenant']}/learning/records/{ok['id']}", headers=admin).json()
    assert "Kabul ölçütü: Tüm bölümler var" in full["task_input"] and "çıktısı" in (full["output"] or "")

    # Ders: haksız ret (DEGERLENDIRICI) → ders yok; AI hatası → personel hafızası; GLOBAL → kurumsal aday
    r1 = _lesson(client, monkeypatch, by["REVIEW"]["id"], {"neden": "DEGERLENDIRICI", "neden_gerekce": "Ret gerekçesiz.", "ders": "Bir şey yap.", "kapsam": "AGENT"})
    assert r1["status"] == "NONE" and r1["cause"] == "DEGERLENDIRICI" and r1["cause_by"] == "AI" and not r1["memory"]
    r2 = _lesson(client, monkeypatch, by["REJECTION"]["id"],
                 {"neden": "MODEL_HATASI", "neden_gerekce": "Tablo yok.", "ders": "Teklif çıktılarında fiyat tablosunu her zaman ekle.", "kapsam": "AGENT"})
    assert r2["status"] == "SAVED" and r2["scope"] == "AGENT" and r2["memory"]
    mem = db_row(db, "SELECT scope, status, agent_id::text FROM memory_items WHERE id = %s", r2["memory"])
    assert mem[0] == "AGENT" and mem[1] == "APPROVED" and mem[2] == w["agent"]
    r3 = _lesson(client, monkeypatch, ok["id"], {"neden": "", "ders": "Müşteriye giden belgelerde kabul ölçütünü madde madde karşıla.", "kapsam": "GLOBAL"})
    assert r3["status"] == "SAVED" and r3["scope"] == "GLOBAL"
    assert db_row(db, "SELECT status FROM memory_items WHERE id = %s", r3["memory"])[0] == "CANDIDATE"

    # Yönetici nedeni düzeltir: AI hatası değil → ders hafızadan geri alınır
    u = client.put(f"/api/v1/company/{w['tenant']}/learning/records/{by['REJECTION']['id']}/cause", headers=admin,
                   json={"cause": "KAPSAM", "note": "İstek sonradan değişti"})
    assert u.status_code == 200, u.text
    assert u.json()["cause"] == "KAPSAM" and u.json()["cause_by"] == "HUMAN" and u.json()["lesson_status"] == "NONE"
    assert db_row(db, "SELECT status FROM memory_items WHERE id = %s", r2["memory"])[0] == "REVOKED"
    assert client.put(f"/api/v1/company/{w['tenant']}/learning/records/{ok['id']}/cause", headers=admin,
                      json={"cause": "ORTAM"}).status_code == 422  # doğru kaydın nedeni olmaz

    s = client.get(f"/api/v1/company/{w['tenant']}/learning/summary", headers=admin).json()
    assert s["labels"]["YANLIS"] == 2 and s["labels"]["DOGRU"] == 1 and s["pairs"] == 2 and s["pending_corporate"] >= 1

    # KVKK: süper admin şirket içeriğini göremez; yetkisiz üye göremez; başka şirket göremez
    assert client.get(f"/api/v1/company/{w['tenant']}/learning/records", headers=_super(client, db)).status_code == 403
    assert client.get(f"/api/v1/company/{w['tenant']}/learning/records", headers=w["member"]["h"]).status_code == 403
    assert client.get(f"/api/v1/company/{w['tenant']}/learning/records", headers=w["outsider"]["h"]).status_code == 403
    assert client.post(f"/api/v1/projects/{pid}/status", headers=admin, json={"action": "cancel"}).status_code == 200


def db_row(db, sql, *args):
    from tests.test_workflow import _exec
    return _exec(db, sql, *args)


def test_test_run_cause_rules():
    assert lr.test_cause("ERROR", "Konteyner başlatılamadı") == "ORTAM"
    assert lr.test_cause("FAILED", "Bağlantı zaman aşımı") == "ORTAM"
    assert lr.test_cause("FAILED", None) == "MODEL_HATASI"
