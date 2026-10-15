from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from pydantic import BaseModel
from typing import Optional, List
import hashlib
import uuid
from datetime import datetime
from app.db.session import get_db
from app.db.models import Actor, Tenant

router = APIRouter(prefix="/auth", tags=["Kimlik Doğrulama (Auth & RBAC)"])

SALT = "recorion_tenant_salt_2026"

def hash_password(password: str) -> str:
    return hashlib.sha256(f"{SALT}_{password}".encode("utf-8")).hexdigest()

def verify_password(password: str, stored_hash: str) -> bool:
    salted = hashlib.sha256(f"{SALT}_{password}".encode("utf-8")).hexdigest()
    plain = hashlib.sha256(password.encode("utf-8")).hexdigest()
    return stored_hash in (salted, plain)

class LoginRequest(BaseModel):
    email: str
    password: str

class UserProfileResponse(BaseModel):
    actor_id: uuid.UUID
    display_name: str
    email: str
    phone: Optional[str] = None
    address: Optional[str] = None
    role: str
    tenant_id: uuid.UUID
    tenant_name: str
    tenant_slug: str
    permissions: List[str] = []

class ProfileUpdateRequest(BaseModel):
    display_name: str
    email: str
    phone: Optional[str] = None
    address: Optional[str] = None
    new_password: Optional[str] = None

@router.post("/login", response_model=UserProfileResponse)
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)):
    """
    RECOrion Giriş Uç Noktası.
    RECDx Süper Admin (cuneyterdil@recdx.com) veya Müşteri Şirket Yöneticisi girişi.
    """
    clean_email = payload.email.strip().lower()
    if clean_email in ("cuneyterdil@recdx.", "cuneyterdil@recdx"):
        clean_email = "cuneyterdil@recdx.com"

    stmt = select(Actor).where(func.lower(Actor.email) == clean_email)
    result = await db.execute(stmt)
    matching_actors = list(result.scalars().all())

    # 1. Şirketin contact_email'i üzerinden şirket yöneticisini bul
    if not matching_actors:
        t_stmt = select(Tenant).where(func.lower(Tenant.contact_email) == clean_email)
        t_res = await db.execute(t_stmt)
        matched_tenants = t_res.scalars().all()
        if matched_tenants:
            t_ids = [t.id for t in matched_tenants]
            act_stmt = select(Actor).where(Actor.tenant_id.in_(t_ids), Actor.role == "COMPANY_ADMIN")
            act_res = await db.execute(act_stmt)
            matching_actors.extend(act_res.scalars().all())

    # 2. Şirket adı veya slug üzerinden şirket yöneticisini bul (örn: siriusmes, sirius)
    if not matching_actors:
        t_search = select(Tenant).where(
            or_(
                func.lower(Tenant.slug).ilike(f"%{clean_email}%"),
                func.lower(Tenant.name).ilike(f"%{clean_email}%")
            )
        )
        t_search_res = await db.execute(t_search)
        matched_tenants = t_search_res.scalars().all()
        if matched_tenants:
            t_ids = [t.id for t in matched_tenants]
            act_stmt = select(Actor).where(Actor.tenant_id.in_(t_ids), Actor.role == "COMPANY_ADMIN")
            act_res = await db.execute(act_stmt)
            matching_actors.extend(act_res.scalars().all())

    # 3. Aktör ad/soyad (display_name) üzerinden bul
    if not matching_actors:
        act_name_stmt = select(Actor).where(func.lower(Actor.display_name).ilike(f"%{clean_email}%"))
        act_name_res = await db.execute(act_name_stmt)
        matching_actors.extend(act_name_res.scalars().all())

    if not matching_actors:
        raise HTTPException(status_code=401, detail="Geçersiz kullanıcı adı veya şifre.")

    # Şifresi doğrulanan aktörleri topla
    valid_actors = []
    for a in matching_actors:
        if a.password_hash and verify_password(payload.password, a.password_hash):
            valid_actors.append(a)

    if not valid_actors:
        raise HTTPException(status_code=401, detail="Geçersiz kullanıcı adı veya şifre.")

    # Öncelik sıralaması:
    # 1. SUPER_ADMIN hesabı en yüksek önceliğe sahiptir
    # 2. Aktif durumdaki hesaplar (status != 'DISABLED')
    # 3. En güncel oluşturulan hesap
    valid_actors.sort(
        key=lambda a: (
            1 if a.role == "SUPER_ADMIN" else 0,
            1 if getattr(a, "status", None) != "DISABLED" else 0,
            getattr(a, "created_at", None) or datetime.min
        ),
        reverse=True
    )
    actor = valid_actors[0]

    # Şirket bilgilerini çek
    tenant_res = await db.execute(select(Tenant).where(Tenant.id == actor.tenant_id))
    tenant = tenant_res.scalar_one_or_none()
    tenant_name = tenant.name if tenant else "Bilinmeyen Kurum"
    tenant_slug = tenant.slug if tenant else "unknown"

    # Süper Admin dışındaki kullanıcılar için onay ve aktiflik denetimleri (Madde 1 & 2)
    if actor.role != "SUPER_ADMIN":
        if not tenant:
            raise HTTPException(status_code=403, detail="Kullanıcıya atanmış geçerli bir şirket kaydı bulunamadı.")

        # Madde 2: Müşteri tanımı pasife alındıktan sonra sisteme giremez
        if not tenant.is_active:
            raise HTTPException(
                status_code=403,
                detail=f"'{tenant.name}' şirket hesabı pasife alınmıştır. Sisteme giriş yapamazsınız. Lütfen sistem yöneticiniz ile iletişime geçiniz."
            )

        if getattr(actor, "status", None) == "DISABLED":
            raise HTTPException(
                status_code=403,
                detail="Kullanıcı hesabınız pasife alınmıştır. Sisteme giriş yapamazsınız."
            )

        # Madde 1: Müşteri satın alması yapıldıktan sonra Süper Yönetici tarafından onaylanmamış ise sisteme login olamaz
        from app.db.models import TenantLead
        lead_stmt = select(TenantLead).where(
            (TenantLead.contact_email == actor.email) | (TenantLead.company_name == tenant.name)
        ).order_by(TenantLead.created_at.desc()).limit(1)
        lead_res = await db.execute(lead_stmt)
        lead_obj = lead_res.scalar_one_or_none()

        if lead_obj and lead_obj.status == "PENDING":
            raise HTTPException(
                status_code=403,
                detail=f"'{tenant.name}' için satın alma başvurunuz henüz Süper Yönetici tarafından onaylanmamıştır. Başvurunuz onaylandığında e-posta ile bilgilendirileceksiniz."
            )

        if lead_obj and lead_obj.status == "REJECTED":
            raise HTTPException(
                status_code=403,
                detail=f"'{tenant.name}' için yapılan satın alma başvurusu reddedilmiştir."
            )

        # Şirket paket bitiş tarihi yoksa da henüz onaylanmamış sayılır
        if not tenant.package_expiry_date:
            raise HTTPException(
                status_code=403,
                detail=f"'{tenant.name}' şirketinin abonelik paketi henüz Süper Yönetici tarafından onaylanıp aktif edilmemiştir."
            )

    # Rol bazlı izinleri belirle
    permissions = []
    if actor.role == "SUPER_ADMIN":
        permissions = ["*"]  # Tüm izinler
    elif actor.role == "COMPANY_ADMIN":
        permissions = [
            "tenant:manage", "tenant:view", "role:create", "role:edit", 
            "user:invite", "user:manage", "agent:hire", "agent:configure", 
            "agent:custom_title", "project:create", "project:manage", 
            "task:create", "task:approve", "task:reject", "chat:participate", 
            "chat:view_a2a", "memory:search", "memory:promote", "billing:view"
        ]
    elif actor.role == "PROJECT_MANAGER":
        permissions = [
            "tenant:view", "agent:hire", "project:manage", "task:create", 
            "task:approve", "task:reject", "chat:participate", "chat:view_a2a", 
            "memory:search", "memory:promote"
        ]
    else:
        permissions = ["tenant:view", "task:create", "chat:participate", "memory:search"]

    return UserProfileResponse(
        actor_id=actor.id,
        display_name=actor.display_name,
        email=actor.email or payload.email,
        phone=actor.phone,
        address=actor.address,
        role=actor.role,
        tenant_id=actor.tenant_id,
        tenant_name=tenant_name,
        tenant_slug=tenant_slug,
        permissions=permissions
    )

@router.get("/profile/{actor_id}", response_model=UserProfileResponse)
async def get_profile(actor_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """
    Kullanıcının profil detaylarını getirir.
    """
    actor = await db.get(Actor, actor_id)
    if not actor:
        raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı.")

    tenant_res = await db.execute(select(Tenant).where(Tenant.id == actor.tenant_id))
    tenant = tenant_res.scalar_one_or_none()

    permissions = ["*"] if actor.role == "SUPER_ADMIN" else ["tenant:view"]

    return UserProfileResponse(
        actor_id=actor.id,
        display_name=actor.display_name,
        email=actor.email or "",
        phone=actor.phone,
        address=actor.address,
        role=actor.role,
        tenant_id=actor.tenant_id,
        tenant_name=tenant.name if tenant else "",
        tenant_slug=tenant.slug if tenant else "",
        permissions=permissions
    )

@router.put("/profile/{actor_id}", response_model=UserProfileResponse)
async def update_profile(actor_id: uuid.UUID, payload: ProfileUpdateRequest, db: AsyncSession = Depends(get_db)):
    """
    Kullanıcının profil bilgilerini (Ad Soyad, Telefon, E-posta, Adres, Şifre) günceller.
    """
    actor = await db.get(Actor, actor_id)
    if not actor:
        raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı.")

    actor.display_name = payload.display_name.strip()
    actor.email = payload.email.strip().lower()
    actor.phone = payload.phone.strip() if payload.phone else None
    actor.address = payload.address.strip() if payload.address else None

    if payload.new_password and len(payload.new_password.strip()) >= 6:
        actor.password_hash = hash_password(payload.new_password.strip())

    await db.commit()
    await db.refresh(actor)

    tenant_res = await db.execute(select(Tenant).where(Tenant.id == actor.tenant_id))
    tenant = tenant_res.scalar_one_or_none()

    permissions = ["*"] if actor.role == "SUPER_ADMIN" else ["tenant:view"]

    return UserProfileResponse(
        actor_id=actor.id,
        display_name=actor.display_name,
        email=actor.email or "",
        phone=actor.phone,
        address=actor.address,
        role=actor.role,
        tenant_id=actor.tenant_id,
        tenant_name=tenant.name if tenant else "",
        tenant_slug=tenant.slug if tenant else "",
        permissions=permissions
    )

