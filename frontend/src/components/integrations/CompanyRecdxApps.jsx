import React, { useCallback, useEffect, useState } from 'react';
import { Save } from 'lucide-react';
import { api } from '../../api';
import { Badge, Button, Card } from '../../ui/components';
import { toast } from '../../ui/feedback';
import RecdxAppsChoice from './RecdxAppsChoice';

const STATE = { ACTIVE: ['Entegrasyon açık', 'success'], NEEDS_ODOO: ['Odoo bağlantısı gerekli', 'warning'], QUOTE: ['Teklif istendi', 'info'], OFF: ['Kapalı', 'neutral'] };
const REQ = { NEW: 'işleniyor', ORDERED: 'Odoo siparişine eklendi', OPPORTUNITY: 'RECDx satış ekibine iletildi', IN_USE: 'zaten kullanıyorsunuz',
  DONE: 'tamamlandı', CANCELLED: 'iptal', FAILED: 'RECDx ekibi ilgileniyor', SKIPPED: 'RECDx ekibi ilgileniyor' };

/** Şirket Yönetimi > Entegrasyonlar: Odoo ve RECDx uygulamaları (ADIM 13.1). Seçime göre entegrasyon açılır veya teklif/sipariş iletilir. */
export default function CompanyRecdxApps({ tenantId, onChanged }) {
  const [data, setData] = useState(null);
  const [choice, setChoice] = useState(null);
  const [busy, setBusy] = useState(false);
  const load = useCallback(() => api.getCompanyRecdxApps(tenantId).then((d) => {
    setData(d);
    setChoice({ has_odoo: d.has_odoo ?? null, apps: Object.fromEntries(d.apps.filter((a) => a.choice).map((a) => [a.code, a.choice])) });
  }).catch((e) => toast.error(e.message)), [tenantId]);
  useEffect(() => { load(); }, [load]);
  if (!data || !choice) return null;
  const save = async () => {
    setBusy(true);
    try {
      const d = await api.setCompanyRecdxApps(tenantId, choice);
      setData(d);
      toast.success('Tercihiniz kaydedildi.');
      onChanged?.();
    } catch (e) { toast.error(e.message); } finally { setBusy(false); }
  };
  return (
    <Card title="RECDx uygulamaları (Odoo)" subtitle={`RECQmind ve RECSlip, Odoo'nuzda çalışır ve RECOrion ile birlikte iş yürütür. Paketiniz: ${data.plan_name || '—'}.`}
      actions={<Button icon={Save} disabled={busy} onClick={save}>{busy ? 'Kaydediliyor…' : 'Kaydet'}</Button>}>
      <div className="pj-meta" style={{ marginBottom: 8 }}>
        {data.apps.map((a) => {
          const [label, tone] = STATE[a.state] || [a.state, 'neutral'];
          return <span key={a.code}><b>{a.title}:</b> <Badge tone={tone}>{label}</Badge>{a.request ? ` · ${REQ[a.request.status] || a.request.status}${a.request.odoo_order_name ? ` (${a.request.odoo_order_name})` : ''}` : ''}</span>;
        })}
      </div>
      <RecdxAppsChoice apps={data.apps} value={choice} onChange={setChoice} idPrefix="co" />
    </Card>
  );
}
