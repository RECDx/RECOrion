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
const MEMORY_TABS = [['APPROVED', 'Onaylı'], ['CANDIDATE', 'Onay bekliyor'], ['REVOKED', 'Reddedilen']];
const EMPTY = { APPROVED: 'Henüz onaylı bilgi yok.', CANDIDATE: 'Onay bekleyen bilgi yok.', REVOKED: 'Reddedilen veya geri alınan bilgi yok.' };
const fmtTime = (d) => (d ? new Date(d).toLocaleString('tr-TR', { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' }) : '');

export default function RightPane({
  selectedTask,
  flowTask,
  memoryItems,
  actors,
  canPromote,
  canRevoke,
  onMemoryAction,
  onApproveQualityGate,
  onRejectQualityGate,
  onSubmitTask
}) {
  const [memTab, setMemTab] = useState('APPROVED');
  const [viewing, setViewing] = useState(false);
  const closeViewer = useCallback(() => setViewing(false), []);
  const status = selectedTask?.status;
  const [gateLabel, gateTone] = GATE[status] || ['Sırada', 'neutral'];
  const art = flowTask?.artifact;

  const counts = (memoryItems || []).reduce((c, m) => ({ ...c, [m.status]: (c[m.status] || 0) + 1 }), {});
  const shown = (memoryItems || []).filter((m) => m.status === memTab).slice(0, 50);
  const agentName = (id) => actors?.find((a) => a.id === id)?.display_name || 'AI personel';

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

        {/* 3. KURUM HAFIZASI (Adım 8.4): onaylı / onay bekleyen / reddedilen; kararlar yalnızca memory:promote yetkisiyle */}
        <div>
          <div className="wa-section-title"><Database size={13} />Hafıza</div>
          <div className="ui-segmented" role="tablist" aria-label="Hafıza durumu" style={{ width: '100%', marginBottom: '10px' }}>
            {MEMORY_TABS.filter(([k]) => k === 'APPROVED' || canPromote).map(([k, l]) => (
              <button key={k} type="button" role="tab" aria-selected={memTab === k} style={{ flex: 1 }}
                className={`ui-segmented-item ${memTab === k ? 'active' : ''}`} onClick={() => setMemTab(k)}>
                {l}{k === 'CANDIDATE' && counts.CANDIDATE ? ` (${counts.CANDIDATE})` : ''}
              </button>
            ))}
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', maxHeight: '320px', overflowY: 'auto' }}>
            {shown.length === 0 ? (
              <p className="pj-hint" style={{ textAlign: 'center', padding: '12px' }}>{EMPTY[memTab]}</p>
            ) : shown.map((m) => (
              <div key={m.id} className="wa-artifact" style={{ fontSize: '0.75rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '6px', marginBottom: '4px' }}>
                  {m.scope === 'GLOBAL'
                    ? <Badge tone="info"><Building2 size={10} /> Kurum hafızası</Badge>
                    : <Badge tone="neutral"><Bot size={10} /> {agentName(m.agent_id)}</Badge>}
                  <span className="pj-hint" style={{ fontSize: '0.65rem' }}>{fmtTime(m.created_at)}</span>
                </div>
                <p style={{ color: 'var(--text-muted)', lineHeight: 1.45, margin: '0 0 6px' }}>{m.content}</p>
                {m.reviewed_by_name && (
                  <p className="pj-hint" style={{ fontSize: '0.66rem', margin: '0 0 6px' }}>
                    {m.status === 'REVOKED' ? 'Karar' : 'Onaylayan'}: {m.reviewed_by_name} · {fmtTime(m.reviewed_at)}{m.review_note ? ` · "${m.review_note}"` : ''}
                  </p>
                )}
                {canPromote && m.status === 'CANDIDATE' && (
                  <div className="ui-grid-2" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '6px' }}>
                    <button type="button" className="btn btn-success" style={{ fontSize: '0.68rem', padding: '4px' }} onClick={() => onMemoryAction?.('promote', m)}>
                      <CheckCircle2 size={11} /> Onayla
                    </button>
                    <button type="button" className="btn btn-secondary" style={{ fontSize: '0.68rem', padding: '4px' }} onClick={() => onMemoryAction?.('reject', m)}>
                      Reddet
                    </button>
                  </div>
                )}
                {canRevoke && m.status === 'APPROVED' && (
                  <div style={{ display: 'flex', gap: '6px' }}>
                    {m.scope === 'AGENT' && (
                      <button type="button" className="btn btn-secondary" style={{ fontSize: '0.66rem', padding: '3px 8px', flex: 1 }} onClick={() => onMemoryAction?.('promote', m)}>
                        <ArrowUpRight size={11} /> Kurum hafızasına taşı
                      </button>
                    )}
                    <button type="button" className="btn btn-ghost" style={{ fontSize: '0.66rem', padding: '3px 8px' }} onClick={() => onMemoryAction?.('revoke', m)}>
                      Geri al
                    </button>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      </div>
    </aside>
  );
}
