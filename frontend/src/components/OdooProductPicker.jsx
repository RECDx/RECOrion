import React, { useCallback, useEffect, useState } from 'react';
import { RefreshCw } from 'lucide-react';
import { api } from '../api';

const money = (v, cur) => `${Number(v || 0).toLocaleString('tr-TR')} ${cur || ''}`.trim();

/**
 * Paket tanımında Odoo satış ürünü seçimi. Seçilen ürünün ID'si plans.odoo_product_id olur;
 * müşteri bu paketi seçtiğinde Odoo'daki satış kaydı bu ürünle açılır.
 */
export default function OdooProductPicker({ value, onChange, planPrice }) {
  const [products, setProducts] = useState([]);
  const [search, setSearch] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      setProducts(await api.getOdooProducts());
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, []);
  useEffect(() => { load(); }, [load]);

  const selectedId = value === '' || value == null ? '' : Number(value);
  const selected = products.find((p) => p.id === selectedId);
  const q = search.trim().toLocaleLowerCase('tr');
  const visible = products.filter((p) => !q || p.id === selectedId || `${p.name} ${p.code || ''} ${p.id}`.toLocaleLowerCase('tr').includes(q));
  const priceMismatch = selected && planPrice !== '' && planPrice != null && Number(selected.list_price) !== Number(planPrice);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 6, gridColumn: '1 / -1' }}>
      <span style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-muted)' }}>Odoo satış ürünü</span>
      <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
        <input
          type="search"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Odoo ürünlerinde ara…"
          className="super-admin-input"
          style={{ flex: '1 1 180px' }}
          aria-label="Odoo ürünlerinde ara"
        />
        <select
          value={selectedId}
          onChange={(e) => onChange(e.target.value === '' ? '' : Number(e.target.value))}
          className="super-admin-input"
          style={{ flex: '2 1 260px' }}
          aria-label="Odoo satış ürünü"
          disabled={loading && products.length === 0}
        >
          <option value="">— Odoo ürünü bağlı değil —</option>
          {selectedId !== '' && !selected && <option value={selectedId}>#{selectedId} (Odoo listesinde bulunamadı)</option>}
          {visible.map((p) => (
            <option key={p.id} value={p.id}>
              #{p.id} · {p.name}{p.code ? ` [${p.code}]` : ''} · {money(p.list_price, p.currency)}
            </option>
          ))}
        </select>
        <button type="button" onClick={load} className="super-admin-btn-secondary" title="Odoo ürün listesini yenile" disabled={loading}>
          <RefreshCw style={{ width: 14, height: 14 }} className={loading ? 'animate-spin' : ''} />
        </button>
      </div>
      {error && <span style={{ fontSize: '0.72rem', color: 'var(--ac-f87171)' }}>{error}</span>}
      {!error && selectedId === '' && (
        <span style={{ fontSize: '0.72rem', color: 'var(--ac-fbbf24)' }}>
          Ürün seçilmezse bu paketle gelen başvurular için Odoo'da satış kaydı açılamaz.
        </span>
      )}
      {selected && (
        <span style={{ fontSize: '0.72rem', color: priceMismatch ? 'var(--ac-fbbf24)' : 'var(--text-dim)' }}>
          Satış kaydı "{selected.name}" ürünüyle açılır; satır fiyatı paketin aylık fiyatından alınır.
          {priceMismatch && ` Odoo liste fiyatı (${money(selected.list_price, selected.currency)}) paket fiyatından farklı.`}
        </span>
      )}
    </div>
  );
}
