import React from 'react';
import './recai.css';

/**
 * #349: AI personel için RECAi Görsel / Ses / Okur anahtarları.
 * Paketinde olmayan yetenek kilitli görünür; işaretsiz anahtar "açık" sayılır (backend ile aynı kural).
 */
export default function RecaiCapabilities({ capabilities = [], value = {}, onChange, disabled = false }) {
  if (!capabilities.length) return null;
  return (
    <div>
      <span className="rc-label">RECAi Yetenekleri</span>
      <div className="rc-caps">
        {capabilities.map((c) => {
          const on = c.in_plan && value[c.code] !== false;
          const locked = !c.in_plan || disabled;
          return (
            <label key={c.code} className={`rc-cap ${on ? 'rc-cap-on' : ''} ${!c.in_plan ? 'rc-cap-locked' : ''}`}
                   data-testid={`recai-cap-${c.code}`}>
              <input type="checkbox" checked={on} disabled={locked}
                     onChange={(e) => onChange && onChange({ ...value, [c.code]: e.target.checked })} />
              <span>
                <span className="rc-cap-name">{c.name}</span>
                {c.description && <span className="rc-cap-desc">{c.description}</span>}
                {!c.in_plan && <span className="rc-cap-lock">🔒 Paketinizde yok — paketinizi yükseltin</span>}
              </span>
            </label>
          );
        })}
      </div>
    </div>
  );
}
