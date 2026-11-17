"""
İSTEK #751: Sektör bilgi paketleri.

- İlk dalga 4 paket açılışta TASLAK yüklenir; uzman beyanı, kontrol eden ve tarih olmadan yayımlanamaz; yayın sürümlenir,
  önceki sürümler geçmişte kalır; taslak düzenlemesi yayını değiştirmez; yayından çekilen paket kullanılmaz.
- Şirket yalnız yayını görür; ek soruları yalnız tenant:manage yazar, yalnız o şirkette geçerlidir, RECDx göremez (KVKK).
- Proje paketi: Beyin AI isterlerden önerir (mesaj ≠ MES), yönetici değiştirir ya da "paket yok" seçer.
- Keşif istemine soru bankası (şirket soruları önce) + sık atlananlar + standartlar, plan istemine aşamalar ve teslimatlar girer.
"""
import json
import uuid
from datetime import date, timedelta

from tests.test_integrations import _super
from tests.test_workflow import _exec, _login, _ready_project, world  # noqa: F401  (fikstür)


def _seed(client):
    from app.db.session import AsyncSessionLocal
    from app.services.sector_packs import ensure_packs

    async def go():
        async with AsyncSessionLocal() as s:
            return await ensure_packs(s)
    return client.portal.call(go)


def _publish_all(client, sa):
    body = {"expert_confirmed": True, "reviewer_name": "Test Uzmanı", "checked_at": date.today().isoformat()}
    packs = client.get("/api/v1/system/sector-packs", headers=sa).json()
    for p in packs:
        if not (p["published"] and not p["published"]["withdrawn"]):
            assert client.post(f"/api/v1/system/sector-packs/{p['id']}/publish", headers=sa, json=body).status_code == 200
    return {p["code"]: p for p in client.get("/api/v1/system/sector-packs", headers=sa).json()}


def test_sector_packs_review_publish_withdraw_and_company_extras(client, db, world):
    w = world
    admin, member = w["admin"]["h"], w["member"]["h"]
    _seed(client)
    assert _seed(client) == 0
    sa = _super(client, db)
    assert client.get("/api/v1/system/sector-packs", headers=admin).status_code == 403
    packs = {p["code"]: p for p in client.get("/api/v1/system/sector-packs", headers=sa).json()}
    assert {"yazilim", "uretim-mes", "erp-devreye-alma", "kalite-uyum"} <= set(packs)
    mes = packs["uretim-mes"]
    assert len(mes["draft_content"]["questions"]) >= 8 and mes["draft_content"]["phases"][0]["deliverables"][0]["verification"]

    base = f"/api/v1/company/{w['tenant']}/sector-packs"
    if mes["published"] is None:  # taslak şirkete görünmez
        assert all(p["code"] != "uretim-mes" for p in client.get(base, headers=member).json())

    pub = f"/api/v1/system/sector-packs/{mes['id']}/publish"
    body = {"expert_confirmed": False, "reviewer_name": "Üretim Uzmanı", "checked_at": date.today().isoformat()}
    assert client.post(pub, headers=sa, json=body).status_code == 422
    assert client.post(pub, headers=sa, json={**body, "expert_confirmed": True, "checked_at": (date.today() + timedelta(days=2)).isoformat()}).status_code == 422
    assert client.post(pub, headers=admin, json={**body, "expert_confirmed": True}).status_code == 403
    r = client.post(pub, headers=sa, json={**body, "expert_confirmed": True})
    assert r.status_code == 200, r.text
    v1 = r.json()["published"]["version"]

    # taslak değişir, yayın değişmez; yeniden yayın sürümü artırır ve öncekini geçmişe yazar
    content = r.json()["draft_content"]
    content["questions"][0]["text"] = "TASLAK EK SORU?"
    assert client.put(f"/api/v1/system/sector-packs/{mes['id']}", headers=sa, json={"content": content}).json()["changed_since_publish"] is True
    seen = next(p for p in client.get(base, headers=member).json() if p["code"] == "uretim-mes")
    assert seen["version"] == v1 and all(q["text"] != "TASLAK EK SORU?" for q in seen["content"]["questions"])
    r2 = client.post(pub, headers=sa, json={**body, "expert_confirmed": True}).json()["published"]
    assert r2["version"] == v1 + 1 and r2["history"][-1]["version"] == v1

    # şirket ekleri: yalnız tenant:manage; yalnız bu şirkette; RECDx göremez
    extras = {"questions": [{"topic": "Hat", "text": "Kalıp değişim süresi ölçülüyor mu?", "why": "SMED hedefi"}], "missed": ["Etiket yazıcısı"]}
    assert client.put(f"{base}/uretim-mes", headers=member, json=extras).status_code == 403
    assert client.put(f"{base}/uretim-mes", headers=admin, json=extras).status_code == 200
    assert client.get(base, headers=sa).status_code == 403
    mine = next(p for p in client.get(base, headers=member).json() if p["code"] == "uretim-mes")
    assert mine["extras"]["questions"][0]["text"] == "Kalıp değişim süresi ölçülüyor mu?"
    (other,) = _exec(db, "SELECT coalesce(string_agg(settings::text, ' '), '') FROM tenants WHERE id <> %s", w["tenant"])
    assert "Kalıp değişim" not in other

    # yayından çekilen paket şirkete görünmez
    assert client.post(f"/api/v1/system/sector-packs/{mes['id']}/withdraw", headers=sa).status_code == 200
    assert all(p["code"] != "uretim-mes" for p in client.get(base, headers=member).json())
    assert client.post(f"/api/v1/system/sector-packs/{mes['id']}/withdraw", headers=sa).status_code == 409
    assert client.post(pub, headers=sa, json={**body, "expert_confirmed": True}).json()["published"]["withdrawn"] is False


def test_project_pack_suggestion_and_prompts(client, db, world, monkeypatch):
    from app.services.evren_client import ChatResult, evren_client

    w = world
    h = w["admin"]["h"]
    _seed(client)
    sa = _super(client, db)
    _publish_all(client, sa)
    pid, _, _ = _ready_project(client, w, f"Paket {uuid.uuid4().hex[:4]}")
    _exec(db, "UPDATE projects SET status = 'PLANNING', plan = NULL, requirements = %s WHERE id = %s",
          "Fabrikadaki 12 makinenin duruşlarını ve OEE değerini izleyen bir üretim takip sistemi; vardiya raporu ve iş emri ERP'den gelecek.", pid)
    # "mesaj" kelimesi MES sayılmaz
    pid2, _, _ = _ready_project(client, w, f"Mesaj {uuid.uuid4().hex[:4]}")
    _exec(db, "UPDATE projects SET status = 'PLANNING', requirements = %s WHERE id = %s", "Müşterilere toplu mesaj gönderme duyurusu hazırlanacak.", pid2)
    assert client.get(f"/api/v1/projects/{pid2}/sector-pack", headers=h).json()["code"] is None

    got = client.get(f"/api/v1/projects/{pid}/sector-pack", headers=h).json()
    assert got["code"] == "uretim-mes" and got["auto"] is True and {o["code"] for o in got["options"]} >= {"yazilim", "kalite-uyum"}
    assert client.put(f"/api/v1/projects/{pid}/sector-pack", headers=w["member"]["h"], json={"code": "yazilim"}).status_code in (403, 404)
    assert client.put(f"/api/v1/projects/{pid}/sector-pack", headers=h, json={"code": "yok-boyle"}).status_code == 404

    # şirket eki keşif istemine paketten önce girer
    client.put(f"/api/v1/company/{w['tenant']}/sector-packs/uretim-mes", headers=h,
               json={"questions": [{"topic": "Hat", "text": "Kalıp değişim süresi ölçülüyor mu?"}], "missed": []})
    seen = []

    async def chat(model_code, messages, **kw):
        seen.append(messages[-1]["content"])
        if "keşif görüşmesi" in messages[-1]["content"]:
            out = {"charter": {"goal": "OEE izleme", "deliverables": [{"name": "Pilot hat", "acceptance": "veri geliyor", "verification": "sayım"}]},
                   "maturity": {"score": 80, "missing": []}, "questions": [], "reminders": [], "research_suggestions": []}
        else:
            out = {"summary": "plan", "steps": [{"key": "S1", "title": "Saha keşfi", "description": "envanter", "acceptance_criteria": "rapor",
                                                  "department": "", "job_title": "Analist", "agent_id": "", "estimated_days": 2, "depends_on": []}],
                   "hire_suggestions": [], "risks": [], "questions": []}
        return ChatResult(json.dumps(out, ensure_ascii=False), None, 100, 50, {})
    monkeypatch.setattr(evren_client, "chat", chat)

    assert client.post(f"/api/v1/projects/{pid}/discovery/round", headers=h, json={"answers": []}).status_code == 200
    p = seen[-1]
    assert "Sektör bilgi paketi: Üretim / MES devreye alma" in p and "PLC" in p and "Başlangıç (baseline) OEE" in p and "ISA-95" in p
    assert p.index("Kalıp değişim süresi") < p.index("Makinelerin kontrol sistemleri")
    assert client.post(f"/api/v1/projects/{pid}/discovery/approve", headers=h, json={}).status_code == 200
    assert client.post(f"/api/v1/projects/{pid}/plan/suggest", headers=h, json={}).status_code == 200
    plan_prompt = seen[-1]
    assert "Standart aşamalar ve teslimat şablonları" in plan_prompt and "Pilot hatta veri toplama" in plan_prompt and "OEE" in plan_prompt

    # yönetici "paket yok" seçerse istemlere girmez
    got = client.put(f"/api/v1/projects/{pid}/sector-pack", headers=h, json={"code": None}).json()
    assert got["code"] is None and got["auto"] is False
    assert client.post(f"/api/v1/projects/{pid}/plan/suggest", headers=h, json={}).status_code == 200
    assert "Sektör bilgi paketi" not in seen[-1]
