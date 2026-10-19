from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import uuid
from app.db.session import get_db
from app.db.models import SystemPermission, TenantRole, Actor

router = APIRouter(prefix="/system", tags=["Sistem Yönetimi & İzin Kataloğu (RECDx Süper Admin)"])

class PermissionCreate(BaseModel):
    code: str
    module: str
    name: str
    description: Optional[str] = None
    default_for_roles: List[str] = []
    is_system: bool = False

class PermissionResponse(BaseModel):
    id: uuid.UUID
    code: str
    module: str
    name: str
    description: Optional[str] = None
    default_for_roles: list
    is_system: bool

    class Config:
        from_attributes = True

@router.get("/permissions", response_model=List[PermissionResponse])
async def list_system_permissions(
    module: Optional[str] = Query(None, description="Modül filtresi (PLATFORM, RBAC, AGENTS, vb.)"),
    db: AsyncSession = Depends(get_db)
):
    """
    Sistemdeki tüm kurumsal izinleri listeler.
    RECDx Süper Admin ve Şirket Yöneticileri rol oluştururken bu listeden seçim yapar.
    """
    stmt = select(SystemPermission)
    if module:
        stmt = stmt.where(SystemPermission.module == module.upper())
    stmt = stmt.order_by(SystemPermission.module, SystemPermission.code)
    result = await db.execute(stmt)
    return result.scalars().all()

@router.post("/permissions", response_model=PermissionResponse)
async def create_system_permission(payload: PermissionCreate, db: AsyncSession = Depends(get_db)):
    """
    RECDx Süper Admin tarafından yeni bir yetki tanımı eklenmesi.
    """
    existing = await db.execute(select(SystemPermission).where(SystemPermission.code == payload.code))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail=f"'{payload.code}' kodlu izin zaten mevcut.")

    perm = SystemPermission(
        code=payload.code,
        module=payload.module.upper(),
        name=payload.name,
        description=payload.description,
        default_for_roles=payload.default_for_roles,
        is_system=payload.is_system
    )
    db.add(perm)
    await db.commit()
    await db.refresh(perm)
    return perm

@router.put("/permissions/{perm_id}", response_model=PermissionResponse)
async def update_system_permission(perm_id: uuid.UUID, payload: PermissionCreate, db: AsyncSession = Depends(get_db)):
    """
    Mevcut bir yetki tanımını güncelleme.
    """
    perm = await db.get(SystemPermission, perm_id)
    if not perm:
        raise HTTPException(status_code=404, detail="İzin tanımı bulunamadı.")

    perm.name = payload.name
    perm.module = payload.module.upper()
    perm.description = payload.description
    perm.default_for_roles = payload.default_for_roles
    
    await db.commit()
    await db.refresh(perm)
    return perm

@router.get("/permissions/{perm_id}", response_model=PermissionResponse)
async def get_system_permission(perm_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """
    Belirli bir yetki tanımının detaylarını getirir.
    """
    perm = await db.get(SystemPermission, perm_id)
    if not perm:
        raise HTTPException(status_code=404, detail="İzin tanımı bulunamadı.")
    return perm

@router.delete("/permissions/{perm_id}")
async def delete_system_permission(perm_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """
    Sistem yetki tanımını siler.
    """
    perm = await db.get(SystemPermission, perm_id)
    if not perm:
        raise HTTPException(status_code=404, detail="İzin tanımı bulunamadı.")
    await db.delete(perm)
    await db.commit()
    return {"success": True, "message": f"'{perm.code}' izin tanımı başarıyla silindi."}


# ==========================================
# SİSTEM YETKİ ROLLERİ YÖNETİMİ (Madde 1)
# ==========================================

class RoleCreate(BaseModel):
    name: str
    description: Optional[str] = None
    permissions: List[str] = []
    is_system: bool = True

class RoleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    permissions: Optional[List[str]] = None
    is_system: Optional[bool] = None

class RoleResponse(BaseModel):
    id: uuid.UUID
    tenant_id: Optional[uuid.UUID] = None
    name: str
    description: Optional[str] = None
    permissions: list = []
    is_system: bool = False
    created_at: Optional[datetime] = None
    actor_count: int = 0

    class Config:
        from_attributes = True

DEFAULT_SYSTEM_ROLES = [
    {
        "name": "Süper Yönetici (Platform Admin)",
        "description": "RECOrion platformunun tam yetkili yöneticisi. Tüm sistem, müşteri ve güvenlik ayarlarını yönetebilir.",
        "permissions": ["*"],
        "is_system": True
    },
    {
        "name": "Kurumsal Operasyon & Müşteri Yöneticisi",
        "description": "Müşteri ve kiralama paketlerini, onay süreçlerini ve bildirim zamanlayıcılarını yönetir.",
        "permissions": ["tenant:view", "tenant:manage", "billing:view"],
        "is_system": True
    },
    {
        "name": "Güvenlik & Uyum Denetçisi (SecOps & Compliance)",
        "description": "Erişim loglarını, rol tanımlarını ve RBAC izin hiyerarşisini denetler.",
        "permissions": ["tenant:view", "role:edit", "chat:export"],
        "is_system": True
    },
    {
        "name": "Yapay Zeka Mimarisi & Ajan Lideri",
        "description": "EVREN modellerini yapılandırır, otonom ajanları ve görev dağılımlarını orkestre eder.",
        "permissions": ["agent:hire", "agent:configure", "agent:custom_title", "agent:quarantine", "project:manage", "chat:participate", "chat:view_a2a"],
        "is_system": True
    },
    {
        "name": "Standart Kurumsal Kullanıcı",
        "description": "Temel sohbet, proje takibi ve hafıza arama yetkilerine sahip standart kullanıcı.",
        "permissions": ["tenant:view", "task:create", "chat:participate", "memory:search"],
        "is_system": True
    }
]

@router.get("/roles", response_model=List[RoleResponse])
async def list_system_roles(db: AsyncSession = Depends(get_db)):
    """
    Sistem genelindeki yetki rollerini ve her role atanmış aktör/kullanıcı sayısını listeler (Madde 1).
    Eğer henüz rol tanımlanmamışsa varsayılan kurumsal sistem rollerini otomatik tohumlar (seed).
    """
    stmt = (
        select(TenantRole, func.count(Actor.id).label("actor_count"))
        .outerjoin(Actor, Actor.role_id == TenantRole.id)
        .where(TenantRole.tenant_id.is_(None))
        .group_by(TenantRole.id)
        .order_by(TenantRole.is_system.desc(), TenantRole.created_at.asc())
    )
    rows = (await db.execute(stmt)).all()

    # Eğer hiç sistem rolü yoksa varsayılanları tohumla
    if not rows:
        perms_res = await db.execute(select(SystemPermission.code))
        all_perms = perms_res.scalars().all()

        for d in DEFAULT_SYSTEM_ROLES:
            perms = list(all_perms) if d["permissions"] == ["*"] else d["permissions"]
            role_obj = TenantRole(
                tenant_id=None,
                name=d["name"],
                description=d["description"],
                permissions=perms,
                is_system=d["is_system"]
            )
            db.add(role_obj)
        await db.commit()

        # Yeniden çek
        rows = (await db.execute(stmt)).all()

    result = []
    for role_obj, actor_count in rows:
        result.append(RoleResponse(
            id=role_obj.id,
            tenant_id=role_obj.tenant_id,
            name=role_obj.name,
            description=role_obj.description,
            permissions=role_obj.permissions or [],
            is_system=role_obj.is_system,
            created_at=role_obj.created_at,
            actor_count=actor_count
        ))
    return result

@router.post("/roles", response_model=RoleResponse)
async def create_system_role(payload: RoleCreate, db: AsyncSession = Depends(get_db)):
    """
    Süper Yönetici tarafından yeni bir Yetki Rolü tanımlanması (Madde 1).
    Alanlar:
    - Rol Adı (name)
    - Rol Açıklama (description)
    - İzin Kataloğundan Çoklu Seçilen İzinler (permissions)
    """
    cleaned_name = payload.name.strip()
    if not cleaned_name:
        raise HTTPException(status_code=400, detail="Rol adı zorunludur.")

    existing = await db.execute(
        select(TenantRole).where(TenantRole.tenant_id.is_(None), TenantRole.name == cleaned_name)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail=f"'{cleaned_name}' adında bir yetki rolü zaten mevcut.")

    role = TenantRole(
        tenant_id=None,
        name=cleaned_name,
        description=payload.description.strip() if payload.description else None,
        permissions=payload.permissions or [],
        is_system=payload.is_system
    )
    db.add(role)
    await db.commit()
    await db.refresh(role)

    return RoleResponse(
        id=role.id,
        tenant_id=role.tenant_id,
        name=role.name,
        description=role.description,
        permissions=role.permissions or [],
        is_system=role.is_system,
        created_at=role.created_at,
        actor_count=0
    )

@router.put("/roles/{role_id}", response_model=RoleResponse)
async def update_system_role(role_id: uuid.UUID, payload: RoleUpdate, db: AsyncSession = Depends(get_db)):
    """
    Mevcut Yetki Rolünü güncelleme (Madde 1).
    """
    role = await db.get(TenantRole, role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Yetki rolü bulunamadı.")

    if payload.name is not None:
        cleaned_name = payload.name.strip()
        if not cleaned_name:
            raise HTTPException(status_code=400, detail="Rol adı boş bırakılamaz.")
        existing = await db.execute(
            select(TenantRole).where(
                TenantRole.tenant_id.is_(None),
                TenantRole.name == cleaned_name,
                TenantRole.id != role_id
            )
        )
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=400, detail=f"'{cleaned_name}' adında başka bir rol mevcut.")
        role.name = cleaned_name

    if payload.description is not None:
        role.description = payload.description.strip() if payload.description else None

    if payload.permissions is not None:
        role.permissions = payload.permissions

    if payload.is_system is not None:
        role.is_system = payload.is_system

    await db.commit()
    await db.refresh(role)

    actor_count_res = await db.execute(
        select(func.count(Actor.id)).where(Actor.role_id == role.id)
    )
    actor_count = actor_count_res.scalar() or 0

    return RoleResponse(
        id=role.id,
        tenant_id=role.tenant_id,
        name=role.name,
        description=role.description,
        permissions=role.permissions or [],
        is_system=role.is_system,
        created_at=role.created_at,
        actor_count=actor_count
    )

@router.delete("/roles/{role_id}")
async def delete_system_role(role_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """
    Yetki Rolünü sistemden silme (Madde 1).
    Eğer role atanmış kullanıcı/aktör varsa silme engellenir.
    """
    role = await db.get(TenantRole, role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Yetki rolü bulunamadı.")

    actor_count_res = await db.execute(
        select(func.count(Actor.id)).where(Actor.role_id == role_id)
    )
    actor_count = actor_count_res.scalar() or 0

    if actor_count > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Bu yetki rolüne atanmış {actor_count} adet aktif kullanıcı/aktör bulunmaktadır. Silmeden önce kullanıcıların rollerini değiştiriniz."
        )

    await db.delete(role)
    await db.commit()
    return {"success": True, "message": f"'{role.name}' yetki rolü başarıyla silindi."}


class SettingUpdatePayload(BaseModel):
    model_code: str

@router.get("/settings")
async def get_system_settings(db: AsyncSession = Depends(get_db)):
    """
    Sistem genelindeki ayarları (varsayılan AI modeli vb.) döndürür.
    """
    from app.db.models import SystemSetting
    result = await db.execute(select(SystemSetting))
    settings = result.scalars().all()
    res = {s.key: s.value for s in settings}
    if "default_manifesto_model" not in res:
        res["default_manifesto_model"] = "deepseek-v4.1-flash"
    return res

@router.get("/settings/default-manifesto-model")
async def get_default_manifesto_model(db: AsyncSession = Depends(get_db)):
    from app.db.models import SystemSetting
    setting = await db.get(SystemSetting, "default_manifesto_model")
    return {"model_code": setting.value if setting else "deepseek-v4.1-flash"}

@router.post("/settings/default-manifesto-model")
async def set_default_manifesto_model(payload: SettingUpdatePayload, db: AsyncSession = Depends(get_db)):
    """
    NACE kodları ve sektör manifestosu/rol promptu üreten Genel AI Modelini seçer (Madde 6).
    """
    from app.db.models import SystemSetting, LLMModel
    # Modelin sistemde olup olmadığını kontrol et
    m_res = await db.execute(select(LLMModel).where(LLMModel.model_code == payload.model_code))
    model_obj = m_res.scalar_one_or_none()
    if not model_obj:
        raise HTTPException(status_code=404, detail=f"'{payload.model_code}' kodlu model sistemde bulunamadı.")

    setting = await db.get(SystemSetting, "default_manifesto_model")
    if not setting:
        setting = SystemSetting(
            key="default_manifesto_model",
            value=payload.model_code,
            description="NACE kodlarına göre şirket manifestosu ve ajan rollerini oluşturan en güçlü EVREN LLM modeli"
        )
        db.add(setting)
    else:
        setting.value = payload.model_code

    await db.commit()
    return {
        "success": True, 
        "message": f"Genel AI Modeli başarıyla '{model_obj.display_name}' ({model_obj.model_code}) olarak güncellendi.",
        "model_code": payload.model_code,
        "display_name": model_obj.display_name
    }


# ================= EMAIL TEMPLATES (Madde 1) =================
from app.db.models import EmailTemplate, NotificationSchedule, Tenant, Plan
from app.services.notification_service import NotificationService

class EmailTemplateCreate(BaseModel):
    code: str
    name: str
    subject: str
    html_content: str
    text_content: Optional[str] = None
    variables: List[str] = []
    is_active: bool = True

class EmailTemplateUpdate(BaseModel):
    name: str
    subject: str
    html_content: str
    text_content: Optional[str] = None
    variables: List[str] = []
    is_active: bool = True

class TestEmailPayload(BaseModel):
    to_email: str
    context: Optional[dict] = None

class NotificationScheduleCreate(BaseModel):
    name: str
    trigger_type: str
    template_code: str
    frequency_days: int = 15
    target_lead_days: int = 90
    is_active: bool = True

class NotificationScheduleUpdate(BaseModel):
    name: str
    trigger_type: str
    template_code: str
    frequency_days: int = 15
    target_lead_days: int = 90
    is_active: bool = True


@router.get("/email-templates")
async def list_email_templates(db: AsyncSession = Depends(get_db)):
    """
    Sistemdeki HTML e-posta şablonlarını listeler (Madde 1).
    """
    res = await db.execute(select(EmailTemplate).order_by(EmailTemplate.created_at.desc()))
    return res.scalars().all()

@router.post("/email-templates")
async def create_email_template(payload: EmailTemplateCreate, db: AsyncSession = Depends(get_db)):
    """
    Yeni bir HTML e-posta şablonu kaydeder (Madde 1).
    """
    code_safe = payload.code.upper().strip()
    existing = await db.execute(select(EmailTemplate).where(EmailTemplate.code == code_safe))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail=f"'{code_safe}' kodlu e-posta şablonu zaten mevcut.")
    
    tmpl = EmailTemplate(
        code=code_safe,
        name=payload.name,
        subject=payload.subject,
        html_content=payload.html_content,
        text_content=payload.text_content,
        variables=payload.variables,
        is_active=payload.is_active
    )
    db.add(tmpl)
    await db.commit()
    await db.refresh(tmpl)
    return tmpl

@router.get("/email-templates/{tmpl_id}")
async def get_email_template(tmpl_id: str, db: AsyncSession = Depends(get_db)):
    try:
        u_id = uuid.UUID(tmpl_id)
        tmpl = await db.get(EmailTemplate, u_id)
    except ValueError:
        res = await db.execute(select(EmailTemplate).where(EmailTemplate.code == tmpl_id))
        tmpl = res.scalar_one_or_none()
    
    if not tmpl:
        raise HTTPException(status_code=404, detail="E-posta şablonu bulunamadı.")
    return tmpl

@router.put("/email-templates/{tmpl_id}")
async def update_email_template(tmpl_id: uuid.UUID, payload: EmailTemplateUpdate, db: AsyncSession = Depends(get_db)):
    tmpl = await db.get(EmailTemplate, tmpl_id)
    if not tmpl:
        raise HTTPException(status_code=404, detail="E-posta şablonu bulunamadı.")
    
    tmpl.name = payload.name
    tmpl.subject = payload.subject
    tmpl.html_content = payload.html_content
    tmpl.text_content = payload.text_content
    tmpl.variables = payload.variables
    tmpl.is_active = payload.is_active

    await db.commit()
    await db.refresh(tmpl)
    return tmpl

@router.delete("/email-templates/{tmpl_id}")
async def delete_email_template(tmpl_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """
    E-Posta Şablonu Silme (Madde 6):
    E-posta şablonu kullanılmadı ise silinebilir, sistemde veya zamanlayıcılarda kullanımda ise silinemez.
    """
    tmpl = await db.get(EmailTemplate, tmpl_id)
    if not tmpl:
        raise HTTPException(status_code=404, detail="E-posta şablonu bulunamadı.")

    # 1. Temel sistem şablonları silinemez
    system_critical_codes = ["WELCOME_CUSTOMER", "PACKAGE_EXPIRATION_REMINDER"]
    if tmpl.code in system_critical_codes:
        raise HTTPException(
            status_code=400,
            detail=f"'{tmpl.name}' ({tmpl.code}) sistemin temel e-posta şablonudur. Sistem güvenliği ve müşteri iletişimi gereği silinemez!"
        )

    # 2. Otomatik bildirim zamanlayıcılarında (Notification Schedules) tanımlı/kullanımda mı?
    sched_res = await db.execute(select(NotificationSchedule).where(NotificationSchedule.template_code == tmpl.code))
    bound_scheds = sched_res.scalars().all()
    if bound_scheds:
        sched_names = ", ".join([f"'{s.name}'" for s in bound_scheds])
        raise HTTPException(
            status_code=400,
            detail=f"'{tmpl.name}' ({tmpl.code}) şablonu şu anda aktif zamanlayıcılar ({sched_names}) tarafından kullanılmaktadır! Kullanımda olan şablonlar silinemez. Silmek için önce ilgili zamanlayıcıları kaldırınız veya güncelleyiniz."
        )

    await db.delete(tmpl)
    await db.commit()
    return {"success": True, "message": f"'{tmpl.name}' şablonu başarıyla silindi."}

@router.post("/email-templates/{tmpl_id}/test-send")
async def send_test_email_template(tmpl_id: uuid.UUID, payload: TestEmailPayload, db: AsyncSession = Depends(get_db)):
    tmpl = await db.get(EmailTemplate, tmpl_id)
    if not tmpl:
        raise HTTPException(status_code=404, detail="E-posta şablonu bulunamadı.")
    
    sample_ctx = {
        "company_name": "Örnek Teknoloji A.Ş.",
        "plan_name": "RECOrion Kurumsal Pro",
        "start_date": "10.10.2026",
        "expiry_date": "10.10.2027",
        "days_remaining": 45,
        "admin_email": payload.to_email,
        "admin_password": "GucluSifre2026!",
        "portal_url": "http://localhost:5173",
        "renewal_url": "http://localhost:5173/#/pricing"
    }
    if payload.context:
        sample_ctx.update(payload.context)

    sent = NotificationService.render_and_send_template(payload.to_email, tmpl, sample_ctx)
    if not sent:
        raise HTTPException(
            status_code=500,
            detail=f"'{tmpl.name}' test e-postası '{payload.to_email}' adresine iletilemedi. Lütfen sunucu SMTP ayarlarını kontrol ediniz."
        )
    return {
        "success": True,
        "message": f"'{tmpl.name}' şablonu test amacıyla '{payload.to_email}' adresine başarıyla iletildi."
    }


# ================= NOTIFICATION SCHEDULES (Madde 2 & 14) =================
@router.get("/schedules")
async def list_notification_schedules(db: AsyncSession = Depends(get_db)):
    """
    Sistemdeki otomatik e-posta zamanlayıcılarını listeler (Madde 2).
    """
    res = await db.execute(select(NotificationSchedule).order_by(NotificationSchedule.created_at.desc()))
    return res.scalars().all()

@router.post("/schedules")
async def create_notification_schedule(payload: NotificationScheduleCreate, db: AsyncSession = Depends(get_db)):
    sched = NotificationSchedule(
        name=payload.name,
        trigger_type=payload.trigger_type,
        template_code=payload.template_code,
        frequency_days=payload.frequency_days,
        target_lead_days=payload.target_lead_days,
        is_active=payload.is_active
    )
    db.add(sched)
    await db.commit()
    await db.refresh(sched)
    return sched

@router.put("/schedules/{sched_id}")
async def update_notification_schedule(sched_id: uuid.UUID, payload: NotificationScheduleUpdate, db: AsyncSession = Depends(get_db)):
    sched = await db.get(NotificationSchedule, sched_id)
    if not sched:
        raise HTTPException(status_code=404, detail="Zamanlama görevi bulunamadı.")
    
    sched.name = payload.name
    sched.trigger_type = payload.trigger_type
    sched.template_code = payload.template_code
    sched.frequency_days = payload.frequency_days
    sched.target_lead_days = payload.target_lead_days
    sched.is_active = payload.is_active

    await db.commit()
    await db.refresh(sched)
    return sched

@router.delete("/schedules/{sched_id}")
async def delete_notification_schedule(sched_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    sched = await db.get(NotificationSchedule, sched_id)
    if not sched:
        raise HTTPException(status_code=404, detail="Zamanlama görevi bulunamadı.")
    await db.delete(sched)
    await db.commit()
    return {"success": True, "message": f"'{sched.name}' zamanlama görevi silindi."}

@router.post("/schedules/{sched_id}/trigger")
async def trigger_schedule_manually(sched_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """
    Zamanlanmış görevi hemen çalıştırır (Madde 2 & 14):
    Paket bitimine 3 ay (90 gün) kala olan şirketleri tarar,
    15 gündür bildirim gitmemişse şablonu render edip gönderir.
    """
    from datetime import datetime, timedelta
    sched = await db.get(NotificationSchedule, sched_id)
    if not sched:
        raise HTTPException(status_code=404, detail="Zamanlama görevi bulunamadı.")

    t_res = await db.execute(select(EmailTemplate).where(EmailTemplate.code == sched.template_code))
    tmpl = t_res.scalar_one_or_none()

    processed_count = 0
    now = datetime.utcnow()

    if sched.trigger_type == 'BEFORE_EXPIRATION_INTERVAL':
        tenants_res = await db.execute(select(Tenant).where(Tenant.is_active == True))
        active_tenants = tenants_res.scalars().all()
        
        for t in active_tenants:
            if not t.package_expiry_date or not t.contact_email:
                continue
            
            exp_date = t.package_expiry_date.replace(tzinfo=None) if t.package_expiry_date.tzinfo else t.package_expiry_date
            days_remaining = (exp_date - now).days
            
            # 3 ay (<= 90 gün) ve henüz süresi bitmemiş
            if 0 <= days_remaining <= sched.target_lead_days:
                should_send = True
                if t.last_reminder_sent_at:
                    last_sent = t.last_reminder_sent_at.replace(tzinfo=None) if t.last_reminder_sent_at.tzinfo else t.last_reminder_sent_at
                    since_last = (now - last_sent).days
                    if since_last < sched.frequency_days:
                        should_send = False
                
                if should_send:
                    plan_obj = await db.get(Plan, t.plan_id) if t.plan_id else None
                    p_name = plan_obj.name if plan_obj else "Kurumsal Paket"
                    
                    ctx = {
                        "company_name": t.name,
                        "plan_name": p_name,
                        "expiry_date": t.package_expiry_date.strftime("%d.%m.%Y"),
                        "days_remaining": days_remaining,
                        "renewal_url": "http://localhost:5173/#/pricing"
                    }
                    if tmpl:
                        NotificationService.render_and_send_template(t.contact_email, tmpl, ctx)
                    else:
                        NotificationService.send_customer_account_activated_notification(ctx)
                    
                    t.last_reminder_sent_at = now
                    processed_count += 1
        
        sched.last_run_at = now
        sched.next_run_at = now + timedelta(days=sched.frequency_days)
        await db.commit()

    return {
        "success": True,
        "message": f"'{sched.name}' başarıyla çalıştırıldı. {processed_count} adet kuruma hatırlatıcı iletildi.",
        "processed_count": processed_count
    }

