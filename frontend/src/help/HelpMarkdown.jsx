import React, { useEffect, useState } from 'react';
import { api } from '../api';
import { slugify } from './helpBus';

/**
 * Yardım sayfası gösterimi (ADIM 15.3): başlık (sayfa içi bağlantılı), paragraf, madde, numaralı adım, tablo, uyarı kutusu
 * (İpucu / Dikkat / Örnek / Not), görsel. HTML üretmez; her şey React öğesi olarak çizilir (güvenli).
 */
function inline(text, k) {
  return (text || '').split(/(\*\*[^*]+\*\*|`[^`]+`|\*[^*\s][^*]*\*)/g).map((p, i) => {
    if (/^\*\*[^*]+\*\*$/.test(p)) return <strong key={`${k}-${i}`}>{p.slice(2, -2)}</strong>;
    if (/^`[^`]+`$/.test(p)) return <code key={`${k}-${i}`}>{p.slice(1, -1)}</code>;
    if (/^\*[^*].*\*$/.test(p)) return <em key={`${k}-${i}`}>{p.slice(1, -1)}</em>;
    return p;
  });
}

function HelpImage({ name, caption }) {
  const [src, setSrc] = useState(null);
  const [zoom, setZoom] = useState(false);
  useEffect(() => {
    let url = null;
    let alive = true;
    api.getHelpAsset(name).then((b) => { url = URL.createObjectURL(b); if (alive) setSrc(url); }).catch(() => {});
    return () => { alive = false; if (url) URL.revokeObjectURL(url); };
  }, [name]);
  if (!src) return null;
  return (
    <figure className="hp-fig">
      <img src={src} alt={caption} loading="lazy" onClick={() => setZoom(true)} title="Büyütmek için tıklayın" />
      <figcaption>{caption}</figcaption>
      {zoom && <div className="hp-zoom" role="button" tabIndex={0} onClick={() => setZoom(false)} onKeyDown={() => setZoom(false)}><img src={src} alt={caption} /></div>}
    </figure>
  );
}

const CALLOUT = /^\*\*(İpucu|Dikkat|Örnek|Not|Önemli):\*\*\s*(.*)$/;
const cells = (l) => l.trim().replace(/^\||\|$/g, '').split(/(?<!\\)\|/).map((c) => c.trim().replace(/\\\|/g, '|'));

export default function HelpMarkdown({ text }) {
  const lines = (text || '').split('\n');
  const out = [];
  let i = 0;
  let key = 0;
  while (i < lines.length) {
    const line = lines[i];
    if (!line.trim()) { i += 1; continue; }
    const h = /^(#{1,4})\s+(.*)$/.exec(line);
    if (h) {
      const Tag = `h${Math.min(6, h[1].length + 2)}`;
      out.push(<Tag key={key++} id={`hp-${slugify(h[2])}`} className="hp-h">{inline(h[2], key)}</Tag>);
      i += 1; continue;
    }
    const img = /^!\[(.*)\]\(([^)]+)\)\s*$/.exec(line);
    if (img) { out.push(<HelpImage key={key++} name={img[2]} caption={img[1]} />); i += 1; continue; }
    if (/^\s*\|/.test(line)) {
      const rows = [];
      while (i < lines.length && /^\s*\|/.test(lines[i])) { if (!/^\s*\|[\s:|-]+\|\s*$/.test(lines[i])) rows.push(cells(lines[i])); i += 1; }
      const [head, ...body] = rows;
      out.push(
        <div key={key++} className="hp-table"><table>
          <thead><tr>{head.map((c, j) => <th key={j}>{inline(c, `${key}h${j}`)}</th>)}</tr></thead>
          <tbody>{body.map((r, ri) => <tr key={ri}>{r.map((c, j) => <td key={j} data-label={head[j]}>{inline(c, `${key}-${ri}-${j}`)}</td>)}</tr>)}</tbody>
        </table></div>);
      continue;
    }
    if (/^>\s?/.test(line)) {
      const q = [];
      while (i < lines.length && /^>\s?/.test(lines[i])) { q.push(lines[i].replace(/^>\s?/, '')); i += 1; }
      const call = CALLOUT.exec(q[0] || '');
      const kind = call ? call[1] : 'Not';
      const rest = (call ? [call[2], ...q.slice(1)] : q).filter((x) => x.trim());
      out.push(
        <div key={key++} className={`hp-callout hp-${slugify(kind)}`}>
          <strong className="hp-callout-t">{kind}</strong>
          {rest.map((r, j) => {
            const li = /^\s*(\d+\.|[-*])\s+(.*)$/.exec(r);
            return <p key={j} className={li ? 'hp-callout-li' : ''}>{li ? <><span>{/\d/.test(li[1]) ? li[1] : '•'}</span> {inline(li[2], `${key}c${j}`)}</> : inline(r, `${key}c${j}`)}</p>;
          })}
        </div>);
      continue;
    }
    if (/^\s*([-*]|\d+\.)\s+/.test(line)) {
      const ordered = /^\s*\d+\./.test(line);
      const items = [];
      while (i < lines.length && /^\s*([-*]|\d+\.)\s+/.test(lines[i])) {
        const m = /^(\s*)([-*]|\d+\.)\s+(.*)$/.exec(lines[i]);
        items.push({ depth: Math.min(2, Math.floor(m[1].length / 2)), text: m[3] });
        i += 1;
        while (i < lines.length && lines[i].trim() && /^\s{2,}\S/.test(lines[i]) && !/^\s*([-*]|\d+\.)\s+/.test(lines[i])) { items[items.length - 1].text += ` ${lines[i].trim()}`; i += 1; }
      }
      const Tag = ordered ? 'ol' : 'ul';
      out.push(<Tag key={key++} className="hp-list">{items.map((it, j) => <li key={j} style={{ marginLeft: it.depth * 18 }}>{inline(it.text, `${key}l${j}`)}</li>)}</Tag>);
      continue;
    }
    const para = [line.trim()];
    i += 1;
    while (i < lines.length && lines[i].trim() && !/^(#{1,4}\s|>|\s*\||!\[|\s*([-*]|\d+\.)\s)/.test(lines[i])) { para.push(lines[i].trim()); i += 1; }
    out.push(<p key={key++}>{inline(para.join(' '), key)}</p>);
  }
  return <div className="hp-md">{out}</div>;
}
