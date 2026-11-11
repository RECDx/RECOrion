import React, { useEffect, useState } from 'react';
import { api } from '../../api';
import { Badge, Button, Card } from '../../ui/components';
import { toast } from '../../ui/feedback';

const fmt = (d) => (d ? new Date(d).toLocaleString('tr-TR', { dateStyle: 'short', timeStyle: 'short' }) : '');
const HOURS = [[1, '1 saat'], [4, '4 saat'], [24, '1 gün'], [72, '3 gün'], [168, '1 hafta']];

/**
 * İSTEK #738: RECDx destek erişimi. KVKK gereği RECDx şirket içeriğinizi göremez; bir sorunu incelemesi için süreli erişim
 * verebilirsiniz. Süre boyunca Merkez Beyin AI iş durumunuzu (proje/adım durumu, durma nedenleri) görür; her okuma burada listelenir.
 */
export default function SupportAccessCard({ tenantId }) {
  const [d, setD] = useState(null);
  const [hours, setHours] = useState(4);
  const [reason, setReason] = useState('');
  const [busy, setBusy] = useState(false);
  useEffect(() => { api.getSupportAccess(tenantId).then(setD).catch((e) => toast.error(e.message)); }, [tenantId]);

  const run = async (fn, ok) => {
    setBusy(true);
    try { setD(await fn()); toast.success(ok); } catch (e) { toast.error(e.message); } finally { setBusy(false); }
  };

  return (
    <Card title="RECDx destek erişimi" subtitle="KVKK gereği RECDx şirketinizin içeriğini göremez. Bir sorunun incelenmesi için süreli erişim verebilirsiniz; her okuma aşağıda listelenir.">
      {!d ? <p className="pj-hint">Yükleniyor…</p> : (
        <>
          {d.active ? (
            <div className="pj-meta" style={{ flexWrap: 'wrap', gap: 10, alignItems: 'center' }}>
              <Badge tone="warning">Erişim açık</Badge>
              <span>{fmt(d.active.expires_at)}'e kadar{d.active.reason ? ` · ${d.active.reason}` : ''}</span>
              <Button size="sm" variant="secondary" disabled={busy} onClick={() => run(() => api.revokeSupportAccess(tenantId), 'Destek erişimi kapatıldı.')}>Erişimi şimdi kapat</Button>
            </div>
          ) : (
            <div className="pj-form">
              <div className="pj-field"><label htmlFor="sa-hours">Süre</label>
                <select id="sa-hours" className="ui-input" value={hours} onChange={(e) => setHours(Number(e.target.value))}>
                  {HOURS.map(([h, l]) => <option key={h} value={h}>{l}</option>)}
                </select></div>
              <div className="pj-field"><label htmlFor="sa-reason">Neden (isteğe bağlı)</label>
                <input id="sa-reason" className="ui-input" maxLength={500} value={reason} placeholder="ör. Teklif adımı takılıyor" onChange={(e) => setReason(e.target.value)} /></div>
              <div className="pj-field" style={{ alignSelf: 'end' }}>
                <Button disabled={busy} onClick={() => run(() => api.grantSupportAccess(tenantId, { hours, reason: reason.trim() || null }), 'RECDx desteğine süreli erişim verildi.')}>Erişim ver</Button>
              </div>
            </div>
          )}
          <h4 style={{ margin: '14px 0 6px', fontSize: '0.85rem' }}>Erişim kayıtları</h4>
          {d.logs.length === 0 ? <p className="pj-hint">RECDx bugüne kadar destek erişimiyle bir şey okumadı.</p> : (
            <ul className="pj-list" aria-label="Destek erişimi kayıtları">
              {d.logs.map((l, i) => <li key={i}><span>{fmt(l.at)} · {l.who}</span><strong>{l.detail || l.action}</strong></li>)}
            </ul>
          )}
        </>
      )}
    </Card>
  );
}
