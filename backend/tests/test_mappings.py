"""
ADIM 12.3: eşleme stüdyosu (sahte Odoo 20 JSON-2 sunucusu; gerçek ağa çıkılmaz).

- RECDx hazır eşlemesinden şirket eşlemesi (taslak); hedefin kendi alan tanımlarıyla denetim (olmayan alan, geçersiz seçenek,
  yalnız Odoo dönüşümü, eşlenmemiş zorunlu alan; hesaplanan/varsayılanı olan zorunlu alanlar sayılmaz).
- Deneme YAZMAZ: yalnızca alan tanımı ve arama; birim/vergi/kategori aranır, stok koduyla mevcut kayıt bulunursa "güncelle".
- Onay: bu sürümün hatasız denemesi şart; kural değişince taslağa döner, sürüm artar.
- RECAi önerisi: hedefte olmayan alana yazan kurallar atılır.
- Yetki: yalnızca integration:manage; ekip üyesi ve RECDx personeli (KVKK) erişemez.
"""
import json
import uuid

import httpx
import pytest

from app.integrations import base, odoo
from tests.test_integrations import _super
from tests.test_workflow import world  # noqa: F401  (fikstür)

KEY = "odoo20-sahte-anahtar"
FIELDS = {
    "product.template": {
        "name": {"string": "Ad", "type": "char", "required": True, "depends": []},
        "default_code": {"string": "İç referans", "type": "char"},
        "type": {"string": "Tür", "type": "selection", "required": True, "selection": [["consu", "Mal"], ["service", "Hizmet"], ["combo", "Kombo"]]},
        "is_storable": {"string": "Stok takibi", "type": "boolean"},
        "uom_id": {"string": "Birim", "type": "many2one", "relation": "uom.uom", "required": True},
        "list_price": {"string": "Satış fiyatı", "type": "float"}, "standard_price": {"string": "Maliyet", "type": "float"},
        "barcode": {"string": "Barkod", "type": "char"},
        "categ_id": {"string": "Kategori", "type": "many2one", "relation": "product.category"},
        "taxes_id": {"string": "Satış vergileri", "type": "many2many", "relation": "account.tax"},
        "supplier_taxes_id": {"string": "Alış vergileri", "type": "many2many", "relation": "account.tax"},
        "description_sale": {"string": "Satış açıklaması", "type": "text"},
        "invoice_policy": {"string": "Faturalama", "type": "selection", "required": True, "depends": ["type"], "selection": [["order", "Sipariş"]]},
        "product_variant_ids": {"string": "Varyantlar", "type": "one2many", "required": True, "relation": "product.product"},
        "create_date": {"string": "Oluşturma", "type": "datetime", "readonly": True},
    },
}


@pytest.fixture
def fake_odoo20(monkeypatch):
    log = []

    def handler(req: httpx.Request) -> httpx.Response:
        assert req.url.host == "odoo20.example" and req.headers.get("authorization") == f"bearer {KEY}"
        _, _, _, model, method = req.url.path.split("/")
        body = json.loads(req.content)
        log.append((model, method, body))
        if method == "fields_get":
            return httpx.Response(200, headers={"content-type": "application/json"}, json=FIELDS.get(model, {}))
        if method == "default_get":
            return httpx.Response(200, headers={"content-type": "application/json"}, json={"type": "consu"} if "type" in body["fields"] else {})
        if method == "search_read" and not body["domain"]:  # RECAi için örnek değerler (birim, vergi listesi)
            rows = {"uom.uom": [{"id": 1, "name": "Units"}, {"id": 16, "name": "kg"}],
                    "account.tax": [{"id": 7, "name": "KDV %20", "amount": 20.0, "type_tax_use": "sale"}]}.get(model, [])
            return httpx.Response(200, headers={"content-type": "application/json"}, json=rows)
        if method == "search_read":
            (fld, op, val), *rest = body["domain"]
            table = {("uom.uom", "name"): {"units": 1, "kg": 16}, ("account.tax", "amount"): {20.0: 7 if rest == [["type_tax_use", "=", "sale"]] else 8},
                     ("product.category", "name"): {"goods": 1}, ("product.template", "default_code"): {"var-01": 55}}
            hit = table.get((model, fld), {}).get(val.lower() if isinstance(val, str) else val)
            return httpx.Response(200, headers={"content-type": "application/json"}, json=[{"id": hit}] if hit else [])
        raise AssertionError(f"Denemede yazma/beklenmeyen çağrı: {model}.{method}")
    monkeypatch.setattr(base, "TRANSPORT", httpx.MockTransport(handler))
    odoo._styles.clear()
    return log


def _seed(client):
    from app.db.session import AsyncSessionLocal
    from app.services.mappings import ensure_templates

    async def go():
        async with AsyncSessionLocal() as s:
            return await ensure_templates(s)
    return client.portal.call(go)


def _odoo_conn(client, w):
    r = client.post(f"/api/v1/company/{w['tenant']}/integrations", headers=w["admin"]["h"], json={
        "connector": "odoo", "name": f"Test Odoo {uuid.uuid4().hex[:4]}", "config": {"url": "https://odoo20.example", "db": "sirket"},
        "secrets": {"api_key": KEY}})
    assert r.status_code == 201, r.text
    return r.json()["id"]


def test_mapping_from_template_check_dry_run_approve(client, db, world, fake_odoo20):
    w = world
    h = w["admin"]["h"]
    _seed(client)
    base_url = f"/api/v1/company/{w['tenant']}/mappings"
    tpls = client.get(f"{base_url}/templates?connector=odoo", headers=h).json()
    assert {t["code"] for t in tpls} >= {"odoo_product", "odoo_partner", "odoo_sale_quote", "odoo_purchase_order", "odoo_task"}
    product_tpl = next(t for t in tpls if t["code"] == "odoo_product")
    cid = _odoo_conn(client, w)

    # Yetki
    assert client.get(base_url, headers=w["member"]["h"]).status_code == 403
    assert client.get(base_url, headers=_super(client, db)).status_code == 403  # KVKK

    r = client.post(base_url, headers=h, json={"connection_id": cid, "object_type": "PRODUCT", "name": "Ürün kartı → Odoo",
                                               "template_id": product_tpl["id"]})
    assert r.status_code == 201, r.text
    m = r.json()
    assert m["status"] == "DRAFT" and m["target"] == {"model": "product.template"} and m["match"] == {"source": "code", "target": "default_code"}
    mid = m["id"]

    fields = client.get(f"/api/v1/company/{w['tenant']}/integrations/{cid}/target-fields?model=product.template", headers=h).json()
    by = {f["name"]: f for f in fields}
    assert by["uom_id"]["required"] is True and by["name"]["required"] is True
    assert by["type"]["required"] is False  # varsayılanı var
    assert by["invoice_policy"]["required"] is False and by["product_variant_ids"]["required"] is False  # hesaplanan / satır listesi
    assert "create_date" not in by  # salt okunur

    c = client.post(f"{base_url}/{mid}/check", headers=h).json()
    assert c["ok"] is True and c["errors"] == [], c
    assert client.post(f"{base_url}/{mid}/approve", headers=h).status_code == 409  # denemeden onay yok

    d = client.post(f"{base_url}/{mid}/dry-run", headers=h, json={}).json()
    assert d["ok"] is True, d
    v = d["values"]
    assert v["type"] == "consu" and v["is_storable"] is True and v["uom_id"] == 1 and v["categ_id"] == 1
    assert v["taxes_id"] == [[6, 0, [7]]] and v["supplier_taxes_id"] == [[6, 0, [8]]] and v["list_price"] == 12500.0
    assert d["action"] == "CREATE" and d["existing_id"] is None
    assert not any(meth in ("create", "write") for _, meth, _ in fake_odoo20)  # deneme yazmadı

    sample = {"code": "VAR-01", "name": "Var olan ürün", "type": "SERVICE", "unit": "Kg", "vat_rate": 10}
    d = client.post(f"{base_url}/{mid}/dry-run", headers=h, json={"sample": sample}).json()
    assert d["action"] == "UPDATE" and d["existing_id"] == 55 and d["values"]["uom_id"] == 16 and d["values"]["type"] == "service"
    assert any("Satış vergileri" in x and "bulunamadı" in x for x in d["warnings"])  # %10 vergi yok: isteğe bağlı alan boş

    bad = client.post(f"{base_url}/{mid}/dry-run", headers=h, json={"sample": {"code": "X", "name": "Birimsiz", "type": "STOCK", "unit": "Ton"}}).json()
    assert bad["ok"] is False and any("Birim: 'Ton'" in e for e in bad["errors"])  # zorunlu ilişki bulunamadı

    r = client.post(f"{base_url}/{mid}/dry-run", headers=h, json={}).json()
    assert r["ok"]
    a = client.post(f"{base_url}/{mid}/approve", headers=h)
    assert a.status_code == 200 and a.json()["status"] == "ACTIVE"

    rules = a.json()["rules"] + [{"target": "barcode", "transform": "const", "params": {"value": "1"}}]
    u = client.put(f"{base_url}/{mid}", headers=h, json={"rules": rules}).json()
    assert u["status"] == "DRAFT" and u["version"] == 2
    c = client.post(f"{base_url}/{mid}/check", headers=h).json()
    assert any("iki kez" in e for e in c["errors"])
    assert client.post(f"{base_url}/{mid}/approve", headers=h).status_code == 409  # son deneme eski sürümde


def test_mapping_check_catches_wrong_fields(client, world, fake_odoo20):
    w = world
    h = w["admin"]["h"]
    cid = _odoo_conn(client, w)
    base_url = f"/api/v1/company/{w['tenant']}/mappings"
    rules = [{"target": "name", "transform": "copy", "source": "name"},
             {"target": "tax_id", "transform": "copy", "source": "vat_rate"},  # Odoo 20'de yok
             {"target": "type", "transform": "map", "source": "type", "params": {"values": {"STOCK": "product"}}},  # eski sürüm değeri
             {"target": "barcode", "transform": "copy", "source": "uydurma"},
             {"target": "description_sale", "transform": "template", "params": {"text": "{name} {yok}"}}]
    m = client.post(base_url, headers=h, json={"connection_id": cid, "object_type": "PRODUCT", "name": "Elle eşleme",
                                               "target": {"model": "product.template"}, "rules": rules}).json()
    c = client.post(f"{base_url}/{m['id']}/check", headers=h).json()
    errs = " | ".join(c["errors"])
    assert "Hedefte 'tax_id' alanı yok" in errs and "product hedefte geçerli değil" in errs and "kaynak alan geçersiz (uydurma)" in errs
    assert "{yok} nesnede yok" in errs
    assert any("uom_id" in x for x in c["warnings"])  # zorunlu birim eşlenmedi
    assert client.post(base_url, headers=h, json={"connection_id": cid, "object_type": "PRODUCT", "name": "Hatalı",
                                                  "target": {"model": "product.template"},
                                                  "rules": [{"target": "name", "transform": "sihir"}]}).status_code == 422
    assert client.post(base_url, headers=h, json={"connection_id": cid, "object_type": "YOK", "name": "Hatalı",
                                                  "target": {"model": "product.template"}}).status_code == 422


def test_recai_mapping_suggestion_drops_invented_fields(client, world, fake_odoo20, monkeypatch):
    from app.services.evren_client import ChatResult, evren_client

    w = world
    cid = _odoo_conn(client, w)
    seen = []

    async def chat(model_code, messages, **kw):
        seen.append(messages[-1]["content"])
        return ChatResult(json.dumps({"rules": [
            {"target": "name", "transform": "copy", "source": "name"},
            {"target": "uom_id", "transform": "lookup", "source": "unit", "params": {"fields": ["name"], "values": {"Adet": ["Units"]}}},
            {"target": "hayali_alan", "transform": "copy", "source": "code"}],
            "match": {"source": "code", "target": "default_code"}, "notes": "Birim Odoo'da aranır."}), None, 800, 200, {})
    monkeypatch.setattr(evren_client, "chat", chat)
    r = client.post(f"/api/v1/company/{w['tenant']}/mappings/suggest", headers=w["admin"]["h"],
                    json={"connection_id": cid, "object_type": "PRODUCT", "target": {"model": "product.template"}})
    assert r.status_code == 200, r.text
    d = r.json()
    assert [x["target"] for x in d["rules"]] == ["name", "uom_id"] and d["dropped"] == 1 and d["errors"] == []
    assert "uom_id: Birim [many2one, zorunlu, ilişki uom.uom]" in seen[0] and "KAYNAK ALANLARI" in seen[0]
    assert "uom.uom:" in seen[0]  # hedefteki örnek birimler verildi


def test_mcp_target_mapping_uses_tool_schema(client, world, monkeypatch):
    """MCP aracına eşleme: alanlar aracın giriş şemasından; arama (lookup) kullanılamaz."""
    from app.integrations.base import WRITE, Tool
    from app.services import tool_gateway

    async def tools(conn):
        return [Tool("create_issue", "Kayıt açar", {"type": "object", "properties": {
            "title": {"type": "string", "description": "Başlık"}, "priority": {"type": "integer", "enum": [1, 2, 3]},
            "due": {"type": "string"}}, "required": ["title"]}, WRITE, None)]
    monkeypatch.setattr(tool_gateway, "connection_tools", tools)
    w = world
    h = w["admin"]["h"]
    conn = client.post(f"/api/v1/company/{w['tenant']}/integrations", headers=h, json={
        "connector": "mcp", "name": f"İş takibi {uuid.uuid4().hex[:4]}", "config": {"url": "https://mcp.example/mcp"}, "secrets": {"token": "t"}}).json()
    base_url = f"/api/v1/company/{w['tenant']}/mappings"
    m = client.post(base_url, headers=h, json={"connection_id": conn["id"], "object_type": "TASK", "name": "Görev → iş takibi",
                                               "target": {"tool": "create_issue"}, "rules": [
                                                   {"target": "title", "transform": "copy", "source": "title"},
                                                   {"target": "priority", "transform": "map", "source": "priority", "params": {"values": {"LOW": 1, "NORMAL": 2, "HIGH": 3}}},
                                                   {"target": "due", "transform": "lookup", "source": "due_date"}]}).json()
    c = client.post(f"{base_url}/{m['id']}/check", headers=h).json()
    assert c["errors"] == ["'due': 'lookup' yalnızca Odoo bağlantılarında kullanılabilir."]
    rules = [r for r in m["rules"] if r["target"] != "due"] + [{"target": "due", "transform": "copy", "source": "due_date"}]
    client.put(f"{base_url}/{m['id']}", headers=h, json={"rules": rules})
    d = client.post(f"{base_url}/{m['id']}/dry-run", headers=h, json={}).json()
    assert d["ok"] is True and d["values"] == {"title": "RECOrion Test: depo sayımı hazırlığı", "priority": 3, "due": "2026-11-15"}
