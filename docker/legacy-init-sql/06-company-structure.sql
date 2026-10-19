-- ==============================================================================
-- RECOrion: Musteri Sirket Yonetimi (Company Admin) - Organizasyon Yapisi
-- Idempotent: tekrar calistirilabilir.
-- ==============================================================================

-- MADDE 1: Departmanlar
CREATE TABLE IF NOT EXISTS departments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    name VARCHAR(128) NOT NULL,
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Ayni sirkette ayni isimde (buyuk/kucuk harf duyarsiz) iki departman olamaz
CREATE UNIQUE INDEX IF NOT EXISTS uq_departments_tenant_name ON departments (tenant_id, lower(name));
CREATE INDEX IF NOT EXISTS idx_departments_tenant_id ON departments (tenant_id);

-- MADDE 2: Sirket Unvanlari & AI Kontrol Altyapisi
ALTER TABLE job_titles DROP CONSTRAINT IF EXISTS job_titles_code_key;
CREATE UNIQUE INDEX IF NOT EXISTS uq_job_titles_tenant_code ON job_titles (COALESCE(tenant_id, '00000000-0000-0000-0000-000000000000'::uuid), lower(code));
ALTER TABLE job_titles ADD COLUMN IF NOT EXISTS ai_review_status VARCHAR(32) DEFAULT 'COMPANY_LOCAL';
ALTER TABLE job_titles ADD COLUMN IF NOT EXISTS ai_review_feedback TEXT;

-- MADDE 3: AI Ajan ve Personel Organizasyon Baglantilari
ALTER TABLE actors ADD COLUMN IF NOT EXISTS department_id UUID REFERENCES departments(id) ON DELETE SET NULL;
ALTER TABLE actors ADD COLUMN IF NOT EXISTS hired_at TIMESTAMPTZ DEFAULT NOW();
ALTER TABLE actors ADD COLUMN IF NOT EXISTS dismissed_at TIMESTAMPTZ;
ALTER TABLE actors ADD COLUMN IF NOT EXISTS description TEXT;
