import React, { useEffect, useState } from 'react';
import { api } from '../../api';
import { Button, Card } from '../../ui/components';
import { toast } from '../../ui/feedback';

/**
 * İSTEK #744: Merkez toplu istatistik gizliliği. k: bir satırın gösterilmesi için gereken en az şirket sayısı (k-anonimlik);
 * baskınlık: tek şirketin payı bu yüzdeyi geçerse satır gizlenir. Merkez Beyin AI ve Merkez raporları bu ayarı kullanır.
 */
export default function PrivacySettingsCard() {
  const [v, setV] = useState(null);
  const [busy, setBusy] = useState(false);
  useEffect(() => { api.getPrivacySettings().then(setV).catch((e) => toast.error(e.message)); }, []);
  const save = async () => {
    setBusy(true);
    try { setV({ ...v, ...(await api.setPrivacySettings({ k_min: Number(v.k_min), dominance_pct: Number(v.dominance_pct) })) }); toast.success('Gizlilik ayarı kaydedildi.'); }
    catch (e) { toast.error(e.message); } finally { setBusy(false); }
  };
  return (
    <Card title="Toplu istatistik gizliliği" subtitle="Merkez Beyin AI ve Merkez raporlarında şirketler arası istatistiğin hangi koşulda gösterileceği (KVKK)."
      actions={<Button onClick={save} disabled={busy || !v}>Kaydet</Button>}>
      {!v ? <p className="pj-hint">Yükleniyor…</p> : (
        <>
          <div className="pj-form">
            <div className="pj-field"><label htmlFor="pv-k">En az şirket sayısı (k)</label>
              <input id="pv-k" className="ui-input" type="number" min={3} max={50} value={v.k_min} onChange={(e) => setV({ ...v, k_min: e.target.value })} /></div>
            <div className="pj-field"><label htmlFor="pv-d">Tek şirket payı en çok (%)</label>
              <input id="pv-d" className="ui-input" type="number" min={30} max={100} value={v.dominance_pct} onChange={(e) => setV({ ...v, dominance_pct: e.target.value })} /></div>
          </div>
          <p className="pj-hint" style={{ marginTop: 8 }}>k büyüdükçe gizlilik artar ama daha az satır görünür (az müşteriyle k=10 çoğu satırı boşaltır); k=3'ün altı şirket tahminine açıktır.
            Baskınlık kuralı, 5 şirket olsa bile verinin çoğu tek şirketten geliyorsa satırı gizler. Önerilen: başlangıçta k=5 ve %60; müşteri sayısı arttıkça k=10.</p>
        </>
      )}
    </Card>
  );
}
