"""
İSTEK #753 — Beyin AI öğrenme etiketleri (tasarım belgesi Bölüm 6, 16.11.2026 onaylı).

Beyin'in her yönlendirmesi #742 öğrenme kaydına (learning_records) yazılır; yeni bir kayıt sistemi kurulmaz. Etiketler ve neden
sınıfları aynıdır (DOGRU / YANLIS / BELIRSIZ; MODEL_HATASI / ORTAM / DEGERLENDIRICI / KAPSAM / BELIRSIZ). Ders yalnız
MODEL_HATASI'ndan çıkar; yöneticinin zevk tercihi Beyin'in hatası sayılmaz (RECAi nedeni sınıflar, yönetici düzeltebilir).

Kaydedilen etkileşimler:
  BRAIN_DISCOVERY  Keşif soruları ve yanıtları — tanım belgesi onaylanınca; hangi soru yanıtlandı/belgeye girdi
  BRAIN_PLAN       Plan önerisi — onaylanan plan DOGRU örnek; yönetici önerilen planı belirgin değiştirdiyse ya da geri bildirimle
                   yeniden istediyse önerilen sürüm YANLIS kaydı olur ve onaylanan planla eşlenir (tercih çifti)
  BRAIN_RESEARCH   Web araştırması — yöneticinin tek tıkla faydalı / kısmen / faydasız değerlendirmesi ve maliyet
  BRAIN_OUTCOME    Proje sonucu — teslim edilen ↔ tanım belgesi uyumu (#752 kapsam raporu), atlanan teslimatlar; eksikle kabul
                   edilen projede onaylı plan kaydı sonradan BELIRSIZ'e çekilir (ilk etiket sonuçla güncellenir)

Öğrenmenin üç katmanı: şirket hafızası (dersler kurumsal aday olarak yönetici onayına düşer), sektör paketi önerileri
(şirketler arası, k-anonim — sector_pack_suggestions), RECAi eğitim verisi (izinli şirketlerin maskeli kayıtları, #743).
Kayıt tutma iş akışını asla durdurmaz (hata yalnız günlüğe yazılır).
"""
import json
import logging
import re
import uuid
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import LearningRecord, Project, Tenant

logger = logging.getLogger("recorion.brain_learning")

SOURCES = ("BRAIN_DISCOVERY", "BRAIN_PLAN", "BRAIN_RESEARCH", "BRAIN_OUTCOME")
JOB_TITLE = "Beyin AI"
SMALL_CHANGE = 0.2  # bu oranın altındaki plan değişikliği "olduğu gibi kabul" sayılır
RATINGS = {"USEFUL": ("DOGRU", "Faydalı"), "PARTIAL": ("BELIRSIZ", "Kısmen faydalı"), "USELESS": ("YANLIS", "Faydasız")}


def _norm(title: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^\wçğıöşü ]", " ", (title or "").casefold())).strip()


def brief_text(project: Project) -> str:
    parts = [f"Beyin AI · {'Case' if project.kind == 'CASE' else 'Proje'}: {project.name}"]
    if project.description:
        parts.append(f"Açıklama: {project.description[:2000]}")
    parts.append(f"İsterler (yöneticinin brifi):\n{(project.requirements or '-')[:5000]}")
    return "\n".join(parts)


def plan_text(plan: Dict[str, Any]) -> str:
    lines = [f"Özet: {plan.get('summary') or '-'}"]
    for i, s in enumerate(plan.get("steps") or [], 1):
        extra = " · ".join(x for x in (f"teslimat: {s['deliverable']}" if s.get("deliverable") else "",
                                       f"doğrulama ({s.get('verification_type') or '-'}): {s['verification']}" if s.get("verification") else "",
                                       f"{s.get('estimated_days', 1)} gün") if x)
        lines.append(f"{i}. {s.get('title')}" + (f" — {extra}" if extra else ""))
        if s.get("acceptance_criteria"):
            lines.append(f"   Kabul ölçütü: {s['acceptance_criteria']}")
    return "\n".join(lines)


def plan_snapshot(plan: Dict[str, Any]) -> Dict[str, Any]:
    """Beyin'in önerdiği planın değişmez kopyası (yönetici düzenlese de karşılaştırma bununla yapılır)."""
    keys = ("key", "title", "agent_id", "assignee_human_id", "deliverable", "verification", "verification_type", "estimated_days",
            "acceptance_criteria", "depends_on")
    return {"summary": plan.get("summary"), "steps": [{k: s.get(k) for k in keys} for s in plan.get("steps") or []],
            "model_code": plan.get("model_code"), "generated_at": plan.get("generated_at")}


def plan_diff(suggested: Dict[str, Any], final: Dict[str, Any]) -> Dict[str, Any]:
    """Önerilen ↔ onaylanan plan farkı: eklenen, çıkarılan, değiştirilen adımlar ve değişim oranı (0–1)."""
    a = {_norm(s.get("title")): s for s in suggested.get("steps") or []}
    b = {_norm(s.get("title")): s for s in final.get("steps") or []}
    added = [b[k].get("title") for k in b if k not in a]
    removed = [a[k].get("title") for k in a if k not in b]
    fields = ("agent_id", "assignee_human_id", "deliverable", "verification", "verification_type", "estimated_days")
    changed = [b[k].get("title") for k in b if k in a and any((a[k].get(f) or None) != (b[k].get(f) or None) for f in fields)]
    base = max(len(a), len(b), 1)
    ratio = min(1.0, (len(added) + len(removed) + 0.5 * len(changed)) / base)
    verdict = "KABUL" if ratio <= SMALL_CHANGE else "DEGISTIRILEREK_KABUL"
    return {"added": added, "removed": removed, "changed": changed, "ratio": round(ratio, 2), "verdict": verdict}


async def _sector(db: AsyncSession, tenant_id) -> Optional[str]:
    tenant = await db.get(Tenant, tenant_id)
    sectors = (tenant.sectors or []) if tenant else []
    s = ", ".join(str(x.get("name") if isinstance(x, dict) else x) for x in sectors[:3])
    return s[:120] or None


async def capture(project: Project, source: str, label: str, *, task_input: str, output: Optional[str] = None,
                  feedback: Optional[str] = None, decided_by=None, data: Optional[Dict[str, Any]] = None,
                  lesson: bool = False, pair_id=None) -> Optional[str]:
    """Beyin kaydı — KENDİ oturumunda: hata çağıranın işlemini geri almaz. Dönen: kayıt kimliği veya None."""
    from app.db.session import AsyncSessionLocal
    from app.services import learning_records as lr

    if (project.settings or {}).get("brain_bench"):  # #754: deneme setinde yöneticiyi RECAi oynar → eğitim verisi olmaz
        return None
    try:
        async with AsyncSessionLocal() as s:
            rec = LearningRecord(tenant_id=project.tenant_id, project_id=project.id, agent_id=None,
                                 decided_by_actor_id=decided_by and uuid.UUID(str(decided_by)), source=source, label=label,
                                 task_input=lr._clip(task_input, lr.MAX_INPUT), output=lr._clip(output, lr.MAX_OUTPUT),
                                 feedback=lr._clip(feedback, 4000), data=data or {}, sector=await _sector(s, project.tenant_id),
                                 job_title=JOB_TITLE, pair_id=pair_id and uuid.UUID(str(pair_id)),
                                 lesson_status="PENDING" if lesson else "SKIPPED")
            s.add(rec)
            await s.commit()
            if lesson:
                lr.spawn_lesson(rec.id)
            return str(rec.id)
    except Exception:
        logger.exception("Beyin öğrenme kaydı yazılamadı (%s)", source)
        return None


# ---------------------------------------------------------------- keşif
async def on_charter_approved(project: Project, actor_id, d: Dict[str, Any], threshold: int) -> None:
    """Tanım belgesi onaylandı: sorulan her soru, yanıtlandı mı (belgeye girdi mi) bilgisiyle kaydedilir."""
    qa = [{"topic": x.get("topic"), "question": x.get("question"), "answered": bool((x.get("answer") or "").strip())}
          for r in d.get("rounds") or [] for x in r.get("qa") or []]
    unanswered = [{"topic": q.get("topic"), "question": q.get("text"), "answered": False} for q in d.get("pending") or []]
    asked = qa + unanswered
    useful = sum(1 for q in asked if q["answered"])
    score = int((d.get("maturity") or {}).get("score") or 0)
    label = "DOGRU" if score >= threshold else "BELIRSIZ"  # eşik altı onay: yönetici eksiklerle ilerledi
    qa_text = "\n".join(f"- [{x.get('topic')}] {x.get('question')} → {x.get('answer') or '(yanıtlanmadı)'}"
                        for r in d.get("rounds") or [] for x in r.get("qa") or [])
    await capture(project, "BRAIN_DISCOVERY", label, decided_by=actor_id,
                  task_input=brief_text(project) + ("\n\nKeşif soruları ve yanıtlar:\n" + qa_text if qa_text else ""),
                  output=json.dumps(d.get("charter") or {}, ensure_ascii=False),
                  feedback=d.get("approve_reason"),
                  data={"score": score, "rounds": len(d.get("rounds") or []), "asked": len(asked), "answered": useful,
                        "questions": asked[:60], "below_threshold": score < threshold})


# ---------------------------------------------------------------- plan
async def on_plan_resuggested(project: Project, previous: Dict[str, Any], feedback: Optional[str], actor_id=None) -> Optional[str]:
    """Yönetici geri bildirimle yeni plan istedi: önceki öneri reddedilmiş sayılır (neden RECAi'ce sınıflanır)."""
    sugg = previous.get("suggested")
    if not sugg or not (feedback or "").strip() or previous.get("approved"):
        return None
    return await capture(project, "BRAIN_PLAN", "YANLIS", decided_by=actor_id, task_input=brief_text(project),
                         output=plan_text(sugg), feedback=f"Yönetici yeni plan istedi: {feedback.strip()}",
                         data={"verdict": "RET", "model_code": sugg.get("model_code")}, lesson=True)


async def on_plan_approved(db: AsyncSession, project: Project, actor_id) -> None:
    """Onaylanan plan DOGRU örnek (yöneticinin son hâli); belirgin değiştirilmişse önerilen sürüm YANLIS olarak eşlenir."""
    plan = project.plan or {}
    sugg = plan.get("suggested")
    if not sugg:  # Beyin önermedi (elle yazılmış plan): Beyin öğrenmesi değil
        return
    diff = plan_diff(sugg, plan)
    from app.services import sector_packs

    try:
        pack, _ = await sector_packs.for_project(db, project, await db.get(Tenant, project.tenant_id))
    except Exception:
        pack = None
    pack_code = pack.code if pack is not None else None
    good = await capture(project, "BRAIN_PLAN", "DOGRU", decided_by=actor_id, task_input=brief_text(project), output=plan_text(plan),
                         feedback=None, data={**diff, "pack_code": pack_code, "model_code": sugg.get("model_code"),
                                              "steps": len(plan.get("steps") or [])})
    if good is None:
        return
    pairs = list(plan.get("rejected_records") or [])
    if diff["verdict"] != "KABUL":
        lines = [f"Yönetici planı onaylamadan önce %{int(diff['ratio'] * 100)} oranında değiştirdi."]
        for k, t in (("added", "Eklenen adımlar"), ("removed", "Çıkarılan adımlar"), ("changed", "Değiştirilen adımlar")):
            if diff[k]:
                lines.append(f"{t}: {', '.join(diff[k][:15])}")
        bad = await capture(project, "BRAIN_PLAN", "YANLIS", decided_by=actor_id, task_input=brief_text(project),
                            output=plan_text(sugg), feedback="\n".join(lines), data={**diff, "pack_code": pack_code}, lesson=True,
                            pair_id=good)
        if bad:
            pairs.append(bad)
    await _pair(pairs, good)


async def _pair(record_ids: List[str], good_id: str) -> None:
    from app.db.session import AsyncSessionLocal

    ids = [uuid.UUID(str(i)) for i in record_ids if i]
    if not ids:
        return
    try:
        async with AsyncSessionLocal() as s:
            for r in (await s.execute(select(LearningRecord).where(LearningRecord.id.in_(ids)))).scalars():
                r.pair_id = uuid.UUID(good_id)
            g = await s.get(LearningRecord, uuid.UUID(good_id))
            if g is not None:
                g.data = {**(g.data or {}), "pairs": len(ids)}
            await s.commit()
    except Exception:
        logger.exception("Plan tercih çifti bağlanamadı")


# ---------------------------------------------------------------- web araştırması
async def on_research_rated(project: Project, research, actor_id) -> None:
    """Yöneticinin tek tık değerlendirmesi; aynı araştırma yeniden değerlendirilirse kayıt güncellenir."""
    from app.db.session import AsyncSessionLocal

    label, text = RATINGS[research.rating]
    res = research.result or {}
    summary = res.get("summary") or ""
    findings = "\n".join(f"- {f.get('text')}" for f in (res.get("findings") or [])[:15] if isinstance(f, dict))
    data = {"research_id": str(research.id), "rating": research.rating, "depth": research.depth, "origin": research.origin,
            "spent_credits": float(research.spent_credits or 0), "sources": len(res.get("sources") or [])}
    try:
        async with AsyncSessionLocal() as s:
            old = (await s.execute(select(LearningRecord).where(LearningRecord.project_id == project.id,
                                                                LearningRecord.source == "BRAIN_RESEARCH",
                                                                LearningRecord.data["research_id"].astext == str(research.id))
                                   )).scalars().first()
            if old is not None:
                old.label, old.data, old.decided_by_actor_id = label, data, actor_id
                old.feedback = f"Yönetici değerlendirmesi: {text}"
                old.cause = old.cause if label == "YANLIS" else None
                await s.commit()
                return
    except Exception:
        logger.exception("Araştırma kaydı güncellenemedi")
        return
    await capture(project, "BRAIN_RESEARCH", label, decided_by=actor_id,
                  task_input=brief_text(project) + f"\n\nAraştırma sorusu: {research.masked_question or research.question}",
                  output=(summary + ("\n\nBulgular:\n" + findings if findings else ""))[:20000],
                  feedback=f"Yönetici değerlendirmesi: {text}", data=data, lesson=label == "YANLIS")


# ---------------------------------------------------------------- proje sonucu
async def on_project_completed(db: AsyncSession, project: Project, actor_id, summary: Optional[str]) -> None:
    """Kapanış: teslim edilen ↔ tanım belgesi uyumu. Eksikle kabulde onaylı plan kaydı sonradan BELIRSIZ'e çekilir."""
    from app.db.session import AsyncSessionLocal
    from app.services import discovery, verification

    cov = await verification.coverage(db, project)
    if not cov.get("total"):
        return
    rows = cov.get("rows") or []
    missing = [r.get("deliverable") or r.get("title") for r in rows if r.get("status") == "MISSING"]
    waived = [r.get("deliverable") or r.get("title") for r in rows if r.get("status") == "WAIVED"]
    charter = discovery.state(project).get("charter") or {}
    planned = [(d.get("name") if isinstance(d, dict) else str(d)) for d in charter.get("deliverables") or []]
    delivered = {_norm(r.get("deliverable") or r.get("title")) for r in rows if r.get("status") in ("VERIFIED", "WAIVED")}
    skipped = [p for p in planned if p and not any(_norm(p) in d or d in _norm(p) for d in delivered if d)]
    label = "DOGRU" if not missing and not waived else "BELIRSIZ"
    fb = [f"Kapsam: {cov.get('summary')}"]
    if missing:
        fb.append(f"Doğrulanmayan teslimatlar: {', '.join(missing[:15])}")
    if skipped:
        fb.append(f"Tanım belgesinde olup doğrulanmış teslimata dönüşmeyenler: {', '.join(skipped[:15])}")
    if summary:
        fb.append(f"Kapanış özeti: {summary[:1500]}")
    await capture(project, "BRAIN_OUTCOME", label, decided_by=actor_id, task_input=brief_text(project),
                  output=json.dumps({"charter_deliverables": planned, "coverage": cov.get("counts")}, ensure_ascii=False),
                  feedback="\n".join(fb), data={"counts": cov.get("counts"), "missing": missing[:30], "waived": waived[:30],
                                                "skipped_requirements": skipped[:30]})
    if label == "DOGRU":
        return
    try:  # sonradan ortaya çıkan sonuç ilk etiketi günceller (kabul edilen plan proje sonunda yetersiz kaldı)
        async with AsyncSessionLocal() as s:
            for r in (await s.execute(select(LearningRecord).where(LearningRecord.project_id == project.id,
                                                                   LearningRecord.source == "BRAIN_PLAN",
                                                                   LearningRecord.label == "DOGRU"))).scalars():
                r.label = "BELIRSIZ"
                r.data = {**(r.data or {}), "original_label": "DOGRU",
                          "relabel_reason": "Proje eksik doğrulanmış teslimatla kapandı: " + ", ".join((missing + waived)[:10])}
            await s.commit()
    except Exception:
        logger.exception("Plan kaydı sonuçla güncellenemedi")


# ---------------------------------------------------------------- sektör paketi önerileri (şirketler arası, k-anonim)
async def sector_pack_suggestions(db: AsyncSession, pack_code: str) -> Dict[str, Any]:
    """Yöneticilerin Beyin planına sık eklediği / çıkardığı adımlar. Yalnız en az k şirkette görülen ve tek şirketin payı
    sınırı aşmayan örüntüler gösterilir (#744); tekil kayıt ya da şirket adı verilmez. Merkez onayıyla pakete girer."""
    from app.services import reports

    priv = await reports.privacy(db)
    k_min, dom = priv["k_min"], priv["dominance_pct"]
    rows = (await db.execute(select(LearningRecord.tenant_id, LearningRecord.data).where(
        LearningRecord.source == "BRAIN_PLAN", LearningRecord.label.in_(("DOGRU", "BELIRSIZ")),
        LearningRecord.data["pack_code"].astext == pack_code))).all()
    out: Dict[str, List[Dict[str, Any]]] = {}
    hidden = 0
    for kind in ("added", "removed"):
        agg: Dict[str, Dict[str, Any]] = {}
        for tid, data in rows:
            for title in set((data or {}).get(kind) or []):
                key = _norm(title)
                if len(key) < 3:
                    continue
                a = agg.setdefault(key, {"title": title, "per": {}})
                a["per"][tid] = a["per"].get(tid, 0) + 1
        shown = []
        for a in agg.values():
            total = sum(a["per"].values())
            if len(a["per"]) < k_min or max(a["per"].values()) * 100 / total > dom:
                hidden += 1
                continue
            shown.append({"title": a["title"], "companies": len(a["per"]), "count": total})
        out[kind] = sorted(shown, key=lambda x: (-x["companies"], -x["count"]))[:30]
    return {"pack_code": pack_code, "plans": len(rows), "k_min": k_min, "dominance_pct": dom, "hidden": hidden, **out}


def lesson_scope(rec: LearningRecord, proposed: str) -> str:
    """Beyin'in kendine ait AI personel hafızası yok: dersleri şirket hafızasına aday (kurumsal, yönetici onayı) olarak düşer."""
    return "GLOBAL" if rec.agent_id is None else proposed


def is_brain(rec: LearningRecord) -> bool:
    return (rec.source or "").startswith("BRAIN_")
