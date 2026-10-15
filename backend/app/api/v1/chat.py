from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional, Dict, Any
from app.db.session import get_db
from app.db.models import ChatMessage, Task, Actor, LLMModel
from app.services.evren_gateway import evren_gateway
from app.services.collective_memory import collective_memory
from app.services.redis_stream import redis_stream
from pydantic import BaseModel
import uuid
import json

from sqlalchemy.orm import selectinload
import logging
from app.services.agent_learning_service import agent_learning_service

logger = logging.getLogger("chat_api")

router = APIRouter(prefix="/chat", tags=["Work Area Chat (Kalıcı Sohbet & Düşünce Akışı)"])


class SendMessageRequest(BaseModel):
    task_id: uuid.UUID
    content: str
    sender_actor_id: Optional[uuid.UUID] = None
    override_model_code: Optional[str] = None  # Dinamik Model Değiştirici desteği
    is_private: bool = False
    message_type: str = "CHAT"  # CHAT, AGENT_TO_AGENT, HANDOFF


class ChatMessageResponse(BaseModel):
    id: uuid.UUID
    task_id: Optional[uuid.UUID] = None
    project_id: Optional[uuid.UUID] = None
    sender_actor_id: Optional[uuid.UUID] = None
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
    db: AsyncSession = Depends(get_db)
):
    """
    Gemini Web Benzeri Kalıcı Sohbet Geçmişi:
    - Bir görevin geçmişteki tüm konuşmalarını, düşünce adımlarını ve cevaplarını getirir.
    - Proje üyeleri birbirinin sohbetlerini şeffafça görebilir.
    - Sadece kendi sohbetini filtrelemek için actor_id kullanılabilir.
    """
    stmt = (
        select(ChatMessage)
        .where(ChatMessage.task_id == task_id)
    )
    if not include_private:
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
    db: AsyncSession = Depends(get_db)
):
    """
    Tüm Proje Seviyesinde Şeffaf Sohbet ve Ajanlar Arası Müzakere Akışı:
    Projedeki tüm insan-AI ve AI-AI diyaloglarını kronolojik olarak listeler.
    """
    stmt = select(ChatMessage).where(ChatMessage.project_id == project_id, ChatMessage.is_private == False)
    if actor_id:
        stmt = stmt.where(ChatMessage.sender_actor_id == actor_id)
    if message_type:
        stmt = stmt.where(ChatMessage.message_type == message_type.upper())

    stmt = stmt.order_by(ChatMessage.created_at.asc())
    result = await db.execute(stmt)
    return result.scalars().all()


@router.post("/send", response_model=ChatCompletionResponse)
async def send_chat_message(payload: SendMessageRequest, db: AsyncSession = Depends(get_db)):
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
    project_id = project.id
    task_id = task.id

    # Görevli ajanın modelini çöz
    model_code = payload.override_model_code or "glm-5.3"
    system_prompt = "Sen RECOrion otonom iş platformunun yetkili AI personelisiniz."
    agent_id = None

    if task.assignee:
        agent_id = str(task.assignee.id)
        if task.assignee.system_prompt:
            system_prompt = task.assignee.system_prompt
        if not payload.override_model_code and task.assignee.preferred_model:
            model_code = task.assignee.preferred_model.model_code

    # 1. Kullanıcı mesajını kaydet
    user_msg = ChatMessage(
        tenant_id=tenant_id,
        project_id=project_id,
        task_id=task_id,
        sender_actor_id=payload.sender_actor_id,
        role="user",
        content=payload.content,
        is_private=payload.is_private,
        message_type=payload.message_type
    )
    db.add(user_msg)
    await db.commit()
    await db.refresh(user_msg)

    # 2. 2 Kademeli RAG Hafıza Taraması (NS_GLOBAL + NS_AGENT)
    citations = await collective_memory.search_memory(
        tenant_id=str(tenant_id),
        query=payload.content,
        assigned_agent_id=agent_id,
        limit=3
    )

    rag_context = ""
    if citations:
        rag_context = "\n\n[İLGİLİ KURUMSAL & PERSONEL HAFIZA BİLGİLERİ]:\n"
        for c in citations:
            rag_context += f"- ({c.get('scope')}): {c.get('content')}\n"

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
    await redis_stream.publish_thought(str(task.id), "ANALYSIS", f"Görev analiz ediliyor. Model: {model_code}. 2 Kademeli hafıza tarandı.")

    # 4. EVREN Modelini Çalıştır
    ai_resp = await evren_gateway.chat_completion(
        model_code=model_code,
        messages=llm_messages
    )

    choice = ai_resp.get("choices", [{}])[0]
    assistant_content = choice.get("message", {}).get("content", "")
    thought_process = choice.get("message", {}).get("thought", "Düşünce adımları başarıyla tamamlandı.")

    # 5. AI Yanıtını chat_messages tablosuna kalıcı yaz
    assistant_msg = ChatMessage(
        tenant_id=tenant_id,
        project_id=project_id,
        task_id=task_id,
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

