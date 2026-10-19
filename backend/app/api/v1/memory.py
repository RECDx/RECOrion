from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional, Dict, Any
from app.db.session import get_db
from app.core.security import CurrentUser, ensure_tenant_content, get_current_user
from app.db.models import MemoryItem
from app.services.collective_memory import collective_memory
from pydantic import BaseModel
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

    class Config:
        from_attributes = True


@router.get("", response_model=List[MemoryItemResponse])
@router.get("/", response_model=List[MemoryItemResponse])
async def list_memory_items(
    tenant_id: uuid.UUID = Query(...),
    scope: Optional[str] = Query(None),
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    ensure_tenant_content(user, tenant_id)
    stmt = select(MemoryItem).where(MemoryItem.tenant_id == tenant_id)
    if scope:
        stmt = stmt.where(MemoryItem.scope == scope.upper())
    stmt = stmt.order_by(MemoryItem.created_at.desc())
    result = await db.execute(stmt)
    return result.scalars().all()


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

    item.scope = "GLOBAL"
    item.agent_id = None
    item.status = "APPROVED"
    await db.commit()
    await db.refresh(item)

    # Qdrant'ta da güncelle
    await collective_memory.add_memory(
        tenant_id=str(item.tenant_id),
        scope="GLOBAL",
        content=item.content,
        source_reference=f"PROMOTED_FROM_{memory_id}"
    )

    return {"status": "promoted", "message": "Bilgi Şirket Kurum Hafızasına (NS_GLOBAL) başarıyla katıldı."}
