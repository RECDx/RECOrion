import React, { useCallback, useEffect, useState } from 'react';
import { CheckCircle2, Coins, Pencil, Plus } from 'lucide-react';
import { api } from '../api';
import { Badge, Button, Card, DataTable, Modal } from '../ui/components';
import { confirmDialog, promptDialog, toast } from '../ui/feedback';
import OdooProductPicker from './OdooProductPicker';

const fmtTl = (v) => (v == null ? '—' : `${Number(v).toLocaleString('tr-TR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} ₺`);
const fmtCr = (v) => Number(v || 0).toLocaleString('tr-TR');
const fmtDate = (d) => (d ? new Date(d).toLocaleString('tr-TR', { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' }) : '—');
const PLANS = [['STARTER', 'Başlangıç'], ['PRO', 'Profesyonel'], ['ENTERPRISE', 'Kurumsal']];
const TONE = { PENDING: 'warning', LOADED: 'success', CANCELLED: 'neutral', EXPIRED: 'neutral' };
const EMPTY = { code: '', name: '', credits: 5000, price_try: '', odoo_product_id: '', plan_codes: [], sort_order: 0, is_active: false };

function PackForm({ pack, onClose, onSaved }) {
  const [f, setF] = useState(pack ? { ...pack, price_try: pack.price_try ?? '', odoo_product_id: pack.odoo_product_id ?? '' } : EMPTY);
  const [busy, setBusy] = useState(false);
  const save = async () => {
    setBusy(true);
    const data = { ...f, credits: Number(f.credits), price_try: f.price_try === '' ? null : Number(f.price_try),
      odoo_product_id: f.odoo_product_id === '' ? null : Number(f.odoo_product_id), sort_order: Number(f.sort_order || 0) };
    try {
      await (pack ? api.updateCreditPack(pack.id, data) : api.createCreditPack(data));
      toast.success('Kredi paketi kaydedildi.');
      onSaved();
      onClose();
    } catch (e) { toast.error(e.message); } finally { setBusy(false); }
  };
  const set = (k) => (e) => setF({ ...f, [k]: e.target.value });
  const togglePlan = (c) => setF({ ...f, plan_codes: f.plan_codes.includes(c) ? f.plan_codes.filter((x) => x !== c) : [...f.plan_codes, c] });
  return (
    <Modal open onClose={onClose} title={pack ? `Kredi paketi: ${pack.name}` : 'Yeni kredi paketi'}
      footer={<><Button variant="ghost" onClick={onClose}>Vazgeç</Button><Button onClick={save} disabled={busy}>Kaydet</Button></>}>
      <div className="pj-steps">
        <label className="pj-hint" htmlFor="cp-code">Kod</label>
        <input id="cp-code" className="ui-input" value={f.code} onChange={set('code')} placeholder="KREDI-10K" />
        <label className="pj-hint" htmlFor="cp-name">Ad</label>
        <input id="cp-name" className="ui-input" value={f.name} onChange={set('name')} placeholder="10.000 Kredi" />
        <label className="pj-hint" htmlFor="cp-credits">Kredi miktarı</label>
        <input id="cp-credits" className="ui-input" type="number" min={100} value={f.credits} onChange={set('credits')} />
        <label className="pj-hint" htmlFor="cp-price">Fiyat (₺, KDV hariç; boşsa satışa kapalı)</label>
        <input id="cp-price" className="ui-input" type="number" min={0} step="0.01" value={f.price_try} onChange={set('price_try')} />
        <OdooProductPicker value={f.odoo_product_id} planPrice={f.price_try} onChange={(id) => setF({ ...f, odoo_product_id: id })} label="Odoo satış ürünü (satış siparişi satırı)" />
        <span className="pj-hint">Geçerli abonelik paketleri (hiçbiri seçilmezse tümü)</span>
        <div style={{ display: 'flex', gap: 14, flexWrap: 'wrap' }}>
          {PLANS.map(([c, n]) => <label key={c} className="pj-hint"><input type="checkbox" checked={f.plan_codes.includes(c)} onChange={() => togglePlan(c)} /> {n}</label>)}
        </div>
        <label className="pj-hint" htmlFor="cp-order">Sıra</label>
        <input id="cp-order" className="ui-input" type="number" value={f.sort_order} onChange={set('sort_order')} style={{ maxWidth: 120 }} />
        <label className="pj-hint"><input type="checkbox" checked={f.is_active} onChange={(e) => setF({ ...f, is_active: e.target.checked })} /> Satışta (fiyat ve Odoo ürünü gerekli)</label>
      </div>
    </Modal>
  );
}

/** İSTEK #747 (Merkez): kredi paketleri tanımı, kredi siparişleri (havale/EFT onayı = kredi yükleme) ve banka bilgisi. */
export default function CreditPacksAdmin() {
  const [packs, setPacks] = useState([]);
  const [orders, setOrders] = useState([]);
  const [billing, setBilling] = useState({ bank_info: '' });
  const [editing, setEditing] = useState(null);
  const [status, setStatus] = useState('PENDING');
  const load = useCallback(async () => {
    try {
      const [p, o, b] = await Promise.all([api.getCreditPacks(), api.getCreditOrders(status || undefined), api.getBillingSettings()]);
      setPacks(p); setOrders(o); setBilling(b);
    } catch (e) { toast.error(e.message); }
  }, [status]);
  useEffect(() => { load(); }, [load]);

  const loadOrder = async (o) => {
    if (!(await confirmDialog({ message: `${o.tenant_name} · ${o.odoo_order_name} · ${fmtTl(o.price_try)} + KDV ödemesi alındı mı? Onaylarsanız Odoo siparişi onaylanır, taslak fatura oluşur${o.kind === 'PLAN_UPGRADE' ? ', şirketin paketi hemen değişir' : ''} ve ${fmtCr(o.credits)} kredi yüklenir.`, confirmText: 'Ödeme alındı, krediyi yükle' }))) return;
    try { await api.loadCreditOrder(o.id); toast.success('Kredi yüklendi; müşteriye bildirildi.'); load(); } catch (e) { toast.error(e.message); }
  };
  const cancelOrder = async (o) => {
    const reason = await promptDialog({ title: 'Siparişi iptal et', message: `${o.tenant_name} · ${o.odoo_order_name} iptal edilecek (Odoo siparişi de iptal edilir). Gerekçe:` });
    if (reason === null) return;
    try { await api.cancelCreditOrderHq(o.id, reason); toast.success('Sipariş iptal edildi.'); load(); } catch (e) { toast.error(e.message); }
  };
  const saveBank = async () => {
    try { setBilling(await api.putBillingSettings({ bank_info: billing.bank_info })); toast.success('Banka bilgileri kaydedildi.'); } catch (e) { toast.error(e.message); }
  };

  return (
    <div className="pj-steps">
      <Card title="Kredi paketleri" subtitle="Müşterilerin satın aldığı ek kredi paketleri. Fiyat KDV hariçtir; satış siparişi seçilen Odoo ürünüyle açılır."
        actions={<Button size="sm" icon={Plus} onClick={() => setEditing({})}>Yeni kredi paketi</Button>}>
        <DataTable rows={packs} pageSize={20} columns={[
          { key: 'name', label: 'Ad', render: (r) => <span><strong>{r.name}</strong> <small className="pj-hint">{r.code}</small></span> },
          { key: 'credits', label: 'Kredi', align: 'right', render: (r) => fmtCr(r.credits) },
          { key: 'price_try', label: 'Fiyat (KDV hariç)', align: 'right', render: (r) => fmtTl(r.price_try) },
          { key: 'odoo_product_id', label: 'Odoo ürünü', render: (r) => (r.odoo_product_id ? `#${r.odoo_product_id}` : '—') },
          { key: 'plan_codes', label: 'Geçerli paketler', sortable: false, render: (r) => (r.plan_codes.length ? r.plan_codes.join(', ') : 'Tümü') },
          { key: 'is_active', label: 'Durum', render: (r) => <Badge tone={r.sellable ? 'success' : 'neutral'}>{r.sellable ? 'Satışta' : (r.is_active ? 'Eksik bilgi' : 'Kapalı')}</Badge> },
          { key: 'edit', label: '', sortable: false, render: (r) => <Button size="sm" variant="ghost" icon={Pencil} aria-label={`${r.name} paketini düzenle`} onClick={() => setEditing(r)}>Düzenle</Button> },
        ]} emptyText="Kredi paketi yok." />
      </Card>

      <Card title="Kredi siparişleri" subtitle="Havale/EFT ile verilen siparişlerde ödeme gelince krediyi siz yüklersiniz; 7 gün içinde ödenmeyen sipariş kendiliğinden iptal olur."
        actions={(
          <select className="ui-input" aria-label="Sipariş durumu" value={status} onChange={(e) => setStatus(e.target.value)} style={{ maxWidth: 200 }}>
            <option value="PENDING">Ödeme bekleyenler</option>
            <option value="LOADED">Kredi yüklenenler</option>
            <option value="">Tümü</option>
          </select>
        )}>
        <DataTable rows={orders} pageSize={20} columns={[
          { key: 'created_at', label: 'Tarih', render: (r) => fmtDate(r.created_at), sortValue: (r) => r.created_at },
          { key: 'tenant_name', label: 'Şirket' },
          { key: 'pack_name', label: 'Sipariş', render: (r) => (r.kind === 'PLAN_UPGRADE' ? `${r.pack_name} (+${fmtCr(r.credits)} kredi)` : r.pack_name) },
          { key: 'odoo_order_name', label: 'Odoo sipariş' },
          { key: 'price_try', label: 'Tutar (KDV hariç)', align: 'right', render: (r) => fmtTl(r.price_try) },
          { key: 'payment_method', label: 'Ödeme', render: (r) => (r.payment_method === 'CARD' ? 'Kart' : 'Havale/EFT') },
          { key: 'status', label: 'Durum', render: (r) => <Badge tone={TONE[r.status] || 'neutral'}>{r.status_label}</Badge> },
          { key: 'act', label: '', sortable: false, render: (r) => (r.status === 'PENDING' ? (
            <span style={{ display: 'flex', gap: 6 }}>
              <Button size="sm" variant="success" icon={CheckCircle2} onClick={() => loadOrder(r)}>Ödeme alındı, krediyi yükle</Button>
              <Button size="sm" variant="ghost" onClick={() => cancelOrder(r)}>İptal</Button>
            </span>
          ) : (r.invoice_drafted ? <small className="pj-hint">Odoo taslak fatura var</small> : null)) },
        ]} emptyText="Sipariş yok." />
      </Card>

      <Card title="Havale/EFT banka bilgileri" subtitle="Müşteriye sipariş anında ekranda ve e-postada gösterilir." actions={<Coins size={18} />}>
        <textarea className="ui-input" rows={4} aria-label="Banka bilgileri" value={billing.bank_info}
          onChange={(e) => setBilling({ ...billing, bank_info: e.target.value })} placeholder="Banka, şube, hesap adı, IBAN…" />
        <div style={{ marginTop: 8 }}><Button size="sm" onClick={saveBank}>Kaydet</Button>
          <span className="pj-hint" style={{ marginLeft: 10 }}>Kartla ödeme: {billing.card_enabled ? 'açık' : 'kapalı (sanal POS sağlayıcısı seçilince açılır)'}</span></div>
      </Card>
      {editing && <PackForm pack={editing.id ? editing : null} onClose={() => setEditing(null)} onSaved={load} />}
    </div>
  );
}
