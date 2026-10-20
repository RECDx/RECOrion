import React from 'react';

/**
 * Model yanıtları için küçük ve güvenli markdown gösterimi: başlık, madde, numaralı madde, **kalın**, `kod`.
 * HTML üretmez (dangerouslySetInnerHTML yok); her şey React öğesi olarak çizilir.
 */
function inline(text, keyBase) {
  const parts = text.split(/(\*\*[^*]+\*\*|`[^`]+`)/g);
  return parts.map((p, i) => {
    if (p.startsWith('**') && p.endsWith('**') && p.length > 4) return <strong key={`${keyBase}-${i}`}>{p.slice(2, -2)}</strong>;
    if (p.startsWith('`') && p.endsWith('`') && p.length > 2) return <code key={`${keyBase}-${i}`}>{p.slice(1, -1)}</code>;
    return p;
  });
}

export default function SimpleMarkdown({ text }) {
  const blocks = [];
  let list = null;
  const flush = () => { if (list) { blocks.push(list); list = null; } };

  (text || '').split('\n').forEach((raw, i) => {
    const line = raw.trimEnd();
    const bullet = /^\s*[-*•]\s+(.*)$/.exec(line);
    const numbered = /^\s*(\d+)[.)]\s+(.*)$/.exec(line);
    const heading = /^(#{1,4})\s+(.*)$/.exec(line);
    if (bullet || numbered) {
      const type = bullet ? 'ul' : 'ol';
      if (!list || list.type !== type) { flush(); list = { type, items: [], key: i }; }
      list.items.push(inline(bullet ? bullet[1] : numbered[2], i));
      return;
    }
    flush();
    if (heading) blocks.push({ type: 'h', text: heading[2], key: i });
    else if (/^\s*(-{3,}|\|[-:| ]+\|)\s*$/.test(line)) blocks.push({ type: 'hr', key: i });
    else if (line.trim()) blocks.push({ type: 'p', text: line, key: i });
  });
  flush();

  return (
    <div className="ai-md">
      {blocks.map((b) => {
        if (b.type === 'h') return <div key={b.key} className="ai-md-h">{inline(b.text, b.key)}</div>;
        if (b.type === 'hr') return <hr key={b.key} />;
        if (b.type === 'p') return <p key={b.key}>{inline(b.text, b.key)}</p>;
        const Tag = b.type;
        return <Tag key={b.key}>{b.items.map((it, j) => <li key={j}>{it}</li>)}</Tag>;
      })}
    </div>
  );
}
