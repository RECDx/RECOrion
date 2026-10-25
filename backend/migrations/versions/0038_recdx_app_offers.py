"""RECDx uygulama teklifleri ve talepleri (ADIM 13.1; kullanıcı kararı 25.10.2026: karma model)

plans.recdx_apps: paket başına RECQmind / RECSlip teklifi — {"recqmind": {"mode": "NONE|DISCOUNT|INCLUDED", "discount": 50,
  "odoo_product_id": 123, "odoo_product_name": "...", "list_price": 1000}}. Süper Admin paket tanımında değiştirir; ürün Odoo'dan
  seçilir (paketin kendi ürünü gibi). Varsayılan: PRO %50 indirim, ENTERPRISE dahil, diğerleri yok.
recdx_app_requests: müşterinin her uygulama seçimi (zaten kullanıyorum / paketime ekle / teklif iste) — Genel Merkez'de görünür.
  "Paketime ekle" Odoo satış siparişine satır (dahilse 0 fiyatla), "teklif iste" Odoo CRM fırsatı olur.

Revision ID: 0038
Revises: 0037
Create Date: 2026-10-25
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision = "0038"
down_revision = "0037"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("plans", sa.Column("recdx_apps", JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")))
    op.execute("""UPDATE plans SET recdx_apps = '{"recqmind": {"mode": "DISCOUNT", "discount": 50}, "recslip": {"mode": "DISCOUNT", "discount": 50}}'::jsonb
                  WHERE code = 'PRO'""")
    op.execute("""UPDATE plans SET recdx_apps = '{"recqmind": {"mode": "INCLUDED"}, "recslip": {"mode": "INCLUDED"}}'::jsonb
                  WHERE code = 'ENTERPRISE'""")
    op.create_table(
        "recdx_app_requests",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("lead_id", UUID(as_uuid=True), sa.ForeignKey("tenant_leads.id", ondelete="SET NULL")),
        sa.Column("plan_id", UUID(as_uuid=True), sa.ForeignKey("plans.id", ondelete="SET NULL")),
        sa.Column("app", sa.String(32), nullable=False),
        sa.Column("choice", sa.String(16), nullable=False),  # USING, ADD, QUOTE
        sa.Column("source", sa.String(16), nullable=False),  # PURCHASE, COMPANY
        sa.Column("mode", sa.String(16)),  # paketteki teklif: NONE, DISCOUNT, INCLUDED
        sa.Column("discount", sa.Numeric(5, 2)),
        sa.Column("list_price", sa.Numeric(14, 2)),
        sa.Column("price", sa.Numeric(14, 2)),
        sa.Column("odoo_product_id", sa.Integer),
        sa.Column("odoo_order_id", sa.Integer),
        sa.Column("odoo_order_name", sa.String(64)),
        sa.Column("odoo_lead_id", sa.Integer),
        sa.Column("status", sa.String(20), nullable=False, server_default="NEW"),  # NEW, ORDERED, OPPORTUNITY, IN_USE, DONE, CANCELLED, FAILED, SKIPPED
        sa.Column("error", sa.Text),
        sa.Column("note", sa.Text),
        sa.Column("created_by_actor_id", UUID(as_uuid=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_recdx_app_requests_tenant", "recdx_app_requests", ["tenant_id", "app"])


def downgrade() -> None:
    op.drop_index("ix_recdx_app_requests_tenant", table_name="recdx_app_requests")
    op.drop_table("recdx_app_requests")
    op.drop_column("plans", "recdx_apps")
