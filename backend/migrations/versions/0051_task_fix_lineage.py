"""Test düzeltme döngüsü (Aşama 2 bulguları F99/F100/F103/F105/F109): düzeltme ve yeniden test adımları hangi test adımına
ait (fix_of_task_id: kök test adımı) ve türü (fix_kind: FIX | RETEST). Böylece bir test adımı için tek açık tur tutulur,
testler geçince turlar kapanır, düzeltme adımı güncel koşu raporuyla çalışır.

Revision ID: 0051
Revises: 0050
Create Date: 2026-11-11
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0051"
down_revision = "0050"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("tasks", sa.Column("fix_of_task_id", postgresql.UUID(as_uuid=True),
                                     sa.ForeignKey("tasks.id", ondelete="SET NULL"), nullable=True))
    op.add_column("tasks", sa.Column("fix_kind", sa.String(8), nullable=True))
    op.create_index("ix_tasks_fix_of_task_id", "tasks", ["fix_of_task_id"])


def downgrade() -> None:
    op.drop_index("ix_tasks_fix_of_task_id", table_name="tasks")
    op.drop_column("tasks", "fix_kind")
    op.drop_column("tasks", "fix_of_task_id")
