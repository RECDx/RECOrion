"""LLM bazında TL fiyat listesi (ADIM 7.5.1)

- llm_model_prices: model başına 1 milyon girdi ve 1 milyon çıktı token'ının TL fiyatı (KDV hariç) ve geçerlilik başlangıcı.
  Fiyatlar değiştirilmez; yeni fiyat yeni satırdır (geçmiş korunur, geçmiş proje maliyetleri değişmez).
- llm_calls.cost_try: çağrının, çağrı anında geçerli fiyatla hesaplanmış TL maliyeti.
- pricing.evren_cr_to_try ayarı: EVREN fiyat birimi CR'nin TL karşılığı (TL fiyat önerisi için).

Kullanıcı kararı 22.10.2026: token maliyetinin TL karşılığı LLM bazında, fiyat geçmişiyle; müşteri tarafı kredi olarak kalır.

Revision ID: 0017
Revises: 0016
Create Date: 2026-10-23
"""
import json

import sqlalchemy as sa
from alembic import op

revision = "0017"
down_revision = "0016"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS llm_model_prices (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            model_id UUID NOT NULL REFERENCES llm_models(id) ON DELETE CASCADE,
            price_in_per_1m_try NUMERIC(14, 4) NOT NULL CHECK (price_in_per_1m_try >= 0),
            price_out_per_1m_try NUMERIC(14, 4) NOT NULL CHECK (price_out_per_1m_try >= 0),
            valid_from TIMESTAMPTZ NOT NULL,
            note TEXT,
            created_by_actor_id UUID REFERENCES actors(id) ON DELETE SET NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            UNIQUE (model_id, valid_from)
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_llm_model_prices_model ON llm_model_prices (model_id, valid_from DESC)")
    op.execute("ALTER TABLE llm_calls ADD COLUMN IF NOT EXISTS cost_try NUMERIC(14, 6)")
    op.get_bind().execute(sa.text(
        "INSERT INTO system_settings (key, value, description) VALUES (:k, CAST(:v AS jsonb), :d) ON CONFLICT (key) DO NOTHING"),
        {"k": "pricing.evren_cr_to_try", "v": json.dumps(None),
         "d": "EVREN fiyat birimi 1 CR'nin TL karşılığı (LLM TL fiyat önerisi için); boşsa öneri hesaplanmaz"})


def downgrade() -> None:
    op.execute("ALTER TABLE llm_calls DROP COLUMN IF EXISTS cost_try")
    op.execute("DROP TABLE IF EXISTS llm_model_prices")
    op.execute("DELETE FROM system_settings WHERE key = 'pricing.evren_cr_to_try'")
