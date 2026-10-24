"""Türkiye mevzuat bilgi paketleri (ADIM 11.2; kullanıcı kararı 24.10.2026: ilk özet kartları Claude hazırlar,
RECDx uzmanı kontrol edip yayımlamadan müşteriye/AI personele açılmaz)

regulation_packs: platform içeriği (müşteri verisi yok).
- draft: düzenlenen taslak {cards: [...]} — yalnızca RECDx Süper Admin görür
- published: uzman kontrolünden geçmiş yayın {version, cards, published_at, reviewer_name, review_note, checked_at};
  müşteriler ve AI personel yalnızca bunu görür. Yeni yayın sürüm numarasını artırır.
tenant_regulation_packs: şirketin açtığı paketler (AI personel bu paketlerin kartlarını kaynak göstererek kullanır).
Taslak kartlar app/seed/regulation_packs.json'dan açılışta yalnızca eksik paketler için yüklenir.

Revision ID: 0030
Revises: 0029
Create Date: 2026-10-24
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision = "0030"
down_revision = "0029"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "regulation_packs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("code", sa.String(40), nullable=False, unique=True),
        sa.Column("title", sa.String(120), nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("draft", JSONB, nullable=False, server_default='{"cards": []}'),
        sa.Column("published", JSONB),
        sa.Column("draft_updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_table(
        "tenant_regulation_packs",
        sa.Column("tenant_id", UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("pack_id", UUID(as_uuid=True), sa.ForeignKey("regulation_packs.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("enabled_by_actor_id", UUID(as_uuid=True)),
        sa.Column("enabled_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("tenant_regulation_packs")
    op.drop_table("regulation_packs")
