"""Eski NACE tablolarını kaldır (nace_catalog, sector_definitions)

NACE yapısı Ticaret Bakanlığı sektör/meslek modeliyle değiştirildi (Odoo #231);
kaldırma kararı kullanıcı tarafından 20.10.2026'da onaylandı. İki tablo da boştur
ve kodda kullanılmaz. Tablo dolu çıkarsa migrasyon veri kaybını önlemek için durur.

Revision ID: 0003
Revises: 0002
Create Date: 2026-10-20
"""
from alembic import op

from migrations.helpers import table_exists, table_is_empty

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None

LEGACY_TABLES = ["nace_catalog", "sector_definitions"]


def upgrade() -> None:
    for name in LEGACY_TABLES:
        if not table_exists(name):
            continue
        if not table_is_empty(name):
            raise RuntimeError(f"'{name}' tablosunda veri var; kaldırmadan önce yedekleyin.")
        op.drop_table(name)


def downgrade() -> None:
    pass
