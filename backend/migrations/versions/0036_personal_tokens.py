"""Kişisel erişim anahtarları (ADIM 12.6): RECOrion'un MCP sunucusuna dış istemcilerden (Claude, Cursor, şirketin kendi sistemi)
kullanıcının kendi yetkileriyle bağlanmak için.

Anahtarın yalnızca SHA-256 özeti saklanır (bir kez gösterilir). scopes: READ (okuma araçları) ve/veya WRITE (proje/Case açma,
plan taslağına adım ekleme). Onay işlemleri anahtarla yapılamaz. Süresi dolan veya iptal edilen anahtar reddedilir.

Revision ID: 0036
Revises: 0035
Create Date: 2026-10-24
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision = "0036"
down_revision = "0035"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "personal_tokens",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("actor_id", UUID(as_uuid=True), sa.ForeignKey("actors.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(80), nullable=False),
        sa.Column("token_hash", sa.String(64), nullable=False, unique=True),
        sa.Column("prefix", sa.String(16), nullable=False),
        sa.Column("scopes", JSONB, nullable=False, server_default=sa.text("'[\"READ\"]'::jsonb")),
        sa.Column("expires_at", sa.DateTime(timezone=True)),
        sa.Column("last_used_at", sa.DateTime(timezone=True)),
        sa.Column("use_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("revoked_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_personal_tokens_actor", "personal_tokens", ["actor_id"])


def downgrade() -> None:
    op.drop_index("ix_personal_tokens_actor", table_name="personal_tokens")
    op.drop_table("personal_tokens")
