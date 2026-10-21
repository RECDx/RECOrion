import React, { useCallback, useEffect, useState } from 'react';
import { CheckCircle2, XCircle } from 'lucide-react';
import { api } from '../../api';
import { Badge, Button, Card } from '../../ui/components';
import { toast } from '../../ui/feedback';
import './docs.css';

/**
 * Kurum Hafızası onay kuyruğu (ADIM 5.5): AI personelin sohbetlerden çıkardığı şirket geneli bilgiler,
 * şirketin tüm AI personelini etkilediği için onaylanmadan öğrenilmez.
 */
export default function MemoryApprovalQueue({ tenantId, canManage = true }) {
  const [items, setItems] = useState(null);
  const [busy, setBusy] = useState('');

  const load = useCallback(() => api.getMemoryCandidates(tenantId).then(setItems).catch((e) => toast.error(e.message)), [tenantId]);
  useEffect(() => { load(); }, [load]);

  const act = async (id, approve) => {
    setBusy(id);
    try {
      if (approve) await api.promoteMemory(id); else await api.rejectMemory(id);
      toast.success(approve ? 'Bilgi Kurum Hafızasına eklendi; tüm AI personel kullanacak.' : 'Bilgi reddedildi.');
      setItems((list) => list.filter((x) => x.id !== id));
    } catch (e) {
      toast.error(e.message);
    } finally {
      setBusy('');
    }
  };

  return (
    <Card title={`Kurum Hafızası Onay Kuyruğu${items?.length ? ` (${items.length})` : ''}`}
      subtitle="AI personelin sohbetlerden çıkardığı şirket geneli bilgiler. Onaylanan bilgiyi şirketin tüm AI personeli kullanır.">
      {!items ? <p className="doc-hint">Yükleniyor…</p> : items.length === 0 ? <p className="doc-hint">Onay bekleyen bilgi yok.</p> : (
        <ul className="doc-list">
          {items.map((m) => (
            <li key={m.id}>
              <div className="doc-main">
                <strong style={{ whiteSpace: 'normal' }}>{m.content}</strong>
                <span>{m.metadata_json?.category || 'Bilgi'} · güven %{Math.round((m.confidence_score || 0) * 100)}{m.created_at ? ` · ${new Date(m.created_at).toLocaleDateString('tr-TR')}` : ''}</span>
              </div>
              <Badge tone="warning">Onay bekliyor</Badge>
              {canManage && (
                <>
                  <Button size="sm" variant="ghost" icon={XCircle} onClick={() => act(m.id, false)} disabled={busy === m.id}>Reddet</Button>
                  <Button size="sm" variant="success" icon={CheckCircle2} onClick={() => act(m.id, true)} disabled={busy === m.id}>Onayla</Button>
                </>
              )}
            </li>
          ))}
        </ul>
      )}
    </Card>
  );
}
