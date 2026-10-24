"""Akıllı model yönlendirici ve kalite test seti (ADIM 11.4; kullanıcı kararı 24.10.2026: ölçüme dayalı öneri + onaylı geçiş)

quality_runs / quality_results: kalite test setinin (app/seed/quality_suite.json) seçilen modellerde koşusu; her vaka kuralla
(JSON geçerliliği, alanlar, kod sözdizimi, kelime sınırı, zorunlu ifadeler) puanlanır — tekrarlanabilir, LLM hakemi yok.
model_route_decisions: Süper Admin'in iş türü için onayladığı model (iz). Onaylı yön system_settings 'model.route.<İŞ_TÜRÜ>'
anahtarına yazılır; AI personelin elle seçilmiş modeli varsa o korunur (yönlendirme yalnızca platform varsayılanını değiştirir).

Revision ID: 0032
Revises: 0031
Create Date: 2026-10-24
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision = "0032"
down_revision = "0031"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "quality_runs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("started_by_actor_id", UUID(as_uuid=True)),
        sa.Column("models", JSONB, nullable=False),
        sa.Column("suite_version", sa.String(20)),
        sa.Column("status", sa.String(16), nullable=False, server_default="RUNNING"),
        sa.Column("progress", sa.String(120)),
        sa.Column("error", sa.Text),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True)),
    )
    op.create_table(
        "quality_results",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("run_id", UUID(as_uuid=True), sa.ForeignKey("quality_runs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("model_code", sa.String(128), nullable=False),
        sa.Column("case_code", sa.String(64), nullable=False),
        sa.Column("task_type", sa.String(32), nullable=False),
        sa.Column("score", sa.Numeric(5, 3), nullable=False),
        sa.Column("checks", JSONB),
        sa.Column("latency_ms", sa.Integer),
        sa.Column("tokens_in", sa.Integer),
        sa.Column("tokens_out", sa.Integer),
        sa.Column("output_excerpt", sa.Text),
        sa.Column("error", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_quality_results_run", "quality_results", ["run_id", "model_code"])
    op.create_table(
        "model_route_decisions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("task_type", sa.String(32), nullable=False),
        sa.Column("model_code", sa.String(128)),  # boş: yönlendirme kaldırıldı (platform varsayılanı)
        sa.Column("previous_model_code", sa.String(128)),
        sa.Column("run_id", UUID(as_uuid=True), sa.ForeignKey("quality_runs.id", ondelete="SET NULL")),
        sa.Column("evidence", JSONB),
        sa.Column("note", sa.Text),
        sa.Column("decided_by_actor_id", UUID(as_uuid=True)),
        sa.Column("decided_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("model_route_decisions")
    op.drop_index("ix_quality_results_run", table_name="quality_results")
    op.drop_table("quality_results")
    op.drop_table("quality_runs")
