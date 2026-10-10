# scripts/fix_turkish_characters.py
# -*- coding: utf-8 -*-
"""
PostgreSQL veritabanındaki email_templates ve notification_schedules tablolarındaki
bozuk Türkçe karakterleri (? veya ??) orijinal düzgün UTF-8 Türkçe metinlerle onarır.
"""
import os
import sys
import asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql+asyncpg://recorion_admin:recorion_dev_2026!@localhost:5432/recorion_db"
)

# Docker içi için fallback
if os.path.exists("/.dockerenv"):
    DATABASE_URL = os.getenv(
        "DATABASE_URL", 
        "postgresql+asyncpg://recorion_admin:recorion_dev_2026!@postgres:5432/recorion_db"
    )

WELCOME_HTML = """<!DOCTYPE html>
<html lang="tr">
<head>
  <meta charset="UTF-8">
  <style>
    body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; background-color: #0b0f19; margin: 0; padding: 24px; color: #e2e8f0; }
    .email-container { max-width: 640px; margin: 0 auto; background: linear-gradient(180deg, #101628 0%, #0d1222 100%); border: 1px solid rgba(113, 52, 226, 0.4); border-radius: 20px; overflow: hidden; box-shadow: 0 20px 40px rgba(0,0,0,0.6); }
    .header { background: linear-gradient(135deg, #7134e2 0%, #314ccd 50%, #146ceb 100%); padding: 32px 24px; text-align: center; }
    .logo-badge { display: inline-block; width: 48px; height: 48px; line-height: 48px; background: rgba(255,255,255,0.2); border-radius: 12px; font-weight: 900; font-size: 24px; color: #fff; margin-bottom: 12px; }
    .title { color: #ffffff; margin: 0; font-size: 22px; font-weight: 800; letter-spacing: -0.5px; }
    .subtitle { color: rgba(255,255,255,0.85); font-size: 13px; margin-top: 6px; font-weight: 500; }
    .content { padding: 32px 28px; }
    .greeting { font-size: 17px; font-weight: 700; color: #f8fafc; margin-bottom: 14px; }
    .info-card { background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(113, 52, 226, 0.25); border-radius: 12px; padding: 18px 20px; margin: 24px 0; }
    .info-row { display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid rgba(255,255,255,0.05); font-size: 13px; }
    .info-row:last-child { border-bottom: none; }
    .info-label { color: #94a3b8; font-weight: 600; }
    .info-val { color: #f1f5f9; font-weight: 700; font-family: monospace; }
    .cta-btn { display: block; width: 85%; margin: 28px auto 12px; padding: 14px 20px; text-align: center; background: linear-gradient(135deg, #7134e2 0%, #146ceb 100%); color: #ffffff; text-decoration: none; border-radius: 12px; font-weight: 800; font-size: 14px; box-shadow: 0 4px 18px rgba(113, 52, 226, 0.4); }
    .footer { text-align: center; padding: 24px; font-size: 11px; color: #64748b; border-top: 1px solid rgba(255,255,255,0.06); }
  </style>
</head>
<body>
  <div class="email-container">
    <div class="header">
      <div class="logo-badge">R</div>
      <h1 class="title">RECOrion Ailesine Hoş Geldiniz</h1>
      <div class="subtitle">Operational Reasoning Intelligence Orchestration Network</div>
    </div>
    <div class="content">
      <div class="greeting">Sayın {{company_name}} Yetkilileri,</div>
      <p>RECOrion kurumsal kiralama paketiniz ve otonom yazılım ekosisteminiz başarıyla aktif edilmiştir. Yapay zeka ajanlarınız kurumunuzun dijital operasyonlarını yönetmek üzere hizmetinizdedir.</p>

      <div class="info-card">
        <div class="info-row"><span class="info-label">Kayıtlı Kurum:</span><span class="info-val">{{company_name}}</span></div>
        <div class="info-row"><span class="info-label">Tanımlı Paket:</span><span class="info-val" style="color: #a78bfa;">{{plan_name}}</span></div>
        <div class="info-row"><span class="info-label">Paket Bitiş Tarihi:</span><span class="info-val">{{package_expiry_date}}</span></div>
        <div class="info-row"><span class="info-label">Yönetici E-Posta:</span><span class="info-val">{{login_email}}</span></div>
        <div class="info-row"><span class="info-label">İlk Giriş Şifresi:</span><span class="info-val" style="color: #38bdf8;">{{password}}</span></div>
      </div>

      <a href="{{portal_url}}" class="cta-btn">RECOrion Konsoluna Giriş Yapın &rarr;</a>

      <p style="font-size: 13px; color: #94a3b8; margin-top: 24px;">Güvenliğiniz için ilk oturum açışınızda şifrenizi profil ayarlarınızdan değiştirmenizi öneririz.</p>
    </div>
    <div class="footer">
      <strong>RECDx Dijital Dönüşüm & Yapay Zeka Teknolojileri A.Ş.</strong><br>
      Maslak Teknopark, Sarıyer / İstanbul | info@recdx.com | www.recdx.com
    </div>
  </div>
</body>
</html>"""

REMINDER_HTML = """<!DOCTYPE html>
<html lang="tr">
<head>
  <meta charset="UTF-8">
  <style>
    body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; background-color: #0b0f19; margin: 0; padding: 24px; color: #e2e8f0; }
    .email-container { max-width: 640px; margin: 0 auto; background: linear-gradient(180deg, #101628 0%, #0d1222 100%); border: 1px solid rgba(239, 68, 68, 0.4); border-radius: 20px; overflow: hidden; box-shadow: 0 20px 40px rgba(0,0,0,0.6); }
    .header { background: linear-gradient(135deg, #ef4444 0%, #b91c1c 50%, #7f1d1d 100%); padding: 32px 24px; text-align: center; }
    .logo-badge { display: inline-block; width: 48px; height: 48px; line-height: 48px; background: rgba(255,255,255,0.2); border-radius: 12px; font-weight: 900; font-size: 24px; color: #fff; margin-bottom: 12px; }
    .title { color: #ffffff; margin: 0; font-size: 22px; font-weight: 800; }
    .subtitle { color: rgba(255,255,255,0.85); font-size: 13px; margin-top: 6px; }
    .content { padding: 32px 28px; }
    .greeting { font-size: 17px; font-weight: 700; color: #f8fafc; margin-bottom: 14px; }
    .alert-box { background: rgba(239, 68, 68, 0.1); border: 1px solid rgba(239, 68, 68, 0.3); border-radius: 10px; padding: 14px 16px; color: #fca5a5; font-size: 13px; margin-bottom: 20px; line-height: 1.5; }
    .info-card { background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(239, 68, 68, 0.25); border-radius: 12px; padding: 18px 20px; margin: 20px 0; }
    .info-row { display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid rgba(255,255,255,0.05); font-size: 13px; }
    .info-row:last-child { border-bottom: none; }
    .info-label { color: #94a3b8; font-weight: 600; }
    .info-val { color: #f1f5f9; font-weight: 700; font-family: monospace; }
    .cta-btn { display: block; width: 85%; margin: 28px auto 12px; padding: 14px 20px; text-align: center; background: linear-gradient(135deg, #ef4444 0%, #b91c1c 100%); color: #ffffff; text-decoration: none; border-radius: 12px; font-weight: 800; font-size: 14px; box-shadow: 0 4px 18px rgba(239, 68, 68, 0.4); }
    .footer { text-align: center; padding: 24px; font-size: 11px; color: #64748b; border-top: 1px solid rgba(255,255,255,0.06); }
  </style>
</head>
<body>
  <div class="email-container">
    <div class="header">
      <div class="logo-badge">⏰</div>
      <h1 class="title">RECOrion Paket Süre Dolumu Hatırlatması</h1>
      <div class="subtitle">Kesintisiz Yapay Zeka Ajan Operasyonları İçin Paket Yenileme</div>
    </div>
    <div class="content">
      <div class="greeting">Sayın {{company_name}} Yetkilileri,</div>
      <div class="alert-box">
        ⚠️ <strong>Hatırlatma:</strong> Kurumunuza tahsis edilmiş olan <strong>{{plan_name}}</strong> paketinizin kiralama süresinin dolmasına <strong>{{days_remaining}} gün</strong> kalmıştır.
      </div>
      <p>Sisteme entegre yapay zeka ajanlarınızın görevlerini kesintisiz icra etmesi, şirket hafızasının korunması ve API servislerinin aksamaması için paket sürenizi uzatmanızı tavsiye ederiz.</p>

      <div class="info-card">
        <div class="info-row"><span class="info-label">Kayıtlı Kurum:</span><span class="info-val">{{company_name}}</span></div>
        <div class="info-row"><span class="info-label">Mevcut Paket:</span><span class="info-val" style="color: #f87171;">{{plan_name}}</span></div>
        <div class="info-row"><span class="info-label">Paket Bitiş Tarihi:</span><span class="info-val">{{expiry_date}}</span></div>
        <div class="info-row"><span class="info-label">Kalan Süre:</span><span class="info-val" style="color: #f59e0b;">{{days_remaining}} Gün</span></div>
      </div>

      <a href="{{renewal_url}}" class="cta-btn">Paket Süresini Uzat / Yenile &rarr;</a>

      <p style="font-size: 13px; color: #94a3b8; margin-top: 24px;">Sorularınız ve kurumsal paket yükseltme teklifleri için müşteri temsilcinizle her zaman iletişime geçebilirsiniz.</p>
    </div>
    <div class="footer">
      <strong>RECDx Dijital Dönüşüm & Yapay Zeka Teknolojileri A.Ş.</strong><br>
      Maslak Teknopark, Sarıyer / İstanbul | info@recdx.com | www.recdx.com
    </div>
  </div>
</body>
</html>"""

async def fix_records():
    print(f"Connecting to database: {DATABASE_URL.split('@')[-1]}")
    engine = create_async_engine(DATABASE_URL)
    async with engine.begin() as conn:
        # 1. Email Templates Güncelle
        print("1. Updating email_templates with proper Turkish UTF-8...")
        await conn.execute(text("""
            UPDATE email_templates
            SET name = :name,
                subject = :subject,
                html_content = :html,
                text_content = :txt,
                updated_at = NOW()
            WHERE code = 'WELCOME_CUSTOMER';
        """), {
            "name": "RECOrion Kurumsal Hoş Geldiniz Bilgilendirmesi",
            "subject": "RECOrion Platformuna Hoş Geldiniz - {{company_name}} Hesap ve Paket Bilgileriniz",
            "html": WELCOME_HTML,
            "txt": "Sayın {{company_name}} Yetkilileri, RECOrion {{plan_name}} kurumsal kiralama paketiniz başarıyla aktif edilmiştir. Giriş: {{portal_url}}"
        })

        await conn.execute(text("""
            UPDATE email_templates
            SET name = :name,
                subject = :subject,
                html_content = :html,
                text_content = :txt,
                updated_at = NOW()
            WHERE code = 'PACKAGE_EXPIRATION_REMINDER';
        """), {
            "name": "RECOrion Paket Süre Dolumu Hatırlatma Bildirimi",
            "subject": "Önemli: RECOrion Paketinizin Süresi Dolmak Üzere - {{company_name}} (Kalan: {{days_remaining}} Gün)",
            "html": REMINDER_HTML,
            "txt": "Sayın {{company_name}} Yetkilileri, RECOrion {{plan_name}} paketinizin dolumuna {{days_remaining}} gün kalmıştır (Bitiş: {{expiry_date}}). Kesintisiz operasyonlar için yenileyin: {{renewal_url}}"
        })

        # 2. Notification Schedules Güncelle
        print("2. Updating notification_schedules with proper Turkish UTF-8...")
        await conn.execute(text("""
            UPDATE notification_schedules
            SET name = 'Müşteri Kayıt Olduğunda Otomatik Hoşgeldiniz E-postası'
            WHERE trigger_type = 'ON_REGISTRATION' OR template_code = 'WELCOME_CUSTOMER';
        """))

        await conn.execute(text("""
            UPDATE notification_schedules
            SET name = 'Paket Bitişine 3 Ay Kala 15 Günde 1 Hatırlatıcı E-postası'
            WHERE trigger_type = 'BEFORE_EXPIRATION_INTERVAL' OR template_code = 'PACKAGE_EXPIRATION_REMINDER';
        """))

        # Kontrol edelim
        print("\n3. Verifying updated email_templates:")
        res = await conn.execute(text("SELECT code, name, subject FROM email_templates;"))
        for row in res.fetchall():
            print(f"  [{row[0]}] -> Name: {row[1]} | Subject: {row[2]}")

        print("\n4. Verifying updated notification_schedules:")
        res = await conn.execute(text("SELECT id, name, trigger_type, template_code FROM notification_schedules;"))
        for row in res.fetchall():
            print(f"  [{row[0]}] -> Name: {row[1]} | Trigger: {row[2]} | Template: {row[3]}")

    await engine.dispose()
    print("\n✓ TÜRKÇE KARAKTER ONARIMI BAŞARIYLA TAMAMLANDI!")

if __name__ == "__main__":
    asyncio.run(fix_records())
