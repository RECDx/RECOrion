-- ==============================================================================
-- RECOrion: Ek Güncelleme Şeması (Odoo Alanları, İzin Kataloğu, Özel Ünvanlar, RECDx Admin)
-- ==============================================================================

-- 1. tenant_leads tablosuna Odoo 19 alanları ekleme
ALTER TABLE tenant_leads ADD COLUMN IF NOT EXISTS odoo_partner_id INT;
ALTER TABLE tenant_leads ADD COLUMN IF NOT EXISTS odoo_order_id INT;
ALTER TABLE tenant_leads ADD COLUMN IF NOT EXISTS odoo_order_name VARCHAR(64);

-- 1.1 actors tablosuna phone ve address alanları ekleme
ALTER TABLE actors ADD COLUMN IF NOT EXISTS phone VARCHAR(32);
ALTER TABLE actors ADD COLUMN IF NOT EXISTS address TEXT;

-- 2. plans tablosuna özel ünvan tanımlama yetkisi bayrağı ekleme
ALTER TABLE plans ADD COLUMN IF NOT EXISTS can_create_custom_titles BOOLEAN DEFAULT false;

-- ENTERPRISE paketine özel ünvan yetkisini ver
UPDATE plans SET can_create_custom_titles = true WHERE code = 'ENTERPRISE';

-- 3. job_titles tablosuna tenant_id ekleme (Müşteriye özel ünvanlar için)
ALTER TABLE job_titles ADD COLUMN IF NOT EXISTS tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE;

-- 4. RECOrion İzin Kataloğu (system_permissions) Tablosu
CREATE TABLE IF NOT EXISTS system_permissions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(64) UNIQUE NOT NULL,
    module VARCHAR(64) NOT NULL, -- PLATFORM, RBAC, AGENTS, PROJECTS, CHAT, MEMORY, BILLING
    name VARCHAR(128) NOT NULL,
    description TEXT,
    default_for_roles JSONB DEFAULT '[]'::jsonb, -- Hangi rollere varsayılan olarak açık: SUPER_ADMIN, COMPANY_ADMIN, PROJECT_MANAGER, STANDARD_USER
    is_system BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- İzinleri Ekle / Güncelle
INSERT INTO system_permissions (code, module, name, description, default_for_roles, is_system)
VALUES 
-- PLATFORM & ŞİRKET
('system:admin', 'PLATFORM', 'Tam Sistem Yönetimi', 'Tüm sistem ve altyapı ayarlarını yönetme süper admin yetkisi', '["SUPER_ADMIN"]'::jsonb, true),
('tenant:manage', 'PLATFORM', 'Şirket ve Paket Yönetimi', 'Şirket profilini, abonelik paketini ve ayarlarını yönetme', '["SUPER_ADMIN", "COMPANY_ADMIN"]'::jsonb, true),
('tenant:view', 'PLATFORM', 'Şirket Bilgilerini Görüntüleme', 'Şirket ve kurum detaylarını görüntüleme', '["SUPER_ADMIN", "COMPANY_ADMIN", "PROJECT_MANAGER", "STANDARD_USER"]'::jsonb, true),

-- RBAC & KULLANICILAR
('role:create', 'RBAC', 'Yeni Rol Tanımlama', 'Şirket içi özel roller oluşturma ve izin atama', '["SUPER_ADMIN", "COMPANY_ADMIN"]'::jsonb, true),
('role:edit', 'RBAC', 'Rol Düzenleme', 'Mevcut rollerin yetki ve tanımlarını değiştirme', '["SUPER_ADMIN", "COMPANY_ADMIN"]'::jsonb, true),
('role:delete', 'RBAC', 'Rol Silme', 'Şirket içi özel rolleri silme', '["SUPER_ADMIN", "COMPANY_ADMIN"]'::jsonb, true),
('user:invite', 'RBAC', 'Kullanıcı Davet Etme', 'Platforma yeni insan kullanıcı davet etme ve şifre belirleme', '["SUPER_ADMIN", "COMPANY_ADMIN"]'::jsonb, true),
('user:manage', 'RBAC', 'Kullanıcı Hesaplarını Yönetme', 'Kullanıcıları askıya alma, rolünü değiştirme ve düzenleme', '["SUPER_ADMIN", "COMPANY_ADMIN"]'::jsonb, true),

-- AI AJAN PERSONELLER & ÜNVANLAR
('agent:hire', 'AGENTS', 'AI Personel İşe Alma', 'Yeni AI ajan personeli tanımlama ve projeye dahil etme', '["SUPER_ADMIN", "COMPANY_ADMIN", "PROJECT_MANAGER"]'::jsonb, true),
('agent:configure', 'AGENTS', 'AI Personel Konfigürasyonu', 'AI modelini, sistem promptunu ve otonomi seviyesini değiştirme', '["SUPER_ADMIN", "COMPANY_ADMIN"]'::jsonb, true),
('agent:custom_title', 'AGENTS', 'Özel AI Ünvanı Tanımlama', 'Kurumsal pakete özel şirket ünvanı ve prompt şablonu üretme', '["SUPER_ADMIN", "COMPANY_ADMIN"]'::jsonb, true),
('agent:quarantine', 'AGENTS', 'AI Personelini Karantinaya Alma', 'Hatalı veya sınır dışına çıkan ajanı durdurma ve dondurma', '["SUPER_ADMIN", "COMPANY_ADMIN", "PROJECT_MANAGER"]'::jsonb, true),

-- PROJE & İŞ AKIŞI (DAG)
('project:create', 'PROJECTS', 'Yeni Proje Başlatma', 'Yeni proje açma, repo ve şablon seçimi yapma', '["SUPER_ADMIN", "COMPANY_ADMIN", "PROJECT_MANAGER"]'::jsonb, true),
('project:manage', 'PROJECTS', 'Proje Ayarlarını Yönetme', 'Proje parametrelerini ve takım atamalarını değiştirme', '["SUPER_ADMIN", "COMPANY_ADMIN", "PROJECT_MANAGER"]'::jsonb, true),
('task:create', 'PROJECTS', 'Görev Oluşturma ve Atama', 'İş akışı görevi oluşturup AI veya insan personele atama', '["SUPER_ADMIN", "COMPANY_ADMIN", "PROJECT_MANAGER", "STANDARD_USER"]'::jsonb, true),
('task:approve', 'PROJECTS', 'Kalite Kapısı Onaylama (Gate Approve)', 'AI çıktısını onaylayıp sonraki personele devretme', '["SUPER_ADMIN", "COMPANY_ADMIN", "PROJECT_MANAGER"]'::jsonb, true),
('task:reject', 'PROJECTS', 'Revizyon İsteme (Gate Reject)', 'AI personelinden geribildirime göre revizyon talep etme', '["SUPER_ADMIN", "COMPANY_ADMIN", "PROJECT_MANAGER"]'::jsonb, true),

-- SOHBET & MÜZAKERE
('chat:participate', 'CHAT', 'AI ile Sohbet ve Görev İletişimi', 'AI personelleri ile görev bazlı etkileşime girme', '["SUPER_ADMIN", "COMPANY_ADMIN", "PROJECT_MANAGER", "STANDARD_USER"]'::jsonb, true),
('chat:view_a2a', 'CHAT', 'Ajanlar Arası Müzakereleri İzleme', 'Ajanların kendi aralarındaki teknik tartışmaları görme', '["SUPER_ADMIN", "COMPANY_ADMIN", "PROJECT_MANAGER"]'::jsonb, true),
('chat:export', 'CHAT', 'Sohbet ve Düşünce Akışını Dışa Aktarma', 'Görüşme ve otonom akış loglarını dışarı aktarma', '["SUPER_ADMIN", "COMPANY_ADMIN"]'::jsonb, true),

-- KOLEKTİF KURUM HAFIZASI (MEMORY)
('memory:search', 'MEMORY', 'Kurum Hafızasında Arama', 'Şirket ve ajan hafıza uzayında semantik arama yapma', '["SUPER_ADMIN", "COMPANY_ADMIN", "PROJECT_MANAGER", "STANDARD_USER"]'::jsonb, true),
('memory:promote', 'MEMORY', 'Hafızayı Kurumsal Hafızaya Terfi Ettirme', 'Ajan tecrübesini Şirket Kurum Hafızasına (NS_GLOBAL) aktarma', '["SUPER_ADMIN", "COMPANY_ADMIN", "PROJECT_MANAGER"]'::jsonb, true),
('memory:revoke', 'MEMORY', 'Kurum Hafızasından Çıkarma / Silme', 'Geçersizleşen veya hatalı kurumsal bilgiyi hafızadan kaldırma', '["SUPER_ADMIN", "COMPANY_ADMIN"]'::jsonb, true),

-- FİNANS & KREDİ
('billing:view', 'BILLING', 'Fatura ve Kredi Durumunu Görme', 'Kalan işlem kredisini ve fatura geçmişini inceleme', '["SUPER_ADMIN", "COMPANY_ADMIN"]'::jsonb, true),
('billing:topup', 'BILLING', 'Kredi Yükleme ve Paket Değiştirme', 'Ek model kredisi satın alma ve paket yükseltme', '["SUPER_ADMIN", "COMPANY_ADMIN"]'::jsonb, true)
ON CONFLICT (code) DO UPDATE SET 
    module = EXCLUDED.module,
    name = EXCLUDED.name,
    description = EXCLUDED.description,
    default_for_roles = EXCLUDED.default_for_roles;

-- 5. RECDx Süper Admin Kullanıcısını Ekleme (E maddesi)
-- Şifre: RECDx_SuperAdmin_2026! (SHA-256 + tuz: recorion_tenant_salt_2026)
-- Hash: hashlib.sha256(b"recorion_tenant_salt_2026_RECDx_SuperAdmin_2026!").hexdigest()
-- f284ec6efdf4079836371cbef878693eb120fcbca2c6ee4b1ea9bebc7ec86e11

-- Önce RECDx Ana Şirketi var mı bakalım
INSERT INTO tenants (slug, name, phone, contact_email, website, address, sector_manifesto)
VALUES (
    'recdx_hq', 
    'RECDx Bilişim Teknolojileri ve Yapay Zeka A.Ş.',
    '+90 216 555 00 00',
    'info@recdx.com',
    'https://recdx.com',
    'Maslak Teknopark, İstanbul',
    'RECDx Çekirdek Kurumsal Yönetim ve Altyapı Manifestosu'
)
ON CONFLICT (slug) DO UPDATE SET name = EXCLUDED.name, contact_email = EXCLUDED.contact_email;

-- RECDx Süper Admin Aktörü
INSERT INTO actors (
    tenant_id, 
    actor_type, 
    display_name, 
    email, 
    role, 
    password_hash, 
    capability_profile, 
    autonomy_level, 
    status
)
SELECT 
    id, 
    'HUMAN', 
    'Muhammed Cüneyt ERDİL', 
    'cuneyterdil@recdx.com', 
    'SUPER_ADMIN', 
    'bc5036ab30d9e3cee5274d10502ddb81bbadd7ef09a7b155b45f8b14785cdc86', 
    'super-admin', 
    'L3', 
    'IDLE'
FROM tenants WHERE slug = 'recdx_hq'
ON CONFLICT DO NOTHING;

-- 6. Sistem Ayarları Tablosu & Varsayılan Manifesto AI Modeli
CREATE TABLE IF NOT EXISTS system_settings (
    key VARCHAR(64) PRIMARY KEY,
    value JSONB NOT NULL,
    description TEXT,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

INSERT INTO system_settings (key, value, description)
VALUES ('default_manifesto_model', '"deepseek-v4.1-flash"'::jsonb, 'NACE kodlarına göre şirket manifestosu ve ajan rollerini oluşturan en güçlü EVREN LLM modeli')
ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value;

