"""
İSTEK #743 — RECAi eğitim veri hattı (yerli ve milli RECAi LLM'i için; EVREN'de eğitilir).

Karar kaydı ve gerekçeler: Claude/senaryo/karar_ogrenme_recai.md §4–5 (11.11.2026). Özet:
- Kaynak #742 öğrenme kayıtlarıdır (tek kayıt, iki tüketici: hafıza + veri seti).
- Yalnız "RECAi model geliştirmeye katkı" izni AÇIK şirketlerin kayıtları girer (varsayılan açık; şirket kapatabilir; kapatınca
  SONRAKİ setlere girmez).
- Maskeleme: TCKN, VKN, IBAN, kart, e-posta, telefon, ad-soyad, firma adı, adres, plaka, tutar → TUTARLI SAHTE değerler
  (aynı değer kayıt boyunca aynı sahte karşılığı alır; yapı ve ilişkiler korunur). Sahte değerler her kayıtta rastgele seçilir ve
  EŞLEME TABLOSU TUTULMAZ (geri çevrilemez → anonim; geri çevrilebilir maskeleme KVKK'da hâlâ kişisel veridir).
- Şirket/kişi kimlikleri (tenant_id, actor_id, proje adı) sete girmez; yalnız sektör ve ünvan (genel bilgi) kalır.
- Dosyalar (sohbet biçimi JSONL):
    sft.jsonl     DOGRU çıktı → örnek gösterme (yalnız doğru hedef olur)
    dpo.jsonl     YANLIS(MODEL_HATASI) + gerekçe + eşlenen DOGRU → tercih çifti
    kto.jsonl     tek başına iyi/kötü işaretli örnek (eşi olmayan MODEL_HATASI yanlışlar dahil)
    reward.jsonl  test koşusu (doğrulanabilir ödül; yazılıma özgü)
    lessons.jsonl genel dersler
  Yalnız MODEL_HATASI olumsuz örnek olur; ORTAM/DEGERLENDIRICI/KAPSAM/BELIRSIZ hiçbir olumsuz dosyaya girmez.
- İçerik MinIO'da (recai-datasets/v{n}/); Merkez yalnız sayıları görür (KVKK). EVREN'e teslim API'si EVREN görüşmesinden sonra.
"""
import json
import random
import re
import secrets
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Actor, LearningRecord, Tenant, TrainingDataset
from app.services.documents import pii

FAKE_FIRST = ["Ayşe", "Mehmet", "Zeynep", "Ali", "Elif", "Mustafa", "Fatma", "Emre", "Selin", "Burak", "Deniz", "Can", "Ece", "Murat",
              "Gizem", "Hakan", "Derya", "Kerem", "Sevgi", "Onur", "Nazlı", "Tolga", "Pınar", "Serkan"]
FAKE_LAST = ["Yılmaz", "Kaya", "Demir", "Şahin", "Çelik", "Yıldız", "Aydın", "Öztürk", "Arslan", "Doğan", "Kılıç", "Koç", "Kurt",
             "Özdemir", "Aslan", "Polat", "Erdem", "Güneş", "Aksoy", "Tekin"]
FAKE_FIRM = ["Anadolu", "Ege", "Marmara", "Toros", "Kuzey", "Güney", "Yeşil", "Mavi", "Atlas", "Doruk", "Pusula", "Çınar"]
FAKE_FIRM_KIND = ["Ticaret Ltd. Şti.", "Sanayi A.Ş.", "Hizmet Ltd. Şti.", "Danışmanlık A.Ş."]
FAKE_STREET = ["Çiçek", "Gül", "Lale", "Papatya", "Menekşe", "Zambak", "Akasya", "Ihlamur"]
CITY_PLATES = ["06", "16", "34", "35", "41", "07", "01", "42"]

_FIRM = re.compile(r"\b(?:[A-ZÇĞİÖŞÜ][\wÇĞİÖŞÜçğıöşü&'.-]*\s+){1,5}(?:A\.?\s?Ş\.?|Ltd\.?\s?Şti\.?|LTD\.?\s?ŞTİ\.?|Limited Şirketi|Anonim Şirketi)",
                   re.UNICODE)
_HONORIFIC = re.compile(r"\b(Sayın|Bay|Bayan|Sn\.|Dr\.|Av\.|Prof\.|Doç\.|Uzm\.|Dt\.)\s+([A-ZÇĞİÖŞÜ][a-zçğıöşü]+(?:\s+[A-ZÇĞİÖŞÜ][a-zçğıöşü]+){0,2})",
                        re.UNICODE)
_VKN = re.compile(r"(?i)(vergi\s*(?:no|numarası|kimlik\s*no)\s*[:=]?\s*)(\d{10})\b")
_PLATE = re.compile(r"\b(0[1-9]|[1-7]\d|8[01])\s?([A-Z]{1,3})\s?(\d{2,4})\b")
_ADDRESS = re.compile(r"[A-ZÇĞİÖŞÜ][\wçğıöşü.]*\s+(?:Mah\.|Mahallesi)(?:[^\n,;]{0,80}?(?:Cad\.|Caddesi|Sok\.|Sokak|Bulvarı|Blv\.))?"
                      r"(?:[^\n,;]{0,40}?No\s*[:.]?\s*\d+[\w/]*)?", re.UNICODE)
_AMOUNT = re.compile(r"(?<![\w.,])(\d{1,3}(?:[.\s]\d{3})+|\d{4,})(?:,(\d{2}))?\s?(TL|₺|TRY|EUR|€|USD|\$)", re.UNICODE)
PII_KEYS = re.compile(r"name|ad[ıi]?$|unvan|ünvan|partner|customer|müşteri|musteri|contact|email|e_posta|phone|telefon|mobile|street|"
                      r"address|adres|city|vat|tax|tckn|iban|plate|plaka", re.I)


def _fake_tckn(rng: random.Random) -> str:
    d = [rng.randint(1, 9)] + [rng.randint(0, 9) for _ in range(8)]
    d.append((sum(d[0:9:2]) * 7 - sum(d[1:8:2])) % 10)
    d.append(sum(d[:10]) % 10)
    return "".join(map(str, d))


class Masker:
    """Bir kayıt için tutarlı sahte değerler (aynı değer → aynı sahte karşılık). Eşleme kaydın işi bitince atılır."""

    def __init__(self, known: Optional[Dict[str, str]] = None):
        self.rng = random.Random(secrets.randbits(64))
        self.known = {k.strip(): v for k, v in (known or {}).items() if k and len(k.strip()) >= 3}
        self.map: Dict[tuple, str] = {}
        self.counts: Dict[str, int] = {}

    def _fake(self, kind: str, value: str) -> str:
        key = (kind, value.strip().casefold())
        if key in self.map:
            return self.map[key]
        r = self.rng
        n = sum(1 for k in self.map if k[0] == kind) + 1
        fake = {
            "KISI": lambda: f"{r.choice(FAKE_FIRST)} {r.choice(FAKE_LAST)}",
            "FIRMA": lambda: f"{r.choice(FAKE_FIRM)} {r.choice(FAKE_FIRM_KIND)}",
            "TCKN": lambda: _fake_tckn(r),
            "VKN": lambda: "".join(str(r.randint(0, 9)) for _ in range(10)),
            "IBAN": lambda: "TR" + "".join(str(r.randint(0, 9)) for _ in range(24)),
            "KART": lambda: "4000 " + " ".join("".join(str(r.randint(0, 9)) for _ in range(4)) for _ in range(3)),
            "EPOSTA": lambda: f"kisi{n}@ornek.com.tr",
            "TELEFON": lambda: f"0555 {r.randint(100, 999)} {r.randint(10, 99)} {r.randint(10, 99)}",
            "PLAKA": lambda: f"{r.choice(CITY_PLATES)} {''.join(r.choice('ABCDEFGHJKLMNPRSTUVYZ') for _ in range(2))} {r.randint(100, 9999)}",
            "ADRES": lambda: f"{r.choice(FAKE_STREET)} Mah. {r.choice(FAKE_STREET)} Sok. No:{r.randint(1, 120)}",
        }[kind]()
        self.map[key] = fake
        self.counts[kind] = self.counts.get(kind, 0) + 1
        return fake

    def _amount(self, m: re.Match) -> str:
        digits = re.sub(r"\D", "", m.group(1))
        val = int(digits) * self.rng.uniform(0.7, 1.3)  # büyüklük korunur, gerçek tutar gizlenir
        whole = f"{int(round(val)):,}".replace(",", ".")
        self.counts["TUTAR"] = self.counts.get("TUTAR", 0) + 1
        return f"{whole}{',' + m.group(2) if m.group(2) else ''} {m.group(3)}"

    def text(self, s: Optional[str]) -> Optional[str]:
        if not s:
            return s
        held: List[str] = []  # sahte değerler işlem bitene kadar korunur (sonraki desenler onları yeniden maskelemesin)

        def hold(kind: str, value: str) -> str:
            held.append(self._fake(kind, value))
            return f"{len(held) - 1}"

        for value, kind in sorted(self.known.items(), key=lambda kv: -len(kv[0])):  # bilinen adlar (uzun önce)
            s = re.sub(r"(?<!\w)" + re.escape(value) + r"(?!\w)", lambda m, k=kind: hold(k, m.group(0)), s, flags=re.I)
        s = pii._IBAN.sub(lambda m: hold("IBAN", re.sub(r"\s", "", m.group(0))), s)
        s = pii._CARD.sub(lambda m: hold("KART", m.group(0)) if pii.luhn_ok(m.group(0)) else m.group(0), s)
        s = pii._EMAIL.sub(lambda m: hold("EPOSTA", m.group(0)), s)
        s = pii._TCKN.sub(lambda m: hold("TCKN", m.group(0)) if pii.tckn_ok(m.group(0)) else m.group(0), s)
        s = _VKN.sub(lambda m: m.group(1) + hold("VKN", m.group(2)), s)
        s = pii._PHONE.sub(lambda m: hold("TELEFON", re.sub(r"\D", "", m.group(0))[-10:]), s)
        s = _FIRM.sub(lambda m: hold("FIRMA", m.group(0)), s)
        s = _HONORIFIC.sub(lambda m: f"{m.group(1)} {hold('KISI', m.group(2))}", s)
        s = _ADDRESS.sub(lambda m: hold("ADRES", m.group(0)), s)
        s = _PLATE.sub(lambda m: hold("PLAKA", m.group(0)), s)
        s = _AMOUNT.sub(self._amount, s)
        return re.sub("(\\d+)", lambda m: held[int(m.group(1))], s)

    def obj(self, v: Any, key: str = "") -> Any:
        """Aktarım nesnesi gibi JSON: kişi/iletişim anahtarlarının değerleri bütünüyle maskelenir, diğer metinler taranır."""
        if isinstance(v, dict):
            return {k: self.obj(x, k) for k, x in v.items()}
        if isinstance(v, list):
            return [self.obj(x, key) for x in v]
        if isinstance(v, str):
            if PII_KEYS.search(key or ""):
                kind = ("EPOSTA" if "mail" in key.lower() else "TELEFON" if re.search(r"phone|telefon|mobile", key, re.I)
                        else "ADRES" if re.search(r"street|address|adres|city", key, re.I) else "FIRMA" if re.search(r"partner|customer|müşteri|musteri|unvan|ünvan", key, re.I)
                        else "KISI")
                return self._fake(kind, v) if v.strip() else v
            return self.text(v)
        return v


# ---------------------------------------------------------------- veri seti
def _system(rec: LearningRecord) -> str:
    who = rec.job_title or "uzman"
    return (f"Sen RECOrion platformunda çalışan bir AI personelsin (ünvan: {who}"
            + (f"; sektör: {rec.sector}" if rec.sector else "") + "). İşi kabul ölçütüne göre eksiksiz ve doğru teslim et.")


async def _known_names(db: AsyncSession, tenant: Tenant) -> Dict[str, str]:
    known = {tenant.name: "FIRMA"}
    for fld, kind in (("contact_email", "EPOSTA"), ("phone", "TELEFON"), ("address", "ADRES")):
        if getattr(tenant, fld, None):
            known[getattr(tenant, fld)] = kind
    for name, typ in (await db.execute(select(Actor.display_name, Actor.actor_type).where(Actor.tenant_id == tenant.id))).all():
        if name and typ == "HUMAN":
            known[name] = "KISI"
            for part in name.split():  # yalnız soyad/ad geçen yerler de
                if len(part) >= 4:
                    known.setdefault(part, "KISI")
    return known


def _jl(rows: Iterable[Dict[str, Any]]) -> bytes:
    return ("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n").encode("utf-8")


async def eligible_counts(db: AsyncSession) -> Dict[str, Any]:
    """Merkez için yalnız toplam sayılar (KVKK: içerik yok)."""
    consent = select(Tenant.id).where(Tenant.recai_training_consent.is_(True))
    base = select(func.count()).select_from(LearningRecord).where(LearningRecord.tenant_id.in_(consent))
    total = (await db.execute(base)).scalar() or 0
    good = (await db.execute(base.where(LearningRecord.label == "DOGRU", LearningRecord.output.isnot(None)))).scalar() or 0
    neg = (await db.execute(base.where(LearningRecord.label == "YANLIS", LearningRecord.cause == "MODEL_HATASI"))).scalar() or 0
    pairs = (await db.execute(base.where(LearningRecord.label == "YANLIS", LearningRecord.cause == "MODEL_HATASI",
                                         LearningRecord.pair_id.isnot(None)))).scalar() or 0
    tests = (await db.execute(base.where(LearningRecord.source == "TEST_RUN"))).scalar() or 0
    tenants_on = (await db.execute(select(func.count()).select_from(Tenant).where(Tenant.recai_training_consent.is_(True),
                                                                                  Tenant.is_active.is_(True)))).scalar() or 0
    tenants_off = (await db.execute(select(func.count()).select_from(Tenant).where(Tenant.recai_training_consent.is_(False)))).scalar() or 0
    return {"records": total, "sft": good, "negatives": neg, "pairs": pairs, "tests": tests,
            "tenants_consenting": tenants_on, "tenants_declined": tenants_off}


async def build(db: AsyncSession, actor_id=None, note: Optional[str] = None) -> TrainingDataset:
    """İzinli şirketlerin kayıtlarından maskeli, sürümlü veri seti üretir ve depoya yazar."""
    from app.services import storage

    tenants = (await db.execute(select(Tenant).where(Tenant.recai_training_consent.is_(True)))).scalars().all()
    files: Dict[str, List[Dict[str, Any]]] = {"sft": [], "dpo": [], "kto": [], "reward": [], "lessons": []}
    masked_counts: Dict[str, int] = {}
    used_tenants = 0
    for t in tenants:
        recs = (await db.execute(select(LearningRecord).where(LearningRecord.tenant_id == t.id)
                                 .order_by(LearningRecord.created_at))).scalars().all()
        if not recs:
            continue
        used_tenants += 1
        known = await _known_names(db, t)
        by_id = {r.id: r for r in recs}
        for r in recs:
            m = Masker(known)
            mt = m.text
            prompt = [{"role": "system", "content": _system(r)}, {"role": "user", "content": mt(r.task_input) or ""}]
            out = (json.dumps(m.obj(json.loads(r.output)), ensure_ascii=False) if r.source == "TRANSFER" and r.output and r.output.startswith("{")
                   else mt(r.output))
            meta = {"source": r.source, "sector": r.sector, "job_title": r.job_title}
            if r.label == "DOGRU" and out and r.task_input:
                files["sft"].append({"messages": prompt + [{"role": "assistant", "content": out}], "meta": meta})
                files["kto"].append({"prompt": prompt, "completion": out, "label": True, "meta": meta})
            elif r.label == "YANLIS" and r.cause == "MODEL_HATASI" and out and r.task_input:
                good = by_id.get(r.pair_id) if r.pair_id else None
                if good is not None and good.output:
                    files["dpo"].append({"prompt": prompt, "chosen": mt(good.output), "rejected": out,
                                         "feedback": mt(r.feedback), "meta": meta})
                files["kto"].append({"prompt": prompt, "completion": out, "label": False, "feedback": mt(r.feedback), "meta": meta})
            if r.source == "TEST_RUN" and r.label in ("DOGRU", "YANLIS") and (r.label == "DOGRU" or r.cause == "MODEL_HATASI"):
                files["reward"].append({"prompt": prompt, "report": mt(r.feedback), "reward": 1 if r.label == "DOGRU" else -1, "meta": meta})
            if r.lesson and r.lesson_status == "SAVED":
                files["lessons"].append({"lesson": mt(r.lesson), "scope": r.lesson_scope, "meta": meta})
            for k, v in m.counts.items():
                masked_counts[k] = masked_counts.get(k, 0) + v
    version = int((await db.execute(select(func.max(TrainingDataset.version)))).scalar() or 0) + 1
    prefix = f"recai-datasets/v{version}"
    for name, rows in files.items():
        await storage.put_object(f"{prefix}/{name}.jsonl", _jl(rows), "application/x-ndjson")
    counts = {k: len(v) for k, v in files.items()}
    manifest = {"version": version, "created_at": datetime.now(timezone.utc).isoformat(), "counts": counts, "tenant_count": used_tenants,
                "masked": masked_counts, "format": "chat-jsonl", "note": note,
                "rules": "Yalnız izinli şirketler; maskeli (eşleme tablosu yok); olumsuz örnek yalnız MODEL_HATASI."}
    await storage.put_object(f"{prefix}/manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2).encode("utf-8"), "application/json")
    ds = TrainingDataset(version=version, counts={**counts, "masked": masked_counts}, tenant_count=used_tenants, storage_prefix=prefix,
                         note=note, created_by_actor_id=actor_id)
    db.add(ds)
    await db.commit()
    return ds


def out(ds: TrainingDataset) -> Dict[str, Any]:
    return {"id": str(ds.id), "version": ds.version, "status": ds.status, "counts": ds.counts or {}, "tenant_count": ds.tenant_count,
            "storage_prefix": ds.storage_prefix, "delivered_at": ds.delivered_at, "note": ds.note, "created_at": ds.created_at}
