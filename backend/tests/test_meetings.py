"""
ADIM 11.3: toplantı kaydından proje taslağı (gerçek ffmpeg; EVREN yazıya çevirme ve Beyin AI sahte).

- Yükleme: yalnızca project:create; ses/video olmayan dosya reddedilir; RECDx göremez (KVKK).
- Arka planda: 16 kHz parçalar → yazıya → KVKK maskeleme (TCKN, e-posta, telefon) → taslak (adımlar doğrulanır).
- Ham ses saklanmaz (geçici klasör silinir). Sessiz/anlamsız kayıtta anlaşılır hata.
- Taslaktan proje: plan taslak (onaysız), kayıt bir kez kullanılır; kayıt yalnızca yükleyene (veya project:manage) görünür.
"""
import io
import json
import math
import shutil
import struct
import time
import wave

import pytest

from tests.test_integrations import _super
from tests.test_workflow import world  # noqa: F401  (fikstür)

pytestmark = pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="ffmpeg yok")

TRANSCRIPT = ("Bugün depo için barkodlu sayım uygulamasını konuştuk. El terminaliyle barkod okutulacak, raf bazında sayım ve fark raporu olacak. "
              "Fark raporu muhasebe müdürü onaylamadan Logo'ya yazılmayacak. Dört hafta içinde canlıya alınmalı. "
              "Muhasebe müdürünün e-postası elif.kaya@ornek.com, telefonu 0532 123 45 67, T.C. kimlik numarası 10000000146.")


def _wav(seconds=3):
    buf = io.BytesIO()
    w = wave.open(buf, "wb")
    w.setnchannels(1)
    w.setsampwidth(2)
    w.setframerate(16000)
    w.writeframes(b"".join(struct.pack("<h", int(2000 * math.sin(2 * math.pi * 300 * i / 16000))) for i in range(16000 * seconds)))
    w.close()
    return buf.getvalue()


@pytest.fixture
def fake_evren(monkeypatch):
    from app.services.evren_client import ChatResult, evren_client

    seen = {"audio": [], "prompts": []}
    say = {"text": TRANSCRIPT}

    async def transcribe(audio, filename, mime, model_code, language="tr"):
        assert model_code == "qwen3-asr-1.7b" and audio[:4] == b"RIFF" and filename.endswith(".wav")
        w = wave.open(io.BytesIO(audio))
        assert w.getframerate() == 16000 and w.getnchannels() == 1  # ffmpeg dönüştürdü
        seen["audio"].append(len(audio))
        return say["text"]

    async def chat(model_code, messages, **kw):
        seen["prompts"].append(messages[-1]["content"])
        return ChatResult(json.dumps({
            "name": "Depo barkodlu sayım uygulaması", "kind": "PROJECT", "description": "Kâğıtla sayım yerine el terminaliyle anlık sayım.",
            "requirements": "- Barkod okutma\n- Raf bazında sayım\n- Fark raporu muhasebe onayıyla Logo'ya\n- 4 hafta",
            "steps": [{"key": "S1", "title": "İhtiyaç analizi", "job_title": "İş Analisti", "estimated_days": 2},
                      {"key": "S2", "title": "Uygulama geliştirme", "job_title": "Yazılım Geliştirici", "estimated_days": 8, "depends_on": ["S1"]},
                      {"key": "S3", "title": "Döngü", "depends_on": ["S9"]}],
            "risks": ["Kablosuz ağ zayıf"], "participants": ["depo şefi", "muhasebe müdürü"], "open_questions": ["Kaç el terminali var?"]}),
            None, 900, 300, {})
    monkeypatch.setattr(evren_client, "transcribe", transcribe, raising=False)
    monkeypatch.setattr(evren_client, "chat", chat)
    return seen, say


def _wait(client, h, url, timeout=60):
    end = time.time() + timeout
    while time.time() < end:
        r = client.get(url, headers=h).json()
        if r["status"] != "PROCESSING":
            return r
        time.sleep(0.5)
    raise AssertionError(f"kayıt işlenmedi: {r}")


def test_meeting_to_project(client, db, world, fake_evren):
    from app.services import meetings

    seen, _ = fake_evren
    w = world
    admin, member = w["admin"]["h"], w["member"]["h"]
    base = f"/api/v1/company/{w['tenant']}/meetings"
    files = {"file": ("toplanti.wav", _wav(), "audio/wav")}
    assert client.post(base, headers=member, files=files, data={"title": "x"}).status_code == 403
    assert client.post(base, headers=_super(client, db), files=files).status_code == 403  # KVKK
    assert client.post(base, headers=admin, files={"file": ("not.txt", b"merhaba", "text/plain")}).status_code == 422

    r = client.post(base, headers=admin, files=files, data={"title": "Depo sayım toplantısı"})
    assert r.status_code == 202, r.text
    rec = _wait(client, admin, f"{base}/{r.json()['id']}")
    assert rec["status"] == "READY", rec
    assert rec["duration_sec"] == 3.0 and len(seen["audio"]) == 1
    assert "elif.kaya@ornek.com" not in rec["transcript"] and "10000000146" not in rec["transcript"]
    assert rec["pii"].get("EMAIL") == 1 and rec["pii"].get("TCKN") == 1
    assert "elif.kaya@ornek.com" not in seen["prompts"][0]  # Beyin AI'a da maskeli metin gitti
    plan = rec["draft"]["plan"]
    assert [s["key"] for s in plan["steps"]] == ["S1", "S2", "S3"] and plan["steps"][2]["depends_on"] == []  # geçersiz bağımlılık atıldı
    assert not (meetings.WORK_DIR / rec["id"]).exists()  # ham ses ve parçalar silindi

    assert client.get(f"{base}/{rec['id']}", headers=member).status_code == 403  # project:create yok
    r = client.post(f"{base}/{rec['id']}/project", headers=admin, json={"name": "Depo sayım (toplantıdan)", "description": rec["draft"]["description"],
                                                                         "requirements": rec["draft"]["requirements"]})
    assert r.status_code == 200, r.text
    assert r.json()["steps"] == 3
    p = client.get(f"/api/v1/projects/{r.json()['id']}", headers=admin).json()
    assert p["requirements"].startswith("- Barkod") and p["plan"]["approved"] is False and p["plan"]["from_meeting"]["title"] == "Depo sayım toplantısı"
    assert client.post(f"{base}/{rec['id']}/project", headers=admin, json={"name": "İkinci kez"}).status_code == 409


def test_meeting_without_speech_and_bad_audio(client, db, world, fake_evren):
    _, say = fake_evren
    w = world
    admin = w["admin"]["h"]
    base = f"/api/v1/company/{w['tenant']}/meetings"
    say["text"] = "Evet."
    r = client.post(base, headers=admin, files={"file": ("sessiz.wav", _wav(), "audio/wav")}, data={"source": "BROWSER"})
    rec = _wait(client, admin, f"{base}/{r.json()['id']}")
    assert rec["status"] == "FAILED" and "anlaşılır konuşma" in rec["error"] and rec["source"] == "BROWSER"
    r = client.post(base, headers=admin, files={"file": ("bozuk.mp3", b"ID3 bu bir ses degil" * 50, "audio/mpeg")})
    rec = _wait(client, admin, f"{base}/{r.json()['id']}")
    assert rec["status"] == "FAILED" and ("okunamadı" in rec["error"] or "çözülemedi" in rec["error"])
