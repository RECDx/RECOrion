"""Kullanıcı daveti e-postası (#635, F21): şirket kullanıcı eklediğinde kişiye şifre belirleme bağlantısı gider.

Revision ID: 0048
Revises: 0047
"""
import json

import sqlalchemy as sa
from alembic import op

revision = "0048"
down_revision = "0047"
branch_labels = None
depends_on = None


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


def upgrade():
    html = _email("RECOrion hesabınız oluşturuldu",
                  "Merhaba {{contact_name}},<br><br><strong>{{company_name}}</strong> sizi RECOrion'a kullanıcı olarak ekledi. "
                  "Kullanıcı adınız: <strong>{{email}}</strong>.<br><br>Aşağıdaki bağlantıdan şifrenizi belirleyerek giriş yapabilirsiniz; "
                  "bağlantı {{valid_hours}} saat geçerlidir. Yöneticiniz size bir başlangıç şifresi ilettiyse onunla da giriş yapabilirsiniz.",
                  "Şifremi Belirle", "reset_url")
    op.get_bind().execute(
        sa.text("INSERT INTO email_templates (code, name, subject, html_content, variables, is_active) "
                "VALUES ('USER_INVITED', 'Kullanıcı Daveti', 'RECOrion hesabınız oluşturuldu', :h, CAST(:v AS jsonb), TRUE) "
                "ON CONFLICT (code) DO NOTHING"),
        {"h": html, "v": json.dumps(["contact_name", "company_name", "email", "reset_url", "valid_hours"])})


def downgrade():
    op.execute("DELETE FROM email_templates WHERE code = 'USER_INVITED'")
