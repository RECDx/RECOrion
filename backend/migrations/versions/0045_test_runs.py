"""ADIM 16.2: Kod Çalıştırma Ortamı koşuları (AI Test Uzmanı projeyi dener).

Revision ID: 0045
Revises: 0044
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision = "0045"
down_revision = "0044"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "test_runs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("project_id", UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("task_id", UUID(as_uuid=True), sa.ForeignKey("tasks.id", ondelete="SET NULL")),
        sa.Column("ref", sa.String(120), nullable=False),
        sa.Column("commit_sha", sa.String(64)),
        sa.Column("status", sa.String(16), nullable=False, server_default="RUNNING"),
        sa.Column("passed", sa.Integer, nullable=False, server_default="0"),
        sa.Column("failed", sa.Integer, nullable=False, server_default="0"),
        sa.Column("skipped", sa.Integer, nullable=False, server_default="0"),
        sa.Column("result", JSONB),
        sa.Column("error", sa.Text),
        sa.Column("started_by_actor_id", UUID(as_uuid=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("finished_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_test_runs_project_id", "test_runs", ["project_id"])


def downgrade():
    op.drop_index("ix_test_runs_project_id", table_name="test_runs")
    op.drop_table("test_runs")
