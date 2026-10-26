"""
Olayla başlayan işler (ADIM 13.2; kullanıcı kararı 25.10.2026).

Kural = ne olunca + koşul + ne yapılsın:
- WEBHOOK: dış sistem imzalı anlık bildirim gönderir (HMAC-SHA256, zaman damgalı; 5 dakikadan eski/ileri istek reddedilir).
- POLL: anlık bildirim gönderemeyen sistem, bağlantının okuma aracıyla (ör. Odoo search_records) periyodik izlenir. İlk
  turda mevcut kayıtlar yalnızca not edilir (eski kayıtlar için iş açılmaz); sonraki turlarda yeni/değişen kayıtlar olay olur.
- SCHEDULE: zamanlayıcı (her gün / hafta / ay; ay sonu dahil), Europe/Istanbul saatiyle.
Koşul: olay verisindeki alanlar (nokta ile iç alan) eq, ne, contains, in, gt, gte, lt, lte, exists ile süzülür.
Ne yapılsın: Case/proje aç (şablon varsa planı taslağa konur; isterler {{alan}} yer tutucularıyla doldurulur) veya yalnızca bildir.
  Açılan iş TASLAK kalır ve yöneticisine bildirilir. Otomatik başlatma yalnızca kuralda açıkça istenmişse ve onaylı
  şablon planıyla (her adıma AI personel atanabildiyse) yapılır; olmazsa iş taslakta kalır, neden bildirilir.
Bilet zenginleştirme (ADIM 13.3): izleme ayarında enrich=helpdesk_ticket ise okunan Helpdesk biletlerine etiket adları ve
  "ticket" ortak nesnesi eklenir (services/support.py); koşullar ticket.category gibi alanlara yazılabilir.
Kapanışta aktarım (ADIM 13.3): eylemde transfer_on_close eşlemeleri varsa açılan iş kapanınca bu eşlemelerle aktarım önerilir
  (kaynak kayda bağlı: ör. biletten açılan Case'in sonucu aynı bilete yazılır, onayla).
Korumalar: aynı olay bir kez işlenir (tekrar engeli), RECOrion'un kendi yazdığı kayıttan gelen olay iş açmaz (döngü engeli),
  kural başına saatlik ve şirket başına saatlik sınır (hız sınırı). Her olay ve sonucu silinemez günlüğe yazılır.
"""
import asyncio
import calendar
import hashlib
import hmac
import json
import logging
import re
import secrets
import time
import uuid
from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple
from zoneinfo import ZoneInfo

from fastapi import HTTPException
from sqlalchemy import column, func, select, table, text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import vault
from app.db.models import (Actor, AutomationLog, AutomationRule, ExternalLink, IntegrationConnection, IntegrationMapping, IntegrationTransfer,
                           Project, ProjectTemplate, Tenant)
from app.db.session import AsyncSessionLocal

logger = logging.getLogger("recorion.automations")

TZ = ZoneInfo("Europe/Istanbul")
TRIGGERS = ("WEBHOOK", "POLL", "SCHEDULE")
ACTIONS = ("CREATE_CASE", "CREATE_PROJECT", "NOTIFY")
OPS = ("eq", "ne", "contains", "in", "gt", "gte", "lt", "lte", "exists")
EVERY = ("DAY", "WEEK", "MONTH")
FIRED = ("DRAFTED", "STARTED", "NOTIFIED")  # hız sınırına sayılan sonuçlar
TENANT_LIMIT_PER_HOUR = 200
SIGNATURE_TOLERANCE = 300  # sn
POLL_MIN_MINUTES = 5
POLL_MAX_EVENTS = 20  # bir turda en fazla açılan olay (fazlası sonraki tura kalır)
PAYLOAD_LIMIT = 16000
LOOP_WINDOW = timedelta(days=7)
ORIGIN_KEYS = ("x_recorion_origin", "recorion_origin")
ENRICHERS = ("helpdesk_ticket", "hr_expense")
SUMMARIES = ("expense_month",)
DEDUPE = table("automation_dedupe", column("rule_id", PGUUID(as_uuid=True)), column("key"), column("tenant_id", PGUUID(as_uuid=True)))

_tasks: set = set()


class AutomationError(Exception):
    """Kural geçersiz veya çalıştırılamadı; mesaj kullanıcıya gösterilebilir."""


def now() -> datetime:
    return datetime.now(timezone.utc)


def binding(rule: AutomationRule) -> str:
    return f"automation:{rule.tenant_id}:{rule.id}"


# ---------------------------------------------------------------- koşul ve yer tutucu
def get_path(data: Any, path: str) -> Any:
    cur = data
    for part in str(path or "").split("."):
        if isinstance(cur, dict):
            cur = cur.get(part)
        elif isinstance(cur, list) and part.isdigit() and int(part) < len(cur):
            cur = cur[int(part)]
        else:
            return None
    # Odoo many2one [id, "Ad"] → ad
    if isinstance(cur, list) and len(cur) == 2 and isinstance(cur[0], int) and isinstance(cur[1], str):
        return cur[1]
    return cur


def _num(v: Any) -> Optional[float]:
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def check(cond: Dict[str, Any], payload: Dict[str, Any]) -> bool:
    v, op, want = get_path(payload, cond.get("field")), cond.get("op", "eq"), cond.get("value")
    if op == "exists":
        return v not in (None, "", [], {}, False)
    if op in ("eq", "ne"):
        same = str(v).strip().lower() == str(want).strip().lower() if v is not None else want in (None, "")
        return same if op == "eq" else not same
    if op == "contains":
        return v is not None and str(want).lower() in (json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) else str(v)).lower()
    if op == "in":
        opts = want if isinstance(want, list) else [x.strip() for x in str(want or "").split(",")]
        return str(v).strip().lower() in {str(o).strip().lower() for o in opts}
    a, b = _num(v), _num(want)
    if a is None or b is None:
        return False
    return {"gt": a > b, "gte": a >= b, "lt": a < b, "lte": a <= b}[op]


def matches(conditions: List[Dict[str, Any]], payload: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    for c in conditions or []:
        if not check(c, payload):
            return False, f"Koşul sağlanmadı: {c.get('field')} {c.get('op')} {c.get('value', '')}".strip()
    return True, None


def render(template: Optional[str], payload: Dict[str, Any]) -> str:
    """{{alan}} / {{alan.iç}} yer tutucularını olay verisiyle doldurur; olmayan alan boş kalır."""
    def one(m):
        v = get_path(payload, m.group(1).strip())
        if v is None:
            return ""
        return json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) else str(v)
    return re.sub(r"\{\{\s*([\w.]+)\s*\}\}", one, template or "")


def clip_payload(payload: Any) -> Any:
    try:
        raw = json.dumps(payload, ensure_ascii=False, default=str)
    except (TypeError, ValueError):
        return {"preview": str(payload)[:PAYLOAD_LIMIT]}
    return payload if len(raw) <= PAYLOAD_LIMIT else {"truncated": True, "preview": raw[:PAYLOAD_LIMIT]}


# ---------------------------------------------------------------- doğrulama
def clean_conditions(raw: Any) -> List[Dict[str, Any]]:
    out = []
    for c in raw or []:
        if not isinstance(c, dict):
            raise AutomationError("Koşul biçimi geçersiz.")
        field_ = str(c.get("field") or "").strip()
        op = str(c.get("op") or "eq").strip()
        if not re.fullmatch(r"[\w.]{1,120}", field_):
            raise AutomationError("Koşul alanı geçersiz (ör. stage_id veya partner.name).")
        if op not in OPS:
            raise AutomationError(f"Bilinmeyen koşul işlemi: {op}")
        out.append({"field": field_, "op": op, "value": c.get("value")})
    if len(out) > 20:
        raise AutomationError("En fazla 20 koşul tanımlanabilir.")
    return out


def clean_schedule(raw: Any) -> Dict[str, Any]:
    s = raw if isinstance(raw, dict) else {}
    every = str(s.get("every") or "DAY").upper()
    if every not in EVERY:
        raise AutomationError("Zamanlayıcı her gün, hafta veya ay olmalı.")
    t = str(s.get("time") or "09:00")
    if not re.fullmatch(r"([01]\d|2[0-3]):[0-5]\d", t):
        raise AutomationError("Saat SS:DD biçiminde olmalı (ör. 09:00).")
    out = {"every": every, "time": t}
    if every == "WEEK":
        wd = int(s.get("weekday", 0))
        if not 0 <= wd <= 6:
            raise AutomationError("Haftanın günü 0 (Pazartesi) ile 6 (Pazar) arasında olmalı.")
        out["weekday"] = wd
    if every == "MONTH":
        d = int(s.get("day", 1))
        if not (d == -1 or 1 <= d <= 31):
            raise AutomationError("Ayın günü 1–31 ya da ay sonu (-1) olmalı.")
        out["day"] = d
    if s.get("summary") in SUMMARIES:
        out["summary"] = s["summary"]
    return out


def clean_poll(raw: Any) -> Dict[str, Any]:
    p = raw if isinstance(raw, dict) else {}
    tool = str(p.get("tool") or "").strip()
    if not tool:
        raise AutomationError("İzleme için bağlantının okuma aracı seçilmeli (ör. search_records).")
    args = p.get("args") if isinstance(p.get("args"), dict) else {}
    try:
        interval = max(POLL_MIN_MINUTES, min(int(p.get("interval_minutes") or 15), 1440))
    except (TypeError, ValueError):
        interval = 15
    out = {"tool": tool, "args": args, "id_field": str(p.get("id_field") or "id"),
           "version_field": str(p.get("version_field") or "") or None, "interval_minutes": interval}
    if p.get("enrich") in ENRICHERS:
        out["enrich"] = p["enrich"]
    return out


async def clean_action(db: AsyncSession, tenant_id: uuid.UUID, raw: Any) -> Dict[str, Any]:
    a = raw if isinstance(raw, dict) else {}
    typ = str(a.get("type") or "CREATE_CASE").upper()
    if typ not in ACTIONS:
        raise AutomationError("Bilinmeyen eylem.")
    out: Dict[str, Any] = {"type": typ}
    notify = []
    for x in a.get("notify_actor_ids") or []:
        actor = await db.get(Actor, _uuid(x))
        if actor and actor.tenant_id == tenant_id and actor.actor_type == "HUMAN":
            notify.append(str(actor.id))
    out["notify_actor_ids"] = notify[:10]
    if typ == "NOTIFY":
        if not notify:
            raise AutomationError("Bildirim gidecek en az bir kişi seçin.")
        out["message"] = str(a.get("message") or "")[:2000]
        return out
    manager = await db.get(Actor, _uuid(a.get("manager_actor_id")))
    if not manager or manager.tenant_id != tenant_id or manager.actor_type != "HUMAN" or manager.status == "DISABLED":
        raise AutomationError("Açılacak işin yöneticisi şirketinizden etkin bir kişi olmalı.")
    out["manager_actor_id"] = str(manager.id)
    out["name"] = str(a.get("name") or "").strip()[:200] or "Otomatik iş {{id}}"
    out["kind"] = "CASE" if typ == "CREATE_CASE" else "PROJECT"
    tpl_id = a.get("template_id")
    if tpl_id:
        tpl = await db.get(ProjectTemplate, _uuid(tpl_id))
        if not tpl or tpl.status != "ACTIVE" or (tpl.tenant_id and tpl.tenant_id != tenant_id):
            raise AutomationError("Seçilen şablon bulunamadı veya arşivde.")
        out["template_id"] = str(tpl.id)
    out["auto_start"] = bool(a.get("auto_start")) and bool(out.get("template_id"))
    if a.get("auto_start") and not out.get("template_id"):
        raise AutomationError("Otomatik başlatma yalnızca onaylı bir şablon planıyla seçilebilir.")
    out["plan_with_recai"] = a.get("plan_with_recai", True) is not False and not out.get("template_id")
    out["transfer_on_close"] = []
    for mid in (a.get("transfer_on_close") or [])[:5]:
        m = await db.get(IntegrationMapping, _uuid(mid))
        if not m or m.tenant_id != tenant_id or m.status == "ARCHIVED":
            raise AutomationError("Kapanışta aktarım için seçilen eşleme bulunamadı.")
        out["transfer_on_close"].append(str(m.id))
    return out


def _uuid(v: Any) -> Optional[uuid.UUID]:
    try:
        return uuid.UUID(str(v))
    except (TypeError, ValueError):
        return None


# ---------------------------------------------------------------- zamanlayıcı
def next_schedule(schedule: Dict[str, Any], after: datetime) -> datetime:
    """after'dan sonraki ilk çalışma anı (UTC)."""
    hh, mm = (int(x) for x in schedule.get("time", "09:00").split(":"))
    local = after.astimezone(TZ)
    every = schedule.get("every", "DAY")

    def at(d: date) -> datetime:
        return datetime(d.year, d.month, d.day, hh, mm, tzinfo=TZ)

    d = local.date()
    for _ in range(400):
        ok = True
        if every == "WEEK":
            ok = d.weekday() == schedule.get("weekday", 0)
        elif every == "MONTH":
            last = calendar.monthrange(d.year, d.month)[1]
            want = schedule.get("day", 1)
            ok = d.day == (last if want == -1 else min(want, last))
        if ok and at(d) > local:
            return at(d).astimezone(timezone.utc)
        d += timedelta(days=1)
    raise AutomationError("Zamanlayıcı için sonraki çalışma anı bulunamadı.")


def initial_next_run(rule: AutomationRule) -> Optional[datetime]:
    if rule.trigger == "SCHEDULE":
        return next_schedule(rule.schedule or {}, now())
    if rule.trigger == "POLL":
        return now()
    return None


# ---------------------------------------------------------------- webhook imzası
def new_secret() -> str:
    return "rxw_" + secrets.token_urlsafe(32)


def sign(secret: str, ts: str, body: bytes) -> str:
    return "sha256=" + hmac.new(secret.encode(), ts.encode() + b"." + body, hashlib.sha256).hexdigest()


def verify(rule: AutomationRule, ts: Optional[str], signature: Optional[str], body: bytes) -> Optional[str]:
    """Hata varsa nedenini döner (gizli bilgi içermez)."""
    if not rule.webhook_secret:
        return "Bu kuralın imza anahtarı yok."
    if not ts or not signature:
        return "İmza başlıkları eksik (X-RECOrion-Timestamp, X-RECOrion-Signature)."
    try:
        age = abs(time.time() - int(ts))
    except ValueError:
        return "Zaman damgası geçersiz."
    if age > SIGNATURE_TOLERANCE:
        return "İstek çok eski veya saat farkı büyük (5 dakikadan fazla)."
    secret = vault.unseal(rule.webhook_secret, binding(rule)).get("secret", "")
    if not hmac.compare_digest(sign(secret, ts, body), signature.strip()):
        return "İmza doğrulanamadı."
    return None


# ---------------------------------------------------------------- olay işleme
async def _log(db: AsyncSession, rule: Optional[AutomationRule], tenant_id, source: str, outcome: str, detail: str = "",
               event_type: Optional[str] = None, external_ref: Optional[str] = None, dedupe_key: Optional[str] = None,
               project_id=None, payload: Any = None) -> AutomationLog:
    row = AutomationLog(tenant_id=tenant_id, rule_id=rule.id if rule else None, rule_name=rule.name if rule else None, source=source,
                        event_type=(event_type or (rule.event_type if rule else None) or None), external_ref=(external_ref or None),
                        dedupe_key=dedupe_key, outcome=outcome, detail=(detail or "")[:2000], project_id=project_id,
                        payload=clip_payload(payload) if payload is not None else None)
    db.add(row)
    return row


async def _is_loop(db: AsyncSession, rule: AutomationRule, payload: Dict[str, Any], record_id: Optional[str]) -> Optional[str]:
    if any(payload.get(k) for k in ORIGIN_KEYS):
        return "Olay RECOrion'un kendi işleminden geliyor (kaynak işareti)."
    if rule.connection_id and record_id:
        since = now() - LOOP_WINDOW
        tr = (await db.execute(select(IntegrationTransfer.id).where(
            IntegrationTransfer.connection_id == rule.connection_id, IntegrationTransfer.external_id == str(record_id),
            IntegrationTransfer.status.in_(("DONE", "ROLLED_BACK")), IntegrationTransfer.done_at >= since).limit(1))).first()
        link = (await db.execute(select(ExternalLink.id).where(
            ExternalLink.connection_id == rule.connection_id, ExternalLink.external_id == str(record_id),
            ExternalLink.updated_at >= since).limit(1))).first()
        if tr or link:
            return f"Kayıt #{record_id} RECOrion tarafından yazıldı; kendi kaydından iş açılmaz."
    return None


async def _rate_limited(db: AsyncSession, rule: AutomationRule) -> Optional[str]:
    since = now() - timedelta(hours=1)
    n_rule = (await db.execute(select(func.count()).select_from(AutomationLog).where(
        AutomationLog.rule_id == rule.id, AutomationLog.outcome.in_(FIRED), AutomationLog.created_at >= since))).scalar() or 0
    if n_rule >= max(1, rule.rate_limit_per_hour or 20):
        return f"Kural saatlik sınıra ulaştı ({rule.rate_limit_per_hour}/saat)."
    n_tenant = (await db.execute(select(func.count()).select_from(AutomationLog).where(
        AutomationLog.tenant_id == rule.tenant_id, AutomationLog.outcome.in_(FIRED), AutomationLog.created_at >= since))).scalar() or 0
    if n_tenant >= TENANT_LIMIT_PER_HOUR:
        return f"Şirketin otomasyon sınırı doldu ({TENANT_LIMIT_PER_HOUR}/saat)."
    return None


async def _claim(db: AsyncSession, rule: AutomationRule, key: str) -> bool:
    res = await db.execute(insert(DEDUPE).values(rule_id=rule.id, key=key[:255], tenant_id=rule.tenant_id)
                           .on_conflict_do_nothing().returning(DEDUPE.c.rule_id))
    return res.first() is not None


async def handle(db: AsyncSession, rule: AutomationRule, source: str, payload: Dict[str, Any], event_type: Optional[str] = None,
                 external_ref: Optional[str] = None, dedupe_key: Optional[str] = None, record_id: Optional[str] = None,
                 test: bool = False) -> Dict[str, Any]:
    """Bir olayı kurala göre işler; günlüğe yazar ve sonucu döner. test=True: hiçbir şey açılmaz, ne olacağı söylenir."""
    payload = payload if isinstance(payload, dict) else {"value": payload}
    src = "TEST" if test else source
    base = dict(event_type=event_type, external_ref=external_ref, dedupe_key=dedupe_key, payload=payload)

    async def done(outcome: str, detail: str = "", project_id=None) -> Dict[str, Any]:
        row = await _log(db, rule, rule.tenant_id, src, outcome, detail, project_id=project_id, **base)
        if outcome in FIRED:
            rule.last_fired_at, rule.fire_count = now(), (rule.fire_count or 0) + 1
        await db.commit()
        return {"outcome": outcome, "detail": detail, "project_id": str(project_id) if project_id else None, "log_id": str(row.id)}

    if rule.status != "ACTIVE" and not test:
        return await done("IGNORED", "Kural duraklatılmış.")
    if rule.event_type and event_type and rule.event_type != event_type:
        return await done("IGNORED", f"Olay türü uymuyor ({event_type}).")
    ok, why = matches(rule.conditions or [], payload)
    if not ok:
        return await done("IGNORED", why)
    loop = await _is_loop(db, rule, payload, record_id)
    if loop:
        return await done("LOOP", loop)
    if test:
        a = rule.action or {}
        name = render(a.get("name"), payload) if a.get("type") != "NOTIFY" else ""
        what = {"CREATE_CASE": f"'{name}' Case'i taslak olarak açılır", "CREATE_PROJECT": f"'{name}' projesi taslak olarak açılır",
                "NOTIFY": "Seçilen kişilere bildirim gider"}[a.get("type", "CREATE_CASE")]
        if a.get("auto_start"):
            what += " ve şablon planıyla başlatılır (adımlara personel atanabilirse)"
        return await done("TEST", f"Koşullar sağlandı: {what}. (Deneme: hiçbir şey açılmadı.)")
    limited = await _rate_limited(db, rule)
    if limited:
        return await done("RATE_LIMITED", limited)
    if dedupe_key and not await _claim(db, rule, dedupe_key):
        return await done("DUPLICATE", "Bu olay daha önce işlendi.")
    try:
        outcome, detail, project_id = await _act(db, rule, payload, external_ref)
    except (AutomationError, HTTPException) as exc:
        await db.rollback()
        msg = str(exc.detail) if isinstance(exc, HTTPException) else str(exc)
        rule = await db.get(AutomationRule, rule.id)
        rule.last_error = msg[:1000]
        if dedupe_key:  # başarısız olay yeniden gönderilirse işlenebilsin
            await db.execute(text("DELETE FROM automation_dedupe WHERE rule_id = :r AND key = :k"), {"r": rule.id, "k": dedupe_key[:255]})
        return await done("FAILED", msg)
    rule.last_error = None
    return await done(outcome, detail, project_id)


async def _act(db: AsyncSession, rule: AutomationRule, payload: Dict[str, Any], external_ref: Optional[str]) -> Tuple[str, str, Any]:
    from app.services import notify

    a = rule.action or {}
    if a.get("type") == "NOTIFY":
        msg = render(a.get("message"), payload) or f"'{rule.name}' otomasyonu tetiklendi."
        for aid in a.get("notify_actor_ids") or []:
            await notify.send(db, aid, f"RECOrion otomasyon: {msg}")
        return "NOTIFIED", f"{len(a.get('notify_actor_ids') or [])} kişiye bildirildi.", None

    from app.services import project_templates as tsvc
    from app.services import projects as psvc

    tenant = await db.get(Tenant, rule.tenant_id)
    await psvc.ensure_project_quota(db, tenant)
    manager = await db.get(Actor, _uuid(a.get("manager_actor_id")))
    if not manager or manager.tenant_id != rule.tenant_id or manager.status == "DISABLED":
        raise AutomationError("Kuralın yöneticisi artık etkin değil; kuralı düzenleyin.")
    name = (render(a.get("name"), payload).strip() or rule.name)[:255]
    reqs = render(rule.requirements, payload).strip()
    facts = "\n".join(f"- {k}: {v}" for k, v in list(_flat(payload).items())[:40])
    requirements = (reqs + ("\n\nOLAY BİLGİLERİ:\n" + facts if facts else "")).strip()[:20000] or None
    p = Project(tenant_id=tenant.id, slug=await psvc.unique_slug(db, tenant.id, name), name=name, kind=a.get("kind", "CASE"),
                description=f"'{rule.name}' otomasyonuyla açıldı.", requirements=requirements, status="DRAFT",
                manager_actor_id=manager.id, created_by_actor_id=manager.id, source_rule_id=rule.id,
                source_ref=(external_ref or None) and external_ref[:255], transfer_on_close=list(a.get("transfer_on_close") or []))
    db.add(p)
    await db.flush()
    await psvc.set_member(db, p, manager, "MANAGER", manager.id)
    template = await db.get(ProjectTemplate, _uuid(a.get("template_id"))) if a.get("template_id") else None
    unmatched: List[str] = []
    if template and template.status == "ACTIVE":
        unmatched = (await tsvc.apply(db, template, p))["unmatched_roles"]
        p.status = "PLANNING"
    await db.commit()
    outcome, detail = "DRAFTED", "İş taslak olarak açıldı; yöneticinin incelemesi bekleniyor."
    if a.get("auto_start") and template:
        started, why = await _auto_start(db, p, manager.id)
        if started:
            outcome, detail = "STARTED", "Onaylı şablon planıyla otomatik başlatıldı."
        else:
            detail = f"Otomatik başlatılamadı, taslakta: {why}"
    elif template and unmatched:
        detail += f" Şirkette olmayan roller: {', '.join(unmatched[:5])}."
    elif a.get("plan_with_recai") and requirements:
        spawn(_plan_background(p.id))
        detail += " RECAi plan taslağını hazırlıyor."
    await _notify_manager(db, rule, p, manager.id, detail, a.get("notify_actor_ids") or [])
    return outcome, detail, p.id


def _flat(d: Any, prefix: str = "") -> Dict[str, str]:
    out: Dict[str, str] = {}
    if isinstance(d, dict):
        for k, v in d.items():
            out.update(_flat(v, f"{prefix}{k}."))
    elif isinstance(d, list) and len(d) == 2 and isinstance(d[0], int) and isinstance(d[1], str):
        out[prefix[:-1]] = d[1]
    elif d not in (None, "", [], {}):
        out[prefix[:-1] or "değer"] = (json.dumps(d, ensure_ascii=False) if isinstance(d, list) else str(d))[:300]
    return out


async def _auto_start(db: AsyncSession, p: Project, actor_id: uuid.UUID) -> Tuple[bool, str]:
    from app.config import settings
    from app.services import project_planning as planning
    from app.services import projects as psvc

    steps = (p.plan or {}).get("steps") or []
    missing = [s.get("title") for s in steps if not s.get("agent_id")]
    if not steps or missing:
        return False, "Şablondaki adımlara uygun AI personel yok (" + ", ".join(missing[:3]) + ")." if missing else "Şablonda adım yok."
    try:
        await planning.approve_plan(db, p, actor_id)
        p = await db.get(Project, p.id)
        days = max(1, int(sum(float(s.get("estimated_days") or 1) for s in steps)))
        today = datetime.now(TZ).date()
        p.start_date, p.end_date = p.start_date or today, p.end_date or today + timedelta(days=days)
        await psvc.transition(db, p, "mark_ready")
        await psvc.transition(db, p, "start")
        if settings.WORKFLOW_ENABLED:
            from app.workflows import engine
            p.workflow_id = await engine.start_project(str(p.id), str(actor_id))
        await db.commit()
        return True, ""
    except Exception as exc:  # başlatılamazsa iş planlamada kalır; neden yöneticiye bildirilir
        await db.rollback()
        detail = exc.detail if isinstance(exc, HTTPException) else str(exc)
        logger.warning("Otomatik başlatma yapılamadı (%s): %s", p.id, detail)
        return False, str(detail)[:300]


async def _notify_manager(db: AsyncSession, rule: AutomationRule, p: Project, manager_id, detail: str, extra: List[str]) -> None:
    from app.services import notify

    text_ = (f"RECOrion otomasyon '{rule.name}': '{p.name}' {'Case' if p.kind == 'CASE' else 'proje'} açıldı. {detail}\n"
             f"{notify.project_url(p.id)}")
    for aid in dict.fromkeys([str(manager_id), *extra]):
        try:
            await notify.send(db, aid, text_)
        except Exception as exc:
            logger.warning("Otomasyon bildirimi gönderilemedi: %s", exc)


async def _plan_background(project_id: uuid.UUID) -> None:
    from app.services import project_planning

    async with AsyncSessionLocal() as db:
        try:
            p = await db.get(Project, project_id)
            if p.status == "DRAFT":
                p.status = "PLANNING"
                await db.commit()
            await project_planning.suggest_plan(db, p)
        except Exception as exc:  # plan hazırlanamazsa iş taslakta kalır; yönetici ekrandan yeniden ister
            logger.warning("Otomasyonla açılan işe plan hazırlanamadı (%s): %s", project_id, exc)


def spawn(coro) -> None:
    t = asyncio.create_task(coro)
    _tasks.add(t)
    t.add_done_callback(_tasks.discard)


# ---------------------------------------------------------------- periyodik izleme
def _records(result: Any) -> List[Dict[str, Any]]:
    if isinstance(result, dict):
        for k in ("records", "items", "results", "data"):
            if isinstance(result.get(k), list):
                return [r for r in result[k] if isinstance(r, dict)]
    if isinstance(result, list):
        return [r for r in result if isinstance(r, dict)]
    return []


async def poll(db: AsyncSession, rule: AutomationRule) -> Dict[str, Any]:
    """Bağlantının okuma aracını çalıştırır; yeni/değişen kayıtlar için olay işler. İlk tur yalnızca başlangıç noktası."""
    from app import integrations
    from app.integrations.base import READ
    from app.services import tool_gateway

    cfg = rule.poll or {}
    rule.next_run_at = now() + timedelta(minutes=cfg.get("interval_minutes") or 15)
    conn = await db.get(IntegrationConnection, rule.connection_id) if rule.connection_id else None
    if not conn or conn.tenant_id != rule.tenant_id or conn.status != "ACTIVE":
        rule.last_error = "İzlenen bağlantı yok veya etkin değil."
        await db.commit()
        return {"error": rule.last_error}
    try:
        ctx = tool_gateway.context(conn)
        tools = {t.name: t for t in await integrations.get(conn.connector).tools(ctx)}
        tool = tools.get(cfg.get("tool"))
        if not tool or tool.kind != READ:
            raise AutomationError(f"'{cfg.get('tool')}' bu bağlantıda okuma aracı değil.")
        result = await asyncio.wait_for(tool.run(ctx, dict(cfg.get("args") or {})), timeout=tool_gateway.CALL_TIMEOUT)
        records = _records(result)
        if cfg.get("enrich") in ENRICHERS and conn.connector == "odoo":
            records = await enricher(cfg["enrich"])(ctx, records)
    except Exception as exc:
        rule.last_error = f"İzleme çalışmadı: {str(exc)[:300]}"
        await db.commit()
        return {"error": rule.last_error}
    id_f, ver_f = cfg.get("id_field") or "id", cfg.get("version_field")
    seen: Dict[str, str] = dict((rule.cursor or {}).get("seen") or {})
    first = not (rule.cursor or {}).get("initialized")
    fresh = []
    for r in records:
        rid = get_path(r, id_f)
        if rid is None:
            continue
        ver = str(get_path(r, ver_f) or "") if ver_f else ""
        if seen.get(str(rid)) == ver:
            continue
        seen[str(rid)] = ver
        if not first:
            fresh.append((str(rid), ver, r))
    # imleç büyümesin: en son 2000 kayıt tutulur
    rule.cursor = {"initialized": True, "seen": dict(list(seen.items())[-2000:])}
    rule.last_error = None
    await db.commit()
    handled = []
    for rid, ver, r in fresh[:POLL_MAX_EVENTS]:
        key = f"{rid}:{ver}" if ver else rid
        ref = f"{conn.connector}:{(cfg.get('args') or {}).get('model') or cfg.get('tool')}:{rid}"
        handled.append(await handle(db, rule, "POLL", r, external_ref=ref, dedupe_key=key, record_id=rid))
    if len(fresh) > POLL_MAX_EVENTS:  # kalanlar sonraki tura: işaretleri geri alınır
        cur = dict(rule.cursor)
        cur["seen"] = {k: v for k, v in cur["seen"].items() if k not in {x[0] for x in fresh[POLL_MAX_EVENTS:]}}
        rule.cursor = cur
        await db.commit()
    return {"baseline": first, "new": len(fresh), "handled": handled}


def enricher(name: str):
    from app.services import expenses, support

    return {"helpdesk_ticket": support.enrich, "hr_expense": expenses.enrich}[name]


async def schedule_payload(db: AsyncSession, rule: AutomationRule, at: datetime) -> Dict[str, Any]:
    """Zamanlayıcı olayının verisi; kuralda özet (ör. ay sonu masraf özeti) varsa bağlantıdan okunup eklenir."""
    local = at.astimezone(TZ)
    last = calendar.monthrange(local.year, local.month)[1]
    payload = {"date": local.date().isoformat(), "time": local.strftime("%H:%M"), "period": local.strftime("%Y-%m"),
               "weekday": local.weekday(), "is_month_end": local.day == last}
    if (rule.schedule or {}).get("summary") == "expense_month":
        from app.services import expenses, tool_gateway

        conn = await db.get(IntegrationConnection, rule.connection_id) if rule.connection_id else None
        if not conn or conn.tenant_id != rule.tenant_id or conn.status != "ACTIVE" or conn.connector != "odoo":
            raise AutomationError("Masraf özeti için etkin Odoo bağlantısı gerekli.")
        payload["expenses"] = await expenses.month_summary(tool_gateway.context(conn), payload["period"])
    return payload


async def run_schedule(db: AsyncSession, rule: AutomationRule) -> Dict[str, Any]:
    due = rule.next_run_at or now()
    rule.next_run_at = next_schedule(rule.schedule or {}, max(now(), due))
    await db.commit()
    try:
        payload = await schedule_payload(db, rule, due)
    except Exception as exc:
        rule.last_error = f"Zamanlayıcı özeti okunamadı: {str(exc)[:300]}"
        await db.commit()
        return {"error": rule.last_error}
    return await handle(db, rule, "SCHEDULE", payload, event_type="schedule", dedupe_key=f"{due.astimezone(TZ):%Y-%m-%dT%H:%M}")


async def run_due() -> int:
    """Vadesi gelen izleme ve zamanlayıcı kurallarını çalıştırır (her backend sürecinde; Redis kilidiyle tek süreç)."""
    from app.core.tokens import redis_client

    client = redis_client()
    try:
        if not await client.set("automations:lock", "1", nx=True, ex=240):
            return 0
    except Exception as exc:
        logger.warning("Otomasyon kilidi alınamadı: %s", exc)
    try:
        n = 0
        async with AsyncSessionLocal() as db:
            ids = (await db.execute(select(AutomationRule.id).where(
                AutomationRule.status == "ACTIVE", AutomationRule.trigger.in_(("POLL", "SCHEDULE")),
                AutomationRule.next_run_at <= now()).limit(50))).scalars().all()
        for rid in ids:
            async with AsyncSessionLocal() as db:
                rule = await db.get(AutomationRule, rid)
                try:
                    await (poll(db, rule) if rule.trigger == "POLL" else run_schedule(db, rule))
                    n += 1
                except Exception as exc:
                    await db.rollback()
                    logger.error("Otomasyon çalıştırılamadı (%s): %s", rid, exc)
        return n
    finally:
        try:
            await client.delete("automations:lock")
            await client.aclose()
        except Exception:
            pass


async def loop(interval: int = 60) -> None:
    logger.info("Otomasyon izleyicisi başladı (her %s sn).", interval)
    while True:
        try:
            await run_due()
        except Exception as exc:
            logger.error("Otomasyon turu hatası: %s", exc)
        await asyncio.sleep(interval)


# ---------------------------------------------------------------- RECAi ile kural taslağı
SUGGEST_PROMPT = """Sen RECOrion'un otomasyon asistanı RECAi'sin. Kullanıcı, dış sistemden gelen bir olay olunca RECOrion'da
iş (Case veya proje) açılmasını istiyor. Anlatımdan bir kural taslağı çıkar. YALNIZCA şu JSON'u ver:
{{"name": "kural adı", "event_type": "olay türü veya boş", "conditions": [{{"field": "alan", "op": "eq|ne|contains|in|gt|gte|lt|lte|exists", "value": "..."}}],
 "case_name": "açılacak işin adı; olay alanları {{{{alan}}}} biçiminde", "kind": "CASE veya PROJECT",
 "requirements": "açılacak işin isterleri: amaç, yapılacaklar, kontrol/onay noktaları, teslim; olay alanları {{{{alan}}}} ile",
 "notes": "kullanıcının kontrol etmesi gerekenler"}}
Kurallar: Yalnızca örnek olayda veya anlatımda geçen alanları kullan; alan uydurma. Türkçe yaz.
ANLATIM:
{text}
ÖRNEK OLAY (varsa):
{sample}"""


async def suggest(tenant_id: uuid.UUID, text_: str, sample: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    from app.services import llm_gateway
    from app.services.llm_gateway import LLMContext

    prompt = SUGGEST_PROMPT.format(text=text_.strip()[:4000],
                                   sample=json.dumps(clip_payload(sample), ensure_ascii=False)[:6000] if sample else "(yok)")
    ctx = LLMContext(tenant_id=tenant_id, purpose="BRAIN", task_type="STRUCTURED")
    messages = [{"role": "user", "content": prompt}]
    data, result = None, None
    for _ in range(2):
        result = await llm_gateway.chat(ctx, messages, temperature=0.2, max_tokens=2500, timeout=180, fallback=True)
        m = re.search(r"\{.*\}", result.content or "", re.S)
        try:
            data = json.loads(m.group(0)) if m else None
        except ValueError:
            data = None
        if isinstance(data, dict) and data.get("name"):
            break
        messages += [{"role": "assistant", "content": result.content or ""}, {"role": "user", "content": "Yalnızca istenen JSON'u ver."}]
    if not isinstance(data, dict) or not data.get("name"):
        raise AutomationError("RECAi şu an kural taslağı üretemedi; biraz sonra yeniden deneyin.")
    try:
        conditions = clean_conditions(data.get("conditions") or [])
    except AutomationError:
        conditions = []
    if sample:  # örnek olayda olmayan alana koşul yazılmaz
        conditions = [c for c in conditions if get_path(sample, c["field"]) is not None or c["op"] == "exists"]
    return {"name": str(data.get("name"))[:160], "event_type": str(data.get("event_type") or "")[:120] or None,
            "conditions": conditions, "case_name": str(data.get("case_name") or "")[:200],
            "kind": "PROJECT" if str(data.get("kind")).upper() == "PROJECT" else "CASE",
            "requirements": str(data.get("requirements") or "")[:8000], "notes": str(data.get("notes") or "")[:1000],
            "model": result.public_model}


# ---------------------------------------------------------------- çıktı
def out(rule: AutomationRule, conn: Optional[IntegrationConnection] = None, webhook_url: Optional[str] = None) -> Dict[str, Any]:
    return {"id": str(rule.id), "name": rule.name, "description": rule.description, "status": rule.status, "trigger": rule.trigger,
            "connection_id": str(rule.connection_id) if rule.connection_id else None, "connection_name": conn.name if conn else None,
            "event_type": rule.event_type, "poll": rule.poll, "schedule": rule.schedule, "conditions": rule.conditions or [],
            "action": rule.action, "requirements": rule.requirements, "rate_limit_per_hour": rule.rate_limit_per_hour,
            "has_secret": bool(rule.webhook_secret), "webhook_url": webhook_url if rule.trigger == "WEBHOOK" else None,
            "next_run_at": rule.next_run_at, "last_fired_at": rule.last_fired_at, "fire_count": rule.fire_count,
            "last_error": rule.last_error, "polling_started": bool((rule.cursor or {}).get("initialized")),
            "created_at": rule.created_at, "updated_at": rule.updated_at}


def log_out(r: AutomationLog, with_payload: bool = False) -> Dict[str, Any]:
    d = {"id": str(r.id), "rule_id": str(r.rule_id) if r.rule_id else None, "rule_name": r.rule_name, "source": r.source,
         "event_type": r.event_type, "external_ref": r.external_ref, "outcome": r.outcome, "detail": r.detail,
         "project_id": str(r.project_id) if r.project_id else None, "created_at": r.created_at}
    if with_payload:
        d["payload"] = r.payload
    return d
