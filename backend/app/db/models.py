import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, Text, Boolean, Integer, Numeric, DateTime, Date, ForeignKey, Index
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.db.session import Base


class Sector(Base):
    """
    Türkiye Ticaret Bakanlığı Sektör Tanımlama Modülü (Madde 1).
    - Sektör Kodu (code: örn: A, B, C...)
    - Sektör Adı (name: örn: AĞAÇ İŞLERİ)
    """
    __tablename__ = "sectors"

    code = Column(String(32), primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    icon = Column(Text, nullable=True)
    image_url = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    professions = relationship("Profession", back_populates="sector", cascade="all, delete-orphan")


class Profession(Base):
    """
    Türkiye Ticaret Bakanlığı Meslek Tanımı Modülü (Madde 1).
    - Meslek Kodu (code: örn: A.01, A.02...)
    - Sektör Kodu (sector_code: örn: A)
    - Meslek Tanım Adı (name: örn: Kerestecilik)
    """
    __tablename__ = "professions"

    code = Column(String(32), primary_key=True)
    sector_code = Column(String(32), ForeignKey("sectors.code", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    sector = relationship("Sector", back_populates="professions")


class LLMProvider(Base):
    __tablename__ = "llm_providers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code = Column(String(64), unique=True, nullable=False)
    name = Column(String(128), nullable=False)
    base_url = Column(String(255), nullable=False)
    api_style = Column(String(32), default="openai")
    secret_ref = Column(String(255))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    models = relationship("LLMModel", back_populates="provider", cascade="all, delete-orphan")


class LLMModel(Base):
    __tablename__ = "llm_models"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    provider_id = Column(UUID(as_uuid=True), ForeignKey("llm_providers.id", ondelete="CASCADE"))
    model_code = Column(String(128), unique=True, nullable=False)
    display_name = Column(String(128), nullable=False)
    model_type = Column(String(32), nullable=False)
    capabilities = Column(JSONB, default=dict)
    context_window = Column(Integer, default=131072)
    effort_coefficient = Column(Numeric, default=1.0)  # RECOrion kredi katsayısı
    status = Column(String(32), default="ACTIVE")
    # EVREN /models senkronundan gelen bilgiler
    evren_task = Column(String(32))
    modalities = Column(JSONB)
    max_output_tokens = Column(Integer)
    prompt_token_price = Column(Numeric(18, 8))
    completion_token_price = Column(Numeric(18, 8))
    pricing_currency = Column(String(8))
    free_until = Column(Date)
    last_synced_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    provider = relationship("LLMProvider", back_populates="models")


class LLMModelPrice(Base):
    """Model başına 1M girdi/çıktı token TL fiyatı (KDV hariç); değiştirilmez, yeni fiyat yeni satırdır (ADIM 7.5.1)."""
    __tablename__ = "llm_model_prices"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    model_id = Column(UUID(as_uuid=True), ForeignKey("llm_models.id", ondelete="CASCADE"), nullable=False)
    price_in_per_1m_try = Column(Numeric(14, 4), nullable=False)
    price_out_per_1m_try = Column(Numeric(14, 4), nullable=False)
    valid_from = Column(DateTime(timezone=True), nullable=False)
    note = Column(Text)
    created_by_actor_id = Column(UUID(as_uuid=True), ForeignKey("actors.id", ondelete="SET NULL"))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)


class Plan(Base):
    __tablename__ = "plans"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code = Column(String(64), unique=True, nullable=False)  # STARTER, PRO, ENTERPRISE
    name = Column(String(128), nullable=False)
    description = Column(Text)
    monthly_price = Column(Numeric, default=0.0)
    currency = Column(String(8), default="TRY")
    max_humans = Column(Integer, default=5)
    max_agents = Column(Integer, default=5)
    max_projects = Column(Integer, default=3)
    monthly_credits = Column(Integer, default=1000)
    storage_gb = Column(Integer, default=10)
    allowed_models = Column(JSONB, default=list)
    features = Column(JSONB, default=dict)
    can_create_custom_titles = Column(Boolean, default=False)
    # Odoo ürün eşleşmesi (product.product id); satış siparişi bu ürün ve monthly_price ile açılır
    odoo_product_id = Column(Integer, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)


class CatalogDepartment(Base):
    """Platform departman kataloğu: genel (GENERAL) veya sektöre özel (SECTOR). Tüm müşterilere açık genel bilgi."""
    __tablename__ = "catalog_departments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code = Column(String(64), unique=True, nullable=False)
    name = Column(String(128), nullable=False)
    description = Column(Text)
    scope = Column(String(16), nullable=False, default="GENERAL")
    sector_code = Column(String(32), ForeignKey("sectors.code", ondelete="CASCADE"), nullable=True)
    profession_codes = Column(JSONB, nullable=False, default=list)
    sort_order = Column(Integer, nullable=False, default=0)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)


class JobTitle(Base):
    """
    Unvan. tenant_id boşsa platform kataloğu (Platform Unvan Bilgisi, tüm müşterilere açık);
    doluysa şirket unvanı (katalogdan alındıysa source_title_id).
    """
    __tablename__ = "job_titles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=True)
    department_id = Column(UUID(as_uuid=True), ForeignKey("departments.id", ondelete="SET NULL"), nullable=True)
    code = Column(String(64), nullable=False)
    title = Column(String(128), nullable=False)
    category = Column(String(64), nullable=False)
    description = Column(Text)
    base_role_prompt = Column(Text, nullable=False)
    required_skills = Column(JSONB, default=list)
    recommended_model_code = Column(String(128))
    autonomy_level = Column(String(8), default="L1")
    ai_review_status = Column(String(32), default="COMPANY_LOCAL")
    ai_review_feedback = Column(Text)
    is_active = Column(Boolean, default=True)
    catalog_department_id = Column(UUID(as_uuid=True), ForeignKey("catalog_departments.id", ondelete="SET NULL"))
    scope = Column(String(16))  # GENERAL, SECTOR (platform) veya COMPANY
    sector_code = Column(String(32))
    profession_codes = Column(JSONB, default=list)
    seniority = Column(String(16))  # JUNIOR, MID, SENIOR, LEAD, MANAGER
    responsibilities = Column(JSONB, default=list)
    kpis = Column(JSONB, default=list)
    source = Column(String(16))  # CATALOG, ADMIN, COMPANY
    source_title_id = Column(UUID(as_uuid=True), ForeignKey("job_titles.id", ondelete="SET NULL"))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    tenant = relationship("Tenant", foreign_keys=[tenant_id])
    department = relationship("Department", foreign_keys=[department_id])
    catalog_department = relationship("CatalogDepartment", foreign_keys=[catalog_department_id])


class SystemPermission(Base):
    __tablename__ = "system_permissions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code = Column(String(64), unique=True, nullable=False)
    module = Column(String(64), nullable=False)  # PLATFORM, RBAC, AGENTS, PROJECTS, CHAT, MEMORY, BILLING
    name = Column(String(128), nullable=False)
    description = Column(Text)
    default_for_roles = Column(JSONB, default=list)
    is_system = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)


class TenantRole(Base):
    __tablename__ = "tenant_roles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=True)
    name = Column(String(64), nullable=False)
    description = Column(Text)
    permissions = Column(JSONB, default=list)
    is_system = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)


class Department(Base):
    """
    Müşteri şirketinin kendi içindeki departmanları (Company Admin tarafından tanımlanır).
    """
    __tablename__ = "departments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(128), nullable=False)
    description = Column(Text)
    catalog_department_id = Column(UUID(as_uuid=True), ForeignKey("catalog_departments.id", ondelete="SET NULL"))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    tenant = relationship("Tenant", foreign_keys=[tenant_id])


class TenantLead(Base):
    __tablename__ = "tenant_leads"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    plan_id = Column(UUID(as_uuid=True), ForeignKey("plans.id", ondelete="SET NULL"), nullable=True)
    company_name = Column(String(255), nullable=False)
    tax_id = Column(String(32))
    tax_office = Column(String(128))
    address = Column(Text)
    phone = Column(String(32))
    website = Column(String(255))
    contact_email = Column(String(255), nullable=False)
    sectors = Column(JSONB, default=list)
    professions = Column(JSONB, default=list)
    nace_codes = Column(JSONB, default=list)
    generated_manifesto = Column(Text)
    assigned_skills = Column(JSONB, default=list)
    odoo_partner_id = Column(Integer)
    odoo_order_id = Column(Integer)
    odoo_order_name = Column(String(64))
    status = Column(String(32), default="PENDING")  # PENDING, CONTACTED, APPROVED, REJECTED
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Başvurunun bağlı olduğu şirket (onay bekleyen veya aktif)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="SET NULL"), nullable=True, index=True)
    contact_name = Column(String(255))
    password_hash = Column(String(255))  # Web kaydında belirlenen şifre (Argon2)
    rejection_reason = Column(Text)
    reviewed_by_actor_id = Column(UUID(as_uuid=True), nullable=True)
    reviewed_at = Column(DateTime(timezone=True))
    odoo_partner_name = Column(String(255))  # eşleşen/açılan Odoo müşterisinin adı
    odoo_sync_status = Column(String(32), default="PENDING")  # PENDING, SYNCED, FAILED, SKIPPED
    odoo_sync_error = Column(Text)
    email_verified_at = Column(DateTime(timezone=True))
    source = Column(String(16), default="WEB")  # WEB, ADMIN

    plan = relationship("Plan")


class Tenant(Base):
    __tablename__ = "tenants"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    slug = Column(String(64), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    tax_id = Column(String(64))
    tax_office = Column(String(128))
    phone = Column(String(32))
    address = Column(Text)
    website = Column(String(255))
    contact_email = Column(String(255))
    plan_id = Column(UUID(as_uuid=True), ForeignKey("plans.id", ondelete="SET NULL"), nullable=True)
    sectors = Column(JSONB, default=list)
    professions = Column(JSONB, default=list)
    nace_codes = Column(JSONB, default=list)
    sector_manifesto = Column(Text)
    package_start_date = Column(DateTime(timezone=True), default=datetime.utcnow)
    package_expiry_date = Column(DateTime(timezone=True))
    last_reminder_sent_at = Column(DateTime(timezone=True))
    brain_model_code = Column(String(128))  # şirketin Beyin AI (organizatör) modeli
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    plan = relationship("Plan")
    actors = relationship("Actor", back_populates="tenant", cascade="all, delete-orphan")
    projects = relationship("Project", back_populates="tenant", cascade="all, delete-orphan")
    memory_items = relationship("MemoryItem", back_populates="tenant", cascade="all, delete-orphan")


class Actor(Base):
    __tablename__ = "actors"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    actor_type = Column(String(16), nullable=False)  # HUMAN, AI_AGENT
    display_name = Column(String(128), nullable=False)
    email = Column(String(255))
    phone = Column(String(32))
    address = Column(Text)
    role = Column(String(64), nullable=False)  # SUPER_ADMIN, ARCHITECT, CODER, QA, ANALYST, etc.
    role_id = Column(UUID(as_uuid=True), ForeignKey("tenant_roles.id", ondelete="SET NULL"), nullable=True)
    job_title_id = Column(UUID(as_uuid=True), ForeignKey("job_titles.id", ondelete="SET NULL"), nullable=True)
    department_id = Column(UUID(as_uuid=True), ForeignKey("departments.id", ondelete="SET NULL"), nullable=True)
    password_hash = Column(String(255))
    capability_profile = Column(String(64))  # reasoning, code-strong, vision
    preferred_model_id = Column(UUID(as_uuid=True), ForeignKey("llm_models.id", ondelete="SET NULL"))
    system_prompt = Column(Text)
    description = Column(Text)
    autonomy_level = Column(String(8), default="L1")  # L1, L2, L3
    consecutive_rejects = Column(Integer, default=0)
    status = Column(String(32), default="IDLE")  # IDLE, WORKING, WAITING, QUARANTINED, DISABLED
    hired_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    dismissed_at = Column(DateTime(timezone=True), nullable=True)
    extra_permissions = Column(JSONB, default=list)
    telegram_chat_id = Column(String(64))  # proje bildirimleri (ADIM 6.5)
    telegram_link_code = Column(String(16))
    telegram_linked_at = Column(DateTime(timezone=True))
    notification_prefs = Column(JSONB, nullable=False, default=dict)
    # Günlük maliyet (TL, KDV hariç; ADIM 7.5.2): insan personelde ücret (kişisel veri), AI personelde isteğe bağlı sabit maliyet
    daily_cost_try = Column(Numeric(12, 2))  # {"email": bool, "telegram": bool} (ADIM 7.3)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    tenant = relationship("Tenant", back_populates="actors")
    preferred_model = relationship("LLMModel")
    job_title = relationship("JobTitle")
    tenant_role = relationship("TenantRole")
    department = relationship("Department")


class Project(Base):
    __tablename__ = "projects"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    slug = Column(String(64), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    field_package = Column(String(32), default="GENEL")  # YAZILIM, GENEL
    # DRAFT > PLANNING > READY > ACTIVE > (PAUSED) > COMPLETED | CANCELLED
    status = Column(String(32), default="DRAFT")
    repo_url = Column(String(255))
    created_by_actor_id = Column(UUID(as_uuid=True), ForeignKey("actors.id", ondelete="SET NULL"))
    kind = Column(String(16), nullable=False, default="PROJECT")  # PROJECT, CASE
    requirements = Column(Text)  # isterler
    manager_actor_id = Column(UUID(as_uuid=True), ForeignKey("actors.id", ondelete="SET NULL"))  # insan proje yöneticisi
    department_id = Column(UUID(as_uuid=True), ForeignKey("departments.id", ondelete="SET NULL"))
    start_date = Column(Date)
    end_date = Column(Date)
    plan = Column(JSONB)  # Beyin AI iş adımları taslağı
    simulation = Column(JSONB)  # süre, kredi, risk
    planning_approved_at = Column(DateTime(timezone=True))
    ready_at = Column(DateTime(timezone=True))
    started_at = Column(DateTime(timezone=True))
    closed_at = Column(DateTime(timezone=True))
    close_summary = Column(Text)
    start_notified_at = Column(DateTime(timezone=True))
    workflow_id = Column(String(128))  # Temporal proje akışı (ADIM 7)
    budget_try = Column(Numeric(16, 2))  # proje bütçesi (TL, KDV hariç; ADIM 7.5.3)
    budget_note = Column(Text)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    tenant = relationship("Tenant", back_populates="projects")
    tasks = relationship("Task", back_populates="project", cascade="all, delete-orphan")


class ProjectMember(Base):
    """Projedeki personel: MANAGER (insan proje yöneticisi), MEMBER (insan), AGENT (AI personel)."""
    __tablename__ = "project_members"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    actor_id = Column(UUID(as_uuid=True), ForeignKey("actors.id", ondelete="CASCADE"), nullable=False)
    role = Column(String(16), nullable=False)
    added_by_actor_id = Column(UUID(as_uuid=True))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    actor = relationship("Actor")


class Task(Base):
    __tablename__ = "tasks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    acceptance_criteria = Column(Text)
    priority = Column(String(16), default="MEDIUM")
    # BACKLOG, READY, IN_PROGRESS, WAITING_APPROVAL, REVISION, QUARANTINED, DONE, CANCELLED
    status = Column(String(32), default="BACKLOG")
    assignee_actor_id = Column(UUID(as_uuid=True), ForeignKey("actors.id", ondelete="SET NULL"))
    estimated_effort = Column(Numeric, default=1.0)  # iş günü
    order_index = Column(Integer, nullable=False, default=0)
    department_id = Column(UUID(as_uuid=True), ForeignKey("departments.id", ondelete="SET NULL"))
    job_title_id = Column(UUID(as_uuid=True), ForeignKey("job_titles.id", ondelete="SET NULL"))  # gereken unvan
    depends_on = Column(JSONB, default=list)  # önce bitmesi gereken görevlerin kimlikleri
    start_date = Column(Date)
    due_date = Column(Date)
    estimated_credits = Column(Numeric(14, 2))
    # İş akışı (ADIM 7): kontrol personeli, onaylayıcı (boş: proje yöneticisi), ret sınırı
    reviewer_actor_id = Column(UUID(as_uuid=True), ForeignKey("actors.id", ondelete="SET NULL"))
    approver_actor_id = Column(UUID(as_uuid=True), ForeignKey("actors.id", ondelete="SET NULL"))
    requires_approval = Column(Boolean, nullable=False, default=True)
    max_rejections = Column(Integer, nullable=False, default=3)
    rejection_count = Column(Integer, nullable=False, default=0)
    started_at = Column(DateTime(timezone=True))
    submitted_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    # Tamamlanınca kayda geçen personel maliyeti (ADIM 7.5.2)
    labor_rate_try = Column(Numeric(12, 2))
    labor_days = Column(Numeric(6, 1))
    labor_cost_try = Column(Numeric(14, 2))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    project = relationship("Project", back_populates="tasks")
    assignee = relationship("Actor", foreign_keys=[assignee_actor_id])
    artifacts = relationship("Artifact", back_populates="task", cascade="all, delete-orphan")
    # Mesajlar silinemez (ADIM 8.1): ORM silmez, veritabanı tetikleyicisi karar verir
    messages = relationship("ChatMessage", back_populates="task", passive_deletes="all")


class ProjectCostItem(Base):
    """Diğer maliyet kalemi (ADIM 7.5.3): materyal, danışmanlık, eğitim, lisans, seyahat, donanım, diğer. TL, KDV hariç."""
    __tablename__ = "project_cost_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    task_id = Column(UUID(as_uuid=True), ForeignKey("tasks.id", ondelete="SET NULL"))
    category = Column(String(24), nullable=False)
    description = Column(String(500), nullable=False)
    quantity = Column(Numeric(14, 3), nullable=False)
    unit = Column(String(24))
    unit_price_try = Column(Numeric(14, 2), nullable=False)
    amount_try = Column(Numeric(16, 2), nullable=False)
    incurred_on = Column(Date, nullable=False)
    attachment_path = Column(String(512))  # belge (fatura vb.); öğrenme hattına girmez
    attachment_name = Column(String(255))
    created_by_actor_id = Column(UUID(as_uuid=True), ForeignKey("actors.id", ondelete="SET NULL"))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)


class ApprovalToken(Base):
    """E-posta/Telegram onay bağlantısı (tek kullanımlık, süreli; yalnızca özeti saklanır)."""
    __tablename__ = "approval_tokens"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    token_hash = Column(String(64), nullable=False, unique=True)
    task_id = Column(UUID(as_uuid=True), ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False)
    actor_id = Column(UUID(as_uuid=True), ForeignKey("actors.id", ondelete="CASCADE"), nullable=False)
    channel = Column(String(16), nullable=False)  # EMAIL, TELEGRAM
    submitted_at = Column(DateTime(timezone=True))  # hangi teslime ait
    expires_at = Column(DateTime(timezone=True), nullable=False)
    used_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)


class TaskEvent(Base):
    """İş akışı olay geçmişi (yalnızca ekleme)."""
    __tablename__ = "task_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    task_id = Column(UUID(as_uuid=True), ForeignKey("tasks.id", ondelete="CASCADE"))
    # PROJECT_STARTED, TASK_STARTED, SUBMITTED, APPROVED, REJECTED, QUARANTINED, RELEASED, DONE, CANCELLED, PROJECT_FINISHED ...
    kind = Column(String(32), nullable=False)
    actor_id = Column(UUID(as_uuid=True), ForeignKey("actors.id", ondelete="SET NULL"))
    note = Column(Text)
    data = Column(JSONB, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)


class Artifact(Base):
    __tablename__ = "artifacts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_id = Column(UUID(as_uuid=True), ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    artifact_type = Column(String(32), nullable=False)  # CODE, DOCUMENT, ANALYSIS, ADR
    storage_path = Column(String(512))
    version = Column(Integer, default=1)
    content_hash = Column(String(128))
    produced_by_actor_id = Column(UUID(as_uuid=True), ForeignKey("actors.id", ondelete="SET NULL"))
    approval_status = Column(String(32), default="DRAFT")  # DRAFT, SUBMITTED, APPROVED, REJECTED
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    task = relationship("Task", back_populates="artifacts")
    producer = relationship("Actor")


class MemoryItem(Base):
    """
    2 Kademeli Kolektif Hafıza Modeli:
    - scope = 'GLOBAL': Şirket Kurum Hafızası (Tüm AI ajanlarının hafıza toplamı)
    - scope = 'AGENT': AI Personel Hafızası (Ajanın kendi uzmanlık dokümanları ve tecrübeleri)
    """
    __tablename__ = "memory_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    scope = Column(String(16), nullable=False)  # GLOBAL, AGENT
    agent_id = Column(UUID(as_uuid=True), ForeignKey("actors.id", ondelete="CASCADE"), nullable=True)
    source_reference = Column(String(255))
    content = Column(Text, nullable=False)
    metadata_json = Column(JSONB, default=dict)
    qdrant_point_id = Column(UUID(as_uuid=True))
    status = Column(String(32), default="APPROVED")  # CANDIDATE, APPROVED, REVOKED
    confidence_score = Column(Numeric, default=1.0)
    embedding_model_version = Column(String(64), default="qwen3-embedding-8b")
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    tenant = relationship("Tenant", back_populates="memory_items")
    agent = relationship("Actor")


class AgentDocument(Base):
    """
    AI Ajanları Uzmanlık / Kaynak Dokümanları (PDF, Word, Excel, vb.)
    Ajanın kolektif ve bireysel hafızasını (RAG) besler.
    """
    __tablename__ = "agent_documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=True)  # boş: platform
    agent_id = Column(UUID(as_uuid=True), ForeignKey("actors.id", ondelete="CASCADE"), nullable=True)
    file_name = Column(String(255), nullable=False)
    original_name = Column(String(255), nullable=False)
    file_type = Column(String(32), nullable=False)  # pdf, docx, xlsx, txt
    file_size = Column(Integer, nullable=False)
    storage_path = Column(String(512), nullable=True)
    extracted_text = Column(Text, nullable=True)
    summary = Column(Text, nullable=True)
    status = Column(String(32), default="INDEXED")  # INDEXED, ERROR, PROCESSING
    memory_item_id = Column(UUID(as_uuid=True), ForeignKey("memory_items.id", ondelete="SET NULL"), nullable=True)
    # Doküman hattı (ADIM 5.4): katman, depolama, sürüm, KVKK maskeleme, öğrenme kartı ve onay
    layer = Column(String(24), nullable=False, default="AGENT")  # AGENT, COMPANY_TITLE, PLATFORM_TITLE
    job_title_id = Column(UUID(as_uuid=True), ForeignKey("job_titles.id", ondelete="CASCADE"))
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"))  # PROJECT katmanı
    promoted_at = Column(DateTime(timezone=True))  # proje kapanınca Kurum Hafızasına aktarıldı
    storage_key = Column(String(512))
    sha256 = Column(String(64))
    version = Column(Integer, nullable=False, default=1)
    previous_document_id = Column(UUID(as_uuid=True), ForeignKey("agent_documents.id", ondelete="SET NULL"))
    masked_text = Column(Text)
    pii_findings = Column(JSONB)
    guard_result = Column(JSONB)
    page_count = Column(Integer)
    ocr_pages = Column(Integer)
    image_count = Column(Integer)
    chunk_count = Column(Integer)
    learning_card = Column(JSONB)
    test_result = Column(JSONB)
    error = Column(Text)
    uploaded_by_actor_id = Column(UUID(as_uuid=True))
    approved_by_actor_id = Column(UUID(as_uuid=True))
    approved_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    tenant = relationship("Tenant")
    agent = relationship("Actor")
    memory_item = relationship("MemoryItem")


class DocumentChunk(Base):
    """Onaylanan dokümanın vektörlenen parçaları (KVKK maskeli metin)."""
    __tablename__ = "document_chunks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("agent_documents.id", ondelete="CASCADE"), nullable=False)
    idx = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    qdrant_point_id = Column(UUID(as_uuid=True))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)


class ChatMessage(Base):
    """
    Gemini Web Benzeri Kalıcı Sohbet Geçmişi ve Canlı Düşünce Akışı
    """
    __tablename__ = "chat_messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"))
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"))
    task_id = Column(UUID(as_uuid=True), ForeignKey("tasks.id", ondelete="CASCADE"))
    # Silinemez kayıt (ADIM 8.1): personel silinse de mesaj kalır; yabancı anahtar yok, ad yazıldığı anda saklanır
    sender_actor_id = Column(UUID(as_uuid=True))
    sender_name = Column(String(255))
    role = Column(String(16), nullable=False)  # user, assistant, system, thought, tool
    content = Column(Text, nullable=False)
    thought_process = Column(Text)
    attachments = Column(JSONB, default=list)
    tokens = Column(Integer, default=0)
    is_private = Column(Boolean, default=False)
    visible_to_actor_id = Column(UUID(as_uuid=True))  # özel mesaj yalnızca bu kişiye görünür (soran kişi)
    message_type = Column(String(32), default="CHAT")  # CHAT, AGENT_TO_AGENT, HANDOFF
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    task = relationship("Task", back_populates="messages")
    sender = relationship("Actor", primaryjoin="foreign(ChatMessage.sender_actor_id) == Actor.id", viewonly=True)

    __table_args__ = (
        Index("idx_orm_chat_messages_task_id", "task_id", "created_at"),
        Index("idx_orm_chat_messages_project_id", "project_id", "created_at"),
    )


class SystemSetting(Base):
    """
    Sistem genelinde global yapılandırmalar (varsayılan AI modelleri vb.)
    """
    __tablename__ = "system_settings"

    key = Column(String(64), primary_key=True)
    value = Column(JSONB, nullable=False)
    description = Column(Text, nullable=True)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)


class EmailTemplate(Base):
    """
    HTML & Metin E-Posta Şablonları (Madde 1)
    """
    __tablename__ = "email_templates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code = Column(String(64), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    subject = Column(String(255), nullable=False)
    html_content = Column(Text, nullable=False)
    text_content = Column(Text)
    variables = Column(JSONB, default=list)
    builder_blocks = Column(JSONB, nullable=True)  # sürükle-bırak editör blokları
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)


class NotificationSchedule(Base):
    """
    E-Posta Gönderim Zamanlama ve Otomasyon Görevleri (Madde 2 & 14)
    """
    __tablename__ = "notification_schedules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    trigger_type = Column(String(64), nullable=False)  # ON_REGISTRATION, BEFORE_EXPIRATION_INTERVAL, MANUAL, CRON_SCHEDULED
    template_code = Column(String(64), nullable=False)
    frequency_days = Column(Integer, default=15)
    target_lead_days = Column(Integer, default=90)
    is_active = Column(Boolean, default=True)
    last_run_at = Column(DateTime(timezone=True))
    next_run_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)


class AuditEvent(Base):
    """
    Değiştirilemez denetim kaydı. Yalnızca ekleme yapılır; UPDATE/DELETE
    veritabanı tetikleyicisiyle engellenir. Şirket/kullanıcı silinse de kayıt kalır.
    """
    __tablename__ = "audit_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    actor_id = Column(UUID(as_uuid=True), nullable=True)
    action = Column(String(128), nullable=False)
    target_type = Column(String(64))
    target_id = Column(String(64))
    payload = Column(JSONB, default=dict)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)


class LLMCall(Base):
    """Her LLM çağrısının ölçümü (token, kredi, süre). Şirket/kullanıcı silinse de kayıt kalır."""
    __tablename__ = "llm_calls"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True))
    task_id = Column(UUID(as_uuid=True))
    actor_id = Column(UUID(as_uuid=True))
    model_id = Column(UUID(as_uuid=True))
    project_id = Column(UUID(as_uuid=True))
    purpose = Column(String(32))
    model_code = Column(String(128))
    tokens_in = Column(Integer, default=0)
    tokens_out = Column(Integer, default=0)
    credits_cost = Column(Numeric, default=0)
    latency_ms = Column(Integer, default=0)
    status = Column(String(32), default="SUCCESS")
    error = Column(Text)
    evren_credits = Column(Numeric(18, 6))
    evren_balance_after = Column(Numeric(18, 4))
    cost_try = Column(Numeric(14, 6))  # çağrı anında geçerli LLM fiyatıyla TL maliyet (ADIM 7.5.1)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)


class CreditLedgerEntry(Base):
    """Değiştirilemez kredi defteri. Bakiye = amount toplamı (kullanım negatif)."""
    __tablename__ = "credit_ledger"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    entry_type = Column(String(24), nullable=False)  # MONTHLY_GRANT, TOPUP, USAGE, EXPIRE, ADJUSTMENT
    amount = Column(Numeric(16, 4), nullable=False)
    period = Column(String(7), nullable=False)
    llm_call_id = Column(UUID(as_uuid=True))
    note = Column(Text)
    created_by_actor_id = Column(UUID(as_uuid=True))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
