"""Doküman hattı (ADIM 5.4, Odoo #273 / #268)

agent_documents tablosu üç katmandaki öğrenme dokümanlarını taşıyacak şekilde genişletilir:
  AGENT          AI personelin dokümanı (şirket içeriği)
  COMPANY_TITLE  şirket unvanının dokümanı (o unvandaki tüm AI personel öğrenir; şirket içeriği)
  PLATFORM_TITLE katalog unvanının dokümanı (tüm müşterilere açık genel bilgi; tenant_id boş)

Hat: yükleme (MinIO) > metin çıkarma / OCR / görsel açıklama > içerik güvenliği (guard) > KVKK maskeleme >
parçalama > öğrenme kartı (özet + anahtar bilgiler + test soruları) > insan onayı > vektörleme.
Yeni sürüm yüklenince eski sürüm onay anında SUPERSEDED olur ve vektörleri silinir.

Revision ID: 0009
Revises: 0008
Create Date: 2026-10-20
"""
import json

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0009"
down_revision = "0008"
branch_labels = None
depends_on = None

SETTINGS = {
    "model.default.ocr": ("deepseek-ocr-2", "Taranmış belge ve görsellerden metin okuma (OCR) modeli"),
    "model.guard": ("qwen3-guard-4b", "Doküman içerik güvenliği (zararlı içerik / prompt saldırısı) modeli"),
    "model.default.vision": ("qwen3-vl-30b", "Görselleri (fotoğraf, şema, çizim) açıklayıp öğrenilebilir metne çeviren model"),
}


def upgrade() -> None:
    op.alter_column("agent_documents", "tenant_id", nullable=True)
    op.alter_column("agent_documents", "agent_id", nullable=True)
    cols = [
        sa.Column("layer", sa.String(24), server_default="AGENT", nullable=False),
        sa.Column("job_title_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("job_titles.id", ondelete="CASCADE")),
        sa.Column("storage_key", sa.String(512)),  # MinIO nesne anahtarı
        sa.Column("sha256", sa.String(64)),
        sa.Column("version", sa.Integer, server_default="1", nullable=False),
        sa.Column("previous_document_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("agent_documents.id", ondelete="SET NULL")),
        sa.Column("masked_text", sa.Text),
        sa.Column("pii_findings", postgresql.JSONB),
        sa.Column("guard_result", postgresql.JSONB),
        sa.Column("page_count", sa.Integer),
        sa.Column("ocr_pages", sa.Integer),
        sa.Column("image_count", sa.Integer),  # görsel modelle açıklanan görsel sayısı
        sa.Column("chunk_count", sa.Integer),
        sa.Column("learning_card", postgresql.JSONB),  # {summary, key_points[], quiz[{question, options[], answer}]}
        sa.Column("test_result", postgresql.JSONB),
        sa.Column("error", sa.Text),
        sa.Column("uploaded_by_actor_id", postgresql.UUID(as_uuid=True)),
        sa.Column("approved_by_actor_id", postgresql.UUID(as_uuid=True)),
        sa.Column("approved_at", sa.DateTime(timezone=True)),
    ]
    for col in cols:
        op.add_column("agent_documents", col)
    op.create_index("ix_agent_documents_job_title", "agent_documents", ["job_title_id"])
    op.create_index("ix_agent_documents_sha", "agent_documents", ["sha256"])

    op.create_table(
        "document_chunks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("document_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("agent_documents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("idx", sa.Integer, nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("qdrant_point_id", postgresql.UUID(as_uuid=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_document_chunks_document", "document_chunks", ["document_id", "idx"])

    bind = op.get_bind()
    for key, (value, desc) in SETTINGS.items():
        bind.execute(sa.text("INSERT INTO system_settings (key, value, description) VALUES (:k, CAST(:v AS jsonb), :d) "
                             "ON CONFLICT (key) DO NOTHING"), {"k": key, "v": json.dumps(value), "d": desc})


def downgrade() -> None:
    op.drop_table("document_chunks")
    op.drop_index("ix_agent_documents_sha", "agent_documents")
    op.drop_index("ix_agent_documents_job_title", "agent_documents")
    for col in ("approved_at", "approved_by_actor_id", "uploaded_by_actor_id", "error", "test_result", "learning_card",
                "chunk_count", "image_count", "ocr_pages", "page_count", "guard_result", "pii_findings", "masked_text",
                "previous_document_id", "version", "sha256", "storage_key", "job_title_id", "layer"):
        op.drop_column("agent_documents", col)
