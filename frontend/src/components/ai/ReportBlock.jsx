import React, { useEffect, useMemo, useState } from 'react';
import { Download } from 'lucide-react';
import { Button } from '../../ui/components';
import { BarList, ColumnChart, compact } from '../../ui/charts';

const BLOCK = /```rapor\s*(\{[\s\S]*?\})\s*```/;

/** Beyin yanıtındaki rapor isteğini ayırır: { text (blok çıkarılmış), spec | null } */
export function splitReport(content) {
  const m = BLOCK.exec(content || '');
  if (!m) return { text: content, spec: null };
  let spec = null;
  try { spec = JSON.parse(m[1]); } catch { spec = null; }
  return { text: (content.slice(0, m.index) + content.slice(m.index + m[0].length)).trim(), spec };
}

const fmt = (v) => compact(v);

function toCsv(r) {
  const esc = (s) => `"${String(s ?? '').replace(/"/g, '""')}"`;
  const head = [...r.dim_labels, r.measure_label].map(esc).join(';');
  const body = r.rows.map((x) => [...x.keys, String(x.value).replace('.', ',')].map(esc).join(';'));
  return `﻿${[head, ...body].join('\r\n')}`;
}

function download(r) {
  const blob = new Blob([toCsv(r)], { type: 'text/csv;charset=utf-8' });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = `${(r.title || 'rapor').replace(/[^\wçğıöşüÇĞİÖŞÜ -]/g, '').slice(0, 60) || 'rapor'}.csv`;
  a.click();
  setTimeout(() => URL.revokeObjectURL(a.href), 1000);
}

function Pivot({ r }) {
  const { rowsK, colsK, cell, rowTot, colTot, total } = useMemo(() => {
    const rk = [], ck = [], c = {}, rt = {}, ct = {};
    let t = 0;
    r.rows.forEach(({ keys: [a, b], value }) => {
      if (!rk.includes(a)) rk.push(a);
      if (!ck.includes(b)) ck.push(b);
      c[`${a}\u0000${b}`] = value;
      rt[a] = (rt[a] || 0) + value; ct[b] = (ct[b] || 0) + value; t += value;
    });
    return { rowsK: rk, colsK: ck, cell: c, rowTot: rt, colTot: ct, total: t };
  }, [r]);
  const avg = r.agg === 'avg';
  return (
    <div className="ui-table-scroll">
      <table className="ui-table">
        <caption className="pj-hint" style={{ textAlign: 'left' }}>{r.dim_labels[0]} × {r.dim_labels[1]} · {r.measure_label}</caption>
        <thead><tr><th>{r.dim_labels[0]}</th>{colsK.map((c) => <th key={c}>{c}</th>)}{!avg && <th>Toplam</th>}</tr></thead>
        <tbody>
          {rowsK.map((a) => (
            <tr key={a}><td data-label={r.dim_labels[0]}>{a}</td>
              {colsK.map((b) => <td key={b} data-label={b}>{cell[`${a}\u0000${b}`] != null ? fmt(cell[`${a}\u0000${b}`]) : '—'}</td>)}
              {!avg && <td data-label="Toplam"><strong>{fmt(rowTot[a])}</strong></td>}</tr>
          ))}
          {!avg && <tr><td><strong>Toplam</strong></td>{colsK.map((b) => <td key={b}><strong>{fmt(colTot[b])}</strong></td>)}<td><strong>{fmt(total)}</strong></td></tr>}
        </tbody>
      </table>
    </div>
  );
}

/** İSTEK #744: Beyin AI rapor bloğu — rapor her görüntülemede kullanıcının yetkisiyle sunucuda çalıştırılır (sayılar uydurulamaz). */
export default function ReportBlock({ spec, run }) {
  const [r, setR] = useState(null);
  const [err, setErr] = useState(null);
  const [view, setView] = useState(null);
  const key = JSON.stringify(spec);
  useEffect(() => {
    let alive = true;
    setR(null); setErr(null);
    run(spec).then((x) => { if (alive) { setR(x); setView(x.chart); } }).catch((e) => alive && setErr(e.message));
    return () => { alive = false; };
  }, [key]); // eslint-disable-line react-hooks/exhaustive-deps

  if (err) return <p className="pj-hint" role="alert">Rapor çalıştırılamadı: {err}</p>;
  if (!r) return <p className="pj-hint">Rapor hazırlanıyor…</p>;
  const two = r.dims.length === 2;
  const data = r.rows.map((x) => ({ key: x.keys.join(' · '), label: x.keys.join(' · '), short: x.keys[0], value: x.value }));
  const views = two ? [['pivot', 'Pivot'], ['table', 'Tablo']] : [['bar', 'Çubuk'], ['column', 'Sütun'], ['table', 'Tablo']];
  return (
    <div className="ai-report" aria-label={r.title}>
      <div className="pj-meta" style={{ justifyContent: 'space-between', flexWrap: 'wrap', gap: 8 }}>
        <strong>{r.title}</strong>
        <span style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
          <span className="ui-segmented" role="tablist">
            {views.map(([k, l]) => <button key={k} type="button" className={`ui-segmented-item ${view === k ? 'active' : ''}`} onClick={() => setView(k)}>{l}</button>)}
          </span>
          <Button size="sm" variant="ghost" icon={Download} onClick={() => download(r)} aria-label="CSV indir (Excel)">Excel/CSV</Button>
        </span>
      </div>
      {(r.date_from || r.date_to || Object.keys(r.filters || {}).length > 0) && (
        <p className="pj-hint">{[r.date_from && `${r.date_from} → ${r.date_to || 'bugün'}`, ...Object.entries(r.filters || {}).map(([k, v]) => `${k}: ${v}`)].filter(Boolean).join(' · ')}</p>
      )}
      {r.rows.length === 0 ? <p className="pj-hint">Bu ölçütlere uyan veri yok.</p>
        : view === 'pivot' && two ? <Pivot r={r} />
        : view === 'column' ? <ColumnChart data={data} caption={r.title} />
        : view === 'bar' ? <BarList data={data} caption={r.title} />
        : (
          <div className="ui-table-scroll">
            <table className="ui-table">
              <thead><tr>{r.dim_labels.map((l) => <th key={l}>{l}</th>)}<th>{r.measure_label}</th></tr></thead>
              <tbody>{r.rows.map((x) => (
                <tr key={x.keys.join('|')}>{x.keys.map((k, i) => <td key={i} data-label={r.dim_labels[i]}>{k}</td>)}<td data-label={r.measure_label}>{fmt(x.value)}</td></tr>
              ))}</tbody>
            </table>
          </div>
        )}
      {r.hidden_groups > 0 && <p className="pj-hint">{r.hidden_groups} satır gizlendi (en az {r.privacy?.k_min} şirket ve tek şirket payı en çok %{r.privacy?.dominance_pct} kuralı).</p>}
      {r.truncated && <p className="pj-hint">İlk 200 satır gösteriliyor; tamamı için filtre daraltın.</p>}
    </div>
  );
}
