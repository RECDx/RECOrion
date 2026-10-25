"""
Toplantı kaydından proje taslağı uçları (ADIM 11.3). Yetki: project:create; KVKK: şirket içeriği, RECDx göremez.

- POST /company/{tid}/meetings                  ses/video yükle (dosya veya tarayıcı kaydı) → arka planda yazıya + taslak
- GET  /company/{tid}/meetings                  son kayıtlarım
- GET  /company/{tid}/meetings/{id}             durum, maskeli metin, taslak
- POST /company/{tid}/meetings/{id}/project     (düzeltilmiş) taslaktan proje oluştur; plan taslak gelir, yönetici onaylar
"""
import shutil
import uuid
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import CurrentUser, ensure_tenant_content, get_current_user
from app.db.models import MeetingRecording, Project
from app.db.session import get_db
from app.services import meetings as msvc

router = APIRouter(tags=["Toplantıdan Proje"])
ALLOWED_PREFIXES = ("audio/", "video/")
ALLOWED_EXT = {".mp3", ".m4a", ".wav", ".webm", ".ogg", ".oga", ".opus", ".mp4", ".mov", ".mkv", ".aac", ".flac", ".wma", ".3gp"}


async def _rec(db: AsyncSession, user: CurrentUser, tenant_id: uuid.UUID, rid: uuid.UUID) -> MeetingRecording:
    ensure_tenant_content(user, tenant_id, "project:create")
    rec = await db.get(MeetingRecording, rid)
    # Kayıt, yükleyen kişinin (veya proje yönetim yetkilisinin) — toplantı içeriği ekip dışına açılmaz
    if not rec or rec.tenant_id != tenant_id or (rec.created_by_actor_id != user.actor_id and not user.has("project:manage")):
        raise HTTPException(status_code=404, detail="Toplantı kaydı bulunamadı.")
    return rec


@router.post("/company/{tenant_id}/meetings", status_code=202)
async def upload(tenant_id: uuid.UUID, file: UploadFile = File(...), title: str = Form("", max_length=200),
                 source: str = Form("UPLOAD"), user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    ensure_tenant_content(user, tenant_id, "project:create")
    from app.db.models import Plan, Tenant
    from app.services import recai

    tenant = await db.get(Tenant, tenant_id)  # #349: RECAi Ses paketinde olmalı
    if tenant and tenant.slug != "recdx_hq" and tenant.plan_id and not recai.plan_capabilities(await db.get(Plan, tenant.plan_id)).get("SES"):
        raise HTTPException(status_code=403, detail="RECAi Ses (toplantıyı yazıya çevirme) paketinizde yer almıyor.")
    name = (file.filename or "kayit").strip()
    ext = ("." + name.rsplit(".", 1)[-1].lower()) if "." in name else ""
    if not ((file.content_type or "").startswith(ALLOWED_PREFIXES) or ext in ALLOWED_EXT):
        raise HTTPException(status_code=422, detail="Yalnızca ses veya video dosyası yüklenebilir (mp3, m4a, wav, webm, mp4…).")
    rec = MeetingRecording(tenant_id=tenant_id, created_by_actor_id=user.actor_id, title=(title.strip() or name)[:200],
                           source="BROWSER" if source == "BROWSER" else "UPLOAD", status="PROCESSING", stage="Kayıt alındı…")
    db.add(rec)
    await db.flush()
    work = msvc.WORK_DIR / str(rec.id)
    work.mkdir(parents=True, exist_ok=True)
    dest = work / f"kaynak{ext or '.bin'}"
    size = 0
    with dest.open("wb") as f:
        while chunk := await file.read(1024 * 1024):
            size += len(chunk)
            if size > msvc.MAX_BYTES:
                f.close()
                shutil.rmtree(work, ignore_errors=True)
                raise HTTPException(status_code=413, detail=f"Dosya en fazla {msvc.MAX_BYTES // (1024 * 1024)} MB olabilir.")
            f.write(chunk)
    if size == 0:
        shutil.rmtree(work, ignore_errors=True)
        raise HTTPException(status_code=422, detail="Dosya boş.")
    await db.commit()
    msvc.start(rec.id, tenant_id, user.actor_id, dest)
    return msvc.out(rec)


@router.get("/company/{tenant_id}/meetings")
async def my_meetings(tenant_id: uuid.UUID, user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    ensure_tenant_content(user, tenant_id, "project:create")
    rows = (await db.execute(select(MeetingRecording).where(MeetingRecording.tenant_id == tenant_id,
                                                            MeetingRecording.created_by_actor_id == user.actor_id)
                             .order_by(MeetingRecording.created_at.desc()).limit(20))).scalars().all()
    return [msvc.out(r) for r in rows]


@router.get("/company/{tenant_id}/meetings/{rec_id}")
async def get_meeting(tenant_id: uuid.UUID, rec_id: uuid.UUID, user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return msvc.out(await _rec(db, user, tenant_id, rec_id), full=True)


class MeetingProjectIn(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    kind: str = Field("PROJECT", pattern="^(PROJECT|CASE)$")
    description: Optional[str] = Field(None, max_length=3000)
    requirements: Optional[str] = Field(None, max_length=8000)
    include_steps: bool = True


@router.post("/company/{tenant_id}/meetings/{rec_id}/project")
async def meeting_to_project(tenant_id: uuid.UUID, rec_id: uuid.UUID, payload: MeetingProjectIn, user: CurrentUser = Depends(get_current_user),
                             db: AsyncSession = Depends(get_db)):
    from app.api.v1.projects import ProjectCreate, create_project

    rec = await _rec(db, user, tenant_id, rec_id)
    if rec.status != "READY":
        raise HTTPException(status_code=409, detail="Bu kayıttan proje oluşturulamaz (taslak hazır değil veya zaten kullanıldı).")
    created = await create_project(ProjectCreate(tenant_id=tenant_id, name=payload.name, kind=payload.kind, description=payload.description,
                                                 requirements=payload.requirements, manager_actor_id=user.actor_id), user, db)
    project = await db.get(Project, uuid.UUID(str(created["id"])))
    rec = await db.get(MeetingRecording, rec_id)
    plan = (rec.draft or {}).get("plan") or {}
    if payload.include_steps and plan.get("steps"):
        project.plan = {**plan, "approved": False, "from_meeting": {"id": str(rec.id), "title": rec.title}}
    rec.status, rec.project_id = "USED", project.id
    await db.commit()
    return {**created, "steps": len(plan.get("steps") or []) if payload.include_steps else 0}
