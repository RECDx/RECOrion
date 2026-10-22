import React, { useCallback, useEffect, useState } from 'react';
import { History, Plus, Save } from 'lucide-react';
import { api } from '../../api';
import { Badge, Button, Card, Modal } from '../../ui/components';
import { toast } from '../../ui/feedback';
import './ai.css';

const tl = (n) => (n == null ? '—' : `${Number(n).toLocaleString('tr-TR', { minimumFractionDigits: 2, maximumFractionDigits: 4 })} ₺`);
const day = (d) => (d ? new Date(d).toLocaleString('tr-TR', { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' }) : '—');
const CHAT_TYPES = ['CHAT', 'VISION', 'DECISION'];

/**
 * LLM TL fiyat listesi (ADIM 7.5.1): model başına 1M girdi/çıktı token TL fiyatı (KDV hariç), fiyat geçmişi ve EVREN CR>TL kuruyla öneri.
 * Fiyatlar değiştirilmez; yeni fiyat yeni satırdır. Proje maliyetlerinde her çağrı çağrı anındaki fiyatla hesaplanır.
 */
export default function LlmPricing() {
  const [data, setData] = useState(null);
  const [rate, setRate] = useState('');
  const [editing, setEditing] = useState(null);
  const [showAll, setShowAll] = useState(false);

  const load = useCallback(() => api.getLlmPrices().then((d) => { setData(d); setRate(d.cr_to_try ?? ''); }).catch((e) => toast.error(e.message)), []);
  useEffect(() => { load(); }, [load]);

  const saveRate = async () => {
    try {
      await api.setEvrenCrRate(rate === '' ? null : Number(rate));
      toast.success('CR > TL kuru kaydedildi.');
      load();
    } catch (e) { toast.error(e.message); }
  };

  if (!data) return <p className="ui-card-subtitle">Yükleniyor…</p>;
  const rows = data.models.filter((m) => showAll || CHAT_TYPES.includes(m.model_type));
  const unpriced = data.models.filter((m) => CHAT_TYPES.includes(m.model_type) && m.status === 'ACTIVE' && !m.current).length;

  return (
    <div className="ai-stack">
      <Card title="LLM TL Fiyatları" subtitle="Model başına 1 milyon girdi ve 1 milyon çıktı token'ının TL fiyatı (KDV hariç). Proje maliyet raporlarında her çağrı, yapıldığı andaki fiyatla hesaplanır; yeni fiyat eskisini silmez.">
        {unpriced > 0 && <p className="ui-badge ui-badge-warning" style={{ marginBottom: 10 }}>{unpriced} aktif sohbet modelinin TL fiyatı tanımlı değil; bu modellerin çağrıları maliyet raporunda fiyatsız görünür.</p>}
        <div className="pj-actions" style={{ display: 'flex', gap: 8, alignItems: 'flex-end', flexWrap: 'wrap', marginBottom: 12 }}>
          <label style={{ display: 'flex', flexDirection: 'column', gap: 4, fontSize: '0.78rem' }}>
            EVREN 1 CR = ? TL (öneri için)
            <input className="ui-input" type="number" min="0" step="0.0001" value={rate} onChange={(e) => setRate(e.target.value)} style={{ width: 160 }} />
          </label>
          <Button variant="secondary" icon={Save} onClick={saveRate}>Kuru kaydet</Button>
          <label style={{ display: 'flex', gap: 6, alignItems: 'center', fontSize: '0.8rem', marginLeft: 'auto' }}>
            <input type="checkbox" checked={showAll} onChange={(e) => setShowAll(e.target.checked)} /> Altyapı modellerini de göster (embedding, OCR, guard…)
          </label>
        </div>
        <div className="ui-table-scroll">
          <table className="ui-table">
            <thead>
              <tr><th>Model</th><th>Tür</th><th>Girdi / 1M</th><th>Çıktı / 1M</th><th>Geçerli</th><th>EVREN</th><th>Öneri</th><th /></tr>
            </thead>
            <tbody>
              {rows.map((m) => (
                <tr key={m.model_code}>
                  <td data-label="Model"><strong>{m.display_name}</strong><br /><small style={{ fontFamily: 'var(--font-mono)', color: 'var(--text-dim)' }}>{m.model_code}</small></td>
                  <td data-label="Tür">{m.model_type}</td>
                  <td data-label="Girdi / 1M">{tl(m.current?.price_in_per_1m_try)}</td>
                  <td data-label="Çıktı / 1M">{tl(m.current?.price_out_per_1m_try)}</td>
                  <td data-label="Geçerli">{m.current ? day(m.current.valid_from) : <Badge tone="warning">Fiyat yok</Badge>}</td>
                  <td data-label="EVREN" style={{ fontSize: '0.75rem' }}>
                    {m.evren.free_until && new Date(m.evren.free_until) > new Date() ? <Badge tone="info">Ücretsiz · {new Date(m.evren.free_until).toLocaleDateString('tr-TR')}</Badge>
                      : `${m.evren.prompt_token_price} / ${m.evren.completion_token_price} ${m.evren.currency || ''}`}
                  </td>
                  <td data-label="Öneri" style={{ fontSize: '0.75rem' }}>{m.suggestion ? `${tl(m.suggestion.price_in_per_1m_try)} / ${tl(m.suggestion.price_out_per_1m_try)}` : '—'}</td>
                  <td data-label=""><Button size="sm" variant="secondary" icon={m.history.length ? History : Plus} onClick={() => setEditing(m)}>{m.current ? 'Fiyat / geçmiş' : 'Fiyat gir'}</Button></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
      {editing && <PriceModal model={editing} onClose={() => setEditing(null)} onSaved={() => { setEditing(null); load(); }} />}
    </div>
  );
}

function PriceModal({ model, onClose, onSaved }) {
  const [form, setForm] = useState({
    price_in_per_1m_try: model.suggestion?.price_in_per_1m_try ?? model.current?.price_in_per_1m_try ?? '',
    price_out_per_1m_try: model.suggestion?.price_out_per_1m_try ?? model.current?.price_out_per_1m_try ?? '',
    valid_from: '', note: '',
  });
  const [busy, setBusy] = useState(false);
  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }));
  const save = async () => {
    if (form.price_in_per_1m_try === '' || form.price_out_per_1m_try === '') return toast.warning('Girdi ve çıktı fiyatını yazın.');
    setBusy(true);
    try {
      const r = await api.addLlmPrice({
        model_code: model.model_code, price_in_per_1m_try: Number(form.price_in_per_1m_try), price_out_per_1m_try: Number(form.price_out_per_1m_try),
        valid_from: form.valid_from ? new Date(form.valid_from).toISOString() : null, note: form.note || null,
      });
      toast.success(`Fiyat kaydedildi${r.backfilled_calls ? `; ${r.backfilled_calls} fiyatlanmamış çağrı bu fiyatla hesaplandı` : ''}.`);
      onSaved();
    } catch (e) { toast.error(e.message); } finally { setBusy(false); }
  };
  return (
    <Modal open onClose={onClose} title={`${model.display_name} · TL fiyatı`} size="md"
      footer={<><Button variant="secondary" onClick={onClose}>Vazgeç</Button><Button icon={Save} onClick={save} disabled={busy}>Yeni fiyatı kaydet</Button></>}>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
        <label style={{ display: 'flex', flexDirection: 'column', gap: 4, fontSize: '0.8rem' }}>1M girdi token (₺)
          <input className="ui-input" type="number" min="0" step="0.0001" value={form.price_in_per_1m_try} onChange={set('price_in_per_1m_try')} /></label>
        <label style={{ display: 'flex', flexDirection: 'column', gap: 4, fontSize: '0.8rem' }}>1M çıktı token (₺)
          <input className="ui-input" type="number" min="0" step="0.0001" value={form.price_out_per_1m_try} onChange={set('price_out_per_1m_try')} /></label>
        <label style={{ display: 'flex', flexDirection: 'column', gap: 4, fontSize: '0.8rem' }}>Geçerlilik başlangıcı (boş: şimdi)
          <input className="ui-input" type="datetime-local" value={form.valid_from} onChange={set('valid_from')} /></label>
        <label style={{ display: 'flex', flexDirection: 'column', gap: 4, fontSize: '0.8rem' }}>Not
          <input className="ui-input" value={form.note} onChange={set('note')} maxLength={500} placeholder="Örn. EVREN Kasım fiyat listesi" /></label>
      </div>
      {model.suggestion && <p className="ui-card-subtitle" style={{ marginTop: 8 }}>Alanlar EVREN fiyatı × CR kuru önerisiyle dolduruldu; kontrol edip kaydedin.</p>}
      <p className="ui-card-subtitle" style={{ marginTop: 8 }}>Geçmiş bir başlangıç tarihi verirseniz, o aralıkta henüz fiyatlanmamış çağrılar bu fiyatla hesaplanır; daha önce fiyatlanmış çağrılar değişmez.</p>
      <h4 style={{ margin: '14px 0 6px', fontSize: '0.85rem' }}>Fiyat geçmişi</h4>
      {model.history.length === 0 ? <p className="ui-card-subtitle">Henüz fiyat girilmedi.</p> : (
        <table className="ui-table">
          <thead><tr><th>Başlangıç</th><th>Girdi / 1M</th><th>Çıktı / 1M</th><th>Not</th></tr></thead>
          <tbody>{model.history.map((h) => (
            <tr key={h.id}><td data-label="Başlangıç">{day(h.valid_from)}</td><td data-label="Girdi / 1M">{tl(h.price_in_per_1m_try)}</td>
              <td data-label="Çıktı / 1M">{tl(h.price_out_per_1m_try)}</td><td data-label="Not">{h.note || ''}</td></tr>
          ))}</tbody>
        </table>
      )}
    </Modal>
  );
}
