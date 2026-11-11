"""İSTEK #742: tek etiketli öğrenme kaydı (sohbet + iş akışı; sektörden bağımsız).

Her onay/ret/değerlendirme/test/aktarım kararı bir kayıt olur: görev girdisi, çıktı anlık görüntüsü, etiket
(DOGRU/YANLIS/BELIRSIZ), neden sınıfı (MODEL_HATASI/ORTAM/DEGERLENDIRICI/KAPSAM/BELIRSIZ), geri bildirim, çıkarılan ders.
Aynı kayıt hem hafızayı (ders → memory_items) hem RECAi veri setini (#743) besler. Ret kaydı, sonradan onaylanan sürümün
kaydına pair_id ile bağlanır (tercih çifti). Ayrıntı: Claude/senaryo/karar_ogrenme_recai.md.

Revision ID: 0054
Revises: 0053
Create Date: 2026-11-11
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision = "0054"
down_revision = "0053"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "learning_records",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("project_id", UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="SET NULL")),
        sa.Column("task_id", UUID(as_uuid=True), sa.ForeignKey("tasks.id", ondelete="SET NULL")),
        sa.Column("agent_id", UUID(as_uuid=True), sa.ForeignKey("actors.id", ondelete="SET NULL")),
        sa.Column("decided_by_actor_id", UUID(as_uuid=True), sa.ForeignKey("actors.id", ondelete="SET NULL")),
        sa.Column("source", sa.String(32), nullable=False),
        sa.Column("label", sa.String(12), nullable=False),
        sa.Column("cause", sa.String(16)),
        sa.Column("cause_by", sa.String(8)),
        sa.Column("cause_reason", sa.Text),
        sa.Column("sector", sa.String(120)),
        sa.Column("job_title", sa.String(128)),
        sa.Column("task_input", sa.Text),
        sa.Column("output", sa.Text),
        sa.Column("output_ref", sa.String(64)),
        sa.Column("feedback", sa.Text),
        sa.Column("pair_id", UUID(as_uuid=True), sa.ForeignKey("learning_records.id", ondelete="SET NULL")),
        sa.Column("lesson", sa.Text),
        sa.Column("lesson_scope", sa.String(8)),
        sa.Column("lesson_memory_id", UUID(as_uuid=True), sa.ForeignKey("memory_items.id", ondelete="SET NULL")),
        sa.Column("lesson_status", sa.String(12), nullable=False, server_default="PENDING"),
        sa.Column("data", JSONB, nullable=False, server_default="{}"),
        sa.Column("reviewed_by_actor_id", UUID(as_uuid=True), sa.ForeignKey("actors.id", ondelete="SET NULL")),
        sa.Column("reviewed_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_learning_records_tenant_created", "learning_records", ["tenant_id", "created_at"])
    op.create_index("ix_learning_records_task", "learning_records", ["task_id"])


def downgrade() -> None:
    op.drop_table("learning_records")
