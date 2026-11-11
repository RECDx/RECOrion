"""İSTEK #743: RECAi eğitim veri hattı.

- tenants.recai_training_consent: "RECAi model geliştirmeye katkı" izni — kullanıcı kararıyla VARSAYILAN AÇIK, şirket kapatabilir.
  Yalnız maskeli/anonim veri kullanılır. Kapatılınca sonraki veri setlerine girmez (önceden eğitilmiş modelden geri çıkarılamaz).
  Hukuki not ve gerekçe: Claude/senaryo/karar_ogrenme_recai.md §4.
- training_datasets: üretilen sürümlü veri setleri (yalnız sayılar ve depolama yolu; içerik MinIO'da, Merkez ekranında gösterilmez).

Revision ID: 0055
Revises: 0054
Create Date: 2026-11-11
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision = "0055"
down_revision = "0054"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("tenants", sa.Column("recai_training_consent", sa.Boolean, nullable=False, server_default=sa.true()))
    op.add_column("tenants", sa.Column("recai_training_consent_at", sa.DateTime(timezone=True)))
    op.add_column("tenants", sa.Column("recai_training_consent_by", UUID(as_uuid=True)))
    op.create_table(
        "training_datasets",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("version", sa.Integer, nullable=False, unique=True),
        sa.Column("status", sa.String(16), nullable=False, server_default="READY"),
        sa.Column("counts", JSONB, nullable=False, server_default="{}"),
        sa.Column("tenant_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("storage_prefix", sa.String(255)),
        sa.Column("delivered_at", sa.DateTime(timezone=True)),
        sa.Column("note", sa.Text),
        sa.Column("created_by_actor_id", UUID(as_uuid=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("training_datasets")
    op.drop_column("tenants", "recai_training_consent_by")
    op.drop_column("tenants", "recai_training_consent_at")
    op.drop_column("tenants", "recai_training_consent")
