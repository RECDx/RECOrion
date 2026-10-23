from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional, Dict, Any
from app.db.session import get_db
from app.core.security import CurrentUser, ensure_tenant_content, get_current_user
from app.db.models import ChatMessage, Task, Actor, LLMModel, Project
from app.services import llm_gateway
from app.services.llm_gateway import LLMContext, LLMError
from app.services import knowledge
from app.services import projects as psvc
from app.services.redis_stream import redis_stream
from pydantic import BaseModel, Field
from typing import Literal
import uuid
import json

from sqlalchemy.orm import selectinload
import logging
from app.services.agent_learning_service import agent_learning_service

logger = logging.getLogger("chat_api")

router = APIRouter(prefix="/chat", tags=["Work Area Chat (Kalıcı Sohbet & Düşünce Akışı)"])


async def _ensure_task_access(db: AsyncSession, user: CurrentUser, task_id: uuid.UUID) -> Task:
    """Görevin sohbeti yalnızca proje ekibine (veya proje yönetim yetkisi olanlara) açıktır (ADIM 8.1)."""
    task = (await db.execute(
        select(Task).options(selectinload(Task.project)).where(Task.id == task_id)
    )).scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Görev bulunamadı.")
    await psvc.load(db, user, task.project_id)
    return task


class SendMessageRequest(BaseModel):
    task_id: uuid.UUID
    content: str = Field(..., min_length=1, max_length=20000)
    sender_actor_id: Optional[uuid.UUID] = None  # yok sayılır: gönderen her zaman oturumdaki kullanıcıdır
    override_model_code: Optional[str] = None  # Dinamik Model Değiştirici desteği
    is_private: bool = False
    # Kullanıcı yalnızca sohbet mesajı yazar; AI-AI ve devir mesajlarını sistem üretir
    message_type: Literal["CHAT"] = "CHAT"


class ChatMessageResponse(BaseModel):
    id: uuid.UUID
    task_id: Optional[uuid.UUID] = None
    project_id: Optional[uuid.UUID] = None
    sender_actor_id: Optional[uuid.UUID] = None
    sender_name: Optional[str] = None
    role: str
    content: str
    thought_process: Optional[str] = None
    attachments: list = []
    is_private: bool = False
    message_type: str = "CHAT"
    created_at: Any

    class Config:
        from_attributes = True


class ChatCompletionResponse(BaseModel):
    user_message: ChatMessageResponse
    assistant_message: ChatMessageResponse
    citations: List[Dict[str, Any]] = []


@router.get("/history/{task_id}", response_model=List[ChatMessageResponse])
async def get_chat_history(
    task_id: uuid.UUID,
    actor_id: Optional[uuid.UUID] = None,
    include_private: bool = False,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Gemini Web Benzeri Kalıcı Sohbet Geçmişi:
    - Bir görevin geçmişteki tüm konuşmalarını, düşünce adımlarını ve cevaplarını getirir.
    - Proje üyeleri birbirinin sohbetlerini şeffafça görebilir.
    - Sadece kendi sohbetini filtrelemek için actor_id kullanılabilir.
    """
    await _ensure_task_access(db, user, task_id)
    stmt = (
        select(ChatMessage)
        .where(ChatMessage.task_id == task_id)
    )
    if include_private:
        # Özel mesajları yalnızca gönderen kişi görür
        stmt = stmt.where((ChatMessage.is_private == False) | (ChatMessage.sender_actor_id == user.actor_id))
    else:
        stmt = stmt.where(ChatMessage.is_private == False)
    if actor_id:
        stmt = stmt.where(ChatMessage.sender_actor_id == actor_id)

    stmt = stmt.order_by(ChatMessage.created_at.asc())
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/project/{project_id}", response_model=List[ChatMessageResponse])
async def get_project_chat_history(
    project_id: uuid.UUID,
    actor_id: Optional[uuid.UUID] = None,
    message_type: Optional[str] = None,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Tüm Proje Seviyesinde Şeffaf Sohbet ve Ajanlar Arası Müzakere Akışı:
    Projedeki tüm insan-AI ve AI-AI diyaloglarını kronolojik olarak listeler.
    """
    await psvc.load(db, user, project_id)
    stmt = select(ChatMessage).where(ChatMessage.project_id == project_id, ChatMessage.is_private == False)
    if actor_id:
        stmt = stmt.where(ChatMessage.sender_actor_id == actor_id)
    if message_type:
        stmt = stmt.where(ChatMessage.message_type == message_type.upper())

    stmt = stmt.order_by(ChatMessage.created_at.asc())
    result = await db.execute(stmt)
    return result.scalars().all()


@router.post("/send", response_model=ChatCompletionResponse)
async def send_chat_message(
    payload: SendMessageRequest,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Work Area üzerinden bir AI personeline mesaj gönderir:
    1. Mesajı kalıcı olarak chat_messages tablosuna kaydeder.
    2. 2 Kademeli Kolektif Hafızayı (NS_GLOBAL & NS_AGENT) tarar.
    3. Görevli ajanın EVREN modelini tetikler.
    4. Ajanın yanıtını ve canlı düşünce sürecini kaydedip döndürür.
    """
    # Görevi, projeyi ve atanan ajanı eager load ile çek
    t_stmt = (
        select(Task)
        .options(
            selectinload(Task.project),
            selectinload(Task.assignee).selectinload(Actor.preferred_model)
        )
        .where(Task.id == payload.task_id)
    )
    t_res = await db.execute(t_stmt)
    task = t_res.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Görev bulunamadı.")

    project = task.project
    tenant_id = project.tenant_id
    ensure_tenant_content(user, tenant_id, "chat:participate")
    await psvc.load(db, user, project.id)
    if project.status in ("COMPLETED", "CANCELLED"):
        raise HTTPException(status_code=409, detail="Kapanmış projeye mesaj yazılamaz; yazışma kaydı salt okunurdur.")
    project_id = project.id
    task_id = task.id

    # Görevli ajan: rol promptu buradan, model LLM Gateway'de çözülür
    # (açık seçim → personelin modeli → platform varsayılanı; paket izni kontrol edilir)
    system_prompt = "Sen RECOrion otonom iş platformunun yetkili AI personelisiniz."
    agent_id = None

    if task.assignee:
        agent_id = str(task.assignee.id)
        if task.assignee.system_prompt:
            system_prompt = task.assignee.system_prompt

    # 1. Kullanıcı mesajını kaydet
    user_msg = ChatMessage(
        tenant_id=tenant_id,
        project_id=project_id,
        task_id=task_id,
        sender_actor_id=user.actor_id,
        role="user",
        content=payload.content,
        is_private=payload.is_private,
        message_type=payload.message_type
    )
    db.add(user_msg)
    await db.commit()
    await db.refresh(user_msg)

    # 2. 4 katmanlı bilgi + proje ekleri (ADIM 5.5): proje, AI personel, şirket unvanı, kurum hafızası, platform unvanı
    scope = await knowledge.scope_for_agent(db, tenant_id, task.assignee.id if task.assignee else None, project_id)
    citations = await knowledge.retrieve(scope, payload.content, limit=6)
    rag_context = knowledge.format_context(citations)

    # 3. Model Mesaj Geçmişini Derle (Rolling Context)
    history_res = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.task_id == task.id)
        .order_by(ChatMessage.created_at.desc())
        .limit(10)
    )
    prev_messages = list(reversed(history_res.scalars().all()))

    llm_messages = [{"role": "system", "content": system_prompt + rag_context}]
    for m in prev_messages:
        llm_messages.append({"role": m.role if m.role in ["user", "assistant"] else "user", "content": m.content})

    # Redis'e anlık düşünce adımı fırlat
    counts = knowledge.layer_counts(citations)
    await redis_stream.publish_thought(str(task.id), "ANALYSIS", "Bilgi katmanları tarandı: " + (
        ", ".join(f"{knowledge.LABELS[k]} {v}" for k, v in counts.items()) or "ilgili bilgi bulunamadı") + ".")

    # 4. LLM Gateway (ölçüm + kredi düşümü). Hata olursa sahte yanıt üretilmez.
    try:
        ai = await llm_gateway.chat(
            LLMContext(tenant_id=tenant_id, purpose="AGENT_CHAT", actor_id=task.assignee.id if task.assignee else None,
                       task_id=task_id, project_id=project_id),
            llm_messages,
            model_code=payload.override_model_code,
        )
    except LLMError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message)

    model_code = ai.model_code
    assistant_content = ai.content
    thought_process = ai.thought

    # 5. AI Yanıtını chat_messages tablosuna kalıcı yaz
    assistant_msg = ChatMessage(
        tenant_id=tenant_id,
        project_id=project_id,
        task_id=task_id,
        sender_actor_id=task.assignee.id if task.assignee else None,
        role="assistant",
        content=assistant_content,
        thought_process=thought_process,
        is_private=payload.is_private,
        message_type=payload.message_type
    )
    db.add(assistant_msg)
    await db.commit()
    await db.refresh(assistant_msg)

    # 6. Yazışmadan Öğrenme (Learn from Chat / Dialogue):
    # Mesajlaşma sonrası arka planda kritik iş kurallarını ve kararları hafızaya indeksle
    learned_items = []
    try:
        dialogue_to_learn = [
            {"role": "user", "content": payload.content},
            {"role": "assistant", "content": assistant_content}
        ]
        target_agent_uuid = uuid.UUID(agent_id) if agent_id else None
        learned_items = await agent_learning_service.learn_from_chat_dialogue(
            tenant_id=tenant_id,
            agent_id=target_agent_uuid,
            messages=dialogue_to_learn,
            task_id=task_id,
            db=db,
            model_code=model_code
        )
    except Exception as learn_err:
        logger.warning(f"Sohbetten öğrenme adımı hatası: {learn_err}")

    return {
        "user_message": user_msg,
        "assistant_message": assistant_msg,
        "citations": citations
    }


@router.post("/learn/{task_id}")
async def learn_from_task_chat_history(
    task_id: uuid.UUID,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Belirli bir göreve ait tüm sohbet geçmişini analiz eder ve
    şirket / personel hafızasına kalıcı know-how, kural ve tercih maddeleri çıkarır.
    """
    stmt = (
        select(Task)
        .options(selectinload(Task.project), selectinload(Task.assignee))
        .where(Task.id == task_id)
    )
    task_res = await db.execute(stmt)
    task = task_res.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Görev bulunamadı.")
    ensure_tenant_content(user, task.project.tenant_id, "chat:participate")
    await psvc.load(db, user, task.project_id)

    msgs_stmt = (
        select(ChatMessage)
        .where(ChatMessage.task_id == task_id)
        .order_by(ChatMessage.created_at.asc())
    )
    messages = (await db.execute(msgs_stmt)).scalars().all()
    if not messages:
        return {"learned_items": [], "count": 0, "message": "Görevde henüz yazışma bulunmuyor."}

    msg_payloads = [{"role": m.role, "content": m.content} for m in messages]
    agent_id = task.assignee.id if task.assignee else None

    learned = await agent_learning_service.learn_from_chat_dialogue(
        tenant_id=task.project.tenant_id,
        agent_id=agent_id,
        messages=msg_payloads,
        task_id=task.id,
        db=db
    )

    return {
        "learned_items": learned,
        "count": len(learned),
        "message": f"Yazışma geçmişinden {len(learned)} bilgi maddesi hafızaya başarıyla kaydedildi."
    }

