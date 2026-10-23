import React, { useCallback, useState } from 'react';
import {
  ShieldCheck,
  CheckCircle2,
  RotateCcw,
  Building2,
  Bot,
  ArrowUpRight,
  FileCode2,
  Database,
  Eye
} from 'lucide-react';
import { Badge } from '../ui/components';
import { ArtifactModal } from './projects/WorkflowTab';
import './workarea.css';

// Kalite kapısı iş adımının gerçek akış durumunu gösterir (ADIM 7.1); renkler tema tonlarından
const GATE = {
  WAITING_APPROVAL: ['Onay bekliyor', 'warning'], DONE: ['Onaylandı', 'success'], REVISION: ['Revizyonda', 'danger'],
  QUARANTINED: ['Karantinada', 'danger'], IN_PROGRESS: ['Çalışılıyor', 'info'], CANCELLED: ['İptal', 'neutral'],
};
const fmtTime = (d) => (d ? new Date(d).toLocaleString('tr-TR', { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' }) : '');

export default function RightPane({
  selectedTask,
  flowTask,
  memoryItems,
  onPromoteMemory,
  onApproveQualityGate,
  onRejectQualityGate,
  onSubmitTask
}) {
  const [activeTab, setActiveTab] = useState('GLOBAL'); // GLOBAL vs AGENT
  const [viewing, setViewing] = useState(false);
  const closeViewer = useCallback(() => setViewing(false), []);
  const status = selectedTask?.status;
  const [gateLabel, gateTone] = GATE[status] || ['Sırada', 'neutral'];
  const art = flowTask?.artifact;

  const filteredMemories = memoryItems?.filter((m) => m.scope === activeTab) || [];

  return (
    <aside className="pane" style={{ borderLeft: '1px solid var(--border-subtle)', background: 'var(--bg-surface)' }}>
      <div className="pane-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <ShieldCheck size={18} className="ui-text-success" />
          <span style={{ fontSize: '0.875rem', fontWeight: '700' }}>
            Kalite Kapısı & Kurum Hafızası
          </span>
        </div>
      </div>

      <div className="pane-content">
        {/* 1. KALİTE KAPISI: karar düğmeleri yalnızca yetkisi olana (Adım 8.3) */}
        <div className="wa-artifact">
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
            <span className="wa-section-title" style={{ margin: 0 }}><ShieldCheck size={14} />Görev kalite kapısı</span>
            <Badge tone={gateTone}>{gateLabel}</Badge>
          </div>
          <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', lineHeight: 1.5, marginBottom: '10px' }}>
            {flowTask?.reviewer ? `Çıktı önce kontrol personeli ${flowTask.reviewer.name} tarafından değerlendirilir. ` : ''}
            {flowTask?.requires_approval === false ? 'Bu adım insan onayı gerektirmez.'
              : `Onaylayıcı: ${flowTask?.approver?.name || 'proje yöneticisi'}.`}
          </p>
          {status === 'WAITING_APPROVAL' && flowTask?.can_decide && (
            <div className="ui-grid-2" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
              <button onClick={() => onApproveQualityGate?.(selectedTask)} className="btn btn-success" style={{ fontSize: '0.75rem', padding: '7px' }}>
                <CheckCircle2 size={13} />
                Onayla & İlerlet
              </button>
              <button onClick={() => onRejectQualityGate?.(selectedTask)} className="btn btn-secondary" style={{ fontSize: '0.75rem', padding: '7px' }}>
                <RotateCcw size={13} />
                Revizyon İste
              </button>
            </div>
          )}
          {status === 'WAITING_APPROVAL' && flowTask && !flowTask.can_decide && (
            <p className="pj-hint" style={{ margin: 0 }}>Karar {flowTask.approver?.name || 'onaylayıcı'} tarafından verilecek.</p>
          )}
          {flowTask?.can_submit && (
            <button onClick={() => onSubmitTask?.(selectedTask)} className="btn btn-primary" style={{ fontSize: '0.75rem', padding: '7px', width: '100%' }}>
              <CheckCircle2 size={13} />
              Çıktıyı teslim et
            </button>
          )}
          {status === 'QUARANTINED' && (
            <p className="ui-text-danger" style={{ fontSize: '0.72rem', margin: 0 }}>
              Bu adım {selectedTask?.rejection_count} kez reddedildi. Kararı proje yöneticisi Projeler &gt; İş Akışı ekranından verir.
            </p>
          )}
        </div>

        {/* 2. ÇIKTI: adımın gerçek son sürümü ve tüm sürümleri (Adım 8.3) */}
        <div className="wa-artifact">
          <div className="wa-section-title"><FileCode2 size={13} />Adımın çıktısı</div>
          {!selectedTask ? <p className="pj-hint" style={{ margin: 0 }}>Bir iş adımı seçin.</p> : !art ? (
            <p className="pj-hint" style={{ margin: 0 }}>Henüz çıktı yok. {flowTask?.ai_working ? 'AI personel çalışıyor; çıktı hazır olunca burada görünür.' : ''}</p>
          ) : (
            <>
              <div className="wa-artifact-name">{art.name}</div>
              <div className="wa-meta" style={{ marginTop: 0, marginBottom: '8px' }}>Sürüm {art.version} · {fmtTime(art.created_at)}</div>
              <button type="button" className="btn btn-secondary" style={{ fontSize: '0.75rem', padding: '6px', width: '100%' }} onClick={() => setViewing(true)}>
                <Eye size={13} />
                Çıktıyı gör{art.version > 1 ? ' (sürümler)' : ''}
              </button>
            </>
          )}
        </div>
        {viewing && art && <ArtifactModal task={{ id: selectedTask.id, title: selectedTask.title }} artifactId={art.id} onClose={closeViewer} />}

        {/* 3. 2 KADEMELİ KOLEKTİF HAFIZA YÖNETİCİSİ */}
        <div>
          <div style={{ fontSize: '0.75rem', fontWeight: '700', color: 'var(--text-dim)', marginBottom: '8px', display: 'flex', alignItems: 'center', gap: '6px' }}>
            <Database size={13} color="#a855f7" />
            2 KADEMELİ KOLEKTİF HAFIZA (QDRANT)
          </div>

          {/* Scope Tabs */}
          <div className="ui-grid-2" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '4px', marginBottom: '10px' }}>
            <button 
              onClick={() => setActiveTab('GLOBAL')}
              className="btn btn-secondary"
              style={{
                fontSize: '0.7rem',
                padding: '6px',
                background: activeTab === 'GLOBAL' ? 'rgba(99, 102, 241, 0.25)' : 'transparent',
                borderColor: activeTab === 'GLOBAL' ? '#6366f1' : 'var(--border-subtle)',
                color: activeTab === 'GLOBAL' ? 'var(--ac-818cf8)' : 'var(--text-muted)'
              }}
            >
              <Building2 size={12} />
              Kurum Hafızası (Global)
            </button>
            <button 
              onClick={() => setActiveTab('AGENT')}
              className="btn btn-secondary"
              style={{
                fontSize: '0.7rem',
                padding: '6px',
                background: activeTab === 'AGENT' ? 'rgba(6, 182, 212, 0.25)' : 'transparent',
                borderColor: activeTab === 'AGENT' ? '#06b6d4' : 'var(--border-subtle)',
                color: activeTab === 'AGENT' ? 'var(--ac-22d3ee)' : 'var(--text-muted)'
              }}
            >
              <Bot size={12} />
              Ajan Hafızası (Agent)
            </button>
          </div>

          {/* Memory Items List */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', maxHeight: '250px', overflowY: 'auto' }}>
            {filteredMemories.length === 0 ? (
              <div style={{ fontSize: '0.72rem', color: 'var(--text-dim)', textAlign: 'center', padding: '15px' }}>
                Bu kategoride kayıt bulunamadı.
              </div>
            ) : (
              filteredMemories.map((m) => (
                <div 
                  key={m.id}
                  style={{
                    padding: '10px',
                    borderRadius: '8px',
                    background: 'rgb(var(--rgb-ov) / 0.02)',
                    border: '1px solid var(--border-subtle)',
                    fontSize: '0.75rem'
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '4px' }}>
                    <span style={{ fontWeight: '600', color: m.scope === 'GLOBAL' ? 'var(--ac-818cf8)' : 'var(--ac-22d3ee)' }}>
                      {m.scope === 'GLOBAL' ? '🏢 Kurumsal Know-How' : '🤖 Ajan Tecrübesi'}
                    </span>
                    <span style={{ fontSize: '0.62rem', color: 'var(--text-dim)' }}>
                      Skor: {m.confidence_score || '1.0'}
                    </span>
                  </div>

                  <p style={{ color: 'var(--text-muted)', lineHeight: 1.4, marginBottom: '6px' }}>
                    {m.content}
                  </p>

                  {/* Promote Button (Agent -> Global Corporate Memory) */}
                  {m.scope === 'AGENT' && (
                    <button
                      onClick={() => onPromoteMemory && onPromoteMemory(m.id)}
                      className="btn btn-secondary"
                      style={{
                        fontSize: '0.65rem',
                        padding: '3px 8px',
                        width: '100%',
                        justifyContent: 'center',
                        borderColor: 'rgba(99, 102, 241, 0.3)',
                        color: 'var(--ac-a5b4fc)'
                      }}
                    >
                      <ArrowUpRight size={11} />
                      Şirket Kurum Hafızasına Terfi Et
                    </button>
                  )}
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </aside>
  );
}
