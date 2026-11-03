"""
İSTEK: şirketin resmi logosu.

- Web başvurusunda logo eklenir (data URL); uygun olmayan görsel başvuruyu e-posta kodu harcanmadan reddeder.
- Şirket yöneticisi Şirket Yönetimi'nden, RECDx süper yöneticisi Ana Merkez'den yükler/kaldırır; diğer kullanıcılar yapamaz.
- Görsel 512 px PNG'ye çevrilir; SVG, bozuk dosya ve 2 MB üstü reddedilir.
- Logo herkese açık adresten (sürümlü) gösterilir; oturum bilgisinde, şirket listesi ve detayında adresi var.
"""
import base64
import io

import pytest
from PIL import Image

from app.services import storage
from tests.test_lifecycle import (  # noqa: F401  (fikstür)
    PASSWORD, _exec, code_from_outbox, purchase_payload, super_headers, tag,
)
from tests.test_workflow import world  # noqa: F401  (fikstür)


def png(w=900, h=300, fmt="PNG", color=(200, 30, 30, 255)):
    img = Image.new("RGBA" if fmt != "JPEG" else "RGB", (w, h), color if fmt != "JPEG" else color[:3])
    buf = io.BytesIO()
    img.save(buf, format=fmt)
    return buf.getvalue()


@pytest.fixture
def store(monkeypatch):
    objects = {}

    async def put_object(key, data, content_type=None):
        objects[key] = data

    async def get_object(key):
        if key not in objects:
            raise storage.StorageError("yok")
        return objects[key]

    async def delete_object(key):
        objects.pop(key, None)

    monkeypatch.setattr(storage, "put_object", put_object)
    monkeypatch.setattr(storage, "get_object", get_object)
    monkeypatch.setattr(storage, "delete_object", delete_object)
    return objects


def test_company_admin_and_super_admin_manage_logo(client, db, world, super_headers, store):
    w, tid = world, world["tenant"]
    url = f"/api/v1/company/{tid}/logo"
    up = lambda h, data, name="logo.png", ct="image/png": client.put(url, headers=h, files={"file": (name, data, ct)})  # noqa: E731

    # Yetki: uzman ve başka şirketin kullanıcısı yükleyemez
    assert up(w["member"]["h"], png()).status_code == 403
    # Uygun olmayan dosyalar
    svg = b'<svg xmlns="http://www.w3.org/2000/svg"><script>alert(1)</script></svg>'
    assert up(w["admin"]["h"], svg, "logo.svg", "image/svg+xml").status_code == 400
    assert up(w["admin"]["h"], b"bozuk-dosya", "logo.png").status_code == 400
    assert up(w["admin"]["h"], png(8, 8)).status_code == 400
    big = b"\x89PNG" + b"0" * (2 * 1024 * 1024 + 10)
    assert "2 MB" in up(w["admin"]["h"], big).json()["detail"]

    # Şirket yöneticisi yükler: 512 px PNG'ye çevrilir, herkese açık adresten gösterilir
    r = up(w["admin"]["h"], png(fmt="JPEG"), "logo.jpg", "image/jpeg")
    assert r.status_code == 200, r.text
    logo_url = r.json()["logo_url"]
    assert logo_url.startswith(f"/api/v1/public/tenant-logo/{tid}?v=")
    img = client.get(logo_url)
    assert img.status_code == 200 and img.headers["content-type"] == "image/png"
    assert "immutable" in img.headers["cache-control"] and img.headers["x-content-type-options"] == "nosniff"
    assert Image.open(io.BytesIO(img.content)).size == (512, 171)

    # Oturum bilgisi ve şirket detayında adres var
    assert client.get("/api/v1/auth/me", headers=w["member"]["h"]).json()["tenant_logo_url"] == logo_url
    assert client.get(f"/api/v1/tenants/{tid}/details", headers=w["admin"]["h"]).json()["tenant"]["logo_url"] == logo_url

    # Ana Merkez: listede görünür, süper yönetici değiştirir ve kaldırır
    row = next(t for t in client.get("/api/v1/tenants", headers=super_headers).json() if t["id"] == tid)
    assert row["logo_url"] == logo_url
    r = up(super_headers, png(300, 300, color=(0, 0, 200, 128)))
    assert r.status_code == 200 and r.json()["logo_url"]
    assert client.delete(url, headers=w["member"]["h"]).status_code == 403
    assert client.delete(url, headers=super_headers).json()["logo_url"] is None
    assert client.get(f"/api/v1/public/tenant-logo/{tid}").status_code == 404
    assert client.get("/api/v1/auth/me", headers=w["admin"]["h"]).json()["tenant_logo_url"] is None
    assert not store


def test_registration_with_logo(client, db, tag, store):
    email = f"logo_{tag}@deneme-sirket.com.tr"
    assert client.post("/api/v1/tenants/purchase-request/send-code", json={"email": email}).status_code == 200
    code = code_from_outbox(email)

    # Uygun olmayan logo başvuruyu reddeder; kod harcanmaz
    bad = "data:image/svg+xml;base64," + base64.b64encode(b"<svg></svg>").decode()
    r = client.post("/api/v1/tenants/purchase-request", json=purchase_payload(email, code, logo_data_url=bad))
    assert r.status_code == 400 and "PNG" in r.json()["detail"]
    assert client.post("/api/v1/tenants/purchase-request", json=purchase_payload(email, code, logo_data_url="data:text/plain,abc")).status_code == 400

    good = "data:image/png;base64," + base64.b64encode(png(400, 400)).decode()
    r = client.post("/api/v1/tenants/purchase-request", json=purchase_payload(email, code, logo_data_url=good))
    assert r.status_code == 200, r.text
    tenant_id, = _exec(db, "SELECT tenant_id FROM tenant_leads WHERE id = %s", r.json()["lead_id"])
    key, = _exec(db, "SELECT logo_key FROM tenants WHERE id = %s", tenant_id)
    assert key == f"{tenant_id}/logo/logo.png" and Image.open(io.BytesIO(store[key])).size == (400, 400)


def test_admin_create_with_logo(client, db, super_headers, tag, store):
    good = "data:image/webp;base64," + base64.b64encode(png(600, 200, fmt="WEBP")).decode()
    r = client.post("/api/v1/tenants/admin-create", headers=super_headers, json={
        "name": f"Logolu Kurum {tag}", "contact_email": f"kurum_{tag}@logolu-kurum.com.tr", "activate_package": False,
        "send_welcome_email": False, "logo_data_url": good})
    assert r.status_code == 200, r.text
    key, = _exec(db, "SELECT logo_key FROM tenants WHERE id = %s", r.json()["tenant_id"])
    assert key and Image.open(io.BytesIO(store[key])).size == (512, 171)
