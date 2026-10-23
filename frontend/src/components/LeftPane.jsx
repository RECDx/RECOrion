import React from 'react';
import { Bot, FolderKanban, Filter, Plus, User, Users } from 'lucide-react';
import { Badge } from '../ui/components';
import { KIND, statusOf } from './projects/projectMeta';
import './workarea.css';

// İş adımı durumu (backend task_flow.STATUS_LABELS ile aynı)
const TASK_STATUS = {
  BACKLOG: ['Sırada', 'neutral'], READY: ['Başlayabilir', 'info'], IN_PROGRESS: ['Çalışılıyor', 'info'],
  WAITING_APPROVAL: ['Onay bekliyor', 'warning'], REVISION: ['Revizyonda', 'danger'], QUARANTINED: ['Karantinada', 'danger'],
  DONE: ['Tamamlandı', 'success'], CANCELLED: ['İptal', 'neutral'],
};
const ROLE = { MANAGER: 'Proje yöneticisi', MEMBER: 'Ekip üyesi', AGENT: 'AI personel' };
const FILTERS = [['ALL', 'Tüm ekip'], ['MY', 'Benim'], ['A2A', 'Ajanlar arası']];

/** Çalışma Alanı sol bölmesi (Adım 8.3): proje seçimi, gerçek ilerleme, iş adımları ve proje ekibi. */
export default function LeftPane({
  project, projects = [], onSelectProject, members = [], flowTasks = {}, canManage,
  tasks, selectedTask, onSelectTask, chatFilter, onSetChatFilter, onCreateTaskModal,
}) {
  const done = tasks?.filter((t) => t.status === 'DONE').length || 0;
  const total = tasks?.length || 0;
  const count = (...s) => tasks?.filter((t) => s.includes(t.status)).length || 0;
  const pst = statusOf(project?.status);

  return (
    <aside className="pane" style={{ borderRight: '1px solid var(--border-subtle)' }}>
      <div className="pane-header" style={{ display: 'block' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <FolderKanban size={18} className="ui-text-accent" />
          {projects.length > 1 ? (
            <select className="ui-input wa-project-select" aria-label="Proje seç" value={project?.id || ''}
              onChange={(e) => onSelectProject?.(projects.find((p) => p.id === e.target.value))}>
              {projects.map((p) => <option key={p.id} value={p.id}>{p.name} · {statusOf(p.status).label}</option>)}
            </select>
          ) : (
            <strong style={{ fontSize: '0.875rem' }}>{project?.name || 'Henüz proje yok'}</strong>
          )}
        </div>
        {project && (
          <div className="wa-meta">
            <span>{KIND[project.kind] || 'Proje'}</span><span>·</span><span>{project.slug}</span>
            <Badge tone={pst.tone}>{pst.label}</Badge>
          </div>
        )}
      </div>

      <div className="pane-content">
        {total > 0 && (
          <div className="wa-progress" aria-label="İlerleme">
            <div className="wa-progress-head"><span>İlerleme</span><strong>{done} / {total} adım tamamlandı</strong></div>
            <div className="wa-progress-track"><div className="wa-progress-bar" style={{ width: `${Math.round((done / total) * 100)}%` }} /></div>
            <div className="wa-progress-counts">
              <span>Çalışılıyor: {count('IN_PROGRESS', 'REVISION')}</span>
              <span>Onay bekliyor: {count('WAITING_APPROVAL')}</span>
              {count('QUARANTINED') > 0 && <span className="ui-text-danger">Karantina: {count('QUARANTINED')}</span>}
            </div>
          </div>
        )}

        <div>
          <div className="wa-section-title"><Filter size={12} />Sohbet görünümü</div>
          <div className="ui-segmented" role="tablist" aria-label="Sohbet görünümü" style={{ width: '100%' }}>
            {FILTERS.map(([k, l]) => (
              <button key={k} type="button" role="tab" aria-selected={chatFilter === k}
                className={`ui-segmented-item ${chatFilter === k ? 'active' : ''}`} style={{ flex: 1 }} onClick={() => onSetChatFilter(k)}>{l}</button>
            ))}
          </div>
        </div>

        <div>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '6px' }}>
            <span className="wa-section-title" style={{ margin: 0 }}>İş adımları ({total})</span>
            {canManage && ['DRAFT', 'PLANNING', 'READY', 'ACTIVE', 'PAUSED'].includes(project?.status) && (
              <button type="button" onClick={onCreateTaskModal} className="btn btn-secondary" style={{ padding: '3px 8px', fontSize: '0.7rem' }}>
                <Plus size={12} />Yeni adım
              </button>
            )}
          </div>
          {total === 0 ? <p className="pj-hint">Bu projede henüz iş adımı yok. Plan Projeler ekranında onaylanınca adımlar burada görünür.</p> : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
              {tasks.map((t) => {
                const f = flowTasks[t.id];
                const [label, tone] = TASK_STATUS[t.status] || [t.status, 'neutral'];
                return (
                  <button key={t.id} type="button" className={`wa-task ${selectedTask?.id === t.id ? 'active' : ''}`}
                    aria-current={selectedTask?.id === t.id} onClick={() => onSelectTask(t)}>
                    <span className="wa-task-top">
                      <span className="wa-task-title">{t.order_index ? `${t.order_index}. ` : ''}{t.title}</span>
                      <Badge tone={tone}>{label}</Badge>
                    </span>
                    <span className="wa-task-sub">
                      {f?.assignee ? <>{f.assignee.type === 'AI_AGENT' ? <Bot size={11} /> : <User size={11} />}{f.assignee.name}</> : 'Atanmadı'}
                      {f?.ai_working && <span className="wa-working">· AI çalışıyor</span>}
                      {f?.artifact && <span>· sürüm {f.artifact.version}</span>}
                    </span>
                  </button>
                );
              })}
            </div>
          )}
        </div>

        <div>
          <div className="wa-section-title"><Users size={13} />Proje ekibi ({members.length})</div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
            {members.map((m) => (
              <div key={m.actor_id} className="wa-member">
                {m.actor_type === 'AI_AGENT' ? <Bot size={14} className="ui-text-accent" /> : <User size={14} className="ui-text-success" />}
                <div>
                  <div className="wa-member-name">{m.display_name}</div>
                  <div className="wa-member-role">{ROLE[m.role] || m.role}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </aside>
  );
}
