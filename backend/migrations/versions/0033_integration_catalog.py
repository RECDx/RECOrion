"""Bağlantı kataloğu (ADIM 12.1)

Platform genelinde (RECDx Süper Admin yönetir) bağlanabilir sistemlerin kartları: Odoo, Logo, Linear, Notion...
method: bağlanma yolu — NATIVE (RECOrion'un kendi bağlayıcısı), MCP_OAUTH (servisin MCP sunucusu, tek tık giriş),
MCP_TOKEN (MCP sunucusu, erişim anahtarıyla), EDGE (şirket sunucusundaki sistem, Edge ajanıyla), PLANNED (yakında).
connector: kullanılacak bağlayıcı kodu (odoo, mcp, edge...); preset: bağlantı formuna önceden doldurulan düz ayarlar
(ör. MCP sunucu adresi). Kimlik bilgisi içermez. code: tohum kodu (açılışta yalnızca eksik olanlar eklenir).

Revision ID: 0033
Revises: 0032
Create Date: 2026-10-24
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision = "0033"
down_revision = "0032"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "integration_catalog",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("code", sa.String(64), unique=True, nullable=False),
        sa.Column("title", sa.String(120), nullable=False),
        sa.Column("vendor", sa.String(120)),
        sa.Column("category", sa.String(40), nullable=False),
        sa.Column("method", sa.String(16), nullable=False),
        sa.Column("connector", sa.String(32)),
        sa.Column("preset", JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("description", sa.Text),
        sa.Column("setup_steps", JSONB, nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("keywords", sa.Text),
        sa.Column("sort", sa.Integer, nullable=False, server_default="100"),
        sa.Column("status", sa.String(16), nullable=False, server_default="ACTIVE"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.add_column("integration_connections", sa.Column("catalog_code", sa.String(64)))


def downgrade() -> None:
    op.drop_column("integration_connections", "catalog_code")
    op.drop_table("integration_catalog")
