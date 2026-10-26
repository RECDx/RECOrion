"""
ADIM 13.2: olayla başlayan işler.

- İmzalı anlık bildirim: imzasız / yanlış imzalı / eski istek reddedilir (günlüğe yazılır); koşul sağlanmazsa iş açılmaz;
  sağlanırsa Case TASLAK açılır, isterler olay verisiyle dolar, yöneticiye bildirilir; aynı olay ikinci kez işlenmez;
  RECOrion'un kendi kaydından gelen olay iş açmaz (döngü); saatlik sınır aşılınca durur.
- İzleme: ilk tur yalnızca başlangıç noktası; sonra yalnızca yeni/değişen kayıt iş açar; RECOrion'un yazdığı kayıt açmaz.
- Zamanlayıcı: haftalık ve ay sonu doğru hesaplanır. Deneme hiçbir şey açmaz. Günlük silinemez. KVKK: RECDx göremez.
"""
import json
import time
import uuid
from datetime import datetime, timezone

import pytest

from app.services import automations as svc
from tests.test_integrations import _super
from tests.test_workflow import _exec, world  # noqa: F401  (fikstür)


def _rule(client, w, **over):
    body = {"name": f"İade talebi {uuid.uuid4().hex[:4]}", "trigger": "WEBHOOK", "event_type": "ticket.created",
            "conditions": [{"field": "priority", "op": "eq", "value": "high"}],
            "action": {"type": "CREATE_CASE", "name": "İade: {{customer.name}} #{{id}}", "manager_actor_id": w["admin"]["id"],
                       "plan_with_recai": False},
            "requirements": "{{customer.name}} müşterisinin iade talebini incele ve yanıtla.", **over}
    r = client.post(f"/api/v1/company/{w['tenant']}/automations", headers=w["admin"]["h"], json=body)
    assert r.status_code == 201, r.text
    return r.json()


def _hook(client, rule, secret, payload, ts=None, event="ticket.created", delivery=None):
    body = json.dumps(payload).encode()
    ts = str(ts or int(time.time()))
    h = {"X-RECOrion-Timestamp": ts, "X-RECOrion-Signature": svc.sign(secret, ts, body), "X-RECOrion-Event": event,
         "Content-Type": "application/json"}
    if delivery:
        h["X-RECOrion-Delivery"] = delivery
    return client.post(f"/api/v1/hooks/{rule['id']}", content=body, headers=h)


def test_signed_webhook_opens_draft_case_once(client, db, world):
    w = world
    rule = _rule(client, w)
    secret = rule.pop("webhook_secret")
    assert secret.startswith("rxw_") and rule["webhook_url"].endswith(f"/api/v1/hooks/{rule['id']}")
    listed = client.get(f"/api/v1/company/{w['tenant']}/automations", headers=w["admin"]["h"])
    assert secret not in listed.text and "webhook_secret" not in listed.text  # anahtar bir kez gösterilir

    # yetki ve KVKK
    assert client.get(f"/api/v1/company/{w['tenant']}/automations", headers=w["member"]["h"]).status_code == 403
    assert client.get(f"/api/v1/company/{w['tenant']}/automations", headers=_super(client, db)).status_code == 403

    good = {"id": 42, "priority": "high", "customer": {"name": "Ayşe Yılmaz"}}
    # imzasız, yanlış imza, eski istek
    assert client.post(f"/api/v1/hooks/{rule['id']}", json=good).status_code == 401
    assert _hook(client, rule, "rxw_yanlis", good).status_code == 401
    assert _hook(client, rule, secret, good, ts=int(time.time()) - 3600).status_code == 401
    assert client.post(f"/api/v1/hooks/{uuid.uuid4()}", json=good).status_code == 404

    # koşul sağlanmıyor
    r = _hook(client, rule, secret, {**good, "id": 41, "priority": "low"})
    assert r.status_code == 202 and r.json()["outcome"] == "IGNORED"
    # olay türü uymuyor
    assert _hook(client, rule, secret, good, event="ticket.closed").json()["outcome"] == "IGNORED"

    r = _hook(client, rule, secret, good)
    assert r.status_code == 202 and r.json()["outcome"] == "DRAFTED", r.text
    pid = r.json()["project_id"]
    name, kind, status, reqs, src, mgr = _exec(db, "SELECT name, kind, status, requirements, source_ref, manager_actor_id::text "
                                                    "FROM projects WHERE id = %s", pid)
    assert name == "İade: Ayşe Yılmaz #42" and kind == "CASE" and status == "DRAFT" and mgr == w["admin"]["id"]
    assert "Ayşe Yılmaz müşterisinin iade talebini" in reqs and "priority: high" in reqs and src == "ticket.created:42"

    # aynı olay ikinci kez gelirse işlenmez
    assert _hook(client, rule, secret, good).json()["outcome"] == "DUPLICATE"
    # RECOrion'un kendi kaydından gelen olay (kaynak işareti) iş açmaz
    assert _hook(client, rule, secret, {**good, "id": 43, "x_recorion_origin": True}).json()["outcome"] == "LOOP"

    log = client.get(f"/api/v1/company/{w['tenant']}/automations/{rule['id']}/log", headers=w["admin"]["h"]).json()
    outcomes = [x["outcome"] for x in log]
    assert outcomes.count("REJECTED") == 3 and outcomes.count("DRAFTED") == 1 and "DUPLICATE" in outcomes and "LOOP" in outcomes
    assert all("rxw_" not in json.dumps(x) for x in log)

    # günlük silinemez / değiştirilemez
    with pytest.raises(Exception, match="değiştirilemez"):
        _exec(db, "UPDATE automation_log SET outcome = 'X' WHERE rule_id = %s", rule["id"])
    db.rollback()
    with pytest.raises(Exception, match="silinemez"):
        _exec(db, "DELETE FROM automation_log WHERE rule_id = %s", rule["id"])
    db.rollback()

    # anahtar yenilenince eski anahtar geçmez
    new = client.post(f"/api/v1/company/{w['tenant']}/automations/{rule['id']}/rotate-secret", headers=w["admin"]["h"]).json()
    assert _hook(client, rule, secret, {**good, "id": 44}).status_code == 401
    assert _hook(client, rule, new["webhook_secret"], {**good, "id": 44}).json()["outcome"] == "DRAFTED"

    # duraklatılan kural iş açmaz
    client.post(f"/api/v1/company/{w['tenant']}/automations/{rule['id']}/status", headers=w["admin"]["h"], json={"status": "PAUSED"})
    assert _hook(client, rule, new["webhook_secret"], {**good, "id": 45}).json()["outcome"] == "IGNORED"


def test_rate_limit_and_dry_run(client, db, world):
    w = world
    rule = _rule(client, w, rate_limit_per_hour=1, conditions=[])
    secret = rule["webhook_secret"]
    before = _exec(db, "SELECT count(*) FROM projects WHERE tenant_id = %s", w["tenant"])[0]
    t = client.post(f"/api/v1/company/{w['tenant']}/automations/{rule['id']}/test", headers=w["admin"]["h"],
                    json={"payload": {"id": 7, "customer": {"name": "Deneme"}}})
    assert t.status_code == 200 and t.json()["outcome"] == "TEST" and "İade: Deneme #7" in t.json()["detail"]
    assert _exec(db, "SELECT count(*) FROM projects WHERE tenant_id = %s", w["tenant"])[0] == before  # deneme bir şey açmaz
    assert _hook(client, rule, secret, {"id": 1}).json()["outcome"] == "DRAFTED"
    assert _hook(client, rule, secret, {"id": 2}).json()["outcome"] == "RATE_LIMITED"


def test_rule_validation(client, world):
    w = world
    base = f"/api/v1/company/{w['tenant']}/automations"
    bad = [
        {"trigger": "EMAIL"},
        {"action": {"type": "CREATE_CASE", "manager_actor_id": w["agent"]}},  # yönetici insan olmalı
        {"action": {"type": "CREATE_CASE", "manager_actor_id": w["admin"]["id"], "auto_start": True}},  # şablonsuz otomatik başlatma
        {"conditions": [{"field": "a; drop", "op": "eq", "value": 1}]},
        {"trigger": "SCHEDULE", "schedule": {"every": "MONTH", "day": 40}},
        {"trigger": "POLL"},  # bağlantı yok
    ]
    for over in bad:
        body = {"name": "Hatalı kural", "trigger": "WEBHOOK", "action": {"type": "CREATE_CASE", "manager_actor_id": w["admin"]["id"]}, **over}
        assert client.post(base, headers=w["admin"]["h"], json=body).status_code == 422, over


def test_schedule_math():
    utc = timezone.utc
    # Pazartesi 09:00 (İstanbul = UTC+3) → bir sonraki Pazartesi
    nxt = svc.next_schedule({"every": "WEEK", "weekday": 0, "time": "09:00"}, datetime(2026, 10, 26, 6, 0, tzinfo=utc))
    assert nxt == datetime(2026, 11, 2, 6, 0, tzinfo=utc)
    # Ay sonu: 26 Ekim'den sonra 31 Ekim 18:00; Şubat'ta 28
    assert svc.next_schedule({"every": "MONTH", "day": -1, "time": "18:00"}, datetime(2026, 10, 26, tzinfo=utc)) == datetime(2026, 10, 31, 15, 0, tzinfo=utc)
    assert svc.next_schedule({"every": "MONTH", "day": -1, "time": "18:00"}, datetime(2027, 2, 1, tzinfo=utc)).day == 28
    assert svc.next_schedule({"every": "MONTH", "day": 31, "time": "08:00"}, datetime(2026, 11, 2, tzinfo=utc)).day == 30
    assert svc.render("{{a.b}} / {{yok}} / {{p}}", {"a": {"b": 5}, "p": [3, "Ürün"]}) == "5 /  / Ürün"


def test_poll_baseline_new_records_and_loop(client, db, world, monkeypatch):
    from app import integrations
    from app.integrations.base import READ, Tool

    w = world
    records = [{"id": 1, "name": "Eski bilet", "write_date": "2026-10-26 08:00:00"}]

    async def run(ctx, args):
        return {"model": "helpdesk.ticket", "count": len(records), "records": list(records)}

    class Fake:
        async def tools(self, ctx):
            return [Tool("search_records", "ara", {"type": "object"}, READ, run)]

    real_get = integrations.get
    monkeypatch.setattr(integrations, "get", lambda c: Fake() if c == "odoo" else real_get(c))
    conn = _exec(db, "INSERT INTO integration_connections (tenant_id, connector, name, config, status) "
                     "VALUES (%s, 'odoo', %s, '{}'::jsonb, 'ACTIVE') RETURNING id::text", w["tenant"], f"İzleme {uuid.uuid4().hex[:4]}")[0]
    db.commit()
    rule = _rule(client, w, trigger="POLL", connection_id=conn, event_type=None, conditions=[],
                 poll={"tool": "search_records", "args": {"model": "helpdesk.ticket"}, "version_field": "write_date", "interval_minutes": 1},
                 action={"type": "CREATE_CASE", "name": "Bilet: {{name}}", "manager_actor_id": w["admin"]["id"], "plan_with_recai": False})
    assert rule["poll"]["interval_minutes"] == 5  # en az 5 dakika
    run_url = f"/api/v1/company/{w['tenant']}/automations/{rule['id']}/run"
    first = client.post(run_url, headers=w["admin"]["h"]).json()
    assert first["baseline"] is True and first["handled"] == []  # eski kayıtlar için iş açılmaz

    records.append({"id": 2, "name": "Kargo gecikti", "write_date": "2026-10-26 09:00:00"})
    # RECOrion'un bu bağlantıya yazdığı kayıt (aktarım) olay gelse de iş açmaz
    _exec(db, "INSERT INTO integration_transfers (tenant_id, connection_id, object_type, trigger, status, external_id, done_at) "
              "VALUES (%s, %s, 'TASK', 'MANUAL', 'DONE', '3', now())", w["tenant"], conn)
    db.commit()
    records.append({"id": 3, "name": "RECOrion'un açtığı", "write_date": "2026-10-26 09:00:00"})
    second = client.post(run_url, headers=w["admin"]["h"]).json()
    got = {h["outcome"] for h in second["handled"]}
    assert second["new"] == 2 and got == {"DRAFTED", "LOOP"}, second
    assert _exec(db, "SELECT count(*) FROM projects WHERE source_rule_id = %s AND name = 'Bilet: Kargo gecikti'", rule["id"])[0] == 1
    # değişmeyen kayıt yeniden iş açmaz; güncellenen kayıt (yeni sürüm) olay olur
    assert client.post(run_url, headers=w["admin"]["h"]).json()["new"] == 0
    records[0]["write_date"] = "2026-10-26 10:00:00"
    assert [h["outcome"] for h in client.post(run_url, headers=w["admin"]["h"]).json()["handled"]] == ["DRAFTED"]


def test_recai_suggests_rule_without_invented_fields(client, world, monkeypatch):
    from app.services import llm_gateway

    class R:
        content = json.dumps({"name": "Acil iade", "event_type": "ticket.created", "kind": "CASE", "case_name": "İade {{id}}",
                              "conditions": [{"field": "priority", "op": "eq", "value": "high"},
                                             {"field": "uydurma_alan", "op": "eq", "value": "x"}],
                              "requirements": "İadeyi incele.", "notes": "Öncelik alanını kontrol edin."})
        public_model = "RECAi Mergen"

    async def fake_chat(*a, **k):
        return R()

    monkeypatch.setattr(llm_gateway, "chat", fake_chat)
    w = world
    r = client.post(f"/api/v1/company/{w['tenant']}/automations/suggest", headers=w["admin"]["h"],
                    json={"text": "Yüksek öncelikli iade biletleri gelince Case açılsın.", "sample": {"id": 5, "priority": "high"}})
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["name"] == "Acil iade" and [c["field"] for c in d["conditions"]] == ["priority"] and d["model"] == "RECAi Mergen"


def test_auto_start_only_with_template_plan(client, db, world):
    w = world

    def template(job_title):
        plan = {"summary": "İade süreci", "steps": [{"key": "S1", "title": "İadeyi incele", "job_title": job_title, "estimated_days": 1,
                                                       "requires_approval": True}]}
        return _exec(db, "INSERT INTO project_templates (tenant_id, name, kind, field_package, plan, status, use_count) "
                         "VALUES (%s, %s, 'CASE', 'GENEL', %s::jsonb, 'ACTIVE', 0) RETURNING id::text",
                     w["tenant"], f"İade şablonu {uuid.uuid4().hex[:4]}", json.dumps(plan))[0]

    ok_tpl, bad_tpl = template("Uzman"), template("Gümrük Müşaviri")
    db.commit()
    act = {"type": "CREATE_CASE", "name": "İade {{id}}", "manager_actor_id": w["admin"]["id"], "auto_start": True}
    started = _rule(client, w, conditions=[], action={**act, "template_id": ok_tpl})
    r = _hook(client, started, started["webhook_secret"], {"id": 501}).json()
    assert r["outcome"] == "STARTED", r
    status, tasks = _exec(db, "SELECT p.status, (SELECT count(*) FROM tasks t WHERE t.project_id = p.id) FROM projects p WHERE p.id = %s", r["project_id"])
    assert status == "ACTIVE" and tasks == 1

    # Şablondaki rol şirkette yoksa başlatılmaz; iş planlamada kalır ve nedeni söylenir
    stays = _rule(client, w, conditions=[], action={**act, "template_id": bad_tpl})
    r = _hook(client, stays, stays["webhook_secret"], {"id": 502}).json()
    assert r["outcome"] == "DRAFTED" and "Otomatik başlatılamadı" in r["detail"], r
    assert _exec(db, "SELECT status FROM projects WHERE id = %s", r["project_id"])[0] == "PLANNING"
