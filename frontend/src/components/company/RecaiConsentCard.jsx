import React, { useEffect, useState } from 'react';
import { api } from '../../api';
import { Card } from '../../ui/components';
import { confirmDialog, toast } from '../../ui/feedback';

/** İSTEK #743: şirket kartında "RECAi model geliştirmeye katkı" izni (varsayılan açık; şirket yöneticisi kapatabilir). */
export default function RecaiConsentCard({ tenantId }) {
  const [c, setC] = useState(null);
  const [busy, setBusy] = useState(false);
  useEffect(() => { api.getRecaiConsent(tenantId).then(setC).catch((e) => toast.error(e.message)); }, [tenantId]);

  const toggle = async (next) => {
    if (!next && !(await confirmDialog({ message: 'İzni kapatırsanız verileriniz sonraki RECAi eğitim setlerine girmez. Daha önce eğitilmiş bir modelden geri çıkarılamaz. Şirketinizin hafızası ve AI personelinizin öğrenmesi etkilenmez. Devam edilsin mi?' }))) return;
    setBusy(true);
    try { setC(await api.setRecaiConsent(tenantId, { consent: next })); toast.success(next ? 'İzin açıldı.' : 'İzin kapatıldı.'); }
    catch (e) { toast.error(e.message); } finally { setBusy(false); }
  };

  return (
    <Card title="RECAi model geliştirmeye katkı" subtitle="RECDx'in yerli ve milli yapay zekâ modeli RECAi'nin gelişimine maskeli verilerle katkı.">
      {!c ? <p className="pj-hint">Yükleniyor…</p> : (
        <>
          <label style={{ display: 'flex', gap: 8, alignItems: 'center', fontWeight: 600 }}>
            <input type="checkbox" checked={c.consent} disabled={busy} onChange={(e) => toggle(e.target.checked)} />
            Maskeli verilerimiz RECAi'nin geliştirilmesinde kullanılabilir
          </label>
          <p className="pj-hint" style={{ marginTop: 8 }}>{c.text}</p>
          {c.changed_at && <p className="pj-hint">Son değişiklik: {new Date(c.changed_at).toLocaleString('tr-TR')}{c.changed_by ? ` · ${c.changed_by}` : ''}</p>}
        </>
      )}
    </Card>
  );
}
