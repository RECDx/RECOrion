"""
Sektör bilgi paketleri uçları (İSTEK #751).

Merkez (RECDx Süper Admin):
- GET  /system/sector-packs                    paketler: taslak içerik + yayın bilgisi
- POST /system/sector-packs                    yeni paket (taslak)
- PUT  /system/sector-packs/{id}               taslağı düzenle (yayındaki sürüm değişmez)
- POST /system/sector-packs/{id}/publish       uzman kontrolü beyanıyla yayımla → yeni sürüm
- POST /system/sector-packs/{id}/withdraw      yayından geri çek (şirketler ve Beyin AI artık kullanmaz)
- GET  /system/sector-packs/{id}/suggestions   #753 şirketlerin plana sık eklediği/çıkardığı adımlar (k-anonim toplam)
Şirket:
- GET  /company/{tid}/sector-packs             yayımlanmış paketler (içerik) + şirketin ekleri
- PUT  /company/{tid}/sector-packs/{code}      şirketin ek soruları ve sık atlanan maddeleri (tenant:manage; yalnız bu şirkette)
Proje:
- GET  /projects/{id}/sector-pack              seçili/önerilen paket ve seçenekler
- PUT  /projects/{id}/sector-pack              paketi seç ya da "paket yok" (proje yöneticisi; taslak/planlama)
"""
import uuid
from datetime import date, datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import CurrentUser, ensure_tenant_content, get_current_user
from app.db.models import SectorPack, Tenant
from app.db.session import get_db
from app.services import projects as psvc
from app.services import sector_packs as ssvc

router = APIRouter(tags=["Sektör Paketleri"])


def _super(user: CurrentUser) -> None:
    if not user.is_super_admin:
        raise HTTPException(status_code=403, detail="Bu işlem yalnızca RECDx Süper Admin içindir.")


def _admin_out(p: SectorPack) -> Dict[str, Any]:
    pub = p.published or {}
    return {"id": str(p.id), "code": p.code, "title": p.title, "description": p.description,
            "sector_codes": p.sector_codes or [], "keywords": p.keywords or [],
            "draft_content": ssvc.clean_content((p.draft or {}).get("content")), "draft_updated_at": p.draft_updated_at,
            "published": {k: pub.get(k) for k in ("version", "published_at", "reviewer_name", "checked_at", "review_note", "withdrawn", "history")}
            if pub else None, "changed_since_publish": ssvc.changed_since_publish(p)}


async def _pack(db: AsyncSession, pack_id: uuid.UUID) -> SectorPack:
    p = await db.get(SectorPack, pack_id)
    if not p:
        raise HTTPException(status_code=404, detail="Paket bulunamadı.")
    return p


@router.get("/system/sector-packs")
async def admin_list(user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    _super(user)
    return [_admin_out(p) for p in (await db.execute(select(SectorPack).order_by(SectorPack.title))).scalars().all()]


class PackIn(BaseModel):
    code: str = Field(..., pattern="^[a-z][a-z0-9-]{1,39}$")
    title: str = Field(..., min_length=2, max_length=120)
    description: Optional[str] = Field(None, max_length=2000)


@router.post("/system/sector-packs", status_code=201)
async def admin_create(payload: PackIn, user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    _super(user)
    if (await db.execute(select(SectorPack.id).where(SectorPack.code == payload.code))).first():
        raise HTTPException(status_code=409, detail="Bu kodla paket var.")
    p = SectorPack(code=payload.code, title=payload.title.strip(), description=payload.description, sector_codes=[], keywords=[],
                   draft={"content": ssvc.clean_content({})})
    db.add(p)
    await db.commit()
    return _admin_out(p)


class DraftIn(BaseModel):
    title: Optional[str] = Field(None, min_length=2, max_length=120)
    description: Optional[str] = Field(None, max_length=2000)
    sector_codes: Optional[List[str]] = None
    keywords: Optional[List[str]] = None
    content: Optional[Dict[str, Any]] = None


@router.put("/system/sector-packs/{pack_id}")
async def admin_update(pack_id: uuid.UUID, payload: DraftIn, user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    _super(user)
    p = await _pack(db, pack_id)
    if payload.title:
        p.title = payload.title.strip()
    if payload.description is not None:
        p.description = payload.description
    if payload.sector_codes is not None or payload.keywords is not None:
        codes, words = ssvc.clean_meta(payload.sector_codes if payload.sector_codes is not None else p.sector_codes,
                                       payload.keywords if payload.keywords is not None else p.keywords)
        p.sector_codes, p.keywords = codes, words
    if payload.content is not None:
        p.draft = {"content": ssvc.clean_content(payload.content)}
        p.draft_updated_at = datetime.now(timezone.utc)
    await db.commit()
    return _admin_out(p)


class PublishIn(BaseModel):
    expert_confirmed: bool
    reviewer_name: str = Field(..., min_length=3, max_length=120)
    checked_at: date
    note: Optional[str] = Field(None, max_length=2000)


@router.post("/system/sector-packs/{pack_id}/publish")
async def admin_publish(pack_id: uuid.UUID, payload: PublishIn, user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    _super(user)
    if not payload.expert_confirmed:
        raise HTTPException(status_code=422, detail="Yayın için paketin bu iş kolunda yetkin bir uzman tarafından kontrol edildiğini onaylayın.")
    if payload.checked_at > date.today():
        raise HTTPException(status_code=422, detail="Kontrol tarihi ileri bir tarih olamaz.")
    p = await _pack(db, pack_id)
    ssvc.publish(p, user.actor_id, payload.reviewer_name, payload.checked_at, payload.note)
    await db.commit()
    return _admin_out(p)


@router.post("/system/sector-packs/{pack_id}/withdraw")
async def admin_withdraw(pack_id: uuid.UUID, user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    _super(user)
    p = await _pack(db, pack_id)
    if not ssvc.live(p):
        raise HTTPException(status_code=409, detail="Paket yayında değil.")
    p.published = {**p.published, "withdrawn": True, "withdrawn_at": datetime.now(timezone.utc).isoformat()}
    await db.commit()
    return _admin_out(p)


@router.get("/system/sector-packs/{pack_id}/suggestions")
async def admin_suggestions(pack_id: uuid.UUID, user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """#753: yöneticilerin bu paketle yapılan Beyin planlarına sık eklediği/çıkardığı adımlar — şirketler arası, k-anonim
    (en az k şirket, tek şirket baskın değil). Tekil kayıt ve şirket adı yok; uzman uygun bulursa taslağa elle ekler."""
    from app.services import brain_learning

    _super(user)
    p = await _pack(db, pack_id)
    return await brain_learning.sector_pack_suggestions(db, p.code)


# ---------------------------------------------------------------- şirket
@router.get("/company/{tenant_id}/sector-packs")
async def company_list(tenant_id: uuid.UUID, user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    ensure_tenant_content(user, tenant_id)
    tenant = await db.get(Tenant, tenant_id)
    return [ssvc.public_out(p, tenant, content=True) for p in await ssvc.published_packs(db)]


class ExtrasIn(BaseModel):
    questions: List[Dict[str, Any]] = Field(default_factory=list)
    missed: List[str] = Field(default_factory=list)


@router.put("/company/{tenant_id}/sector-packs/{code}")
async def company_extras(tenant_id: uuid.UUID, code: str, payload: ExtrasIn, user: CurrentUser = Depends(get_current_user),
                         db: AsyncSession = Depends(get_db)):
    ensure_tenant_content(user, tenant_id)
    p = (await db.execute(select(SectorPack).where(SectorPack.code == code))).scalar_one_or_none()
    if not ssvc.live(p):
        raise HTTPException(status_code=404, detail="Paket bulunamadı.")
    tenant = await db.get(Tenant, tenant_id)
    extras = ssvc.save_extras(tenant, code, payload.model_dump())
    await db.commit()
    return extras


# ---------------------------------------------------------------- proje
async def _project_view(db: AsyncSession, project) -> Dict[str, Any]:
    tenant = await db.get(Tenant, project.tenant_id)
    pack, auto = await ssvc.for_project(db, project, tenant)
    return {**ssvc.project_out(pack, auto),
            "options": [{"code": p.code, "title": p.title, "version": (p.published or {}).get("version")} for p in await ssvc.published_packs(db)]}


@router.get("/projects/{project_id}/sector-pack")
async def project_pack(project_id: uuid.UUID, user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    project = await psvc.load(db, user, project_id)
    return await _project_view(db, project)


class ProjectPackIn(BaseModel):
    code: Optional[str] = Field(None, max_length=40)


@router.put("/projects/{project_id}/sector-pack")
async def set_project_pack(project_id: uuid.UUID, payload: ProjectPackIn, user: CurrentUser = Depends(get_current_user),
                           db: AsyncSession = Depends(get_db)):
    project = await psvc.load(db, user, project_id, manage=True)
    if project.status not in ("DRAFT", "PLANNING"):
        raise HTTPException(status_code=409, detail="Sektör paketi yalnız taslak veya planlama aşamasındaki projede değiştirilir.")
    if payload.code:
        p = (await db.execute(select(SectorPack).where(SectorPack.code == payload.code))).scalar_one_or_none()
        if not ssvc.live(p):
            raise HTTPException(status_code=404, detail="Paket bulunamadı.")
    ssvc.select_for_project(project, payload.code or None)
    from app.services import task_flow

    await task_flow.log(db, project, None, "SECTOR_PACK_SET", user.actor_id,
                        f"Sektör paketi: {payload.code or 'yok'}", {"code": payload.code or None})
    await db.commit()
    return await _project_view(db, project)
