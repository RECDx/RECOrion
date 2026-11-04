import React, { useCallback, useEffect, useRef, useState } from 'react';
import { ArrowLeft, BookOpen, ChevronRight, Compass, LifeBuoy, Maximize2, Minimize2, Send, Sparkles, X } from 'lucide-react';
import { api, session } from '../api';
import { Badge, Button } from '../ui/components';
import { toast } from '../ui/feedback';
import HelpMarkdown from './HelpMarkdown';
import { getHelpScreen, navigateTo, openDialogTitle } from './helpBus';
import './help.css';

const EXAMPLES = {
  super: ['Yeni bir müşteri şirketi nasıl eklerim?', 'Bir kiralama paketini nasıl değiştiririm?'],
  company: ['RECSlip aylık sürecini nasıl kurarım?', 'Yeni bir AI personeli nasıl işe alırım?', 'Kullanıcıya rol nasıl veririm?'],
  workspace: ['Yeni bir proje nasıl açarım?', 'Onaylarım ekranında RECSlip fişini nasıl onaylarım?', 'Odoo anahtarımı nereden eklerim?'],
};

/**
 * Yardım (Bilgi Birikimi) paneli — ADIM 15.3/15.4. Sağdan açılır, ekranı kapatmaz; F1 / "Yardım" düğmesi ile açılır.
 * Sekmeler: Bu ekran (bulunulan ekranın anlatımı), İçindekiler (yetkiye göre süzülmüş kılavuzlar), RECAi'ye sor (soru-cevap).
 */
export default function HelpCenter() {
  const [open, setOpen] = useState(false);
  const [wide, setWide] = useState(false);
  const [tab, setTab] = useState('ask');
  const [page, setPage] = useState(null);
  const [trail, setTrail] = useState([]);
  const [tree, setTree] = useState(null);
  const [anchor, setAnchor] = useState(null);
  const [chat, setChat] = useState([]);
  const [q, setQ] = useState('');
  const [busy, setBusy] = useState(false);
  const bodyRef = useRef(null);
  const pageRef = useRef(null);

  const loadPage = useCallback(async (slug, anc = null, push = true) => {
    try {
      const p = await api.getHelpPage(slug);
      if (push && pageRef.current) setTrail((t) => [...t, pageRef.current.slug]);
      pageRef.current = p;
      setPage(p);
      setAnchor(anc);
      setTab('page');
    } catch (e) { toast.error(e.message); }
  }, []);

  const openContext = useCallback(async () => {
    const screen = getHelpScreen();
    try {
      const c = await api.getHelpContext(screen, openDialogTitle());
      await loadPage(c.page.slug, c.anchor, false);
      setTrail([]);
    } catch { setTab(tree ? 'toc' : 'ask'); }
  }, [loadPage, tree]);

  useEffect(() => {
    const onHelp = (e) => {
      const d = e.detail || {};
      setOpen(true);
      if (d.slug) loadPage(d.slug, d.anchor, false);
      else if (d.tab === 'ask') setTab('ask');
      else if (d.tab === 'toc') setTab('toc');
      else openContext();
      if (d.question) setQ(d.question);
    };
    const onKey = (e) => {
      if (e.key === 'F1') { e.preventDefault(); onHelp({ detail: {} }); }
      else if (e.key === 'Escape' && open && !document.querySelector('[role="dialog"][aria-modal="true"]')) setOpen(false);
    };
    window.addEventListener('recorion:help', onHelp);
    window.addEventListener('keydown', onKey);
    return () => { window.removeEventListener('recorion:help', onHelp); window.removeEventListener('keydown', onKey); };
  }, [open, openContext, loadPage]);

  useEffect(() => { if (open && !tree) api.getHelpTree().then(setTree).catch(() => setTree({ guides: [] })); }, [open, tree]);
  useEffect(() => {
    if (tab !== 'page' || !page) return;
    const el = anchor ? document.getElementById(`hp-${anchor}`) : null;
    if (el) el.scrollIntoView({ block: 'start' }); else bodyRef.current?.scrollTo({ top: 0 });
  }, [page, anchor, tab]);

  if (!open || !session.getToken()) return null;
  const area = (getHelpScreen().split('/')[0]) || 'workspace';

  const ask = async (text) => {
    const question = (text ?? q).trim();
    if (question.length < 3 || busy) return;
    setQ('');
    const history = chat.flatMap((m) => [{ role: 'user', content: m.q }, { role: 'assistant', content: m.a?.answer || '' }]);
    setChat((c) => [...c, { q: question, a: null }]);
    setBusy(true);
    try {
      const a = await api.askHelp({ question, history, screen: getHelpScreen() });
      setChat((c) => c.map((m, i) => (i === c.length - 1 ? { ...m, a } : m)));
    } catch (e) {
      setChat((c) => c.map((m, i) => (i === c.length - 1 ? { ...m, a: { answer: e.message, sources: [], error: true } } : m)));
    } finally { setBusy(false); }
  };

  return (
    <aside className={`hp-panel ${wide ? 'wide' : ''}`} aria-label="Yardım">
      <header className="hp-head">
        <strong><LifeBuoy size={16} /> Yardım</strong>
        <span className="hp-head-actions">
          <button type="button" className="ui-icon-btn" onClick={() => setWide((w) => !w)} title={wide ? 'Daralt' : 'Genişlet'}>{wide ? <Minimize2 size={15} /> : <Maximize2 size={15} />}</button>
          <button type="button" className="ui-icon-btn" onClick={() => setOpen(false)} aria-label="Yardımı kapat"><X size={16} /></button>
        </span>
      </header>
      <nav className="hp-tabs" role="tablist">
        <button type="button" role="tab" aria-selected={tab === 'ask'} className={tab === 'ask' ? 'active' : ''} onClick={() => setTab('ask')}><Sparkles size={14} /> RECAi'ye sor</button>
        <button type="button" role="tab" aria-selected={tab === 'page'} className={tab === 'page' ? 'active' : ''} onClick={openContext}><Compass size={14} /> Bu ekran</button>
        <button type="button" role="tab" aria-selected={tab === 'toc'} className={tab === 'toc' ? 'active' : ''} onClick={() => setTab('toc')}><BookOpen size={14} /> İçindekiler</button>
      </nav>

      <div className="hp-body" ref={bodyRef}>
        {tab === 'ask' && (
          <div className="hp-ask">
            {chat.length === 0 && (
              <div className="hp-intro">
                <p>Sorunuzu kendi cümlenizle yazın. RECAi, kullanım kılavuzundan ve <strong>yetkiniz dahilindeki</strong> ekranlardan yanıt verir; gerekirse sizi ilgili ekrana götürür.</p>
                {(EXAMPLES[area] || EXAMPLES.workspace).map((x) => <button key={x} type="button" className="hp-chip" onClick={() => ask(x)}>{x}</button>)}
              </div>
            )}
            {chat.map((m, i) => (
              <div key={i} className="hp-turn">
                <div className="hp-q">{m.q}</div>
                <div className={`hp-a ${m.a?.denied ? 'denied' : ''}`}>
                  {!m.a ? <span className="pj-hint">RECAi yanıt hazırlıyor…</span> : (
                    <>
                      {m.a.denied && <Badge tone="warning">Yetki dışı</Badge>}
                      <HelpMarkdown text={m.a.answer} />
                      {m.a.navigate && <Button size="sm" icon={ChevronRight} onClick={() => { navigateTo(m.a.navigate); }}>Ekrana git</Button>}
                      {m.a.sources?.length > 0 && (
                        <div className="hp-sources"><small>Dayandığı yardım sayfaları:</small>
                          {m.a.sources.map((s) => <button key={s.slug} type="button" className="hp-link" onClick={() => loadPage(s.slug)}>{s.guide_title} › {s.title}</button>)}
                        </div>
                      )}
                    </>
                  )}
                </div>
              </div>
            ))}
            <form className="hp-askbox" onSubmit={(e) => { e.preventDefault(); ask(); }}>
              <textarea className="ui-input" rows={2} value={q} placeholder="Örn. RECSlip'te muhasebe kriterini nasıl gevşetirim?" aria-label="RECAi'ye soru"
                onChange={(e) => setQ(e.target.value)} onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); ask(); } }} />
              <Button type="submit" icon={Send} disabled={busy || q.trim().length < 3}>Sor</Button>
            </form>
          </div>
        )}

        {tab === 'toc' && (
          <div className="hp-toc" aria-label="Yardım içindekiler">
            {!tree ? <p className="pj-hint">Yükleniyor…</p> : tree.guides.map((g) => (
              <details key={g.guide} open={tree.guides.length === 1 || g.guide === (area === 'super' ? 'merkez' : area === 'company' ? 'sirket' : 'workarea')}>
                <summary>{g.title}</summary>
                <ul>{g.pages.map((p) => (
                  <li key={p.slug} className={`lv${p.level}`}><button type="button" className="hp-link" onClick={() => loadPage(p.slug, null, false)}>{p.title}</button></li>
                ))}</ul>
              </details>
            ))}
          </div>
        )}

        {tab === 'page' && page && (
          <article className="hp-page">
            <div className="hp-crumb">
              {trail.length > 0 && <button type="button" className="ui-icon-btn" title="Geri" onClick={() => { const t = [...trail]; const prev = t.pop(); setTrail(t); loadPage(prev, null, false); }}><ArrowLeft size={14} /></button>}
              <small>{page.guide_title} › {page.section}{page.parent_page && page.parent_page.title !== page.section ? ` › ${page.parent_page.title}` : ''}</small>
            </div>
            <h2 className="hp-title">{page.title}</h2>
            {page.screens?.filter((k) => !k.endsWith('/')).slice(0, 1).map((k) => (
              <Button key={k} size="sm" variant="secondary" icon={ChevronRight} onClick={() => navigateTo(k)}>Bu ekranı aç</Button>))}
            <HelpMarkdown text={page.body} />
            {page.children?.length > 0 && (
              <ul className="hp-children">{page.children.map((c) => <li key={c.slug}><button type="button" className="hp-link" onClick={() => loadPage(c.slug)}>{c.title}</button></li>)}</ul>
            )}
          </article>
        )}
      </div>
    </aside>
  );
}
