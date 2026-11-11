"""
İSTEK #738 — Beyin AI'nin iki kapsamı (ayrıntı ve gerekçe: Claude/senaryo/karar_ogrenme_recai.md §6).

İlke: Beyin AI ezberlemez; YETKİLİ araçlarla sorgular. KVKK sınırı burada uygulanır.

Şirket Beyin'i — kendi şirketinin her şeyi + platform yardımı; sınırı konuşan kullanıcının ROLÜ:
  projeleri yalnız görebildikleri (project:manage yoksa yöneticisi/üyesi olduğu), kredi yalnız billing:view ile, öğrenme özeti
  yalnız memory:promote ile. Başka şirketleri bilmez. Öğrendiği yalnız şirket hafızasına (kurumsal aday → yönetici onayı).

Merkez Beyin'i — sistemin İŞLEYİŞİNE hakim, müşteri İÇERİĞİNE değil:
  platform (yardım, şablon kullanımı, modeller), şirket bazında işletim bilgisi (kredi, son etkinlik, takılan adım SAYISI),
  şirketler arası toplu istatistik — her satır EN AZ 5 ŞİRKETİN verisinden (k-anonimlik; küçük şirket içerikten tanınmasın).
  Maskeli de olsa tekil kayıt göstermez; RECAi eğitim havuzu gezilebilir arşiv değildir.
  İçerik yalnız müşterinin verdiği SÜRELİ destek erişimiyle ve her okuma kayda geçerek görülür.
"""
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import CurrentUser
from app.db.models import (LearningRecord, LLMCall, Project, ProjectMember, ProjectTemplate, SupportAccessGrant, SupportAccessLog,
                           Task, TaskEvent, Tenant)

STATUS_TR = {"BACKLOG": "sırada", "READY": "başlayabilir", "IN_PROGRESS": "çalışılıyor", "WAITING_APPROVAL": "onay bekliyor",
             "REVISION": "revizyonda", "QUARANTINED": "karantinada", "DONE": "tamamlandı", "CANCELLED": "iptal"}


def now() -> datetime:
    return datetime.now(timezone.utc)


def _lines(items: List[str], empty: str = "- (yok)") -> str:
    return "\n".join(f"- {i}" for i in items) or empty


# ---------------------------------------------------------------- yardım (kılavuz)
async def help_section(db: AsyncSession, user: CurrentUser, question: str, limit: int = 3) -> Tuple[str, List[Dict[str, Any]]]:
    """Kullanıcının görebildiği kılavuz sayfalarından en ilgili bölümler (yetkisiz sayfa içeriği verilmez)."""
    from app.services import help_center as hc

    try:
        hits = await hc.search(db, user, (question or "")[:500], limit=8)
    except Exception:
        return "", []
    pages = [p for p, _r, _ in hits if hc.can_see(user, p)][:limit]
    if not pages:
        return "", []
    text = "\n\n".join(f"### {hc.guide_title(p.guide)} › {p.title}\n{(p.body or '')[:1500]}" for p in pages)
    return text, [{"slug": p.slug, "title": p.title, "guide_title": hc.guide_title(p.guide),
                   "screen": next((k for k in (p.screen_keys or []) if not k.endswith("/")), None)} for p in pages]


# ---------------------------------------------------------------- şirket (rol sınırlı)
async def _projects_for(db: AsyncSession, user: Optional[CurrentUser], tenant_id) -> List[Project]:
    q = select(Project).where(Project.tenant_id == tenant_id, Project.status.notin_(("ARCHIVED",)))
    if user is not None and not user.has("project:manage"):
        member_of = select(ProjectMember.project_id).where(ProjectMember.actor_id == user.actor_id)
        q = q.where(or_(Project.id.in_(member_of), Project.manager_actor_id == user.actor_id))
    return (await db.execute(q.order_by(Project.updated_at.desc()).limit(25))).scalars().all()


async def company_facts(db: AsyncSession, tenant: Tenant, user: Optional[CurrentUser]) -> str:
    """Şirket Beyin'i için güncel iş durumu. user None: destek erişimi (tüm projeler, yalnız durum bilgisi)."""
    projects = await _projects_for(db, user, tenant.id)
    ids = [p.id for p in projects] or [None]
    counts: Dict[Any, Dict[str, int]] = {}
    for pid, st, n in (await db.execute(select(Task.project_id, Task.status, func.count()).where(Task.project_id.in_(ids))
                                        .group_by(Task.project_id, Task.status))).all():
        counts.setdefault(pid, {})[st] = int(n)
    rows = []
    for p in projects:
        c = counts.get(p.id, {})
        total = sum(c.values())
        done = c.get("DONE", 0)
        detail = ", ".join(f"{STATUS_TR.get(k, k)} {v}" for k, v in c.items() if k not in ("DONE",) and v)
        rows.append(f"{p.name} [{p.status}] — {done}/{total} adım tamam" + (f"; {detail}" if detail else ""))
    parts = [f"# Projeler ({'tümü' if user is None or user.has('project:manage') else 'yalnız ekibinde olduğunuz'})", _lines(rows)]
    if user is not None:
        waiting = (await db.execute(select(Task.title, Project.name).join(Project, Project.id == Task.project_id).where(
            Project.tenant_id == tenant.id, Task.status == "WAITING_APPROVAL",
            or_(Task.approver_actor_id == user.actor_id, and_(Task.approver_actor_id.is_(None), Project.manager_actor_id == user.actor_id))
        ).limit(15))).all()
        parts += ["# Onayınızı bekleyen adımlar", _lines([f"{t} ({p})" for t, p in waiting])]
    stuck = (await db.execute(select(Task.title, Project.name).join(Project, Project.id == Task.project_id).where(
        Project.id.in_(ids), Task.status == "QUARANTINED").limit(10))).all()
    if stuck:
        parts += ["# Karantinada (yönetici kararı bekleyen) adımlar", _lines([f"{t} ({p})" for t, p in stuck])]
    if user is None or user.has("billing:view"):
        from app.services import credits
        used = (await db.execute(select(func.sum(LLMCall.credits_cost)).where(
            LLMCall.tenant_id == tenant.id, LLMCall.created_at >= now() - timedelta(days=30)))).scalar() or 0
        parts += ["# Son 30 gün RECAi kullanımı", f"- {float(used):.0f} kredi (dönem {credits.current_period()})"]
    if user is None or user.has("memory:promote"):
        lab = dict((await db.execute(select(LearningRecord.label, func.count()).where(LearningRecord.tenant_id == tenant.id)
                                     .group_by(LearningRecord.label))).all())
        if lab:
            parts += ["# Öğrenme kayıtları (Şirket Yönetimi › Öğrenme)",
                      f"- doğru {lab.get('DOGRU', 0)}, yanlış {lab.get('YANLIS', 0)}, belirsiz {lab.get('BELIRSIZ', 0)}"]
    return "\n".join(parts)


# ---------------------------------------------------------------- Merkez (toplu, k ≥ 5)
async def platform_facts(db: AsyncSession) -> str:
    from app.services import reports
    priv = await reports.privacy(db)  # #744: k eşiği ve baskınlık sınırı Merkez ayarıdır
    k_min, dom = priv["k_min"], priv["dominance_pct"]
    parts: List[str] = []
    # Ünvan bazında doğru/yanlış — yalnız en az k şirkette görülen ve tek şirketin payı sınırı aşmayan ünvanlar
    rows = (await db.execute(select(LearningRecord.job_title, LearningRecord.tenant_id,
                                    func.count().filter(LearningRecord.label == "YANLIS"),
                                    func.count().filter(LearningRecord.label == "DOGRU"),
                                    func.count().filter(LearningRecord.cause == "MODEL_HATASI"), func.count())
                             .where(LearningRecord.job_title.isnot(None))
                             .group_by(LearningRecord.job_title, LearningRecord.tenant_id))).all()
    agg: Dict[str, Dict[str, Any]] = {}
    for title, tid, bad, ok, mh, n in rows:
        a = agg.setdefault(title, {"bad": 0, "ok": 0, "mh": 0, "per": {}})
        a["bad"] += bad
        a["ok"] += ok
        a["mh"] += mh
        a["per"][tid] = n
    shown, hidden = [], 0
    for title, a in sorted(agg.items()):
        total = sum(a["per"].values())
        if len(a["per"]) < k_min or (total and max(a["per"].values()) * 100 / total > dom):
            hidden += 1
            continue
        shown.append(f"{title}: {len(a['per'])} şirket, doğru {a['ok']}, yanlış {a['bad']} (AI hatası {a['mh']})")
    parts += [f"# Ünvan bazında öğrenme istatistiği (en az {k_min} şirket; tek şirket payı en çok %{dom})", _lines(shown)]
    if hidden:
        parts.append(f"- ({hidden} ünvan gösterilmedi: {k_min}'ten az şirkette görüldü ya da tek şirket baskın — KVKK k-anonimlik)")
    # Takılmalar ve model sağlığı (sayı)
    since = now() - timedelta(days=30)
    blocked = (await db.execute(select(func.count()).select_from(TaskEvent).where(TaskEvent.kind == "BLOCKED",
                                                                                  TaskEvent.created_at >= since))).scalar() or 0
    calls = (await db.execute(select(LLMCall.purpose, func.count(), func.avg(LLMCall.latency_ms),
                                     func.count().filter(LLMCall.status != "SUCCESS"))
                              .where(LLMCall.created_at >= since).group_by(LLMCall.purpose))).all()
    parts += ["# Son 30 gün işletim (toplam)", f"- durma (BLOCKED) olayı: {blocked}",
              _lines([f"{p or '-'}: {n} çağrı, ort. {float(a or 0) / 1000:.1f} sn, hata {e}" for p, n, a, e in calls])]
    tpl = (await db.execute(select(ProjectTemplate.name, ProjectTemplate.use_count).where(ProjectTemplate.tenant_id.is_(None))
                            .order_by(ProjectTemplate.use_count.desc()).limit(10))).all()
    parts += ["# RECDx şablonlarının kullanımı", _lines([f"{n}: {u}" for n, u in tpl])]
    # Şirket sağlığı (işletim bilgisi; içerik değil)
    last = dict((await db.execute(select(TaskEvent.tenant_id, func.max(TaskEvent.created_at)).group_by(TaskEvent.tenant_id))).all())
    quarantined = dict((await db.execute(select(Project.tenant_id, func.count()).join(Task, Task.project_id == Project.id)
                                         .where(Task.status == "QUARANTINED").group_by(Project.tenant_id))).all())
    tenants = (await db.execute(select(Tenant.id, Tenant.name).where(Tenant.is_active.is_(True)).limit(60))).all()
    health = []
    for tid, name in tenants:
        la = last.get(tid)
        health.append(f"{name}: son etkinlik {la.date().isoformat() if la else 'yok'}, karantinada adım {quarantined.get(tid, 0)}")
    parts += ["# Şirket sağlığı (yalnız işletim bilgisi)", _lines(health)]
    return "\n".join(parts)


# ---------------------------------------------------------------- destek erişimi
async def active_grant(db: AsyncSession, tenant_id) -> Optional[SupportAccessGrant]:
    return (await db.execute(select(SupportAccessGrant).where(
        SupportAccessGrant.tenant_id == tenant_id, SupportAccessGrant.revoked_at.is_(None), SupportAccessGrant.expires_at > now())
        .order_by(SupportAccessGrant.expires_at.desc()).limit(1))).scalar_one_or_none()


async def log_access(db: AsyncSession, grant: SupportAccessGrant, actor_id, action: str, detail: Optional[str] = None) -> None:
    db.add(SupportAccessLog(grant_id=grant.id, tenant_id=grant.tenant_id, actor_id=actor_id, action=action,
                            detail=(detail or None) and detail[:500]))
