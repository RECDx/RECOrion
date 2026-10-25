"""
Çıktıdan kayda aktarım (ADIM 12.4): RECAi'nin ürettiği iş çıktısı → onaylı eşleme → şirketin kendi sistemi.

Akış:
1. Tetik: elle (proje yöneticisi "Sisteme aktar"), adım bitince (adımda tanımlı eşlemeler) veya proje kapanınca.
2. RECAi çıktıdan ortak iş nesnelerini çıkarır (bir çıktıda birden çok ürün/cari olabilir; her biri ayrı aktarım).
3. Eşleme ile hedef değerleri üretilir (yalnızca okuma/arama). Eksik/hatalıysa NEEDS_FIX: kullanıcı nesneyi düzeltir.
4. Önizleme onaya düşer: onaylayıcı proje yöneticisi (proje yoksa entegrasyon yöneticisi). Şirket kuralı gereği (nesne türü,
   tutar eşiği) ikinci onay entegrasyon yöneticisinden ve FARKLI bir kişiden gelir.
5. Onaylanınca Temporal kuyruğunda yazılır (kesinti/geçici hatada yeniden denenir; iş mantığı hatasında durur).
   Eşleştirme alanı varsa önce hedefte aranır: kayıt varsa güncellenir, yoksa açılır — çift kayıt olmaz (dış kayıt bağı).
   Güncellemeden önce eski değerler saklanır.
6. Geri alma: açılan kayıt arşivlenir (siparişte iptal edilir); güncellenen kaydın eski değerleri geri yazılır.
Hiçbir yazma onaysız yapılmaz; her adım silinemez aktarım kaydına düşer. Şahıs carisinin TCKN'si ekranda maskelenir.
"""
import asyncio
import json
import logging
import re
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import (Actor, ExternalLink, IntegrationConnection, IntegrationMapping, IntegrationTransfer, Project, Task,
                           Tenant)
from app.integrations.base import ToolError
from app.services import business_objects as bo
from app.services import llm_gateway
from app.services import mappings as ms
from app.services.llm_gateway import LLMContext, LLMError

logger = logging.getLogger("recorion.transfers")
DEFAULT_POLICY = {"double_approval_objects": ["ORDER"], "amount_threshold": 100000}
MAX_ITEMS = 20
OUTPUT_LIMIT = 30000
CANCEL_METHODS = {"sale.order": "action_cancel", "purchase.order": "button_cancel"}
OPEN = ("EXTRACTING", "NEEDS_FIX", "PENDING_APPROVAL", "APPROVED", "RUNNING")
_tasks: set = set()


class TransferFailed(Exception):
    """İş mantığı hatası (hedef sistem kaydı reddetti): yeniden denenmez."""


def now() -> datetime:
    return datetime.now(timezone.utc)


def session():
    from app.workflows.activities import session as s

    return s()


# --- şirket kuralları ---

def policy(tenant: Tenant) -> Dict[str, Any]:
    return {**DEFAULT_POLICY, **((tenant.settings or {}).get("transfer") or {})}


def amount(object_type: str, obj: Dict[str, Any]) -> Decimal:
    if object_type == "ORDER":
        total = Decimal(0)
        for line in obj.get("lines") or []:
            q, p, d = Decimal(str(line.get("quantity") or 0)), Decimal(str(line.get("unit_price") or 0)), Decimal(str(line.get("discount") or 0))
            total += q * p * (1 - d / 100)
        return total.quantize(Decimal("0.01"))
    if object_type == "PRODUCT":
        return Decimal(str(obj.get("sale_price") or 0)).quantize(Decimal("0.01"))
    return Decimal(0)


def required_approvals(pol: Dict[str, Any], object_type: str, amt: Decimal) -> int:
    if object_type in (pol.get("double_approval_objects") or []):
        return 2
    thr = pol.get("amount_threshold")
    return 2 if thr not in (None, "") and amt > Decimal(str(thr)) else 1


# --- RECAi: çıktıdan nesne çıkarma ---

EXTRACT_PROMPT = """Sen RECAi'sin. Aşağıdaki iş çıktısından şirketin sistemine aktarılacak "{label}" kayıtlarını çıkar.
Yalnızca çıktıda AÇIKÇA geçen bilgileri yaz; olmayan alanı boş bırak, uydurma (fiyat, kod, VKN, tarih tahmin etme).
Sayıları sayı olarak yaz (1.250,50 → 1250.5). Seçenekli alanlarda yalnızca listelenen kodları kullan.
En fazla {max_items} kayıt. Yanıtın YALNIZCA şu JSON olsun: {{"items": [{{...alanlar...}}], "notes": "kısa not veya boş"}}
ALANLAR:
{fields}
İŞ ÇIKTISI:
"""


def _field_brief(fields: List[Dict[str, Any]], indent: str = "- ") -> str:
    out = []
    for f in fields:
        line = f"{indent}{f['key']}: {f['label']} [{f['type']}{', zorunlu' if f.get('required') else ''}"
        if f.get("options"):
            line += ", seçenekler " + "/".join(f["options"])
        out.append(line + "]")
        if f["type"] == "lines":
            out.append(_field_brief(f["fields"], "    - "))
    return "\n".join(out)


async def extract(tenant_id: uuid.UUID, project_id: Optional[uuid.UUID], object_type: str, text: str) -> Dict[str, Any]:
    spec = bo.OBJECTS[object_type]
    prompt = EXTRACT_PROMPT.format(label=spec["label"], max_items=MAX_ITEMS, fields=_field_brief(spec["fields"]))
    ctx = LLMContext(tenant_id=tenant_id, purpose="BRAIN", project_id=project_id, task_type="STRUCTURED")
    messages = [{"role": "user", "content": prompt + text[:OUTPUT_LIMIT]}]
    for _ in range(2):
        result = await llm_gateway.chat(ctx, messages, temperature=0.1, max_tokens=6000, timeout=240, fallback=True)
        m = re.search(r"\{.*\}", result.content or "", re.S)
        try:
            data = json.loads(m.group(0)) if m else None
        except ValueError:
            data = None
        if isinstance(data, dict) and isinstance(data.get("items"), list):
            return {"items": [i for i in data["items"] if isinstance(i, dict)][:MAX_ITEMS], "notes": str(data.get("notes") or "")[:500],
                    "model": result.public_model}
        messages += [{"role": "assistant", "content": result.content or ""}, {"role": "user", "content": "Yalnızca istenen JSON'u ver."}]
    raise ValueError("RECAi çıktıdan kayıt çıkaramadı.")


async def output_text(db: AsyncSession, task: Task) -> str:
    from app.services import agent_work

    return await agent_work.artifact_text(await agent_work.latest_artifact(db, task.id), 200_000)


async def project_text(db: AsyncSession, project: Project) -> str:
    tasks = (await db.execute(select(Task).where(Task.project_id == project.id, Task.status == "DONE").order_by(Task.created_at))).scalars()
    parts = [f"PROJE: {project.name}\n{project.close_summary or ''}"]
    for t in tasks:
        txt = await output_text(db, t)
        if txt:
            parts.append(f"\n## {t.title}\n{txt[:8000]}")
    return "\n".join(parts)


# --- öneri (onaya düşen aktarım) ---

async def _mapping_ready(db: AsyncSession, tenant_id: uuid.UUID, mapping_id) -> tuple:
    m = await db.get(IntegrationMapping, mapping_id)
    if not m or m.tenant_id != tenant_id or m.status != "ACTIVE":
        raise ValueError("Eşleme bulunamadı veya onaylı değil.")
    conn = await db.get(IntegrationConnection, m.connection_id) if m.connection_id else None
    if not conn or conn.status != "ACTIVE":
        raise ValueError("Eşlemenin bağlantısı etkin değil.")
    return m, conn


async def prepare(db: AsyncSession, tr: IntegrationTransfer, obj: Dict[str, Any]) -> IntegrationTransfer:
    """Nesneden hedef değerlerini üretir (okuma/arama) ve durumu belirler. Çağıran commit eder."""
    m, conn = await _mapping_ready(db, tr.tenant_id, tr.mapping_id)
    clean, errs = bo.validate(tr.object_type, obj)
    tgt = ms.adapter(conn)
    built = await ms.build(m, clean or obj, tgt)
    errors = list(dict.fromkeys(errs + built.errors))
    if not ms.applies(m, clean):
        errors.append(f"Bu kayıt eşlemenin koşuluna uymuyor ({m.when.get('field')} = {m.when.get('equals')}).")
    action = "CREATE"
    match = m.match or {}
    if not errors and match.get("source") and clean.get(match["source"]) not in (None, ""):
        try:
            action = "UPDATE" if await tgt.find(m.target, match["target"], clean[match["source"]]) else "CREATE"
        except (ToolError, ms.MappingError) as exc:
            built.warnings.append(f"Mevcut kayıt aranamadı: {exc}")
    tenant = await db.get(Tenant, tr.tenant_id)
    amt = amount(tr.object_type, clean)
    tr.object, tr.values, tr.preview, tr.action, tr.amount = clean or obj, built.values, built.preview, action, amt
    tr.problems = {"errors": errors, "warnings": built.warnings}
    tr.mapping_version, tr.connection_id, tr.connection_name = m.version, conn.id, conn.name
    tr.required_approvals = required_approvals(policy(tenant), tr.object_type, amt)
    tr.approvals, tr.error = [], None
    tr.status = "NEEDS_FIX" if errors else "PENDING_APPROVAL"
    return tr


async def propose(db: AsyncSession, tenant_id: uuid.UUID, mapping_id, trigger: str, text: str, project: Optional[Project] = None,
                  task: Optional[Task] = None, actor: Optional[Actor] = None,
                  placeholder: Optional[IntegrationTransfer] = None) -> List[IntegrationTransfer]:
    """RECAi çıktıdan nesneleri çıkarır; her nesne için aktarım önerisi açar ve onaylayıcıya bildirir.
    placeholder: ekranda hemen görünen "hazırlanıyor" kaydı; ilk nesne ona yazılır."""
    m, _ = await _mapping_ready(db, tenant_id, mapping_id)
    base = dict(tenant_id=tenant_id, project_id=project.id if project else None, task_id=task.id if task else None, mapping_id=m.id,
                object_type=m.object_type, trigger=trigger, created_by_actor_id=actor.id if actor else None,
                created_by_name=actor.display_name if actor else "RECAi")
    def fail(msg: str) -> List[IntegrationTransfer]:
        tr = placeholder or IntegrationTransfer(**base)
        tr.status, tr.error = "FAILED", msg
        db.add(tr)
        return [tr]
    if not text.strip():
        out = fail("Aktarılacak iş çıktısı bulunamadı.")
        await db.commit()
        return out
    try:
        found = await extract(tenant_id, project.id if project else None, m.object_type, text)
    except (LLMError, ValueError) as exc:
        out = fail(getattr(exc, "message", None) or str(exc))
        await db.commit()
        return out
    items = found["items"] or [{}]
    out = []
    for i, item in enumerate(items):
        tr = placeholder if (i == 0 and placeholder) else IntegrationTransfer(**base)
        db.add(tr)
        try:
            await prepare(db, tr, item)
        except (ToolError, ms.MappingError, ValueError) as exc:
            tr.object, tr.status, tr.problems = item, "NEEDS_FIX", {"errors": [str(exc)], "warnings": []}
        if found.get("notes") and tr.problems is not None:
            tr.problems["warnings"] = tr.problems.get("warnings", []) + [f"RECAi: {found['notes']}"]
        out.append(tr)
    await db.commit()
    for tr in out:
        await notify_pending(db, tr)
    return out


def spawn(coro) -> None:
    t = asyncio.create_task(coro)
    _tasks.add(t)
    t.add_done_callback(_tasks.discard)


async def propose_background(tenant_id: uuid.UUID, mapping_ids: List[str], trigger: str, project_id=None, task_id=None,
                             actor_id=None) -> None:
    async with session() as db:
        try:
            project = await db.get(Project, project_id) if project_id else None
            task = await db.get(Task, task_id) if task_id else None
            actor = await db.get(Actor, actor_id) if actor_id else None
            text = await output_text(db, task) if task else await project_text(db, project) if project else ""
            for mid in mapping_ids:
                try:
                    await propose(db, tenant_id, uuid.UUID(str(mid)), trigger, text, project, task, actor)
                except ValueError as exc:  # eşleme artık onaylı değil: önerilmez, kayda geçer
                    logger.warning("Aktarım önerilemedi (%s): %s", mid, exc)
        except Exception:
            logger.exception("Aktarım önerisi hazırlanamadı")


async def fill_background(transfer_id: uuid.UUID, text_from: str) -> None:
    """Elle başlatılan önerinin "hazırlanıyor" kaydını arka planda doldurur."""
    async with session() as db:
        try:
            tr = await db.get(IntegrationTransfer, transfer_id)
            project = await db.get(Project, tr.project_id) if tr.project_id else None
            task = await db.get(Task, tr.task_id) if tr.task_id else None
            actor = await db.get(Actor, tr.created_by_actor_id) if tr.created_by_actor_id else None
            text = await output_text(db, task) if text_from == "TASK" and task else await project_text(db, project) if project else ""
            await propose(db, tr.tenant_id, tr.mapping_id, tr.trigger, text, project, task, actor, placeholder=tr)
        except Exception as exc:
            logger.exception("Aktarım önerisi hazırlanamadı")
            async with session() as db2:
                tr = await db2.get(IntegrationTransfer, transfer_id)
                if tr and tr.status == "EXTRACTING":
                    tr.status, tr.error = "FAILED", f"Öneri hazırlanamadı ({exc.__class__.__name__})."
                    await db2.commit()


async def after_step_done(db: AsyncSession, task: Task, project: Project) -> None:
    """Adım bitince (onaylı veya onaysız) adımda tanımlı eşlemelerle aktarım önerileri (arka planda)."""
    if task.transfer_mapping_ids:
        spawn(propose_background(project.tenant_id, list(task.transfer_mapping_ids), "STEP_DONE", project.id, task.id))


async def after_project_closed(project: Project) -> None:
    if project.status == "COMPLETED" and project.transfer_on_close:
        spawn(propose_background(project.tenant_id, list(project.transfer_on_close), "PROJECT_CLOSED", project.id, None))


# --- onay ---

async def _approvers(db: AsyncSession, tr: IntegrationTransfer) -> List[uuid.UUID]:
    project = await db.get(Project, tr.project_id) if tr.project_id else None
    if len(tr.approvals or []) == 0 and project and project.manager_actor_id:
        return [project.manager_actor_id]
    done = {a["actor_id"] for a in tr.approvals or []}
    admins = (await db.execute(select(Actor).where(Actor.tenant_id == tr.tenant_id, Actor.actor_type == "HUMAN",
                                                   Actor.role == "COMPANY_ADMIN", Actor.status != "DISABLED"))).scalars()
    return [a.id for a in admins if str(a.id) not in done]


async def notify_pending(db: AsyncSession, tr: IntegrationTransfer) -> None:
    from app.services import notify

    if tr.status == "NEEDS_FIX" and tr.project_id:
        project = await db.get(Project, tr.project_id)
        if project and project.manager_actor_id and project.manager_actor_id != tr.created_by_actor_id:
            try:
                await notify.send(db, project.manager_actor_id, f"RECOrion: '{project.name}' projesinde '{tr.connection_name}' aktarım önerisinde "
                                  "eksik/hatalı bilgi var; Aktarımlar bölümünden düzeltip onaya gönderin.")
            except Exception as exc:
                logger.warning("Aktarım düzeltme bildirimi gidemedi: %s", exc)
    if tr.status != "PENDING_APPROVAL":
        return
    second = len(tr.approvals or []) > 0
    text = (f"RECOrion: '{tr.connection_name}' sistemine aktarım {'ikinci ' if second else ''}onayınızı bekliyor "
            f"({bo.OBJECTS[tr.object_type]['label']}: {(tr.object or {}).get('name') or (tr.object or {}).get('title') or (tr.object or {}).get('partner_ref') or ''}). "
            "Onaylarım ekranından önizleyip onaylayın veya reddedin.")
    for aid in await _approvers(db, tr):
        try:
            await notify.send(db, aid, text)
        except Exception as exc:
            logger.warning("Aktarım onayı bildirilemedi: %s", exc)


async def can_decide(db: AsyncSession, user, tr: IntegrationTransfer) -> bool:
    if tr.tenant_id != user.tenant_id or user.is_platform_staff or tr.status != "PENDING_APPROVAL":
        return False
    done = {a["actor_id"] for a in tr.approvals or []}
    if str(user.actor_id) in done:
        return False  # aynı kişi iki kez onaylayamaz
    if not tr.approvals:  # ilk onay: proje yöneticisi veya entegrasyon yöneticisi
        project = await db.get(Project, tr.project_id) if tr.project_id else None
        return bool(project and project.manager_actor_id == user.actor_id) or user.has("integration:manage")
    return user.has("integration:manage")  # ikinci onay: entegrasyon yöneticisi


async def decide(db: AsyncSession, tr: IntegrationTransfer, user, approve: bool, note: Optional[str]) -> IntegrationTransfer:
    from fastapi import HTTPException

    if tr.status != "PENDING_APPROVAL":
        raise HTTPException(status_code=409, detail="Bu aktarım onay beklemiyor.")
    if not await can_decide(db, user, tr):
        raise HTTPException(status_code=403, detail="Bu aktarımı onaylama yetkiniz yok (aynı kişi iki kez onaylayamaz).")
    m = await db.get(IntegrationMapping, tr.mapping_id) if tr.mapping_id else None
    if approve and (not m or m.status != "ACTIVE" or m.version != tr.mapping_version):
        raise HTTPException(status_code=409, detail="Eşleme bu öneriden sonra değişti; önizlemeyi yenileyin.")
    if not approve:
        tr.status, tr.decision_note = "REJECTED", (note or "").strip() or None
        tr.approvals = (tr.approvals or []) + [{"actor_id": str(user.actor_id), "name": user.actor.display_name, "at": now().isoformat(),
                                                "note": tr.decision_note, "approve": False}]
        return tr
    tr.approvals = (tr.approvals or []) + [{"actor_id": str(user.actor_id), "name": user.actor.display_name, "at": now().isoformat(),
                                            "note": (note or "").strip() or None, "approve": True}]
    if len(tr.approvals) >= tr.required_approvals:
        tr.status = "APPROVED"
    return tr


# --- yazma (Temporal aktivitesi) ---

def _transient(msg: str) -> bool:
    return bool(re.search(r"ulaşılamadı|yanıt vermedi|çevrimdışı|geçici olarak|HTTP 50[234]|zaman aşımı|timeout", msg, re.I))


def _writable(v: Any) -> Any:
    """Odoo okuma biçimi → yazma biçimi: [id, ad] → id; [id, id...] (çoklu ilişki) → [[6, 0, [...]]]."""
    if isinstance(v, list) and len(v) == 2 and isinstance(v[0], int) and isinstance(v[1], str):
        return v[0]
    if isinstance(v, list) and all(isinstance(x, int) for x in v):
        return [[6, 0, v]]
    return v


async def _odoo_write(conn: IntegrationConnection, m: IntegrationMapping, tr: IntegrationTransfer) -> Dict[str, Any]:
    from app.integrations import odoo

    tgt = ms.adapter(conn)
    model = m.target["model"]
    vals = dict(tr.values or {})
    match = m.match or {}
    mv = str((tr.object or {}).get(match.get("source")) or "") if match.get("source") else ""
    existing = await tgt.find(m.target, match["target"], (tr.object or {})[match["source"]]) if mv else None
    if existing:
        plain = [k for k, v in vals.items() if not (isinstance(v, list) and v and isinstance(v[0], list) and v[0][0] == 0)]
        rows = await odoo._kw(tgt.ctx, model, "read", [[existing]], {"fields": plain}) if plain else []
        before = {k: _writable(v) for k, v in (rows[0] if rows else {}).items() if k != "id"}
        await odoo._kw(tgt.ctx, model, "write", [[existing], vals])
        rid, action = existing, "UPDATE"
    else:
        created = await odoo._kw(tgt.ctx, model, "create", [vals])
        rid, action, before = created[0] if isinstance(created, list) else created, "CREATE", None
    name = ""
    try:
        rows = await odoo._kw(tgt.ctx, model, "read", [[rid]], {"fields": ["display_name"]})
        name = (rows[0] or {}).get("display_name") or ""
    except ToolError:
        pass
    base = odoo._url(tgt.ctx)
    url = f"{base}/odoo/{model}/{rid}" if odoo._styles.get(base) == "json2" else f"{base}/web#id={rid}&model={model}&view_type=form"
    return {"id": str(rid), "action": action, "before": before, "ref": f"{name or model} (#{rid})", "url": url, "match_value": mv,
            "target_key": model}


async def _tool_write(conn: IntegrationConnection, m: IntegrationMapping, tr: IntegrationTransfer) -> Dict[str, Any]:
    from app.services import tool_gateway

    tools = {t.name: t for t in await tool_gateway.connection_tools(conn)}
    tool = tools.get(m.target.get("tool"))
    if not tool:
        raise TransferFailed(f"Bağlantıda '{m.target.get('tool')}' aracı artık yok.")
    match = m.match or {}
    mv = str((tr.object or {}).get(match.get("source")) or "") if match.get("source") else ""
    existing = await ms.adapter(conn).find(m.target, match["target"], (tr.object or {})[match["source"]]) if mv and m.target.get("find_tool") else None
    if existing not in (None, ""):
        upd = tools.get(m.target.get("update_tool") or "")
        if not upd:
            raise TransferFailed(f"Hedefte bu kayıt zaten var (#{existing}); güncelleme aracı tanımlı olmadığı için yeni kayıt açılmadı.")
        result = await upd.run(tool_gateway.context(conn), {**dict(tr.values or {}), "id": existing})
        rid = str(existing)
        text = (result.get("text") if isinstance(result, dict) else str(result)) or ""
        return {"id": rid, "action": "UPDATE", "before": None, "ref": f"{m.target.get('update_tool')} (#{rid})", "url": None,
                "result": {"text": text[:2000]}, "match_value": mv, "target_key": m.target.get("tool")}
    result = await tool.run(tool_gateway.context(conn), dict(tr.values or {}))
    data = result.get("data") if isinstance(result, dict) else None
    rid = str((data or {}).get("id") or (result.get("id") if isinstance(result, dict) else "") or "")
    text = (result.get("text") if isinstance(result, dict) else str(result)) or ""
    return {"id": rid or None, "action": "CREATE", "before": None, "ref": f"{m.target.get('tool')}{f' (#{rid})' if rid else ''}",
            "url": None, "result": {"text": text[:2000]}, "match_value": mv, "target_key": m.target.get("tool")}


async def execute(transfer_id: str) -> Dict[str, Any]:
    """Onaylı aktarımı yazar. Tekrarlanırsa (Temporal yeniden denemesi) DONE kayıt yeniden yazılmaz.
    Geçici hata → istisna (yeniden denenir); iş mantığı hatası → FAILED + TransferFailed (yeniden denenmez)."""
    async with session() as db:
        tr = await db.get(IntegrationTransfer, uuid.UUID(transfer_id))
        if not tr or tr.status not in ("APPROVED", "RUNNING"):
            return {"status": tr.status if tr else "MISSING"}
        m = await db.get(IntegrationMapping, tr.mapping_id)
        conn = await db.get(IntegrationConnection, tr.connection_id) if tr.connection_id else None
        if not m or not conn or conn.status != "ACTIVE":
            tr.status, tr.error = "FAILED", "Eşleme veya bağlantı artık etkin değil."
            await db.commit()
            raise TransferFailed(tr.error)
        tr.status, tr.attempts = "RUNNING", int(tr.attempts or 0) + 1
        await db.commit()
        try:
            res = await (_odoo_write(conn, m, tr) if conn.connector == "odoo" else _tool_write(conn, m, tr))
        except ToolError as exc:
            if _transient(str(exc)):
                tr.error = str(exc)[:1000]
                await db.commit()
                raise  # Temporal yeniden dener
            tr.status, tr.error = "FAILED", str(exc)[:1000]
            await db.commit()
            await _notify_result(db, tr)
            raise TransferFailed(tr.error)
        except TransferFailed as exc:
            tr.status, tr.error = "FAILED", str(exc)[:1000]
            await db.commit()
            await _notify_result(db, tr)
            raise
        tr.status, tr.action, tr.external_id, tr.external_ref, tr.external_url = "DONE", res["action"], res["id"], res["ref"][:255], res["url"]
        tr.before, tr.result, tr.error, tr.done_at = res["before"], res.get("result"), None, now()
        if res["id"] and res["match_value"]:
            link = (await db.execute(select(ExternalLink).where(ExternalLink.connection_id == conn.id, ExternalLink.target_key == res["target_key"],
                                                                ExternalLink.match_value == res["match_value"][:255]))).scalars().first()
            if link:
                link.external_id, link.last_transfer_id = res["id"], tr.id
            else:
                db.add(ExternalLink(tenant_id=tr.tenant_id, connection_id=conn.id, target_key=res["target_key"], match_value=res["match_value"][:255],
                                    external_id=res["id"], last_transfer_id=tr.id))
        await db.commit()
        await _notify_result(db, tr)
        return {"status": tr.status, "external_id": tr.external_id}


async def mark_failed(transfer_id: str, reason: str) -> None:
    async with session() as db:
        tr = await db.get(IntegrationTransfer, uuid.UUID(transfer_id))
        if tr and tr.status in ("APPROVED", "RUNNING"):
            tr.status, tr.error = "FAILED", (reason or "Aktarım yazılamadı.")[:1000]
            await db.commit()
            await _notify_result(db, tr)


async def _notify_result(db: AsyncSession, tr: IntegrationTransfer) -> None:
    from app.services import notify

    targets = {tr.created_by_actor_id} | {uuid.UUID(a["actor_id"]) for a in tr.approvals or []}
    text = (f"RECOrion: '{tr.connection_name}' aktarımı tamamlandı: {tr.external_ref}." if tr.status == "DONE"
            else f"RECOrion: '{tr.connection_name}' aktarımı yapılamadı: {tr.error}")
    for aid in [t for t in targets if t]:
        try:
            await notify.send(db, aid, text)
        except Exception as exc:
            logger.warning("Aktarım sonucu bildirilemedi: %s", exc)


async def enqueue(transfer_id: str) -> str:
    """Temporal kuyruğuna verir; iş akışı motoru yoksa backend içinde (3 deneme) çalıştırır."""
    from app.config import settings

    if settings.WORKFLOW_ENABLED:
        try:
            from app.workflows import engine

            await engine.start_transfer(transfer_id)
            return "TEMPORAL"
        except Exception as exc:
            logger.warning("Aktarım iş akışı başlatılamadı, yerel çalıştırılıyor: %s", exc)
    spawn(_run_local(transfer_id))
    return "LOCAL"


async def _run_local(transfer_id: str) -> None:
    for attempt in range(3):
        try:
            await execute(transfer_id)
            return
        except TransferFailed:
            return
        except Exception as exc:
            logger.warning("Aktarım denemesi %s başarısız: %s", attempt + 1, exc)
            await asyncio.sleep(2 * (attempt + 1))
    await mark_failed(transfer_id, "Dış sisteme 3 denemede ulaşılamadı.")


# --- geri alma ---

async def rollback(db: AsyncSession, tr: IntegrationTransfer, user) -> IntegrationTransfer:
    from fastapi import HTTPException

    from app.integrations import odoo

    if tr.status != "DONE":
        raise HTTPException(status_code=409, detail="Yalnızca tamamlanmış aktarım geri alınabilir.")
    conn = await db.get(IntegrationConnection, tr.connection_id) if tr.connection_id else None
    m = await db.get(IntegrationMapping, tr.mapping_id) if tr.mapping_id else None
    if not conn or conn.connector != "odoo" or not m or not tr.external_id:
        raise HTTPException(status_code=409, detail="Bu sistemde geri alma desteklenmiyor; kaydı sistemin kendisinden düzeltin.")
    tgt = ms.adapter(conn)
    model, rid = m.target["model"], int(tr.external_id)
    try:
        if tr.action == "UPDATE":
            if not tr.before:
                raise HTTPException(status_code=409, detail="Eski değerler kaydedilmemiş; geri alınamaz.")
            await odoo._kw(tgt.ctx, model, "write", [[rid], tr.before])
        else:
            fields = await odoo._kw(tgt.ctx, model, "fields_get", [], {"attributes": ["type"]})
            if "active" in fields:
                await odoo._kw(tgt.ctx, model, "write", [[rid], {"active": False}])
            elif model in CANCEL_METHODS:
                await odoo._kw(tgt.ctx, model, CANCEL_METHODS[model], [[rid]])
            else:
                raise HTTPException(status_code=409, detail="Bu kayıt türü arşivlenemiyor veya iptal edilemiyor; Odoo'da elle düzeltin.")
    except ToolError as exc:
        raise HTTPException(status_code=502, detail=str(exc))
    tr.status, tr.rolled_back_at, tr.rolled_back_by_actor_id = "ROLLED_BACK", now(), user.actor_id
    return tr


def out(tr: IntegrationTransfer, viewer=None) -> Dict[str, Any]:
    obj = bo.mask_pii(tr.object_type, tr.object or {})
    return {"id": str(tr.id), "project_id": str(tr.project_id) if tr.project_id else None, "task_id": str(tr.task_id) if tr.task_id else None,
            "mapping_id": str(tr.mapping_id) if tr.mapping_id else None, "mapping_version": tr.mapping_version,
            "connection_id": str(tr.connection_id) if tr.connection_id else None, "connection_name": tr.connection_name,
            "object_type": tr.object_type, "object_label": bo.OBJECTS.get(tr.object_type, {}).get("label"), "trigger": tr.trigger,
            "object": obj, "preview": tr.preview or [], "problems": tr.problems or {"errors": [], "warnings": []}, "action": tr.action,
            "amount": float(tr.amount) if tr.amount is not None else None, "status": tr.status, "required_approvals": tr.required_approvals,
            "approvals": tr.approvals or [], "decision_note": tr.decision_note, "external_id": tr.external_id, "external_ref": tr.external_ref,
            "external_url": tr.external_url, "error": tr.error, "attempts": tr.attempts, "created_by_name": tr.created_by_name,
            "created_at": tr.created_at, "done_at": tr.done_at, "rolled_back_at": tr.rolled_back_at}
