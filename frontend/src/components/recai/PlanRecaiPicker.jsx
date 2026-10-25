import React from 'react';
import { RECAI_CAPABILITIES, RECAI_TIERS } from './names';
import './recai.css';

/** #349: Süper Admin paket formu — pakete dahil RECAi adları ve Görsel/Ses/Okur yetenekleri. */
export default function PlanRecaiPicker({ form, onChange }) {
  const tiers = form.recai_tiers || [];
  const toggleTier = (code, on) => {
    const next = on ? [...tiers, code] : tiers.filter((c) => c !== code);
    onChange({ ...form, recai_tiers: RECAI_TIERS.map((t) => t.code).filter((c) => next.includes(c)) });
  };
  const toggleCap = (feature, on) => onChange({ ...form, features: { ...form.features, [feature]: on } });

  return (
    <div className="rc-box" data-testid="plan-recai">
      <span className="rc-label">Pakete dahil RECAi ({tiers.length} ad seçili)</span>
      <div className="rc-caps">
        {RECAI_TIERS.map((t) => {
          const on = tiers.includes(t.code);
          return (
            <label key={t.code} className={`rc-cap ${on ? 'rc-cap-on' : ''}`}>
              <input type="checkbox" checked={on} onChange={(e) => toggleTier(t.code, e.target.checked)} />
              <span><span className="rc-cap-name">{t.name}</span><span className="rc-cap-desc">{t.hint}</span></span>
            </label>
          );
        })}
      </div>
      <span className="rc-label rc-label-gap">Dahil yetenekler</span>
      <div className="rc-caps">
        {RECAI_CAPABILITIES.map((c) => {
          const on = !!form.features?.[c.feature];
          return (
            <label key={c.code} className={`rc-cap ${on ? 'rc-cap-on' : ''}`}>
              <input type="checkbox" checked={on} onChange={(e) => toggleCap(c.feature, e.target.checked)} />
              <span><span className="rc-cap-name">{c.name}</span><span className="rc-cap-desc">{c.hint}</span></span>
            </label>
          );
        })}
      </div>
      {!tiers.length && <p className="rc-hint ui-text-danger">En az bir RECAi adı seçin (seçilmezse RECAi Mergen kullanılır).</p>}
    </div>
  );
}
