"""ADIM 15.2: Yardım (Bilgi Birikimi) sayfaları — kullanım kılavuzlarından, Türkçe tam metin dizinli.

Revision ID: 0044
Revises: 0043
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, TSVECTOR

revision = "0044"
down_revision = "0043"
branch_labels = None
depends_on = None

SEARCH = ("setweight(to_tsvector('turkish', coalesce(title, '')), 'A') || "
          "setweight(to_tsvector('turkish', coalesce(section, '')), 'B') || "
          "setweight(to_tsvector('turkish', coalesce(body, '')), 'C')")


def upgrade():
    op.create_table(
        "help_pages",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("slug", sa.String(255), nullable=False, unique=True),
        sa.Column("guide", sa.String(16), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("parent_slug", sa.String(255)),
        sa.Column("sort", sa.Integer, nullable=False, server_default="0"),
        sa.Column("level", sa.Integer, nullable=False, server_default="2"),
        sa.Column("section", sa.String(255)),
        sa.Column("body", sa.Text, nullable=False, server_default=""),
        sa.Column("audience", sa.String(16), nullable=False, server_default="CUSTOMER"),
        sa.Column("screen_keys", JSONB, nullable=False, server_default="[]"),
        sa.Column("permissions", JSONB, nullable=False, server_default="[]"),
        sa.Column("search", TSVECTOR, sa.Computed(SEARCH, persisted=True)),
    )
    op.create_index("ix_help_pages_search", "help_pages", ["search"], postgresql_using="gin")


def downgrade():
    op.drop_index("ix_help_pages_search", table_name="help_pages")
    op.drop_table("help_pages")
