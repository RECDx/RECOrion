import React, { useState } from 'react';
import { api } from '../../api';
import { toast } from '../../ui/feedback';

const MODES = [['PLAN', 'Paket ayarı'], ['ON', 'Açık (istisna)'], ['OFF', 'Kapalı (istisna)']];
const modeOf = (v) => (v === true ? 'ON' : v === false ? 'OFF' : 'PLAN');

/**
 * Merkez › Şirket detayı (#636): şirkete özel ünvan tanımlama izni paketten bağımsız açılır/kapatılır ya da pakete bırakılır.
 * Seçim hemen kaydedilir (şirket formunun Kaydet düğmesinden bağımsız); istenince "Paket ayarı"na dönülerek geri alınır.
 */
export default function TenantCustomTitles({ tenant, plan, onChanged }) {
  const [mode, setMode] = useState(modeOf(tenant.custom_titles_override));
  const [busy, setBusy] = useState(false);
  const planOn = !!plan?.can_create_custom_titles;
  const change = async (next) => {
    setBusy(true);
    try {
      const r = await api.setTenantCustomTitles(tenant.id, next);
      setMode(next);
      onChanged?.(r);
      toast.success(`Şirkete özel ünvan: ${MODES.find(([k]) => k === next)[1]} (geçerli: ${r.effective ? 'açık' : 'kapalı'}).`);
    } catch (e) { toast.error(e.message); } finally { setBusy(false); }
  };
  return (
    <div>
      <label htmlFor="tenant-custom-titles" style={{ display: 'block', fontSize: '0.7rem', fontWeight: 700, marginBottom: 3 }}>Şirkete özel ünvan</label>
      <select id="tenant-custom-titles" className="super-admin-select" value={mode} disabled={busy} onChange={(e) => change(e.target.value)}>
        {MODES.map(([k, l]) => <option key={k} value={k}>{k === 'PLAN' ? `${l} (${planOn ? 'açık' : 'kapalı'})` : l}</option>)}
      </select>
    </div>
  );
}
