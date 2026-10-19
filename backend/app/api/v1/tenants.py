from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, func, delete
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import uuid
import re
from app.db.session import get_db
from app.db.models import Tenant, Plan, Actor, TenantLead, EmailTemplate, Sector, Profession
from pydantic import BaseModel

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
    plan.features = payload.features
    plan.can_create_custom_titles = payload.can_create_custom_titles
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
async def approve_registered_tenant(tenant_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """
    Şirket detay ekranı üzerinden şirketi onaylama ve aktifleştirme (Madde 5 & 7).
    Satın almayı onaylayıp 1 yıllık paket kullanım süresi atar.
    """
    tenant = await db.get(Tenant, tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Şirket bulunamadı.")

    now = datetime.utcnow()
    tenant.is_active = True
    if not tenant.package_start_date:
        tenant.package_start_date = now
    tenant.package_expiry_date = now + timedelta(days=365)

    # Varsa ilgili lead kaydını da APPROVED yap
    lead_stmt = select(TenantLead).where(TenantLead.company_name == tenant.name).order_by(TenantLead.created_at.desc()).limit(1)
    lead_res = await db.execute(lead_stmt)
    lead_obj = lead_res.scalar_one_or_none()
    if lead_obj:
        lead_obj.status = "APPROVED"

    await db.commit()
    await db.refresh(tenant)

    # Hoş geldiniz şablonu ile e-posta gönder
    from app.services.notification_service import NotificationService
    plan_obj = await db.get(Plan, tenant.plan_id) if tenant.plan_id else None
    plan_title = plan_obj.name if plan_obj else "Kurumsal Paket"

    welcome_ctx = {
        "company_name": tenant.name,
        "contact_name": tenant.name + " Yetkilisi",
        "email": tenant.contact_email,
        "login_email": tenant.contact_email,
        "password": "Mevcut şifreniz geçerlidir",
        "plan_name": plan_title,
        "package_expiry_date": tenant.package_expiry_date.strftime("%d.%m.%Y"),
        "odoo_order_name": "Süper Admin Onay",
        "login_url": "http://localhost:5173/"
    }

    tmpl_res = await db.execute(select(EmailTemplate).where(EmailTemplate.code == "WELCOME_CUSTOMER"))
    welcome_tmpl = tmpl_res.scalar_one_or_none()
    if welcome_tmpl and tenant.contact_email:
        NotificationService.render_and_send_template(tenant.contact_email, welcome_tmpl, welcome_ctx)

    return {
        "success": True,
        "message": f"'{tenant.name}' şirketi başarıyla onaylandı ve 1 yıllık paket süresi ({tenant.package_expiry_date.strftime('%d.%m.%Y')}) tanımlandı.",
        "package_expiry_date": tenant.package_expiry_date.isoformat()
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
    sectors: List[str] = []
    professions: List[str] = []
    nace_codes: List[str] = []


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


@router.post("/purchase-request", response_model=PurchaseResponse)
async def submit_purchase_request(payload: PurchaseRequest, db: AsyncSession = Depends(get_db)):
    """
    Resmi RECOrion Web Sitesinden Paket Satın Alma / Kiralama Başvurusu.
    - Plan kontrolü yapar
    - Sektör ve Meslek tanımları ile Kurumsal Manifesto üretir (Madde 1)
    - Odoo 19 üzerinde res.partner ve sale.order (teklif) oluşturur
    - info@recdx.com adresine bildirim gönderir
    - Müşteri e-postasına profesyonel onay e-postası gönderir
    """
    import hashlib
    from app.db.models import TenantLead
    from app.services.manifesto_service import ManifestoService
    from app.services.notification_service import NotificationService
    from app.services.odoo_service import OdooService

    # Official / Kurumsal e-posta zorunluluğu (Madde 3)
    validate_corporate_email(payload.contact_email, "İletişim e-posta")

    # Vergi No ve Vergi Dairesi mükerrerlik kontrolü (Madde 2)
    await validate_unique_tax_info(db, payload.tax_id, payload.tax_office)

    # Yönetici E-Posta tekillik kontrolü (Madde 3)
    await validate_unique_admin_email(db, payload.contact_email)

    # 1. Planı bul
    p_res = await db.execute(select(Plan).where(Plan.code == payload.plan_code.upper()))
    plan = p_res.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail=f"'{payload.plan_code}' kodlu kiralama paketi bulunamadı.")

    # 2. AI ile Kurumsal Manifesto Üret (Sektör ve Meslek Tanımları ile)
    manifesto_data = ManifestoService.generate_manifesto(
        company_name=payload.company_name,
        sectors=payload.sectors,
        professions=payload.professions,
        website=payload.website
    )

    # 3. Güvenli Şifre Hashleme (SHA-256 + Salt)
    salt = "recorion_tenant_salt_2026"
    pw_hash = hashlib.sha256(f"{salt}_{payload.password}".encode("utf-8")).hexdigest()

    # 4. Odoo 19 res.partner & sale.order Entegrasyonu (A maddesi)
    odoo_partner_id = None
    odoo_order_id = None
    odoo_order_name = None

    try:
        odoo_partner_id = OdooService.get_or_create_partner(
            company_name=payload.company_name,
            contact_email=payload.contact_email,
            phone=payload.phone,
            address=payload.address,
            website=payload.website,
            tax_id=payload.tax_id
        )

        if odoo_partner_id:
            so_res = OdooService.create_sale_order(
                partner_id=odoo_partner_id,
                plan_code=plan.code,
                address=payload.address
            )
            if so_res.get("success"):
                odoo_order_id = so_res.get("order_id")
                odoo_order_name = so_res.get("order_name")
    except Exception as e:
        # Odoo bağlantı hatası genel akışı durdurmasın ama loglansın
        import logging
        logging.getLogger("recorion_odoo").error(f"Odoo işlemi sırasında istisna: {e}")

    # 5. Lead Kaydını Oluştur
    lead = TenantLead(
        plan_id=plan.id,
        company_name=payload.company_name,
        tax_id=payload.tax_id,
        tax_office=payload.tax_office,
        address=payload.address,
        phone=payload.phone,
        website=payload.website,
        contact_email=payload.contact_email,
        sectors=payload.sectors or [],
        professions=payload.professions or [],
        nace_codes=[],
        generated_manifesto=manifesto_data["manifesto"],
        assigned_skills=manifesto_data["assigned_skills"],
        odoo_partner_id=odoo_partner_id,
        odoo_order_id=odoo_order_id,
        odoo_order_name=odoo_order_name,
        status="PENDING",
        notes=f"Yetkili: {payload.contact_name} | PasswordHash: {pw_hash} | Sektör: {manifesto_data['sector_focus']} | OdooRef: {odoo_order_name or 'N/A'}"
    )
    db.add(lead)
    await db.commit()
    await db.refresh(lead)

    # 6.1. Kayıtlı Şirketler (Tenants) Listesi için Onay Bekleyen Tenant Kaydı Oluştur
    import re
    clean_slug = re.sub(r'[^a-zA-Z0-9]', '', payload.company_name.lower())[:16] or "tenant"
    slug_cand = f"{clean_slug}_{str(lead.id)[:6]}"

    pending_tenant = Tenant(
        slug=slug_cand,
        name=payload.company_name,
        tax_id=payload.tax_id,
        tax_office=payload.tax_office,
        phone=payload.phone,
        address=payload.address,
        website=payload.website,
        contact_email=payload.contact_email,
        plan_id=plan.id,
        sectors=payload.sectors or [],
        professions=payload.professions or [],
        sector_manifesto=manifesto_data["manifesto"],
        package_start_date=None,
        package_expiry_date=None,
        is_active=False
    )
    db.add(pending_tenant)
    await db.flush()

    # 6.2. Şirket Yöneticisi Aktörü Oluştur (IDLE)
    pending_admin_actor = Actor(
        tenant_id=pending_tenant.id,
        actor_type="HUMAN",
        display_name=f"{payload.contact_name} (Yönetici)",
        email=payload.contact_email,
        phone=payload.phone,
        address=payload.address,
        role="COMPANY_ADMIN",
        password_hash=pw_hash,
        autonomy_level="L3",
        status="IDLE"
    )
    db.add(pending_admin_actor)
    await db.commit()

    # 7. E-posta Bildirimlerini Gönder
    email_payload = {
        "company_name": payload.company_name,
        "contact_name": payload.contact_name,
        "contact_email": payload.contact_email,
        "phone": payload.phone,
        "website": payload.website,
        "address": payload.address,
        "tax_id": payload.tax_id,
        "tax_office": payload.tax_office,
        "plan_code": plan.code,
        "plan_name": plan.name,
        "monthly_price": float(plan.monthly_price),
        "currency": plan.currency,
        "sectors": payload.sectors,
        "professions": payload.professions,
        "generated_manifesto": manifesto_data["manifesto"],
        "odoo_order_name": odoo_order_name
    }

    admin_ok = NotificationService.send_admin_new_customer_notification(email_payload)
    cust_ok = NotificationService.send_customer_welcome_notification(email_payload)

    return PurchaseResponse(
        lead_id=lead.id,
        company_name=lead.company_name,
        plan_code=plan.code,
        plan_name=plan.name,
        monthly_price=float(plan.monthly_price),
        currency=plan.currency,
        contact_email=lead.contact_email,
        generated_manifesto=lead.generated_manifesto,
        assigned_skills=lead.assigned_skills,
        odoo_order_name=odoo_order_name,
        status=lead.status,
        admin_notified=admin_ok,
        customer_notified=cust_ok,
        message=f"Kiralama talebiniz başarıyla alınmıştır. Odoo Sipariş Referansı: {odoo_order_name or 'İşleniyor'}. İlgili müşteri temsilcisi en kısa sürede sizinle iletişime geçecektir."
    )


@router.get("/leads")
async def list_tenant_leads(db: AsyncSession = Depends(get_db)):
    """
    Süper Admin için gelen satın alma ve kiralama taleplerini listeler.
    """
    from app.db.models import TenantLead
    res = await db.execute(select(TenantLead).order_by(TenantLead.created_at.desc()))
    return res.scalars().all()


@router.post("/leads/{lead_id}/approve")
async def approve_tenant_lead(lead_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """
    RECDx Yetkilisi (A.9 Maddesi & Madde 7):
    Müşterinin ödemesi geldikten sonra siparişi ve üyeliği onaylar.
    - Satın almayı onaylayıp 1 yıllık paket kullanım süresi hesaplar (Madde 7).
    - Tenant ortamı aktive edilir
    - Şirket Yöneticisi (COMPANY_ADMIN) oluşturulur
    - Odoo siparişi onaylanır (action_confirm)
    - Müşteriye Kurumsal Hoş Geldiniz e-postası (şifre, bitiş tarihi, paket) gönderilir (Madde 1).
    """
    from app.db.models import TenantLead, Actor
    from app.services.odoo_service import OdooService

    lead = await db.get(TenantLead, lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead başvurusu bulunamadı.")

    # 1. Şirket slug üret
    import re
    clean_slug = re.sub(r'[^a-zA-Z0-9]', '', lead.company_name.lower())[:16] or "tenant"
    slug_candidate = f"{clean_slug}_{str(lead.id)[:6]}"

    # 2. 1 yıllık paket kullanım süresi hesapla (Madde 7)
    start_date = datetime.utcnow()
    expiry_date = start_date + timedelta(days=365)

    # 3. Mevcut Tenant var mı kontrol et, varsa aktif et, yoksa oluştur
    lead_slug_part = str(lead.id)[:6]
    tenant = None

    # Öncelikle lead id ile üretilmiş slug eşleşmesine bak
    if lead_slug_part:
        existing_by_slug = await db.execute(
            select(Tenant).where(Tenant.slug.contains(lead_slug_part)).order_by(Tenant.created_at.desc())
        )
        tenant = existing_by_slug.scalars().first()

    # Bulunamazsa şirket adı ve e-posta eşleşmesine bak
    if not tenant:
        existing_by_info = await db.execute(
            select(Tenant).where(
                (Tenant.name == lead.company_name) & (Tenant.contact_email == lead.contact_email)
            ).order_by(Tenant.created_at.desc())
        )
        tenant = existing_by_info.scalars().first()

    # Hala bulunamazsa sadece ada göre en son oluşturulanı ara
    if not tenant:
        existing_by_name = await db.execute(
            select(Tenant).where(Tenant.name == lead.company_name).order_by(Tenant.created_at.desc())
        )
        tenant = existing_by_name.scalars().first()

    if tenant:
        tenant.is_active = True
        tenant.package_start_date = start_date
        tenant.package_expiry_date = expiry_date
        if not tenant.plan_id:
            tenant.plan_id = lead.plan_id
        if not tenant.sectors:
            tenant.sectors = lead.sectors
        if not tenant.professions:
            tenant.professions = lead.professions
        if not tenant.sector_manifesto:
            tenant.sector_manifesto = lead.generated_manifesto
    else:
        tenant = Tenant(
            slug=slug_candidate,
            name=lead.company_name,
            tax_id=lead.tax_id,
            tax_office=lead.tax_office,
            phone=lead.phone,
            address=lead.address,
            website=lead.website,
            contact_email=lead.contact_email,
            plan_id=lead.plan_id,
            sectors=lead.sectors or [],
            professions=lead.professions or [],
            sector_manifesto=lead.generated_manifesto,
            package_start_date=start_date,
            package_expiry_date=expiry_date,
            is_active=True
        )
        db.add(tenant)
        await db.flush()

    # 4. Şirket Yöneticisi Kullanıcısını Güncelle veya Oluştur
    contact_name = "Şirket Yöneticisi"
    pw_hash = None
    initial_pw = None
    if lead.notes:
        for part in lead.notes.split("|"):
            if "Yetkili:" in part:
                contact_name = part.replace("Yetkili:", "").strip()
            if "PasswordHash:" in part:
                pw_hash = part.replace("PasswordHash:", "").strip()

    admin_actor_res = await db.execute(
        select(Actor).where(Actor.tenant_id == tenant.id, Actor.role == "COMPANY_ADMIN").order_by(Actor.created_at.desc())
    )
    admin_actor = admin_actor_res.scalars().first()
    if admin_actor:
        admin_actor.status = "IDLE"
        if pw_hash and not admin_actor.password_hash:
            admin_actor.password_hash = pw_hash
    else:
        admin_actor = Actor(
            tenant_id=tenant.id,
            actor_type="HUMAN",
            display_name=f"{contact_name} (Yönetici)",
            email=lead.contact_email,
            role="COMPANY_ADMIN",
            password_hash=pw_hash,
            autonomy_level="L3",
            status="IDLE"
        )
        db.add(admin_actor)

    # 5. Odoo Siparişini Onayla (Varsa)
    if lead.odoo_order_id:
        try:
            OdooService.confirm_sale_order(lead.odoo_order_id)
        except Exception as odoo_err:
            import logging
            logging.getLogger(__name__).warning(f"Odoo sipariş onaylama atlandı / hata: {odoo_err}")

    # 6. Lead durumunu güncelle
    lead.status = "APPROVED"
    await db.commit()

    # 7. Müşteriye "Hoş Geldiniz - Hesap Bilgileri ve Paket Süresi" E-postası Gönder (Madde 1)
    from app.services.notification_service import NotificationService
    plan_obj = await db.get(Plan, lead.plan_id) if lead.plan_id else None
    plan_title = plan_obj.name if plan_obj else "RECOrion Paketi"

    welcome_ctx = {
        "company_name": lead.company_name,
        "contact_name": contact_name,
        "email": lead.contact_email,
        "login_email": lead.contact_email,
        "password": initial_pw or "Kayıt sırasında belirlediğiniz şifreniz",
        "plan_name": plan_title,
        "package_expiry_date": expiry_date.strftime("%d.%m.%Y"),
        "odoo_order_name": lead.odoo_order_name or "Belirtilmedi",
        "login_url": "http://localhost:5173/"
    }

    tmpl_res = await db.execute(select(EmailTemplate).where(EmailTemplate.code == "WELCOME_CUSTOMER").order_by(EmailTemplate.created_at.desc()))
    welcome_tmpl = tmpl_res.scalars().first()
    email_sent = False
    try:
        if welcome_tmpl:
            email_sent = NotificationService.render_and_send_template(lead.contact_email, welcome_tmpl, welcome_ctx)
        else:
            email_sent = NotificationService.send_customer_account_activated_notification(welcome_ctx)
    except Exception as email_err:
        import logging
        logging.getLogger(__name__).warning(f"Aktivasyon e-postası gönderilemedi: {email_err}")

    return {
        "success": True,
        "message": f"'{lead.company_name}' şirketi ve yöneticisi ({lead.contact_email}) başarıyla aktive edildi. Kullanıcı adı ve şifresini içeren aktivasyon e-postası müşteriye iletildi.",
        "tenant_id": tenant.id,
        "tenant_slug": tenant.slug,
        "admin_email": lead.contact_email,
        "odoo_order_name": lead.odoo_order_name,
        "activation_email_sent": email_sent,
        "status": "APPROVED"
    }


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
async def admin_create_tenant(payload: AdminTenantCreate, db: AsyncSession = Depends(get_db)):
    """
    Süper Admin tarafından doğrudan yeni müşteri kurumu ve yöneticisi ekleme (Madde 9 & 7).
    - 1 yıllık paket kullanım süresi hesaplar
    - Otomatik şirket slug'ı üretir
    - Kurumsal AI manifestosu hazırlar
    - Yönetici kullanıcısını oluşturur
    - Müşteriye Hoş Geldiniz şablonu ile e-posta gönderir
    """
    from app.api.v1.auth import hash_password
    from app.services.manifesto_service import ManifestoService
    from app.services.notification_service import NotificationService
    import secrets
    import string

    clean_tax_id = payload.tax_id.strip() if payload.tax_id else ""
    # Official / Kurumsal e-posta zorunluluğu (Madde 2)
    clean_email = validate_corporate_email(payload.contact_email, "İletişim e-posta")
    clean_name = payload.name.strip() if payload.name else ""

    # Mevcut bir şirket var mı kontrol et (aynı vergi no, aynı email veya aynı ünvan ile)
    existing_tenant = None
    if clean_tax_id:
        t_res = await db.execute(select(Tenant).where(Tenant.tax_id == clean_tax_id))
        existing_tenant = t_res.scalars().first()
    if not existing_tenant and clean_email:
        t_res = await db.execute(select(Tenant).where(func.lower(Tenant.contact_email) == clean_email))
        existing_tenant = t_res.scalars().first()
    if not existing_tenant and clean_name:
        t_res = await db.execute(select(Tenant).where(func.lower(Tenant.name) == clean_name.lower()))
        existing_tenant = t_res.scalars().first()

    # 1. Slug üret
    clean_slug = re.sub(r'[^a-zA-Z0-9]', '', payload.name.lower())[:16] or "tenant"
    rnd_suffix = str(uuid.uuid4())[:6]
    slug_candidate = f"{clean_slug}_{rnd_suffix}"

    # 2. Şifre belirle
    plain_password = payload.admin_password
    if not plain_password:
        symbols = "!@#$%&*+?"
        chars = string.ascii_letters + string.digits + symbols
        plain_password = ''.join(secrets.choice(chars) for _ in range(12))

    # 3. NACE kodlarını alıp Manifesto oluştur
    nace_items = []
    manifesto_data = ManifestoService.generate_manifesto(
        company_name=payload.name,
        sectors=payload.sectors,
        professions=payload.professions,
        website=payload.website
    )

    start_date = None
    expiry_date = None

    if existing_tenant:
        # Şirket zaten sistemde mevcut; mükerrer insert YAPMA, kartı UPDATE et! (Madde 3 Hatası Çözümü)
        await validate_unique_tax_info(db, payload.tax_id, payload.tax_office, exclude_tenant_id=existing_tenant.id)
        await validate_unique_admin_email(db, clean_email, exclude_tenant_id=existing_tenant.id)

        existing_tenant.name = payload.name.strip()
        existing_tenant.tax_id = payload.tax_id
        existing_tenant.tax_office = payload.tax_office
        existing_tenant.phone = payload.phone
        existing_tenant.address = payload.address
        existing_tenant.website = payload.website
        existing_tenant.contact_email = clean_email
        if payload.plan_id:
            existing_tenant.plan_id = payload.plan_id
        if payload.sectors:
            existing_tenant.sectors = payload.sectors
        if payload.professions:
            existing_tenant.professions = payload.professions
        existing_tenant.sector_manifesto = manifesto_data["manifesto"]

        tenant = existing_tenant

        # Admin Actor'ü bul veya oluştur (Yetkili kullanıcı)
        act_res = await db.execute(select(Actor).where(Actor.tenant_id == tenant.id, Actor.role == "COMPANY_ADMIN").limit(1))
        admin_actor = act_res.scalar_one_or_none()
        if not admin_actor:
            admin_actor = Actor(
                tenant_id=tenant.id,
                actor_type="HUMAN",
                display_name=payload.admin_name.strip() if payload.admin_name and payload.admin_name.strip() else f"{payload.name} Yöneticisi",
                email=clean_email,
                phone=payload.phone,
                role="COMPANY_ADMIN",
                password_hash=hash_password(plain_password),
                autonomy_level="L3",
                status="IDLE"
            )
            db.add(admin_actor)
        else:
            if payload.admin_name and payload.admin_name.strip():
                admin_actor.display_name = payload.admin_name.strip()
            admin_actor.email = clean_email
            admin_actor.phone = payload.phone
            admin_actor.status = "IDLE"
            if payload.admin_password and payload.admin_password.strip():
                admin_actor.password_hash = hash_password(payload.admin_password.strip())
            elif plain_password:
                admin_actor.password_hash = hash_password(plain_password)
    else:
        # Yeni Şirket Ekle
        await validate_unique_tax_info(db, payload.tax_id, payload.tax_office)
        await validate_unique_admin_email(db, clean_email)

        tenant = Tenant(
            slug=slug_candidate,
            name=payload.name.strip(),
            tax_id=payload.tax_id,
            tax_office=payload.tax_office,
            phone=payload.phone,
            address=payload.address,
            website=payload.website,
            contact_email=clean_email,
            plan_id=payload.plan_id,
            sectors=payload.sectors or [],
            professions=payload.professions or [],
            sector_manifesto=manifesto_data["manifesto"],
            package_start_date=start_date,
            package_expiry_date=expiry_date,
            is_active=True
        )
        db.add(tenant)
        await db.flush()

        admin_actor = Actor(
            tenant_id=tenant.id,
            actor_type="HUMAN",
            display_name=payload.admin_name.strip() if payload.admin_name and payload.admin_name.strip() else f"{payload.name} Yöneticisi",
            email=clean_email,
            phone=payload.phone,
            role="COMPANY_ADMIN",
            password_hash=hash_password(plain_password),
            autonomy_level="L3",
            status="IDLE"
        )
        db.add(admin_actor)

    # 5.1 Odoo 19 Entegrasyonu: Müşteri Partneri ve Satış Siparişi Aç (Madde 2)
    from app.services.odoo_service import OdooService
    odoo_partner_id = None
    odoo_order_id = None
    odoo_order_name = None

    try:
        plan_obj = await db.get(Plan, payload.plan_id) if payload.plan_id else None
        plan_code = plan_obj.code if plan_obj else "STARTER"

        odoo_partner_id = OdooService.get_or_create_partner(
            company_name=payload.name.strip(),
            contact_email=payload.contact_email.strip().lower(),
            phone=payload.phone or "",
            address=payload.address or "",
            website=payload.website or "",
            tax_id=payload.tax_id or ""
        )

        if odoo_partner_id:
            so_res = OdooService.create_sale_order(
                partner_id=odoo_partner_id,
                plan_code=plan_code,
                address=payload.address
            )
            if so_res.get("success"):
                odoo_order_id = so_res.get("order_id")
                odoo_order_name = so_res.get("order_name")
                import logging
                logging.getLogger("recorion_odoo").info(
                    f"✓ Süper Admin müşteri kaydı: Odoo Siparişi başarıyla oluşturuldu -> Ref: {odoo_order_name} (ID: {odoo_order_id})"
                )
    except Exception as odoo_err:
        import logging
        logging.getLogger("recorion_odoo").error(f"Süper Admin müşteri eklerken Odoo entegrasyon hatası: {odoo_err}")

    # 6. TenantLead ile senkronize et
    lead = None
    l_res = await db.execute(
        select(TenantLead).where(
            or_(
                TenantLead.tax_id == tenant.tax_id,
                func.lower(TenantLead.contact_email) == clean_email,
                func.lower(TenantLead.company_name) == tenant.name.lower()
            )
        ).order_by(TenantLead.created_at.desc()).limit(1)
    )
    lead = l_res.scalars().first()

    if lead:
        lead.company_name = tenant.name
        lead.contact_email = tenant.contact_email
        lead.phone = tenant.phone
        lead.tax_id = tenant.tax_id
        lead.tax_office = tenant.tax_office
        lead.website = tenant.website
        lead.address = tenant.address
        lead.plan_id = tenant.plan_id
        lead.sectors = payload.sectors or []
        lead.professions = tenant.professions or []
        lead.generated_manifesto = tenant.sector_manifesto
        lead.status = "APPROVED"
        if odoo_partner_id:
            lead.odoo_partner_id = odoo_partner_id
        if odoo_order_id:
            lead.odoo_order_id = odoo_order_id
        if odoo_order_name:
            lead.odoo_order_name = odoo_order_name
        lead.notes = f"Yetkili: {admin_actor.display_name} | PasswordHash: {hash_password(plain_password)} | Sektör: {manifesto_data.get('sector_focus', 'Genel')} | OdooRef: {odoo_order_name or 'N/A'}"
    else:
        lead = TenantLead(
            company_name=tenant.name,
            contact_email=tenant.contact_email,
            phone=tenant.phone,
            tax_id=tenant.tax_id,
            tax_office=tenant.tax_office,
            website=tenant.website,
            address=tenant.address,
            plan_id=tenant.plan_id,
            sectors=payload.sectors or [],
            professions=payload.professions or [],
            generated_manifesto=tenant.sector_manifesto,
            odoo_partner_id=odoo_partner_id,
            odoo_order_id=odoo_order_id,
            odoo_order_name=odoo_order_name,
            status="APPROVED",
            notes=f"Yetkili: {admin_actor.display_name} | PasswordHash: {hash_password(plain_password)} | Sektör: {manifesto_data.get('sector_focus', 'Genel')} | OdooRef: {odoo_order_name or 'N/A'}"
        )
        db.add(lead)

    await db.commit()
    await db.refresh(tenant)

    # 7. E-posta Gönder (İstenmişse)
    email_sent = False
    if payload.send_welcome_email and tenant.contact_email:
        plan_obj = await db.get(Plan, payload.plan_id) if payload.plan_id else None
        plan_title = plan_obj.name if plan_obj else "Kurumsal Paket"

        welcome_ctx = {
            "company_name": tenant.name,
            "contact_name": admin_actor.display_name,
            "email": tenant.contact_email,
            "login_email": admin_actor.email,
            "password": plain_password,
            "plan_name": plan_title,
            "package_expiry_date": expiry_date.strftime("%d.%m.%Y") if expiry_date else "Onay Bekliyor",
            "odoo_order_name": odoo_order_name or "Süper Admin Doğrudan Kayıt",
            "login_url": "http://localhost:5173/"
        }

        tmpl_res = await db.execute(select(EmailTemplate).where(EmailTemplate.code == "WELCOME_CUSTOMER").order_by(EmailTemplate.created_at.desc()))
        welcome_tmpl = tmpl_res.scalars().first()
        if welcome_tmpl:
            email_sent = NotificationService.render_and_send_template(tenant.contact_email, welcome_tmpl, welcome_ctx)
        else:
            email_sent = NotificationService.send_customer_account_activated_notification(welcome_ctx)

    msg = f"'{tenant.name}' kurumu ve yetkili kullanıcısı ({admin_actor.display_name}) başarıyla kaydedildi."
    if odoo_order_name:
        msg += f" Odoo 19 Satış Siparişi oluşturuldu: {odoo_order_name}."

    return {
        "success": True,
        "message": msg,
        "tenant_id": str(tenant.id),
        "slug": tenant.slug,
        "admin_name": admin_actor.display_name,
        "admin_email": admin_actor.email,
        "admin_password": plain_password,
        "is_active": tenant.is_active,
        "package_expiry_date": expiry_date.isoformat() if expiry_date else None,
        "welcome_email_sent": email_sent,
        "odoo_order_id": odoo_order_id,
        "odoo_order_name": odoo_order_name
    }


@router.post("/{tenant_id}/send-welcome")
async def send_manual_welcome_email(tenant_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """
    Müşteriye manuel olarak Hoş Geldiniz E-Postası Gönderir.
    """
    from app.services.notification_service import NotificationService
    tenant = await db.get(Tenant, tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Şirket bulunamadı.")

    act_res = await db.execute(select(Actor).where(Actor.tenant_id == tenant.id, Actor.role.in_(["COMPANY_ADMIN", "SUPER_ADMIN"])).limit(1))
    admin_actor = act_res.scalar_one_or_none()

    target_email = tenant.contact_email or (admin_actor.email if admin_actor and admin_actor.email else None)
    if not target_email:
        raise HTTPException(status_code=400, detail="Şirketin veya yönetici kullanıcısının geçerli bir e-posta adresi bulunamadı.")

    if not tenant.contact_email and target_email:
        tenant.contact_email = target_email
        await db.commit()

    plan_obj = await db.get(Plan, tenant.plan_id) if tenant.plan_id else None
    plan_title = plan_obj.name if plan_obj else "Kurumsal Paket"

    welcome_ctx = {
        "company_name": tenant.name,
        "contact_name": admin_actor.display_name if admin_actor else f"{tenant.name} Yetkilisi",
        "email": target_email,
        "login_email": admin_actor.email if admin_actor and admin_actor.email else target_email,
        "password": "Mevcut şifreniz geçerlidir",
        "plan_name": plan_title,
        "package_expiry_date": tenant.package_expiry_date.strftime("%d.%m.%Y") if tenant.package_expiry_date else "Onay Bekliyor",
        "odoo_order_name": "Süper Admin İletimi",
        "login_url": "http://localhost:5173/"
    }

    tmpl_res = await db.execute(select(EmailTemplate).where(EmailTemplate.code == "WELCOME_CUSTOMER"))
    welcome_tmpl = tmpl_res.scalar_one_or_none()
    sent = False
    if welcome_tmpl:
        sent = NotificationService.render_and_send_template(target_email, welcome_tmpl, welcome_ctx)
    else:
        sent = NotificationService.send_customer_account_activated_notification(welcome_ctx)

    if not sent:
        raise HTTPException(
            status_code=500,
            detail=f"'{tenant.name}' şirketine ({target_email}) Hoş Geldiniz e-postası iletilemedi. Lütfen sunucu e-posta ayarlarını kontrol ediniz."
        )

    return {
        "success": True,
        "message": f"'{tenant.name}' şirketine ({target_email}) Hoş Geldiniz e-postası başarıyla iletildi."
    }


@router.post("/{tenant_id}/send-reminder")
async def send_manual_expiration_reminder(tenant_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """
    Müşteriye manuel olarak Paket Süre Sonu Hatırlatıcı E-Postası Gönderir (Madde 14).
    """
    from app.services.notification_service import NotificationService
    tenant = await db.get(Tenant, tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Şirket bulunamadı.")

    act_res = await db.execute(select(Actor).where(Actor.tenant_id == tenant.id, Actor.role.in_(["COMPANY_ADMIN", "SUPER_ADMIN"])).limit(1))
    admin_actor = act_res.scalar_one_or_none()

    target_email = tenant.contact_email or (admin_actor.email if admin_actor and admin_actor.email else None)
    if not target_email:
        raise HTTPException(status_code=400, detail="Şirketin veya yönetici kullanıcısının geçerli bir e-posta adresi bulunamadı.")

    now = datetime.utcnow()
    days_rem = 0
    if tenant.package_expiry_date:
        exp_date = tenant.package_expiry_date.replace(tzinfo=None) if tenant.package_expiry_date.tzinfo else tenant.package_expiry_date
        days_rem = (exp_date - now).days

    plan_obj = await db.get(Plan, tenant.plan_id) if tenant.plan_id else None
    plan_title = plan_obj.name if plan_obj else "Kurumsal Paket"

    # Hatırlatıcı şablonu getir
    tmpl_res = await db.execute(select(EmailTemplate).where(EmailTemplate.code == "PACKAGE_EXPIRATION_REMINDER"))
    tmpl = tmpl_res.scalar_one_or_none()

    ctx = {
        "company_name": tenant.name,
        "plan_name": plan_title,
        "expiry_date": tenant.package_expiry_date.strftime("%d.%m.%Y") if tenant.package_expiry_date else "Belirtilmedi",
        "days_remaining": max(0, days_rem),
        "renewal_url": "http://localhost:5173/#/pricing"
    }

    sent = False
    if tmpl:
        sent = NotificationService.render_and_send_template(target_email, tmpl, ctx)
    else:
        sent = NotificationService.send_customer_account_activated_notification(ctx)

    if not sent:
        raise HTTPException(
            status_code=500,
            detail=f"'{tenant.name}' şirketine ({target_email}) hatırlatıcı e-postası iletilemedi. Lütfen sunucu e-posta ayarlarını kontrol ediniz."
        )

    tenant.last_reminder_sent_at = now
    await db.commit()

    return {
        "success": True,
        "message": f"'{tenant.name}' şirketine ({target_email}) hatırlatıcı e-postası başarıyla iletildi.",
        "days_remaining": days_rem,
        "sent_at": now.isoformat()
    }


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



