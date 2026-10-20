"""Platform departman ve unvan kataloğu (ADIM 5.1, Odoo #270)

- catalog_departments: genel (GENERAL) ve sektöre özel (SECTOR) platform departmanları;
  ilgili meslek grupları profession_codes içinde tutulur.
- job_titles: platform kataloğu alanları (departman, kapsam, sektör, meslek grupları, kıdem,
  sorumluluklar, başarı ölçütleri, kaynak). Şirket unvanı katalogdan alındıysa source_title_id.
  Platform unvan kodları benzersizdir.
- departments: şirket departmanı katalogdan alındıysa catalog_department_id.

Revision ID: 0008
Revises: 0007
Create Date: 2026-10-20
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0008"
down_revision = "0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "catalog_departments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("code", sa.String(64), nullable=False, unique=True),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("scope", sa.String(16), nullable=False, server_default="GENERAL"),  # GENERAL, SECTOR
        sa.Column("sector_code", sa.String(32), sa.ForeignKey("sectors.code", ondelete="CASCADE"), nullable=True),
        sa.Column("profession_codes", postgresql.JSONB, nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("sort_order", sa.Integer, nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_catalog_departments_sector", "catalog_departments", ["sector_code"])

    op.add_column("job_titles", sa.Column("catalog_department_id", postgresql.UUID(as_uuid=True),
                                          sa.ForeignKey("catalog_departments.id", ondelete="SET NULL")))
    op.add_column("job_titles", sa.Column("scope", sa.String(16)))  # GENERAL, SECTOR (platform), COMPANY
    op.add_column("job_titles", sa.Column("sector_code", sa.String(32)))
    op.add_column("job_titles", sa.Column("profession_codes", postgresql.JSONB, server_default=sa.text("'[]'::jsonb")))
    op.add_column("job_titles", sa.Column("seniority", sa.String(16)))
    op.add_column("job_titles", sa.Column("responsibilities", postgresql.JSONB, server_default=sa.text("'[]'::jsonb")))
    op.add_column("job_titles", sa.Column("kpis", postgresql.JSONB, server_default=sa.text("'[]'::jsonb")))
    op.add_column("job_titles", sa.Column("source", sa.String(16)))  # CATALOG, ADMIN, COMPANY
    op.add_column("job_titles", sa.Column("source_title_id", postgresql.UUID(as_uuid=True),
                                          sa.ForeignKey("job_titles.id", ondelete="SET NULL")))
    op.add_column("job_titles", sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")))
    op.alter_column("job_titles", "recommended_model_code", server_default=None)
    op.execute("UPDATE job_titles SET scope = CASE WHEN tenant_id IS NULL THEN 'GENERAL' ELSE 'COMPANY' END, "
               "source = CASE WHEN tenant_id IS NULL THEN 'ADMIN' ELSE 'COMPANY' END")
    op.create_index("ix_job_titles_catalog_department", "job_titles", ["catalog_department_id"])
    op.create_index("ix_job_titles_sector", "job_titles", ["sector_code"])
    op.execute("CREATE UNIQUE INDEX uq_job_titles_platform_code ON job_titles (code) WHERE tenant_id IS NULL")

    op.add_column("departments", sa.Column("catalog_department_id", postgresql.UUID(as_uuid=True),
                                           sa.ForeignKey("catalog_departments.id", ondelete="SET NULL")))


def downgrade() -> None:
    op.drop_column("departments", "catalog_department_id")
    op.execute("DROP INDEX IF EXISTS uq_job_titles_platform_code")
    for col in ("updated_at", "source_title_id", "source", "kpis", "responsibilities", "seniority",
                "profession_codes", "sector_code", "scope", "catalog_department_id"):
        op.drop_column("job_titles", col)
    op.drop_table("catalog_departments")
