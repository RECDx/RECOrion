"""İSTEK #754: Beyin AI deneme seti koşuları.

Revision ID: 0064
Revises: 0063
Create Date: 2026-11-18
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0064"
down_revision = "0063"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "brain_bench_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("status", sa.String(16), nullable=False, server_default="RUNNING"),
        sa.Column("label", sa.String(200)),
        sa.Column("case_codes", postgresql.JSONB, nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("results", postgresql.JSONB, nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("total", sa.Numeric(5, 1)),
        sa.Column("error", sa.Text),
        sa.Column("started_by", postgresql.UUID(as_uuid=True)),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("finished_at", sa.DateTime(timezone=True)),
    )


def downgrade() -> None:
    op.drop_table("brain_bench_runs")
