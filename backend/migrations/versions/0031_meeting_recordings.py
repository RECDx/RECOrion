"""Toplantı kaydından proje taslağı (ADIM 11.3; kullanıcı kararı 24.10.2026: dosya yükleme + tarayıcıda kayıt)

meeting_recordings: yükleme/kayıt → yazıya çevirme (EVREN qwen3-asr-1.7b, 10 dk'lık parçalar) → KVKK maskeleme →
Beyin AI proje taslağı → kullanıcı onayıyla proje. Ham ses SAKLANMAZ (işlem bitince silinir; veri en aza indirme);
yalnızca maskeli metin ve taslak kalır. Şirket içeriğidir (KVKK: RECDx göremez).
model.default.transcription: yazıya çevirme modeli (altyapı modeli, paket listesinden bağımsız).

Revision ID: 0031
Revises: 0030
Create Date: 2026-10-24
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision = "0031"
down_revision = "0030"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "meeting_recordings",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("created_by_actor_id", UUID(as_uuid=True), sa.ForeignKey("actors.id", ondelete="SET NULL")),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("source", sa.String(16), nullable=False, server_default="UPLOAD"),
        sa.Column("status", sa.String(16), nullable=False, server_default="PROCESSING"),
        sa.Column("stage", sa.String(200)),
        sa.Column("duration_sec", sa.Numeric(10, 1)),
        sa.Column("transcript_masked", sa.Text),
        sa.Column("pii", JSONB),
        sa.Column("draft", JSONB),
        sa.Column("project_id", UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="SET NULL")),
        sa.Column("error", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_meeting_recordings_tenant", "meeting_recordings", ["tenant_id", "created_at"])
    op.execute("INSERT INTO system_settings (key, value, description) VALUES ('model.default.transcription', '\"qwen3-asr-1.7b\"', "
               "'Toplantı/ses kaydını yazıya çevirme modeli') ON CONFLICT (key) DO NOTHING")


def downgrade() -> None:
    op.execute("DELETE FROM system_settings WHERE key = 'model.default.transcription'")
    op.drop_index("ix_meeting_recordings_tenant", table_name="meeting_recordings")
    op.drop_table("meeting_recordings")
