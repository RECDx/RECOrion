"""
RECAi adları (#349; kullanıcı kararı 25.10.2026): müşteriye EVREN model adları yerine RECAi adları gösterilir.

- CHAT adları (unvan ve AI personelde seçilir): RECAi Mergen (genel, varsayılan), RECAi Hızlı, RECAi Derin.
- CAPABILITY adları (pakette yetenek; sistem ihtiyaç olunca kullanır): RECAi Görsel (VISION), RECAi Ses (TRANSCRIPTION),
  RECAi Okur (OCR). Paket başına açılır (features: vision_enabled / transcription_enabled / ocr_enabled); AI personel
  bazında şirket kapatabilir (actors.recai_capabilities).
- Her adın arkasındaki modeli (+ yedeğini) yalnızca RECDx Süper Admin değiştirir; müşteride ad değişmez, seçimler kendiliğinden
  yeni modele geçer. Gerçek model adı yalnızca Süper Admin ekranlarında görünür.
"""
from typing import Any, Dict, Iterable, List, Optional, Set

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import RecaiTier

DEFAULT_TIER = "MERGEN"
TIER_NAMES = {"MERGEN": "RECAi Mergen", "HIZLI": "RECAi Hızlı", "DERIN": "RECAi Derin", "GORSEL": "RECAi Görsel", "SES": "RECAi Ses",
              "OKUR": "RECAi Okur"}
CHAT_TIERS = ("MERGEN", "HIZLI", "DERIN")
CAPABILITY_FEATURE = {"GORSEL": "vision_enabled", "SES": "transcription_enabled", "OKUR": "ocr_enabled"}
PURPOSE_TIER = {"VISION": "GORSEL", "TRANSCRIPTION": "SES", "OCR": "OKUR"}
INFRA_NAME = "RECAi altyapı"  # embedding, sıralama, güvenlik denetimi: müşteriye ayrıca gösterilmez


async def tiers(db: AsyncSession) -> Dict[str, RecaiTier]:
    return {t.code: t for t in (await db.execute(select(RecaiTier).order_by(RecaiTier.sort))).scalars()}


def models_of(t: Optional[RecaiTier]) -> List[str]:
    return [c for c in ((t.model_code, t.fallback_model_code) if t else ()) if c]


# Eski seçimlerin taşındığı ad (0039 geçişiyle aynı): adlardan birinin arkasında olmayan sohbet modelleri için
LEGACY_MODEL_TIER = {"deepseek-v4-flash": "MERGEN", "auto": "HIZLI", "qwen3.8-flash-next": "HIZLI", "gemma-4-31b": "HIZLI",
                     "mimo-v2.6-pro": "DERIN", "deepseek-v4.1-flash": "DERIN", "glm-5.3": "DERIN"}


def tier_for_model(code: Optional[str], all_tiers: Dict[str, RecaiTier]) -> Optional[str]:
    """Modelin RECAi adı: önce asıl modeli olduğu ad, sonra yedeği olduğu ad, sonra eski eşleme."""
    if not code:
        return None
    low = code.lower()
    for t in all_tiers.values():
        if t.model_code.lower() == low:
            return t.code
    for t in all_tiers.values():
        if (t.fallback_model_code or "").lower() == low:
            return t.code
    return LEGACY_MODEL_TIER.get(low)


def public_name(code: Optional[str], all_tiers: Dict[str, RecaiTier], purpose: Optional[str] = None) -> str:
    """Raporlarda müşteriye gösterilecek ad (gerçek model adı yerine)."""
    if purpose in PURPOSE_TIER and PURPOSE_TIER[purpose] in all_tiers:
        return all_tiers[PURPOSE_TIER[purpose]].name
    if purpose in ("EMBEDDING", "RERANK", "GUARD"):
        return INFRA_NAME
    t = tier_for_model(code, all_tiers)
    return all_tiers[t].name if t else "RECAi"


def plan_tiers(plan) -> List[str]:
    """Paketin seçilebilir adları (paket yoksa — RECDx — hepsi)."""
    if plan is None:
        return list(CHAT_TIERS)
    return [c for c in (plan.recai_tiers or []) if c in CHAT_TIERS] or [DEFAULT_TIER]


def plan_capabilities(plan) -> Dict[str, bool]:
    feats = (plan.features or {}) if plan is not None else None
    return {code: (True if feats is None else bool(feats.get(flag))) for code, flag in CAPABILITY_FEATURE.items()}


def allowed_models(plan, all_tiers: Dict[str, RecaiTier]) -> Set[str]:
    """Paketin kullanabileceği modeller: seçilebilir adların asıl ve yedek modelleri."""
    out: Set[str] = set()
    for code in plan_tiers(plan):
        out.update(m.lower() for m in models_of(all_tiers.get(code)))
    return out


def capability_allowed(plan, actor, code: str) -> bool:
    """Yetenek bu pakette ve (varsa) bu AI personelde açık mı."""
    if not plan_capabilities(plan).get(code, False):
        return False
    caps = (getattr(actor, "recai_capabilities", None) or {}) if actor is not None else {}
    return caps.get(code, True) is not False


def out(t: RecaiTier, admin: bool = False) -> Dict[str, Any]:
    d = {"code": t.code, "name": t.name, "kind": t.kind, "description": t.description}
    if admin:
        d.update({"model_code": t.model_code, "fallback_model_code": t.fallback_model_code, "purpose": t.purpose, "updated_at": t.updated_at})
    return d


def choose(code: Optional[str], allowed: Iterable[str]) -> str:
    """Geçerli seçilebilir ad (pakette yoksa paketin ilk adı)."""
    allowed = list(allowed)
    return code if code in allowed else (DEFAULT_TIER if DEFAULT_TIER in allowed else allowed[0])


async def options(db: AsyncSession, plan, bypass: bool = False) -> List[Dict[str, Any]]:
    """Seçilebilir RECAi adları (müşteri ekranları için; gerçek model adı yok). available: paketinde var mı.
    effort_coefficient: arkasındaki modelin kredi katsayısı (kredi tahmini için)."""
    from app.db.models import LLMModel

    all_tiers = await tiers(db)
    in_plan = set(CHAT_TIERS) if bypass else set(plan_tiers(plan))
    out = []
    for code in CHAT_TIERS:
        t = all_tiers.get(code)
        if not t:
            continue
        m = (await db.execute(select(LLMModel).where(LLMModel.model_code == t.model_code))).scalar_one_or_none()
        out.append({"code": code, "model_code": code, "name": t.name, "display_name": t.name, "description": t.description,
                    "model_type": "CHAT", "available": code in in_plan,
                    "effort_coefficient": float(m.effort_coefficient or 1) if m else 1.0})
    return out


async def capability_options(db: AsyncSession, plan, bypass: bool = False) -> List[Dict[str, Any]]:
    all_tiers = await tiers(db)
    caps = {k: True for k in CAPABILITY_FEATURE} if bypass else plan_capabilities(plan)
    return [{"code": c, "name": all_tiers[c].name if c in all_tiers else TIER_NAMES[c],
             "description": all_tiers[c].description if c in all_tiers else None, "in_plan": bool(caps.get(c))} for c in CAPABILITY_FEATURE]
