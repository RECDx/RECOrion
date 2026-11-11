"""
İSTEK #742 — Tek etiketli öğrenme kaydı: AI personel HEM sohbetten HEM iş akışından öğrenir. Sektörden bağımsızdır.

Karar kaydı ve gerekçeler: Claude/senaryo/karar_ogrenme_recai.md (11.11.2026). Özet:
- Her karar bir kayıt olur: onay (DOGRU), ret/kontrol reti (YANLIS), test koşusu, aktarım onayı/reddi/geri alınması, iptal (BELIRSIZ),
  sohbette kullanıcının söylediği kural (DOGRU). Yazılım testi sinyallerden yalnız biridir.
- Yanlışlar ATILMAZ: etiketlenir. Ret kaydı, sonradan onaylanan sürüme pair_id ile bağlanır (tercih çifti: "şu kötü, bu iyi").
- Neden sınıfı yanlış etiket riskine karşıdır: yalnız MODEL_HATASI olumsuz ders/örnek olur. ORTAM (altyapı/test ortamı),
  DEGERLENDIRICI (haksız/okunamayan değerlendirme), KAPSAM (iş değişti/iptal) ayrı tutulur. Sınıfı önce kural, sonra RECAi önerir;
  şirket yöneticisi düzeltebilir (cause_by=HUMAN).
- Aynı kayıt iki yere gider: ders → hafıza (AGENT doğrudan; GLOBAL kurumsal aday, yönetici onayı) ve RECAi veri seti (#743).
- Hafıza RECOrion'da kalır (bilgi); model eğitimi (beceri) EVREN'de. İzni kapatan şirketin hafızası çalışmaya devam eder.

Ders çıkarma arka planda (LEARNING_LESSONS_ENABLED), llm_gateway üzerinden, meşgul modelde yedek modelle. Kayıt tutma hiçbir zaman
iş akışını durdurmaz (hata yalnız günlüğe yazılır).
"""
import asyncio
import json
import logging
import re
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Actor, LearningRecord, MemoryItem, Project, Task, Tenant

logger = logging.getLogger("recorion.learning")

LABELS = ("DOGRU", "YANLIS", "BELIRSIZ")
CAUSES = ("MODEL_HATASI", "ORTAM", "DEGERLENDIRICI", "KAPSAM", "BELIRSIZ")
LABEL_TR = {"DOGRU": "Doğru", "YANLIS": "Yanlış", "BELIRSIZ": "Belirsiz"}
CAUSE_TR = {"MODEL_HATASI": "AI personelin hatası", "ORTAM": "Ortam / altyapı", "DEGERLENDIRICI": "Değerlendirme hatası",
            "KAPSAM": "Kapsam değişikliği", "BELIRSIZ": "Belirsiz"}
SOURCE_TR = {"APPROVAL": "Onay", "REJECTION": "Yönetici reti", "REVIEW": "Kontrol personeli reti", "TEST_RUN": "Test koşusu",
             "TRANSFER": "Sisteme aktarım", "CHAT": "Sohbet", "CANCEL": "İptal"}
MAX_INPUT, MAX_OUTPUT = 8000, 20000

_bg: set = set()


def now() -> datetime:
    return datetime.now(timezone.utc)


def _clip(text: Optional[str], n: int) -> Optional[str]:
    if not text:
        return None
    return text if len(text) <= n else text[:n] + "\n…(kısaltıldı)"


def task_input_text(task: Task) -> str:
    parts = [f"Adım: {task.title}"]
    if task.description:
        parts.append(f"Açıklama: {task.description}")
    if task.acceptance_criteria:
        parts.append(f"Kabul ölçütü: {task.acceptance_criteria}")
    return "\n".join(parts)


async def _context(db: AsyncSession, tenant_id, agent_id) -> Dict[str, Optional[str]]:
    tenant = await db.get(Tenant, tenant_id)
    agent = await db.get(Actor, agent_id) if agent_id else None
    sectors = (tenant.sectors or []) if tenant else []
    sector = ", ".join(str(s.get("name") if isinstance(s, dict) else s) for s in sectors[:3]) if sectors else None
    return {"sector": (sector or None) and sector[:120], "job_title": agent.role[:128] if agent and agent.role else None}


async def _ai_agent(db: AsyncSession, actor_id) -> Optional[Actor]:
    a = await db.get(Actor, actor_id) if actor_id else None
    return a if a is not None and a.actor_type == "AI_AGENT" else None


async def capture_task(task: Task, project: Project, source: str, label: str, **kw) -> Optional[str]:
    """İş adımı kararını kayda geçirir — KENDİ oturumunda: kayıt hatası çağıranın işlemini geri almaz, iş akışını durdurmaz.
    Yalnız AI personelin işi kaydedilir (insanın işi AI öğrenmesi değildir). Dönen: kayıt kimliği veya None."""
    from app.db.session import AsyncSessionLocal

    task_id, project_id = task.id, project.id
    try:
        async with AsyncSessionLocal() as s:
            t, p = await s.get(Task, task_id), await s.get(Project, project_id)
            rec = await _capture(s, t, p, source, label, **kw) if t is not None and p is not None else None
            return str(rec.id) if rec is not None else None
    except Exception:  # öğrenme yardımcıdır; iş akışını asla durdurmaz
        logger.exception("Öğrenme kaydı yazılamadı")
        return None


async def _capture(db: AsyncSession, task: Task, project: Project, source: str, label: str, *, decided_by=None,
                   feedback: Optional[str] = None, cause: Optional[str] = None, cause_by: Optional[str] = None,
                   output: Optional[str] = None, output_ref: Optional[str] = None, need_output: bool = False,
                   data: Optional[Dict[str, Any]] = None, lesson: bool = True) -> Optional[LearningRecord]:
    agent = await _ai_agent(db, task.assignee_actor_id)
    if agent is None:
        return None
    if output is None:
        from app.services import agent_work
        art = await agent_work.latest_artifact(db, task.id)
        if art is not None:
            output = await agent_work.artifact_text(art, MAX_OUTPUT)
            output_ref = output_ref or f"artifact:{art.id}:v{art.version}"
    if need_output and not output:
        return None
    ctx = await _context(db, project.tenant_id, agent.id)
    rec = LearningRecord(tenant_id=project.tenant_id, project_id=project.id, task_id=task.id, agent_id=agent.id,
                         decided_by_actor_id=decided_by and uuid.UUID(str(decided_by)), source=source, label=label,
                         cause=cause if label != "DOGRU" else None, cause_by=cause_by if label != "DOGRU" else None,
                         task_input=_clip(task_input_text(task), MAX_INPUT), output=_clip(output, MAX_OUTPUT),
                         output_ref=output_ref, feedback=_clip(feedback, 4000), data=data or {}, **ctx,
                         lesson_status="PENDING" if lesson else "SKIPPED")
    db.add(rec)
    await db.flush()
    if label == "DOGRU":  # bu adımın eşlenmemiş yanlış sürümleri bu doğru sürüme bağlanır (tercih çifti)
        prev = (await db.execute(select(LearningRecord).where(LearningRecord.task_id == task.id, LearningRecord.label == "YANLIS",
                                                              LearningRecord.pair_id.is_(None), LearningRecord.id != rec.id))).scalars().all()
        for p in prev:
            p.pair_id = rec.id
        rec.data = {**(rec.data or {}), "pairs": len(prev)}
        if not prev and not (feedback or "").strip():
            rec.lesson_status = "SKIPPED"  # sıradan onay: ders çıkarılmaz (gürültü ve maliyet), veri setinde örnek olarak kalır
    await db.commit()
    if rec.lesson_status == "PENDING":
        spawn_lesson(rec.id)
    return rec


async def capture_chat(db: AsyncSession, tenant_id, agent_id, task_id, fact: str, memory_id, scope: str) -> None:
    """Sohbetten öğrenilen kural da aynı kayda girer (kullanıcının söylediği kural: DOGRU; ders zaten hafızada)."""
    try:
        task = await db.get(Task, task_id) if task_id else None
        ctx = await _context(db, tenant_id, agent_id)
        db.add(LearningRecord(tenant_id=tenant_id, project_id=task.project_id if task else None, task_id=task_id, agent_id=agent_id,
                              source="CHAT", label="DOGRU", lesson=fact, lesson_scope=scope, lesson_memory_id=memory_id,
                              lesson_status="SAVED", task_input=_clip(task_input_text(task), MAX_INPUT) if task else None, **ctx))
        await db.flush()
    except Exception:
        logger.exception("Sohbet öğrenme kaydı yazılamadı")


# ---------------------------------------------------------------- neden sınıfı (kural)
ENV_HINTS = re.compile(r"zaman aşımı|timeout|bağlantı|connection|docker|kurulum başarısız|install|disk|bellek|memory|sandbox|"
                       r"ortam|erişilemedi|unreachable|503|502|504", re.I)


def test_cause(run_status: str, error: Optional[str], report: str = "") -> str:
    """Test koşusu kaldığında ilk tahmin: koşu ERROR ya da altyapı belirtisi → ORTAM; değilse MODEL_HATASI (RECAi inceler)."""
    if run_status == "ERROR" or (error and ENV_HINTS.search(error)):
        return "ORTAM"
    return "MODEL_HATASI"


# ---------------------------------------------------------------- ders çıkarma (RECAi)
LESSON_SYSTEM = """Sen RECOrion'un öğrenme motoru RECAi'sin. Bir AI personelin iş adımı kararını inceler, (1) olumsuz kararın
NEDENİNİ sınıflandırır, (2) personelin gelecekte benzer işlerde kullanacağı kısa ve genel bir DERS çıkarırsın.
Her sektörden iş olabilir (sağlık, turizm, üretim, finans, hukuk, yazılım…).

Neden sınıfları (yalnız etiket YANLIS ise):
- MODEL_HATASI: personelin çıktısı gerçekten eksik/yanlış (kabul ölçütünü karşılamıyor, istenmeyeni yapmış, uydurmuş).
- ORTAM: altyapı/test ortamı/bağlantı sorunu; çıktının kalitesiyle ilgisi yok.
- DEGERLENDIRICI: ret haksız ya da gerekçesiz; çıktı aslında istenene uygun.
- KAPSAM: iş tanımı sonradan değişmiş; çıktı eski isteğe göre doğruydu.
- BELIRSIZ: karar vermeye yetecek bilgi yok.

Ders kuralları:
- Yalnız neden MODEL_HATASI ise (ya da etiket DOGRU ve önceki yanlış sürümden ders çıkıyorsa) ders yaz; diğerlerinde "ders": "".
- Ders genel ve tekrar kullanılabilir olmalı ("Bunu yapma; doğrusu şu" / "Böyle yap"). Kişi adı, müşteri adı, tutar, tarih,
  proje kod adı YAZMA.
- kapsam: AGENT (bu personelin çalışma biçimi) ya da GLOBAL (şirketin tüm işlerinde geçerli kural). Emin değilsen AGENT.
Yanıtı YALNIZCA JSON ver: {"neden": "...", "neden_gerekce": "...", "ders": "...", "kapsam": "AGENT"}"""


def _json(text: str) -> Dict[str, Any]:
    m = re.search(r"\{.*\}", text or "", re.S)
    try:
        return json.loads(m.group(0)) if m else {}
    except json.JSONDecodeError:
        return {}


async def _lesson_prompt(db: AsyncSession, rec: LearningRecord) -> str:
    parts = [f"Kaynak: {SOURCE_TR.get(rec.source, rec.source)} · Etiket: {rec.label}"
             + (f" · Kural önerisi neden: {rec.cause}" if rec.cause else ""),
             f"Ünvan: {rec.job_title or '-'} · Sektör: {rec.sector or '-'}", "", rec.task_input or ""]
    if rec.label == "DOGRU" and rec.id:
        wrong = (await db.execute(select(LearningRecord).where(LearningRecord.pair_id == rec.id)
                                  .order_by(LearningRecord.created_at))).scalars().all()
        for w in wrong[-2:]:
            parts += ["", f"ÖNCEKİ REDDEDİLEN SÜRÜM ({SOURCE_TR.get(w.source, w.source)}) GEREKÇESİ:", w.feedback or "-",
                      "ÖNCEKİ SÜRÜM (kısaltılmış):", _clip(w.output, 3000) or "-"]
    parts += ["", "KARAR GEREKÇESİ / GERİ BİLDİRİM:", rec.feedback or "-", "", "ÇIKTI (kısaltılmış):", _clip(rec.output, 6000) or "-"]
    return "\n".join(parts)


async def _save_lesson(db: AsyncSession, rec: LearningRecord, lesson: str, scope: str) -> MemoryItem:
    from app.services.collective_memory import collective_memory

    meta = {"source_type": "workflow_learning", "learning_record_id": str(rec.id), "task_id": str(rec.task_id) if rec.task_id else None,
            "label": rec.label, "cause": rec.cause, "extracted_from": rec.source}
    if scope == "GLOBAL":  # kurumsal ders tüm personeli etkiler → şirket yöneticisinin onayına düşer
        mem = MemoryItem(tenant_id=rec.tenant_id, scope="GLOBAL", agent_id=None, source_reference=f"LEARNING_{rec.id}",
                         content=lesson, metadata_json={**meta, "proposed_by_agent_id": str(rec.agent_id) if rec.agent_id else None},
                         status="CANDIDATE", confidence_score=0.8)
        db.add(mem)
        await db.flush()
        return mem
    mem = MemoryItem(tenant_id=rec.tenant_id, scope="AGENT", agent_id=rec.agent_id, source_reference=f"LEARNING_{rec.id}",
                     content=lesson, metadata_json=meta, status="APPROVED", confidence_score=0.85)
    db.add(mem)
    await db.flush()
    try:
        point = await collective_memory.add_memory(tenant_id=str(rec.tenant_id), scope="AGENT", agent_id=str(rec.agent_id),
                                                   source_reference=f"LEARNING_{rec.id}", content=lesson,
                                                   metadata={**meta, "memory_item_id": str(mem.id)})
        mem.qdrant_point_id = uuid.UUID(str(point["point_id"]))
    except Exception as exc:
        logger.warning("Ders vektörlenemedi: %s", exc)
    return mem


async def extract_lesson(db: AsyncSession, record_id) -> LearningRecord:
    """Kaydın nedenini RECAi ile sınıflar ve (gerekiyorsa) dersi hafızaya yazar. İnsanın verdiği neden (HUMAN) korunur."""
    from app.services import llm_gateway
    from app.services.llm_gateway import LLMContext

    rec = await db.get(LearningRecord, uuid.UUID(str(record_id)))
    if rec is None or rec.lesson_status not in ("PENDING", "FAILED"):
        return rec
    try:
        res = await llm_gateway.chat(LLMContext(tenant_id=rec.tenant_id, purpose="LEARNING", actor_id=rec.agent_id,
                                                task_id=rec.task_id, project_id=rec.project_id),
                                     [{"role": "system", "content": LESSON_SYSTEM},
                                      {"role": "user", "content": await _lesson_prompt(db, rec)}],
                                     temperature=0.2, max_tokens=1200, timeout=150, fallback=True)
    except Exception as exc:
        rec.lesson_status, rec.data = "FAILED", {**(rec.data or {}), "lesson_error": str(exc)[:300]}
        await db.commit()
        return rec
    d = _json(res.content)
    if rec.label == "YANLIS" and rec.cause_by != "HUMAN":
        cause = str(d.get("neden") or "").upper()
        if cause in CAUSES and not (rec.cause_by == "SYSTEM" and rec.cause == "ORTAM"):  # kuralın ORTAM tespiti korunur
            rec.cause, rec.cause_by = cause, "AI"
        rec.cause_reason = _clip(str(d.get("neden_gerekce") or "").strip(), 1000) or rec.cause_reason
    lesson = str(d.get("ders") or "").strip()
    usable = lesson and len(lesson) >= 15 and (rec.label == "DOGRU" or rec.cause == "MODEL_HATASI")
    if not usable:
        rec.lesson_status = "NONE"
        await db.commit()
        return rec
    scope = "GLOBAL" if str(d.get("kapsam") or "").upper() == "GLOBAL" else "AGENT"
    mem = await _save_lesson(db, rec, lesson[:1500], scope)
    rec.lesson, rec.lesson_scope, rec.lesson_memory_id, rec.lesson_status = lesson[:1500], scope, mem.id, "SAVED"
    await db.commit()
    return rec


async def _lesson_later(record_id) -> None:
    from app.db.session import AsyncSessionLocal

    try:
        async with AsyncSessionLocal() as s:
            await extract_lesson(s, record_id)
    except Exception:
        logger.exception("Ders çıkarılamadı")


def spawn_lesson(record_id) -> None:
    from app.config import settings

    if not settings.LEARNING_LESSONS_ENABLED:
        return
    try:
        t = asyncio.get_running_loop().create_task(_lesson_later(record_id))
    except RuntimeError:
        return
    _bg.add(t)
    t.add_done_callback(_bg.discard)


# ---------------------------------------------------------------- yönetici düzeltmesi
async def set_cause(db: AsyncSession, rec: LearningRecord, cause: str, actor_id, note: Optional[str] = None) -> LearningRecord:
    """Şirket yöneticisi nedeni düzeltir. MODEL_HATASI değilse bu kayıttan çıkan ders hafızadan geri alınır (yanlış ders öğrenilmesin)."""
    from app.services.collective_memory import collective_memory

    if rec.label != "YANLIS":
        raise ValueError("Yalnız 'Yanlış' etiketli kayıtların nedeni değiştirilebilir.")
    if cause not in CAUSES:
        raise ValueError("Geçersiz neden.")
    rec.cause, rec.cause_by, rec.reviewed_by_actor_id, rec.reviewed_at = cause, "HUMAN", actor_id, now()
    if note:
        rec.cause_reason = _clip(note.strip(), 1000)
    if cause != "MODEL_HATASI" and rec.lesson_memory_id:
        mem = await db.get(MemoryItem, rec.lesson_memory_id)
        if mem is not None and mem.status != "REVOKED":
            if mem.qdrant_point_id:
                try:
                    await collective_memory.delete_points([str(mem.qdrant_point_id)])
                except Exception as exc:
                    logger.warning("Ders vektörü silinemedi: %s", exc)
            mem.status, mem.review_note = "REVOKED", "Öğrenme kaydının nedeni düzeltildi (AI personelin hatası değil)."
            mem.reviewed_by_actor_id, mem.reviewed_at = actor_id, now()
        rec.lesson_status = "NONE"
    elif cause == "MODEL_HATASI" and rec.lesson_status in ("NONE", "FAILED") and not rec.lesson_memory_id:
        rec.lesson_status = "PENDING"
        await db.commit()
        spawn_lesson(rec.id)
        return rec
    await db.commit()
    return rec


def out(rec: LearningRecord, names: Optional[Dict] = None, full: bool = False) -> Dict[str, Any]:
    names = names or {}
    d = {"id": str(rec.id), "source": rec.source, "source_label": SOURCE_TR.get(rec.source, rec.source),
         "label": rec.label, "label_text": LABEL_TR.get(rec.label, rec.label), "cause": rec.cause,
         "cause_text": CAUSE_TR.get(rec.cause) if rec.cause else None, "cause_by": rec.cause_by, "cause_reason": rec.cause_reason,
         "project_id": str(rec.project_id) if rec.project_id else None, "task_id": str(rec.task_id) if rec.task_id else None,
         "agent_id": str(rec.agent_id) if rec.agent_id else None, "agent_name": names.get(rec.agent_id),
         "job_title": rec.job_title, "task_title": (rec.task_input or "").split("\n", 1)[0].removeprefix("Adım: ") or None,
         "feedback": rec.feedback, "lesson": rec.lesson, "lesson_scope": rec.lesson_scope, "lesson_status": rec.lesson_status,
         "paired": bool(rec.pair_id) or bool((rec.data or {}).get("pairs")), "created_at": rec.created_at}
    if full:
        d.update({"task_input": rec.task_input, "output": rec.output, "data": rec.data})
    return d
