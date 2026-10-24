import React, { useCallback, useEffect, useState } from 'react';
import { Plus, Save } from 'lucide-react';
import { api } from '../../api';
import { Badge, Button, Card, Modal } from '../../ui/components';
import { toast } from '../../ui/feedback';
import { METHOD_TONE } from './Catalog';
import '../projects/projects.css';
import './integrations.css';

/** Bağlantı kataloğu yönetimi (ADIM 12.1, RECDx Süper Admin): kartlar şirketlerin "Bağlantı ekle" galerisinde görünür. */
export default function IntegrationCatalogAdmin() {
  const [data, setData] = useState(null);
  const [connectors, setConnectors] = useState([]);
  const [editing, setEditing] = useState(null);
  const load = useCallback(() => Promise.all([api.getCatalogAdmin().then(setData), api.getConnectors().then((c) => setConnectors(c.connectors))])
    .catch((e) => toast.error(e.message)), []);
  useEffect(() => { load(); }, [load]);
  if (!data) return <p className="pj-hint">Yükleniyor…</p>;
  return (
    <div className="pj-steps">
      <Card title="Bağlantı kataloğu" subtitle="Şirketlerin bağlanabileceği sistemler ve bağlanma yolları. Kartlar kimlik bilgisi içermez; ön ayar yalnızca düz alanlardır (ör. MCP adresi)."
        actions={<Button icon={Plus} onClick={() => setEditing({ category: 'ERP', method: 'MCP_OAUTH', connector: 'mcp', preset: {}, setup_steps: [], sort: 100 })}>Kart ekle</Button>}>
        <div className="ui-table-scroll">
          <table className="ui-table">
            <thead><tr><th>Sistem</th><th>Kategori</th><th>Bağlanma yolu</th><th>Bağlayıcı</th><th>Durum</th><th /></tr></thead>
            <tbody>{data.entries.map((e) => (
              <tr key={e.id}>
                <td data-label="Sistem"><strong>{e.title}</strong><br /><small className="pj-hint">{e.code}{e.vendor ? ` · ${e.vendor}` : ''}</small></td>
                <td data-label="Kategori">{e.category}</td>
                <td data-label="Bağlanma yolu"><Badge tone={METHOD_TONE[e.method]}>{e.method_label}</Badge></td>
                <td data-label="Bağlayıcı">{e.connector || '—'}</td>
                <td data-label="Durum"><Badge tone={e.status === 'ACTIVE' ? 'success' : 'neutral'}>{e.status === 'ACTIVE' ? 'Yayında' : 'Arşivde'}</Badge></td>
                <td data-label=""><Button size="sm" variant="secondary" onClick={() => setEditing(e)}>Düzenle</Button></td>
              </tr>
            ))}</tbody>
          </table>
        </div>
      </Card>
      {editing && <EntryModal entry={editing} meta={data} connectors={connectors} onClose={() => setEditing(null)}
        onSaved={() => { setEditing(null); load(); }} />}
    </div>
  );
}

function EntryModal({ entry, meta, connectors, onClose, onSaved }) {
  const [f, setF] = useState({ ...entry, preset_text: JSON.stringify(entry.preset || {}, null, 2), steps_text: (entry.setup_steps || []).join('\n') });
  const [busy, setBusy] = useState(false);
  const set = (k) => (e) => setF((x) => ({ ...x, [k]: e.target.value }));
  const save = async (status) => {
    let preset;
    try { preset = JSON.parse(f.preset_text || '{}'); } catch { return toast.warning('Ön ayar geçerli JSON olmalı, ör. {"url": "https://..."}'); }
    const body = { code: f.code, title: f.title, vendor: f.vendor, category: f.category, method: f.method,
      connector: f.method === 'PLANNED' ? null : f.connector, preset, description: f.description, keywords: f.keywords,
      setup_steps: f.steps_text.split('\n').map((s) => s.trim()).filter(Boolean), sort: Number(f.sort) || 100, status: status || f.status || 'ACTIVE' };
    setBusy(true);
    try {
      if (entry.id) await api.updateCatalogEntry(entry.id, body); else await api.createCatalogEntry(body);
      toast.success('Kart kaydedildi.');
      onSaved();
    } catch (e) { toast.error(e.message); } finally { setBusy(false); }
  };
  return (
    <Modal open onClose={onClose} title={entry.id ? `${entry.title} · düzenle` : 'Kart ekle'} size="lg"
      footer={<>
        <Button variant="secondary" onClick={onClose}>Vazgeç</Button>
        {entry.id && <Button variant="ghost" disabled={busy} onClick={() => save(entry.status === 'ACTIVE' ? 'ARCHIVED' : 'ACTIVE')}>{entry.status === 'ACTIVE' ? 'Arşivle' : 'Yayına al'}</Button>}
        <Button icon={Save} disabled={busy || (f.title || '').trim().length < 2} onClick={() => save()}>Kaydet</Button>
      </>}>
      <div className="pj-form">
        <div className="pj-field"><label htmlFor="ca-code">Kod *</label>
          <input id="ca-code" className="ui-input" value={f.code || ''} disabled={!!entry.id} onChange={set('code')} placeholder="ör. logo_tiger" /></div>
        <div className="pj-field"><label htmlFor="ca-title">Sistem adı *</label>
          <input id="ca-title" className="ui-input" value={f.title || ''} maxLength={120} onChange={set('title')} /></div>
        <div className="pj-field"><label htmlFor="ca-vendor">Üretici</label>
          <input id="ca-vendor" className="ui-input" value={f.vendor || ''} onChange={set('vendor')} /></div>
        <div className="pj-field"><label htmlFor="ca-cat">Kategori</label>
          <select id="ca-cat" className="ui-input" value={f.category} onChange={set('category')}>{meta.categories.map((c) => <option key={c}>{c}</option>)}</select></div>
        <div className="pj-field"><label htmlFor="ca-method">Bağlanma yolu</label>
          <select id="ca-method" className="ui-input" value={f.method} onChange={set('method')}>
            {Object.entries(meta.methods).map(([k, l]) => <option key={k} value={k}>{l}</option>)}</select></div>
        {f.method !== 'PLANNED' && (
          <div className="pj-field"><label htmlFor="ca-conn">Bağlayıcı</label>
            <select id="ca-conn" className="ui-input" value={f.connector || ''} onChange={set('connector')}>
              {connectors.map((c) => <option key={c.code} value={c.code}>{c.title}</option>)}</select></div>
        )}
        <div className="pj-field full"><label htmlFor="ca-desc">Açıklama</label>
          <textarea id="ca-desc" className="ui-input" rows={2} value={f.description || ''} onChange={set('description')} /></div>
        <div className="pj-field full"><label htmlFor="ca-preset">Ön ayar (JSON; kimlik bilgisi yazmayın)</label>
          <textarea id="ca-preset" className="ui-input ig-inline" rows={3} value={f.preset_text} onChange={set('preset_text')} /></div>
        <div className="pj-field full"><label htmlFor="ca-steps">Kurulum adımları (her satır bir adım)</label>
          <textarea id="ca-steps" className="ui-input" rows={4} value={f.steps_text} onChange={set('steps_text')} /></div>
        <div className="pj-field"><label htmlFor="ca-kw">Arama kelimeleri</label>
          <input id="ca-kw" className="ui-input" value={f.keywords || ''} onChange={set('keywords')} /></div>
        <div className="pj-field"><label htmlFor="ca-sort">Sıra</label>
          <input id="ca-sort" className="ui-input" type="number" value={f.sort} onChange={set('sort')} /></div>
      </div>
    </Modal>
  );
}
