import React, { useCallback, useEffect, useState } from 'react';
import { PlayCircle } from 'lucide-react';
import { api } from '../../api';
import { Badge, Button, Modal } from '../../ui/components';
import { toast } from '../../ui/feedback';

const caseLink = (id) => `#/workspace?project=${id}`;

/** RECSlip.App v2 aylık masraf süreci (ADIM 14): kurulum (Odoo bağlantısı, Case yöneticisi, kapanış raporu), durum, hemen çalıştır. */
export default function RecslipSetup({ tenantId, people }) {
  const [data, setData] = useState(null);
  const [setup, setSetup] = useState(false);
  const [busy, setBusy] = useState(false);
  const load = useCallback(() => api.getRecslip(tenantId).then(setData).catch(() => setData({ connections: [], cases: [], credentials: [] })), [tenantId]);
  useEffect(() => { load(); }, [load]);
  if (!data) return null;
  const current = data.cases.find((c) => c.status === 'ACTIVE');
  const run = async () => {
    setBusy(true);
    try {
      const r = await api.runRecslip(tenantId);
      toast.success(`RECSlip: ${r.pending ?? 0} bekleyen adım · AI onayı ${r.auto ?? 0} · insana ${r.review ?? 0}${r.failed ? ` · hata ${r.failed}` : ''}`);
      load();
    } catch (e) { toast.error(e.message); } finally { setBusy(false); }
  };
  const keys = data.credentials.filter((c) => c.usable).length;
  return (
    <div className="ig-steps" aria-label="RECSlip.App v2 aylık süreç">
      <p><strong>RECSlip.App v2 aylık süreç</strong> {current ? <Badge tone="success">Çalışıyor</Badge> : <Badge tone="neutral">Kurulmadı</Badge>}</p>
      <p className="pj-hint">Fişler v2'de okunup onaya gönderilince onay adımlarını kişilerin AI personeli kriterlere göre yürütür; her ay bir Case açılır,
        ay sonu kesim ve aktarım dosyası Case'te. Onaylayanlar kendi Odoo anahtarlarını Bağlantılarım'dan ekler ({keys} kişi ekledi).</p>
      {current ? (
        <p><a href={caseLink(current.project_id)}>{current.name}</a> · aktarım {current.calendar?.export ? new Date(current.calendar.export).toLocaleDateString('tr-TR') : '—'}
          {' '}<Button size="sm" variant="secondary" icon={PlayCircle} disabled={busy} onClick={run}>Şimdi çalıştır</Button></p>
      ) : (
        <Button size="sm" onClick={() => setSetup(true)} disabled={!data.connections.length}>Kur</Button>
      )}
      {!data.connections.length && <p className="pj-hint">Önce Entegrasyonlar'da RECSlip.App v2 kurulu Odoo'yu bağlayın.</p>}
      {setup && <SetupModal tenantId={tenantId} data={data} people={people} onClose={() => setSetup(false)} onDone={() => { setSetup(false); load(); }} />}
    </div>
  );
}

function SetupModal({ tenantId, data, people, onClose, onDone }) {
  const [agents, setAgents] = useState([]);
  const [conn, setConn] = useState(data.connections[0]?.id || '');
  const [manager, setManager] = useState('');
  const [agent, setAgent] = useState('');
  const [approver, setApprover] = useState('');
  const [busy, setBusy] = useState(false);
  useEffect(() => { api.getCompanyAIAgents(tenantId).then((a) => setAgents(a || [])).catch(() => setAgents([])); }, [tenantId]);
  const save = async () => {
    setBusy(true);
    try {
      await api.setupRecslip(tenantId, { connection_id: conn, manager_actor_id: manager, report_agent_id: agent, report_approver_id: approver });
      toast.success('RECSlip aylık süreci kuruldu; bu ayın Case\'i açıldı.');
      onDone();
    } catch (e) { toast.error(e.message); } finally { setBusy(false); }
  };
  const sel = (id, label, value, set, list) => (
    <div className="pj-field full"><label htmlFor={id}>{label}</label>
      <select id={id} className="ui-input" value={value} onChange={(e) => set(e.target.value)}>
        <option value="">Seçin</option>
        {list.map((x) => <option key={x.id} value={x.id}>{x.display_name || x.name}</option>)}
      </select></div>);
  return (
    <Modal open onClose={onClose} title="RECSlip.App v2 aylık süreç" size="md"
      footer={<><Button variant="secondary" onClick={onClose}>Vazgeç</Button>
        <Button disabled={busy || !conn || !manager || !agent || !approver} onClick={save}>{busy ? 'Kuruluyor…' : 'Kur ve bu ayın Case\'ini aç'}</Button></>}>
      <div className="pj-form">
        {sel('rs-conn', 'RECSlip.App v2 kurulu Odoo', conn, setConn, data.connections)}
        {sel('rs-manager', 'Case yöneticisi (muhasebeci; aktarım dosyası onun anahtarıyla oluşturulur)', manager, setManager, people)}
        {sel('rs-agent', 'Kapanış raporunu yazacak AI personel', agent, setAgent, agents)}
        {sel('rs-approver', 'Kapanış raporunu onaylayacak kişi (muhasebe müdürü)', approver, setApprover, people)}
        <p className="pj-hint">Ayarlar ve onay kriterleri önerilen varsayılanlarla gelir; Case'in RECSlip sekmesinden değiştirilir.</p>
      </div>
    </Modal>
  );
}
