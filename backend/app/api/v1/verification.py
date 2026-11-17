"""
Teslimata göre doğrulama uçları (İSTEK #752).

- GET /projects/{id}/verification              kapsam raporu: "N teslimattan M tanesi doğrulandı" + adım bazında durum
- POST /tasks/{id}/verification/evidence       kanıt ekle (not, bağlantı ya da Proje Eki)
- PUT  /tasks/{id}/verification/measure        ölçülen değeri gir
- PUT  /tasks/{id}/verification/checklist      kontrol listesi maddelerini işaretle
Kayıtları adımın sorumlusu (insan), onaylayıcısı, kontrol personeli ya da proje yöneticisi girer; adım bitmişse değişmez.
"""
import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.core.security import CurrentUser, forbidden, get_current_user
from app.db.models import Task
from app.db.session import get_db
from app.services import projects as psvc
from app.services import task_flow
from app.services import verification as vsvc
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(tags=["Teslimat Doğrulaması"])


@router.get("/projects/{project_id}/verification")
async def project_coverage(project_id: uuid.UUID, user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    project = await psvc.load(db, user, project_id)
    return await vsvc.coverage(db, project)


async def _editable(db: AsyncSession, user: CurrentUser, task_id: uuid.UUID, vtype: Optional[str] = None):
    task = await db.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="İş adımı bulunamadı.")
    project = await psvc.load(db, user, task.project_id)
    allowed = (user.has("project:manage") or project.manager_actor_id == user.actor_id
               or user.actor_id in (task.assignee_actor_id, task.approver_actor_id, task.reviewer_actor_id))
    if not allowed:
        raise forbidden("Doğrulama kaydını adımın sorumlusu, onaylayıcısı ya da proje yöneticisi girer.")
    if not task.verification:
        raise HTTPException(status_code=409, detail="Bu adım için doğrulama yöntemi tanımlanmamış.")
    if task.status in ("DONE", "CANCELLED"):
        raise HTTPException(status_code=409, detail="Adım kapandı; doğrulama kaydı değiştirilemez.")
    if vtype and task.verification.get("type") not in vtype.split("|"):
        raise HTTPException(status_code=409, detail="Bu adımın doğrulama türü bu kaydı kabul etmiyor.")
    return task, project


async def _done(db, project, task, user, kind, note):
    await task_flow.log(db, project, task, kind, user.actor_id, note[:1000])
    await db.commit()
    st, why = await vsvc.evaluate(db, project, task)
    return {"status": st, "status_label": vsvc.STATUS_TR[st], "reason": why, "verification": task.verification}


class EvidenceIn(BaseModel):
    kind: str = Field(..., pattern="^(note|link|document)$")
    text: Optional[str] = Field(None, max_length=1000)
    url: Optional[str] = Field(None, max_length=1000, pattern=r"^https?://")
    document_id: Optional[uuid.UUID] = None


@router.post("/tasks/{task_id}/verification/evidence")
async def add_evidence(task_id: uuid.UUID, payload: EvidenceIn, user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    task, project = await _editable(db, user, task_id)
    if payload.kind == "note" and len((payload.text or "").strip()) < 5:
        raise HTTPException(status_code=422, detail="Kanıt notu en az 5 karakter olmalı.")
    if payload.kind == "link" and not payload.url:
        raise HTTPException(status_code=422, detail="Bağlantı adresi (https://…) gerekli.")
    if payload.kind == "document" and not payload.document_id:
        raise HTTPException(status_code=422, detail="Proje Eki seçin.")
    try:
        await vsvc.add_evidence(db, task, user.actor_id, payload.kind, (payload.text or "").strip(), payload.url,
                                str(payload.document_id) if payload.document_id else None)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    label = {"note": "not", "link": "bağlantı", "document": "Proje Eki"}[payload.kind]
    return await _done(db, project, task, user, "EVIDENCE_ADDED", f"Kanıt eklendi ({label}): {payload.text or payload.url or ''}")


class MeasureIn(BaseModel):
    value: str = Field(..., min_length=1, max_length=60)
    unit: Optional[str] = Field(None, max_length=30)
    note: Optional[str] = Field(None, max_length=500)


@router.put("/tasks/{task_id}/verification/measure")
async def set_measure(task_id: uuid.UUID, payload: MeasureIn, user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    task, project = await _editable(db, user, task_id, "MEASURE")
    vsvc.set_measure(task, user.actor_id, payload.value.strip(), payload.unit, payload.note)
    return await _done(db, project, task, user, "MEASURE_RECORDED", f"Ölçüm: {payload.value} {payload.unit or ''}".strip())


class ChecklistIn(BaseModel):
    items: List[bool] = Field(..., max_length=50)


@router.put("/tasks/{task_id}/verification/checklist")
async def set_checklist(task_id: uuid.UUID, payload: ChecklistIn, user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    task, project = await _editable(db, user, task_id, "CHECKLIST")
    v = vsvc.set_checklist(task, user.actor_id, payload.items)
    done = sum(1 for i in v.get("checklist") or [] if i.get("ok"))
    return await _done(db, project, task, user, "CHECKLIST_UPDATED", f"Kontrol listesi: {done}/{len(v.get('checklist') or [])} madde işaretli")
