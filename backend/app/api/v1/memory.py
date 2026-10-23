from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional, Dict, Any
from app.db.session import get_db
from app.core.security import CurrentUser, ensure_tenant_content, get_current_user
from app.db.models import Actor, MemoryItem
from app.services.collective_memory import collective_memory
from pydantic import BaseModel, Field
from datetime import datetime, timezone
import uuid

router = APIRouter(prefix="/memory", tags=["2 Kademeli Kolektif Hafıza (Collective Memory)"])


class AddMemoryRequest(BaseModel):
    tenant_id: uuid.UUID
    scope: str  # GLOBAL veya AGENT
    content: str
    agent_id: Optional[uuid.UUID] = None
    source_reference: Optional[str] = None
    metadata: Dict[str, Any] = {}


class SearchMemoryRequest(BaseModel):
    tenant_id: uuid.UUID
    query: str
    assigned_agent_id: Optional[uuid.UUID] = None
    limit: int = 5


class MemoryItemResponse(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    scope: str
    agent_id: Optional[uuid.UUID] = None
    source_reference: Optional[str] = None
    content: str
    status: str
    confidence_score: float
    metadata_json: Optional[Dict[str, Any]] = None
    created_at: Optional[Any] = None
    # Onay izi (ADIM 8.4)
    reviewed_by_actor_id: Optional[uuid.UUID] = None
    reviewed_by_name: Optional[str] = None
    reviewed_at: Optional[Any] = None
    review_note: Optional[str] = None

    class Config:
        from_attributes = True


class ReviewIn(BaseModel):
    note: Optional[str] = Field(None, max_length=1000)


def _review(item: MemoryItem, user: CurrentUser, note: Optional[str] = None) -> None:
    item.reviewed_by_actor_id, item.reviewed_at = user.actor_id, datetime.now(timezone.utc)
    item.review_note = (note or "").strip() or None


async def _decorate(db: AsyncSession, items: List[MemoryItem]) -> List[Dict[str, Any]]:
    ids = {i.reviewed_by_actor_id for i in items if i.reviewed_by_actor_id}
    names = dict((await db.execute(select(Actor.id, Actor.display_name).where(Actor.id.in_(ids)))).all()) if ids else {}
    return [{**MemoryItemResponse.model_validate(i).model_dump(), "reviewed_by_name": names.get(i.reviewed_by_actor_id)} for i in items]


@router.get("", response_model=List[MemoryItemResponse])
@router.get("/", response_model=List[MemoryItemResponse])
async def list_memory_items(
    tenant_id: uuid.UUID = Query(...),
    scope: Optional[str] = Query(None),
    status: Optional[str] = Query(None, description="APPROVED, CANDIDATE (onay bekleyen), REVOKED"),
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    ensure_tenant_content(user, tenant_id)
    stmt = select(MemoryItem).where(MemoryItem.tenant_id == tenant_id)
    if scope:
        stmt = stmt.where(MemoryItem.scope == scope.upper())
    if status:
        stmt = stmt.where(MemoryItem.status == status.upper())
    # Onay bekleyen ve reddedilen bilgiler (henüz/artık kurum bilgisi değil) yalnızca onay yetkisi olana görünür
    if not user.has("memory:promote"):
        stmt = stmt.where(MemoryItem.status == "APPROVED")
    stmt = stmt.order_by(MemoryItem.created_at.desc())
    result = await db.execute(stmt)
    return await _decorate(db, result.scalars().all())


@router.post("/add")
async def add_memory_item(payload: AddMemoryRequest, user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    ensure_tenant_content(user, payload.tenant_id, "memory:promote")
    if payload.scope not in ["GLOBAL", "AGENT"]:
        raise HTTPException(status_code=400, detail="Scope yalnızca 'GLOBAL' veya 'AGENT' olabilir.")

    # 1. Qdrant'a ekle ve vektörize et
    qd_res = await collective_memory.add_memory(
        tenant_id=str(payload.tenant_id),
        scope=payload.scope,
        content=payload.content,
        agent_id=str(payload.agent_id) if payload.agent_id else None,
        source_reference=payload.source_reference,
        metadata=payload.metadata
    )

    # 2. PostgreSQL'e kaydet
    item = MemoryItem(
        tenant_id=payload.tenant_id,
        scope=payload.scope,
        agent_id=payload.agent_id,
        source_reference=payload.source_reference,
        content=payload.content,
        metadata_json=payload.metadata,
        qdrant_point_id=uuid.UUID(qd_res["point_id"]),
        status="APPROVED"
    )
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return item


@router.post("/search")
async def search_memory(payload: SearchMemoryRequest, user: CurrentUser = Depends(get_current_user)):
    """
    2 Kademeli RAG Hibrit Arama (Şirket Kurum Hafızası + AI Personel Hafızası).
    """
    ensure_tenant_content(user, payload.tenant_id, "memory:search")
    results = await collective_memory.search_memory(
        tenant_id=str(payload.tenant_id),
        query=payload.query,
        assigned_agent_id=str(payload.assigned_agent_id) if payload.assigned_agent_id else None,
        limit=payload.limit
    )
    return {"results": results}


@router.post("/promote/{memory_id}")
async def promote_to_corporate_memory(memory_id: uuid.UUID, user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """
    İnsan İnceleme Kuyruğu Onayı:
    Bir ajanın projedeki tecrübesini Şirket Kurum Hafızasına (NS_GLOBAL) terfi ettirir;
    böylece tüm personelin ortak aklına dönüşür.
    """
    stmt = select(MemoryItem).where(MemoryItem.id == memory_id)
    res = await db.execute(stmt)
    item = res.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Hafıza kaydı bulunamadı.")
    ensure_tenant_content(user, item.tenant_id, "memory:promote")

    if item.scope == "GLOBAL" and item.status == "APPROVED":
        return {"status": "promoted", "message": "Bu bilgi zaten Kurum Hafızasında."}
    if item.status == "REVOKED":
        raise HTTPException(status_code=409, detail="Reddedilmiş veya geri alınmış bilgi terfi ettirilemez.")
    meta = {"memory_item_id": str(item.id), "approved_by": str(user.actor_id)}
    if item.qdrant_point_id:
        # Vektörü olan (AI personel) bilgi: aynı nokta Kurum Hafızasına taşınır; ikinci kopya oluşmaz
        await collective_memory.set_scope([str(item.qdrant_point_id)], "GLOBAL", {"agent_id": None, **meta})
    else:
        # Aday (henüz vektörlenmemiş) bilgi önce vektörlenir; başarısız olursa kayıt değişmez
        point = await collective_memory.add_memory(
            tenant_id=str(item.tenant_id),
            scope="GLOBAL",
            content=item.content,
            source_reference=item.source_reference or f"PROMOTED_FROM_{memory_id}",
            metadata=meta,
        )
        item.qdrant_point_id = uuid.UUID(point["point_id"])
    item.scope = "GLOBAL"
    item.agent_id = None
    item.status = "APPROVED"
    _review(item, user)
    await db.commit()

    return {"status": "promoted", "message": "Bilgi Şirket Kurum Hafızasına (NS_GLOBAL) başarıyla katıldı."}


@router.post("/{memory_id}/reject")
async def reject_memory_candidate(memory_id: uuid.UUID, payload: Optional[ReviewIn] = None,
                                  user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Onay bekleyen Kurum Hafızası adayını reddeder (öğrenilmez); gerekçe isteğe bağlı."""
    item = await db.get(MemoryItem, memory_id)
    if not item:
        raise HTTPException(status_code=404, detail="Hafıza kaydı bulunamadı.")
    ensure_tenant_content(user, item.tenant_id, "memory:promote")
    if item.status != "CANDIDATE":
        raise HTTPException(status_code=409, detail="Yalnızca onay bekleyen bilgiler reddedilebilir.")
    item.status = "REVOKED"
    _review(item, user, payload.note if payload else None)
    await db.commit()
    return {"status": "rejected"}


@router.post("/{memory_id}/revoke")
async def revoke_memory_item(memory_id: uuid.UUID, payload: ReviewIn, user: CurrentUser = Depends(get_current_user),
                             db: AsyncSession = Depends(get_db)):
    """Onaylı bilgiyi geri alır (yanlış/eskimiş bilgi): vektör silinir, AI personel artık kullanmaz; kayıt ve iz kalır."""
    item = await db.get(MemoryItem, memory_id)
    if not item:
        raise HTTPException(status_code=404, detail="Hafıza kaydı bulunamadı.")
    ensure_tenant_content(user, item.tenant_id, "memory:promote")
    if item.status != "APPROVED":
        raise HTTPException(status_code=409, detail="Yalnızca onaylı bilgi geri alınabilir.")
    if not (payload.note or "").strip():
        raise HTTPException(status_code=422, detail="Geri alma gerekçesini yazın.")
    if item.qdrant_point_id:
        await collective_memory.delete_points([str(item.qdrant_point_id)])
    item.status, item.qdrant_point_id = "REVOKED", None
    _review(item, user, payload.note)
    await db.commit()
    return {"status": "revoked"}
