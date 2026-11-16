"""İSTEK #750: Beyin AI web derin araştırması — yönetici onaylı, tahmini / en fazla kredi gösterimli araştırma işleri.

Revision ID: 0060
Revises: 0059
Create Date: 2026-11-17
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0060"
down_revision = "0059"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "web_research",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="CASCADE")),
        sa.Column("requested_by", postgresql.UUID(as_uuid=True)),
        sa.Column("question", sa.Text, nullable=False),
        sa.Column("masked_question", sa.Text, nullable=False),
        sa.Column("pii", postgresql.JSONB),
        sa.Column("depth", sa.String(16), nullable=False),
        sa.Column("origin", sa.String(16), nullable=False, server_default="MANAGER"),  # MANAGER, BRAIN_SUGGESTION
        sa.Column("status", sa.String(16), nullable=False, server_default="RUNNING"),  # RUNNING, DONE, FAILED, CANCELLED
        sa.Column("stage", sa.String(16)),  # PLANNING, SEARCHING, READING, SYNTHESIZING
        sa.Column("estimated_credits", sa.Numeric(14, 4)),
        sa.Column("max_credits", sa.Numeric(14, 4), nullable=False),
        sa.Column("spent_credits", sa.Numeric(14, 4), nullable=False, server_default="0"),
        sa.Column("result", postgresql.JSONB),
        sa.Column("error", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("finished_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_web_research_tenant_id", "web_research", ["tenant_id"])
    op.create_index("ix_web_research_project_id", "web_research", ["project_id"])


def downgrade() -> None:
    op.drop_table("web_research")
