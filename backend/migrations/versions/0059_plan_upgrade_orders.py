"""İSTEK #747 ek: paket yükseltme siparişi (hemen geçerli, oransal fark) — kredi siparişleriyle aynı akış (Odoo satış siparişi,
havale/EFT Merkez onayı). credit_orders: kind (CREDIT / PLAN_UPGRADE), target_plan_id, from_plan_id.

Revision ID: 0059
Revises: 0058
Create Date: 2026-11-16
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0059"
down_revision = "0058"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("credit_orders", sa.Column("kind", sa.String(16), nullable=False, server_default="CREDIT"))
    op.add_column("credit_orders", sa.Column("target_plan_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("plans.id", ondelete="SET NULL")))
    op.add_column("credit_orders", sa.Column("from_plan_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("plans.id", ondelete="SET NULL")))


def downgrade() -> None:
    op.drop_column("credit_orders", "from_plan_id")
    op.drop_column("credit_orders", "target_plan_id")
    op.drop_column("credit_orders", "kind")
