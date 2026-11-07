"""Senaryo (ADIM 17) Aşama 1 düzeltmeleri.

- tenants.custom_titles_override (#636): Merkez şirkete özel ünvan iznini paketten bağımsız açar/kapatır (None = paket).
- plans: şirkete özel ünvan PRO ve Kurumsal (ENTERPRISE) pakette açık (kullanıcı kararı 07.11.2026).
- recslip_exports.local_path (#658): aktarım dosyası RECOrion'a alınmaz; muhasebecinin indirdiği yer (isteğe bağlı).

Revision ID: 0047
Revises: 0046
"""
import sqlalchemy as sa
from alembic import op

revision = "0047"
down_revision = "0046"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("tenants", sa.Column("custom_titles_override", sa.Boolean()))
    op.add_column("recslip_exports", sa.Column("local_path", sa.String(500)))
    op.execute("UPDATE plans SET can_create_custom_titles = true WHERE code IN ('PRO', 'ENTERPRISE')")
    # #641 (F27): izin açıklaması gerçekteki özelliği anlatsın
    op.execute("UPDATE system_permissions SET description = 'AI Personel İşe Al sihirbazı; işe alınan personel için sektör ve ünvan Deep Search araştırması (Kaynaklar sekmesi).' WHERE code = 'agent:hire'")


def downgrade():
    op.drop_column("recslip_exports", "local_path")
    op.drop_column("tenants", "custom_titles_override")
