"""
ADIM 12.2: ortak iş nesneleri (ürün kartı, cari, teklif/sipariş, görev, doküman) — sistemden bağımsız, sürümlü şema.

- Zorunlu alan, sayı (Türkçe biçim 1.250,50 dahil), seçenek (kod veya Türkçe etiket), tarih, e-posta, biçim denetimi.
- VKN (GİB algoritması) ve TCKN denetimi; şahıs TCKN'si kayıtlarda maskelenir (KVKK).
- Bilinmeyen alanlar atılır; sipariş kalemleri tek tek doğrulanır, hatalar satır numarasıyla.
"""
from app.services import business_objects as bo
from tests.test_workflow import world  # noqa: F401  (fikstür)


def _vkn(prefix: str) -> str:
    """9 haneden geçerli VKN üretir (algoritmanın kendisiyle değil, bağımsız hesapla)."""
    total = 0
    for i, c in enumerate(prefix):
        t = (int(c) + 9 - i) % 10
        if t:
            v = (t * pow(2, 9 - i)) % 9
            total += v if v else 9
    return prefix + str((10 - total % 10) % 10)


def test_catalog_lists_all_objects():
    codes = {o["code"] for o in bo.catalog()}
    assert codes == {"PRODUCT", "PARTNER", "ORDER", "TASK", "SUPPORT_TICKET", "DOCUMENT"}
    product = next(o for o in bo.catalog() if o["code"] == "PRODUCT")
    assert product["version"] == bo.VERSION and {"code", "name", "unit", "vat_rate"} <= {f["key"] for f in product["fields"]}


def test_product_validation():
    clean, errors = bo.validate("PRODUCT", {"name": "  El terminali  ", "type": "Stoklu ürün", "unit": "adet", "sale_price": "1.250,50",
                                             "purchase_price": 900, "vat_rate": "20", "barcode": "8690000000017", "uydurma": "atılır"})
    assert errors == []
    assert clean == {"name": "El terminali", "type": "STOCK", "unit": "Adet", "sale_price": 1250.5, "purchase_price": 900.0,
                     "vat_rate": 20.0, "barcode": "8690000000017"}
    _, errors = bo.validate("PRODUCT", {"type": "UÇAK", "unit": "Adet", "sale_price": "çok", "vat_rate": 150, "barcode": "x"})
    assert "Ürün adı zorunlu." in errors
    assert any("Tür şunlardan biri" in e for e in errors) and any("Satış fiyatı sayı" in e for e in errors)
    assert any("KDV oranı" in e and "arasında" in e for e in errors) and any("Barkod biçimi" in e for e in errors)
    assert bo.validate("YOK", {})[1] == ["Bilinmeyen nesne türü: YOK"]
    assert bo.validate("PRODUCT", "metin")[1] == ["Nesne alan-değer biçiminde olmalı."]


def test_partner_tax_numbers_and_pii():
    vkn = _vkn("123456789")
    clean, errors = bo.validate("PARTNER", {"kind": "COMPANY", "name": "ABC Makine Ltd. Şti.", "tax_number": vkn, "email": "satis@abc.com.tr",
                                             "country": "tr", "roles": ["CUSTOMER", "CUSTOMER", "SUPPLIER"]})
    assert errors == [] and clean["country"] == "TR" and clean["roles"] == ["CUSTOMER", "SUPPLIER"]
    bad_vkn = vkn[:-1] + str((int(vkn[-1]) + 1) % 10)
    assert "VKN geçersiz" in bo.validate("PARTNER", {"kind": "COMPANY", "name": "X", "tax_number": bad_vkn})[1][0]
    assert bo.tckn_ok("10000000146") and not bo.tckn_ok("10000000147") and not bo.tckn_ok("01234567890")
    clean, errors = bo.validate("PARTNER", {"kind": "Şahıs", "name": "Ayşe Yılmaz", "tax_number": "100 000 001 46", "email": "yanlis"})
    assert errors == ["E-posta geçerli bir e-posta değil."] and clean["tax_number"] == "10000000146"
    assert bo.mask_pii("PARTNER", clean)["tax_number"] == "10*******46"
    company = {"kind": "COMPANY", "tax_number": vkn}
    assert bo.mask_pii("PARTNER", company) == company  # şirket VKN'si ticari bilgi


def test_order_lines_validated_per_row():
    clean, errors = bo.validate("ORDER", {"direction": "SALE", "stage": "Teklif", "partner_ref": "ABC Makine", "date": "2026-11-02T10:00:00",
                                           "lines": [{"product_code": "ELT-01", "description": "El terminali", "quantity": 5, "unit_price": "12.500,00", "vat_rate": 20},
                                                     {"description": "", "quantity": -1, "unit_price": 10}]})
    assert clean["stage"] == "QUOTE" and clean["date"] == "2026-11-02" and clean["lines"][0]["unit_price"] == 12500.0
    assert "2. kalem: Açıklama zorunlu." in errors and any(e.startswith("2. kalem: Miktar") for e in errors)
    _, errors = bo.validate("ORDER", {"direction": "SALE", "stage": "ORDER", "partner_ref": "X", "lines": []})
    assert errors == ["Kalemler zorunlu."]
    _, errors = bo.validate("TASK", {"title": "Sayım", "due_date": "31.12.2026"})
    assert errors == ["Bitiş tarihi YYYY-AA-GG biçiminde tarih olmalı."]


def test_objects_api(client, world):
    h = world["member"]["h"]
    r = client.get("/api/v1/integrations/objects", headers=h)
    assert r.status_code == 200 and len(r.json()["objects"]) == 6
    r = client.post("/api/v1/integrations/objects/PRODUCT/validate", headers=h, json={"name": "Vida", "type": "SERVICE", "unit": "Saat"})
    assert r.json() == {"ok": True, "object": {"name": "Vida", "type": "SERVICE", "unit": "Saat"}, "errors": []}
    assert client.post("/api/v1/integrations/objects/YOK/validate", headers=h, json={}).status_code == 404
    assert client.get("/api/v1/integrations/objects").status_code == 401
