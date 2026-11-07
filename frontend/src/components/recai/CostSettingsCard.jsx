import React, { useEffect, useState } from 'react';
import { Save, Scale } from 'lucide-react';
import { api } from '../../api';
import { Button, Card } from '../../ui/components';
import { toast } from '../../ui/feedback';

const LEVELS = [['JUNIOR', 'Junior'], ['MID', 'Orta'], ['SENIOR', 'Kıdemli'], ['LEAD', 'Lider'], ['MANAGER', 'Müdür']];
const FAMILIES = [['IT', 'Yazılım / BT'], ['GENERAL', 'Genel']];
const n = (v) => (v === '' || v == null ? null : Number(v));

/**
 * Merkez › Kiralama Paketleri (#664): insan eşdeğeri referans maaşları (aile × kıdem, aylık brüt TL), işveren maliyet
 * katsayısı, aylık iş günü ve RECDx'in gerçek kredi maliyeti (yalnız Merkez'de kullanılır).
 */
export default function CostSettingsCard() {
  const [f, setF] = useState(null);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState('');
  useEffect(() => {
    api.getCostSettings().then((d) => setF({
      salary_bands: d?.salary_bands || { IT: {}, GENERAL: {} }, employer_factor: d?.employer_factor ?? '',
      work_days_month: d?.work_days_month ?? '', real_credit_cost_try: d?.real_credit_cost_try ?? '',
    })).catch((e) => setErr(e.message));
  }, []);
  const band = (fam, lvl, v) => setF((p) => ({ ...p, salary_bands: { ...p.salary_bands, [fam]: { ...(p.salary_bands[fam] || {}), [lvl]: v } } }));
  const save = async () => {
    setBusy(true);
    try {
      const bands = Object.fromEntries(FAMILIES.map(([fam]) => [fam, Object.fromEntries(LEVELS.map(([l]) => [l, n(f.salary_bands[fam]?.[l])]))]));
      const r = await api.saveCostSettings({ salary_bands: bands, employer_factor: n(f.employer_factor), work_days_month: n(f.work_days_month),
        real_credit_cost_try: n(f.real_credit_cost_try) });
      if (r) setF((p) => ({ ...p, ...r, real_credit_cost_try: r.real_credit_cost_try ?? '' }));
      toast.success('Maliyet ayarları kaydedildi.');
    } catch (e) { toast.error(e.message); } finally { setBusy(false); }
  };
  return (
    <Card title="İnsan eşdeğeri ve maliyet ayarları" actions={<Scale size={18} />}
      subtitle="Müşteri raporlarında insan eşdeğeri bu referanslarla hesaplanır; gerçek kredi maliyeti yalnız Merkez'de kullanılır.">
      {err ? <p className="ui-text-danger">{err}</p> : !f ? <p className="pj-hint">Yükleniyor…</p> : (
        <div className="pj-form">
          <div className="ui-table-scroll">
            <table className="ui-table" aria-label="Referans aylık brüt maaşlar">
              <thead><tr><th>Aile</th>{LEVELS.map(([k, l]) => <th key={k}>{l} (₺/ay brüt)</th>)}</tr></thead>
              <tbody>
                {FAMILIES.map(([fam, label]) => (
                  <tr key={fam}>
                    <td data-label="Aile">{label}</td>
                    {LEVELS.map(([lvl, l]) => (
                      <td key={lvl} data-label={l}>
                        <input className="ui-input" type="number" min="0" step="500" aria-label={`${label} ${l} aylık brüt maaş`}
                          value={f.salary_bands[fam]?.[lvl] ?? ''} onChange={(e) => band(fam, lvl, e.target.value)} />
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="pj-field">
            <label htmlFor="cs-factor">İşveren maliyet katsayısı</label>
            <input id="cs-factor" className="ui-input" type="number" min="1" step="0.01" value={f.employer_factor}
              onChange={(e) => setF({ ...f, employer_factor: e.target.value })} />
          </div>
          <div className="pj-field">
            <label htmlFor="cs-days">Aylık iş günü</label>
            <input id="cs-days" className="ui-input" type="number" min="1" max="31" value={f.work_days_month}
              onChange={(e) => setF({ ...f, work_days_month: e.target.value })} />
          </div>
          <div className="pj-field">
            <label htmlFor="cs-real">RECDx gerçek kredi maliyeti (TL, isteğe bağlı — EVREN/GPU)</label>
            <input id="cs-real" className="ui-input" type="number" min="0" step="0.0001" placeholder="Tanımsız" value={f.real_credit_cost_try}
              onChange={(e) => setF({ ...f, real_credit_cost_try: e.target.value })} />
          </div>
          <p className="pj-hint">Günlük insan maliyeti = aylık brüt × katsayı ÷ aylık iş günü. Ünvanın kendi referans maaşı varsa o kullanılır.</p>
          <div className="pj-actions"><Button icon={Save} disabled={busy} onClick={save} aria-label="Maliyet ayarlarını kaydet">{busy ? 'Kaydediliyor…' : 'Ayarları kaydet'}</Button></div>
        </div>
      )}
    </Card>
  );
}
