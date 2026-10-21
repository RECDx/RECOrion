"""Proje ekleri katmanı (ADIM 5.5, Odoo #274)

agent_documents: project_id (PROJECT katmanı) ve promoted_at (proje kapanınca Kurum Hafızasına aktarıldı).

Revision ID: 0011
Revises: 0010
Create Date: 2026-10-21
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0011"
down_revision = "0010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("agent_documents", sa.Column("project_id", postgresql.UUID(as_uuid=True),
                                               sa.ForeignKey("projects.id", ondelete="CASCADE")))
    op.add_column("agent_documents", sa.Column("promoted_at", sa.DateTime(timezone=True)))
    op.create_index("ix_agent_documents_project", "agent_documents", ["project_id"])


def downgrade() -> None:
    op.drop_index("ix_agent_documents_project", "agent_documents")
    op.drop_column("agent_documents", "promoted_at")
    op.drop_column("agent_documents", "project_id")
