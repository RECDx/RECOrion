"""Varsayılan modeller deepseek-v4-flash, yedek model mimo-v2.6-pro (kullanıcı kararı 23.10.2026)

Son 7 günün ölçümü (Süper Admin panosu, ADIM 9.4): mimo-v2.6-pro hata oranı %18,9 (EVREN 503 "Model şu anda dolu",
zaman aşımı), deepseek-v4-flash %4,2. Beyin AI, sohbet ve Süper Yönetici asistanı varsayılanı deepseek-v4-flash olur;
model.fallback ayarı meşgul/yanıtsız modelde ilk denenecek yedek modeldir (mimo-v2.6-pro).

Revision ID: 0025
Revises: 0024
Create Date: 2026-10-23
"""
import json

import sqlalchemy as sa
from alembic import op

revision = "0025"
down_revision = "0024"
branch_labels = None
depends_on = None

DEFAULTS = {"model.default.brain": "deepseek-v4-flash", "model.default.chat": "deepseek-v4-flash",
            "model.platform_assistant": "deepseek-v4-flash"}


def upgrade() -> None:
    bind = op.get_bind()
    for key, value in DEFAULTS.items():
        bind.execute(sa.text("UPDATE system_settings SET value = CAST(:v AS jsonb) WHERE key = :k"), {"k": key, "v": json.dumps(value)})
    bind.execute(sa.text(
        "INSERT INTO system_settings (key, value, description) VALUES (:k, CAST(:v AS jsonb), :d) ON CONFLICT (key) DO NOTHING"),
        {"k": "model.fallback", "v": json.dumps("mimo-v2.6-pro"),
         "d": "Asıl model meşgul veya yanıtsızken ilk denenecek yedek model"})


def downgrade() -> None:
    bind = op.get_bind()
    for key in DEFAULTS:
        bind.execute(sa.text("UPDATE system_settings SET value = CAST(:v AS jsonb) WHERE key = :k"), {"k": key, "v": json.dumps("mimo-v2.6-pro")})
    op.execute("DELETE FROM system_settings WHERE key = 'model.fallback'")
