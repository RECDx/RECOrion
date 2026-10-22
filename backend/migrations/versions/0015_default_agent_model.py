"""AI personel için varsayılan model ayarı (model.default.agent)

22.10.2026 canlı testleri: mimo-v2.6-pro EVREN'de yoğunlukta 503 "Model şu anda dolu" veriyor ve uzun çıktılarda zaman
aşımına düşüyor; deepseek-v4-flash ~17 token/sn ile en hızlı ve kararlı seçenek. Kullanıcı kararıyla yeni işe alınan AI
personelin varsayılan modeli deepseek-v4-flash. Mevcut personelin modeli değişmez.

Revision ID: 0015
Revises: 0014
Create Date: 2026-10-22
"""
import json

import sqlalchemy as sa
from alembic import op

revision = "0015"
down_revision = "0014"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.get_bind().execute(sa.text(
        "INSERT INTO system_settings (key, value, description) VALUES (:k, CAST(:v AS jsonb), :d) ON CONFLICT (key) DO NOTHING"),
        {"k": "model.default.agent", "v": json.dumps("deepseek-v4-flash"),
         "d": "Yeni işe alınan AI personelin varsayılan modeli; personelin modeli yanıt vermezse ilk yedek model"})


def downgrade() -> None:
    op.execute("DELETE FROM system_settings WHERE key = 'model.default.agent'")
