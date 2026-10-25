"""RECAi adları (#349; kullanıcı kararı 25.10.2026): müşteriye EVREN model adları yerine RECAi adları.

recai_tiers: RECAi adı → arkasındaki model (+ yedek). kind CHAT: unvan/AI personelde seçilebilir (Mergen, Hızlı, Derin);
  kind CAPABILITY: pakette yetenek (Görsel, Ses, Okur) — purpose ile ilgili LLM çağrısında kullanılır. Modeli yalnızca
  RECDx Süper Admin değiştirir; müşteride ad değişmez.
plans.recai_tiers: paketteki seçilebilir adlar; plans.features: vision_enabled, transcription_enabled, ocr_enabled.
actors.recai_tier, actors.recai_capabilities (personel bazında Görsel/Ses/Okur açık-kapalı), job_titles.recommended_tier,
tenants.brain_tier. Mevcut model seçimleri eşleşen ada taşınır.

Revision ID: 0039
Revises: 0038
Create Date: 2026-10-25
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision = "0039"
down_revision = "0038"
branch_labels = None
depends_on = None

TIERS = [
    ("MERGEN", "RECAi Mergen", "CHAT", None, "Genel iş, planlama ve analiz için dengeli RECAi.", "deepseek-v4-flash", "mimo-v2.6-pro", 10),
    ("HIZLI", "RECAi Hızlı", "CHAT", None, "Kısa ve hızlı yanıtlar; yoğun günlük işler için.", "qwen3.8-flash-next", "deepseek-v4-flash", 20),
    ("DERIN", "RECAi Derin", "CHAT", None, "Uzun analiz ve dikkatli akıl yürütme gerektiren işler için.", "mimo-v2.6-pro", "deepseek-v4.1-flash", 30),
    ("GORSEL", "RECAi Görsel", "CAPABILITY", "VISION", "Görsel, şema ve fotoğrafları anlama.", "qwen3-vl-30b", None, 40),
    ("SES", "RECAi Ses", "CAPABILITY", "TRANSCRIPTION", "Toplantı ve ses kayıtlarını yazıya çevirme.", "qwen3-asr-1.7b", None, 50),
    ("OKUR", "RECAi Okur", "CAPABILITY", "OCR", "Fiş, fatura ve taranmış belgeleri okuma.", "deepseek-ocr-2", "dots-ocr", 60),
]
# Mevcut model seçimlerinin taşınacağı ad
MODEL_TO_TIER = {"deepseek-v4-flash": "MERGEN", "auto": "HIZLI", "qwen3.8-flash-next": "HIZLI", "gemma-4-31b": "HIZLI",
                 "mimo-v2.6-pro": "DERIN", "deepseek-v4.1-flash": "DERIN", "glm-5.3": "DERIN"}


def upgrade() -> None:
    op.create_table(
        "recai_tiers",
        sa.Column("code", sa.String(16), primary_key=True),
        sa.Column("name", sa.String(64), nullable=False),
        sa.Column("kind", sa.String(16), nullable=False),
        sa.Column("purpose", sa.String(32)),
        sa.Column("description", sa.Text),
        sa.Column("model_code", sa.String(128), nullable=False),
        sa.Column("fallback_model_code", sa.String(128)),
        sa.Column("sort", sa.Integer, nullable=False, server_default="100"),
        sa.Column("updated_by_actor_id", sa.dialects.postgresql.UUID(as_uuid=True)),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    t = sa.table("recai_tiers", sa.column("code"), sa.column("name"), sa.column("kind"), sa.column("purpose"), sa.column("description"),
                 sa.column("model_code"), sa.column("fallback_model_code"), sa.column("sort"))
    op.bulk_insert(t, [dict(zip(("code", "name", "kind", "purpose", "description", "model_code", "fallback_model_code", "sort"), r)) for r in TIERS])

    op.add_column("plans", sa.Column("recai_tiers", JSONB, nullable=False, server_default=sa.text("'[]'::jsonb")))
    op.add_column("actors", sa.Column("recai_tier", sa.String(16)))
    op.add_column("actors", sa.Column("recai_capabilities", JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")))
    op.add_column("job_titles", sa.Column("recommended_tier", sa.String(16)))
    op.add_column("tenants", sa.Column("brain_tier", sa.String(16)))

    case = "CASE lower({col}) " + " ".join(f"WHEN '{m}' THEN '{t}'" for m, t in MODEL_TO_TIER.items()) + " ELSE 'MERGEN' END"
    op.execute(f"UPDATE actors a SET recai_tier = {case.format(col='m.model_code')} FROM llm_models m WHERE m.id = a.preferred_model_id")
    op.execute(f"UPDATE job_titles SET recommended_tier = {case.format(col='recommended_model_code')} WHERE recommended_model_code IS NOT NULL")
    op.execute(f"UPDATE tenants SET brain_tier = {case.format(col='brain_model_code')} WHERE brain_model_code IS NOT NULL")
    # Paketler: modellerinden adlar ve yetenekler
    for tier, models in (("MERGEN", ["deepseek-v4-flash"]), ("HIZLI", ["qwen3.8-flash-next", "gemma-4-31b", "auto"]),
                         ("DERIN", ["mimo-v2.6-pro", "deepseek-v4.1-flash", "glm-5.3"])):
        cond = " OR ".join(f"allowed_models ? '{m}'" for m in models)
        op.execute(f"UPDATE plans SET recai_tiers = recai_tiers || '[\"{tier}\"]'::jsonb WHERE {cond}")
    op.execute("UPDATE plans SET recai_tiers = '[\"MERGEN\"]'::jsonb WHERE recai_tiers = '[]'::jsonb")
    op.execute("""UPDATE plans SET features = coalesce(features, '{}'::jsonb)
                  || jsonb_build_object('vision_enabled', allowed_models ? 'qwen3-vl-30b',
                                        'transcription_enabled', allowed_models ? 'qwen3-asr-1.7b')""")


def downgrade() -> None:
    op.drop_column("tenants", "brain_tier")
    op.drop_column("job_titles", "recommended_tier")
    op.drop_column("actors", "recai_capabilities")
    op.drop_column("actors", "recai_tier")
    op.drop_column("plans", "recai_tiers")
    op.drop_table("recai_tiers")
