"""Çıktıdan kayda aktarım (ADIM 12.4)

integration_transfers: bir iş çıktısından (adım veya proje) çıkarılan ortak iş nesnesinin, onaylı eşlemeyle dış sisteme yazılması.
  Durum: EXTRACTING (RECAi çıktıdan nesneyi çıkarıyor) → NEEDS_FIX (eksik/hatalı; düzeltilmeli) | PENDING_APPROVAL →
  APPROVED (kuyrukta) → RUNNING → DONE | FAILED; REJECTED; ROLLED_BACK (arşivlendi / iptal edildi / eski değerler geri yazıldı).
  approvals: onaylayanlar [{actor_id, name, at, note}]; required_approvals 1 veya 2 (şirket kuralı: nesne türü / tutar eşiği).
  before: güncellemeden önceki hedef değerleri (geri alma için). Kayıt silinemez; kimlik/nesne türü/eşleme değiştirilemez.
external_links: dış kayıt bağı — bağlantı + hedef + eşleştirme değeri → dış kayıt kimliği (tekrar aktarımda çift kayıt yok).
tenants.settings: şirket tercihleri (ör. aktarım onay kuralları).
tasks.transfer_mapping_ids: adım onaylanınca önerilecek aktarımlar; projects.transfer_on_close: proje kapanınca.

Revision ID: 0035
Revises: 0034
Create Date: 2026-10-24
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision = "0035"
down_revision = "0034"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("tenants", sa.Column("settings", JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")))
    op.add_column("tasks", sa.Column("transfer_mapping_ids", JSONB, nullable=False, server_default=sa.text("'[]'::jsonb")))
    op.add_column("projects", sa.Column("transfer_on_close", JSONB, nullable=False, server_default=sa.text("'[]'::jsonb")))
    op.create_table(
        "integration_transfers",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("project_id", UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="SET NULL")),
        sa.Column("task_id", UUID(as_uuid=True), sa.ForeignKey("tasks.id", ondelete="SET NULL")),
        sa.Column("mapping_id", UUID(as_uuid=True), sa.ForeignKey("integration_mappings.id", ondelete="SET NULL")),
        sa.Column("mapping_version", sa.Integer),
        sa.Column("connection_id", UUID(as_uuid=True), sa.ForeignKey("integration_connections.id", ondelete="SET NULL")),
        sa.Column("connection_name", sa.String(120)),
        sa.Column("object_type", sa.String(16), nullable=False),
        sa.Column("trigger", sa.String(16), nullable=False),
        sa.Column("object", JSONB),
        sa.Column("values", JSONB),
        sa.Column("preview", JSONB),
        sa.Column("problems", JSONB),
        sa.Column("action", sa.String(8)),
        sa.Column("amount", sa.Numeric(18, 2)),
        sa.Column("status", sa.String(20), nullable=False, server_default="EXTRACTING"),
        sa.Column("required_approvals", sa.Integer, nullable=False, server_default="1"),
        sa.Column("approvals", JSONB, nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("decision_note", sa.Text),
        sa.Column("external_id", sa.String(64)),
        sa.Column("external_ref", sa.String(255)),
        sa.Column("external_url", sa.Text),
        sa.Column("before", JSONB),
        sa.Column("result", JSONB),
        sa.Column("error", sa.Text),
        sa.Column("attempts", sa.Integer, nullable=False, server_default="0"),
        sa.Column("created_by_actor_id", UUID(as_uuid=True)),
        sa.Column("created_by_name", sa.String(160)),
        sa.Column("done_at", sa.DateTime(timezone=True)),
        sa.Column("rolled_back_at", sa.DateTime(timezone=True)),
        sa.Column("rolled_back_by_actor_id", UUID(as_uuid=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_integration_transfers_tenant", "integration_transfers", ["tenant_id", "status", "created_at"])
    op.create_index("ix_integration_transfers_project", "integration_transfers", ["project_id"])
    op.create_table(
        "external_links",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("connection_id", UUID(as_uuid=True), sa.ForeignKey("integration_connections.id", ondelete="CASCADE"), nullable=False),
        sa.Column("target_key", sa.String(120), nullable=False),
        sa.Column("match_value", sa.String(255), nullable=False),
        sa.Column("external_id", sa.String(64), nullable=False),
        sa.Column("last_transfer_id", UUID(as_uuid=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("connection_id", "target_key", "match_value", name="uq_external_link"),
    )
    op.execute("""
    CREATE OR REPLACE FUNCTION integration_transfers_guard() RETURNS trigger AS $$
    BEGIN
      IF TG_OP = 'DELETE' OR TG_OP = 'TRUNCATE' THEN
        IF TG_OP = 'DELETE' AND OLD.tenant_id::text = COALESCE(current_setting('recorion.purge_tenant', true), '') THEN RETURN OLD; END IF;
        RAISE EXCEPTION 'integration_transfers kayıtları silinemez';
      END IF;
      IF NEW.tenant_id IS DISTINCT FROM OLD.tenant_id OR NEW.object_type IS DISTINCT FROM OLD.object_type
         OR NEW.mapping_id IS DISTINCT FROM OLD.mapping_id OR NEW.created_by_actor_id IS DISTINCT FROM OLD.created_by_actor_id THEN
        RAISE EXCEPTION 'aktarım kaydının kimliği, nesne türü ve eşlemesi değiştirilemez';
      END IF;
      RETURN NEW;
    END; $$ LANGUAGE plpgsql
    """)
    op.execute("CREATE TRIGGER trg_integration_transfers_guard BEFORE UPDATE OR DELETE ON integration_transfers "
               "FOR EACH ROW EXECUTE FUNCTION integration_transfers_guard()")
    op.execute("CREATE TRIGGER trg_integration_transfers_no_truncate BEFORE TRUNCATE ON integration_transfers "
               "FOR EACH STATEMENT EXECUTE FUNCTION integration_transfers_guard()")


def downgrade() -> None:
    op.drop_table("external_links")
    op.drop_table("integration_transfers")
    op.execute("DROP FUNCTION IF EXISTS integration_transfers_guard()")
    op.drop_column("projects", "transfer_on_close")
    op.drop_column("tasks", "transfer_mapping_ids")
    op.drop_column("tenants", "settings")
