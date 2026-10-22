import React, { useCallback, useEffect, useState } from 'react';
import { Bot, CheckCircle2, FileText, RotateCcw, Send, ShieldAlert } from 'lucide-react';
import { api } from '../../api';
import { Badge, Button, Card, EmptyState, Modal } from '../../ui/components';
import SimpleMarkdown from '../ai/SimpleMarkdown';
import { confirmDialog, promptDialog, toast } from '../../ui/feedback';
import { fmtDay } from './projectMeta';

const TONE = { BACKLOG: 'neutral', READY: 'info', IN_PROGRESS: 'info', WAITING_APPROVAL: 'warning', REVISION: 'danger',
  QUARANTINED: 'danger', DONE: 'success', CANCELLED: 'neutral' };
const EVENT = { PROJECT_STARTED: 'Proje akışı başladı', TASK_STARTED: 'Adım başladı', SUBMITTED: 'Teslim edildi', APPROVED: 'Onaylandı',
  REJECTED: 'Revizyon istendi', QUARANTINED: 'Karantinaya alındı', RELEASED: 'Yeniden denemeye açıldı', DONE: 'Tamamlandı',
  CANCELLED: 'İptal edildi', PROJECT_FINISHED: 'Tüm adımlar tamamlandı', AI_OUTPUT: 'AI personel çıktı üretti',
  REVIEW_PASSED: 'Kontrolden geçti', REVIEW_FAILED: 'Kontrol personeli düzeltme istedi', BLOCKED: 'Adım durdu' };
const fmtTime = (d) => (d ? new Date(d).toLocaleString('tr-TR', { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' }) : '');

/** İş Akışı (ADIM 7.1): adımların canlı akış durumu, teslim/onay/karantina kararları ve olay geçmişi. */
export default function WorkflowTab({ project }) {
  const [flow, setFlow] = useState(null);
  const [busy, setBusy] = useState('');
  const [viewing, setViewing] = useState(null);
  const closeViewer = useCallback(() => setViewing(null), []);
  const live = ['ACTIVE', 'PAUSED'].includes(project.status);

  const load = useCallback(() => api.getProjectWorkflow(project.id).then(setFlow).catch((e) => toast.error(e.message)), [project.id]);
  useEffect(() => { load(); }, [load]);
  useEffect(() => {
    if (!live) return undefined;
    const t = setInterval(load, 4000);
    return () => clearInterval(t);
  }, [live, load]);

  const run = async (id, fn, message) => {
    setBusy(id);
    try {
      await fn();
      toast.success(message);
      setTimeout(load, 1200);
    } catch (e) {
      toast.error(e.message);
    } finally {
      setBusy('');
    }
  };

  const submit = async (t) => {
    const note = await promptDialog({ title: 'Çıktıyı teslim et', message: `'${t.title}' için teslim notu (isteğe bağlı):` });
    if (note !== null) run(t.id, () => api.submitTask(t.id, note), 'Teslim edildi.');
  };
  const reject = async (t) => {
    const note = await promptDialog({ title: 'Revizyon iste', message: 'Gerekçe (personel buna göre düzeltecek):' });
    if (note && note.trim()) run(t.id, () => api.decideTask(t.id, false, note.trim()), 'Revizyon istendi.');
  };
  const cancelTask = async (t) => {
    if (await confirmDialog({ message: `'${t.title}' iptal edilsin mi? Bu adıma bağlı adımlar beklemeden devam eder.` })) {
      run(t.id, () => api.releaseTask(t.id, 'cancel'), 'Adım iptal edildi.');
    }
  };

  if (!flow) return <p className="pj-hint">Yükleniyor…</p>;
  if (!flow.workflow_id && !flow.events.length) {
    return <EmptyState icon={ShieldAlert} title="İş akışı henüz başlamadı" description="Proje başlatıldığında iş adımları bağımlılık sırasına göre burada ilerler." />;
  }
  const titles = Object.fromEntries(flow.tasks.map((t) => [t.id, t.title]));
  const count = (s) => flow.tasks.filter((t) => s.includes(t.status)).length;

  return (
    <div className="pj-split wide-left">
      <div className="pj-steps">
        <div className="pj-stats">
          <div className="pj-stat"><span>Çalışılıyor</span><strong>{count(['IN_PROGRESS', 'REVISION'])}</strong></div>
          <div className="pj-stat"><span>Onay bekliyor</span><strong>{count(['WAITING_APPROVAL'])}</strong></div>
          <div className="pj-stat"><span>Karantina</span><strong>{count(['QUARANTINED'])}</strong></div>
          <div className="pj-stat"><span>Tamamlandı</span><strong>{count(['DONE'])} / {flow.tasks.length}</strong></div>
        </div>
        {project.status === 'PAUSED' && <div className="pj-note medium">Proje duraklatıldı: süren adımlar devam eder, yeni adım açılmaz.</div>}
        {flow.tasks.map((t) => (
          <div key={t.id} className="pj-step">
            <div className="pj-step-key">{t.order_index}</div>
            <div className="pj-steps" style={{ gap: 6 }}>
              <div className="pj-sub" style={{ justifyContent: 'space-between' }}>
                <strong style={{ color: 'var(--text-main)', fontSize: '0.9rem' }}>{t.title}</strong>
                <Badge tone={TONE[t.status] || 'neutral'}>{t.status_label}</Badge>
              </div>
              <div className="pj-meta">
                <span>Personel: {t.assignee ? `${t.assignee.name}${t.assignee.type === 'AI_AGENT' ? ' (AI)' : ''}` : 'Atanmadı'}</span>
                {t.reviewer && <span>Kontrol: {t.reviewer.name}</span>}
                {t.requires_approval && <span>Onaylayıcı: {t.approver?.name || '—'}</span>}
                {t.rejection_count > 0 && <span>Ret: {t.rejection_count} / {t.max_rejections}</span>}
                {t.depends_on.length > 0 && <span>Önce: {t.depends_on.map((d) => titles[d]).filter(Boolean).join(', ')}</span>}
                {t.completed_at && <span>Bitiş: {fmtDay(t.completed_at)}</span>}
              </div>
              {t.ai_working && (
                <div className="pj-note info" style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <Bot size={15} /> {t.assignee?.name} çalışıyor{t.status === 'REVISION' ? ' (geri bildirime göre düzeltiyor)' : ''}…
                </div>
              )}
              {t.artifact && (
                <div className="pj-actions">
                  <Button size="sm" variant="ghost" icon={FileText} onClick={() => setViewing({ task: t, id: t.artifact.id })}>
                    Çıktıyı gör (sürüm {t.artifact.version})
                  </Button>
                </div>
              )}
              {(t.can_submit || t.can_decide || t.can_release) && (
                <div className="pj-actions">
                  {t.can_submit && (
                    <Button size="sm" icon={Send} onClick={() => submit(t)} disabled={busy === t.id}>
                      {t.assignee?.type === 'AI_AGENT' ? 'AI çıktısını teslim et' : 'Çıktıyı teslim et'}
                    </Button>
                  )}
                  {t.can_decide && (
                    <>
                      <Button size="sm" variant="success" icon={CheckCircle2} onClick={() => run(t.id, () => api.decideTask(t.id, true), 'Onaylandı.')} disabled={busy === t.id}>Onayla</Button>
                      <Button size="sm" variant="secondary" icon={RotateCcw} onClick={() => reject(t)} disabled={busy === t.id}>Revizyon iste</Button>
                    </>
                  )}
                  {t.can_release && (
                    <>
                      <Button size="sm" icon={RotateCcw} onClick={() => run(t.id, () => api.releaseTask(t.id, 'retry'), 'Adım yeniden denemeye açıldı.')} disabled={busy === t.id}>Yeniden dene</Button>
                      <Button size="sm" variant="danger" onClick={() => cancelTask(t)} disabled={busy === t.id}>Adımı iptal et</Button>
                    </>
                  )}
                </div>
              )}
              {t.status === 'QUARANTINED' && (
                <p className="pj-note high" style={{ margin: 0 }}>{t.rejection_count} kez reddedildi. Yeniden denemek ret sayacını sıfırlar; gerekirse önce Ekip sekmesinden başka personel ekleyin.</p>
              )}
            </div>
          </div>
        ))}
      </div>
      {viewing && <ArtifactModal task={viewing.task} artifactId={viewing.id} onClose={closeViewer} />}
      <Card title="Akış geçmişi" subtitle="Silinemez kayıt: her teslim, onay, ret ve karar.">
        <ul className="pj-list">
          {flow.events.map((e) => (
            <li key={e.id} style={{ alignItems: 'flex-start' }}>
              <span>
                <strong>{EVENT[e.kind] || e.kind}</strong>{e.task_id && titles[e.task_id] ? ` · ${titles[e.task_id]}` : ''}
                {e.note && <><br /><small className="pj-hint">“{e.note}”</small></>}
                <br /><small className="pj-hint">{fmtTime(e.created_at)}{e.actor ? ` · ${e.actor.name}` : ''}</small>
              </span>
            </li>
          ))}
        </ul>
      </Card>
    </div>
  );
}

function ArtifactModal({ task, artifactId, onClose }) {
  const [id, setId] = useState(artifactId);
  const [art, setArt] = useState(null);
  useEffect(() => {
    setArt(null);
    api.getTaskArtifact(task.id, id).then(setArt).catch((e) => { toast.error(e.message); onClose(); });
  }, [task.id, id, onClose]);
  return (
    <Modal open onClose={onClose} title={`${task.title} · çıktı`} size="lg"
      footer={art?.versions?.length > 1 && (
        <select className="ui-input" aria-label="Sürüm" value={id} onChange={(e) => setId(e.target.value)}>
          {art.versions.map((v) => <option key={v.id} value={v.id}>Sürüm {v.version} · {fmtTime(v.created_at)}</option>)}
        </select>
      )}>
      {!art ? <p className="pj-hint">Yükleniyor…</p> : <SimpleMarkdown text={art.content || '(boş)'} />}
    </Modal>
  );
}
