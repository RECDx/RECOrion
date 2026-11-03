import React, { useCallback, useEffect, useState } from 'react';
import { Save } from 'lucide-react';
import { api } from '../../api';
import { Badge, Button, Card } from '../../ui/components';
import { toast } from '../../ui/feedback';

const fmt = (d) => (d ? new Date(d).toLocaleString('tr-TR', { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' }) : '—');
const money = (v, c) => `${Number(v || 0).toLocaleString('tr-TR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} ${c || 'TRY'}`;
const STATUS = { AUTO_DONE: ['AI onayladı', 'success'], PENDING: ['İnsan kararı bekliyor', 'warning'], HUMAN_APPROVED: ['İnsan onayladı', 'success'],
  HUMAN_REFUSED: ['İnsan reddetti', 'danger'], ELSEWHERE: ["Odoo'dan karar verildi", 'neutral'], FAILED: ['Hata', 'danger'] };
const RISK = [['none', 'Yok'], ['low', 'Düşük'], ['high', 'Yüksek']];
const SOURCES = [['rule', 'Kural'], ['vendor', 'Tedarikçi hafızası'], ['exact', 'Tam eşleşme'], ['memory', 'Onaylı hafıza'], ['manual', 'Elle (muhasebeci)']];

/** RECSlip.App v2 aylık Case'i (ADIM 14): takvim, ayarlar ve onay kriterleri (Case yöneticisi değiştirir), AI kararları, aktarım. */
export default function RecslipCaseTab({ project }) {
  const [data, setData] = useState(null);
  const [s, setS] = useState(null);
  const [busy, setBusy] = useState(false);
  const load = useCallback(() => api.getRecslipCase(project.id).then((d) => { setData(d); setS(d.settings); }).catch((e) => toast.error(e.message)), [project.id]);
  useEffect(() => { load(); }, [load]);
  if (!data || !s) return <p className="pj-hint">Yükleniyor…</p>;
  const ro = !data.can_edit;
  const set = (path, value) => setS((prev) => {
    const next = structuredClone(prev);
    let o = next;
    path.slice(0, -1).forEach((k) => { o = o[k]; });
    o[path[path.length - 1]] = value;
    return next;
  });
  const num = (path, props = {}) => (
    <input className="ui-input" type="number" disabled={ro} value={path.reduce((o, k) => o[k], s)} {...props}
      onChange={(e) => set(path, e.target.value === '' ? '' : Number(e.target.value))} />);
  const toggleIn = (path, value) => {
    const list = path.reduce((o, k) => o[k], s);
    set(path, list.includes(value) ? list.filter((x) => x !== value) : [...list, value]);
  };
  const save = async () => {
    setBusy(true);
    try { const r = await api.saveRecslipSettings(project.id, s); setData({ ...data, ...r }); setS(r.settings); toast.success('RECSlip ayarları kaydedildi.'); }
    catch (e) { toast.error(e.message); } finally { setBusy(false); }
  };
  const c = s.criteria;
  const counts = (role) => Object.entries(data.counts?.[role] || {}).map(([k, v]) => `${STATUS[k]?.[0] || k}: ${v}`).join(' · ') || 'karar yok';
  return (
    <div className="pj-steps">
      <Card title={`Dönem ${data.period}`} subtitle="Takvim ve durum">
        <ul className="pj-list" aria-label="RECSlip takvimi">
          <li><span>Ay sonu kesim</span><strong>{fmt(data.calendar.cutoff)}</strong></li>
          <li><span>Geç gelen fişler için son</span><strong>{fmt(data.calendar.late_until)}</strong></li>
          <li><span>Aktarım dosyası</span><strong>{fmt(data.calendar.export)}</strong></li>
          <li><span>Yönetici adımları</span><small>{counts('manager')}</small></li>
          <li><span>Muhasebe adımları</span><small>{counts('accountant')}</small></li>
          <li><span>AI–insan uyumu</span><strong>{data.agreement == null ? 'henüz insan kararı yok' : `%${data.agreement}`}</strong></li>
          <li><span>Aktarım</span>{data.export ? (
            <small>{data.export.name || '—'} · {data.export.receipt_count ?? 0} fiş · {money(data.export.total)} · <Badge tone={data.export.status === 'POSTED' ? 'success'
              : data.export.status === 'FAILED' ? 'danger' : 'info'}>{data.export.status}</Badge>{data.export.last_error ? ` · ${data.export.last_error}` : ''}</small>
          ) : <small>henüz yok</small>}</li>
        </ul>
      </Card>

      <Card title="Ayarlar ve onay kriterleri" subtitle={ro ? 'Yalnızca Case yöneticisi değiştirebilir.' : 'Sonraki ayın Case\'i bu ayarlarla açılır.'}
        actions={!ro && <Button icon={Save} disabled={busy} onClick={save}>Kaydet</Button>}>
        <div className="pj-form" aria-label="RECSlip ayarları">
          <div className="pj-field"><label>Fiş ve onay takibi (dakika)</label>{num(['poll_minutes'], { min: 5, max: 1440 })}</div>
          <div className="pj-field"><label>Onaya gönderilmemiş fiş hatırlatması (gün)</label>{num(['submit_reminder_days'], { min: 0 })}</div>
          <div className="pj-field"><label>Kesim günü (-1: ayın son günü)</label>{num(['cutoff', 'day'], { min: -1, max: 28 })}</div>
          <div className="pj-field"><label>Kesim saati</label><input className="ui-input" type="time" disabled={ro} value={s.cutoff.time} onChange={(e) => set(['cutoff', 'time'], e.target.value)} /></div>
          <div className="pj-field"><label>Geç fiş toleransı (sonraki ayın günü)</label>{num(['late_tolerance_day'], { min: 0, max: 27 })}</div>
          <div className="pj-field"><label>Aktarım günü (sonraki ay)</label>{num(['export', 'day'], { min: 1, max: 28 })}</div>
          <div className="pj-field"><label>Aktarım saati</label><input id="rs-export-time" className="ui-input" type="time" disabled={ro} value={s.export.time} onChange={(e) => set(['export', 'time'], e.target.value)} /></div>
          <div className="pj-field"><label>Tekrar sayısı</label>{num(['retry', 'count'], { min: 0, max: 10 })}</div>
          <div className="pj-field"><label>Tekrar aralığı (saat)</label>{num(['retry', 'interval_hours'], { min: 1, max: 168 })}</div>
          <div className="pj-field"><label>İşlenmedi hatırlatması (gün)</label>{num(['posted_reminder_days'], { min: 0 })}</div>
        </div>
        <h4 className="pj-sub">Yönetici / yetkili AI onayı</h4>
        <div className="pj-form" aria-label="Yönetici onay kriterleri">
          <label className="pj-field full" style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
            <input type="checkbox" disabled={ro} checked={c.manager.approve_all} onChange={(e) => set(['criteria', 'manager', 'approve_all'], e.target.checked)} /> Tümünü AI onaylasın (eşikler aranmaz)</label>
          <div className="pj-field"><label>En yüksek fiş tutarı</label>{num(['criteria', 'manager', 'max_amount'], { min: 0 })}</div>
          <div className="pj-field"><label>Çalışan başına aylık sınır</label>{num(['criteria', 'manager', 'monthly_employee_limit'], { min: 0 })}</div>
          <div className="pj-field"><label>İzinli risk</label><span>{RISK.map(([k, l]) => (
            <label key={k} style={{ marginRight: 10 }}><input type="checkbox" disabled={ro} checked={c.manager.risk_levels.includes(k)} onChange={() => toggleIn(['criteria', 'manager', 'risk_levels'], k)} /> {l}</label>))}</span></div>
          <label className="pj-field" style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
            <input type="checkbox" disabled={ro} checked={c.manager.weekend_to_human} onChange={(e) => set(['criteria', 'manager', 'weekend_to_human'], e.target.checked)} /> Hafta sonu harcaması insana</label>
          <label className="pj-field" style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
            <input type="checkbox" disabled={ro} checked={c.manager.duplicate_to_human} onChange={(e) => set(['criteria', 'manager', 'duplicate_to_human'], e.target.checked)} /> Mükerrer şüphesi insana</label>
        </div>
        <h4 className="pj-sub">Muhasebe AI onayı</h4>
        <div className="pj-form" aria-label="Muhasebe onay kriterleri">
          <label className="pj-field full" style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
            <input type="checkbox" disabled={ro} checked={c.accountant.approve_all} onChange={(e) => set(['criteria', 'accountant', 'approve_all'], e.target.checked)} /> Tümünü AI onaylasın (eşikler aranmaz; düzeltmeler yine yapılır)</label>
          <div className="pj-field"><label>En yüksek fiş tutarı</label>{num(['criteria', 'accountant', 'max_amount'], { min: 0 })}</div>
          <div className="pj-field"><label>En düşük fiş güveni</label>{num(['criteria', 'accountant', 'min_confidence'], { min: 0, max: 100 })}</div>
          <div className="pj-field"><label>AI düzeltmesi için en düşük güven</label>{num(['criteria', 'accountant', 'correct_min_confidence'], { min: 0, max: 100 })}</div>
          <div className="pj-field"><label>İzinli risk</label><span>{RISK.map(([k, l]) => (
            <label key={k} style={{ marginRight: 10 }}><input type="checkbox" disabled={ro} checked={c.accountant.risk_levels.includes(k)} onChange={() => toggleIn(['criteria', 'accountant', 'risk_levels'], k)} /> {l}</label>))}</span></div>
          <div className="pj-field full"><label>Güvenli sayılan eşleşme kaynakları (diğerleri RECAi:Mergen ikinci görüşüne gider)</label><span>{SOURCES.map(([k, l]) => (
            <label key={k} style={{ marginRight: 10 }}><input type="checkbox" disabled={ro} checked={c.accountant.safe_sources.includes(k)} onChange={() => toggleIn(['criteria', 'accountant', 'safe_sources'], k)} /> {l}</label>))}</span></div>
          <label className="pj-field" style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
            <input type="checkbox" disabled={ro} checked={c.accountant.kkeg_to_human} onChange={(e) => set(['criteria', 'accountant', 'kkeg_to_human'], e.target.checked)} /> KKEG'li fiş insana</label>
        </div>
      </Card>

      <Card title="AI kararları" subtitle={`${data.decisions.length} adım`}>
        {data.decisions.length === 0 ? <p className="pj-hint">Henüz değerlendirilen onay adımı yok.</p> : (
          <ul className="pj-list" aria-label="RECSlip AI kararları">
            {data.decisions.map((d) => {
              const [label, tone] = STATUS[d.status] || [d.status, 'neutral'];
              return (
                <li key={d.id}>
                  <span><strong>{d.expense_name}</strong> · {money(d.amount, d.currency)} · {d.role_label} · {d.approver_name || '—'}<br />
                    <small className="pj-hint">{(d.reasons || []).join(' ')}{d.corrections?.length ? ` · düzeltme: ${d.corrections.map((x) => `${x.line} → ${x.new}`).join(', ')}` : ''}
                      {d.error ? ` · ${d.error}` : ''}</small></span>
                  <Badge tone={tone}>{label}</Badge>
                </li>
              );
            })}
          </ul>
        )}
      </Card>
    </div>
  );
}
