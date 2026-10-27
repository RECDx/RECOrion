import logging
import uuid
from datetime import datetime
from typing import List, Optional

import redis.asyncio as aioredis
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.security import (
    CurrentUser, create_access_token, get_current_user, hash_password, load_current_user,
    password_needs_upgrade, verify_password,
)
from app.core import permission_catalog
from app.db.models import Actor, Tenant, TenantLead, TenantRole
from app.db.session import get_db

# Diğer modüller şifre fonksiyonlarını buradan içe aktarır
__all__ = ["router", "hash_password", "verify_password"]

router = APIRouter(prefix="/auth", tags=["Kimlik Doğrulama (Auth & RBAC)"])
logger = logging.getLogger("recorion.auth")

INVALID_CREDENTIALS = "Geçersiz kullanıcı adı veya şifre."


class LoginRequest(BaseModel):
    email: str
    password: str
    remember_me: bool = False


class UserProfileResponse(BaseModel):
    actor_id: uuid.UUID
    display_name: str
    email: str
    phone: Optional[str] = None
    address: Optional[str] = None
    role: str
    role_name: Optional[str] = None
    tenant_id: uuid.UUID
    tenant_name: str
    tenant_slug: str
    is_super_admin: bool = False
    permissions: List[str] = []


class LoginResponse(UserProfileResponse):
    access_token: str
    token_type: str = "bearer"
    expires_at: datetime


class ProfileUpdateRequest(BaseModel):
    display_name: str
    email: str
    phone: Optional[str] = None
    address: Optional[str] = None
    new_password: Optional[str] = None


# ---------------------------------------------------------------------------
# Hatalı giriş denemesi kilidi (Redis). Redis erişilemezse giriş engellenmez.
# ---------------------------------------------------------------------------
def _lock_key(email: str) -> str:
    return f"auth:failed:{email}"


async def _redis() -> aioredis.Redis:
    from app.core.tokens import redis_client
    return redis_client()


async def _is_locked(email: str) -> bool:
    try:
        client = await _redis()
        try:
            return int(await client.get(_lock_key(email)) or 0) >= settings.LOGIN_MAX_FAILED_ATTEMPTS
        finally:
            await client.aclose()
    except Exception as exc:
        logger.warning("Giriş kilidi kontrol edilemedi: %s", exc)
        return False


async def _register_failure(email: str) -> None:
    try:
        client = await _redis()
        try:
            key = _lock_key(email)
            await client.incr(key)
            await client.expire(key, settings.LOGIN_LOCK_MINUTES * 60)
        finally:
            await client.aclose()
    except Exception as exc:
        logger.warning("Hatalı giriş kaydedilemedi: %s", exc)


async def _clear_failures(email: str) -> None:
    try:
        client = await _redis()
        try:
            await client.delete(_lock_key(email))
        finally:
            await client.aclose()
    except Exception:
        pass


async def _profile(db: AsyncSession, actor: Actor, user: Optional[CurrentUser] = None) -> dict:
    user = user or await load_current_user(db, actor)
    tenant = await db.get(Tenant, actor.tenant_id)
    role = await db.get(TenantRole, actor.role_id) if actor.role_id else None
    return dict(
        actor_id=actor.id,
        display_name=actor.display_name,
        email=actor.email or "",
        phone=actor.phone,
        address=actor.address,
        role=actor.role,
        role_name=(role.name if role else None) or permission_catalog.role_label(actor.role),
        tenant_id=actor.tenant_id,
        tenant_name=tenant.name if tenant else "",
        tenant_slug=tenant.slug if tenant else "",
        is_super_admin=user.is_super_admin,
        permissions=sorted(user.permissions),
    )


async def _check_tenant_can_login(db: AsyncSession, actor: Actor, is_platform_staff: bool) -> None:
    """Müşteri kullanıcıları için şirket aktiflik ve onay kontrolleri."""
    if is_platform_staff:
        return
    tenant = await db.get(Tenant, actor.tenant_id)
    if not tenant:
        raise HTTPException(status_code=403, detail="Kullanıcıya atanmış geçerli bir şirket kaydı bulunamadı.")
    if not tenant.is_active:
        raise HTTPException(
            status_code=403,
            detail=f"'{tenant.name}' şirket hesabı pasife alınmıştır. Sisteme giriş yapamazsınız. Lütfen sistem yöneticiniz ile iletişime geçiniz.",
        )

    lead = (await db.execute(
        select(TenantLead)
        .where((TenantLead.contact_email == actor.email) | (TenantLead.company_name == tenant.name))
        .order_by(TenantLead.created_at.desc()).limit(1)
    )).scalar_one_or_none()
    if lead and lead.status == "PENDING":
        raise HTTPException(
            status_code=403,
            detail=f"'{tenant.name}' için satın alma başvurunuz henüz Süper Yönetici tarafından onaylanmamıştır. Başvurunuz onaylandığında e-posta ile bilgilendirileceksiniz.",
        )
    if lead and lead.status == "REJECTED":
        raise HTTPException(status_code=403, detail=f"'{tenant.name}' için yapılan satın alma başvurusu reddedilmiştir.")
    if not tenant.package_expiry_date:
        raise HTTPException(
            status_code=403,
            detail=f"'{tenant.name}' şirketinin abonelik paketi henüz Süper Yönetici tarafından onaylanıp aktif edilmemiştir.",
        )


@router.post("/login", response_model=LoginResponse)
async def login(payload: LoginRequest, request: Request, db: AsyncSession = Depends(get_db)):
    """
    RECOrion giriş uç noktası. Başarılı girişte JWT erişim token'ı döner;
    sonraki isteklerde `Authorization: Bearer <token>` başlığı ile gönderilmelidir.
    """
    email = payload.email.strip().lower()
    if await _is_locked(email):
        raise HTTPException(
            status_code=429,
            detail=f"Çok fazla hatalı giriş denemesi. Lütfen {settings.LOGIN_LOCK_MINUTES} dakika sonra tekrar deneyin.",
        )

    candidates = (await db.execute(
        select(Actor).where(func.lower(Actor.email) == email, Actor.actor_type == "HUMAN")
    )).scalars().all()
    valid = [a for a in candidates if verify_password(payload.password, a.password_hash)]
    if not valid:
        await _register_failure(email)
        raise HTTPException(status_code=401, detail=INVALID_CREDENTIALS)

    # Aynı e-posta birden fazla kayıtta varsa: süper admin > aktif hesap > en yeni hesap
    valid.sort(
        key=lambda a: (a.role == "SUPER_ADMIN", a.status != "DISABLED", a.created_at or datetime.min),
        reverse=True,
    )
    actor = valid[0]

    user = await load_current_user(db, actor)
    if actor.status == "DISABLED":
        raise HTTPException(status_code=403, detail="Kullanıcı hesabınız pasife alınmıştır. Sisteme giriş yapamazsınız.")
    await _check_tenant_can_login(db, actor, user.is_platform_staff)

    if password_needs_upgrade(actor.password_hash):
        actor.password_hash = hash_password(payload.password)
        await db.commit()
        await db.refresh(actor)

    await _clear_failures(email)
    request.state.audit_actor_id = actor.id

    token, expires_at = create_access_token(actor, remember_me=payload.remember_me)
    return LoginResponse(**await _profile(db, actor, user), access_token=token, expires_at=expires_at)


@router.get("/me", response_model=UserProfileResponse)
async def get_me(user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Token sahibi kullanıcının güncel profilini ve izinlerini döner."""
    return UserProfileResponse(**await _profile(db, user.actor, user))


@router.get("/profile/{actor_id}", response_model=UserProfileResponse)
async def get_profile(actor_id: uuid.UUID, user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Kullanıcının kendi profil detayları."""
    return UserProfileResponse(**await _profile(db, user.actor, user))


@router.put("/profile/{actor_id}", response_model=UserProfileResponse)
async def update_profile(
    actor_id: uuid.UUID,
    payload: ProfileUpdateRequest,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Kullanıcının kendi profil bilgilerini (Ad Soyad, Telefon, E-posta, Adres, Şifre) günceller."""
    actor = await db.get(Actor, user.actor_id)

    new_email = payload.email.strip().lower()
    if new_email != (actor.email or "").lower():
        taken = (await db.execute(
            select(Actor.id).where(func.lower(Actor.email) == new_email, Actor.id != actor.id)
        )).first()
        if taken:
            raise HTTPException(status_code=409, detail="Bu e-posta adresi başka bir kullanıcı tarafından kullanılıyor.")

    actor.display_name = payload.display_name.strip()
    actor.email = new_email
    actor.phone = payload.phone.strip() if payload.phone else None
    actor.address = payload.address.strip() if payload.address else None

    if payload.new_password:
        new_password = payload.new_password.strip()
        if len(new_password) < 8:
            raise HTTPException(status_code=400, detail="Yeni şifre en az 8 karakter olmalıdır.")
        actor.password_hash = hash_password(new_password)

    await db.commit()
    await db.refresh(actor)
    return UserProfileResponse(**await _profile(db, actor))


# ---------------------------------------------------------------------------
# Şifre belirleme / sıfırlama (tek kullanımlık e-posta bağlantısı)
# ---------------------------------------------------------------------------
class PasswordResetRequest(BaseModel):
    email: str


class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str


@router.post("/password-reset/request")
async def request_password_reset(payload: PasswordResetRequest, request: Request, db: AsyncSession = Depends(get_db)):
    """
    Şifre sıfırlama bağlantısı gönderir. Hesabın var olup olmadığı yanıttan anlaşılmaz.
    Sınır: aynı e-postaya saatte 3, aynı IP'den saatte 10 talep.
    """
    from app.core.tokens import hit_rate_limit
    from app.services.customer_lifecycle import RESET_LINK_HOURS, set_password_link
    from app.services.notification_service import NotificationService

    email = payload.email.strip().lower()
    generic = {"success": True, "message": "Bu e-posta adresiyle kayıtlı bir hesap varsa şifre belirleme bağlantısı gönderildi."}
    ip = request.client.host if request.client else "unknown"
    if await hit_rate_limit(f"pwreset:email:{email}", 3, 3600) or await hit_rate_limit(f"pwreset:ip:{ip}", 10, 3600):
        return generic

    actor = (await db.execute(
        select(Actor).where(func.lower(Actor.email) == email, Actor.actor_type == "HUMAN", Actor.status != "DISABLED")
        .order_by(Actor.created_at.desc())
    )).scalars().first()
    if actor:
        link = await set_password_link(actor, hours=RESET_LINK_HOURS)
        await NotificationService.send_by_code(db, "PASSWORD_RESET", actor.email, {
            "contact_name": actor.display_name, "reset_url": link, "valid_hours": RESET_LINK_HOURS,
        })
    return generic


@router.post("/password-reset/confirm")
async def confirm_password_reset(payload: PasswordResetConfirm, db: AsyncSession = Depends(get_db)):
    """Bağlantıdaki token ile yeni şifreyi belirler. Token tek kullanımlıktır."""
    from app.core.tokens import consume_link_token
    from app.services.customer_lifecycle import SET_PASSWORD_PURPOSE

    new_password = (payload.new_password or "").strip()
    if len(new_password) < 8:
        raise HTTPException(status_code=400, detail="Yeni şifre en az 8 karakter olmalıdır.")
    actor_id = await consume_link_token(SET_PASSWORD_PURPOSE, payload.token)
    actor = await db.get(Actor, uuid.UUID(actor_id)) if actor_id else None
    if not actor or actor.status == "DISABLED":
        raise HTTPException(status_code=400, detail="Bağlantı geçersiz veya süresi dolmuş. Lütfen yeni bağlantı isteyin.")
    actor.password_hash = hash_password(new_password)
    await db.commit()
    await _clear_failures((actor.email or "").lower())
    return {"success": True, "message": "Şifreniz belirlendi. Yeni şifrenizle giriş yapabilirsiniz.", "email": actor.email}


# ---------------------------------------------------------------- Telegram bağlantısı (ADIM 6.5)
@router.get("/telegram")
async def telegram_status(user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    from app.services import telegram_service

    actor = await db.get(Actor, user.actor_id)
    return {"enabled": telegram_service.enabled(), "linked": bool(actor.telegram_chat_id),
            "linked_at": actor.telegram_linked_at, "bot_username": settings.TELEGRAM_BOT_USERNAME or None}


@router.post("/telegram/link")
async def telegram_link(user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Tek kullanımlık bağlama kodu üretir; kullanıcı botta /start KOD yazınca hesap bağlanır."""
    from app.services import telegram_service

    if not telegram_service.enabled():
        raise HTTPException(status_code=503, detail="Telegram bildirimleri henüz yapılandırılmadı (TELEGRAM_BOT_TOKEN).")
    actor = await db.get(Actor, user.actor_id)
    actor.telegram_link_code = telegram_service.new_link_code()
    await db.commit()
    return {"code": actor.telegram_link_code, "deep_link": telegram_service.deep_link(actor.telegram_link_code),
            "bot_username": settings.TELEGRAM_BOT_USERNAME or None}


@router.delete("/telegram/link")
async def telegram_unlink(user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    actor = await db.get(Actor, user.actor_id)
    actor.telegram_chat_id, actor.telegram_link_code, actor.telegram_linked_at = None, None, None
    await db.commit()
    return {"success": True}
