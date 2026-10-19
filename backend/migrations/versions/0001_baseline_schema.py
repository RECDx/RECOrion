"""Başlangıç şeması (19.10.2026 itibarıyla çalışan veritabanının birebir kopyası)

Mevcut bir kurulumda tablolar zaten varsa hiçbir şey yapmaz; Alembic yalnızca
bu sürümü işaretler. Böylece canlı veritabanı veri kaybı olmadan devralınır.

Revision ID: 0001
Revises:
Create Date: 2026-10-19
"""
from migrations.helpers import run_sql_file, table_exists

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    if table_exists("tenants"):
        return
    run_sql_file("0001_baseline_schema.sql")


def downgrade() -> None:
    raise NotImplementedError("Başlangıç şeması geri alınamaz.")
