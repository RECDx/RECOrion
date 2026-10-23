import React, { useCallback, useEffect, useState } from 'react';
import { api } from '../../api';
import { Card } from '../../ui/components';
import { toast } from '../../ui/feedback';
import { BarList, BudgetBars, ColumnChart, compact, tl, tlShort } from '../../ui/charts';
import '../projects/projects.css';

const PERIODS = [[7, '7 gün'], [30, '30 gün'], [90, '90 gün'], [365, '1 yıl']];
const fmtDay = (iso) => new Date(`${iso}T00:00:00`).toLocaleDateString('tr-TR', { day: '2-digit', month: 'short' });

/** Şirket panosu (ADIM 9.1): proje durumları, kredi tüketimi, maliyet grafikleri. TL, KDV hariç. */
export default function CompanyDashboard({ tenantId, departments = [], fixedDepartment = null, title = 'Genel Bakış' }) {
  const [days, setDays] = useState(30);
  const [dept, setDept] = useState(fixedDepartment || '');
  const [d, setD] = useState(null);
  const [loading, setLoading] = useState(false);

  const load = useCallback(() => {
    if (!tenantId) return;
    setLoading(true);
    api.getCompanyDashboard(tenantId, days, dept || null).then(setD).catch((e) => toast.error(e.message)).finally(() => setLoading(false));
  }, [tenantId, days, dept]);
  useEffect(() => { load(); }, [load]);

  if (!d) return <p className="pj-hint">Yükleniyor…</p>;
  const s = d.projects.by_status;
  const t = d.tasks.by_status;
  const c = d.costs.totals;
  const series = (key) => d.series.map((x) => ({ key: x.date, label: fmtDay(x.date), short: fmtDay(x.date), value: x[key] }));
  const anyCost = d.by_model.some((m) => m.cost > 0);
  const unpriced = d.by_model.reduce((n, m) => n + m.unpriced_calls, 0);

  return (
    <div className="pj-steps dash-root" style={{ opacity: loading ? 0.6 : 1, transition: 'opacity .2s' }}>
      {/* Filtreler: tek satır, tüm panoyu kapsar */}
      <div className="pj-actions" style={{ alignItems: 'center', flexWrap: 'wrap' }}>
        <h2 style={{ fontSize: '1.1rem', margin: '0 12px 0 0' }}>{title}</h2>
        <div className="ui-segmented" role="tablist" aria-label="Dönem">
          {PERIODS.map(([k, l]) => (
            <button key={k} type="button" role="tab" aria-selected={days === k} className={`ui-segmented-item ${days === k ? 'active' : ''}`}
              onClick={() => setDays(k)}>{l}</button>
          ))}
        </div>
        {!fixedDepartment && departments.length > 0 && (
          <select className="ui-input" style={{ width: 'auto', minWidth: 180 }} aria-label="Departman" value={dept} onChange={(e) => setDept(e.target.value)}>
            <option value="">Tüm şirket</option>
            {departments.map((x) => <option key={x.id} value={x.id}>{x.name}</option>)}
          </select>
        )}
        <span className="pj-hint">TL, KDV hariç · grafikler son {d.days} gün</span>
      </div>

      <div className="pj-stats">
        <div className="pj-stat"><span>Aktif proje</span><strong>{(s.ACTIVE || 0) + (s.PAUSED || 0)}</strong></div>
        <div className="pj-stat"><span>Tamamlanan</span><strong>{s.COMPLETED || 0}</strong>
          {d.projects.on_time + d.projects.late > 0 && <small className="pj-hint">zamanında {d.projects.on_time} · geç {d.projects.late}</small>}</div>
        <div className="pj-stat"><span>İptal edilen</span><strong>{s.CANCELLED || 0}</strong></div>
        <div className="pj-stat"><span>Hazırlıkta</span><strong>{(s.DRAFT || 0) + (s.PLANNING || 0) + (s.READY || 0)}</strong></div>
      </div>
      <div className="pj-stats">
        <div className="pj-stat"><span>Tamamlanan adım</span><strong>{t.DONE || 0} / {d.tasks.total}</strong></div>
        <div className="pj-stat"><span>Onay bekleyen adım</span><strong>{t.WAITING_APPROVAL || 0}</strong></div>
        <div className="pj-stat"><span>Revizyondaki adım</span><strong>{t.REVISION || 0}</strong></div>
        <div className="pj-stat"><span>Karantinadaki adım</span><strong className={t.QUARANTINED ? 'ui-text-danger' : undefined}>{t.QUARANTINED || 0}</strong></div>
      </div>

      {d.credits && (
        <Card title="Kredi" subtitle={`Dönem ${d.credits.period}${d.credits.unlimited ? ' · sınırsız (RECDx)' : ''}`}>
          <div className="pj-stats">
            <div className="pj-stat"><span>Bu ay kullanılan</span><strong>{compact(d.credits.used_this_period)}</strong></div>
            <div className="pj-stat"><span>Aylık hak</span><strong>{d.credits.unlimited ? '∞' : compact(d.credits.monthly_grant)}</strong></div>
            <div className="pj-stat"><span>Kalan aylık</span><strong>{d.credits.unlimited ? '∞' : compact(d.credits.monthly_remaining)}</strong></div>
            <div className="pj-stat"><span>Ek kredi bakiyesi</span><strong>{compact(d.credits.topup_balance)}</strong></div>
          </div>
        </Card>
      )}

      <div className="pj-split">
        <Card title="Günlük kredi tüketimi" subtitle="RECOrion kredisi">
          <ColumnChart data={series('credits')} caption="Günlük kredi tüketimi" unit=" kredi" empty="Bu dönemde kredi tüketimi yok." />
        </Card>
        <Card title="Günlük token maliyeti" subtitle={unpriced ? `${unpriced} çağrının TL fiyatı tanımsız (0 sayıldı)` : 'LLM çağrılarının TL karşılığı'}>
          <ColumnChart data={series('cost')} caption="Günlük token maliyeti (TL)" format={(v) => tl(v)}
            empty="Bu dönemde TL maliyeti oluşmadı. LLM TL fiyatları RECDx tarafından girildiğinde burada görünür." />
        </Card>
      </div>

      <div className="pj-split">
        <Card title="LLM bazında" subtitle={anyCost ? 'Token maliyeti (TL), seçilen dönem' : 'Kredi tüketimi (TL fiyatı henüz girilmedi)'}>
          <BarList caption="LLM bazında maliyet" format={anyCost ? tl : (v) => `${compact(v)} kredi`}
            data={d.by_model.map((m) => ({ key: m.model_code, label: m.model_code, value: anyCost ? m.cost : m.credits,
              note: `${m.calls} çağrı · ${compact(m.credits)} kredi` }))} empty="Bu dönemde LLM çağrısı yok." />
        </Card>
        <Card title="Maliyet dağılımı" subtitle="Tüm projeler (taslaklar hariç). Personel maliyeti yalnızca toplam olarak gösterilir.">
          <div className="pj-stats dash-stats-2">
            <div className="pj-stat"><span>Personel</span><strong title={tl(c.labor)}>{tlShort(c.labor)}</strong></div>
            <div className="pj-stat"><span>Token (LLM)</span><strong title={tl(c.token)}>{tlShort(c.token)}</strong></div>
            <div className="pj-stat"><span>Diğer kalemler</span><strong title={tl(c.other)}>{tlShort(c.other)}</strong></div>
            <div className="pj-stat"><span>Toplam</span><strong title={tl(c.actual)}>{tlShort(c.actual)}</strong></div>
          </div>
          {c.budget_projects > 0 && <p className="pj-hint" style={{ marginTop: 8 }}>Bütçesi tanımlı {c.budget_projects} projenin toplam bütçesi {tl(c.budget)}.</p>}
          <div style={{ marginTop: 12 }}>
            <BarList caption="Diğer maliyet kalemleri" format={tl} empty="Henüz maliyet kalemi yok."
              data={d.costs.by_category.map((x) => ({ key: x.category, label: x.label, value: x.amount }))} />
          </div>
        </Card>
      </div>

      <Card title="Projeler: bütçe ve gerçekleşen" subtitle="Gerçekleşen = personel + token + diğer kalemler">
        <BudgetBars caption="Proje bütçe ve gerçekleşen"
          data={d.costs.projects.filter((p) => p.actual > 0 || p.budget != null).map((p) => ({
            key: p.project_id, label: p.name, actual: p.actual, budget: p.budget, status: `${p.status_label} · ${p.tasks_done}/${p.tasks_total} adım` }))} />
      </Card>
    </div>
  );
}
