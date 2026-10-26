"""Olayla başlayan işler (ADIM 13.2): otomasyon kuralları, tekrar engeli ve silinemez çalışma günlüğü.

automation_rules: ne olunca (WEBHOOK imzalı anlık bildirim / POLL bağlantının okuma aracıyla periyodik izleme /
  SCHEDULE zamanlayıcı) + koşul + ne yapılsın (şablondan Case/proje aç, bildir). webhook_secret kimlik kasasında şifreli.
automation_dedupe: aynı olay (kural + anahtar) bir kez işlenir; eşzamanlı iki teslimde biri kazanır.
automation_log: her olay ve sonucu; UPDATE/DELETE/TRUNCATE engelli (şirket silinirken KVKK temizliği hariç).
projects.source_rule_id / source_ref: işi açan kural ve dış kayıt (ör. Odoo bileti) — döngü engeli ve Case-bilet bağı.

Revision ID: 0040
Revises: 0039
Create Date: 2026-10-26
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision = "0040"
down_revision = "0039"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "automation_rules",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(160), nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("status", sa.String(16), nullable=False, server_default="ACTIVE"),  # ACTIVE, PAUSED, ARCHIVED
        sa.Column("trigger", sa.String(16), nullable=False),  # WEBHOOK, POLL, SCHEDULE
        sa.Column("connection_id", UUID(as_uuid=True), sa.ForeignKey("integration_connections.id", ondelete="SET NULL")),
        sa.Column("event_type", sa.String(120)),
        sa.Column("poll", JSONB),
        sa.Column("schedule", JSONB),
        sa.Column("conditions", JSONB, nullable=False, server_default="[]"),
        sa.Column("action", JSONB, nullable=False),
        sa.Column("requirements", sa.Text),
        sa.Column("webhook_secret", sa.Text),
        sa.Column("rate_limit_per_hour", sa.Integer, nullable=False, server_default="20"),
        sa.Column("cursor", JSONB),
        sa.Column("next_run_at", sa.DateTime(timezone=True)),
        sa.Column("last_fired_at", sa.DateTime(timezone=True)),
        sa.Column("fire_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("last_error", sa.Text),
        sa.Column("created_by_actor_id", UUID(as_uuid=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_automation_rules_tenant", "automation_rules", ["tenant_id"])
    op.create_index("ix_automation_rules_due", "automation_rules", ["status", "trigger", "next_run_at"])

    op.create_table(
        "automation_dedupe",
        sa.Column("rule_id", UUID(as_uuid=True), sa.ForeignKey("automation_rules.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("key", sa.String(255), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "automation_log",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        # şirket silinince (KVKK) günlük de gider: tetikleyici yalnızca bu işlemde silmeye izin verir
        sa.Column("tenant_id", UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("rule_id", UUID(as_uuid=True)),
        sa.Column("rule_name", sa.String(160)),
        sa.Column("source", sa.String(16), nullable=False),  # WEBHOOK, POLL, SCHEDULE, TEST
        sa.Column("event_type", sa.String(120)),
        sa.Column("external_ref", sa.String(255)),
        sa.Column("dedupe_key", sa.String(255)),
        sa.Column("outcome", sa.String(16), nullable=False),
        sa.Column("detail", sa.Text),
        sa.Column("project_id", UUID(as_uuid=True)),
        sa.Column("payload", JSONB),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_automation_log_rule", "automation_log", ["rule_id", "created_at"])
    op.create_index("ix_automation_log_tenant", "automation_log", ["tenant_id", "created_at"])
    op.execute("""
        CREATE OR REPLACE FUNCTION automation_log_append_only() RETURNS trigger AS $$
        BEGIN
            IF TG_OP = 'DELETE' AND OLD.tenant_id::text = COALESCE(current_setting('recorion.purge_tenant', true), '') THEN
                RETURN OLD;
            END IF;
            RAISE EXCEPTION 'automation_log kayıtları değiştirilemez ve silinemez (yalnızca ekleme yapılabilir)';
        END;
        $$ LANGUAGE plpgsql
    """)
    op.execute("""
        CREATE TRIGGER trg_automation_log_append_only BEFORE UPDATE OR DELETE ON automation_log
        FOR EACH ROW EXECUTE FUNCTION automation_log_append_only()
    """)
    op.execute("""
        CREATE TRIGGER trg_automation_log_no_truncate BEFORE TRUNCATE ON automation_log
        FOR EACH STATEMENT EXECUTE FUNCTION automation_log_append_only()
    """)

    op.add_column("projects", sa.Column("source_rule_id", UUID(as_uuid=True)))
    op.add_column("projects", sa.Column("source_ref", sa.String(255)))


def downgrade() -> None:
    op.drop_column("projects", "source_ref")
    op.drop_column("projects", "source_rule_id")
    op.execute("DROP TABLE IF EXISTS automation_log")
    op.execute("DROP FUNCTION IF EXISTS automation_log_append_only()")
    op.drop_table("automation_dedupe")
    op.drop_table("automation_rules")
