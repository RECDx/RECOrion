"""
RECQmind entegrasyonu (ADIM 13.3): destek bileti → RECOrion Case → sonuç onayla bilete.

- Okuma: Odoo helpdesk.ticket kayıtları otomasyonun izleme (POLL) turunda okunur; enrich() etiket adlarını tek okumayla getirir ve
  her kayda "ticket" ortak nesnesini (SUPPORT_TICKET: tür, kanal, öncelik, müşteri...) ekler. Kural koşulları bu alanlara yazılır
  (ör. ticket.category = RETURN). Tür, bilet etiketlerinden; etiket yoksa konu ve mesajdaki anahtar sözcüklerden bulunur.
- Hazır kurallar: İade / İptal / Kargo / Ürün sorusu için birer izleme kuralı. Her biri biletten Case'i ilgili şablonla TASLAK açar
  (Case'in kaynak kaydı = bilet) ve Case kapanınca Helpdesk eşlemesiyle aktarım önerir: bilet "Çözüldü" aşamasına alınır, çözüm
  bilete iç not olarak yazılır — yazma her zaman onayla (12.4). İlk turda mevcut biletler yalnızca not edilir.
- Yalnızca RECQmind'ı kullanan (Odoo'su olan ve USING/ADD seçmiş) şirkette açılır.
"""
import html
import re
from typing import Any, Dict, List, Optional

from app.services import business_objects as bo

MODEL = "helpdesk.ticket"
ENRICHER = "helpdesk_ticket"
FIELDS = ["id", "name", "description", "partner_name", "partner_email", "partner_phone", "priority", "tag_ids", "stage_id", "team_id",
          "create_date"]
PRIORITY = {"0": "LOW", "1": "NORMAL", "2": "HIGH", "3": "URGENT"}
# Sıra önemli: "iptal ve iade" gibi metinde ilk eşleşen tür seçilir
KEYWORDS = [
    ("CANCEL", r"iptal|vazgeç|cancel"),
    ("RETURN", r"iade|geri gönder|cayma|return|refund"),
    ("SHIPPING", r"kargo|teslimat|gönderi|ulaşmadı|gelmedi|gecik|shipping|delivery|tracking"),
    ("PRODUCT_QUESTION", r"soru|bilgi al|uyumlu mu|ürün hakkında|nasıl kullan|question"),
    ("ORDER", r"sipariş|order"),
]
TAGS = {"RETURN": ["iade", "return", "returns", "refund"], "CANCEL": ["iptal", "cancel", "cancellation"],
        "SHIPPING": ["kargo", "shipping", "delivery", "teslimat"], "PRODUCT_QUESTION": ["ürün sorusu", "soru", "question"],
        "ORDER": ["sipariş", "order"]}
CHANNELS = [("TRENDYOL", "trendyol"), ("HEPSIBURADA", "hepsiburada"), ("AMAZON", "amazon"), ("N11", "n11")]
PRESETS = [
    {"category": "RETURN", "template": "recqmind-iade", "name": "RECQmind: İade biletleri → İade Case'i"},
    {"category": "CANCEL", "template": "recqmind-iptal", "name": "RECQmind: İptal biletleri → İptal Case'i"},
    {"category": "SHIPPING", "template": "recqmind-kargo", "name": "RECQmind: Kargo problemleri → Kargo Case'i"},
    {"category": "PRODUCT_QUESTION", "template": "recqmind-urun-sorusu", "name": "RECQmind: Ürün soruları → Ürün sorusu Case'i"},
]
CASE_NAME = "{{ticket.category_label}}: {{ticket.subject}} (bilet #{{id}})"
REQUIREMENTS = ("RECQmind'dan gelen {{ticket.channel_label}} destek biletini sonuçlandır.\n"
                "Müşteri: {{ticket.customer_name}} ({{ticket.customer_email}})\n"
                "Konu: {{ticket.subject}}\n"
                "Müşteri mesajı: {{ticket.description}}\n"
                "Son adımda müşteriye yanıt taslağını ve bilete yazılacak iç notu (yapılan işlem ve sonuç) hazırla. "
                "Case kapanınca sonuç onayla Odoo biletine yazılır; müşteriye RECOrion'dan doğrudan yazılmaz.")


def tr_lower(s: str) -> str:
    return (s or "").replace("İ", "i").replace("I", "ı").lower()


def plain(text: Any) -> str:
    """Odoo html alanı → düz metin."""
    if not isinstance(text, str):
        return ""
    t = re.sub(r"<br\s*/?>|</p>|</div>", "\n", text, flags=re.I)
    t = html.unescape(re.sub(r"<[^>]+>", "", t))
    return re.sub(r"\n{3,}", "\n\n", t).strip()


def category(tag_names: List[str], subject: str, body: str) -> str:
    tags = [tr_lower(t).strip() for t in tag_names]
    for code, names in TAGS.items():
        if any(t in names for t in tags):
            return code
    for text_ in (subject, body):
        low = tr_lower(text_)
        for code, pat in KEYWORDS:
            if re.search(pat, low):
                return code
    return "OTHER"


def channel(*texts: str) -> str:
    low = tr_lower(" ".join(t for t in texts if t))
    for code, word in CHANNELS:
        if word in low:
            return code
    return "EMAIL" if "@" in low else "OTHER"


def _name(v: Any) -> Optional[str]:
    return v[1] if isinstance(v, list) and len(v) == 2 and isinstance(v[1], str) else None


def to_object(record: Dict[str, Any], tag_names: Optional[List[str]] = None) -> Dict[str, Any]:
    """Odoo helpdesk.ticket kaydı → SUPPORT_TICKET (+ ekranda/şablonda kullanılacak Türkçe etiketler)."""
    if tag_names is None:
        tag_names = [t for t in (record.get("tag_names") or []) if isinstance(t, str)]
    subject = str(record.get("name") or "").strip()
    body = plain(record.get("description"))
    obj = {"ticket_ref": str(record.get("id") or ""), "subject": subject[:255], "description": body[:8000],
           "category": category(tag_names, subject, body),
           "channel": channel(*tag_names, subject, str(record.get("partner_email") or ""), str(record.get("partner_name") or ""),
                              _name(record.get("team_id")) or ""),
           "priority": PRIORITY.get(str(record.get("priority") or "1"), "NORMAL"),
           "customer_name": record.get("partner_name") or None, "customer_email": record.get("partner_email") or None,
           "customer_phone": record.get("partner_phone") or None, "status": "OPEN"}
    clean, _ = bo.validate("SUPPORT_TICKET", obj)  # biçimi bozuk alan (ör. geçersiz e-posta) atılır
    clean["category_label"] = bo.SUPPORT_CATEGORY_LABELS[clean["category"]]
    clean["channel_label"] = bo.SUPPORT_CHANNEL_LABELS[clean["channel"]]
    clean["tags"] = tag_names
    clean["stage"] = _name(record.get("stage_id"))
    return clean


async def enrich(ctx, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """İzleme turunda okunan biletlere etiket adlarını (tek okuma) ve ortak nesneyi ekler."""
    from app.integrations import odoo
    from app.integrations.base import ToolError

    ids = sorted({t for r in records for t in (r.get("tag_ids") or []) if isinstance(t, int)})
    names: Dict[int, str] = {}
    if ids:
        try:
            for row in await odoo._kw(ctx, "helpdesk.tag", "read", [ids], {"fields": ["name"]}) or []:
                names[row["id"]] = row.get("name") or ""
        except ToolError:  # etiket modeli izinli değilse tür anahtar sözcüklerden bulunur
            names = {}
    out = []
    for r in records:
        tags = [names[t] for t in (r.get("tag_ids") or []) if t in names]
        out.append({**r, "tag_names": tags, "ticket": to_object(r, tags)})
    return out


def normalize_sample(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Elle deneme (örnek olay): bilet kaydı verildiyse ortak nesne eklenir (Odoo'ya gidilmez)."""
    if isinstance(payload, dict) and "ticket" not in payload and payload.get("name") is not None:
        return {**payload, "ticket": to_object(payload)}
    return payload


def poll_config(interval_minutes: int = 10) -> Dict[str, Any]:
    return {"tool": "search_records", "args": {"model": MODEL, "domain": [], "fields": FIELDS, "order": "id desc", "limit": 50},
            "id_field": "id", "version_field": None, "interval_minutes": interval_minutes, "enrich": ENRICHER}


def preset_rules(connection_id, manager_actor_id, templates: Dict[str, Any], categories: List[str], mapping_id=None,
                 interval_minutes: int = 10, auto_start: bool = False) -> List[Dict[str, Any]]:
    """Seçilen türler için hazır kural tanımları (otomasyon API'sinin kural biçiminde)."""
    rules = []
    for p in PRESETS:
        if p["category"] not in categories or p["template"] not in templates:
            continue
        rules.append({
            "name": p["name"], "trigger": "POLL", "connection_id": connection_id, "poll": poll_config(interval_minutes),
            "description": "RECQmind hazır kuralı (Adım 13.3): yeni Helpdesk biletinden Case açar; Case kapanınca sonuç onayla bilete yazılır.",
            "conditions": [{"field": "ticket.category", "op": "eq", "value": p["category"]}],
            "action": {"type": "CREATE_CASE", "name": CASE_NAME, "manager_actor_id": str(manager_actor_id),
                       "template_id": str(templates[p["template"]]), "auto_start": auto_start, "plan_with_recai": False,
                       "transfer_on_close": [str(mapping_id)] if mapping_id else []},
            "requirements": REQUIREMENTS, "rate_limit_per_hour": 20})
    return rules


def closing_defaults(project, item: Dict[str, Any]) -> Dict[str, Any]:
    """Biletten açılan Case'in sonucu: RECAi çözümü bulamadıysa kapanış özeti; Case tamamlandıysa durum Çözüldü."""
    out = dict(item)
    if not str(out.get("resolution") or "").strip() and getattr(project, "close_summary", None):
        out["resolution"] = project.close_summary
    if not out.get("status") and getattr(project, "status", None) == "COMPLETED":
        out["status"] = "SOLVED"
    return out
