"""Proje durumlarına PLANNING ve COMPLETED eklenir (ADIM 6)

Eski durum değerleri (PROVISIONING, RELEASE_PENDING, RELEASED, PROVISION_FAILED) mevcut kayıtlar için korunur.

Revision ID: 0013
Revises: 0012
Create Date: 2026-10-21
"""
from alembic import op

revision = "0013"
down_revision = "0012"
branch_labels = None
depends_on = None

NEW = ("DRAFT", "PLANNING", "READY", "ACTIVE", "PAUSED", "COMPLETED", "CANCELLED",
       "PROVISIONING", "RELEASE_PENDING", "RELEASED", "PROVISION_FAILED")
OLD = ("DRAFT", "PROVISIONING", "READY", "ACTIVE", "RELEASE_PENDING", "RELEASED", "PROVISION_FAILED", "PAUSED", "CANCELLED")


def _check(values) -> str:
    return "status IN (" + ", ".join(f"'{v}'" for v in values) + ")"


def upgrade() -> None:
    op.execute("ALTER TABLE projects DROP CONSTRAINT IF EXISTS projects_status_check")
    op.execute(f"ALTER TABLE projects ADD CONSTRAINT projects_status_check CHECK ({_check(NEW)})")
    op.execute("ALTER TABLE project_members ADD CONSTRAINT project_members_role_check CHECK (role IN ('MANAGER', 'MEMBER', 'AGENT'))")


def downgrade() -> None:
    op.execute("ALTER TABLE project_members DROP CONSTRAINT IF EXISTS project_members_role_check")
    op.execute("ALTER TABLE projects DROP CONSTRAINT IF EXISTS projects_status_check")
    op.execute(f"ALTER TABLE projects ADD CONSTRAINT projects_status_check CHECK ({_check(OLD)})")
