"""İSTEK #752: Teslimata göre doğrulama — iş adımının teslimatı ve doğrulama bilgisi (tür, yöntem, kanıt, ölçüm, kontrol listesi).

Revision ID: 0062
Revises: 0061
Create Date: 2026-11-17
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0062"
down_revision = "0061"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("tasks", sa.Column("deliverable", sa.Text))
    op.add_column("tasks", sa.Column("verification", postgresql.JSONB))


def downgrade() -> None:
    op.drop_column("tasks", "verification")
    op.drop_column("tasks", "deliverable")
