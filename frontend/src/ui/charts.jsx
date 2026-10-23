import React, { useEffect, useRef, useState } from 'react';
import './charts.css';

/**
 * Dashboard grafikleri (ADIM 9): bağımlılıksız, tema uyumlu küçük SVG/HTML grafikler.
 * Kurallar (dataviz): tek seri = tek renk (--viz-series-1), çift eksen yok, ince işaretler, 4px yuvarlak uç,
 * seyrek etiket, üzerine gelince/odakta ipucu, her grafikte tablo görünümü. Metin hiçbir zaman seri rengini almaz.
 */
export const compact = (n) => {
  const v = Number(n || 0);
  const a = Math.abs(v);
  if (a >= 1e6) return `${(v / 1e6).toLocaleString('tr-TR', { maximumFractionDigits: 1 })} mn`;
  if (a >= 1e4) return `${(v / 1e3).toLocaleString('tr-TR', { maximumFractionDigits: 1 })} bin`;
  return v.toLocaleString('tr-TR', { maximumFractionDigits: a < 10 ? 2 : 0 });
};
/** Kart değerleri için kısa TL (24,5 bin ₺); tam tutar title/tablo görünümünde. */
export const tlShort = (n) => (n == null ? '—' : Math.abs(Number(n)) >= 1e4 ? `${compact(n)} ₺` : `${Number(n).toLocaleString('tr-TR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} ₺`);
export const tl = (n) => (n == null ? '—' : `${Number(n).toLocaleString('tr-TR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} ₺`);

function niceMax(v) {
  if (v <= 0) return 1;
  const p = 10 ** Math.floor(Math.log10(v));
  return [1, 2, 2.5, 5, 10].map((m) => m * p).find((x) => x >= v) || 10 * p;
}

function useTip() {
  const [tip, setTip] = useState(null);
  const box = useRef(null);
  const show = (e, lines) => {
    const r = box.current?.getBoundingClientRect();
    const t = e.currentTarget.getBoundingClientRect();
    if (!r) return;
    setTip({ x: t.left - r.left + t.width / 2, y: t.top - r.top, lines });
  };
  return { tip, box, show, hide: () => setTip(null) };
}

function Tip({ tip }) {
  if (!tip) return null;
  return (
    <div className="viz-tip" role="status" style={{ left: tip.x, top: tip.y }}>
      {tip.lines.map(([value, label], i) => (
        <div key={i}><strong>{value}</strong> <span>{label}</span></div>
      ))}
    </div>
  );
}

function TableView({ caption, columns, rows }) {
  return (
    <details className="viz-table">
      <summary>Tablo olarak göster</summary>
      <div className="ui-table-scroll">
        <table className="ui-table">
          <caption className="sr-only">{caption}</caption>
          <thead><tr>{columns.map((c) => <th key={c}>{c}</th>)}</tr></thead>
          <tbody>{rows.map((r, i) => <tr key={i}>{r.map((v, j) => <td key={j} data-label={columns[j]}>{v}</td>)}</tr>)}</tbody>
        </table>
      </div>
    </details>
  );
}

/** Kabın gerçek genişliği: SVG ölçeklenmez, yazılar her genişlikte aynı boyda kalır. */
function useWidth(ref, initial = 600) {
  const [w, setW] = useState(initial);
  useEffect(() => {
    if (!ref.current || typeof ResizeObserver === 'undefined') return undefined;
    const ro = new ResizeObserver(([e]) => setW(Math.max(240, Math.round(e.contentRect.width))));
    ro.observe(ref.current);
    return () => ro.disconnect();
  }, [ref]);
  return w;
}

/** Zaman serisi sütunları: data = [{ key, label, value }], label eksende/ipucunda tarih. */
export function ColumnChart({ data, format = compact, unit = '', caption, height = 180, empty }) {
  const { tip, box, show, hide } = useTip();
  const W = useWidth(box), H = height, L = 44, B = 22, T = 10;
  if (empty && !data.some((d) => d.value > 0)) return <div className="viz-root" ref={box}><p className="pj-hint">{empty}</p></div>;
  const max = niceMax(Math.max(0, ...data.map((d) => d.value)));
  const band = (W - L) / Math.max(1, data.length);
  const bw = Math.min(24, Math.max(2, band - 2));
  const y = (v) => T + (H - T - B) * (1 - v / max);
  const ticks = [0, max / 2, max];
  const labelEvery = Math.ceil(data.length / Math.max(2, Math.floor((W - L) / 70)));
  return (
    <div className="viz-root" ref={box}>
      <svg width={W} height={H} viewBox={`0 0 ${W} ${H}`} className="viz-svg" role="img" aria-label={caption}>
        {ticks.map((t) => (
          <g key={t}>
            <line x1={L} x2={W} y1={y(t)} y2={y(t)} className="viz-grid" />
            <text x={L - 6} y={y(t) + 4} className="viz-tick" textAnchor="end">{compact(t)}</text>
          </g>
        ))}
        {data.map((d, i) => {
          const x = L + i * band + (band - bw) / 2;
          const h = Math.max(0, H - B - y(d.value));
          const r = Math.min(4, bw / 2, h);
          const lines = [[`${format(d.value)}${unit}`, d.label]];
          return (
            <g key={d.key} tabIndex={0} className="viz-hit" onPointerEnter={(e) => show(e, lines)} onPointerLeave={hide}
              onFocus={(e) => show(e, lines)} onBlur={hide} aria-label={`${d.label}: ${format(d.value)}${unit}`}>
              <rect x={L + i * band} y={T} width={band} height={H - T - B} fill="transparent" />
              {h > 0 && (
                <path className="viz-mark" d={`M${x},${H - B} V${H - B - h + r} Q${x},${H - B - h} ${x + r},${H - B - h} H${x + bw - r} Q${x + bw},${H - B - h} ${x + bw},${H - B - h + r} V${H - B} Z`} />
              )}
              {i % labelEvery === 0 && <text x={x + bw / 2} y={H - 6} className="viz-tick" textAnchor="middle">{d.short || d.label}</text>}
            </g>
          );
        })}
        <line x1={L} x2={W} y1={H - B} y2={H - B} className="viz-axis" />
      </svg>
      <Tip tip={tip} />
      <TableView caption={caption} columns={['Tarih', 'Değer']} rows={data.map((d) => [d.label, `${format(d.value)}${unit}`])} />
    </div>
  );
}

/** Yatay çubuklar (tek seri): data = [{ key, label, value, note }], değer çubuğun ucunda. */
export function BarList({ data, format = compact, caption, empty = 'Veri yok.' }) {
  const { tip, box, show, hide } = useTip();
  if (!data.length) return <p className="pj-hint">{empty}</p>;
  const max = Math.max(...data.map((d) => d.value), 0) || 1;
  return (
    <div className="viz-root" ref={box}>
      <ul className="viz-bars" aria-label={caption}>
        {data.map((d) => {
          const lines = [[format(d.value), d.label], ...(d.note ? [[d.note, '']] : [])];
          return (
            <li key={d.key} tabIndex={0} onPointerEnter={(e) => show(e, lines)} onPointerLeave={hide} onFocus={(e) => show(e, lines)} onBlur={hide}>
              <span className="viz-bar-label" title={d.label}>{d.label}</span>
              <span className="viz-bar-track"><span className="viz-bar" style={{ width: `${Math.max(1.5, (d.value / max) * 100)}%` }} /></span>
              <span className="viz-bar-value">{format(d.value)}</span>
            </li>
          );
        })}
      </ul>
      <Tip tip={tip} />
      <TableView caption={caption} columns={['Kalem', 'Değer', 'Not']} rows={data.map((d) => [d.label, format(d.value), d.note || ''])} />
    </div>
  );
}

/** Bütçe / gerçekleşen (bullet): çubuk = gerçekleşen, dikey çizgi = bütçe; bütçe aşımı durum etiketiyle (yalnızca renk değil). */
export function BudgetBars({ data, caption }) {
  const { tip, box, show, hide } = useTip();
  if (!data.length) return <p className="pj-hint">Henüz maliyeti olan proje yok.</p>;
  const max = Math.max(...data.map((d) => Math.max(d.actual, d.budget || 0)), 0) || 1;
  return (
    <div className="viz-root" ref={box}>
      <div className="viz-legend" aria-hidden="true">
        <span><i className="viz-key-bar" /> Gerçekleşen</span><span><i className="viz-key-tick" /> Bütçe</span>
      </div>
      <ul className="viz-bars" aria-label={caption}>
        {data.map((d) => {
          const over = d.budget != null && d.actual > d.budget;
          const lines = [[tl(d.actual), 'gerçekleşen'], [d.budget != null ? tl(d.budget) : 'tanımsız', 'bütçe'], [d.status, '']];
          return (
            <li key={d.key} tabIndex={0} onPointerEnter={(e) => show(e, lines)} onPointerLeave={hide} onFocus={(e) => show(e, lines)} onBlur={hide}>
              <span className="viz-bar-label" title={d.label}>{d.label}</span>
              <span className="viz-bar-track">
                <span className="viz-bar" style={{ width: `${Math.max(1.5, (d.actual / max) * 100)}%` }} />
                {d.budget != null && <span className="viz-tick-mark" style={{ left: `${(d.budget / max) * 100}%` }} />}
              </span>
              <span className="viz-bar-value">
                {tl(d.actual)}{over && <span className="viz-status viz-status-critical">▲ bütçe aşıldı</span>}
              </span>
            </li>
          );
        })}
      </ul>
      <Tip tip={tip} />
      <TableView caption={caption} columns={['Proje', 'Durum', 'Bütçe', 'Gerçekleşen', 'Fark']}
        rows={data.map((d) => [d.label, d.status, d.budget != null ? tl(d.budget) : '—', tl(d.actual), d.budget != null ? tl(d.budget - d.actual) : '—'])} />
    </div>
  );
}
