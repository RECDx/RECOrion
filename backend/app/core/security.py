"""
Kimlik doğrulama ve yetki çekirdeği.

- Şifreler Argon2id ile saklanır. Eski SHA-256 hash'ler doğrulanabilir ve
  başarılı girişte otomatik olarak Argon2'ye yükseltilir.
- Oturum, SECRET_KEY ile imzalanan JWT erişim token'ıdır (Authorization: Bearer).
- Her istekte kullanıcı veritabanından yeniden okunur; pasife alınan kullanıcı
  veya şirket token süresi dolmadan da erişimi kaybeder.
- KVKK: Süper admin müşteri şirketlerinin yönetim verisine erişebilir,
  içeriklerine (proje, sohbet, hafıza, doküman) erişemez.
"""
import hashlib
import hmac
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Optional, Set

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError
from fastapi import Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.models import Actor, Tenant, TenantRole
from app.db.session import get_db

HQ_TENANT_SLUG = "recdx_hq"
JWT_ALGORITHM = "HS256"
WILDCARD = "*"

# Yalnızca RECDx ana şirketindeki kullanıcılara verilebilen izinler
PLATFORM_ONLY_PERMISSIONS = {WILDCARD, "system:admin"}

ROLE_BASE_PERMISSIONS = {
    "COMPANY_ADMIN": {
        "tenant:manage", "tenant:view", "role:create", "role:edit", "role:delete",
        "user:invite", "user:manage", "agent:hire", "agent:configure",
        "agent:custom_title", "agent:quarantine", "project:create", "project:manage",
        "task:create", "task:approve", "task:reject", "chat:participate",
        "chat:view_a2a", "chat:export", "memory:search", "memory:promote", "memory:revoke",
        "billing:view", "department:dashboard", "integration:manage",
    },
    "PROJECT_MANAGER": {
        "tenant:view", "agent:hire", "project:create", "project:manage", "task:create",
        "task:approve", "task:reject", "chat:participate", "chat:view_a2a",
        "memory:search", "memory:promote",
    },
}
DEFAULT_PERMISSIONS = {"tenant:view", "task:create", "chat:participate", "memory:search"}

# ---------------------------------------------------------------------------
# Şifreler
# ---------------------------------------------------------------------------
_hasher = PasswordHasher()
_LEGACY_SALT = "recorion_tenant_salt_2026"  # yalnızca eski hash'leri doğrulamak için


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password: str, stored_hash: Optional[str]) -> bool:
    if not stored_hash:
        return False
    if stored_hash.startswith("$argon2"):
        try:
            return _hasher.verify(stored_hash, password)
        except (VerificationError, InvalidHashError):
            return False
    legacy = (
        hashlib.sha256(f"{_LEGACY_SALT}_{password}".encode("utf-8")).hexdigest(),
        hashlib.sha256(password.encode("utf-8")).hexdigest(),
    )
    return any(hmac.compare_digest(stored_hash, h) for h in legacy)


def password_needs_upgrade(stored_hash: Optional[str]) -> bool:
    if not stored_hash or not stored_hash.startswith("$argon2"):
        return True
    return _hasher.check_needs_rehash(stored_hash)


# ---------------------------------------------------------------------------
# Token
# ---------------------------------------------------------------------------
def _secret() -> str:
    if len(settings.SECRET_KEY or "") < 32:
        raise RuntimeError("SECRET_KEY .env içinde en az 32 karakter olarak tanımlanmalıdır.")
    return settings.SECRET_KEY


def create_access_token(actor: Actor, remember_me: bool = False) -> tuple[str, datetime]:
    now = datetime.now(timezone.utc)
    lifetime = timedelta(days=settings.REMEMBER_ME_DAYS) if remember_me else timedelta(hours=settings.ACCESS_TOKEN_HOURS)
    expires_at = now + lifetime
    claims = {
        "sub": str(actor.id),
        "tid": str(actor.tenant_id),
        "role": actor.role,
        "iat": int(now.timestamp()),
        "exp": int(expires_at.timestamp()),
    }
    return jwt.encode(claims, _secret(), algorithm=JWT_ALGORITHM), expires_at


def _unauthorized(detail: str = "Oturum açmanız gerekiyor.") -> HTTPException:
    return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail, headers={"WWW-Authenticate": "Bearer"})


def forbidden(detail: str = "Bu işlem için yetkiniz yok.") -> HTTPException:
    return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


KVKK_CONTENT_DENIED = (
    "KVKK gereği RECDx yöneticileri müşteri şirketlerin proje, sohbet, hafıza ve doküman "
    "içeriklerine erişemez."
)

# ---------------------------------------------------------------------------
# Geçerli kullanıcı
# ---------------------------------------------------------------------------
_hq_tenant_id: Optional[uuid.UUID] = None


async def get_hq_tenant_id(db: AsyncSession) -> Optional[uuid.UUID]:
    global _hq_tenant_id
    if _hq_tenant_id is None:
        _hq_tenant_id = (await db.execute(select(Tenant.id).where(Tenant.slug == HQ_TENANT_SLUG))).scalar_one_or_none()
    return _hq_tenant_id


@dataclass
class CurrentUser:
    actor: Actor
    actor_id: uuid.UUID  # ORM nesnesinden bağımsız kopya (oturum kapandıktan sonra da okunabilir)
    tenant_id: uuid.UUID
    is_super_admin: bool
    is_platform_staff: bool  # RECDx ana şirketi çalışanı
    permissions: Set[str] = field(default_factory=set)

    def has(self, permission: str) -> bool:
        return self.is_super_admin or WILDCARD in self.permissions or permission in self.permissions


async def compute_permissions(db: AsyncSession, actor: Actor, is_platform_staff: bool) -> Set[str]:
    if actor.role == "SUPER_ADMIN" and is_platform_staff:
        return {WILDCARD}
    perms = set(ROLE_BASE_PERMISSIONS.get(actor.role, DEFAULT_PERMISSIONS))
    if actor.role_id:
        role = await db.get(TenantRole, actor.role_id)
        if role and (role.tenant_id is None or role.tenant_id == actor.tenant_id):
            perms.update(role.permissions or [])
    perms.update(actor.extra_permissions or [])
    if not is_platform_staff:
        perms -= PLATFORM_ONLY_PERMISSIONS
    return perms


async def load_current_user(db: AsyncSession, actor: Actor) -> CurrentUser:
    hq_id = await get_hq_tenant_id(db)
    is_staff = hq_id is not None and actor.tenant_id == hq_id
    perms = await compute_permissions(db, actor, is_staff)
    return CurrentUser(
        actor=actor,
        actor_id=actor.id,
        tenant_id=actor.tenant_id,
        is_super_admin=WILDCARD in perms and is_staff,
        is_platform_staff=is_staff,
        permissions=perms,
    )


async def get_optional_user(request: Request, db: AsyncSession = Depends(get_db)) -> Optional[CurrentUser]:
    cached = getattr(request.state, "user", None)
    if cached is not None:
        return cached

    header = request.headers.get("authorization", "")
    if not header.lower().startswith("bearer "):
        return None
    try:
        claims = jwt.decode(header[7:].strip(), _secret(), algorithms=[JWT_ALGORITHM])
        actor_id = uuid.UUID(claims["sub"])
    except (jwt.PyJWTError, KeyError, ValueError):
        raise _unauthorized("Oturumunuzun süresi dolmuş veya geçersiz. Lütfen tekrar giriş yapın.")

    actor = await db.get(Actor, actor_id)
    if not actor or actor.actor_type != "HUMAN" or actor.status == "DISABLED":
        raise _unauthorized("Kullanıcı hesabı bulunamadı veya pasife alınmış.")

    user = await load_current_user(db, actor)
    if not user.is_platform_staff:
        tenant = await db.get(Tenant, actor.tenant_id)
        if not tenant or not tenant.is_active:
            raise _unauthorized("Şirket hesabı pasife alınmış.")

    request.state.user = user
    return user


async def get_current_user(user: Optional[CurrentUser] = Depends(get_optional_user)) -> CurrentUser:
    if user is None:
        raise _unauthorized()
    return user


# ---------------------------------------------------------------------------
# Şirket erişim kontrolleri (handler içinden çağrılır)
# ---------------------------------------------------------------------------
def ensure_tenant_management(user: CurrentUser, tenant_id: uuid.UUID, permission: Optional[str] = None) -> None:
    """Şirket yönetim verisi: şirketin kendi kullanıcıları veya süper admin."""
    if user.is_super_admin:
        return
    if user.tenant_id != tenant_id:
        raise forbidden("Bu şirkete ait verilere erişim yetkiniz yok.")
    if permission and not user.has(permission):
        raise forbidden()


def ensure_tenant_content(user: CurrentUser, tenant_id: uuid.UUID, permission: Optional[str] = None) -> None:
    """Şirket içeriği (proje, sohbet, hafıza, doküman): yalnızca şirketin kendi kullanıcıları."""
    if user.tenant_id != tenant_id:
        raise forbidden(KVKK_CONTENT_DENIED if user.is_platform_staff else "Bu şirkete ait verilere erişim yetkiniz yok.")
    if permission and not user.has(permission):
        raise forbidden()
