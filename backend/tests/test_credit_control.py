"""İSTEK #746: kredi bitince proje duraklatma (karantina yok), devam engeli, haftalık sınır, kullanım tahmini, EVREN koruma sınırı."""
import asyncio
import uuid
from datetime import datetime
from decimal import Decimal

from app.db.models import Tenant
from app.services import credit_control, credits
from tests.test_workflow import _exec, _flow, _ready_project, _wait, ai, world  # noqa: F401  (fikstürler)


def _grant(db, tenant_id, amount):
    """Bu dönemin aylık hakkını elle yazar (ensure_period_grant artık eklemez)."""
    _exec(db, "INSERT INTO credit_ledger (id, tenant_id, entry_type, amount, period, note, created_at) "
              "VALUES (gen_random_uuid(), %s, 'MONTHLY_GRANT', %s, %s, 'test', now()) ON CONFLICT DO NOTHING RETURNING id",
          tenant_id, amount, credits.current_period())


def test_forecast_and_settings_units():
    now = datetime(2026, 11, 10, 12, tzinfo=credits.TZ)  # ayın 9,5 günü geçti
    day = credits.forecast_depletion(Decimal(950), Decimal(1000), now)  # günde ~100 kredi → ~10 gün
    assert day == "2026-11-20"
    assert credits.forecast_depletion(Decimal(0), Decimal(1000), now) is None
    assert credits.forecast_depletion(Decimal(100), Decimal(0), now) is None
    t = Tenant(slug="x", name="x", settings={})
    assert credits.spend_settings(t) == {"weekly_cap_pct": None, "auto_resume_after_topup": False, "weekly_cap_lifted_week": None}
    t.settings = {"credit": {"weekly_cap_pct": 35, "auto_resume_after_topup": True}}
    assert credits.spend_settings(t)["weekly_cap_pct"] == 35 and credits.spend_settings(t)["auto_resume_after_topup"]
    assert credits.week_key(now) == "2026-W46"


def test_parallel_slots_limit_and_release():
    t = Tenant(id=uuid.uuid4(), slug=f"slot_{uuid.uuid4().hex[:6]}", name="x", plan_id=None)

    async def run():
        assert await credit_control.parallel_limit(None, t) == 5  # paket yoksa varsayılan
        ids = [str(uuid.uuid4()) for _ in range(6)]
        got = [await credit_control.acquire_slot(None, t, i) for i in ids]
        assert got == [True] * 5 + [False]  # 6. iş sırada bekler
        assert await credit_control.acquire_slot(None, t, ids[0])  # aynı iş yeniden alabilir
        await credit_control.release_slot(t.id, ids[1])
        assert await credit_control.acquire_slot(None, t, ids[5])
        for i in ids:
            await credit_control.release_slot(t.id, i)
    asyncio.run(run())


def test_credit_exhaustion_pauses_project_not_quarantine(client, db, world, ai):
    w, h = world, world["admin"]["h"]
    _grant(db, w["tenant"], 1)  # bakiye 1 kredi: ilk AI çalışması kredi yetersizliğine düşer
    pid, _, _ = _ready_project(client, w, "Kredi Bitti Projesi")
    try:
        assert client.post(f"/api/v1/projects/{pid}/status", headers=h, json={"action": "start"}).status_code == 200
        _wait(client, h, pid, lambda t, f: f["status"] == "PAUSED", "kredi bitince proje duraklamalı", 40)
        detail = client.get(f"/api/v1/projects/{pid}", headers=h).json()
        assert detail["pause_reason"] == "CREDIT"
        tasks = {t["title"]: t for t in _flow(client, h, pid)["tasks"]}
        assert tasks["AI adımı"]["status"] != "QUARANTINED"  # karantinaya düşmedi
        r = client.post(f"/api/v1/projects/{pid}/status", headers=h, json={"action": "resume"})
        assert r.status_code == 409 and "kredi" in r.json()["detail"].lower()  # kredi yüklenmeden devam yok
        cr = client.get(f"/api/v1/company/{w['tenant']}/credits", headers=h).json()
        assert cr["summary"]["level"] == "EXHAUSTED" and any(p["id"] == pid for p in cr["credit_paused"])

        _exec(db, "INSERT INTO credit_ledger (id, tenant_id, entry_type, amount, period, note, created_at) "
                  "VALUES (gen_random_uuid(), %s, 'TOPUP', 50000, %s, 'test', now()) RETURNING id", w["tenant"], credits.current_period())
        res = client.post(f"/api/v1/company/{w['tenant']}/credits/resume-paused", headers=h)
        assert res.status_code == 200 and "Kredi Bitti Projesi" in res.json()["resumed"], res.text
        _wait(client, h, pid, lambda t, f: t["AI adımı"]["status"] == "WAITING_APPROVAL", "kredi yüklenince kaldığı yerden onaya gelmeli", 60)
        kinds = [e["kind"] for e in _flow(client, h, pid)["events"]]
        assert "PROJECT_RESUMED" in kinds and "BLOCKED" not in kinds
    finally:
        client.post(f"/api/v1/projects/{pid}/status", headers=h, json={"action": "cancel", "summary": "Test temizliği"})


def test_weekly_cap_settings_and_lift(client, db, world):
    w, h, member = world, world["admin"]["h"], world["member"]["h"]
    _grant(db, w["tenant"], 10000)
    _exec(db, "INSERT INTO credit_ledger (id, tenant_id, entry_type, amount, period, note, created_at) "
              "VALUES (gen_random_uuid(), %s, 'USAGE', -1500, %s, 'test', now()) RETURNING id", w["tenant"], credits.current_period())
    base = f"/api/v1/company/{w['tenant']}/credits"
    assert client.put(f"{base}/settings", headers=member, json={"weekly_cap_pct": 10}).status_code == 403  # yalnız yönetim
    assert client.put(f"{base}/settings", headers=h, json={"weekly_cap_pct": 2}).status_code == 422  # en az %5
    r = client.put(f"{base}/settings", headers=h, json={"weekly_cap_pct": 10, "auto_resume_after_topup": True})
    assert r.status_code == 200 and r.json()["weekly_cap_pct"] == 10
    s = client.get(base, headers=h).json()["summary"]
    assert s["weekly_cap_reached"] is True and s["week_used"] >= 1500  # bu haftaki kullanım sınırı aştı
    assert client.post(f"{base}/lift-weekly-cap", headers=h).status_code == 200
    assert client.get(base, headers=h).json()["summary"]["weekly_cap_reached"] is False  # bu hafta için kalktı
    assert client.put(f"{base}/settings", headers=h, json={"weekly_cap_pct": None}).json()["weekly_cap_pct"] is None
