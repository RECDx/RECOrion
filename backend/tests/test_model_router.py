"""
ADIM 11.4: akıllı model yönlendirici ve kalite test seti (EVREN sahte).

- Puanlama kuralla: her vakada iyi çıktı tam puan, kötü çıktı düşük puan; kod asla çalıştırılmaz (yalnızca sözdizimi).
- İş türü sınıflandırma.
- Koşu → öneri (kalite + hız + güvenilirlik) → Süper Admin onayı → platform varsayılanı iş türüne göre değişir;
  AI personelin seçili modeli ve açık seçim önce gelir; eşik altı model gerekçesiz onaylanamaz; yönlendirme kaldırılabilir.
- Yalnızca Süper Admin.
"""
import time
import uuid

import pytest

from app.services import model_router as rsvc
from tests.test_integrations import _super
from tests.test_workflow import _exec, world  # noqa: F401  (fikstür)

GOOD = {
    "kod-iban": "```python\ndef iban_dogrula(iban: str) -> bool:\n    s = iban.replace(' ', '').upper()\n    if not s.startswith('TR') or len(s) != 26:\n"
                "        return False\n    r = s[4:] + s[:4]\n    n = ''.join(str(int(c, 36)) for c in r)\n    return int(n) % 97 == 1\n```",
    "kod-sql": "SELECT musteri_id, SUM(tutar) AS toplam FROM siparisler WHERE EXTRACT(YEAR FROM tarih) = 2026 GROUP BY musteri_id ORDER BY toplam DESC LIMIT 5;",
    "analiz-iade": "Riskler:\n- Kargo firmasıyla entegrasyon gecikmesi\n- Stok kayıtlarının hatalı güncellenmesi\n- Ödeme iadesinin gecikmesi\n"
                   "İlk adımlar:\n1. Mevcut iade sürecini çıkar\n2. Kargo ve ödeme entegrasyonlarını belirle\n3. İade portalını tasarla",
    "analiz-hikaye": "1. Bir bayi olarak, sipariş durumunu görmek istiyorum, böylece planlama yapabilirim.\n2. Bir bayi olarak, kargo takip numarasını "
                     "almak istiyorum, böylece gönderimi izleyebilirim.\n3. Bir bayi olarak, gecikmede e-posta almak istiyorum, böylece müşterimi bilgilendiririm.",
    "ozet-toplanti": "Depo sayımı kâğıttan el terminaliyle barkod okutmaya geçecek; raf bazında sayım ve fark raporu olacak. Fark raporu muhasebe "
                     "onayı olmadan Logo'ya yazılmayacak. Dört hafta içinde canlıya alınacak; zayıf kablosuz ağ nedeniyle çevrimdışı çalışmalı.",
    "ozet-madde": "- İşe alım ilan, ön eleme, mülakat ve teklif aşamalarından oluşur.\n- Aday verileri KVKK'ya uygun saklanır ve süresi dolanlar silinir.\n"
                  "- Oryantasyon planı hazırlanır ve SGK bildirgesi işe başlamadan önce verilir.",
    "yazim-eposta": "Sayın Müşterimiz,\n\nSiparişinizin 3 gün gecikeceğini bildirmekten üzgünüz ve özür dileriz. Yeni teslim tarihi [TARİH] olacaktır. "
                    "Anlayışınız için teşekkür ederiz.\n\nSaygılarımızla",
    "yazim-duzelt": "Yarınki toplantıya herkesin katılması gerekiyor, saat onda başlayacak.",
    "json-fatura": '{"fatura_no": "FTR-2026-0042", "tarih": "2026-10-12", "tutar": 15750.0, "para_birimi": "TRY"}',
    "json-siniflandir": '[{"id": 1, "kategori": "KARGO"}, {"id": 2, "kategori": "FATURA"}, {"id": 3, "kategori": "URUN"}]',
}
BAD = "Bu konuda yardımcı olamıyorum. import os; os.system('echo kotu')"


def _case(code):
    return next(c for c in rsvc.load_suite()["cases"] if c["code"] == code)


def test_grading_rules_are_strict_and_never_execute_code():
    suite = rsvc.load_suite()
    assert {c["task_type"] for c in suite["cases"]} == set(rsvc.TASK_TYPES)
    for c in suite["cases"]:
        good, _ = rsvc.grade(c, GOOD[c["code"]])
        bad, _ = rsvc.grade(c, BAD)
        assert good == 1.0, (c["code"], rsvc.grade(c, GOOD[c["code"]]))
        assert bad < 0.5, (c["code"], bad)
    # Sözdizimi bozuk kod ve yanlış fonksiyon adı puan kaybettirir; kod çalıştırılmaz
    s, checks = rsvc.grade(_case("kod-iban"), "```python\ndef baska(:\n```")
    assert s < 0.5 and not next(x for x in checks if x["type"] == "python_parse")["ok"]
    assert rsvc.grade(_case("json-fatura"), '{"fatura_no": "FTR-2026-0042", "tarih": "12.10.2026", "tutar": "15.750,00", "para_birimi": "TL"}')[0] < 1.0
    assert rsvc.grade(_case("json-fatura"), '{"fatura_no": "FTR-2026-0042", "tarih": "2026-10-12", "tutar": "15.750,00", "para_birimi": "TL"}')[0] == 1.0


def test_classify_task_types():
    assert rsvc.classify("Bayi portalı API geliştirme", "Sipariş servisini Python ile yaz") == "CODE"
    assert rsvc.classify("Toplantı notlarını özetle") == "SUMMARY"
    assert rsvc.classify("Müşterilere duyuru e-postası metni") == "WRITING"
    assert rsvc.classify("Faturalardan alanları çıkar, JSON tablo ver") == "STRUCTURED"
    assert rsvc.classify("Pazar ve rakip değerlendirmesi") == "ANALYSIS"
    assert rsvc.classify("Ekran tasarımı", job_title="Yazılım Geliştirici") == "CODE"


def test_quality_run_recommend_approve_and_route(client, db, world, monkeypatch):
    from app.db.models import Actor
    from app.db.session import AsyncSessionLocal
    from app.services import llm_gateway
    from app.services.evren_client import ChatResult, evren_client

    cases = {c["prompt"]: c["code"] for c in rsvc.load_suite()["cases"]}

    async def chat(model_code, messages, **kw):
        code = cases.get(messages[-1]["content"])
        if model_code == "deepseek-v4-flash":
            return ChatResult(GOOD.get(code, "tamam"), None, 100, 50, {})
        return ChatResult(BAD, None, 100, 50, {})  # diğer model kötü cevap verir
    monkeypatch.setattr(evren_client, "chat", chat)

    sa, admin = _super(client, db), world["admin"]["h"]
    assert client.get("/api/v1/system/model-router", headers=admin).status_code == 403
    assert client.post("/api/v1/system/model-router/runs", headers=sa, json={"models": ["qwen3-embedding-8b"]}).status_code == 422  # sohbet modeli değil
    r = client.post("/api/v1/system/model-router/runs", headers=sa, json={"models": ["deepseek-v4-flash", "mimo-v2.6-pro"]})
    assert r.status_code == 202, r.text
    run_id = r.json()["id"]
    assert client.post("/api/v1/system/model-router/runs", headers=sa, json={"models": ["glm-5.3"]}).status_code == 409  # süren koşu
    end = time.time() + 60
    while time.time() < end:
        run = client.get(f"/api/v1/system/model-router/runs/{run_id}", headers=sa).json()
        if run["status"] != "RUNNING":
            break
        time.sleep(0.5)
    assert run["status"] == "DONE" and len(run["results"]) == 20, run
    rec = run["recommendation"]
    for tt in rsvc.TASK_TYPES:
        assert rec[tt]["recommended"] == "deepseek-v4-flash", (tt, rec[tt])
        assert next(c for c in rec[tt]["candidates"] if c["model_code"] == "mimo-v2.6-pro")["eligible"] is False

    # Eşik altı model gerekçesiz onaylanamaz; önerilen onaylanır, iz tutulur
    assert client.post("/api/v1/system/model-router/routes", headers=sa,
                       json={"task_type": "CODE", "model_code": "mimo-v2.6-pro", "run_id": run_id}).status_code == 422
    r = client.post("/api/v1/system/model-router/routes", headers=sa, json={"task_type": "CODE", "model_code": "glm-5.3", "note": "Deneme"})
    assert r.status_code == 200 and r.json()["routes"]["CODE"] == "glm-5.3"
    ov = client.get("/api/v1/system/model-router", headers=sa).json()
    assert ov["decisions"][0]["task_type"] == "CODE" and ov["decisions"][0]["model_code"] == "glm-5.3"
    assert ov["recommendation_run_id"] == run_id

    async def resolved(task_type, actor_id=None):
        async with AsyncSessionLocal() as s:
            tenant = await llm_gateway._tenant(s, uuid.UUID(world["tenant"]))
            return (await llm_gateway.resolve_model(s, tenant, "AGENT_CHAT", None, actor_id, task_type)).model_code
    assert client.portal.call(resolved, "CODE") == "glm-5.3"  # onaylı yön platform varsayılanını değiştirdi
    assert client.portal.call(resolved, "WRITING") == "deepseek-v4-flash"  # yön yok → platform varsayılanı
    agent_model = _exec(db, "SELECT m.model_code FROM actors a JOIN llm_models m ON m.id = a.preferred_model_id WHERE a.id = %s", world["agent"])
    if agent_model:  # AI personelin seçili modeli yönlendirmeden önce gelir
        assert client.portal.call(resolved, "CODE", uuid.UUID(world["agent"])) == agent_model[0]
    assert client.post("/api/v1/system/model-router/routes", headers=sa, json={"task_type": "CODE", "model_code": None}).json()["routes"]["CODE"] is None
    assert client.portal.call(resolved, "CODE") == "deepseek-v4-flash"
