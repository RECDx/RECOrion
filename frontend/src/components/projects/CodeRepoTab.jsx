import React, { useCallback, useEffect, useState } from 'react';
import { FileCode2, GitBranch, GitMerge } from 'lucide-react';
import { api } from '../../api';
import { Badge, Button, Card, EmptyState, Modal } from '../../ui/components';
import { confirmDialog, toast } from '../../ui/feedback';

const STATE = { OPEN: ['Onay bekliyor', 'warning'], MERGED: ['Ana dala birleşti', 'success'], CLOSED: ['Kapatıldı', 'neutral'] };
const FILE = { added: 'eklendi', modified: 'değişti', deleted: 'silindi', changed: 'değişti' };
const fmtTime = (d) => (d ? new Date(d).toLocaleString('tr-TR', { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' }) : '');

/** Kod Deposu (ADIM 8.5): RECOrion Gitea deposu; AI personel adım dalına çalışır, ana dala birleştirme insan onayıyla. */
export default function CodeRepoTab({ project }) {
  const [repo, setRepo] = useState(null);
  const [busy, setBusy] = useState(false);
  const [viewing, setViewing] = useState(null);
  const closed = ['COMPLETED', 'CANCELLED'].includes(project.status);
  const load = useCallback(() => api.getProjectRepository(project.id).then(setRepo).catch((e) => toast.error(e.message)), [project.id]);
  useEffect(() => { load(); }, [load]);

  const setMode = async (mode) => {
    if (mode === 'NONE' && !(await confirmDialog({ message: 'Kod deposu kullanılmasın mı? Depo ve geçmişi silinmez; yeni çıktılar artık commit edilmez.' }))) return;
    setBusy(true);
    try {
      setRepo({ ...(await api.setProjectRepository(project.id, mode)), can_manage: repo?.can_manage });
      toast.success(mode === 'RECORION' ? 'Kod deposu açıldı; AI personelin kod çıktıları adım dallarına commit edilecek.' : 'Kod deposu kullanımı kapatıldı.');
    } catch (e) { toast.error(e.message); } finally { setBusy(false); }
  };
  const merge = async (s) => {
    if (!(await confirmDialog({ message: `'${s.title}' adımının değişiklikleri ana dala (main) birleştirilsin mi?` }))) return;
    try { await api.mergeRepositoryStep(project.id, s.task_id); toast.success('Ana dala birleştirildi.'); load(); } catch (e) { toast.error(e.message); }
  };

  if (!repo) return <p className="pj-hint">Yükleniyor…</p>;
  const on = repo.mode === 'RECORION';
  const steps = (repo.steps || []).filter((s) => s.branch || s.pr);

  return (
    <div className="pj-steps">
      <Card title="Kod deposu" subtitle="AI personel her iş adımında kendi dalına çalışır; adım onaylanınca değişiklikler ana dala (main) birleştirilir."
        actions={<GitBranch size={18} />}>
        {!repo.enabled ? (
          <p className="pj-hint">Kod deposu sunucusu bu kurulumda yapılandırılmamış. RECDx ile iletişime geçin.</p>
        ) : on ? (
          <div className="pj-actions" style={{ alignItems: 'center' }}>
            <Badge tone="success">RECOrion deposu açık</Badge>
            <span className="pj-hint" style={{ fontFamily: 'var(--font-mono)' }} title="Depo özeldir; dosyalar bu ekrandan görüntülenir">{repo.url}</span>
            {repo.can_manage && !closed && <Button variant="ghost" size="sm" disabled={busy} onClick={() => setMode('NONE')}>Kullanma</Button>}
          </div>
        ) : (
          <div className="pj-actions" style={{ alignItems: 'center' }}>
            <Badge tone="neutral">Depo yok</Badge>
            {repo.can_manage && !closed
              ? <Button icon={GitBranch} disabled={busy} onClick={() => setMode('RECORION')}>{busy ? 'Açılıyor…' : 'RECOrion deposunu aç'}</Button>
              : <span className="pj-hint">Depoyu proje yöneticisi açar.</span>}
            {repo.url && <span className="pj-hint">Önceki depo korunuyor: {repo.url}</span>}
          </div>
        )}
        <p className="pj-hint" style={{ marginTop: 10 }}>
          Kod dosyaları AI çıktısındaki yolu belirtilmiş kod bloklarından oluşur (ör. <code>```python src/app.py</code>); her adımın dokümanı
          <code> docs/adimlar/</code> altına yazılır. GitHub/GitLab'a yansıtma ilerleyen sürümde.
        </p>
      </Card>

      {on && (steps.length === 0 ? (
        <EmptyState icon={FileCode2} title="Henüz commit yok" description="AI personel bir iş adımının çıktısını ürettiğinde değişiklikler burada görünür." />
      ) : steps.map((s) => {
        const [label, tone] = STATE[s.state] || ['—', 'neutral'];
        return (
          <Card key={s.task_id} title={`${s.order_index ? `${s.order_index}. ` : ''}${s.title}`}
            subtitle={<span style={{ fontFamily: 'var(--font-mono)' }}>{s.branch} → {repo.base}{s.pr ? ` · istek #${s.pr}` : ''}</span>}
            actions={<Badge tone={tone}>{label}</Badge>}>
            {s.error && <p className="ui-text-danger" style={{ fontSize: '0.75rem' }}>{s.error}</p>}
            {s.merged_at && <p className="pj-hint">Birleştirildi: {fmtTime(s.merged_at)}</p>}
            <ul className="pj-list">
              {s.files.map((f) => (
                <li key={f.path}>
                  <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.78rem' }}>{f.path}</span>
                  <small className="pj-hint">{FILE[f.status] || f.status}{f.additions ? ` · +${f.additions}` : ''}</small>
                  {f.status !== 'deleted' && (
                    <button type="button" className="ui-icon-btn" aria-label={`${f.path} dosyasını gör`}
                      onClick={() => setViewing({ path: f.path, ref: s.state === 'MERGED' ? repo.base : s.branch })}><FileCode2 size={14} /></button>
                  )}
                </li>
              ))}
            </ul>
            {repo.can_manage && s.status === 'DONE' && s.state === 'OPEN' && (
              <div className="pj-actions" style={{ marginTop: 8 }}>
                <Button size="sm" icon={GitMerge} onClick={() => merge(s)}>Ana dala birleştir</Button>
                <span className="pj-hint">Bu adım onay gerektirmediği veya birleştirme yapılamadığı için bekliyor.</span>
              </div>
            )}
          </Card>
        );
      }))}
      {viewing && <FileModal project={project} file={viewing} onClose={() => setViewing(null)} />}
    </div>
  );
}

function FileModal({ project, file, onClose }) {
  const [data, setData] = useState(null);
  useEffect(() => {
    api.getRepositoryFile(project.id, file.ref, file.path).then(setData).catch((e) => { toast.error(e.message); onClose(); });
  }, [project.id, file.ref, file.path, onClose]);
  return (
    <Modal open onClose={onClose} title={file.path} size="lg">
      <p className="pj-hint" style={{ fontFamily: 'var(--font-mono)' }}>{file.ref}{data ? ` · ${data.size} bayt` : ''}</p>
      {!data ? <p className="pj-hint">Yükleniyor…</p> : (
        <pre style={{ fontFamily: 'var(--font-mono)', fontSize: '0.78rem', whiteSpace: 'pre-wrap', background: 'var(--bg-dark)',
          border: '1px solid var(--border-subtle)', borderRadius: 8, padding: 12, maxHeight: '60vh', overflow: 'auto' }}>{data.content}</pre>
      )}
    </Modal>
  );
}
