import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, Text, Boolean, Integer, Numeric, DateTime, ForeignKey, Index
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
    effort_coefficient = Column(Numeric, default=1.0)
    status = Column(String(32), default="ACTIVE")
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    provider = relationship("LLMProvider", back_populates="models")


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


class JobTitle(Base):
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
    recommended_model_code = Column(String(128), default="glm-5.3")
    autonomy_level = Column(String(8), default="L1")
    ai_review_status = Column(String(32), default="COMPANY_LOCAL")
    ai_review_feedback = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    tenant = relationship("Tenant", foreign_keys=[tenant_id])
    department = relationship("Department", foreign_keys=[department_id])


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
    status = Column(String(32), default="DRAFT")  # DRAFT, PROVISIONING, READY, ACTIVE, RELEASED
    repo_url = Column(String(255))
    created_by_actor_id = Column(UUID(as_uuid=True), ForeignKey("actors.id", ondelete="SET NULL"))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    tenant = relationship("Tenant", back_populates="projects")
    tasks = relationship("Task", back_populates="project", cascade="all, delete-orphan")


class Task(Base):
    __tablename__ = "tasks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    acceptance_criteria = Column(Text)
    priority = Column(String(16), default="MEDIUM")
    status = Column(String(32), default="BACKLOG")  # BACKLOG, READY, IN_PROGRESS, WAITING_APPROVAL, DONE
    assignee_actor_id = Column(UUID(as_uuid=True), ForeignKey("actors.id", ondelete="SET NULL"))
    estimated_effort = Column(Numeric, default=1.0)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    project = relationship("Project", back_populates="tasks")
    assignee = relationship("Actor")
    artifacts = relationship("Artifact", back_populates="task", cascade="all, delete-orphan")
    messages = relationship("ChatMessage", back_populates="task", cascade="all, delete-orphan")


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
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    agent_id = Column(UUID(as_uuid=True), ForeignKey("actors.id", ondelete="CASCADE"), nullable=False)
    file_name = Column(String(255), nullable=False)
    original_name = Column(String(255), nullable=False)
    file_type = Column(String(32), nullable=False)  # pdf, docx, xlsx, txt
    file_size = Column(Integer, nullable=False)
    storage_path = Column(String(512), nullable=True)
    extracted_text = Column(Text, nullable=True)
    summary = Column(Text, nullable=True)
    status = Column(String(32), default="INDEXED")  # INDEXED, ERROR, PROCESSING
    memory_item_id = Column(UUID(as_uuid=True), ForeignKey("memory_items.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    tenant = relationship("Tenant")
    agent = relationship("Actor")
    memory_item = relationship("MemoryItem")


class ChatMessage(Base):
    """
    Gemini Web Benzeri Kalıcı Sohbet Geçmişi ve Canlı Düşünce Akışı
    """
    __tablename__ = "chat_messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"))
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"))
    task_id = Column(UUID(as_uuid=True), ForeignKey("tasks.id", ondelete="CASCADE"))
    sender_actor_id = Column(UUID(as_uuid=True), ForeignKey("actors.id", ondelete="SET NULL"))
    role = Column(String(16), nullable=False)  # user, assistant, system, thought, tool
    content = Column(Text, nullable=False)
    thought_process = Column(Text)
    attachments = Column(JSONB, default=list)
    tokens = Column(Integer, default=0)
    is_private = Column(Boolean, default=False)
    message_type = Column(String(32), default="CHAT")  # CHAT, AGENT_TO_AGENT, HANDOFF
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    task = relationship("Task", back_populates="messages")
    sender = relationship("Actor")

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
