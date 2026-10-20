import React, { useEffect, useRef, useState } from 'react';
import { Send } from 'lucide-react';
import { Button, EmptyState } from '../../ui/components';
import { toast } from '../../ui/feedback';
import { fmtDate, fmtPrecise } from './format';
import SimpleMarkdown from './SimpleMarkdown';
import './ai.css';

/**
 * Basit sohbet paneli (Beyin AI ve Süper Yönetici asistanı).
 * loadHistory(): Promise<message[]>; send(content): Promise<{ message, model_code, credits }>
 */
export default function ChatPanel({ loadHistory, send, icon, emptyTitle, emptyText, suggestions = [], placeholder }) {
  const [messages, setMessages] = useState([]);
  const [draft, setDraft] = useState('');
  const [busy, setBusy] = useState(false);
  const [loaded, setLoaded] = useState(false);
  const logRef = useRef(null);

  useEffect(() => {
    let alive = true;
    loadHistory()
      .then((rows) => alive && setMessages(rows))
      .catch((e) => toast.error(e.message))
      .finally(() => alive && setLoaded(true));
    return () => { alive = false; };
  }, [loadHistory]);

  useEffect(() => {
    logRef.current?.scrollTo({ top: logRef.current.scrollHeight, behavior: 'smooth' });
  }, [messages, busy]);

  const submit = async (text) => {
    const content = (text ?? draft).trim();
    if (!content || busy) return;
    setDraft('');
    setBusy(true);
    const pending = { id: `local-${Date.now()}`, role: 'user', content, created_at: new Date().toISOString() };
    setMessages((m) => [...m, pending]);
    try {
      const res = await send(content);
      setMessages((m) => [...m, { ...res.message, model_code: res.model_code, credits: res.credits }]);
    } catch (e) {
      // Yanıt alınamadıysa soru kaydedilmez; kullanıcı tekrar deneyebilsin diye metni geri koy
      setMessages((m) => m.filter((x) => x.id !== pending.id));
      setDraft(content);
      toast.error(e.message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="ai-chat">
      <div className="ai-chat-log" ref={logRef}>
        {loaded && messages.length === 0 && (
          <EmptyState icon={icon} title={emptyTitle} description={emptyText} action={suggestions.length > 0 && (
            <div className="ai-suggestions">
              {suggestions.map((s) => <button key={s} type="button" className="ai-chip" onClick={() => submit(s)}>{s}</button>)}
            </div>
          )} />
        )}
        {messages.map((m) => (
          <div key={m.id} className={`ai-msg ${m.role === 'user' ? 'ai-msg-user' : 'ai-msg-assistant'}`}>
            {m.role === 'user' ? m.content : <SimpleMarkdown text={m.content} />}
            <div className="ai-msg-meta">
              {fmtDate(m.created_at)}
              {m.model_code ? ` · ${m.model_code}` : ''}
              {m.credits ? ` · ${fmtPrecise(m.credits)} kredi` : ''}
            </div>
          </div>
        ))}
        {busy && <div className="ai-typing">Yanıt hazırlanıyor…</div>}
      </div>
      <form className="ai-chat-input" onSubmit={(e) => { e.preventDefault(); submit(); }}>
        <textarea
          className="ui-input"
          rows={2}
          value={draft}
          maxLength={8000}
          placeholder={placeholder}
          onChange={(e) => setDraft(e.target.value)}
          onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); submit(); } }}
          aria-label="Mesaj"
        />
        <Button type="submit" icon={Send} disabled={busy || !draft.trim()}>Gönder</Button>
      </form>
    </div>
  );
}
