"""Proje kod deposu (ADIM 8.5, Gitea)

- projects.repo_mode: NONE (depo yok) | RECORION (RECOrion Gitea deposu); repo_owner / repo_name: Gitea'daki yeri
- tasks.repo_branch / repo_pr_number / repo_merged_at: iş adımının dalı, ana dala birleştirme isteği ve birleştirme zamanı

Revision ID: 0023
Revises: 0022
Create Date: 2026-10-23
"""
from alembic import op

revision = "0023"
down_revision = "0022"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        ALTER TABLE projects
            ADD COLUMN IF NOT EXISTS repo_mode VARCHAR(16) NOT NULL DEFAULT 'NONE' CHECK (repo_mode IN ('NONE', 'RECORION')),
            ADD COLUMN IF NOT EXISTS repo_owner VARCHAR(64),
            ADD COLUMN IF NOT EXISTS repo_name VARCHAR(100)
    """)
    op.execute("""
        ALTER TABLE tasks
            ADD COLUMN IF NOT EXISTS repo_branch VARCHAR(120),
            ADD COLUMN IF NOT EXISTS repo_pr_number INTEGER,
            ADD COLUMN IF NOT EXISTS repo_merged_at TIMESTAMPTZ
    """)


def downgrade() -> None:
    op.execute("ALTER TABLE tasks DROP COLUMN IF EXISTS repo_merged_at, DROP COLUMN IF EXISTS repo_pr_number, DROP COLUMN IF EXISTS repo_branch")
    op.execute("ALTER TABLE projects DROP COLUMN IF EXISTS repo_name, DROP COLUMN IF EXISTS repo_owner, DROP COLUMN IF EXISTS repo_mode")
