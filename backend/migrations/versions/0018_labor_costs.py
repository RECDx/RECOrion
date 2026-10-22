"""Personel maliyeti (ADIM 7.5.2)

- actors.daily_cost_try: insan personelin günlük maliyeti; AI personel için isteğe bağlı günlük sabit maliyet (TL, KDV hariç).
  Kişisel veridir (KVKK): kişi bazında yalnızca Şirket Yönetimi görür.
- tasks.labor_*: iş adımı tamamlandığında kullanılan günlük ücret, gerçekleşen iş günü ve personel maliyeti (sonradan ücret
  değişse de geçmiş adımın maliyeti değişmez).

Revision ID: 0018
Revises: 0017
Create Date: 2026-10-23
"""
from alembic import op

revision = "0018"
down_revision = "0017"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE actors ADD COLUMN IF NOT EXISTS daily_cost_try NUMERIC(12, 2) CHECK (daily_cost_try >= 0)")
    op.execute("""
        ALTER TABLE tasks
            ADD COLUMN IF NOT EXISTS labor_rate_try NUMERIC(12, 2),
            ADD COLUMN IF NOT EXISTS labor_days NUMERIC(6, 1),
            ADD COLUMN IF NOT EXISTS labor_cost_try NUMERIC(14, 2)
    """)


def downgrade() -> None:
    op.execute("ALTER TABLE tasks DROP COLUMN IF EXISTS labor_rate_try, DROP COLUMN IF EXISTS labor_days, DROP COLUMN IF EXISTS labor_cost_try")
    op.execute("ALTER TABLE actors DROP COLUMN IF EXISTS daily_cost_try")
