import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { ChevronDown, ChevronRight, Download, FileCode2, Folder, FolderOpen, Search, X } from 'lucide-react';
// Monaco (VS Code'un editörü) yerel paketten; yalnız sözdizimi renklendirme dilleri + temel editör işçisi (CDN yok)
import * as monaco from 'monaco-editor/esm/vs/editor/edcore.main';
import 'monaco-editor/esm/vs/basic-languages/monaco.contribution';
import EditorWorker from 'monaco-editor/esm/vs/editor/editor.worker?worker';
import { api } from '../../api';
import { Badge, Button, EmptyState, Modal } from '../../ui/components';
import { toast } from '../../ui/feedback';
import './CodeExplorer.css';

globalThis.MonacoEnvironment = { getWorker: () => new EditorWorker() };

/** Dosya uzantısından Monaco dili (bilinmeyen: düz metin). */
function languageOf(path) {
  const name = path.split('/').pop().toLowerCase();
  const ext = name.includes('.') ? `.${name.split('.').pop()}` : '';
  const hit = monaco.languages.getLanguages().find((l) => (l.filenames || []).map((f) => f.toLowerCase()).includes(name)
    || (ext && (l.extensions || []).includes(ext)));
  return hit ? hit.id : 'plaintext';
}

/** RECOrion teması (html[data-theme]) → Monaco teması; tema değişince güncellenir. */
function useMonacoTheme() {
  useEffect(() => {
    const apply = () => monaco.editor.setTheme(document.documentElement.getAttribute('data-theme') === 'light' ? 'vs' : 'vs-dark');
    apply();
    const obs = new MutationObserver(apply);
    obs.observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] });
    return () => obs.disconnect();
  }, []);
}

const EDITOR_OPTIONS = { readOnly: true, domReadOnly: true, automaticLayout: true, minimap: { enabled: true }, lineNumbers: 'on',
  scrollBeyondLastLine: false, fontSize: 13, renderWhitespace: 'selection', wordWrap: 'off' };

/** Düz dosya listesinden ağaç: { name, path, type, children } */
function buildTree(entries) {
  const root = { children: new Map() };
  for (const e of entries) {
    const parts = e.path.split('/');
    let node = root;
    parts.forEach((part, i) => {
      const path = parts.slice(0, i + 1).join('/');
      const isLeaf = i === parts.length - 1;
      if (!node.children.has(part)) node.children.set(part, { name: part, path, type: isLeaf ? e.type : 'tree', children: new Map() });
      node = node.children.get(part);
    });
  }
  const sort = (n) => [...n.children.values()]
    .sort((a, b) => (a.type === b.type ? a.name.localeCompare(b.name, 'tr') : a.type === 'tree' ? -1 : 1))
    .map((c) => ({ ...c, children: sort(c) }));
  return sort(root);
}

function TreeNodes({ nodes, depth, expanded, toggle, onOpen, activePath }) {
  return nodes.map((n) => {
    const open = expanded.has(n.path);
    const isDir = n.type === 'tree';
    return (
      <li key={n.path} role="treeitem" aria-expanded={isDir ? open : undefined} aria-selected={n.path === activePath}>
        <button type="button" className={`cx-node${n.path === activePath ? ' active' : ''}`} style={{ paddingLeft: 8 + depth * 14 }}
          onClick={() => (isDir ? toggle(n.path) : onOpen(n.path))} title={n.path}>
          {isDir ? (open ? <ChevronDown size={13} /> : <ChevronRight size={13} />) : <span className="cx-node-pad" />}
          {isDir ? (open ? <FolderOpen size={14} /> : <Folder size={14} />) : <FileCode2 size={14} />}
          <span className="cx-node-name">{n.name}</span>
        </button>
        {isDir && open && n.children.length > 0 && (
          <ul role="group"><TreeNodes nodes={n.children} depth={depth + 1} expanded={expanded} toggle={toggle} onOpen={onOpen} activePath={activePath} /></ul>
        )}
      </li>
    );
  });
}

/**
 * Kod Gezgini (ADIM 16.1, #609): VS Code benzeri salt okuma görünüm.
 * Sol: dal seçimi, arama, dosya ağacı · Orta: sekmeler + Monaco (renklendirme, satır no, küçük harita) · Zip indirme.
 * initial: { path, ref, line? } — Adımlar görünümünden gelinirse o dosya açılır.
 */
export default function CodeExplorer({ project, initial }) {
  useMonacoTheme();
  const [refs, setRefs] = useState([]);
  const [ref, setRef] = useState(initial?.ref || 'main');
  const [tree, setTree] = useState(null);
  const [expanded, setExpanded] = useState(() => new Set());
  const [tabs, setTabs] = useState([]); // { key, path, ref }
  const [active, setActive] = useState(null);
  const [query, setQuery] = useState('');
  const [results, setResults] = useState(null);
  const [searching, setSearching] = useState(false);
  const [downloading, setDownloading] = useState(false);
  const hostRef = useRef(null);
  const editorRef = useRef(null);
  const modelsRef = useRef(new Map()); // key → { model, viewState }
  const pendingLine = useRef(null);

  useEffect(() => { api.getRepositoryRefs(project.id).then(setRefs).catch((e) => toast.error(e.message)); }, [project.id]);
  useEffect(() => {
    api.getRepositoryTree(project.id, ref).then(setTree).catch((e) => { setTree({ entries: [], error: e.message }); });
  }, [project.id, ref]);

  // Editör bir kez kurulur; sekme değişince modeli değişir (görünüm durumu korunur)
  useEffect(() => {
    editorRef.current = monaco.editor.create(hostRef.current, { ...EDITOR_OPTIONS, model: null });
    const models = modelsRef.current;
    return () => {
      editorRef.current?.dispose();
      models.forEach(({ model }) => model.dispose());
      models.clear();
    };
  }, []);

  const showTab = useCallback(async (tab, line) => {
    const ed = editorRef.current;
    if (!ed) return;
    const prev = ed.getModel();
    if (prev) {
      const prevEntry = [...modelsRef.current.values()].find((m) => m.model === prev);
      if (prevEntry) prevEntry.viewState = ed.saveViewState();
    }
    let entry = modelsRef.current.get(tab.key);
    if (!entry) {
      try {
        const data = await api.getRepositoryFile(project.id, tab.ref, tab.path);
        entry = { model: monaco.editor.createModel(data.content, languageOf(tab.path)), viewState: null };
        modelsRef.current.set(tab.key, entry);
      } catch (e) {
        toast.error(e.message);
        return;
      }
    }
    ed.setModel(entry.model);
    // Doküman (md/düz metin) satır kaydırmalı; kod kaydırmasız
    ed.updateOptions({ wordWrap: ['markdown', 'plaintext'].includes(entry.model.getLanguageId()) ? 'on' : 'off' });
    if (entry.viewState) ed.restoreViewState(entry.viewState);
    if (line) {
      ed.revealLineInCenter(line);
      ed.setSelection(new monaco.Selection(line, 1, line, entry.model.getLineMaxColumn(line)));
    }
    ed.focus();
  }, [project.id]);

  const openFile = useCallback((path, line, atRef = ref) => {
    const key = `${atRef}:${path}`;
    pendingLine.current = line || null;
    setTabs((t) => (t.some((x) => x.key === key) ? t : [...t, { key, path, ref: atRef }]));
    setActive(key);
    // Klasörleri aç
    setExpanded((s) => {
      const n = new Set(s);
      path.split('/').slice(0, -1).forEach((_, i, arr) => n.add(arr.slice(0, i + 1).join('/')));
      return n;
    });
  }, [ref]);

  useEffect(() => {
    const tab = tabs.find((t) => t.key === active);
    if (tab) showTab(tab, pendingLine.current);
    else editorRef.current?.setModel(null);
    pendingLine.current = null;
  }, [active, tabs, showTab]);

  const openedInitial = useRef(null);
  useEffect(() => {
    if (initial?.path && openedInitial.current !== initial) {
      openedInitial.current = initial;
      openFile(initial.path, initial.line, initial.ref || 'main');
    }
  }, [initial, openFile]);

  const closeTab = (key) => {
    const entry = modelsRef.current.get(key);
    setTabs((t) => {
      const rest = t.filter((x) => x.key !== key);
      if (active === key) setActive(rest.length ? rest[rest.length - 1].key : null);
      return rest;
    });
    if (entry) {
      if (editorRef.current?.getModel() === entry.model) editorRef.current.setModel(null);
      entry.model.dispose();
      modelsRef.current.delete(key);
    }
  };

  const toggle = (path) => setExpanded((s) => { const n = new Set(s); if (n.has(path)) n.delete(path); else n.add(path); return n; });
  const nodes = useMemo(() => buildTree(tree?.entries || []), [tree]);
  const activeTab = tabs.find((t) => t.key === active);

  const runSearch = async (e) => {
    e.preventDefault();
    const q = query.trim();
    if (q.length < 2) { setResults(null); return; }
    setSearching(true);
    try { setResults(await api.searchRepository(project.id, ref, q)); } catch (err) { toast.error(err.message); } finally { setSearching(false); }
  };
  const download = async () => {
    setDownloading(true);
    try { await api.downloadRepositoryArchive(project.id, ref); } catch (e) { toast.error(e.message); } finally { setDownloading(false); }
  };
  const refLabel = (r) => (r.name === 'main' ? 'main (ana dal)' : r.task_title ? `${r.order_index ? `${r.order_index}. ` : ''}${r.task_title}` : r.name);

  return (
    <div className="cx-root">
      <div className="cx-toolbar">
        <label className="cx-ref">
          <span className="pj-hint">Dal</span>
          <select className="ui-input" aria-label="Dal veya iş adımı seçimi" value={ref} onChange={(e) => { setTree(null); setResults(null); setRef(e.target.value); }}>
            {(refs.length ? refs : [{ name: ref }]).map((r) => <option key={r.name} value={r.name}>{refLabel(r)}</option>)}
          </select>
        </label>
        <form className="cx-search" onSubmit={runSearch} role="search">
          <input className="ui-input" value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Dosya adı veya kod ara…"
            aria-label="Depoda ara" maxLength={100} />
          <Button type="submit" size="sm" variant="secondary" icon={Search} disabled={searching || query.trim().length < 2}>
            {searching ? 'Aranıyor…' : 'Ara'}
          </Button>
        </form>
        <Button size="sm" variant="ghost" icon={Download} disabled={downloading} onClick={download}>{downloading ? 'İndiriliyor…' : 'Zip indir'}</Button>
      </div>

      <div className="cx-body">
        <aside className="cx-side" aria-label="Dosyalar">
          {results ? (
            <div className="cx-results">
              <div className="cx-results-head">
                <span className="pj-hint">"{results.q}": {results.files.length} dosya adı, {results.matches.length} satır{results.truncated ? ' (ilk 200)' : ''}</span>
                <button type="button" className="ui-icon-btn" aria-label="Aramayı kapat" onClick={() => setResults(null)}><X size={14} /></button>
              </div>
              <ul className="cx-hitlist">
                {results.files.map((p) => (
                  <li key={`f:${p}`}><button type="button" className="cx-hit" onClick={() => openFile(p)}><FileCode2 size={13} /><span>{p}</span></button></li>
                ))}
                {results.matches.map((m) => (
                  <li key={`m:${m.path}:${m.line}`}>
                    <button type="button" className="cx-hit" onClick={() => openFile(m.path, m.line)}>
                      <span className="cx-hit-path">{m.path}:{m.line}</span>
                      <code className="cx-hit-text">{m.text}</code>
                    </button>
                  </li>
                ))}
                {!results.files.length && !results.matches.length && <li className="pj-hint cx-pad">Sonuç yok.</li>}
              </ul>
            </div>
          ) : !tree ? <p className="pj-hint cx-pad">Yükleniyor…</p> : tree.error ? <p className="ui-text-danger cx-pad">{tree.error}</p> : (
            <ul className="cx-tree" role="tree" aria-label="Depo dosya ağacı">
              <TreeNodes nodes={nodes} depth={0} expanded={expanded} toggle={toggle} onOpen={(p) => openFile(p)} activePath={activeTab?.ref === ref ? activeTab?.path : null} />
            </ul>
          )}
          {tree?.truncated && <p className="pj-hint cx-pad">Depo çok büyük; ilk 2000 kayıt gösteriliyor.</p>}
        </aside>

        <section className="cx-main" aria-label="Kod görüntüleyici">
          <div className="cx-tabs" role="tablist" aria-label="Açık dosyalar">
            {tabs.map((t) => (
              <div key={t.key} className={`cx-tab${t.key === active ? ' active' : ''}`} role="tab" aria-selected={t.key === active} title={`${t.path} · ${t.ref}`}>
                <button type="button" className="cx-tab-name" onClick={() => setActive(t.key)}>
                  {t.path.split('/').pop()}{t.ref !== ref && <small className="cx-tab-ref">{t.ref.slice(0, 18)}</small>}
                </button>
                <button type="button" className="cx-tab-close" aria-label={`${t.path} sekmesini kapat`} onClick={() => closeTab(t.key)}><X size={12} /></button>
              </div>
            ))}
            {activeTab && <span className="cx-tab-info pj-hint"><Badge tone="neutral">Salt okuma</Badge> {activeTab.path}</span>}
          </div>
          <div className="cx-editor-wrap">
            <div ref={hostRef} className="cx-editor" />
            {!activeTab && (
              <div className="cx-empty">
                <EmptyState icon={FileCode2} title="Dosya seçin" description="Soldaki ağaçtan ya da arama sonuçlarından bir dosya açın. Kod salt okunur; değişiklikler AI personelin iş adımlarıyla yapılır." />
              </div>
            )}
          </div>
        </section>
      </div>
    </div>
  );
}

/** Bir iş adımında dosyanın farkı: adımın ayrıldığı nokta (base) ↔ adımın son hâli (head). Silinen/yeni dosyada karşı taraf boş. */
export function DiffModal({ project, file, onClose }) {
  useMonacoTheme();
  const hostRef = useRef(null);
  const [state, setState] = useState('loading');
  useEffect(() => {
    let editor = null;
    let models = [];
    let cancelled = false;
    const get = (sha) => (sha ? api.getRepositoryFile(project.id, sha, file.path).then((d) => d.content).catch(() => '') : Promise.resolve(''));
    Promise.all([get(file.status === 'added' ? null : file.base), file.status === 'deleted' ? Promise.resolve('') : get(file.head)]).then(([a, b]) => {
      if (cancelled || !hostRef.current) return;
      const lang = languageOf(file.path);
      models = [monaco.editor.createModel(a, lang), monaco.editor.createModel(b, lang)];
      editor = monaco.editor.createDiffEditor(hostRef.current, { ...EDITOR_OPTIONS, renderSideBySide: window.innerWidth > 900, originalEditable: false });
      editor.setModel({ original: models[0], modified: models[1] });
      setState('ready');
    });
    return () => { cancelled = true; editor?.dispose(); models.forEach((m) => m.dispose()); };
  }, [project.id, file]);
  return (
    <Modal open onClose={onClose} title={`Fark: ${file.path}`} size="lg">
      <p className="pj-hint">Sol: adım başlamadan önce · Sağ: {file.title ? `"${file.title}" adımının` : 'adımın'} son hâli{state === 'loading' ? ' · yükleniyor…' : ''}</p>
      <div ref={hostRef} className="cx-diff" />
    </Modal>
  );
}
