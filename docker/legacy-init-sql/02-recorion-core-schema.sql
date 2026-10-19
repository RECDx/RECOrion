-- ==============================================================================
-- RECOrion: Çekirdek Veritabanı Şeması ve Başlangıç Tohum Verileri (Sürüm 3.0)
-- PostgreSQL 16 + pgvector (Dark DB İzolasyonu)
-- ==============================================================================

-- ------------------------------------------------------------------------------
-- 1. NACE FAALİYET KODLARI KATALOĞU
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS nace_catalog (
    code VARCHAR(16) PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    sector_group VARCHAR(64) NOT NULL,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ------------------------------------------------------------------------------
-- 2. LLM SAĞLAYICILARI VE 13 EVREN MODELİ
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS llm_providers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(64) UNIQUE NOT NULL,
    name VARCHAR(128) NOT NULL,
    base_url VARCHAR(255) NOT NULL,
    api_style VARCHAR(32) DEFAULT 'openai',
    secret_ref VARCHAR(255),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS llm_models (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    provider_id UUID REFERENCES llm_providers(id) ON DELETE CASCADE,
    model_code VARCHAR(128) UNIQUE NOT NULL,
    display_name VARCHAR(128) NOT NULL,
    model_type VARCHAR(32) NOT NULL, -- AUDIO, OCR, GUARD, RERANKER, EMBEDDING, VISION, CHAT
    capabilities JSONB DEFAULT '{}'::jsonb,
    context_window INT DEFAULT 131072,
    effort_coefficient NUMERIC DEFAULT 1.0,
    status VARCHAR(32) DEFAULT 'ACTIVE',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ------------------------------------------------------------------------------
-- 3. ÇOK KİRACILI (MULTI-TENANT) ŞİRKETLER
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS tenants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    slug VARCHAR(64) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    tax_id VARCHAR(64),
    nace_codes JSONB DEFAULT '[]'::jsonb,
    sector_manifesto TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ------------------------------------------------------------------------------
-- 4. AKTÖRLER (İNSAN VE AI PERSONELLERİ - ROL EŞİTLİĞİ PRENSİBİ)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS actors (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    actor_type VARCHAR(16) NOT NULL CHECK (actor_type IN ('HUMAN', 'AI_AGENT')),
    display_name VARCHAR(128) NOT NULL,
    email VARCHAR(255),
    role VARCHAR(64) NOT NULL, -- SUPER_ADMIN, PROJECT_MANAGER, ARCHITECT, ANALYST, CODER, QA, PR
    password_hash VARCHAR(255),
    capability_profile VARCHAR(64), -- reasoning, code-strong, vision, operational
    preferred_model_id UUID REFERENCES llm_models(id) ON DELETE SET NULL,
    system_prompt TEXT,
    autonomy_level VARCHAR(8) DEFAULT 'L1' CHECK (autonomy_level IN ('L1', 'L2', 'L3')),
    consecutive_rejects INT DEFAULT 0,
    status VARCHAR(32) DEFAULT 'IDLE' CHECK (status IN ('IDLE', 'WORKING', 'WAITING', 'QUARANTINED', 'DISABLED')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ------------------------------------------------------------------------------
-- 5. ONAY GRUPLARI VE ÜYELİKLER (MAKER-CHECKER MEKANİZMASI)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS approval_groups (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    code VARCHAR(64) NOT NULL,
    name VARCHAR(128) NOT NULL,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE (tenant_id, code)
);

CREATE TABLE IF NOT EXISTS approval_group_members (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    group_id UUID REFERENCES approval_groups(id) ON DELETE CASCADE,
    actor_id UUID REFERENCES actors(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE (group_id, actor_id)
);

-- ------------------------------------------------------------------------------
-- 6. PROJELER VE İŞ AKIŞLARI (DAG)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    slug VARCHAR(64) NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    field_package VARCHAR(32) DEFAULT 'GENEL', -- YAZILIM, GENEL, HUKUK, E-TICARET
    status VARCHAR(32) DEFAULT 'DRAFT' CHECK (status IN ('DRAFT', 'PROVISIONING', 'READY', 'ACTIVE', 'RELEASE_PENDING', 'RELEASED', 'PROVISION_FAILED', 'PAUSED', 'CANCELLED')),
    repo_url VARCHAR(255),
    created_by_actor_id UUID REFERENCES actors(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE (tenant_id, slug)
);

-- ------------------------------------------------------------------------------
-- 7. BACKLOG, EPİC'LER VE GÖREVLER (DAG DÜĞÜMLERİ)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    acceptance_criteria TEXT,
    priority VARCHAR(16) DEFAULT 'MEDIUM' CHECK (priority IN ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')),
    status VARCHAR(32) DEFAULT 'BACKLOG' CHECK (status IN ('BACKLOG', 'READY', 'IN_PROGRESS', 'WAITING_APPROVAL', 'IN_DEBATE', 'REVISION', 'DONE', 'BLOCKED', 'QUARANTINED', 'CANCELLED', 'FAILED', 'TIMED_OUT')),
    assignee_actor_id UUID REFERENCES actors(id) ON DELETE SET NULL,
    estimated_effort NUMERIC DEFAULT 1.0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ------------------------------------------------------------------------------
-- 8. ÇIKTILAR VE SÜRÜMLER (ARTIFACTS - MINIO DEPOSU İLE ENTEGRE)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS artifacts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id UUID REFERENCES tasks(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    artifact_type VARCHAR(32) NOT NULL, -- CODE, DOCUMENT, ANALYSIS, SPREADSHEET, ADR
    storage_path VARCHAR(512), -- MinIO: recorion-artifacts/...
    version INT DEFAULT 1,
    content_hash VARCHAR(128),
    produced_by_actor_id UUID REFERENCES actors(id) ON DELETE SET NULL,
    approval_status VARCHAR(32) DEFAULT 'DRAFT' CHECK (approval_status IN ('DRAFT', 'SUBMITTED', 'APPROVED', 'REJECTED', 'SUPERSEDED')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ------------------------------------------------------------------------------
-- 9. İKİ KADEMELİ KOLEKTİF HAFIZA TABLOSU (STRICT TWO-TIER MEMORY)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS memory_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    scope VARCHAR(16) NOT NULL CHECK (scope IN ('GLOBAL', 'AGENT')), -- GLOBAL: Şirket Kurum Hafızası, AGENT: AI Personel Hafızası
    agent_id UUID REFERENCES actors(id) ON DELETE CASCADE, -- scope=AGENT ise zorunlu, scope=GLOBAL ise NULL
    source_reference VARCHAR(255),
    content TEXT NOT NULL,
    metadata_json JSONB DEFAULT '{}'::jsonb,
    qdrant_point_id UUID,
    status VARCHAR(32) DEFAULT 'APPROVED' CHECK (status IN ('CANDIDATE', 'APPROVED', 'REVOKED')),
    confidence_score NUMERIC DEFAULT 1.0,
    embedding_model_version VARCHAR(64) DEFAULT 'qwen3-embedding-8b',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ------------------------------------------------------------------------------
-- 10. DEBATE ARENA (TARTIŞMA ALANI VE ADR MİMARİ KARARLARI)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS debate_threads (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id UUID REFERENCES tasks(id) ON DELETE CASCADE,
    issue_description TEXT NOT NULL,
    initiator_actor_id UUID REFERENCES actors(id) ON DELETE SET NULL,
    referee_actor_id UUID REFERENCES actors(id) ON DELETE SET NULL,
    status VARCHAR(32) DEFAULT 'OPEN' CHECK (status IN ('OPEN', 'RESOLVED', 'ESCALATED_TO_HUMAN')),
    adr_summary TEXT, -- Mimari Karar Kaydı Özeti
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ------------------------------------------------------------------------------
-- 11. DENETİM LOGLARI VE TELEMETRİ (AUDIT LOGS & CREDITS)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS audit_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    actor_id UUID REFERENCES actors(id) ON DELETE SET NULL,
    action VARCHAR(64) NOT NULL,
    target_type VARCHAR(64),
    target_id VARCHAR(64),
    payload JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS llm_calls (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    task_id UUID REFERENCES tasks(id) ON DELETE SET NULL,
    actor_id UUID REFERENCES actors(id) ON DELETE SET NULL,
    model_id UUID REFERENCES llm_models(id) ON DELETE SET NULL,
    tokens_in INT DEFAULT 0,
    tokens_out INT DEFAULT 0,
    credits_cost NUMERIC DEFAULT 0,
    latency_ms INT DEFAULT 0,
    status VARCHAR(32) DEFAULT 'SUCCESS',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ------------------------------------------------------------------------------
-- 12. SOHBET GEÇMİŞİ VE CANLI DÜŞÜNCE AKIŞI (CHAT MESSAGES & THOUGHT PROCESS)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS chat_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    task_id UUID REFERENCES tasks(id) ON DELETE CASCADE,
    sender_actor_id UUID REFERENCES actors(id) ON DELETE SET NULL,
    role VARCHAR(16) NOT NULL CHECK (role IN ('user', 'assistant', 'system', 'thought', 'tool')),
    content TEXT NOT NULL,
    thought_process TEXT,
    attachments JSONB DEFAULT '[]'::jsonb,
    tokens INT DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_chat_messages_task_id ON chat_messages(task_id, created_at);
CREATE INDEX IF NOT EXISTS idx_chat_messages_project_id ON chat_messages(project_id, created_at);

-- ==============================================================================
-- TOHUM VERİLERİ (SEED DATA)
-- ==============================================================================

-- 1. NACE Kataloğu
INSERT INTO nace_catalog (code, title, sector_group, description) VALUES
('62.01', 'Bilgisayar programlama faaliyetleri', 'Bilişim ve Yazılım', 'Sistem, uygulama, veri tabanı ve yapay zeka yazılımları geliştirme'),
('62.02', 'Bilgisayar danışmanlık faaliyetleri', 'Bilişim ve Danışmanlık', 'BT altyapısı, sistem analizi ve yazılım mimarisi danışmanlığı'),
('69.10', 'Hukuk faaliyetleri', 'Hukuk ve Adalet', 'Avukatlık, hukuki danışmanlık, sözleşme hazırlama ve dava takibi'),
('69.20', 'Muhasebe, defter tutma ve denetim; vergi danışmanlığı', 'Maliye ve Denetim', 'Mali müşavirlik, vergi beyannamesi, bordrolama ve bağımsız denetim'),
('70.22', 'İşletme ve diğer idari danışmanlık faaliyetleri', 'Yönetim Danışmanlığı', 'Stratejik planlama, kurumsal yeniden yapılanma ve süreç optimizasyonu'),
('71.12', 'Mühendislik faaliyetleri ve teknik danışmanlık', 'Mühendislik ve Mimarlık', 'Statik, mekanik, elektrik mühendisliği ve teknik şartname tasarımı'),
('73.11', 'Reklam ajanslarının faaliyetleri', 'Pazarlama ve Reklam', 'Dijital pazarlama, kampanya yönetimi, metin yazarlığı ve PR'),
('47.91', 'İnternet üzerinden perakende ticaret', 'E-Ticaret ve Perakende', 'Pazar yeri entegrasyonu, sipariş takibi, ürün yönetimi'),
('52.29', 'Taşımacılığı destekleyici diğer faaliyetler', 'Lojistik ve Tedarik', 'Sevkiyat yönetimi, navlun, depo ve lojistik koordinasyonu')
ON CONFLICT (code) DO NOTHING;

-- 2. EVREN LLM Sağlayıcısı
INSERT INTO llm_providers (code, name, base_url, api_style, is_active)
VALUES ('EVREN', 'TÜBİTAK BİLGEM EVREN (Türkiye Ulusal LLM Merkezi)', 'https://evren-llmapi.ssyz.org.tr/v1', 'openai', true)
ON CONFLICT (code) DO UPDATE SET base_url = EXCLUDED.base_url;

-- 3. 13 EVREN Modeli
DO $$
DECLARE
    evren_id UUID;
BEGIN
    SELECT id INTO evren_id FROM llm_providers WHERE code = 'EVREN';

    INSERT INTO llm_models (provider_id, model_code, display_name, model_type, context_window, effort_coefficient, capabilities) VALUES
    (evren_id, 'qwen3-asr-1.7b', 'Qwen3 ASR 1.7B', 'AUDIO', 32768, 0.5, '{"speech_to_text": true, "transcription": true}'::jsonb),
    (evren_id, 'deepseek-ocr-2', 'DeepSeek OCR 2', 'OCR', 32768, 0.6, '{"pdf_extract": true, "document_ocr": true}'::jsonb),
    (evren_id, 'dots-ocr', 'Dots OCR', 'OCR', 32768, 0.8, '{"tables": true, "forms": true, "complex_docs": true}'::jsonb),
    (evren_id, 'qwen3-guard-4b', 'Qwen3 Guard 4B', 'GUARD', 16384, 0.3, '{"jailbreak_defense": true, "prompt_injection_defense": true}'::jsonb),
    (evren_id, 'qwen3-reranker-8b', 'Qwen3 Reranker 8B', 'RERANKER', 8192, 0.4, '{"cross_encoder": true, "context_ranking": true}'::jsonb),
    (evren_id, 'qwen3-embedding-8b', 'Qwen3 Embedding 8B', 'EMBEDDING', 32768, 0.3, '{"dense_vector": 4096, "two_tier_memory": true}'::jsonb),
    (evren_id, 'qwen3-vl-30b', 'Qwen3 VL 30B', 'VISION', 131072, 1.5, '{"figma_analysis": true, "ui_screenshot": true, "diagram": true}'::jsonb),
    (evren_id, 'glm-5.3', 'GLM 5.3 (Sistem Mimarı)', 'CHAT', 131072, 2.0, '{"orchestration": true, "architecture": true, "tool_calling": true}'::jsonb),
    (evren_id, 'qwen3.8-flash-next', 'Qwen3.8 Flash Next (Operasyonel)', 'CHAT', 131072, 0.7, '{"fast_inference": true, "summarization": true}'::jsonb),
    (evren_id, 'deepseek-v4.1-flash', 'DeepSeek V4.1 Flash (Kıdemli Kod)', 'CHAT', 131072, 1.2, '{"senior_coding": true, "refactoring": true, "unit_tests": true}'::jsonb),
    (evren_id, 'mimo-v2.6-pro', 'MIMO V2.6 Pro (İş Analisti & Muhakeme)', 'CHAT', 131072, 1.8, '{"complex_reasoning": true, "backlog_generator": true}'::jsonb),
    (evren_id, 'gemma-4-31b', 'Gemma 4 31B (Dokümantasyon & PR)', 'CHAT', 131072, 1.0, '{"documentation": true, "pr_marketing": true}'::jsonb),
    (evren_id, 'deepseek-v4-flash', 'DeepSeek V4 Flash (Hızlı Kod & QA)', 'CHAT', 131072, 0.8, '{"qa_review": true, "rapid_code": true}'::jsonb)
    ON CONFLICT (model_code) DO NOTHING;
END $$;

-- 4. Örnek Demo Tenant (RECOrion Teknoloji A.Ş.)
INSERT INTO tenants (slug, name, tax_id, nace_codes, sector_manifesto)
VALUES (
    'recorion-demo',
    'RECOrion Teknoloji A.Ş.',
    'TR-1234567890',
    '["62.01", "70.22"]'::jsonb,
    'RECOrion Teknoloji A.Ş., yapay zekâ orkestrasyonu, otonom yazılım ve kurumsal akıl yürütme alanında öncü teknoloji üreticisidir. Tüm çalışanlar (İnsan ve AI) rol eşitliği ve kalite kapıları disipliniyle görev yapar.'
)
ON CONFLICT (slug) DO NOTHING;

-- 5. Örnek Kullanıcılar ve AI Personelleri
DO $$
DECLARE
    t_id UUID;
    m_glm UUID;
    m_code UUID;
    m_qa UUID;
    m_analyst UUID;
    human_admin_id UUID;
BEGIN
    SELECT id INTO t_id FROM tenants WHERE slug = 'recorion-demo';
    SELECT id INTO m_glm FROM llm_models WHERE model_code = 'glm-5.3';
    SELECT id INTO m_code FROM llm_models WHERE model_code = 'deepseek-v4.1-flash';
    SELECT id INTO m_qa FROM llm_models WHERE model_code = 'deepseek-v4-flash';
    SELECT id INTO m_analyst FROM llm_models WHERE model_code = 'mimo-v2.6-pro';

    -- İnsan Süper Admin
    INSERT INTO actors (tenant_id, actor_type, display_name, email, role, status)
    VALUES (t_id, 'HUMAN', 'Cüneyt Admin', 'admin@recorion.local', 'SUPER_ADMIN', 'IDLE')
    ON CONFLICT DO NOTHING
    RETURNING id INTO human_admin_id;

    -- AI Personeli 1: Sistem Mimarı
    INSERT INTO actors (tenant_id, actor_type, display_name, role, capability_profile, preferred_model_id, autonomy_level, system_prompt, status)
    VALUES (t_id, 'AI_AGENT', 'Sistem Mimarı Ajan', 'ARCHITECT', 'reasoning', m_glm, 'L2', 'Sen RECOrion Sistem Mimarı Ajanısın. Dağıtık mimarileri, veri modellerini ve teknik sözleşmeleri tasarlarsın.', 'IDLE')
    ON CONFLICT DO NOTHING;

    -- AI Personeli 2: Kıdemli Kodlayıcı
    INSERT INTO actors (tenant_id, actor_type, display_name, role, capability_profile, preferred_model_id, autonomy_level, system_prompt, status)
    VALUES (t_id, 'AI_AGENT', 'Kıdemli Kodlayıcı Ajan', 'CODER', 'code-strong', m_code, 'L1', 'Sen RECOrion Kıdemli Kodlayıcı Ajanısın. Temiz kod, birim testler ve SOLID prensiplerine tam bağlı çalışırsın.', 'IDLE')
    ON CONFLICT DO NOTHING;

    -- AI Personeli 3: QA Test Ajanı
    INSERT INTO actors (tenant_id, actor_type, display_name, role, capability_profile, preferred_model_id, autonomy_level, system_prompt, status)
    VALUES (t_id, 'AI_AGENT', 'QA Test Ajanı', 'QA', 'code-strong', m_qa, 'L1', 'Sen RECOrion Kalite Güvence Ajanısın. Kod standartlarını denetler, güvenlik açıklarını yakalar ve Debate Arena başlatırsın.', 'IDLE')
    ON CONFLICT DO NOTHING;

    -- AI Personeli 4: İş Analisti Ajanı
    INSERT INTO actors (tenant_id, actor_type, display_name, role, capability_profile, preferred_model_id, autonomy_level, system_prompt, status)
    VALUES (t_id, 'AI_AGENT', 'İş Analisti Ajanı', 'ANALYST', 'reasoning', m_analyst, 'L2', 'Sen RECOrion İş Analisti Ajanısın. Müşteri isterlerini Backlog, Epic ve kabul kriterlerine dönüştürürsün.', 'IDLE')
    ON CONFLICT DO NOTHING;

    -- 6. Şirket Kurum Hafızasına (NS_GLOBAL) Kök Manifesto Kaydı
    INSERT INTO memory_items (tenant_id, scope, agent_id, source_reference, content, status, confidence_score)
    VALUES (
        t_id,
        'GLOBAL',
        NULL,
        'ROOT_MANIFESTO',
        'Kurumsal Manifesto: RECOrion Teknoloji A.Ş., deterministik durum makineleri, rol eşitliği ve iki kademeli kolektif hafıza prensiplerine göre çalışır. Güvenlik, kalite ve şeffaflık tavizsizdir.',
        'APPROVED',
        1.0
    )
    ON CONFLICT DO NOTHING;
END $$;
