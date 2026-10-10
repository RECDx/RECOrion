-- 03_mail_templates_and_tenant_enhancements.sql
-- Mail Şablonları, Zamanlama (Schedule) ve Şirket Geliştirmeleri

-- 1. Email Templates Tablosu
CREATE TABLE IF NOT EXISTS email_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(64) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    subject VARCHAR(255) NOT NULL,
    html_content TEXT NOT NULL,
    text_content TEXT,
    variables JSONB DEFAULT '[]'::jsonb,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. Notification Schedules Tablosu (Madde 2 & 14)
CREATE TABLE IF NOT EXISTS notification_schedules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    trigger_type VARCHAR(64) NOT NULL, -- 'ON_REGISTRATION', 'BEFORE_EXPIRATION_INTERVAL', 'MANUAL', 'CRON_SCHEDULED'
    template_code VARCHAR(64) NOT NULL,
    frequency_days INT DEFAULT 15,
    target_lead_days INT DEFAULT 90, -- 3 ay (90 gün)
    is_active BOOLEAN DEFAULT TRUE,
    last_run_at TIMESTAMPTZ,
    next_run_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3. Tenants Tablosu Yeni Alanları (Madde 7, 10, 11, 12)
ALTER TABLE tenants ADD COLUMN IF NOT EXISTS tax_office VARCHAR(128);
ALTER TABLE tenants ADD COLUMN IF NOT EXISTS package_start_date TIMESTAMPTZ DEFAULT NOW();
ALTER TABLE tenants ADD COLUMN IF NOT EXISTS package_expiry_date TIMESTAMPTZ DEFAULT (NOW() + INTERVAL '1 year');
ALTER TABLE tenants ADD COLUMN IF NOT EXISTS last_reminder_sent_at TIMESTAMPTZ;

-- 4. Tenant Leads Tablosu Yeni Alanları (Madde 12)
ALTER TABLE tenant_leads ADD COLUMN IF NOT EXISTS tax_office VARCHAR(128);

-- Mevcut tenant'ların başlangıç ve bitiş tarihlerini garanti altına alalım
UPDATE tenants SET package_start_date = created_at WHERE package_start_date IS NULL;
UPDATE tenants SET package_expiry_date = (created_at + INTERVAL '1 year') WHERE package_expiry_date IS NULL;

-- 5. Varsayılan Mail Şablonları Seed (Madde 1)
INSERT INTO email_templates (code, name, subject, html_content, text_content, variables, is_active)
VALUES
(
    'WELCOME_CUSTOMER',
    'RECOrion Kurumsal Hoş Geldiniz Bilgilendirmesi',
    'RECOrion Platformuna Hoş Geldiniz - {{company_name}} Hesap ve Paket Bilgileriniz',
    '<!DOCTYPE html>
<html lang="tr">
<head>
  <meta charset="UTF-8">
  <style>
    body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; background-color: #0b0f19; margin: 0; padding: 24px; color: #e2e8f0; }
    .email-container { max-width: 640px; margin: 0 auto; background: linear-gradient(180deg, #101628 0%, #0d1222 100%); border: 1px solid rgba(113, 52, 226, 0.4); border-radius: 20px; overflow: hidden; box-shadow: 0 20px 40px rgba(0,0,0,0.6); }
    .header { background: linear-gradient(135deg, #7134e2 0%, #314ccd 50%, #146ceb 100%); padding: 32px 24px; text-align: center; }
    .logo-badge { display: inline-block; width: 48px; height: 48px; line-height: 48px; background: rgba(255,255,255,0.2); border-radius: 12px; font-weight: 900; font-size: 24px; color: #fff; margin-bottom: 12px; }
    .title { font-size: 24px; font-weight: 800; color: #ffffff; margin: 0; }
    .subtitle { font-size: 13px; color: rgba(255,255,255,0.85); margin-top: 6px; }
    .content { padding: 32px 28px; line-height: 1.6; }
    .greeting { font-size: 16px; font-weight: 700; color: #fff; margin-bottom: 16px; }
    .info-card { background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.08); border-radius: 14px; padding: 20px; margin: 24px 0; }
    .info-row { display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid rgba(255,255,255,0.05); font-size: 14px; }
    .info-row:last-child { border-bottom: none; }
    .info-label { color: #94a3b8; font-weight: 600; }
    .info-val { color: #fff; font-weight: 700; font-family: monospace; }
    .cta-btn { display: inline-block; background: linear-gradient(135deg, #7134e2 0%, #146ceb 100%); color: #ffffff !important; text-decoration: none; font-weight: 800; font-size: 15px; padding: 14px 32px; border-radius: 12px; margin: 20px 0; box-shadow: 0 4px 15px rgba(113, 52, 226, 0.4); }
    .footer { padding: 24px; text-align: center; font-size: 12px; color: #64748b; border-top: 1px solid rgba(255,255,255,0.06); background: rgba(0,0,0,0.2); }
  </style>
</head>
<body>
  <div class="email-container">
    <div class="header">
      <div class="logo-badge">R</div>
      <h1 class="title">RECOrion Ailesine Hoş Geldiniz</h1>
      <div class="subtitle">Operasyonel Muhakeme ve Otonom Yapay Zeka Ajan Orkestrasyonu</div>
    </div>
    <div class="content">
      <div class="greeting">Sayın {{company_name}} Yetkilileri,</div>
      <p>RECOrion kurumsal kiralama paketiniz ve otonom yazılım ekosisteminiz başarıyla aktif edilmiştir. Şirketinizin NACE faaliyet kodlarına göre eğitilmiş çekirdek manifesto ve yapay zeka ajanı iş güçleriniz görev alabilmeniz için hazırdır.</p>
      
      <div class="info-card">
        <div class="info-row">
          <span class="info-label">Kayıtlı Kurum:</span>
          <span class="info-val">{{company_name}}</span>
        </div>
        <div class="info-row">
          <span class="info-label">Aktif Kiralama Paketi:</span>
          <span class="info-val" style="color: #38bdf8;">{{plan_name}}</span>
        </div>
        <div class="info-row">
          <span class="info-label">Aktivasyon Tarihi:</span>
          <span class="info-val">{{start_date}}</span>
        </div>
        <div class="info-row">
          <span class="info-label">Paket Bitiş Tarihi:</span>
          <span class="info-val" style="color: #34d399;">{{expiry_date}}</span>
        </div>
        <div class="info-row">
          <span class="info-label">Yönetici E-Posta:</span>
          <span class="info-val">{{admin_email}}</span>
        </div>
        <div class="info-row">
          <span class="info-label">İlk Giriş Şifresi:</span>
          <span class="info-val" style="color: #f59e0b;">{{admin_password}}</span>
        </div>
      </div>

      <div style="text-align: center;">
        <a href="{{portal_url}}" class="cta-btn">RECOrion Konsoluna Giriş Yapın &rarr;</a>
      </div>

      <p style="font-size: 13px; color: #94a3b8; margin-top: 24px;">Güvenliğiniz için ilk oturum açışınızda şifrenizi profil ayarlarınızdan güncellemenizi rica ederiz.</p>
    </div>
    <div class="footer">
      <strong>RECDx Dijital Dönüşüm & Yapay Zeka Teknolojileri A.Ş.</strong><br>
      Maslak Teknopark, Sarıyer / İstanbul | info@recdx.com | www.recdx.com
    </div>
  </div>
</body>
</html>',
    'Sayın {{company_name}} Yetkilileri, RECOrion kiralama paketiniz ({{plan_name}}) aktif edilmiştir. Giriş e-postanız: {{admin_email}}, Şifreniz: {{admin_password}}, Paket Bitiş Tarihi: {{expiry_date}}. Giriş Portalı: {{portal_url}}',
    '["company_name", "plan_name", "start_date", "expiry_date", "admin_email", "admin_password", "portal_url"]'::jsonb,
    TRUE
)
ON CONFLICT (code) DO UPDATE SET
    name = EXCLUDED.name,
    subject = EXCLUDED.subject,
    html_content = EXCLUDED.html_content,
    variables = EXCLUDED.variables;

INSERT INTO email_templates (code, name, subject, html_content, text_content, variables, is_active)
VALUES
(
    'PACKAGE_EXPIRATION_REMINDER',
    'RECOrion Paket Süre Dolumu Hatırlatma Bildirimi',
    'Önemli: RECOrion Paketinizin Süresi Dolmak Üzere - {{company_name}} (Kalan: {{days_remaining}} Gün)',
    '<!DOCTYPE html>
<html lang="tr">
<head>
  <meta charset="UTF-8">
  <style>
    body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; background-color: #0b0f19; margin: 0; padding: 24px; color: #e2e8f0; }
    .email-container { max-width: 640px; margin: 0 auto; background: linear-gradient(180deg, #101628 0%, #0d1222 100%); border: 1px solid rgba(245, 158, 11, 0.4); border-radius: 20px; overflow: hidden; box-shadow: 0 20px 40px rgba(0,0,0,0.6); }
    .header { background: linear-gradient(135deg, #d97706 0%, #b45309 50%, #78350f 100%); padding: 32px 24px; text-align: center; }
    .logo-badge { display: inline-block; width: 48px; height: 48px; line-height: 48px; background: rgba(255,255,255,0.2); border-radius: 12px; font-weight: 900; font-size: 24px; color: #fff; margin-bottom: 12px; }
    .title { font-size: 22px; font-weight: 800; color: #ffffff; margin: 0; }
    .subtitle { font-size: 13px; color: rgba(255,255,255,0.9); margin-top: 6px; }
    .content { padding: 32px 28px; line-height: 1.6; }
    .greeting { font-size: 16px; font-weight: 700; color: #fff; margin-bottom: 16px; }
    .alert-banner { background: rgba(245, 158, 11, 0.12); border-left: 4px solid #f59e0b; padding: 14px 18px; border-radius: 8px; margin-bottom: 24px; color: #fde68a; font-size: 14px; }
    .info-card { background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.08); border-radius: 14px; padding: 20px; margin: 24px 0; }
    .info-row { display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid rgba(255,255,255,0.05); font-size: 14px; }
    .info-row:last-child { border-bottom: none; }
    .info-label { color: #94a3b8; font-weight: 600; }
    .info-val { color: #fff; font-weight: 700; font-family: monospace; }
    .cta-btn { display: inline-block; background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%); color: #000000 !important; text-decoration: none; font-weight: 800; font-size: 15px; padding: 14px 32px; border-radius: 12px; margin: 20px 0; box-shadow: 0 4px 15px rgba(245, 158, 11, 0.4); }
    .footer { padding: 24px; text-align: center; font-size: 12px; color: #64748b; border-top: 1px solid rgba(255,255,255,0.06); background: rgba(0,0,0,0.2); }
  </style>
</head>
<body>
  <div class="email-container">
    <div class="header">
      <div class="logo-badge">&#9888;</div>
      <h1 class="title">RECOrion Paket Süre Dolumu Hatırlatması</h1>
      <div class="subtitle">Kesintisiz Yapay Zeka Ajan Operasyonları İçin Paket Yenileme</div>
    </div>
    <div class="content">
      <div class="greeting">Sayın {{company_name}} Yetkilileri,</div>
      
      <div class="alert-banner">
        <strong>Hatırlatma:</strong> Kurumunuza tahsis edilmiş olan <strong>{{plan_name}}</strong> paketinin kullanım süresinin dolmasına <strong>{{days_remaining}} gün</strong> kalmıştır.
      </div>

      <p>Sisteme entegre yapay zeka ajanlarınızın görevlerini kesintisiz icra etmesi, şirket hafızası ve projelerinizin aktif kalması adına paket yenileme sürecinizi başlatmanızı önemle rica ederiz.</p>
      
      <div class="info-card">
        <div class="info-row">
          <span class="info-label">Kayıtlı Kurum:</span>
          <span class="info-val">{{company_name}}</span>
        </div>
        <div class="info-row">
          <span class="info-label">Mevcut Paket:</span>
          <span class="info-val" style="color: #38bdf8;">{{plan_name}}</span>
        </div>
        <div class="info-row">
          <span class="info-label">Paket Bitiş Tarihi:</span>
          <span class="info-val" style="color: #ef4444;">{{expiry_date}}</span>
        </div>
        <div class="info-row">
          <span class="info-label">Kalan Süre:</span>
          <span class="info-val" style="color: #f59e0b;">{{days_remaining}} Gün</span>
        </div>
      </div>

      <div style="text-align: center;">
        <a href="{{renewal_url}}" class="cta-btn">Paketi Hemen Yenileyin &rarr;</a>
      </div>

      <p style="font-size: 13px; color: #94a3b8; margin-top: 24px;">Sorularınız ve kurumsal paket yükseltme teklifleri için RECDx Müşteri Başarı ekibimiz ile iletişime geçebilirsiniz.</p>
    </div>
    <div class="footer">
      <strong>RECDx Dijital Dönüşüm & Yapay Zeka Teknolojileri A.Ş.</strong><br>
      Maslak Teknopark, Sarıyer / İstanbul | info@recdx.com | www.recdx.com
    </div>
  </div>
</body>
</html>',
    'Sayın {{company_name}} Yetkilileri, RECOrion {{plan_name}} paketinizin dolumuna {{days_remaining}} gün kalmıştır (Bitiş: {{expiry_date}}). Kesintisiz operasyonlar için yenileyin: {{renewal_url}}',
    '["company_name", "plan_name", "expiry_date", "days_remaining", "renewal_url"]'::jsonb,
    TRUE
)
ON CONFLICT (code) DO UPDATE SET
    name = EXCLUDED.name,
    subject = EXCLUDED.subject,
    html_content = EXCLUDED.html_content,
    variables = EXCLUDED.variables;

-- 6. Varsayılan Schedule Tanımları Seed (Madde 2)
INSERT INTO notification_schedules (name, trigger_type, template_code, frequency_days, target_lead_days, is_active)
VALUES
(
    'Müşteri Kayıt Olduğunda Otomatik Hoşgeldiniz E-postası',
    'ON_REGISTRATION',
    'WELCOME_CUSTOMER',
    0,
    0,
    TRUE
),
(
    'Paket Bitişine 3 Ay Kala 15 Günde 1 Hatırlatıcı E-postası',
    'BEFORE_EXPIRATION_INTERVAL',
    'PACKAGE_EXPIRATION_REMINDER',
    15,
    90,
    TRUE
)
ON CONFLICT DO NOTHING;
