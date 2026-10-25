import React from 'react';
import { Badge } from '../../ui/components';
import './integrations.css';

const money = (v) => `${Number(v || 0).toLocaleString('tr-TR', { maximumFractionDigits: 2 })} ₺`;

export function offerText(offer) {
  if (!offer || offer.mode === 'NONE') return ['Bu pakette yok; teklif isteyebilirsiniz', 'neutral'];
  if (offer.mode === 'INCLUDED') return ['Paketinize dahil', 'success'];
  return [`Paketinizde %${offer.discount} indirimli${offer.list_price ? `: ${money(offer.price)} (liste ${money(offer.list_price)})` : ''}`, 'info'];
}

/**
 * Odoo ve RECDx uygulamaları seçimi (ADIM 13.1). Satın alma formunda ve Şirket Yönetimi'nde kullanılır.
 * apps: [{code, title, subtitle, description, with_recorion, url, store_url, offer}] — offer paketin teklifidir.
 * value: {has_odoo, apps: {code: USING|ADD|QUOTE|NO}}
 */
export default function RecdxAppsChoice({ apps, value, onChange, idPrefix = 'ra' }) {
  const v = value || { has_odoo: null, apps: {} };
  const setOdoo = (has) => {
    const next = { ...v.apps };
    if (!has) Object.keys(next).forEach((k) => { if (['USING', 'ADD'].includes(next[k])) next[k] = 'QUOTE'; });
    onChange({ has_odoo: has, apps: next });
  };
  const setApp = (code, choice) => onChange({ ...v, apps: { ...v.apps, [code]: choice } });
  return (
    <div className="ra-box">
      <fieldset className="ra-odoo">
        <legend>Şirketinizde Odoo kullanıyor musunuz?</legend>
        {[[true, 'Evet'], [false, 'Hayır']].map(([k, l]) => (
          <label key={String(k)}><input type="radio" name={`${idPrefix}-odoo`} checked={v.has_odoo === k} onChange={() => setOdoo(k)} /> {l}</label>
        ))}
        <p className="ra-hint">RECDx'in Odoo uygulamaları (Odoo Enterprise, Odoo.sh veya kendi sunucunuz) RECOrion ile birlikte çalışır.</p>
      </fieldset>
      {apps.map((a) => {
        const [otext, otone] = offerText(a.offer);
        const choice = v.apps[a.code] || '';
        const options = [
          ...(v.has_odoo ? [['USING', 'Zaten kullanıyorum (yalnızca entegrasyon)']] : []),
          ...(v.has_odoo && a.offer?.available ? [['ADD', 'Paketime ekle']] : []),
          ['QUOTE', 'Teklif istiyorum'], ['NO', 'Hayır'],
        ];
        return (
          <fieldset key={a.code} className="ra-app" aria-label={a.title}>
            <legend>{a.title} <small>{a.subtitle}</small></legend>
            <p className="ra-hint">{a.description} <b>RECOrion ile:</b> {a.with_recorion} <a href={a.url} target="_blank" rel="noreferrer">Ayrıntı</a></p>
            {a.offer && <p><Badge tone={otone}>{otext}</Badge></p>}
            <div className="ra-options" role="radiogroup" aria-label={`${a.title} seçimi`}>
              {options.map(([k, l]) => (
                <label key={k}><input type="radio" name={`${idPrefix}-${a.code}`} checked={choice === k} onChange={() => setApp(a.code, k)} /> {l}</label>
              ))}
            </div>
            {choice === 'QUOTE' && !a.offer?.available && (
              <p className="ra-hint">RECDx ekibi size teklif hazırlar. Dilerseniz <a href={a.store_url} target="_blank" rel="noreferrer">Odoo Apps</a> üzerinden de satın alabilirsiniz.</p>
            )}
          </fieldset>
        );
      })}
    </div>
  );
}
