import React, { useEffect, useRef, useState } from 'react';
import { Send, Sparkles } from 'lucide-react';
import { Button, Modal } from '../../ui/components';
import { toast } from '../../ui/feedback';
import './titleDesign.css';

const FIRST = 'Bu ünvanı kendi cümlelerinizle anlatın: ne iş yapacak, hangi çıktıları üretecek, kime teslim edecek, neyi asla yapmamalı? '
  + 'Ben eksikleri sorup iş tanımını, sorumlulukları, yetkinlikleri, başarı ölçütlerini ve rol promptunu hazırlayacağım. '
  + 'Hazır olunca "Forma al" ile forma aktarıp kaydedersiniz.';

/**
 * İSTEK #739: ünvanı sohbetle tanımlama paneli (Merkez katalog ve Şirket Yönetimi ortak).
 * send(messages, draft, context) → {reply, draft, ready}; onApply(draft) taslağı forma aktarır. Sohbet hiçbir şeyi kaydetmez.
 */
export default function TitleDesignChat({ open, onClose, send, onApply, initialDraft, context, scopeNote }) {
  const [messages, setMessages] = useState([]);
  const [draft, setDraft] = useState(initialDraft || {});
  const [ready, setReady] = useState(false);
  const [text, setText] = useState('');
  const [busy, setBusy] = useState(false);
  const endRef = useRef(null);

  useEffect(() => { if (open) { setMessages([]); setDraft(initialDraft || {}); setReady(false); setText(''); } }, [open]); // eslint-disable-line react-hooks/exhaustive-deps
  useEffect(() => { endRef.current?.scrollIntoView?.({ block: 'end' }); }, [messages, busy]);

  const submit = async () => {
    const msg = text.trim();
    if (!msg || busy) return;
    const next = [...messages, { role: 'user', content: msg }];
    setMessages(next); setText(''); setBusy(true);
    try {
      const r = await send(next, draft, context || {});
      setMessages([...next, { role: 'assistant', content: r.reply }]);
      setDraft(r.draft || draft); setReady(!!r.ready);
    } catch (e) {
      setMessages(next);
      toast.error(e.message);
    } finally { setBusy(false); }
  };

  const hasDraft = !!(draft.title || draft.description || draft.base_role_prompt);
  const list = (k, label) => (draft[k]?.length ? <div><strong>{label}</strong><ul>{draft[k].map((x, i) => <li key={i}>{x}</li>)}</ul></div> : null);

  return (
    <Modal open={open} onClose={onClose} size="lg" title="RECAi ile ünvan tanımla"
      footer={<><Button variant="secondary" onClick={onClose}>Kapat</Button>
        <Button onClick={() => { onApply(draft); onClose(); }} disabled={!hasDraft || busy}>{ready ? 'Forma al' : 'Taslağı forma al'}</Button></>}>
      <div className="td-wrap">
        <section className="td-chat" aria-label="Sohbet">
          <div className="td-msgs" role="log" aria-live="polite">
            <div className="td-msg td-ai"><Sparkles size={14} aria-hidden /> {FIRST}</div>
            {messages.map((m, i) => <div key={i} className={`td-msg ${m.role === 'user' ? 'td-user' : 'td-ai'}`}>{m.content}</div>)}
            {busy && <div className="td-msg td-ai td-busy">RECAi düşünüyor… (1–2 dk sürebilir)</div>}
            <div ref={endRef} />
          </div>
          <div className="td-input">
            <textarea className="ui-input" rows={3} value={text} maxLength={2000} aria-label="Mesajınız"
              placeholder="ör. Kliniğimizde randevu ve hasta hatırlatmalarını yönetecek, hastalarla nazik konuşacak bir asistan…"
              onChange={(e) => setText(e.target.value)}
              onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); submit(); } }} />
            <Button icon={Send} onClick={submit} disabled={busy || !text.trim()} aria-label="Gönder">Gönder</Button>
          </div>
          {scopeNote && <p className="pj-hint">{scopeNote}</p>}
        </section>
        <section className="td-draft" aria-label="Ünvan taslağı">
          <h4>Taslak {ready && <span className="td-ready">hazır</span>}</h4>
          {!hasDraft ? <p className="pj-hint">Anlattıkça taslak burada oluşur.</p> : (
            <>
              {draft.title && <div><strong>Ünvan</strong><p>{draft.title}</p></div>}
              {draft.description && <div><strong>İş tanımı</strong><p>{draft.description}</p></div>}
              {list('responsibilities', 'Sorumluluklar')}
              {list('required_skills', 'Yetkinlikler')}
              {list('kpis', 'Başarı ölçütleri')}
              {draft.base_role_prompt && <div><strong>Rol promptu</strong><pre className="td-prompt">{draft.base_role_prompt}</pre></div>}
            </>
          )}
        </section>
      </div>
    </Modal>
  );
}
