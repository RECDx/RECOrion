"""Başvuruda eşleşen Odoo müşterisinin adı (onay ekranında yanlış eşleşme görünsün)

Revision ID: 0006
Revises: 0005
Create Date: 2026-10-20
"""
from alembic import op
import sqlalchemy as sa

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("tenant_leads", sa.Column("odoo_partner_name", sa.String(255)))


def downgrade() -> None:
    op.drop_column("tenant_leads", "odoo_partner_name")
