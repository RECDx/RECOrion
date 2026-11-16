import React, { useCallback, useEffect, useState } from 'react';
import { ShoppingCart } from 'lucide-react';
import { api } from '../../api';
import { Badge, Button, Card, Modal } from '../../ui/components';
import { confirmDialog, toast } from '../../ui/feedback';
import { fmtCredits, fmtDate } from './format';

const fmtTl = (v) => (v == null ? '—' : `${Number(v).toLocaleString('tr-TR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} ₺`);
const TONE = { PENDING: 'warning', LOADED: 'success', CANCELLED: 'neutral', EXPIRED: 'neutral' };

/** #747: "Ek kredi al" — paket ve ödeme yöntemi seçilir; Odoo'da satış siparişi açılır, havale/EFT bilgisi gösterilir. */
export function BuyCreditsModal({ tenantId, store, onClose, onOrdered }) {
  const [packId, setPackId] = useState(store.packs[0]?.id || '');
  const [method, setMethod] = useState('TRANSFER');
  const [busy, setBusy] = useState(false);
  const [done, setDone] = useState(null);
  const order = async () => {
    setBusy(true);
    try {
      const o = await api.placeCreditOrder(tenantId, { pack_id: packId, payment_method: method });
      setDone(o);
      onOrdered?.();
    } catch (e) { toast.error(e.message); } finally { setBusy(false); }
  };
  return (
    <Modal open onClose={onClose} title="Ek kredi al"
      footer={done ? <Button onClick={onClose}>Kapat</Button>
        : <><Button variant="ghost" onClick={onClose}>Vazgeç</Button><Button icon={ShoppingCart} onClick={order} disabled={busy || !packId}>Siparişi oluştur</Button></>}>
      {done ? (
        <div className="ai-stack">
          <p><strong>{fmtCredits(done.credits)} kredi</strong> siparişiniz alındı. Sipariş no: <strong>{done.odoo_order_name}</strong> · {fmtTl(done.price_try)} + KDV</p>
          <p className="pj-hint" style={{ margin: 0 }}>Havale/EFT açıklamasına sipariş numarasını yazın. Ödeme RECDx'e ulaşınca kredi yüklenir ve size e-posta gelir;
            {` ${store.valid_days}`} gün içinde ödeme gelmezse sipariş kendiliğinden iptal edilir.</p>
          <pre className="ai-pre">{store.bank_info || 'Banka bilgileri için RECDx ile iletişime geçin.'}</pre>
        </div>
      ) : store.packs.length === 0 ? (
        <p className="pj-hint">Şu an satın alınabilir kredi paketi yok. RECDx ile iletişime geçin.</p>
      ) : (
        <div className="ai-stack">
          <div className="ai-stats" role="radiogroup" aria-label="Kredi paketi">
            {store.packs.map((p) => (
              <button key={p.id} type="button" role="radio" aria-checked={packId === p.id}
                className={`ai-stat ai-pick${packId === p.id ? ' active' : ''}`} onClick={() => setPackId(p.id)}>
                <div className="ai-stat-label">{p.name}</div>
                <div className="ai-stat-value">{fmtTl(p.price_try)}</div>
                <div className="ai-stat-note">KDV hariç · kredi başı {p.unit_price_try?.toLocaleString('tr-TR')} ₺</div>
              </button>
            ))}
          </div>
          <fieldset className="pj-hint" style={{ border: 0, padding: 0, margin: 0 }}>
            <legend>Ödeme yöntemi</legend>
            <label style={{ marginRight: 16 }}><input type="radio" name="pay" checked={method === 'TRANSFER'} onChange={() => setMethod('TRANSFER')} /> Havale/EFT</label>
            <label><input type="radio" name="pay" checked={method === 'CARD'} disabled={!store.card_enabled} onChange={() => setMethod('CARD')} />
              {' '}Kart (sanal POS){store.card_enabled ? '' : ' — yakında'}</label>
          </fieldset>
          <p className="pj-hint" style={{ margin: 0 }}>Sipariş, RECDx'in Odoo sisteminde satış siparişi olarak açılır. Havale/EFT'de kredi, ödeme RECDx'e ulaşınca yüklenir.</p>
        </div>
      )}
    </Modal>
  );
}

/** #747 ek: paket yükseltme — hemen geçerli; bu ayın kalan günleri için oransal fiyat ve kredi farkı. */
export function UpgradePlanModal({ tenantId, store, onClose, onOrdered }) {
  const [planId, setPlanId] = useState(store.upgrade_options[0]?.plan_id || '');
  const [busy, setBusy] = useState(false);
  const [done, setDone] = useState(null);
  const order = async () => {
    setBusy(true);
    try { setDone(await api.placePlanUpgrade(tenantId, { plan_id: planId })); onOrdered?.(); } catch (e) { toast.error(e.message); } finally { setBusy(false); }
  };
  return (
    <Modal open onClose={onClose} title="Paketi yükselt"
      footer={done ? <Button onClick={onClose}>Kapat</Button>
        : <><Button variant="ghost" onClick={onClose}>Vazgeç</Button><Button onClick={order} disabled={busy || !planId}>Yükseltme siparişi oluştur</Button></>}>
      {done ? (
        <div className="ai-stack">
          <p>Yükseltme siparişiniz alındı. Sipariş no: <strong>{done.odoo_order_name}</strong> · {fmtTl(done.price_try)} + KDV</p>
          <p className="pj-hint" style={{ margin: 0 }}>Ödeme RECDx'e ulaşınca paketiniz hemen değişir ve bu ayın kredi farkı ({fmtCredits(done.credits)} kredi) yüklenir.</p>
          <pre className="ai-pre">{store.bank_info || 'Banka bilgileri için RECDx ile iletişime geçin.'}</pre>
        </div>
      ) : store.upgrade_options.length === 0 ? (
        <p className="pj-hint">Şu an geçebileceğiniz üst paket yok. RECDx ile iletişime geçin.</p>
      ) : (
        <div className="ai-stack">
          <p className="pj-hint" style={{ margin: 0 }}>Şu anki paketiniz: <strong>{store.current_plan?.name || '—'}</strong>. Yükseltme hemen geçerli olur; bu ay için yalnız kalan
            günlerin farkı ödenir, gelecek aydan itibaren yeni paketin aylık ücreti ve kredisi geçerlidir.</p>
          <div className="ai-stats" role="radiogroup" aria-label="Yeni paket">
            {store.upgrade_options.map((o) => (
              <button key={o.plan_id} type="button" role="radio" aria-checked={planId === o.plan_id}
                className={`ai-stat ai-pick${planId === o.plan_id ? ' active' : ''}`} onClick={() => setPlanId(o.plan_id)}>
                <div className="ai-stat-label">{o.name}</div>
                <div className="ai-stat-value">{fmtTl(o.prorated_price_try)}</div>
                <div className="ai-stat-note">Bu ay ({o.days_left}/{o.days_in_month} gün) fark + KDV · +{fmtCredits(o.prorated_credits)} kredi · sonra aylık {fmtTl(o.monthly_price)}</div>
              </button>
            ))}
          </div>
        </div>
      )}
    </Modal>
  );
}

/** #747: şirketin kredi siparişleri ve "Ek kredi al" düğmesi. */
export default function CreditOrders({ tenantId, canManage, onChanged }) {
  const [store, setStore] = useState(null);
  const [buying, setBuying] = useState(false);
  const [upgrading, setUpgrading] = useState(false);
  const load = useCallback(() => api.getCreditStore(tenantId).then(setStore).catch(() => setStore(null)), [tenantId]);
  useEffect(() => { load(); }, [load]);
  if (!store) return null;
  const cancel = async (o) => {
    if (!(await confirmDialog({ message: `${o.odoo_order_name} numaralı ${fmtCredits(o.credits)} kredi siparişi iptal edilsin mi?` }))) return;
    try { await api.cancelCreditOrder(tenantId, o.id); toast.success('Sipariş iptal edildi.'); load(); } catch (e) { toast.error(e.message); }
  };
  return (
    <Card title="Ek kredi" subtitle="Ek krediler dönem sonunda silinmez; sonraki aylara devreder."
      actions={canManage ? <span style={{ display: 'flex', gap: 6 }}><Button size="sm" icon={ShoppingCart} onClick={() => setBuying(true)}>Ek kredi al</Button>
        <Button size="sm" variant="secondary" onClick={() => setUpgrading(true)}>Paketi yükselt</Button></span> : null}>
      {store.orders.length === 0 ? <p className="ai-dim">Henüz kredi siparişi yok.</p> : (
        <ul className="ai-list" aria-label="Kredi siparişlerim">
          {store.orders.map((o) => (
            <li key={o.id}>
              <span>{fmtDate(o.created_at)} · {o.pack_name} · {o.odoo_order_name} · {fmtTl(o.price_try)} + KDV</span>
              <span>
                <Badge tone={TONE[o.status] || 'neutral'}>{o.status_label}</Badge>
                {canManage && o.status === 'PENDING' && <> <Button size="sm" variant="ghost" onClick={() => cancel(o)}>İptal et</Button></>}
              </span>
            </li>
          ))}
        </ul>
      )}
      {upgrading && <UpgradePlanModal tenantId={tenantId} store={store} onClose={() => { setUpgrading(false); load(); onChanged?.(); }} onOrdered={load} />}
      {buying && <BuyCreditsModal tenantId={tenantId} store={store} onClose={() => { setBuying(false); load(); onChanged?.(); }} onOrdered={load} />}
    </Card>
  );
}
