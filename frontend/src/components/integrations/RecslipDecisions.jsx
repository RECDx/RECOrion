import React, { useState } from 'react';
import { api } from '../../api';
import { Badge, Button } from '../../ui/components';
import { promptDialog, toast } from '../../ui/feedback';

const money = (v, c) => `${Number(v || 0).toLocaleString('tr-TR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} ${c || 'TRY'}`;

/** RECSlip.App v2 (ADIM 14.3): AI personelin kriter dışı bulduğu fiş; karar kişinin kendi Odoo anahtarıyla verilir. */
export function RecslipDecisionCard({ d, onChange }) {
  const [busy, setBusy] = useState(false);
  const [apply, setApply] = useState(true);
  const decide = async (approve) => {
    let note = '';
    if (!approve) {
      note = await promptDialog({ title: 'Fişi reddet', message: 'Red gerekçesi (çalışana ve RECSlip geçmişine yazılır):' });
      if (note === null) return;
      if (!note.trim()) { toast.error('Red gerekçesi yazın.'); return; }
    }
    setBusy(true);
    try {
      await api.decideRecslip(d.id, { approve, note, apply_corrections: apply });
      toast.success(approve ? 'Fiş onaylandı (RECSlip).' : 'Fiş reddedildi (RECSlip).');
      onChange?.();
    } catch (e) { toast.error(e.message); } finally { setBusy(false); }
  };
  return (
    <li aria-label={`RECSlip fişi: ${d.expense_name}`} data-recslip-decision={d.id}>
      <span>
        <strong>{d.expense_name}</strong> · {money(d.amount, d.currency)} · {d.employee_name || '—'} <Badge tone="info">{d.role_label} onayı</Badge><br />
        <small className="pj-hint">{d.agent_name ? `${d.agent_name}: ` : 'RECAi: '}{(d.reasons || []).join(' ')}</small>
        {d.corrections?.length > 0 && (
          <>
            <br /><small className="pj-hint">Önerilen hesap düzeltmeleri:</small>
            <ul className="pj-hint" aria-label="Önerilen hesap düzeltmeleri" style={{ margin: '2px 0 0 16px' }}>
              {d.corrections.map((c) => (
                <li key={c.line_id}><small>'{c.line}': {c.old || '—'} → <strong>{c.new}</strong> (güven {Math.round(c.confidence)}) {c.reason}</small></li>
              ))}
            </ul>
            <label style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
              <input type="checkbox" checked={apply} onChange={(e) => setApply(e.target.checked)} /> <small>Onaylarken düzeltmeleri uygula</small>
            </label>
          </>
        )}
      </span>
      <Button size="sm" disabled={busy} onClick={() => decide(true)}>Onayla</Button>
      <Button size="sm" variant="secondary" disabled={busy} onClick={() => decide(false)}>Reddet</Button>
    </li>
  );
}
