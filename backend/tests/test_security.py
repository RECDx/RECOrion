"""
Kimlik doğrulama, yetki, KVKK ayrımı ve denetim kaydı testleri.

Senaryo: iki müşteri şirketi (A ve B) ve bir RECDx süper admini.
Her test gerçek bir kötüye kullanım denemesini doğrular.
"""
import hashlib
import uuid
from datetime import datetime, timedelta, timezone

import psycopg2
import psycopg2.extras
import pytest

from app.core.security import hash_password

PASSWORD = "Guclu-Test-Sifresi-2026"


def _insert(db, sql, *params):
    with db.cursor() as cur:
        cur.execute(sql + " RETURNING id", params)
        return cur.fetchone()[0]


@pytest.fixture(scope="module")
def world(db):
    """Test şirketleri, kullanıcılar ve şirket B'ye ait içerik."""
    tag = uuid.uuid4().hex[:8]
    expiry = datetime.now(timezone.utc) + timedelta(days=365)
    pw = hash_password(PASSWORD)

    def tenant(name):
        return _insert(db, "INSERT INTO tenants (slug, name, is_active, package_expiry_date) VALUES (%s, %s, TRUE, %s)",
                       f"{name}_{tag}", f"{name} {tag}", expiry)

    def human(tenant_id, email, role, extra=None):
        return _insert(db, "INSERT INTO actors (tenant_id, actor_type, display_name, email, role, password_hash, status, extra_permissions) "
                           "VALUES (%s, 'HUMAN', %s, %s, %s, %s, 'IDLE', %s::jsonb)",
                       tenant_id, email, email, role, pw, psycopg2.extras.Json(extra or []))


    with db.cursor() as cur:
        cur.execute("SELECT id FROM tenants WHERE slug = 'recdx_hq'")
        hq = cur.fetchone()[0]

    a, b = tenant("sirket_a"), tenant("sirket_b")
    w = {
        "tag": tag, "hq": hq, "a": a, "b": b,
        "super": f"super_{tag}@recdx.com",
        "admin_a": f"admin_a_{tag}@a-sirket.com.tr",
        "user_a": f"user_a_{tag}@a-sirket.com.tr",
        "admin_b": f"admin_b_{tag}@b-sirket.com.tr",
        "sneaky_b": f"sneaky_b_{tag}@b-sirket.com.tr",
    }
    w["super_id"] = human(hq, w["super"], "SUPER_ADMIN")
    w["admin_a_id"] = human(a, w["admin_a"], "COMPANY_ADMIN")
    w["user_a_id"] = human(a, w["user_a"], "STANDARD_USER")
    w["admin_b_id"] = human(b, w["admin_b"], "COMPANY_ADMIN")
    # Müşteri kullanıcısına elle "*" ve system:admin verilmiş olsa bile süper admin olmamalı
    w["sneaky_b_id"] = human(b, w["sneaky_b"], "COMPANY_ADMIN", ["*", "system:admin"])

    w["agent_b"] = _insert(db, "INSERT INTO actors (tenant_id, actor_type, display_name, role, status) "
                               "VALUES (%s, 'AI_AGENT', 'Analist B', 'ANALYST', 'IDLE')", b)
    w["project_b"] = _insert(db, "INSERT INTO projects (tenant_id, slug, name, status) VALUES (%s, 'gizli', 'Gizli Proje', 'ACTIVE')", b)
    w["task_b"] = _insert(db, "INSERT INTO tasks (project_id, title, status) VALUES (%s, 'Gizli Görev', 'BACKLOG')", w["project_b"])
    return w


def login(client, email, password=PASSWORD, **extra):
    return client.post("/api/v1/auth/login", json={"email": email, "password": password, **extra})


def auth(client, email):
    r = login(client, email)
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


# ---------------------------------------------------------------------------
# Politika tablosu bütünlüğü
# ---------------------------------------------------------------------------
def test_every_api_route_has_explicit_policy():
    from app.core.access_policy import POLICY
    from app.main import app

    routes = {
        (method.upper(), path)
        for path, ops in app.openapi()["paths"].items() if path.startswith("/api/v1")
        for method in ops
    }
    missing = sorted(routes - set(POLICY))
    stale = sorted(set(POLICY) - routes)
    assert not missing, f"Politika tablosunda tanımsız uçlar: {missing}"
    assert not stale, f"Politika tablosunda artık var olmayan uçlar: {stale}"


# ---------------------------------------------------------------------------
# Giriş
# ---------------------------------------------------------------------------
def test_protected_endpoints_require_token(client, world):
    for path in ["/api/v1/tenants/", f"/api/v1/company/{world['a']}/users", "/api/v1/models/",
                 f"/api/v1/chat/project/{world['project_b']}", f"/api/v1/memory/?tenant_id={world['b']}"]:
        assert client.get(path).status_code == 401, path


def test_invalid_token_rejected(client):
    r = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer sahte.token.degeri"})
    assert r.status_code == 401


def test_login_returns_token_and_profile(client, world):
    r = login(client, world["admin_a"])
    assert r.status_code == 200
    body = r.json()
    assert body["access_token"] and body["tenant_id"] == str(world["a"])
    assert body["is_super_admin"] is False
    me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {body['access_token']}"})
    assert me.status_code == 200 and me.json()["email"] == world["admin_a"]


def test_login_does_not_match_by_name_or_slug(client, world):
    # Eski kod e-posta yerine şirket adı/slug ile de eşleştiriyordu
    assert login(client, f"sirket_a_{world['tag']}").status_code == 401


def test_legacy_sha256_password_is_upgraded_on_login(client, db, world):
    email = f"legacy_{world['tag']}@a-sirket.com.tr"
    legacy_hash = hashlib.sha256(f"recorion_tenant_salt_2026_{PASSWORD}".encode()).hexdigest()
    _insert(db, "INSERT INTO actors (tenant_id, actor_type, display_name, email, role, password_hash, status) "
                "VALUES (%s, 'HUMAN', 'Eski Kullanıcı', %s, 'STANDARD_USER', %s, 'IDLE')", world["a"], email, legacy_hash)
    assert login(client, email).status_code == 200
    with db.cursor() as cur:
        cur.execute("SELECT password_hash FROM actors WHERE email = %s", (email,))
        assert cur.fetchone()[0].startswith("$argon2")


def test_login_locks_after_repeated_failures(client, world):
    email = f"kilit_{world['tag']}@a-sirket.com.tr"
    for _ in range(5):
        assert login(client, email, "yanlis").status_code == 401
    assert login(client, email, "yanlis").status_code == 429


def test_model_catalog_only_for_super_admin(client, world):
    """#349: gerçek EVREN model kataloğunu müşteri göremez (RECAi adlarını görür: /company/{id}/recai)."""
    r = client.get("/api/v1/models/", headers=auth(client, world["admin_a"]))
    assert r.status_code == 403
    r = client.get(f"/api/v1/company/{world['a']}/recai", headers=auth(client, world["admin_a"]))
    assert r.status_code == 200 and {t["code"] for t in r.json()["tiers"]} == {"MERGEN", "HIZLI", "DERIN"}
    assert all(t["model_code"] in ("MERGEN", "HIZLI", "DERIN") for t in r.json()["tiers"])  # kod RECAi kodu, gerçek model değil


# ---------------------------------------------------------------------------
# Şirket izolasyonu
# ---------------------------------------------------------------------------
def test_company_admin_cannot_access_other_company(client, world):
    h = auth(client, world["admin_a"])
    assert client.get(f"/api/v1/company/{world['a']}/users", headers=h).status_code == 200
    assert client.get(f"/api/v1/company/{world['b']}/users", headers=h).status_code == 403
    assert client.get(f"/api/v1/projects/?tenant_id={world['b']}", headers=h).status_code == 403
    assert client.get(f"/api/v1/chat/history/{world['task_b']}", headers=h).status_code == 403
    assert client.post("/api/v1/memory/search", headers=h,
                       json={"tenant_id": str(world["b"]), "query": "gizli"}).status_code == 403


def test_company_admin_cannot_use_platform_endpoints(client, world):
    h = auth(client, world["admin_a"])
    assert client.get("/api/v1/tenants/", headers=h).status_code == 403
    assert client.post("/api/v1/sectors/", headers=h, json={"code": "Z", "name": "Sahte"}).status_code == 403


def test_customer_wildcard_permission_does_not_grant_super_admin(client, world):
    h = auth(client, world["sneaky_b"])
    assert client.get("/api/v1/tenants/", headers=h).status_code == 403
    assert client.get(f"/api/v1/company/{world['a']}/users", headers=h).status_code == 403


def test_standard_user_cannot_manage_users(client, world):
    h = auth(client, world["user_a"])
    r = client.post(f"/api/v1/company/{world['a']}/users", headers=h,
                    json={"display_name": "Yeni", "email": f"yeni_{world['tag']}@a-sirket.com.tr", "password": PASSWORD})
    assert r.status_code == 403


def test_admin_cannot_grant_permissions_they_do_not_have(client, world):
    h = auth(client, world["admin_a"])
    r = client.put(f"/api/v1/company/{world['a']}/users/{world['user_a_id']}", headers=h,
                   json={"extra_permissions": ["system:admin"]})
    assert r.status_code == 403


def test_profile_takeover_blocked(client, world):
    h = auth(client, world["admin_a"])
    r = client.put(f"/api/v1/auth/profile/{world['admin_b_id']}", headers=h,
                   json={"display_name": "Ele Geçirildi", "email": "saldirgan@kotu.com", "new_password": "YeniSifre123"})
    assert r.status_code == 403
    assert client.get(f"/api/v1/auth/profile/{world['admin_b_id']}", headers=h).status_code == 403


# ---------------------------------------------------------------------------
# KVKK: süper admin yönetim verisine erişir, içeriğe erişemez
# ---------------------------------------------------------------------------
def test_super_admin_can_manage_customer_company(client, world):
    h = auth(client, world["super"])
    assert client.get("/api/v1/tenants/", headers=h).status_code == 200
    assert client.get(f"/api/v1/company/{world['b']}/users", headers=h).status_code == 200
    assert client.get(f"/api/v1/company/{world['b']}/ai-agents", headers=h).status_code == 200
    assert client.get(f"/api/v1/tenants/{world['b']}/details", headers=h).status_code == 200


def test_super_admin_cannot_read_customer_content(client, world):
    h = auth(client, world["super"])
    denied = [
        client.get(f"/api/v1/projects/?tenant_id={world['b']}", headers=h),
        client.get(f"/api/v1/projects/{world['project_b']}/tasks", headers=h),
        client.get(f"/api/v1/chat/project/{world['project_b']}", headers=h),
        client.get(f"/api/v1/chat/history/{world['task_b']}", headers=h),
        client.get(f"/api/v1/memory/?tenant_id={world['b']}", headers=h),
        client.post("/api/v1/memory/search", headers=h, json={"tenant_id": str(world["b"]), "query": "x"}),
        client.get(f"/api/v1/company/{world['b']}/ai-agents/{world['agent_b']}/documents", headers=h),
    ]
    for r in denied:
        assert r.status_code == 403, r.request.url
        assert "KVKK" in r.json()["detail"]


# ---------------------------------------------------------------------------
# Denetim kaydı
# ---------------------------------------------------------------------------
def test_mutations_are_audited_and_log_is_append_only(client, db, world):
    h = auth(client, world["admin_a"])
    r = client.post(f"/api/v1/company/{world['a']}/departments", headers=h, json={"name": f"Denetim {world['tag']}"})
    assert r.status_code == 201, r.text

    with db.cursor() as cur:
        cur.execute(
            "SELECT action, payload->>'status' FROM audit_events WHERE actor_id = %s AND tenant_id = %s ORDER BY created_at DESC LIMIT 1",
            (world["admin_a_id"], world["a"]),
        )
        action, status = cur.fetchone()
    assert action == "POST /api/v1/company/{tenant_id}/departments" and status == "201"

    for sql in ("UPDATE audit_events SET action = 'x'", "DELETE FROM audit_events", "TRUNCATE audit_events"):
        with pytest.raises(psycopg2.Error):
            with db.cursor() as cur:
                cur.execute(sql)


def test_failed_login_is_audited(client, db, world):
    login(client, f"denetim_{world['tag']}@a-sirket.com.tr", "yanlis")
    with db.cursor() as cur:
        cur.execute("SELECT count(*) FROM audit_events WHERE action = 'POST /api/v1/auth/login' AND payload->>'status' = '401'")
        assert cur.fetchone()[0] >= 1


# ---------------------------------------------------------------------------
# SSRF
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("url", [
    "http://127.0.0.1/", "http://localhost:8000/api/v1/health", "http://postgres:5432/",
    "http://redis:6379/", "http://169.254.169.254/latest/meta-data/", "http://10.0.0.5/", "file:///etc/passwd",
    "http://[::1]/",
])
def test_internal_urls_are_blocked(url):
    import asyncio
    from app.core.net import UnsafeURLError, assert_public_url

    with pytest.raises(UnsafeURLError):
        asyncio.run(assert_public_url(url))


def test_policy_matches_most_specific_template():
    from app.core.access_policy import match_rule

    assert match_rule("GET", "/api/v1/tenants/plans")[0] == "/api/v1/tenants/plans"
    assert match_rule("GET", "/api/v1/health/")[0] == "/api/v1/health/"
    tid = "8e2b6b5e-1111-4222-8333-444455556666"
    assert match_rule("GET", f"/api/v1/company/{tid}/job-titles/system-templates")[0].endswith("/job-titles/system-templates")
    assert match_rule("POST", f"/api/v1/company/{tid}/ai-agents/deep-search-sector-title")[0].endswith("/ai-agents/deep-search-sector-title")
    # Tanımsız uç varsayılan olarak yalnızca süper admine açık
    assert match_rule("GET", "/api/v1/olmayan-uc")[1].kind == "SUPER_ADMIN"
