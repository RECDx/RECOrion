"""Proje şablonları (ADIM 11.1; kullanıcı kararı 24.10.2026: şirket içi + RECDx platform şablonları, ücretli satış yok)

tenant_id NULL = RECDx platform şablonu (tüm şirketler görür; Süper Admin yönetir).
tenant_id dolu = şirket şablonu (yalnızca o şirket; KVKK: RECDx göremez).
plan: adımlar (başlık, açıklama, kabul ölçütü, departman, unvan, süre, bağımlılık, onay ayarları, şema konumu);
kişi kimliği (AI/insan personel, onaylayıcı), çıktı, ek ve yazışma içermez.
code: platform şablonlarının tohum kodu (açılışta yalnızca eksik olanlar eklenir).

Revision ID: 0029
Revises: 0028
Create Date: 2026-10-24
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision = "0029"
down_revision = "0028"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "project_templates",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE")),
        sa.Column("code", sa.String(64), unique=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("category", sa.String(80)),
        sa.Column("kind", sa.String(16), nullable=False, server_default="PROJECT"),
        sa.Column("field_package", sa.String(32), nullable=False, server_default="GENEL"),
        sa.Column("plan", JSONB, nullable=False),
        sa.Column("status", sa.String(16), nullable=False, server_default="ACTIVE"),
        sa.Column("source_project_id", UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="SET NULL")),
        sa.Column("use_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("created_by_actor_id", UUID(as_uuid=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_project_templates_tenant", "project_templates", ["tenant_id", "status"])
    op.add_column("projects", sa.Column("template_id", UUID(as_uuid=True), sa.ForeignKey("project_templates.id", ondelete="SET NULL")))


def downgrade() -> None:
    op.drop_column("projects", "template_id")
    op.drop_index("ix_project_templates_tenant", table_name="project_templates")
    op.drop_table("project_templates")
