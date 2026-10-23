"""
ADIM 8.3: Work Area gerçek veri — mesaja dosya eki.

- Ek, bu projenin Proje Eki olmalı (başka projenin/katmanın belgesi eklenemez); en fazla 5.
- Eklerin KVKK maskeli metni yalnızca o mesajla AI'a verilir; işlenmemiş dosya için not düşülür.
- Mesajda ek bilgisi (kimlik, ad) saklanır ve geçmişte görünür.
"""
import pytest

from app.services.evren_client import ChatResult, evren_client
from tests.test_workflow import _exec, _ready_project, world  # noqa: F401  (fikstür)


@pytest.fixture
def seen(monkeypatch):
    prompts = []

    async def chat(model_code, messages, **kw):
        prompts.append(messages[-1]["content"])
        return ChatResult("Dosyayı okudum.", None, 100, 10, {})
    monkeypatch.setattr(evren_client, "chat", chat)
    return prompts


def _doc(db, w, pid, name, masked=None, status="PENDING_APPROVAL", guard='{"safe": true}'):
    return str(_exec(db, "INSERT INTO agent_documents (tenant_id, project_id, layer, file_name, original_name, file_type, file_size, "
                         "extracted_text, masked_text, status, guard_result) VALUES (%s, %s, 'PROJECT', %s, %s, 'txt', 10, %s, %s, %s, "
                         "CAST(%s AS jsonb)) RETURNING id",
                     w["tenant"], pid, name, name, masked and "Ham: Ali Veli 05321234567", masked, status, guard if masked else None)[0])


def test_message_attachments(client, db, world, seen, monkeypatch):
    from app.api.v1 import chat as chat_api
    monkeypatch.setattr(chat_api, "ATTACHMENT_WAIT_SECONDS", 2)  # işlenen ek için bekleme (testte kısa)
    w = world
    pid, human_id, _ = _ready_project(client, w, "Ekli Sohbet")
    other, _, _ = _ready_project(client, w, "Başka Ekli")
    ready = _doc(db, w, pid, "sozlesme.txt", masked="Teslim süresi 30 gün. Yetkili: [AD_SOYAD] [TELEFON]")
    waiting = _doc(db, w, pid, "taslak.pdf", status="PROCESSING")
    # Metni ve güvenlik sonucu hazır, öğrenme kartı henüz üretiliyor: kart beklenmeden okunur
    carding = _doc(db, w, pid, "karti-bekleyen.txt", masked="Kod adı ZEYTIN-7", status="PROCESSING")
    risky = _doc(db, w, pid, "riskli.txt", masked="Zararlı talimat içeriği", status="QUARANTINED")
    foreign = _doc(db, w, other, "baska.txt", masked="Başka projenin gizli içeriği")
    h = w["member"]["h"]
    send = {"task_id": human_id, "content": "Ekteki sözleşmede teslim süresi ne?"}

    assert client.post("/api/v1/chat/send", headers=h, json={**send, "attachments": [foreign]}).status_code == 422
    assert client.post("/api/v1/chat/send", headers=h, json={**send, "attachments": [ready] * 6}).status_code == 422
    assert not seen  # reddedilen isteklerde AI çağrılmadı

    r = client.post("/api/v1/chat/send", headers=h, json={**send, "attachments": [ready, waiting, risky, carding]})
    assert r.status_code == 200, r.text
    att = r.json()["user_message"]["attachments"]
    assert [a["name"] for a in att] == ["sozlesme.txt", "taslak.pdf", "riskli.txt", "karti-bekleyen.txt"] and att[0]["document_id"] == ready
    # Yanıt çağrısı (sonrasında sohbetten öğrenme çağrısı da yapılır)
    prompt = next(p for p in seen if p.startswith("Ekteki sözleşmede"))
    assert "[Ek: sozlesme.txt]" in prompt and "Teslim süresi 30 gün" in prompt
    assert "05321234567" not in prompt  # KVKK: maskelenmiş metin verilir
    assert "[Ek: taslak.pdf]" in prompt and "hâlâ işleniyor" in prompt
    assert "[Ek: riskli.txt]" in prompt and "Zararlı talimat" not in prompt  # karantinadaki ekin içeriği kullanılmaz
    assert "[Ek: karti-bekleyen.txt]\nKod adı ZEYTIN-7" in prompt
    hist = client.get(f"/api/v1/chat/history/{human_id}", headers=w["admin"]["h"]).json()
    assert any(m["attachments"] and m["attachments"][0]["name"] == "sozlesme.txt" for m in hist)

    # Sonraki mesajda ek metni tekrar gönderilmez (yalnızca eklendiği mesajla)
    before = len(seen)
    client.post("/api/v1/chat/send", headers=h, json=send)
    assert len(seen) > before and not any("[Ek:" in p for p in seen[before:])


def test_chat_falls_back_when_model_busy(client, world, monkeypatch):
    """Personelin modeli meşgul (EVREN 503) ise sohbet paketteki yedek modelle yanıtlanır."""
    from app.services.evren_client import EvrenError
    calls = []

    async def chat(model_code, messages, **kw):
        calls.append(model_code)
        if len(calls) == 1:
            raise EvrenError("Model şu anda dolu")
        return ChatResult("Yedek modelden yanıt.", None, 50, 5, {})
    monkeypatch.setattr(evren_client, "chat", chat)
    w = world
    pid, human_id, _ = _ready_project(client, w, "Yedek Modelli Sohbet")
    r = client.post("/api/v1/chat/send", headers=w["admin"]["h"], json={"task_id": human_id, "content": "Durum?"})
    assert r.status_code == 200, r.text
    assert r.json()["assistant_message"]["content"] == "Yedek modelden yanıt." and len(set(calls[:2])) == 2
