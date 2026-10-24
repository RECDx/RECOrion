"""Eşleme stüdyosu (ADIM 12.3)

Ortak iş nesnesinin (ürün kartı, cari...) bir bağlantıdaki hedefe (Odoo modeli, MCP aracı, Edge şablonu) nasıl yazılacağı.
tenant_id NULL = RECDx hazır eşlemesi (şablon; connection_id boş); dolu = şirketin eşlemesi (KVKK: RECDx göremez).
target: {"model": "product.template"} | {"tool": "create_issue"}; rules: hedef alan kuralları (kopyala, sabit, değer eşle,
metin şablonu, arama, kalemler); match: tekrar aktarımda aynı kaydı bulmak için kaynak→hedef alanı; when: koşul
(ör. yalnızca satış siparişleri). status DRAFT → ACTIVE (yönetici onayı); onaydan sonra düzenleme taslağa döndürür.
last_check / last_dry_run: son doğrulama ve deneme (yazmadan) sonucu.

Revision ID: 0034
Revises: 0033
Create Date: 2026-10-24
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision = "0034"
down_revision = "0033"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "integration_mappings",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE")),
        sa.Column("connection_id", UUID(as_uuid=True), sa.ForeignKey("integration_connections.id", ondelete="CASCADE")),
        sa.Column("code", sa.String(64), unique=True),
        sa.Column("connector", sa.String(32), nullable=False),
        sa.Column("object_type", sa.String(16), nullable=False),
        sa.Column("name", sa.String(160), nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("target", JSONB, nullable=False),
        sa.Column("rules", JSONB, nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("match", JSONB),
        sa.Column("when", JSONB),
        sa.Column("status", sa.String(16), nullable=False, server_default="DRAFT"),
        sa.Column("version", sa.Integer, nullable=False, server_default="1"),
        sa.Column("source_template_id", UUID(as_uuid=True), sa.ForeignKey("integration_mappings.id", ondelete="SET NULL")),
        sa.Column("last_check", JSONB),
        sa.Column("last_dry_run", JSONB),
        sa.Column("approved_by_actor_id", UUID(as_uuid=True)),
        sa.Column("approved_at", sa.DateTime(timezone=True)),
        sa.Column("created_by_actor_id", UUID(as_uuid=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_integration_mappings_tenant", "integration_mappings", ["tenant_id", "object_type", "status"])


def downgrade() -> None:
    op.drop_index("ix_integration_mappings_tenant", table_name="integration_mappings")
    op.drop_table("integration_mappings")
