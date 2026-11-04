"""Yardım (Bilgi Birikimi) ve RECAi Yardım Asistanı (ADIM 15). Giriş yapmış herkes; içerik kullanıcının yetkisine göre süzülür."""
import re
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import CurrentUser, forbidden, get_current_user
from app.db.models import HelpPage
from app.db.session import get_db
from app.services import help_assistant, help_center as hc

router = APIRouter(prefix="/help", tags=["Yardım"])


@router.get("/tree")
async def tree(user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """İçindekiler: kullanıcının görebildiği kılavuzlar ve sayfalar (sıralı)."""
    pages = await hc.visible(db, user)
    guides: List[Dict] = []
    for g, title, _aud in hc.GUIDES:
        items = [hc.page_out(p) for p in pages if p.guide == g]
        if items:
            guides.append({"guide": g, "title": title, "pages": items})
    return {"guides": guides}


@router.get("/page")
async def page(slug: str = Query(..., max_length=255), user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    p = (await db.execute(select(HelpPage).where(HelpPage.slug == slug))).scalar_one_or_none()
    if not p:
        raise HTTPException(status_code=404, detail="Yardım sayfası bulunamadı.")
    if not hc.can_see(user, p):
        raise forbidden("Bu yardım sayfası yetkiniz dahilindeki modüllerin dışında.")
    children = [hc.page_out(c) for c in await hc.visible(db, user) if c.parent_slug == p.slug]
    parent = None
    if p.parent_slug:
        pp = (await db.execute(select(HelpPage).where(HelpPage.slug == p.parent_slug))).scalar_one_or_none()
        parent = hc.page_out(pp) if pp and hc.can_see(user, pp) else None
    return {**hc.page_out(p, body=True), "children": children, "parent_page": parent}


@router.get("/context")
async def context(screen: str = Query(..., max_length=120), title: Optional[str] = Query(None, max_length=200),
                  user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """F1: bulunulan ekranın (ve açık pencerenin) yardım sayfası."""
    c = await hc.context(db, user, screen, title)
    if not c:
        raise HTTPException(status_code=404, detail="Bu ekran için yardım sayfası yok.")
    return c


@router.get("/search")
async def search(q: str = Query(..., min_length=2, max_length=300), user: CurrentUser = Depends(get_current_user),
                 db: AsyncSession = Depends(get_db)):
    return [{**hc.page_out(p), "snippet": snip} for p, _r, snip in await hc.search(db, user, q)]


class AskIn(BaseModel):
    question: str = Field(..., min_length=1, max_length=1000)
    history: List[Dict[str, str]] = Field(default_factory=list, max_length=20)
    screen: Optional[str] = Field(None, max_length=120)


@router.post("/ask")
async def ask(payload: AskIn, user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """RECAi Yardım Asistanı: yalnız yetkili kılavuz bölümlerinden yanıt; yetki dışı konuda yanıt vermez."""
    return await help_assistant.ask(db, user, payload.question, payload.history, payload.screen)


@router.get("/assets/{name}")
async def asset(name: str, user: CurrentUser = Depends(get_current_user)):
    """Kılavuz görselleri; Merkez Yönetim görselleri (sy-) yalnız RECDx'e."""
    if not re.fullmatch(r"[a-z0-9_-]+(__[23])?\.webp", name):
        raise HTTPException(status_code=404, detail="Görsel bulunamadı.")
    if name.startswith("sy-") and not user.is_super_admin:
        raise forbidden("Bu görsel yetkiniz dahilinde değil.")
    f = hc.IMG / name
    if not f.exists():
        raise HTTPException(status_code=404, detail="Görsel bulunamadı.")
    return FileResponse(f, media_type="image/webp", headers={"Cache-Control": "private, max-age=86400"})
