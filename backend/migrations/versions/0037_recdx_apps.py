"""RECDx uygulama tercihleri (ADIM 13.1)

Müşteri paket satın alırken (ve sonra Şirket Yönetimi'nde) "Odoo'nuz var mı; RECQmind / RECSlip kullanıyor musunuz,
kullanmak ister misiniz?" sorularını yanıtlar. Yanıt başvuruda (tenant_leads.preferences) ve şirkette
(tenants.settings["recdx_apps"]) tutulur. integration_catalog.requires_app: kart yalnızca şirket o uygulamayı
kullanıyorsa ve Odoo'su varsa görünür (RECQmind, RECSlip kartları).

Revision ID: 0037
Revises: 0036
Create Date: 2026-10-25
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision = "0037"
down_revision = "0036"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("tenant_leads", sa.Column("preferences", JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")))
    op.add_column("integration_catalog", sa.Column("requires_app", sa.String(32)))


def downgrade() -> None:
    op.drop_column("integration_catalog", "requires_app")
    op.drop_column("tenant_leads", "preferences")
