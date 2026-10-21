"""
Öğrenme dokümanları (ADIM 5.4): AI personel, şirket unvanı ve platform katalog unvanı dokümanları.

Yetki
- AI personel ve şirket unvanı dokümanları şirket içeriğidir (KVKK): yalnızca şirketin kendi kullanıcıları.
- Platform katalog unvanı dokümanları genel bilgidir: yalnızca Süper Admin yönetir.
Doküman kimliğiyle yapılan işlemlerde (onay, ret, test, sürüm, silme) yetki dokümanın katmanından çözülür.
"""
import uuid
from typing import Any, Dict, List, Optional
from urllib.parse import quote

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile
from fastapi.responses import PlainTextResponse, RedirectResponse, Response
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import CurrentUser, ensure_tenant_content, forbidden, get_current_user
from app.db.models import Actor, AgentDocument, DocumentChunk, JobTitle, Tenant
from app.db.session import get_db
from app.services import storage
from app.services.documents import pipeline
from app.services.plan_features import deny, ensure_document_quota, entitlements

router = APIRouter(tags=["Öğrenme Dokümanları"])

HIDDEN = ("DELETED",)
LEGACY_LINK_TYPES = ("web", "youtube", "deep_search")


def doc_out(d: AgentDocument, full: bool = False) -> Dict[str, Any]:
    text = d.masked_text or d.extracted_text
    out = {
        "id": str(d.id), "layer": d.layer or "AGENT", "tenant_id": str(d.tenant_id) if d.tenant_id else None,
        "agent_id": str(d.agent_id) if d.agent_id else None, "job_title_id": str(d.job_title_id) if d.job_title_id else None,
        "file_name": d.file_name, "original_name": d.original_name, "file_type": d.file_type, "file_size": d.file_size,
        "status": d.status or "INDEXED", "version": d.version or 1,
        "previous_document_id": str(d.previous_document_id) if d.previous_document_id else None,
        "summary": d.summary, "extracted_text_preview": (text[:400] + ("..." if len(text) > 400 else "")) if text else None,
        "pii_findings": d.pii_findings or {}, "guard_level": (d.guard_result or {}).get("level"),
        "page_count": d.page_count, "ocr_pages": d.ocr_pages, "image_count": d.image_count, "chunk_count": d.chunk_count,
        "error": d.error, "has_card": bool(d.learning_card), "test_percent": (d.test_result or {}).get("percent"),
        "memory_item_id": str(d.memory_item_id) if d.memory_item_id else None, "storage_path": d.storage_path,
        "created_at": d.created_at, "updated_at": d.updated_at, "approved_at": d.approved_at,
    }
    if full:
        out.update({"learning_card": d.learning_card, "test_result": d.test_result, "guard_result": d.guard_result})
    return out


async def _list(db: AsyncSession, *conds) -> List[Dict[str, Any]]:
    rows = (await db.execute(select(AgentDocument).where(*conds, AgentDocument.status.notin_(HIDDEN))
                             .order_by(AgentDocument.created_at.desc()))).scalars().all()
    return [doc_out(d) for d in rows]


async def _agent(db: AsyncSession, tenant_id: uuid.UUID, agent_id: uuid.UUID) -> Actor:
    agent = await db.get(Actor, agent_id)
    if not agent or agent.tenant_id != tenant_id or agent.actor_type != "AI_AGENT":
        raise HTTPException(status_code=404, detail="AI personel bulunamadı.")
    return agent


async def _company_title(db: AsyncSession, tenant_id: uuid.UUID, title_id: uuid.UUID) -> JobTitle:
    title = await db.get(JobTitle, title_id)
    if not title or title.tenant_id != tenant_id:
        raise HTTPException(status_code=404, detail="Şirket unvanı bulunamadı.")
    return title


async def _platform_title(db: AsyncSession, title_id: uuid.UUID) -> JobTitle:
    title = await db.get(JobTitle, title_id)
    if not title or title.tenant_id is not None:
        raise HTTPException(status_code=404, detail="Katalog unvanı bulunamadı.")
    return title


async def _check_upload(db: AsyncSession, current: CurrentUser, layer: str, tenant_id, agent_id, title_id, size: int) -> None:
    """Paket izinleri ve kotalar (platform kataloğu için uygulanmaz)."""
    if layer == "PLATFORM_TITLE":
        return
    tenant = await db.get(Tenant, tenant_id)
    ent = await entitlements(db, tenant, current)
    if layer == "COMPANY_TITLE" and not ent.can_upload_title_documents:
        deny(f"'{ent.plan_name}' paketiniz unvanlara bilgi dokümanı yüklemeye izin vermiyor.")
    await ensure_document_quota(db, ent, tenant_id, agent_id, size, job_title_id=title_id if layer == "COMPANY_TITLE" else None)


async def _upload(db: AsyncSession, bg: BackgroundTasks, current: CurrentUser, file: UploadFile, *, layer: str,
                  tenant_id=None, agent_id=None, title_id=None, previous: Optional[AgentDocument] = None) -> Dict[str, Any]:
    data = await file.read()
    await _check_upload(db, current, layer, tenant_id, agent_id, title_id, len(data))
    doc = await pipeline.create_document(db, layer=layer, tenant_id=tenant_id, agent_id=agent_id, job_title_id=title_id,
                                         filename=file.filename, data=data, actor_id=current.actor_id, previous=previous)
    bg.add_task(pipeline.process_document, doc.id)
    return doc_out(doc)


# ---------------------------------------------------------------- AI personel dokümanları
@router.get("/company/{tenant_id}/ai-agents/{agent_id}/documents")
async def list_agent_documents(tenant_id: uuid.UUID, agent_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    await _agent(db, tenant_id, agent_id)
    return await _list(db, AgentDocument.tenant_id == tenant_id, AgentDocument.agent_id == agent_id)


@router.post("/company/{tenant_id}/ai-agents/{agent_id}/documents", status_code=201)
async def upload_agent_document(tenant_id: uuid.UUID, agent_id: uuid.UUID, bg: BackgroundTasks, file: UploadFile = File(...),
                                current: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Doküman veya görsel yükler; arka planda işlenir ve onaya düşer (öğrenme onaydan sonra başlar)."""
    await _agent(db, tenant_id, agent_id)
    return await _upload(db, bg, current, file, layer="AGENT", tenant_id=tenant_id, agent_id=agent_id)


@router.delete("/company/{tenant_id}/ai-agents/{agent_id}/documents/{document_id}")
async def delete_agent_document(tenant_id: uuid.UUID, agent_id: uuid.UUID, document_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    doc = await db.get(AgentDocument, document_id)
    if not doc or doc.tenant_id != tenant_id or doc.agent_id != agent_id:
        raise HTTPException(status_code=404, detail="Doküman bulunamadı.")
    await pipeline.delete(db, doc)
    return {"success": True}


@router.get("/company/{tenant_id}/ai-agents/{agent_id}/documents/{document_id}/download")
async def download_agent_document(tenant_id: uuid.UUID, agent_id: uuid.UUID, document_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    doc = await db.get(AgentDocument, document_id)
    if not doc or doc.tenant_id != tenant_id or doc.agent_id != agent_id:
        raise HTTPException(status_code=404, detail="Doküman bulunamadı.")
    return await _download(doc)


# ---------------------------------------------------------------- şirket unvanı dokümanları
@router.get("/company/{tenant_id}/job-titles/{title_id}/documents")
async def list_company_title_documents(tenant_id: uuid.UUID, title_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    await _company_title(db, tenant_id, title_id)
    return await _list(db, AgentDocument.tenant_id == tenant_id, AgentDocument.job_title_id == title_id,
                       AgentDocument.layer == "COMPANY_TITLE")


@router.post("/company/{tenant_id}/job-titles/{title_id}/documents", status_code=201)
async def upload_company_title_document(tenant_id: uuid.UUID, title_id: uuid.UUID, bg: BackgroundTasks, file: UploadFile = File(...),
                                        current: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Bu unvandaki tüm AI personelin öğreneceği şirkete özel bilgi dokümanı (Şirket Unvan Bilgisi)."""
    await _company_title(db, tenant_id, title_id)
    return await _upload(db, bg, current, file, layer="COMPANY_TITLE", tenant_id=tenant_id, title_id=title_id)


# ---------------------------------------------------------------- platform katalog unvanı dokümanları
@router.get("/catalog/titles/{title_id}/documents")
async def list_platform_title_documents(title_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    await _platform_title(db, title_id)
    return await _list(db, AgentDocument.job_title_id == title_id, AgentDocument.layer == "PLATFORM_TITLE")


@router.post("/catalog/titles/{title_id}/documents", status_code=201)
async def upload_platform_title_document(title_id: uuid.UUID, bg: BackgroundTasks, file: UploadFile = File(...),
                                         current: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Tüm müşterilerdeki bu unvanın öğreneceği genel bilgi (Platform Unvan Bilgisi). Şirkete özel bilgi içermemeli."""
    await _platform_title(db, title_id)
    return await _upload(db, bg, current, file, layer="PLATFORM_TITLE", title_id=title_id)


# ---------------------------------------------------------------- doküman işlemleri
async def _doc(db: AsyncSession, document_id: uuid.UUID, user: CurrentUser, manage: bool) -> AgentDocument:
    doc = await db.get(AgentDocument, document_id)
    if not doc or doc.status in HIDDEN:
        raise HTTPException(status_code=404, detail="Doküman bulunamadı.")
    if doc.layer == "PLATFORM_TITLE":
        if not user.is_super_admin:
            raise forbidden("Platform katalog dokümanlarını yalnızca RECDx yöneticileri yönetebilir.")
    else:
        ensure_tenant_content(user, doc.tenant_id, "agent:configure" if manage else "tenant:view")
    return doc


@router.get("/documents/{document_id}")
async def get_document(document_id: uuid.UUID, current: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    doc = await _doc(db, document_id, current, manage=False)
    out = doc_out(doc, full=True)
    # Sürüm zinciri (en yeni önce)
    chain, prev_id = [], doc.previous_document_id
    while prev_id and len(chain) < 20:
        prev = await db.get(AgentDocument, prev_id)
        if not prev:
            break
        chain.append({"id": str(prev.id), "version": prev.version, "status": prev.status, "created_at": prev.created_at})
        prev_id = prev.previous_document_id
    out["previous_versions"] = chain
    out["chunk_preview"] = [c.content[:300] for c in (await db.execute(
        select(DocumentChunk).where(DocumentChunk.document_id == doc.id).order_by(DocumentChunk.idx).limit(3))).scalars()]
    return out


class ApproveIn(BaseModel):
    summary: Optional[str] = Field(None, max_length=4000)
    key_points: Optional[List[str]] = None
    quiz: Optional[List[Dict[str, Any]]] = None


@router.post("/documents/{document_id}/approve")
async def approve_document(document_id: uuid.UUID, payload: ApproveIn, current: CurrentUser = Depends(get_current_user),
                           db: AsyncSession = Depends(get_db)):
    """Öğrenme kartını (gerekirse düzenleyerek) onaylar; doküman vektörlenir ve AI personel öğrenir."""
    doc = await _doc(db, document_id, current, manage=True)
    card = {k: v for k, v in payload.model_dump().items() if v is not None}
    await pipeline.approve(db, doc, current.actor_id, card or None)
    return doc_out(doc, full=True)


class RejectIn(BaseModel):
    reason: Optional[str] = Field(None, max_length=500)


@router.post("/documents/{document_id}/reject")
async def reject_document(document_id: uuid.UUID, payload: RejectIn, current: CurrentUser = Depends(get_current_user),
                          db: AsyncSession = Depends(get_db)):
    doc = await _doc(db, document_id, current, manage=True)
    await pipeline.reject(db, doc, payload.reason)
    return doc_out(doc)


@router.post("/documents/{document_id}/test")
async def test_document(document_id: uuid.UUID, current: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Öğrenme kartındaki soruları modele dokümana dayanarak cevaplatır ve puanlar."""
    doc = await _doc(db, document_id, current, manage=True)
    return await pipeline.run_test(db, doc)


@router.post("/documents/{document_id}/reprocess")
async def reprocess_document(document_id: uuid.UUID, bg: BackgroundTasks, current: CurrentUser = Depends(get_current_user),
                             db: AsyncSession = Depends(get_db)):
    doc = await _doc(db, document_id, current, manage=True)
    if doc.status not in ("FAILED", "PENDING_APPROVAL", "QUARANTINED") or not doc.storage_key:
        raise HTTPException(status_code=409, detail="Bu doküman yeniden işlenemez.")
    bg.add_task(pipeline.process_document, doc.id)
    return doc_out(doc)


@router.post("/documents/{document_id}/versions", status_code=201)
async def upload_new_version(document_id: uuid.UUID, bg: BackgroundTasks, file: UploadFile = File(...),
                             current: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Yeni sürüm yükler; yeni sürüm onaylanınca eskisi SUPERSEDED olur ve AI personel eskisini unutur."""
    prev = await _doc(db, document_id, current, manage=True)
    if prev.file_type in LEGACY_LINK_TYPES:
        raise HTTPException(status_code=400, detail="Web/video kaynakları için sürüm yüklenemez.")
    newer = (await db.execute(select(func.count()).select_from(AgentDocument).where(
        AgentDocument.previous_document_id == prev.id, AgentDocument.status.notin_(("DELETED", "REJECTED", "FAILED"))))).scalar()
    if newer:
        raise HTTPException(status_code=409, detail="Bu dokümanın daha yeni bir sürümü zaten var.")
    return await _upload(db, bg, current, file, layer=prev.layer, tenant_id=prev.tenant_id, agent_id=prev.agent_id,
                         title_id=prev.job_title_id, previous=prev)


@router.delete("/documents/{document_id}")
async def delete_document(document_id: uuid.UUID, current: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    doc = await _doc(db, document_id, current, manage=True)
    await pipeline.delete(db, doc)
    return {"success": True}


async def _download(doc: AgentDocument):
    if doc.file_type in ("web", "youtube") or (doc.storage_path or "").startswith(("http://", "https://")):
        return RedirectResponse(url=doc.storage_path)
    if doc.file_type == "deep_search":
        return PlainTextResponse(content=doc.extracted_text or "Rapor içeriği bulunamadı.", media_type="text/plain; charset=utf-8")
    if not doc.storage_key:
        raise HTTPException(status_code=404, detail="Dosya depoda bulunamadı.")
    try:
        data = await storage.get_object(doc.storage_key)
    except storage.StorageError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    return Response(content=data, media_type=pipeline.CONTENT_TYPES.get(doc.file_type, "application/octet-stream"),
                    headers={"Content-Disposition": f"attachment; filename*=UTF-8''{quote(doc.original_name)}"})


@router.get("/documents/{document_id}/download")
async def download_document(document_id: uuid.UUID, current: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await _download(await _doc(db, document_id, current, manage=False))
