from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from app.db.session import get_db
from app.db.models import LLMModel, LLMProvider
from pydantic import BaseModel
import uuid
from datetime import date, datetime, timezone

router = APIRouter(prefix="/models", tags=["LLM Models"])


class ModelResponse(BaseModel):
    id: uuid.UUID
    model_code: str
    display_name: str
    model_type: str
    context_window: int
    effort_coefficient: float
    status: str
    evren_task: Optional[str] = None
    modalities: Optional[List[str]] = None
    max_output_tokens: Optional[int] = None
    prompt_token_price: Optional[float] = None
    completion_token_price: Optional[float] = None
    pricing_currency: Optional[str] = None
    free_until: Optional[date] = None
    last_synced_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ModelCreate(BaseModel):
    model_code: str
    display_name: str
    model_type: str = "CHAT"
    context_window: int = 131072
    effort_coefficient: float = 1.0
    status: str = "ACTIVE"
    provider_id: Optional[uuid.UUID] = None

class ModelUpdate(BaseModel):
    display_name: str
    model_type: str
    context_window: int
    effort_coefficient: float
    status: str

@router.get("", response_model=List[ModelResponse])
@router.get("/", response_model=List[ModelResponse])
async def list_models(
    model_type: Optional[str] = Query(None, description="Filtre: CHAT, CODE, VISION, EMBEDDING, RERANKER, OCR, AUDIO"),
    db: AsyncSession = Depends(get_db)
):
    """
    Sistemde kayıtlı EVREN modellerini listeler.
    """
    stmt = select(LLMModel)
    if model_type:
        stmt = stmt.where(LLMModel.model_type == model_type.upper())
    stmt = stmt.order_by(LLMModel.model_type, LLMModel.model_code)
    result = await db.execute(stmt)
    return result.scalars().all()

@router.post("", response_model=ModelResponse)
@router.post("/", response_model=ModelResponse)
async def create_model(payload: ModelCreate, db: AsyncSession = Depends(get_db)):
    """
    Yeni bir EVREN LLM Modeli ekler (Madde 8).
    """
    from fastapi import HTTPException
    existing = await db.execute(select(LLMModel).where(LLMModel.model_code == payload.model_code))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail=f"'{payload.model_code}' kodlu model zaten mevcut.")

    provider_id = payload.provider_id
    if not provider_id:
        p_res = await db.execute(select(LLMProvider).limit(1))
        prov = p_res.scalar_one_or_none()
        if prov:
            provider_id = prov.id

    model_obj = LLMModel(
        provider_id=provider_id,
        model_code=payload.model_code.strip().lower(),
        display_name=payload.display_name.strip(),
        model_type=payload.model_type.strip().upper(),
        context_window=payload.context_window,
        effort_coefficient=payload.effort_coefficient,
        status=payload.status.strip().upper()
    )
    db.add(model_obj)
    await db.commit()
    await db.refresh(model_obj)
    return model_obj

# EVREN görev türü → RECOrion model türü
EVREN_TASK_TYPES = {
    "chat": "CHAT", "vision_chat": "VISION", "embedding": "EMBEDDING", "rerank": "RERANKER", "ocr": "OCR",
    "audio_transcription": "AUDIO", "tts": "TTS", "guard": "GUARD", "decision": "DECISION",
}


@router.post("/sync-evren")
async def sync_evren_models(db: AsyncSession = Depends(get_db)):
    """
    EVREN model kataloğunu çeker. Mevcut modellerin bağlam, çıktı sınırı ve fiyat bilgileri güncellenir;
    yeni modeller PASİF eklenir (Süper Admin katsayısını belirleyip aktifleştirir). Katalogda artık
    bulunmayan modeller silinmez, listede ayrıca bildirilir.
    """
    from fastapi import HTTPException
    from app.services.evren_client import EvrenError, evren_client

    try:
        remote = await evren_client.list_models()
    except EvrenError as exc:
        raise HTTPException(status_code=503, detail=f"EVREN model listesi alınamadı: {exc}")

    existing = {m.model_code.lower(): m for m in (await db.execute(select(LLMModel))).scalars()}
    provider = (await db.execute(select(LLMProvider).limit(1))).scalar_one_or_none()
    now = datetime.now(timezone.utc)
    added, updated = [], []
    for item in remote:
        code = str(item.get("id") or "").strip().lower()
        if not code:
            continue
        pricing = item.get("pricing") or {}
        free_until = pricing.get("free_until")
        fields = {
            "evren_task": item.get("task"),
            "modalities": item.get("modalities"),
            "max_output_tokens": item.get("default_max_output_tokens"),
            "prompt_token_price": pricing.get("prompt_token_price"),
            "completion_token_price": pricing.get("completion_token_price"),
            "pricing_currency": pricing.get("currency"),
            "free_until": date.fromisoformat(free_until) if free_until else None,
            "last_synced_at": now,
        }
        if item.get("context_length"):
            fields["context_window"] = int(item["context_length"])
        model = existing.get(code)
        if model:
            for key, value in fields.items():
                setattr(model, key, value)
            updated.append(code)
        else:
            db.add(LLMModel(provider_id=provider.id if provider else None, model_code=code, display_name=code,
                            model_type=EVREN_TASK_TYPES.get(str(item.get("task")), "CHAT"),
                            context_window=fields.pop("context_window", 8192), effort_coefficient=1.0,
                            status="INACTIVE", **fields))
            added.append(code)
    await db.commit()
    remote_codes = {str(i.get("id") or "").lower() for i in remote}
    return {"success": True, "added": added, "updated": updated,
            "missing_in_evren": sorted(c for c in existing if c not in remote_codes)}


@router.get("/{model_id}", response_model=ModelResponse)
async def get_model(model_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    from fastapi import HTTPException
    model_obj = await db.get(LLMModel, model_id)
    if not model_obj:
        raise HTTPException(status_code=404, detail="Model bulunamadı.")
    return model_obj

@router.put("/{model_id}", response_model=ModelResponse)
async def update_model(model_id: uuid.UUID, payload: ModelUpdate, db: AsyncSession = Depends(get_db)):
    from fastapi import HTTPException
    model_obj = await db.get(LLMModel, model_id)
    if not model_obj:
        raise HTTPException(status_code=404, detail="Model bulunamadı.")

    model_obj.display_name = payload.display_name.strip()
    model_obj.model_type = payload.model_type.strip().upper()
    model_obj.context_window = payload.context_window
    model_obj.effort_coefficient = payload.effort_coefficient
    model_obj.status = payload.status.strip().upper()

    await db.commit()
    await db.refresh(model_obj)
    return model_obj

@router.delete("/{model_id}")
async def delete_model(model_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    from fastapi import HTTPException
    model_obj = await db.get(LLMModel, model_id)
    if not model_obj:
        raise HTTPException(status_code=404, detail="Model bulunamadı.")
    
    await db.delete(model_obj)
    await db.commit()
    return {"success": True, "message": f"'{model_obj.display_name}' ({model_obj.model_code}) modeli başarıyla silindi."}

