"""Proje kod deposunun müşterinin GitHub/Gitea hesabına yansıtılması (ADIM 10.3, Odoo #297)

mirror_connection_id: şirketin GitHub/Gitea bağlantısı (token kimlik kasasında); bağlantı silinirse yansıtma ayarı boşalır.
mirror_repo: hedef depo 'sahip/depo'. Yansıtma Gitea push mirror ile yapılır (her commit'te ve düzenli aralıkla).

Revision ID: 0027
Revises: 0026
Create Date: 2026-10-23
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision = "0027"
down_revision = "0026"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("projects", sa.Column("mirror_connection_id", UUID(as_uuid=True),
                                        sa.ForeignKey("integration_connections.id", ondelete="SET NULL")))
    op.add_column("projects", sa.Column("mirror_repo", sa.String(200)))


def downgrade() -> None:
    op.drop_column("projects", "mirror_repo")
    op.drop_column("projects", "mirror_connection_id")
