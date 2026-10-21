"""İş akışı motoru (ADIM 7.1): iş adımı akış alanları ve silinemez olay geçmişi

- tasks: kontrol personeli, onaylayıcı, onay gerekliliği, ret sayısı/sınırı, akış zamanları
- projects: Temporal akış kimliği
- task_events: iş adımının tüm akış olayları (yalnızca ekleme; güncelleme tetikleyiciyle engellenir)

Revision ID: 0014
Revises: 0013
Create Date: 2026-10-22
"""
from alembic import op

revision = "0014"
down_revision = "0013"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        ALTER TABLE tasks
            ADD COLUMN IF NOT EXISTS reviewer_actor_id UUID REFERENCES actors(id) ON DELETE SET NULL,
            ADD COLUMN IF NOT EXISTS approver_actor_id UUID REFERENCES actors(id) ON DELETE SET NULL,
            ADD COLUMN IF NOT EXISTS requires_approval BOOLEAN NOT NULL DEFAULT TRUE,
            ADD COLUMN IF NOT EXISTS max_rejections INTEGER NOT NULL DEFAULT 3,
            ADD COLUMN IF NOT EXISTS rejection_count INTEGER NOT NULL DEFAULT 0,
            ADD COLUMN IF NOT EXISTS started_at TIMESTAMPTZ,
            ADD COLUMN IF NOT EXISTS submitted_at TIMESTAMPTZ,
            ADD COLUMN IF NOT EXISTS completed_at TIMESTAMPTZ
    """)
    op.execute("ALTER TABLE projects ADD COLUMN IF NOT EXISTS workflow_id VARCHAR(128)")
    op.execute("""
        CREATE TABLE IF NOT EXISTS task_events (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
            project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
            task_id UUID REFERENCES tasks(id) ON DELETE CASCADE,
            kind VARCHAR(32) NOT NULL,
            actor_id UUID REFERENCES actors(id) ON DELETE SET NULL,
            note TEXT,
            data JSONB NOT NULL DEFAULT '{}'::jsonb,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_task_events_project ON task_events (project_id, created_at)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_task_events_task ON task_events (task_id, created_at)")
    # Olay geçmişi değiştirilemez (proje/şirket silinince CASCADE ile toplu silme serbest)
    op.execute("""
        CREATE OR REPLACE FUNCTION task_events_immutable() RETURNS trigger AS $$
        BEGIN
            RAISE EXCEPTION 'task_events kayıtları değiştirilemez';
        END;
        $$ LANGUAGE plpgsql
    """)
    op.execute("DROP TRIGGER IF EXISTS trg_task_events_immutable ON task_events")
    op.execute("CREATE TRIGGER trg_task_events_immutable BEFORE UPDATE ON task_events FOR EACH ROW EXECUTE FUNCTION task_events_immutable()")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS task_events")
    op.execute("DROP FUNCTION IF EXISTS task_events_immutable()")
    op.execute("ALTER TABLE projects DROP COLUMN IF EXISTS workflow_id")
    op.execute("""
        ALTER TABLE tasks
            DROP COLUMN IF EXISTS reviewer_actor_id, DROP COLUMN IF EXISTS approver_actor_id,
            DROP COLUMN IF EXISTS requires_approval, DROP COLUMN IF EXISTS max_rejections,
            DROP COLUMN IF EXISTS rejection_count, DROP COLUMN IF EXISTS started_at,
            DROP COLUMN IF EXISTS submitted_at, DROP COLUMN IF EXISTS completed_at
    """)
