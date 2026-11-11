"""İSTEK #740: otomasyonla açılan iş bitince sonucun e-postayla iletilmesi için şablon (AUTOMATION_RESULT).
Değişkenler HTML kaçışıyla yerleşir (notification_service); sonuç metni <pre> içinde satırları korur.

Revision ID: 0057
Revises: 0056
Create Date: 2026-11-11
"""
import json

import sqlalchemy as sa
from alembic import op

revision = "0057"
down_revision = "0056"
branch_labels = None
depends_on = None

HTML = ("<p>Merhaba {{contact_name}},</p><p><strong>{{rule_name}}</strong> otomasyonunun açtığı <strong>{{project_name}}</strong> "
        "tamamlandı. Sonuç:</p><pre style=\"white-space:pre-wrap;font-family:inherit\">{{result_text}}</pre>"
        "<p><a href=\"{{project_url}}\">Ayrıntıyı RECOrion'da aç</a></p>")


def upgrade() -> None:
    op.get_bind().execute(
        sa.text("INSERT INTO email_templates (code, name, subject, html_content, variables, is_active) "
                "VALUES (:c, :n, :s, :h, CAST(:v AS jsonb), TRUE) ON CONFLICT (code) DO NOTHING"),
        {"c": "AUTOMATION_RESULT", "n": "Otomasyon Sonucu", "s": "{{project_name}} — sonuç", "h": HTML,
         "v": json.dumps(["contact_name", "rule_name", "project_name", "result_text", "project_url"])})


def downgrade() -> None:
    op.execute("DELETE FROM email_templates WHERE code = 'AUTOMATION_RESULT'")
