"""
Proje maliyet kalemleri ve bütçe uçları (ADIM 7.5.3). Proje yöneticisi (veya project:manage) yönetir.
Kalemler proje kapanana kadar değiştirilebilir. Belge (fatura vb.) öğrenme hattına girmez; nesne deposunda ayrı saklanır.
"""
import uuid
from datetime import date
from decimal import Decimal
from typing import Optional
from urllib.parse import quote

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import Response
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import CurrentUser, get_current_user
from app.db.models import ProjectCostItem, Task
from app.db.session import get_db
from app.services import costs, storage
from app.services import projects as psvc

router = APIRouter(prefix="/projects", tags=["Proje Maliyeti"])

CLOSED = ("COMPLETED", "CANCELLED")
MAX_ATTACHMENT = 20 * 1024 * 1024
ATTACHMENT_TYPES = {"pdf": "application/pdf", "png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg",
                    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"}


class ItemIn(BaseModel):
    category: str = Field(pattern="^(MATERYAL|DANISMANLIK|EGITIM|LISANS|SEYAHAT|DONANIM|DIGER)$")
    description: str = Field(min_length=2, max_length=500)
    quantity: Decimal = Field(gt=0, le=1_000_000)
    unit: Optional[str] = Field(None, max_length=24)
    unit_price_try: Decimal = Field(ge=0, le=1_000_000_000)
    incurred_on: Optional[date] = None
    task_id: Optional[uuid.UUID] = None


async def _project(db, user, project_id, editable=True):
    project = await psvc.load(db, user, project_id, manage=True)
    if editable and project.status in CLOSED:
        raise HTTPException(status_code=409, detail="Kapanmış projenin maliyet kalemleri değiştirilemez.")
    return project


async def _check_task(db, project, task_id):
    if task_id:
        task = await db.get(Task, task_id)
        if not task or task.project_id != project.id:
            raise HTTPException(status_code=422, detail="İş adımı bu projeye ait değil.")


async def _item(db, project, item_id) -> ProjectCostItem:
    item = await db.get(ProjectCostItem, item_id)
    if not item or item.project_id != project.id:
        raise HTTPException(status_code=404, detail="Maliyet kalemi bulunamadı.")
    return item


def _amount(q: Decimal, p: Decimal) -> Decimal:
    return (q * p).quantize(Decimal("0.01"))


@router.get("/{project_id}/cost-items")
async def list_items(project_id: uuid.UUID, user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    project = await _project(db, user, project_id, editable=False)
    return (await costs.project_costs(db, project))["items"]


@router.post("/{project_id}/cost-items", status_code=201)
async def add_item(project_id: uuid.UUID, payload: ItemIn, user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    project = await _project(db, user, project_id)
    await _check_task(db, project, payload.task_id)
    item = ProjectCostItem(tenant_id=project.tenant_id, project_id=project.id, task_id=payload.task_id, category=payload.category,
                           description=payload.description.strip(), quantity=payload.quantity, unit=(payload.unit or None),
                           unit_price_try=payload.unit_price_try, amount_try=_amount(payload.quantity, payload.unit_price_try),
                           incurred_on=payload.incurred_on or date.today(), created_by_actor_id=user.actor_id)
    db.add(item)
    await db.commit()
    return costs.item_out(item)


@router.put("/{project_id}/cost-items/{item_id}")
async def update_item(project_id: uuid.UUID, item_id: uuid.UUID, payload: ItemIn, user: CurrentUser = Depends(get_current_user),
                      db: AsyncSession = Depends(get_db)):
    project = await _project(db, user, project_id)
    item = await _item(db, project, item_id)
    await _check_task(db, project, payload.task_id)
    item.category, item.description, item.quantity = payload.category, payload.description.strip(), payload.quantity
    item.unit, item.unit_price_try, item.task_id = (payload.unit or None), payload.unit_price_try, payload.task_id
    item.amount_try = _amount(payload.quantity, payload.unit_price_try)
    item.incurred_on = payload.incurred_on or item.incurred_on
    await db.commit()
    return costs.item_out(item)


@router.delete("/{project_id}/cost-items/{item_id}")
async def delete_item(project_id: uuid.UUID, item_id: uuid.UUID, user: CurrentUser = Depends(get_current_user),
                      db: AsyncSession = Depends(get_db)):
    project = await _project(db, user, project_id)
    item = await _item(db, project, item_id)
    if item.attachment_path:
        try:
            await storage.delete_object(item.attachment_path)
        except Exception:
            pass
    await db.delete(item)
    await db.commit()
    return {"success": True}


@router.post("/{project_id}/cost-items/{item_id}/attachment")
async def upload_attachment(project_id: uuid.UUID, item_id: uuid.UUID, file: UploadFile = File(...),
                            user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    project = await _project(db, user, project_id)
    item = await _item(db, project, item_id)
    ext = (file.filename or "").rsplit(".", 1)[-1].lower()
    if ext not in ATTACHMENT_TYPES:
        raise HTTPException(status_code=422, detail="Belge PDF, PNG, JPG, XLSX veya DOCX olmalı.")
    data = await file.read()
    if len(data) > MAX_ATTACHMENT:
        raise HTTPException(status_code=413, detail="Belge en fazla 20 MB olabilir.")
    key = f"cost-items/{project.id}/{item.id}.{ext}"
    if item.attachment_path and item.attachment_path != key:
        try:
            await storage.delete_object(item.attachment_path)
        except Exception:
            pass
    await storage.put_object(key, data, ATTACHMENT_TYPES[ext])
    item.attachment_path, item.attachment_name = key, (file.filename or f"belge.{ext}")[:255]
    await db.commit()
    return costs.item_out(item)


@router.get("/{project_id}/cost-items/{item_id}/attachment")
async def download_attachment(project_id: uuid.UUID, item_id: uuid.UUID, user: CurrentUser = Depends(get_current_user),
                              db: AsyncSession = Depends(get_db)):
    project = await _project(db, user, project_id, editable=False)
    item = await _item(db, project, item_id)
    if not item.attachment_path:
        raise HTTPException(status_code=404, detail="Bu kalemin belgesi yok.")
    data = await storage.get_object(item.attachment_path)
    ext = item.attachment_path.rsplit(".", 1)[-1]
    return Response(content=data, media_type=ATTACHMENT_TYPES.get(ext, "application/octet-stream"),
                    headers={"Content-Disposition": f"attachment; filename*=UTF-8''{quote(item.attachment_name or 'belge')}"})


class BudgetIn(BaseModel):
    budget_try: Optional[Decimal] = Field(None, ge=0, le=100_000_000_000)
    budget_note: Optional[str] = Field(None, max_length=2000)


@router.put("/{project_id}/budget")
async def set_budget(project_id: uuid.UUID, payload: BudgetIn, user: CurrentUser = Depends(get_current_user),
                     db: AsyncSession = Depends(get_db)):
    project = await _project(db, user, project_id)
    project.budget_try, project.budget_note = payload.budget_try, (payload.budget_note or None)
    await db.commit()
    return {"budget_try": float(project.budget_try) if project.budget_try is not None else None, "budget_note": project.budget_note}
