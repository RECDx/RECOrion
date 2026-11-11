"""İSTEK #741: platform proje şablonunun şirkete kopyası. Şirket kopyası hangi RECDx şablonundan alındığını tutar
(source_template_id); platform şablonu silinir/arşivlenirse kopya etkilenmez.

Revision ID: 0053
Revises: 0052
Create Date: 2026-11-11
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision = "0053"
down_revision = "0052"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("project_templates", sa.Column("source_template_id", UUID(as_uuid=True),
                                                 sa.ForeignKey("project_templates.id", ondelete="SET NULL")))


def downgrade() -> None:
    op.drop_column("project_templates", "source_template_id")
