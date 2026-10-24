import React, { useCallback, useEffect, useState } from 'react';
import { FlaskConical, Route } from 'lucide-react';
import { api } from '../../api';
import { Badge, Button, Card, EmptyState } from '../../ui/components';
import { confirmDialog, promptDialog, toast } from '../../ui/feedback';
import '../projects/projects.css';

const pct = (v) => (v == null ? '—' : `%${Math.round(v * 100)}`);
const sec = (ms) => (ms == null ? '—' : `${(ms / 1000).toFixed(1)} sn`);
const fmt = (d) => (d ? new Date(d).toLocaleString('tr-TR', { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' }) : '');
const tone = (q) => (q == null ? 'neutral' : q >= 0.85 ? 'success' : q >= 0.7 ? 'info' : q >= 0.5 ? 'warning' : 'danger');

/** Süper Admin › Model Yönlendirici (ADIM 11.4): kalite test seti, iş türü başına öneri, onaylı geçiş ve iz. */
export default function ModelRouterPanel() {
  const [ov, setOv] = useState(null);
  const [run, setRun] = useState(null);
  const [picked, setPicked] = useState(null);
  const load = useCallback(async () => {
    try {
      const o = await api.getModelRouter();
      setOv(o);
      setPicked((p) => p || new Set(o.models.map((m) => m.model_code)));
      if (o.recommendation_run_id) setRun(await api.getQualityRun(o.recommendation_run_id));
    } catch (e) { toast.error(e.message); }
  }, []);
  useEffect(() => { load(); }, [load]);
  const running = ov?.last_run?.status === 'RUNNING';
  useEffect(() => {
    if (!running) return undefined;
    const t = setInterval(load, 5000);
    return () => clearInterval(t);
  }, [running, load]);

  if (!ov) return <p className="pj-hint">Yükleniyor…</p>;
  const start = async () => {
    if (!(await confirmDialog({ message: `Kalite testi ${picked.size} modelde çalıştırılsın mı? (${Object.values(ov.suite.cases).reduce((a, b) => a + b, 0)} vaka × ${picked.size} model; EVREN kredisi harcanır)` }))) return;
    try { await api.startQualityRun([...picked]); toast.success('Kalite testi başladı.'); load(); } catch (e) { toast.error(e.message); }
  };
  const approve = async (tt, model) => {
    const cand = ov.recommendation?.[tt]?.candidates.find((c) => c.model_code === model);
    let note = null;
    if (cand && !cand.eligible) {
      note = await promptDialog({ title: 'Eşik altı model', message: 'Bu model kalite eşiğinin altında. Yine de onaylamak için gerekçe yazın:' });
      if (!note) return;
    } else if (!(await confirmDialog({ message: `${ov.task_types[tt]} işleri için platform varsayılanı '${model}' olsun mu? AI personelin seçili modeli olan şirketler etkilenmez.` }))) return;
    try { await api.setModelRoute(tt, model, ov.recommendation_run_id, note); toast.success('Yönlendirme onaylandı.'); load(); } catch (e) { toast.error(e.message); }
  };
  const clear = async (tt) => {
    if (!(await confirmDialog({ message: `${ov.task_types[tt]} yönlendirmesi kaldırılsın mı? Platform varsayılan modeline dönülür.` }))) return;
    try { await api.setModelRoute(tt, null, null, null); load(); } catch (e) { toast.error(e.message); }
  };

  const types = Object.keys(ov.task_types);
  const matrix = {};
  (run?.results || []).forEach((r) => {
    const k = `${r.model_code}|${r.task_type}`;
    (matrix[k] = matrix[k] || []).push(r.score);
  });
  const runModels = run?.models || [];

  return (
    <div className="pj-steps">
      <Card title="Akıllı model yönlendirici" subtitle={`İş türüne göre platform varsayılan modeli. Öneri: kalite ×${ov.weights.quality} + hız ×${ov.weights.speed} + güvenilirlik ×${ov.weights.reliability}; kalite %${Math.round(ov.quality_min * 100)} altı önerilmez. Onayınız olmadan hiçbir şey değişmez.`}
        actions={<Route size={18} />}>
        <div className="ui-table-scroll">
          <table className="ui-table" aria-label="İş türü yönlendirmeleri">
            <thead><tr><th>İş türü</th><th>Şu an</th><th>Öneri (son test)</th><th>Puan</th><th /></tr></thead>
            <tbody>{types.map((tt) => {
              const rec = ov.recommendation?.[tt];
              const best = rec?.candidates?.find((c) => c.model_code === rec.recommended);
              return (
                <tr key={tt}>
                  <td data-label="İş türü"><strong>{ov.task_types[tt]}</strong></td>
                  <td data-label="Şu an">{ov.routes[tt] ? <code>{ov.routes[tt]}</code> : <span className="pj-hint">platform varsayılanı</span>}</td>
                  <td data-label="Öneri">{rec?.recommended ? <code>{rec.recommended}</code> : <span className="pj-hint">{ov.recommendation ? 'eşiği geçen model yok' : 'test yok'}</span>}</td>
                  <td data-label="Puan">{best ? <span className="pj-hint">kalite {pct(best.quality)} · hız {pct(best.speed)} · güvenilirlik {pct(best.reliability)} ({best.reliability_source})</span> : '—'}</td>
                  <td data-label="">
                    <div className="pj-actions">
                      {rec?.recommended && rec.recommended !== ov.routes[tt] && <Button size="sm" onClick={() => approve(tt, rec.recommended)}>Önerileni onayla</Button>}
                      {ov.routes[tt] && <Button size="sm" variant="ghost" onClick={() => clear(tt)}>Kaldır</Button>}
                    </div>
                  </td>
                </tr>
              );
            })}</tbody>
          </table>
        </div>
      </Card>

      <Card title="Kalite test seti" subtitle={`Sürüm ${ov.suite.version} · iş türü başına ${Object.values(ov.suite.cases)[0]} vaka · çıktılar kuralla puanlanır (JSON alanları, kod sözdizimi, kelime/madde sınırı, zorunlu ifadeler); kod çalıştırılmaz.`}
        actions={<FlaskConical size={18} />}>
        <div className="pj-actions" style={{ marginBottom: 10 }}>
          {ov.models.map((m) => (
            <label key={m.model_code} className="pj-hint" style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
              <input type="checkbox" disabled={running} checked={picked?.has(m.model_code) || false}
                onChange={(e) => setPicked((p) => { const n = new Set(p); if (e.target.checked) n.add(m.model_code); else n.delete(m.model_code); return n; })} />
              {m.model_code}
            </label>
          ))}
        </div>
        <div className="pj-actions" style={{ alignItems: 'center' }}>
          <Button icon={FlaskConical} disabled={running || !picked?.size} onClick={start}>{running ? 'Test sürüyor…' : 'Kalite testini çalıştır'}</Button>
          {ov.last_run && <span className="pj-hint" role="status">Son koşu: {fmt(ov.last_run.started_at)} · {ov.last_run.status === 'RUNNING' ? ov.last_run.progress : ov.last_run.status === 'DONE' ? 'tamamlandı' : `hata: ${ov.last_run.error}`}</span>}
        </div>
        {run && runModels.length > 0 && (
          <div className="ui-table-scroll" style={{ marginTop: 12 }}>
            <table className="ui-table" aria-label="Kalite matrisi">
              <thead><tr><th>Model</th>{types.map((tt) => <th key={tt}>{ov.task_types[tt]}</th>)}</tr></thead>
              <tbody>{runModels.map((m) => (
                <tr key={m}>
                  <td data-label="Model"><code>{m}</code></td>
                  {types.map((tt) => {
                    const s = matrix[`${m}|${tt}`];
                    const q = s ? s.reduce((a, b) => a + b, 0) / s.length : null;
                    return <td key={tt} data-label={ov.task_types[tt]}><Badge tone={tone(q)}>{pct(q)}</Badge></td>;
                  })}
                </tr>
              ))}</tbody>
            </table>
          </div>
        )}
      </Card>

      <Card title="Canlı ölçümler (son 7 gün)" subtitle="Gerçek kullanım: çağrı sayısı, hata oranı ve ortanca yanıt süresi (kalite testi çağrıları hariç).">
        {Object.keys(ov.live).length === 0 ? <EmptyState icon={Route} title="Ölçüm yok" description="Son 7 günde sohbet modeli çağrısı yapılmamış." /> : (
          <div className="ui-table-scroll">
            <table className="ui-table" aria-label="Canlı ölçümler">
              <thead><tr><th>Model</th><th>Çağrı</th><th>Hata oranı</th><th>Ortanca süre</th></tr></thead>
              <tbody>{Object.entries(ov.live).sort((a, b) => b[1].calls - a[1].calls).map(([m, v]) => (
                <tr key={m}><td data-label="Model"><code>{m}</code></td><td data-label="Çağrı">{v.calls}</td>
                  <td data-label="Hata oranı"><Badge tone={v.error_rate > 0.1 ? 'danger' : v.error_rate > 0.03 ? 'warning' : 'success'}>{pct(v.error_rate)}</Badge></td>
                  <td data-label="Ortanca süre">{sec(v.p50_ms)}</td></tr>
              ))}</tbody>
            </table>
          </div>
        )}
      </Card>

      {ov.decisions.length > 0 && (
        <Card title="Karar geçmişi" subtitle="Onaylanan ve kaldırılan yönlendirmeler.">
          <ul className="pj-list">
            {ov.decisions.map((d, i) => (
              <li key={i}><span><strong>{ov.task_types[d.task_type] || d.task_type}</strong>: {d.previous_model_code || 'varsayılan'} → {d.model_code || 'varsayılan'}
                <br /><small className="pj-hint">{fmt(d.decided_at)}{d.note ? ` · ${d.note}` : ''}</small></span></li>
            ))}
          </ul>
        </Card>
      )}
    </div>
  );
}
