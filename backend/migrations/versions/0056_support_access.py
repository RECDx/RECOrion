"""İSTEK #738: süreli ve kayıtlı RECDx destek erişimi.

KVKK: süper yönetici müşteri içeriğini göremez. Müşteri kendi ekranından "RECDx desteğine X saat erişim ver" der; o süre boyunca
Merkez Beyin AI o şirketin iş durumunu (proje/adım durumu, durma nedenleri, öğrenme özeti) görebilir. Her erişim kayda geçer ve
müşteri kaydı görür; süre bitince ya da müşteri kapatınca erişim biter. Ayrıntı: Claude/senaryo/karar_ogrenme_recai.md §6.

Revision ID: 0056
Revises: 0055
Create Date: 2026-11-11
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision = "0056"
down_revision = "0055"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "support_access_grants",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("granted_by_actor_id", UUID(as_uuid=True), sa.ForeignKey("actors.id", ondelete="SET NULL")),
        sa.Column("reason", sa.Text),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_support_access_grants_tenant", "support_access_grants", ["tenant_id", "expires_at"])
    op.create_table(
        "support_access_logs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("grant_id", UUID(as_uuid=True), sa.ForeignKey("support_access_grants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("tenant_id", UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("actor_id", UUID(as_uuid=True), sa.ForeignKey("actors.id", ondelete="SET NULL")),
        sa.Column("action", sa.String(64), nullable=False),
        sa.Column("detail", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("support_access_logs")
    op.drop_table("support_access_grants")
