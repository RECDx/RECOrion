"""
RECSlip.App v2 aylık masraf süreci (ADIM 14). Odoo yerine sahte bir RECSlip v2 sunucusu, EVREN yerine sahte RECAi:Mergen.

- Kişisel anahtar (Bağlantılarım): denenir, kasada saklanır, asla geri dönmez; geçersiz anahtar kaydedilmez.
- Kurulum: Case yöneticisinin anahtarı şart; 7 adımlı aylık Case açılır ve başlar; ayarlar varsayılanlarla.
- Yönetici adımı: kriterlere uyan fiş kişinin anahtarıyla AI onayı; uymayan Onaylarım'a düşer, insan kararı kendi anahtarıyla.
- Muhasebe adımı: onaylı kaynaklı kalem güvenli; Mergen farklı ve güvenli → düzeltme + onay; emin değilse insana.
- Anahtarı olmayan onaylayıcının adımına dokunulmaz; ayarlar sınırlanır, yalnızca Case yöneticisi değiştirir.
- Kesim ve aktarım: S1/S4 kesimde, S5 aktarım zamanında teslim edilir; dosya Case'e eklenir.
"""
import base64
import json
import time
import uuid
from datetime import date, datetime, timedelta, timezone

import pytest

from app.integrations import odoo
from app.integrations.base import ToolError
from app.services import llm_gateway, storage
from tests.test_workflow import _exec, world  # noqa: F401  (fikstür)

KEYS = {"key-admin": 2, "key-yonetici": 10, "key-muhasebeci": 9}


class FakeV2:
    """RECSlip v2'nin RECOrion'un kullandığı uçları (JSON-2 _kw düzeyinde)."""

    def __init__(self):
        self.version = "20.0.2.34.0"
        self.expenses, self.lines, self.steps, self.calls, self.exports = {}, {}, {}, [], {}
        self.candidates = {"770012": 501, "760099": 502}
        self.export_state = "exported"

    def add(self, eid, amount, roles, lines, risk="none", date_="2026-11-10", **extra):
        self.expenses[eid] = {"id": eid, "name": f"Fiş {eid}", "date": date_, "total_amount_currency": amount, "currency_id": [1, "TRY"],
                              "employee_id": [7, "Test Çalışanı"], "product_id": [3, "Yemek"], "rs_state": "approval",
                              "rs_doc_type": "okc_fisi", "rs_confidence": 95, "rs_risk_level": risk, "rs_risk_notes": False,
                              "rs_is_duplicate": False, "rs_balance_ok": True, **extra}
        for i, (role, uid) in enumerate(roles):
            sid = eid * 10 + i
            self.steps[sid] = {"id": sid, "expense_id": [eid, f"Fiş {eid}"], "role": role, "user_ids": [uid],
                               "state": "pending" if i == 0 else "waiting", "pending_since": False, "seq": i}
        for ln in lines:
            self.lines[ln["id"]] = {"expense_id": [eid, f"Fiş {eid}"], "vat_rate": 20, "needs_review": False, "not_expense": False,
                                    "ai_reason": False, "confidence": 90, **ln}

    def _step(self, eid):
        return next((s for s in sorted(self.steps.values(), key=lambda s: s["seq"]) if s["expense_id"][0] == eid and s["state"] == "pending"), None)

    async def kw(self, ctx, model, method, args, kw=None):
        kw = kw or {}
        key = ctx.secrets.get("api_key") or "key-admin"
        if key not in KEYS:
            raise ToolError("Odoo API anahtarı geçersiz veya süresi dolmuş.")
        uid = KEYS[key]
        self.calls.append((uid, model, method, args, kw))
        if (model, method) == ("res.users", "context_get"):
            return {"uid": uid}
        if (model, method) == ("res.users", "read"):
            return [{"id": uid, "login": {2: "admin", 9: "muhasebeci@recdx.com", 10: "yonetici@recdx.com"}[uid], "name": f"Kullanıcı {uid}"}]
        if (model, method) == ("ir.module.module", "search_read"):
            return [{"installed_version": self.version}]
        if (model, method) == ("recslip.approval", "search_read"):
            return [{k: v for k, v in s.items() if k != "seq"} for s in self.steps.values() if s["state"] == "pending"]
        if (model, method) == ("hr.expense", "read"):
            return [dict(self.expenses[i]) for i in args[0] if i in self.expenses]
        if (model, method) == ("recslip.expense.line", "search_read"):
            ids = args[0][0][2]
            return [{"id": lid, **ln} for lid, ln in self.lines.items() if ln["expense_id"][0] in ids]
        if (model, method) == ("hr.expense", "search_read"):
            dom = {d[0]: d[2] for d in args[0]}
            if "employee_id" in dom:
                return [{"total_amount_currency": e["total_amount_currency"]} for e in self.expenses.values()]
            states = dom.get("rs_state")
            states = states if isinstance(states, list) else [states]
            return [{"id": e["id"], "name": e["name"], "employee_id": e["employee_id"], "total_amount_currency": e["total_amount_currency"]}
                    for e in self.expenses.values() if e["rs_state"] in states]
        if (model, method) == ("hr.expense", "search_count"):
            states = {d[0]: d[2] for d in args[0]}.get("rs_state")
            return sum(1 for e in self.expenses.values() if e["rs_state"] == states)
        if (model, method) == ("hr.expense", "rs_external_mergen_inputs"):
            assert uid == 9, "Mergen girdisi muhasebecinin anahtarıyla istenir"
            return {"system": "MERGEN PROMPT {KALEMLER}", "schema": {}, "candidates": self.candidates, "line_ids": kw["line_ids"]}
        if (model, method) in (("hr.expense", "rs_external_approve"), ("hr.expense", "rs_external_refuse")):
            eid = args[0][0]
            step = self._step(eid)
            if not step or uid not in step["user_ids"]:
                raise ToolError(f"Odoo: You are not an approver of 'Fiş {eid}' at this step.")
            for lid, acc in (kw.get("line_accounts") or {}).items():
                self.lines[int(lid)]["account_id"] = [acc, f"Hesap {acc}"]
            step.update(state="approved" if method == "rs_external_approve" else "refused", agent=kw.get("agent"), reason=kw.get("reason"))
            nxt = next((s for s in sorted(self.steps.values(), key=lambda s: s["seq"]) if s["expense_id"][0] == eid and s["state"] == "waiting"), None)
            if method == "rs_external_refuse":
                self.expenses[eid]["rs_state"] = "refused"
            elif nxt:
                nxt["state"] = "pending"
            else:
                self.expenses[eid]["rs_state"] = "done"
            return [{"id": eid, "rs_state": self.expenses[eid]["rs_state"]}]
        if (model, method) == ("hr.expense", "rs_external_export"):
            assert uid == 9
            if getattr(self, "fail_export", 0):  # geçici hata (tekrar aralığı denemesi)
                self.fail_export -= 1
                raise ToolError("Odoo: geçici bağlantı hatası")
            for i in args[0]:
                self.expenses[i]["rs_state"] = "exported"
            self.exports[77] = {"state": "exported"}
            return {"export_id": 77, "name": "RECSlip_Luka_1_2026-12-05.xls", "software": "luka", "receipt_count": len(args[0]),
                    "total": 120.0, "attachment_id": 88, "not_exported_ids": []}
        if (model, method) == ("ir.attachment", "read"):
            return [{"name": "RECSlip_Luka_1_2026-12-05.xls", "datas": base64.b64encode(b"<table>luka</table>").decode()}]
        if (model, method) == ("recslip.export", "read"):
            return [{"state": self.export_state}]
        raise AssertionError(f"beklenmeyen çağrı {model}.{method}")


class FakeMergen:
    def __init__(self):
        self.answers, self.calls = {}, 0

    async def chat(self, ctx, messages, **kw):
        self.calls += 1
        items = [{"id": lid, "hesap_kodu": code, "guven": conf, "gerekce": "Yemek gideri", "inceleme_gerekli": conf < 0.6}
                 for lid, (code, conf) in self.answers.items()]
        return type("R", (), {"content": json.dumps({"kalemler": items}), "fallback_from": None})()


@pytest.fixture
def v2(monkeypatch):
    fake, mergen, objects = FakeV2(), FakeMergen(), {}

    async def put_object(key, data, content_type=None):
        objects[key] = data

    monkeypatch.setattr(odoo, "_kw", fake.kw)
    monkeypatch.setattr(llm_gateway, "chat", mergen.chat)
    monkeypatch.setattr(storage, "put_object", put_object)
    fake.mergen, fake.objects = mergen, objects
    return fake


@pytest.fixture(scope="module")
def slip(world, db):
    w = world
    conn = _exec(db, "INSERT INTO integration_connections (tenant_id, connector, name, config, status) VALUES (%s, 'odoo', %s, %s::jsonb, 'ACTIVE') "
                     "RETURNING id::text", w["tenant"], f"RECSlip v2 {uuid.uuid4().hex[:4]}",
                 json.dumps({"url": "https://v2-staging.example.com", "db": "stg"}))[0]
    db.commit()
    return {"conn": conn}


def _cred(client, h, conn, key, agent=None):
    return client.post("/api/v1/me/credentials", headers=h, json={"connection_id": conn, "api_key": key, "agent_actor_id": agent,
                                                                  "expires_at": (datetime.now(timezone.utc) + timedelta(days=90)).isoformat()})


def test_personal_credential_is_tested_and_never_returned(client, world, slip, v2):
    w = world
    bad = _cred(client, w["member"]["h"], slip["conn"], "yanlis-anahtar")
    assert bad.status_code == 400 and "denenemedi" in bad.json()["detail"]
    r = _cred(client, w["member"]["h"], slip["conn"], "key-yonetici", w["agent"])
    assert r.status_code == 201, r.text
    c = r.json()
    assert c["external_uid"] == 10 and c["external_login"] == "yonetici@recdx.com" and c["usable"] and c["has_key"]
    assert "key-yonetici" not in json.dumps(client.get("/api/v1/me/credentials", headers=w["member"]["h"]).json())
    assert client.get("/api/v1/me/credentials", headers=w["outsider"]["h"]).json()["credentials"] == []
    assert client.get(f"/api/v1/company/{w['tenant']}/credentials", headers=w["outsider"]["h"]).status_code == 403
    listed = client.get(f"/api/v1/company/{w['tenant']}/credentials", headers=w["admin"]["h"]).json()
    assert any(x["external_login"] == "yonetici@recdx.com" for x in listed) and "key-yonetici" not in json.dumps(listed)


def test_setup_needs_manager_key_then_opens_monthly_case(client, world, slip, v2, db):
    w = world
    body = {"connection_id": slip["conn"], "manager_actor_id": w["admin"]["id"], "report_agent_id": w["reviewer"], "report_approver_id": w["admin"]["id"]}
    r = client.post(f"/api/v1/company/{w['tenant']}/recslip/setup", headers=w["admin"]["h"], json=body)
    assert r.status_code == 400 and "anahtar" in r.json()["detail"]
    assert _cred(client, w["admin"]["h"], slip["conn"], "key-muhasebeci", w["reviewer"]).status_code == 201
    v2.version = "20.0.2.30.0"
    assert client.post(f"/api/v1/company/{w['tenant']}/recslip/setup", headers=w["admin"]["h"], json=body).status_code == 400  # eski v2
    v2.version = "20.0.2.34.0"
    r = client.post(f"/api/v1/company/{w['tenant']}/recslip/setup", headers=w["admin"]["h"], json=body)
    assert r.status_code == 201, r.text
    case = r.json()
    assert case["name"].startswith("RECSlip masraf süreci ") and case["settings"]["poll_minutes"] == 15
    assert case["settings"]["criteria"]["manager"]["max_amount"] == 2500
    slip["case"] = case["project_id"]
    titles = [t[0] for t in _exec_all(db, "SELECT title FROM tasks WHERE project_id = %s ORDER BY order_index", case["project_id"])]
    assert titles[0] == "Fiş takibi ve AI onay yürütme" and titles[-1] == "Kapanış raporu" and len(titles) == 7
    # aynı dönem ikinci kez açılmaz
    assert client.post(f"/api/v1/company/{w['tenant']}/recslip/setup", headers=w["admin"]["h"], json=body).json()["project_id"] == case["project_id"]


def _exec_all(db, sql, *params):
    with db.cursor() as cur:
        cur.execute(sql, params)
        return cur.fetchall()


def test_manager_agent_approves_within_criteria_human_decides_the_rest(client, world, slip, v2):
    w = world
    v2.add(101, 120.0, [("manager", 10), ("accountant", 9)], [{"id": 1011, "name": "KAHVE", "amount_total": 120, "account_id": [501, "770012"], "match_source": "memory"}])
    v2.add(102, 9000.0, [("manager", 10)], [{"id": 1021, "name": "OTEL", "amount_total": 9000, "account_id": [501, "770012"], "match_source": "memory"}])
    v2.add(103, 50.0, [("manager", 55)], [{"id": 1031, "name": "SU", "amount_total": 50, "account_id": [501, "770012"], "match_source": "memory"}])
    r = client.post(f"/api/v1/company/{w['tenant']}/recslip/run", headers=w["admin"]["h"])
    assert r.status_code == 200, r.text
    step = v2.steps[1010]
    assert step["state"] == "approved" and step["agent"] == "Kodcu", "yöneticinin AI personeli kendi anahtarıyla onayladı"
    assert v2.steps[1020]["state"] == "pending", "sınırı aşan fiş insana düştü"
    assert v2.steps[1030]["state"] == "pending" and not any(c[3] == [[103]] and "rs_external" in c[2] for c in v2.calls), "anahtarı olmayana dokunulmaz"
    mine = client.get("/api/v1/me/recslip-decisions", headers=w["member"]["h"]).json()
    assert [d["expense_id"] for d in mine] == [102] and "sınırı" in mine[0]["reasons"][0]
    assert client.post(f"/api/v1/recslip-decisions/{mine[0]['id']}/decide", headers=w["admin"]["h"], json={"approve": True}).status_code == 403
    r = client.post(f"/api/v1/recslip-decisions/{mine[0]['id']}/decide", headers=w["member"]["h"], json={"approve": False})
    assert r.status_code == 400  # red gerekçesiz olmaz
    r = client.post(f"/api/v1/recslip-decisions/{mine[0]['id']}/decide", headers=w["member"]["h"], json={"approve": True, "note": "Fuar oteli"})
    assert r.status_code == 200 and r.json()["status"] == "HUMAN_APPROVED"
    assert v2.steps[1020]["state"] == "approved" and v2.steps[1020]["agent"] is None, "insan kararı: AI bayrağı yok"


def test_accountant_agent_safe_lines_second_opinion_and_correction(client, world, slip, v2):
    w = world
    v2.add(201, 300.0, [("accountant", 9)], [{"id": 2011, "name": "KAHVE", "amount_total": 300, "account_id": [501, "770012"], "match_source": "exact"}])
    v2.add(202, 400.0, [("accountant", 9)], [{"id": 2021, "name": "TONER", "amount_total": 400, "account_id": [501, "770012"], "match_source": "ai"}])
    v2.add(203, 400.0, [("accountant", 9)], [{"id": 2031, "name": "BELİRSİZ", "amount_total": 400, "account_id": [501, "770012"], "match_source": "rag"}])
    v2.mergen.answers = {2021: ("760099", 0.95), 2031: ("760099", 0.5)}
    assert client.post(f"/api/v1/company/{w['tenant']}/recslip/run", headers=w["admin"]["h"]).status_code == 200
    assert v2.steps[2010]["state"] == "approved", "onaylı kaynaktan gelen kalem: ikinci görüşsüz onay"
    assert v2.steps[2020]["state"] == "approved" and v2.lines[2021]["account_id"][0] == 502, "Mergen güvenli farklı hesap: düzeltme + onay"
    assert v2.steps[2030]["state"] == "pending", "Mergen emin değil: insana"
    case = client.get(f"/api/v1/projects/{slip['case']}/recslip", headers=w["admin"]["h"]).json()
    by_exp = {d["expense_id"]: d for d in case["decisions"]}
    assert by_exp[202]["corrections"][0]["new"] == "760099" and by_exp[202]["status"] == "AUTO_DONE"
    assert by_exp[203]["status"] == "PENDING" and by_exp[203]["role_label"] == "Muhasebe"


def test_settings_are_clamped_and_only_the_case_manager_changes_them(client, world, slip, v2):
    w = world
    r = client.put(f"/api/v1/projects/{slip['case']}/recslip", headers=w["member"]["h"], json={"settings": {"poll_minutes": 1}})
    assert r.status_code in (403, 404)
    r = client.put(f"/api/v1/projects/{slip['case']}/recslip", headers=w["admin"]["h"], json={"settings": {
        "poll_minutes": 1, "export": {"day": 40, "time": "25:00"}, "retry": {"count": 2, "interval_hours": 12},
        "criteria": {"accountant": {"approve_all": True, "safe_sources": ["memory", "uydurma"]}}, "uydurma": 1}})
    assert r.status_code == 200, r.text
    s = r.json()["settings"]
    assert s["poll_minutes"] == 5 and s["export"] == {"day": 28, "time": "10:00"} and s["retry"] == {"count": 2, "interval_hours": 12}
    assert s["criteria"]["accountant"]["approve_all"] is True and s["criteria"]["accountant"]["safe_sources"] == ["memory"]
    assert "uydurma" not in s and s["criteria"]["manager"]["max_amount"] == 2500


def test_unsent_receipt_and_key_expiry_reminders(client, world, slip, v2, db, monkeypatch):
    """HATA #591: okunup onaya gönderilmeyen fiş için Case yöneticisine N günde bir; anahtar bitişine 14 gün kala ve bitince birer kez."""
    import asyncio

    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
    from sqlalchemy.pool import NullPool

    from app.config import settings
    from app.services import recslip as rs
    from app.services import recslip_case as rc

    sent = []

    async def fake_notify(db_, actor_ids, text):
        sent.append(([str(a) for a in actor_ids], text))
    monkeypatch.setattr(rc, "_notify", fake_notify)
    Session = async_sessionmaker(create_async_engine(settings.DATABASE_URL, poolclass=NullPool), expire_on_commit=False)

    async def run(fn, at):
        async with Session() as s:
            from app.db.models import IntegrationConnection, Project
            p = await s.get(Project, uuid.UUID(slip["case"]))
            conn = await s.get(IntegrationConnection, uuid.UUID(slip["conn"]))
            return await (rc.advance(s, conn, p, at) if fn == "advance" else rc.remind_keys(s, conn, p, at))

    period = _exec(db, "SELECT settings->>'period' FROM projects WHERE id = %s", slip["case"])[0]
    cal = rs.calendar_of(period, rs.DEFAULT_SETTINGS)
    v2.add(401, 50.0, [], [], rs_state="analyzed")
    t0 = cal["cutoff"] - timedelta(days=10)
    asyncio.run(run("advance", t0))
    unsent = [x for x in sent if "onaya gönderilmedi" in x[1]]
    assert len(unsent) == 1 and "Fiş 401" in unsent[0][1] and unsent[0][0] == [w_id := world["admin"]["id"]]
    asyncio.run(run("advance", t0 + timedelta(hours=5)))
    assert len([x for x in sent if "onaya gönderilmedi" in x[1]]) == 1, "aralık dolmadan tekrar yok"
    asyncio.run(run("advance", t0 + timedelta(days=2, minutes=1)))
    assert len([x for x in sent if "onaya gönderilmedi" in x[1]]) == 2
    v2.expenses[401]["rs_state"] = "approval"

    # Anahtar bitişi: 14 gün kala bir kez, bitince bir kez
    now = rs.now()
    _exec(db, "UPDATE personal_credentials SET expires_at = %s WHERE connection_id = %s AND actor_id = %s",
          now + timedelta(days=5), slip["conn"], w_id)
    assert asyncio.run(run("keys", now)) == 1 and asyncio.run(run("keys", now + timedelta(hours=1))) == 0
    assert asyncio.run(run("keys", now + timedelta(days=6))) == 1
    keys = [x for x in sent if "anahtarınızın süresi" in x[1]]
    assert len(keys) == 2 and "doluyor" in keys[0][1] and "doldu" in keys[1][1] and keys[0][0] == [w_id]
    _exec(db, "UPDATE personal_credentials SET expires_at = %s WHERE connection_id = %s AND actor_id = %s",
          now + timedelta(days=90), slip["conn"], w_id)


def test_cutoff_and_export_submit_steps_and_attach_the_file(client, world, slip, v2, db):
    import asyncio

    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
    from sqlalchemy.pool import NullPool

    from app.config import settings
    from app.services import recslip as rs
    from app.services import recslip_case as rc

    # test kendi döngüsünde çalışır: uygulamanın havuzu yerine havuzsuz ayrı bağlantı
    AsyncSessionLocal = async_sessionmaker(create_async_engine(settings.DATABASE_URL, poolclass=NullPool), expire_on_commit=False)

    w = world
    period = _exec(db, "SELECT settings->>'period' FROM projects WHERE id = %s", slip["case"])[0]
    deadline = time.time() + 30  # S1-S4 adımları akışta çalışmaya başlasın
    while time.time() < deadline and (_exec(db, "SELECT count(*) FROM tasks WHERE project_id = %s AND status = 'IN_PROGRESS'", slip["case"])[0] or 0) < 4:
        time.sleep(0.5)

    async def advance(at):
        async with AsyncSessionLocal() as s:
            from app.db.models import IntegrationConnection, Project
            p = await s.get(Project, uuid.UUID(slip["case"]))
            conn = await s.get(IntegrationConnection, uuid.UUID(slip["conn"]))
            return await rc.advance(s, conn, p, at)

    def until(at, keys, timeout=40):
        """Adımlar akışta sırayla açılır: istenen adımlar teslim edilene kadar ilerletilir."""
        done, end = set(), time.time() + timeout
        while time.time() < end and not keys <= done:
            done |= set(asyncio.run(advance(at))["done"])
            time.sleep(0.5)
        return done

    cal = rs.calendar_of(period, rs.DEFAULT_SETTINGS)
    assert asyncio.run(advance(cal["cutoff"] - timedelta(minutes=1)))["done"] == [], "kesimden önce teslim yok"
    assert {"S1", "S4"} <= until(cal["cutoff"] + timedelta(minutes=1), {"S1", "S4"})
    v2.add(301, 120.0, [], [{"id": 3011, "name": "KAHVE", "amount_total": 120, "account_id": [501, "770012"], "match_source": "memory"}])
    v2.expenses[301]["rs_state"] = "done"  # tamamlanmış fiş: aktarılacak
    export_at = rs.calendar_of(period, {**rs.DEFAULT_SETTINGS, "export": {"day": 28, "time": "10:00"}})["export"] + timedelta(minutes=1)
    # İlk deneme başarısız: tekrar aralığı (24 saat) dolmadan yeniden denenmez (HATA #590)
    v2.fail_export = 1
    assert {"S2", "S3"} <= until(export_at, {"S2", "S3"})
    for _ in range(3):
        assert "S5" not in asyncio.run(advance(export_at + timedelta(hours=1)))["done"]
    assert _exec(db, "SELECT attempts FROM recslip_exports WHERE project_id = %s", slip["case"])[0] == 1
    export_at += timedelta(hours=25)
    assert "S5" in until(export_at, {"S5"})
    assert _exec(db, "SELECT attempts FROM recslip_exports WHERE project_id = %s", slip["case"])[0] == 2
    exp = _exec(db, "SELECT status, name, artifact_id, odoo_export_id FROM recslip_exports WHERE project_id = %s", slip["case"])
    # #658 (kullanıcı kararı): dosya RECOrion'a alınmaz; RECSlip'te kalır, Case adını ve v2 kaydını tutar
    assert exp[0] == "CREATED" and exp[1].startswith("RECSlip_Luka") and exp[2] is None and exp[3]
    assert not any(v == b"<table>luka</table>" for v in v2.objects.values()), "dosya içeriği RECOrion'a çekilmez"
    case = client.get(f"/api/v1/projects/{slip['case']}/recslip", headers=w["admin"]["h"]).json()
    assert case["export"]["odoo_link"].endswith(f"/odoo/recslip.export/{exp[3]}")
    path = r"C:\Muhasebe\RECSlip\RECSlip_Luka_1.xls"
    assert client.put(f"/api/v1/projects/{slip['case']}/recslip/export-path", headers=w["member"]["h"], json={"local_path": path}).status_code in (403, 404)
    r = client.put(f"/api/v1/projects/{slip['case']}/recslip/export-path", headers=w["admin"]["h"], json={"local_path": path})
    assert r.status_code == 200 and r.json()["export"]["local_path"] == path, r.text
    v2.export_state = "posted"
    assert "S6" in until(export_at + timedelta(hours=1), {"S6"})
    desc = _exec(db, "SELECT description FROM tasks WHERE project_id = %s AND order_index = 7", slip["case"])[0]
    assert "DÖNEM VERİSİ" in desc and "Aktarım: RECSlip_Luka" in desc, "kapanış raporunu yazacak AI personele dönem verisi"
