"""Temel API duman testleri (test veritabanı üzerinde)."""


def test_health(client):
    r = client.get("/api/v1/health/")
    assert r.status_code == 200
    assert r.json()["services"]["postgres"] == "healthy"


def test_sectors_and_professions(client):
    sectors = client.get("/api/v1/sectors/").json()
    assert len(sectors) == 11

    k = client.get("/api/v1/professions/", params={"sector_code": "K"}).json()
    assert len(k) == 15

    everything = client.get("/api/v1/professions/", params={"limit": 500}).json()
    assert len(everything) == 184


def test_plans_listed(client):
    r = client.get("/api/v1/tenants/plans")
    assert r.status_code == 200
    assert {p["code"] for p in r.json()} == {"STARTER", "PRO", "ENTERPRISE"}


def test_models_listed(client):
    r = client.get("/api/v1/models/")
    assert r.status_code == 200
    assert len(r.json()) == 15


def test_login_rejects_wrong_password(client):
    r = client.post("/api/v1/auth/login", json={"email": "yok@ornek-sirket.com.tr", "password": "yanlis"})
    assert r.status_code == 401
