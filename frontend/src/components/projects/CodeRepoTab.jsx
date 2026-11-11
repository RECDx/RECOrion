import React, { Suspense, lazy, useCallback, useEffect, useState } from 'react';
import { Copy, FileCode2, FolderTree, GitBranch, GitCompare, GitMerge, ListChecks } from 'lucide-react';
import { api } from '../../api';
import { Badge, Button, Card, EmptyState } from '../../ui/components';
import { confirmDialog, toast } from '../../ui/feedback';

const STATE = { OPEN: ['Onay bekliyor', 'warning'], MERGED: ['Ana dala birleşti', 'success'], CLOSED: ['Kapatıldı', 'neutral'] };
// F84: açık birleştirme isteğinde etiket adımın gerçek akış durumunu söyler (İş Akışı ile aynı)
const TASK = { BACKLOG: ['Sırada', 'neutral'], READY: ['Başlayabilir', 'info'], IN_PROGRESS: ['Çalışılıyor', 'info'],
  WAITING_APPROVAL: ['Onay bekliyor', 'warning'], REVISION: ['Revizyonda', 'danger'], QUARANTINED: ['Karantinada', 'danger'],
  DONE: ['Tamamlandı · birleştirilmedi', 'warning'], CANCELLED: ['İptal edildi', 'neutral'] };
const FILE = { added: 'eklendi', modified: 'değişti', deleted: 'silindi', changed: 'değişti' };
// Kod Gezgini (ADIM 16.1): Monaco yalnız bu görünüm açılınca yüklenir
const CodeExplorer = lazy(() => import('./CodeExplorer'));
const DiffModal = lazy(() => import('./CodeExplorer').then((m) => ({ default: m.DiffModal })));
const fmtTime = (d) => (d ? new Date(d).toLocaleString('tr-TR', { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' }) : '');

/** Kod Deposu (ADIM 8.5): RECOrion Gitea deposu; AI personel adım dalına çalışır, ana dala birleştirme insan onayıyla. */
export default function CodeRepoTab({ project }) {
  const [repo, setRepo] = useState(null);
  const [busy, setBusy] = useState(false);
  const [view, setView] = useState('explorer');
  const [explorerAt, setExplorerAt] = useState(null);
  const [diff, setDiff] = useState(null);
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
            {repo.can_manage && !closed && <Button variant="ghost" size="sm" disabled={busy} onClick={() => setMode('NONE')}
              title="Bu projede kod deposunu kapatır: AI personelin kodu artık depoya yazılmaz, testler çalışmaz. Depo silinmez; yeniden açılabilir.">Depoyu kullanma</Button>}
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
          <code> docs/adimlar/</code> altına yazılır.
        </p>
      </Card>

      {on && <MirrorCard project={project} repo={repo} closed={closed} onChange={(r) => setRepo({ ...r, can_manage: repo.can_manage })} />}

      {on && (
        <div className="ui-segmented" role="radiogroup" aria-label="Kod deposu görünümü" style={{ alignSelf: 'flex-start' }}>
          {[['explorer', 'Kod Gezgini', FolderTree], ['steps', 'Adımlar', ListChecks]].map(([v, label, Icon]) => (
            <button key={v} type="button" role="radio" aria-checked={view === v} className={`ui-segmented-item${view === v ? ' active' : ''}`}
              onClick={() => setView(v)}><Icon size={14} /><span>{label}</span></button>
          ))}
        </div>
      )}

      {on && view === 'explorer' && (
        <Suspense fallback={<p className="pj-hint">Kod Gezgini yükleniyor…</p>}>
          <CodeExplorer project={project} initial={explorerAt} />
        </Suspense>
      )}

      {on && view === 'steps' && (steps.length === 0 ? (
        <EmptyState icon={FileCode2} title="Henüz commit yok" description="AI personel bir iş adımının çıktısını ürettiğinde değişiklikler burada görünür." />
      ) : steps.map((s) => {
        const [label, tone] = (s.state === 'OPEN' ? TASK[s.status] : STATE[s.state]) || STATE[s.state] || ['—', 'neutral'];
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
                  {(s.base_sha || s.head_sha) && (
                    <button type="button" className="ui-icon-btn" aria-label={`${f.path} farkını gör`} title="Farkı gör"
                      onClick={() => setDiff({ path: f.path, status: f.status, base: s.base_sha, head: s.head_sha || s.branch, title: s.title })}><GitCompare size={14} /></button>
                  )}
                  {f.status !== 'deleted' && (
                    <button type="button" className="ui-icon-btn" aria-label={`${f.path} dosyasını Kod Gezgini'nde aç`} title="Kod Gezgini'nde aç"
                      onClick={() => { setExplorerAt({ path: f.path, ref: s.state === 'MERGED' ? repo.base : s.branch }); setView('explorer'); }}><FileCode2 size={14} /></button>
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
      {diff && <Suspense fallback={null}><DiffModal project={project} file={diff} onClose={() => setDiff(null)} /></Suspense>}
    </div>
  );
}

/** Müşterinin GitHub/Gitea hesabına yansıtma (ADIM 10.3, #297): şirket bağlantısının token'ıyla, her commit'te. */
function MirrorCard({ project, repo, closed, onChange }) {
  const [targets, setTargets] = useState(null);
  const [cid, setCid] = useState('');
  const [target, setTarget] = useState('');
  const [busy, setBusy] = useState(false);
  const m = repo.mirror;
  const editable = repo.can_manage && !closed;
  useEffect(() => {
    if (!editable || m) return;
    api.getMirrorTargets(project.id).then((t) => { setTargets(t); setCid((c) => c || t[0]?.id || ''); }).catch((e) => toast.error(e.message));
  }, [project.id, editable, m]);
  const save = async () => {
    setBusy(true);
    try { onChange(await api.setRepositoryMirror(project.id, cid, target.trim())); toast.success('Yansıtma kuruldu; her commit hedef depoya da gönderilir.'); }
    catch (e) { toast.error(e.message); } finally { setBusy(false); }
  };
  const clear = async () => {
    if (!(await confirmDialog({ message: 'Yansıtma kaldırılsın mı? Hedef depodaki kod silinmez; yeni commitler artık gönderilmez.' }))) return;
    try { onChange(await api.clearRepositoryMirror(project.id)); toast.success('Yansıtma kaldırıldı.'); } catch (e) { toast.error(e.message); }
  };
  return (
    <Card title="Şirket hesabına yansıtma" subtitle="Ana depo RECOrion'da kalır; her commit şirketin GitHub/Gitea deposuna da gönderilir." actions={<Copy size={18} />}>
      {m ? (
        <>
          <div className="pj-actions" style={{ alignItems: 'center' }}>
            <Badge tone={m.last_error ? 'danger' : 'success'}>{m.last_error ? 'Gönderim hatası' : 'Yansıtılıyor'}</Badge>
            <span className="pj-hint" style={{ fontFamily: 'var(--font-mono)' }}>{m.remote || m.repo}</span>
            {editable && <Button variant="ghost" size="sm" onClick={clear}>Kaldır</Button>}
          </div>
          {m.last_update && !String(m.last_update).startsWith('0001') && <p className="pj-hint">Son gönderim: {fmtTime(m.last_update)}</p>}
          {m.last_error && <p className="ui-text-danger" style={{ fontSize: '0.75rem' }}>{m.last_error}</p>}
        </>
      ) : !editable ? (
        <p className="pj-hint">Yansıtma yok. Proje yöneticisi şirketin GitHub/Gitea bağlantısıyla kurabilir.</p>
      ) : targets && targets.length === 0 ? (
        <p className="pj-hint">Şirketin GitHub/Gitea bağlantısı yok. Şirket yöneticisi Şirket Yönetimi › Entegrasyonlar ekranından ekler.</p>
      ) : (
        <div className="pj-form">
          <div className="pj-field">
            <label htmlFor="mirror-conn">Bağlantı</label>
            <select id="mirror-conn" className="ui-input" value={cid} onChange={(e) => setCid(e.target.value)}>
              {(targets || []).map((t) => <option key={t.id} value={t.id}>{t.name} ({t.connector === 'github' ? 'GitHub' : 'Gitea'})</option>)}
            </select>
          </div>
          <div className="pj-field">
            <label htmlFor="mirror-repo">Hedef depo</label>
            <input id="mirror-repo" className="ui-input" value={target} placeholder="sirket/proje-adi" onChange={(e) => setTarget(e.target.value)} />
            <p className="pj-hint">Depo hedef hesapta önceden açılmış ve boş olmalı.</p>
          </div>
          <div className="pj-actions"><Button icon={Copy} disabled={busy || !cid || !/^[^/\s]+\/[^/\s]+$/.test(target.trim())} onClick={save}>{busy ? 'Kuruluyor…' : 'Yansıt'}</Button></div>
        </div>
      )}
    </Card>
  );
}
