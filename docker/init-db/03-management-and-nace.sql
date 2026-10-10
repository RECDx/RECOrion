-- ==============================================================================
-- RECOrion: Yönetim Konsolu, Paketler, Ünvanlar & NACE Şeması (Adım 1)
-- ==============================================================================

-- 1. NACE Kataloğu Şema Güncellemesi
ALTER TABLE nace_catalog ALTER COLUMN title TYPE TEXT;
ALTER TABLE nace_catalog ALTER COLUMN sector_group DROP NOT NULL;
ALTER TABLE nace_catalog ALTER COLUMN sector_group SET DEFAULT 'GENEL';

-- 2. Paketler (Kiralama & Abonelik Planları)
CREATE TABLE IF NOT EXISTS plans (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(64) UNIQUE NOT NULL, -- STARTER, PRO, ENTERPRISE
    name VARCHAR(128) NOT NULL,
    description TEXT,
    monthly_price NUMERIC DEFAULT 0.0,
    currency VARCHAR(8) DEFAULT 'TRY',
    max_humans INT DEFAULT 5,
    max_agents INT DEFAULT 5,
    max_projects INT DEFAULT 3,
    monthly_credits INT DEFAULT 1000,
    storage_gb INT DEFAULT 10,
    allowed_models JSONB DEFAULT '[]'::jsonb,
    features JSONB DEFAULT '{}'::jsonb,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 3. Standart Kurumsal Ünvanlar ve Base Rol Prompt Şablonları
CREATE TABLE IF NOT EXISTS job_titles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(64) UNIQUE NOT NULL, -- ARCHITECT, BACKEND_DEV, etc.
    title VARCHAR(128) NOT NULL,
    category VARCHAR(64) NOT NULL, -- YAZILIM, ANALIZ, FINANS, HUKUK, IK, PAZARLAMA, YONETIM
    description TEXT,
    base_role_prompt TEXT NOT NULL,
    required_skills JSONB DEFAULT '[]'::jsonb,
    recommended_model_code VARCHAR(128) DEFAULT 'glm-5.3',
    autonomy_level VARCHAR(8) DEFAULT 'L1',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 4. Müşteri Satın Alma / Kiralama Başvuruları (Leads)
CREATE TABLE IF NOT EXISTS tenant_leads (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    plan_id UUID REFERENCES plans(id) ON DELETE SET NULL,
    company_name VARCHAR(255) NOT NULL,
    tax_id VARCHAR(32),
    address TEXT,
    phone VARCHAR(32),
    website VARCHAR(255),
    contact_email VARCHAR(255) NOT NULL,
    nace_codes JSONB DEFAULT '[]'::jsonb,
    generated_manifesto TEXT,
    assigned_skills JSONB DEFAULT '[]'::jsonb,
    status VARCHAR(32) DEFAULT 'PENDING' CHECK (status IN ('PENDING', 'CONTACTED', 'APPROVED', 'REJECTED')),
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 5. Şirket İçi Roller ve Yetkilendirme Matrisi (RBAC)
CREATE TABLE IF NOT EXISTS tenant_roles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    name VARCHAR(64) NOT NULL,
    description TEXT,
    permissions JSONB DEFAULT '[]'::jsonb, -- ['project:create', 'task:approve', 'agent:hire', etc.]
    is_system BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 6. Tenants ve Actors tablolarına yeni alanlar
ALTER TABLE tenants ADD COLUMN IF NOT EXISTS phone VARCHAR(32);
ALTER TABLE tenants ADD COLUMN IF NOT EXISTS address TEXT;
ALTER TABLE tenants ADD COLUMN IF NOT EXISTS website VARCHAR(255);
ALTER TABLE tenants ADD COLUMN IF NOT EXISTS contact_email VARCHAR(255);
ALTER TABLE tenants ADD COLUMN IF NOT EXISTS plan_id UUID REFERENCES plans(id) ON DELETE SET NULL;

ALTER TABLE actors ADD COLUMN IF NOT EXISTS role_id UUID REFERENCES tenant_roles(id) ON DELETE SET NULL;
ALTER TABLE actors ADD COLUMN IF NOT EXISTS job_title_id UUID REFERENCES job_titles(id) ON DELETE SET NULL;

-- 7. İndeksler
CREATE INDEX IF NOT EXISTS idx_nace_catalog_code ON nace_catalog(code);
CREATE INDEX IF NOT EXISTS idx_tenant_leads_status ON tenant_leads(status);
CREATE INDEX IF NOT EXISTS idx_tenant_roles_tenant_id ON tenant_roles(tenant_id);
