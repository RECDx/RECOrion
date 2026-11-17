"""İSTEK #751: Sektör bilgi paketleri — Merkez'de sürümlenen, uzman kontrolüyle yayımlanan iş kolu paketleri.

Revision ID: 0061
Revises: 0060
Create Date: 2026-11-17
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0061"
down_revision = "0060"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "sector_packs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("code", sa.String(40), nullable=False, unique=True),
        sa.Column("title", sa.String(120), nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("sector_codes", postgresql.JSONB, nullable=False, server_default="[]"),
        sa.Column("keywords", postgresql.JSONB, nullable=False, server_default="[]"),
        sa.Column("draft", postgresql.JSONB, nullable=False, server_default="{}"),
        sa.Column("published", postgresql.JSONB),
        sa.Column("draft_updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("sector_packs")
