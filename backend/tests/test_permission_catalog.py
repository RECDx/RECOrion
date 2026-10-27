"""
İzin kataloğu ve roller (İSTEK #353).

- Veritabanındaki katalog ve sistem rolleri app/core/permission_catalog.py ile aynı; rollerdeki her kod katalogda.
- Müşteri RECDx'e ait rolü görmez ve atayamaz; RECDx görür.
- Ayrıntılı roller yalnızca kendi ekranlarını açar (Entegrasyon Yöneticisi, Finans, Uzman).
- "Şirket Yöneticisi" rolü atanınca kullanıcı şirket yöneticisi olur; son yönetici rolden alınamaz, pasife alınamaz.
- Kişisel erişim anahtarı token:manage ister.
"""
import uuid
from datetime import datetime, timedelta, timezone

import psycopg2.extras
import pytest

from app.core import permission_catalog as pc
from app.core.security import hash_password

PASSWORD = "Guclu-Test-Sifresi-2026"


def _one(db, sql, *params):
    with db.cursor() as cur:
        cur.execute(sql, params)
        return cur.fetchone()


def _insert(db, sql, *params):
    return _one(db, sql + " RETURNING id", *params)[0]


def _h(client, email):
    r = client.post("/api/v1/auth/login", json={"email": email, "password": PASSWORD})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.fixture(scope="module")
def w(db, client):
    tag = uuid.uuid4().hex[:8]
    t = _insert(db, "INSERT INTO tenants (slug, name, is_active, package_expiry_date) VALUES (%s, %s, TRUE, %s)",
                f"yetki_{tag}", f"Yetki {tag}", datetime.now(timezone.utc) + timedelta(days=365))
    hq = _one(db, "SELECT id FROM tenants WHERE slug = 'recdx_hq'")[0]
    out = {"t": t, "tag": tag, "admin": f"yonetici_{tag}@yetki-test.com.tr", "super": f"super_{tag}@recdx.com"}
    for email, tid, role in ((out["admin"], t, "COMPANY_ADMIN"), (out["super"], hq, "SUPER_ADMIN")):
        _insert(db, "INSERT INTO actors (tenant_id, actor_type, display_name, email, role, password_hash, status, extra_permissions) "
                    "VALUES (%s, 'HUMAN', %s, %s, %s, %s, 'IDLE', %s::jsonb)", tid, email, email, role, hash_password(PASSWORD),
                psycopg2.extras.Json([]))
    out["ah"] = _h(client, out["admin"])
    out["roles"] = {r["name"]: r for r in client.get("/api/v1/system/roles", headers=out["ah"]).json()}
    return out


def _user(client, w, name, role):
    email = f"{name}_{w['tag']}@yetki-test.com.tr"
    r = client.post(f"/api/v1/company/{w['t']}/users", headers=w["ah"], json={
        "display_name": name, "email": email, "password": PASSWORD, "role_id": w["roles"][role]["id"]})
    assert r.status_code == 200, r.text
    return r.json(), _h(client, email)


def test_catalog_matches_database(db):
    with db.cursor() as cur:
        cur.execute("SELECT code, module, name FROM system_permissions")
        rows = {c: (m, n) for c, m, n in cur.fetchall()}
        cur.execute("SELECT name, base_role, permissions FROM tenant_roles WHERE tenant_id IS NULL")
        roles = {n: (b, p) for n, b, p in cur.fetchall()}
    assert set(pc.CODES) <= set(rows)
    for code, module, name, _ in pc.PERMISSIONS:
        assert rows[code] == (module, name)
        assert module in pc.MODULES
    for r in pc.SYSTEM_ROLES:
        base, perms = roles[r["name"]]
        assert base == r.get("base_role")
        assert set(perms) == (set(pc.CODES) if r["permissions"] == ["*"] else set(r["permissions"]))
        assert set(r["permissions"]) <= set(pc.CODES) | {"*"}
    # Şirket Yöneticisi platforma özel izin almaz, müşteri izinlerinin tamamını alır
    assert set(roles["Şirket Yöneticisi"][1]) == set(pc.CUSTOMER_CODES)


def test_platform_role_hidden_from_customers(client, w):
    assert "Süper Yönetici (Platform Admin)" not in w["roles"]
    assert {"Şirket Yöneticisi", "Entegrasyon Yöneticisi", "Uzman Kullanıcı"} <= set(w["roles"])
    sh = _h(client, w["super"])
    staff = {r["name"]: r for r in client.get("/api/v1/system/roles", headers=sh).json()}
    platform = staff["Süper Yönetici (Platform Admin)"]
    # Müşteri yöneticisi RECDx rolünü kimliğini bilse de atayamaz
    r = client.post(f"/api/v1/company/{w['t']}/users", headers=w["ah"], json={
        "display_name": "Sızma", "email": f"sizma_{w['tag']}@yetki-test.com.tr", "password": PASSWORD, "role_id": platform["id"]})
    assert r.status_code == 404
    mods = client.get("/api/v1/system/permission-modules", headers=w["ah"]).json()
    assert [m["code"] for m in mods] == list(pc.MODULES)
    perms = client.get("/api/v1/system/permissions", headers=w["ah"]).json()
    assert {p["code"]: p["enforced"] for p in perms}["billing:topup"] is False
    assert all(p["module_name"] for p in perms)


def test_integration_manager_opens_only_integration_screens(client, w):
    u, h = _user(client, w, "bt", "Entegrasyon Yöneticisi")
    assert u["role"] == "Entegrasyon Yöneticisi"
    t = w["t"]
    assert client.get(f"/api/v1/company/{t}/mappings", headers=h).status_code == 200
    assert client.get(f"/api/v1/company/{t}/automations", headers=h).status_code == 200
    assert client.get(f"/api/v1/company/{t}/transfers", headers=h).status_code == 200
    assert client.put(f"/api/v1/company/{t}/manifesto", headers=h, json={"manifesto": "x"}).status_code == 403
    assert client.post(f"/api/v1/company/{t}/departments", headers=h, json={"name": "BT Deneme"}).status_code == 403
    assert client.get(f"/api/v1/company/{t}/dashboard", headers=h).status_code == 403
    assert client.get(f"/api/v1/company/{t}/credits", headers=h).status_code == 403
    me = client.get("/api/v1/auth/me", headers=h).json()
    assert me["role_name"] == "Entegrasyon Yöneticisi" and "mapping:manage" in me["permissions"]


def test_finance_sees_dashboard_with_costs_specialist_does_not(client, w):
    _, fh = _user(client, w, "finans", "Finans ve Raporlama Sorumlusu")
    r = client.get(f"/api/v1/company/{w['t']}/dashboard", headers=fh)
    assert r.status_code == 200, r.text
    assert r.json()["can_view_costs"] is True
    assert client.get(f"/api/v1/company/{w['t']}/credits", headers=fh).status_code == 200
    assert client.get(f"/api/v1/company/{w['t']}/mappings", headers=fh).status_code == 403

    u, uh = _user(client, w, "uzman", "Uzman Kullanıcı")
    assert u["role"] == "USER"
    assert client.get(f"/api/v1/company/{w['t']}/dashboard", headers=uh).status_code == 403
    assert client.post("/api/v1/me/personal-tokens", headers=uh, json={"name": "Claude"}).status_code != 403


def test_company_admin_role_and_last_admin_protection(client, db, w):
    u, uh = _user(client, w, "ikinciyonetici", "Şirket Yöneticisi")
    assert u["role"] == "COMPANY_ADMIN" and u["role_name"] == "Şirket Yöneticisi"
    assert client.get(f"/api/v1/company/{w['t']}/dashboard", headers=uh).status_code == 200

    admin_id = _one(db, "SELECT id FROM actors WHERE email = %s", w["admin"])[0]
    # İki yönetici varken biri Uzman'a alınabilir; kalan son yönetici alınamaz ve pasife alınamaz
    r = client.put(f"/api/v1/company/{w['t']}/users/{u['id']}", headers=w["ah"], json={"role_id": w["roles"]["Uzman Kullanıcı"]["id"]})
    assert r.status_code == 200, r.text
    assert r.json()["role"] == "USER"
    r = client.put(f"/api/v1/company/{w['t']}/users/{admin_id}", headers=w["ah"], json={"role_id": w["roles"]["Proje Yöneticisi"]["id"]})
    assert r.status_code == 400 and "Şirket Yöneticisi" in r.json()["detail"]
    r = client.put(f"/api/v1/company/{w['t']}/users/{admin_id}", headers=w["ah"], json={"status": "DISABLED"})
    assert r.status_code == 400


def test_role_permissions_are_exact(client, w):
    """Rol atanmış kullanıcı yalnızca rolündeki izinleri alır: denetçi iş adımı ekleyemez, anahtar oluşturamaz."""
    _, h = _user(client, w, "denetci", "Güvenlik ve Uyum Denetçisi")
    me = client.get("/api/v1/auth/me", headers=h).json()
    assert set(me["permissions"]) == set(w["roles"]["Güvenlik ve Uyum Denetçisi"]["permissions"])
    assert client.post("/api/v1/me/personal-tokens", headers=h, json={"name": "Claude"}).status_code == 403
    assert client.get(f"/api/v1/company/{w['t']}/dashboard", headers=h).status_code == 200
