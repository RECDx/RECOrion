"""
Paket tanımında Odoo ürün seçimi (Odoo #269). Odoo'ya gerçek çağrı yapılmaz.
"""
import uuid

import pytest

from app.core.security import hash_password
from app.services.odoo_service import OdooService, OdooUnavailable

PASSWORD = "Odoo-Urun-Testi-2026"
PRODUCTS = [{"id": 31, "name": "RECOrion - Profesyonel Paketi", "code": None, "list_price": 39900.0, "currency": "TRY", "type": "consu"}]


def _exec(db, sql, *params):
    with db.cursor() as cur:
        cur.execute(sql, params)
        return cur.fetchone() if cur.description else None


@pytest.fixture(scope="module")
def super_headers(client, db):
    hq = _exec(db, "SELECT id FROM tenants WHERE slug = 'recdx_hq'")[0]
    email = f"odoo_super_{uuid.uuid4().hex[:8]}@recdx.com"
    _exec(db, "INSERT INTO actors (tenant_id, actor_type, display_name, email, role, password_hash, status) "
              "VALUES (%s, 'HUMAN', 'Odoo Super', %s, 'SUPER_ADMIN', %s, 'IDLE')", hq, email, hash_password(PASSWORD))
    r = client.post("/api/v1/auth/login", json={"email": email, "password": PASSWORD})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.fixture
def fake_odoo(monkeypatch):
    calls = []

    def list_products(search=None, product_ids=None, limit=200):
        calls.append((search, product_ids))
        rows = PRODUCTS
        if product_ids:
            rows = [p for p in rows if p["id"] in product_ids]
        return rows

    monkeypatch.setattr(OdooService, "list_products", staticmethod(list_products))
    return calls


def _plan_payload(**extra):
    return {"code": f"T{uuid.uuid4().hex[:6]}", "name": "Test Paketi", "monthly_price": 100, "currency": "TRY",
            "max_humans": 1, "max_agents": 1, "max_projects": 1, "monthly_credits": 10, "storage_gb": 1,
            "allowed_models": [], "features": {}, "can_create_custom_titles": False, "is_active": False, **extra}


def test_products_require_super_admin(client):
    assert client.get("/api/v1/tenants/odoo/products").status_code == 401


def test_products_listed(client, super_headers, fake_odoo):
    r = client.get("/api/v1/tenants/odoo/products?search=RECOrion", headers=super_headers)
    assert r.status_code == 200 and r.json()[0]["id"] == 31
    assert fake_odoo[-1][0] == "RECOrion"


def test_plan_product_is_validated(client, db, super_headers, fake_odoo):
    assert client.post("/api/v1/tenants/plans", json=_plan_payload(odoo_product_id=999), headers=super_headers).status_code == 400
    r = client.post("/api/v1/tenants/plans", json=_plan_payload(odoo_product_id=31), headers=super_headers)
    assert r.status_code == 200, r.text
    plan = r.json()
    update = {k: v for k, v in _plan_payload().items() if k != "code"}
    assert client.put(f"/api/v1/tenants/plans/{plan['id']}", json={**update, "odoo_product_id": 999}, headers=super_headers).status_code == 400
    r = client.put(f"/api/v1/tenants/plans/{plan['id']}", json={**update, "odoo_product_id": None}, headers=super_headers)
    assert r.status_code == 200 and r.json()["odoo_product_id"] is None
    _exec(db, "DELETE FROM plans WHERE id = %s", plan["id"])


def test_odoo_down_returns_503(client, super_headers, monkeypatch):
    def down(*a, **k):
        raise OdooUnavailable("Odoo bağlantısı kurulamadı.")
    monkeypatch.setattr(OdooService, "list_products", staticmethod(down))
    assert client.get("/api/v1/tenants/odoo/products", headers=super_headers).status_code == 503
