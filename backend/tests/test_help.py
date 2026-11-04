"""
ADIM 15: Yardım (Bilgi Birikimi) ve RECAi Yardım Asistanı.

- İçindekiler ve sayfalar kitleye (RECDx / müşteri) ve menü izinlerine göre süzülür; yetkisiz sayfa ve Merkez görselleri 403.
- F1: ekran anahtarı (+ açık pencere başlığı) doğru sayfayı ve sayfa içi başlığı bulur.
- Arama Türkçe, yalnız görülebilen sayfalar.
- Asistan: yetkili bölümlerden yanıt + kaynak + ekrana git; konu yetki dışındaysa modele gitmeden "cevap veremiyorum";
  modelin yetki dışı ekran/kaynak önermesi süzülür; model yanıt vermezse sayfalar listelenir.
"""
import asyncio
import json

import pytest

from app.services import llm_gateway
from tests.test_lifecycle import super_headers, tag  # noqa: F401  (fikstür)
from tests.test_workflow import world  # noqa: F401  (fikstür)


@pytest.fixture(scope="module", autouse=True)
def pages(client):
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
    from sqlalchemy.pool import NullPool

    from app.config import settings
    from app.services import help_center

    Session = async_sessionmaker(create_async_engine(settings.DATABASE_URL, poolclass=NullPool), expire_on_commit=False)

    async def run():  # test kendi döngüsünde: havuzsuz bağlantı
        async with Session() as db:
            await help_center.sync(db, force=True)
    asyncio.run(run())


def _guides(client, h):
    return {g["guide"]: g["pages"] for g in client.get("/api/v1/help/tree", headers=h).json()["guides"]}


def test_tree_and_pages_follow_audience_and_permissions(client, world, super_headers):
    w = world
    member, admin = _guides(client, w["member"]["h"]), _guides(client, w["admin"]["h"])
    sa = _guides(client, super_headers)
    assert "merkez" not in member and "merkez" not in admin and "merkez" in sa
    slugs = lambda g: {p["slug"] for p in g}  # noqa: E731
    otomasyon = "sirket/kurum-zekasi/otomasyonlar"
    assert otomasyon in slugs(admin["sirket"]) and otomasyon not in slugs(member["sirket"])
    assert any(s.startswith("sirket/recslip-app-v2") for s in slugs(admin["sirket"]))
    assert not any(s.startswith("sirket/recslip-app-v2") for s in slugs(member["sirket"]))
    assert "workarea/work-space/onaylarim" in slugs(member["workarea"])
    # Sayfa: yetkisiz 403, yetkili gövde + görseller
    assert client.get("/api/v1/help/page", params={"slug": otomasyon}, headers=w["member"]["h"]).status_code == 403
    merkez = next(iter(slugs(sa["merkez"])))
    assert client.get("/api/v1/help/page", params={"slug": merkez}, headers=w["admin"]["h"]).status_code == 403
    r = client.get("/api/v1/help/page", params={"slug": otomasyon}, headers=w["admin"]["h"]).json()
    assert "RECSlip.App v2 aylık süreç" in r["body"] and "company/AUTOMATIONS" in r["screens"]
    img = next(x for x in r["body"].split("(") if x.split(")")[0].endswith(".webp")).split(")")[0]
    assert client.get(f"/api/v1/help/assets/{img}", headers=w["member"]["h"]).headers["content-type"] == "image/webp"
    assert client.get("/api/v1/help/assets/sy-kayitli-sirketler.webp", headers=w["admin"]["h"]).status_code == 403
    assert client.get("/api/v1/help/assets/sy-kayitli-sirketler.webp", headers=super_headers).status_code == 200
    assert client.get("/api/v1/help/assets/..%2F..%2Fmain.py", headers=super_headers).status_code == 404
    assert client.get("/api/v1/help/tree").status_code == 401


def test_f1_context_and_search(client, world, super_headers):
    w = world
    ctx = lambda h, screen, title=None: client.get("/api/v1/help/context", headers=h, params={"screen": screen, **({"title": title} if title else {})})  # noqa: E731
    r = ctx(w["admin"]["h"], "company/AUTOMATIONS", "RECSlip.App v2 aylık süreç").json()
    assert r["page"]["slug"] == "sirket/kurum-zekasi/otomasyonlar" and r["anchor"].startswith("recslip-app-v2-aylik-surec")
    assert ctx(w["member"]["h"], "workspace/project/recslip").json()["page"]["title"] == "RECSlip sekmesi"
    assert ctx(w["member"]["h"], "workspace/INBOX").json()["page"]["slug"] == "workarea/work-space/onaylarim"
    assert ctx(super_headers, "super/TENANTS").json()["page"]["guide"] == "merkez"
    # Yetkisiz ekranın sayfası yerine genel düzen sayfası (menü erişimi olmayan uzman)
    r = ctx(w["member"]["h"], "company/AUTOMATIONS").json()
    assert r["page"]["slug"] != "sirket/kurum-zekasi/otomasyonlar"
    # Arama: Türkçe çekimlerle, yalnız görülebilen sayfalar
    hits = client.get("/api/v1/help/search", headers=w["admin"]["h"], params={"q": "otomasyonlar kuralı"}).json()
    assert hits and any("otomasyon" in h["slug"] for h in hits)
    member_hits = client.get("/api/v1/help/search", headers=w["member"]["h"], params={"q": "kayıtlı şirketler pasife al"}).json()
    assert all(h["guide"] != "merkez" for h in member_hits)


class FakeRECAi:
    def __init__(self):
        self.calls, self.reply, self.fail = [], None, False

    async def chat(self, ctx, messages, **kw):
        self.calls.append(messages)
        if self.fail:
            raise llm_gateway.LLMUnavailable("meşgul", "m1")
        return type("R", (), {"content": json.dumps(self.reply), "fallback_from": None})()


def test_recai_answers_from_permitted_pages_and_refuses_the_rest(client, world, super_headers, monkeypatch):
    w = world
    fake = FakeRECAi()
    monkeypatch.setattr(llm_gateway, "chat", fake.chat)
    ask = lambda h, q, **kw: client.post("/api/v1/help/ask", headers=h, json={"question": q, **kw}).json()  # noqa: E731

    # Şirket yöneticisi: RECSlip kurulumu — yetkili bölümlerden yanıt, kaynak ve "Ekrana git"
    fake.reply = {"cevap": "**Otomasyonlar** ekranında **Kur** düğmesine basın.", "kaynaklar": ["sirket/kurum-zekasi/otomasyonlar"],
                  "ekran": "company/AUTOMATIONS", "yetki_disi": False}
    r = ask(w["admin"]["h"], "RECSlip aylık süreci otomasyonlar ekranından nasıl kurulur?", screen="company/AUTOMATIONS")
    assert not r["denied"] and "Kur" in r["answer"] and r["navigate"] == "company/AUTOMATIONS"
    assert r["sources"][0]["slug"] == "sirket/kurum-zekasi/otomasyonlar"
    sent = json.dumps(fake.calls[-1], ensure_ascii=False)
    assert "Merkez Yönetim" not in sent, "modele yalnız yetkili bölümler gider"

    # Uzman: yalnız RECDx yönetim ekranlarında geçen konu — modele gitmeden ret, Merkez içeriği anılmaz
    n = len(fake.calls)
    r = ask(w["member"]["h"], "LLM TL fiyatlarını ve EVREN model kataloğunu nasıl güncellerim?")
    assert r["denied"] and "cevap veremiyorum" in r["answer"] and "Merkez" not in r["answer"] and len(fake.calls) == n

    # Uzman: sınırdaki konular (müşteri kılavuzunda ama menüsü kapalı / RECDx ekranı) — modele yalnız yetkili bölümler ve
    # yetki dışı başlıkların ADI gider; model yetki dışı derse ret
    fake.reply = {"cevap": "", "kaynaklar": [], "ekran": "", "yetki_disi": True}
    for q in ["Kayıtlı şirketler ekranında bir şirketi nasıl pasife alırım ve kiralama paketini nasıl değiştiririm?",
              "Otomasyonlar ekranında hazır kuralları nasıl kurarım, yeni otomasyon kuralı nasıl eklenir?"]:
        r = ask(w["member"]["h"], q)
        assert r["denied"] and "cevap veremiyorum" in r["answer"]
        if len(fake.calls) > n:
            prompt = fake.calls[-1][0]["content"]
            assert "YETKİSİ OLMAYAN" in prompt and "Sistem Kimliği" not in prompt and "[sirket/kurum-zekasi/otomasyonlar]" not in prompt
            n = len(fake.calls)

    # Model yetki dışı ekran/kaynak önerirse süzülür; model "yetki dışı" derse ret
    fake.reply = {"cevap": "Onaylarım'dan karar verin.", "kaynaklar": ["merkez/x", "workarea/work-space/onaylarim"], "ekran": "super/TENANTS"}
    r = ask(w["member"]["h"], "Onaylarım ekranında RECSlip fişini nasıl onaylarım?")
    assert not r["denied"] and r["navigate"] is None and all(not s["slug"].startswith("merkez") for s in r["sources"])
    fake.reply = {"cevap": "", "kaynaklar": [], "ekran": "", "yetki_disi": True}
    assert ask(w["member"]["h"], "Onaylarım ekranında başkasının onayını nasıl görürüm?")["denied"]

    # Model yanıt vermezse: ilgili sayfalar listelenir
    fake.fail = True
    r = ask(w["member"]["h"], "Onaylarım ekranında RECSlip fişini nasıl onaylarım?")
    assert r.get("degraded") and r["sources"] and not r["denied"]
    # Süper yönetici Merkez Yönetim konusunu sorabilir
    fake.fail = False
    fake.reply = {"cevap": "Kartta **Pasife Al**'a basın.", "kaynaklar": ["merkez/musteriler/kayitli-sirketler"], "ekran": "super/TENANTS"}
    r = ask(super_headers, "Kayıtlı şirketler ekranında bir şirketi nasıl pasife alırım?")
    assert not r["denied"] and r["navigate"] == "super/TENANTS"
