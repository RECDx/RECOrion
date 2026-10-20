"""LLM Gateway ve kredi muhasebesi; şirket Beyin AI modeli

- credit_ledger: değiştirilemez kredi defteri (aylık hak, ek kredi, kullanım, süre sonu, düzeltme).
  Bakiye = tutarların toplamı. UPDATE/DELETE/TRUNCATE tetikleyiciyle engellenir.
- llm_calls: amaç, model kodu, proje ve hata alanları; şirket/kullanıcı bağı silinse de kayıt kalsın
  diye yabancı anahtarlar kaldırılır.
- tenants.brain_model_code: şirketin Beyin AI (organizatör) modeli.
- Varsayılan model ayarları ve kredi uyarı e-posta şablonları.

Revision ID: 0007
Revises: 0006
Create Date: 2026-10-20
"""
import json

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None

MODEL_SETTINGS = {
    "model.default.chat": ("mimo-v2.6-pro", "AI personel sohbetlerinde model belirtilmemişse kullanılan model"),
    "model.default.brain": ("mimo-v2.6-pro", "Şirketler Beyin AI modeli seçmemişse kullanılan organizatör model"),
    "model.platform_assistant": ("mimo-v2.6-pro", "Süper Yönetici asistanının (Ana AI) modeli"),
    "model.default.embedding": ("qwen3-embedding-8b", "Hafıza vektörleme modeli"),
    "model.default.rerank": ("qwen3-reranker-8b", "Hafıza arama sonuçlarını yeniden sıralama modeli"),
}

TEMPLATES = [
    ("CREDIT_LOW", "Kredi Uyarısı (%80)", "RECOrion kredinizin %{{percent}}'i kullanıldı - {{company_name}}",
     "<p>Sayın {{contact_name}},</p><p><strong>{{company_name}}</strong> şirketinin {{period}} dönemi aylık RECOrion "
     "kredisinin <strong>%{{percent}}</strong>'i kullanıldı. Kalan kredi: <strong>{{remaining}}</strong>.</p>"
     "<p>Kredi bittiğinde AI personelleriniz yeni işlem yapamaz. Ek kredi veya paket yükseltme için info@recdx.com "
     "adresinden bize ulaşabilirsiniz.</p>", ["contact_name", "company_name", "period", "percent", "remaining"]),
    ("CREDIT_EXHAUSTED", "Kredi Tükendi", "RECOrion krediniz tükendi - {{company_name}}",
     "<p>Sayın {{contact_name}},</p><p><strong>{{company_name}}</strong> şirketinin {{period}} dönemi RECOrion kredisi "
     "tükendi. AI personelleriniz yeni dönem başlayana veya ek kredi yüklenene kadar işlem yapamaz.</p>"
     "<p>Ek kredi için info@recdx.com adresinden bize ulaşabilirsiniz.</p>", ["contact_name", "company_name", "period"]),
]


def upgrade() -> None:
    op.create_table(
        "credit_ledger",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("entry_type", sa.String(24), nullable=False),  # MONTHLY_GRANT, TOPUP, USAGE, EXPIRE, ADJUSTMENT
        sa.Column("amount", sa.Numeric(16, 4), nullable=False),
        sa.Column("period", sa.String(7), nullable=False),  # YYYY-MM
        sa.Column("llm_call_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("note", sa.Text),
        sa.Column("created_by_actor_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_credit_ledger_tenant_period", "credit_ledger", ["tenant_id", "period"])
    # Aynı dönem için tek aylık hak ve tek süre sonu kaydı
    op.execute("CREATE UNIQUE INDEX uq_credit_ledger_monthly ON credit_ledger (tenant_id, period, entry_type) "
               "WHERE entry_type IN ('MONTHLY_GRANT', 'EXPIRE')")
    op.execute("""
        CREATE OR REPLACE FUNCTION credit_ledger_block_mutation() RETURNS trigger AS $$
        BEGIN
            RAISE EXCEPTION 'credit_ledger değiştirilemez (yalnızca ekleme yapılabilir)';
        END;
        $$ LANGUAGE plpgsql
    """)
    op.execute("CREATE TRIGGER trg_credit_ledger_no_update_delete BEFORE UPDATE OR DELETE ON credit_ledger "
               "FOR EACH ROW EXECUTE FUNCTION credit_ledger_block_mutation()")
    op.execute("CREATE TRIGGER trg_credit_ledger_no_truncate BEFORE TRUNCATE ON credit_ledger "
               "FOR EACH STATEMENT EXECUTE FUNCTION credit_ledger_block_mutation()")

    for fk in ("llm_calls_tenant_id_fkey", "llm_calls_actor_id_fkey", "llm_calls_task_id_fkey", "llm_calls_model_id_fkey"):
        op.execute(f"ALTER TABLE llm_calls DROP CONSTRAINT IF EXISTS {fk}")
    op.add_column("llm_calls", sa.Column("purpose", sa.String(32)))
    op.add_column("llm_calls", sa.Column("model_code", sa.String(128)))
    op.add_column("llm_calls", sa.Column("project_id", postgresql.UUID(as_uuid=True)))
    op.add_column("llm_calls", sa.Column("error", sa.Text))
    op.create_index("ix_llm_calls_tenant_created", "llm_calls", ["tenant_id", "created_at"])

    op.add_column("tenants", sa.Column("brain_model_code", sa.String(128)))

    # EVREN model kataloğu bilgileri (EVREN /models senkronundan gelir)
    op.add_column("llm_models", sa.Column("evren_task", sa.String(32)))
    op.add_column("llm_models", sa.Column("modalities", postgresql.JSONB))
    op.add_column("llm_models", sa.Column("max_output_tokens", sa.Integer))
    op.add_column("llm_models", sa.Column("prompt_token_price", sa.Numeric(18, 8)))
    op.add_column("llm_models", sa.Column("completion_token_price", sa.Numeric(18, 8)))
    op.add_column("llm_models", sa.Column("pricing_currency", sa.String(8)))
    op.add_column("llm_models", sa.Column("free_until", sa.Date))
    op.add_column("llm_models", sa.Column("last_synced_at", sa.DateTime(timezone=True)))
    # EVREN'in bu çağrı için ayırdığı/düştüğü kredi (CR) ve çağrı sırasında kalan EVREN bakiyesi
    op.add_column("llm_calls", sa.Column("evren_credits", sa.Numeric(18, 6)))
    op.add_column("llm_calls", sa.Column("evren_balance_after", sa.Numeric(18, 4)))

    bind = op.get_bind()
    for key, (value, desc) in MODEL_SETTINGS.items():
        bind.execute(sa.text("INSERT INTO system_settings (key, value, description) VALUES (:k, CAST(:v AS jsonb), :d) "
                             "ON CONFLICT (key) DO NOTHING"), {"k": key, "v": json.dumps(value), "d": desc})
    for code, name, subject, html, variables in TEMPLATES:
        bind.execute(sa.text("INSERT INTO email_templates (code, name, subject, html_content, variables, is_active) "
                             "VALUES (:c, :n, :s, :h, CAST(:v AS jsonb), TRUE) ON CONFLICT (code) DO NOTHING"),
                     {"c": code, "n": name, "s": subject, "h": html, "v": json.dumps(variables)})


def downgrade() -> None:
    op.drop_column("tenants", "brain_model_code")
    for col in ("last_synced_at", "free_until", "pricing_currency", "completion_token_price", "prompt_token_price",
                "max_output_tokens", "modalities", "evren_task"):
        op.drop_column("llm_models", col)
    for col in ("evren_balance_after", "evren_credits"):
        op.drop_column("llm_calls", col)
    for col in ("error", "project_id", "model_code", "purpose"):
        op.drop_column("llm_calls", col)
    op.drop_table("credit_ledger")
    op.execute("DROP FUNCTION IF EXISTS credit_ledger_block_mutation()")
