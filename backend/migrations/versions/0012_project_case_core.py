"""Proje/Case çekirdeği (ADIM 6, Odoo #252 / #288)

projects
  kind (PROJECT | CASE), requirements (isterler), manager_actor_id (insan proje yöneticisi), department_id,
  start_date / end_date, plan (Beyin AI iş adımları taslağı), simulation (süre / kredi / risk),
  planning_approved_at, ready_at, started_at, closed_at, close_summary, start_notified_at.
  Durumlar: DRAFT > PLANNING > READY > ACTIVE > (PAUSED) > COMPLETED | CANCELLED
project_members
  projedeki AI ve insan personel; rol: MANAGER, MEMBER (insan), AGENT (AI personel).
tasks
  order_index, department_id, job_title_id (gereken unvan), depends_on (görev kimlikleri), start_date, due_date,
  estimated_credits.
actors
  Telegram bildirimi: telegram_chat_id, telegram_link_code, telegram_linked_at.

Revision ID: 0012
Revises: 0011
Create Date: 2026-10-21
"""
import json

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0012"
down_revision = "0011"
branch_labels = None
depends_on = None

UUID = postgresql.UUID(as_uuid=True)

TEMPLATES = [
    ("PROJECT_START_REMINDER", "Proje Başlangıç Hatırlatması", "Projenizin başlangıç tarihi geldi: {{project_name}}",
     "<p>Merhaba {{contact_name}},</p><p><strong>{{project_name}}</strong> projesinin başlangıç tarihi ({{start_date}}) geldi "
     "ancak proje henüz başlatılmadı.</p><p>Projede {{agent_count}} AI personel ve {{task_count}} iş adımı hazır bekliyor. "
     "Projeyi başlatmak için RECOrion Work Space'e girin:</p><p><a href=\"{{project_url}}\">Projeyi aç</a></p>",
     ["contact_name", "project_name", "start_date", "agent_count", "task_count", "project_url"]),
]


def upgrade() -> None:
    for col in (
        sa.Column("kind", sa.String(16), server_default="PROJECT", nullable=False),
        sa.Column("requirements", sa.Text),
        sa.Column("manager_actor_id", UUID, sa.ForeignKey("actors.id", ondelete="SET NULL")),
        sa.Column("department_id", UUID, sa.ForeignKey("departments.id", ondelete="SET NULL")),
        sa.Column("start_date", sa.Date),
        sa.Column("end_date", sa.Date),
        sa.Column("plan", postgresql.JSONB),
        sa.Column("simulation", postgresql.JSONB),
        sa.Column("planning_approved_at", sa.DateTime(timezone=True)),
        sa.Column("ready_at", sa.DateTime(timezone=True)),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("closed_at", sa.DateTime(timezone=True)),
        sa.Column("close_summary", sa.Text),
        sa.Column("start_notified_at", sa.DateTime(timezone=True)),
    ):
        op.add_column("projects", col)
    op.create_index("ix_projects_tenant_status", "projects", ["tenant_id", "status"])

    op.create_table(
        "project_members",
        sa.Column("id", UUID, primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("project_id", UUID, sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("actor_id", UUID, sa.ForeignKey("actors.id", ondelete="CASCADE"), nullable=False),
        sa.Column("role", sa.String(16), nullable=False),  # MANAGER, MEMBER, AGENT
        sa.Column("added_by_actor_id", UUID),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.UniqueConstraint("project_id", "actor_id", name="uq_project_member"),
    )

    for col in (
        sa.Column("order_index", sa.Integer, server_default="0", nullable=False),
        sa.Column("department_id", UUID, sa.ForeignKey("departments.id", ondelete="SET NULL")),
        sa.Column("job_title_id", UUID, sa.ForeignKey("job_titles.id", ondelete="SET NULL")),
        sa.Column("depends_on", postgresql.JSONB, server_default=sa.text("'[]'::jsonb")),
        sa.Column("start_date", sa.Date),
        sa.Column("due_date", sa.Date),
        sa.Column("estimated_credits", sa.Numeric(14, 2)),
    ):
        op.add_column("tasks", col)

    op.add_column("actors", sa.Column("telegram_chat_id", sa.String(64)))
    op.add_column("actors", sa.Column("telegram_link_code", sa.String(16)))
    op.add_column("actors", sa.Column("telegram_linked_at", sa.DateTime(timezone=True)))
    op.create_index("ix_actors_telegram_code", "actors", ["telegram_link_code"])

    # Eski kayıtlar: oluşturan kişi proje yöneticisi ve ekip üyesi olur
    op.execute("UPDATE projects SET manager_actor_id = created_by_actor_id WHERE manager_actor_id IS NULL")
    op.execute("INSERT INTO project_members (project_id, actor_id, role) SELECT id, created_by_actor_id, 'MANAGER' "
               "FROM projects WHERE created_by_actor_id IS NOT NULL ON CONFLICT DO NOTHING")
    op.execute("INSERT INTO project_members (project_id, actor_id, role) SELECT DISTINCT t.project_id, t.assignee_actor_id, "
               "CASE WHEN a.actor_type = 'AI_AGENT' THEN 'AGENT' ELSE 'MEMBER' END FROM tasks t JOIN actors a ON a.id = t.assignee_actor_id "
               "ON CONFLICT DO NOTHING")

    bind = op.get_bind()
    for code, name, subject, html, variables in TEMPLATES:
        bind.execute(sa.text("INSERT INTO email_templates (code, name, subject, html_content, variables, is_active) "
                             "VALUES (:c, :n, :s, :h, CAST(:v AS jsonb), TRUE) ON CONFLICT (code) DO NOTHING"),
                     {"c": code, "n": name, "s": subject, "h": html, "v": json.dumps(variables)})


def downgrade() -> None:
    op.drop_index("ix_actors_telegram_code", "actors")
    for col in ("telegram_linked_at", "telegram_link_code", "telegram_chat_id"):
        op.drop_column("actors", col)
    for col in ("estimated_credits", "due_date", "start_date", "depends_on", "job_title_id", "department_id", "order_index"):
        op.drop_column("tasks", col)
    op.drop_table("project_members")
    op.drop_index("ix_projects_tenant_status", "projects")
    for col in ("start_notified_at", "close_summary", "closed_at", "started_at", "ready_at", "planning_approved_at",
                "simulation", "plan", "end_date", "start_date", "department_id", "manager_actor_id", "requirements", "kind"):
        op.drop_column("projects", col)
