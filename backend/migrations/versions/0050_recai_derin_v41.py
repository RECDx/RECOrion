"""RECAi kademeleri: EVREN MiMo-V2.6-Pro'yu emekliye ayırdı (6.11.2026 gecesi; 1.1.2027'ye kadar istekler
deepseek-v4.1-flash'a yönlendiriliyor). Kullanıcı kararı 08.11.2026:
- RECAi Derin: mimo-v2.6-pro → deepseek-v4.1-flash; yedek deepseek-v4.1-flash (artık aynı model) → gemma-4-31b
- RECAi Mergen yedeği: mimo-v2.6-pro → gemma-4-31b (ayrı sunucu grubu; ölçümlerde %0 hata)
- Genel ilk yedek (model.fallback): mimo-v2.6-pro → gemma-4-31b
Yalnız eski değer duruyorsa değiştirilir (Süper Admin'in sonradan yaptığı seçim ezilmez).

Revision ID: 0050
Revises: 0049
Create Date: 2026-11-08
"""
from alembic import op

revision = "0050"
down_revision = "0049"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("UPDATE recai_tiers SET model_code = 'deepseek-v4.1-flash', fallback_model_code = 'gemma-4-31b', updated_at = now() "
               "WHERE code = 'DERIN' AND model_code = 'mimo-v2.6-pro'")
    op.execute("UPDATE recai_tiers SET fallback_model_code = 'gemma-4-31b', updated_at = now() "
               "WHERE code = 'MERGEN' AND fallback_model_code = 'mimo-v2.6-pro'")
    op.execute("UPDATE system_settings SET value = '\"gemma-4-31b\"'::jsonb "
               "WHERE key = 'model.fallback' AND value = '\"mimo-v2.6-pro\"'::jsonb")


def downgrade() -> None:
    op.execute("UPDATE recai_tiers SET model_code = 'mimo-v2.6-pro', fallback_model_code = 'deepseek-v4.1-flash' "
               "WHERE code = 'DERIN' AND model_code = 'deepseek-v4.1-flash' AND fallback_model_code = 'gemma-4-31b'")
    op.execute("UPDATE recai_tiers SET fallback_model_code = 'mimo-v2.6-pro' WHERE code = 'MERGEN' AND fallback_model_code = 'gemma-4-31b'")
    op.execute("UPDATE system_settings SET value = '\"mimo-v2.6-pro\"'::jsonb WHERE key = 'model.fallback' AND value = '\"gemma-4-31b\"'::jsonb")
