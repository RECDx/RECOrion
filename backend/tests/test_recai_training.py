"""
İSTEK #743: RECAi eğitim veri hattı.

- Maskeleme: TCKN, VKN, IBAN, e-posta, telefon, firma, unvanlı kişi, adres, plaka, tutar, bilinen adlar → tutarlı sahte değer;
  aynı değer kayıt içinde aynı sahte karşılığı alır; iki ayrı kayıtta karşılık sabit değildir (eşleme tutulmaz).
- İzin: varsayılan açık; şirket yöneticisi kapatır; RECDx personeli değiştiremez; üye değiştiremez.
- Veri seti: yalnız izinli şirketler; DOGRU → sft; MODEL_HATASI + eş → dpo; ORTAM/DEGERLENDIRICI olumsuz dosyalara girmez;
  gerçek ad/IBAN sete girmez; Merkez yalnız sayıları görür.
"""
import json

from app.services import storage
from app.services import training_data as td
from tests.test_integrations import _super
from tests.test_workflow import _exec, world  # noqa: F401  (fikstür)

TCKN = "10000000146"  # kontrol haneleri geçerli örnek


def test_masker_consistent_and_irreversible():
    text = (f"Sayın Ahmet Yılmaz (TCKN {TCKN}) için Deniz Lojistik Ltd. Şti. adına teklif. Vergi No: 1234567890. "
            "IBAN TR33 0006 1005 1978 6457 8413 26, tel 0532 123 45 67, ahmet@firma.com. Adres: Kadıköy Mah. Bağdat Cad. No:12. "
            "Araç 34 ABC 123. Tutar 125.000 TL. Tekrar: Ahmet Yılmaz, ahmet@firma.com.")
    m = td.Masker({"Ahmet Yılmaz": "KISI"})
    out = m.text(text)
    for secret in ("Ahmet", "Yılmaz", TCKN, "Deniz Lojistik", "1234567890", "TR33", "0532", "ahmet@firma.com", "Bağdat", "34 ABC 123", "125.000"):
        assert secret not in out, (secret, out)
    assert "Sayın " in out and "Vergi No: " in out and " TL" in out  # yapı korunur
    fake_person = m.map[("KISI", "ahmet yılmaz")]
    assert out.count(fake_person) == 2  # aynı kişi → aynı sahte ad
    assert m.counts["KISI"] >= 1 and m.counts["TCKN"] == 1 and m.counts["IBAN"] == 1
    # eşleme tutulmaz: yeni kayıtta karşılıklar yeniden rastgele (sabit bir sözlük yok)
    others = {td.Masker({"Ahmet Yılmaz": "KISI"}).text("Ahmet Yılmaz") for _ in range(8)}
    assert len(others) > 1
    obj = td.Masker().obj({"partner_name": "Deniz Lojistik", "email": "a@b.com", "lines": [{"product": "Diş fırçası", "qty": 3}]})
    assert obj["partner_name"] != "Deniz Lojistik" and obj["email"] != "a@b.com" and obj["lines"][0]["product"] == "Diş fırçası"


def _rec(db, tenant, agent, label, cause=None, output="Çıktı", source="APPROVAL", pair=None, feedback=None):
    return str(_exec(db, "INSERT INTO learning_records (id, tenant_id, agent_id, source, label, cause, task_input, output, feedback, pair_id, "
                         "job_title, data, lesson_status) VALUES (gen_random_uuid(), %s, %s, %s, %s, %s, %s, %s, %s, %s, 'Uzman', '{}', 'NONE') "
                         "RETURNING id", tenant, agent, source, label, cause,
                     "Adım: Teklif hazırla\nKabul ölçütü: Fiyat tablosu", output, feedback, pair)[0])


def test_consent_and_dataset(client, db, world, monkeypatch):
    w = world
    admin = w["admin"]["h"]
    c = client.get(f"/api/v1/company/{w['tenant']}/recai-consent", headers=admin).json()
    assert c["consent"] is True and "maskelendikten sonra" in c["text"]  # varsayılan açık (kullanıcı kararı)
    sa = _super(client, db)
    assert client.get(f"/api/v1/company/{w['tenant']}/recai-consent", headers=sa).json()["consent"] is True  # Merkez görür
    assert client.put(f"/api/v1/company/{w['tenant']}/recai-consent", headers=sa, json={"consent": False}).status_code == 403  # değiştiremez
    assert client.put(f"/api/v1/company/{w['tenant']}/recai-consent", headers=w["member"]["h"], json={"consent": False}).status_code == 403

    good = _rec(db, w["tenant"], w["agent"], "DOGRU", output="Sayın Ahmet Yılmaz, IBAN TR33 0006 1005 1978 6457 8413 26. Fiyat tablosu ekte.")
    _rec(db, w["tenant"], w["agent"], "YANLIS", "MODEL_HATASI", output="Tablo yok.", source="REJECTION", pair=good, feedback="Fiyat tablosu eksik")
    _rec(db, w["tenant"], w["agent"], "YANLIS", "DEGERLENDIRICI", output="Haksız ret edilen çıktı", source="REVIEW")
    _rec(db, w["tenant"], w["agent"], "YANLIS", "ORTAM", output="Ortam hatası çıktısı", source="TEST_RUN")

    objects = {}

    async def put_object(key, data, content_type=None):
        objects[key] = data
    monkeypatch.setattr(storage, "put_object", put_object)

    s = client.get("/api/v1/system/recai-training/summary", headers=sa).json()
    assert s["eligible"]["tenants_consenting"] >= 1 and s["eligible"]["pairs"] >= 1
    assert client.get("/api/v1/system/recai-training/summary", headers=admin).status_code == 403  # yalnız Merkez
    r = client.post("/api/v1/system/recai-training/datasets", headers=sa, json={"note": "deneme"})
    assert r.status_code == 201, r.text
    ds = r.json()
    prefix = ds["storage_prefix"]
    lines = lambda n: [json.loads(x) for x in objects[f"{prefix}/{n}.jsonl"].decode("utf-8").splitlines() if x.strip()]  # noqa: E731
    sft, dpo, kto, reward = lines("sft"), lines("dpo"), lines("kto"), lines("reward")
    mine = [x for x in sft if "Fiyat tablosu ekte" in x["messages"][-1]["content"]]
    assert mine and "Ahmet" not in json.dumps(mine) and "TR33" not in json.dumps(mine)
    assert any(x["rejected"] == "Tablo yok." and "Fiyat tablosu ekte" in x["chosen"] for x in dpo)
    dumped = json.dumps(kto + reward + dpo, ensure_ascii=False)
    assert "Haksız ret" not in dumped and "Ortam hatası" not in dumped  # yalnız AI hatası olumsuz örnek
    assert "tenant" not in json.dumps(sft[0]["meta"])
    assert json.loads(objects[f"{prefix}/manifest.json"])["counts"]["dpo"] == ds["counts"]["dpo"]

    # izin kapatılınca sonraki sete girmez
    assert client.put(f"/api/v1/company/{w['tenant']}/recai-consent", headers=admin, json={"consent": False}).json()["consent"] is False
    ds2 = client.post("/api/v1/system/recai-training/datasets", headers=sa, json={}).json()
    sft2 = [json.loads(x) for x in objects[f"{ds2['storage_prefix']}/sft.jsonl"].decode("utf-8").splitlines() if x.strip()]
    assert not any("Fiyat tablosu ekte" in x["messages"][-1]["content"] for x in sft2) and ds2["version"] == ds["version"] + 1
    client.put(f"/api/v1/company/{w['tenant']}/recai-consent", headers=admin, json={"consent": True})
