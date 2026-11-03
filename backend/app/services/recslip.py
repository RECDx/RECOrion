"""
RECSlip.App v2 aylık masraf süreci (ADIM 14; kullanıcı kararları 02-03.11.2026). Yalnızca v2 (Odoo 20, recslip 20.0.2.34+);
v1 (rec_fld_* / x_studio_*) desteklenmez.

Akış: fiş v2'de okunur ve onaya gönderilir; zinciri v2 kurar (onay kuralı varsa kurala göre, yoksa yönetici → muhasebe).
RECOrion bekleyen onay adımlarını izler; adımın onaylayıcısı RECOrion'da kişisel anahtarını tanımladıysa (Bağlantılarım) o
kişinin AI personeli fişi kriterlere göre değerlendirir:
- Yönetici/ek onaylayıcı: tutar, risk, mükerrer, hafta sonu, kategori, çalışanın aylık toplamı.
- Muhasebeci: kalemin hesabı onaylı kaynaktan (kural, tedarikçi hafızası, tam eşleşme, onaylı hafıza) geldiyse güvenli; değilse
  RECAi:Mergen ikinci görüşü (şirketin v2'deki etkin promptu, aynı aday hesaplar ve onaylı örnekler; model llm_gateway ile,
  yedek modelli). Farklı hesap, güven eşiğin üstündeyse düzeltme olur; değilse insana düşer. Fiş: bakiye, KKEG, belge türü,
  güven, risk, tutar.
Kriterlere uyan fiş kişinin kendi anahtarıyla AI onayı olarak onaylanır (v2'de "RECAi" bayrağı, gerekçe, iz notu); uymayan,
AI önerisi ve gerekçesiyle kişinin Onaylarım ekranına düşer. İnsan kararı AI önerisiyle karşılaştırılır (uyum oranı).
"Tümünü AI onaylasın" açıksa eşikler aranmaz (ikinci görüş düzeltmeleri yine yapılır).

Her ay bir Case açılır ("RECSlip masraf süreci AAAA-AA"); ayarlar ve kriterler Case'te durur (projects.settings) ve sonraki
aya kopyalanır. Case adımları: S1 fiş takibi, S2 yönetici onayları, S3 muhasebe onayları, S4 ay sonu kesim, S5 aktarım dosyası,
S6 muhasebe programına işleme (RECRobo şimdilik elle), S7 kapanış raporu (Muhasebe AI personeli). S1-S6 muhasebeciye atanır ve
koşulu oluşunca servis teslim eder; S7'yi AI personel yazar, muhasebe müdürü onaylar.
"""
import calendar
import copy
import json
import logging
import re
import uuid
from datetime import date, datetime, time, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Actor, IntegrationConnection, PersonalCredential, Project, RecslipDecision, Task
from app.integrations.base import Context, ToolError
from app.services import personal_credentials as pcs

logger = logging.getLogger("recorion.recslip")
TZ = ZoneInfo("Europe/Istanbul")
APP = "recslip"
MIN_VERSION = (20, 0, 2, 34)
SAFE_SOURCES_ALL = ("rule", "vendor", "exact", "memory", "manual")
STEP_ROLES = {"manager": "Yönetici", "extra": "Ek onaylayıcı", "accountant": "Muhasebe"}

# Varsayılanlar (kullanıcı onaylı öneriler, 03.11.2026); Case ayarlarında değiştirilir
DEFAULT_SETTINGS: Dict[str, Any] = {
    "poll_minutes": 15,
    "submit_reminder_days": 2,
    "human_reminder_days": 1,
    "cutoff": {"day": -1, "time": "18:00"},          # ayın son günü
    "late_tolerance_day": 3,                         # sonraki ayın 3'ü 23:59'a kadar önceki ayın fişleri beklenir
    "export": {"day": 5, "time": "10:00"},           # sonraki ayın 5'i
    "retry": {"count": 3, "interval_hours": 24},
    "posted_reminder_days": 2,
    "criteria": {
        "manager": {"approve_all": False, "max_amount": 2500, "risk_levels": ["none"], "duplicate_to_human": True,
                    "weekend_to_human": True, "categories": [], "monthly_employee_limit": 15000},
        "accountant": {"approve_all": False, "max_amount": 5000, "risk_levels": ["none", "low"], "min_confidence": 85,
                       "safe_sources": ["rule", "vendor", "exact", "memory"], "second_opinion": True,
                       "correct_min_confidence": 90, "kkeg_to_human": True,
                       "blocked_doc_types": ["belge_degil", "yurtdisi_belge"]},
    },
}

EXPENSE_FIELDS = ["id", "name", "date", "total_amount_currency", "currency_id", "employee_id", "product_id", "vendor_id",
                  "rs_state", "rs_doc_type", "rs_receipt_no", "rs_vendor_vat", "rs_confidence", "rs_confidence_level",
                  "rs_risk_level", "rs_risk_notes", "rs_reading_notes", "rs_is_duplicate", "rs_balance_ok",
                  "rs_lines_match_total", "rs_skip_export", "rs_approval_role", "rs_quick_approval", "rs_ai_approved"]
LINE_FIELDS = ["id", "expense_id", "name", "amount_total", "vat_rate", "account_id", "match_source", "confidence",
               "needs_review", "not_expense", "ai_reason"]
STEP_FIELDS = ["id", "expense_id", "role", "user_ids", "state", "pending_since"]


class RecslipError(Exception):
    pass


def now() -> datetime:
    return datetime.now(timezone.utc)


# ---------------------------------------------------------------- ayarlar ve takvim
def _merge(base: Dict[str, Any], over: Dict[str, Any]) -> Dict[str, Any]:
    out = copy.deepcopy(base)
    for k, v in (over or {}).items():
        out[k] = _merge(out[k], v) if isinstance(v, dict) and isinstance(out.get(k), dict) else v
    return out


def settings_of(project: Optional[Project]) -> Dict[str, Any]:
    raw = (project.settings or {}) if project else {}
    return _merge(DEFAULT_SETTINGS, {k: v for k, v in raw.items() if k in DEFAULT_SETTINGS})


def validate_settings(s: Dict[str, Any]) -> Dict[str, Any]:
    """Ekrandan gelen ayarları sınırlar içine alır (bilinmeyen anahtar atılır)."""
    m = _merge(DEFAULT_SETTINGS, {k: v for k, v in (s or {}).items() if k in DEFAULT_SETTINGS})

    def num(v, lo, hi, default):
        try:
            return max(lo, min(hi, type(default)(v)))
        except (TypeError, ValueError):
            return default
    m["poll_minutes"] = num(m["poll_minutes"], 5, 1440, 15)
    for k, d in (("submit_reminder_days", 2), ("human_reminder_days", 1), ("posted_reminder_days", 2)):
        m[k] = num(m[k], 0, 60, d)
    m["late_tolerance_day"] = num(m["late_tolerance_day"], 0, 27, 3)
    m["cutoff"]["day"] = num(m["cutoff"]["day"], -1, 28, -1) or -1
    m["export"]["day"] = num(m["export"]["day"], 1, 28, 5)
    for part in ("cutoff", "export"):
        if not re.fullmatch(r"([01]\d|2[0-3]):[0-5]\d", str(m[part].get("time") or "")):
            m[part]["time"] = DEFAULT_SETTINGS[part]["time"]
    m["retry"]["count"] = num(m["retry"]["count"], 0, 10, 3)
    m["retry"]["interval_hours"] = num(m["retry"]["interval_hours"], 1, 168, 24)
    c = m["criteria"]
    for role in ("manager", "accountant"):
        c[role]["approve_all"] = bool(c[role].get("approve_all"))
        c[role]["max_amount"] = num(c[role]["max_amount"], 0, 10_000_000, 1000.0)
        c[role]["risk_levels"] = [x for x in c[role].get("risk_levels") or [] if x in ("none", "low", "high")]
    c["manager"]["monthly_employee_limit"] = num(c["manager"]["monthly_employee_limit"], 0, 100_000_000, 15000.0)
    c["manager"]["categories"] = [str(x)[:120] for x in c["manager"].get("categories") or []][:50]
    c["accountant"]["min_confidence"] = num(c["accountant"]["min_confidence"], 0, 100, 85.0)
    c["accountant"]["correct_min_confidence"] = num(c["accountant"]["correct_min_confidence"], 0, 100, 90.0)
    c["accountant"]["safe_sources"] = [x for x in c["accountant"].get("safe_sources") or [] if x in SAFE_SOURCES_ALL]
    return m


def period_of(d: date) -> str:
    return f"{d.year:04d}-{d.month:02d}"


def next_period(period: str) -> str:
    y, m = (int(x) for x in period.split("-"))
    return f"{y + (m == 12):04d}-{(m % 12) + 1:02d}"


def _at(y: int, m: int, day: int, hhmm: str) -> datetime:
    last = calendar.monthrange(y, m)[1]
    d = last if day < 0 else min(day, last)
    h, mi = (int(x) for x in hhmm.split(":"))
    return datetime.combine(date(y, m, d), time(h, mi), TZ).astimezone(timezone.utc)


def calendar_of(period: str, s: Dict[str, Any]) -> Dict[str, datetime]:
    """Dönemin kesim, geç fiş sonu ve aktarım zamanları (UTC)."""
    y, m = (int(x) for x in period.split("-"))
    ny, nm = (int(x) for x in next_period(period).split("-"))
    return {"cutoff": _at(y, m, s["cutoff"]["day"], s["cutoff"]["time"]),
            "late_until": _at(ny, nm, s["late_tolerance_day"], "23:59") if s["late_tolerance_day"] else _at(y, m, -1, "23:59"),
            "export": _at(ny, nm, s["export"]["day"], s["export"]["time"])}


# ---------------------------------------------------------------- Odoo okuma (v2)
async def _kw(ctx: Context, model: str, method: str, args: list, kw: Optional[Dict[str, Any]] = None) -> Any:
    from app.integrations import odoo
    return await odoo._kw(ctx, model, method, args, kw or {})


async def check_v2(ctx: Context) -> str:
    """Bağlantıdaki Odoo'da RECSlip v2 kurulu mu; sürümü döner. Değilse RecslipError."""
    rows = await _kw(ctx, "ir.module.module", "search_read", [[["name", "=", "recslip"], ["state", "=", "installed"]]],
                     {"fields": ["installed_version"], "limit": 1})
    version = (rows[0].get("installed_version") if rows else "") or ""
    parts = tuple(int(x) for x in re.findall(r"\d+", version)[:4])
    if not parts or parts < MIN_VERSION:
        raise RecslipError(f"Bu Odoo'da RECSlip.App v2 ({'.'.join(map(str, MIN_VERSION))} veya sonrası) kurulu değil"
                           f"{f' (kurulu: {version})' if version else ''}.")
    return version


def _m2o(v: Any) -> Tuple[Optional[int], Optional[str]]:
    return (v[0], v[1]) if isinstance(v, list) and len(v) == 2 else (None, None)


async def pending_steps(ctx: Context, limit: int = 200) -> List[Dict[str, Any]]:
    """Bekleyen onay adımları; her biri fiş ve kalemleriyle."""
    steps = await _kw(ctx, "recslip.approval", "search_read", [[["state", "=", "pending"]]],
                      {"fields": STEP_FIELDS, "limit": limit, "order": "id"}) or []
    ids = sorted({_m2o(s["expense_id"])[0] for s in steps if _m2o(s["expense_id"])[0]})
    if not ids:
        return []
    expenses = {e["id"]: e for e in await _kw(ctx, "hr.expense", "read", [ids], {"fields": EXPENSE_FIELDS}) or []}
    lines: Dict[int, List[Dict[str, Any]]] = {}
    for ln in await _kw(ctx, "recslip.expense.line", "search_read", [[["expense_id", "in", ids]]], {"fields": LINE_FIELDS}) or []:
        lines.setdefault(_m2o(ln["expense_id"])[0], []).append(ln)
    out = []
    for s in steps:
        eid = _m2o(s["expense_id"])[0]
        if eid in expenses:
            out.append({**s, "expense": expenses[eid], "lines": lines.get(eid, [])})
    return out


async def employee_month_total(ctx: Context, employee_id: int, d: date) -> float:
    first, last = date(d.year, d.month, 1), date(d.year, d.month, calendar.monthrange(d.year, d.month)[1])
    rows = await _kw(ctx, "hr.expense", "search_read", [[
        ["employee_id", "=", employee_id], ["date", ">=", first.isoformat()], ["date", "<=", last.isoformat()],
        ["rs_state", "in", ["approval", "done", "exported", "posted_external"]]]], {"fields": ["total_amount_currency"], "limit": 2000})
    return round(sum(float(r.get("total_amount_currency") or 0) for r in rows or []), 2)


# ---------------------------------------------------------------- değerlendirme
def _date(v: Any) -> Optional[date]:
    try:
        return date.fromisoformat(str(v)[:10]) if v else None
    except ValueError:
        return None


def check_manager(exp: Dict[str, Any], crit: Dict[str, Any], month_total: float) -> Tuple[str, List[str]]:
    """Yönetici/ek onaylayıcı kriterleri → (APPROVE | REVIEW, gerekçeler)."""
    amount = float(exp.get("total_amount_currency") or 0)
    reasons: List[str] = []
    if exp.get("rs_is_duplicate") and crit.get("duplicate_to_human", True):
        reasons.append("Mükerrer şüphesi var.")
    if not crit.get("approve_all"):
        if amount > float(crit["max_amount"]):
            reasons.append(f"Tutar {amount:,.2f} sınırı ({float(crit['max_amount']):,.2f}) aşıyor.")
        if (exp.get("rs_risk_level") or "none") not in crit["risk_levels"]:
            reasons.append(f"Risk seviyesi: {exp.get('rs_risk_level')}" + (f" ({exp['rs_risk_notes']})" if exp.get("rs_risk_notes") else "") + ".")
        d = _date(exp.get("date"))
        if crit.get("weekend_to_human") and d and d.weekday() >= 5:
            reasons.append("Hafta sonu harcaması.")
        cats = crit.get("categories") or []
        cat = _m2o(exp.get("product_id"))[1]
        if cats and cat not in cats:
            reasons.append(f"Kategori ({cat or '—'}) izinli listede değil.")
        limit = float(crit.get("monthly_employee_limit") or 0)
        if limit and month_total > limit:
            reasons.append(f"Çalışanın bu ayki toplamı {month_total:,.2f} sınırı ({limit:,.2f}) aşıyor.")
    if reasons:
        return "REVIEW", reasons
    return "APPROVE", [f"Kriterlere uygun: {amount:,.2f} {(_m2o(exp.get('currency_id'))[1] or 'TRY')}, risk "
                       f"{exp.get('rs_risk_level') or 'none'}" + (", tümünü onayla açık" if crit.get("approve_all") else "") + "."]


def check_accountant_receipt(exp: Dict[str, Any], lines: List[Dict[str, Any]], crit: Dict[str, Any]) -> List[str]:
    """Muhasebe: fiş düzeyi engeller (eşiklerden bağımsız olanlar 'tümünü onayla'da da aranır)."""
    reasons = []
    if not exp.get("rs_balance_ok"):
        reasons.append("Ön muhasebe özeti dengede değil.")
    if exp.get("rs_is_duplicate"):
        reasons.append("Mükerrer şüphesi var.")
    if not lines:
        reasons.append("Fişte kalem yok.")
    if crit.get("approve_all"):
        return reasons
    amount = float(exp.get("total_amount_currency") or 0)
    if amount > float(crit["max_amount"]):
        reasons.append(f"Tutar {amount:,.2f} sınırı ({float(crit['max_amount']):,.2f}) aşıyor.")
    if (exp.get("rs_risk_level") or "none") not in crit["risk_levels"]:
        reasons.append(f"Risk seviyesi: {exp.get('rs_risk_level')}" + (f" ({exp['rs_risk_notes']})" if exp.get("rs_risk_notes") else "") + ".")
    if float(exp.get("rs_confidence") or 0) < float(crit["min_confidence"]):
        reasons.append(f"Fiş güveni {float(exp.get('rs_confidence') or 0):.0f} (en az {float(crit['min_confidence']):.0f}).")
    if exp.get("rs_doc_type") in (crit.get("blocked_doc_types") or []):
        reasons.append(f"Belge türü ({exp.get('rs_doc_type')}) insan kontrolü istiyor.")
    if crit.get("kkeg_to_human") and any(ln.get("not_expense") for ln in lines):
        reasons.append("KKEG (gider değil) işaretli kalem var.")
    return reasons


MERGEN_ASK = "Classify every line of KALEMLER and return the JSON described in your instructions."


def _json(text: str) -> Dict[str, Any]:
    m = re.search(r"\{.*\}", text or "", re.S)
    if not m:
        return {}
    try:
        return json.loads(m.group(0))
    except json.JSONDecodeError:
        return {}


async def second_opinion(tenant_id, person_ctx: Context, expense_id: int, line_ids: List[int]) -> Dict[int, Dict[str, Any]]:
    """RECAi:Mergen ikinci görüşü: v2'nin hazırladığı prompt ile, llm_gateway üzerinden (yedek modelli). Aday dışı kod atılır."""
    from app.services import llm_gateway
    from app.services.llm_gateway import LLMContext

    inputs = await _kw(person_ctx, "hr.expense", "rs_external_mergen_inputs", [[expense_id]], {"line_ids": line_ids})
    candidates = {str(k): int(v) for k, v in (inputs.get("candidates") or {}).items()}
    if not candidates:
        return {}
    messages = [{"role": "system", "content": inputs["system"]}, {"role": "user", "content": MERGEN_ASK}]
    ctx = LLMContext(tenant_id=tenant_id, purpose="BRAIN", task_type="STRUCTURED")
    answer: Dict[str, Any] = {}
    for attempt in range(2):
        result = await llm_gateway.chat(ctx, messages, temperature=0.1, max_tokens=4000, timeout=240, fallback=True)
        answer = _json(result.content)
        wrong = [i for i in answer.get("kalemler") or [] if i.get("hesap_kodu") and str(i["hesap_kodu"]) not in candidates]
        if answer.get("kalemler") and not wrong:
            break
        messages += [{"role": "assistant", "content": result.content or ""},
                     {"role": "user", "content": "Önceki yanıtta aday listesinde olmayan kod veya eksik kalem vardı. Yalnızca ADAY_HESAPLAR "
                                                 "içindeki kodları (ya da null) kullan ve her kalem için bir sonuç ver."}]
    out: Dict[int, Dict[str, Any]] = {}
    for item in answer.get("kalemler") or []:
        try:
            lid = int(item.get("id"))
        except (TypeError, ValueError):
            continue
        code = str(item.get("hesap_kodu")) if item.get("hesap_kodu") else None
        conf = round(max(0.0, min(1.0, float(item.get("guven") or 0))) * 100, 1)
        out[lid] = {"code": code if code in candidates else None, "account_id": candidates.get(code) if code else None,
                    "confidence": conf, "reason": str(item.get("gerekce") or "")[:500],
                    "review": bool(item.get("inceleme_gerekli")) or conf < 60, "kkeg": bool(item.get("kkeg_mi")),
                    "tags": [str(t) for t in item.get("uyari_etiketleri") or []][:8]}
    return out


async def check_accountant(tenant_id, person_ctx: Context, exp: Dict[str, Any], lines: List[Dict[str, Any]],
                           crit: Dict[str, Any]) -> Tuple[str, List[str], List[Dict[str, Any]]]:
    """Muhasebe kriterleri + kalem kontrolü → (APPROVE | REVIEW, gerekçeler, düzeltmeler)."""
    reasons = check_accountant_receipt(exp, lines, crit)
    safe = set(crit.get("safe_sources") or [])
    unsafe = [ln for ln in lines if (ln.get("match_source") or "") not in safe]
    corrections: List[Dict[str, Any]] = []
    if unsafe and crit.get("second_opinion", True):
        try:
            opinion = await second_opinion(tenant_id, person_ctx, exp["id"], [ln["id"] for ln in unsafe])
        except Exception as exc:  # ikinci görüş alınamazsa fiş insana düşer
            logger.warning("RECAi:Mergen ikinci görüşü alınamadı (fiş %s): %s", exp.get("id"), exc)
            opinion = None
            reasons.append(f"RECAi:Mergen ikinci görüşü alınamadı ({str(exc)[:120]}).")
        for ln in unsafe if opinion is not None else []:
            o = opinion.get(ln["id"])
            cur_id, cur_name = _m2o(ln.get("account_id"))
            if not o or not o["account_id"]:
                if not crit.get("approve_all"):
                    reasons.append(f"'{ln['name']}': RECAi:Mergen emin değil" + (f" ({o['reason']})" if o and o.get("reason") else "") + ".")
                continue
            if o["account_id"] == cur_id:
                if o["review"] and not crit.get("approve_all"):
                    reasons.append(f"'{ln['name']}': hesap aynı ama güven düşük ({o['confidence']:.0f}).")
                continue
            if o["confidence"] >= float(crit["correct_min_confidence"]):
                corrections.append({"line_id": ln["id"], "line": ln["name"], "old": cur_name, "old_id": cur_id, "new": o["code"],
                                    "new_id": o["account_id"], "reason": o["reason"], "confidence": o["confidence"]})
            elif not crit.get("approve_all"):
                reasons.append(f"'{ln['name']}': RECAi:Mergen farklı hesap öneriyor ({o['code']}, güven {o['confidence']:.0f}); insan kararı gerekli.")
    elif unsafe and not crit.get("approve_all"):
        reasons.append(f"{len(unsafe)} kalemin hesabı onaylı kaynaktan gelmiyor.")
    if reasons:
        return "REVIEW", reasons, corrections
    msg = "Kriterlere uygun; kalem hesapları onaylı kaynaktan veya RECAi:Mergen ile uyumlu."
    if corrections:
        msg += f" {len(corrections)} kalemin hesabı düzeltildi."
    return "APPROVE", [msg], corrections


# ---------------------------------------------------------------- yürütme
def _agent_name(agent: Optional[Actor], role: str) -> str:
    return agent.display_name if agent else ("RECAi Muhasebe Kontrol Personeli" if role == "accountant" else "RECAi Masraf Onay Asistanı")


async def _person(db: AsyncSession, conn: IntegrationConnection, uids: List[int]) -> Tuple[Optional[PersonalCredential], Optional[Actor], Optional[Actor]]:
    creds = await pcs.by_external_uids(db, conn.id, [int(u) for u in uids or []])
    for cred in creds:
        owner = await db.get(Actor, cred.actor_id)
        if owner and owner.status != "DISABLED":
            agent = await db.get(Actor, cred.agent_actor_id) if cred.agent_actor_id else None
            return cred, owner, agent
    return None, None, None


async def _call_person(db: AsyncSession, cred: PersonalCredential, ctx: Context, method: str, ids: List[int], **kw) -> Any:
    try:
        return await _kw(ctx, "hr.expense", method, [ids], kw)
    except ToolError as exc:
        if "geçersiz" in str(exc) or "süresi dolmuş" in str(exc):
            await pcs.mark_invalid(db, cred, str(exc))
        raise


async def process_step(db: AsyncSession, tenant_id, conn: IntegrationConnection, project: Optional[Project],
                       step: Dict[str, Any], s: Dict[str, Any], month_totals: Dict[int, float]) -> Optional[RecslipDecision]:
    """Bir bekleyen adımı değerlendirir ve sonuca göre işler. Daha önce değerlendirilmişse (FAILED dışında) dokunmaz."""
    exp, lines, role = step["expense"], step["lines"], step["role"]
    dec = (await db.execute(select(RecslipDecision).where(RecslipDecision.connection_id == conn.id,
                                                          RecslipDecision.step_id == step["id"]))).scalar_one_or_none()
    if dec and dec.status != "FAILED":
        return None
    cred, owner, agent = await _person(db, conn, step.get("user_ids") or [])
    if not cred:
        return None  # onaylayıcı RECOrion'da anahtar tanımlamadı: adım Odoo'da insanla yürür
    ctx = pcs.context(conn, cred)
    crit = s["criteria"]["accountant" if role == "accountant" else "manager"]
    corrections: List[Dict[str, Any]] = []
    try:
        if role == "accountant":
            verdict, reasons, corrections = await check_accountant(tenant_id, ctx, exp, lines, crit)
        else:
            emp_id = _m2o(exp.get("employee_id"))[0]
            d = _date(exp.get("date")) or date.today()
            if emp_id and emp_id not in month_totals:
                month_totals[emp_id] = await employee_month_total(ctx, emp_id, d)
            verdict, reasons = check_manager(exp, crit, month_totals.get(emp_id, 0.0))
    except ToolError as exc:
        verdict, reasons = "REVIEW", [f"Fiş okunamadı: {str(exc)[:200]}"]
    if not dec:
        dec = RecslipDecision(tenant_id=tenant_id, connection_id=conn.id, step_id=step["id"], role=role, expense_id=exp["id"])
        db.add(dec)
    dec.project_id = project.id if project else None
    dec.expense_name, dec.employee_name = (exp.get("name") or "")[:255], (_m2o(exp.get("employee_id"))[1] or "")[:160]
    dec.amount, dec.currency = exp.get("total_amount_currency"), (_m2o(exp.get("currency_id"))[1] or "TRY")[:3]
    dec.receipt_date = _date(exp.get("date"))
    dec.approver_actor_id, dec.agent_actor_id = owner.id, agent.id if agent else None
    dec.verdict, dec.reasons, dec.corrections, dec.error = verdict, reasons, corrections, None
    if verdict == "APPROVE":
        try:
            await _call_person(db, cred, ctx, "rs_external_approve", [exp["id"]], agent=_agent_name(agent, role),
                               reason=" ".join(reasons)[:2000], line_accounts={str(c["line_id"]): c["new_id"] for c in corrections} or None)
            dec.status, dec.decided_at = "AUTO_DONE", now()
        except ToolError as exc:
            dec.status, dec.error = "FAILED", str(exc)[:1000]
    else:
        dec.status = "PENDING"
    await db.commit()
    if dec.status == "PENDING":
        await _notify_review(db, dec, owner)
    return dec


async def _notify_review(db: AsyncSession, dec: RecslipDecision, owner: Actor) -> None:
    from app.config import settings
    from app.services import notify

    try:
        await notify.send(db, owner.id, f"RECSlip: '{dec.expense_name}' ({dec.amount} {dec.currency}) {STEP_ROLES.get(dec.role, dec.role).lower()} "
                                        f"onayınızı bekliyor. AI önerisi: {'; '.join(dec.reasons)[:300]}\n"
                                        f"{settings.PUBLIC_APP_URL.rstrip('/')}/#/approvals")
    except Exception as exc:
        logger.warning("RECSlip bildirimi gönderilemedi: %s", exc)


async def settle_elsewhere(db: AsyncSession, conn: IntegrationConnection, pending_ids: List[int]) -> int:
    """Kişinin Onaylarım'ında bekleyen ama Odoo'da artık beklemeyen adımlar (Odoo'dan karar verildi): ELSEWHERE."""
    rows = (await db.execute(select(RecslipDecision).where(RecslipDecision.connection_id == conn.id,
                                                           RecslipDecision.status == "PENDING"))).scalars().all()
    n = 0
    for d in rows:
        if d.step_id not in pending_ids:
            d.status, d.decided_at = "ELSEWHERE", now()
            n += 1
    if n:
        await db.commit()
    return n


async def run_connection(db: AsyncSession, conn: IntegrationConnection, project: Optional[Project]) -> Dict[str, int]:
    """Bir bağlantının bekleyen onay adımlarını işler. Dönüş: sayaçlar."""
    from app.services import tool_gateway

    s = settings_of(project)
    company_ctx = tool_gateway.context(conn)
    steps = await pending_steps(company_ctx)
    await settle_elsewhere(db, conn, [st["id"] for st in steps])
    counts = {"pending": len(steps), "auto": 0, "review": 0, "failed": 0, "skipped": 0}
    totals: Dict[int, float] = {}
    for st in steps:
        dec = await process_step(db, conn.tenant_id, conn, project, st, s, totals)
        if not dec:
            counts["skipped"] += 1
        else:
            counts[{"AUTO_DONE": "auto", "PENDING": "review"}.get(dec.status, "failed")] += 1
    return counts


async def decide(db: AsyncSession, dec: RecslipDecision, actor: Actor, approve: bool, note: Optional[str],
                 apply_corrections: bool = True) -> RecslipDecision:
    """İnsan kararı (Onaylarım): kişinin kendi anahtarıyla; AI bayrağı atılmaz (karar insanındır)."""
    from fastapi import HTTPException

    if dec.status != "PENDING":
        raise HTTPException(status_code=409, detail="Bu fiş artık karar beklemiyor.")
    if dec.approver_actor_id != actor.id:
        raise HTTPException(status_code=403, detail="Bu fişin onaylayıcısı siz değilsiniz.")
    conn = await db.get(IntegrationConnection, dec.connection_id)
    cred = (await db.execute(select(PersonalCredential).where(PersonalCredential.actor_id == actor.id,
                                                              PersonalCredential.connection_id == conn.id))).scalar_one_or_none()
    if not pcs.usable(cred):
        raise HTTPException(status_code=409, detail="Odoo anahtarınız geçersiz veya süresi dolmuş; Bağlantılarım'dan yenileyin.")
    ctx = pcs.context(conn, cred)
    if not approve and not (note or "").strip():
        raise HTTPException(status_code=400, detail="Red gerekçesi yazın.")
    try:
        if approve:
            accounts = {str(c["line_id"]): c["new_id"] for c in dec.corrections or []} if apply_corrections else {}
            await _call_person(db, cred, ctx, "rs_external_approve", [dec.expense_id], line_accounts=accounts or None)
        else:
            await _call_person(db, cred, ctx, "rs_external_refuse", [dec.expense_id], reason=note.strip())
    except ToolError as exc:
        raise HTTPException(status_code=400, detail=f"Odoo: {exc}")
    dec.status = "HUMAN_APPROVED" if approve else "HUMAN_REFUSED"
    dec.decided_by_actor_id, dec.decided_at, dec.human_note = actor.id, now(), (note or "").strip()[:2000] or None
    # uyum: AI "onayla" dediyse insan onayı; AI "insan baksın" dediyse karar uyum sayılmaz; düzeltme önerisi kabul edildi mi
    dec.human_agreed = (approve and dec.verdict == "APPROVE") or (bool(dec.corrections) and approve and apply_corrections) or None
    await db.commit()
    return dec


def decision_out(d: RecslipDecision, approver: Optional[Actor] = None, agent: Optional[Actor] = None) -> Dict[str, Any]:
    return {"id": str(d.id), "expense_id": d.expense_id, "step_id": d.step_id, "role": d.role, "role_label": STEP_ROLES.get(d.role, d.role),
            "expense_name": d.expense_name, "employee_name": d.employee_name, "amount": float(d.amount or 0), "currency": d.currency,
            "receipt_date": d.receipt_date, "verdict": d.verdict, "status": d.status, "reasons": d.reasons or [],
            "corrections": d.corrections or [], "error": d.error, "approver_name": approver.display_name if approver else None,
            "agent_name": agent.display_name if agent else None, "created_at": d.created_at, "decided_at": d.decided_at,
            "human_agreed": d.human_agreed, "human_note": d.human_note}
