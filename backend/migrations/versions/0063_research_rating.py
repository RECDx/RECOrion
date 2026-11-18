"""İSTEK #753: Beyin AI öğrenme etiketleri — web araştırmasının faydası (yönetici tek tıkla değerlendirir).

Revision ID: 0063
Revises: 0062
Create Date: 2026-11-18
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0063"
down_revision = "0062"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("web_research", sa.Column("rating", sa.String(12)))  # USEFUL, PARTIAL, USELESS
    op.add_column("web_research", sa.Column("rated_by", postgresql.UUID(as_uuid=True)))
    op.add_column("web_research", sa.Column("rated_at", sa.DateTime(timezone=True)))


def downgrade() -> None:
    op.drop_column("web_research", "rated_at")
    op.drop_column("web_research", "rated_by")
    op.drop_column("web_research", "rating")
