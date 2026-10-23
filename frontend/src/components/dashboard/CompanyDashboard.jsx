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
  const c = d.costs?.totals || {};  // parasal yetkisi olmayana costs gelmez (ADIM 9.3)
  const series = (key) => d.series.map((x) => ({ key: x.date, label: fmtDay(x.date), short: fmtDay(x.date), value: x[key] }));
  const money = d.can_view_costs !== false;  // parasal bilgiler billing:view ister (ADIM 9.3)
  const anyCost = money && d.by_model.some((m) => m.cost > 0);
  const unpriced = d.by_model.reduce((n, m) => n + (m.unpriced_calls || 0), 0);

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
        {d.department_locked && <span className="ui-badge ui-badge-info">Departman: {d.department_name}</span>}
        {!d.department_locked && !fixedDepartment && departments.length > 0 && (
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
        {money && <Card title="Günlük token maliyeti" subtitle={unpriced ? `${unpriced} çağrının TL fiyatı tanımsız (0 sayıldı)` : 'LLM çağrılarının TL karşılığı'}>
          <ColumnChart data={series('cost')} caption="Günlük token maliyeti (TL)" format={(v) => tl(v)}
            empty="Bu dönemde TL maliyeti oluşmadı. LLM TL fiyatları RECDx tarafından girildiğinde burada görünür." />
        </Card>}
      </div>

      <div className="pj-split">
        <Card title="LLM bazında" subtitle={anyCost ? 'Token maliyeti (TL), seçilen dönem' : 'Kredi tüketimi (TL fiyatı henüz girilmedi)'}>
          <BarList caption="LLM bazında maliyet" format={anyCost ? tl : (v) => `${compact(v)} kredi`}
            data={d.by_model.map((m) => ({ key: m.model_code, label: m.model_code, value: anyCost ? m.cost : m.credits,
              note: `${m.calls} çağrı · ${compact(m.credits)} kredi` }))} empty="Bu dönemde LLM çağrısı yok." />
        </Card>
        {money && <Card title="Maliyet dağılımı" subtitle="Tüm projeler (taslaklar hariç). Personel maliyeti yalnızca toplam olarak gösterilir.">
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
        </Card>}
      </div>

      <div className="pj-split">
        {money && <Card title="Tahmini tasarruf (ROI)" subtitle={`Son ${d.days} gün · AI personelin tamamladığı adımlar`}>
          {d.roi.available ? (
            <>
              <div className="dash-hero" title={tl(d.roi.saving)}>{tlShort(d.roi.saving)}</div>
              <div className="pj-stats dash-stats-2">
                <div className="pj-stat"><span>İnsanla yapılsaydı</span><strong title={tl(d.roi.human_equivalent)}>{tlShort(d.roi.human_equivalent)}</strong></div>
                <div className="pj-stat"><span>AI maliyeti</span><strong title={tl(d.roi.ai_cost)}>{tlShort(d.roi.ai_cost)}</strong></div>
              </div>
              <p className="pj-hint" style={{ marginTop: 8 }}>{d.roi.assumption} {compact(d.roi.work_days)} iş günü · {d.roi.rated_humans} kişinin ortalaması.
                {d.roi.unpriced_calls ? ` ${d.roi.unpriced_calls} çağrının TL fiyatı tanımsız; AI maliyeti eksik olabilir.` : ''}</p>
            </>
          ) : (
            <p className="pj-hint">{d.roi.reason} AI personel bu dönemde {compact(d.roi.work_days)} iş günü çalıştı.</p>
          )}
        </Card>}
        <Card title="İlk seferde onay" subtitle="Revizyon istenmeden tamamlanan adımların payı (AI personel)">
          <BarList caption="AI personel ilk seferde onay oranı" format={(v) => `%${Math.round(v * 100)}`} empty="Bu dönemde tamamlanan AI adımı yok."
            data={d.agents.filter((a) => a.completed).map((a) => ({ key: a.actor_id, label: a.name, value: a.first_pass_rate,
              note: `${a.completed} adım · ${a.revisions} revizyon` }))} />
        </Card>
      </div>

      <Card title="AI personel karnesi" subtitle={`Son ${d.days} gün. Otonomi: insan revizyonu istenmeden tamamlanan adımların payı.`}>
        {d.agents.length === 0 ? <p className="pj-hint">Bu kapsamda iş almış AI personel yok.</p> : (
          <div className="ui-table-scroll">
            <table className="ui-table dash-table">
              <thead><tr><th>AI personel</th><th>Tamamlanan</th><th>İlk seferde onay</th><th>Otonomi</th><th>Revizyon</th><th>Karantina</th>
                <th>Ort. süre</th><th>Kredi</th>{money && <th>Maliyet</th>}</tr></thead>
              <tbody>{d.agents.map((a) => (
                <tr key={a.actor_id}>
                  <td data-label="AI personel"><strong>{a.name}</strong><br /><small className="pj-hint">{a.title}</small></td>
                  <td data-label="Tamamlanan">{a.completed} / {a.assigned}</td>
                  <td data-label="İlk seferde onay">{a.first_pass_rate == null ? '—' : `%${Math.round(a.first_pass_rate * 100)}`}</td>
                  <td data-label="Otonomi">{a.autonomy_rate == null ? '—' : `%${Math.round(a.autonomy_rate * 100)}`}</td>
                  <td data-label="Revizyon">{a.revisions}</td>
                  <td data-label="Karantina" className={a.quarantined ? 'ui-text-danger' : undefined}>{a.quarantined}</td>
                  <td data-label="Ort. süre">{a.avg_hours == null ? '—' : a.avg_hours < 1 ? `${Math.round(a.avg_hours * 60)} dk` : `${compact(a.avg_hours)} sa`}</td>
                  <td data-label="Kredi">{compact(a.credits)}</td>
                  {money && <td data-label="Maliyet" title={a.unpriced_calls ? `${a.unpriced_calls} çağrının TL fiyatı tanımsız` : undefined}>{tl(a.cost)}</td>}
                </tr>
              ))}</tbody>
            </table>
          </div>
        )}
      </Card>

      <Card title="Ekip iş durumu" subtitle="İnsan personel · açık adımlar ve dönemde tamamlananlar (ücret bilgisi içermez)">
        {d.people.length === 0 ? <p className="pj-hint">Bu kapsamda iş atanmış insan personel yok.</p> : (
          <div className="ui-table-scroll">
            <table className="ui-table dash-table">
              <thead><tr><th>Personel</th><th>Açık</th><th>Çalışılıyor</th><th>Onay bekliyor</th><th>Tamamlanan</th><th>Geciken</th></tr></thead>
              <tbody>{d.people.map((p) => (
                <tr key={p.actor_id}>
                  <td data-label="Personel"><strong>{p.name}</strong><br /><small className="pj-hint">{p.title}</small></td>
                  <td data-label="Açık">{p.open}</td><td data-label="Çalışılıyor">{p.working}</td>
                  <td data-label="Onay bekliyor">{p.waiting_approval}</td><td data-label="Tamamlanan">{p.done}</td>
                  <td data-label="Geciken" className={p.overdue ? 'ui-text-danger' : undefined}>{p.overdue}</td>
                </tr>
              ))}</tbody>
            </table>
          </div>
        )}
      </Card>

      {money && <Card title="Projeler: bütçe ve gerçekleşen" subtitle="Gerçekleşen = personel + token + diğer kalemler">
        <BudgetBars caption="Proje bütçe ve gerçekleşen"
          data={d.costs.projects.filter((p) => p.actual > 0 || p.budget != null).map((p) => ({
            key: p.project_id, label: p.name, actual: p.actual, budget: p.budget, status: `${p.status_label} · ${p.tasks_done}/${p.tasks_total} adım` }))} />
      </Card>}
    </div>
  );
}
