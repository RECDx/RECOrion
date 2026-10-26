"""
Ortak iş nesneleri (ADIM 12.2): RECOrion'un dış sistemlere yazdığı kayıtların sistemden bağımsız, sürümlü şeması.

Aktarım şablonları (12.4) bu nesnelere göre yazılır, belirli bir ERP'ye göre değil; her sistem için yalnızca eşleme
(12.3) tanımlanır: ör. PRODUCT → Odoo product.template, Logo malzeme kartı, SAP malzeme ana verisi.
validate() nesneyi doğrular ve sadeleştirir (bilinmeyen alan atılır, sayı/tarih/e-posta biçimi, VKN/TCKN denetimi);
hata iletileri Türkçe ve alan etiketlidir (önizleme ekranında ve AI'a geri bildirimde gösterilir).
KVKK: TCKN (şahıs carisi) kişisel veridir; nesnede yalnızca aktarım için tutulur, kayıtlarda maskelenir (mask_pii).
"""
import re
from datetime import date
from typing import Any, Dict, List, Optional, Tuple

VERSION = "1"
UNITS = ["Adet", "Kg", "g", "Ton", "Lt", "ml", "m", "m²", "m³", "Saat", "Gün", "Paket", "Koli", "Kutu"]
CURRENCIES = ["TRY", "USD", "EUR", "GBP"]
SUPPORT_CATEGORIES = ["RETURN", "CANCEL", "SHIPPING", "PRODUCT_QUESTION", "ORDER", "OTHER"]
SUPPORT_CATEGORY_LABELS = {"RETURN": "İade", "CANCEL": "İptal", "SHIPPING": "Kargo", "PRODUCT_QUESTION": "Ürün sorusu",
                           "ORDER": "Sipariş", "OTHER": "Diğer"}
SUPPORT_CHANNELS = ["TRENDYOL", "HEPSIBURADA", "AMAZON", "N11", "WEB", "EMAIL", "OTHER"]
SUPPORT_CHANNEL_LABELS = {"TRENDYOL": "Trendyol", "HEPSIBURADA": "Hepsiburada", "AMAZON": "Amazon", "N11": "n11", "WEB": "Web sitesi",
                          "EMAIL": "E-posta", "OTHER": "Diğer"}


def F(key: str, label: str, type_: str, required: bool = False, help: str = "", **kw) -> Dict[str, Any]:
    return {"key": key, "label": label, "type": type_, "required": required, "help": help, **kw}


LINE_FIELDS = [
    F("product_code", "Ürün kodu", "string", help="Ürün kartındaki stok kodu", max_length=64),
    F("description", "Açıklama", "string", True, max_length=500),
    F("quantity", "Miktar", "number", True, min=0),
    F("unit", "Birim", "enum", options=UNITS),
    F("unit_price", "Birim fiyat", "number", True, min=0),
    F("vat_rate", "KDV oranı (%)", "number", min=0, max=100),
    F("discount", "İndirim (%)", "number", min=0, max=100),
]

OBJECTS: Dict[str, Dict[str, Any]] = {
    "PRODUCT": {"label": "Ürün / hizmet kartı", "fields": [
        F("code", "Stok kodu", "string", help="Şirketteki ürün kodu; aynı kodla ikinci kayıt açılmaz (güncellenir)", max_length=64),
        F("name", "Ürün adı", "string", True, max_length=255),
        F("type", "Tür", "enum", True, options=["STOCK", "SERVICE", "CONSUMABLE"],
          option_labels={"STOCK": "Stoklu ürün", "SERVICE": "Hizmet", "CONSUMABLE": "Sarf malzemesi"}),
        F("unit", "Birim", "enum", True, options=UNITS),
        F("sale_price", "Satış fiyatı", "number", min=0),
        F("purchase_price", "Alış fiyatı / maliyet", "number", min=0),
        F("currency", "Para birimi", "enum", options=CURRENCIES),
        F("vat_rate", "KDV oranı (%)", "number", min=0, max=100, help="Türkiye: 0, 1, 10 veya 20"),
        F("barcode", "Barkod", "string", max_length=64, pattern=r"^[0-9A-Za-z\-]{4,64}$"),
        F("category", "Kategori", "string", max_length=120),
        F("description", "Açıklama", "text", max_length=4000),
    ]},
    "PARTNER": {"label": "Cari (müşteri / tedarikçi)", "fields": [
        F("kind", "Cari türü", "enum", True, options=["COMPANY", "PERSON"], option_labels={"COMPANY": "Şirket", "PERSON": "Şahıs"}),
        F("name", "Unvan / ad soyad", "string", True, max_length=255),
        F("tax_number", "VKN / TCKN", "string", help="Şirket: 10 haneli VKN; şahıs: 11 haneli TCKN", max_length=20),
        F("tax_office", "Vergi dairesi", "string", max_length=120),
        F("email", "E-posta", "email", max_length=254),
        F("phone", "Telefon", "string", max_length=32, pattern=r"^[0-9+()\s\-]{7,32}$"),
        F("street", "Adres", "string", max_length=255),
        F("district", "İlçe", "string", max_length=80),
        F("city", "İl", "string", max_length=80),
        F("zip", "Posta kodu", "string", max_length=10),
        F("country", "Ülke kodu", "string", max_length=2, help="ISO kodu, ör. TR"),
        F("roles", "Rol", "list", options=["CUSTOMER", "SUPPLIER"], option_labels={"CUSTOMER": "Müşteri", "SUPPLIER": "Tedarikçi"}),
    ]},
    "ORDER": {"label": "Teklif / sipariş", "fields": [
        F("direction", "Yön", "enum", True, options=["SALE", "PURCHASE"], option_labels={"SALE": "Satış", "PURCHASE": "Satın alma"}),
        F("stage", "Aşama", "enum", True, options=["QUOTE", "ORDER"], option_labels={"QUOTE": "Teklif", "ORDER": "Sipariş"}),
        F("partner_ref", "Cari", "string", True, help="Carinin VKN'si veya unvanı (hedef sistemde aranır)", max_length=255),
        F("date", "Tarih", "date"),
        F("currency", "Para birimi", "enum", options=CURRENCIES),
        F("notes", "Not", "text", max_length=4000),
        F("lines", "Kalemler", "lines", True, fields=LINE_FIELDS, max_items=200),
    ]},
    "TASK": {"label": "Görev", "fields": [
        F("title", "Başlık", "string", True, max_length=255),
        F("description", "Açıklama", "text", max_length=8000),
        F("due_date", "Bitiş tarihi", "date"),
        F("assignee_email", "Sorumlu e-postası", "email", max_length=254),
        F("project_ref", "Proje", "string", max_length=255),
        F("priority", "Öncelik", "enum", options=["LOW", "NORMAL", "HIGH"], option_labels={"LOW": "Düşük", "NORMAL": "Normal", "HIGH": "Yüksek"}),
    ]},
    # ADIM 13.3: RECQmind/Helpdesk bileti. ticket_ref ile mevcut bilet bulunur; resolution bilete iç not olarak yazılır.
    "SUPPORT_TICKET": {"label": "Destek kaydı", "fields": [
        F("ticket_ref", "Bilet no", "string", help="Destek sistemindeki bilet numarası; doluysa mevcut bilet güncellenir", max_length=64),
        F("subject", "Konu", "string", max_length=255, help="Yeni bilet açılırken zorunlu"),
        F("description", "Müşteri mesajı", "text", max_length=8000),
        F("category", "Tür", "enum", options=SUPPORT_CATEGORIES, option_labels=SUPPORT_CATEGORY_LABELS),
        F("channel", "Kanal", "enum", options=SUPPORT_CHANNELS, option_labels=SUPPORT_CHANNEL_LABELS),
        F("priority", "Öncelik", "enum", options=["LOW", "NORMAL", "HIGH", "URGENT"],
          option_labels={"LOW": "Düşük", "NORMAL": "Normal", "HIGH": "Yüksek", "URGENT": "Acil"}),
        F("customer_name", "Müşteri adı", "string", max_length=255),
        F("customer_email", "Müşteri e-postası", "email", max_length=254),
        F("customer_phone", "Müşteri telefonu", "string", max_length=32, pattern=r"^[0-9+()\s\-]{7,32}$"),
        F("order_ref", "Sipariş no", "string", max_length=64),
        F("product_ref", "Ürün", "string", max_length=255, help="Ürün adı veya stok kodu"),
        F("status", "Durum", "enum", options=["OPEN", "SOLVED"], option_labels={"OPEN": "Açık", "SOLVED": "Çözüldü"}),
        F("resolution", "Çözüm / iç not", "text", max_length=8000, help="Yapılan işlem ve müşteriye verilecek yanıt; bilete iç not olarak yazılır"),
    ]},
    # ADIM 13.4: RECSlip/Odoo masraf kaydı. expense_ref ile mevcut kayıt bulunur; resolution kayda iç not olarak yazılır.
    "EXPENSE_RECEIPT": {"label": "Masraf fişi", "fields": [
        F("expense_ref", "Masraf no", "string", help="Masraf sistemindeki kayıt numarası; doluysa mevcut kayıt güncellenir", max_length=64),
        F("description", "Açıklama", "string", max_length=255, help="Yeni masraf açılırken zorunlu"),
        F("date", "Fiş tarihi", "date"),
        F("total_amount", "Toplam tutar (KDV dahil)", "number", min=0),
        F("vat_amount", "KDV tutarı", "number", min=0),
        F("currency", "Para birimi", "enum", options=CURRENCIES),
        F("vendor_name", "Satıcı", "string", max_length=255),
        F("vendor_tax_number", "Satıcı VKN/TCKN", "string", max_length=20),
        F("receipt_no", "Fiş / belge no", "string", max_length=64),
        F("category", "Masraf türü", "string", max_length=120, help="Odoo'daki masraf ürünü (ör. Yemek, Yol)"),
        F("employee_name", "Çalışan", "string", max_length=255),
        F("payment", "Ödeyen", "enum", options=["EMPLOYEE", "COMPANY"], option_labels={"EMPLOYEE": "Çalışan (geri ödenecek)", "COMPANY": "Şirket"}),
        F("resolution", "Karar / iç not", "text", max_length=8000, help="Sorunlu fişte verilen karar ve gerekçe; kayda iç not olarak yazılır"),
    ]},
    "DOCUMENT": {"label": "Doküman", "fields": [
        F("title", "Başlık", "string", True, max_length=255),
        F("artifact_id", "RECOrion çıktısı", "string", True, help="Adım çıktısının (dosyanın) kimliği", max_length=64),
        F("folder", "Klasör", "string", max_length=255),
        F("description", "Açıklama", "text", max_length=4000),
    ]},
}

EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def catalog() -> List[Dict[str, Any]]:
    return [{"code": k, "label": v["label"], "version": VERSION, "fields": v["fields"]} for k, v in OBJECTS.items()]


def tckn_ok(n: str) -> bool:
    """TCKN algoritması (11 hane, ilk hane 0 değil, 10. ve 11. hane denetimi)."""
    if not re.fullmatch(r"[1-9][0-9]{10}", n):
        return False
    d = [int(c) for c in n]
    return (sum(d[0:9:2]) * 7 - sum(d[1:8:2])) % 10 == d[9] and sum(d[:10]) % 10 == d[10]


def vkn_ok(n: str) -> bool:
    """Vergi kimlik numarası denetimi (10 hane, GİB algoritması)."""
    if not re.fullmatch(r"[0-9]{10}", n):
        return False
    total = 0
    for i, c in enumerate(n[:9]):
        t = (int(c) + 9 - i) % 10
        if t:
            v = (t * 2 ** (9 - i)) % 9
            total += 9 if v == 0 else v
    return (10 - total % 10) % 10 == int(n[9])


def _num(v: Any) -> Optional[float]:
    if isinstance(v, bool):
        return None
    if isinstance(v, (int, float)):
        return float(v)
    if isinstance(v, str):
        t = v.strip().replace("₺", "").replace("TL", "").replace(" ", "")
        if re.fullmatch(r"-?\d{1,3}(\.\d{3})+(,\d+)?", t) or re.fullmatch(r"-?\d+,\d+", t):  # Türkçe biçim: 1.250,50
            t = t.replace(".", "").replace(",", ".")
        try:
            return float(t)
        except ValueError:
            return None
    return None


def _field(f: Dict[str, Any], v: Any, label: str) -> Tuple[Any, Optional[str]]:
    t = f["type"]
    if t in ("string", "text", "email"):
        v = str(v).strip()
        if f.get("max_length") and len(v) > f["max_length"]:
            return None, f"{label} en fazla {f['max_length']} karakter olabilir."
        if t == "email" and not EMAIL.match(v):
            return None, f"{label} geçerli bir e-posta değil."
        if f.get("pattern") and not re.match(f["pattern"], v):
            return None, f"{label} biçimi geçersiz."
        return v, None
    if t == "number":
        n = _num(v)
        if n is None:
            return None, f"{label} sayı olmalı."
        if "min" in f and n < f["min"] or "max" in f and n > f["max"]:
            return None, f"{label} {f.get('min', '-∞')} ile {f.get('max', '∞')} arasında olmalı."
        return round(n, 6), None
    if t == "enum":
        opts = f["options"]
        hit = next((o for o in opts if str(v).strip().lower() == o.lower()), None)
        if hit is None and f.get("option_labels"):  # Türkçe etiketle de kabul (ör. "Hizmet")
            hit = next((k for k, lab in f["option_labels"].items() if str(v).strip().lower() == lab.lower()), None)
        return (hit, None) if hit else (None, f"{label} şunlardan biri olmalı: {', '.join(opts)}.")
    if t == "list":
        items = v if isinstance(v, list) else [v]
        bad = [x for x in items if x not in f["options"]]
        return (list(dict.fromkeys(items)), None) if not bad else (None, f"{label} geçersiz: {', '.join(map(str, bad))}.")
    if t == "date":
        try:
            return date.fromisoformat(str(v).strip()[:10]).isoformat(), None
        except ValueError:
            return None, f"{label} YYYY-AA-GG biçiminde tarih olmalı."
    return v, None


def validate(object_type: str, data: Any) -> Tuple[Dict[str, Any], List[str]]:
    """Nesneyi doğrular. Dönüş: (temiz nesne, hatalar). Hatalar boşsa nesne aktarılabilir."""
    spec = OBJECTS.get(object_type)
    if not spec:
        return {}, [f"Bilinmeyen nesne türü: {object_type}"]
    if not isinstance(data, dict):
        return {}, ["Nesne alan-değer biçiminde olmalı."]
    clean, errors = {}, []
    for f in spec["fields"]:
        v = data.get(f["key"])
        if v in (None, "", []):
            if f["required"]:
                errors.append(f"{f['label']} zorunlu.")
            continue
        if f["type"] == "lines":
            if not isinstance(v, list):
                errors.append(f"{f['label']} liste olmalı.")
                continue
            if len(v) > f.get("max_items", 200):
                errors.append(f"{f['label']} en fazla {f['max_items']} satır olabilir.")
                continue
            rows = []
            for i, row in enumerate(v, 1):
                rc, re_ = validate_fields(f["fields"], row, prefix=f"{i}. kalem: ")
                rows.append(rc)
                errors += re_
            clean[f["key"]] = rows
            continue
        val, err = _field(f, v, f["label"])
        if err:
            errors.append(err)
        else:
            clean[f["key"]] = val
    if object_type == "PARTNER" and clean.get("tax_number"):
        n = re.sub(r"\D", "", clean["tax_number"])
        kind = clean.get("kind")
        if kind == "COMPANY" and not vkn_ok(n):
            errors.append("VKN geçersiz (10 haneli vergi kimlik numarası olmalı).")
        elif kind == "PERSON" and not tckn_ok(n):
            errors.append("TCKN geçersiz.")
        clean["tax_number"] = n
    if object_type == "PARTNER" and clean.get("country"):
        clean["country"] = clean["country"].upper()
    return clean, errors


def validate_fields(fields: List[Dict[str, Any]], data: Any, prefix: str = "") -> Tuple[Dict[str, Any], List[str]]:
    if not isinstance(data, dict):
        return {}, [f"{prefix}alan-değer biçiminde olmalı."]
    clean, errors = {}, []
    for f in fields:
        v = data.get(f["key"])
        if v in (None, "", []):
            if f["required"]:
                errors.append(f"{prefix}{f['label']} zorunlu.")
            continue
        val, err = _field(f, v, f"{prefix}{f['label']}")
        if err:
            errors.append(err)
        else:
            clean[f["key"]] = val
    return clean, errors


def mask_pii(object_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """Kayıt/günlük için: şahıs carisinin TCKN'si maskelenir (KVKK); şirket VKN'si ticari bilgidir, açık kalır."""
    if object_type == "PARTNER" and data.get("kind") == "PERSON" and data.get("tax_number"):
        n = str(data["tax_number"])
        return {**data, "tax_number": n[:2] + "*" * max(0, len(n) - 4) + n[-2:]}
    return data
