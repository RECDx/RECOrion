from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel
from typing import Optional, List
import hashlib
import uuid
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
    actor = result.scalar_one_or_none()

    if not actor:
        raise HTTPException(status_code=401, detail="Geçersiz kullanıcı adı veya şifre.")

    if not actor.password_hash or not verify_password(payload.password, actor.password_hash):
        raise HTTPException(status_code=401, detail="Geçersiz kullanıcı adı veya şifre.")

    # Şirket bilgilerini çek
    tenant_res = await db.execute(select(Tenant).where(Tenant.id == actor.tenant_id))
    tenant = tenant_res.scalar_one_or_none()
    tenant_name = tenant.name if tenant else "Bilinmeyen Kurum"
    tenant_slug = tenant.slug if tenant else "unknown"

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

