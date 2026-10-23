"""Departman panosu yetkisi (ADIM 9.3)

- department:dashboard: kendi departmanının insan ve AI personelinin iş durumunu ve AI karnesini görme.
  Varsayılan olarak şirket yöneticisine; şirket yöneticisi rol ekranından departman müdürü gibi rollere verebilir.
  Parasal bilgiler (TL maliyet, bütçe, tahmini tasarruf) ayrıca billing:view ister.

Revision ID: 0024
Revises: 0023
Create Date: 2026-10-23
"""
from alembic import op

revision = "0024"
down_revision = "0023"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        INSERT INTO system_permissions (id, code, module, name, description, default_for_roles, is_system, created_at)
        VALUES (gen_random_uuid(), 'department:dashboard', 'REPORTS', 'Departman Panosu',
                'Kendi departmanının insan ve AI personelinin iş durumunu ve AI personel karnesini görme',
                '["SUPER_ADMIN", "COMPANY_ADMIN"]'::jsonb, TRUE, now())
        ON CONFLICT (code) DO NOTHING
    """)


def downgrade() -> None:
    op.execute("DELETE FROM system_permissions WHERE code = 'department:dashboard'")
