"""Referans verisi: LLM modelleri, paketler, sektör/meslek, izinler, mail şablonları

Her tablo yalnızca boşsa doldurulur; mevcut kurulumdaki veriye dokunulmaz.
Kaynaklar: trade_ministry_catalog.json (Ticaret Bakanlığı), eski init-db seed'leri
ve 19.10.2026 itibarıyla canlı sistemdeki model/paket tanımları.

Revision ID: 0002
Revises: 0001
Create Date: 2026-10-19
"""
import json

from alembic import op
import sqlalchemy as sa

from migrations.helpers import DATA_DIR, run_sql_file, table_is_empty

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None

EVREN_PROVIDER = {
    "code": "EVREN",
    "name": "TÜBİTAK BİLGEM EVREN (Türkiye Ulusal LLM Merkezi)",
    "base_url": "https://evren-llmapi.ssyz.org.tr/v1",
    "api_style": "openai",
}

# (model_code, display_name, model_type, capabilities, context_window, effort_coefficient)
LLM_MODELS = [
    ("qwen3-asr-1.7b", "Qwen3 ASR 1.7B", "AUDIO", {"transcription": True, "speech_to_text": True}, 32768, 0.5),
    ("auto", "EVREN Auto (Akilli Model Secici)", "CHAT", {"auto_routing": True}, 32768, 1.0),
    ("deepseek-v4.1-flash", "DeepSeek V4.1 Flash (Kıdemli Kod)", "CHAT", {"unit_tests": True, "refactoring": True, "senior_coding": True}, 1048576, 1.2),
    ("deepseek-v4-flash", "DeepSeek V4 Flash (Hızlı Kod & QA)", "CHAT", {"qa_review": True, "rapid_code": True}, 1048576, 0.8),
    ("gemma-4-31b", "Gemma 4 31B (Dokümantasyon & PR)", "CHAT", {"pr_marketing": True, "documentation": True}, 262144, 1.0),
    ("glm-5.3", "GLM 5.3 (Sistem Mimarı)", "CHAT", {"architecture": True, "tool_calling": True, "orchestration": True}, 524288, 2.0),
    ("mimo-v2.6-pro", "MIMO V2.6 Pro (İş Analisti & Muhakeme)", "CHAT", {"backlog_generator": True, "complex_reasoning": True}, 1048576, 1.8),
    ("qwen3.8-flash-next", "Qwen3.8 Flash Next (Operasyonel)", "CHAT", {"summarization": True, "fast_inference": True}, 262144, 0.7),
    ("laya", "Laya (Karar Destek)", "DECISION", {"decision": True}, 8192, 1.0),
    ("qwen3-embedding-8b", "Qwen3 Embedding 8B", "EMBEDDING", {"dense_vector": 4096, "two_tier_memory": True}, 40960, 0.3),
    ("qwen3-guard-4b", "Qwen3 Guard 4B", "GUARD", {"jailbreak_defense": True, "prompt_injection_defense": True}, 16384, 0.3),
    ("deepseek-ocr-2", "DeepSeek OCR 2", "OCR", {"pdf_extract": True, "document_ocr": True}, 8192, 0.6),
    ("dots-ocr", "Dots OCR", "OCR", {"forms": True, "tables": True, "complex_docs": True}, 131072, 0.8),
    ("qwen3-reranker-8b", "Qwen3 Reranker 8B", "RERANKER", {"cross_encoder": True, "context_ranking": True}, 4096, 0.4),
    ("qwen3-vl-30b", "Qwen3 VL 30B", "VISION", {"diagram": True, "ui_screenshot": True, "figma_analysis": True}, 262144, 1.5),
]

PLANS = [
    {
        "code": "STARTER", "name": "Başlangıç (KOBİ) Paketi",
        "description": "Küçük ekipler ve dijital dönüşüme yeni başlayan işletmeler için ideal otonom yapay zeka paketi.",
        "monthly_price": 14900, "max_humans": 5, "max_agents": 5, "max_projects": 3, "monthly_credits": 5000, "storage_gb": 20,
        "allowed_models": ["deepseek-v4-flash", "gemma-4-31b", "qwen3.8-flash-next", "qwen3-asr-1.7b", "qwen3-embedding-8b"],
        "features": {"sla": "48h", "support": "email", "multi_modal": "basic", "debate_arena": False, "domain_packs": ["GENEL", "OFIS"], "nace_manifesto": True},
        "can_create_custom_titles": False,
    },
    {
        "code": "PRO", "name": "Profesyonel (Büyüyen Şirket) Paketi",
        "description": "Orta ölçekli şirketler, yazılım evleri ve departman bazlı otonom iş akışları için güçlü paket.",
        "monthly_price": 39900, "max_humans": 25, "max_agents": 20, "max_projects": 20, "monthly_credits": 25000, "storage_gb": 100,
        "allowed_models": ["deepseek-v4-flash", "gemma-4-31b", "qwen3.8-flash-next", "qwen3-asr-1.7b", "glm-5.3", "deepseek-v4.1-flash",
                           "mimo-v2.6-pro", "qwen3-vl-30b", "whisper-large-v3", "qwen3-reranker-8b", "qwen3-embedding-8b"],
        "features": {"sla": "12h", "support": "priority", "multi_modal": "full_vision_ocr", "debate_arena": True, "domain_packs": ["YAZILIM", "GENEL", "FINANS", "HUKUK"], "nace_manifesto": True},
        "can_create_custom_titles": False,
    },
    {
        "code": "ENTERPRISE", "name": "Kurumsal (Enterprise) Paketi",
        "description": "Büyük kurumlar, holdingler ve regülasyona tabi yapılar için tüm 13 model ve sınırsız otonom orkestrasyon.",
        "monthly_price": 99000, "max_humans": 100, "max_agents": 100, "max_projects": 100, "monthly_credits": 100000, "storage_gb": 1000,
        "allowed_models": ["qwen3-asr-1.7b", "deepseek-ocr-2", "dots-ocr", "qwen3-guard-4b", "qwen3-reranker-8b", "qwen3-embedding-8b", "qwen3-vl-30b",
                           "glm-5.3", "qwen3.8-flash-next", "deepseek-v4.1-flash", "mimo-v2.6-pro", "gemma-4-31b", "deepseek-v4-flash"],
        "features": {"sla": "1h", "support": "dedicated_account_manager", "multi_modal": "full_suite_dedicated", "debate_arena": True,
                     "domain_packs": ["TUM_SEKTORLER"], "nace_manifesto": True, "on_prem_option": True},
        "can_create_custom_titles": True,
    },
]

ALL = ["SUPER_ADMIN", "COMPANY_ADMIN", "PROJECT_MANAGER", "STANDARD_USER"]
ADMINS = ["SUPER_ADMIN", "COMPANY_ADMIN"]
MANAGERS = ["SUPER_ADMIN", "COMPANY_ADMIN", "PROJECT_MANAGER"]

# (code, module, name, description, default_for_roles)
PERMISSIONS = [
    ("system:admin", "PLATFORM", "Tam Sistem Yönetimi", "Tüm sistem ve altyapı ayarlarını yönetme süper admin yetkisi", ["SUPER_ADMIN"]),
    ("tenant:manage", "PLATFORM", "Şirket ve Paket Yönetimi", "Şirket profilini, abonelik paketini ve ayarlarını yönetme", ADMINS),
    ("tenant:view", "PLATFORM", "Şirket Bilgilerini Görüntüleme", "Şirket ve kurum detaylarını görüntüleme", ALL),
    ("role:create", "RBAC", "Yeni Rol Tanımlama", "Şirket içi özel roller oluşturma ve izin atama", ADMINS),
    ("role:edit", "RBAC", "Rol Düzenleme", "Mevcut rollerin yetki ve tanımlarını değiştirme", ADMINS),
    ("role:delete", "RBAC", "Rol Silme", "Şirket içi özel rolleri silme", ADMINS),
    ("user:invite", "RBAC", "Kullanıcı Davet Etme", "Platforma yeni insan kullanıcı davet etme ve şifre belirleme", ADMINS),
    ("user:manage", "RBAC", "Kullanıcı Hesaplarını Yönetme", "Kullanıcıları askıya alma, rolünü değiştirme ve düzenleme", ADMINS),
    ("agent:hire", "AGENTS", "AI Personel İşe Alma", "Yeni AI ajan personeli tanımlama ve projeye dahil etme", MANAGERS),
    ("agent:configure", "AGENTS", "AI Personel Konfigürasyonu", "AI modelini, sistem promptunu ve otonomi seviyesini değiştirme", ADMINS),
    ("agent:custom_title", "AGENTS", "Özel AI Ünvanı Tanımlama", "Kurumsal pakete özel şirket ünvanı ve prompt şablonu üretme", ADMINS),
    ("agent:quarantine", "AGENTS", "AI Personelini Karantinaya Alma", "Hatalı veya sınır dışına çıkan ajanı durdurma ve dondurma", MANAGERS),
    ("project:create", "PROJECTS", "Yeni Proje Başlatma", "Yeni proje açma, repo ve şablon seçimi yapma", MANAGERS),
    ("project:manage", "PROJECTS", "Proje Ayarlarını Yönetme", "Proje parametrelerini ve takım atamalarını değiştirme", MANAGERS),
    ("task:create", "PROJECTS", "Görev Oluşturma ve Atama", "İş akışı görevi oluşturup AI veya insan personele atama", ALL),
    ("task:approve", "PROJECTS", "Kalite Kapısı Onaylama (Gate Approve)", "AI çıktısını onaylayıp sonraki personele devretme", MANAGERS),
    ("task:reject", "PROJECTS", "Revizyon İsteme (Gate Reject)", "AI personelinden geribildirime göre revizyon talep etme", MANAGERS),
    ("chat:participate", "CHAT", "AI ile Sohbet ve Görev İletişimi", "AI personelleri ile görev bazlı etkileşime girme", ALL),
    ("chat:view_a2a", "CHAT", "Ajanlar Arası Müzakereleri İzleme", "Ajanların kendi aralarındaki teknik tartışmaları görme", MANAGERS),
    ("chat:export", "CHAT", "Sohbet ve Düşünce Akışını Dışa Aktarma", "Görüşme ve otonom akış loglarını dışarı aktarma", ADMINS),
    ("memory:search", "MEMORY", "Kurum Hafızasında Arama", "Şirket ve ajan hafıza uzayında semantik arama yapma", ALL),
    ("memory:promote", "MEMORY", "Hafızayı Kurumsal Hafızaya Terfi Ettirme", "Ajan tecrübesini Şirket Kurum Hafızasına (NS_GLOBAL) aktarma", MANAGERS),
    ("memory:revoke", "MEMORY", "Kurum Hafızasından Çıkarma / Silme", "Geçersizleşen veya hatalı kurumsal bilgiyi hafızadan kaldırma", ADMINS),
    ("billing:view", "BILLING", "Fatura ve Kredi Durumunu Görme", "Kalan işlem kredisini ve fatura geçmişini inceleme", ADMINS),
    ("billing:topup", "BILLING", "Kredi Yükleme ve Paket Değiştirme", "Ek model kredisi satın alma ve paket yükseltme", ADMINS),
]

SCHEDULES = [
    ("Müşteri Kayıt Olduğunda Otomatik Hoşgeldiniz E-postası", "ON_REGISTRATION", "WELCOME_CUSTOMER", 0, 0),
    ("Paket Bitişine 3 Ay Kala 15 Günde 1 Hatırlatıcı E-postası", "BEFORE_EXPIRATION_INTERVAL", "PACKAGE_EXPIRATION_REMINDER", 15, 90),
]

HQ_TENANT = {
    "slug": "recdx_hq",
    "name": "RECDx Teknoloji & Dijital Dönüşüm Danışmanlığı LTD. Şirketi",
    "contact_email": "info@recdx.com",
    "website": "https://recdx.com",
    "sector_manifesto": "RECDx Çekirdek Kurumsal Yönetim ve Altyapı Manifestosu",
}


def _exec(sql: str, params: dict) -> None:
    op.get_bind().execute(sa.text(sql), params)


def upgrade() -> None:
    if table_is_empty("llm_providers"):
        _exec("INSERT INTO llm_providers (code, name, base_url, api_style, is_active) VALUES (:code, :name, :base_url, :api_style, TRUE)", EVREN_PROVIDER)

    if table_is_empty("llm_models"):
        provider_id = op.get_bind().execute(sa.text("SELECT id FROM llm_providers WHERE code = 'EVREN'")).scalar()
        for code, name, mtype, caps, ctx, coef in LLM_MODELS:
            _exec(
                "INSERT INTO llm_models (provider_id, model_code, display_name, model_type, capabilities, context_window, effort_coefficient, status) "
                "VALUES (:pid, :code, :name, :mtype, CAST(:caps AS jsonb), :ctx, :coef, 'ACTIVE')",
                {"pid": provider_id, "code": code, "name": name, "mtype": mtype, "caps": json.dumps(caps), "ctx": ctx, "coef": coef},
            )

    if table_is_empty("plans"):
        for p in PLANS:
            _exec(
                "INSERT INTO plans (code, name, description, monthly_price, currency, max_humans, max_agents, max_projects, monthly_credits, "
                "storage_gb, allowed_models, features, can_create_custom_titles, is_active) "
                "VALUES (:code, :name, :description, :monthly_price, 'TRY', :max_humans, :max_agents, :max_projects, :monthly_credits, "
                ":storage_gb, CAST(:allowed_models AS jsonb), CAST(:features AS jsonb), :can_create_custom_titles, TRUE)",
                {**p, "allowed_models": json.dumps(p["allowed_models"]), "features": json.dumps(p["features"])},
            )

    if table_is_empty("sectors"):
        catalog = json.loads((DATA_DIR / "trade_ministry_catalog.json").read_text(encoding="utf-8"))
        for s in catalog["sectors"]:
            _exec("INSERT INTO sectors (code, name, icon, is_active, created_at, updated_at) VALUES (:code, :name, :icon, TRUE, NOW(), NOW())",
                  {"code": s["code"], "name": s["name"], "icon": s.get("icon", "📁")})
        for p in catalog["professions"]:
            _exec("INSERT INTO professions (code, sector_code, name, is_active, created_at, updated_at) VALUES (:code, :sector_code, :name, TRUE, NOW(), NOW())",
                  {"code": p["code"], "sector_code": p["sector_code"], "name": p["name"]})

    if table_is_empty("system_permissions"):
        for code, module, name, desc, roles in PERMISSIONS:
            _exec("INSERT INTO system_permissions (code, module, name, description, default_for_roles, is_system) "
                  "VALUES (:code, :module, :name, :desc, CAST(:roles AS jsonb), TRUE)",
                  {"code": code, "module": module, "name": name, "desc": desc, "roles": json.dumps(roles)})

    if table_is_empty("system_settings"):
        _exec("INSERT INTO system_settings (key, value, description) VALUES ('default_manifesto_model', CAST(:v AS jsonb), :d)",
              {"v": json.dumps("mimo-v2.6-pro"), "d": "Şirket manifestosu ve ajan rollerini oluşturan varsayılan EVREN LLM modeli"})

    if table_is_empty("email_templates"):
        run_sql_file("0002_email_templates.sql")

    if table_is_empty("notification_schedules"):
        for name, trigger, tmpl, freq, lead in SCHEDULES:
            _exec("INSERT INTO notification_schedules (name, trigger_type, template_code, frequency_days, target_lead_days, is_active) "
                  "VALUES (:name, :trigger, :tmpl, :freq, :lead, TRUE)",
                  {"name": name, "trigger": trigger, "tmpl": tmpl, "freq": freq, "lead": lead})

    if table_is_empty("tenants"):
        _exec("INSERT INTO tenants (slug, name, contact_email, website, sector_manifesto, is_active) "
              "VALUES (:slug, :name, :contact_email, :website, :sector_manifesto, TRUE)", HQ_TENANT)


def downgrade() -> None:
    pass
