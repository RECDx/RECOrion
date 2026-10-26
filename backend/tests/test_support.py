"""
ADIM 13.3: RECQmind — Helpdesk bileti → Case → sonuç onayla bilete (sahte Odoo 19 JSON-2 sunucusu, sahte EVREN).

- Bilet ortak nesneye çevrilir: tür etiketten, etiket yoksa konu/mesajdaki sözcükten; kanal, öncelik, html mesaj düz metne.
- Hazır kurallar yalnızca RECQmind'ı kullanan şirkette kurulur; Helpdesk eşlemesi yoksa taslak eklenir; ikinci kurulum çift kural açmaz.
- İzleme: ilk tur başlangıç; yeni iade bileti şablonlu İade Case'i açar (kaynak = bilet, kapanışta aktarım = Helpdesk eşlemesi);
  başka türdeki bilet bu kuralda iş açmaz.
- Case sonucu: aktarım bilete bağlı tek öneridir (yeni bilet açılmaz); yalnızca durum yazılır (konu/mesaj ezilmez), çözüm iç not
  olarak eklenir; onaysız yazma yok.
"""
import json
import time
import uuid

import httpx
import pytest

from app.config import settings
from app.integrations import base, odoo
from app.services import support
from app.services import transfers as tsvc
from tests.test_mappings import KEY, _odoo_conn, _seed
from tests.test_workflow import _exec, world  # noqa: F401  (fikstür)

TICKET_FIELDS = {
    "name": {"string": "Konu", "type": "char", "required": True, "depends": []},
    "description": {"string": "Açıklama", "type": "html"},
    "partner_name": {"string": "Müşteri adı", "type": "char"}, "partner_email": {"string": "Müşteri e-postası", "type": "char"},
    "partner_phone": {"string": "Müşteri telefonu", "type": "char"},
    "priority": {"string": "Öncelik", "type": "selection", "selection": [["0", "Düşük"], ["1", "Orta"], ["2", "Yüksek"], ["3", "Acil"]]},
    "tag_ids": {"string": "Etiketler", "type": "many2many", "relation": "helpdesk.tag"},
    "stage_id": {"string": "Aşama", "type": "many2one", "relation": "helpdesk.stage"},
    "team_id": {"string": "Ekip", "type": "many2one", "relation": "helpdesk.team"},
}


@pytest.fixture
def helpdesk(monkeypatch):
    st = {"tickets": {1: {"id": 1, "name": "Eski bilet", "description": "<p>eski</p>", "priority": "1", "tag_ids": [], "stage_id": [1, "Yeni"]}},
          "tags": {5: "İade", 6: "Kargo"}, "stages": {1: "Yeni", 4: "Çözüldü"}, "calls": [], "notes": []}

    def ok(data):
        return httpx.Response(200, headers={"content-type": "application/json"}, json=data)

    def handler(req: httpx.Request) -> httpx.Response:
        assert req.headers.get("authorization") == f"bearer {KEY}"
        _, _, _, model, method = req.url.path.split("/")
        body = json.loads(req.content)
        st["calls"].append((model, method, body))
        if method == "fields_get":
            return ok(TICKET_FIELDS if model == "helpdesk.ticket" else {})
        if method == "default_get":
            return ok({})
        if model in ("helpdesk.tag", "helpdesk.stage"):
            table = st["tags"] if model == "helpdesk.tag" else st["stages"]
            if method == "read":
                return ok([{"id": i, "name": table[i]} for i in body["ids"] if i in table])
            (fld, op, val), = body["domain"]
            return ok([{"id": i} for i, n in table.items() if n.lower() == str(val).lower()])
        if model == "helpdesk.ticket":
            t = st["tickets"]
            if method == "search_read":
                if not body["domain"]:  # izleme: en yeniden eskiye
                    return ok([{f: r.get(f) for f in body["fields"]} for r in sorted(t.values(), key=lambda r: -r["id"])])
                (fld, op, val), = body["domain"]
                return ok([{"id": val}] if fld == "id" and val in t else [])
            if method == "read":
                return ok([{"id": i, **{f: t[i].get(f) for f in body.get("fields", []) if f != "display_name"},
                            **({"display_name": t[i]["name"]} if "display_name" in body.get("fields", []) else {})} for i in body["ids"]])
            if method == "write":
                for i in body["ids"]:
                    t[i].update(body["vals"])
                return ok(True)
            if method == "create":
                raise AssertionError("Case sonucu yeni bilet açmamalı")
            if method == "message_post":
                st["notes"].append((body["ids"], body["body"], body.get("subtype_xmlid")))
                return ok(99)
        raise AssertionError(f"beklenmeyen çağrı {model}.{method}")
    monkeypatch.setattr(base, "TRANSPORT", httpx.MockTransport(handler))
    monkeypatch.setattr(settings, "WORKFLOW_ENABLED", False)
    odoo._styles.clear()
    return st


def _seed_templates(client):
    from app.db.session import AsyncSessionLocal
    from app.services.project_templates import ensure_platform_templates

    async def go():
        async with AsyncSessionLocal() as s:
            return await ensure_platform_templates(s)
    return client.portal.call(go)


def test_ticket_to_object_classifies_and_cleans():
    o = support.to_object({"id": 7, "name": "Sipariş hakkında", "description": "<p>Ürün <b>gelmedi</b>,<br/>kargo nerede?</p>",
                           "priority": "2", "partner_name": "Ayşe Yılmaz", "partner_email": "ayse@trendyol-mail.example", "tag_ids": [5]},
                          ["İade"])
    assert o["category"] == "RETURN" and o["category_label"] == "İade"  # etiket, sözcükten önce gelir
    assert o["channel"] == "TRENDYOL" and o["priority"] == "HIGH" and o["ticket_ref"] == "7"
    assert o["description"] == "Ürün gelmedi,\nkargo nerede?"
    assert support.to_object({"id": 8, "name": "SİPARİŞİMİ İPTAL ETMEK İSTİYORUM"})["category"] == "CANCEL"  # Türkçe büyük harf
    assert support.to_object({"id": 9, "name": "Soru", "description": "Bu kulaklık iPhone ile uyumlu mu?"})["category"] == "PRODUCT_QUESTION"
    assert support.to_object({"id": 10, "name": "Kargom 5 gündür gelmedi"})["category"] == "SHIPPING"
    weird = support.to_object({"id": 11, "name": "Merhaba", "partner_email": "bozuk-adres", "priority": "9"})
    assert weird["category"] == "OTHER" and "customer_email" not in weird and weird["priority"] == "NORMAL"


def test_recqmind_presets_case_and_reply_to_ticket(client, db, world, helpdesk, monkeypatch):
    from app.services.evren_client import ChatResult, evren_client

    w = world
    h = w["admin"]["h"]
    T = f"/api/v1/company/{w['tenant']}"
    _seed(client)
    _seed_templates(client)
    cid = _odoo_conn(client, w)

    # RECQmind açık değilken: hazır eşleme görünmez, kural kurulamaz
    _exec(db, "UPDATE tenants SET settings = coalesce(settings, '{}'::jsonb) - 'recdx_apps' WHERE id = %s", w["tenant"])
    db.commit()
    assert "odoo_helpdesk_ticket" not in {t["code"] for t in client.get(f"{T}/mappings/templates", headers=h).json()}
    st = client.get(f"{T}/automations/presets/recqmind", headers=h).json()
    assert st["available"] is False and "RECQmind" in st["reason"]
    body = {"connection_id": cid, "manager_actor_id": w["admin"]["id"], "categories": ["RETURN", "SHIPPING"]}
    assert client.post(f"{T}/automations/presets/recqmind", headers=h, json=body).status_code == 409
    assert client.get(f"{T}/automations/presets/recqmind", headers=w["member"]["h"]).status_code == 403

    _exec(db, "UPDATE tenants SET settings = coalesce(settings, '{}'::jsonb) || %s::jsonb WHERE id = %s",
          json.dumps({"recdx_apps": {"has_odoo": True, "apps": {"recqmind": "USING"}}}), w["tenant"])
    db.commit()
    assert "odoo_helpdesk_ticket" in {t["code"] for t in client.get(f"{T}/mappings/templates", headers=h).json()}
    r = client.post(f"{T}/automations/presets/recqmind", headers=h, json=body)
    assert r.status_code == 201, r.text
    out = r.json()
    assert {x["name"] for x in out["rules"]} == {"RECQmind: İade biletleri → İade Case'i", "RECQmind: Kargo problemleri → Kargo Case'i"}
    assert out["mapping"]["status"] == "DRAFT" and any("Eşleme Stüdyosu" in n for n in out["notes"])
    again = client.post(f"{T}/automations/presets/recqmind", headers=h, json=body).json()
    assert again["rules"] == [] and sum("zaten kurulu" in n for n in again["notes"]) == 2
    ret = next(x for x in out["rules"] if "İade" in x["name"])
    assert ret["poll"]["enrich"] == "helpdesk_ticket" and ret["conditions"] == [{"field": "ticket.category", "op": "eq", "value": "RETURN"}]
    assert ret["action"]["transfer_on_close"] == [out["mapping"]["id"]]

    # Örnek biletle deneme: ortak nesne eklenir, hiçbir şey açılmaz
    test = client.post(f"{T}/automations/{ret['id']}/test", headers=h, json={"payload": {"id": 900, "name": "İade talebi", "tag_ids": []}}).json()
    assert test["outcome"] == "TEST", test

    # İzleme: ilk tur başlangıç; sonra yeni iade bileti İade Case'i açar, kargo bileti bu kuralda açmaz
    run = f"{T}/automations/{ret['id']}/run"
    assert client.post(run, headers=h).json()["baseline"] is True
    helpdesk["tickets"][2] = {"id": 2, "name": "Kulaklık iadesi", "description": "<p>Kutusu hasarlı geldi</p>", "priority": "2",
                              "partner_name": "Ayşe Yılmaz", "partner_email": "ayse@example.com", "tag_ids": [5], "stage_id": [1, "Yeni"]}
    helpdesk["tickets"][3] = {"id": 3, "name": "Kargo gecikti", "description": "", "priority": "1", "tag_ids": [6], "stage_id": [1, "Yeni"]}
    res = client.post(run, headers=h).json()
    assert sorted(x["outcome"] for x in res["handled"]) == ["DRAFTED", "IGNORED"], res
    pid = next(x["project_id"] for x in res["handled"] if x["outcome"] == "DRAFTED")
    name, kind, status, ref, toc, reqs, tpl = _exec(
        db, "SELECT name, kind, status, source_ref, transfer_on_close::text, requirements, template_id::text FROM projects WHERE id = %s", pid)
    assert name == "İade: Kulaklık iadesi (bilet #2)" and kind == "CASE" and status == "PLANNING"
    assert ref == "odoo:helpdesk.ticket:2" and json.loads(toc) == [out["mapping"]["id"]] and "Kutusu hasarlı geldi" in reqs
    assert _exec(db, "SELECT code FROM project_templates WHERE id = %s", tpl)[0] == "recqmind-iade"
    assert client.get(f"/api/v1/projects/{pid}", headers=h).json()["source_label"] == "Odoo destek bileti #2"

    # Eşleme denenir ve onaylanır (deneme yazmaz)
    mid = out["mapping"]["id"]
    dry = client.post(f"{T}/mappings/{mid}/dry-run", headers=h, json={}).json()
    assert dry["ok"], dry
    assert client.post(f"{T}/mappings/{mid}/approve", headers=h).status_code == 200
    assert not any(m in ("write", "create", "message_post") for _, m, _ in helpdesk["calls"])

    # Case sonucu: RECAi çıktıdan çözümü çıkarır; bilete bağlı tek öneri, yalnızca durum + iç not
    async def chat(model_code, messages, **kw):
        return ChatResult(json.dumps({"items": [
            {"subject": "Başka konu", "description": "ezilmemeli", "status": "SOLVED",
             "resolution": "Ürün depoda incelendi, iade onaylandı.\nÜcret iadesi 3 iş günü içinde yapılacak."},
            {"subject": "İkinci kayıt", "status": "OPEN"}]}), None, 500, 200, {})
    monkeypatch.setattr(evren_client, "chat", chat)

    async def text(db_, project):
        return "Case özeti: iade onaylandı."
    monkeypatch.setattr(tsvc, "project_text", text)
    _exec(db, "UPDATE projects SET status = 'COMPLETED' WHERE id = %s", pid)
    db.commit()
    r = client.post(f"/api/v1/projects/{pid}/transfers", headers=h, json={"mapping_id": mid})
    assert r.status_code == 202, r.text
    end = time.time() + 30
    while time.time() < end:
        rows = client.get(f"/api/v1/projects/{pid}/transfers", headers=h).json()
        if rows and all(x["status"] != "EXTRACTING" for x in rows):
            break
        time.sleep(0.4)
    assert len(rows) == 1, rows
    tr = rows[0]
    assert tr["status"] == "PENDING_APPROVAL" and tr["action"] == "UPDATE" and tr["object"]["ticket_ref"] == "2", tr
    assert [p["target"] for p in tr["preview"]] == ["stage_id", "(iç not)"], tr["preview"]  # konu/mesaj ezilmez
    assert not any(m in ("write", "message_post") for _, m, _ in helpdesk["calls"])  # onaysız yazma yok

    assert client.post(f"/api/v1/transfers/{tr['id']}/decision", headers=h, json={"approve": True}).status_code == 200
    end = time.time() + 30
    while time.time() < end and client.get(f"/api/v1/transfers/{tr['id']}", headers=h).json()["status"] != "DONE":
        time.sleep(0.4)
    done = client.get(f"/api/v1/transfers/{tr['id']}", headers=h).json()
    assert done["status"] == "DONE" and done["external_id"] == "2", done
    t2 = helpdesk["tickets"][2]
    assert t2["stage_id"] == 4 and t2["name"] == "Kulaklık iadesi" and t2["description"] == "<p>Kutusu hasarlı geldi</p>"
    (ids, note, subtype), = helpdesk["notes"]
    assert ids == [2] and subtype == "mail.mt_note" and "iade onaylandı.<br/>Ücret iadesi" in note and "RECOrion Case sonucu" in note


def test_closing_defaults_from_case():
    class P:
        status, close_summary = "COMPLETED", "İade onaylandı, ücret iadesi yapıldı."
    assert support.closing_defaults(P(), {"ticket_ref": "2"}) == {"ticket_ref": "2", "resolution": P.close_summary, "status": "SOLVED"}
    # RECAi'nin bulduğu çözüm ve durum korunur; iptal edilen Case bileti çözülmüş saymaz
    assert support.closing_defaults(P(), {"resolution": "RECAi", "status": "OPEN"}) == {"resolution": "RECAi", "status": "OPEN"}
    P.status = "CANCELLED"
    assert "status" not in support.closing_defaults(P(), {})
