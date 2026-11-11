"""EVREN MiMo-V2.6-Pro'yu emekliye ayırdı (6.11.2026; istekler 1.1.2027'ye kadar deepseek-v4.1-flash'a yönleniyor). 0050'nin
devamı (Aşama 2 bulgusu F62, #665 açık maddesi): MiMo seçilemesin, yerine fiilen çalışan deepseek-v4.1-flash yazılsın.
- AI personelin tercih ettiği model MiMo ise → deepseek-v4.1-flash (EVREN zaten oraya yönlendiriyor; davranış değişmez)
- Ünvan kataloğunda önerilen model ve manifesto varsayılan modeli → deepseek-v4.1-flash
- llm_models: mimo-v2.6-pro INACTIVE (seçim listelerinden düşer)
Yalnız MiMo olan değerler değişir. Downgrade yalnız model durumunu geri alır (diğerleri zaten aynı modele gidiyordu).

Revision ID: 0052
Revises: 0051
Create Date: 2026-11-11
"""
from alembic import op

revision = "0052"
down_revision = "0051"
branch_labels = None
depends_on = None

OLD, NEW = "mimo-v2.6-pro", "deepseek-v4.1-flash"


def upgrade() -> None:
    op.execute(f"""UPDATE actors SET preferred_model_id = (SELECT id FROM llm_models WHERE model_code = '{NEW}')
                   WHERE preferred_model_id = (SELECT id FROM llm_models WHERE model_code = '{OLD}')
                     AND EXISTS (SELECT 1 FROM llm_models WHERE model_code = '{NEW}')""")
    op.execute(f"UPDATE job_titles SET recommended_model_code = '{NEW}' WHERE recommended_model_code = '{OLD}'")
    op.execute(f"""UPDATE system_settings SET value = '"{NEW}"'::jsonb WHERE value = '"{OLD}"'::jsonb""")
    op.execute(f"UPDATE llm_models SET status = 'INACTIVE' WHERE model_code = '{OLD}'")


def downgrade() -> None:
    op.execute(f"UPDATE llm_models SET status = 'ACTIVE' WHERE model_code = '{OLD}'")
