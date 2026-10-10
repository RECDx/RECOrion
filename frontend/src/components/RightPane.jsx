import React, { useState } from 'react';
import { 
  ShieldCheck, 
  CheckCircle2, 
  RotateCcw, 
  BookOpen, 
  Building2, 
  Bot, 
  ArrowUpRight, 
  FileCode2, 
  Sparkles,
  Layers,
  Database,
  Award
} from 'lucide-react';

export default function RightPane({ 
  selectedTask, 
  memoryItems, 
  onPromoteMemory, 
  onApproveQualityGate, 
  onRejectQualityGate 
}) {
  const [activeTab, setActiveTab] = useState('GLOBAL'); // GLOBAL vs AGENT
  const [gateStatus, setGateStatus] = useState('WAITING_APPROVAL'); // WAITING_APPROVAL, APPROVED, REVISION

  const handleApprove = () => {
    setGateStatus('APPROVED');
    onApproveQualityGate && onApproveQualityGate(selectedTask);
  };

  const handleReject = () => {
    setGateStatus('REVISION');
    onRejectQualityGate && onRejectQualityGate(selectedTask);
  };

  const filteredMemories = memoryItems?.filter((m) => m.scope === activeTab) || [];

  return (
    <aside className="pane" style={{ borderLeft: '1px solid var(--border-subtle)', background: 'var(--bg-surface)' }}>
      {/* Pane Header: Quality Gate & Memory */}
      <div className="pane-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <ShieldCheck size={18} color="#10b981" />
          <span style={{ fontSize: '0.875rem', fontWeight: '700' }}>
            Kalite Kapısı & Kurum Hafızası
          </span>
        </div>
      </div>

      <div className="pane-content">
        {/* 1. DETERMINISTIC QUALITY GATE (KALİTE KAPISI) */}
        <div style={{
          padding: '14px',
          borderRadius: '12px',
          background: 'var(--gradient-card)',
          border: '1px solid rgba(16, 185, 129, 0.3)',
          boxShadow: '0 4px 15px rgba(0, 0, 0, 0.3)'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
            <span style={{ fontSize: '0.75rem', fontWeight: '700', color: '#34d399', display: 'flex', alignItems: 'center', gap: '5px' }}>
              <ShieldCheck size={14} />
              GÖREV KALİTE KAPISI
            </span>
            <span className="badge" style={{
              fontSize: '0.62rem',
              background: gateStatus === 'APPROVED' ? 'rgba(16, 185, 129, 0.2)' : gateStatus === 'REVISION' ? 'rgba(244, 63, 94, 0.2)' : 'rgba(245, 158, 11, 0.2)',
              color: gateStatus === 'APPROVED' ? '#34d399' : gateStatus === 'REVISION' ? '#f43f5e' : '#fbbf24'
            }}>
              {gateStatus === 'APPROVED' ? '✓ ONAYLANDI' : gateStatus === 'REVISION' ? '↺ REVİZYON' : '⏳ ONAY BEKLİYOR'}
            </span>
          </div>

          <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', lineHeight: 1.5, marginBottom: '12px' }}>
            AI Personeli tarafından üretilen kod ve doküman artefaktları deterministik doğrulama kriterlerini karşılamadan iş akışında ilerleyemez.
          </p>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
            <button 
              onClick={handleApprove}
              className="btn btn-success"
              style={{ fontSize: '0.75rem', padding: '7px' }}
            >
              <CheckCircle2 size={13} />
              Onayla & İlerlet
            </button>
            <button 
              onClick={handleReject}
              className="btn btn-secondary"
              style={{ fontSize: '0.75rem', padding: '7px', borderColor: 'rgba(244, 63, 94, 0.3)', color: '#f43f5e' }}
            >
              <RotateCcw size={13} />
              Revizyon İste
            </button>
          </div>
        </div>

        {/* 2. ARTIFACT PREVIEW */}
        <div style={{
          padding: '12px',
          borderRadius: '10px',
          background: 'rgba(255, 255, 255, 0.02)',
          border: '1px solid var(--border-subtle)'
        }}>
          <div style={{ fontSize: '0.72rem', fontWeight: '700', color: 'var(--text-dim)', marginBottom: '8px', display: 'flex', alignItems: 'center', gap: '5px' }}>
            <FileCode2 size={13} color="#38bdf8" />
            ÜRETİLEN ARTEFAKT (MINIO S3)
          </div>

          <div style={{
            background: 'var(--bg-dark)',
            borderRadius: '6px',
            padding: '10px',
            fontFamily: 'var(--font-mono)',
            fontSize: '0.72rem',
            color: '#a5f3fc',
            lineHeight: 1.5,
            border: '1px solid rgba(255, 255, 255, 0.05)'
          }}>
            <div style={{ color: '#818cf8', marginBottom: '4px' }}>// Görev Teslimatı:</div>
            <div>[MİMARİ_PLAN_V1.md]</div>
            <div style={{ color: 'var(--text-dim)', fontSize: '0.65rem', marginTop: '4px' }}>
              Depolama: recorion-artifacts/projects/{selectedTask?.project_id?.slice(0, 8)}/
            </div>
          </div>
        </div>

        {/* 3. 2 KADEMELİ KOLEKTİF HAFIZA YÖNETİCİSİ */}
        <div>
          <div style={{ fontSize: '0.75rem', fontWeight: '700', color: 'var(--text-dim)', marginBottom: '8px', display: 'flex', alignItems: 'center', gap: '6px' }}>
            <Database size={13} color="#a855f7" />
            2 KADEMELİ KOLEKTİF HAFIZA (QDRANT)
          </div>

          {/* Scope Tabs */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '4px', marginBottom: '10px' }}>
            <button 
              onClick={() => setActiveTab('GLOBAL')}
              className="btn btn-secondary"
              style={{
                fontSize: '0.7rem',
                padding: '6px',
                background: activeTab === 'GLOBAL' ? 'rgba(99, 102, 241, 0.25)' : 'transparent',
                borderColor: activeTab === 'GLOBAL' ? '#6366f1' : 'var(--border-subtle)',
                color: activeTab === 'GLOBAL' ? '#818cf8' : 'var(--text-muted)'
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
                color: activeTab === 'AGENT' ? '#22d3ee' : 'var(--text-muted)'
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
                    background: 'rgba(255, 255, 255, 0.02)',
                    border: '1px solid var(--border-subtle)',
                    fontSize: '0.75rem'
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '4px' }}>
                    <span style={{ fontWeight: '600', color: m.scope === 'GLOBAL' ? '#818cf8' : '#22d3ee' }}>
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
                        color: '#a5b4fc'
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
