"""
ADIM 11.2: Türkiye mevzuat bilgi paketleri.

- Taslak paketler açılışta yüklenir; uzman kontrolü onayı, kontrol eden ve tarih olmadan yayımlanamaz; yayın sürümlenir.
- Müşteri yalnızca yayını görür (taslak 404); yayından sonraki taslak düzenlemesi yayını değiştirmez.
- Paketi yalnızca tenant:manage açar; RECDx şirketin paket ayarlarını göremez (KVKK).
- AI bağlamı: yalnızca şirketin açtığı paketlerden, metinle ilgili kartlar; kaynak/sürüm ve hukuki uyarı ile.
"""
from datetime import date, timedelta

from tests.test_integrations import _super
from tests.test_workflow import _exec, _ready_project, world  # noqa: F401  (fikstür)


def _seed(client):
    from app.db.session import AsyncSessionLocal
    from app.services.regulations import ensure_packs

    async def go():
        async with AsyncSessionLocal() as s:
            return await ensure_packs(s)
    return client.portal.call(go)


def _context(client, tenant_id, text):
    from app.db.session import AsyncSessionLocal
    from app.services import regulations

    async def go():
        async with AsyncSessionLocal() as s:
            return await regulations.context_for(s, tenant_id, text)
    return client.portal.call(go)


def test_regulation_packs_review_publish_and_use(client, db, world, monkeypatch):
    from app.services.evren_client import ChatResult, evren_client

    w = world
    admin, member = w["admin"]["h"], w["member"]["h"]
    _seed(client)
    assert _seed(client) == 0
    sa = _super(client, db)
    packs = {p["code"]: p for p in client.get("/api/v1/system/regulation-packs", headers=sa).json()}
    assert {"kvkk", "sgk", "vergi", "efatura", "isg"} <= set(packs)
    sgk = packs["sgk"]
    assert client.get("/api/v1/system/regulation-packs", headers=admin).status_code == 403

    base = f"/api/v1/company/{w['tenant']}/regulation-packs"
    if sgk["published"] is None:  # taslak müşteriye görünmez
        assert all(p["code"] != "sgk" for p in client.get(base, headers=member).json())
        assert client.get(f"{base}/{sgk['id']}", headers=member).status_code == 404

    pub = f"/api/v1/system/regulation-packs/{sgk['id']}/publish"
    body = {"expert_confirmed": False, "reviewer_name": "Av. Test Uzman", "checked_at": date.today().isoformat()}
    assert client.post(pub, headers=sa, json=body).status_code == 422  # uzman kontrolü beyanı yok
    assert client.post(pub, headers=sa, json={**body, "expert_confirmed": True, "checked_at": (date.today() + timedelta(days=3)).isoformat()}).status_code == 422
    assert client.post(pub, headers=admin, json={**body, "expert_confirmed": True}).status_code == 403
    r = client.post(pub, headers=sa, json={**body, "expert_confirmed": True, "note": "5510 güncel metne göre kontrol edildi"})
    assert r.status_code == 200, r.text
    v1 = r.json()["published"]["version"]
    assert r.json()["changed_since_publish"] is False

    # Taslak değişir, yayın değişmez; yeniden yayın sürümü artırır
    cards = r.json()["draft_cards"]
    edited = [{**cards[0], "body": cards[0]["body"] + " (taslak ek)"}] + cards[1:]
    assert client.put(f"/api/v1/system/regulation-packs/{sgk['id']}", headers=sa, json={"cards": edited}).json()["changed_since_publish"] is True
    seen = client.get(f"{base}/{sgk['id']}", headers=member).json()
    assert seen["version"] == v1 and "(taslak ek)" not in seen["cards"][0]["body"] and seen["reviewer_name"] == "Av. Test Uzman"
    assert "hukuki/mali danışmanlık değildir" in seen["disclaimer"]
    assert client.post(pub, headers=sa, json={**body, "expert_confirmed": True}).json()["published"]["version"] == v1 + 1

    # Paket kapalıyken AI bağlamına girmez; açınca ilgili kart girer
    q = "Yeni çalışanın SGK işe giriş bildirgesini ne zaman vermeliyiz?"
    assert _context(client, w["tenant"], q)[0] == ""
    assert client.put(f"{base}/{sgk['id']}", headers=member, json={"enabled": True}).status_code == 403
    assert client.get(base, headers=sa).status_code == 403  # KVKK: RECDx şirket ayarını göremez
    assert client.put(f"{base}/{sgk['id']}", headers=admin, json={"enabled": True}).json()["enabled"] is True
    ctx, used = _context(client, w["tenant"], q)
    assert used[0]["card"] == "sgk-ise-giris" and used[0]["version"] == v1 + 1
    assert "5510 sayılı Kanun md. 8" in ctx and "hukuki/mali danışmanlık değildir" in ctx and "mevzuat.gov.tr" in ctx
    assert _context(client, w["tenant"], "Logonun rengi mavi olsun, sunum şablonunu güncelle")[0] == ""

    # Sohbette AI personele giden bağlamda kart ve uyarı var
    pid, _, _ = _ready_project(client, w, "Mevzuat Sohbeti")
    task = str(_exec(db, "SELECT id FROM tasks WHERE project_id = %s AND title = 'AI adımı'", pid)[0])
    systems = []

    async def chat(model_code, messages, **kw):
        systems.append(messages[0]["content"])
        return ChatResult("İşe başlamadan önce bildirilir (SGK paketi).", None, 50, 10, {})
    monkeypatch.setattr(evren_client, "chat", chat)
    r = client.post("/api/v1/chat/send", headers=admin, json={"task_id": task, "content": q})
    assert r.status_code == 200, r.text
    assert "Mevzuat bilgi paketleri" in systems[0] and "Sigortalı işe giriş bildirgesi" in systems[0]

    assert client.put(f"{base}/{sgk['id']}", headers=admin, json={"enabled": False}).json()["enabled"] is False
    assert _context(client, w["tenant"], q)[0] == ""
