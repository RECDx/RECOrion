"""
RECSlip entegrasyonu (ADIM 13.4): sorunlu masraf fişi → RECOrion Case; ay sonu kapanış kontrolü.

- Okuma: Odoo hr.expense kayıtları izleme turunda okunur; enrich() satıcının VKN'sini (res.partner) ve sürüme/şirkete göre var
  olan ek alanları (Odoo'nun mükerrer ve fiş okuma alanları, RECSlip.App rec_fld_* / eski Studio x_studio_* alanları) tek okumayla
  getirir; her kayda "slip" ortak nesnesini (EXPENSE_RECEIPT) ve sorun listesini ekler: mükerrer olabilir, VKN/TCKN yok, VKN/TCKN
  geçersiz, fiş görseli yok, okuma doğrulanmalı, tutar yok. Kural koşulu: slip.has_problem = true (reddedilen, iptal edilen ve
  aktarılmayacak fişte false). Durum etiketi RECSlip onay akışından (Yönetici/Muhasebe onayında, Aktarıldı...) gelir.
- Sorunlu fiş kuralı: sorunlu fişten "Sorunlu masraf fişi" Case'i TASLAK açılır (kaynak = masraf kaydı); Case kapanınca masraf
  eşlemesiyle aktarım önerilir: karar ve yapılanlar masraf kaydına iç not olarak yazılır — onayla (12.4). Sorun listesi
  değişirse (ör. sonradan mükerrer çıktı) kayıt yeniden değerlendirilir.
- Ay sonu kapanış kuralı: her ayın son günü dönemin masraf özeti (adet, tutar, duruma göre, sorunlu fişler) Odoo'dan okunur ve
  "Ay sonu masraf kapanışı" Case'i bu özetle açılır.
- Yalnızca RECSlip'i kullanan (Odoo'su olan ve USING/ADD seçmiş) şirkette açılır.
"""
import calendar
from datetime import date
from typing import Any, Dict, List, Optional

from app.services import business_objects as bo

MODEL = "hr.expense"
APP = "recslip"
ENRICHER = "hr_expense"
SUMMARY = "expense_month"
MAPPING_CODE = "odoo_expense"
MODELS_NEEDED = ["hr.expense", "res.partner"]
FIELDS = ["id", "name", "date", "total_amount", "currency_id", "vendor_id", "employee_id", "product_id", "state", "payment_mode",
          "description", "nb_attachment"]
# RECSlip.App (19.0.1.2: rec_fld_*) ve eski Studio kurulumu (x_studio_*) alanları; ilk bulunan kullanılır
SLIP_FIELDS = {"duplicate": ["rec_fld_is_mukerrer", "x_studio_is_mukerrer"], "tax_no": ["rec_fld_vkn_tckn", "x_studio_vkn_tckn"],
               "receipt_no": ["rec_fld_fis_No", "x_fis_no"], "vat": ["rec_fld_toplam_kdv_tutar", "x_studio_toplam_kdv_tutar", "tax_amount"],
               "approval": ["rec_fld_onay_durumu", "x_studio_onay_durumu"], "refuse_reason": ["rec_fld_red_nedeni", "x_studio_red_nedeni"]}
# Sürüme / kuruluma göre olabilen alanlar: varsa okunur
OPTIONAL = ["duplicate_expense_ids", "extract_state"] + [f for names in SLIP_FIELDS.values() for f in names]
APPROVALS = {"onayinda_taslak": "Taslak", "taslak": "Taslak", "onayinda_yonetici": "Yönetici onayında", "yonetici": "Yönetici onayında",
             "onayinda_muhasebe": "Muhasebe onayında", "muhasebe": "Muhasebe onayında", "tamamlandi": "Tamamlandı",
             "iptal_edildi": "İptal edildi", "iptal": "İptal edildi", "aktarildi": "Aktarıldı", "aktarilmayacak": "Aktarılmayacak"}
CLOSED_APPROVALS = ("iptal_edildi", "iptal", "aktarilmayacak")
PROBLEMS = {"DUPLICATE": "Mükerrer olabilir", "MISSING_VKN": "Satıcı VKN/TCKN yok", "INVALID_VKN": "VKN/TCKN geçersiz",
            "NO_RECEIPT": "Fiş görseli yok", "LOW_CONFIDENCE": "Fiş okuması doğrulanmalı", "NO_AMOUNT": "Tutar yok"}
STATES = {"draft": "Taslak", "submitted": "Onaya gönderildi", "reported": "Onaya gönderildi", "approved": "Onaylandı",
          "posted": "Muhasebeleşti", "in_payment": "Ödemede", "paid": "Ödendi", "refused": "Reddedildi", "done": "Ödendi"}
UNCERTAIN_EXTRACT = ("waiting_validation", "to_validate", "error_status")
PRESETS = [
    {"code": "PROBLEM", "label": "Sorunlu fiş", "template": "recslip-sorunlu-fis", "name": "RECSlip: Sorunlu masraf fişi → Case"},
    {"code": "MONTH_END", "label": "Ay sonu kapanış", "template": "recslip-ay-sonu", "name": "RECSlip: Ay sonu masraf kapanışı"},
]
CASE_NAME = "Sorunlu fiş: {{slip.description}} · {{slip.total_amount}} {{slip.currency}} (masraf #{{id}})"
REQUIREMENTS = ("RECSlip'in okuduğu masraf fişindeki sorunu çöz.\n"
                "Sorunlar: {{slip.problem_text}}\n"
                "Fiş: {{slip.description}} · tarih {{slip.date}} · tutar {{slip.total_amount}} {{slip.currency}} · satıcı {{slip.vendor_name}} "
                "(VKN/TCKN: {{slip.vendor_tax_number}}) · fiş no {{slip.receipt_no}} · çalışan {{slip.employee_name}}\n"
                "Mükerrer ise diğer kaydı bul ve hangisinin geçerli olduğunu belirt; VKN eksik/geçersizse doğru VKN'yi veya fişin "
                "gider yazılamayacağını belirt. Son adımda masraf kaydına yazılacak iç notu (karar ve gerekçe) hazırla. Case kapanınca "
                "not onayla Odoo'daki masraf kaydına yazılır; muhasebe kaydı RECOrion'dan değiştirilmez.")
MONTH_NAME = "Ay sonu masraf kapanışı {{period}}"
MONTH_REQUIREMENTS = ("{{period}} dönemi masraf kapanışını yap.\n"
                      "Odoo özeti ({{date}}): {{expenses.count}} fiş, toplam {{expenses.total}} · {{expenses.by_state}}\n"
                      "Sorunlu fiş: {{expenses.problem_count}} ({{expenses.problem_text}})\n"
                      "Onay bekleyen ve sorunlu fişleri kapat, LUCA/Logo aktarımı öncesi kontrol listesini tamamla, kapanış raporunu "
                      "muhasebe müdürünün onayına sun.")


def _name(v: Any) -> Optional[str]:
    return v[1] if isinstance(v, list) and len(v) == 2 and isinstance(v[1], str) else None


def _id(v: Any) -> Optional[int]:
    return v[0] if isinstance(v, list) and v and isinstance(v[0], int) else v if isinstance(v, int) else None


def slip_value(record: Dict[str, Any], key: str) -> Any:
    for f in SLIP_FIELDS[key]:
        v = record.get(f)
        if v not in (None, False, ""):
            return v
    return None


def tax_number_problem(n: str) -> Optional[str]:
    digits = "".join(c for c in (n or "") if c.isdigit())
    if not digits:
        return "MISSING_VKN"
    if len(digits) == 10 and bo.vkn_ok(digits) or len(digits) == 11 and bo.tckn_ok(digits):
        return None
    return "INVALID_VKN"


def problems(record: Dict[str, Any], vendor_vat: Optional[str]) -> List[str]:
    out = []
    if record.get("duplicate_expense_ids") or slip_value(record, "duplicate"):
        out.append("DUPLICATE")
    p = tax_number_problem(str(slip_value(record, "tax_no") or vendor_vat or ""))
    if p:
        out.append(p)
    if "nb_attachment" in record and not record.get("nb_attachment"):
        out.append("NO_RECEIPT")
    if record.get("extract_state") in UNCERTAIN_EXTRACT:
        out.append("LOW_CONFIDENCE")
    try:
        if float(record.get("total_amount") or 0) <= 0:
            out.append("NO_AMOUNT")
    except (TypeError, ValueError):
        out.append("NO_AMOUNT")
    return out


def to_object(record: Dict[str, Any], vendor_vat: Optional[str] = None) -> Dict[str, Any]:
    """Odoo hr.expense kaydı → EXPENSE_RECEIPT (+ sorunlar ve ekranda/şablonda kullanılacak etiketler)."""
    if vendor_vat is None:
        vendor_vat = record.get("vendor_vat")
    tax_no = "".join(c for c in str(slip_value(record, "tax_no") or vendor_vat or "") if c.isdigit())
    obj = {"expense_ref": str(record.get("id") or ""), "description": str(record.get("name") or "").strip()[:255] or None,
           "date": record.get("date") or None, "total_amount": record.get("total_amount"), "vat_amount": slip_value(record, "vat"),
           "currency": (_name(record.get("currency_id")) or "TRY").upper()[:3], "vendor_name": _name(record.get("vendor_id")),
           "vendor_tax_number": tax_no or None, "receipt_no": str(slip_value(record, "receipt_no") or "").strip()[:64] or None,
           "category": _name(record.get("product_id")), "employee_name": _name(record.get("employee_id")),
           "payment": "EMPLOYEE" if record.get("payment_mode") == "own_account" else "COMPANY" if record.get("payment_mode") else None}
    clean, _ = bo.validate("EXPENSE_RECEIPT", {k: v for k, v in obj.items() if v not in (None, "")})
    probs = problems(record, vendor_vat)
    approval = slip_value(record, "approval")
    closed = record.get("state") == "refused" or approval in CLOSED_APPROVALS  # reddedilen/iptal fiş için Case açılmaz
    clean.update({"problems": probs, "problem_text": ", ".join(PROBLEMS[p] for p in probs) or "Yok",
                  "has_problem": bool(probs) and not closed,
                  "problem_key": ",".join(sorted(probs)), "state": record.get("state"), "approval": approval,
                  # RECSlip onay akışı varsa durum etiketi ondan (Yönetici/Muhasebe onayında, Aktarıldı...), yoksa Odoo durumundan
                  "state_label": APPROVALS.get(str(approval), approval) if approval
                  else STATES.get(str(record.get("state") or ""), record.get("state")),
                  "refuse_reason": slip_value(record, "refuse_reason"),
                  "currency": clean.get("currency") or "TRY"})
    for k in ("vendor_name", "vendor_tax_number", "receipt_no", "employee_name", "description", "date"):
        clean.setdefault(k, "—")  # şablon metninde boş yer tutucu kalmasın
    return clean


async def _optional_fields(ctx) -> List[str]:
    from app.integrations import odoo

    have = await odoo._kw(ctx, MODEL, "fields_get", [], {"attributes": ["type"]})
    return [f for f in OPTIONAL if f in (have or {})]


async def enrich(ctx, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """İzleme turunda okunan masraflara ek alanları, satıcı VKN'sini ve ortak nesneyi (sorunlarla) ekler."""
    from app.integrations import odoo
    from app.integrations.base import ToolError

    ids = [r["id"] for r in records if isinstance(r.get("id"), int)]
    extra: Dict[int, Dict[str, Any]] = {}
    if ids:
        try:
            opt = await _optional_fields(ctx)
            if opt:
                for row in await odoo._kw(ctx, MODEL, "read", [ids], {"fields": opt}) or []:
                    extra[row["id"]] = row
        except ToolError:
            extra = {}
    rows = [{**r, **{k: v for k, v in extra.get(r.get("id"), {}).items() if k != "id"}} for r in records]
    vendors = sorted({_id(r.get("vendor_id")) for r in rows if _id(r.get("vendor_id"))})
    vat: Dict[int, str] = {}
    if vendors:
        try:
            for p in await odoo._kw(ctx, "res.partner", "read", [vendors], {"fields": ["vat"]}) or []:
                vat[p["id"]] = p.get("vat") or ""
        except ToolError:  # res.partner izinli değilse VKN yalnızca masraf kaydındaki alandan okunur
            vat = {}
    out = []
    for r in rows:
        v = vat.get(_id(r.get("vendor_id")))
        out.append({**r, "vendor_vat": v, "slip": to_object(r, v)})
    return out


def normalize_sample(payload: Dict[str, Any]) -> Dict[str, Any]:
    if isinstance(payload, dict) and "slip" not in payload and payload.get("total_amount") is not None:
        return {**payload, "slip": to_object(payload)}
    return payload


async def month_summary(ctx, period: str, limit: int = 500) -> Dict[str, Any]:
    """Dönemin (YYYY-AA) masraf özeti: adet, toplam, duruma göre, sorunlu fişler (okuma)."""
    from app.integrations import odoo

    y, m = (int(x) for x in period.split("-"))
    first, last = date(y, m, 1), date(y, m, calendar.monthrange(y, m)[1])
    rows = await odoo._kw(ctx, MODEL, "search_read", [[["date", ">=", first.isoformat()], ["date", "<=", last.isoformat()]]],
                          {"fields": FIELDS, "limit": limit, "order": "date asc"}) or []
    rows = await enrich(ctx, rows)
    by_state: Dict[str, int] = {}
    total, probs = 0.0, {}
    for r in rows:
        by_state[r["slip"]["state_label"] or "—"] = by_state.get(r["slip"]["state_label"] or "—", 0) + 1
        total += float(r.get("total_amount") or 0)
        for p in r["slip"]["problems"]:
            probs[p] = probs.get(p, 0) + 1
    problem_rows = [r for r in rows if r["slip"]["has_problem"]]
    return {"count": len(rows), "total": f"{total:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
            "by_state": ", ".join(f"{k}: {v}" for k, v in sorted(by_state.items())) or "kayıt yok",
            "problem_count": len(problem_rows), "problem_text": ", ".join(f"{PROBLEMS[k]}: {v}" for k, v in probs.items()) or "yok",
            "problem_ids": [r["id"] for r in problem_rows][:50], "truncated": len(rows) >= limit}


def closing_defaults(project, item: Dict[str, Any]) -> Dict[str, Any]:
    """Masraftan açılan Case'in sonucu: RECAi kararı bulamadıysa kapanış özeti iç not olur."""
    out = dict(item)
    if not str(out.get("resolution") or "").strip() and getattr(project, "close_summary", None):
        out["resolution"] = project.close_summary
    return out


def poll_config(interval_minutes: int = 15) -> Dict[str, Any]:
    return {"tool": "search_records", "args": {"model": MODEL, "domain": [], "fields": FIELDS, "order": "id desc", "limit": 50},
            "id_field": "id", "version_field": "slip.problem_key", "interval_minutes": interval_minutes, "enrich": ENRICHER}


def preset_rules(connection_id, manager_actor_id, templates: Dict[str, Any], codes: List[str], mapping_id=None,
                 interval_minutes: int = 15, auto_start: bool = False) -> List[Dict[str, Any]]:
    rules = []
    for p in PRESETS:
        if p["code"] not in codes or p["template"] not in templates:
            continue
        action = {"type": "CREATE_CASE", "manager_actor_id": str(manager_actor_id), "template_id": str(templates[p["template"]]),
                  "auto_start": auto_start, "plan_with_recai": False}
        if p["code"] == "PROBLEM":
            rules.append({"name": p["name"], "trigger": "POLL", "connection_id": connection_id, "poll": poll_config(interval_minutes),
                          "description": "RECSlip hazır kuralı (Adım 13.4): sorunlu masraf fişinden Case açar; karar onayla masraf kaydına yazılır.",
                          "conditions": [{"field": "slip.has_problem", "op": "eq", "value": True}],
                          "action": {**action, "name": CASE_NAME, "transfer_on_close": [str(mapping_id)] if mapping_id else []},
                          "requirements": REQUIREMENTS, "rate_limit_per_hour": 20})
        else:
            rules.append({"name": p["name"], "trigger": "SCHEDULE", "connection_id": connection_id,
                          "schedule": {"every": "MONTH", "day": -1, "time": "10:00", "summary": SUMMARY},
                          "description": "RECSlip hazır kuralı (Adım 13.4): her ayın son günü dönemin masraf özetiyle kapanış Case'i açar.",
                          "conditions": [], "action": {**action, "name": MONTH_NAME}, "requirements": MONTH_REQUIREMENTS,
                          "rate_limit_per_hour": 5})
    return rules
