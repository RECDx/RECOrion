"""
RECDx uygulamaları (ADIM 13.1): RECDx'in Odoo üzerinde çalışan ürünleriyle entegrasyon tercihi.

- RECQmind: pazar yeri (Trendyol, Hepsiburada, Amazon...) e-postalarından Odoo Helpdesk bileti açan AI destek masası.
- RECSlip: masraf fişlerini AI ile okuyup ön muhasebe kaydı hazırlayan Odoo uygulaması (LUCA/Logo aktarımı).
Müşteri paket alırken veya sonra Şirket Yönetimi'nde yanıtlar: Odoo'nuz var mı; her uygulama için USING (kullanıyorum),
INTERESTED (kullanmak isterim → RECDx satış ekibine bilgi), NO. Entegrasyon (katalog kartı, hazır eşlemeler, kurallar)
yalnızca Odoo varsa VE uygulama USING ise açılır. Tercih tenants.settings["recdx_apps"] içinde tutulur.
"""
from datetime import datetime, timezone
from typing import Any, Dict, Optional

APPS: Dict[str, Dict[str, Any]] = {
    "recqmind": {"title": "RECQmind", "subtitle": "Pazar yeri AI destek masası (Odoo Helpdesk)",
                 "description": "Trendyol, Hepsiburada, Amazon gibi pazar yerlerinden e-postayla gelen sipariş, soru, problem ve iade "
                                "bildirimlerini Odoo Helpdesk'te bilete dönüştürür, sınıflandırır ve önceliklendirir.",
                 "with_recorion": "İade, iptal, kargo problemi gibi birden çok kişi gerektiren biletler RECOrion'da Case olarak açılır; "
                                  "AI personel siparişi ve stoğu inceler, yanıt taslağı hazırlar, sonuç onayla Odoo biletine yazılır.",
                 "url": "https://www.recdx.com/recqmind"},
    "recslip": {"title": "RECSlip", "subtitle": "AI masraf fişi ve ön muhasebe (Odoo)",
                "description": "Masraf fişlerini AI ile okur, şirketin faaliyet alanına göre hesaplara ayırır, onaydan sonra LUCA/Logo'ya "
                               "aktarım dosyası hazırlar.",
                "with_recorion": "Sorunlu fişler (mükerrer, eksik VKN, düşük güven) RECOrion'da Case olur; ay sonu kapanış kontrolü "
                                 "otomatik açılır, eksikler ve onay bekleyenler takip edilir.",
                "url": "https://www.recdx.com/recslip-mukellef"},
}
CHOICES = ("USING", "INTERESTED", "NO")


def clean(raw: Any) -> Dict[str, Any]:
    """Gelen tercihi doğrular; bilinmeyen uygulama/seçim atılır. Odoo yoksa uygulama 'kullanıyorum' olamaz (ilgi kalabilir)."""
    raw = raw if isinstance(raw, dict) else {}
    has_odoo = raw.get("has_odoo")
    has_odoo = bool(has_odoo) if has_odoo is not None else None
    apps = {}
    for code in APPS:
        v = str((raw.get("apps") or {}).get(code) or "").upper()
        if v in CHOICES:
            apps[code] = "INTERESTED" if (v == "USING" and has_odoo is False) else v
    return {"has_odoo": has_odoo, "apps": apps}


def get(tenant) -> Dict[str, Any]:
    pref = (tenant.settings or {}).get("recdx_apps") or {}
    return {"has_odoo": pref.get("has_odoo"), "apps": pref.get("apps") or {}, "updated_at": pref.get("updated_at")}


def is_active(tenant, code: str) -> bool:
    """Entegrasyon açık mı: şirketin Odoo'su var ve uygulamayı kullanıyor."""
    pref = get(tenant)
    return bool(pref["has_odoo"]) and pref["apps"].get(code) == "USING"


def store(tenant, pref: Dict[str, Any], actor_id=None) -> Dict[str, Any]:
    data = {**clean(pref), "updated_at": datetime.now(timezone.utc).isoformat(), "updated_by": str(actor_id) if actor_id else None}
    tenant.settings = {**(tenant.settings or {}), "recdx_apps": data}
    return data


def interests(pref: Dict[str, Any]) -> list:
    return [APPS[c]["title"] for c, v in (pref.get("apps") or {}).items() if v == "INTERESTED" and c in APPS]


def describe(tenant=None, connections: Optional[list] = None) -> Dict[str, Any]:
    """Ekran için: uygulamalar, tercihler ve her uygulamanın durumu (açık / Odoo bağlantısı gerekli / kapalı)."""
    pref = get(tenant) if tenant is not None else {"has_odoo": None, "apps": {}, "updated_at": None}
    odoo_connected = any(c.connector == "odoo" and c.status == "ACTIVE" for c in (connections or []))
    out = []
    for code, a in APPS.items():
        choice = pref["apps"].get(code)
        if pref["has_odoo"] and choice == "USING":
            state = "ACTIVE" if odoo_connected else "NEEDS_ODOO"
        elif choice == "INTERESTED":
            state = "INTERESTED"
        else:
            state = "OFF"
        out.append({"code": code, **a, "choice": choice, "state": state})
    return {"has_odoo": pref["has_odoo"], "updated_at": pref.get("updated_at"), "odoo_connected": odoo_connected, "apps": out,
            "choices": {"USING": "Kullanıyorum", "INTERESTED": "Kullanmak isterim", "NO": "Hayır"}}
