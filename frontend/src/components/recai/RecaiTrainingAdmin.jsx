import React, { useCallback, useEffect, useState } from 'react';
import { api } from '../../api';
import { Badge, Button, Card } from '../../ui/components';
import { confirmDialog, toast } from '../../ui/feedback';

const FILES = [['sft', 'Örnek (doğru çıktı)'], ['dpo', 'Tercih çifti (yanlış → doğru)'], ['kto', 'İyi/kötü işaretli'],
  ['reward', 'Test ödülü'], ['lessons', 'Genel ders']];
const fmt = (d) => (d ? new Date(d).toLocaleString('tr-TR', { dateStyle: 'short', timeStyle: 'short' }) : '');

/**
 * İSTEK #743: Merkez › EVREN Modelleri › RECAi eğitim verisi. Yalnız SAYILAR görünür (KVKK: içerik Merkez'de gösterilmez).
 * İzinli şirketlerin maskeli kayıtlarından sürümlü veri seti üretilir; EVREN'e teslim API'si görüşmeden sonra eklenecek.
 */
export default function RecaiTrainingAdmin() {
  const [data, setData] = useState(null);
  const [busy, setBusy] = useState(false);
  const load = useCallback(() => api.getRecaiTrainingSummary().then(setData).catch((e) => toast.error(e.message)), []);
  useEffect(() => { load(); }, [load]);

  const build = async () => {
    if (!(await confirmDialog({ message: 'İzinli şirketlerin kayıtlarından maskeli yeni bir veri seti sürümü üretilsin mi? (Gerçek ad, kimlik, IBAN, tutar gibi bilgiler geri çevrilemez biçimde değiştirilir.)' }))) return;
    setBusy(true);
    try { const d = await api.buildRecaiDataset({}); toast.success(`Veri seti v${d.version} üretildi.`); load(); }
    catch (e) { toast.error(e.message); } finally { setBusy(false); }
  };

  const e = data?.eligible || {};
  return (
    <Card title="RECAi eğitim verisi" subtitle="Yerli ve milli RECAi modeli için, izin veren şirketlerin maskeli öğrenme kayıtlarından üretilen veri setleri. Burada yalnız sayılar görünür."
      actions={<Button onClick={build} disabled={busy || !data}>{busy ? 'Üretiliyor…' : 'Yeni veri seti üret'}</Button>}>
      {!data ? <p className="pj-hint">Yükleniyor…</p> : (
        <>
          <div className="pj-meta" style={{ flexWrap: 'wrap', gap: 12 }} aria-label="Uygun veri">
            <span>İzin veren şirket: <strong>{e.tenants_consenting}</strong></span>
            <span>İzni kapatan: <strong>{e.tenants_declined}</strong></span>
            <span>Kayıt: <strong>{e.records}</strong></span>
            <span>Doğru örnek: <strong>{e.sft}</strong></span>
            <span>AI hatası (olumsuz): <strong>{e.negatives}</strong></span>
            <span>Tercih çifti: <strong>{e.pairs}</strong></span>
            <span>Test sonucu: <strong>{e.tests}</strong></span>
          </div>
          <p className="pj-hint" style={{ marginTop: 8 }}>{data.delivery}</p>
          {data.datasets.length > 0 && (
            <div className="ui-table-scroll" style={{ marginTop: 10 }}>
              <table className="ui-table">
                <thead><tr><th>Sürüm</th><th>Tarih</th><th>Şirket</th>{FILES.map(([k, l]) => <th key={k}>{l}</th>)}<th>Teslim</th></tr></thead>
                <tbody>{data.datasets.map((d) => (
                  <tr key={d.id}>
                    <td data-label="Sürüm">v{d.version}</td>
                    <td data-label="Tarih">{fmt(d.created_at)}</td>
                    <td data-label="Şirket">{d.tenant_count}</td>
                    {FILES.map(([k, l]) => <td key={k} data-label={l}>{d.counts?.[k] ?? 0}</td>)}
                    <td data-label="Teslim">{d.delivered_at ? fmt(d.delivered_at) : <Badge tone="neutral">Bekliyor</Badge>}</td>
                  </tr>
                ))}</tbody>
              </table>
            </div>
          )}
        </>
      )}
    </Card>
  );
}
