"""ADIM 14: RECSlip.App v2 aylık masraf süreci.

- personal_credentials: kişinin şirket bağlantısındaki kendi anahtarı (RECSlip v2 onayları kişinin kendi anahtarıyla)
- recslip_decisions: her onay adımı için AI değerlendirmesi ve sonucu (otomatik, insana düşen, insan kararı)
- recslip_exports: aylık aktarım dosyaları, denemeler ve muhasebeye işlendi durumu
- projects.settings: Case ayarları (RECSlip: takip sıklığı, aktarım zamanı, tekrar, onay kriterleri)

Revision ID: 0042
Revises: 0041
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision = "0042"
down_revision = "0041"
branch_labels = None
depends_on = None


def _ts(name, nullable=True):
    return sa.Column(name, sa.DateTime(timezone=True), nullable=nullable)


def upgrade():
    op.add_column("projects", sa.Column("settings", JSONB))
    op.create_table(
        "personal_credentials",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("actor_id", UUID(as_uuid=True), sa.ForeignKey("actors.id", ondelete="CASCADE"), nullable=False),
        sa.Column("connection_id", UUID(as_uuid=True), sa.ForeignKey("integration_connections.id", ondelete="CASCADE"), nullable=False),
        sa.Column("agent_actor_id", UUID(as_uuid=True), sa.ForeignKey("actors.id", ondelete="SET NULL")),
        sa.Column("external_uid", sa.Integer),
        sa.Column("external_login", sa.String(160)),
        sa.Column("external_name", sa.String(160)),
        sa.Column("secret", sa.Text),
        _ts("expires_at"),
        sa.Column("status", sa.String(16), nullable=False, server_default="ACTIVE"),
        _ts("last_test_at"),
        sa.Column("last_test_ok", sa.Boolean),
        sa.Column("last_error", sa.Text),
        _ts("created_at"), _ts("updated_at"),
        sa.UniqueConstraint("actor_id", "connection_id", name="uq_personal_credential"),
    )
    op.create_index("ix_personal_credentials_conn_uid", "personal_credentials", ["connection_id", "external_uid"])
    op.create_table(
        "recslip_decisions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("project_id", UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="SET NULL")),
        sa.Column("connection_id", UUID(as_uuid=True), sa.ForeignKey("integration_connections.id", ondelete="CASCADE"), nullable=False),
        sa.Column("expense_id", sa.Integer, nullable=False),
        sa.Column("step_id", sa.Integer, nullable=False),
        sa.Column("role", sa.String(16), nullable=False),
        sa.Column("expense_name", sa.String(255)),
        sa.Column("employee_name", sa.String(160)),
        sa.Column("amount", sa.Numeric(14, 2)),
        sa.Column("currency", sa.String(3)),
        sa.Column("receipt_date", sa.Date),
        sa.Column("approver_actor_id", UUID(as_uuid=True), sa.ForeignKey("actors.id", ondelete="SET NULL")),
        sa.Column("agent_actor_id", UUID(as_uuid=True), sa.ForeignKey("actors.id", ondelete="SET NULL")),
        sa.Column("verdict", sa.String(16), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("reasons", JSONB, nullable=False, server_default="[]"),
        sa.Column("corrections", JSONB, nullable=False, server_default="[]"),
        sa.Column("error", sa.Text),
        sa.Column("decided_by_actor_id", UUID(as_uuid=True)),
        _ts("decided_at"),
        sa.Column("human_agreed", sa.Boolean),
        sa.Column("human_note", sa.Text),
        _ts("created_at"), _ts("updated_at"),
        sa.UniqueConstraint("connection_id", "step_id", name="uq_recslip_decision_step"),
    )
    op.create_index("ix_recslip_decisions_tenant_status", "recslip_decisions", ["tenant_id", "status"])
    op.create_table(
        "recslip_exports",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("project_id", UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="SET NULL")),
        sa.Column("connection_id", UUID(as_uuid=True), sa.ForeignKey("integration_connections.id", ondelete="CASCADE"), nullable=False),
        sa.Column("period", sa.String(7), nullable=False),
        sa.Column("odoo_export_id", sa.Integer),
        sa.Column("name", sa.String(255)),
        sa.Column("software", sa.String(16)),
        sa.Column("receipt_count", sa.Integer),
        sa.Column("total", sa.Numeric(14, 2)),
        sa.Column("not_exported", sa.Integer),
        sa.Column("artifact_id", UUID(as_uuid=True), sa.ForeignKey("artifacts.id", ondelete="SET NULL")),
        sa.Column("status", sa.String(16), nullable=False, server_default="PENDING"),
        sa.Column("attempts", sa.Integer, nullable=False, server_default="0"),
        _ts("next_attempt_at"),
        sa.Column("last_error", sa.Text),
        _ts("posted_at"),
        _ts("created_at"), _ts("updated_at"),
        sa.UniqueConstraint("connection_id", "period", name="uq_recslip_export_period"),
    )
    # RECSlip v1 kaldırıldı (kullanıcı kararı 02.11.2026): hazır kural şablonları ve masraf eşlemesi arşivlenir, v1 kuralları durur
    op.execute("UPDATE project_templates SET status = 'ARCHIVED' WHERE code IN ('recslip-sorunlu-fis', 'recslip-ay-sonu')")
    op.execute("UPDATE integration_mappings SET status = 'ARCHIVED' WHERE code = 'odoo_expense'")
    op.execute("UPDATE automation_rules SET status = 'PAUSED', last_error = 'RECSlip v1 kuralı: RECSlip.App v2 aylık sürecine geçildi (ADIM 14).' "
               "WHERE status = 'ACTIVE' AND (poll->>'enrich' = 'hr_expense' OR schedule->>'summary' = 'expense_month')")


def downgrade():
    op.drop_table("recslip_exports")
    op.drop_index("ix_recslip_decisions_tenant_status", table_name="recslip_decisions")
    op.drop_table("recslip_decisions")
    op.drop_index("ix_personal_credentials_conn_uid", table_name="personal_credentials")
    op.drop_table("personal_credentials")
    op.drop_column("projects", "settings")
