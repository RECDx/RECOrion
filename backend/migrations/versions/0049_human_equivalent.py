"""Kredinin TL karşılığı ve insan eşdeğeri (#664, kullanıcı kararı 07.11.2026).

- plans.credit_unit_price_try: kredi birim fiyatı (boş = aylık ücret ÷ aylık kredi); plans.topup_credit_price_try: ek kredi fiyatı.
- job_titles.reference_salary_try: ünvana özel referans aylık brüt maaş (boş = kıdem/aile bandı).
- system_settings: cost.salary_bands (2026 referans aylık brüt TL; Yazılım/BT ve Genel × kıdem), cost.employer_factor (1,25),
  cost.work_days_month (22), cost.real_credit_cost_try (RECDx'in gerçek kredi maliyeti; EVREN/GPU belli olunca, boş).
  Kaynak: 2026 Türkiye maaş anketleri (net → brüt), asgari ücret brüt 33.030 TL; ayrıntı Claude\\olcumler\\maas_referans_2026.md.

Revision ID: 0049
Revises: 0048
"""
import json

import sqlalchemy as sa
from alembic import op

revision = "0049"
down_revision = "0048"
branch_labels = None
depends_on = None

BANDS = {"IT": {"JUNIOR": 85000, "MID": 140000, "SENIOR": 210000, "LEAD": 240000, "MANAGER": 260000},
         "GENERAL": {"JUNIOR": 50000, "MID": 75000, "SENIOR": 110000, "LEAD": 135000, "MANAGER": 190000}}
SETTINGS = {"cost.salary_bands": BANDS, "cost.employer_factor": 1.25, "cost.work_days_month": 22, "cost.real_credit_cost_try": None}


def upgrade():
    op.add_column("plans", sa.Column("credit_unit_price_try", sa.Numeric(10, 4)))
    op.add_column("plans", sa.Column("topup_credit_price_try", sa.Numeric(10, 4)))
    op.add_column("job_titles", sa.Column("reference_salary_try", sa.Numeric(12, 2)))
    bind = op.get_bind()
    for k, v in SETTINGS.items():
        bind.execute(sa.text("INSERT INTO system_settings (key, value) VALUES (:k, CAST(:v AS jsonb)) ON CONFLICT (key) DO NOTHING"),
                     {"k": k, "v": json.dumps(v)})


def downgrade():
    op.execute("DELETE FROM system_settings WHERE key LIKE 'cost.%'")
    op.drop_column("job_titles", "reference_salary_try")
    op.drop_column("plans", "topup_credit_price_try")
    op.drop_column("plans", "credit_unit_price_try")
