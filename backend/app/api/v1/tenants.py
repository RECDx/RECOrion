from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, func, delete
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import uuid
import re
from app.db.session import get_db
from app.db.models import Tenant, Plan, Actor, TenantLead, EmailTemplate, Sector, Profession
from pydantic import BaseModel
from app.config import settings
from app.core.security import CurrentUser, get_current_user
from app.core.tokens import hit_rate_limit, issue_email_code, verify_email_code, EMAIL_CODE_TTL_MINUTES
from app.services import customer_lifecycle as lifecycle
from app.services.notification_service import NotificationService

router = APIRouter(prefix="/tenants", tags=["Tenants (Şirketler)"])


class PlanResponse(BaseModel):
    id: uuid.UUID
    code: str
    name: str
    description: Optional[str] = None
    monthly_price: float
    currency: str
    max_humans: int
    max_agents: int
    max_projects: int
    monthly_credits: int
    storage_gb: int
    allowed_models: List[str]
    features: Dict[str, Any]
    odoo_product_id: Optional[int] = None
    is_active: bool

    class Config:
        from_attributes = True


class PlanCreate(BaseModel):
    code: str
    name: str
    description: Optional[str] = None
    monthly_price: float = 0.0
    currency: str = "TRY"
    max_humans: int = 5
    max_agents: int = 5
    max_projects: int = 3
    monthly_credits: int = 1000
    storage_gb: int = 10
    allowed_models: List[str] = ["deepseek-v3"]
    features: Dict[str, Any] = {}
    can_create_custom_titles: bool = False
    odoo_product_id: Optional[int] = None
    is_active: bool = True

class PlanUpdate(BaseModel):
    name: str
    description: Optional[str] = None
    monthly_price: float = 0.0
    currency: str = "TRY"
    max_humans: int = 5
    max_agents: int = 5
    max_projects: int = 3
    monthly_credits: int = 1000
    storage_gb: int = 10
    allowed_models: List[str] = []
    features: Dict[str, Any] = {}
    can_create_custom_titles: bool = False
    odoo_product_id: Optional[int] = None
    is_active: bool = True


class TenantCreate(BaseModel):
    slug: str
    name: str
    tax_id: Optional[str] = None
    tax_office: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    website: Optional[str] = None
    contact_email: Optional[str] = None
    plan_id: Optional[uuid.UUID] = None
    sectors: List[str] = []
    professions: List[str] = []
    nace_codes: List[str] = []
    sector_manifesto: Optional[str] = None

class TenantUpdate(BaseModel):
    name: str
    tax_id: Optional[str] = None
    tax_office: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    website: Optional[str] = None
    contact_email: Optional[str] = None
    is_active: bool = True
    sector_manifesto: Optional[str] = None
    plan_id: Optional[uuid.UUID] = None
    sectors: List[str] = []
    professions: List[str] = []
    nace_codes: List[str] = []
    package_expiry_date: Optional[str] = None

class AdminTenantCreate(BaseModel):
    name: str
    tax_id: Optional[str] = None
    tax_office: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    website: Optional[str] = None
    contact_email: str
    plan_id: Optional[uuid.UUID] = None
    sectors: List[str] = []
    professions: List[str] = []
    nace_codes: List[str] = []
    admin_name: str = "Şirket Yöneticisi"
    admin_password: Optional[str] = None
    activate_package: bool = True
    send_welcome_email: bool = True

class ManifestoRequest(BaseModel):
    company_name: str
    sectors: List[str] = []
    professions: List[str] = []
    nace_codes: List[str] = []
    website: Optional[str] = None

class TenantAdminUpdate(BaseModel):
    actor_id: Optional[uuid.UUID] = None
    display_name: str
    email: str
    phone: Optional[str] = None
    address: Optional[str] = None
    new_password: Optional[str] = None

class TenantResponse(BaseModel):
    id: uuid.UUID
    slug: str
    name: str
    tax_id: Optional[str] = None
    tax_office: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    website: Optional[str] = None
    contact_email: Optional[str] = None
    plan_id: Optional[uuid.UUID] = None
    plan_name: Optional[str] = None
    sectors: list = []
    professions: list = []
    nace_codes: list = []
    sector_manifesto: Optional[str] = None
    package_start_date: Optional[Any] = None
    package_expiry_date: Optional[Any] = None
    last_reminder_sent_at: Optional[Any] = None
    days_remaining: Optional[int] = None
    is_warning_3_months: Optional[bool] = False
    admin_name: Optional[str] = None
    admin_email: Optional[str] = None
    is_active: bool

    class Config:
        from_attributes = True

@router.get("/plans", response_model=List[PlanResponse])
async def list_plans(active_only: bool = False, db: AsyncSession = Depends(get_db)):
    """
    Sistemdeki kiralama paketlerini listeler (Madde 7).
    """
    stmt = select(Plan)
    if active_only:
        stmt = stmt.where(Plan.is_active == True)
    stmt = stmt.order_by(Plan.monthly_price.asc())
    result = await db.execute(stmt)
    return result.scalars().all()

@router.post("/plans", response_model=PlanResponse)
async def create_plan(payload: PlanCreate, db: AsyncSession = Depends(get_db)):
    """
    Yeni bir kiralama paketi tanımlama (Madde 7).
    """
    code_safe = payload.code.upper().strip()
    existing = await db.execute(select(Plan).where(Plan.code == code_safe))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail=f"'{code_safe}' kodlu paket zaten mevcut.")

    plan = Plan(
        code=code_safe,
        name=payload.name.strip(),
        description=payload.description,
        monthly_price=payload.monthly_price,
        currency=payload.currency.upper(),
        max_humans=payload.max_humans,
        max_agents=payload.max_agents,
        max_projects=payload.max_projects,
        monthly_credits=payload.monthly_credits,
        storage_gb=payload.storage_gb,
        allowed_models=payload.allowed_models,
        features=payload.features,
        can_create_custom_titles=payload.can_create_custom_titles,
        odoo_product_id=payload.odoo_product_id,
        is_active=payload.is_active
    )
    db.add(plan)
    await db.commit()
    await db.refresh(plan)
    return plan

@router.get("/plans/{plan_id}", response_model=PlanResponse)
async def get_plan(plan_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    plan = await db.get(Plan, plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Paket bulunamadı.")
    return plan

@router.put("/plans/{plan_id}", response_model=PlanResponse)
async def update_plan(plan_id: uuid.UUID, payload: PlanUpdate, db: AsyncSession = Depends(get_db)):
    """
    Kiralama paketini güncelleme (Madde 7).
    """
    plan = await db.get(Plan, plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Paket bulunamadı.")

    plan.name = payload.name.strip()
    plan.description = payload.description
    plan.monthly_price = payload.monthly_price
    plan.currency = payload.currency.upper()
    plan.max_humans = payload.max_humans
    plan.max_agents = payload.max_agents
    plan.max_projects = payload.max_projects
    plan.monthly_credits = payload.monthly_credits
    plan.storage_gb = payload.storage_gb
    plan.allowed_models = payload.allowed_models
    # Formda gönderilmeyen paket izinleri silinmesin diye birleştir
    plan.features = {**(plan.features or {}), **(payload.features or {})}
    plan.can_create_custom_titles = payload.can_create_custom_titles
    plan.odoo_product_id = payload.odoo_product_id
    plan.is_active = payload.is_active

    await db.commit()
    await db.refresh(plan)
    return plan

@router.delete("/plans/{plan_id}")
async def delete_plan(plan_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """
    Kiralama paketini silme (Madde 3):
    Kiralama paketini hiçbir müşteri almadı ise silinebilir, aksi takdirde silinemez.
    """
    plan = await db.get(Plan, plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Paket bulunamadı.")
    
    # 1. Bu paketi kullanan aktif/kayıtlı şirketleri say
    t_res = await db.execute(select(func.count()).select_from(Tenant).where(Tenant.plan_id == plan_id))
    t_count = t_res.scalar() or 0

    # 2. Bu paketi talep eden müşteri başvurularını say
    lead_res = await db.execute(select(func.count()).select_from(TenantLead).where(TenantLead.plan_id == plan_id))
    lead_count = lead_res.scalar() or 0

    total_customers = t_count + lead_count
    if total_customers > 0:
        detail_msg = (
            f"'{plan.name}' ({plan.code}) kiralama paketini kullanan veya talep eden {total_customers} müşteri "
            f"({t_count} kayıtlı şirket, {lead_count} başvuru) bulunmaktadır! "
            f"Kiralama paketi yalnızca hiçbir müşteri almadığı takdirde silinebilir. Silme işlemi engellendi."
        )
        raise HTTPException(status_code=400, detail=detail_msg)

    await db.delete(plan)
    await db.commit()
    return {"success": True, "message": f"'{plan.name}' ({plan.code}) paketi başarıyla silindi."}

def _turkish_search_variants(text: str) -> List[str]:
    variants = set()
    cleaned = text.strip()
    if not cleaned:
        return []
    variants.add(cleaned)
    variants.add(cleaned.lower())
    variants.add(cleaned.upper())
    tr_upper = cleaned.replace("i", "İ").replace("ı", "I").replace("ş", "Ş").replace("ğ", "Ğ").replace("ü", "Ü").replace("ç", "Ç").replace("ö", "Ö").upper()
    variants.add(tr_upper)
    tr_lower = cleaned.replace("İ", "i").replace("I", "ı").replace("Ş", "ş").replace("Ğ", "ğ").replace("Ü", "ü").replace("Ç", "ç").replace("Ö", "ö").lower()
    variants.add(tr_lower)
    return [v for v in variants if v]

@router.get("", response_model=List[TenantResponse])
@router.get("/", response_model=List[TenantResponse])
async def list_tenants(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Tenant).order_by(Tenant.created_at.desc()))
    tenants = result.scalars().all()

    # Planları ve Admin Aktörleri getir
    plans_res = await db.execute(select(Plan))
    plans = {p.id: p for p in plans_res.scalars().all()}

    actors_res = await db.execute(select(Actor).where(Actor.role == "COMPANY_ADMIN"))
    admins_by_tenant = {}
    for a in actors_res.scalars().all():
        if a.tenant_id not in admins_by_tenant:
            admins_by_tenant[a.tenant_id] = a

    enriched = []
    now = datetime.utcnow()
    for t in tenants:
        plan_obj = plans.get(t.plan_id)
        admin_actor = admins_by_tenant.get(t.id)

        days_rem = None
        is_warn = False
        if t.package_expiry_date:
            exp_date = t.package_expiry_date.replace(tzinfo=None) if t.package_expiry_date.tzinfo else t.package_expiry_date
            days_rem = (exp_date - now).days
            if days_rem <= 90:
                is_warn = True

        enriched.append({
            "id": t.id,
            "slug": t.slug,
            "name": t.name,
            "tax_id": t.tax_id,
            "tax_office": t.tax_office,
            "phone": t.phone,
            "address": t.address,
            "website": t.website,
            "contact_email": t.contact_email,
            "plan_id": t.plan_id,
            "plan_name": plan_obj.name if plan_obj else "Belirtilmedi",
            "sectors": t.sectors or [],
            "professions": t.professions or [],
            "nace_codes": t.nace_codes or [],
            "sector_manifesto": t.sector_manifesto,
            "package_start_date": t.package_start_date,
            "package_expiry_date": t.package_expiry_date,
            "last_reminder_sent_at": t.last_reminder_sent_at,
            "days_remaining": days_rem,
            "is_warning_3_months": is_warn,
            "admin_name": admin_actor.display_name if admin_actor else None,
            "admin_email": admin_actor.email if admin_actor else t.contact_email,
            "is_active": t.is_active
        })
    return enriched

async def validate_unique_tax_info(
    db: AsyncSession,
    tax_id: Optional[str],
    tax_office: Optional[str] = None,
    exclude_tenant_id: Optional[uuid.UUID] = None
):
    """
    Bir Müşteri için mükerrer kayıt olmaması adına Vergi No ve Vergi Dairesi tekilliğini denetler.
    Aynı Vergi No ve Vergi Dairesinden başka bir şirket varsa HTTPException(400) fırlatır (Madde 2).
    """
    if not tax_id or not str(tax_id).strip():
        return

    clean_tax_id = str(tax_id).strip()
    clean_tax_office = str(tax_office).strip() if tax_office else ""

    stmt = select(Tenant).where(Tenant.tax_id == clean_tax_id)
    if exclude_tenant_id:
        stmt = stmt.where(Tenant.id != exclude_tenant_id)

    res = await db.execute(stmt)
    matching_tenants = res.scalars().all()

    for t in matching_tenants:
        t_office = (t.tax_office or "").strip()
        if clean_tax_office and t_office:
            if clean_tax_office.lower() == t_office.lower():
                raise HTTPException(
                    status_code=400,
                    detail=f"'{clean_tax_id}' Vergi Numarası ve '{clean_tax_office}' Vergi Dairesi ile kayıtlı bir şirket ('{t.name}') zaten mevcuttur. Mükerrer kayıt oluşturulamaz."
                )
        else:
            raise HTTPException(
                status_code=400,
                detail=f"'{clean_tax_id}' Vergi Numarası ile kayıtlı bir şirket ('{t.name}') zaten mevcuttur. Mükerrer kayıt oluşturulamaz."
            )


async def validate_unique_admin_email(
    db: AsyncSession,
    email: Optional[str],
    exclude_actor_id: Optional[uuid.UUID] = None,
    exclude_tenant_id: Optional[uuid.UUID] = None
):
    """
    Müşteri Tanımlaması yapılırken Yönetici Mail adresi girildiğinde tekilliği kontrol eder.
    Aynı mail adresi başka bir şirkette varsa HTTPException(400) fırlatır (Madde 3).
    """
    if not email or not str(email).strip():
        return
    clean_email = str(email).strip().lower()
    stmt = select(Actor).where(func.lower(Actor.email) == clean_email)
    if exclude_actor_id:
        stmt = stmt.where(Actor.id != exclude_actor_id)
    if exclude_tenant_id:
        stmt = stmt.where(Actor.tenant_id != exclude_tenant_id)
    res = await db.execute(stmt)
    existing_actor = res.scalar_one_or_none()
    if existing_actor:
        actor_tenant = await db.get(Tenant, existing_actor.tenant_id) if existing_actor.tenant_id else None
        company_info = f" ('{actor_tenant.name}')" if actor_tenant else ""
        raise HTTPException(
            status_code=400,
            detail=f"'{clean_email}' e-posta adresi ile kayıtlı bir kullanıcı{company_info} zaten mevcuttur. Lütfen farklı bir yönetici e-posta adresi giriniz."
        )


PUBLIC_EMAIL_DOMAINS = {
    "gmail.com", "googlemail.com",
    "hotmail.com", "hotmail.com.tr", "outlook.com", "outlook.com.tr", "live.com", "msn.com", "windowslive.com",
    "yahoo.com", "yahoo.com.tr", "ymail.com", "myyahoo.com",
    "yandex.com", "yandex.com.tr", "ya.ru", "narod.ru",
    "icloud.com", "me.com", "mac.com",
    "mail.ru", "bk.ru", "inbox.ru", "list.ru",
    "proton.me", "protonmail.com", "tutanota.com", "tutamail.com",
    "zoho.com",
    "gmx.com", "gmx.de", "gmx.net",
    "aol.com", "aim.com"
}

def validate_tax_id(tax_id: Optional[str]) -> Optional[str]:
    """
    Vergi kimlik numarası: şirketler için 10 haneli VKN, şahıs şirketleri için 11 haneli TCKN.
    Boş bırakılabilir; girilmişse biçimi doğrulanır (Odoo müşteri eşleştirmesi bu numarayla yapılır).
    """
    if not tax_id or not str(tax_id).strip():
        return None
    clean = re.sub(r"\s+", "", str(tax_id))
    if not clean.isdigit() or len(clean) not in (10, 11):
        raise HTTPException(status_code=400, detail="Vergi numarası 10 haneli VKN veya 11 haneli TCKN olmalıdır.")
    if len(set(clean)) == 1 or clean in "01234567890123" or clean in "98765432109876":
        raise HTTPException(status_code=400, detail="Lütfen gerçek vergi numaranızı girin (ardışık veya tekrar eden rakamlar kabul edilmez).")
    if not (_vkn_checksum_ok(clean) if len(clean) == 10 else _tckn_checksum_ok(clean)):
        raise HTTPException(status_code=400, detail="Vergi numarası geçersiz (kontrol hanesi tutmuyor). Lütfen numarayı kontrol edin.")
    return clean


def _vkn_checksum_ok(v: str) -> bool:
    """Gelir İdaresi 10 haneli VKN kontrol hanesi algoritması."""
    d = [int(c) for c in v]
    total = 0
    for i in range(9):
        t = (d[i] + (9 - i)) % 10
        if t:
            t = (t * 2 ** (9 - i)) % 9 or 9
        total += t
    return (10 - total % 10) % 10 == d[9]


def _tckn_checksum_ok(v: str) -> bool:
    """11 haneli T.C. kimlik numarası kontrol haneleri."""
    d = [int(c) for c in v]
    if d[0] == 0:
        return False
    if (sum(d[0:9:2]) * 7 - sum(d[1:8:2])) % 10 != d[9]:
        return False
    return sum(d[:10]) % 10 == d[10]


def validate_corporate_email(email: Optional[str], field_name: str = "E-posta") -> str:
    """
    Müşterinin official (kurumsal) mail adresi ile kayıt edilmesini zorunlu kılar.
    Genel/ücretsiz (gmail, hotmail vb.) adresleri engeller (Madde 2 & 3).
    """
    if not email or not str(email).strip():
        raise HTTPException(status_code=400, detail=f"{field_name} adresi zorunludur.")
    
    clean_email = str(email).strip().lower()
    if "@" not in clean_email:
        raise HTTPException(status_code=400, detail=f"Geçerli bir {field_name.lower()} adresi giriniz.")
    
    parts = clean_email.split("@")
    if len(parts) != 2 or not parts[0].strip() or not parts[1].strip():
        raise HTTPException(status_code=400, detail=f"Geçerli bir {field_name.lower()} adresi giriniz.")
    
    domain = parts[1].strip().lower()
    if domain in PUBLIC_EMAIL_DOMAINS or any(domain == d or domain.endswith("." + d) for d in PUBLIC_EMAIL_DOMAINS):
        raise HTTPException(
            status_code=400,
            detail=f"Müşteri kurumsal/official bir şirket e-posta adresi (şirket alan adı) ile kayıt edilmelidir. Genel/ücretsiz e-posta sağlayıcıları ('{domain}') kabul edilmemektedir."
        )
    return clean_email


@router.post("/", response_model=TenantResponse)
async def create_tenant(payload: TenantCreate, db: AsyncSession = Depends(get_db)):
    # Official / Kurumsal e-posta kontrolü (Madde 2)
    validate_corporate_email(payload.contact_email, "İletişim e-posta")

    # Vergi No ve Vergi Dairesi mükerrerlik kontrolü (Madde 2)
    await validate_unique_tax_info(db, payload.tax_id, payload.tax_office)

    # Slug benzersizlik kontrolü
    existing = await db.execute(select(Tenant).where(Tenant.slug == payload.slug))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Bu şirket kodu (slug) zaten kullanımda.")

    start_date = datetime.utcnow()
    expiry_date = start_date + timedelta(days=365)

    tenant = Tenant(
        slug=payload.slug,
        name=payload.name,
        tax_id=payload.tax_id,
        tax_office=payload.tax_office,
        phone=payload.phone,
        address=payload.address,
        website=payload.website,
        contact_email=payload.contact_email,
        plan_id=payload.plan_id,
        sectors=payload.sectors or [],
        professions=payload.professions or [],
        sector_manifesto=payload.sector_manifesto or f"{payload.name} kurumsal standartlar ve yapay zeka operasyon manifestosu.",
        package_start_date=start_date,
        package_expiry_date=expiry_date,
        is_active=True
    )
    db.add(tenant)
    await db.commit()
    await db.refresh(tenant)
    return tenant

@router.get("/{tenant_id}/details")
async def get_tenant_details(tenant_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """
    Kayıtlı şirketin detay bilgileri, planı ve şirket yöneticisi aktörleri (Madde 5).
    """
    tenant = await db.get(Tenant, tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Şirket bulunamadı.")

    plan_obj = None
    if tenant.plan_id:
        plan_obj = await db.get(Plan, tenant.plan_id)

    # Şirket yöneticilerini getir
    actors_stmt = select(Actor).where(Actor.tenant_id == tenant_id, Actor.role == "COMPANY_ADMIN")
    actors_res = await db.execute(actors_stmt)
    admins = actors_res.scalars().all()

    # İlgili lead kaydı var mı
    lead_stmt = select(TenantLead).where(TenantLead.company_name == tenant.name).order_by(TenantLead.created_at.desc()).limit(1)
    lead_res = await db.execute(lead_stmt)
    lead_obj = lead_res.scalar_one_or_none()

    admin_data = []
    for a in admins:
        admin_data.append({
            "id": str(a.id),
            "display_name": a.display_name,
            "email": a.email,
            "phone": a.phone,
            "address": a.address,
            "role": a.role,
            "status": a.status,
            "created_at": a.created_at.isoformat() if a.created_at else None
        })

    return {
        "tenant": {
            "id": str(tenant.id),
            "slug": tenant.slug,
            "name": tenant.name,
            "tax_id": tenant.tax_id,
            "tax_office": tenant.tax_office,
            "phone": tenant.phone,
            "address": tenant.address,
            "website": tenant.website,
            "contact_email": tenant.contact_email,
            "plan_id": str(tenant.plan_id) if tenant.plan_id else None,
            "sectors": tenant.sectors or [],
            "professions": tenant.professions or [],
            "sector_manifesto": tenant.sector_manifesto,
            "package_start_date": tenant.package_start_date.isoformat() if tenant.package_start_date else None,
            "package_expiry_date": tenant.package_expiry_date.isoformat() if tenant.package_expiry_date else None,
            "last_reminder_sent_at": tenant.last_reminder_sent_at.isoformat() if tenant.last_reminder_sent_at else None,
            "is_active": tenant.is_active,
            "created_at": tenant.created_at.isoformat() if tenant.created_at else None
        },
        "plan": {
            "id": str(plan_obj.id) if plan_obj else None,
            "name": plan_obj.name if plan_obj else "Belirtilmedi",
            "code": plan_obj.code if plan_obj else "NONE",
            "monthly_price": float(plan_obj.monthly_price) if plan_obj else 0.0,
            "currency": plan_obj.currency if plan_obj else "TRY"
        } if plan_obj else None,
        "admins": admin_data,
        "lead_status": lead_obj.status if lead_obj else ("APPROVED" if tenant.is_active else "PENDING"),
        "odoo_order_name": lead_obj.odoo_order_name if lead_obj else None
    }

@router.put("/{tenant_id}")
async def update_tenant(tenant_id: uuid.UUID, payload: TenantUpdate, db: AsyncSession = Depends(get_db)):
    """
    Şirket bilgilerini güncelleme (Madde 5).
    """
    tenant = await db.get(Tenant, tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Şirket bulunamadı.")

    # Vergi No ve Vergi Dairesi mükerrerlik kontrolü (Madde 2)
    payload.tax_id = validate_tax_id(payload.tax_id)
    await validate_unique_tax_info(db, payload.tax_id, payload.tax_office, exclude_tenant_id=tenant_id)

    prev_active = tenant.is_active
    tenant.name = payload.name.strip()
    tenant.tax_id = payload.tax_id
    tenant.tax_office = payload.tax_office
    tenant.phone = payload.phone
    tenant.address = payload.address
    tenant.website = payload.website
    tenant.contact_email = payload.contact_email
    tenant.is_active = payload.is_active
    tenant.sector_manifesto = payload.sector_manifesto
    tenant.plan_id = payload.plan_id
    tenant.sectors = payload.sectors or []
    tenant.professions = payload.professions or []
    if payload.package_expiry_date:
        try:
            tenant.package_expiry_date = datetime.fromisoformat(payload.package_expiry_date.replace("Z", ""))
        except Exception:
            pass

    # Aktiflik durumu değiştiyse bağlı aktörleri güncelle (Süper admin hariç)
    if prev_active != tenant.is_active:
        new_actor_status = "IDLE" if tenant.is_active else "DISABLED"
        act_res = await db.execute(select(Actor).where(Actor.tenant_id == tenant.id))
        for act in act_res.scalars().all():
            if act.role != "SUPER_ADMIN":
                act.status = new_actor_status

    await db.commit()
    await db.refresh(tenant)
    return tenant

@router.post("/{tenant_id}/toggle-status")
async def toggle_tenant_status(tenant_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """
    Müşteri kartını pasife alma veya tekrar aktif etme (Madde 4).
    """
    tenant = await db.get(Tenant, tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Şirket bulunamadı.")

    tenant.is_active = not tenant.is_active
    new_actor_status = "IDLE" if tenant.is_active else "DISABLED"

    # Bağlı insan/şirket aktörlerinin durumunu güncelle (Süper admin hariç)
    act_res = await db.execute(select(Actor).where(Actor.tenant_id == tenant.id))
    for act in act_res.scalars().all():
        if act.role != "SUPER_ADMIN":
            act.status = new_actor_status

    await db.commit()
    await db.refresh(tenant)

    status_text = "Aktif" if tenant.is_active else "Pasif"
    return {
        "success": True,
        "is_active": tenant.is_active,
        "message": f"'{tenant.name}' şirketinin kartı başarıyla '{status_text}' durumuna alındı.",
        "tenant_id": str(tenant.id)
    }


@router.delete("/{tenant_id}")
async def delete_tenant(tenant_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """
    Süper Admin Şirket Silme (Madde 1):
    Şirket içerisinde hiçbir departman, AI Ajanı, Proje eklenmemiş olması şartıyla şirketi ve ilişkili kayıtlarını siler.
    """
    from app.db.models import Department, Project, Actor, TenantLead, JobTitle, TenantRole
    tenant = await db.get(Tenant, tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Şirket bulunamadı.")

    # 0. Ana Şirket Koruma Kontrolü (RECDx Teknoloji & Dijital Dönüşüm Danışmanlığı LTD. Şirketi Silinemez)
    tenant_name_lower = (tenant.name or "").lower()
    tenant_slug_lower = (tenant.slug or "").lower()
    if tenant_slug_lower in ("recdx", "recdx_hq") or "recdx teknoloji" in tenant_name_lower or "dijital dönüşüm" in tenant_name_lower:
        raise HTTPException(
            status_code=400,
            detail="RECDx Teknoloji & Dijital Dönüşüm Danışmanlığı LTD. Şirketi sistemin ana şirketidir ve silinemez!"
        )

    # 1. Departman kontrolü
    dept_count = await db.scalar(
        select(func.count(Department.id)).where(Department.tenant_id == tenant_id)
    ) or 0
    if dept_count > 0:
        raise HTTPException(
            status_code=400,
            detail=f"'{tenant.name}' şirketine ait {dept_count} adet tanımlı departman bulunmaktadır. Şirket silinmeden önce tüm departmanlar silinmelidir."
        )

    # 2. AI Ajanı kontrolü
    agent_count = await db.scalar(
        select(func.count(Actor.id)).where(
            Actor.tenant_id == tenant_id,
            Actor.actor_type == "AI_AGENT"
        )
    ) or 0
    if agent_count > 0:
        raise HTTPException(
            status_code=400,
            detail=f"'{tenant.name}' şirketine ait {agent_count} adet tanımlı Yapay Zeka Ajanı bulunmaktadır. Şirket silinmeden önce tüm AI ajanları silinmelidir."
        )

    # 3. Proje kontrolü
    project_count = await db.scalar(
        select(func.count(Project.id)).where(Project.tenant_id == tenant_id)
    ) or 0
    if project_count > 0:
        raise HTTPException(
            status_code=400,
            detail=f"'{tenant.name}' şirketine ait {project_count} adet proje bulunmaktadır. Şirket silinmeden önce tüm projeler silinmelidir."
        )

    # 4. Şirkete ait lead/başvuru kayıtları varsa temizle
    lead_res = await db.execute(
        select(TenantLead).where(
            (TenantLead.company_name == tenant.name) | (TenantLead.contact_email == tenant.contact_email)
        )
    )
    for lead_item in lead_res.scalars().all():
        await db.delete(lead_item)

    # 5. Şirkete ait unvan ve roller varsa temizle
    await db.execute(delete(JobTitle).where(JobTitle.tenant_id == tenant_id))
    await db.execute(delete(TenantRole).where(TenantRole.tenant_id == tenant_id))

    # 6. Şirketi sil (Actor kayıtları CASCADE ile temizlenir)
    company_name = tenant.name
    await db.delete(tenant)
    await db.commit()

    return {
        "success": True,
        "message": f"'{company_name}' şirketi sistemden başarıyla silindi.",
        "tenant_id": str(tenant_id)
    }


@router.put("/{tenant_id}/admin-user")
async def update_tenant_admin_user(tenant_id: uuid.UUID, payload: TenantAdminUpdate, db: AsyncSession = Depends(get_db)):
    """
    Şirket Admin rolündeki kullanıcının bilgilerini ve şifresini güncelleme (Madde 5).
    Müşteri Admin ekranında girilen bilgiler hem Admin kullanıcısını hem de Müşteri kartını (Tenant) UPDATE eder (Madde 3).
    """
    from app.api.v1.auth import hash_password

    tenant = await db.get(Tenant, tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Şirket kaydı bulunamadı.")

    clean_email = payload.email.strip().lower()

    actor = None
    if payload.actor_id:
        actor = await db.get(Actor, payload.actor_id)
    
    if not actor:
        # Şirketin ilk COMPANY_ADMIN kullanıcısını bul
        stmt = select(Actor).where(Actor.tenant_id == tenant_id, Actor.role == "COMPANY_ADMIN").limit(1)
        res = await db.execute(stmt)
        actor = res.scalar_one_or_none()

    # Yönetici e-posta tekillik kontrolü (farklı bir şirkete ait olmamalı)
    await validate_unique_admin_email(
        db, 
        clean_email, 
        exclude_actor_id=actor.id if actor else None,
        exclude_tenant_id=tenant_id
    )

    if not actor:
        # Eğer hiç admin yoksa oluştur
        actor = Actor(
            tenant_id=tenant_id,
            actor_type="HUMAN",
            display_name=payload.display_name.strip(),
            email=clean_email,
            phone=payload.phone,
            address=payload.address,
            role="COMPANY_ADMIN",
            autonomy_level="L3",
            status="IDLE"
        )
        db.add(actor)
    else:
        actor.display_name = payload.display_name.strip()
        actor.email = clean_email
        actor.phone = payload.phone
        if payload.address:
            actor.address = payload.address

    if payload.new_password and len(payload.new_password.strip()) >= 6:
        actor.password_hash = hash_password(payload.new_password.strip())

    # ========================================================
    # MÜŞTERİ KARTINI (TENANT) DA UPDATE ET (Madde 3 Hatası Çözümü)
    # ========================================================
    tenant.contact_email = clean_email
    if payload.phone:
        tenant.phone = payload.phone
    if payload.address and not tenant.address:
        tenant.address = payload.address

    # Varsa ilgili başvuru (lead) kaydını da güncelle
    lead_stmt = select(TenantLead).where(
        (TenantLead.company_name == tenant.name) | (TenantLead.contact_email == clean_email)
    ).limit(1)
    lead_res = await db.execute(lead_stmt)
    lead = lead_res.scalar_one_or_none()
    if lead:
        lead.contact_email = clean_email
        if payload.phone:
            lead.phone = payload.phone

    await db.commit()
    await db.refresh(actor)
    await db.refresh(tenant)

    return {
        "success": True,
        "message": f"Şirket yöneticisi '{actor.display_name}' ({actor.email}) ve '{tenant.name}' müşteri kartı başarıyla güncellendi.",
        "actor_id": str(actor.id),
        "tenant_id": str(tenant.id),
        "display_name": actor.display_name,
        "email": actor.email,
        "phone": actor.phone
    }

@router.post("/{tenant_id}/generate-password")
async def generate_tenant_admin_password(tenant_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """
    Şirket Admin kullanıcısı için güçlü ve güvenli şifre oluşturur (Madde 5).
    """
    from app.api.v1.auth import hash_password
    import secrets
    import string

    stmt = select(Actor).where(Actor.tenant_id == tenant_id, Actor.role == "COMPANY_ADMIN").limit(1)
    res = await db.execute(stmt)
    actor = res.scalar_one_or_none()
    if not actor:
        raise HTTPException(status_code=404, detail="Şirkete ait 'COMPANY_ADMIN' rolünde kullanıcı bulunamadı.")

    # 14 Karakterlik Güçlü Şifre Üret
    symbols = "!@#$%&*+?"
    chars = string.ascii_letters + string.digits + symbols
    while True:
        password = ''.join(secrets.choice(chars) for _ in range(14))
        if (any(c.islower() for c in password)
            and any(c.isupper() for c in password)
            and any(c.isdigit() for c in password)
            and any(c in symbols for c in password)):
            break

    actor.password_hash = hash_password(password)
    await db.commit()

    return {
        "success": True,
        "message": f"'{actor.display_name}' için yeni güçlü şifre başarıyla oluşturuldu ve kaydedildi.",
        "actor_email": actor.email,
        "generated_password": password
    }

@router.post("/{tenant_id}/approve")
async def approve_registered_tenant(
    tenant_id: uuid.UUID,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Şirket detay ekranından şirketi onaylama ve aktifleştirme: 1 yıllık paket süresi,
    bağlı başvurunun onayı, Odoo siparişinin onayı ve aktivasyon e-postası.
    """
    tenant = await db.get(Tenant, tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Şirket bulunamadı.")
    result = await lifecycle.activate_tenant(db, tenant, user.actor_id)
    expiry = result["package_expiry_date"]
    return {
        "success": True,
        "message": f"'{tenant.name}' şirketi onaylandı ve paket süresi {expiry.strftime('%d.%m.%Y')} tarihine kadar tanımlandı.",
        "package_expiry_date": expiry.isoformat(),
        "activation_email_sent": result["email_sent"],
    }


class PurchaseRequest(BaseModel):
    plan_code: str  # STARTER, PRO, ENTERPRISE
    company_name: str
    tax_id: Optional[str] = None
    tax_office: Optional[str] = None
    address: Optional[str] = None
    phone: str
    website: Optional[str] = None
    contact_name: str
    contact_email: str
    password: str
    email_code: str  # e-posta doğrulama kodu (/purchase-request/send-code)
    company_fax: Optional[str] = None  # bot tuzağı: gerçek kullanıcılar bu alanı görmez, boş gönderir
    sectors: List[str] = []
    professions: List[str] = []
    nace_codes: List[str] = []


class SendCodeRequest(BaseModel):
    email: str


class LeadRejectRequest(BaseModel):
    reason: str


class LeadOut(BaseModel):
    id: uuid.UUID
    tenant_id: Optional[uuid.UUID] = None
    plan_id: Optional[uuid.UUID] = None
    plan_name: Optional[str] = None
    company_name: str
    contact_name: Optional[str] = None
    contact_email: str
    phone: Optional[str] = None
    tax_id: Optional[str] = None
    tax_office: Optional[str] = None
    website: Optional[str] = None
    address: Optional[str] = None
    sectors: list = []
    professions: list = []
    nace_codes: list = []
    generated_manifesto: Optional[str] = None
    status: str
    source: Optional[str] = None
    rejection_reason: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    email_verified_at: Optional[datetime] = None
    odoo_partner_id: Optional[int] = None
    odoo_order_id: Optional[int] = None
    odoo_order_name: Optional[str] = None
    odoo_partner_name: Optional[str] = None
    odoo_sync_status: Optional[str] = None
    odoo_sync_error: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


def _client_ip(request: Request) -> str:
    fwd = request.headers.get("x-forwarded-for")
    return fwd.split(",")[0].strip() if fwd else (request.client.host if request.client else "unknown")


MIN_PASSWORD_LENGTH = 8


class PurchaseResponse(BaseModel):
    lead_id: uuid.UUID
    company_name: str
    plan_code: str
    plan_name: str
    monthly_price: float
    currency: str
    contact_email: str
    generated_manifesto: str
    assigned_skills: List[str]
    odoo_order_name: Optional[str] = None
    status: str
    admin_notified: bool
    customer_notified: bool
    message: str


class RoleCreate(BaseModel):
    name: str
    description: Optional[str] = None
    permissions: List[str] = []


class RoleResponse(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    name: str
    description: Optional[str] = None
    permissions: list
    is_system: bool

    class Config:
        from_attributes = True


@router.post("/purchase-request/send-code")
async def send_purchase_email_code(payload: SendCodeRequest, request: Request, db: AsyncSession = Depends(get_db)):
    """
    Web sitesi başvurusu için kurumsal e-postaya 6 haneli doğrulama kodu gönderir.
    Sınırlar: aynı e-postaya dakikada 1 / saatte 5, aynı IP'den saatte 20 istek.
    """
    email = validate_corporate_email(payload.email, "İletişim e-posta")
    await validate_unique_admin_email(db, email)
    ip = _client_ip(request)
    if await hit_rate_limit(f"code:min:{email}", 1, 60):
        raise HTTPException(status_code=429, detail="Yeni kod istemeden önce lütfen 1 dakika bekleyin.")
    if await hit_rate_limit(f"code:hour:{email}", 5, 3600) or await hit_rate_limit(f"code:ip:{ip}", settings.EMAIL_CODE_IP_LIMIT_PER_HOUR, 3600):
        raise HTTPException(status_code=429, detail="Çok fazla doğrulama kodu istendi. Lütfen daha sonra tekrar deneyin.")

    code = await issue_email_code(email)
    sent = await NotificationService.send_by_code(db, "EMAIL_VERIFICATION_CODE", email,
                                                  {"code": code, "valid_minutes": EMAIL_CODE_TTL_MINUTES})
    if not sent:
        raise HTTPException(status_code=503, detail="Doğrulama kodu e-postası gönderilemedi. Lütfen daha sonra tekrar deneyin.")
    return {"success": True, "message": f"Doğrulama kodu {email} adresine gönderildi.", "valid_minutes": EMAIL_CODE_TTL_MINUTES}


@router.post("/purchase-request", response_model=PurchaseResponse)
async def submit_purchase_request(
    payload: PurchaseRequest, request: Request, background: BackgroundTasks, db: AsyncSession = Depends(get_db)
):
    """
    Resmi web sitesinden paket satın alma / kiralama başvurusu.
    1. E-posta doğrulama kodu, bot tuzağı ve IP sınırı kontrol edilir.
    2. Onay bekleyen şirket kartı, şirket yöneticisi ve başvuru kaydı oluşturulur (birbirine bağlı).
    3. Arka planda: Odoo müşteri + satış teklifi, ardından müşteriye ve RECDx'e bildirim.
    """
    from app.services.manifesto_service import ManifestoService
    from app.api.v1.auth import hash_password

    if payload.company_fax:
        raise HTTPException(status_code=400, detail="Başvuru alınamadı.")
    if await hit_rate_limit(f"purchase:ip:{_client_ip(request)}", settings.PURCHASE_IP_LIMIT_PER_HOUR, 3600):
        raise HTTPException(status_code=429, detail="Çok fazla başvuru denemesi. Lütfen daha sonra tekrar deneyin.")

    email = validate_corporate_email(payload.contact_email, "İletişim e-posta")
    payload.tax_id = validate_tax_id(payload.tax_id)
    if len((payload.password or "").strip()) < MIN_PASSWORD_LENGTH:
        raise HTTPException(status_code=400, detail=f"Şifre en az {MIN_PASSWORD_LENGTH} karakter olmalıdır.")
    if not await verify_email_code(email, payload.email_code):
        raise HTTPException(status_code=400, detail="E-posta doğrulama kodu hatalı veya süresi dolmuş. Lütfen yeni kod isteyin.")

    await validate_unique_tax_info(db, payload.tax_id, payload.tax_office)
    await validate_unique_admin_email(db, email)

    plan = (await db.execute(select(Plan).where(Plan.code == payload.plan_code.upper(), Plan.is_active == True))).scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail=f"'{payload.plan_code}' kodlu aktif kiralama paketi bulunamadı.")

    manifesto_data = ManifestoService.generate_manifesto(
        company_name=payload.company_name, sectors=payload.sectors,
        professions=payload.professions, website=payload.website,
    )
    pw_hash = hash_password(payload.password.strip())

    tenant = Tenant(
        slug=await lifecycle.unique_slug(db, payload.company_name),
        name=payload.company_name.strip(),
        tax_id=payload.tax_id, tax_office=payload.tax_office, phone=payload.phone,
        address=payload.address, website=payload.website, contact_email=email,
        plan_id=plan.id, sectors=payload.sectors or [], professions=payload.professions or [],
        sector_manifesto=manifesto_data["manifesto"],
        package_start_date=None, package_expiry_date=None, is_active=False,
    )
    db.add(tenant)
    await db.flush()
    db.add(Actor(
        tenant_id=tenant.id, actor_type="HUMAN", display_name=payload.contact_name.strip(),
        email=email, phone=payload.phone, address=payload.address, role="COMPANY_ADMIN",
        password_hash=pw_hash, autonomy_level="L3", status="IDLE",
    ))
    lead = TenantLead(
        tenant_id=tenant.id, plan_id=plan.id, company_name=tenant.name, contact_name=payload.contact_name.strip(),
        contact_email=email, password_hash=pw_hash, tax_id=payload.tax_id, tax_office=payload.tax_office,
        address=payload.address, phone=payload.phone, website=payload.website,
        sectors=payload.sectors or [], professions=payload.professions or [], nace_codes=[],
        generated_manifesto=manifesto_data["manifesto"], assigned_skills=manifesto_data["assigned_skills"],
        status="PENDING", source="WEB", email_verified_at=datetime.utcnow(), odoo_sync_status="PENDING",
    )
    db.add(lead)
    await db.commit()
    await db.refresh(lead)

    background.add_task(lifecycle.process_new_lead, lead.id)

    return PurchaseResponse(
        lead_id=lead.id, company_name=lead.company_name, plan_code=plan.code, plan_name=plan.name,
        monthly_price=float(plan.monthly_price), currency=plan.currency, contact_email=lead.contact_email,
        generated_manifesto=lead.generated_manifesto, assigned_skills=lead.assigned_skills or [],
        odoo_order_name=None, status=lead.status, admin_notified=True, customer_notified=True,
        message="Başvurunuz alındı. RECDx ekibi inceledikten sonra hesabınız aktifleştirilecek ve size e-posta ile bilgi verilecektir.",
    )


@router.get("/leads", response_model=List[LeadOut])
async def list_tenant_leads(db: AsyncSession = Depends(get_db)):
    """Süper Admin için satın alma ve kiralama başvuruları (şifre bilgisi dönmez)."""
    rows = (await db.execute(
        select(TenantLead, Plan.name).outerjoin(Plan, Plan.id == TenantLead.plan_id).order_by(TenantLead.created_at.desc())
    )).all()
    return [LeadOut.model_validate(lead).model_copy(update={"plan_name": plan_name}) for lead, plan_name in rows]


async def _get_lead(db: AsyncSession, lead_id: uuid.UUID) -> TenantLead:
    lead = await db.get(TenantLead, lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Başvuru bulunamadı.")
    return lead


@router.post("/leads/{lead_id}/approve")
async def approve_tenant_lead(lead_id: uuid.UUID, user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """
    RECDx yetkilisi ödemeyi/başvuruyu onaylar: şirket ve 1 yıllık paket aktifleşir,
    Odoo siparişi onaylanır, müşteriye aktivasyon e-postası (şifre içermez) gönderilir.
    """
    lead = await _get_lead(db, lead_id)
    if lead.status == "APPROVED":
        raise HTTPException(status_code=400, detail="Bu başvuru zaten onaylanmış.")
    if not lead.tenant_id:
        raise HTTPException(status_code=409, detail="Başvuruya bağlı şirket kaydı bulunamadı; şirketi 'Yeni Müşteri Ekle' ile oluşturun.")
    tenant = await db.get(Tenant, lead.tenant_id)
    if not tenant:
        raise HTTPException(status_code=409, detail="Başvuruya bağlı şirket kaydı silinmiş.")

    result = await lifecycle.activate_tenant(db, tenant, user.actor_id, lead)
    return {
        "success": True,
        "message": f"'{tenant.name}' şirketi aktifleştirildi." + (
            " Aktivasyon e-postası gönderildi." if result["email_sent"] else " Aktivasyon e-postası gönderilemedi; şirket kartından tekrar gönderebilirsiniz."),
        "tenant_id": tenant.id,
        "tenant_slug": tenant.slug,
        "admin_email": lead.contact_email,
        "odoo_order_name": lead.odoo_order_name,
        "activation_email_sent": result["email_sent"],
        "status": "APPROVED",
    }


@router.post("/leads/{lead_id}/reject")
async def reject_tenant_lead(
    lead_id: uuid.UUID, payload: LeadRejectRequest,
    user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db),
):
    """Başvuruyu reddeder: şirket pasif kalır, Odoo teklifi iptal edilir, müşteriye gerekçeli e-posta gider."""
    reason = (payload.reason or "").strip()
    if len(reason) < 5:
        raise HTTPException(status_code=400, detail="Lütfen müşteriye iletilecek bir ret gerekçesi yazın.")
    lead = await _get_lead(db, lead_id)
    if lead.status == "APPROVED":
        raise HTTPException(status_code=400, detail="Onaylanmış bir başvuru reddedilemez; şirketi pasife alabilirsiniz.")
    sent = await lifecycle.reject_lead(db, lead, user.actor_id, reason)
    return {"success": True, "message": f"'{lead.company_name}' başvurusu reddedildi.", "email_sent": sent, "status": "REJECTED"}


@router.post("/leads/{lead_id}/odoo-sync")
async def retry_lead_odoo_sync(lead_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Başarısız Odoo senkronizasyonunu yeniden dener."""
    await _get_lead(db, lead_id)
    await lifecycle.sync_lead_to_odoo(lead_id)
    lead = await _get_lead(db, lead_id)
    await db.refresh(lead)
    return {"success": lead.odoo_sync_status in ("SYNCED", "SKIPPED"), "odoo_sync_status": lead.odoo_sync_status,
            "odoo_order_name": lead.odoo_order_name, "odoo_sync_error": lead.odoo_sync_error}


@router.post("/{tenant_id}/roles", response_model=RoleResponse)
async def create_tenant_role(tenant_id: uuid.UUID, payload: RoleCreate, db: AsyncSession = Depends(get_db)):
    """
    Müşteri Şirket Yöneticisi (D Maddesi):
    Şirket içi özel rol oluşturur ve izin kataloğundaki yetkileri atar.
    """
    from app.db.models import TenantRole, SystemPermission
    tenant = await db.get(Tenant, tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Şirket bulunamadı.")

    # İzin kodlarını doğrula
    if payload.permissions:
        perms_res = await db.execute(select(SystemPermission.code))
        valid_codes = set(perms_res.scalars().all())
        invalid = [p for p in payload.permissions if p not in valid_codes and p != "*"]
        if invalid:
            raise HTTPException(status_code=400, detail=f"Geçersiz izin kodları: {invalid}")

    role = TenantRole(
        tenant_id=tenant.id,
        name=payload.name,
        description=payload.description,
        permissions=payload.permissions,
        is_system=False
    )
    db.add(role)
    await db.commit()
    await db.refresh(role)
    return role


@router.get("/{tenant_id}/roles", response_model=List[RoleResponse])
async def list_tenant_roles(tenant_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """
    Şirketin tanımlı rollerini ve yetkilerini listeler.
    """
    from app.db.models import TenantRole
    res = await db.execute(select(TenantRole).where(TenantRole.tenant_id == tenant_id).order_by(TenantRole.created_at))
    return res.scalars().all()


@router.post("/admin-create")
async def admin_create_tenant(
    payload: AdminTenantCreate, background: BackgroundTasks,
    user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db),
):
    """
    Süper Admin tarafından doğrudan müşteri kurumu ve yöneticisi ekleme.
    - Şirket, yönetici ve başvuru kaydı (kaynak: ADMIN) birbirine bağlı oluşturulur.
    - Yönetici şifresi verilmezse hesap şifresiz açılır; aktivasyon e-postasındaki
      bağlantıyla kullanıcı şifresini kendisi belirler (şifre e-postayla gönderilmez).
    - activate_package=True ise şirket hemen 1 yıllık paketle aktifleşir; değilse
      onay bekleyen olarak kalır ve şirket kartından/başvurulardan onaylanır.
    - Odoo müşteri ve satış teklifi arka planda açılır.
    """
    from app.api.v1.auth import hash_password
    from app.services.manifesto_service import ManifestoService

    email = validate_corporate_email(payload.contact_email, "İletişim e-posta")
    payload.tax_id = validate_tax_id(payload.tax_id)
    name = (payload.name or "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="Şirket ünvanı zorunludur.")
    password = (payload.admin_password or "").strip()
    if password and len(password) < MIN_PASSWORD_LENGTH:
        raise HTTPException(status_code=400, detail=f"Yönetici şifresi en az {MIN_PASSWORD_LENGTH} karakter olmalıdır.")

    await validate_unique_tax_info(db, payload.tax_id, payload.tax_office)
    await validate_unique_admin_email(db, email)

    plan = await db.get(Plan, payload.plan_id) if payload.plan_id else None
    manifesto_data = ManifestoService.generate_manifesto(
        company_name=name, sectors=payload.sectors, professions=payload.professions, website=payload.website,
    )
    tenant = Tenant(
        slug=await lifecycle.unique_slug(db, name), name=name, tax_id=payload.tax_id, tax_office=payload.tax_office,
        phone=payload.phone, address=payload.address, website=payload.website, contact_email=email,
        plan_id=plan.id if plan else None, sectors=payload.sectors or [], professions=payload.professions or [],
        sector_manifesto=manifesto_data["manifesto"], package_start_date=None, package_expiry_date=None, is_active=False,
    )
    db.add(tenant)
    await db.flush()
    admin_name = (payload.admin_name or "").strip() or f"{name} Yöneticisi"
    admin_actor = Actor(
        tenant_id=tenant.id, actor_type="HUMAN", display_name=admin_name, email=email, phone=payload.phone,
        role="COMPANY_ADMIN", password_hash=hash_password(password) if password else None,
        autonomy_level="L3", status="IDLE",
    )
    db.add(admin_actor)
    lead = TenantLead(
        tenant_id=tenant.id, plan_id=tenant.plan_id, company_name=name, contact_name=admin_name, contact_email=email,
        phone=payload.phone, tax_id=payload.tax_id, tax_office=payload.tax_office, website=payload.website,
        address=payload.address, sectors=payload.sectors or [], professions=payload.professions or [], nace_codes=[],
        generated_manifesto=tenant.sector_manifesto, status="PENDING", source="ADMIN",
        odoo_sync_status="PENDING" if plan else "SKIPPED",
    )
    db.add(lead)
    await db.commit()
    await db.refresh(tenant)

    if plan:
        background.add_task(lifecycle.sync_lead_to_odoo, lead.id)

    email_sent = False
    expiry = None
    if payload.activate_package:
        result = await lifecycle.activate_tenant(db, tenant, user.actor_id, lead)
        email_sent = result["email_sent"] and payload.send_welcome_email
        expiry = result["package_expiry_date"]

    msg = f"'{tenant.name}' kurumu ve yöneticisi ({admin_name}) kaydedildi."
    msg += " Paket aktifleştirildi." if payload.activate_package else " Şirket kartındaki 'Onayla' ile aktifleştirebilirsiniz."
    if not password:
        msg += " Yönetici şifresini aktivasyon e-postasındaki bağlantıdan kendisi belirleyecek."
    return {
        "success": True,
        "message": msg,
        "tenant_id": str(tenant.id),
        "slug": tenant.slug,
        "admin_name": admin_name,
        "admin_email": email,
        "is_active": tenant.is_active,
        "package_expiry_date": expiry.isoformat() if expiry else None,
        "welcome_email_sent": email_sent,
        "lead_id": str(lead.id),
    }


@router.post("/{tenant_id}/send-welcome")
async def send_manual_welcome_email(tenant_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """
    Müşteriye aktivasyon e-postasını yeniden gönderir. E-posta şifre içermez; yeni bir
    şifre belirleme bağlantısı (72 saat geçerli) içerir.
    """
    tenant = await db.get(Tenant, tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Şirket bulunamadı.")
    admin = await lifecycle.company_admin(db, tenant.id)
    if not admin or not (admin.email or tenant.contact_email):
        raise HTTPException(status_code=400, detail="Şirket yöneticisinin geçerli bir e-posta adresi bulunamadı.")
    sent = await lifecycle.send_activation_email(db, tenant, admin, has_known_password=bool(admin.password_hash))
    if not sent:
        raise HTTPException(status_code=502, detail="Aktivasyon e-postası gönderilemedi. E-posta ayarlarını ve ACCOUNT_ACTIVATED şablonunu kontrol ediniz.")
    return {"success": True, "message": f"'{tenant.name}' şirketine ({admin.email or tenant.contact_email}) aktivasyon e-postası gönderildi."}


@router.post("/{tenant_id}/send-reminder")
async def send_manual_expiration_reminder(tenant_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Müşteriye paket süre sonu hatırlatıcı e-postasını hemen gönderir."""
    from app.services.scheduler_service import send_expiration_reminder

    tenant = await db.get(Tenant, tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Şirket bulunamadı.")
    if not tenant.contact_email:
        raise HTTPException(status_code=400, detail="Şirketin geçerli bir e-posta adresi bulunamadı.")
    sent, days_rem = await send_expiration_reminder(db, tenant)
    if not sent:
        raise HTTPException(status_code=502, detail="Hatırlatıcı e-postası gönderilemedi. E-posta ayarlarını ve PACKAGE_EXPIRATION_REMINDER şablonunu kontrol ediniz.")
    await db.commit()
    return {"success": True, "message": f"'{tenant.name}' şirketine hatırlatıcı e-postası gönderildi.", "days_remaining": days_rem}


@router.post("/generate-manifesto")
async def generate_company_manifesto_endpoint(payload: ManifestoRequest, db: AsyncSession = Depends(get_db)):
    """
    Şirket adı ve seçilen Sektör / Meslek gruplarına göre Kurumsal AI Manifestosu üretir.
    """
    from app.services.manifesto_service import ManifestoService

    data = ManifestoService.generate_manifesto(
        company_name=payload.company_name,
        sectors=payload.sectors,
        professions=payload.professions,
        website=payload.website
    )
    return data



