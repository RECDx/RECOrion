"""
ADIM 13.4: RECSlip — sorunlu masraf fişi → Case → karar onayla masraf kaydına; ay sonu kapanış (sahte Odoo 19 JSON-2, sahte EVREN).

- Fiş ortak nesneye çevrilir: RECSlip alanları (rec_fld_*) ve eski Studio alanları (x_studio_*) okunur; sorunlar: mükerrer, VKN
  yok/geçersiz, fiş görseli yok, okuma doğrulanmalı, tutar yok. Reddedilen/iptal/aktarılmayacak fiş Case açmaz.
- Hazır kurallar yalnızca RECSlip'i kullanan şirkette kurulur; masraf eşlemesi yoksa taslak eklenir.
- İzleme: ilk tur başlangıç; sorunlu yeni fiş "Sorunlu masraf fişi" Case'i açar (kaynak = masraf), sorunsuz fiş açmaz; sorun
  listesi değişen fiş yeniden değerlendirilir.
- Ay sonu kuralı hemen çalıştırılınca dönem özetiyle kapanış Case'i açılır.
- Case kararı masraf kaydına yalnızca iç not olarak yazılır (tutar/açıklama ezilmez, yeni masraf açılmaz); onaysız yazma yok.
"""
import json
import time
from datetime import date

import httpx
import pytest

from app.config import settings
from app.integrations import base, odoo
from app.services import expenses
from app.services import transfers as tsvc
from tests.test_mappings import KEY, _odoo_conn, _seed
from tests.test_support import _seed_templates
from tests.test_workflow import _exec, world  # noqa: F401  (fikstür)

EXPENSE_FIELDS = {
    "name": {"string": "Açıklama", "type": "char", "required": True},
    "date": {"string": "Tarih", "type": "date"},
    "total_amount_currency": {"string": "Toplam", "type": "monetary"},
    "total_amount": {"string": "Toplam (şirket)", "type": "monetary"},
    "product_id": {"string": "Kategori", "type": "many2one", "relation": "product.product"},
    "vendor_id": {"string": "Tedarikçi", "type": "many2one", "relation": "res.partner"},
    "employee_id": {"string": "Çalışan", "type": "many2one", "relation": "hr.employee", "required": True},
    "payment_mode": {"string": "Ödeyen", "type": "selection", "required": True,
                     "selection": [["own_account", "Çalışan"], ["company_account", "Şirket"]]},
    "state": {"string": "Durum", "type": "selection"},
    "nb_attachment": {"string": "Ek", "type": "integer"},
    "rec_fld_is_mukerrer": {"string": "Mükerrer Kayıt", "type": "boolean"},
    "rec_fld_vkn_tckn": {"string": "VKN/TCKN", "type": "text"},
    "rec_fld_fis_No": {"string": "Fiş/Satış No", "type": "text"},
    "rec_fld_toplam_kdv_tutar": {"string": "Toplam KDV Tutarı", "type": "monetary"},
    "rec_fld_onay_durumu": {"string": "Onay Durumu", "type": "selection"},
    "rec_fld_red_nedeni": {"string": "Red Nedeni", "type": "text"},
}
TODAY = date.today().isoformat()


def _expense(i, **kw):
    r = {"id": i, "name": f"Fiş {i}", "date": TODAY, "total_amount": 250.0, "currency_id": [1, "TRY"], "vendor_id": False,
         "employee_id": [1, "Administrator"], "product_id": [3, "Meals"], "state": "draft", "payment_mode": "own_account",
         "description": False, "nb_attachment": 1, "rec_fld_is_mukerrer": False, "rec_fld_vkn_tckn": "1234567890",
         "rec_fld_fis_No": f"F-{i}", "rec_fld_toplam_kdv_tutar": 22.73, "rec_fld_onay_durumu": "onayinda_yonetici",
         "rec_fld_red_nedeni": False}
    r.update(kw)
    return r


@pytest.fixture
def slip(monkeypatch):
    st = {"expenses": {1: _expense(1)}, "calls": [], "notes": []}

    def ok(data):
        return httpx.Response(200, headers={"content-type": "application/json"}, json=data)

    def handler(req: httpx.Request) -> httpx.Response:
        assert req.headers.get("authorization") == f"bearer {KEY}"
        _, _, _, model, method = req.url.path.split("/")
        body = json.loads(req.content)
        st["calls"].append((model, method, body))
        if method == "fields_get":
            return ok(EXPENSE_FIELDS if model == "hr.expense" else {})
        if method == "default_get":
            return ok({"employee_id": 1, "payment_mode": "own_account"} if model == "hr.expense" else {})
        if model == "res.partner" and method == "read":
            return ok([{"id": i, "vat": "TR1234567890"} for i in body["ids"]])
        if model == "hr.expense":
            e = st["expenses"]
            if method == "search_read":
                dom = body.get("domain") or []
                if dom and dom[0][0] == "id":
                    return ok([{"id": dom[0][2]}] if dom[0][2] in e else [])
                rows = [r for r in e.values() if all(
                    (r["date"] >= v if op == ">=" else r["date"] <= v) for f, op, v in dom if f == "date")]
                return ok([{f: r.get(f) for f in body["fields"]} for r in sorted(rows, key=lambda r: -r["id"])])
            if method == "read":
                return ok([{"id": i, **{f: e[i].get(f) for f in body.get("fields", []) if f in e[i]}} for i in body["ids"] if i in e])
            if method == "write":
                for i in body["ids"]:
                    e[i].update(body["vals"])
                return ok(True)
            if method == "create":
                raise AssertionError("Case kararı yeni masraf açmamalı")
            if method == "message_post":
                st["notes"].append((body["ids"], body["body"], body.get("subtype_xmlid")))
                return ok(99)
        return ok([])  # eşleme denemesindeki adla arama (ürün, çalışan): bulunamadı
    monkeypatch.setattr(base, "TRANSPORT", httpx.MockTransport(handler))
    monkeypatch.setattr(settings, "WORKFLOW_ENABLED", False)
    odoo._styles.clear()
    return st


def test_expense_to_object_and_problems():
    o = expenses.to_object(_expense(5))
    assert o["expense_ref"] == "5" and o["vendor_tax_number"] == "1234567890" and o["receipt_no"] == "F-5" and o["vat_amount"] == 22.73
    assert o["has_problem"] is False and o["problem_text"] == "Yok" and o["state_label"] == "Yönetici onayında"
    assert o["payment"] == "EMPLOYEE" and o["category"] == "Meals" and o["employee_name"] == "Administrator"
    bad = expenses.to_object(_expense(6, rec_fld_is_mukerrer=True, rec_fld_vkn_tckn="1234567891", nb_attachment=0, total_amount=0))
    assert bad["problems"] == ["DUPLICATE", "INVALID_VKN", "NO_RECEIPT", "NO_AMOUNT"] and bad["has_problem"]
    assert bad["problem_key"] == "DUPLICATE,INVALID_VKN,NO_AMOUNT,NO_RECEIPT"
    # VKN masrafta yoksa satıcının VKN'si; o da yoksa eksik
    assert expenses.to_object(_expense(7, rec_fld_vkn_tckn=False), "TR1234567890")["vendor_tax_number"] == "1234567890"
    assert expenses.to_object(_expense(8, rec_fld_vkn_tckn=False))["problems"] == ["MISSING_VKN"]
    # eski Studio kurulumu
    studio = {k: v for k, v in _expense(9).items() if not k.startswith("rec_fld_")}
    studio.update({"x_studio_is_mukerrer": True, "x_studio_vkn_tckn": "1234567890", "x_fis_no": "S-9", "x_studio_onay_durumu": "muhasebe"})
    so = expenses.to_object(studio)
    assert so["problems"] == ["DUPLICATE"] and so["receipt_no"] == "S-9" and so["state_label"] == "Muhasebe onayında"
    # iptal / reddedilen fiş için Case açılmaz
    assert expenses.to_object(_expense(10, rec_fld_is_mukerrer=True, rec_fld_onay_durumu="iptal_edildi"))["has_problem"] is False
    assert expenses.to_object(_expense(11, rec_fld_is_mukerrer=True, rec_fld_onay_durumu=False, state="refused"))["has_problem"] is False
    # Odoo'nun fiş okuması doğrulama bekliyorsa
    assert expenses.to_object(_expense(12, extract_state="waiting_validation"))["problems"] == ["LOW_CONFIDENCE"]


def test_recslip_presets_problem_case_month_end_and_note(client, db, world, slip, monkeypatch):
    from app.services.evren_client import ChatResult, evren_client

    w = world
    h = w["admin"]["h"]
    T = f"/api/v1/company/{w['tenant']}"
    _seed(client)
    _seed_templates(client)
    cid = _odoo_conn(client, w)

    # RECSlip açık değilken: hazır eşleme görünmez, kural kurulamaz; bilinmeyen uygulama yok
    _exec(db, "UPDATE tenants SET settings = coalesce(settings, '{}'::jsonb) - 'recdx_apps' WHERE id = %s", w["tenant"])
    db.commit()
    assert "odoo_expense" not in {t["code"] for t in client.get(f"{T}/mappings/templates", headers=h).json()}
    st = client.get(f"{T}/automations/presets/recslip", headers=h).json()
    assert st["available"] is False and "RECSlip" in st["reason"]
    assert {c["code"] for c in st["categories"]} == {"PROBLEM", "MONTH_END"}
    body = {"connection_id": cid, "manager_actor_id": w["admin"]["id"]}
    assert client.post(f"{T}/automations/presets/recslip", headers=h, json=body).status_code == 409
    assert client.get(f"{T}/automations/presets/yok", headers=h).status_code == 404
    assert client.get(f"{T}/automations/presets/recslip", headers=w["member"]["h"]).status_code == 403

    _exec(db, "UPDATE tenants SET settings = coalesce(settings, '{}'::jsonb) || %s::jsonb WHERE id = %s",
          json.dumps({"recdx_apps": {"has_odoo": True, "apps": {"recslip": "USING"}}}), w["tenant"])
    db.commit()
    assert "odoo_expense" in {t["code"] for t in client.get(f"{T}/mappings/templates", headers=h).json()}
    r = client.post(f"{T}/automations/presets/recslip", headers=h, json=body)
    assert r.status_code == 201, r.text
    out = r.json()
    rules = {x["trigger"]: x for x in out["rules"]}
    assert set(rules) == {"POLL", "SCHEDULE"} and out["mapping"]["status"] == "DRAFT"
    prob, month = rules["POLL"], rules["SCHEDULE"]
    assert prob["poll"]["enrich"] == "hr_expense" and prob["poll"]["version_field"] == "slip.problem_key"
    assert prob["conditions"] == [{"field": "slip.has_problem", "op": "eq", "value": True}]
    assert prob["action"]["transfer_on_close"] == [out["mapping"]["id"]]
    assert month["schedule"] == {"every": "MONTH", "time": "10:00", "day": -1, "summary": "expense_month"}
    again = client.post(f"{T}/automations/presets/recslip", headers=h, json=body).json()
    assert again["rules"] == [] and sum("zaten kurulu" in n for n in again["notes"]) == 2

    # Örnek fişle deneme: ortak nesne eklenir, hiçbir şey açılmaz
    test = client.post(f"{T}/automations/{prob['id']}/test", headers=h,
                       json={"payload": _expense(900, rec_fld_is_mukerrer=True)}).json()
    assert test["outcome"] == "TEST", test

    # İzleme: ilk tur başlangıç; sorunlu yeni fiş Case açar, sorunsuz fiş açmaz
    run = f"{T}/automations/{prob['id']}/run"
    assert client.post(run, headers=h).json()["baseline"] is True
    slip["expenses"][2] = _expense(2, name="Taksi", rec_fld_vkn_tckn=False, total_amount=480.0)
    slip["expenses"][3] = _expense(3, name="Kırtasiye")
    res = client.post(run, headers=h).json()
    assert sorted(x["outcome"] for x in res["handled"]) == ["DRAFTED", "IGNORED"], res
    pid = next(x["project_id"] for x in res["handled"] if x["outcome"] == "DRAFTED")
    name, kind, ref, toc, reqs, tpl = _exec(
        db, "SELECT name, kind, source_ref, transfer_on_close::text, requirements, template_id::text FROM projects WHERE id = %s", pid)
    assert name == "Sorunlu fiş: Taksi · 480.0 TRY (masraf #2)" and kind == "CASE", name
    assert ref == "odoo:hr.expense:2" and json.loads(toc) == [out["mapping"]["id"]] and "Satıcı VKN/TCKN yok" in reqs
    assert _exec(db, "SELECT code FROM project_templates WHERE id = %s", tpl)[0] == "recslip-sorunlu-fis"
    assert client.get(f"/api/v1/projects/{pid}", headers=h).json()["source_label"] == "Odoo masraf #2"
    # aynı sorun tekrar Case açmaz; sorun listesi değişince yeniden değerlendirilir
    assert client.post(run, headers=h).json()["new"] == 0
    slip["expenses"][2]["rec_fld_is_mukerrer"] = True
    again = client.post(run, headers=h).json()
    assert again["new"] == 1 and again["handled"][0]["outcome"] == "DRAFTED"

    # Ay sonu kuralı hemen çalıştırılır: dönem özetiyle kapanış Case'i
    m = client.post(f"{T}/automations/{month['id']}/run", headers=h)
    assert m.status_code == 200, m.text
    (mres,) = m.json()["handled"]
    assert mres["outcome"] == "DRAFTED", mres
    mname, mreqs, mtpl = _exec(db, "SELECT name, requirements, template_id::text FROM projects WHERE id = %s", mres["project_id"])
    assert mname == f"Ay sonu masraf kapanışı {TODAY[:7]}" and "3 fiş, toplam 980,00" in mreqs and "Sorunlu fiş: 1" in mreqs, mreqs
    assert _exec(db, "SELECT code FROM project_templates WHERE id = %s", mtpl)[0] == "recslip-ay-sonu"

    # Eşleme denenir ve onaylanır (deneme yazmaz)
    mid = out["mapping"]["id"]
    dry = client.post(f"{T}/mappings/{mid}/dry-run", headers=h, json={}).json()
    assert dry["ok"], dry
    assert client.post(f"{T}/mappings/{mid}/approve", headers=h).status_code == 200
    assert not any(m_ in ("write", "create", "message_post") for _, m_, _ in slip["calls"])

    # Case kararı: masrafa bağlı tek öneri; tutar/açıklama ezilmez, karar iç not olarak yazılır
    async def chat(model_code, messages, **kw):
        return ChatResult(json.dumps({"items": [{"description": "ezilmemeli", "total_amount": 1, "resolution": ""}]}), None, 500, 200, {})
    monkeypatch.setattr(evren_client, "chat", chat)

    async def text(db_, project):
        return "Case özeti."
    monkeypatch.setattr(tsvc, "project_text", text)
    _exec(db, "UPDATE projects SET status = 'COMPLETED', close_summary = %s WHERE id = %s",
          "Satıcı VKN'si fişten okundu: 1234567890.\nGider yazılabilir.", pid)
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
    assert tr["status"] == "PENDING_APPROVAL" and tr["action"] == "UPDATE" and tr["object"]["expense_ref"] == "2", tr
    assert [p["target"] for p in tr["preview"]] == ["(iç not)"], tr["preview"]
    assert client.post(f"/api/v1/transfers/{tr['id']}/decision", headers=h, json={"approve": True}).status_code == 200
    end = time.time() + 30
    while time.time() < end and client.get(f"/api/v1/transfers/{tr['id']}", headers=h).json()["status"] != "DONE":
        time.sleep(0.4)
    done = client.get(f"/api/v1/transfers/{tr['id']}", headers=h).json()
    assert done["status"] == "DONE" and done["external_id"] == "2", done
    e2 = slip["expenses"][2]
    assert e2["name"] == "Taksi" and e2["total_amount"] == 480.0
    (ids, note, subtype), = slip["notes"]
    assert ids == [2] and subtype == "mail.mt_note" and "fişten okundu: 1234567890.<br/>Gider" in note and "RECOrion Case kararı" in note
