"""
İSTEK #739: ünvanı sohbetle tanımlama (Merkez katalog + Şirket Yönetimi).

- Şirket yöneticisi serbest anlatım gönderir; RECAi yanıtı ve taslak döner (kaydetmez), şirketin kredisiyle (tenant_id).
- Taslak alanları temizlenir; modelin boş bıraktığı alan önceki taslaktan korunur; JSON gelmezse taslak korunur.
- Yetkisiz kullanıcı ve başka şirket reddedilir; Merkez ucu yalnız Süper Admin; platform maliyeti (tenant_id None).
- Sohbetin son mesajı kullanıcıdan olmalı.
"""
import json

from app.services import llm_gateway, title_design
from tests.test_integrations import _super
from tests.test_workflow import world  # noqa: F401  (fikstür)


class _R:
    def __init__(self, content):
        self.content, self.credits, self.public_model = content, 0.5, "RECAi"


def _fake(monkeypatch, content, seen):
    async def chat(ctx, messages, **k):
        seen.append({"tenant": ctx.tenant_id, "messages": messages})
        return _R(content)
    monkeypatch.setattr(llm_gateway, "chat", chat)


def test_company_title_design_chat(client, db, world, monkeypatch):
    w = world
    seen = []
    _fake(monkeypatch, json.dumps({"cevap": "Hastalara hangi kanaldan ulaşılacak?", "hazir": False, "taslak": {
        "title": "Hasta İletişim Asistanı", "description": "Randevu hatırlatma ve hasta iletişimi.",
        "responsibilities": ["Randevu hatırlatması gönderir", ""], "required_skills": "İletişim\nKVKK bilgisi",
        "kpis": [], "base_role_prompt": "Sen {{company_name}} kliniğinde hasta iletişim asistanısın."}}, ensure_ascii=False), seen)
    body = {"messages": [{"role": "user", "content": "Kliniğimizde randevuları hatırlatacak bir asistan istiyorum."}],
            "draft": {"kpis": ["Kaçırılan randevu oranı düşer"]}, "context": {"sector": "Sağlık"}}
    r = client.post(f"/api/v1/company/{w['tenant']}/job-titles/design-chat", headers=w["admin"]["h"], json=body)
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["reply"].startswith("Hastalara") and d["ready"] is False
    assert d["draft"]["title"] == "Hasta İletişim Asistanı"
    assert d["draft"]["responsibilities"] == ["Randevu hatırlatması gönderir"]
    assert d["draft"]["required_skills"] == ["İletişim", "KVKK bilgisi"]
    assert d["draft"]["kpis"] == ["Kaçırılan randevu oranı düşer"]  # model boş bıraktı → önceki korunur
    assert str(seen[0]["tenant"]) == w["tenant"]  # şirketin kredisi
    state = seen[0]["messages"][1]["content"]
    assert "Sektör: Sağlık" in state and "Şirket:" in state

    # yetkisiz kullanıcı ve başka şirket
    assert client.post(f"/api/v1/company/{w['tenant']}/job-titles/design-chat", headers=w["member"]["h"], json=body).status_code == 403
    assert client.post(f"/api/v1/company/{w['tenant']}/job-titles/design-chat", headers=w["outsider"]["h"], json=body).status_code == 403
    # son mesaj kullanıcıdan olmalı
    bad = {"messages": [{"role": "assistant", "content": "merhaba"}]}
    assert client.post(f"/api/v1/company/{w['tenant']}/job-titles/design-chat", headers=w["admin"]["h"], json=bad).status_code == 422


def test_catalog_title_design_chat_platform_only(client, db, world, monkeypatch):
    w = world
    seen = []
    _fake(monkeypatch, "JSON değil, düz metin yanıt.", seen)
    body = {"messages": [{"role": "user", "content": "Tur operasyon uzmanı tanımlayalım."}], "draft": {"title": "Tur Operasyon Uzmanı"}}
    assert client.post("/api/v1/catalog/titles/design-chat", headers=w["admin"]["h"], json=body).status_code == 403
    r = client.post("/api/v1/catalog/titles/design-chat", headers=_super(client, db), json=body)
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["reply"] == "JSON değil, düz metin yanıt." and d["draft"]["title"] == "Tur Operasyon Uzmanı"
    assert seen[0]["tenant"] is None  # platform maliyeti


def test_clean_draft_limits():
    d = title_design.clean_draft({"title": "x" * 500, "responsibilities": [str(i) for i in range(40)], "evil": "y"})
    assert len(d["title"]) == 128 and len(d["responsibilities"]) == 20 and "evil" not in d
