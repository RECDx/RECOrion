"""
ADIM 12.4: çıktıdan kayda aktarım (sahte Odoo 20 JSON-2 sunucusu, sahte EVREN; gerçek ağa çıkılmaz).

- RECAi adım çıktısından birden çok nesne çıkarır; her biri ayrı öneri; eksik bilgi → düzeltme gerekir (NEEDS_FIX).
- Onay: proje yöneticisi; şirket kuralıyla (nesne türü / tutar eşiği) ikinci onay entegrasyon yöneticisinden ve farklı kişiden.
- Onaysız yazma yok; onaydan sonra kuyruğa alınır ve yazılır; stok koduyla mevcut kayıt bulunursa güncellenir (çift kayıt yok),
  eski değerler saklanır; geri alma: açılan kayıt arşivlenir, güncellenen kaydın eski değerleri geri yazılır.
- Geçici hata yeniden denenir; iş mantığı hatası FAILED. Kayıt silinemez. Ekip üyesi onaylayamaz; RECDx göremez (KVKK).
- Adım bitince tanımlı eşlemelerle otomatik öneri.
"""
import json
import time
import uuid

import httpx
import psycopg2
import pytest

from app.config import settings
from app.core.security import hash_password
from app.integrations import base, odoo
from app.services import transfers as tsvc
from tests.test_integrations import _super
from tests.test_mappings import FIELDS, KEY, _odoo_conn, _seed
from tests.test_workflow import PASSWORD, _exec, _login, _ready_project, world  # noqa: F401  (fikstür)

OUTPUT = """# Depo sayım projesi — ürün kartı önerisi
1. El terminali: stok kodu RECT-ELT-01, birim Adet, satış 12.500 TL, alış 9.800 TL, KDV %20.
2. Barkod etiketi rulosu: stok kodu RECT-ETK-02, birim Adet, satış 150 TL, KDV %20.
3. Kurulum hizmeti (birim belirtilmedi)."""


@pytest.fixture
def odoo_db(monkeypatch):
    st = {"records": {"product.template": {55: {"id": 55, "default_code": "RECT-ETK-02", "name": "Eski etiket", "list_price": 99.0,
                                                 "uom_id": [1, "Units"], "taxes_id": [7], "active": True}}},
          "next": 100, "calls": [], "fail": None}
    fields = {m: {**f, "active": {"string": "Etkin", "type": "boolean"}} for m, f in FIELDS.items()}

    def ok(data):
        return httpx.Response(200, headers={"content-type": "application/json"}, json=data)

    def handler(req: httpx.Request) -> httpx.Response:
        assert req.headers.get("authorization") == f"bearer {KEY}"
        _, _, _, model, method = req.url.path.split("/")
        body = json.loads(req.content)
        st["calls"].append((model, method, body))
        if st["fail"] and method in ("create", "write"):
            kind, st["fail"] = st["fail"], None if st["fail"] == "once" else st["fail"]
            if kind in ("once", "always"):
                return httpx.Response(503, headers={"content-type": "application/json"}, json={"message": "Service Unavailable"})
            return httpx.Response(422, headers={"content-type": "application/json"}, json={"message": "Barkod zaten kullanılıyor"})
        if method == "fields_get":
            return ok(fields.get(model, {}))
        if method == "default_get":
            return ok({"type": "consu"} if "type" in body["fields"] else {})
        recs = st["records"].setdefault(model, {})
        if method == "search_read":
            if not body["domain"]:
                return ok([])
            (fld, op, val), *rest = body["domain"]
            table = {("uom.uom", "name"): {"units": 1, "adet": 1, "kg": 16}, ("account.tax", "amount"): {20.0: 7 if rest == [["type_tax_use", "=", "sale"]] else 8},
                     ("product.category", "name"): {}}
            if (model, fld) in table:
                hit = table[(model, fld)].get(val.lower() if isinstance(val, str) else val)
                return ok([{"id": hit}] if hit else [])
            return ok([{"id": r["id"]} for r in recs.values() if str(r.get(fld) or "").lower() == str(val).lower() and r.get("active", True)])
        if method == "create":
            ids = []
            for vals in body["vals_list"]:
                st["next"] += 1
                recs[st["next"]] = {"id": st["next"], "active": True, **vals}
                ids.append(st["next"])
            return ok(ids)
        if method == "write":
            for i in body["ids"]:
                recs[i].update(body["vals"])
            return ok(True)
        if method == "read":
            return ok([{"id": i, **{f: recs[i].get(f) for f in body.get("fields", [])},
                        **({"display_name": recs[i].get("name")} if "display_name" in body.get("fields", []) else {})} for i in body["ids"]])
        raise AssertionError(f"beklenmeyen çağrı {model}.{method}")
    monkeypatch.setattr(base, "TRANSPORT", httpx.MockTransport(handler))
    monkeypatch.setattr(settings, "WORKFLOW_ENABLED", False)  # yerel kuyruk (Temporal canlı testte)
    odoo._styles.clear()
    return st


@pytest.fixture
def fake_extract(monkeypatch):
    from app.services.evren_client import ChatResult, evren_client

    seen = []

    async def chat(model_code, messages, **kw):
        seen.append(messages[-1]["content"])
        return ChatResult(json.dumps({"items": [
            {"code": "RECT-ELT-01", "name": "El terminali", "type": "STOCK", "unit": "Adet", "sale_price": "12.500", "purchase_price": 9800, "vat_rate": 20},
            {"code": "RECT-ETK-02", "name": "Barkod etiketi rulosu", "type": "STOCK", "unit": "Adet", "sale_price": 150, "vat_rate": 20},
            {"name": "Kurulum hizmeti", "type": "SERVICE"}], "notes": "Kurulum hizmetinin birimi çıktıda yok."}), None, 900, 300, {})
    monkeypatch.setattr(evren_client, "chat", chat)

    async def text(db, task):
        return OUTPUT
    monkeypatch.setattr(tsvc, "output_text", text)
    return seen


def _active_mapping(client, w):
    h = w["admin"]["h"]
    _seed(client)
    cid = _odoo_conn(client, w)
    tpl = next(t for t in client.get(f"/api/v1/company/{w['tenant']}/mappings/templates?connector=odoo", headers=h).json() if t["code"] == "odoo_product")
    m = client.post(f"/api/v1/company/{w['tenant']}/mappings", headers=h, json={"connection_id": cid, "object_type": "PRODUCT", "name": "Ürün → Odoo",
                                                                               "template_id": tpl["id"]}).json()
    assert client.post(f"/api/v1/company/{w['tenant']}/mappings/{m['id']}/dry-run", headers=h, json={}).json()["ok"]
    assert client.post(f"/api/v1/company/{w['tenant']}/mappings/{m['id']}/approve", headers=h).status_code == 200
    return m["id"], cid


def _project_with_done_step(client, db, w):
    pid, human, _ = _ready_project(client, w, f"Aktarım {uuid.uuid4().hex[:4]}")
    _exec(db, "UPDATE projects SET status = 'ACTIVE' WHERE id = %s", pid)
    _exec(db, "UPDATE tasks SET status = 'DONE' WHERE id = %s", human)
    return pid, human


def _wait(client, h, pid, cond, timeout=30):
    end = time.time() + timeout
    while time.time() < end:
        rows = client.get(f"/api/v1/projects/{pid}/transfers", headers=h).json()
        if cond(rows):
            return rows
        time.sleep(0.4)
    raise AssertionError(f"beklenen duruma gelmedi: {rows}")


def _second_admin(client, db, w):
    email = f"ikinci_{uuid.uuid4().hex[:6]}@test.example"
    _exec(db, "INSERT INTO actors (tenant_id, actor_type, display_name, email, role, password_hash, status) "
              "VALUES (%s, 'HUMAN', 'İkinci Yönetici', %s, 'COMPANY_ADMIN', %s, 'IDLE')", w["tenant"], email, hash_password(PASSWORD))
    return _login(client, email)


def test_step_output_to_odoo_with_approval_update_and_rollback(client, db, world, odoo_db, fake_extract):
    w = world
    h = w["admin"]["h"]
    mid, cid = _active_mapping(client, w)
    pid, task_id = _project_with_done_step(client, db, w)

    opts = client.get(f"/api/v1/projects/{pid}/transfer-options", headers=h).json()
    assert [o["id"] for o in opts] == [mid] and opts[0]["object_label"] == "Ürün / hizmet kartı"
    assert client.post(f"/api/v1/tasks/{task_id}/transfers", headers=w["member"]["h"], json={"mapping_id": mid}).status_code == 403
    r = client.post(f"/api/v1/tasks/{task_id}/transfers", headers=h, json={"mapping_id": mid})
    assert r.status_code == 202 and r.json()["status"] == "EXTRACTING"
    rows = _wait(client, h, pid, lambda rs: len(rs) == 3 and all(x["status"] != "EXTRACTING" for x in rs))
    by = {(x["object"].get("code") or x["object"].get("name")): x for x in rows}
    assert "RECT-ELT-01" in fake_extract[0] or "El terminali" in fake_extract[0]
    new, upd, fix = by["RECT-ELT-01"], by["RECT-ETK-02"], by["Kurulum hizmeti"]
    assert new["status"] == "PENDING_APPROVAL" and new["action"] == "CREATE" and new["object"]["sale_price"] == 12500.0
    assert upd["status"] == "PENDING_APPROVAL" and upd["action"] == "UPDATE"
    assert fix["status"] == "NEEDS_FIX" and any("Birim" in e for e in fix["problems"]["errors"])
    assert any("RECAi:" in x for x in new["problems"]["warnings"])
    assert not any(m in ("create", "write") for _, m, _ in odoo_db["calls"])  # onaysız yazma yok

    # Ekip üyesi ve RECDx personeli onaylayamaz / göremez
    assert client.post(f"/api/v1/transfers/{new['id']}/decision", headers=w["member"]["h"], json={"approve": True}).status_code == 403
    assert client.get(f"/api/v1/transfers/{new['id']}", headers=_super(client, db)).status_code == 403
    mine = client.get("/api/v1/me/transfer-approvals", headers=h).json()
    assert {x["id"] for x in mine} >= {new["id"], upd["id"]} and fix["id"] not in {x["id"] for x in mine}

    # Düzeltme: birim girilince öneri onaya düşer
    r = client.put(f"/api/v1/transfers/{fix['id']}", headers=h, json={"object": {**fix["object"], "unit": "Saat", "code": "RECT-KUR-03"}})
    assert r.json()["status"] in ("PENDING_APPROVAL", "NEEDS_FIX")

    # Onay → yazılır (yeni kayıt)
    r = client.post(f"/api/v1/transfers/{new['id']}/decision", headers=h, json={"approve": True, "note": "uygun"})
    assert r.status_code == 200 and r.json()["status"] in ("APPROVED", "RUNNING", "DONE")
    rows = _wait(client, h, pid, lambda rs: next(x for x in rs if x["id"] == new["id"])["status"] == "DONE")
    done = next(x for x in rows if x["id"] == new["id"])
    rec = odoo_db["records"]["product.template"][int(done["external_id"])]
    assert rec["default_code"] == "RECT-ELT-01" and rec["uom_id"] == 1 and rec["taxes_id"] == [[6, 0, [7]]] and rec["list_price"] == 12500.0
    assert done["external_ref"].startswith("El terminali") and done["external_url"].endswith(f"/odoo/product.template/{done['external_id']}")
    link = _exec(db, "SELECT external_id FROM external_links WHERE connection_id = %s AND match_value = 'RECT-ELT-01'", cid)
    assert link and link[0] == done["external_id"]

    # Mevcut kayıt güncellenir; eski değerler saklanır; geri alınca eski değerler geri yazılır
    client.post(f"/api/v1/transfers/{upd['id']}/decision", headers=h, json={"approve": True})
    _wait(client, h, pid, lambda rs: next(x for x in rs if x["id"] == upd["id"])["status"] == "DONE")
    assert odoo_db["records"]["product.template"][55]["name"] == "Barkod etiketi rulosu" and len(odoo_db["records"]["product.template"]) == 2
    r = client.post(f"/api/v1/transfers/{upd['id']}/rollback", headers=h)
    assert r.status_code == 200 and r.json()["status"] == "ROLLED_BACK"
    old = odoo_db["records"]["product.template"][55]
    assert old["name"] == "Eski etiket" and old["list_price"] == 99.0 and old["uom_id"] == 1 and old["taxes_id"] == [[6, 0, [7]]]
    # Açılan kayıt geri alınınca arşivlenir
    client.post(f"/api/v1/transfers/{new['id']}/rollback", headers=h)
    assert rec["active"] is False
    assert client.post(f"/api/v1/transfers/{new['id']}/rollback", headers=h).status_code == 409

    # Kayıt silinemez
    with pytest.raises(psycopg2.Error):
        _exec(db, "DELETE FROM integration_transfers WHERE id = %s", new["id"])
    log = client.get(f"/api/v1/company/{w['tenant']}/transfers", headers=h).json()
    assert {new["id"], upd["id"], fix["id"]} <= {x["id"] for x in log}


def test_double_approval_and_failures(client, db, world, odoo_db, fake_extract):
    w = world
    h = w["admin"]["h"]
    mid, _ = _active_mapping(client, w)
    pid, task_id = _project_with_done_step(client, db, w)
    pol = client.put(f"/api/v1/company/{w['tenant']}/transfer-policy", headers=h, json={"double_approval_objects": [], "amount_threshold": 1000})
    assert pol.json()["amount_threshold"] == 1000
    assert client.put(f"/api/v1/company/{w['tenant']}/transfer-policy", headers=w["member"]["h"], json={}).status_code == 403
    client.post(f"/api/v1/tasks/{task_id}/transfers", headers=h, json={"mapping_id": mid})
    rows = _wait(client, h, pid, lambda rs: len(rs) == 3 and all(x["status"] != "EXTRACTING" for x in rs))
    big = next(x for x in rows if x["object"].get("code") == "RECT-ELT-01")  # 12.500 TL > eşik
    small = next(x for x in rows if x["object"].get("code") == "RECT-ETK-02")
    assert big["required_approvals"] == 2 and small["required_approvals"] == 1

    r = client.post(f"/api/v1/transfers/{big['id']}/decision", headers=h, json={"approve": True}).json()
    assert r["status"] == "PENDING_APPROVAL" and len(r["approvals"]) == 1
    assert client.post(f"/api/v1/transfers/{big['id']}/decision", headers=h, json={"approve": True}).status_code == 403  # aynı kişi
    second = _second_admin(client, db, w)
    assert big["id"] in {x["id"] for x in client.get("/api/v1/me/transfer-approvals", headers=second).json()}
    odoo_db["fail"] = "once"  # geçici hata: yeniden denenir
    client.post(f"/api/v1/transfers/{big['id']}/decision", headers=second, json={"approve": True})
    rows = _wait(client, h, pid, lambda rs: next(x for x in rs if x["id"] == big["id"])["status"] == "DONE", timeout=40)
    assert next(x for x in rows if x["id"] == big["id"])["attempts"] == 2

    odoo_db["fail"] = "business"  # iş mantığı hatası: yeniden denenmez
    client.post(f"/api/v1/transfers/{small['id']}/decision", headers=h, json={"approve": True})
    rows = _wait(client, h, pid, lambda rs: next(x for x in rs if x["id"] == small["id"])["status"] == "FAILED")
    failed = next(x for x in rows if x["id"] == small["id"])
    assert "Barkod zaten kullanılıyor" in failed["error"] and failed["attempts"] == 1
    odoo_db["fail"] = None
    assert client.post(f"/api/v1/transfers/{small['id']}/retry", headers=h).status_code == 200
    _wait(client, h, pid, lambda rs: next(x for x in rs if x["id"] == small["id"])["status"] == "DONE")

    # Ret: yazılmaz
    other = next(x for x in client.get(f"/api/v1/projects/{pid}/transfers", headers=h).json() if x["object"].get("name") == "Kurulum hizmeti")
    assert client.post(f"/api/v1/transfers/{other['id']}/decision", headers=h, json={"approve": False}).status_code == 409  # düzeltme bekliyor


def test_step_done_auto_proposal(client, db, world, odoo_db, fake_extract):
    from app.db.models import Project, Task
    from app.db.session import AsyncSessionLocal

    w = world
    h = w["admin"]["h"]
    mid, _ = _active_mapping(client, w)
    pid, task_id = _project_with_done_step(client, db, w)
    assert client.put(f"/api/v1/tasks/{task_id}/transfer-rules", headers=h, json={"mapping_ids": [str(uuid.uuid4())]}).status_code == 422
    r = client.put(f"/api/v1/tasks/{task_id}/transfer-rules", headers=h, json={"mapping_ids": [mid]})
    assert r.status_code == 200 and r.json()["mapping_ids"] == [mid]

    async def done():
        async with AsyncSessionLocal() as s:
            await tsvc.after_step_done(s, await s.get(Task, uuid.UUID(task_id)), await s.get(Project, uuid.UUID(pid)))
    client.portal.call(done)
    rows = _wait(client, h, pid, lambda rs: len(rs) == 3)
    assert {x["trigger"] for x in rows} == {"STEP_DONE"} and {x["created_by_name"] for x in rows} == {"RECAi"}
