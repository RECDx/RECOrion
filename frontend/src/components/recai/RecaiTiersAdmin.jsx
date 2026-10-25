import React, { useEffect, useState } from 'react';
import { api } from '../../api';
import { Badge, Button, Card } from '../../ui/components';
import { confirmDialog, toast } from '../../ui/feedback';
import './recai.css';

// Adın amacına göre seçilebilen EVREN model türü (backend ile aynı kural)
const TYPE_FOR = { VISION: 'VISION', TRANSCRIPTION: 'AUDIO', OCR: 'OCR' };

/**
 * #349 Süper Admin: RECAi adlarının arkasındaki EVREN modelleri. Müşteri yalnızca adı görür; burada model değişince
 * o adı kullanan tüm AI personeller kendiliğinden yeni modele geçer. Gerçek model adları yalnızca bu ekranda görünür.
 */
export default function RecaiTiersAdmin({ models = [] }) {
  const [tiers, setTiers] = useState([]);
  const [draft, setDraft] = useState({});
  const [saving, setSaving] = useState('');

  const load = () => api.getRecaiTiers()
    .then((rows) => { setTiers(rows); setDraft(Object.fromEntries(rows.map((t) => [t.code, { model_code: t.model_code, fallback_model_code: t.fallback_model_code || '' }]))); })
    .catch((e) => toast.error(e.message));
  useEffect(() => { load(); }, []);

  const choices = (t) => models.filter((m) => m.status === 'ACTIVE' && m.model_type === (TYPE_FOR[t.purpose] || 'CHAT'));
  const changed = (t) => draft[t.code] && (draft[t.code].model_code !== t.model_code || (draft[t.code].fallback_model_code || '') !== (t.fallback_model_code || ''));
  const set = (code, key, value) => setDraft({ ...draft, [code]: { ...draft[code], [key]: value } });

  const save = async (t) => {
    const d = draft[t.code];
    if (!(await confirmDialog({ message: `${t.name} artık ${d.model_code} ile çalışacak. Bu adı kullanan tüm müşterilerin AI personelleri hemen yeni modele geçer. Onaylıyor musunuz?` }))) return;
    setSaving(t.code);
    try {
      await api.updateRecaiTier(t.code, { model_code: d.model_code, fallback_model_code: d.fallback_model_code || null });
      toast.success(`${t.name} güncellendi.`);
      await load();
    } catch (e) {
      toast.error(e.message);
    } finally {
      setSaving('');
    }
  };

  return (
    <Card title="RECAi Adları" subtitle="Müşteri yalnızca RECAi adını görür; arkasındaki EVREN modelini buradan değiştirirsiniz. Değişiklik denetim kaydına yazılır.">
      <table className="rt-table" data-testid="recai-tiers">
        <thead><tr><th>Ad</th><th>Model</th><th>Yedek model</th><th /></tr></thead>
        <tbody>
          {tiers.map((t) => (
            <tr key={t.code}>
              <td>
                <div className="rt-name">{t.name} <Badge tone={t.kind === 'CHAT' ? 'info' : 'neutral'}>{t.kind === 'CHAT' ? 'Seçilebilir ad' : 'Yetenek'}</Badge></div>
                {t.description && <div className="rt-desc">{t.description}</div>}
              </td>
              <td>
                <select className="ui-input" aria-label={`${t.name} modeli`} value={draft[t.code]?.model_code || ''} onChange={(e) => set(t.code, 'model_code', e.target.value)}>
                  {!choices(t).some((m) => m.model_code === draft[t.code]?.model_code) && <option value={draft[t.code]?.model_code}>{draft[t.code]?.model_code}</option>}
                  {choices(t).map((m) => <option key={m.model_code} value={m.model_code}>{m.display_name} ({m.model_code})</option>)}
                </select>
              </td>
              <td>
                <select className="ui-input" aria-label={`${t.name} yedek modeli`} value={draft[t.code]?.fallback_model_code || ''} onChange={(e) => set(t.code, 'fallback_model_code', e.target.value)}>
                  <option value="">Yok</option>
                  {choices(t).map((m) => <option key={m.model_code} value={m.model_code}>{m.display_name} ({m.model_code})</option>)}
                </select>
              </td>
              <td className="rt-actions">
                <Button size="sm" disabled={!changed(t) || saving === t.code} onClick={() => save(t)}>Kaydet</Button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </Card>
  );
}
