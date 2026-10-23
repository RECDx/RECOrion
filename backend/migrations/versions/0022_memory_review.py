"""Hafıza onayının izi (ADIM 8.4)

- memory_items.reviewed_by_actor_id / reviewed_at / review_note: Kurum Hafızasına terfi eden veya reddedilen bilgiyi
  kimin, ne zaman (ve ret gerekçesiyle) karara bağladığı. Kişi silinse de iz kalır (yabancı anahtar yok).

Revision ID: 0022
Revises: 0021
Create Date: 2026-10-23
"""
from alembic import op

revision = "0022"
down_revision = "0021"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        ALTER TABLE memory_items
            ADD COLUMN IF NOT EXISTS reviewed_by_actor_id UUID,
            ADD COLUMN IF NOT EXISTS reviewed_at TIMESTAMPTZ,
            ADD COLUMN IF NOT EXISTS review_note TEXT
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_memory_items_tenant_status ON memory_items (tenant_id, status, created_at)")


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_memory_items_tenant_status")
    op.execute("ALTER TABLE memory_items DROP COLUMN IF EXISTS review_note, DROP COLUMN IF EXISTS reviewed_at, "
               "DROP COLUMN IF EXISTS reviewed_by_actor_id")
