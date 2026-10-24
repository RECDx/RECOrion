"""
RECOrion'un kendi MCP sunucusu (ADIM 12.6): Claude, Cursor veya şirketin kendi sistemi RECOrion'da proje/Case açabilir,
plan taslağına adım ekleyebilir, durum sorabilir, onay bekleyenleri listeleyebilir.

- Taşıma: MCP Streamable HTTP (2025-06-18), POST /api/v1/mcp; yanıtlar JSON (SSE akışı sunulmaz; GET 405).
- Kimlik: kişisel erişim anahtarı (Authorization: Bearer rxp_...). Anahtar kullanıcının KENDİ yetkileriyle çalışır; kapsam READ
  (okuma araçları) ve WRITE (proje açma, plan taslağına adım). Onay/ret araçları bilerek YOKTUR: kararlar RECOrion ekranında,
  e-postada veya Telegram'da insan tarafından verilir. Dışarıdan açılan projenin planı RECAi tarafından taslak hazırlanır ve
  proje yöneticisinin onayını bekler.
- KVKK: RECDx platform personeli anahtar oluşturamaz/kullanamaz (müşteri içeriği). Her araç çağrısı denetim kaydına yazılır.
- Anahtar yönetimi: GET/POST /me/personal-tokens, DELETE /me/personal-tokens/{id} (anahtar bir kez gösterilir; özeti saklanır).
"""
import asyncio
import hashlib
import json
import logging
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel, Field
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.audit import write_audit_event
from app.core.security import CurrentUser, forbidden, get_current_user, load_current_user
from app.core.tokens import hit_rate_limit
from app.db.models import Actor, IntegrationTransfer, PersonalToken, Project, ProjectMember, Task, Tenant
from app.db.session import AsyncSessionLocal, get_db

router = APIRouter(tags=["RECOrion MCP sunucusu"])
logger = logging.getLogger("recorion.mcp_server")
PROTOCOL_VERSION = "2025-06-18"
SUPPORTED_VERSIONS = ("2025-06-18", "2025-03-26")
SERVER_INFO = {"name": "RECOrion", "version": "1.0"}
PREFIX = "rxp_"
RATE = (120, 60)  # anahtar başına dakikada 120 istek
OUTPUT_LIMIT = 20000
MAX_TOKENS_PER_USER = 10
_tasks: set = set()


def now() -> datetime:
    return datetime.now(timezone.utc)


def _hash(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()


def server_url() -> str:
    return settings.PUBLIC_APP_URL.rstrip("/") + "/api/v1/mcp"


# --- anahtar yönetimi ---

def token_out(t: PersonalToken) -> Dict[str, Any]:
    return {"id": str(t.id), "name": t.name, "prefix": t.prefix, "scopes": t.scopes or [], "expires_at": t.expires_at,
            "last_used_at": t.last_used_at, "use_count": t.use_count, "revoked_at": t.revoked_at, "created_at": t.created_at,
            "active": t.revoked_at is None and (t.expires_at is None or t.expires_at > now())}


class TokenIn(BaseModel):
    name: str = Field(..., min_length=2, max_length=80)
    scopes: List[str] = Field(default_factory=lambda: ["READ"])
    days: Optional[int] = Field(90, ge=1, le=365)


@router.get("/me/personal-tokens")
async def list_tokens(user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    rows = (await db.execute(select(PersonalToken).where(PersonalToken.actor_id == user.actor_id).order_by(PersonalToken.created_at.desc()))).scalars()
    return {"server_url": server_url(), "tokens": [token_out(t) for t in rows]}


@router.post("/me/personal-tokens", status_code=201)
async def create_token(payload: TokenIn, user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if user.is_platform_staff:
        raise forbidden("KVKK gereği RECDx personeli müşteri içeriğine erişen anahtar oluşturamaz.")
    scopes = sorted(set(payload.scopes))
    if not scopes or any(s not in ("READ", "WRITE") for s in scopes):
        raise HTTPException(status_code=422, detail="Kapsam READ ve/veya WRITE olmalı.")
    active = (await db.execute(select(func.count()).select_from(PersonalToken).where(
        PersonalToken.actor_id == user.actor_id, PersonalToken.revoked_at.is_(None)))).scalar() or 0
    if active >= MAX_TOKENS_PER_USER:
        raise HTTPException(status_code=409, detail=f"En fazla {MAX_TOKENS_PER_USER} etkin anahtarınız olabilir; kullanmadıklarınızı iptal edin.")
    raw = PREFIX + secrets.token_urlsafe(32)
    t = PersonalToken(tenant_id=user.tenant_id, actor_id=user.actor_id, name=payload.name.strip(), token_hash=_hash(raw), prefix=raw[:10],
                      scopes=scopes, expires_at=now() + timedelta(days=payload.days or 90))
    db.add(t)
    await db.commit()
    await write_audit_event(action="PERSONAL_TOKEN_CREATED", actor_id=user.actor_id, tenant_id=user.tenant_id, target_type="personal_token",
                            target_id=str(t.id), payload={"name": t.name, "scopes": scopes})
    return {**token_out(t), "token": raw, "server_url": server_url()}


@router.delete("/me/personal-tokens/{token_id}")
async def revoke_token(token_id: uuid.UUID, user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    t = await db.get(PersonalToken, token_id)
    if not t or t.actor_id != user.actor_id:
        raise HTTPException(status_code=404, detail="Anahtar bulunamadı.")
    if not t.revoked_at:
        t.revoked_at = now()
        await db.commit()
        await write_audit_event(action="PERSONAL_TOKEN_REVOKED", actor_id=user.actor_id, tenant_id=user.tenant_id, target_type="personal_token",
                                target_id=str(t.id))
    return token_out(t)


# --- MCP araçları ---

def _schema(props: Dict[str, Any], required: List[str]) -> Dict[str, Any]:
    return {"type": "object", "properties": props, "required": required}


TOOLS = [
    {"name": "list_projects", "scope": "READ", "title": "Projeleri listele",
     "description": "Erişebildiğiniz RECOrion projelerini ve Case'leri listeler (durum, adım ilerlemesi, yönetici).",
     "inputSchema": _schema({"status": {"type": "string", "description": "İsteğe bağlı durum süzgeci: DRAFT, PLANNING, READY, ACTIVE, PAUSED, COMPLETED, CANCELLED"}}, [])},
    {"name": "get_project", "scope": "READ", "title": "Proje durumu",
     "description": "Projenin durumu, iş adımları (kim, durum, tarih), onay bekleyenler ve dış sisteme aktarılan kayıtlar.",
     "inputSchema": _schema({"project_id": {"type": "string", "description": "Proje kimliği (list_projects'ten)"}}, ["project_id"])},
    {"name": "get_step_output", "scope": "READ", "title": "Adım çıktısı",
     "description": "Bir iş adımının son çıktısını (RECAi personelinin ürettiği metin) döner.",
     "inputSchema": _schema({"task_id": {"type": "string", "description": "İş adımı kimliği (get_project'ten)"}}, ["task_id"])},
    {"name": "list_my_approvals", "scope": "READ", "title": "Onayımı bekleyenler",
     "description": "Kararınızı bekleyen iş adımları ve dış sisteme aktarımlar. Karar RECOrion ekranında verilir (bu sunucuda onay aracı yoktur).",
     "inputSchema": _schema({}, [])},
    {"name": "create_project", "scope": "WRITE", "title": "Proje veya Case aç",
     "description": "RECOrion'da yeni proje veya Case açar (yöneticisi siz olursunuz). İster yazılırsa RECAi plan taslağı hazırlar; "
                    "plan sizin onayınızı bekler, onaylanmadan iş başlamaz.",
     "inputSchema": _schema({"name": {"type": "string", "description": "Proje adı"},
                             "kind": {"type": "string", "enum": ["PROJECT", "CASE"], "description": "PROJECT (çok adımlı) veya CASE (tek vaka)"},
                             "description": {"type": "string", "description": "Kısa amaç"},
                             "requirements": {"type": "string", "description": "İsterler (kapsam, kısıtlar, onay noktaları, teslim tarihi)"},
                             "plan_with_recai": {"type": "boolean", "description": "RECAi plan taslağı hazırlasın mı (varsayılan evet)"}}, ["name"])},
    {"name": "add_step", "scope": "WRITE", "title": "Plan taslağına adım ekle",
     "description": "Henüz başlamamış (taslak/planlama) projenin plan taslağına iş adımı ekler; plan yeniden onay bekler.",
     "inputSchema": _schema({"project_id": {"type": "string"}, "title": {"type": "string", "description": "Adım adı"},
                             "description": {"type": "string"}, "job_title": {"type": "string", "description": "Bu işi yapacak rol/unvan"},
                             "estimated_days": {"type": "number", "description": "Tahmini iş günü"},
                             "depends_on": {"type": "array", "items": {"type": "string"}, "description": "Önce bitmesi gereken adım anahtarları (ör. S1)"}},
                            ["project_id", "title"])},
]
TOOL_BY_NAME = {t["name"]: t for t in TOOLS}


class ToolFail(Exception):
    pass


def _uuid(v: Any, what: str) -> uuid.UUID:
    try:
        return uuid.UUID(str(v))
    except ValueError:
        raise ToolFail(f"{what} geçersiz.")


async def _load_project(db: AsyncSession, user: CurrentUser, pid: Any, manage: bool = False) -> Project:
    from app.services import projects as psvc

    try:
        return await psvc.load(db, user, _uuid(pid, "Proje kimliği"), manage=manage)
    except HTTPException as exc:
        raise ToolFail(str(exc.detail))


def _project_url(p: Project) -> str:
    return f"{settings.PUBLIC_APP_URL.rstrip('/')}/#/workspace?project={p.id}"


async def _list_projects(db, user, args):
    stmt = select(Project).where(Project.tenant_id == user.tenant_id)
    if not user.has("project:manage"):
        member_of = select(ProjectMember.project_id).where(ProjectMember.actor_id == user.actor_id)
        stmt = stmt.where(or_(Project.id.in_(member_of), Project.manager_actor_id == user.actor_id))
    if args.get("status"):
        stmt = stmt.where(Project.status == str(args["status"]).upper())
    rows = (await db.execute(stmt.order_by(Project.created_at.desc()).limit(100))).scalars().all()
    counts = {}
    for pid, status, n in (await db.execute(select(Task.project_id, Task.status, func.count()).where(Task.project_id.in_([p.id for p in rows] or [uuid.uuid4()]))
                                            .group_by(Task.project_id, Task.status))).all():
        c = counts.setdefault(pid, {"total": 0, "done": 0})
        c["total"] += n
        c["done"] += n if status == "DONE" else 0
    managers = {a.id: a.display_name for a in (await db.execute(select(Actor).where(Actor.id.in_([p.manager_actor_id for p in rows if p.manager_actor_id] or [uuid.uuid4()])))).scalars()}
    return {"projects": [{"id": str(p.id), "name": p.name, "kind": p.kind, "status": p.status, "manager": managers.get(p.manager_actor_id),
                          "steps_done": counts.get(p.id, {}).get("done", 0), "steps_total": counts.get(p.id, {}).get("total", 0),
                          "start_date": p.start_date, "end_date": p.end_date, "url": _project_url(p)} for p in rows]}


async def _get_project(db, user, args):
    from app.services import task_flow

    p = await _load_project(db, user, args.get("project_id"))
    tasks = (await db.execute(select(Task).where(Task.project_id == p.id).order_by(Task.order_index, Task.created_at))).scalars().all()
    names = {a.id: a.display_name for a in (await db.execute(select(Actor).where(Actor.id.in_([t.assignee_actor_id for t in tasks if t.assignee_actor_id] or [uuid.uuid4()])))).scalars()}
    transfers = (await db.execute(select(IntegrationTransfer).where(IntegrationTransfer.project_id == p.id, IntegrationTransfer.status == "DONE"))).scalars()
    plan_steps = [{"key": s.get("key"), "title": s.get("title"), "job_title": s.get("job_title"), "estimated_days": s.get("estimated_days")}
                  for s in ((p.plan or {}).get("steps") or [])] if not tasks else []
    return {"id": str(p.id), "name": p.name, "kind": p.kind, "status": p.status, "description": p.description, "url": _project_url(p),
            "plan_approved": bool(p.planning_approved_at), "plan_draft_steps": plan_steps,
            "steps": [{"id": str(t.id), "title": t.title, "status": t.status, "status_label": task_flow.STATUS_LABELS.get(t.status, t.status),
                       "assignee": names.get(t.assignee_actor_id), "due_date": t.due_date, "completed_at": t.completed_at} for t in tasks],
            "waiting_approval": sum(1 for t in tasks if t.status == "WAITING_APPROVAL"),
            "external_records": [{"system": x.connection_name, "record": x.external_ref, "url": x.external_url} for x in transfers]}


async def _get_step_output(db, user, args):
    from app.services import agent_work

    task = await db.get(Task, _uuid(args.get("task_id"), "Adım kimliği"))
    if not task:
        raise ToolFail("İş adımı bulunamadı.")
    await _load_project(db, user, task.project_id)
    art = await agent_work.latest_artifact(db, task.id)
    text = await agent_work.artifact_text(art, OUTPUT_LIMIT + 1)
    return {"task_id": str(task.id), "title": task.title, "status": task.status, "version": art.version if art else None,
            "output": text[:OUTPUT_LIMIT] if text else None, "truncated": len(text or "") > OUTPUT_LIMIT}


async def _list_my_approvals(db, user, args):
    from app.services import approvals, transfers

    tasks = await approvals.pending_for(db, user.actor_id, user.tenant_id)
    rows = (await db.execute(select(IntegrationTransfer).where(IntegrationTransfer.tenant_id == user.tenant_id,
                                                               IntegrationTransfer.status == "PENDING_APPROVAL"))).scalars().all()
    mine = [t for t in rows if await transfers.can_decide(db, user, t)]
    return {"steps": [{"project": i.get("project_name"), "title": i.get("title"), "kind": i.get("kind")} for i in tasks],
            "transfers": [{"system": t.connection_name, "object": t.object_type, "action": t.action, "amount": float(t.amount) if t.amount else None}
                          for t in mine],
            "note": "Kararlar RECOrion'daki Onaylarım ekranından verilir: " + settings.PUBLIC_APP_URL.rstrip("/") + "/#/workspace"}


async def _plan_background(project_id: uuid.UUID) -> None:
    from app.services import project_planning

    async with AsyncSessionLocal() as db:
        try:
            p = await db.get(Project, project_id)
            await project_planning.suggest_plan(db, p)
        except Exception as exc:  # plan hazırlanamazsa proje taslakta kalır; yönetici ekrandan yeniden ister
            logger.warning("MCP ile açılan projeye plan hazırlanamadı (%s): %s", project_id, exc)


async def _create_project(db, user, args):
    from app.services import projects as psvc

    if not user.has("project:create"):
        raise ToolFail("Proje açma yetkiniz yok.")
    name = str(args.get("name") or "").strip()
    if len(name) < 2:
        raise ToolFail("Proje adı en az 2 karakter olmalı.")
    tenant = await db.get(Tenant, user.tenant_id)
    try:
        await psvc.ensure_project_quota(db, tenant)
    except HTTPException as exc:
        raise ToolFail(str(exc.detail))
    kind = "CASE" if str(args.get("kind") or "").upper() == "CASE" else "PROJECT"
    requirements = str(args.get("requirements") or "").strip()[:20000] or None
    p = Project(tenant_id=tenant.id, slug=await psvc.unique_slug(db, tenant.id, name), name=name[:255], kind=kind,
                description=(str(args.get("description") or "").strip()[:4000] or None), requirements=requirements, status="DRAFT",
                manager_actor_id=user.actor_id, created_by_actor_id=user.actor_id)
    db.add(p)
    await db.flush()
    await psvc.set_member(db, p, user.actor, "MANAGER", user.actor_id)
    await db.commit()
    planning = bool(requirements) and args.get("plan_with_recai", True) is not False
    if planning:
        t = asyncio.create_task(_plan_background(p.id))
        _tasks.add(t)
        t.add_done_callback(_tasks.discard)
    return {"id": str(p.id), "name": p.name, "kind": p.kind, "status": p.status, "url": _project_url(p),
            "message": ("RECAi plan taslağını hazırlıyor; hazır olunca RECOrion'da Planlama sekmesinden inceleyip onaylayın. "
                        "Plan onaylanmadan iş başlamaz.") if planning else "Proje taslak olarak açıldı; isterleri RECOrion'da yazıp planlamaya geçin."}


async def _add_step(db, user, args):
    p = await _load_project(db, user, args.get("project_id"), manage=True)
    if p.status not in ("DRAFT", "PLANNING"):
        raise ToolFail("Adım yalnızca başlamamış (taslak/planlama) projenin plan taslağına eklenebilir.")
    title = str(args.get("title") or "").strip()
    if len(title) < 2:
        raise ToolFail("Adım adı en az 2 karakter olmalı.")
    plan = dict(p.plan or {"summary": "", "steps": [], "risks": [], "questions": []})
    steps = list(plan.get("steps") or [])
    keys = {s.get("key") for s in steps}
    deps = [str(d) for d in (args.get("depends_on") or []) if str(d) in keys]
    n = len(steps) + 1
    while f"S{n}" in keys:
        n += 1
    try:
        days = max(0.5, min(float(args.get("estimated_days") or 1), 365))
    except (TypeError, ValueError):
        days = 1
    step = {"key": f"S{n}", "title": title[:255], "description": str(args.get("description") or "")[:4000],
            "job_title": str(args.get("job_title") or "")[:120], "estimated_days": days, "depends_on": deps, "requires_approval": True}
    plan["steps"] = steps + [step]
    plan["approved"] = False
    p.plan, p.planning_approved_at = plan, None
    if p.status == "DRAFT":
        p.status = "PLANNING"
    await db.commit()
    return {"project_id": str(p.id), "step": step, "plan_steps": len(plan["steps"]), "url": _project_url(p),
            "message": "Adım plan taslağına eklendi; plan yeniden onay bekliyor (personel ataması RECOrion'da yapılır)."}


HANDLERS = {"list_projects": _list_projects, "get_project": _get_project, "get_step_output": _get_step_output,
            "list_my_approvals": _list_my_approvals, "create_project": _create_project, "add_step": _add_step}


# --- MCP uç noktası ---

def _rpc_error(req_id, code: int, message: str, status: int = 200) -> JSONResponse:
    return JSONResponse({"jsonrpc": "2.0", "id": req_id, "error": {"code": code, "message": message}}, status_code=status)


def _unauth(message: str) -> JSONResponse:
    return JSONResponse({"jsonrpc": "2.0", "id": None, "error": {"code": -32001, "message": message}}, status_code=401,
                        headers={"WWW-Authenticate": 'Bearer realm="RECOrion"'})


async def _authenticate(request: Request, db: AsyncSession):
    header = request.headers.get("authorization", "")
    raw = header[7:].strip() if header.lower().startswith("bearer ") else ""
    if not raw.startswith(PREFIX):
        return None, None, "Kişisel erişim anahtarı gerekli (Authorization: Bearer rxp_...). RECOrion > Bağlantılarım ekranından oluşturun."
    t = (await db.execute(select(PersonalToken).where(PersonalToken.token_hash == _hash(raw)))).scalar_one_or_none()
    if not t or t.revoked_at or (t.expires_at and t.expires_at <= now()):
        return None, None, "Anahtar geçersiz, iptal edilmiş veya süresi dolmuş."
    actor = await db.get(Actor, t.actor_id)
    if not actor or actor.status == "DISABLED" or actor.actor_type != "HUMAN":
        return None, None, "Anahtarın sahibi olan kullanıcı pasif."
    user = await load_current_user(db, actor)
    tenant = await db.get(Tenant, actor.tenant_id)
    if user.is_platform_staff or not tenant or not tenant.is_active:
        return None, None, "Bu anahtarla erişim yok."
    return t, user, None


@router.get("/mcp")
async def mcp_get():
    return Response(status_code=405, headers={"Allow": "POST"})


@router.post("/mcp")
async def mcp(request: Request, db: AsyncSession = Depends(get_db)):
    try:
        msg = json.loads(await request.body() or b"{}")
    except ValueError:
        return _rpc_error(None, -32700, "Geçersiz JSON.", 400)
    if isinstance(msg, list):
        return _rpc_error(None, -32600, "Toplu (batch) istek desteklenmiyor.", 400)
    token, user, why = await _authenticate(request, db)
    if not user:
        return _unauth(why)
    if await hit_rate_limit(f"mcp:{token.id}", *RATE):
        return _rpc_error(msg.get("id"), -32002, "Çok fazla istek; bir dakika sonra tekrar deneyin.", 429)
    method, req_id, params = msg.get("method"), msg.get("id"), msg.get("params") or {}
    token.last_used_at, token.use_count = now(), int(token.use_count or 0) + 1
    await db.commit()
    if req_id is None:  # bildirim (ör. notifications/initialized): yanıt gövdesi yok
        return Response(status_code=202)
    scopes = set(token.scopes or [])
    if method == "initialize":
        version = params.get("protocolVersion") if params.get("protocolVersion") in SUPPORTED_VERSIONS else PROTOCOL_VERSION
        return JSONResponse({"jsonrpc": "2.0", "id": req_id, "result": {
            "protocolVersion": version, "capabilities": {"tools": {"listChanged": False}}, "serverInfo": SERVER_INFO,
            "instructions": "RECOrion: AI personelle proje/Case yürütme. Okuma araçlarıyla durumu sorun; proje açabilir ve plan taslağına "
                            "adım ekleyebilirsiniz. Onaylar insan tarafından RECOrion'da verilir."}})
    if method == "ping":
        return JSONResponse({"jsonrpc": "2.0", "id": req_id, "result": {}})
    if method == "tools/list":
        tools = [{"name": t["name"], "title": t["title"], "description": t["description"], "inputSchema": t["inputSchema"],
                  "annotations": {"readOnlyHint": t["scope"] == "READ", "destructiveHint": False, "openWorldHint": False}}
                 for t in TOOLS if t["scope"] in scopes]
        return JSONResponse({"jsonrpc": "2.0", "id": req_id, "result": {"tools": tools}})
    if method == "tools/call":
        name, args = params.get("name"), params.get("arguments") or {}
        spec = TOOL_BY_NAME.get(name)
        if not spec:
            return _rpc_error(req_id, -32602, f"Bilinmeyen araç: {name}")
        if spec["scope"] not in scopes:
            return _rpc_error(req_id, -32003, f"Bu anahtarın '{spec['scope']}' kapsamı yok.")
        if not isinstance(args, dict):
            return _rpc_error(req_id, -32602, "arguments nesne olmalı.")
        try:
            data, is_error = await HANDLERS[name](db, user, args), False
        except ToolFail as exc:
            data, is_error = {"error": str(exc)}, True
        except Exception:
            logger.exception("MCP aracı çalışmadı: %s", name)
            data, is_error = {"error": "Araç çalıştırılamadı."}, True
        await write_audit_event(action="MCP_TOOL_CALL", actor_id=user.actor_id, tenant_id=user.tenant_id, target_type="mcp_tool", target_id=name,
                                payload={"token": token.name, "ok": not is_error, "args": {k: (str(v)[:120]) for k, v in args.items()}})
        text = json.dumps(data, ensure_ascii=False, default=str, indent=1)
        return JSONResponse({"jsonrpc": "2.0", "id": req_id, "result": {
            "content": [{"type": "text", "text": text[:OUTPUT_LIMIT + 2000]}], "structuredContent": json.loads(json.dumps(data, default=str)),
            "isError": is_error}})
    return _rpc_error(req_id, -32601, f"Desteklenmeyen yöntem: {method}")
