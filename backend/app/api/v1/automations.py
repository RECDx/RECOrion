"""
Otomasyon kuralları ve imzalı anlık bildirim (ADIM 13.2).

Kuralları integration:manage yetkisi olan şirket kullanıcısı yönetir; KVKK: RECDx Süper Admin şirketin kurallarını ve
günlüğünü göremez. Anlık bildirim ucu herkese açıktır; kimlik imzayla (HMAC-SHA256 + zaman damgası) uç içinde doğrulanır.
İmza anahtarı yalnızca oluşturulurken / yenilenirken bir kez gösterilir.
"""
import json
import uuid
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core import vault
from app.core.audit import write_audit_event
from app.core.security import CurrentUser, ensure_tenant_content, forbidden, get_current_user
from app.core.tokens import hit_rate_limit
from app.db.models import AutomationLog, AutomationRule, IntegrationConnection, IntegrationMapping, ProjectTemplate, Tenant
from app.db.session import get_db
from app.services import automations as svc
from app.services import business_objects as bo
from app.services import expenses, recdx_apps
from app.services import support
from app.services.llm_gateway import LLMError

router = APIRouter(tags=["Otomasyonlar"])
HOOK_RATE = (60, 60)  # kural başına dakikada 60 anlık bildirim
BODY_LIMIT = 256 * 1024


def _manage(user: CurrentUser, tenant_id: uuid.UUID) -> None:
    ensure_tenant_content(user, tenant_id)
    if not user.has("automation:manage"):
        raise forbidden("Otomasyonları yalnızca otomasyon kuralları yetkisi olanlar yönetebilir.")


def hook_url(rule: AutomationRule) -> str:
    return f"{settings.PUBLIC_APP_URL.rstrip('/')}/api/v1/hooks/{rule.id}"


async def _rule(db: AsyncSession, user: CurrentUser, tenant_id: uuid.UUID, rid: uuid.UUID) -> AutomationRule:
    _manage(user, tenant_id)
    rule = await db.get(AutomationRule, rid)
    if not rule or rule.tenant_id != tenant_id or rule.status == "ARCHIVED":
        raise HTTPException(status_code=404, detail="Otomasyon bulunamadı.")
    return rule


async def _out(db: AsyncSession, rule: AutomationRule) -> Dict[str, Any]:
    conn = await db.get(IntegrationConnection, rule.connection_id) if rule.connection_id else None
    return svc.out(rule, conn, hook_url(rule))


class RuleIn(BaseModel):
    name: str = Field(..., min_length=2, max_length=160)
    description: Optional[str] = Field(None, max_length=2000)
    trigger: str
    connection_id: Optional[uuid.UUID] = None
    event_type: Optional[str] = Field(None, max_length=120)
    poll: Optional[Dict[str, Any]] = None
    schedule: Optional[Dict[str, Any]] = None
    conditions: List[Dict[str, Any]] = []
    action: Dict[str, Any]
    requirements: Optional[str] = Field(None, max_length=20000)
    rate_limit_per_hour: int = Field(20, ge=1, le=200)


async def _apply(db: AsyncSession, rule: AutomationRule, p: RuleIn) -> None:
    trigger = p.trigger.upper()
    if trigger not in svc.TRIGGERS:
        raise HTTPException(status_code=422, detail="Tetik anlık bildirim (WEBHOOK), izleme (POLL) veya zamanlayıcı (SCHEDULE) olmalı.")
    try:
        conn = None
        if p.connection_id:
            conn = await db.get(IntegrationConnection, p.connection_id)
            if not conn or conn.tenant_id != rule.tenant_id:
                raise svc.AutomationError("Bağlantı bulunamadı.")
        if trigger == "POLL" and not conn:
            raise svc.AutomationError("İzleme için bir bağlantı seçin.")
        rule.trigger, rule.connection_id = trigger, conn.id if conn else None
        rule.name, rule.description = p.name.strip(), (p.description or "").strip() or None
        rule.event_type = (p.event_type or "").strip() or None
        rule.conditions = svc.clean_conditions(p.conditions)
        new_poll = svc.clean_poll(p.poll) if trigger == "POLL" else None
        if new_poll != rule.poll:  # izlenen sorgu değişince başlangıç noktası yeniden alınır
            rule.cursor = None
        rule.poll = new_poll
        rule.schedule = svc.clean_schedule(p.schedule) if trigger == "SCHEDULE" else None
        rule.action = await svc.clean_action(db, rule.tenant_id, p.action)
        rule.requirements = (p.requirements or "").strip() or None
        rule.rate_limit_per_hour = p.rate_limit_per_hour
    except svc.AutomationError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    rule.next_run_at = svc.initial_next_run(rule)


def _secret(rule: AutomationRule) -> str:
    secret = svc.new_secret()
    rule.webhook_secret = vault.seal({"secret": secret}, svc.binding(rule))
    return secret


@router.get("/company/{tenant_id}/automations")
async def list_rules(tenant_id: uuid.UUID, user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    _manage(user, tenant_id)
    rows = (await db.execute(select(AutomationRule).where(AutomationRule.tenant_id == tenant_id, AutomationRule.status != "ARCHIVED")
                             .order_by(AutomationRule.created_at.desc()))).scalars().all()
    return [await _out(db, r) for r in rows]


@router.post("/company/{tenant_id}/automations", status_code=201)
async def create_rule(tenant_id: uuid.UUID, payload: RuleIn, user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    _manage(user, tenant_id)
    rule = AutomationRule(id=uuid.uuid4(), tenant_id=tenant_id, created_by_actor_id=user.actor_id, status="ACTIVE", action={})
    await _apply(db, rule, payload)
    secret = _secret(rule) if rule.trigger == "WEBHOOK" else None
    db.add(rule)
    await db.commit()
    await write_audit_event(action="AUTOMATION_CREATED", actor_id=user.actor_id, target_type="automation_rule", target_id=str(rule.id),
                            payload={"name": rule.name, "trigger": rule.trigger})
    out = await _out(db, rule)
    if secret:
        out["webhook_secret"] = secret  # yalnızca bu yanıtta
    return out


@router.put("/company/{tenant_id}/automations/{rid}")
async def update_rule(tenant_id: uuid.UUID, rid: uuid.UUID, payload: RuleIn, user: CurrentUser = Depends(get_current_user),
                      db: AsyncSession = Depends(get_db)):
    rule = await _rule(db, user, tenant_id, rid)
    await _apply(db, rule, payload)
    secret = _secret(rule) if rule.trigger == "WEBHOOK" and not rule.webhook_secret else None
    await db.commit()
    out = await _out(db, rule)
    if secret:
        out["webhook_secret"] = secret
    return out


class StatusIn(BaseModel):
    status: str


@router.post("/company/{tenant_id}/automations/{rid}/status")
async def set_status(tenant_id: uuid.UUID, rid: uuid.UUID, payload: StatusIn, user: CurrentUser = Depends(get_current_user),
                     db: AsyncSession = Depends(get_db)):
    rule = await _rule(db, user, tenant_id, rid)
    status = payload.status.upper()
    if status not in ("ACTIVE", "PAUSED", "ARCHIVED"):
        raise HTTPException(status_code=422, detail="Durum ACTIVE, PAUSED veya ARCHIVED olmalı.")
    rule.status = status
    if status == "ACTIVE":
        rule.next_run_at = rule.next_run_at or svc.initial_next_run(rule)
    await db.commit()
    await write_audit_event(action="AUTOMATION_STATUS", actor_id=user.actor_id, target_type="automation_rule", target_id=str(rule.id),
                            payload={"status": status})
    return await _out(db, rule)


@router.post("/company/{tenant_id}/automations/{rid}/rotate-secret")
async def rotate_secret(tenant_id: uuid.UUID, rid: uuid.UUID, user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    rule = await _rule(db, user, tenant_id, rid)
    if rule.trigger != "WEBHOOK":
        raise HTTPException(status_code=409, detail="İmza anahtarı yalnızca anlık bildirim kurallarında vardır.")
    secret = _secret(rule)
    await db.commit()
    await write_audit_event(action="AUTOMATION_SECRET_ROTATED", actor_id=user.actor_id, target_type="automation_rule", target_id=str(rule.id))
    return {**(await _out(db, rule)), "webhook_secret": secret}


class TestIn(BaseModel):
    payload: Dict[str, Any] = {}
    event_type: Optional[str] = None


@router.post("/company/{tenant_id}/automations/{rid}/test")
async def test_rule(tenant_id: uuid.UUID, rid: uuid.UUID, payload: TestIn, user: CurrentUser = Depends(get_current_user),
                    db: AsyncSession = Depends(get_db)):
    """Örnek olayla dener: koşullar ve döngü engeli değerlendirilir, ne olacağı söylenir; hiçbir şey açılmaz."""
    rule = await _rule(db, user, tenant_id, rid)
    sample = payload.payload
    enrich = (rule.poll or {}).get("enrich")
    if enrich == "helpdesk_ticket":
        sample = support.normalize_sample(sample)
    elif enrich == "hr_expense":
        sample = expenses.normalize_sample(sample)
    rid_ = svc.get_path(sample, (rule.poll or {}).get("id_field") or "id")
    return await svc.handle(db, rule, "TEST", sample, event_type=payload.event_type,
                            record_id=str(rid_) if rid_ is not None else None, test=True)


@router.post("/company/{tenant_id}/automations/{rid}/run")
async def run_now(tenant_id: uuid.UUID, rid: uuid.UUID, user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """İzleme kuralını hemen çalıştırır (ilk çalıştırma yalnızca başlangıç noktasını alır); zamanlayıcı kuralını şimdiki zamanla
    bir kez çalıştırır (ör. ay sonu kapanışını beklemeden; sıradaki çalışma zamanı değişmez)."""
    rule = await _rule(db, user, tenant_id, rid)
    if rule.trigger not in ("POLL", "SCHEDULE"):
        raise HTTPException(status_code=409, detail="Hemen çalıştırma izleme ve zamanlayıcı kurallarında vardır; diğerlerini örnek olayla deneyin.")
    if rule.status != "ACTIVE":
        raise HTTPException(status_code=409, detail="Kural duraklatılmış.")
    if rule.trigger == "SCHEDULE":
        try:
            sample = await svc.schedule_payload(db, rule, svc.now())
        except Exception as exc:
            raise HTTPException(status_code=502, detail=f"Zamanlayıcı özeti okunamadı: {str(exc)[:300]}")
        return {"handled": [await svc.handle(db, rule, "SCHEDULE", sample, event_type="schedule",
                                             dedupe_key=f"manual:{svc.now():%Y-%m-%dT%H:%M:%S}")]}
    res = await svc.poll(db, rule)
    if res.get("error"):
        raise HTTPException(status_code=502, detail=res["error"])
    return res


@router.get("/company/{tenant_id}/automations/{rid}/log")
async def rule_log(tenant_id: uuid.UUID, rid: uuid.UUID, limit: int = Query(50, le=200), user: CurrentUser = Depends(get_current_user),
                   db: AsyncSession = Depends(get_db)):
    _manage(user, tenant_id)
    rows = (await db.execute(select(AutomationLog).where(AutomationLog.tenant_id == tenant_id, AutomationLog.rule_id == rid)
                             .order_by(AutomationLog.created_at.desc()).limit(limit))).scalars().all()
    return [svc.log_out(r, with_payload=True) for r in rows]


@router.get("/company/{tenant_id}/automation-log")
async def tenant_log(tenant_id: uuid.UUID, limit: int = Query(100, le=500), user: CurrentUser = Depends(get_current_user),
                     db: AsyncSession = Depends(get_db)):
    _manage(user, tenant_id)
    rows = (await db.execute(select(AutomationLog).where(AutomationLog.tenant_id == tenant_id)
                             .order_by(AutomationLog.created_at.desc()).limit(limit))).scalars().all()
    return [svc.log_out(r) for r in rows]


class SuggestIn(BaseModel):
    text: str = Field(..., min_length=10, max_length=4000)
    sample: Optional[Dict[str, Any]] = None


@router.post("/company/{tenant_id}/automations/suggest")
async def suggest(tenant_id: uuid.UUID, payload: SuggestIn, user: CurrentUser = Depends(get_current_user)):
    """RECAi anlatımdan kural taslağı ve açılacak işin isterlerini yazar; kaydedilmez."""
    _manage(user, tenant_id)
    try:
        return await svc.suggest(tenant_id, payload.text, payload.sample)
    except svc.AutomationError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except LLMError as exc:
        raise HTTPException(status_code=503, detail=str(exc))


# ---------------------------------------------------------------- RECDx uygulaması hazır kuralları (ADIM 13.3 RECQmind, 13.4 RECSlip)
PRESET_APPS = {
    "recqmind": {"svc": support, "label": "RECQmind", "object_type": "SUPPORT_TICKET", "mapping": "odoo_helpdesk_ticket",
                 "mapping_label": "Helpdesk", "target_label": "bilete", "interval": 10,
                 "key": lambda p: p["category"], "title": lambda p: bo.SUPPORT_CATEGORY_LABELS[p["category"]],
                 "pick": "En az bir tür seçin (İade, İptal, Kargo, Ürün sorusu)."},
    "recslip": {"svc": expenses, "label": "RECSlip", "object_type": "EXPENSE_RECEIPT", "mapping": "odoo_expense",
                "mapping_label": "Masraf", "target_label": "masraf kaydına", "interval": 15,
                "key": lambda p: p["code"], "title": lambda p: p["label"],
                "pick": "En az bir kural seçin (Sorunlu fiş, Ay sonu kapanış)."},
}


def _app(app: str) -> Dict[str, Any]:
    if app not in PRESET_APPS:
        raise HTTPException(status_code=404, detail="Bu uygulamanın hazır kuralı yok.")
    return PRESET_APPS[app]


async def _preset_state(db: AsyncSession, tenant_id: uuid.UUID, app: str) -> Dict[str, Any]:
    cfg = _app(app)
    presets = cfg["svc"].PRESETS
    tenant = await db.get(Tenant, tenant_id)
    conns = (await db.execute(select(IntegrationConnection).where(IntegrationConnection.tenant_id == tenant_id,
                                                                  IntegrationConnection.connector == "odoo",
                                                                  IntegrationConnection.status == "ACTIVE"))).scalars().all()
    templates = {t.code: t.id for t in (await db.execute(select(ProjectTemplate).where(
        ProjectTemplate.tenant_id.is_(None), ProjectTemplate.status == "ACTIVE",
        ProjectTemplate.code.in_([p["template"] for p in presets])))).scalars()}
    mappings = (await db.execute(select(IntegrationMapping).where(IntegrationMapping.tenant_id == tenant_id,
                                                                  IntegrationMapping.object_type == cfg["object_type"],
                                                                  IntegrationMapping.status != "ARCHIVED"))).scalars().all()
    rules = (await db.execute(select(AutomationRule).where(AutomationRule.tenant_id == tenant_id, AutomationRule.status != "ARCHIVED",
                                                           AutomationRule.name.in_([p["name"] for p in presets])))).scalars().all()
    active = recdx_apps.is_active(tenant, app) if tenant else False
    reason = None if active else (f"{cfg['label']} şirketinizde açık değil (Şirket Yönetimi → RECDx uygulamaları: Odoo var ve "
                                  "'Zaten kullanıyorum' / 'Paketime ekle').")
    if active and not conns:
        reason = f"Etkin bir Odoo bağlantısı yok; Entegrasyonlar'dan {cfg['label']}'in kurulu olduğu Odoo'yu bağlayın."
    return {"tenant": tenant, "connections": conns, "templates": templates, "mappings": mappings, "rules": rules,
            "available": reason is None, "reason": reason}


@router.get("/company/{tenant_id}/automations/presets/{app}")
async def app_presets(tenant_id: uuid.UUID, app: str, user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Uygulamanın hazır kuralları: açılabilir mi, hangi bağlantılar, hangileri zaten kurulu."""
    _manage(user, tenant_id)
    cfg = _app(app)
    st = await _preset_state(db, tenant_id, app)
    have = {(r.name, str(r.connection_id)) for r in st["rules"]}
    return {"available": st["available"], "reason": st["reason"],
            "connections": [{"id": str(c.id), "name": c.name} for c in st["connections"]],
            "mappings": [{"id": str(m.id), "name": m.name, "status": m.status, "connection_id": str(m.connection_id)} for m in st["mappings"]],
            "categories": [{"code": cfg["key"](p), "label": cfg["title"](p), "rule_name": p["name"],
                            "template_ready": p["template"] in st["templates"],
                            "installed_on": [cid for (n, cid) in have if n == p["name"]]} for p in cfg["svc"].PRESETS]}


class PresetIn(BaseModel):
    connection_id: uuid.UUID
    manager_actor_id: uuid.UUID
    categories: Optional[List[str]] = None  # boşsa hepsi
    interval_minutes: Optional[int] = Field(None, ge=5, le=1440)
    auto_start: bool = False


@router.post("/company/{tenant_id}/automations/presets/{app}", status_code=201)
async def install_presets(tenant_id: uuid.UUID, app: str, payload: PresetIn, user: CurrentUser = Depends(get_current_user),
                          db: AsyncSession = Depends(get_db)):
    """Seçilen hazır kuralları kurar; bağlantıda uygulamanın eşlemesi yoksa hazır eşlemeden TASLAK kopya açar
    (Case sonucunun Odoo kaydına yazılabilmesi için eşlemenin Eşleme Stüdyosu'nda denenip onaylanması gerekir)."""
    _manage(user, tenant_id)
    cfg = _app(app)
    svc_, presets = cfg["svc"], cfg["svc"].PRESETS
    st = await _preset_state(db, tenant_id, app)
    if not st["available"]:
        raise HTTPException(status_code=409, detail=st["reason"])
    conn = next((c for c in st["connections"] if c.id == payload.connection_id), None)
    if not conn:
        raise HTTPException(status_code=404, detail="Odoo bağlantısı bulunamadı veya etkin değil.")
    allowed = [m.strip() for m in ((conn.config or {}).get("allowed_models") or "").split(",") if m.strip()]
    if allowed and svc_.MODEL not in allowed:
        raise HTTPException(status_code=422, detail=f"Bu bağlantıda {svc_.MODEL} modeli izinli değil; bağlantı ayarlarında izinli modellere ekleyin.")
    keys = {cfg["key"](p) for p in presets}
    chosen = payload.categories if payload.categories is not None else [cfg["key"](p) for p in presets]
    cats = [c for c in dict.fromkeys(x.upper() for x in chosen) if c in keys]
    if not cats:
        raise HTTPException(status_code=422, detail=cfg["pick"])
    notes: List[str] = []
    mapping = next((m for m in st["mappings"] if m.connection_id == conn.id), None)
    if not mapping:
        tpl = (await db.execute(select(IntegrationMapping).where(IntegrationMapping.tenant_id.is_(None),
                                                                 IntegrationMapping.code == cfg["mapping"]))).scalars().first()
        if tpl:
            mapping = IntegrationMapping(tenant_id=tenant_id, connection_id=conn.id, connector="odoo", object_type=tpl.object_type,
                                         name=tpl.name, description=tpl.description, target=tpl.target, rules=tpl.rules, match=tpl.match,
                                         when=tpl.when, source_template_id=tpl.id, status="DRAFT", created_by_actor_id=user.actor_id)
            db.add(mapping)
            await db.flush()
            notes.append(f"{cfg['mapping_label']} eşlemesi taslak olarak eklendi: Eşleme Stüdyosu'nda 'Dene' ve 'Onayla' yapılınca "
                         f"Case sonuçları {cfg['target_label']} yazılabilir.")
        else:
            notes.append(f"Hazır {cfg['mapping_label']} eşlemesi bulunamadı; Case sonucu {cfg['target_label']} yazılmaz.")
    elif mapping.status != "ACTIVE":
        notes.append(f"{cfg['mapping_label']} eşlemesi henüz onaylı değil: onaylanınca Case sonuçları {cfg['target_label']} yazılabilir.")
    have = {(r.name, r.connection_id) for r in st["rules"]}
    created = []
    for spec in svc_.preset_rules(conn.id, payload.manager_actor_id, st["templates"], cats, mapping.id if mapping else None,
                                  payload.interval_minutes or cfg["interval"], payload.auto_start):
        if (spec["name"], conn.id) in have:
            notes.append(f"'{spec['name']}' bu bağlantıda zaten kurulu; atlandı.")
            continue
        rule = AutomationRule(id=uuid.uuid4(), tenant_id=tenant_id, created_by_actor_id=user.actor_id, status="ACTIVE", action={})
        await _apply(db, rule, RuleIn(**spec))
        db.add(rule)
        created.append(rule)
    missing = [cfg["title"](p) for p in presets if cfg["key"](p) in cats and p["template"] not in st["templates"]]
    if missing:
        notes.append("Şablonu bulunamayan kurallar kurulmadı: " + ", ".join(missing))
    await db.commit()
    for rule in created:
        await write_audit_event(action="AUTOMATION_CREATED", actor_id=user.actor_id, target_type="automation_rule", target_id=str(rule.id),
                                payload={"name": rule.name, "trigger": rule.trigger, "preset": app})
    return {"rules": [await _out(db, r) for r in created], "mapping": {"id": str(mapping.id), "status": mapping.status} if mapping else None,
            "notes": notes}


# ---------------------------------------------------------------- anlık bildirim (herkese açık; imzayla)
@router.post("/hooks/{rid}", status_code=202)
async def webhook(rid: uuid.UUID, request: Request, db: AsyncSession = Depends(get_db)):
    if await hit_rate_limit(f"hook:{rid}", *HOOK_RATE):
        raise HTTPException(status_code=429, detail="Çok fazla istek; biraz sonra yeniden deneyin.")
    rule = await db.get(AutomationRule, rid)
    if not rule or rule.trigger != "WEBHOOK" or rule.status == "ARCHIVED":
        raise HTTPException(status_code=404, detail="Uç bulunamadı.")
    body = await request.body()
    if len(body) > BODY_LIMIT:
        raise HTTPException(status_code=413, detail="İstek gövdesi çok büyük (en fazla 256 KB).")
    h = request.headers
    error = svc.verify(rule, h.get("x-recorion-timestamp"), h.get("x-recorion-signature"), body)
    if error:
        await svc._log(db, rule, rule.tenant_id, "WEBHOOK", "REJECTED", error)
        await db.commit()
        raise HTTPException(status_code=401, detail=error)
    try:
        payload = json.loads(body or b"{}")
    except ValueError:
        raise HTTPException(status_code=400, detail="Gövde geçerli JSON olmalı.")
    if not isinstance(payload, dict):
        payload = {"items": payload}
    event_type = h.get("x-recorion-event") or (str(payload.get("event")) if payload.get("event") else None)
    record_id = payload.get("id") if isinstance(payload.get("id"), (str, int)) else None
    delivery = h.get("x-recorion-delivery") or (f"{event_type or 'event'}:{record_id}" if record_id is not None else None)
    ref = str(payload.get("ref") or "")[:255] or (f"{event_type or 'event'}:{record_id}" if record_id is not None else None)
    return await svc.handle(db, rule, "WEBHOOK", payload, event_type=event_type, external_ref=ref, dedupe_key=delivery,
                            record_id=str(record_id) if record_id is not None else None)
