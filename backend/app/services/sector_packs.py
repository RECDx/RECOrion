"""
İSTEK #751 — Sektör bilgi paketleri.

- Her iş kolu için RECDx (Merkez) yönetimindeki, sürümlenen ve uzman kontrolünden geçen paket: keşif soru bankası, standart
  aşamalar ve teslimat şablonları (kabul + doğrulama yöntemi), tipik roller ve insan/AI iş bölümü, sık atlanan gereksinimler,
  tipik riskler, KPI'lar, ilgili mevzuat/standartlar. Mevzuat paketleriyle aynı yayın kuralı: taslak yalnız Merkez'de,
  şirket ve Beyin AI yalnız uzman beyanıyla yayımlanmış sürümü görür.
- Şirket kendi ek sorularını ve sık atlanan maddelerini tanımlayabilir (tenant.settings['sector_packs']['extras'][kod]);
  bunlar yalnız o şirkette geçerlidir, Merkez göremez (KVKK).
- Proje bir pakete bağlanır (project.settings['sector_pack']); seçilmemişse Beyin AI şirketin sektörü, projenin alan paketi ve
  isterlerdeki anahtar kelimelerle önerir. Paket keşif turuna (soru bankası, sık atlananlar, riskler, standartlar) ve plan
  önerisine (aşamalar, teslimatlar, roller, KPI) girer.
"""
import json
import re
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Project, SectorPack, Tenant

SEED_FILE = Path(__file__).resolve().parent.parent / "seed" / "sector_packs.json"
SPLITS = ("AI", "HUMAN", "AI+HUMAN")
LIMITS = {"questions": 40, "phases": 12, "roles": 15, "missed": 30, "risks": 20, "kpis": 15, "standards": 15}
EXTRA_LIMITS = {"questions": 20, "missed": 20}
MIN_SCORE = 2  # öneri eşiği: en az iki anahtar kelime ya da sektör eşleşmesi + bir anahtar kelime


def _s(v: Any, n: int) -> str:
    return str(v or "").strip()[:n]


def _norm(text: str) -> str:
    return (text or "").replace("I", "ı").replace("İ", "i").lower()


def _question(q: Any) -> Optional[Dict[str, str]]:
    if not isinstance(q, dict) or not _s(q.get("text"), 600):
        return None
    return {"topic": _s(q.get("topic"), 60) or "Soru", "text": _s(q.get("text"), 600), "why": _s(q.get("why"), 300)}


def _lines(items: Any, n: int, size: int = 300) -> List[str]:
    return [_s(x, size) for x in (items if isinstance(items, list) else []) if _s(x, size)][:n]


def clean_content(c: Any) -> Dict[str, Any]:
    c = c if isinstance(c, dict) else {}
    phases = []
    for p in (c.get("phases") if isinstance(c.get("phases"), list) else [])[:LIMITS["phases"]]:
        if not isinstance(p, dict) or not _s(p.get("name"), 120):
            continue
        split = _s(p.get("split"), 10).upper()
        dels = [{"name": _s(d.get("name"), 200), "acceptance": _s(d.get("acceptance"), 400), "verification": _s(d.get("verification"), 400)}
                for d in (p.get("deliverables") or []) if isinstance(d, dict) and _s(d.get("name"), 200)][:8]
        phases.append({"name": _s(p.get("name"), 120), "split": split if split in SPLITS else "AI+HUMAN", "deliverables": dels})
    roles = []
    for r in (c.get("roles") if isinstance(c.get("roles"), list) else [])[:LIMITS["roles"]]:
        if isinstance(r, dict) and _s(r.get("role"), 120):
            side = _s(r.get("side"), 10).upper()
            roles.append({"role": _s(r.get("role"), 120), "side": side if side in ("AI", "HUMAN") else "HUMAN", "note": _s(r.get("note"), 300)})
    standards = [{"title": _s(s.get("title"), 160), "note": _s(s.get("note"), 300)}
                 for s in (c.get("standards") if isinstance(c.get("standards"), list) else []) if isinstance(s, dict) and _s(s.get("title"), 160)]
    return {"questions": [q for q in map(_question, c.get("questions") if isinstance(c.get("questions"), list) else []) if q][:LIMITS["questions"]],
            "phases": phases, "roles": roles,
            "missed": _lines(c.get("missed"), LIMITS["missed"]), "risks": _lines(c.get("risks"), LIMITS["risks"]),
            "kpis": _lines(c.get("kpis"), LIMITS["kpis"], 200), "standards": standards[:LIMITS["standards"]]}


def clean_meta(sector_codes: Any, keywords: Any) -> Tuple[List[str], List[str]]:
    codes = sorted({_s(c, 4).upper() for c in (sector_codes or []) if re.fullmatch(r"[A-Za-z]{1,4}", _s(c, 4))})
    words = []
    for k in keywords or []:
        k = _norm(_s(k, 40))
        if k and k not in words:
            words.append(k)
    return codes, words[:40]


def clean_extras(e: Any) -> Dict[str, Any]:
    e = e if isinstance(e, dict) else {}
    return {"questions": [q for q in map(_question, e.get("questions") if isinstance(e.get("questions"), list) else []) if q][:EXTRA_LIMITS["questions"]],
            "missed": _lines(e.get("missed"), EXTRA_LIMITS["missed"])}


async def ensure_packs(db: AsyncSession, path: Path = SEED_FILE) -> int:
    """Tohum dosyasındaki eksik paketleri TASLAK olarak ekler; yayın Merkez'de uzman kontrolüyle yapılır."""
    if not path.exists():
        return 0
    have = set((await db.execute(select(SectorPack.code))).scalars())
    added = 0
    for p in json.loads(path.read_text(encoding="utf-8")):
        if p["code"] in have:
            continue
        codes, words = clean_meta(p.get("sector_codes"), p.get("keywords"))
        db.add(SectorPack(code=p["code"], title=p["title"], description=p.get("description"), sector_codes=codes, keywords=words,
                          draft={"content": clean_content(p.get("content"))}))
        added += 1
    await db.commit()
    return added


def publish(pack: SectorPack, actor_id, reviewer_name: str, checked_at: date, note: Optional[str]) -> Dict[str, Any]:
    content = clean_content((pack.draft or {}).get("content"))
    if not content["questions"] and not content["phases"]:
        raise HTTPException(status_code=422, detail="Yayımlanacak içerik yok: en az bir keşif sorusu ya da aşama gerekli.")
    prev = pack.published or {}
    version = (prev.get("version") or 0) + 1
    history = list(prev.get("history") or [])
    if prev.get("version"):
        history.append({k: prev.get(k) for k in ("version", "published_at", "reviewer_name", "checked_at")})
    pack.published = {"version": version, "content": content, "published_at": datetime.now(timezone.utc).isoformat(),
                      "reviewer_name": reviewer_name.strip(), "checked_at": checked_at.isoformat(),
                      "review_note": (note or "").strip() or None, "publisher_actor_id": str(actor_id), "history": history[-20:],
                      "withdrawn": False}
    return pack.published


def changed_since_publish(pack: SectorPack) -> bool:
    return clean_content((pack.draft or {}).get("content")) != ((pack.published or {}).get("content") or None)


def live(pack: Optional[SectorPack]) -> bool:
    pub = (pack.published or {}) if pack else {}
    return bool(pub.get("version")) and not pub.get("withdrawn")


async def published_packs(db: AsyncSession) -> List[SectorPack]:
    rows = (await db.execute(select(SectorPack).where(SectorPack.published.isnot(None)).order_by(SectorPack.title))).scalars().all()
    return [p for p in rows if live(p)]


def extras_of(tenant: Tenant, code: str) -> Dict[str, Any]:
    return clean_extras((((tenant.settings or {}).get("sector_packs") or {}).get("extras") or {}).get(code))


def save_extras(tenant: Tenant, code: str, extras: Dict[str, Any]) -> Dict[str, Any]:
    sp = dict((tenant.settings or {}).get("sector_packs") or {})
    ex = dict(sp.get("extras") or {})
    clean = clean_extras(extras)
    if clean["questions"] or clean["missed"]:
        ex[code] = clean
    else:
        ex.pop(code, None)
    tenant.settings = {**(tenant.settings or {}), "sector_packs": {**sp, "extras": ex}}
    return clean


def public_out(pack: SectorPack, tenant: Optional[Tenant] = None, content: bool = False) -> Dict[str, Any]:
    pub = pack.published or {}
    c = pub.get("content") or {}
    d = {"id": str(pack.id), "code": pack.code, "title": pack.title, "description": pack.description, "sector_codes": pack.sector_codes or [],
         "version": pub.get("version"), "checked_at": pub.get("checked_at"), "reviewer_name": pub.get("reviewer_name"),
         "counts": {k: len(c.get(k) or []) for k in LIMITS}}
    if content:
        d["content"] = c
    if tenant is not None:
        d["extras"] = extras_of(tenant, pack.code)
    return d


# ---------------------------------------------------------------- proje bağlantısı
def score(pack: SectorPack, tenant: Tenant, project: Project) -> int:
    # şirket sektörü tek başına yetmez (ör. elektronik şirketinin üretim projesi yazılım değildir): +1, iş metni belirleyicidir
    s = min(1, len(set(pack.sector_codes or []) & {str(x).upper() for x in (tenant.sectors or [])}))
    text = _norm(" ".join([project.name or "", project.description or "", project.requirements or ""]))
    # kısa kelimeler (mes, api, erp…) tam kelime olmalı ("mesaj" MES değildir); uzunlarda Türkçe ek serbest ("uygulaması")
    s += sum(1 for k in pack.keywords or []
             if re.search(rf"(?<![a-zçğıöşü0-9]){re.escape(k)}{'(?![a-zçğıöşü0-9])' if len(k) <= 4 else ''}", text))
    if pack.code == "yazilim" and (project.field_package or "").upper() == "YAZILIM":
        s += 3
    return s


async def suggest(db: AsyncSession, tenant: Tenant, project: Project) -> Optional[SectorPack]:
    best, best_s = None, 0
    for p in await published_packs(db):
        s = score(p, tenant, project)
        if s > best_s:
            best, best_s = p, s
    return best if best_s >= MIN_SCORE else None


async def for_project(db: AsyncSession, project: Project, tenant: Optional[Tenant] = None) -> Tuple[Optional[SectorPack], bool]:
    """(paket, otomatik mi). Yönetici "paket yok" seçtiyse (code None, auto False) paket kullanılmaz."""
    sel = (project.settings or {}).get("sector_pack")
    if isinstance(sel, dict) and not sel.get("auto"):
        if not sel.get("code"):
            return None, False
        p = (await db.execute(select(SectorPack).where(SectorPack.code == sel["code"]))).scalar_one_or_none()
        return (p if live(p) else None), False
    tenant = tenant or await db.get(Tenant, project.tenant_id)
    return await suggest(db, tenant, project), True


def select_for_project(project: Project, code: Optional[str]) -> None:
    project.settings = {**(project.settings or {}), "sector_pack": {"code": code, "auto": False}}


def _header(pack: SectorPack) -> str:
    pub = pack.published or {}
    return f"{pack.title} (sürüm {pub.get('version')}, uzman kontrolü {pub.get('checked_at')})"


def discovery_context(pack: Optional[SectorPack], tenant: Tenant, asked: List[str]) -> str:
    """Keşif istemi için: soru bankası (daha önce sorulmamış olanlar), sık atlananlar, riskler, standartlar + şirket ekleri."""
    if not pack:
        return ""
    c, ex = (pack.published or {}).get("content") or {}, extras_of(tenant, pack.code)
    seen = {_norm(a)[:80] for a in asked}
    bank = [q for q in ex["questions"] + (c.get("questions") or []) if _norm(q["text"])[:80] not in seen][:15]
    out = [f"# Sektör bilgi paketi: {_header(pack)}"]
    if bank:
        out.append("Soru bankası (şirketin kendi soruları önce; projeye uyanları kendi cümlelerinle sor, uymayanı atla):")
        out += [f"- [{q['topic']}] {q['text']}" + (f" (neden: {q['why']})" if q.get("why") else "") for q in bank]
    missed = ex["missed"] + (c.get("missed") or [])
    if missed:
        out.append("Bu iş kolunda sık atlanan gereksinimler (hatırlatmalarda ve eksiklerde kullan):")
        out += [f"- {m}" for m in missed[:20]]
    if c.get("risks"):
        out.append("Tipik riskler: " + "; ".join(c["risks"][:10]))
    if c.get("standards"):
        out.append("İlgili mevzuat ve standartlar: " + "; ".join(f"{s['title']} ({s['note']})" if s.get("note") else s["title"]
                                                               for s in c["standards"][:10]))
    return "\n".join(out)


def plan_context(pack: Optional[SectorPack]) -> str:
    """Plan istemi için: standart aşamalar, teslimat şablonları (kabul + doğrulama), roller ve iş bölümü, KPI'lar."""
    if not pack:
        return ""
    c = (pack.published or {}).get("content") or {}
    out = [f"# Sektör bilgi paketi: {_header(pack)}",
           "Standart aşamalar ve teslimat şablonları (tanım belgesiyle çelişirse tanım belgesi geçerlidir; projeye uymayanı alma):"]
    split_label = {"AI": "AI personel", "HUMAN": "insan", "AI+HUMAN": "AI hazırlar, insan onaylar/uygular"}
    for p in c.get("phases") or []:
        out.append(f"- {p['name']} [{split_label.get(p['split'], p['split'])}]")
        out += [f"    · {d['name']} — kabul: {d['acceptance'] or '-'}; doğrulama: {d['verification'] or '-'}" for d in p.get("deliverables") or []]
    if c.get("roles"):
        out.append("Tipik roller ve iş bölümü: " + "; ".join(f"{r['role']} ({'insan' if r['side'] == 'HUMAN' else 'AI'})"
                                                            + (f": {r['note']}" if r.get("note") else "") for r in c["roles"]))
    if c.get("kpis"):
        out.append("İzlenecek KPI'lar: " + "; ".join(c["kpis"]))
    if c.get("missed"):
        out.append("Sık atlananlar (planda bir adımın kapsamına ya da kabul ölçütüne girmeli): " + "; ".join(c["missed"][:15]))
    return "\n".join(out)


def project_out(pack: Optional[SectorPack], auto: bool) -> Dict[str, Any]:
    if not pack:
        return {"code": None, "auto": auto}
    pub = pack.published or {}
    return {"code": pack.code, "title": pack.title, "version": pub.get("version"), "auto": auto}
