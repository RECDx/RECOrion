"""
Mevzuat bilgi paketleri uçları (ADIM 11.2).

Süper Admin (RECDx):
- GET  /system/regulation-packs                  paketler: taslak kartlar + yayın bilgisi
- POST /system/regulation-packs                  yeni paket (taslak)
- PUT  /system/regulation-packs/{id}             taslağı düzenle (yayındaki sürüm değişmez)
- POST /system/regulation-packs/{id}/publish     uzman kontrolü beyanıyla yayımla (kontrol eden, tarih, not) → yeni sürüm
Şirket:
- GET  /company/{tid}/regulation-packs           yayımlanmış paketler ve şirkette açık olup olmadığı
- GET  /company/{tid}/regulation-packs/{id}      yayımlanmış kartlar
- PUT  /company/{tid}/regulation-packs/{id}      paketi aç/kapat (tenant:manage)
"""
import uuid
from datetime import date, datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import CurrentUser, ensure_tenant_content, get_current_user
from app.db.models import RegulationPack, TenantRegulationPack
from app.db.session import get_db
from app.services import regulations as rsvc

router = APIRouter(tags=["Mevzuat Paketleri"])


def _super(user: CurrentUser) -> None:
    if not user.is_super_admin:
        raise HTTPException(status_code=403, detail="Bu işlem yalnızca RECDx Süper Admin içindir.")


def _admin_out(p: RegulationPack) -> Dict[str, Any]:
    pub = p.published or {}
    return {"id": str(p.id), "code": p.code, "title": p.title, "description": p.description,
            "draft_cards": (p.draft or {}).get("cards") or [], "draft_updated_at": p.draft_updated_at,
            "published": {k: pub.get(k) for k in ("version", "published_at", "reviewer_name", "checked_at", "review_note")} if pub else None,
            "published_card_count": len(pub.get("cards") or []), "changed_since_publish": rsvc.changed_since_publish(p)}


@router.get("/system/regulation-packs")
async def admin_list(user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    _super(user)
    rows = (await db.execute(select(RegulationPack).order_by(RegulationPack.title))).scalars().all()
    return [_admin_out(p) for p in rows]


class PackIn(BaseModel):
    code: str = Field(..., pattern="^[a-z][a-z0-9-]{1,39}$")
    title: str = Field(..., min_length=2, max_length=120)
    description: Optional[str] = Field(None, max_length=2000)


@router.post("/system/regulation-packs", status_code=201)
async def admin_create(payload: PackIn, user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    _super(user)
    if (await db.execute(select(RegulationPack.id).where(RegulationPack.code == payload.code))).first():
        raise HTTPException(status_code=409, detail="Bu kodla paket var.")
    p = RegulationPack(code=payload.code, title=payload.title.strip(), description=payload.description, draft={"cards": []})
    db.add(p)
    await db.commit()
    return _admin_out(p)


class DraftIn(BaseModel):
    title: Optional[str] = Field(None, min_length=2, max_length=120)
    description: Optional[str] = Field(None, max_length=2000)
    cards: Optional[List[Dict[str, Any]]] = None


@router.put("/system/regulation-packs/{pack_id}")
async def admin_update(pack_id: uuid.UUID, payload: DraftIn, user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    _super(user)
    p = await db.get(RegulationPack, pack_id)
    if not p:
        raise HTTPException(status_code=404, detail="Paket bulunamadı.")
    if payload.title:
        p.title = payload.title.strip()
    if payload.description is not None:
        p.description = payload.description
    if payload.cards is not None:
        p.draft = {"cards": rsvc.clean_cards(payload.cards)}
        p.draft_updated_at = datetime.now(timezone.utc)
    await db.commit()
    return _admin_out(p)


class PublishIn(BaseModel):
    expert_confirmed: bool
    reviewer_name: str = Field(..., min_length=3, max_length=120)
    checked_at: date
    note: Optional[str] = Field(None, max_length=2000)


@router.post("/system/regulation-packs/{pack_id}/publish")
async def admin_publish(pack_id: uuid.UUID, payload: PublishIn, user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    _super(user)
    if not payload.expert_confirmed:
        raise HTTPException(status_code=422, detail="Yayın için kartların bir uzman tarafından güncel mevzuata göre kontrol edildiğini onaylayın.")
    if payload.checked_at > date.today():
        raise HTTPException(status_code=422, detail="Kontrol tarihi ileri bir tarih olamaz.")
    p = await db.get(RegulationPack, pack_id)
    if not p:
        raise HTTPException(status_code=404, detail="Paket bulunamadı.")
    rsvc.publish(p, user.actor_id, payload.reviewer_name, payload.checked_at, payload.note)
    await db.commit()
    return _admin_out(p)


# ---------------------------------------------------------------- şirket
async def _enabled_ids(db: AsyncSession, tenant_id: uuid.UUID) -> set:
    return set((await db.execute(select(TenantRegulationPack.pack_id).where(TenantRegulationPack.tenant_id == tenant_id))).scalars())


@router.get("/company/{tenant_id}/regulation-packs")
async def company_list(tenant_id: uuid.UUID, user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    ensure_tenant_content(user, tenant_id)
    enabled = await _enabled_ids(db, tenant_id)
    rows = (await db.execute(select(RegulationPack).where(RegulationPack.published.isnot(None)).order_by(RegulationPack.title))).scalars().all()
    return [rsvc.public_out(p, p.id in enabled) for p in rows]


@router.get("/company/{tenant_id}/regulation-packs/{pack_id}")
async def company_pack(tenant_id: uuid.UUID, pack_id: uuid.UUID, user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    ensure_tenant_content(user, tenant_id)
    p = await db.get(RegulationPack, pack_id)
    if not p or not p.published:  # taslak müşteriye görünmez
        raise HTTPException(status_code=404, detail="Paket bulunamadı.")
    return rsvc.public_out(p, p.id in await _enabled_ids(db, tenant_id), cards=True)


class EnableIn(BaseModel):
    enabled: bool


@router.put("/company/{tenant_id}/regulation-packs/{pack_id}")
async def company_toggle(tenant_id: uuid.UUID, pack_id: uuid.UUID, payload: EnableIn, user: CurrentUser = Depends(get_current_user),
                         db: AsyncSession = Depends(get_db)):
    ensure_tenant_content(user, tenant_id, "tenant:manage")
    p = await db.get(RegulationPack, pack_id)
    if not p or not p.published:
        raise HTTPException(status_code=404, detail="Paket bulunamadı.")
    row = await db.get(TenantRegulationPack, (tenant_id, pack_id))
    if payload.enabled and not row:
        db.add(TenantRegulationPack(tenant_id=tenant_id, pack_id=pack_id, enabled_by_actor_id=user.actor_id))
    elif not payload.enabled and row:
        await db.delete(row)
    await db.commit()
    return rsvc.public_out(p, payload.enabled)
