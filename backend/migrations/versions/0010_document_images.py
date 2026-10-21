"""Doküman hattında görsel açıklama (Odoo #285)

0009'un ilk hâliyle kurulmuş veritabanlarında eksik kalan görsel alanlarını tamamlar.
Yeni kurulumlarda 0009 bu alanları zaten oluşturur; işlemler tekrar çalıştırılabilir.

Revision ID: 0010
Revises: 0009
Create Date: 2026-10-21
"""
import json

from alembic import op
import sqlalchemy as sa

revision = "0010"
down_revision = "0009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE agent_documents ADD COLUMN IF NOT EXISTS image_count INTEGER")
    op.get_bind().execute(sa.text(
        "INSERT INTO system_settings (key, value, description) VALUES (:k, CAST(:v AS jsonb), :d) ON CONFLICT (key) DO NOTHING"),
        {"k": "model.default.vision", "v": json.dumps("qwen3-vl-30b"),
         "d": "Görselleri (fotoğraf, şema, çizim) açıklayıp öğrenilebilir metne çeviren model"})


def downgrade() -> None:
    pass  # alanlar 0009'a aittir
