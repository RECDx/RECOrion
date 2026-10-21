"""
Doküman hattı (ADIM 5.4).

  create_document   dosyayı doğrular, MinIO'ya yazar                                    -> UPLOADED
  process_document  metin çıkarma/OCR > görsel açıklama > guard > KVKK maskeleme > parçalama > öğrenme kartı -> PENDING_APPROVAL
                    (zararlı içerik: QUARANTINED, hata: FAILED)
  run_test          öğrenme kartındaki soruları dokümana dayanarak modele sordurur, puanlar
  approve           parçaları vektörler (Qdrant), eski sürümü SUPERSEDED yapar             -> APPROVED
  reject / delete   vektörleri ve depodaki dosyayı kaldırır

AI personeller yalnızca maskeli metni öğrenir; asıl dosya depoda erişim kontrollü kalır.
"""
import hashlib
import json
import logging
import re
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from fastapi import HTTPException
from sqlalchemy import delete as sa_delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.models import Actor, AgentDocument, DocumentChunk, MemoryItem, Tenant
from app.db.session import AsyncSessionLocal
from app.services import llm_gateway, storage
from app.services.documents import chunking, pii
from app.services.documents.extract import IMAGE_EXTS, SUPPORTED_EXTS, ExtractionError, extract
from app.services.llm_gateway import LLMContext, LLMError

logger = logging.getLogger("recorion.documents")

MAX_BYTES = 50 * 1024 * 1024
CARD_SOURCE_CHARS = 14000
VISION_PROMPT = """Bu görsel "{name}" adlı öğrenme kaynağında yer alıyor ve bir yapay zeka personel bundan öğrenecek.
Görselde ne olduğunu Türkçe, öğrenilebilir biçimde ayrıntılı açıkla: ürün/nesne ve özellikleri, görünen yazılar,
ölçü ve sayılar, tablo veya şemadaki ilişkiler, süreç adımları, kalite/hata işaretleri. Emin olmadığın şeyi yazma.
KVKK: kişileri tanımlamaya çalışma, yüz/kimlik/plaka gibi kişisel bilgileri yazma; gerekiyorsa sadece "bir kişi" de.
Düz metin yaz (başlık, madde işareti veya markdown kullanma), en fazla 200 kelime."""
SCOPE_BY_LAYER = {"AGENT": "AGENT", "COMPANY_TITLE": "TITLE", "PLATFORM_TITLE": "PLATFORM_TITLE"}
ACTIVE = ("UPLOADED", "PROCESSING", "PENDING_APPROVAL", "APPROVED", "QUARANTINED")
CONTENT_TYPES = {"pdf": "application/pdf", "png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg",
                 "txt": "text/plain", "csv": "text/csv", "md": "text/markdown", "json": "application/json"}


def _now():
    return datetime.now(timezone.utc)


def _owner_filter(doc_layer: str, agent_id, job_title_id):
    return AgentDocument.agent_id == agent_id if doc_layer == "AGENT" else AgentDocument.job_title_id == job_title_id


# ---------------------------------------------------------------- yükleme
async def create_document(db: AsyncSession, *, layer: str, tenant_id: Optional[uuid.UUID], agent_id: Optional[uuid.UUID],
                          job_title_id: Optional[uuid.UUID], filename: str, data: bytes, actor_id: Optional[uuid.UUID],
                          previous: Optional[AgentDocument] = None) -> AgentDocument:
    original = (filename or "dokuman").strip()[:200]
    ext = original.rsplit(".", 1)[-1].lower() if "." in original else ""
    if ext not in SUPPORTED_EXTS:
        raise HTTPException(status_code=400, detail=f"Desteklenmeyen dosya türü (.{ext or '?'}). PDF, Word, Excel, PowerPoint, "
                                                    "metin, görsel ve eski Office biçimleri (.doc, .xls, .ppt) yüklenebilir.")
    if not data:
        raise HTTPException(status_code=400, detail="Yüklenen dosya boş.")
    if len(data) > MAX_BYTES:
        raise HTTPException(status_code=400, detail="Dosya boyutu 50 MB sınırını aşıyor.")

    sha = hashlib.sha256(data).hexdigest()
    dup = (await db.execute(select(AgentDocument).where(
        AgentDocument.layer == layer, _owner_filter(layer, agent_id, job_title_id),
        AgentDocument.sha256 == sha, AgentDocument.status.in_(ACTIVE)))).scalars().first()
    if dup:
        raise HTTPException(status_code=409, detail=f"Bu dosya zaten yüklü ('{dup.original_name}', sürüm {dup.version}).")

    clean = re.sub(r"[^A-Za-z0-9_.-]", "_", original)
    doc = AgentDocument(
        id=uuid.uuid4(), tenant_id=tenant_id, agent_id=agent_id, job_title_id=job_title_id, layer=layer,
        file_name=clean, original_name=original, file_type=ext, file_size=len(data), sha256=sha,
        status="UPLOADED", uploaded_by_actor_id=actor_id,
        version=(previous.version + 1) if previous else 1, previous_document_id=previous.id if previous else None,
    )
    owner = agent_id or job_title_id
    doc.storage_key = f"{tenant_id or 'platform'}/{layer.lower()}/{owner}/{doc.id}/{clean}"
    doc.storage_path = f"minio://{settings.MINIO_DOCUMENTS_BUCKET}/{doc.storage_key}"
    try:
        await storage.put_object(doc.storage_key, data, CONTENT_TYPES.get(ext))
    except storage.StorageError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    db.add(doc)
    await db.commit()
    await db.refresh(doc)
    return doc


# ---------------------------------------------------------------- işleme
def _ctx(doc: AgentDocument, purpose: str, use_agent_model: bool = False) -> LLMContext:
    """Kredi her zaman dokümanın şirketine yazılır; model yalnızca test için AI personelin kendi modelidir."""
    return LLMContext(tenant_id=doc.tenant_id, purpose=purpose, actor_id=doc.agent_id if use_agent_model else None)


def _parse_json(text: str) -> Dict[str, Any]:
    text = text.strip()
    if "```" in text:
        text = text.split("```")[1].removeprefix("json").strip()
    start, end = text.find("{"), text.rfind("}")
    return json.loads(text[start:end + 1])


async def build_card(doc: AgentDocument, text: str) -> Dict[str, Any]:
    prompt = f"""Aşağıdaki doküman bir yapay zeka personelin öğrenmesi için yüklendi ("{doc.original_name}").
Yalnızca dokümandaki bilgilere dayanarak Türkçe bir öğrenme kartı hazırla. Bilgi uydurma.
KVKK: kişi adlarını, telefon, e-posta, kimlik gibi kişisel verileri karta yazma; gerekiyorsa "sorumlu usta" gibi rolüyle an.
Sadece şu JSON'u döndür:
{{"summary": "3-5 cümlelik özet",
  "key_points": ["dokümandaki en önemli 5-10 bilgi; her biri tek cümle"],
  "quiz": [{{"question": "dokümana dayalı soru", "options": ["A", "B", "C", "D"], "answer": 0}}]}}
quiz 3-5 çoktan seçmeli soru içersin; answer doğru seçeneğin sırası (0-3).

DOKÜMAN:
{text[:CARD_SOURCE_CHARS]}"""
    result = await llm_gateway.chat(_ctx(doc, "LEARNING_CARD"), [{"role": "user", "content": prompt}],
                                    temperature=0.2, max_tokens=3000, timeout=150)
    card = _parse_json(result.content)
    quiz = []
    for q in card.get("quiz") or []:
        opts = [str(o) for o in (q.get("options") or [])][:6]
        try:
            ans = int(q.get("answer"))
        except (TypeError, ValueError):
            continue
        if q.get("question") and len(opts) >= 2 and 0 <= ans < len(opts):
            quiz.append({"question": str(q["question"]), "options": opts, "answer": ans})
    return {"summary": str(card.get("summary") or "").strip(),
            "key_points": [str(k).strip() for k in (card.get("key_points") or []) if str(k).strip()][:12],
            "quiz": quiz[:6], "model_code": result.model_code}


async def _ocr_enabled(db: AsyncSession, doc: AgentDocument) -> bool:
    if doc.tenant_id is None:
        return True
    from app.services.plan_features import entitlements

    tenant = await db.get(Tenant, doc.tenant_id)
    return bool(tenant and (await entitlements(db, tenant)).ocr_enabled) or bool(tenant and tenant.slug == "recdx_hq")


async def process_document(doc_id: uuid.UUID) -> None:
    """Arka planda çalışır; kendi oturumunu açar. Hata dokümanın durumuna yazılır."""
    async with AsyncSessionLocal() as db:
        doc = await db.get(AgentDocument, doc_id)
        if not doc or doc.status not in ("UPLOADED", "FAILED", "PENDING_APPROVAL", "QUARANTINED"):
            return
        doc.status, doc.error = "PROCESSING", None
        await db.commit()
        try:
            data = await storage.get_object(doc.storage_key)
            ocr_ctx = _ctx(doc, "OCR")

            async def ocr(png: bytes) -> str:
                return await llm_gateway.ocr(ocr_ctx, png)

            media_allowed = await _ocr_enabled(db, doc)  # OCR ve görsel açıklama aynı paket iznine bağlı
            extracted = await extract(data, doc.file_type, ocr if media_allowed else None)
            text = (extracted.text or "").strip()
            is_image_file = doc.file_type in IMAGE_EXTS

            # Görseller (yüklenen resim veya doküman içindeki resimler) görsel modelle açıklanır
            descriptions = []
            if extracted.images and media_allowed:
                vctx = _ctx(doc, "VISION")
                for i, png in enumerate(extracted.images, 1):
                    try:
                        described = await llm_gateway.describe_image(vctx, png, VISION_PROMPT.format(name=doc.original_name))
                    except LLMError:
                        if is_image_file:
                            raise
                        continue  # doküman içindeki bir görsel açıklanamazsa metin yine öğrenilir
                    if described:
                        descriptions.append(described if is_image_file else f"--- Görsel {i} ---\n{described}")
            if is_image_file:
                parts = [f"Görsel açıklaması:\n{descriptions[0]}" if descriptions else "",
                         f"Görseldeki yazılar:\n{text}" if len(text) >= 3 else ""]
                text = "\n\n".join(p for p in parts if p)
            elif descriptions:
                text = text + "\n\n" + "\n\n".join(descriptions)
            doc.image_count = len(descriptions) or None
            if len(text) < 20:
                raise ExtractionError("Dokümandan okunabilir metin veya görsel içerik çıkarılamadı.")
            masked, findings = pii.mask(text)

            sample = masked[:4000] + ("\n...\n" + masked[len(masked) // 2:len(masked) // 2 + 2000] if len(masked) > 8000 else "")
            try:
                guard = await llm_gateway.guard(_ctx(doc, "GUARD"), sample)
            except LLMError as exc:  # guard kesintisi hattı durdurmaz; onay ekranında belirtilir
                guard = {"safe": None, "level": "Unchecked", "categories": [], "error": exc.message}

            await db.execute(sa_delete(DocumentChunk).where(DocumentChunk.document_id == doc.id))
            parts = chunking.split(masked)
            for i, part in enumerate(parts):
                db.add(DocumentChunk(document_id=doc.id, idx=i, content=part))

            doc.extracted_text = masked[:100000]  # KVKK: veritabanında yalnızca maskeli metin tutulur
            doc.masked_text = masked
            doc.pii_findings = findings
            doc.guard_result = guard
            doc.page_count, doc.ocr_pages, doc.chunk_count = extracted.page_count or None, extracted.ocr_pages or None, len(parts)

            if guard.get("safe") is False:
                doc.status = "QUARANTINED"
                doc.error = "İçerik güvenliği kontrolü bu dokümanı riskli buldu (" + (", ".join(guard.get("categories") or []) or guard.get("level")) + "). Doküman öğrenilmeyecek."
            else:
                try:
                    doc.learning_card = await build_card(doc, masked)
                    doc.summary = doc.learning_card.get("summary") or masked[:300]
                except (LLMError, ValueError, KeyError) as exc:
                    doc.learning_card = None
                    doc.summary = masked[:300]
                    doc.error = f"Öğrenme kartı üretilemedi ({getattr(exc, 'message', exc)}); doküman yine de incelenip onaylanabilir."
                doc.status = "PENDING_APPROVAL"
            await db.commit()
        except (ExtractionError, LLMError) as exc:
            await db.rollback()
            doc = await db.get(AgentDocument, doc_id)
            doc.status, doc.error = "FAILED", getattr(exc, "message", None) or str(exc)
            await db.commit()
        except Exception as exc:  # beklenmeyen hata da dokümana yazılır
            logger.exception("Doküman işlenemedi (%s)", doc_id)
            await db.rollback()
            doc = await db.get(AgentDocument, doc_id)
            doc.status, doc.error = "FAILED", "Doküman işlenirken beklenmeyen bir hata oluştu."
            await db.commit()


# ---------------------------------------------------------------- test, onay, ret, silme
async def run_test(db: AsyncSession, doc: AgentDocument) -> Dict[str, Any]:
    """Öğrenme kartındaki soruları yalnızca dokümanı bağlam vererek modele sorar; doğru cevap oranını ölçer."""
    quiz = (doc.learning_card or {}).get("quiz") or []
    if not quiz:
        raise HTTPException(status_code=400, detail="Bu dokümanın test soruları yok.")
    questions = "\n".join(f"{i + 1}. {q['question']}\n" + "\n".join(f"   {chr(65 + j)}) {o}" for j, o in enumerate(q["options"]))
                          for i, q in enumerate(quiz))
    prompt = f"""Aşağıdaki dokümanı oku ve soruları yalnızca dokümana göre cevapla.
Sadece JSON döndür: {{"answers": ["A", "C", ...]}} (soru sırasıyla, her biri tek harf).

DOKÜMAN:
{(doc.masked_text or '')[:CARD_SOURCE_CHARS]}

SORULAR:
{questions}"""
    result = await llm_gateway.chat(_ctx(doc, "LEARNING_TEST", use_agent_model=True), [{"role": "user", "content": prompt}],
                                    temperature=0, max_tokens=400, timeout=120)
    try:
        answers = [str(a).strip().upper()[:1] for a in _parse_json(result.content).get("answers") or []]
    except (ValueError, KeyError):
        answers = re.findall(r"\b([A-F])\b", result.content.upper())
    details = []
    for i, q in enumerate(quiz):
        given = answers[i] if i < len(answers) else None
        details.append({"question": q["question"], "expected": chr(65 + q["answer"]), "given": given,
                        "correct": given == chr(65 + q["answer"])})
    correct = sum(d["correct"] for d in details)
    doc.test_result = {"score": correct, "total": len(quiz), "percent": round(correct * 100 / len(quiz)),
                       "model_code": result.model_code, "tested_at": _now().isoformat(), "details": details}
    await db.commit()
    return doc.test_result


async def _drop_vectors(db: AsyncSession, doc: AgentDocument) -> None:
    from app.services.collective_memory import collective_memory

    chunks = (await db.execute(select(DocumentChunk).where(DocumentChunk.document_id == doc.id))).scalars().all()
    await collective_memory.delete_points([str(c.qdrant_point_id) for c in chunks if c.qdrant_point_id])
    for c in chunks:
        c.qdrant_point_id = None
    if doc.memory_item_id:
        item = await db.get(MemoryItem, doc.memory_item_id)
        doc.memory_item_id = None
        if item:
            await db.delete(item)


async def approve(db: AsyncSession, doc: AgentDocument, actor_id: uuid.UUID, card: Optional[Dict[str, Any]] = None) -> AgentDocument:
    from app.services.collective_memory import collective_memory

    if doc.status != "PENDING_APPROVAL":
        raise HTTPException(status_code=409, detail="Yalnızca onay bekleyen dokümanlar onaylanabilir.")
    if card:
        doc.learning_card = {**(doc.learning_card or {}), **{k: v for k, v in card.items() if k in ("summary", "key_points", "quiz")}}
        doc.summary = (doc.learning_card.get("summary") or doc.summary or "")[:2000]

    chunks = (await db.execute(select(DocumentChunk).where(DocumentChunk.document_id == doc.id)
                               .order_by(DocumentChunk.idx))).scalars().all()
    payload = {"tenant_id": str(doc.tenant_id) if doc.tenant_id else "PLATFORM", "scope": SCOPE_BY_LAYER[doc.layer],
               "layer": doc.layer, "agent_id": str(doc.agent_id) if doc.agent_id else None,
               "job_title_id": str(doc.job_title_id) if doc.job_title_id else None, "document_id": str(doc.id),
               "source_reference": doc.original_name, "version": doc.version}
    indexed = []
    try:
        for c in chunks:
            point = await collective_memory.index_chunk(embed_tenant_id=doc.tenant_id, actor_id=doc.agent_id,
                                                        content=c.content, payload={**payload, "chunk_idx": c.idx})
            c.qdrant_point_id = uuid.UUID(point)
            indexed.append(point)
    except LLMError:
        await collective_memory.delete_points(indexed)  # yarım kalan vektörleme geri alınır
        await db.rollback()
        raise

    if doc.layer == "AGENT" and doc.tenant_id:  # mevcut hafıza ekranında görünsün
        agent = await db.get(Actor, doc.agent_id)
        item = MemoryItem(tenant_id=doc.tenant_id, scope="AGENT", agent_id=doc.agent_id, source_reference=doc.original_name,
                          content=(doc.summary or "")[:20000], status="APPROVED", confidence_score=1.0,
                          metadata_json={"document_id": str(doc.id), "version": doc.version, "chunks": len(chunks),
                                         "agent_name": agent.display_name if agent else None})
        db.add(item)
        await db.flush()
        doc.memory_item_id = item.id

    if doc.previous_document_id:
        prev = await db.get(AgentDocument, doc.previous_document_id)
        if prev and prev.status == "APPROVED":
            await _drop_vectors(db, prev)
            prev.status = "SUPERSEDED"
    doc.status, doc.approved_by_actor_id, doc.approved_at, doc.error = "APPROVED", actor_id, _now(), None
    await db.commit()
    return doc


async def reject(db: AsyncSession, doc: AgentDocument, reason: Optional[str]) -> AgentDocument:
    if doc.status not in ("PENDING_APPROVAL", "QUARANTINED", "FAILED"):
        raise HTTPException(status_code=409, detail="Bu doküman reddedilemez.")
    doc.status, doc.error = "REJECTED", (reason or "Yetkili tarafından reddedildi.")[:500]
    await db.commit()
    return doc


async def delete(db: AsyncSession, doc: AgentDocument) -> None:
    """Vektörler, hafıza kaydı ve depodaki dosya silinir; denetim için kayıt DELETED olarak kalır."""
    await _drop_vectors(db, doc)
    await db.execute(sa_delete(DocumentChunk).where(DocumentChunk.document_id == doc.id))
    if doc.storage_key:
        await storage.delete_object(doc.storage_key)
    doc.status, doc.extracted_text, doc.masked_text, doc.learning_card = "DELETED", None, None, None
    await db.commit()
