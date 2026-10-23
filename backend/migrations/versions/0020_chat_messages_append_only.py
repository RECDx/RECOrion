"""Silinemez mesaj kaydı (ADIM 8.1)

- chat_messages: UPDATE ve TRUNCATE her zaman, DELETE ise yalnızca şirket kaydı silinirken (KVKK, işlem içinde
  `recorion.purge_tenant` = o şirketin kimliği) yapılabilir. İş adımı/proje silinince mesajlar sessizce gitmez.
- Gönderen personel silinse de mesaj kalır: sender_actor_id yabancı anahtarı kaldırılır, gönderenin adı
  yazıldığı anda sender_name alanına kaydedilir.

Revision ID: 0020
Revises: 0019
Create Date: 2026-10-23
"""
from alembic import op

revision = "0020"
down_revision = "0019"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE chat_messages DROP CONSTRAINT IF EXISTS chat_messages_sender_actor_id_fkey")
    op.execute("ALTER TABLE chat_messages ADD COLUMN IF NOT EXISTS sender_name VARCHAR(255)")
    op.execute("""
        UPDATE chat_messages m SET sender_name = a.display_name
        FROM actors a WHERE a.id = m.sender_actor_id AND m.sender_name IS NULL
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_chat_messages_tenant_sender ON chat_messages (tenant_id, sender_actor_id, created_at)")
    op.execute("""
        CREATE OR REPLACE FUNCTION chat_messages_fill_sender() RETURNS trigger AS $$
        BEGIN
            IF NEW.sender_name IS NULL AND NEW.sender_actor_id IS NOT NULL THEN
                SELECT display_name INTO NEW.sender_name FROM actors WHERE id = NEW.sender_actor_id;
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql
    """)
    op.execute("DROP TRIGGER IF EXISTS trg_chat_messages_fill_sender ON chat_messages")
    op.execute("""
        CREATE TRIGGER trg_chat_messages_fill_sender BEFORE INSERT ON chat_messages
        FOR EACH ROW EXECUTE FUNCTION chat_messages_fill_sender()
    """)
    op.execute("""
        CREATE OR REPLACE FUNCTION chat_messages_append_only() RETURNS trigger AS $$
        BEGIN
            IF TG_OP = 'DELETE' AND OLD.tenant_id::text = COALESCE(current_setting('recorion.purge_tenant', true), '') THEN
                RETURN OLD;
            END IF;
            RAISE EXCEPTION 'chat_messages kayıtları değiştirilemez ve silinemez (yalnızca ekleme yapılabilir)';
        END;
        $$ LANGUAGE plpgsql
    """)
    op.execute("DROP TRIGGER IF EXISTS trg_chat_messages_append_only ON chat_messages")
    op.execute("""
        CREATE TRIGGER trg_chat_messages_append_only BEFORE UPDATE OR DELETE ON chat_messages
        FOR EACH ROW EXECUTE FUNCTION chat_messages_append_only()
    """)
    op.execute("DROP TRIGGER IF EXISTS trg_chat_messages_no_truncate ON chat_messages")
    op.execute("""
        CREATE TRIGGER trg_chat_messages_no_truncate BEFORE TRUNCATE ON chat_messages
        FOR EACH STATEMENT EXECUTE FUNCTION chat_messages_append_only()
    """)


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS trg_chat_messages_no_truncate ON chat_messages")
    op.execute("DROP TRIGGER IF EXISTS trg_chat_messages_append_only ON chat_messages")
    op.execute("DROP TRIGGER IF EXISTS trg_chat_messages_fill_sender ON chat_messages")
    op.execute("DROP FUNCTION IF EXISTS chat_messages_append_only()")
    op.execute("DROP FUNCTION IF EXISTS chat_messages_fill_sender()")
    op.execute("ALTER TABLE chat_messages DROP COLUMN IF EXISTS sender_name")
    op.execute("DROP INDEX IF EXISTS ix_chat_messages_tenant_sender")
