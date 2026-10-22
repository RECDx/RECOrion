import React, { useEffect, useState } from 'react';
import { CheckCircle2, RotateCcw, ShieldCheck } from 'lucide-react';
import { api } from '../../api';
import { Badge, Button, Card } from '../../ui/components';
import ThemeToggle from '../../ui/ThemeToggle';
import SimpleMarkdown from '../ai/SimpleMarkdown';
import '../projects/projects.css';

function tokenFromHash() {
  return new URLSearchParams(window.location.hash.split('?')[1] || '').get('token') || '';
}
const fmt = (d) => (d ? new Date(d).toLocaleString('tr-TR', { day: '2-digit', month: 'long', hour: '2-digit', minute: '2-digit' }) : '—');

/** E-posta/Telegram'daki tek kullanımlık bağlantıyla açılan onay sayfası (ADIM 7.3). Giriş gerektirmez. */
export default function ApprovePage({ onDone }) {
  const [token] = useState(tokenFromHash);
  const [data, setData] = useState(null);
  const [error, setError] = useState('');
  const [note, setNote] = useState('');
  const [busy, setBusy] = useState(false);
  const [done, setDone] = useState(null);

  useEffect(() => {
    api.getApproval(token).then(setData).catch((e) => setError(e.message));
  }, [token]);

  const decide = async (approve) => {
    if (!approve && !note.trim()) return setError('Revizyon isterken gerekçeyi yazın; personel buna göre düzeltecek.');
    setBusy(true);
    setError('');
    try {
      await api.decideApproval(token, approve, note.trim());
      setDone(approve ? 'approved' : 'revision');
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div style={{ minHeight: '100dvh', padding: '32px 16px', display: 'flex', justifyContent: 'center', background: 'var(--bg-dark)' }}>
      <div style={{ position: 'fixed', top: 16, right: 16 }}><ThemeToggle compact /></div>
      <div style={{ width: 'min(100%, 860px)', display: 'flex', flexDirection: 'column', gap: 16 }}>
        <div className="pj-sub"><ShieldCheck size={16} /> RECOrion · İş adımı onayı</div>
        {done ? (
          <Card title={done === 'approved' ? 'Onaylandı' : 'Revizyon istendi'}>
            <p className="pj-hint">{done === 'approved'
              ? 'Kararınız iş akışına iletildi; sonraki adımlar başlayacak.'
              : 'Gerekçeniz personele iletildi; düzeltilmiş sürüm yeniden onayınıza gelecek.'}</p>
            <Button style={{ marginTop: 12 }} onClick={onDone}>RECOrion'a git</Button>
          </Card>
        ) : !data ? (
          <Card title={error ? 'Bağlantı kullanılamıyor' : 'Yükleniyor…'}>
            {error && <p className="pj-note medium">{error}</p>}
            {error && <Button style={{ marginTop: 12 }} variant="secondary" onClick={onDone}>RECOrion'a git</Button>}
          </Card>
        ) : (
          <>
            <Card title={data.task_title} subtitle={`${data.project_name} · teslim: ${fmt(data.submitted_at)}`}
              actions={data.rejection_count > 0 && <Badge tone="warning">Ret: {data.rejection_count} / {data.max_rejections}</Badge>}>
              <div className="pj-meta">
                <span>Personel: {data.assignee || '—'}</span>
                <span>Onaylayıcı: {data.approver}</span>
                <span>Bağlantı geçerliliği: {fmt(data.expires_at)}</span>
              </div>
              {data.description && <p className="pj-hint" style={{ marginTop: 10 }}>{data.description}</p>}
              {data.acceptance_criteria && <p className="pj-note info" style={{ marginTop: 10 }}>Kabul ölçütü: {data.acceptance_criteria}</p>}
            </Card>
            {data.artifact && (
              <Card title={`Çıktı · sürüm ${data.artifact.version}`}>
                <div style={{ maxHeight: '55vh', overflowY: 'auto' }}><SimpleMarkdown text={data.artifact.content || '(boş)'} /></div>
              </Card>
            )}
            <Card title="Kararınız">
              <div className="pj-field">
                <label htmlFor="ap-note">Not (revizyon için gerekçe zorunlu)</label>
                <textarea id="ap-note" className="ui-input" rows={3} value={note} onChange={(e) => setNote(e.target.value)}
                  placeholder="Neyin düzeltilmesi gerektiğini yazın…" />
              </div>
              {error && <p className="ui-text-danger" style={{ fontSize: '0.85rem' }}>{error}</p>}
              <div className="pj-actions" style={{ marginTop: 10 }}>
                <Button variant="success" icon={CheckCircle2} onClick={() => decide(true)} disabled={busy}>Onayla</Button>
                <Button variant="secondary" icon={RotateCcw} onClick={() => decide(false)} disabled={busy}>Revizyon iste</Button>
              </div>
              <p className="pj-hint" style={{ marginTop: 10 }}>Bu bağlantı yalnızca size özeldir ve tek kullanımlıktır.</p>
            </Card>
          </>
        )}
      </div>
    </div>
  );
}
