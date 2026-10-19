"""Denetim kaydını değiştirilemez yap; sistem rollerindeki geçersiz izin kodlarını düzelt

- audit_events: şirket/kullanıcı silinince kayıtların silinmemesi için yabancı anahtarlar
  kaldırılır; UPDATE, DELETE ve TRUNCATE tetikleyiciyle engellenir.
- tenant_roles: varsayılan sistem rolleri izin kataloğunda olmayan kodlar içeriyordu
  (tenant:create, lead:approve, chat:access ...). Bu kodlar katalogdaki karşılıklarıyla
  değiştirilir. Süper Yönetici rolüne dokunulmaz.

Revision ID: 0004
Revises: 0003
Create Date: 2026-10-20
"""
import json

from alembic import op
import sqlalchemy as sa

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None

ROLE_PERMISSIONS = {
    "Kurumsal Operasyon & Müşteri Yöneticisi": ["tenant:view", "tenant:manage", "billing:view"],
    "Güvenlik & Uyum Denetçisi (SecOps & Compliance)": ["tenant:view", "role:edit", "chat:export"],
    "Yapay Zeka Mimarisi & Ajan Lideri": [
        "agent:hire", "agent:configure", "agent:custom_title", "agent:quarantine",
        "project:manage", "chat:participate", "chat:view_a2a",
    ],
    "Standart Kurumsal Kullanıcı": ["tenant:view", "task:create", "chat:participate", "memory:search"],
}


def upgrade() -> None:
    op.execute("ALTER TABLE audit_events DROP CONSTRAINT IF EXISTS audit_events_actor_id_fkey")
    op.execute("ALTER TABLE audit_events DROP CONSTRAINT IF EXISTS audit_events_tenant_id_fkey")
    op.execute("ALTER TABLE audit_events ALTER COLUMN action TYPE varchar(128)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_audit_events_tenant_id ON audit_events (tenant_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_audit_events_created_at ON audit_events (created_at)")
    op.execute("""
        CREATE OR REPLACE FUNCTION audit_events_block_mutation() RETURNS trigger AS $$
        BEGIN
            RAISE EXCEPTION 'audit_events tablosu değiştirilemez (yalnızca ekleme yapılabilir)';
        END;
        $$ LANGUAGE plpgsql
    """)
    op.execute("DROP TRIGGER IF EXISTS trg_audit_events_no_update_delete ON audit_events")
    op.execute("""
        CREATE TRIGGER trg_audit_events_no_update_delete
        BEFORE UPDATE OR DELETE ON audit_events
        FOR EACH ROW EXECUTE FUNCTION audit_events_block_mutation()
    """)
    op.execute("DROP TRIGGER IF EXISTS trg_audit_events_no_truncate ON audit_events")
    op.execute("""
        CREATE TRIGGER trg_audit_events_no_truncate
        BEFORE TRUNCATE ON audit_events
        FOR EACH STATEMENT EXECUTE FUNCTION audit_events_block_mutation()
    """)

    bind = op.get_bind()
    for name, perms in ROLE_PERMISSIONS.items():
        bind.execute(
            sa.text("UPDATE tenant_roles SET permissions = CAST(:p AS jsonb) WHERE tenant_id IS NULL AND is_system AND name = :n"),
            {"p": json.dumps(perms), "n": name},
        )


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS trg_audit_events_no_update_delete ON audit_events")
    op.execute("DROP TRIGGER IF EXISTS trg_audit_events_no_truncate ON audit_events")
    op.execute("DROP FUNCTION IF EXISTS audit_events_block_mutation()")
