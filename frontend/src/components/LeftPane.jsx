import React, { useState } from 'react';
import { 
  FolderKanban, 
  CheckCircle2, 
  Clock, 
  Users, 
  Bot, 
  User, 
  Plus, 
  Filter, 
  GitBranch, 
  Sparkles,
  ChevronRight,
  Shield,
  Layers
} from 'lucide-react';

export default function LeftPane({ 
  project, 
  tasks, 
  selectedTask, 
  onSelectTask, 
  actors, 
  chatFilter, 
  onSetChatFilter,
  onCreateTaskModal
}) {
  const [filterType, setFilterType] = useState('ALL'); // ALL, MY, A2A

  const handleFilterChange = (type) => {
    setFilterType(type);
    onSetChatFilter(type);
  };

  return (
    <aside className="pane" style={{ borderRight: '1px solid var(--border-subtle)' }}>
      {/* Pane Header: Project Details */}
      <div className="pane-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <FolderKanban size={18} color="#6366f1" />
          <div>
            <div style={{ fontSize: '0.875rem', fontWeight: '700' }}>
              {project?.name || 'Vaka Projesi Yükleniyor...'}
            </div>
            <div style={{ fontSize: '0.7rem', color: 'var(--text-dim)', display: 'flex', gap: '6px' }}>
              <span>Kod: {project?.slug || 'REC-001'}</span>
              <span>•</span>
              <span style={{ color: '#22d3ee' }}>{project?.field_package || 'YAZILIM'}</span>
            </div>
          </div>
        </div>
      </div>

      <div className="pane-content">
        {/* Workflow State Machine Pipeline Overview */}
        <div style={{
          padding: '10px 12px',
          borderRadius: '10px',
          background: 'rgba(99, 102, 241, 0.08)',
          border: '1px solid rgba(99, 102, 241, 0.2)'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
            <span style={{ fontSize: '0.72rem', fontWeight: '700', color: '#818cf8', display: 'flex', alignItems: 'center', gap: '5px' }}>
              <GitBranch size={13} />
              OTONOM İŞ AKIŞI ZİNCİRİ
            </span>
            <span style={{ fontSize: '0.65rem', color: 'var(--text-dim)' }}>Temporal Engine</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: '0.68rem', color: 'var(--text-muted)' }}>
            <span style={{ color: '#38bdf8', fontWeight: '600' }}>Analist</span>
            <span>➔</span>
            <span style={{ color: '#c084fc', fontWeight: '600' }}>Mimar</span>
            <span>➔</span>
            <span style={{ color: '#34d399', fontWeight: '600' }}>Coder</span>
            <span>➔</span>
            <span style={{ color: '#f59e0b', fontWeight: '600' }}>QA</span>
          </div>
        </div>

        {/* Chat Visibility Filter Bar (Proje İçi Şeffaflık) */}
        <div>
          <div style={{ fontSize: '0.72rem', fontWeight: '700', color: 'var(--text-dim)', marginBottom: '6px', display: 'flex', alignItems: 'center', gap: '5px' }}>
            <Filter size={12} />
            SOHBET VE GÖRÜNÜM FİLTRESİ
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '4px' }}>
            <button 
              onClick={() => handleFilterChange('ALL')}
              className="btn btn-secondary"
              style={{
                fontSize: '0.68rem',
                padding: '6px 4px',
                background: filterType === 'ALL' ? 'rgba(99, 102, 241, 0.25)' : 'rgba(255, 255, 255, 0.03)',
                borderColor: filterType === 'ALL' ? '#6366f1' : 'var(--border-subtle)',
                color: filterType === 'ALL' ? '#818cf8' : 'var(--text-muted)'
              }}
            >
              Tüm Ekip
            </button>
            <button 
              onClick={() => handleFilterChange('MY')}
              className="btn btn-secondary"
              style={{
                fontSize: '0.68rem',
                padding: '6px 4px',
                background: filterType === 'MY' ? 'rgba(16, 185, 129, 0.25)' : 'rgba(255, 255, 255, 0.03)',
                borderColor: filterType === 'MY' ? '#10b981' : 'var(--border-subtle)',
                color: filterType === 'MY' ? '#34d399' : 'var(--text-muted)'
              }}
            >
              Benim
            </button>
            <button 
              onClick={() => handleFilterChange('A2A')}
              className="btn btn-secondary"
              style={{
                fontSize: '0.68rem',
                padding: '6px 4px',
                background: filterType === 'A2A' ? 'rgba(168, 85, 247, 0.25)' : 'rgba(255, 255, 255, 0.03)',
                borderColor: filterType === 'A2A' ? '#a855f7' : 'var(--border-subtle)',
                color: filterType === 'A2A' ? '#c084fc' : 'var(--text-muted)'
              }}
            >
              Ajanlar Arası
            </button>
          </div>
        </div>

        {/* Tasks Section */}
        <div>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
            <span style={{ fontSize: '0.75rem', fontWeight: '700', color: 'var(--text-dim)' }}>
              GÖREVLER ({tasks?.length || 0})
            </span>
            <button 
              onClick={onCreateTaskModal}
              className="btn btn-secondary"
              style={{ padding: '3px 8px', fontSize: '0.7rem' }}
            >
              <Plus size={12} />
              Yeni Görev
            </button>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
            {tasks?.map((t) => {
              const isSelected = selectedTask?.id === t.id;
              return (
                <div 
                  key={t.id}
                  onClick={() => onSelectTask(t)}
                  style={{
                    padding: '10px 12px',
                    borderRadius: '8px',
                    background: isSelected ? 'rgba(99, 102, 241, 0.16)' : 'rgba(255, 255, 255, 0.02)',
                    border: `1px solid ${isSelected ? '#6366f1' : 'var(--border-subtle)'}`,
                    cursor: 'pointer',
                    transition: 'all 0.15s ease'
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '4px' }}>
                    <span style={{ fontSize: '0.8rem', fontWeight: '600', color: isSelected ? '#ffffff' : 'var(--text-main)' }}>
                      {t.title}
                    </span>
                    <span className="badge" style={{
                      fontSize: '0.6rem',
                      background: t.priority === 'HIGH' ? 'rgba(244, 63, 94, 0.18)' : 'rgba(148, 163, 184, 0.12)',
                      color: t.priority === 'HIGH' ? '#f43f5e' : '#cbd5e1'
                    }}>
                      {t.priority}
                    </span>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: '0.68rem', color: 'var(--text-dim)' }}>
                    <span>Durum: <b style={{ color: '#38bdf8' }}>{t.status}</b></span>
                    <span>Efor: {t.estimated_effort} sp</span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Assigned Team Section */}
        <div>
          <div style={{ fontSize: '0.75rem', fontWeight: '700', color: 'var(--text-dim)', marginBottom: '8px', display: 'flex', alignItems: 'center', gap: '6px' }}>
            <Users size={14} />
            PROJE EKİBİ & AI PERSONELLERİ
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
            {actors?.map((a) => (
              <div 
                key={a.id}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  padding: '7px 10px',
                  borderRadius: '8px',
                  background: 'rgba(255, 255, 255, 0.02)',
                  border: '1px solid var(--border-subtle)'
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <div style={{
                    width: '26px',
                    height: '26px',
                    borderRadius: '6px',
                    background: a.actor_type === 'AI_AGENT' ? 'rgba(99, 102, 241, 0.2)' : 'rgba(16, 185, 129, 0.2)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center'
                  }}>
                    {a.actor_type === 'AI_AGENT' ? (
                      <Bot size={14} color="#818cf8" />
                    ) : (
                      <User size={14} color="#34d399" />
                    )}
                  </div>
                  <div>
                    <div style={{ fontSize: '0.78rem', fontWeight: '600' }}>
                      {a.display_name}
                    </div>
                    <div style={{ fontSize: '0.66rem', color: 'var(--text-dim)' }}>
                      {a.role}
                    </div>
                  </div>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                  <span className={`badge ${a.autonomy_level === 'L3' ? 'badge-l3' : a.autonomy_level === 'L2' ? 'badge-l2' : 'badge-l1'}`} style={{ fontSize: '0.62rem' }}>
                    {a.autonomy_level}
                  </span>
                  <span style={{ width: '6px', height: '6px', borderRadius: '50%', background: a.status === 'IDLE' ? '#10b981' : '#f59e0b' }}></span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </aside>
  );
}
