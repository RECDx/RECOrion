import React, { useCallback, useEffect, useState } from 'react';
import { RefreshCw } from 'lucide-react';
import { api } from '../../api';
import { Card } from '../../ui/components';
import { toast } from '../../ui/feedback';
import { BarList, ColumnChart, compact } from '../../ui/charts';
import '../projects/projects.css';

const PERIODS = [[7, '7 gün'], [30, '30 gün'], [90, '90 gün']];
// Durum: renk + ikon + metin (renk tek başına anlam taşımaz)
const STATE = { OK: ['● Çalışıyor', 'success'], SLOW: ['▲ Yavaş', 'warning'], DOWN: ['✕ Erişilemiyor', 'danger'], OFF: ['○ Kapalı', 'neutral'] };
const OVERALL = { OK: ['Tüm sistemler çalışıyor', 'success'], DEGRADED: ['Bazı bileşenlerde sorun var', 'warning'], DOWN: ['Çekirdek bileşen erişilemiyor', 'danger'] };
const fmtDay = (iso) => new Date(`${iso}T00:00:00`).toLocaleDateString('tr-TR', { day: '2-digit', month: 'short' });
const secs = (ms) => (ms == null ? '—' : ms < 1000 ? `${ms} ms` : `${(ms / 1000).toLocaleString('tr-TR', { maximumFractionDigits: 1 })} sn`);

export function usePlatformHealth() {
  const [health, setHealth] = useState(null);
  const [busy, setBusy] = useState(false);
  const load = useCallback((refresh = false) => {
    setBusy(true);
    return api.getPlatformHealth(refresh).then(setHealth).catch(() => setHealth({ status: 'DOWN', services: [] })).finally(() => setBusy(false));
  }, []);
  useEffect(() => { load(); const t = setInterval(() => load(), 60000); return () => clearInterval(t); }, [load]);
  return { health, busy, load };
}

/** Başlıktaki genel durum rozeti (ADIM 9.4): sabit "Sistem Çevrimiçi" yerine gerçek ölçüm. */
export function HealthBadge({ health }) {
  if (!health) return <span className="ui-badge ui-badge-neutral">Durum ölçülüyor…</span>;
  const [label, tone] = OVERALL[health.status] || OVERALL.DEGRADED;
  return <span className={`ui-badge ui-badge-${tone}`} role="status">{label}</span>;
}

/** Altyapı durumu: her bileşenin gerçek durumu, gecikmesi ve açıklaması. */
export function SystemHealthPanel({ health, busy, onRefresh }) {
  return (
    <Card title="Altyapı ve entegrasyon durumu" subtitle={health?.checked_at ? `Ölçüm: ${new Date(health.checked_at * 1000).toLocaleTimeString('tr-TR')}` : 'Ölçülüyor…'}
      actions={<button type="button" className="ui-icon-btn" aria-label="Yeniden ölç" title="Yeniden ölç" disabled={busy} onClick={() => onRefresh(true)}>
        <RefreshCw size={14} className={busy ? 'spin' : undefined} /></button>}>
      <ul className="pj-list">
        {(health?.services || []).map((s) => {
          const [label, tone] = STATE[s.status] || STATE.DOWN;
          return (
            <li key={s.key}>
              <span><strong>{s.name}</strong>{s.detail && <><br /><small className="pj-hint">{s.detail}</small></>}</span>
              <small className="pj-hint">{s.latency_ms != null ? secs(s.latency_ms) : ''}</small>
              <span className={`ui-badge ui-badge-${tone}`}>{label}</span>
            </li>
          );
        })}
      </ul>
    </Card>
  );
}

/** Platform göstergeleri (ADIM 9.4): LLM sağlığı, şirket başına kullanım, paket dağılımı. Müşteri içeriği yok (KVKK). */
export default function PlatformDashboard() {
  const [days, setDays] = useState(7);
  const [d, setD] = useState(null);
  const [loading, setLoading] = useState(false);
  useEffect(() => {
    setLoading(true);
    api.getPlatformDashboard(days).then(setD).catch((e) => toast.error(e.message)).finally(() => setLoading(false));
  }, [days]);
  if (!d) return <p className="pj-hint">Yükleniyor…</p>;
  const series = (key) => d.llm.series.map((x) => ({ key: x.date, label: fmtDay(x.date), short: fmtDay(x.date), value: x[key] }));
  const failRate = d.llm.calls ? d.llm.failed / d.llm.calls : 0;
  return (
    <div className="pj-steps dash-root" style={{ opacity: loading ? 0.6 : 1, transition: 'opacity .2s' }}>
      <div className="pj-actions" style={{ alignItems: 'center', flexWrap: 'wrap' }}>
        <h3 style={{ fontSize: '1rem', margin: '0 12px 0 0' }}>Platform kullanımı ve LLM sağlığı</h3>
        <div className="ui-segmented" role="tablist" aria-label="Dönem">
          {PERIODS.map(([k, l]) => (
            <button key={k} type="button" role="tab" aria-selected={days === k} className={`ui-segmented-item ${days === k ? 'active' : ''}`} onClick={() => setDays(k)}>{l}</button>
          ))}
        </div>
        <span className="pj-hint">Yalnızca sayılar; müşteri içeriği gösterilmez (KVKK)</span>
      </div>
      <div className="pj-stats">
        <div className="pj-stat"><span>LLM çağrısı</span><strong>{compact(d.llm.calls)}</strong></div>
        <div className="pj-stat"><span>Hata oranı</span><strong className={failRate > 0.1 ? 'ui-text-danger' : undefined}>%{(failRate * 100).toLocaleString('tr-TR', { maximumFractionDigits: 1 })}</strong>
          <small className="pj-hint">{d.llm.failed} başarısız</small></div>
        <div className="pj-stat"><span>EVREN bakiyesi</span><strong>{d.llm.evren_balance == null ? '—' : compact(d.llm.evren_balance)}</strong></div>
        <div className="pj-stat"><span>Süresi 30 günde dolan paket</span><strong>{d.tenants.expiring_30d}</strong></div>
      </div>
      <div className="pj-split">
        <Card title="Günlük LLM çağrısı"><ColumnChart data={series('calls')} caption="Günlük LLM çağrısı" unit=" çağrı" empty="Bu dönemde çağrı yok." /></Card>
        <Card title="Günlük başarısız çağrı" subtitle="Zaman aşımı, model dolu (503), bağlantı hatası">
          <ColumnChart data={series('failed')} caption="Günlük başarısız çağrı" unit=" hata" empty="Bu dönemde başarısız çağrı yok." />
        </Card>
      </div>
      <Card title="Model sağlığı" subtitle="Gecikme ve hız tek istek başınadır (başarılı çağrılar). EVREN kapasite (GPU) talebi için girdi.">
        <div className="ui-table-scroll">
          <table className="ui-table dash-table">
            <thead><tr><th>Model</th><th>Çağrı</th><th>Hata</th><th>Gecikme p50</th><th>Gecikme p95</th><th>Çıktı hızı</th><th>Çıktı token</th></tr></thead>
            <tbody>{d.llm.models.map((m) => (
              <tr key={m.model_code}>
                <td data-label="Model" style={{ fontFamily: 'var(--font-mono)' }}>{m.model_code}</td>
                <td data-label="Çağrı">{compact(m.calls)}</td>
                <td data-label="Hata" className={m.fail_rate > 0.1 ? 'ui-text-danger' : undefined}>%{(m.fail_rate * 100).toLocaleString('tr-TR', { maximumFractionDigits: 1 })} ({m.failed})</td>
                <td data-label="Gecikme p50">{secs(m.p50_ms)}</td><td data-label="Gecikme p95">{secs(m.p95_ms)}</td>
                <td data-label="Çıktı hızı">{m.tokens_per_sec == null ? '—' : `${m.tokens_per_sec.toLocaleString('tr-TR')} token/sn`}</td>
                <td data-label="Çıktı token">{compact(m.tokens_out)}</td>
              </tr>
            ))}</tbody>
          </table>
        </div>
      </Card>
      <div className="pj-split">
        <Card title="Şirket başına kredi kullanımı" subtitle="İlk 10 şirket, seçilen dönem">
          <BarList caption="Şirket başına kredi" format={(v) => `${compact(v)} kredi`} empty="Bu dönemde kullanım yok."
            data={d.usage_by_tenant.map((u) => ({ key: u.tenant_id, label: u.name, value: u.credits, note: `${u.plan || 'Paketsiz'} · ${u.calls} çağrı` }))} />
        </Card>
        <Card title="Aktif şirketlerin paket dağılımı" subtitle={`${d.tenants.active} aktif · ${d.tenants.inactive} pasif · dönemde ${d.tenants.new_in_period} yeni`}>
          <BarList caption="Paket dağılımı" format={(v) => `${v} şirket`} empty="Aktif müşteri şirketi yok."
            data={Object.entries(d.tenants.by_plan).map(([k, v]) => ({ key: k, label: k, value: v }))} />
        </Card>
      </div>
    </div>
  );
}
