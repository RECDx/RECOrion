import React, { useCallback, useEffect, useState } from 'react';
import { CheckCircle2, ShieldAlert } from 'lucide-react';
import { api } from '../../api';
import { Badge, Button, EmptyState } from '../../ui/components';
import { promptDialog, toast } from '../../ui/feedback';
import '../projects/projects.css';

const fmt = (d) => (d ? new Date(d).toLocaleString('tr-TR', { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' }) : '');

/** Onay kuyruğu (ADIM 7.3): kişinin tüm projelerde kararını bekleyen onaylar ve karantinadaki adımlar. */
export default function ApprovalsInbox({ onOpenProject, onCount }) {
  const [items, setItems] = useState(null);
  const [tools, setTools] = useState([]);  // Adım 10: AI personelin onay bekleyen yazma işlemleri
  const load = useCallback(() => Promise.all([api.getMyApprovals(), api.getMyToolApprovals().catch(() => [])])
    .then(([r, t]) => { setItems(r); setTools(t); onCount?.(r.length + t.length); })
    .catch((e) => { setItems([]); toast.error(e.message); }), [onCount]);
  const decideTool = async (c, approve) => {
    const note = approve ? '' : await promptDialog({ title: 'Reddet', message: 'Ret gerekçesi (isteğe bağlı):' });
    if (note === null) return;
    try {
      const r = await api.decideToolCall(c.id, approve, note);
      r.status === 'EXECUTED' ? toast.success('Onaylandı ve çalıştırıldı.') : r.status === 'REJECTED' ? toast.success('Reddedildi.') : toast.error(r.error || 'Çalıştırılamadı.');
      load();
    } catch (e) { toast.error(e.message); }
  };
  useEffect(() => {
    load();
    const t = setInterval(load, 15000);
    return () => clearInterval(t);
  }, [load]);

  return (
    <div className="pj-page">
      <div className="pj-head">
        <div className="pj-title">
          <h2>Onaylarım</h2>
          <span className="pj-sub">Kararınızı bekleyen iş adımları. E-postadaki bağlantıdan veya Telegram butonlarından da karar verebilirsiniz.</span>
        </div>
      </div>
      {tools.length > 0 && (
        <div style={{ marginBottom: 16 }}>
          <h3 style={{ fontSize: '0.95rem', margin: '0 0 8px' }}>Araç işlemleri (yazma)</h3>
          <ul className="pj-list" aria-label="Onay bekleyen araç işlemleri">
            {tools.map((c) => (
              <li key={c.id}>
                <span>
                  <strong>{c.actor_name}</strong> · {c.connection_name} · <code>{c.tool}</code><br />
                  <small className="pj-hint" title={JSON.stringify(c.arguments)}>{JSON.stringify(c.arguments).slice(0, 160)} · {fmt(c.created_at)}</small>
                </span>
                <Badge tone="warning">Onay bekliyor</Badge>
                <Button size="sm" onClick={() => decideTool(c, true)}>Onayla ve çalıştır</Button>
                <Button size="sm" variant="secondary" onClick={() => decideTool(c, false)}>Reddet</Button>
              </li>
            ))}
          </ul>
        </div>
      )}
      {!items ? <p className="pj-hint">Yükleniyor…</p> : items.length === 0 ? (
        <EmptyState icon={CheckCircle2} title="Bekleyen karar yok" description="Onayınızı bekleyen bir iş adımı olduğunda burada görünür." />
      ) : (
        <ul className="pj-list">
          {items.map((i) => (
            <li key={i.task_id}>
              <span>
                <strong>{i.title}</strong><br />
                <small className="pj-hint">{i.project_name}{i.assignee ? ` · ${i.assignee}` : ''}{i.submitted_at ? ` · teslim ${fmt(i.submitted_at)}` : ''}
                  {i.rejection_count ? ` · ret ${i.rejection_count}` : ''}</small>
              </span>
              {i.kind === 'APPROVAL' ? <Badge tone="warning">Onay bekliyor</Badge> : <Badge tone="danger"><ShieldAlert size={12} /> Karantinada</Badge>}
              <Button size="sm" onClick={() => onOpenProject(i.project_id)}>İncele</Button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
