"""Entegrasyon katmanı çekirdeği (ADIM 10.1)

- integration_connections: şirketin dış sistem bağlantıları (Odoo, Telegram, Trello, Gitea/GitHub, dış MCP sunucusu...);
  config düz ayarlar, secret kimlik kasasında şifreli (AES-256-GCM, app/core/vault.py).
- agent_tool_grants: AI personel bazında araç yetkisi (bağlantı + araç; "*" = bağlantının tüm araçları).
- tool_calls: her araç çağrısının kaydı. Silinemez (şirket silme/KVKK istisnası); çağrının kimliği, aracı ve argümanları
  sonradan değiştirilemez, yalnızca durum/sonuç alanları ilerler. Yazma çağrıları insan onayı bekler.
- integration:manage yetkisi (şirket yöneticisinde varsayılan).

Revision ID: 0026
Revises: 0025
Create Date: 2026-10-23
"""
from alembic import op

revision = "0026"
down_revision = "0025"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS integration_connections (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
            connector VARCHAR(32) NOT NULL,
            name VARCHAR(120) NOT NULL,
            config JSONB NOT NULL DEFAULT '{}'::jsonb,
            secret TEXT,
            status VARCHAR(16) NOT NULL DEFAULT 'ACTIVE' CHECK (status IN ('ACTIVE', 'DISABLED')),
            last_test_at TIMESTAMPTZ,
            last_test_ok BOOLEAN,
            last_error TEXT,
            created_by_actor_id UUID,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            UNIQUE (tenant_id, name)
        )
    """)
    op.execute("""
        CREATE TABLE IF NOT EXISTS agent_tool_grants (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
            connection_id UUID NOT NULL REFERENCES integration_connections(id) ON DELETE CASCADE,
            actor_id UUID NOT NULL REFERENCES actors(id) ON DELETE CASCADE,
            tool VARCHAR(120) NOT NULL,
            created_by_actor_id UUID,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            UNIQUE (connection_id, actor_id, tool)
        )
    """)
    op.execute("""
        CREATE TABLE IF NOT EXISTS tool_calls (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
            connection_id UUID,
            connection_name VARCHAR(120),
            actor_id UUID,
            actor_name VARCHAR(255),
            project_id UUID,
            task_id UUID,
            tool VARCHAR(160) NOT NULL,
            kind VARCHAR(8) NOT NULL CHECK (kind IN ('READ', 'WRITE')),
            arguments JSONB NOT NULL DEFAULT '{}'::jsonb,
            status VARCHAR(24) NOT NULL CHECK (status IN ('PENDING_APPROVAL', 'REJECTED', 'EXECUTED', 'FAILED', 'DENIED')),
            result JSONB,
            error TEXT,
            approver_actor_id UUID,
            decided_by_actor_id UUID,
            decided_at TIMESTAMPTZ,
            decision_note TEXT,
            latency_ms INTEGER,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            executed_at TIMESTAMPTZ
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_tool_calls_tenant ON tool_calls (tenant_id, created_at)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_tool_calls_pending ON tool_calls (tenant_id, status) WHERE status = 'PENDING_APPROVAL'")
    op.execute("""
        CREATE OR REPLACE FUNCTION tool_calls_guard() RETURNS trigger AS $$
        BEGIN
            IF TG_OP = 'DELETE' THEN
                IF OLD.tenant_id::text = COALESCE(current_setting('recorion.purge_tenant', true), '') THEN
                    RETURN OLD;
                END IF;
                RAISE EXCEPTION 'tool_calls kayıtları silinemez';
            END IF;
            IF NEW.tenant_id IS DISTINCT FROM OLD.tenant_id OR NEW.connection_id IS DISTINCT FROM OLD.connection_id
               OR NEW.actor_id IS DISTINCT FROM OLD.actor_id OR NEW.tool IS DISTINCT FROM OLD.tool OR NEW.kind IS DISTINCT FROM OLD.kind
               OR NEW.arguments IS DISTINCT FROM OLD.arguments OR NEW.created_at IS DISTINCT FROM OLD.created_at
               OR NEW.project_id IS DISTINCT FROM OLD.project_id OR NEW.task_id IS DISTINCT FROM OLD.task_id THEN
                RAISE EXCEPTION 'tool_calls kaydının kimliği, aracı ve argümanları değiştirilemez';
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql
    """)
    op.execute("DROP TRIGGER IF EXISTS trg_tool_calls_guard ON tool_calls")
    op.execute("CREATE TRIGGER trg_tool_calls_guard BEFORE UPDATE OR DELETE ON tool_calls FOR EACH ROW EXECUTE FUNCTION tool_calls_guard()")
    op.execute("DROP TRIGGER IF EXISTS trg_tool_calls_no_truncate ON tool_calls")
    op.execute("CREATE TRIGGER trg_tool_calls_no_truncate BEFORE TRUNCATE ON tool_calls FOR EACH STATEMENT EXECUTE FUNCTION tool_calls_guard()")
    op.execute("""
        INSERT INTO system_permissions (id, code, module, name, description, default_for_roles, is_system, created_at)
        VALUES (gen_random_uuid(), 'integration:manage', 'INTEGRATIONS', 'Entegrasyon Yönetimi',
                'Dış sistem bağlantılarını (MCP) tanımlama, AI personele araç yetkisi verme, araç çağrılarını onaylama',
                '["SUPER_ADMIN", "COMPANY_ADMIN"]'::jsonb, TRUE, now())
        ON CONFLICT (code) DO NOTHING
    """)


def downgrade() -> None:
    op.execute("DELETE FROM system_permissions WHERE code = 'integration:manage'")
    op.execute("DROP TABLE IF EXISTS tool_calls")
    op.execute("DROP FUNCTION IF EXISTS tool_calls_guard()")
    op.execute("DROP TABLE IF EXISTS agent_tool_grants")
    op.execute("DROP TABLE IF EXISTS integration_connections")
