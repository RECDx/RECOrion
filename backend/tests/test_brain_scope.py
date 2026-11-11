"""
İSTEK #738: Beyin AI'nin iki kapsamı.

- Şirket Beyin'i: kullanıcının ROLÜYLE sınırlı iş durumu (üye yalnız ekibinde olduğu projeyi, kredi bilgisini billing:view olmadan
  görmez); kılavuzdan sistem kullanımı; başka şirketi bilmez; yanıtta kılavuz kaynakları döner.
- Merkez Beyin'i: toplu istatistik yalnız en az 5 şirkette görülen ünvanlar için (k-anonimlik); içerik yok.
- Destek erişimi: yalnız şirket yöneticisi verir/kapatır; süper admin kendine veremez; erişim varken Merkez o şirketin iş durumunu
  görür ve her soru şirketin kayıtlarına düşer; kapatılınca 403.
"""
import uuid

from app.services import llm_gateway
from tests.test_integrations import _super
from tests.test_workflow import _exec, world  # noqa: F401  (fikstür)


class _R:
    def __init__(self):
        self.content, self.credits, self.public_model, self.tokens_in, self.tokens_out = "Yanıt.", 0.1, "RECAi", 10, 5


def _capture(monkeypatch):
    seen = []

    async def chat(ctx, messages, **k):
        seen.append(messages[0]["content"])
        return _R()
    monkeypatch.setattr(llm_gateway, "chat", chat)
    return seen


def test_company_brain_is_role_scoped(client, db, world, monkeypatch):
    w = world
    admin, member = w["admin"]["h"], w["member"]["h"]
    mine = client.post("/api/v1/projects", headers=admin, json={"tenant_id": w["tenant"], "name": "Üyenin Projesi"}).json()["id"]
    client.post("/api/v1/projects", headers=admin, json={"tenant_id": w["tenant"], "name": "Gizli Yönetim Projesi"})
    _exec(db, "INSERT INTO project_members (id, project_id, actor_id, role, created_at) VALUES (gen_random_uuid(), %s, %s, 'MEMBER', now())",
          mine, w["member"]["id"])
    other = _exec(db, "INSERT INTO tenants (id, slug, name, is_active) VALUES (gen_random_uuid(), %s, 'Başka Şirket A.Ş.', TRUE) RETURNING id",
                  f"baska_{uuid.uuid4().hex[:6]}")[0]
    _exec(db, "INSERT INTO projects (id, tenant_id, name, slug, status) VALUES (gen_random_uuid(), %s, 'Başkasının Projesi', %s, 'ACTIVE')",
          other, f"bp-{uuid.uuid4().hex[:6]}")
    seen = _capture(monkeypatch)
    r = client.post(f"/api/v1/company/{w['tenant']}/brain/chat", headers=member, json={"content": "Proje nasıl oluşturulur?"})
    assert r.status_code == 200, r.text
    assert "sources" in r.json()
    p = seen[-1]
    assert "Üyenin Projesi" in p and "Gizli Yönetim Projesi" not in p and "yalnız ekibinde olduğunuz" in p
    assert "RECAi kullanımı" not in p  # kredi bilgisi billing:view ister
    assert "Başkasının Projesi" not in p and "Başka Şirket" not in p  # başka şirketi bilmez

    client.post(f"/api/v1/company/{w['tenant']}/brain/chat", headers=admin, json={"content": "Durum nedir?"})
    assert "Gizli Yönetim Projesi" in seen[-1] and "Üyenin Projesi" in seen[-1]


def test_merkez_brain_k_anonymity_and_support_access(client, db, world, monkeypatch):
    w = world
    sa = _super(client, db)
    tenants = [str(_exec(db, "INSERT INTO tenants (id, slug, name, is_active) VALUES (gen_random_uuid(), %s, %s, TRUE) RETURNING id",
                         f"k_{uuid.uuid4().hex[:8]}", f"K Şirketi {i}")[0]) for i in range(5)]
    wide, narrow = f"Geniş Ünvan {uuid.uuid4().hex[:6]}", f"Dar Ünvan {uuid.uuid4().hex[:6]}"
    for t in tenants[:5]:
        _exec(db, "INSERT INTO learning_records (id, tenant_id, source, label, job_title, data, lesson_status) "
                  "VALUES (gen_random_uuid(), %s, 'APPROVAL', 'DOGRU', %s, '{}', 'NONE')", t, wide)
    for t in tenants[:2]:
        _exec(db, "INSERT INTO learning_records (id, tenant_id, source, label, job_title, data, lesson_status) "
                  "VALUES (gen_random_uuid(), %s, 'REJECTION', 'YANLIS', %s, '{}', 'NONE')", t, narrow)
    seen = _capture(monkeypatch)
    r = client.post("/api/v1/system/assistant/chat", headers=sa, json={"content": "Hangi ünvanlar zorlanıyor?"})
    assert r.status_code == 200, r.text
    assert wide in seen[-1] and narrow not in seen[-1] and "k-anonimlik" in seen[-1]

    # Destek erişimi yokken şirket içeriği istenemez
    proj = client.post("/api/v1/projects", headers=w["admin"]["h"], json={"tenant_id": w["tenant"], "name": "Destek Projesi"}).json()["id"]
    assert proj
    body = {"content": "Bu şirkette ne takılıyor?", "support_tenant_id": w["tenant"]}
    assert client.post("/api/v1/system/assistant/chat", headers=sa, json=body).status_code == 403
    assert client.post(f"/api/v1/company/{w['tenant']}/support-access", headers=sa, json={"hours": 4}).status_code == 403
    assert client.post(f"/api/v1/company/{w['tenant']}/support-access", headers=w["member"]["h"], json={"hours": 4}).status_code == 403
    g = client.post(f"/api/v1/company/{w['tenant']}/support-access", headers=w["admin"]["h"], json={"hours": 4, "reason": "Hata incelemesi"})
    assert g.status_code == 201, g.text and g.json()["active"]
    assert any(x["tenant_id"] == w["tenant"] for x in client.get("/api/v1/system/support-access/active", headers=sa).json())
    r = client.post("/api/v1/system/assistant/chat", headers=sa, json=body)
    assert r.status_code == 200, r.text
    assert "Destek Projesi" in seen[-1] and r.json()["support"]["tenant_id"] == w["tenant"]
    logs = client.get(f"/api/v1/company/{w['tenant']}/support-access", headers=w["admin"]["h"]).json()["logs"]
    assert logs and logs[0]["action"] == "BEYIN_SORU" and "takılıyor" in logs[0]["detail"]
    assert client.post(f"/api/v1/company/{w['tenant']}/support-access/revoke", headers=w["admin"]["h"]).json()["active"] is None
    assert client.post("/api/v1/system/assistant/chat", headers=sa, json=body).status_code == 403

