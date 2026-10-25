import React from 'react';
import OdooProductPicker from '../OdooProductPicker';
import './integrations.css';

const APPS = [['recqmind', 'RECQmind'], ['recslip', 'RECSlip']];
const MODES = [['NONE', 'Yok'], ['DISCOUNT', 'İndirimli'], ['INCLUDED', 'Pakete dahil']];

/** Paket tanımında RECDx uygulama teklifi (ADIM 13.1): yok / indirimli (%) / dahil + Odoo'dan ürün (fiyatlı veya fiyatsız). */
export default function PlanAppOffers({ value, onChange }) {
  const offers = value || {};
  const set = (code, patch) => onChange({ ...offers, [code]: { ...(offers[code] || { mode: 'NONE' }), ...patch } });
  return (
    <fieldset className="pao-box">
      <legend>RECDx uygulamaları (Odoo)</legend>
      <p className="pao-hint">Müşteri "paketime ekle" derse Odoo siparişine seçilen ürün eklenir: indirimliyse ürünün Odoo fiyatından yüzde
        düşülür, dahilse 0 fiyatla. "Zaten kullanıyorum" diyen müşteriye yalnızca entegrasyon açılır.</p>
      {APPS.map(([code, title]) => {
        const o = offers[code] || { mode: 'NONE' };
        return (
          <div key={code} className="pao-row">
            <strong>{title}</strong>
            <label>Teklif
              <select className="super-admin-input" aria-label={`${title} teklifi`} value={o.mode || 'NONE'} onChange={(e) => set(code, { mode: e.target.value, ...(e.target.value === 'DISCOUNT' ? { discount: o.discount ?? 50 } : {}) })}>
                {MODES.map(([k, l]) => <option key={k} value={k}>{l}</option>)}
              </select>
            </label>
            {o.mode === 'DISCOUNT' && (
              <label>İndirim (%)
                <input type="number" min="1" max="99" className="super-admin-input" aria-label={`${title} indirim yüzdesi`} value={o.discount ?? 50}
                  onChange={(e) => set(code, { discount: Number(e.target.value) })} />
              </label>
            )}
            {o.mode !== 'NONE' && (
              <OdooProductPicker label={`${title} için Odoo ürünü`} value={o.odoo_product_id ?? ''}
                onChange={(id) => set(code, { odoo_product_id: id === '' ? null : id })} />
            )}
          </div>
        );
      })}
    </fieldset>
  );
}
