"""Diğer maliyet kalemleri ve proje bütçesi (ADIM 7.5.3)

- project_cost_items: materyal, danışmanlık, eğitim, lisans, seyahat, donanım, diğer; miktar × birim fiyat (TL, KDV hariç),
  isteğe bağlı iş adımı ve belge (fatura vb.). Belgeler öğrenme hattına (Proje Ekleri) girmez, ayrı saklanır.
- projects.budget_try / budget_note: proje bütçesi.

Revision ID: 0019
Revises: 0018
Create Date: 2026-10-23
"""
from alembic import op

revision = "0019"
down_revision = "0018"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS project_cost_items (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
            project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
            task_id UUID REFERENCES tasks(id) ON DELETE SET NULL,
            category VARCHAR(24) NOT NULL CHECK (category IN ('MATERYAL', 'DANISMANLIK', 'EGITIM', 'LISANS', 'SEYAHAT', 'DONANIM', 'DIGER')),
            description VARCHAR(500) NOT NULL,
            quantity NUMERIC(14, 3) NOT NULL CHECK (quantity > 0),
            unit VARCHAR(24),
            unit_price_try NUMERIC(14, 2) NOT NULL CHECK (unit_price_try >= 0),
            amount_try NUMERIC(16, 2) NOT NULL,
            incurred_on DATE NOT NULL,
            attachment_path VARCHAR(512),
            attachment_name VARCHAR(255),
            created_by_actor_id UUID REFERENCES actors(id) ON DELETE SET NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_project_cost_items_project ON project_cost_items (project_id, incurred_on)")
    op.execute("ALTER TABLE projects ADD COLUMN IF NOT EXISTS budget_try NUMERIC(16, 2) CHECK (budget_try >= 0)")
    op.execute("ALTER TABLE projects ADD COLUMN IF NOT EXISTS budget_note TEXT")


def downgrade() -> None:
    op.execute("ALTER TABLE projects DROP COLUMN IF EXISTS budget_note, DROP COLUMN IF EXISTS budget_try")
    op.execute("DROP TABLE IF EXISTS project_cost_items")
