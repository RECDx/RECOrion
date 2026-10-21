import React, { useCallback, useEffect, useState } from 'react';
import { Layers, Search } from 'lucide-react';
import { api } from '../../api';
import { Badge, Button } from '../../ui/components';
import { toast } from '../../ui/feedback';
import './docs.css';

const TONES = { PROJECT: 'info', AGENT: 'success', TITLE: 'warning', GLOBAL: 'info', PLATFORM_TITLE: 'neutral' };
const HINTS = {
  AGENT: 'Bu personele yüklediğiniz dokümanlar ve sohbetlerden öğrendikleri',
  TITLE: 'Bu unvandaki tüm AI personele verdiğiniz bilgiler',
  GLOBAL: 'Şirketinizin tüm AI personelinin ortak bilgisi (onaylı)',
  PLATFORM_TITLE: 'RECOrion kataloğundaki genel mesleki bilgi',
};

/** AI personelin bilgi katmanları ve "bilgisini sına" aracı (ADIM 5.5). */
export default function AgentKnowledgePanel({ tenantId, agentId }) {
  const [summary, setSummary] = useState(null);
  const [query, setQuery] = useState('');
  const [result, setResult] = useState(null);
  const [busy, setBusy] = useState(false);

  const load = useCallback(() => api.getAgentKnowledge(tenantId, agentId).then(setSummary).catch(() => {}), [tenantId, agentId]);
  useEffect(() => { load(); }, [load]);

  const search = async (e) => {
    e.preventDefault();
    if (query.trim().length < 2) return;
    setBusy(true);
    try {
      setResult(await api.searchAgentKnowledge(tenantId, agentId, query.trim()));
    } catch (err) {
      toast.error(err.message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="kn-panel">
      <div className="kn-head"><Layers size={16} /> <strong>Bilgi katmanları</strong> <span className="doc-hint">Bu personel bir soruyu cevaplarken şu kaynakları birlikte kullanır; projede çalışırken proje ekleri de eklenir.</span></div>
      <div className="kn-layers">
        {(summary?.layers || []).map((l) => (
          <div key={l.layer} className="kn-layer" title={HINTS[l.layer]}>
            <span className="kn-layer-name">{l.label}</span>
            <span className="kn-layer-count">{l.documents}</span>
            <span className="doc-hint">{l.title ? `${l.title} · ` : ''}{l.layer === 'GLOBAL' ? 'onaylı bilgi' : 'onaylı doküman'}</span>
          </div>
        ))}
      </div>
      <form className="kn-search" onSubmit={search}>
        <input className="ui-input" value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Bilgisini sınayın: örn. fire oranı nasıl hesaplanır?" aria-label="Bilgi sorgusu" />
        <Button type="submit" size="sm" icon={Search} disabled={busy || query.trim().length < 2}>{busy ? 'Aranıyor…' : 'Sına'}</Button>
      </form>
      {result && (
        result.results.length === 0 ? <p className="doc-hint">Bu soru için hiçbir katmanda bilgi bulunamadı; personel bu konuda bilgisi olmadığını söyler.</p> : (
          <ul className="kn-results">
            {result.results.map((h, i) => (
              <li key={i}>
                <Badge tone={TONES[h.layer] || 'neutral'}>{h.label}</Badge>
                <span className="doc-hint">{h.source}</span>
                <p>{h.content.slice(0, 320)}{h.content.length > 320 ? '…' : ''}</p>
              </li>
            ))}
          </ul>
        )
      )}
    </div>
  );
}
