"""Müşteri yaşam döngüsü: başvuru-şirket bağı, paket izinleri, Odoo ürün eşleşmesi, yeni mail şablonları

- tenant_leads: şirkete doğrudan bağ (tenant_id), yetkili adı ve şifre hash'i kendi
  alanlarında (önceden notes metnine gömülüydü), ret nedeni, inceleyen, Odoo senkron
  durumu, e-posta doğrulama zamanı, kaynak (WEB / ADMIN)
- plans: odoo_product_id (önceden kodda sabitti: 30/31/32) ve #241 paket izinleri
  (features içinde; mevcut değerler korunur, yalnızca eksik anahtarlar eklenir).
  PRO paketindeki katalogda olmayan 'whisper-large-v3' kaldırılır.
- email_templates.builder_blocks: sürükle-bırak editörün blok yapısı (düzenlemede HTML kaybolmasın)
- Yeni şablonlar: EMAIL_VERIFICATION_CODE, ACCOUNT_ACTIVATED, LEAD_RECEIVED, LEAD_REJECTED,
  PASSWORD_RESET, ADMIN_NEW_LEAD (yalnızca yoksa eklenir)
- "Müşteri Kayıt Olduğunda" zamanlaması WELCOME_CUSTOMER (açık şifre içeriyordu) yerine
  ACCOUNT_ACTIVATED şablonunu kullanır.

Revision ID: 0005
Revises: 0004
Create Date: 2026-10-20
"""
import json

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None

PLAN_DEFAULTS = {
    "STARTER": {"odoo_product_id": 30, "features": {
        "can_change_llm": False, "can_edit_role_prompt": False, "can_upload_title_documents": False,
        "max_documents_per_agent": 20, "ocr_enabled": False}},
    "PRO": {"odoo_product_id": 31, "features": {
        "can_change_llm": True, "can_edit_role_prompt": False, "can_upload_title_documents": False,
        "max_documents_per_agent": 100, "ocr_enabled": True}},
    "ENTERPRISE": {"odoo_product_id": 32, "features": {
        "can_change_llm": True, "can_edit_role_prompt": True, "can_upload_title_documents": True,
        "max_documents_per_agent": 1000, "ocr_enabled": True}},
}


def _email(title: str, body: str, button_label: str = "", button_var: str = "") -> str:
    """Tablo tabanlı, e-posta istemcileriyle uyumlu basit şablon (satır içi stiller)."""
    button = ""
    if button_label:
        button = (
            f'<tr><td style="padding:8px 32px 28px 32px;"><a href="{{{{{button_var}}}}}" '
            'style="display:inline-block;background:#5b3fd6;color:#ffffff;text-decoration:none;'
            f'font-weight:700;padding:12px 22px;border-radius:8px;font-size:15px;">{button_label}</a></td></tr>'
        )
    return (
        '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#f4f6fb;padding:24px 0;'
        'font-family:Segoe UI,Arial,sans-serif;"><tr><td align="center">'
        '<table role="presentation" width="600" cellpadding="0" cellspacing="0" style="max-width:600px;width:100%;'
        'background:#ffffff;border-radius:12px;overflow:hidden;border:1px solid #e2e8f0;">'
        '<tr><td style="background:linear-gradient(135deg,#7134e2,#146ceb);background-color:#5b3fd6;padding:22px 32px;'
        'color:#ffffff;font-size:20px;font-weight:800;">RECOrion</td></tr>'
        f'<tr><td style="padding:28px 32px 8px 32px;color:#0f172a;font-size:20px;font-weight:700;">{title}</td></tr>'
        f'<tr><td style="padding:8px 32px 16px 32px;color:#334155;font-size:15px;line-height:1.6;">{body}</td></tr>'
        f'{button}'
        '<tr><td style="padding:18px 32px;background:#f8fafc;color:#64748b;font-size:12px;border-top:1px solid #e2e8f0;">'
        'Bu e-posta RECOrion platformu tarafından otomatik gönderilmiştir. RECDx Teknoloji &amp; Dijital Dönüşüm Danışmanlığı</td></tr>'
        '</table></td></tr></table>'
    )


TEMPLATES = [
    ("EMAIL_VERIFICATION_CODE", "E-Posta Doğrulama Kodu", "RECOrion doğrulama kodunuz: {{code}}",
     _email("E-posta adresinizi doğrulayın",
            "Merhaba,<br><br>RECOrion başvurunuzu tamamlamak için doğrulama kodunuz:"
            '<div style="font-size:30px;font-weight:800;letter-spacing:8px;color:#5b3fd6;margin:18px 0;">{{code}}</div>'
            "Kod {{valid_minutes}} dakika geçerlidir. Bu işlemi siz yapmadıysanız bu e-postayı dikkate almayın."),
     ["code", "valid_minutes"]),
    ("LEAD_RECEIVED", "Başvuru Alındı (Müşteri)", "RECOrion başvurunuz alındı - {{company_name}}",
     _email("Başvurunuz alındı",
            "Sayın {{contact_name}},<br><br><strong>{{company_name}}</strong> adına <strong>{{plan_name}}</strong> paketi için "
            "yaptığınız başvuru alınmıştır. Sipariş referansınız: <strong>{{order_ref}}</strong>.<br><br>"
            "RECDx ekibi başvurunuzu inceledikten sonra hesabınız aktifleştirilecek ve size ayrıca e-posta ile bilgi verilecektir."),
     ["contact_name", "company_name", "plan_name", "order_ref"]),
    ("ADMIN_NEW_LEAD", "Yeni Başvuru Bildirimi (RECDx)", "[RECOrion] Yeni başvuru: {{company_name}} ({{plan_name}})",
     _email("Yeni müşteri başvurusu",
            "<strong>{{company_name}}</strong> web sitesi üzerinden <strong>{{plan_name}}</strong> paketi için başvurdu.<br><br>"
            "Yetkili: {{contact_name}} &lt;{{contact_email}}&gt;<br>Telefon: {{phone}}<br>Sipariş: {{order_ref}}<br><br>"
            "Başvuruyu Süper Admin konsolundaki Başvuru Onay Durum ekranından inceleyebilirsiniz.",
            "Başvuruyu İncele", "review_url"),
     ["company_name", "plan_name", "contact_name", "contact_email", "phone", "order_ref", "review_url"]),
    ("ACCOUNT_ACTIVATED", "Hesap Aktivasyonu", "RECOrion hesabınız aktif - {{company_name}}",
     _email("Hesabınız aktifleştirildi",
            "Sayın {{contact_name}},<br><br><strong>{{company_name}}</strong> için <strong>{{plan_name}}</strong> paketiniz "
            "aktifleştirilmiştir. Paket bitiş tarihi: <strong>{{package_expiry_date}}</strong>.<br><br>"
            "Kullanıcı adınız: <strong>{{login_email}}</strong><br>{{password_instruction}}",
            "{{action_label}}", "action_url"),
     ["contact_name", "company_name", "plan_name", "package_expiry_date", "login_email", "password_instruction", "action_label", "action_url"]),
    ("LEAD_REJECTED", "Başvuru Sonucu (Ret)", "RECOrion başvurunuz hakkında - {{company_name}}",
     _email("Başvurunuz hakkında",
            "Sayın {{contact_name}},<br><br><strong>{{company_name}}</strong> adına yaptığınız başvuru bu aşamada onaylanamamıştır."
            "<br><br>Açıklama: {{reason}}<br><br>Sorularınız için info@recdx.com adresinden bize ulaşabilirsiniz."),
     ["contact_name", "company_name", "reason"]),
    ("PASSWORD_RESET", "Şifre Belirleme / Sıfırlama", "RECOrion şifre belirleme bağlantınız",
     _email("Şifrenizi belirleyin",
            "Merhaba {{contact_name}},<br><br>RECOrion hesabınız için şifre belirleme talebi aldık. Aşağıdaki bağlantı "
            "{{valid_hours}} saat geçerlidir. Bu talebi siz yapmadıysanız bu e-postayı dikkate almayın; şifreniz değişmez.",
            "Şifremi Belirle", "reset_url"),
     ["contact_name", "reset_url", "valid_hours"]),
]


def upgrade() -> None:
    # --- tenant_leads ---
    op.add_column("tenant_leads", sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="SET NULL"), nullable=True))
    op.add_column("tenant_leads", sa.Column("contact_name", sa.String(255)))
    op.add_column("tenant_leads", sa.Column("password_hash", sa.String(255)))
    op.add_column("tenant_leads", sa.Column("rejection_reason", sa.Text))
    op.add_column("tenant_leads", sa.Column("reviewed_by_actor_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("tenant_leads", sa.Column("reviewed_at", sa.DateTime(timezone=True)))
    op.add_column("tenant_leads", sa.Column("odoo_sync_status", sa.String(32), server_default="PENDING"))
    op.add_column("tenant_leads", sa.Column("odoo_sync_error", sa.Text))
    op.add_column("tenant_leads", sa.Column("email_verified_at", sa.DateTime(timezone=True)))
    op.add_column("tenant_leads", sa.Column("source", sa.String(16), server_default="WEB"))
    op.create_index("ix_tenant_leads_tenant_id", "tenant_leads", ["tenant_id"])

    # --- plans ---
    op.add_column("plans", sa.Column("odoo_product_id", sa.Integer, nullable=True))
    bind = op.get_bind()
    rows = bind.execute(sa.text("SELECT id, code, features, allowed_models FROM plans")).mappings().all()
    for r in rows:
        d = PLAN_DEFAULTS.get(r["code"])
        features = dict(r["features"] or {})
        if d:
            for k, v in d["features"].items():
                features.setdefault(k, v)
        models = [m for m in (r["allowed_models"] or []) if m != "whisper-large-v3"]
        bind.execute(
            sa.text("UPDATE plans SET features = CAST(:f AS jsonb), allowed_models = CAST(:m AS jsonb), "
                    "odoo_product_id = COALESCE(odoo_product_id, :pid) WHERE id = :id"),
            {"f": json.dumps(features), "m": json.dumps(models), "pid": d["odoo_product_id"] if d else None, "id": r["id"]},
        )

    # --- email_templates ---
    op.add_column("email_templates", sa.Column("builder_blocks", postgresql.JSONB, nullable=True))
    for code, name, subject, html, variables in TEMPLATES:
        bind.execute(
            sa.text("INSERT INTO email_templates (code, name, subject, html_content, variables, is_active) "
                    "VALUES (:c, :n, :s, :h, CAST(:v AS jsonb), TRUE) ON CONFLICT (code) DO NOTHING"),
            {"c": code, "n": name, "s": subject, "h": html, "v": json.dumps(variables)},
        )

    bind.execute(sa.text(
        "UPDATE notification_schedules SET template_code = 'ACCOUNT_ACTIVATED' "
        "WHERE trigger_type = 'ON_REGISTRATION' AND template_code = 'WELCOME_CUSTOMER'"
    ))


def downgrade() -> None:
    op.drop_column("email_templates", "builder_blocks")
    op.drop_column("plans", "odoo_product_id")
    op.drop_index("ix_tenant_leads_tenant_id", table_name="tenant_leads")
    for col in ("source", "email_verified_at", "odoo_sync_error", "odoo_sync_status", "reviewed_at",
                "reviewed_by_actor_id", "rejection_reason", "password_hash", "contact_name", "tenant_id"):
        op.drop_column("tenant_leads", col)
