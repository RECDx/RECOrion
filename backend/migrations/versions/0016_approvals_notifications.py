"""Her yerden onay ve bildirim kanalları (ADIM 7.3)

- approval_tokens: e-posta/Telegram onay bağlantıları için tek kullanımlık, süreli belirteçler (yalnızca özeti saklanır);
  belirteç belirli bir teslime (submitted_at) bağlıdır, yeni teslim veya karar eski belirteçleri geçersiz kılar
- actors.notification_prefs: kişinin bildirim kanalı tercihleri ({"email": true, "telegram": true})
- e-posta şablonları: onay isteği, yeni iş adımı, revizyon, dikkat gerektiren adım, proje akışı bitti

Revision ID: 0016
Revises: 0015
Create Date: 2026-10-22
"""
import json

import sqlalchemy as sa
from alembic import op

revision = "0016"
down_revision = "0015"
branch_labels = None
depends_on = None

BTN = ('display:inline-block;padding:10px 18px;border-radius:8px;text-decoration:none;font-weight:600;color:#ffffff;'
       'background:{bg};margin-right:8px')
TEMPLATES = [
    ("TASK_APPROVAL_REQUEST", "İş Adımı Onay İsteği", "Onayınız bekleniyor: {{task_title}}",
     "<p>Merhaba {{contact_name}},</p><p><strong>{{project_name}}</strong> projesinde <strong>{{task_title}}</strong> iş adımı "
     "{{submitted_by}} tarafından teslim edildi ve onayınızı bekliyor.</p><p>{{submit_note}}</p>"
     f"<p><a href=\"{{{{approve_url}}}}\" style=\"{BTN.format(bg='#10b981')}\">İncele ve karar ver</a></p>"
     "<p style=\"color:#64748b;font-size:12px\">Bağlantı yalnızca size özeldir, tek kullanımlıktır ve {{expires_at}} tarihine kadar "
     "geçerlidir. Başkasıyla paylaşmayın. Kararı RECOrion Work Space'teki Onaylarım ekranından da verebilirsiniz.</p>",
     ["contact_name", "project_name", "task_title", "submitted_by", "submit_note", "approve_url", "expires_at"]),
    ("TASK_ASSIGNED", "Yeni İş Adımı", "Size yeni bir iş adımı açıldı: {{task_title}}",
     "<p>Merhaba {{contact_name}},</p><p><strong>{{project_name}}</strong> projesinde size <strong>{{task_title}}</strong> iş adımı "
     "açıldı.</p><p><a href=\"{{project_url}}\">Projeyi aç</a></p>",
     ["contact_name", "project_name", "task_title", "project_url"]),
    ("TASK_REVISION", "Revizyon İstendi", "Revizyon istendi: {{task_title}}",
     "<p>Merhaba {{contact_name}},</p><p><strong>{{project_name}}</strong> projesindeki <strong>{{task_title}}</strong> iş adımı "
     "revizyona gönderildi.</p><p>Gerekçe: {{note}}</p><p><a href=\"{{project_url}}\">Projeyi aç</a></p>",
     ["contact_name", "project_name", "task_title", "note", "project_url"]),
    ("TASK_ATTENTION", "Kararınız Gereken İş Adımı", "Kararınız bekleniyor: {{task_title}}",
     "<p>Merhaba {{contact_name}},</p><p><strong>{{project_name}}</strong> projesindeki <strong>{{task_title}}</strong> iş adımı "
     "durdu: {{reason}}</p><p>Yeniden denemeye veya iptal etmeye siz karar verin.</p><p><a href=\"{{project_url}}\">Projeyi aç</a></p>",
     ["contact_name", "project_name", "task_title", "reason", "project_url"]),
    ("PROJECT_FINISHED", "Proje İş Adımları Tamamlandı", "Tüm iş adımları tamamlandı: {{project_name}}",
     "<p>Merhaba {{contact_name}},</p><p><strong>{{project_name}}</strong> projesinin tüm iş adımları tamamlandı. Kapanış özetini "
     "yazıp projeyi kapatabilir, onaylı ekleri Kurum Hafızasına aktarabilirsiniz.</p><p><a href=\"{{project_url}}\">Projeyi aç</a></p>",
     ["contact_name", "project_name", "project_url"]),
]


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS approval_tokens (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            token_hash VARCHAR(64) NOT NULL UNIQUE,
            task_id UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
            actor_id UUID NOT NULL REFERENCES actors(id) ON DELETE CASCADE,
            channel VARCHAR(16) NOT NULL,
            submitted_at TIMESTAMPTZ,
            expires_at TIMESTAMPTZ NOT NULL,
            used_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_approval_tokens_task ON approval_tokens (task_id)")
    op.execute("ALTER TABLE actors ADD COLUMN IF NOT EXISTS notification_prefs JSONB NOT NULL DEFAULT '{}'::jsonb")
    bind = op.get_bind()
    for code, name, subject, html, variables in TEMPLATES:
        bind.execute(sa.text("INSERT INTO email_templates (code, name, subject, html_content, variables, is_active) "
                             "VALUES (:c, :n, :s, :h, CAST(:v AS jsonb), TRUE) ON CONFLICT (code) DO NOTHING"),
                     {"c": code, "n": name, "s": subject, "h": html, "v": json.dumps(variables)})


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS approval_tokens")
    op.execute("ALTER TABLE actors DROP COLUMN IF EXISTS notification_prefs")
    op.execute("DELETE FROM email_templates WHERE code IN ('TASK_APPROVAL_REQUEST', 'TASK_ASSIGNED', 'TASK_REVISION', "
               "'TASK_ATTENTION', 'PROJECT_FINISHED')")
