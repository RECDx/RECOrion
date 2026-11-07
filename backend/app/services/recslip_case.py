"""
RECSlip.App v2 aylık Case'i (ADIM 14.4): her ay "RECSlip masraf süreci AAAA-AA" Case'i açılır ve servis yürütür.

Adımlar (S1-S6 muhasebeciye/Case yöneticisine atanır, koşulu oluşunca servis teslim eder; S7'yi AI personel yazar):
  S1 Fiş takibi ve AI onay yürütme   — dönem kesimine kadar; teslim notu: AI/insan karar sayıları
  S2 Yönetici onayları               — geç fiş sonuna kadar; bekleyenler not edilir
  S3 Muhasebe onayları               — geç fiş sonuna kadar; AI düzeltmeleri, uyum oranı
  S4 Ay sonu kesim                   — kesim anında: onaya gönderilmemiş, onayda bekleyen fişler; çalışanlara hatırlatma
  S5 Aktarım dosyası                 — aktarım zamanında: tamamlanan fişlerden şirketin aktarım tipine göre dosya (v2'de), Case'e eklenir;
                                       başarısızsa tekrar (sayı/aralık ayarlarda)
  S6 Muhasebe programına işleme      — RECRobo şimdilik elle; v2'de "işlendi" olunca teslim; olmazsa hatırlatma, tekrar sayısı
                                       dolunca aktarım iptal edilir ve fişler sonraki ayın dosyasına devreder
  S7 Kapanış raporu                  — Muhasebe AI personeli yazar, muhasebe müdürü onaylar
Ayarlar ve kriterler Case'te (projects.settings); sonraki ayın Case'i öncekinin ayarlarıyla açılır. Durum bilgisi settings['state'].
"""
import base64
import hashlib
import logging
import uuid
from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings as app_settings
from app.db.models import (Actor, Artifact, IntegrationConnection, PersonalCredential, Project, RecslipDecision, RecslipExport,
                           Task, Tenant)
from app.integrations.base import ToolError
from app.services import personal_credentials as pcs
from app.services import recslip as rs

logger = logging.getLogger("recorion.recslip")
SOURCE = "recslip"

STEPS = [
    ("S1", "Fiş takibi ve AI onay yürütme", "Okunan fişlerin onay adımları izlenir; kişisel anahtarı tanımlı onaylayıcıların AI personeli kriterlere "
     "göre onaylar, kriter dışı fişler kişinin Onaylarım ekranına gerekçeyle düşer.", "Dönem kesimine kadar bütün onay adımları değerlendirildi"),
    ("S2", "Yönetici onayları", "Yönetici ve ek onaylayıcı adımları: AI onayları ve insan kararları.", "Dönemin yönetici adımları kapandı veya devri not edildi"),
    ("S3", "Muhasebe onayları", "Muhasebe adımları: tek düzen hesap planı kontrolü, RECAi:Mergen ikinci görüşü, AI düzeltmeleri ve insan kararları.",
     "Dönemin muhasebe adımları kapandı veya devri not edildi"),
    ("S4", "Ay sonu kesim", "Kesim anında onaya gönderilmemiş ve onayda bekleyen fişler listelenir; sorumlulara hatırlatma gider.", "Açık fiş listesi"),
    ("S5", "Aktarım dosyası", "Tamamlanan fişlerden şirketin aktarım tipine göre (Luka 1./2. sınıf, Logo 4 Web) aktarım dosyası oluşturulur.",
     "Aktarım dosyası Case'e eklendi"),
    ("S6", "Muhasebe programına işleme", "Dosya RECRobo ile (şimdilik elle) muhasebe programına işlenir; RECSlip'te 'Muhasebeye işlendi' "
     "işaretlenir. İşlenmezse hatırlatılır; tekrar sayısı dolunca aktarım iptal edilir ve fişler sonraki aya devreder.", "Dosya işlendi veya devredildi"),
    ("S7", "Kapanış raporu", "Dönem özeti: fiş sayıları, AI ve insan onayları, AI düzeltmeleri, AI-insan uyum oranı, bekleme süreleri, aktarım sonucu.",
     "Kapanış raporu muhasebe müdürünce onaylandı"),
]
DEPENDS = {"S5": ["S2", "S3", "S4"], "S6": ["S5"], "S7": ["S6"]}


def source_ref(conn_id, period: str) -> str:
    return f"{SOURCE}:{conn_id}:{period}"


async def case_for(db: AsyncSession, conn_id, period: str) -> Optional[Project]:
    return (await db.execute(select(Project).where(Project.source_ref == source_ref(conn_id, period)))).scalar_one_or_none()


async def latest_case(db: AsyncSession, conn_id) -> Optional[Project]:
    return (await db.execute(select(Project).where(Project.source_ref.like(f"{SOURCE}:{conn_id}:%"))
                             .order_by(Project.created_at.desc()).limit(1))).scalar_one_or_none()


async def _usable_cred(db: AsyncSession, actor_id, conn_id) -> Optional[PersonalCredential]:
    cred = (await db.execute(select(PersonalCredential).where(PersonalCredential.actor_id == actor_id,
                                                              PersonalCredential.connection_id == conn_id))).scalar_one_or_none()
    return cred if pcs.usable(cred) else None


async def create_case(db: AsyncSession, conn: IntegrationConnection, period: str, manager: Actor, report_agent: Actor,
                      report_approver: Actor, s: Dict[str, Any]) -> Project:
    """Dönemin Case'ini açar, planı onaylar ve başlatır (S1-S6 yöneticide, S7 AI personelde)."""
    from app.services import project_planning as planning
    from app.services import projects as psvc

    existing = await case_for(db, conn.id, period)
    if existing:
        return existing
    tenant = await db.get(Tenant, conn.tenant_id)
    await psvc.ensure_project_quota(db, tenant)
    name = f"RECSlip masraf süreci {period}"
    settings = {**rs.validate_settings(s), "connection_id": str(conn.id), "period": period, "manager_actor_id": str(manager.id),
                "report_agent_id": str(report_agent.id), "report_approver_id": str(report_approver.id), "state": {}}
    steps = []
    for key, title, desc, acc in STEPS:
        steps.append({"key": key, "title": title, "description": desc, "acceptance_criteria": acc,
                      "agent_id": str(report_agent.id if key == "S7" else manager.id), "estimated_days": 1,
                      "requires_approval": key == "S7", "approver_actor_id": str(report_approver.id) if key == "S7" else None,
                      "depends_on": DEPENDS.get(key, [])})
    p = Project(tenant_id=conn.tenant_id, slug=await psvc.unique_slug(db, conn.tenant_id, name), name=name, kind="CASE",
                description="RECSlip.App v2 aylık masraf süreci: onaylar, ay sonu kesim, aktarım dosyası, kapanış raporu.",
                requirements=f"{period} dönemi RECSlip masraf fişlerinin onay süreci, kesimi, aktarımı ve kapanışı.", status="DRAFT",
                manager_actor_id=manager.id, created_by_actor_id=manager.id, source_ref=source_ref(conn.id, period),
                plan={"summary": "RECSlip aylık masraf süreci", "steps": steps}, settings=settings)
    db.add(p)
    await db.flush()
    await psvc.set_member(db, p, manager, "MANAGER", manager.id)
    await planning.approve_plan(db, p, manager.id)
    p = await db.get(Project, p.id)
    cal = rs.calendar_of(period, settings)
    y, m = (int(x) for x in period.split("-"))
    p.start_date, p.end_date = date(y, m, 1), (cal["export"] + timedelta(days=7)).date()
    await psvc.transition(db, p, "mark_ready")
    await psvc.transition(db, p, "start")
    if app_settings.WORKFLOW_ENABLED:
        from app.workflows import engine
        p.workflow_id = await engine.start_project(str(p.id), str(manager.id))
    await db.commit()
    return p


async def setup(db: AsyncSession, tenant_id, connection_id, manager_id, report_agent_id, report_approver_id,
                s: Optional[Dict[str, Any]] = None, today: Optional[date] = None) -> Project:
    """Paketi kurar: bağlantıda v2'yi doğrular, bu ayın Case'ini açar."""
    from app.services import tool_gateway

    conn = await db.get(IntegrationConnection, connection_id)
    if not conn or conn.tenant_id != tenant_id or conn.connector != "odoo" or conn.status != "ACTIVE":
        raise HTTPException(status_code=404, detail="Odoo bağlantısı bulunamadı veya etkin değil.")
    try:
        await rs.check_v2(tool_gateway.context(conn))
    except (rs.RecslipError, ToolError) as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    manager, agent, approver = (await db.get(Actor, manager_id), await db.get(Actor, report_agent_id), await db.get(Actor, report_approver_id))
    for a, kind, label in ((manager, "HUMAN", "Case yöneticisi (muhasebeci)"), (agent, "AI_AGENT", "Kapanış raporu AI personeli"),
                           (approver, "HUMAN", "Kapanış raporu onaylayıcısı")):
        if not a or a.tenant_id != tenant_id or a.actor_type != kind or a.status == "DISABLED":
            raise HTTPException(status_code=400, detail=f"{label} bu şirkette uygun bir kişi değil.")
    if not await _usable_cred(db, manager.id, conn.id):
        raise HTTPException(status_code=400, detail="Case yöneticisinin (muhasebecinin) bu bağlantıda kişisel Odoo anahtarı yok; "
                                                    "önce Bağlantılarım'dan tanımlamalı (aktarım dosyası onun anahtarıyla oluşturulur).")
    return await create_case(db, conn, rs.period_of(today or rs.now().astimezone(rs.TZ).date()), manager, agent, approver, s or {})


# ---------------------------------------------------------------- adımların teslimi
async def _tasks(db: AsyncSession, p: Project) -> Dict[str, Task]:
    rows = (await db.execute(select(Task).where(Task.project_id == p.id).order_by(Task.order_index))).scalars().all()
    return {STEPS[t.order_index - 1][0]: t for t in rows if t.order_index and t.order_index <= len(STEPS)}


async def _submit(db: AsyncSession, p: Project, task: Task, note: str) -> bool:
    from app.services import task_flow

    if task.status not in task_flow.WORKING:
        return False
    if app_settings.WORKFLOW_ENABLED:
        from app.workflows import engine
        await engine.signal_task(str(task.id), "submit", {"actor_id": str(p.manager_actor_id), "note": note[:4000]})
    else:
        await task_flow.submit(db, task.id, {"actor_id": str(p.manager_actor_id), "note": note[:4000]})
    return True


def _state(p: Project) -> Dict[str, Any]:
    return dict((p.settings or {}).get("state") or {})


def _save_state(p: Project, st: Dict[str, Any]) -> None:
    p.settings = {**(p.settings or {}), "state": st}


async def decision_counts(db: AsyncSession, p: Project) -> Dict[str, Dict[str, int]]:
    rows = (await db.execute(select(RecslipDecision.role, RecslipDecision.status, func.count()).where(RecslipDecision.project_id == p.id)
                             .group_by(RecslipDecision.role, RecslipDecision.status))).all()
    out: Dict[str, Dict[str, int]] = {}
    for role, status, n in rows:
        out.setdefault("accountant" if role == "accountant" else "manager", {})[status] = n
    return out


def _counts_text(c: Dict[str, int]) -> str:
    labels = {"AUTO_DONE": "AI onayladı", "PENDING": "insan kararı bekliyor", "HUMAN_APPROVED": "insan onayladı",
              "HUMAN_REFUSED": "insan reddetti", "ELSEWHERE": "Odoo'dan karar verildi", "FAILED": "hata"}
    return ", ".join(f"{labels.get(k, k)}: {v}" for k, v in sorted(c.items())) or "karar yok"


async def agreement(db: AsyncSession, p: Project) -> Optional[float]:
    rows = (await db.execute(select(RecslipDecision.human_agreed).where(RecslipDecision.project_id == p.id,
                                                                        RecslipDecision.status.in_(("HUMAN_APPROVED", "HUMAN_REFUSED"))))).all()
    vals = [r[0] for r in rows]
    return round(100 * sum(1 for v in vals if v) / len(vals), 1) if vals else None


async def open_receipts(ctx, period: str) -> Dict[str, Any]:
    y, m = (int(x) for x in period.split("-"))
    last = date(y, m, 1).replace(day=28) + timedelta(days=4)
    last = last - timedelta(days=last.day)
    dom = [["date", ">=", f"{period}-01"], ["date", "<=", last.isoformat()]]
    unsent = await rs._kw(ctx, "hr.expense", "search_read", [dom + [["rs_state", "in", ["analyzed", "draft", "ai_error"]]]],
                          {"fields": ["id", "name", "employee_id", "total_amount_currency"], "limit": 500}) or []
    waiting = await rs._kw(ctx, "hr.expense", "search_count", [dom + [["rs_state", "=", "approval"]]]) or 0
    done = await rs._kw(ctx, "hr.expense", "search_count", [dom + [["rs_state", "=", "done"]]]) or 0
    return {"unsent": unsent, "waiting": waiting, "done": done}


async def _store_artifact(db: AsyncSession, task: Task, name: str, data: bytes, producer_id) -> Artifact:
    from app.services import agent_work, storage

    version = ((await db.execute(select(func.max(Artifact.version)).where(Artifact.task_id == task.id))).scalar() or 0) + 1
    art = Artifact(task_id=task.id, name=name[:255], artifact_type="DOCUMENT", version=version, produced_by_actor_id=producer_id,
                   content_hash=hashlib.sha256(data).hexdigest(), approval_status="SUBMITTED")
    art.storage_path = agent_work.artifact_key(task, version)
    await storage.put_object(art.storage_path, data)
    db.add(art)
    await db.flush()
    return art


async def export_period(db: AsyncSession, conn: IntegrationConnection, p: Project, task: Task,
                        at: Optional[datetime] = None) -> RecslipExport:
    """Dönemin aktarım dosyası (muhasebecinin anahtarıyla, v2'de); Case'e eklenir.
    Hata: ayardaki tekrar aralığı kadar sonra yeniden denenir (HATA #590: önceden her turda deneniyordu); sayı dolunca FAILED."""
    at = at or rs.now()
    s = rs.settings_of(p)
    period = (p.settings or {}).get("period")
    exp = (await db.execute(select(RecslipExport).where(RecslipExport.connection_id == conn.id, RecslipExport.period == period))).scalar_one_or_none()
    if not exp:
        exp = RecslipExport(tenant_id=conn.tenant_id, connection_id=conn.id, project_id=p.id, period=period, status="PENDING", attempts=0)
        db.add(exp)
    if exp.status in ("CREATED", "POSTED", "FAILED"):
        return exp
    if exp.odoo_export_id:
        # Dosya v2'de zaten oluşmuş (önceki denemede yalnız Case'e alma adımı kalmıştı): beklemeden tamamlanır,
        # yeniden aktarım yapılmaz (#658)
        exp.status, exp.last_error, exp.next_attempt_at = "CREATED", None, None
        await db.commit()
        return exp
    if exp.next_attempt_at and at < exp.next_attempt_at:
        return exp  # tekrar zamanı gelmedi
    exp.attempts = (exp.attempts or 0) + 1
    try:
        cred = await _usable_cred(db, p.manager_actor_id, conn.id)
        if not cred:
            raise rs.RecslipError("Case yöneticisinin Odoo anahtarı geçersiz veya süresi dolmuş (Bağlantılarım).")
        ctx = pcs.context(conn, cred)
        y, m = (int(x) for x in period.split("-"))
        last = (date(y, m, 28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
        # dönem sonuna kadarki tamamlanmış fişler (önceki aylardan devredenler dahil)
        rows = await rs._kw(ctx, "hr.expense", "search_read", [[["rs_state", "=", "done"], ["date", "<=", last.isoformat()]]],
                            {"fields": ["id"], "limit": 5000}) or []
        ids = [r["id"] for r in rows]
        if not ids:
            exp.status, exp.receipt_count, exp.last_error = "CREATED", 0, None
            await db.commit()
            return exp
        res = await rs._kw(ctx, "hr.expense", "rs_external_export", [ids])
        exp.odoo_export_id, exp.name, exp.software = res.get("export_id") or None, res.get("name"), res.get("software")
        exp.receipt_count, exp.total, exp.not_exported = res.get("receipt_count"), res.get("total"), len(res.get("not_exported_ids") or [])
        # Kullanıcı kararı (07.11.2026, #658): aktarım dosyası RECOrion'a alınmaz; RECSlip'te (v2) kalır, Case dosyanın adını,
        # v2 kaydını ve indirme bağlantısını tutar. Muhasebeci indirdiyse bilgisayardaki yolunu Case'e yazabilir (local_path).
        exp.status, exp.last_error, exp.next_attempt_at = "CREATED", None, None
    except (ToolError, rs.RecslipError) as exc:
        exp.last_error = str(exc)[:1000]
        retry = s["retry"]
        if exp.attempts > retry["count"]:
            exp.status = "FAILED"
        else:
            exp.next_attempt_at = at + timedelta(hours=retry["interval_hours"])
    await db.commit()
    return exp


async def _notify(db: AsyncSession, actor_ids: List[Any], text: str) -> None:
    from app.services import notify

    for aid in dict.fromkeys(str(a) for a in actor_ids if a):
        try:
            await notify.send(db, aid, text)
        except Exception as exc:
            logger.warning("RECSlip bildirimi gönderilemedi: %s", exc)


KEY_WARN_DAYS = 14  # Bağlantılarım'daki sarı rozetle aynı


async def _remind_unsent(db: AsyncSession, conn: IntegrationConnection, p: Project, s: Dict[str, Any], st: Dict[str, Any],
                         cal: Dict[str, datetime], at: datetime) -> None:
    """HATA #591: okunmuş ama "Onaya gönderilmemiş fiş hatırlatması (gün)"den uzun süredir gönderilmemiş fişler; kesime kadar
    her N günde bir Case yöneticisine (muhasebeci) liste gider. 0 = kapalı."""
    from app.services import tool_gateway

    days = int(s.get("submit_reminder_days") or 0)
    if days <= 0 or at >= cal["cutoff"]:
        return
    last = datetime.fromisoformat(st["submit_reminded"]) if st.get("submit_reminded") else None
    if last and at - last < timedelta(days=days):
        return
    st["submit_reminded"] = at.isoformat()
    _save_state(p, st)
    older = (at - timedelta(days=days)).astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    rows = await rs._kw(tool_gateway.context(conn), "hr.expense", "search_read",
                        [[["rs_state", "in", ["analyzed", "draft", "ai_error"]], ["create_date", "<=", older]]],
                        {"fields": ["id", "name", "employee_id", "total_amount_currency"], "limit": 200}) or []
    if rows:
        names = ", ".join(f"{r.get('name')} ({(r.get('employee_id') or [None, '?'])[1]})" for r in rows[:10])
        await _notify(db, [p.manager_actor_id], f"RECSlip {(p.settings or {}).get('period')}: {len(rows)} fiş okundu ama {days} günden uzun "
                                                f"süredir onaya gönderilmedi: {names}{' …' if len(rows) > 10 else ''}. Çalışanlara hatırlatın; "
                                                f"kesim {cal['cutoff'].astimezone(rs.TZ):%d.%m.%Y %H:%M}.")
    await db.commit()


async def remind_keys(db: AsyncSession, conn: IntegrationConnection, p: Project, at: datetime) -> int:
    """HATA #591: kişisel Odoo anahtarının bitişine 14 gün kala ve bittiğinde sahibine birer kez hatırlatma (durum Case'te tutulur)."""
    from app.db.models import PersonalCredential

    st = _state(p)
    sent = st.setdefault("key_reminders", {})
    creds = (await db.execute(select(PersonalCredential).where(PersonalCredential.connection_id == conn.id,
                                                               PersonalCredential.expires_at.isnot(None)))).scalars().all()
    n = 0
    for c in creds:
        stage = "expired" if c.expires_at <= at else ("soon" if c.expires_at - at <= timedelta(days=KEY_WARN_DAYS) else None)
        mark = f"{stage}:{c.expires_at.isoformat()}"
        if not stage or sent.get(str(c.id)) == mark:
            continue
        sent[str(c.id)] = mark
        day = c.expires_at.astimezone(rs.TZ).strftime("%d.%m.%Y")
        text = (f"RECSlip: '{conn.name}' için Odoo anahtarınızın süresi doldu ({day}). AI personeliniz sizin adınıza onay yapamıyor; "
                "Odoo'da yeni API anahtarı oluşturup Work Space › Bağlantılarım'dan güncelleyin." if stage == "expired" else
                f"RECSlip: '{conn.name}' için Odoo anahtarınızın süresi {day} tarihinde doluyor. Odoo'da yeni API anahtarı oluşturup "
                "Work Space › Bağlantılarım'dan güncelleyin; aksi halde onaylar size düşer.")
        await _notify(db, [c.actor_id], text)
        n += 1
    _save_state(p, st)
    await db.commit()
    return n


async def advance(db: AsyncSession, conn: IntegrationConnection, p: Project, at: Optional[datetime] = None) -> Dict[str, Any]:
    """Case'in zamana ve duruma bağlı adımlarını ilerletir (kesim, aktarım, işlendi kontrolü, tekrar)."""
    from app.services import notify, tool_gateway

    at = at or rs.now()
    s, st = rs.settings_of(p), _state(p)
    period = (p.settings or {}).get("period")
    cal = rs.calendar_of(period, s)
    tasks = await _tasks(db, p)
    done: List[str] = []
    counts = await decision_counts(db, p)
    await _remind_unsent(db, conn, p, s, st, cal, at)
    if at >= cal["cutoff"] and not st.get("S1"):
        if await _submit(db, p, tasks["S1"], "Dönem kesimine kadar onay adımları değerlendirildi. Yönetici: "
                                            f"{_counts_text(counts.get('manager', {}))}. Muhasebe: {_counts_text(counts.get('accountant', {}))}."):
            st["S1"] = at.isoformat()
            done.append("S1")
    if at >= cal["cutoff"] and not st.get("S4"):
        info = await open_receipts(tool_gateway.context(conn), period)
        note = (f"Kesim ({cal['cutoff'].astimezone(rs.TZ):%d.%m.%Y %H:%M}): onaya gönderilmemiş {len(info['unsent'])} fiş, onayda bekleyen "
                f"{info['waiting']}, tamamlanan {info['done']}. Geç gelen fişler {cal['late_until'].astimezone(rs.TZ):%d.%m.%Y} sonuna kadar beklenir.")
        if await _submit(db, p, tasks["S4"], note):
            st["S4"] = at.isoformat()
            done.append("S4")
            if info["unsent"]:
                await _notify(db, [p.manager_actor_id], f"RECSlip {period}: onaya gönderilmemiş {len(info['unsent'])} fiş var; çalışanlara hatırlatın. "
                                                        f"{notify.project_url(p.id)}")
    if at >= cal["late_until"]:
        for key, role in (("S2", "manager"), ("S3", "accountant")):
            if not st.get(key):
                c = counts.get(role, {})
                note = f"{'Yönetici' if role == 'manager' else 'Muhasebe'} adımları: {_counts_text(c)}."
                if role == "accountant":
                    corr = (await db.execute(select(func.count()).select_from(RecslipDecision).where(
                        RecslipDecision.project_id == p.id, RecslipDecision.role == "accountant",
                        func.jsonb_array_length(RecslipDecision.corrections) > 0))).scalar() or 0
                    rate = await agreement(db, p)
                    note += f" AI hesap düzeltmesi yapılan fiş: {corr}." + (f" AI-insan uyumu: %{rate}." if rate is not None else "")
                if c.get("PENDING"):
                    note += f" Karar bekleyen {c['PENDING']} fiş sonraki dönemde de izlenir."
                if await _submit(db, p, tasks[key], note):
                    st[key] = at.isoformat()
                    done.append(key)
    if at >= cal["export"] and not st.get("S5"):
        exp = await export_period(db, conn, p, tasks["S5"], at)
        if exp.status == "CREATED":
            note = (f"Aktarım dosyası: {exp.name or 'dosya yok'} · {exp.receipt_count or 0} fiş · toplam {float(exp.total or 0):,.2f}"
                    + (f" · aktarılmayacak {exp.not_exported}" if exp.not_exported else "") + ".")
            if await _submit(db, p, tasks["S5"], note):
                st["S5"] = at.isoformat()
                done.append("S5")
                if exp.receipt_count:
                    await _notify(db, [p.manager_actor_id], f"RECSlip {period}: aktarım dosyası hazır ({exp.name}). RECRobo ile muhasebe "
                                                            f"programına işleyin, sonra RECSlip'te 'Muhasebeye işlendi' işaretleyin. {notify.project_url(p.id)}")
        elif exp.status == "FAILED" and not st.get("S5_failed"):
            st["S5_failed"] = at.isoformat()
            await _notify(db, [p.manager_actor_id], f"RECSlip {period}: aktarım dosyası {exp.attempts} denemede oluşturulamadı: {exp.last_error}. "
                                                    f"{notify.project_url(p.id)}")
    if st.get("S5") and not st.get("S6"):
        done += await _check_posted(db, conn, p, tasks, s, st, at)
    _save_state(p, st)
    await db.commit()
    return {"done": done}


async def _check_posted(db: AsyncSession, conn: IntegrationConnection, p: Project, tasks: Dict[str, Task], s: Dict[str, Any],
                        st: Dict[str, Any], at: datetime) -> List[str]:
    from app.services import notify, tool_gateway

    period = (p.settings or {}).get("period")
    exp = (await db.execute(select(RecslipExport).where(RecslipExport.connection_id == conn.id, RecslipExport.period == period))).scalar_one_or_none()
    if not exp or not exp.odoo_export_id:  # dosya yoksa (tamamlanan fiş yok) işlenecek bir şey de yok
        if await _submit(db, p, tasks["S6"], "Bu dönemde aktarılacak fiş olmadığı için muhasebe programına işlenecek dosya yok."):
            st["S6"] = at.isoformat()
            await _prepare_report(db, p, tasks)
            return ["S6"]
        return []
    state = (await rs._kw(tool_gateway.context(conn), "recslip.export", "read", [[exp.odoo_export_id]], {"fields": ["state"]}) or [{}])[0].get("state")
    if state == "posted":
        exp.status, exp.posted_at = "POSTED", at
        if await _submit(db, p, tasks["S6"], f"{exp.name} muhasebe programına işlendi."):
            st["S6"] = at.isoformat()
            await _prepare_report(db, p, tasks)
            return ["S6"]
        return []
    created = datetime.fromisoformat(st["S5"])
    reminders = int(st.get("S6_reminders") or 0)
    due = created + timedelta(days=s["posted_reminder_days"]) + timedelta(hours=s["retry"]["interval_hours"] * reminders)
    if at < due:
        return []
    if reminders < s["retry"]["count"]:
        st["S6_reminders"] = reminders + 1
        await _notify(db, [p.manager_actor_id], f"RECSlip {period}: {exp.name} henüz muhasebe programına işlenmedi ({reminders + 1}. hatırlatma). "
                                                f"RECRobo ile işleyip RECSlip'te 'Muhasebeye işlendi' işaretleyin. {notify.project_url(p.id)}")
        return []
    # tekrar sayısı doldu: aktarım iptal, fişler sonraki ayın dosyasına devreder
    cred = await _usable_cred(db, p.manager_actor_id, conn.id)
    note = f"{exp.name} {reminders} hatırlatmaya rağmen işlenmedi"
    try:
        if cred and state == "exported":
            await rs._kw(pcs.context(conn, cred), "recslip.export", "action_cancel", [[exp.odoo_export_id]])
            note += "; aktarım iptal edildi, fişler sonraki ayın dosyasına devredildi."
            exp.status = "FAILED"
    except ToolError as exc:
        note += f"; aktarım iptal edilemedi ({exc})."
    if await _submit(db, p, tasks["S6"], note):
        st["S6"] = at.isoformat()
        await _prepare_report(db, p, tasks)
        await _notify(db, [p.manager_actor_id], f"RECSlip {period}: {note} {notify.project_url(p.id)}")
        return ["S6"]
    return []


async def _prepare_report(db: AsyncSession, p: Project, tasks: Dict[str, Task]) -> None:
    """S7'yi yazacak AI personele dönem verisini adım açıklamasına koyar (rapor yalnızca bu veriye dayanır)."""
    counts = await decision_counts(db, p)
    rate = await agreement(db, p)
    exp = (await db.execute(select(RecslipExport).where(RecslipExport.project_id == p.id))).scalars().first()
    corr = (await db.execute(select(RecslipDecision.expense_name, RecslipDecision.corrections).where(
        RecslipDecision.project_id == p.id, func.jsonb_array_length(RecslipDecision.corrections) > 0).limit(30))).all()
    lines = [f"Dönem: {(p.settings or {}).get('period')}",
             f"Yönetici adımları: {_counts_text(counts.get('manager', {}))}",
             f"Muhasebe adımları: {_counts_text(counts.get('accountant', {}))}",
             f"AI-insan uyum oranı: {'%' + str(rate) if rate is not None else 'insan kararı yok'}",
             f"Aktarım: {exp.name if exp else 'yok'} · {exp.receipt_count if exp else 0} fiş · durum {exp.status if exp else '-'}"]
    for name, cs in corr:
        for c in cs[:5]:
            lines.append(f"Düzeltme · {name}: '{c.get('line')}' {c.get('old')} → {c.get('new')} ({c.get('reason')})")
    t = tasks["S7"]
    t.description = (STEPS[6][2] + "\n\nDÖNEM VERİSİ (raporu yalnızca bu veriye dayandır):\n" + "\n".join(f"- {x}" for x in lines))[:20000]


# ---------------------------------------------------------------- izleyici
async def tick(db: AsyncSession, at: Optional[datetime] = None) -> Dict[str, Any]:
    """Her RECSlip bağlantısı için: son Case'e göre onayları işler (takip sıklığında), Case'i ilerletir, yeni ayın Case'ini açar."""
    at = at or rs.now()
    out: Dict[str, Any] = {}
    refs = (await db.execute(select(Project).where(Project.source_ref.like(f"{SOURCE}:%"), Project.status == "ACTIVE"))).scalars().all()
    by_conn: Dict[str, List[Project]] = {}
    for p in refs:
        by_conn.setdefault((p.settings or {}).get("connection_id"), []).append(p)
    for cid, cases in by_conn.items():
        conn = await db.get(IntegrationConnection, uuid.UUID(cid)) if cid else None
        if not conn or conn.status != "ACTIVE":
            continue
        cases.sort(key=lambda c: (c.settings or {}).get("period") or "")
        newest = cases[-1]
        try:
            cur = rs.period_of(at.astimezone(rs.TZ).date())
            if (newest.settings or {}).get("period", "") < cur:
                prev = newest.settings or {}
                manager, agent, approver = (await db.get(Actor, uuid.UUID(prev["manager_actor_id"])),
                                            await db.get(Actor, uuid.UUID(prev["report_agent_id"])),
                                            await db.get(Actor, uuid.UUID(prev["report_approver_id"])))
                newest = await create_case(db, conn, cur, manager, agent, approver, rs.settings_of(newest))
                cases.append(newest)
            st = _state(newest)
            last = datetime.fromisoformat(st["last_run"]) if st.get("last_run") else None
            if not last or at - last >= timedelta(minutes=rs.settings_of(newest)["poll_minutes"]):
                out[cid] = await rs.run_connection(db, conn, newest)
                st = _state(newest)
                st["last_run"] = at.isoformat()
                _save_state(newest, st)
                await db.commit()
            for c in cases:
                await advance(db, conn, c, at)
            await remind_keys(db, conn, newest, at)
        except Exception as exc:  # bir şirketin hatası diğerlerini durdurmaz
            await db.rollback()
            logger.error("RECSlip turu hatası (%s): %s", cid, exc)
            out[cid] = {"error": str(exc)[:300]}
    return out


async def loop(interval: int = 60) -> None:
    import asyncio

    from app.db.session import AsyncSessionLocal

    logger.info("RECSlip izleyicisi başladı (her %s sn).", interval)
    while True:
        try:
            async with AsyncSessionLocal() as db:
                await tick(db)
        except Exception as exc:
            logger.error("RECSlip izleyici hatası: %s", exc)
        await asyncio.sleep(interval)
