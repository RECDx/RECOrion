"""İzin kataloğu güncellemesi (ADIM 16.3, #611-#613).

- İşleve bağlı olmayan iki izin kaldırıldı: billing:topup (Ek Kredi ve Paket Talebi), chat:export (Sohbeti Dışa Aktarma).
  Sistem rollerinden, şirkete özel rollerden ve kullanıcı ek izinlerinden de çıkarılır.
- "Sektörel Manifesto Yönetimi" açıklamasındaki NACE ifadesi kaldırıldı (NACE sistemden çıkarılmıştı, #304).
- role:edit / role:delete (şirkete özel rol düzenleme/silme) ve chat:view_a2a artık kodda denetleniyor; veri değişikliği gerekmez.

Revision ID: 0046
Revises: 0045
"""
import sqlalchemy as sa
from alembic import op

revision = "0046"
down_revision = "0045"
branch_labels = None
depends_on = None

REMOVED = ("billing:topup", "chat:export")
MANIFESTO_NEW = "Şirketin sektör ve meslek bilgilerini ve kurumsal manifestoyu düzenleme, RECAi'ye yazdırma."
MANIFESTO_OLD = "Sektörler, NACE kodları ve kurumsal manifestoyu düzenleme, RECAi'ye yazdırma."
AUDITOR = "Güvenlik ve Uyum Denetçisi"
AUDITOR_NEW = "Salt okunur denetim: panolar, maliyet ve kredi, ajanlar arası konuşmalar."
AUDITOR_OLD = "Salt okunur denetim: panolar, maliyet ve kredi, ajanlar arası konuşmalar, sohbet dışa aktarma."


def upgrade() -> None:
    conn = op.get_bind()
    for code in REMOVED:
        conn.execute(sa.text("DELETE FROM system_permissions WHERE code = :c"), dict(c=code))
        has = dict(c=code, j=f'["{code}"]')
        conn.execute(sa.text("UPDATE tenant_roles SET permissions = permissions - CAST(:c AS text) WHERE permissions @> CAST(:j AS jsonb)"), has)
        conn.execute(sa.text("UPDATE actors SET extra_permissions = extra_permissions - CAST(:c AS text) "
                             "WHERE extra_permissions @> CAST(:j AS jsonb)"), has)
    conn.execute(sa.text("UPDATE system_permissions SET description = :d WHERE code = 'manifesto:manage'"), dict(d=MANIFESTO_NEW))
    conn.execute(sa.text("UPDATE tenant_roles SET description = :d WHERE tenant_id IS NULL AND name = :n"), dict(d=AUDITOR_NEW, n=AUDITOR))


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(sa.text("UPDATE system_permissions SET description = :d WHERE code = 'manifesto:manage'"), dict(d=MANIFESTO_OLD))
    conn.execute(sa.text("UPDATE tenant_roles SET description = :d WHERE tenant_id IS NULL AND name = :n"), dict(d=AUDITOR_OLD, n=AUDITOR))
    conn.execute(sa.text(
        "INSERT INTO system_permissions (code, module, name, description, default_for_roles, is_system) VALUES "
        "('billing:topup', 'BILLING', 'Ek Kredi ve Paket Talebi', 'RECDx''ten ek kredi veya paket değişikliği talep etme.', "
        "'[\"Süper Yönetici (Platform Admin)\", \"Şirket Yöneticisi\", \"Finans ve Raporlama Sorumlusu\"]'::jsonb, true), "
        "('chat:export', 'CHAT', 'Sohbeti Dışa Aktarma', 'Sohbet ve düşünce akışını dışa aktarma.', "
        "'[\"Süper Yönetici (Platform Admin)\", \"Şirket Yöneticisi\", \"Güvenlik ve Uyum Denetçisi\"]'::jsonb, true) ON CONFLICT (code) DO NOTHING"))
