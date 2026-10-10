from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, func
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import uuid
import re
from app.db.session import get_db
from app.db.models import Tenant, NaceCatalog, Plan, Actor, TenantLead, EmailTemplate
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

class NaceCreate(BaseModel):
    code: str
    title: str
    sector_group: str
    description: Optional[str] = None

class NaceUpdate(BaseModel):
    title: str
    sector_group: str
    description: Optional[str] = None

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
    nace_codes: List[str] = []
    admin_name: str = "Şirket Yöneticisi"
    admin_password: Optional[str] = None
    activate_package: bool = True
    send_welcome_email: bool = True

class ManifestoRequest(BaseModel):
    company_name: str
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
async def list_plans(db: AsyncSession = Depends(get_db)):
    """
    Sistemdeki kiralama paketlerini listeler (Madde 7).
    """
    result = await db.execute(select(Plan).order_by(Plan.monthly_price.asc()))
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

@router.get("/nace-catalog")
async def get_nace_catalog(
    query: Optional[str] = Query(None, description="Kod veya faaliyet alanında arama"),
    sector: Optional[str] = Query(None, description="Sektör grubu filtresi"),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db)
):
    """
    Sistemdeki NACE Rev.2 faaliyet kodlarını listeler ve filtreler (Madde 12).
    """
    stmt = select(NaceCatalog)
    if query:
        patterns = _turkish_search_variants(query)
        conditions = [NaceCatalog.code.ilike(f"%{query.strip()}%")]
        for p in patterns:
            conditions.append(NaceCatalog.title.ilike(f"%{p}%"))
        stmt = stmt.where(or_(*conditions))
    if sector:
        stmt = stmt.where(NaceCatalog.sector_group == sector)

    stmt = stmt.order_by(NaceCatalog.code.asc()).limit(limit).offset(offset)
    result = await db.execute(stmt)
    items = result.scalars().all()
    return items

@router.post("/nace-catalog")
async def create_nace_code(payload: NaceCreate, db: AsyncSession = Depends(get_db)):
    """
    Yeni NACE Kodu Tanımlama (Madde 12).
    """
    code_clean = payload.code.strip()
    existing = await db.get(NaceCatalog, code_clean)
    if existing:
        raise HTTPException(status_code=400, detail=f"'{code_clean}' kodlu NACE tanımı zaten mevcut.")

    item = NaceCatalog(
        code=code_clean,
        title=payload.title.strip(),
        sector_group=payload.sector_group.strip(),
        description=payload.description
    )
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return item

@router.get("/nace-catalog/{code}")
async def get_nace_code(code: str, db: AsyncSession = Depends(get_db)):
    item = await db.get(NaceCatalog, code.strip())
    if not item:
        raise HTTPException(status_code=404, detail="NACE kodu bulunamadı.")
    return item

@router.put("/nace-catalog/{code}")
async def update_nace_code(code: str, payload: NaceUpdate, db: AsyncSession = Depends(get_db)):
    """
    NACE Kodu Güncelleme (Madde 12).
    """
    item = await db.get(NaceCatalog, code.strip())
    if not item:
        raise HTTPException(status_code=404, detail="NACE kodu bulunamadı.")

    item.title = payload.title.strip()
    item.sector_group = payload.sector_group.strip()
    item.description = payload.description

    await db.commit()
    await db.refresh(item)
    return item

@router.delete("/nace-catalog/{code}")
async def delete_nace_code(code: str, db: AsyncSession = Depends(get_db)):
    """
    NACE Kodu Silme (Madde 12).
    """
    item = await db.get(NaceCatalog, code.strip())
    if not item:
        raise HTTPException(status_code=404, detail="NACE kodu bulunamadı.")

    await db.delete(item)
    await db.commit()
    return {"success": True, "message": f"'{item.code}' ({item.title}) NACE kodu başarıyla silindi."}

@router.get("", response_model=List[TenantResponse])
@router.get("/", response_model=List[TenantResponse])
async def list_tenants(db: AsyncSession = Depends(get_db)):
    import re
    # 0. Henüz Tenant kaydı açılmamış bekleyen (PENDING) lead'leri otomatik senkronize et
    pending_leads_res = await db.execute(select(TenantLead).where(TenantLead.status == "PENDING"))
    pending_leads = pending_leads_res.scalars().all()
    if pending_leads:
        existing_tenants_res = await db.execute(select(Tenant))
        existing_tenants = existing_tenants_res.scalars().all()
        existing_slugs = {t.slug for t in existing_tenants}
        created_any = False
        for pl in pending_leads:
            lead_slug_part = str(pl.id)[:6]
            has_tenant = any(lead_slug_part in t.slug for t in existing_tenants)
            if not has_tenant:
                clean_slug = re.sub(r'[^a-zA-Z0-9]', '', pl.company_name.lower())[:16] or "tenant"
                slug_cand = f"{clean_slug}_{lead_slug_part}"
                if slug_cand in existing_slugs:
                    slug_cand = f"{clean_slug}_{str(uuid.uuid4())[:6]}"
                new_t = Tenant(
                    slug=slug_cand,
                    name=pl.company_name,
                    tax_id=pl.tax_id,
                    tax_office=pl.tax_office,
                    phone=pl.phone,
                    address=pl.address,
                    website=pl.website,
                    contact_email=pl.contact_email,
                    plan_id=pl.plan_id,
                    nace_codes=pl.nace_codes or [],
                    sector_manifesto=pl.generated_manifesto,
                    package_start_date=None,
                    package_expiry_date=None,
                    is_active=False
                )
                db.add(new_t)
                await db.flush()

                contact_name = "Şirket Yöneticisi"
                pw_hash = None
                if pl.notes:
                    for part in pl.notes.split("|"):
                        if "Yetkili:" in part:
                            contact_name = part.replace("Yetkili:", "").strip()
                        if "PasswordHash:" in part:
                            pw_hash = part.replace("PasswordHash:", "").strip()

                admin_actor = Actor(
                    tenant_id=new_t.id,
                    actor_type="HUMAN",
                    display_name=f"{contact_name} (Yönetici)",
                    email=pl.contact_email,
                    phone=pl.phone,
                    address=pl.address,
                    role="COMPANY_ADMIN",
                    password_hash=pw_hash,
                    autonomy_level="L3",
                    status="DISABLED"
                )
                db.add(admin_actor)
                existing_slugs.add(slug_cand)
                created_any = True
        if created_any:
            await db.commit()

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

@router.post("/", response_model=TenantResponse)
async def create_tenant(payload: TenantCreate, db: AsyncSession = Depends(get_db)):
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
        nace_codes=payload.nace_codes,
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
            "nace_codes": tenant.nace_codes or [],
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
    tenant.nace_codes = payload.nace_codes
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

@router.put("/{tenant_id}/admin-user")
async def update_tenant_admin_user(tenant_id: uuid.UUID, payload: TenantAdminUpdate, db: AsyncSession = Depends(get_db)):
    """
    Şirket Admin rolündeki kullanıcının bilgilerini ve şifresini güncelleme (Madde 5).
    """
    from app.api.v1.auth import hash_password
    actor = None
    if payload.actor_id:
        actor = await db.get(Actor, payload.actor_id)
    else:
        # Şirketin ilk COMPANY_ADMIN kullanıcısını bul
        stmt = select(Actor).where(Actor.tenant_id == tenant_id, Actor.role == "COMPANY_ADMIN").limit(1)
        res = await db.execute(stmt)
        actor = res.scalar_one_or_none()

    if not actor:
        # Eğer hiç admin yoksa oluştur
        actor = Actor(
            tenant_id=tenant_id,
            actor_type="HUMAN",
            display_name=payload.display_name.strip(),
            email=payload.email.strip().lower(),
            phone=payload.phone,
            address=payload.address,
            role="COMPANY_ADMIN",
            autonomy_level="L3",
            status="IDLE"
        )
        db.add(actor)
    else:
        actor.display_name = payload.display_name.strip()
        actor.email = payload.email.strip().lower()
        actor.phone = payload.phone
        actor.address = payload.address

    if payload.new_password and len(payload.new_password.strip()) >= 6:
        actor.password_hash = hash_password(payload.new_password.strip())

    await db.commit()
    await db.refresh(actor)
    return {
        "success": True,
        "message": f"Şirket yöneticisi '{actor.display_name}' ({actor.email}) başarıyla güncellendi.",
        "actor_id": str(actor.id),
        "display_name": actor.display_name,
        "email": actor.email
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
    - NACE kodlarını çözümler ve AI ile Kurumsal Manifesto üretir
    - Odoo 19 üzerinde res.partner ve sale.order (teklif) oluşturur
    - info@recdx.com adresine bildirim gönderir
    - Müşteri e-postasına profesyonel onay e-postası gönderir
    """
    import hashlib
    from app.db.models import TenantLead
    from app.services.manifesto_service import ManifestoService
    from app.services.notification_service import NotificationService
    from app.services.odoo_service import OdooService

    # 1. Planı bul
    p_res = await db.execute(select(Plan).where(Plan.code == payload.plan_code.upper()))
    plan = p_res.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail=f"'{payload.plan_code}' kodlu kiralama paketi bulunamadı.")

    # 2. Seçilen NACE kodlarının başlıklarını sorgula
    nace_items = []
    if payload.nace_codes:
        n_res = await db.execute(select(NaceCatalog).where(NaceCatalog.code.in_(payload.nace_codes)))
        for nc in n_res.scalars().all():
            nace_items.append({"code": nc.code, "title": nc.title, "sector_group": nc.sector_group})

    # 3. AI ile Kurumsal Manifesto Üret
    manifesto_data = ManifestoService.generate_manifesto(
        company_name=payload.company_name,
        nace_items=nace_items,
        website=payload.website
    )

    # 4. Güvenli Şifre Hashleme (SHA-256 + Salt)
    salt = "recorion_tenant_salt_2026"
    pw_hash = hashlib.sha256(f"{salt}_{payload.password}".encode("utf-8")).hexdigest()

    # 5. Odoo 19 res.partner & sale.order Entegrasyonu (A maddesi)
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

    # 6. Lead Kaydını Oluştur
    lead = TenantLead(
        plan_id=plan.id,
        company_name=payload.company_name,
        tax_id=payload.tax_id,
        tax_office=payload.tax_office,
        address=payload.address,
        phone=payload.phone,
        website=payload.website,
        contact_email=payload.contact_email,
        nace_codes=payload.nace_codes,
        generated_manifesto=manifesto_data["manifesto"],
        assigned_skills=manifesto_data["assigned_skills"],
        odoo_partner_id=odoo_partner_id,
        odoo_order_id=odoo_order_id,
        odoo_order_name=odoo_order_name,
        status="PENDING",
        notes=f"Yetkili: {payload.contact_name} | PasswordHash: {pw_hash} | InitialPassword: {payload.password} | Sektör: {manifesto_data['sector_focus']} | OdooRef: {odoo_order_name or 'N/A'}"
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
        nace_codes=payload.nace_codes or [],
        sector_manifesto=manifesto_data["manifesto"],
        package_start_date=None,
        package_expiry_date=None,
        is_active=False
    )
    db.add(pending_tenant)
    await db.flush()

    # 6.2. Şirket Yöneticisi Aktörü Oluştur (DISABLED / ONAY BEKLİYOR)
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
        status="DISABLED"
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
        "nace_codes": payload.nace_codes,
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

    # 3. Mevcut unapproved Tenant var mı kontrol et, varsa aktif et, yoksa oluştur
    lead_slug_part = str(lead.id)[:6]
    existing_tenant_res = await db.execute(
        select(Tenant).where(
            (Tenant.slug.contains(lead_slug_part)) | 
            ((Tenant.name == lead.company_name) & (Tenant.contact_email == lead.contact_email))
        )
    )
    tenant = existing_tenant_res.scalar_one_or_none()

    if tenant:
        tenant.is_active = True
        tenant.package_start_date = start_date
        tenant.package_expiry_date = expiry_date
        if not tenant.plan_id:
            tenant.plan_id = lead.plan_id
        if not tenant.nace_codes:
            tenant.nace_codes = lead.nace_codes
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
            nace_codes=lead.nace_codes,
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
            if "InitialPassword:" in part:
                initial_pw = part.replace("InitialPassword:", "").strip()

    admin_actor_res = await db.execute(
        select(Actor).where(Actor.tenant_id == tenant.id, Actor.role == "COMPANY_ADMIN")
    )
    admin_actor = admin_actor_res.scalar_one_or_none()
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
        OdooService.confirm_sale_order(lead.odoo_order_id)

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

    tmpl_res = await db.execute(select(EmailTemplate).where(EmailTemplate.code == "WELCOME_CUSTOMER"))
    welcome_tmpl = tmpl_res.scalar_one_or_none()
    email_sent = False
    if welcome_tmpl:
        email_sent = NotificationService.render_and_send_template(lead.contact_email, welcome_tmpl, welcome_ctx)
    else:
        email_sent = NotificationService.send_customer_account_activated_notification(welcome_ctx)

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
    if payload.nace_codes:
        n_res = await db.execute(select(NaceCatalog).where(NaceCatalog.code.in_(payload.nace_codes)))
        for nc in n_res.scalars().all():
            nace_items.append({"code": nc.code, "title": nc.title, "sector_group": nc.sector_group})
    
    manifesto_data = ManifestoService.generate_manifesto(
        company_name=payload.name,
        nace_items=nace_items,
        website=payload.website
    )

    # 4. Paket Tarihleri (Onay durumuna göre)
    if payload.activate_package:
        start_date = datetime.utcnow()
        expiry_date = start_date + timedelta(days=365)
        is_active = True
        actor_status = "IDLE"
    else:
        start_date = None
        expiry_date = None
        is_active = False
        actor_status = "DISABLED"

    tenant = Tenant(
        slug=slug_candidate,
        name=payload.name.strip(),
        tax_id=payload.tax_id,
        tax_office=payload.tax_office,
        phone=payload.phone,
        address=payload.address,
        website=payload.website,
        contact_email=payload.contact_email.strip().lower(),
        plan_id=payload.plan_id,
        nace_codes=payload.nace_codes,
        sector_manifesto=manifesto_data["manifesto"],
        package_start_date=start_date,
        package_expiry_date=expiry_date,
        is_active=is_active
    )
    db.add(tenant)
    await db.flush()

    # 5. Admin Actor oluştur
    admin_actor = Actor(
        tenant_id=tenant.id,
        actor_type="HUMAN",
        display_name=payload.admin_name.strip() or f"{payload.name} Yöneticisi",
        email=payload.contact_email.strip().lower(),
        role="COMPANY_ADMIN",
        password_hash=hash_password(plain_password),
        autonomy_level="L3",
        status=actor_status
    )
    db.add(admin_actor)

    # 6. TenantLead ile de senkronize et
    lead = TenantLead(
        company_name=tenant.name,
        contact_email=tenant.contact_email,
        phone=tenant.phone,
        tax_id=tenant.tax_id,
        tax_office=tenant.tax_office,
        website=tenant.website,
        address=tenant.address,
        plan_id=tenant.plan_id,
        status="APPROVED" if is_active else "PENDING"
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
            "odoo_order_name": "Süper Admin Doğrudan Kayıt",
            "login_url": "http://localhost:5173/"
        }

        tmpl_res = await db.execute(select(EmailTemplate).where(EmailTemplate.code == "WELCOME_CUSTOMER"))
        welcome_tmpl = tmpl_res.scalar_one_or_none()
        if welcome_tmpl:
            email_sent = NotificationService.render_and_send_template(tenant.contact_email, welcome_tmpl, welcome_ctx)
        else:
            email_sent = NotificationService.send_customer_account_activated_notification(welcome_ctx)

    msg = f"'{tenant.name}' kurumu başarıyla oluşturuldu ve paketi aktif edildi." if is_active else f"'{tenant.name}' kurumu paketi başlatılmadan (onay bekleyen olarak) kaydedildi."

    return {
        "success": True,
        "message": msg,
        "tenant_id": str(tenant.id),
        "slug": tenant.slug,
        "admin_email": admin_actor.email,
        "admin_password": plain_password,
        "is_active": is_active,
        "package_expiry_date": expiry_date.isoformat() if expiry_date else None,
        "welcome_email_sent": email_sent
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
    Şirket adı ve seçilen NACE kodlarına göre Kurumsal AI Manifestosu üretir (Madde 13).
    """
    from app.services.manifesto_service import ManifestoService
    nace_items = []
    if payload.nace_codes:
        n_res = await db.execute(select(NaceCatalog).where(NaceCatalog.code.in_(payload.nace_codes)))
        for nc in n_res.scalars().all():
            nace_items.append({"code": nc.code, "title": nc.title, "sector_group": nc.sector_group})

    data = ManifestoService.generate_manifesto(
        company_name=payload.company_name,
        nace_items=nace_items,
        website=payload.website
    )
    return data



