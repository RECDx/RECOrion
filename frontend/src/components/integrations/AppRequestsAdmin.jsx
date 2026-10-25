import React, { useCallback, useEffect, useState } from 'react';
import { RotateCcw } from 'lucide-react';
import { api } from '../../api';
import { Badge, Button, Card, EmptyState } from '../../ui/components';
import { promptDialog, toast } from '../../ui/feedback';
import '../projects/projects.css';
import './integrations.css';

const STATUS = { NEW: ['Yeni', 'info'], ORDERED: ['Siparişte', 'success'], OPPORTUNITY: ['CRM fırsatı', 'info'], IN_USE: ['Zaten kullanıyor', 'neutral'],
  DONE: ['Tamamlandı', 'success'], CANCELLED: ['İptal', 'neutral'], FAILED: ['Hata', 'danger'], SKIPPED: ['Odoo kapalı', 'warning'] };
const MODE = { NONE: 'pakette yok', DISCOUNT: 'indirimli', INCLUDED: 'pakete dahil' };
const fmt = (d) => (d ? new Date(d).toLocaleString('tr-TR', { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' }) : '');
const money = (v) => (v == null ? '—' : `${Number(v).toLocaleString('tr-TR', { maximumFractionDigits: 2 })}`);

/** Genel Merkez: RECDx uygulama talepleri (ADIM 13.1) — müşterinin RECQmind/RECSlip seçimi, Odoo siparişi / CRM fırsatı, durum. */
export default function AppRequestsAdmin() {
  const [rows, setRows] = useState(null);
  const [filter, setFilter] = useState('');
  const load = useCallback(() => api.getAppRequests().then(setRows).catch((e) => { toast.error(e.message); setRows([]); }), []);
  useEffect(() => { load(); }, [load]);
  const update = async (r, status) => {
    const note = await promptDialog({ title: 'Not', message: 'İsteğe bağlı not (ör. kurulum yapıldı):', defaultValue: r.note || '' });
    if (note === null) return;
    try { await api.updateAppRequest(r.id, { status, note }); toast.success('Talep güncellendi.'); load(); } catch (e) { toast.error(e.message); }
  };
  const retry = async (r) => {
    try { const x = await api.retryAppRequest(r.id); x.status === 'FAILED' ? toast.error(x.error || 'Yine başarısız.') : toast.success('Odoo işlemi yapıldı.'); load(); }
    catch (e) { toast.error(e.message); }
  };
  const shown = (rows || []).filter((r) => !filter || r.status === filter);
  return (
    <div className="pj-steps">
      <Card title="Uygulama talepleri" subtitle="Müşterilerin RECQmind ve RECSlip seçimleri. 'Paketime ekle' Odoo siparişine satır, 'teklif istiyorum' Odoo CRM fırsatı olur; 'zaten kullanıyorum' yalnızca entegrasyon açar.">
        <div className="ui-segmented" role="tablist" style={{ marginBottom: 10, flexWrap: 'wrap' }}>
          {[['', 'Tümü'], ['NEW', 'Yeni'], ['ORDERED', 'Siparişte'], ['OPPORTUNITY', 'CRM fırsatı'], ['IN_USE', 'Zaten kullanıyor'], ['FAILED', 'Hata'], ['DONE', 'Tamamlandı']].map(([k, l]) => (
            <button key={k} type="button" className={`ui-segmented-item ${filter === k ? 'active' : ''}`} onClick={() => setFilter(k)}>{l}</button>
          ))}
        </div>
        {!rows ? <p className="pj-hint">Yükleniyor…</p> : shown.length === 0 ? <EmptyState title="Talep yok" description="Müşteriler satın almada veya Şirket Yönetimi'nden seçim yaptıkça burada görünür." /> : (
          <div className="ui-table-scroll">
            <table className="ui-table" aria-label="Uygulama talepleri">
              <thead><tr><th>Şirket</th><th>Uygulama</th><th>Seçim</th><th>Paket teklifi</th><th>Fiyat</th><th>Odoo</th><th>Durum</th><th>Tarih</th><th /></tr></thead>
              <tbody>{shown.map((r) => {
                const [label, tone] = STATUS[r.status] || [r.status, 'neutral'];
                return (
                  <tr key={r.id}>
                    <td data-label="Şirket"><strong>{r.tenant_name}</strong><br /><small className="pj-hint">{r.source === 'PURCHASE' ? 'satın almada' : 'Şirket Yönetimi'}</small></td>
                    <td data-label="Uygulama">{r.app_title}</td>
                    <td data-label="Seçim">{r.choice_label}</td>
                    <td data-label="Paket teklifi">{MODE[r.mode] || '—'}{r.discount ? ` %${r.discount}` : ''}</td>
                    <td data-label="Fiyat">{r.choice === 'ADD' ? `${money(r.price)} (liste ${money(r.list_price)})` : '—'}</td>
                    <td data-label="Odoo">{r.odoo_order_name || (r.odoo_lead_id ? `Fırsat #${r.odoo_lead_id}` : '—')}</td>
                    <td data-label="Durum"><Badge tone={tone}>{label}</Badge>{(r.error || r.note) && <><br /><small className={r.error ? 'ui-text-danger' : 'pj-hint'}>{r.error || r.note}</small></>}</td>
                    <td data-label="Tarih">{fmt(r.created_at)}</td>
                    <td data-label="">
                      <div className="pj-actions">
                        {['FAILED', 'SKIPPED'].includes(r.status) && r.choice !== 'USING' && <Button size="sm" variant="secondary" icon={RotateCcw} onClick={() => retry(r)}>Yeniden dene</Button>}
                        {!['DONE', 'CANCELLED'].includes(r.status) && <Button size="sm" variant="secondary" onClick={() => update(r, 'DONE')}>Tamamlandı</Button>}
                        {!['DONE', 'CANCELLED'].includes(r.status) && <Button size="sm" variant="ghost" onClick={() => update(r, 'CANCELLED')}>İptal</Button>}
                      </div>
                    </td>
                  </tr>
                );
              })}</tbody>
            </table>
          </div>
        )}
      </Card>
    </div>
  );
}
