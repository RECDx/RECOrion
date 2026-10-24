import React, { useEffect, useMemo, useState } from 'react';
import { Plug, Sparkles } from 'lucide-react';
import { api } from '../../api';
import { Badge, Button, EmptyState, Modal } from '../../ui/components';
import { toast } from '../../ui/feedback';

export const METHOD_TONE = { NATIVE: 'success', MCP_OAUTH: 'info', MCP_TOKEN: 'info', EDGE: 'warning', PLANNED: 'neutral' };

/** Bağlantı kataloğu (ADIM 12.1): sistem kartları, kategori/arama ve RECAi bağlanma rehberi. Seçilen kart → bağlantı formu. */
export function CatalogGallery({ tenantId, catalog, onClose, onPick }) {
  const [category, setCategory] = useState('ALL');
  const [q, setQ] = useState('');
  const [ask, setAsk] = useState('');
  const [advice, setAdvice] = useState(null);
  const [busy, setBusy] = useState(false);
  const shown = useMemo(() => {
    const needle = q.trim().toLocaleLowerCase('tr');
    return catalog.entries.filter((e) => (category === 'ALL' || e.category === category)
      && (!needle || `${e.title} ${e.vendor || ''} ${e.keywords || ''} ${e.description || ''}`.toLocaleLowerCase('tr').includes(needle)));
  }, [catalog, category, q]);
  const used = catalog.categories.filter((c) => catalog.entries.some((e) => e.category === c));

  const advise = async () => {
    if (ask.trim().length < 3) return toast.warning('Kullandığınız sistemi kısaca yazın.');
    setBusy(true);
    setAdvice(null);
    try { setAdvice(await api.adviseIntegration(tenantId, ask.trim())); } catch (e) { toast.error(e.message); } finally { setBusy(false); }
  };

  return (
    <Modal open onClose={onClose} title="Bağlantı ekle" size="lg" footer={<Button variant="secondary" onClick={onClose}>Vazgeç</Button>}>
      <div className="pj-form" style={{ marginBottom: 10 }}>
        <div className="pj-field full">
          <label htmlFor="ig-search">Sistem ara</label>
          <input id="ig-search" className="ui-input" value={q} onChange={(e) => setQ(e.target.value)} placeholder="ör. Logo, Jira, Notion, muhasebe" />
        </div>
      </div>
      <div className="ui-segmented ig-cats" role="tablist" aria-label="Kategoriler">
        {[['ALL', 'Tümü'], ...used.map((c) => [c, c])].map(([k, l]) => (
          <button key={k} type="button" className={`ui-segmented-item ${category === k ? 'active' : ''}`} onClick={() => setCategory(k)}>{l}</button>
        ))}
      </div>
      {shown.length === 0 ? <EmptyState icon={Plug} title="Bu aramaya uyan sistem yok" description="Aşağıdan RECAi'ye sorun; en uygun bağlanma yolunu önersin." /> : (
        <div className="pj-grid" role="list" aria-label="Bağlantı kataloğu">
          {shown.map((e) => (
            <button key={e.code} type="button" role="listitem" className="pj-card" onClick={() => onPick(e)} aria-disabled={e.method === 'PLANNED'}>
              <span className="pj-meta"><Badge tone={METHOD_TONE[e.method]}>{e.method_label}</Badge><span>{e.category}</span></span>
              <strong>{e.title}</strong>
              {e.description && <span className="pj-hint">{e.description}</span>}
            </button>
          ))}
        </div>
      )}
      <div className="ig-advisor">
        <label htmlFor="ig-ask"><Sparkles size={15} /> Aradığınız sistem yok mu? RECAi'ye sorun</label>
        <textarea id="ig-ask" className="ui-input" rows={2} maxLength={1500} value={ask} onChange={(e) => setAsk(e.target.value)}
          placeholder="ör. Logo Tiger 3 kullanıyoruz, sunucu şirketin içinde; muhasebe ve stok verisine erişmek istiyoruz." />
        <div className="pj-actions"><Button size="sm" icon={Sparkles} disabled={busy} onClick={advise}>{busy ? 'RECAi düşünüyor…' : 'Nasıl bağlanırım?'}</Button></div>
        {advice && (
          <div className="ig-advice" aria-label="RECAi önerisi">
            <p>{advice.summary}</p>
            {advice.steps.length > 0 && <ol>{advice.steps.map((s, i) => <li key={i}>{s}</li>)}</ol>}
            {advice.notes && <p className="pj-hint">{advice.notes}</p>}
            {advice.entry && advice.entry.method !== 'PLANNED' && (
              <Button size="sm" onClick={() => onPick(advice.entry)}>{advice.entry.title} ile devam et</Button>
            )}
          </div>
        )}
      </div>
    </Modal>
  );
}

/** Kartın kurulum adımları (bağlantı formunun üstünde). */
export function SetupSteps({ entry, redirectUri }) {
  if (!entry) return null;
  return (
    <div className="ig-steps">
      <p><Badge tone={METHOD_TONE[entry.method]}>{entry.method_label}</Badge> {entry.description}</p>
      {entry.setup_steps?.length > 0 && <ol aria-label="Kurulum adımları">{entry.setup_steps.map((s, i) => <li key={i}>{s}</li>)}</ol>}
      {entry.method === 'MCP_OAUTH' && redirectUri && (
        <p className="pj-hint">Yönlendirme adresi (servis isterse): <code className="ig-inline">{redirectUri}</code></p>
      )}
    </div>
  );
}
