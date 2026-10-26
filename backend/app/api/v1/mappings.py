"""
Eşleme stüdyosu uçları (ADIM 12.3). Eşlemeler şirketin içeriğidir: yalnızca integration:manage (KVKK: RECDx göremez).

- GET  /company/{tid}/mappings                         şirketin eşlemeleri (bağlantıya göre süzülebilir)
- GET  /company/{tid}/mappings/templates               RECDx hazır eşlemeleri (bağlantı türüne göre)
- POST /company/{tid}/mappings                         yeni eşleme (boş veya hazır eşlemeden kopya) — taslak
- PUT  /company/{tid}/mappings/{id}                    düzenle (onaylıysa taslağa döner, sürüm artar)
- POST /company/{tid}/mappings/{id}/check              hedefin alan tanımlarıyla doğrula
- POST /company/{tid}/mappings/{id}/dry-run            örnek nesneyle dene (YAZMAZ; yalnızca okuma/arama)
- POST /company/{tid}/mappings/{id}/approve            onayla (son deneme bu sürümde ve hatasız olmalı)
- POST /company/{tid}/mappings/{id}/archive            arşivle
- POST /company/{tid}/mappings/suggest                 RECAi eşleme önerisi (kaydetmez; şirketin kredisinden)
- GET  /company/{tid}/integrations/{cid}/target-fields hedefin yazılabilir alanları (stüdyo seçim kutuları)
"""
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import vault
from app.core.security import CurrentUser, ensure_tenant_content, forbidden, get_current_user
from app.db.models import IntegrationConnection, IntegrationMapping, Tenant
from app.db.session import get_db
from app.integrations.base import ToolError
from app.services import business_objects as bo
from app.services import mappings as ms
from app.services.llm_gateway import LLMError

router = APIRouter(tags=["Eşleme Stüdyosu"])
TARGET_KEYS = ("model", "tool", "find_tool", "update_tool")  # araç hedefinde: ara (eşleştirme) ve güncelle araçları


def _manage(user: CurrentUser, tenant_id: uuid.UUID) -> None:
    ensure_tenant_content(user, tenant_id)
    if not user.has("integration:manage"):
        raise forbidden("Eşlemeleri yalnızca entegrasyon yönetimi yetkisi olanlar yönetebilir.")


async def _connection(db: AsyncSession, tenant_id: uuid.UUID, cid: uuid.UUID) -> IntegrationConnection:
    conn = await db.get(IntegrationConnection, cid)
    if not conn or conn.tenant_id != tenant_id:
        raise HTTPException(status_code=404, detail="Bağlantı bulunamadı.")
    if conn.connector not in ms.SUPPORTED:
        raise HTTPException(status_code=422, detail="Bu sistem türü için eşleme desteklenmiyor (Odoo, MCP sunucusu veya Edge Connector).")
    return conn


async def _mapping(db: AsyncSession, user: CurrentUser, tenant_id: uuid.UUID, mid: uuid.UUID) -> IntegrationMapping:
    _manage(user, tenant_id)
    m = await db.get(IntegrationMapping, mid)
    if not m or m.tenant_id != tenant_id:
        raise HTTPException(status_code=404, detail="Eşleme bulunamadı.")
    return m


def out(m: IntegrationMapping) -> Dict[str, Any]:
    return {"id": str(m.id), "code": m.code, "connection_id": str(m.connection_id) if m.connection_id else None, "connector": m.connector,
            "object_type": m.object_type, "object_label": bo.OBJECTS.get(m.object_type, {}).get("label"), "name": m.name,
            "description": m.description, "target": m.target, "rules": m.rules or [], "match": m.match, "when": m.when, "status": m.status,
            "version": m.version, "source_template_id": str(m.source_template_id) if m.source_template_id else None,
            "last_check": m.last_check, "last_dry_run": m.last_dry_run, "approved_at": m.approved_at, "updated_at": m.updated_at}


def _target(object_type: str, target: Dict[str, Any]) -> Dict[str, Any]:
    return {**{k: v for k, v in target.items() if k in TARGET_KEYS}, **ms.clean_target_options(object_type, target)}


def _errors(exc: Exception) -> HTTPException:
    if isinstance(exc, LLMError):
        return HTTPException(status_code=exc.status_code, detail=exc.message)
    if isinstance(exc, (ToolError, vault.VaultError)):
        return HTTPException(status_code=502, detail=str(exc))
    return HTTPException(status_code=422, detail=str(exc))


@router.get("/company/{tenant_id}/mappings")
async def list_mappings(tenant_id: uuid.UUID, connection_id: Optional[uuid.UUID] = None, user: CurrentUser = Depends(get_current_user),
                        db: AsyncSession = Depends(get_db)):
    _manage(user, tenant_id)
    stmt = select(IntegrationMapping).where(IntegrationMapping.tenant_id == tenant_id, IntegrationMapping.status != "ARCHIVED")
    if connection_id:
        stmt = stmt.where(IntegrationMapping.connection_id == connection_id)
    return [out(m) for m in (await db.execute(stmt.order_by(IntegrationMapping.object_type, IntegrationMapping.name))).scalars()]


@router.get("/company/{tenant_id}/mappings/templates")
async def templates(tenant_id: uuid.UUID, connector: Optional[str] = None, user: CurrentUser = Depends(get_current_user),
                    db: AsyncSession = Depends(get_db)):
    _manage(user, tenant_id)
    stmt = select(IntegrationMapping).where(IntegrationMapping.tenant_id.is_(None), IntegrationMapping.status == "ACTIVE")
    if connector:
        stmt = stmt.where(IntegrationMapping.connector == connector)
    tenant = await db.get(Tenant, tenant_id)
    return [out(m) for m in (await db.execute(stmt.order_by(IntegrationMapping.object_type))).scalars() if ms.template_visible(m.code, tenant)]


@router.get("/company/{tenant_id}/integrations/{cid}/target-fields")
async def target_fields(tenant_id: uuid.UUID, cid: uuid.UUID, model: Optional[str] = None, tool: Optional[str] = None,
                        user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    _manage(user, tenant_id)
    conn = await _connection(db, tenant_id, cid)
    try:
        fields = await ms.adapter(conn).fields({"model": model} if conn.connector == "odoo" else {"tool": tool})
    except (ToolError, ms.MappingError, vault.VaultError) as exc:
        raise _errors(exc)
    return [{"name": n, **f} for n, f in sorted(fields.items(), key=lambda kv: (not kv[1].get("required"), kv[0]))]


class MappingIn(BaseModel):
    connection_id: uuid.UUID
    object_type: str
    name: str = Field(..., min_length=2, max_length=160)
    description: Optional[str] = Field(None, max_length=2000)
    target: Dict[str, Any] = Field(default_factory=dict)
    rules: List[Dict[str, Any]] = Field(default_factory=list, max_length=ms.MAX_RULES)
    match: Optional[Dict[str, Any]] = None
    when: Optional[Dict[str, Any]] = None
    template_id: Optional[uuid.UUID] = None


class MappingUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=160)
    description: Optional[str] = Field(None, max_length=2000)
    target: Optional[Dict[str, Any]] = None
    rules: Optional[List[Dict[str, Any]]] = Field(None, max_length=ms.MAX_RULES)
    match: Optional[Dict[str, Any]] = None
    when: Optional[Dict[str, Any]] = None


def _clean_when(when: Optional[Dict[str, Any]], object_type: str) -> Optional[Dict[str, Any]]:
    if not when:
        return None
    if when.get("field") not in {f["key"] for f in bo.OBJECTS[object_type]["fields"]}:
        raise HTTPException(status_code=422, detail="Koşul alanı nesnede yok.")
    return {"field": when["field"], "equals": str(when.get("equals") or "")}


@router.post("/company/{tenant_id}/mappings", status_code=201)
async def create_mapping(tenant_id: uuid.UUID, payload: MappingIn, user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    _manage(user, tenant_id)
    conn = await _connection(db, tenant_id, payload.connection_id)
    tpl = None
    if payload.template_id:
        tpl = await db.get(IntegrationMapping, payload.template_id)
        if not tpl or tpl.tenant_id is not None or tpl.status != "ACTIVE":
            raise HTTPException(status_code=404, detail="Hazır eşleme bulunamadı.")
        if tpl.connector != conn.connector:
            raise HTTPException(status_code=422, detail="Hazır eşleme bu sistem türü için değil.")
        if not ms.template_visible(tpl.code, await db.get(Tenant, tenant_id)):
            raise HTTPException(status_code=404, detail="Hazır eşleme bulunamadı.")
    object_type = tpl.object_type if tpl else payload.object_type
    if object_type not in bo.OBJECTS:
        raise HTTPException(status_code=422, detail="Bilinmeyen nesne türü.")
    try:
        rules = ms.clean_rules(tpl.rules if tpl else payload.rules)
    except ms.MappingError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    target = tpl.target if tpl else payload.target
    if not (target.get("model") if conn.connector == "odoo" else target.get("tool")):
        raise HTTPException(status_code=422, detail="Hedef seçilmedi (Odoo modeli veya araç).")
    m = IntegrationMapping(tenant_id=tenant_id, connection_id=conn.id, connector=conn.connector, object_type=object_type,
                           name=payload.name.strip(), description=(tpl.description if tpl and not payload.description else payload.description),
                           target=_target(object_type, target), rules=rules,
                           match=(tpl.match if tpl else payload.match), when=(tpl.when if tpl else _clean_when(payload.when, object_type)),
                           source_template_id=tpl.id if tpl else None, status="DRAFT", created_by_actor_id=user.actor_id)
    db.add(m)
    await db.commit()
    return out(m)


@router.put("/company/{tenant_id}/mappings/{mid}")
async def update_mapping(tenant_id: uuid.UUID, mid: uuid.UUID, payload: MappingUpdate, user: CurrentUser = Depends(get_current_user),
                         db: AsyncSession = Depends(get_db)):
    m = await _mapping(db, user, tenant_id, mid)
    if m.status == "ARCHIVED":
        raise HTTPException(status_code=409, detail="Arşivlenmiş eşleme düzenlenemez.")
    changed = False
    if payload.rules is not None:
        try:
            m.rules = ms.clean_rules(payload.rules)
        except ms.MappingError as exc:
            raise HTTPException(status_code=422, detail=str(exc))
        changed = True
    if payload.target is not None:
        m.target, changed = _target(m.object_type, payload.target), True
    if "match" in payload.model_fields_set:
        m.match, changed = payload.match, True
    if "when" in payload.model_fields_set:
        m.when, changed = _clean_when(payload.when, m.object_type), True
    if payload.name:
        m.name = payload.name.strip()
    if payload.description is not None:
        m.description = payload.description
    if changed:  # kural değişti: yeniden deneme ve onay gerekir
        m.version += 1
        m.status, m.approved_at, m.approved_by_actor_id, m.last_check = "DRAFT", None, None, None
    await db.commit()
    return out(m)


@router.post("/company/{tenant_id}/mappings/{mid}/check")
async def check_mapping(tenant_id: uuid.UUID, mid: uuid.UUID, user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    m = await _mapping(db, user, tenant_id, mid)
    conn = await _connection(db, tenant_id, m.connection_id)
    try:
        fields = await ms.adapter(conn).fields(m.target)
    except (ToolError, ms.MappingError, vault.VaultError) as exc:
        raise _errors(exc)
    errors, warnings = ms.check(m.object_type, m.rules or [], fields, m.connector, m.match)
    for r in m.rules or []:  # kalem kuralları: satır modelinin alanlarıyla
        if r["transform"] == "lines" and fields.get(r["target"], {}).get("relation"):
            lf = await ms.adapter(conn).fields({"model": fields[r["target"]]["relation"]})
            e2, _ = ms.check(m.object_type, r["params"].get("rules") or [], lf, m.connector, nested=True)
            errors += [f"Kalem: {e}" for e in e2]
    m.last_check = {"ok": not errors, "errors": errors, "warnings": warnings, "version": m.version, "at": datetime.now(timezone.utc).isoformat()}
    await db.commit()
    return m.last_check


class DryRunIn(BaseModel):
    sample: Optional[Dict[str, Any]] = None


@router.post("/company/{tenant_id}/mappings/{mid}/dry-run")
async def dry_run(tenant_id: uuid.UUID, mid: uuid.UUID, payload: DryRunIn, user: CurrentUser = Depends(get_current_user),
                  db: AsyncSession = Depends(get_db)):
    m = await _mapping(db, user, tenant_id, mid)
    conn = await _connection(db, tenant_id, m.connection_id)
    try:
        result = await ms.dry_run(m, conn, payload.sample)
    except (ToolError, ms.MappingError, vault.VaultError) as exc:
        raise _errors(exc)
    m.last_dry_run = result
    await db.commit()
    return result


@router.post("/company/{tenant_id}/mappings/{mid}/approve")
async def approve(tenant_id: uuid.UUID, mid: uuid.UUID, user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    m = await _mapping(db, user, tenant_id, mid)
    last = m.last_dry_run or {}
    if not last or last.get("version") != m.version:
        raise HTTPException(status_code=409, detail="Önce bu sürümü örnek kayıtla deneyin (Dene).")
    if not last.get("ok"):
        raise HTTPException(status_code=409, detail="Son denemede hata var; düzeltip yeniden deneyin.")
    m.status, m.approved_at, m.approved_by_actor_id = "ACTIVE", datetime.now(timezone.utc), user.actor_id
    await db.commit()
    return out(m)


@router.post("/company/{tenant_id}/mappings/{mid}/archive")
async def archive(tenant_id: uuid.UUID, mid: uuid.UUID, user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    m = await _mapping(db, user, tenant_id, mid)
    m.status = "ARCHIVED"
    await db.commit()
    return out(m)


class SuggestIn(BaseModel):
    connection_id: uuid.UUID
    object_type: str
    target: Dict[str, Any]


@router.post("/company/{tenant_id}/mappings/suggest")
async def suggest(tenant_id: uuid.UUID, payload: SuggestIn, user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    _manage(user, tenant_id)
    conn = await _connection(db, tenant_id, payload.connection_id)
    if payload.object_type not in bo.OBJECTS:
        raise HTTPException(status_code=422, detail="Bilinmeyen nesne türü.")
    try:
        return await ms.suggest(tenant_id, conn, payload.object_type, payload.target)
    except (ToolError, ms.MappingError, vault.VaultError, LLMError) as exc:
        raise _errors(exc)
