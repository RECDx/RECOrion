"""
İSTEK #744 — Beyin AI ile rapor (tablo, grafik, pivot) ve Merkez toplu raporları.

Karar (Claude/senaryo/karar_ogrenme_recai.md §7):
- Beyin AI SQL YAZMAZ. Yalnız bu dosyadaki ONAYLI rapor kataloğundan seçer ve parametre verir (boyut, ölçü, filtre, tarih);
  sorgu her zaman kod içindeki sabit sorgulardır, şirket filtresi her raporda zorunludur.
- Sonuç konuşan kullanıcının ROLÜYLE süzülür: proje yetkisi yoksa yalnız ekibindeki projeler; kredi/maliyet billing:view;
  öğrenme memory:promote; aktarım entegrasyon izinleri.
- Merkez raporları yalnız toplu/işletim bilgisidir; k-anonimlik eşiği ve baskınlık kuralı Merkez ayarıdır (privacy_settings).
"""
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, Callable, Dict, List, Optional

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import CurrentUser
from app.db.models import (Actor, Department, IntegrationTransfer, LearningRecord, LLMCall, Project, ProjectMember, SystemSetting,
                           Task, TaskEvent, Tenant)

MAX_ROWS, MAX_GROUPS = 20000, 200
STATUS_TR = {"BACKLOG": "Sırada", "READY": "Başlayabilir", "IN_PROGRESS": "Çalışılıyor", "WAITING_APPROVAL": "Onay bekliyor",
             "REVISION": "Revizyonda", "QUARANTINED": "Karantinada", "DONE": "Tamamlandı", "CANCELLED": "İptal"}
LABEL_TR = {"DOGRU": "Doğru", "YANLIS": "Yanlış", "BELIRSIZ": "Belirsiz"}
CAUSE_TR = {"MODEL_HATASI": "AI hatası", "ORTAM": "Ortam", "DEGERLENDIRICI": "Değerlendirme", "KAPSAM": "Kapsam", "BELIRSIZ": "Belirsiz"}


class ReportError(Exception):
    def __init__(self, message: str, status: int = 422):
        super().__init__(message)
        self.status = status


def _month(d) -> Optional[str]:
    return d.strftime("%Y-%m") if d else None


def _days(a, b) -> Optional[float]:
    return round((b - a).total_seconds() / 86400, 1) if a and b else None


# ---------------------------------------------------------------- Merkez gizlilik ayarı
PRIVACY_KEY = "privacy.aggregate"
PRIVACY_DEFAULT = {"k_min": 5, "dominance_pct": 60}


async def privacy(db: AsyncSession) -> Dict[str, int]:
    row = await db.get(SystemSetting, PRIVACY_KEY)
    v = row.value if row is not None and isinstance(row.value, dict) else {}
    return {"k_min": int(v.get("k_min", PRIVACY_DEFAULT["k_min"])), "dominance_pct": int(v.get("dominance_pct", PRIVACY_DEFAULT["dominance_pct"]))}


async def set_privacy(db: AsyncSession, k_min: int, dominance_pct: int) -> Dict[str, int]:
    if not 3 <= k_min <= 50:
        raise ReportError("k en az 3, en çok 50 olabilir.")
    if not 30 <= dominance_pct <= 100:
        raise ReportError("Baskınlık sınırı %30 ile %100 arasında olmalı.")
    row = await db.get(SystemSetting, PRIVACY_KEY)
    val = {"k_min": k_min, "dominance_pct": dominance_pct}
    if row is None:
        db.add(SystemSetting(key=PRIVACY_KEY, value=val, description="Merkez toplu istatistik: k-anonimlik ve baskınlık (#744)"))
    else:
        row.value = val
    await db.commit()
    return val


def suppress(groups: Dict[tuple, Dict[str, Any]], tenant_counts: Dict[tuple, Dict[Any, int]], k_min: int, dominance_pct: int) -> int:
    """k'dan az şirkete dayanan ya da tek şirketin payı sınırı aşan grupları siler; silinen sayısını döner."""
    hidden = 0
    for key in list(groups):
        tc = tenant_counts.get(key, {})
        total = sum(tc.values())
        if len(tc) < k_min or (total and max(tc.values()) * 100 / total > dominance_pct):
            del groups[key]
            hidden += 1
    return hidden


# ---------------------------------------------------------------- şirket raporları (satır üreticiler)
async def _visible_projects(db: AsyncSession, user: CurrentUser, tenant_id) -> List[Project]:
    q = select(Project).where(Project.tenant_id == tenant_id)
    if not user.has("project:manage"):
        member_of = select(ProjectMember.project_id).where(ProjectMember.actor_id == user.actor_id)
        q = q.where(or_(Project.id.in_(member_of), Project.manager_actor_id == user.actor_id))
    return (await db.execute(q)).scalars().all()


async def _names(db: AsyncSession, tenant_id) -> Dict[Any, str]:
    return dict((await db.execute(select(Actor.id, Actor.display_name).where(Actor.tenant_id == tenant_id))).all())


def _in_range(d, frm: Optional[date], to: Optional[date]) -> bool:
    if d is None:
        return frm is None and to is None
    dd = d.date() if isinstance(d, datetime) else d
    return (frm is None or dd >= frm) and (to is None or dd <= to)


async def rows_projects(db, tenant_id, user, frm, to):
    projects = await _visible_projects(db, user, tenant_id)
    names = await _names(db, tenant_id)
    ids = [p.id for p in projects] or [None]
    tasks = (await db.execute(select(Task.project_id, Task.status).where(Task.project_id.in_(ids)))).all()
    by: Dict[Any, List[str]] = defaultdict(list)
    for pid, st in tasks:
        by[pid].append(st)
    out = []
    for p in projects:
        if not _in_range(p.created_at, frm, to):
            continue
        st = [s for s in by[p.id] if s != "CANCELLED"]
        out.append({"project": p.name, "status": p.status, "kind": "Case" if p.kind == "CASE" else "Proje",
                    "manager": names.get(p.manager_actor_id, "—"), "month": _month(p.created_at),
                    "count": 1, "steps": len(st), "steps_done": sum(1 for s in st if s == "DONE")})
    return out


async def rows_tasks(db, tenant_id, user, frm, to):
    projects = {p.id: p for p in await _visible_projects(db, user, tenant_id)}
    names = await _names(db, tenant_id)
    depts = dict((await db.execute(select(Department.id, Department.name).where(Department.tenant_id == tenant_id))).all())
    actors = {a.id: a for a in (await db.execute(select(Actor).where(Actor.tenant_id == tenant_id))).scalars()}
    rows = (await db.execute(select(Task).where(Task.project_id.in_(list(projects) or [None])).limit(MAX_ROWS))).scalars().all()
    out = []
    for t in rows:
        when = t.completed_at or t.created_at
        if not _in_range(when, frm, to):
            continue
        a = actors.get(t.assignee_actor_id)
        out.append({"project": projects[t.project_id].name, "status": STATUS_TR.get(t.status, t.status),
                    "assignee": names.get(t.assignee_actor_id, "—"),
                    "assignee_type": ("AI personel" if a.actor_type == "AI_AGENT" else "İnsan") if a else "—",
                    "job_title": (a.role if a and a.role else "—"), "department": depts.get(t.department_id, "—"),
                    "month": _month(when), "count": 1, "rejections": int(t.rejection_count or 0),
                    "duration_days": _days(t.started_at, t.completed_at)})
    return out


async def rows_ai_usage(db, tenant_id, user, frm, to):
    from app.services import human_equivalent as he
    tenant = await db.get(Tenant, tenant_id)
    unit = Decimal(str(await he.tenant_credit_unit(db, tenant) or 0))
    visible = {p.id: p.name for p in await _visible_projects(db, user, tenant_id)}
    names = await _names(db, tenant_id)
    q = select(LLMCall).where(LLMCall.tenant_id == tenant_id)
    if frm:
        q = q.where(LLMCall.created_at >= datetime.combine(frm, datetime.min.time(), tzinfo=timezone.utc))
    if to:
        q = q.where(LLMCall.created_at < datetime.combine(to + timedelta(days=1), datetime.min.time(), tzinfo=timezone.utc))
    out = []
    for c in (await db.execute(q.limit(MAX_ROWS))).scalars():
        if c.project_id and c.project_id not in visible and not user.has("project:manage"):
            continue
        cr = Decimal(str(c.credits_cost or 0))
        out.append({"project": visible.get(c.project_id, "Proje dışı") if c.project_id else "Proje dışı",
                    "agent": names.get(c.actor_id, "Sistem / Beyin AI"), "purpose": c.purpose or "—", "month": _month(c.created_at),
                    "calls": 1, "credits": float(cr), "cost_try": float((cr * unit).quantize(Decimal("0.01")))})
    return out


async def rows_learning(db, tenant_id, user, frm, to):
    names = await _names(db, tenant_id)
    out = []
    for r in (await db.execute(select(LearningRecord).where(LearningRecord.tenant_id == tenant_id).limit(MAX_ROWS))).scalars():
        if not _in_range(r.created_at, frm, to):
            continue
        out.append({"agent": names.get(r.agent_id, "—"), "job_title": r.job_title or "—", "label": LABEL_TR.get(r.label, r.label),
                    "cause": CAUSE_TR.get(r.cause, "—") if r.cause else "—", "source": r.source, "month": _month(r.created_at),
                    "count": 1, "ok": int(r.label == "DOGRU"), "wrong": int(r.label == "YANLIS"),
                    "ai_errors": int(r.cause == "MODEL_HATASI")})
    return out


async def rows_transfers(db, tenant_id, user, frm, to):
    out = []
    for t in (await db.execute(select(IntegrationTransfer).where(IntegrationTransfer.tenant_id == tenant_id).limit(MAX_ROWS))).scalars():
        if not _in_range(t.created_at, frm, to):
            continue
        out.append({"status": t.status, "object_type": t.object_type, "connection": t.connection_name or "—",
                    "month": _month(t.created_at), "count": 1, "amount": float(t.amount or 0)})
    return out


# ---------------------------------------------------------------- Merkez raporları (toplu)
async def rows_platform_titles(db, frm, to):
    out = []
    for r in (await db.execute(select(LearningRecord.tenant_id, LearningRecord.job_title, LearningRecord.label, LearningRecord.cause,
                                      LearningRecord.created_at).limit(MAX_ROWS * 5))).all():
        if not _in_range(r.created_at, frm, to):
            continue
        out.append({"_tenant": r.tenant_id, "job_title": r.job_title or "—", "label": LABEL_TR.get(r.label, r.label),
                    "month": _month(r.created_at), "count": 1, "ok": int(r.label == "DOGRU"), "wrong": int(r.label == "YANLIS"),
                    "ai_errors": int(r.cause == "MODEL_HATASI")})
    return out


async def rows_platform_usage(db, frm, to):
    q = select(LLMCall.tenant_id, LLMCall.purpose, LLMCall.latency_ms, LLMCall.status, LLMCall.created_at)
    if frm:
        q = q.where(LLMCall.created_at >= datetime.combine(frm, datetime.min.time(), tzinfo=timezone.utc))
    out = []
    for r in (await db.execute(q.limit(MAX_ROWS * 5))).all():
        if not _in_range(r.created_at, frm, to):
            continue
        out.append({"_tenant": r.tenant_id or "RECDx", "purpose": r.purpose or "—", "month": _month(r.created_at), "calls": 1,
                    "latency_s": (r.latency_ms or 0) / 1000, "errors": int((r.status or "SUCCESS") != "SUCCESS")})
    return out


async def rows_tenant_health(db, frm, to):
    since = datetime.now(timezone.utc) - timedelta(days=30)
    from sqlalchemy import func
    last = dict((await db.execute(select(TaskEvent.tenant_id, func.max(TaskEvent.created_at)).group_by(TaskEvent.tenant_id))).all())
    q30 = dict((await db.execute(select(LLMCall.tenant_id, func.sum(LLMCall.credits_cost)).where(LLMCall.created_at >= since)
                                 .group_by(LLMCall.tenant_id))).all())
    quar = dict((await db.execute(select(Project.tenant_id, func.count()).join(Task, Task.project_id == Project.id)
                                  .where(Task.status == "QUARANTINED").group_by(Project.tenant_id))).all())
    out = []
    for tid, name in (await db.execute(select(Tenant.id, Tenant.name).where(Tenant.is_active.is_(True)))).all():
        la = last.get(tid)
        out.append({"tenant": name, "count": 1, "credits_30d": float(q30.get(tid) or 0), "quarantined": int(quar.get(tid, 0)),
                    "idle_days": (datetime.now(timezone.utc) - la).days if la else 9999})
    return out


# ---------------------------------------------------------------- katalog
def _dims(**kw):
    return kw


CATALOG: Dict[str, Dict[str, Any]] = {
    "projects": {"title": "Projeler", "rows": rows_projects, "perm": None,
                 "dims": _dims(status="Durum", kind="Tür", manager="Proje yöneticisi", month="Ay", project="Proje"),
                 "measures": {"count": ("Proje sayısı", "sum"), "steps": ("Adım sayısı", "sum"), "steps_done": ("Tamamlanan adım", "sum")}},
    "tasks": {"title": "İş adımları", "rows": rows_tasks, "perm": None,
              "dims": _dims(project="Proje", status="Durum", assignee="Atanan", assignee_type="Atanan türü", job_title="Ünvan",
                            department="Departman", month="Ay"),
              "measures": {"count": ("Adım sayısı", "sum"), "rejections": ("Ret sayısı", "sum"),
                           "duration_days": ("Ort. süre (gün)", "avg")}},
    "ai_usage": {"title": "RECAi kullanımı ve maliyeti", "rows": rows_ai_usage, "perm": "billing:view",
                 "dims": _dims(project="Proje", agent="AI personel", purpose="İş türü", month="Ay"),
                 "measures": {"credits": ("Kredi", "sum"), "cost_try": ("AI maliyeti (TL)", "sum"), "calls": ("Çağrı sayısı", "sum")}},
    "learning": {"title": "Öğrenme kayıtları", "rows": rows_learning, "perm": "memory:promote",
                 "dims": _dims(agent="AI personel", job_title="Ünvan", label="Etiket", cause="Neden", source="Kaynak", month="Ay"),
                 "measures": {"count": ("Kayıt", "sum"), "ok": ("Doğru", "sum"), "wrong": ("Yanlış", "sum"),
                              "ai_errors": ("AI hatası", "sum")}},
    "transfers": {"title": "Sisteme aktarımlar", "rows": rows_transfers, "perm": ("integration:approve", "integration:manage", "mapping:manage"),
                  "dims": _dims(status="Durum", object_type="Nesne", connection="Bağlantı", month="Ay"),
                  "measures": {"count": ("Aktarım", "sum"), "amount": ("Tutar", "sum")}},
}
PLATFORM_CATALOG: Dict[str, Dict[str, Any]] = {
    "platform_titles": {"title": "Ünvan bazında öğrenme (toplu)", "rows": rows_platform_titles, "k": True,
                        "dims": _dims(job_title="Ünvan", label="Etiket", month="Ay"),
                        "measures": {"count": ("Kayıt", "sum"), "ok": ("Doğru", "sum"), "wrong": ("Yanlış", "sum"),
                                     "ai_errors": ("AI hatası", "sum")}},
    "platform_usage": {"title": "RECAi çağrıları (toplu)", "rows": rows_platform_usage, "k": True,
                       "dims": _dims(purpose="İş türü", month="Ay"),
                       "measures": {"calls": ("Çağrı", "sum"), "latency_s": ("Ort. süre (sn)", "avg"), "errors": ("Hata", "sum")}},
    "tenant_health": {"title": "Şirket sağlığı (işletim bilgisi)", "rows": rows_tenant_health, "k": False,
                      "dims": _dims(tenant="Şirket"),
                      "measures": {"credits_30d": ("Son 30 gün kredi", "sum"), "quarantined": ("Karantinadaki adım", "sum"),
                                   "idle_days": ("Son etkinlikten beri gün", "sum")}},
}


def _allowed(user: Optional[CurrentUser], perm) -> bool:
    if perm is None or user is None:
        return True
    perms = perm if isinstance(perm, tuple) else (perm,)
    return any(user.has(p) for p in perms)


def catalog_out(user: Optional[CurrentUser], platform: bool = False) -> List[Dict[str, Any]]:
    cat = PLATFORM_CATALOG if platform else CATALOG
    return [{"code": k, "title": v["title"], "dims": v["dims"], "measures": {m: lbl for m, (lbl, _) in v["measures"].items()}}
            for k, v in cat.items() if platform or _allowed(user, v.get("perm"))]


def catalog_prompt(user: Optional[CurrentUser], platform: bool = False) -> str:
    lines = []
    for r in catalog_out(user, platform):
        lines.append(f"- {r['code']} ({r['title']}): boyutlar {', '.join(f'{k}={v}' for k, v in r['dims'].items())}; "
                     f"ölçüler {', '.join(f'{k}={v}' for k, v in r['measures'].items())}")
    return "\n".join(lines)


def _parse_date(v) -> Optional[date]:
    if not v:
        return None
    try:
        return date.fromisoformat(str(v)[:10])
    except ValueError:
        raise ReportError(f"Geçersiz tarih: {v}")


async def run(db: AsyncSession, spec: Dict[str, Any], *, tenant_id=None, user: Optional[CurrentUser] = None,
              platform: bool = False) -> Dict[str, Any]:
    cat = PLATFORM_CATALOG if platform else CATALOG
    code = str(spec.get("report") or "")
    r = cat.get(code)
    if r is None:
        raise ReportError("Bu rapor katalogda yok.")
    if not platform and not _allowed(user, r.get("perm")):
        raise ReportError("Bu raporu görme yetkiniz yok.", 403)
    dims = [d for d in (spec.get("dims") or []) if d in r["dims"]][:2]
    if not dims:
        dims = [next(iter(r["dims"]))]
    measure = spec.get("measure") if spec.get("measure") in r["measures"] else next(iter(r["measures"]))
    label, agg = r["measures"][measure]
    frm, to = _parse_date(spec.get("date_from")), _parse_date(spec.get("date_to"))
    rows = await (r["rows"](db, frm, to) if platform else r["rows"](db, tenant_id, user, frm, to))
    filters = {k: str(v) for k, v in (spec.get("filters") or {}).items() if k in r["dims"] and v not in (None, "")}
    rows = [x for x in rows if all(str(x.get(k)) == v for k, v in filters.items())]
    groups: Dict[tuple, List[float]] = defaultdict(list)
    tenants: Dict[tuple, Dict[Any, int]] = defaultdict(lambda: defaultdict(int))
    for x in rows:
        key = tuple(x.get(d) or "—" for d in dims)
        val = x.get(measure)
        if val is not None:
            groups[key].append(float(val))
        if "_tenant" in x:
            tenants[key][x["_tenant"]] += 1
    out_groups = {k: (round(sum(v) / len(v), 2) if agg == "avg" else round(sum(v), 2)) for k, v in groups.items() if v}
    hidden, priv = 0, None
    if platform and r.get("k"):
        priv = await privacy(db)
        hidden = suppress(out_groups, tenants, priv["k_min"], priv["dominance_pct"])  # type: ignore[arg-type]
    items = sorted(out_groups.items(), key=lambda kv: (kv[0] if "month" in dims else (-kv[1], kv[0])))
    items = items[:MAX_GROUPS]
    chart = spec.get("chart") if spec.get("chart") in ("bar", "column", "line", "table", "pivot") else (
        "column" if dims[0] == "month" else "bar")
    if spec.get("chart") == "pie":
        chart = "bar"  # pasta grafiği yerine çubuk (karşılaştırma daha doğru okunur)
    if len(dims) == 2 and chart in ("bar", "column", "line"):
        chart = "pivot"
    return {"report": code, "title": spec.get("title") or f"{r['title']} — {label}", "dims": dims,
            "dim_labels": [r["dims"][d] for d in dims], "measure": measure, "measure_label": label, "agg": agg, "chart": chart,
            "rows": [{"keys": list(k), "value": v} for k, v in items], "filters": filters,
            "date_from": frm.isoformat() if frm else None, "date_to": to.isoformat() if to else None,
            "hidden_groups": hidden, "privacy": priv, "truncated": len(out_groups) > MAX_GROUPS}


# ---------------------------------------------------------------- Beyin yanıtından rapor isteğini ayıklama
import json as _json  # noqa: E402
import re as _re  # noqa: E402

BLOCK = _re.compile(r"```rapor\s*(\{.*?\})\s*```", _re.S)

PROMPT = """
# Rapor verebilirsin (İSTEK #744)
Kullanıcı rapor, tablo, grafik, pivot, sayı dökümü isterse yanıtının SONUNA aşağıdaki biçimde TEK bir rapor bloğu ekle; sistem raporu
kullanıcının yetkisiyle çalıştırıp tablo/grafik olarak gösterir. Sayıları kendin uydurma; bloğun önüne raporu bir iki cümleyle tanıt.
```rapor
{{"report": "<kod>", "dims": ["<boyut>", "<isteğe bağlı 2. boyut: pivot sütunu>"], "measure": "<ölçü>",
 "filters": {{"<boyut>": "<değer>"}}, "date_from": "YYYY-MM-DD", "date_to": "YYYY-MM-DD", "chart": "bar|column|line|table|pivot",
 "title": "<kısa başlık>"}}
```
Zaman serisi için dims ["month"] ve chart "column"; iki boyut verirsen pivot olur. Yalnız aşağıdaki raporları kullan:
{catalog}
"""


def extract(text: str) -> Optional[Dict[str, Any]]:
    m = BLOCK.search(text or "")
    if not m:
        return None
    try:
        d = _json.loads(m.group(1))
        return d if isinstance(d, dict) and d.get("report") else None
    except _json.JSONDecodeError:
        return None
