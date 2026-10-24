"""Edge Connector (ADIM 10.5): müşteri sunucusundaki ajan (Logo/Mikro vb.) yalnızca dışa bağlanır, iş kuyruğundan iş alır

integration_connections:
- agent_token_hash: ajan anahtarının SHA-256 özeti (anahtar bir kez gösterilir, saklanmaz)
- agent_seen_at: ajanın son yoklaması (çevrimiçi/çevrimdışı)
- agent_info: ajanın bildirdiği sürüm, sunucu adı ve izinli sorgu şablonları kataloğu (SQL yok; yalnızca ad, açıklama, parametreler, tür)
edge_jobs: araç çağrısının ajana giden işi (QUEUED → RUNNING → DONE/FAILED; süresi dolan EXPIRED)

Revision ID: 0028
Revises: 0027
Create Date: 2026-10-24
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision = "0028"
down_revision = "0027"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("integration_connections", sa.Column("agent_token_hash", sa.String(64)))
    op.add_column("integration_connections", sa.Column("agent_seen_at", sa.DateTime(timezone=True)))
    op.add_column("integration_connections", sa.Column("agent_info", JSONB))
    op.create_index("ix_integration_connections_agent_token", "integration_connections", ["agent_token_hash"], unique=True,
                    postgresql_where=sa.text("agent_token_hash IS NOT NULL"))
    op.create_table(
        "edge_jobs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("connection_id", UUID(as_uuid=True), sa.ForeignKey("integration_connections.id", ondelete="CASCADE"), nullable=False),
        sa.Column("template", sa.String(100), nullable=False),
        sa.Column("params", JSONB, nullable=False, server_default="{}"),
        sa.Column("status", sa.String(16), nullable=False, server_default="QUEUED"),
        sa.Column("result", JSONB),
        sa.Column("error", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("picked_at", sa.DateTime(timezone=True)),
        sa.Column("done_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_edge_jobs_queue", "edge_jobs", ["connection_id", "status", "created_at"])


def downgrade() -> None:
    op.drop_index("ix_edge_jobs_queue", table_name="edge_jobs")
    op.drop_table("edge_jobs")
    op.drop_index("ix_integration_connections_agent_token", table_name="integration_connections")
    op.drop_column("integration_connections", "agent_info")
    op.drop_column("integration_connections", "agent_seen_at")
    op.drop_column("integration_connections", "agent_token_hash")
