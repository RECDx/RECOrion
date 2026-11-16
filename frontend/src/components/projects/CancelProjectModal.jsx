import React, { useEffect, useState } from 'react';
import { api } from '../../api';
import { Button, Modal } from '../../ui/components';
import { toast } from '../../ui/feedback';

const fmtTl = (v) => (v == null ? '—' : `${Number(v).toLocaleString('tr-TR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} ₺`);
const fmtCr = (v) => Number(v || 0).toLocaleString('tr-TR', { maximumFractionDigits: 2 });

/**
 * #745: proje/Case iptali. Harcanan, teslimata dönüşen ve kayıp maliyet gösterilir; gerekçe ve "geri alınamaz" onayı
 * zorunludur. Kayıt akış geçmişine ve "İptal edilen işler" raporuna düşer.
 */
export default function CancelProjectModal({ project, initialReason = '', onClose, onConfirm }) {
  const [preview, setPreview] = useState(null);
  const [reason, setReason] = useState(initialReason);
  const [agree, setAgree] = useState(false);
  const [busy, setBusy] = useState(false);
  const noun = project.kind === 'CASE' ? "Case'i" : 'Projeyi';

  useEffect(() => {
    api.getProjectCancelPreview(project.id).then(setPreview).catch((e) => { toast.error(e.message); onClose(); });
  }, [project.id, onClose]);

  const confirm = async () => {
    setBusy(true);
    try { await onConfirm(reason.trim()); } finally { setBusy(false); }
  };
  const ready = reason.trim().length >= 5 && agree && !busy;

  return (
    <Modal open onClose={onClose} title={`${noun} iptal et: ${project.name}`}
      footer={<><Button variant="ghost" onClick={onClose}>Vazgeç</Button><Button variant="danger" onClick={confirm} disabled={!ready || !preview}>İptal et</Button></>}>
      {!preview ? <p className="pj-hint">Maliyet hesaplanıyor…</p> : (
        <div className="pj-steps">
          <table className="ui-table" aria-label="İptal maliyet özeti">
            <tbody>
              <tr><th scope="row">Harcanan toplam (AI)</th><td>{fmtCr(preview.spent.credits)} kredi</td><td>{fmtTl(preview.spent.try)}</td></tr>
              <tr><th scope="row">Teslimata dönüşen</th><td>{fmtCr(preview.delivered.credits)} kredi</td><td>{fmtTl(preview.delivered.try)}</td></tr>
              <tr><th scope="row"><strong>Kayıp maliyet</strong></th><td><strong>{fmtCr(preview.lost.credits)} kredi</strong></td><td><strong>{fmtTl(preview.lost.try)}</strong></td></tr>
            </tbody>
          </table>
          <p className="pj-hint" style={{ margin: 0 }}>
            Kayıp maliyet: onaylanmamış, iptal edilen ya da yarım kalan adımların ve planlamanın AI maliyeti. Personel ve diğer giderler
            ({fmtTl(preview.other_costs_try)}) ayrıca Maliyet sekmesinde.
          </p>
          {preview.done_steps.length > 0 && (
            <p className="pj-hint" style={{ margin: 0 }}>Saklanacak tamamlanmış teslimatlar: {preview.done_steps.map((s) => s.title).join(', ')}
              {preview.has_repo ? ' (kod deposu açık kalır)' : ''}.</p>
          )}
          {preview.open_steps.length > 0 && (
            <p className="pj-hint" style={{ margin: 0 }}>İptal edilecek açık adımlar ({preview.open_steps.length}): {preview.open_steps.map((s) => s.title).join(', ')}.</p>
          )}
          <label className="pj-hint" htmlFor="cancel-reason">İptal gerekçesi (zorunlu; akış geçmişine ve iptal raporuna yazılır)</label>
          <textarea id="cancel-reason" className="ui-input" rows={4} value={reason} maxLength={4000} onChange={(e) => setReason(e.target.value)} />
          <label className="pj-hint" style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
            <input type="checkbox" checked={agree} onChange={(e) => setAgree(e.target.checked)} />
            Bu işlemin geri alınamayacağını ve kayıp maliyetin raporlanacağını anladım.
          </label>
        </div>
      )}
    </Modal>
  );
}
