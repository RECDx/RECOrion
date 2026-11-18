// İSTEK #754: Beyin AI deneme seti (Merkez). Kısa brifler canlı test şirketinde keşif → tanım → plan aşamasına kadar koşar;
// yöneticiyi RECAi gizli cevap anahtarıyla oynar. Her geliştirmeden sonra yeniden koşturulur, önceki koşuyla karşılaştırılır.
import React, { useCallback, useEffect, useState } from 'react';
import { FlaskConical, Play } from 'lucide-react';
import { api } from '../../api';
import { Badge, Button, Card, EmptyState, Modal } from '../../ui/components';
import { confirmDialog, toast } from '../../ui/feedback';
import '../projects/projects.css';

const PARTS = [['discovery', 'Keşif'], ['charter', 'Tanım'], ['plan', 'Plan yapısı'], ['verification', 'Doğrulama']];
const STATUS = { RUNNING: ['info', 'Sürüyor'], DONE: ['success', 'Tamamlandı'], FAILED: ['danger', 'Kaldı'] };
const fmt = (d) => (d ? new Date(d).toLocaleString('tr-TR', { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' }) : '—');
const tone = (v) => (v >= 75 ? 'success' : v >= 55 ? 'warning' : 'danger');
const Delta = ({ v }) => (v == null ? null : <small className="pj-hint"> ({v > 0 ? '+' : ''}{v})</small>);

function CaseResult({ r, delta, weights }) {
  const [open, setOpen] = useState(false);
  const s = r.scores;
  const d = r.details || {};
  return (
    <li>
      <span>
        <strong>{r.title}</strong> <small className="pj-hint">{r.sector}</small><br />
        {s ? (
          <>
            <Badge tone={tone(s.total)}>{s.total} / 100</Badge><Delta v={delta?.total} />{' '}
            {PARTS.map(([k, l]) => <small key={k} className="pj-hint"> · {l} {s[k]}/{weights[k]}<Delta v={delta?.[k]} /></small>)}
            <br /><small className="pj-hint">{r.rounds} keşif turu · {d.steps} adım · {r.seconds} sn · {r.credits} kredi</small>
          </>
        ) : r.error ? <Badge tone="danger">Kaldı: {r.error}</Badge> : null}
        {open && s && (
          <div className="pj-steps">
            {d.judge_note && <small className="pj-hint">Değerlendirici: {d.judge_note}</small>}
            {(d.missed || []).length > 0 && <div><strong>Keşfin kaçırdığı</strong>
              <ul className="pj-list">{d.missed.map((m) => <li key={m}><span>{m}</span></li>)}</ul></div>}
            <small className="pj-hint">
              Plan denetimi: {Object.entries(d.plan_checks || {}).map(([k, v]) => `${{ ui_step: 'arayüz tasarımı adımı', acceptance_step: 'kabul testi adımı', human_step: 'insan adımı', not_layered: 'katmana göre değil' }[k] || k} ${v ? '✓' : '✗'}`).join(' · ')}
              {' '}· somut doğrulamalı adım {d.verified_steps}/{d.steps} · planda karşılanan anahtar maddesi {(d.in_plan || []).length}
            </small>
            <div><strong>Plan adımları</strong><ul className="pj-list">{(d.step_titles || []).map((t, i) => <li key={`${i}-${t}`}><span>{t}</span></li>)}</ul></div>
          </div>
        )}
      </span>
      {s && <Button size="sm" variant="ghost" onClick={() => setOpen(!open)}>{open ? 'Gizle' : 'Ayrıntı'}</Button>}
    </li>
  );
}

export default function BrainBench() {
  const [meta, setMeta] = useState(null);
  const [runs, setRuns] = useState(null);
  const [showCases, setShowCases] = useState(false);
  const [busy, setBusy] = useState(false);
  const load = useCallback(() => {
    api.getBrainBenchRuns().then(setRuns).catch((e) => toast.error(e.message));
  }, []);
  useEffect(() => {
    api.getBrainBenchCases().then(setMeta).catch((e) => toast.error(e.message));
    load();
  }, [load]);
  const running = (runs || []).some((r) => r.status === 'RUNNING');
  useEffect(() => {
    if (!running) return undefined;
    const t = setInterval(load, 15000);
    return () => clearInterval(t);
  }, [running, load]);

  const start = async () => {
    if (!(await confirmDialog({ message: `${meta?.cases?.length || 8} brif canlı test şirketinde keşif, tanım ve plan aşamasına kadar koşturulacak (yaklaşık 30–60 dk, birkaç yüz kredi). Başlatılsın mı?` }))) return;
    setBusy(true);
    try {
      await api.startBrainBench({});
      toast.success('Deneme seti başladı; sonuçlar brif brif gelir.');
      load();
    } catch (e) { toast.error(e.message); } finally { setBusy(false); }
  };

  return (
    <Card title="Beyin deneme seti"
      subtitle="Farklı sektörlerden kısa brifler canlı test şirketinde keşif → tanım belgesi → plan aşamasına kadar koşturulur. Yöneticiyi RECAi gizli cevap anahtarıyla oynar; Beyin AI'nın eksikleri sorup sormadığı ve planın kalitesi puanlanır. Her geliştirmeden sonra yeniden koşturup önceki koşuyla karşılaştırın."
      actions={<>
        <Button size="sm" variant="secondary" onClick={() => setShowCases(true)}>Brifler ve ölçüt</Button>
        <Button size="sm" icon={Play} disabled={running || busy || !meta} onClick={start}>{running ? 'Koşu sürüyor…' : 'Seti koştur'}</Button>
      </>}>
      {!runs ? <p className="pj-hint">Yükleniyor…</p> : !runs.length ? (
        <EmptyState icon={FlaskConical} title="Henüz koşu yok" description="İlk koşu, sonraki geliştirmeler için karşılaştırma tabanı olur." />
      ) : (
        <div className="pj-steps">
          {runs.map((run, i) => (
            <details key={run.id} open={i === 0}>
              <summary>
                <Badge tone={STATUS[run.status][0]}>{STATUS[run.status][1]}</Badge>{' '}
                <strong>{run.total != null ? `${run.total} / 100` : '—'}</strong>{' '}
                <small className="pj-hint">{fmt(run.started_at)}{run.label ? ` · ${run.label}` : ''} · {run.results.length}/{run.case_codes.length} brif
                  {run.previous_id ? ' · önceki koşuyla karşılaştırmalı' : ''}</small>
              </summary>
              {run.error && <p className="pj-hint">{run.error}</p>}
              <ul className="pj-list" aria-label="Brif sonuçları">
                {run.results.map((r) => <CaseResult key={r.code} r={r} delta={run.delta?.[r.code]} weights={meta?.weights || {}} />)}
              </ul>
            </details>
          ))}
        </div>
      )}
      <Modal open={showCases} onClose={() => setShowCases(false)} title="Brifler ve puanlama ölçütü" size="lg">
        {meta && (
          <div className="pj-steps">
            <small className="pj-hint">
              Puan (100): Keşif {meta.weights.discovery} — cevap anahtarı maddelerinin soruyla ortaya çıkan ya da belgeye giren oranı ·
              Tanım {meta.weights.charter} — belgenin bölümleri ve olgunluk · Plan yapısı {meta.weights.plan} — teslimat/akış bazlı kurgu,
              yazılımda arayüz tasarımı ve kabul testi adımı, insan adımı · Doğrulama {meta.weights.verification} — adımların somut
              doğrulaması ve anahtar maddelerinin planda karşılanması. Keşif en fazla {meta.rounds} tur.
            </small>
            <ul className="pj-list">
              {meta.cases.map((c) => (
                <li key={c.code}><span><strong>{c.title}</strong> <Badge tone="neutral">{c.sector}</Badge><br />
                  Brif: “{c.brief}”<br />
                  <small className="pj-hint">Gizli cevap anahtarı ({c.key.length}): {c.key.map((k) => k.fact).join(' · ')}</small></span></li>
              ))}
            </ul>
          </div>
        )}
      </Modal>
    </Card>
  );
}
