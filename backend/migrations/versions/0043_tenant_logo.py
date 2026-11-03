"""İSTEK: şirketin resmi logosu (kayıt, Şirket Yönetimi, Ana Merkez).

Revision ID: 0043
Revises: 0042
"""
import sqlalchemy as sa
from alembic import op

revision = "0043"
down_revision = "0042"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("tenants", sa.Column("logo_key", sa.String(255)))
    op.add_column("tenants", sa.Column("logo_updated_at", sa.DateTime(timezone=True)))


def downgrade():
    op.drop_column("tenants", "logo_updated_at")
    op.drop_column("tenants", "logo_key")
