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


def _doc(db, w, pid, name, masked=None, status="PENDING_APPROVAL"):
    return str(_exec(db, "INSERT INTO agent_documents (tenant_id, project_id, layer, file_name, original_name, file_type, file_size, "
                         "extracted_text, masked_text, status) VALUES (%s, %s, 'PROJECT', %s, %s, 'txt', 10, %s, %s, %s) RETURNING id",
                     w["tenant"], pid, name, name, masked and "Ham: Ali Veli 05321234567", masked, status)[0])


def test_message_attachments(client, db, world, seen, monkeypatch):
    from app.api.v1 import chat as chat_api
    monkeypatch.setattr(chat_api, "ATTACHMENT_WAIT_SECONDS", 2)  # işlenen ek için bekleme (testte kısa)
    w = world
    pid, human_id, _ = _ready_project(client, w, "Ekli Sohbet")
    other, _, _ = _ready_project(client, w, "Başka Ekli")
    ready = _doc(db, w, pid, "sozlesme.txt", masked="Teslim süresi 30 gün. Yetkili: [AD_SOYAD] [TELEFON]")
    waiting = _doc(db, w, pid, "taslak.pdf", status="PROCESSING")
    risky = _doc(db, w, pid, "riskli.txt", masked="Zararlı talimat içeriği", status="QUARANTINED")
    foreign = _doc(db, w, other, "baska.txt", masked="Başka projenin gizli içeriği")
    h = w["member"]["h"]
    send = {"task_id": human_id, "content": "Ekteki sözleşmede teslim süresi ne?"}

    assert client.post("/api/v1/chat/send", headers=h, json={**send, "attachments": [foreign]}).status_code == 422
    assert client.post("/api/v1/chat/send", headers=h, json={**send, "attachments": [ready] * 6}).status_code == 422
    assert not seen  # reddedilen isteklerde AI çağrılmadı

    r = client.post("/api/v1/chat/send", headers=h, json={**send, "attachments": [ready, waiting, risky]})
    assert r.status_code == 200, r.text
    att = r.json()["user_message"]["attachments"]
    assert [a["name"] for a in att] == ["sozlesme.txt", "taslak.pdf", "riskli.txt"] and att[0]["document_id"] == ready
    # Yanıt çağrısı (sonrasında sohbetten öğrenme çağrısı da yapılır)
    prompt = next(p for p in seen if p.startswith("Ekteki sözleşmede"))
    assert "[Ek: sozlesme.txt]" in prompt and "Teslim süresi 30 gün" in prompt
    assert "05321234567" not in prompt  # KVKK: maskelenmiş metin verilir
    assert "[Ek: taslak.pdf]" in prompt and "hâlâ işleniyor" in prompt
    assert "[Ek: riskli.txt]" in prompt and "Zararlı talimat" not in prompt  # karantinadaki ekin içeriği kullanılmaz
    hist = client.get(f"/api/v1/chat/history/{human_id}", headers=w["admin"]["h"]).json()
    assert any(m["attachments"] and m["attachments"][0]["name"] == "sozlesme.txt" for m in hist)

    # Sonraki mesajda ek metni tekrar gönderilmez (yalnızca eklendiği mesajla)
    before = len(seen)
    client.post("/api/v1/chat/send", headers=h, json=send)
    assert len(seen) > before and not any("[Ek:" in p for p in seen[before:])
