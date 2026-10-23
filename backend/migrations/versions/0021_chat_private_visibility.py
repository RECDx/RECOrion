"""Özel yazışmanın görünürlüğü (ADIM 8.2)

- chat_messages.visible_to_actor_id: özel (is_private) mesaj yalnızca bu kişiye görünür. Kullanıcının özel sorusu ve
  AI'ın o soruya yanıtı soran kişiye aittir (önceden yanıt, gönderen = AI olduğu için soran kişiye görünmüyordu).
- Mevcut özel mesajlar gönderenlerine ait sayılır. Kayıt silinemez olduğundan geriye dönük doldurma tetikleyiciyi
  bu migrasyon süresince devre dışı bırakır.

Revision ID: 0021
Revises: 0020
Create Date: 2026-10-23
"""
from alembic import op

revision = "0021"
down_revision = "0020"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE chat_messages ADD COLUMN IF NOT EXISTS visible_to_actor_id UUID")
    op.execute("ALTER TABLE chat_messages DISABLE TRIGGER trg_chat_messages_append_only")
    op.execute("UPDATE chat_messages SET visible_to_actor_id = sender_actor_id WHERE is_private AND visible_to_actor_id IS NULL")
    op.execute("ALTER TABLE chat_messages ENABLE TRIGGER trg_chat_messages_append_only")


def downgrade() -> None:
    op.execute("ALTER TABLE chat_messages DISABLE TRIGGER trg_chat_messages_append_only")
    op.execute("ALTER TABLE chat_messages DROP COLUMN IF EXISTS visible_to_actor_id")
    op.execute("ALTER TABLE chat_messages ENABLE TRIGGER trg_chat_messages_append_only")
