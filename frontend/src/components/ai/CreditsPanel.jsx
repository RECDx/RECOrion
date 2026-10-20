import React, { useCallback, useEffect, useState } from 'react';
import { Coins, RefreshCw } from 'lucide-react';
import { api } from '../../api';
import { Badge, Button, Card, DataTable, EmptyState } from '../../ui/components';
import { ENTRY_LABELS, fmtCredits, fmtDate, fmtTokens, purposeLabel } from './format';
import './ai.css';

function Meter({ percent }) {
  const p = Math.min(100, Math.max(0, percent || 0));
  return (
    <div className="ai-meter" role="progressbar" aria-valuenow={p} aria-valuemin={0} aria-valuemax={100}>
      <div className={`ai-meter-fill ${p >= 100 ? 'danger' : p >= 80 ? 'warn' : ''}`} style={{ width: `${p}%` }} />
    </div>
  );
}

function Breakdown({ title, rows, label }) {
  return (
    <Card title={title}>
      {rows.length === 0 ? <p className="ai-dim">Bu dönem kullanım yok.</p> : (
        <ul className="ai-list">
          {rows.slice(0, 8).map((r) => (
            <li key={r.key || 'none'}>
              <span>{label(r)}</span>
              <span>{fmtCredits(r.credits)} kredi · {r.calls} işlem</span>
            </li>
          ))}
        </ul>
      )}
    </Card>
  );
}

/** Şirketin bu dönemki kredi durumu. Şirket yöneticisi ve Süper Admin (yönetim verisi) görür. */
export default function CreditsPanel({ tenantId, compact = false, refreshKey = 0 }) {
  const [data, setData] = useState(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      setData(await api.getCompanyCredits(tenantId));
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, [tenantId]);

  useEffect(() => { if (tenantId) load(); }, [tenantId, load, refreshKey]);

  if (error) return <EmptyState icon={Coins} title="Kredi bilgisi alınamadı" description={error} action={<Button variant="secondary" onClick={load}>Tekrar dene</Button>} />;
  if (!data) return <p className="ai-dim">Kredi bilgisi yükleniyor…</p>;

  const s = data.summary;
  const stats = s.unlimited ? (
    <div className="ai-stats">
      <div className="ai-stat"><div className="ai-stat-label">Kullanım ({s.period})</div><div className="ai-stat-value">{fmtCredits(s.used_this_period)}</div><div className="ai-stat-note">RECDx platformu: sınırsız, yalnızca ölçülür</div></div>
    </div>
  ) : (
    <>
      <div className="ai-stats">
        <div className="ai-stat"><div className="ai-stat-label">Kullanılabilir kredi</div><div className="ai-stat-value">{fmtCredits(s.balance)}</div><div className="ai-stat-note">Aylık + ek kredi</div></div>
        <div className="ai-stat"><div className="ai-stat-label">Bu ay kullanılan</div><div className="ai-stat-value">{fmtCredits(s.used_this_period)}</div><div className="ai-stat-note">%{s.percent_used} · dönem {s.period}</div></div>
        <div className="ai-stat"><div className="ai-stat-label">Aylık hak</div><div className="ai-stat-value">{fmtCredits(s.monthly_grant)}</div><div className="ai-stat-note">Kalan {fmtCredits(s.monthly_remaining)} · ay sonunda silinir</div></div>
        <div className="ai-stat"><div className="ai-stat-label">Ek kredi</div><div className="ai-stat-value">{fmtCredits(s.topup_balance)}</div><div className="ai-stat-note">Sonraki aylara devreder</div></div>
      </div>
      <Meter percent={s.percent_used} />
      {s.balance <= 0 && <Badge tone="danger">Kredi tükendi: AI personeller yeni işlem yapamaz</Badge>}
      {s.balance > 0 && s.percent_used >= 80 && <Badge tone="warning">Aylık kredinin %{s.percent_used}'i kullanıldı</Badge>}
    </>
  );

  if (compact) return <div className="ai-stack">{stats}</div>;

  return (
    <div className="ai-stack">
      <Card
        title="RECOrion Kredisi"
        subtitle="Her yapay zeka işlemi model katsayısı × (giriş token/1000 + 2 × çıkış token/1000) kredi harcar."
        actions={<Button variant="ghost" size="sm" icon={RefreshCw} onClick={load} disabled={loading}>Yenile</Button>}
      >
        <div className="ai-stack">{stats}</div>
      </Card>

      <div className="ai-breakdowns">
        <Breakdown title="Modele göre" rows={data.by_model} label={(r) => r.key || '—'} />
        <Breakdown title="AI personele göre" rows={data.by_actor} label={(r) => r.name} />
        <Breakdown title="İşlem türüne göre" rows={data.by_purpose} label={(r) => purposeLabel(r.key)} />
      </div>

      <Card title="Son işlemler" subtitle={data.failed_calls ? `Bu dönem ${data.failed_calls} işlem başarısız oldu (kredi düşülmedi).` : undefined}>
        <DataTable
          rows={data.recent_calls.map((c, i) => ({ ...c, id: i }))}
          pageSize={10}
          columns={[
            { key: 'created_at', label: 'Zaman', render: (r) => fmtDate(r.created_at), sortValue: (r) => r.created_at },
            { key: 'purpose', label: 'İşlem', render: (r) => purposeLabel(r.purpose) },
            { key: 'model_code', label: 'Model' },
            { key: 'actor_name', label: 'AI Personel', hideOnMobile: true, render: (r) => r.actor_name || '—' },
            { key: 'tokens', label: 'Token (giriş/çıkış)', hideOnMobile: true, sortable: false, render: (r) => `${fmtTokens(r.tokens_in)} / ${fmtTokens(r.tokens_out)}` },
            { key: 'credits', label: 'Kredi', align: 'right', render: (r) => fmtCredits(r.credits) },
            { key: 'status', label: 'Durum', render: (r) => <Badge tone={r.status === 'SUCCESS' ? 'success' : 'danger'}>{r.status === 'SUCCESS' ? 'Başarılı' : 'Başarısız'}</Badge> },
          ]}
          emptyText="Henüz yapay zeka işlemi yapılmadı."
        />
      </Card>

      {data.ledger.length > 0 && (
        <Card title="Kredi hareketleri">
          <ul className="ai-list">
            {data.ledger.map((e, i) => (
              <li key={i}>
                <span>{ENTRY_LABELS[e.entry_type] || e.entry_type} · {e.period}{e.note ? ` · ${e.note}` : ''}</span>
                <span>{e.amount > 0 ? '+' : ''}{fmtCredits(e.amount)}</span>
              </li>
            ))}
          </ul>
        </Card>
      )}
    </div>
  );
}
