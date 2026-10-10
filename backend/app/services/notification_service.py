import os
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import Dict, Any, List

logger = logging.getLogger("recorion_notification")

# Test ve denetim için gönderilen maillerin in-memory kaydı
SENT_EMAILS_LOG: List[Dict[str, Any]] = []

class NotificationService:
    """
    RECOrion Satın Alma & Kiralama Talepleri İçin Profesyonel E-Posta Bildirim Servisi.
    """
    ADMIN_NOTIFICATION_EMAIL = os.getenv("ADMIN_NOTIFICATION_EMAIL", "info@recdx.com")

    @classmethod
    def get_smtp_config(cls) -> Dict[str, Any]:
        return {
            "host": os.getenv("SMTP_HOST") or "mail.recdx.com",
            "port": int(os.getenv("SMTP_PORT") or "587"),
            "user": os.getenv("SMTP_USER") or "info@recdx.com",
            "password": os.getenv("SMTP_PASSWORD") or "J18BG&d@",
            "from_email": os.getenv("FROM_EMAIL") or "info@recdx.com",
        }

    @classmethod
    def _send_email(cls, to_email: str, subject: str, html_body: str, text_body: str) -> bool:
        cfg = cls.get_smtp_config()
        record = {
            "timestamp": datetime.utcnow().isoformat(),
            "to": to_email,
            "subject": subject,
            "html": html_body,
            "text": text_body,
            "delivered": False
        }

        # 1. Gerçek SMTP ile Gönderim (mail.recdx.com)
        if cfg["host"] and cfg["user"]:
            try:
                msg = MIMEMultipart("alternative")
                msg["Subject"] = subject
                msg["From"] = f"RECOrion <{cfg['from_email']}>"
                msg["To"] = to_email

                part1 = MIMEText(text_body, "plain", "utf-8")
                part2 = MIMEText(html_body, "html", "utf-8")
                msg.attach(part1)
                msg.attach(part2)

                with smtplib.SMTP(cfg["host"], cfg["port"], timeout=15) as server:
                    try:
                        server.starttls()
                    except Exception:
                        pass
                    server.login(cfg["user"], cfg["password"])
                    server.sendmail(cfg["from_email"], [to_email], msg.as_string())
                
                record["delivered"] = True
                logger.info(f"✓ E-posta SMTP üzerinden başarıyla teslim edildi: {to_email} - Konu: {subject}")
                SENT_EMAILS_LOG.append(record)
                return True
            except Exception as e:
                logger.error(f"SMTP gönderim hatası ({to_email}): {e}. Odoo yedek kanalı deneniyor...")
                record["smtp_error"] = str(e)

        # 2. Odoo Yedek Kanalı (SMTP hata verirse Odoo mail.mail üzerinden gönder)
        try:
            from app.services.odoo_service import OdooService
            odoo_cfg = OdooService.get_config()
            if odoo_cfg["url"] and odoo_cfg["user"]:
                common, uid, models = OdooService._get_connection()
                if uid and models:
                    mail_vals = {
                        "email_from": cfg["from_email"],
                        "email_to": to_email,
                        "subject": subject,
                        "body_html": html_body,
                    }
                    mail_id = models.execute_kw(odoo_cfg["db"], uid, odoo_cfg["password"], "mail.mail", "create", [mail_vals])
                    models.execute_kw(odoo_cfg["db"], uid, odoo_cfg["password"], "mail.mail", "send", [[mail_id]])
                    record["delivered"] = True
                    logger.info(f"✓ E-posta Odoo yedek kanalı üzerinden başarıyla gönderildi: {to_email}")
                    SENT_EMAILS_LOG.append(record)
                    return True
        except Exception as odoo_err:
            logger.error(f"Odoo e-posta gönderim hatası: {odoo_err}")
            record["odoo_error"] = str(odoo_err)

        SENT_EMAILS_LOG.append(record)
        return False

    @classmethod
    def render_and_send_template(
        cls, 
        to_email: str, 
        template: Any,
        context: Dict[str, Any]
    ) -> bool:
        """
        Şablon içerisindeki {{degisken}} alanlarını context ile dinamik olarak doldurur ve gönderir (Madde 1 & 2).
        """
        if not to_email:
            return False

        subject = template.subject if hasattr(template, 'subject') else template.get('subject', '')
        html = template.html_content if hasattr(template, 'html_content') else template.get('html_content', '')
        text = template.text_content if hasattr(template, 'text_content') else template.get('text_content', '')

        for k, v in context.items():
            val_str = str(v) if v is not None else ""
            placeholder = f"{{{{{k}}}}}"
            subject = subject.replace(placeholder, val_str)
            html = html.replace(placeholder, val_str)
            if text:
                text = text.replace(placeholder, val_str)

        if not text:
            import re
            text = re.sub(r'<[^>]+>', ' ', html)

        return cls._send_email(to_email, subject, html, text)

    @classmethod
    def send_admin_new_customer_notification(cls, lead: Dict[str, Any]) -> bool:
        """
        Yeni müşteri geldiğinde info@recdx.com adresine detaylı bildirim gönderir.
        """
        subject = f"[RECOrion Satın Alma] Yeni Müşteri Geldi: {lead.get('company_name')} ({lead.get('plan_code', 'BELİRTİLMEDİ')})"
        
        nace_str = ", ".join(lead.get("nace_codes", []))
        
        text_body = f"""RECDx Yönetim Ekibinin Dikkatine,

RECOrion resmi web sitesi üzerinden yeni bir müşteri satın alma / kiralama talebinde bulunmuştur.

MÜŞTERİ BİLGİLERİ:
- Şirket Ünvanı: {lead.get('company_name')}
- Yetkili Kişi: {lead.get('contact_name')}
- E-Posta: {lead.get('contact_email')}
- Telefon: {lead.get('phone')}
- Web Adresi: {lead.get('website', '-')}
- Adres: {lead.get('address', '-')}
- Vergi No: {lead.get('tax_id', '-')}

TALEP EDİLEN PAKET:
- Paket: {lead.get('plan_name')} ({lead.get('plan_code')})
- Aylık Fiyat: {lead.get('monthly_price')} {lead.get('currency', 'TRY')}

SEKTÖR VE NACE ALANLARI:
- NACE Kodları: {nace_str}

OTOMATİK OLUŞTURULAN MANİFESTO ÖZETİ:
{lead.get('generated_manifesto', '')[:300]}...

Lütfen en kısa sürede müşteri ile irtibata geçiniz.
RECOrion Otomasyon Sistemi
"""

        html_body = f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="font-family: Arial, sans-serif; background-color: #0d1117; color: #c9d1d9; padding: 20px;">
  <div style="max-width: 650px; margin: auto; background-color: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 25px;">
    <h2 style="color: #58a6ff; margin-top: 0;">🚀 RECOrion Yeni Müşteri Kiralama Talebi</h2>
    <p>Resmi web sitesi üzerinden yeni bir kurumsal satın alma/kiralama talebi alınmıştır.</p>
    
    <table style="width: 100%; border-collapse: collapse; margin-top: 15px;">
      <tr><td style="padding: 8px; color: #8b949e; width: 140px;"><b>Şirket Ünvanı:</b></td><td style="padding: 8px; color: #f0f6fc;"><b>{lead.get('company_name')}</b></td></tr>
      <tr><td style="padding: 8px; color: #8b949e;"><b>Yetkili:</b></td><td style="padding: 8px;">{lead.get('contact_name')} ({lead.get('contact_email')})</td></tr>
      <tr><td style="padding: 8px; color: #8b949e;"><b>Telefon:</b></td><td style="padding: 8px;">{lead.get('phone')}</td></tr>
      <tr><td style="padding: 8px; color: #8b949e;"><b>Web:</b></td><td style="padding: 8px;">{lead.get('website', '-')}</td></tr>
      <tr><td style="padding: 8px; color: #8b949e;"><b>Seçilen Paket:</b></td><td style="padding: 8px; color: #3fb950;"><b>{lead.get('plan_name')} ({lead.get('plan_code')}) - {lead.get('monthly_price')} {lead.get('currency', 'TRY')}/Ay</b></td></tr>
      <tr><td style="padding: 8px; color: #8b949e;"><b>NACE Kodları:</b></td><td style="padding: 8px;">{nace_str}</td></tr>
    </table>

    <div style="margin-top: 20px; padding: 15px; background-color: #0d1117; border-left: 4px solid #58a6ff; border-radius: 4px;">
      <h4 style="margin: 0 0 10px 0; color: #79c0ff;">AI Sektör Manifestosu Özeti:</h4>
      <pre style="white-space: pre-wrap; font-family: monospace; font-size: 12px; color: #8b949e; margin: 0;">{lead.get('generated_manifesto', '')[:400]}...</pre>
    </div>

    <p style="font-size: 12px; color: #8b949e; margin-top: 25px;">Bu e-posta RECOrion Otomasyon Çekirdeği tarafından otomatik olarak oluşturulmuştur.</p>
  </div>
</body>
</html>
"""
        return cls._send_email(cls.ADMIN_NOTIFICATION_EMAIL, subject, html_body, text_body)

    @classmethod
    def send_customer_welcome_notification(cls, lead: Dict[str, Any]) -> bool:
        """
        Müşterinin başvuru esnasında girdiği e-posta adresine profesyonel geri bildirim gönderir.
        """
        to_email = lead.get("contact_email")
        if not to_email:
            return False

        subject = f"RECOrion Yapay Zeka Ekosistemine Hoş Geldiniz - Kiralama Talebiniz Alındı ({lead.get('company_name')})"

        text_body = f"""Sayın {lead.get('contact_name')},

{lead.get('company_name')} adına RECOrion Yapay Zeka İşletim Sistemi için gerçekleştirmiş olduğunuz {lead.get('plan_name')} ({lead.get('plan_code')}) kiralama talebiniz başarıyla alınmıştır.

Yapay zeka operasyon uzmanlarımız ve kurumsal müşteri temsilcimiz en kısa süre içerisinde şirketinizle iletişime geçerek ortam aktivasyonunuzu tamamlayacaktır.

Şirketiniz için NACE faaliyet alanlarınız doğrultusunda AI tarafından oluşturulan "Kurumsal Yapay Zeka Manifestosu" aşağıda yer almaktadır:

--------------------------------------------------------------------------------
{lead.get('generated_manifesto', '')}
--------------------------------------------------------------------------------

Hesabınız için belirlediğiniz şifreniz güvenli biçimde şifrelenerek kayıt altına alınmıştır.

Her türlü soru ve talebiniz için info@recdx.com üzerinden bizimle doğrudan iletişime geçebilirsiniz.

Saygılarımızla,
RECDx Bilişim Teknolojileri & RECOrion Ekibi
https://recdx.com | info@recdx.com
"""

        html_body = f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background-color: #090d16; color: #e6edf3; padding: 25px;">
  <div style="max-width: 650px; margin: auto; background-color: #121826; border: 1px solid #233044; border-radius: 12px; overflow: hidden; box-shadow: 0 10px 30px rgba(0,0,0,0.5);">
    <div style="background: linear-gradient(135deg, #1f6feb 0%, #388bfd 100%); padding: 30px; text-align: center;">
      <h1 style="color: #ffffff; margin: 0; font-size: 24px; font-weight: 700; letter-spacing: 1px;">RECOrion</h1>
      <p style="color: #e6edf3; margin: 8px 0 0 0; font-size: 14px; opacity: 0.9;">Otonom Kurumsal Yapay Zeka Ekosistemi</p>
    </div>

    <div style="padding: 30px;">
      <h2 style="color: #58a6ff; font-size: 20px; margin-top: 0;">Sayın {lead.get('contact_name')},</h2>
      <p style="font-size: 15px; line-height: 1.6; color: #c9d1d9;">
        <b>{lead.get('company_name')}</b> adına yapmış olduğunuz 
        <span style="color: #3fb950; font-weight: bold;">{lead.get('plan_name')} ({lead.get('plan_code')})</span> 
        kiralama talebiniz başarıyla alınmıştır.
      </p>
      
      <div style="background-color: #1b2333; border: 1px solid #303e54; border-radius: 8px; padding: 18px; margin: 20px 0;">
        <h4 style="margin: 0 0 10px 0; color: #79c0ff; font-size: 14px; text-transform: uppercase;">Talep Özeti</h4>
        <ul style="margin: 0; padding-left: 20px; font-size: 14px; color: #8b949e; line-height: 1.7;">
          <li><b>Şirket:</b> {lead.get('company_name')}</li>
          <li><b>Telefon:</b> {lead.get('phone')}</li>
          <li><b>Aylık Kiralama:</b> {lead.get('monthly_price')} {lead.get('currency', 'TRY')}</li>
          <li><b>Güvenlik:</b> Giriş şifreniz güvenli şifreleme ile muhafaza edilmektedir.</li>
        </ul>
      </div>

      <p style="font-size: 14px; line-height: 1.6; color: #8b949e;">
        İlgili müşteri temsilcisi arkadaşlarımız şirketinizin NACE faaliyet kodlarına uygun ortam provizyonunu başlatmak üzere en kısa sürede sizinle irtibata geçecektir.
      </p>

      <div style="margin-top: 25px; padding: 20px; background-color: #0d1117; border-left: 4px solid #3fb950; border-radius: 6px;">
        <h3 style="margin: 0 0 12px 0; color: #3fb950; font-size: 15px;">📜 Şirketiniz İçin Üretilen Kurumsal Yapay Zeka Manifestosu</h3>
        <pre style="white-space: pre-wrap; font-family: monospace; font-size: 12px; color: #c9d1d9; margin: 0; line-height: 1.5; max-height: 250px; overflow-y: auto;">{lead.get('generated_manifesto', '')}</pre>
      </div>

      <div style="border-top: 1px solid #21262d; margin-top: 30px; padding-top: 20px; font-size: 13px; color: #8b949e; text-align: center;">
        <p style="margin: 0 0 5px 0;">Sorularınız için: <a href="mailto:info@recdx.com" style="color: #58a6ff; text-decoration: none;">info@recdx.com</a></p>
        <p style="margin: 0;">© 2026 RECDx Bilişim Teknolojileri. Tüm hakları saklıdır.</p>
      </div>
    </div>
  </div>
</body>
</html>
"""
        return cls._send_email(to_email, subject, html_body, text_body)

    @classmethod
    def send_customer_account_activated_notification(cls, data: Dict[str, Any]) -> bool:
        """
        RECDx Genel Yetkilisi (Süper Admin) ödemeyi onaylayıp hesabı aktive ettiğinde (A.9 maddesi),
        müşteriye hesabının açıldığını, kullanıcı adını ve şifresini içeren aktivasyon e-postasını gönderir.
        """
        to_email = data.get("contact_email")
        if not to_email:
            return False

        company_name = data.get("company_name", "Kurum")
        contact_name = data.get("contact_name", "Yetkili")
        login_email = data.get("login_email", to_email)
        password = data.get("password", "Kayıt sırasında belirlediğiniz şifreniz")
        plan_name = data.get("plan_name", "RECOrion Paketi")
        odoo_order_name = data.get("odoo_order_name", "S00000")
        login_url = data.get("login_url", "http://localhost:5173/")

        subject = f"🎉 RECOrion Hesabınız Aktif Edildi - Kurumsal Giriş Bilgileriniz ({company_name})"

        text_body = f"""Sayın {contact_name},

{company_name} adına gerçekleştirdiğiniz RECOrion {plan_name} aboneliğinizin ödemesi RECDx yetkilimiz tarafından doğrulanmış ve hesabınız başarıyla AKTİF EDİLMİŞTİR!

Odoo Sipariş No: {odoo_order_name}

KURUMSAL GİRİŞ BİLGİLERİNİZ:
--------------------------------------------------------------------------------
Giriş Adresi   : {login_url}
Kullanıcı Adı  : {login_email}
Şifreniz       : {password}
Abonelik Paketi: {plan_name}
--------------------------------------------------------------------------------

Hemen giriş yaparak kurumsal yapay zeka personellerinizi ve projelerinizi yönetmeye başlayabilirsiniz.
Güvenliğiniz için ilk girişinizden sonra şifrenizi profil ayarlarınızdan değiştirebilirsiniz.

Teknik destek ve operasyonel sorularınız için info@recdx.com adresinden bize 7/24 ulaşabilirsiniz.

Başarılar dileriz,
RECDx Bilişim Teknolojileri & RECOrion Ekibi
https://recdx.com | info@recdx.com
"""

        html_body = f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background-color: #090d16; color: #e6edf3; padding: 25px;">
  <div style="max-width: 650px; margin: auto; background-color: #121826; border: 1px solid #233044; border-radius: 12px; overflow: hidden; box-shadow: 0 10px 30px rgba(0,0,0,0.5);">
    <div style="background: linear-gradient(135deg, #10b981 0%, #059669 100%); padding: 30px; text-align: center;">
      <h1 style="color: #ffffff; margin: 0; font-size: 24px; font-weight: 700; letter-spacing: 1px;">🎉 Hesabınız Aktif Edildi</h1>
      <p style="color: #e6edf3; margin: 8px 0 0 0; font-size: 14px; opacity: 0.95;">RECOrion Otonom Kurumsal Yapay Zeka Ekosistemi</p>
    </div>

    <div style="padding: 30px;">
      <h2 style="color: #34d399; font-size: 20px; margin-top: 0;">Sayın {contact_name},</h2>
      <p style="font-size: 15px; line-height: 1.6; color: #c9d1d9;">
        <b>{company_name}</b> adına talep ettiğiniz <span style="color: #38bdf8; font-weight: bold;">{plan_name}</span> aboneliğinizin ödemesi RECDx yetkilimiz tarafından incelenerek onaylanmıştır.
        Yapay zeka çalışma alanınız ve şirket ortamınız kullanıma açılmıştır!
      </p>

      <div style="background-color: #1a2234; border: 1px solid #10b981; border-radius: 10px; padding: 20px; margin: 25px 0;">
        <h3 style="margin: 0 0 15px 0; color: #34d399; font-size: 15px; text-transform: uppercase; letter-spacing: 0.5px;">🔐 Kurumsal Giriş Bilgileriniz</h3>
        <table style="width: 100%; border-collapse: collapse; font-size: 14px;">
          <tr>
            <td style="padding: 8px 0; color: #94a3b8; width: 140px;"><b>Giriş Adresi:</b></td>
            <td style="padding: 8px 0;"><a href="{login_url}" style="color: #38bdf8; text-decoration: none; font-weight: 600;">{login_url}</a></td>
          </tr>
          <tr>
            <td style="padding: 8px 0; color: #94a3b8;"><b>Kullanıcı Adı:</b></td>
            <td style="padding: 8px 0; color: #f8fafc; font-weight: 600;">{login_email}</td>
          </tr>
          <tr>
            <td style="padding: 8px 0; color: #94a3b8;"><b>Şifreniz:</b></td>
            <td style="padding: 8px 0; color: #fbbf24; font-family: monospace; font-size: 16px; font-weight: bold;">{password}</td>
          </tr>
          <tr>
            <td style="padding: 8px 0; color: #94a3b8;"><b>Odoo Sipariş No:</b></td>
            <td style="padding: 8px 0; color: #94a3b8;">{odoo_order_name}</td>
          </tr>
        </table>
      </div>

      <div style="text-align: center; margin: 30px 0;">
        <a href="{login_url}" style="display: inline-block; background: linear-gradient(135deg, #6366f1 0%, #06b6d4 100%); color: #ffffff; text-decoration: none; padding: 14px 32px; border-radius: 8px; font-weight: bold; font-size: 15px; box-shadow: 0 4px 15px rgba(99, 102, 241, 0.4);">
          🚀 RECOrion Çalışma Alanına Giriş Yap →
        </a>
      </div>

      <p style="font-size: 13px; line-height: 1.6; color: #94a3b8;">
        ℹ️ <i>Güvenliğiniz için sisteme giriş yaptıktan sonra şifrenizi profil ayarlarınızdan değiştirebilirsiniz.</i>
      </p>

      <div style="border-top: 1px solid #21262d; margin-top: 30px; padding-top: 20px; font-size: 13px; color: #8b949e; text-align: center;">
        <p style="margin: 0 0 5px 0;">Destek: <a href="mailto:info@recdx.com" style="color: #58a6ff; text-decoration: none;">info@recdx.com</a></p>
        <p style="margin: 0;">© 2026 RECDx Bilişim Teknolojileri. Tüm hakları saklıdır.</p>
      </div>
    </div>
  </div>
</body>
</html>
"""
        return cls._send_email(to_email, subject, html_body, text_body)
