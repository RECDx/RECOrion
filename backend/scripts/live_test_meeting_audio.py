"""
Canlı test (e2e/) için sentetik Türkçe toplantı kaydı üretir: EVREN voxcpm2 (metinden sese). Gerçek kişi sesi yoktur.

Kullanım (e2e/live_e2e.mjs çağırır):
    docker exec -w /app recorion_backend python scripts/live_test_meeting_audio.py /tmp/e2e_toplanti.mp3
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import httpx  # noqa: E402

from app.config import settings  # noqa: E402

TEXT = ("Merhaba arkadaşlar, bugünkü toplantının konusu depo için barkodlu stok sayım uygulaması. Şu an sayımı kağıtla yapıyoruz ve "
        "her ay sonu iki gün kaybediyoruz. Hedefimiz, depo personelinin el terminaliyle barkod okutup sayımı anında Logo'ya aktarması. "
        "Kapsamda üç şey var: ürün barkodu okutma, raf bazında sayım ve fark raporu. Fark raporu muhasebe müdürünün onayından geçmeden "
        "Logo'ya yazılmamalı. Teslim tarihi olarak dört hafta içinde canlıya almak istiyoruz. Riskler: depoda kablosuz ağ zayıf, ayrıca "
        "personel yeni sisteme alışmakta zorlanabilir. Bu yüzden çevrimdışı çalışabilmeli ve kısa bir kullanım eğitimi verilmeli.")


def main(out: str) -> None:
    r = httpx.post(f"{settings.EVREN_API_BASE_URL.rstrip('/')}/audio/speech", headers={"Authorization": f"Bearer {settings.EVREN_API_KEY}"},
                   json={"model": "voxcpm2", "input": TEXT, "voice": "default", "response_format": "mp3"}, timeout=180)
    r.raise_for_status()
    Path(out).write_bytes(r.content)
    print(f"{len(r.content)} bayt")


if __name__ == "__main__":
    main(sys.argv[1])
