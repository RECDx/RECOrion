import React, { useCallback, useEffect, useState } from 'react';
import { Coins, RefreshCw } from 'lucide-react';
import { api } from '../../api';
import { Badge, Button, Card, DataTable, EmptyState } from '../../ui/components';
import { toast } from '../../ui/feedback';
import CreditOrders from './BuyCredits';
import { ENTRY_LABELS, fmtCredits, fmtDate, fmtTokens, purposeLabel } from './format';
import './ai.css';

const fmtDay = (d) => (d ? new Date(`${d}T12:00:00`).toLocaleDateString('tr-TR', { day: 'numeric', month: 'long' }) : '');

/** #746: şirketin harcama ayarları — haftalık sınır (varsayılan kapalı) ve kredi yüklenince kendiliğinden devam. */
function SpendSettings({ tenantId, settings, onSaved }) {
  const [on, setOn] = useState(Boolean(settings?.weekly_cap_pct));
  const [pct, setPct] = useState(settings?.weekly_cap_pct || 35);
  const [auto, setAuto] = useState(Boolean(settings?.auto_resume_after_topup));
  const [busy, setBusy] = useState(false);
  const save = async () => {
    setBusy(true);
    try {
      await api.putCreditSettings(tenantId, { weekly_cap_pct: on ? Number(pct) : null, auto_resume_after_topup: auto });
      toast.success('Harcama ayarları kaydedildi.');
      onSaved?.();
    } catch (e) { toast.error(e.message); } finally { setBusy(false); }
  };
  return (
    <Card title="Harcama ayarları" subtitle="Haftalık sınır şirketin kendi koyduğu frendir; satılmaz ve kredi bitmeden yeni AI işlerini durdurur.">
      <div className="ai-stack">
        <label className="pj-hint" style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
          <input type="checkbox" checked={on} onChange={(e) => setOn(e.target.checked)} /> Haftalık harcama sınırı uygula
        </label>
        {on && (
          <label className="pj-hint" htmlFor="cap-pct">Haftada en fazla aylık hakkın %
            <input id="cap-pct" className="ui-input" type="number" min={5} max={100} value={pct} onChange={(e) => setPct(e.target.value)} style={{ maxWidth: 90, marginLeft: 8 }} />
          </label>
        )}
        <label className="pj-hint" style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
          <input type="checkbox" checked={auto} onChange={(e) => setAuto(e.target.checked)} /> Kredi yüklenince duraklayan işler kendiliğinden devam etsin
        </label>
        <div><Button size="sm" onClick={save} disabled={busy}>Kaydet</Button></div>
      </div>
    </Card>
  );
}

function Meter({ percent }) {
  const p = Math.min(100, Math.max(0, percent || 0));
  return (
    <div className="ai-meter" role="progressbar" aria-valuenow={p} aria-valuemin={0} aria-valuemax={100}>
      <div className={`ai-meter-fill ${p >= 95 ? 'danger' : p >= 80 ? 'warn' : ''}`} style={{ width: `${p}%` }} />
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
export default function CreditsPanel({ tenantId, compact = false, refreshKey = 0, canManage = false }) {
  const [data, setData] = useState(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [busy, setBusy] = useState(false);
  const act = async (fn, okText) => {  // #746
    setBusy(true);
    try {
      const r = await fn();
      const blocked = r?.blocked || [];
      if (blocked.length) toast.error(`${blocked.length} iş devam ettirilemedi: ${blocked[0].reason}`);
      else toast.success(okText);
      await load();
    } catch (e) { toast.error(e.message); } finally { setBusy(false); }
  };

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
      {/* #746: kullanım göstergesi — bu hızla ne zaman biter */}
      <p className="pj-hint" style={{ margin: 0 }}>
        Bu ayın hakkının %{s.percent_used}'i kullanıldı{s.depletes_on ? `; bu hızla ${fmtDay(s.depletes_on)} tarihinde biter` : ''}.
        {s.settings?.weekly_cap_pct ? ` Haftalık sınır: aylık hakkın %${s.settings.weekly_cap_pct}'i (bu hafta ${fmtCredits(s.week_used)} kredi).` : ''}
        {data.parallel_limit ? ` Aynı anda en fazla ${data.parallel_limit} AI adımı çalışır; fazlası sırada bekler (kredi düşmez).` : ''}
      </p>
      {s.level === 'EXHAUSTED' && (
        <div className="pj-note danger" role="alert">
          <strong>Kredi bitti.</strong> Şirketin aktif proje ve Case'leri duraklatıldı; işler kredi yüklenince kaldığı yerden sürer.
          {canManage ? 'Aşağıdaki "Ek kredi" kartından ek kredi alabilirsiniz; paket yükseltme için RECDx ile iletişime geçin.'
            : 'Ek kredi için şirket yöneticinize başvurun.'}
        </div>
      )}
      {s.level !== 'EXHAUSTED' && s.weekly_cap_reached && (
        <div className="pj-note medium" role="alert">
          <strong>Haftalık harcama sınırı doldu.</strong> Yeni AI işleri bu hafta başlamaz.
          {canManage && <> <Button size="sm" variant="secondary" onClick={() => act(() => api.liftWeeklyCap(tenantId), 'Sınır bu hafta için kaldırıldı.')} disabled={busy}>Bu hafta için sınırı kaldır</Button></>}
        </div>
      )}
      {s.level === 'WARN95' && <Badge tone="danger">Aylık kredinin %{s.percent_used}'i kullanıldı</Badge>}
      {s.level === 'WARN80' && <Badge tone="warning">Aylık kredinin %{s.percent_used}'i kullanıldı</Badge>}
      {(data.credit_paused || []).length > 0 && (
        <div className="pj-note medium">
          Kredi / haftalık sınır nedeniyle duraklayan işler: {data.credit_paused.map((p) => p.name).join(', ')}.
          {canManage && s.balance > 0 && !s.weekly_cap_reached && <> <Button size="sm" onClick={() => act(() => api.resumeCreditPaused(tenantId), 'İşler kaldığı yerden devam ediyor.')} disabled={busy}>Tümünü devam ettir</Button></>}
        </div>
      )}
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
      {!s.unlimited && <CreditOrders tenantId={tenantId} canManage={canManage} onChanged={load} />}
      {canManage && !s.unlimited && <SpendSettings tenantId={tenantId} settings={s.settings} onSaved={load} />}

      <div className="ai-breakdowns">
        <Breakdown title="Modele göre" rows={data.by_model} label={(r) => r.key || '—'} />
        <Breakdown title="AI personele göre" rows={data.by_actor} label={(r) => r.name} />
        <Breakdown title="İşlem türüne göre" rows={data.by_purpose} label={(r) => purposeLabel(r.key)} />
      </div>
      {/* F115: kapsam farkı açıklaması */}
      <p className="pj-hint" style={{ margin: 0 }}>
        Bu döküm bu dönemin şirket genelidir (tüm projeler ve sohbetler). "AI personele göre" kredi, personelin hem kendi işleri hem
        kontrol personeli olarak yaptığı değerlendirmeleri içerir. Proje Maliyet ekranı ise krediyi iş adımına göre toplar; adımdaki
        kontrol personeli payı orada ayrıca gösterilir.
      </p>

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
