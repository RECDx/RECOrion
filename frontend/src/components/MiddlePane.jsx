import React, { useState, useRef, useEffect } from 'react';
import { 
  Send, 
  Bot, 
  User, 
  Sparkles, 
  Brain, 
  ChevronDown, 
  ChevronUp, 
  Lock, 
  Globe, 
  BookOpen, 
  Cpu, 
  CheckCircle,
  MessageSquare,
  Zap,
  ShieldCheck,
  RefreshCw,
  Paperclip
} from 'lucide-react';
import { api } from '../api';
import { toast } from '../ui/feedback';
import { Badge } from '../ui/components';
import { ACCEPT } from './docs/docMeta';
import SimpleMarkdown from './ai/SimpleMarkdown';
import './workarea.css';

const CLOSED = ['COMPLETED', 'CANCELLED'];

export default function MiddlePane({ 
  selectedTask, 
  messages, 
  onSendMessage, 
  isLoading,
  actors,
  liveThought,
  liveStatus,
  project,
  currentUser,
  flowTask,
}) {
  const assignee = actors?.find((a) => a.id === selectedTask?.assignee_actor_id);
  const readOnly = CLOSED.includes(project?.status);
  const [pending, setPending] = useState([]); // mesajla gönderilecek ekler (Proje Eklerine yüklenmiş)
  const [inputText, setInputText] = useState('');
  const [isPrivate, setIsPrivate] = useState(false);
  const [expandedThoughts, setExpandedThoughts] = useState({});
  const [uploading, setUploading] = useState(0);
  const messagesEndRef = useRef(null);
  const fileRef = useRef(null);

  // Mesaja eklenen dosyalar (Adım 8.3): Proje Eklerine yüklenir ve mesaja bağlanır; AI o mesajda dosyanın metnini okur,
  // proje yöneticisi onaylayınca projedeki AI personel kalıcı olarak öğrenir
  const attachFiles = async (files) => {
    const list = [...(files || [])].slice(0, Math.max(0, 5 - pending.length));
    if (files?.length > list.length) toast.warning('Bir mesaja en fazla 5 dosya eklenebilir.');
    if (!list.length || !selectedTask?.project_id) return;
    setUploading(list.length);
    for (const file of list) {
      const fd = new FormData();
      fd.append('file', file);
      try {
        const doc = await api.uploadProjectDocument(selectedTask.project_id, fd);
        setPending((p) => [...p, { id: doc.id, name: doc.original_name || file.name }]);
      } catch (err) {
        toast.error(`${file.name}: ${err.message}`);
      }
      setUploading((n) => n - 1);
    }
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading, liveThought]);

  const toggleThought = (msgId) => {
    setExpandedThoughts((prev) => ({
      ...prev,
      [msgId]: !prev[msgId]
    }));
  };

  const handleSend = async (e) => {
    e.preventDefault();
    if (!inputText.trim() || isLoading || uploading) return;
    const text = inputText;
    setInputText('');
    const ok = await onSendMessage({ content: text, isPrivate, attachments: pending });
    if (ok === false) setInputText(text); // gönderilemezse yazılan kaybolmaz
    else setPending([]);
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend(e);
    }
  };

  return (
    <main className="pane" style={{ background: 'var(--sf-0a0d14)' }}>
      {/* Pane Header: Task & Selected AI Agent Context */}
      <div className="pane-header" style={{ padding: '10px 18px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div style={{
            width: '32px',
            height: '32px',
            borderRadius: '8px',
            background: 'linear-gradient(135deg, rgba(99, 102, 241, 0.3) 0%, rgba(6, 182, 212, 0.3) 100%)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            border: '1px solid rgba(99, 102, 241, 0.3)'
          }}>
            <Bot size={18} color="var(--ac-818cf8)" />
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span style={{ fontSize: '0.9rem', fontWeight: '700' }}>
                {selectedTask?.title || 'Lütfen sol panelden bir görev seçin'}
              </span>
              <span className="badge badge-ai" style={{ fontSize: '0.65rem' }}>
                {assignee?.display_name || 'Atanmadı'}
              </span>
              {liveStatus && (
                <span className={`live-dot live-${liveStatus}`} role="status"
                  title={liveStatus === 'live' ? 'Canlı: yeni mesajlar ve AI adımları anında görünür' : 'Canlı bağlantı kuruluyor…'}>
                  {liveStatus === 'live' ? 'Canlı' : 'Bağlanıyor…'}
                </span>
              )}
            </div>
            {selectedTask && (
              <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>
                Durum: <b>{flowTask?.status_label || selectedTask.status}</b>
                {flowTask?.approver && <> · Onaylayıcı: <b>{flowTask.approver.name}</b></>}
                {' · '}Yanıtlar proje ekleri, personel bilgisi ve kurum hafızasıyla verilir
              </div>
            )}
          </div>
        </div>

        {/* AI personelin unvanına göre atanmış modeli (sohbette değiştirilmez; Şirket Yönetimi > AI Personel) */}
        {assignee?.actor_type === 'AI_AGENT' && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.72rem', color: 'var(--text-dim)' }}
            title="Model, AI personelin ayarlarından Şirket Yönetimi'nde değiştirilir.">
            <Cpu size={13} />
            <span>Model: <b style={{ color: 'var(--ac-38bdf8)', fontFamily: 'var(--font-mono)' }}>{assignee.preferred_model_code || 'şirket varsayılanı'}</b></span>
          </div>
        )}
      </div>

      {/* Messages Stream (Gemini Web Persistent Chat) */}
      <div className="pane-content" style={{ padding: '20px 24px' }}>
        {(!messages || messages.length === 0) ? (
          <div style={{
            margin: 'auto',
            textAlign: 'center',
            maxWidth: '480px',
            padding: '30px',
            borderRadius: '16px',
            background: 'rgb(var(--rgb-ov) / 0.02)',
            border: '1px dashed var(--border-subtle)'
          }}>
            <Sparkles size={36} color="var(--ac-818cf8)" style={{ marginBottom: '12px' }} />
            <h3 style={{ fontSize: '1rem', fontWeight: '700', marginBottom: '6px' }}>
              RECOrion Otonom Çalışma Alanı
            </h3>
            <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', lineHeight: 1.6 }}>
              Bu görevde atanan AI personeli ile mesajlaşmaya başlayabilirsiniz.
              Konuşmalarınız, akıl yürütme adımları ve kurumsal hafıza atıfları kalıcı olarak saklanır.
            </p>
          </div>
        ) : (
          messages.map((m, idx) => {
            const isUser = m.role === 'user';
            const isA2A = m.message_type === 'AGENT_TO_AGENT';
            const isThoughtOpen = expandedThoughts[m.id || idx];

            return (
              <div 
                key={m.id || idx}
                className={`chat-bubble ${isUser ? 'chat-bubble-user' : isA2A ? 'chat-bubble-a2a' : 'chat-bubble-ai'}`}
              >
                {/* Message Header */}
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                    {isUser ? (
                      <span style={{ fontWeight: '700', fontSize: '0.78rem', color: 'var(--ac-818cf8)', display: 'flex', alignItems: 'center', gap: '4px' }}>
                        <User size={13} />
                        {m.sender_actor_id && m.sender_actor_id === currentUser?.actor_id ? `${m.sender_name || 'Siz'} (siz)` : (m.sender_name || 'Kullanıcı')}
                      </span>
                    ) : isA2A ? (
                      <span style={{ fontWeight: '700', fontSize: '0.78rem', color: 'var(--ac-c084fc)', display: 'flex', alignItems: 'center', gap: '4px' }}>
                        <Zap size={13} />
                        🤖 Ajanlar Arası Müzakere
                      </span>
                    ) : (
                      <span style={{ fontWeight: '700', fontSize: '0.78rem', color: 'var(--ac-38bdf8)', display: 'flex', alignItems: 'center', gap: '4px' }}>
                        <Bot size={13} />
                        {m.sender_name || 'RECAi'}
                      </span>
                    )}

                    {m.is_private && <Badge tone="warning"><Lock size={10} /> Yalnızca siz görüyorsunuz</Badge>}
                  </div>

                  <span style={{ fontSize: '0.68rem', color: 'var(--text-dim)' }}>
                    {m.created_at ? new Date(m.created_at).toLocaleTimeString('tr-TR', { hour: '2-digit', minute: '2-digit' }) : ''}
                  </span>
                </div>

                {/* Gemini Web-Like Thought Process Accordion */}
                {m.thought_process && (
                  <div className="thought-box">
                    <div className="thought-header" onClick={() => toggleThought(m.id || idx)}>
                      <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                        <Brain size={13} />
                        Düşünce Süreci (Thought Process)
                      </span>
                      {isThoughtOpen ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                    </div>
                    {isThoughtOpen && (
                      <div className="thought-content">
                        {m.thought_process}
                      </div>
                    )}
                  </div>
                )}

                {/* Mesaj metni: kullanıcı yazdığı gibi, AI yanıtı Markdown olarak (güvenli, HTML üretmez) */}
                {isUser ? (
                  <div style={{ whiteSpace: 'pre-wrap', lineHeight: 1.6 }}>{m.content}</div>
                ) : (
                  <div style={{ lineHeight: 1.6 }}><SimpleMarkdown text={m.content || ''} /></div>
                )}

                {/* Mesaj ekleri (Adım 8.3) */}
                {m.attachments?.length > 0 && (
                  <div className="wa-chips" style={{ marginTop: '8px' }}>
                    {m.attachments.map((a) => (
                      <button key={a.document_id} type="button" className="wa-chip" title={`${a.name} dosyasını indir`}
                        onClick={() => api.downloadDocument(a.document_id, a.name).catch((err) => toast.error(err.message))}>
                        <Paperclip size={11} /><span>{a.name}</span>
                      </button>
                    ))}
                  </div>
                )}

                {/* Citations & Memory Chips */}
                {m.citations && m.citations.length > 0 && (
                  <div style={{ marginTop: '10px', paddingTop: '8px', borderTop: '1px solid rgb(var(--rgb-ov) / 0.06)' }}>
                    <div style={{ fontSize: '0.68rem', color: 'var(--text-dim)', marginBottom: '4px', display: 'flex', alignItems: 'center', gap: '4px' }}>
                      <BookOpen size={11} /> 2 Kademeli Kolektif Hafıza Kaynakları:
                    </div>
                    <div style={{ display: 'flex', flexWrap: 'wrap' }}>
                      {m.citations.map((c, cIdx) => (
                        <span key={cIdx} className="citation-chip">
                          <Globe size={10} />
                          [{c.scope}]: {c.content?.slice(0, 45)}...
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            );
          })
        )}

        {/* Canlı düşünce adımı (Adım 8.2): AI'ın o an ne yaptığı; arka plandaki iş adımı çalışmaları da görünür */}
        {(isLoading || liveThought) && (
          <div className="chat-bubble chat-bubble-ai thinking-pulse" role="status" aria-live="polite" style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <Brain size={18} color="var(--ac-818cf8)" />
            <span style={{ fontSize: '0.85rem', color: 'var(--ac-c084fc)', fontWeight: '600' }}>
              {liveThought || 'Mesaj gönderiliyor…'}
            </span>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Rich Input Bar */}
      {readOnly ? (
        <div className="wa-readonly" role="note">
          <Lock size={13} /> Proje {project?.status === 'CANCELLED' ? 'iptal edildi' : 'tamamlandı'}; yazışma kaydı salt okunurdur ve değiştirilemez.
        </div>
      ) : (
      <div style={{
        padding: '14px 20px',
        borderTop: '1px solid var(--border-subtle)',
        background: 'rgb(var(--rgb-sf-0a0e18) / 0.85)',
        backdropFilter: 'blur(10px)'
      }}>
        <form onSubmit={handleSend}>
          {/* Options above textarea */}
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px', fontSize: '0.72rem' }}>
            <label style={{ display: 'flex', alignItems: 'center', gap: '6px', cursor: 'pointer', color: 'var(--text-muted)' }}>
              <input 
                type="checkbox" 
                checked={isPrivate} 
                onChange={(e) => setIsPrivate(e.target.checked)}
                style={{ cursor: 'pointer' }}
              />
              <span>Özel mesaj (soru ve yanıtı yalnızca siz görürsünüz)</span>
            </label>

            <span style={{ color: 'var(--text-dim)' }}>
              Enter: Gönder • Shift+Enter: Yeni Satır
            </span>
          </div>

          {pending.length > 0 && (
            <div className="wa-chips" style={{ marginBottom: '8px' }} aria-label="Mesaja eklenecek dosyalar">
              {pending.map((a) => (
                <span key={a.id} className="wa-chip">
                  <Paperclip size={11} /><span>{a.name}</span>
                  <button type="button" className="wa-chip-remove" aria-label={`${a.name} ekini kaldır`}
                    onClick={() => setPending((p) => p.filter((x) => x.id !== a.id))}>×</button>
                </span>
              ))}
            </div>
          )}
          <div style={{
            display: 'flex',
            gap: '10px',
            alignItems: 'flex-end',
            background: 'var(--bg-input)',
            borderRadius: '12px',
            padding: '8px 12px',
            border: '1px solid var(--border-subtle)',
            transition: 'border-color 0.2s'
          }}>
            <button
              type="button"
              className="ui-icon-btn"
              aria-label="Dosya veya görsel ekle"
              title="Dosya veya görsel ekle (mesaja bağlanır ve Proje Eklerine yüklenir)"
              disabled={!selectedTask || uploading > 0}
              onClick={() => fileRef.current?.click()}
            >
              {uploading ? <RefreshCw size={15} className="spin" /> : <Paperclip size={15} />}
            </button>
            <input ref={fileRef} type="file" multiple accept={ACCEPT} hidden onChange={(e) => { attachFiles(e.target.files); e.target.value = ''; }} />
            <textarea
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={selectedTask ? `${selectedTask.title} hakkında AI personeline talimat verin...` : "Lütfen bir görev seçin..."}
              rows={2}
              disabled={!selectedTask || isLoading}
              style={{
                flex: 1,
                background: 'transparent',
                border: 'none',
                color: 'var(--nt-f8fafc)',
                fontSize: '0.875rem',
                fontFamily: 'var(--font-sans)',
                resize: 'none',
                outline: 'none',
                lineHeight: 1.5
              }}
            />

            <button
              type="submit"
              disabled={!inputText.trim() || isLoading || !selectedTask || uploading > 0}
              className="btn btn-primary"
              style={{
                padding: '8px 16px',
                borderRadius: '8px',
                opacity: (!inputText.trim() || isLoading || !selectedTask) ? 0.5 : 1
              }}
            >
              <Send size={15} />
              Gönder
            </button>
          </div>
        </form>
      </div>
      )}
    </main>
  );
}
