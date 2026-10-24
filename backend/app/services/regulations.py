"""
Türkiye mevzuat bilgi paketleri (ADIM 11.2).

- Paket = özet kartlar (başlık, yasal dayanak, metin, etiketler, resmi kaynak bağlantıları). Platform içeriğidir, müşteri verisi yok.
- Taslak (draft) yalnızca RECDx'te düzenlenir. Müşteri ve AI personel yalnızca UZMAN KONTROLÜNDEN geçmiş yayını (published)
  görür; yayın sürüm numarası, kontrol eden, kontrol tarihi ve notuyla kaydedilir (kullanıcı kararı 24.10.2026).
- Şirket paketi açar; AI personel iş adımı/sohbet metniyle ilgili kartları (yerel kelime eşleştirmesi; kart sayısı az,
  sonuç öngörülebilir) bağlamında kaynak ve sürüm göstererek kullanır. Her kullanımda "hukuki danışmanlık değildir" uyarısı.
"""
import json
import re
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import RegulationPack, TenantRegulationPack

SEED_FILE = Path(__file__).resolve().parent.parent / "seed" / "regulation_packs.json"
DISCLAIMER = ("Bu bilgiler genel bilgilendirme amaçlıdır, hukuki/mali danışmanlık değildir. Mevzuat değişebilir; işlem öncesi "
              "güncel resmi kaynağı ve gerekiyorsa uzmanınızı kontrol edin.")
MAX_CARDS, MAX_CONTEXT_CARDS, MAX_CONTEXT_CHARS = 60, 3, 4000
STOP = set("ve veya ile için bir bu şu o da de ki mi mı mu mü ne nasıl nedir gibi olan olarak daha çok en her hangi kadar "
           "sonra önce ise ama fakat ancak yani biz siz onlar ben sen var yok gerek lütfen hazırla yaz yap ilgili yeni "
           "şirket şirketimiz firma bizim olur olursa istedi istiyor yapmalıyız".split())
MIN_SCORE, RELATIVE = 4, 0.4  # en iyi eşleşmenin %40'ının altındaki kartlar bağlama alınmaz (ilgisiz kart gürültüsü)


def _norm(text: str) -> str:
    return (text or "").replace("I", "ı").replace("İ", "i").lower()


def _stems(text: str) -> set:
    words = re.findall(r"[a-zçğıöşü0-9]+", _norm(text))
    return {w[:5] for w in words if len(w) >= 3 and w not in STOP}


def clean_cards(cards: Any) -> List[Dict[str, Any]]:
    out, codes = [], set()
    for c in (cards if isinstance(cards, list) else [])[:MAX_CARDS]:
        title, body = str(c.get("title") or "").strip()[:200], str(c.get("body") or "").strip()[:4000]
        if not title or not body:
            continue
        code = re.sub(r"[^a-z0-9-]", "-", _norm(c.get("code") or title))[:60].strip("-") or f"kart-{len(out) + 1}"
        while code in codes:
            code += "-2"
        codes.add(code)
        sources = [{"title": str(s.get("title") or s.get("url"))[:200], "url": str(s["url"])[:500]}
                   for s in c.get("sources") or [] if isinstance(s, dict) and str(s.get("url") or "").startswith("https://")][:5]
        out.append({"code": code, "title": title, "body": body, "legal_basis": str(c.get("legal_basis") or "").strip()[:300],
                    "tags": [str(t).strip()[:40] for t in c.get("tags") or [] if str(t).strip()][:15], "sources": sources})
    return out


async def ensure_packs(db: AsyncSession, path: Path = SEED_FILE) -> int:
    """Tohum dosyasındaki paketlerden eksik olanları TASLAK olarak ekler (yayın uzman kontrolüyle Süper Admin'den)."""
    if not path.exists():
        return 0
    have = set((await db.execute(select(RegulationPack.code))).scalars())
    added = 0
    for p in json.loads(path.read_text(encoding="utf-8")):
        if p["code"] in have:
            continue
        db.add(RegulationPack(code=p["code"], title=p["title"], description=p.get("description"), draft={"cards": clean_cards(p["cards"])}))
        added += 1
    await db.commit()
    return added


def publish(pack: RegulationPack, actor_id, reviewer_name: str, checked_at: date, note: Optional[str]) -> Dict[str, Any]:
    cards = clean_cards((pack.draft or {}).get("cards"))
    if not cards:
        raise HTTPException(status_code=422, detail="Yayımlanacak kart yok.")
    version = ((pack.published or {}).get("version") or 0) + 1
    pack.published = {"version": version, "cards": cards, "published_at": datetime.now(timezone.utc).isoformat(),
                      "reviewer_name": reviewer_name.strip(), "checked_at": checked_at.isoformat(), "review_note": (note or "").strip() or None,
                      "publisher_actor_id": str(actor_id)}
    return pack.published


def changed_since_publish(pack: RegulationPack) -> bool:
    return clean_cards((pack.draft or {}).get("cards")) != ((pack.published or {}).get("cards") or None)


def public_out(pack: RegulationPack, enabled: bool = False, cards: bool = False) -> Dict[str, Any]:
    pub = pack.published or {}
    d = {"id": str(pack.id), "code": pack.code, "title": pack.title, "description": pack.description, "version": pub.get("version"),
         "checked_at": pub.get("checked_at"), "reviewer_name": pub.get("reviewer_name"), "card_count": len(pub.get("cards") or []),
         "enabled": enabled, "disclaimer": DISCLAIMER}
    if cards:
        d["cards"] = pub.get("cards") or []
    return d


async def enabled_packs(db: AsyncSession, tenant_id) -> List[RegulationPack]:
    rows = (await db.execute(select(RegulationPack).join(TenantRegulationPack, TenantRegulationPack.pack_id == RegulationPack.id)
                             .where(TenantRegulationPack.tenant_id == tenant_id, RegulationPack.published.isnot(None)))).scalars().all()
    return list(rows)


def score(query_stems: set, card: Dict[str, Any]) -> float:
    title, tags = _stems(card["title"]), _stems(" ".join(card.get("tags") or []))
    body = _stems(card["body"] + " " + card.get("legal_basis", ""))
    return 3 * len(query_stems & tags) + 2 * len(query_stems & title) + 0.5 * len(query_stems & body)


async def relevant(db: AsyncSession, tenant_id, text: str, limit: int = MAX_CONTEXT_CARDS) -> List[Tuple[RegulationPack, Dict[str, Any]]]:
    stems = _stems(text)
    if not stems:
        return []
    scored = []
    for pack in await enabled_packs(db, tenant_id):
        for card in (pack.published or {}).get("cards") or []:
            s = score(stems, card)
            if s >= MIN_SCORE:
                scored.append((s, pack, card))
    scored.sort(key=lambda x: -x[0])
    best = scored[0][0] if scored else 0
    return [(p, c) for s, p, c in scored[:limit] if s >= best * RELATIVE]


def format_context(items: List[Tuple[RegulationPack, Dict[str, Any]]]) -> str:
    if not items:
        return ""
    out, used = ["\n\n# Mevzuat bilgi paketleri (şirketin açtığı, RECDx uzman kontrolünden geçmiş özetler)"], 0
    for pack, c in items:
        block = (f"\n## {c['title']} — {pack.title} paketi, sürüm {pack.published.get('version')} "
                 f"(kontrol: {pack.published.get('checked_at')})\nDayanak: {c.get('legal_basis') or '-'}\n{c['body']}\n"
                 f"Resmi kaynak: {', '.join(s['url'] for s in c.get('sources') or []) or '-'}")
        if used + len(block) > MAX_CONTEXT_CHARS:
            break
        out.append(block)
        used += len(block)
    out.append("\nBu kartları kullanırsan paket adını, sürümünü ve yasal dayanağı belirt; kesin hukuki/mali görüş verme, "
               f"oran/tutar/süre gibi değişebilen bilgiler için resmi kaynağa yönlendir. Yanıtının sonuna şu uyarıyı ekle: \"{DISCLAIMER}\"")
    return "\n".join(out)


async def context_for(db: AsyncSession, tenant_id, text: str) -> Tuple[str, List[Dict[str, Any]]]:
    """(bağlam metni, kullanılan kartların özeti) — kayıt/canlı akış için."""
    items = await relevant(db, tenant_id, text)
    return format_context(items), [{"pack": p.code, "version": p.published.get("version"), "card": c["code"]} for p, c in items]
