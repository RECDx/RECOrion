"""
İSTEK #742 — Öğrenme kayıtları (Şirket Yönetimi › Öğrenme).

Şirket içeriğidir (KVKK): süper admin göremez (access_policy content=True).
- GET  /company/{tid}/learning/summary              sayılar: etiket, neden, kaynak; kaydedilen ders; onay bekleyen kurumsal ders
- GET  /company/{tid}/learning/records              liste (filtre: label, cause, source, agent_id)
- GET  /company/{tid}/learning/records/{id}         kayıt ayrıntısı (girdi, çıktı)
- PUT  /company/{tid}/learning/records/{id}/cause   yönetici nedeni düzeltir; AI hatası değilse çıkan ders hafızadan geri alınır
"""
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import CurrentUser, get_current_user
from app.db.models import Actor, LearningRecord, MemoryItem
from app.db.session import get_db
from app.services import learning_records as lr

router = APIRouter(prefix="/company", tags=["Öğrenme kayıtları (#742)"])


async def _names(db: AsyncSession, ids) -> dict:
    ids = {i for i in ids if i}
    return dict((await db.execute(select(Actor.id, Actor.display_name).where(Actor.id.in_(ids)))).all()) if ids else {}


@router.get("/{tenant_id}/learning/summary")
async def learning_summary(tenant_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    async def grouped(col):
        rows = (await db.execute(select(col, func.count()).where(LearningRecord.tenant_id == tenant_id).group_by(col))).all()
        return {str(k): int(v) for k, v in rows if k is not None}

    pending = (await db.execute(select(func.count()).select_from(MemoryItem).where(
        MemoryItem.tenant_id == tenant_id, MemoryItem.scope == "GLOBAL", MemoryItem.status == "CANDIDATE"))).scalar()
    pairs = (await db.execute(select(func.count()).select_from(LearningRecord).where(
        LearningRecord.tenant_id == tenant_id, LearningRecord.pair_id.isnot(None)))).scalar()
    return {"labels": await grouped(LearningRecord.label), "causes": await grouped(LearningRecord.cause),
            "sources": await grouped(LearningRecord.source), "lessons": await grouped(LearningRecord.lesson_status),
            "pairs": int(pairs or 0), "pending_corporate": int(pending or 0),
            "label_text": lr.LABEL_TR, "cause_text": lr.CAUSE_TR, "source_text": lr.SOURCE_TR}


@router.get("/{tenant_id}/learning/records")
async def learning_records(tenant_id: uuid.UUID, label: Optional[str] = None, cause: Optional[str] = None,
                           source: Optional[str] = None, agent_id: Optional[uuid.UUID] = None,
                           limit: int = Query(100, ge=1, le=500), db: AsyncSession = Depends(get_db)):
    q = select(LearningRecord).where(LearningRecord.tenant_id == tenant_id)
    if label:
        q = q.where(LearningRecord.label == label)
    if cause:
        q = q.where(LearningRecord.cause == cause)
    if source:
        q = q.where(LearningRecord.source == source)
    if agent_id:
        q = q.where(LearningRecord.agent_id == agent_id)
    rows = (await db.execute(q.order_by(LearningRecord.created_at.desc()).limit(limit))).scalars().all()
    names = await _names(db, [r.agent_id for r in rows])
    return [lr.out(r, names) for r in rows]


async def _get(db: AsyncSession, tenant_id: uuid.UUID, record_id: uuid.UUID) -> LearningRecord:
    rec = await db.get(LearningRecord, record_id)
    if rec is None or rec.tenant_id != tenant_id:
        raise HTTPException(status_code=404, detail="Öğrenme kaydı bulunamadı.")
    return rec


@router.get("/{tenant_id}/learning/records/{record_id}")
async def learning_record(tenant_id: uuid.UUID, record_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    rec = await _get(db, tenant_id, record_id)
    return lr.out(rec, await _names(db, [rec.agent_id]), full=True)


class CauseIn(BaseModel):
    cause: str = Field(..., pattern="^(MODEL_HATASI|ORTAM|DEGERLENDIRICI|KAPSAM|BELIRSIZ)$")
    note: Optional[str] = Field(None, max_length=1000)


@router.put("/{tenant_id}/learning/records/{record_id}/cause")
async def set_learning_cause(tenant_id: uuid.UUID, record_id: uuid.UUID, payload: CauseIn,
                             user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    rec = await _get(db, tenant_id, record_id)
    try:
        rec = await lr.set_cause(db, rec, payload.cause, user.actor_id, payload.note)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    return lr.out(rec, await _names(db, [rec.agent_id]))


# ---------------------------------------------------------------- İSTEK #743: RECAi geliştirmeye katkı izni (şirket kartı)
CONSENT_TEXT = ("RECAi, RECDx'in yerli ve milli yapay zekâ modelidir. Bu izin açıkken AI personelinizin onaylanan ve reddedilen "
                "işlerinden çıkan örnekler, kişisel ve şirkete özgü bilgiler (ad, kimlik/vergi no, IBAN, telefon, e-posta, adres, "
                "firma adı, tutar) geri çevrilemez biçimde maskelendikten sonra RECAi'nin geliştirilmesinde kullanılır. "
                "İzni istediğiniz an kapatabilirsiniz; kapatınca verileriniz sonraki eğitim setlerine girmez, ancak önceden eğitilmiş "
                "bir modelden geri çıkarılamaz. Şirketinizin hafızası ve AI personelinizin öğrenmesi izinden bağımsız çalışmaya devam eder.")


@router.get("/{tenant_id}/recai-consent")
async def get_recai_consent(tenant_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    from app.db.models import Tenant
    t = await db.get(Tenant, tenant_id)
    if t is None:
        raise HTTPException(status_code=404, detail="Şirket bulunamadı.")
    by = await db.get(Actor, t.recai_training_consent_by) if t.recai_training_consent_by else None
    return {"consent": bool(t.recai_training_consent), "changed_at": t.recai_training_consent_at,
            "changed_by": by.display_name if by else None, "text": CONSENT_TEXT}


class ConsentIn(BaseModel):
    consent: bool


@router.put("/{tenant_id}/recai-consent")
async def set_recai_consent(tenant_id: uuid.UUID, payload: ConsentIn, user: CurrentUser = Depends(get_current_user),
                            db: AsyncSession = Depends(get_db)):
    """İzin müşterinin kararıdır: RECDx personeli değiştiremez."""
    from datetime import datetime, timezone
    from app.db.models import Tenant
    if user.is_platform_staff or user.tenant_id != tenant_id:
        raise HTTPException(status_code=403, detail="Bu izni yalnızca şirketin kendi yöneticisi değiştirebilir.")
    t = await db.get(Tenant, tenant_id)
    t.recai_training_consent = payload.consent
    t.recai_training_consent_at, t.recai_training_consent_by = datetime.now(timezone.utc), user.actor_id
    await db.commit()
    return await get_recai_consent(tenant_id, db)


# ---------------------------------------------------------------- İSTEK #743: Merkez — RECAi veri seti (yalnız sayılar)
system_router = APIRouter(prefix="/system/recai-training", tags=["RECAi eğitim verisi (#743)"])


@system_router.get("/summary")
async def recai_training_summary(db: AsyncSession = Depends(get_db)):
    from app.db.models import TrainingDataset
    from app.services import training_data as td
    rows = (await db.execute(select(TrainingDataset).order_by(TrainingDataset.version.desc()).limit(20))).scalars().all()
    return {"eligible": await td.eligible_counts(db), "datasets": [td.out(d) for d in rows],
            "delivery": "EVREN eğitim API'si henüz yok; veri setleri RECOrion deposunda bekler (EVREN görüşmesinden sonra teslim)."}


class BuildIn(BaseModel):
    note: Optional[str] = Field(None, max_length=500)


@system_router.post("/datasets", status_code=201)
async def build_recai_dataset(payload: BuildIn, user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    from app.services import training_data as td
    return td.out(await td.build(db, user.actor_id, payload.note))
