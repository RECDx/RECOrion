"""İSTEK #747: ek kredi satın alma — kredi paketleri (Merkez tanımı, Odoo ürünü), kredi siparişleri (Odoo satış siparişi,
havale/EFT Merkez onayıyla yükleme, 7 gün sonra otomatik iptal), e-posta şablonları ve banka bilgisi ayarı.

Revision ID: 0058
Revises: 0057
Create Date: 2026-11-16
"""
import json

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0058"
down_revision = "0057"
branch_labels = None
depends_on = None

ORDER_HTML = ("<p>Merhaba {{contact_name}},</p><p><strong>{{company_name}}</strong> için <strong>{{credits}} kredi</strong> "
              "siparişiniz alındı (sipariş no: <strong>{{order_name}}</strong>, tutar {{amount}} TL + KDV).</p>"
              "<p>Havale/EFT açıklamasına sipariş numarasını yazın. Ödeme RECDx'e ulaşınca krediniz yüklenir ve size bildirilir. "
              "Ödeme {{valid_days}} gün içinde gelmezse sipariş kendiliğinden iptal edilir.</p>"
              "<pre style=\"white-space:pre-wrap;font-family:inherit\">{{bank_info}}</pre>")
LOADED_HTML = ("<p>Merhaba {{contact_name}},</p><p><strong>{{company_name}}</strong> hesabına <strong>{{credits}} kredi</strong> "
               "yüklendi (sipariş no: {{order_name}}). Kredi nedeniyle duraklayan işleriniz Kredi ve Kullanım ekranından "
               "devam ettirilebilir.</p>")


def upgrade() -> None:
    op.create_table(
        "credit_packs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("code", sa.String(32), nullable=False, unique=True),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("credits", sa.Integer, nullable=False),
        sa.Column("price_try", sa.Numeric(14, 2)),  # KDV hariç; boşsa satışa kapalı
        sa.Column("odoo_product_id", sa.Integer),
        sa.Column("plan_codes", postgresql.JSONB, nullable=False, server_default=sa.text("'[]'::jsonb")),  # boş = tüm paketler
        sa.Column("sort_order", sa.Integer, nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_table(
        "credit_orders",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("pack_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("credit_packs.id", ondelete="SET NULL")),
        sa.Column("pack_name", sa.String(128), nullable=False),
        sa.Column("credits", sa.Integer, nullable=False),
        sa.Column("price_try", sa.Numeric(14, 2), nullable=False),
        sa.Column("payment_method", sa.String(16), nullable=False),  # TRANSFER, CARD
        sa.Column("status", sa.String(16), nullable=False, server_default="PENDING"),  # PENDING, LOADED, CANCELLED, EXPIRED
        sa.Column("odoo_order_id", sa.Integer),
        sa.Column("odoo_order_name", sa.String(64)),
        sa.Column("odoo_invoice_ids", postgresql.JSONB),
        sa.Column("ledger_entry_id", postgresql.UUID(as_uuid=True), unique=True),  # bir sipariş yalnız bir kez kredi yükler
        sa.Column("created_by_actor_id", postgresql.UUID(as_uuid=True)),
        sa.Column("decided_by_actor_id", postgresql.UUID(as_uuid=True)),
        sa.Column("decided_at", sa.DateTime(timezone=True)),
        sa.Column("expires_at", sa.DateTime(timezone=True)),
        sa.Column("note", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_credit_orders_status", "credit_orders", ["status"])
    bind = op.get_bind()
    for i, n in enumerate((5000, 10000, 15000, 20000)):  # fiyat ve Odoo ürünü Merkez'de girilir; o zamana kadar satışa kapalı
        bind.execute(sa.text("INSERT INTO credit_packs (code, name, credits, sort_order, is_active) VALUES (:c, :n, :k, :o, false) "
                             "ON CONFLICT (code) DO NOTHING"),
                     {"c": f"KREDI-{n // 1000}K", "n": f"{n:,} Kredi".replace(",", "."), "k": n, "o": i + 1})
    for code, name, subject, html, variables in (
        ("CREDIT_ORDER_CREATED", "Ek Kredi Siparişi Alındı", "{{company_name}} — {{credits}} kredi siparişi ({{order_name}})", ORDER_HTML,
         ["contact_name", "company_name", "credits", "order_name", "amount", "bank_info", "valid_days"]),
        ("CREDIT_ORDER_LOADED", "Ek Kredi Yüklendi", "{{company_name}} — {{credits}} kredi yüklendi", LOADED_HTML,
         ["contact_name", "company_name", "credits", "order_name"])):
        bind.execute(sa.text("INSERT INTO email_templates (code, name, subject, html_content, variables, is_active) "
                             "VALUES (:c, :n, :s, :h, CAST(:v AS jsonb), TRUE) ON CONFLICT (code) DO NOTHING"),
                     {"c": code, "n": name, "s": subject, "h": html, "v": json.dumps(variables)})


def downgrade() -> None:
    op.get_bind().execute(sa.text("DELETE FROM email_templates WHERE code IN ('CREDIT_ORDER_CREATED', 'CREDIT_ORDER_LOADED')"))
    op.drop_index("ix_credit_orders_status", table_name="credit_orders")
    op.drop_table("credit_orders")
    op.drop_table("credit_packs")
