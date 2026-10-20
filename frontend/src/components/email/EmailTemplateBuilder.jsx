import React, { useMemo, useRef, useState } from 'react';
import { ArrowDown, ArrowUp, Copy, GripVertical, Monitor, Plus, Redo2, Smartphone, Trash2, Undo2 } from 'lucide-react';
import { BLOCK_FIELDS, EMAIL_PRESET_BLOCKS, OPTION_LABELS, blockSummary, compileBlocksToHtml, createBlock, newBlockId } from './emailBlocks';
import './email-builder.css';

const PALETTE = [
  ['Başlık ve metin', ['HEADER', 'HEADING', 'GREETING', 'CONTENT', 'INFO_BOX']],
  ['Bilgi kartları', ['CODE_BOX', 'PACKAGE_INFO', 'CREDENTIALS']],
  ['Buton ve görsel', ['BUTTON', 'IMAGE', 'DIVIDER']],
  ['Alt bilgi ve gelişmiş', ['FOOTER', 'HTML']],
];
const DND_TYPE = 'application/x-recorion-email-block';
const labelOf = (type) => EMAIL_PRESET_BLOCKS.find((p) => p.type === type)?.label || type;

/**
 * Sürükle-bırak e-posta şablonu düzenleyicisi.
 * Bloklar soldan tıklanarak (seçili bloğun altına) ya da sürüklenerek istenen konuma eklenir;
 * tuvaldeki bloklar tutamaktan sürüklenerek sıralanır. Sağda seçili bloğun ayarları ve canlı önizleme vardır.
 */
export default function EmailTemplateBuilder({ blocks, onChange, variables = [] }) {
  const [selectedId, setSelectedId] = useState(blocks[0]?.id || null);
  const [panel, setPanel] = useState('SETTINGS');
  const [device, setDevice] = useState('desktop');
  const [dropIndex, setDropIndex] = useState(null);
  const [past, setPast] = useState([]);
  const [future, setFuture] = useState([]);
  const dragRef = useRef(null); // { kind: 'new', type } | { kind: 'move', index }
  const focusRef = useRef(null); // son odaklanan metin alanı: { key, el }
  const canvasRef = useRef(null);

  const selectedIndex = blocks.findIndex((b) => b.id === selectedId);
  const selected = selectedIndex >= 0 ? blocks[selectedIndex] : null;
  const html = useMemo(() => compileBlocksToHtml(blocks), [blocks]);

  const commit = (next) => {
    setPast((p) => [...p.slice(-40), blocks]);
    setFuture([]);
    onChange(next);
  };
  const undo = () => {
    if (!past.length) return;
    setFuture((f) => [blocks, ...f]);
    onChange(past[past.length - 1]);
    setPast((p) => p.slice(0, -1));
  };
  const redo = () => {
    if (!future.length) return;
    setPast((p) => [...p, blocks]);
    onChange(future[0]);
    setFuture((f) => f.slice(1));
  };

  const insertAt = (type, index) => {
    const block = createBlock(type);
    if (!block) return;
    const next = [...blocks];
    next.splice(Math.max(0, Math.min(index, next.length)), 0, block);
    commit(next);
    setSelectedId(block.id);
    setPanel('SETTINGS');
  };
  const move = (from, to) => {
    if (to < 0 || to > blocks.length || from === to || from + 1 === to) return;
    const next = [...blocks];
    const [item] = next.splice(from, 1);
    next.splice(to > from ? to - 1 : to, 0, item);
    commit(next);
  };
  const update = (key, value) => commit(blocks.map((b) => (b.id === selectedId ? { ...b, [key]: value } : b)));
  const duplicate = (index) => {
    const copy = { ...blocks[index], id: newBlockId() };
    const next = [...blocks];
    next.splice(index + 1, 0, copy);
    commit(next);
    setSelectedId(copy.id);
  };
  const remove = (index) => {
    const next = blocks.filter((_, i) => i !== index);
    commit(next);
    setSelectedId(next[Math.min(index, next.length - 1)]?.id || null);
  };

  // Seçili alanın imleç konumuna {{değişken}} ekler
  const insertVariable = (name) => {
    const token = `{{${name}}}`;
    const target = focusRef.current;
    if (!selected || !target || !(target.key in selected)) {
      const first = (BLOCK_FIELDS[selected?.type] || []).find((f) => ['text', 'textarea', 'code'].includes(f.kind));
      if (first) update(first.key, `${selected[first.key] || ''}${token}`);
      return;
    }
    const value = String(selected[target.key] || '');
    const start = target.el.selectionStart ?? value.length;
    const end = target.el.selectionEnd ?? value.length;
    update(target.key, value.slice(0, start) + token + value.slice(end));
    requestAnimationFrame(() => {
      target.el.focus();
      target.el.setSelectionRange(start + token.length, start + token.length);
    });
  };

  // --- sürükle-bırak: bırakma konumu farenin dikey konumundan hesaplanır (kartın üst/alt yarısı)
  const indexFromPoint = (clientY) => {
    const cards = [...(canvasRef.current?.querySelectorAll('.eb-card') || [])];
    const hit = cards.findIndex((c) => { const r = c.getBoundingClientRect(); return clientY < r.top + r.height / 2; });
    return hit === -1 ? cards.length : hit;
  };
  const onCanvasDragOver = (e) => {
    if (!dragRef.current) return;
    e.preventDefault();
    e.dataTransfer.dropEffect = dragRef.current.kind === 'new' ? 'copy' : 'move';
    const index = indexFromPoint(e.clientY);
    if (index !== dropIndex) setDropIndex(index);
  };
  const onDrop = (e) => {
    e.preventDefault();
    const drag = dragRef.current;
    const index = indexFromPoint(e.clientY);
    dragRef.current = null;
    setDropIndex(null);
    if (!drag) return;
    if (drag.kind === 'new') insertAt(drag.type, index);
    else move(drag.index, index);
  };
  const endDrag = () => { dragRef.current = null; setDropIndex(null); };

  const renderField = (f) => {
    const value = selected[f.key] ?? '';
    const common = {
      id: `eb-${f.key}`,
      value,
      onFocus: (e) => { focusRef.current = { key: f.key, el: e.target }; },
      onChange: (e) => update(f.key, e.target.value),
    };
    if (f.kind === 'textarea' || f.kind === 'code') {
      return <textarea {...common} className={`ui-input ${f.kind === 'code' ? 'eb-code' : ''}`} rows={f.kind === 'code' ? 10 : 4} />;
    }
    if (f.kind === 'select') {
      return (
        <select {...common} className="ui-input">
          <option value="">Varsayılan</option>
          {f.options.map((o) => <option key={o} value={o}>{OPTION_LABELS[o] || o}</option>)}
        </select>
      );
    }
    if (f.kind === 'color') {
      return (
        <div className="eb-color">
          <input type="color" value={/^#[0-9a-f]{6}$/i.test(value) ? value : '#000000'} onChange={(e) => update(f.key, e.target.value)} aria-label={f.label} />
          <input {...common} className="ui-input" placeholder="Varsayılan" />
        </div>
      );
    }
    return <input {...common} className="ui-input" />;
  };

  return (
    <div className="eb">
      <aside className="eb-palette" aria-label="Bloklar">
        <div className="eb-head">Bloklar <span>tıkla veya sürükle</span></div>
        {PALETTE.map(([group, types]) => (
          <div key={group} className="eb-group">
            <div className="eb-group-title">{group}</div>
            {types.map((type) => (
              <button
                type="button" key={type} className="eb-preset" draggable
                onDragStart={(e) => { dragRef.current = { kind: 'new', type }; e.dataTransfer.setData(DND_TYPE, type); e.dataTransfer.effectAllowed = 'copy'; }}
                onDragEnd={endDrag}
                onClick={() => insertAt(type, selectedIndex >= 0 ? selectedIndex + 1 : blocks.length)}
                title="Seçili bloğun altına ekler; sürükleyerek istediğiniz yere bırakabilirsiniz"
              >
                <GripVertical size={13} /> <span>{labelOf(type)}</span> <Plus size={13} />
              </button>
            ))}
          </div>
        ))}
      </aside>

      <section className="eb-canvas" ref={canvasRef} onDragOver={onCanvasDragOver} onDrop={onDrop} onDragLeave={(e) => { if (!e.currentTarget.contains(e.relatedTarget)) setDropIndex(null); }} aria-label="Şablon tuvali">
        <div className="eb-head">
          Şablon ({blocks.length} blok)
          <span className="eb-tools">
            <button type="button" className="ui-icon-btn" onClick={undo} disabled={!past.length} title="Geri al" aria-label="Geri al"><Undo2 size={15} /></button>
            <button type="button" className="ui-icon-btn" onClick={redo} disabled={!future.length} title="Yinele" aria-label="Yinele"><Redo2 size={15} /></button>
          </span>
        </div>
        {blocks.length === 0 && (
          <div className={`eb-empty ${dropIndex === 0 ? 'over' : ''}`}>Soldan bir blok sürükleyip buraya bırakın veya tıklayarak ekleyin.</div>
        )}
        {blocks.map((b, i) => (
          <React.Fragment key={b.id}>
            {dropIndex === i && <div className="eb-drop-line" />}
            <div
              className={`eb-card ${b.id === selectedId ? 'selected' : ''}`}
              draggable
              onDragStart={(e) => { dragRef.current = { kind: 'move', index: i }; e.dataTransfer.setData(DND_TYPE, b.id); e.dataTransfer.effectAllowed = 'move'; }}
              onDragEnd={endDrag}
              onClick={() => { setSelectedId(b.id); setPanel('SETTINGS'); }}
              role="button" tabIndex={0}
              onKeyDown={(e) => { if (e.key === 'Enter') setSelectedId(b.id); }}
            >
              <GripVertical size={15} className="eb-grip" />
              <div className="eb-card-body">
                <strong>{labelOf(b.type)}</strong>
                <span>{blockSummary(b) || '—'}</span>
              </div>
              <div className="eb-card-actions" onClick={(e) => e.stopPropagation()}>
                <button type="button" className="ui-icon-btn" disabled={i === 0} onClick={() => move(i, i - 1)} title="Yukarı" aria-label="Yukarı taşı"><ArrowUp size={13} /></button>
                <button type="button" className="ui-icon-btn" disabled={i === blocks.length - 1} onClick={() => move(i, i + 2)} title="Aşağı" aria-label="Aşağı taşı"><ArrowDown size={13} /></button>
                <button type="button" className="ui-icon-btn" onClick={() => duplicate(i)} title="Çoğalt" aria-label="Çoğalt"><Copy size={13} /></button>
                <button type="button" className="ui-icon-btn" onClick={() => remove(i)} title="Sil" aria-label="Sil"><Trash2 size={13} /></button>
              </div>
            </div>
          </React.Fragment>
        ))}
        {dropIndex === blocks.length && blocks.length > 0 && <div className="eb-drop-line" />}
      </section>

      <aside className="eb-side">
        <div className="ui-segmented">
          <button type="button" className={`ui-segmented-item ${panel === 'SETTINGS' ? 'active' : ''}`} onClick={() => setPanel('SETTINGS')}>Blok ayarları</button>
          <button type="button" className={`ui-segmented-item ${panel === 'PREVIEW' ? 'active' : ''}`} onClick={() => setPanel('PREVIEW')}>Önizleme</button>
        </div>

        {panel === 'SETTINGS' ? (
          !selected ? <p className="eb-hint">Düzenlemek için tuvalden bir blok seçin.</p> : (
            <div className="eb-fields">
              <div className="eb-field-title">{labelOf(selected.type)}</div>
              {(BLOCK_FIELDS[selected.type] || []).length === 0 && <p className="eb-hint">Bu bloğun ayarı yok.</p>}
              {(BLOCK_FIELDS[selected.type] || []).map((f) => (
                <div className="eb-field" key={f.key}>
                  <label htmlFor={`eb-${f.key}`}>{f.label}</label>
                  {renderField(f)}
                </div>
              ))}
              {variables.length > 0 && (
                <div className="eb-field">
                  <label>Değişken ekle</label>
                  <div className="eb-vars">
                    {variables.map((v) => (
                      <button type="button" key={v} className="eb-var" onMouseDown={(e) => e.preventDefault()} onClick={() => insertVariable(v)}>{`{{${v}}}`}</button>
                    ))}
                  </div>
                  <span className="eb-hint">Önce bir metin alanına tıklayın; değişken imlecin olduğu yere eklenir.</span>
                </div>
              )}
            </div>
          )
        ) : (
          <div className="eb-preview">
            <div className="eb-tools">
              <button type="button" className={`ui-icon-btn ${device === 'desktop' ? 'active' : ''}`} onClick={() => setDevice('desktop')} title="Masaüstü" aria-label="Masaüstü önizleme"><Monitor size={15} /></button>
              <button type="button" className={`ui-icon-btn ${device === 'mobile' ? 'active' : ''}`} onClick={() => setDevice('mobile')} title="Telefon" aria-label="Telefon önizleme"><Smartphone size={15} /></button>
            </div>
            <iframe title="E-posta önizleme" sandbox="" srcDoc={html} className={`eb-frame ${device}`} />
          </div>
        )}
      </aside>
    </div>
  );
}
