"""
ADIM 7.1 + 7.2: Temporal iş akışı (gerçek Temporal sunucusu, test kuyruğu; EVREN ve nesne deposu sahte).

- Proje başlayınca akış başlar; bağımlılık sırası, teslim, onay/ret, 3 ret sonrası karantina, yeniden deneme, iptal,
  değiştirilemez olay geçmişi.
- AI personel işini kendisi yapar; kontrol personeli değerlendirir (ret = geri dönüş); insan reddinde geri bildirimle
  yeniden çalışır; önceki adımın çıktısı sonraki adıma bağlam olur; model hatasında adım durur, yönetici yeniden dener.
"""
import json
import time
import uuid
from datetime import date, timedelta

import psycopg2
import pytest

from app.core.security import hash_password
from app.services import storage
from app.services.evren_client import ChatResult, EvrenError, evren_client

PASSWORD = "Akis-Testi-Sifresi-2026"


def _exec(db, sql, *params):
    with db.cursor() as cur:
        cur.execute(sql, params)
        return cur.fetchone() if cur.description else None


def _login(client, email):
    r = client.post("/api/v1/auth/login", json={"email": email, "password": PASSWORD})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.fixture(scope="module")
def world(client, db):
    tag = uuid.uuid4().hex[:6]
    tid = _exec(db, "INSERT INTO tenants (id, slug, name, plan_id, is_active) VALUES (gen_random_uuid(), %s, 'Akış Ltd', "
                    "(SELECT id FROM plans WHERE code = 'PRO'), TRUE) RETURNING id", f"akis_{tag}")[0]

    def human(name, role):
        email = f"akis_{name}_{tag}@akis-test.com.tr"
        aid = _exec(db, "INSERT INTO actors (tenant_id, actor_type, display_name, email, role, password_hash, status) "
                        "VALUES (%s, 'HUMAN', %s, %s, %s, %s, 'IDLE') RETURNING id", tid, name, email, role, hash_password(PASSWORD))[0]
        return {"id": str(aid), "h": _login(client, email)}

    model = _exec(db, "SELECT id FROM llm_models WHERE model_code = 'deepseek-v4-flash'")[0]

    def agent(name):
        return str(_exec(db, "INSERT INTO actors (tenant_id, actor_type, display_name, role, status, preferred_model_id, system_prompt) "
                             "VALUES (%s, 'AI_AGENT', %s, 'Uzman', 'IDLE', %s, %s) RETURNING id", tid, name, model, f"Sen {name} adlı AI personelsin.")[0])
    return {"tenant": str(tid), "admin": human("Yonetici", "COMPANY_ADMIN"), "member": human("Uzman", "USER"),
            "outsider": human("Diger", "USER"), "agent": agent("Kodcu"), "reviewer": agent("Kontrolcu")}


class FakeAI:
    """EVREN yerine: iş çıktısı üretir; kontrol personeli ilk `fail_reviews` değerlendirmede reddeder."""

    def __init__(self):
        self.work_prompts, self.reviews, self.fail_reviews, self.broken, self.truncate, self.flaky = [], 0, 0, False, 0, 0
        self.bad_reviews = 0  # kontrol yanıtı kesik/okunamaz JSON

    async def chat(self, model_code, messages, **kw):
        system, prompt = messages[0]["content"], messages[-1]["content"]
        if "kontrol personelisin" in system:
            if self.bad_reviews:
                self.bad_reviews -= 1
                return ChatResult('{"passed": false, "score": 40, "issues": ["Uzun bulgu listesi kesil', None, 500, 3000, {})
            self.reviews += 1
            passed = self.reviews > self.fail_reviews
            return ChatResult(json.dumps({"passed": passed, "score": 90 if passed else 40, "summary": "Değerlendirme",
                                          "issues": [] if passed else [f"Eksik bölüm {self.reviews}"]}), None, 500, 80, {})
        if self.broken:
            raise RuntimeError("model yanıt vermedi")
        if self.flaky:  # personelin modeli meşgul (EVREN 503 "Model şu anda dolu")
            self.flaky -= 1
            self.busy_model = model_code
            raise EvrenError("Model şu anda dolu")
        if "kaldığın yerden devam et" in prompt:  # devam isteği: kesilen çıktının geri kalanı
            prompt = next(m["content"] for m in messages if m["role"] == "user")
        elif self.truncate:  # token sınırında kesilen çıktı
            self.truncate -= 1
            return ChatResult("PARÇA-1 ", None, 1200, 6000, {"choices": [{"finish_reason": "length"}]})
        self.work_prompts.append(prompt)
        title = prompt.split("Başlık: ", 1)[1].split("\n", 1)[0]
        return ChatResult(f"# {title} çıktısı #{len(self.work_prompts)}\nİçerik.", None, 1200, 300, {})


@pytest.fixture
def ai(monkeypatch):
    fake, objects = FakeAI(), {}

    async def put_object(key, data, content_type=None):
        objects[key] = data

    async def get_object(key):
        return objects[key]

    monkeypatch.setattr(evren_client, "chat", fake.chat)
    monkeypatch.setattr(storage, "put_object", put_object)
    monkeypatch.setattr(storage, "get_object", get_object)
    return fake


def _ready_project(client, w, name, reviewer=False):
    """Plan onaylı (1 AI adımı) + insan adımı + bağımlı AI adımı; başlamaya hazır proje."""
    h = w["admin"]["h"]
    pid = client.post("/api/v1/projects", headers=h, json={"tenant_id": w["tenant"], "name": name, "requirements": "Test isterleri"}).json()["id"]
    step = {"key": "S1", "title": "AI adımı", "estimated_days": 1, "agent_id": w["agent"], "acceptance_criteria": "Tüm bölümler var"}
    if reviewer:
        step["reviewer_agent_id"] = w["reviewer"]
    assert client.put(f"/api/v1/projects/{pid}/plan", headers=h, json={"summary": "s", "steps": [step]}).status_code == 200
    assert client.post(f"/api/v1/projects/{pid}/plan/approve", headers=h).status_code == 200
    human_task = client.post(f"/api/v1/projects/{pid}/tasks", headers=h, json={"title": "İnsan adımı", "assignee_actor_id": w["member"]["id"]}).json()
    dep_task = client.post(f"/api/v1/projects/{pid}/tasks", headers=h, json={
        "title": "Bağımlı adım", "assignee_actor_id": w["agent"], "depends_on": [human_task["id"]]}).json()
    start = date.today()
    assert client.put(f"/api/v1/projects/{pid}", headers=h, json={"start_date": start.isoformat(), "end_date": (start + timedelta(days=10)).isoformat()}).status_code == 200
    r = client.post(f"/api/v1/projects/{pid}/status", headers=h, json={"action": "mark_ready"})
    assert r.status_code == 200, r.text
    return pid, human_task["id"], dep_task["id"]


def _flow(client, h, pid):
    r = client.get(f"/api/v1/projects/{pid}/workflow", headers=h)
    assert r.status_code == 200, r.text
    return r.json()


def _wait(client, h, pid, cond, what, timeout=30):
    deadline = time.time() + timeout
    while time.time() < deadline:
        flow = _flow(client, h, pid)
        by_title = {t["title"]: t for t in flow["tasks"]}
        if cond(by_title, flow):
            return by_title, flow
        time.sleep(0.4)
    raise AssertionError(f"Beklenen akış durumu oluşmadı: {what}\n{json.dumps(_flow(client, h, pid), default=str, ensure_ascii=False)[:3000]}")


def test_workflow_full_cycle(client, world, ai):
    w = world
    admin, member, outsider = w["admin"]["h"], w["member"]["h"], w["outsider"]["h"]
    pid, human_id, dep_id = _ready_project(client, w, "Akış Projesi")
    ai.truncate = 1  # ilk AI çıktısı token sınırında kesilir; devam ettirilip birleştirilmeli
    ai.flaky = 1  # personelin modeli ilk çağrıda meşgul; adım durmadan yedek modelle sürmeli

    assert client.post(f"/api/v1/projects/{pid}/status", headers=admin, json={"action": "start"}).status_code == 200
    # AI adımı kendiliğinden çalışıp onaya gelir; insan adımı çalışılıyor; bağımlı adım bekler
    tasks, flow = _wait(client, admin, pid, lambda t, f: t["AI adımı"]["status"] == "WAITING_APPROVAL" and t["İnsan adımı"]["status"] == "IN_PROGRESS",
                        "AI adımı çıktısını teslim etmeli, insan adımı başlamalı")
    assert flow["workflow_id"] == f"project-{pid}"
    assert tasks["Bağımlı adım"]["status"] in ("BACKLOG", "READY")
    assert tasks["İnsan adımı"]["approver"]["id"] == w["admin"]["id"]  # onaylayıcı varsayılan: proje yöneticisi
    ai_task = tasks["AI adımı"]
    assert ai_task["artifact"]["version"] == 1 and not ai_task["can_submit"]
    art = client.get(f"/api/v1/tasks/{ai_task['id']}/artifacts/{ai_task['artifact']['id']}", headers=member)
    assert art.status_code == 200 and art.json()["content"].startswith("PARÇA-1 # AI adımı çıktısı")
    assert next(e for e in flow["events"] if e["kind"] == "AI_OUTPUT")["data"]["parts"] == 2
    assert not any(e["kind"] == "BLOCKED" for e in flow["events"])  # meşgul model yedek modelle aşıldı
    first_out = next(e for e in flow["events"] if e["kind"] == "AI_OUTPUT")
    assert ai.busy_model == "deepseek-v4-flash" and first_out["data"]["fallback_from"] == "deepseek-v4-flash"
    assert first_out["data"]["model"] != "deepseek-v4-flash" and "yedek model" in first_out["note"]
    assert client.get(f"/api/v1/tasks/{ai_task['id']}/artifacts/{ai_task['artifact']['id']}", headers=outsider).status_code == 403
    assert client.post(f"/api/v1/tasks/{ai_task['id']}/submit", headers=admin, json={}).status_code == 409  # AI kendi teslim eder

    # İnsan reddi > AI geri bildirimle yeniden çalışır (sürüm 2) > onay
    assert client.post(f"/api/v1/tasks/{ai_task['id']}/decision", headers=admin, json={"approve": False, "note": "Maliyet bölümünü ekle"}).status_code == 200
    tasks, _ = _wait(client, admin, pid, lambda t, f: t["AI adımı"]["status"] == "WAITING_APPROVAL" and (t["AI adımı"]["artifact"] or {}).get("version") == 2,
                     "AI geri bildirimle sürüm 2 üretmeli")
    assert "Maliyet bölümünü ekle" in ai.work_prompts[-1] and "PARÇA-1 # AI adımı çıktısı #1" in ai.work_prompts[-1]
    assert client.post(f"/api/v1/tasks/{ai_task['id']}/decision", headers=admin, json={"approve": True}).status_code == 200

    # Yetki: ekip dışı göremez; üye yalnızca kendi adımını teslim eder; onay yöneticide
    assert client.get(f"/api/v1/projects/{pid}/workflow", headers=outsider).status_code == 403

    # İnsan adımı: 3 ret > karantina > yeniden dene > onay
    for i in range(1, 4):
        r = client.post(f"/api/v1/tasks/{human_id}/submit", headers=member, json={"note": f"Teslim {i}"})
        assert r.status_code == 200, r.text
        _wait(client, admin, pid, lambda t, f: t["İnsan adımı"]["status"] == "WAITING_APPROVAL", f"teslim {i} onay beklemeli")
        assert client.post(f"/api/v1/tasks/{human_id}/decision", headers=member, json={"approve": True}).status_code == 403
        assert client.post(f"/api/v1/tasks/{human_id}/decision", headers=admin, json={"approve": False}).status_code == 422  # gerekçe şart
        assert client.post(f"/api/v1/tasks/{human_id}/decision", headers=admin, json={"approve": False, "note": f"Eksik {i}"}).status_code == 200
        expected = "QUARANTINED" if i == 3 else "REVISION"
        tasks, _ = _wait(client, admin, pid, lambda t, f: t["İnsan adımı"]["status"] == expected, f"ret {i} sonrası {expected}")
    assert tasks["İnsan adımı"]["rejection_count"] == 3 and tasks["İnsan adımı"]["can_release"]
    assert client.post(f"/api/v1/tasks/{human_id}/submit", headers=member, json={}).status_code == 409
    assert client.post(f"/api/v1/tasks/{human_id}/release", headers=member, json={"action": "retry"}).status_code == 403
    assert client.post(f"/api/v1/tasks/{human_id}/release", headers=admin, json={"action": "retry", "note": "Bir kez daha"}).status_code == 200
    tasks, _ = _wait(client, admin, pid, lambda t, f: t["İnsan adımı"]["status"] == "IN_PROGRESS", "yeniden deneme")
    assert tasks["İnsan adımı"]["rejection_count"] == 0
    client.post(f"/api/v1/tasks/{human_id}/submit", headers=member, json={"note": "Son hali"})
    _wait(client, admin, pid, lambda t, f: t["İnsan adımı"]["status"] == "WAITING_APPROVAL", "son teslim")
    assert client.post(f"/api/v1/tasks/{human_id}/decision", headers=admin, json={"approve": True, "note": "Tamam"}).status_code == 200

    # Bağımlı AI adımı insan adımı bitince kendiliğinden çalışır > onay > proje akışı biter
    tasks, _ = _wait(client, admin, pid, lambda t, f: t["Bağımlı adım"]["status"] == "WAITING_APPROVAL", "bağımlı AI adımı çıktı üretmeli")
    assert client.post(f"/api/v1/tasks/{dep_id}/decision", headers=admin, json={"approve": True}).status_code == 200
    _, flow = _wait(client, admin, pid, lambda t, f: any(e["kind"] == "PROJECT_FINISHED" for e in f["events"]), "proje akışı bitmeli")
    kinds = [e["kind"] for e in reversed(flow["events"])]
    assert kinds[0] == "PROJECT_STARTED" and kinds.count("REJECTED") == 4 and "QUARANTINED" in kinds and "RELEASED" in kinds
    assert kinds.count("DONE") == 3 and kinds.count("AI_OUTPUT") == 3
    # Akış kendiliğinden bitti; projeyi kapatmak motor hatası vermemeli
    r = client.post(f"/api/v1/projects/{pid}/status", headers=admin, json={"action": "complete", "summary": "Bitti"})
    assert r.status_code == 200 and r.json()["status"] == "COMPLETED", r.text


def test_reviewer_loop_and_blocked_agent(client, world, ai):
    """Kontrol personeli 2 kez reddeder (AI geri bildirimle düzeltir), 3. sürüm geçer; model hatasında adım durur."""
    w = world
    admin = w["admin"]["h"]
    ai.fail_reviews = 2
    pid, human_id, _ = _ready_project(client, w, "Kontrol Projesi", reviewer=True)
    assert client.post(f"/api/v1/projects/{pid}/status", headers=admin, json={"action": "start"}).status_code == 200
    tasks, flow = _wait(client, admin, pid, lambda t, f: t["AI adımı"]["status"] == "WAITING_APPROVAL", "kontrolden geçip onaya gelmeli", timeout=45)
    t = tasks["AI adımı"]
    assert t["reviewer"]["id"] == w["reviewer"] and t["artifact"]["version"] == 3 and t["rejection_count"] == 2
    kinds = [e["kind"] for e in reversed(flow["events"]) if e["task_id"] == t["id"]]
    assert kinds.count("REVIEW_FAILED") == 2 and kinds.count("REVIEW_PASSED") == 1 and "REJECTED" not in kinds
    assert "Eksik bölüm 2" in ai.work_prompts[-1]  # kontrol personelinin bulguları geri bildirim olarak gitti

    # Kontrol personelinin 2 reddi sayaca dahil: insanın reddi 3. ret olur > karantina
    assert client.post(f"/api/v1/tasks/{t['id']}/decision", headers=admin, json={"approve": False, "note": "Bir daha"}).status_code == 200
    _wait(client, admin, pid, lambda x, f: x["AI adımı"]["status"] == "QUARANTINED", "3. retle karantina", timeout=30)

    # Model hatası: yeniden denemede AI çalışamaz > adım durur (BLOCKED) > yönetici tekrar dener
    ai.broken = True
    assert client.post(f"/api/v1/tasks/{t['id']}/release", headers=admin, json={"action": "retry"}).status_code == 200
    tasks, flow = _wait(client, admin, pid, lambda x, f: any(e["kind"] == "BLOCKED" for e in f["events"]) and x["AI adımı"]["status"] == "QUARANTINED",
                        "model hatasında adım durmalı", timeout=90)
    assert any(e["kind"] == "BLOCKED" and "model yanıt vermedi" in (e["note"] or "") for e in flow["events"])
    ai.broken = False
    assert client.post(f"/api/v1/tasks/{t['id']}/release", headers=admin, json={"action": "retry"}).status_code == 200
    _wait(client, admin, pid, lambda x, f: x["AI adımı"]["status"] == "WAITING_APPROVAL", "yeniden denemede çıktı üretmeli", timeout=45)
    assert client.post(f"/api/v1/projects/{pid}/status", headers=admin, json={"action": "cancel"}).status_code == 200


def test_workflow_pause_and_cancel(client, world, db, ai):
    w = world
    admin = w["admin"]["h"]
    pid, human_id, _ = _ready_project(client, w, "İptal Projesi")
    assert client.post(f"/api/v1/projects/{pid}/status", headers=admin, json={"action": "start"}).status_code == 200
    _wait(client, admin, pid, lambda t, f: t["İnsan adımı"]["status"] == "IN_PROGRESS", "başlamalı")
    assert client.post(f"/api/v1/projects/{pid}/status", headers=admin, json={"action": "pause"}).status_code == 200
    assert client.post(f"/api/v1/projects/{pid}/status", headers=admin, json={"action": "resume"}).status_code == 200
    assert client.post(f"/api/v1/projects/{pid}/status", headers=admin, json={"action": "cancel", "summary": "Vazgeçildi"}).status_code == 200
    _wait(client, admin, pid, lambda t, f: all(x["status"] == "CANCELLED" for x in t.values()), "tüm adımlar iptal olmalı")
    # Kapanmış projede akış komutu yok
    assert client.post(f"/api/v1/tasks/{human_id}/submit", headers=w["member"]["h"], json={}).status_code == 409

    # Olay geçmişi değiştirilemez
    with pytest.raises(psycopg2.Error):
        _exec(db, "UPDATE task_events SET note = 'değişti' WHERE project_id = %s", pid)


def test_unreadable_review_is_retried_or_recorded(client, world, ai):
    """Kontrol yanıtı kesik/okunamaz gelirse bir kez yeniden istenir; yine okunamazsa sessizce geçilmez, kayda düşer."""
    w = world
    admin = w["admin"]["h"]
    ai.bad_reviews = 1  # ilk yanıt bozuk, ikinci yanıt geçerli
    pid, _, _ = _ready_project(client, w, "Okunamayan Kontrol 1", reviewer=True)
    client.post(f"/api/v1/projects/{pid}/status", headers=admin, json={"action": "start"})
    tasks, flow = _wait(client, admin, pid, lambda t, f: t["AI adımı"]["status"] == "WAITING_APPROVAL", "yeniden istenen kontrolle onaya gelmeli", 45)
    kinds = [e["kind"] for e in flow["events"] if e["task_id"] == tasks["AI adımı"]["id"]]
    assert "REVIEW_PASSED" in kinds and "REVIEW_SKIPPED" not in kinds
    client.post(f"/api/v1/projects/{pid}/status", headers=admin, json={"action": "cancel"})

    ai.bad_reviews = 2  # iki yanıt da bozuk: kayda düşer, karar onaylayıcıya kalır
    pid, _, _ = _ready_project(client, w, "Okunamayan Kontrol 2", reviewer=True)
    client.post(f"/api/v1/projects/{pid}/status", headers=admin, json={"action": "start"})
    tasks, flow = _wait(client, admin, pid, lambda t, f: t["AI adımı"]["status"] == "WAITING_APPROVAL", "kontrol yapılamadan onaya gelmeli", 45)
    skipped = [e for e in flow["events"] if e["task_id"] == tasks["AI adımı"]["id"] and e["kind"] == "REVIEW_SKIPPED"]
    assert len(skipped) == 1 and "okunamadı" in skipped[0]["note"] and skipped[0]["actor"]["id"] == w["reviewer"]
    client.post(f"/api/v1/projects/{pid}/status", headers=admin, json={"action": "cancel"})
