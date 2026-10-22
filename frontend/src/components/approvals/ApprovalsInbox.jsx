import React, { useCallback, useEffect, useState } from 'react';
import { CheckCircle2, ShieldAlert } from 'lucide-react';
import { api } from '../../api';
import { Badge, Button, EmptyState } from '../../ui/components';
import { toast } from '../../ui/feedback';
import '../projects/projects.css';

const fmt = (d) => (d ? new Date(d).toLocaleString('tr-TR', { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' }) : '');

/** Onay kuyruğu (ADIM 7.3): kişinin tüm projelerde kararını bekleyen onaylar ve karantinadaki adımlar. */
export default function ApprovalsInbox({ onOpenProject, onCount }) {
  const [items, setItems] = useState(null);
  const load = useCallback(() => api.getMyApprovals().then((r) => { setItems(r); onCount?.(r.length); })
    .catch((e) => { setItems([]); toast.error(e.message); }), [onCount]);
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
