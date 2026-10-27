from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import uuid
from app.core import permission_catalog as pc
from app.core.security import CurrentUser, get_current_user
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
    module_name: Optional[str] = None
    enforced: bool = True  # False: henüz bir işleme bağlı değil (kodda denetlenmiyor)

    class Config:
        from_attributes = True


def _perm_out(p: SystemPermission) -> PermissionResponse:
    out = PermissionResponse.model_validate(p)
    out.module_name = pc.MODULES.get(p.module, p.module)
    out.enforced = p.code in pc.CODES and p.code not in pc.NOT_ENFORCED
    return out


@router.get("/permission-modules")
async def list_permission_modules():
    """İzin modülleri (kod -> ekranda görünen ad), müşteri menüsü sırasıyla."""
    return [{"code": k, "name": v} for k, v in pc.MODULES.items()]


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
    order = {m: i for i, m in enumerate(pc.MODULES)}
    rank = {c: i for i, c in enumerate(pc.CODES)}
    rows = (await db.execute(stmt)).scalars().all()
    rows.sort(key=lambda p: (order.get(p.module, 99), rank.get(p.code, 999), p.code))
    return [_perm_out(p) for p in rows]

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
    base_role: Optional[str] = None

class RoleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    permissions: Optional[List[str]] = None
    is_system: Optional[bool] = None
    base_role: Optional[str] = None

BASE_ROLES = ("COMPANY_ADMIN", "PROJECT_MANAGER", "USER")  # SUPER_ADMIN yalnızca göçle (RECDx rolü)


async def _check_role_payload(db: AsyncSession, permissions: Optional[List[str]], base_role: Optional[str]) -> None:
    if permissions:
        valid = set((await db.execute(select(SystemPermission.code))).scalars().all())
        bad = sorted({p for p in permissions if p not in valid and p != "*"})
        if bad:
            raise HTTPException(status_code=400, detail=f"Geçersiz izin kodları: {', '.join(bad)}")
    if base_role and base_role not in BASE_ROLES:
        raise HTTPException(status_code=400, detail="Temel rol Şirket Yöneticisi, Proje Yöneticisi, Uzman Kullanıcı veya boş olabilir.")


def is_platform_role(role: TenantRole) -> bool:
    """Yalnızca RECDx'e ait rol: müşterilere listelenmez ve atanamaz."""
    perms = set(role.permissions or [])
    return role.base_role == "SUPER_ADMIN" or bool(perms & pc.PLATFORM_ONLY)

class RoleResponse(BaseModel):
    id: uuid.UUID
    tenant_id: Optional[uuid.UUID] = None
    name: str
    description: Optional[str] = None
    permissions: list = []
    is_system: bool = False
    base_role: Optional[str] = None
    base_role_name: Optional[str] = None
    created_at: Optional[datetime] = None
    actor_count: int = 0

    class Config:
        from_attributes = True


def _role_out(role_obj: TenantRole, actor_count: int) -> RoleResponse:
    return RoleResponse(
        id=role_obj.id, tenant_id=role_obj.tenant_id, name=role_obj.name, description=role_obj.description,
        permissions=role_obj.permissions or [], is_system=role_obj.is_system, base_role=role_obj.base_role,
        base_role_name=pc.role_label(role_obj.base_role) if role_obj.base_role else None,
        created_at=role_obj.created_at, actor_count=actor_count,
    )


@router.get("/roles", response_model=List[RoleResponse])
async def list_system_roles(user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
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

        for d in pc.SYSTEM_ROLES:
            perms = list(all_perms) if d["permissions"] == ["*"] else list(d["permissions"])
            db.add(TenantRole(tenant_id=None, name=d["name"], description=d["description"], permissions=perms,
                              is_system=True, base_role=d.get("base_role")))
        await db.commit()

        # Yeniden çek
        rows = (await db.execute(stmt)).all()

    # Müşteriler RECDx'e ait rolü görmez; şirket başına kullanıcı sayısı da yalnızca RECDx'e gösterilir
    if not user.is_platform_staff:
        return [_role_out(r, 0) for r, _ in rows if not is_platform_role(r)]
    return [_role_out(r, n) for r, n in rows]

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
    await _check_role_payload(db, payload.permissions, payload.base_role)

    role = TenantRole(
        tenant_id=None,
        name=cleaned_name,
        description=payload.description.strip() if payload.description else None,
        permissions=payload.permissions or [],
        is_system=payload.is_system,
        base_role=payload.base_role or None,
    )
    db.add(role)
    await db.commit()
    await db.refresh(role)

    return _role_out(role, 0)

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

    if role.base_role == "SUPER_ADMIN" and (payload.permissions is not None or "base_role" in payload.model_fields_set):
        raise HTTPException(status_code=400, detail="RECDx süper yönetici rolünün izinleri değiştirilemez.")
    await _check_role_payload(db, payload.permissions, payload.base_role)
    if payload.permissions is not None:
        role.permissions = payload.permissions
    if "base_role" in payload.model_fields_set:
        role.base_role = payload.base_role or None
        # Bu role bağlı kullanıcıların rol kodu da güncellenir (şirket yöneticisi denetimleri buna bakar)
        for a in (await db.execute(select(Actor).where(Actor.role_id == role.id))).scalars():
            a.role = role.base_role or role.name

    if payload.is_system is not None:
        role.is_system = payload.is_system

    await db.commit()
    await db.refresh(role)

    actor_count_res = await db.execute(
        select(func.count(Actor.id)).where(Actor.role_id == role.id)
    )
    actor_count = actor_count_res.scalar() or 0

    return _role_out(role, actor_count)

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
    builder_blocks: Optional[list] = None  # sürükle-bırak editör blokları
    is_active: bool = True

class EmailTemplateUpdate(BaseModel):
    name: str
    subject: str
    html_content: str
    text_content: Optional[str] = None
    variables: List[str] = []
    builder_blocks: Optional[list] = None  # sürükle-bırak editör blokları
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
        builder_blocks=payload.builder_blocks,
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
    tmpl.builder_blocks = payload.builder_blocks
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
    system_critical_codes = ["WELCOME_CUSTOMER", "PACKAGE_EXPIRATION_REMINDER", "ACCOUNT_ACTIVATED",
                             "EMAIL_VERIFICATION_CODE", "LEAD_RECEIVED", "LEAD_REJECTED", "PASSWORD_RESET", "ADMIN_NEW_LEAD"]
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
        "portal_url": "http://localhost:5173",
        "renewal_url": "http://localhost:5173/#/pricing"
    }
    if payload.context:
        sample_ctx.update(payload.context)

    sample_ctx.setdefault("code", "123456")
    sample_ctx.setdefault("valid_minutes", 10)
    sample_ctx.setdefault("contact_name", "Ayşe Yılmaz")
    sample_ctx.setdefault("login_email", payload.to_email)
    sample_ctx.setdefault("password_instruction", "Kayıt sırasında belirlediğiniz şifre ile giriş yapabilirsiniz.")
    sample_ctx.setdefault("action_label", "Şifremi Belirle / Giriş Yap")
    sample_ctx.setdefault("action_url", "http://localhost:5173")
    sample_ctx.setdefault("reset_url", "http://localhost:5173")
    sample_ctx.setdefault("valid_hours", 72)
    sample_ctx.setdefault("reason", "Örnek ret gerekçesi")
    sample_ctx.setdefault("order_ref", "S00042")
    sample_ctx.setdefault("package_expiry_date", "10.10.2027")
    import asyncio
    snapshot = {"subject": tmpl.subject, "html_content": tmpl.html_content, "text_content": tmpl.text_content}
    sent = await asyncio.to_thread(NotificationService.render_and_send_template, payload.to_email, snapshot, sample_ctx)
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
    Zamanlamayı hemen çalıştırır (otomatik zamanlayıcıyla aynı kurallar):
    paket bitimine target_lead_days gün kalan ve son frequency_days günde hatırlatma
    almamış şirketlere şablonlu e-posta gönderir.
    """
    from app.services.scheduler_service import run_schedule

    sched = await db.get(NotificationSchedule, sched_id)
    if not sched:
        raise HTTPException(status_code=404, detail="Zamanlama görevi bulunamadı.")
    if sched.trigger_type != "BEFORE_EXPIRATION_INTERVAL":
        raise HTTPException(status_code=400, detail="Bu zamanlama türü elle çalıştırılamaz; şirket aktivasyonunda otomatik kullanılır.")
    processed_count = await run_schedule(db, sched)
    return {
        "success": True,
        "message": f"'{sched.name}' çalıştırıldı. {processed_count} kuruma hatırlatıcı iletildi.",
        "processed_count": processed_count
    }

