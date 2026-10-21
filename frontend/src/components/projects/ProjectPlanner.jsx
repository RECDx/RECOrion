import React, { useCallback, useEffect, useRef, useState } from 'react';
import { ArrowLeft, MessagesSquare, Pause, Play, Save } from 'lucide-react';
import { api } from '../../api';
import { Badge, Button, Card } from '../../ui/components';
import { confirmDialog, toast } from '../../ui/feedback';
import DocumentLibrary from '../docs/DocumentLibrary';
import PlanTab from './PlanTab';
import WorkflowTab from './WorkflowTab';
import { CloseTab, ReadinessTab, TeamSimTab } from './ProjectTabs';
import { ProjectFields } from './ProjectHub';
import { KIND, fmtDay, isEditable, statusOf } from './projectMeta';
import './projects.css';

const TABS = [
  ['info', 'Bilgiler & İsterler'],
  ['docs', 'Proje Ekleri'],
  ['plan', 'Beyin AI Planlama'],
  ['team', 'Ekip & Simülasyon'],
  ['ready', 'Hazırlık & Bildirim'],
  ['flow', 'İş Akışı'],
  ['close', 'Kapanış'],
];
const CONFIRM = {
  start: 'Proje başlatılsın mı? Bağımlılığı olmayan iş adımları AI personele açılır.',
  pause: 'Proje duraklatılsın mı?',
  complete: 'Proje tamamlandı olarak kapatılsın mı?',
  cancel: 'Proje iptal edilsin mi? Bu işlem geri alınamaz.',
  reopen_planning: 'Proje yeniden planlamaya alınsın mı?',
};
const DONE_MSG = { start_planning: 'Planlamaya alındı.', mark_ready: 'Proje başlamaya hazır.', start: 'Proje başlatıldı.', pause: 'Proje duraklatıldı.',
  resume: 'Proje devam ediyor.', complete: 'Proje tamamlandı.', cancel: 'Proje iptal edildi.', reopen_planning: 'Proje planlamaya geri alındı.' };
const pickForm = (p) => ({ name: p.name, kind: p.kind, manager_actor_id: p.manager_actor_id || '',
  department_id: p.department_id || '', start_date: p.start_date || '', end_date: p.end_date || '', description: p.description || '', requirements: p.requirements || '' });

/** Proje/Case planlama ekranı (ADIM 6.2–6.5). */
export default function ProjectPlanner({ projectId, tenant, currentUser, onBack, onOpenWork }) {
  const [project, setProject] = useState(null);
  const [actors, setActors] = useState([]);
  const [departments, setDepartments] = useState([]);
  const [tab, setTab] = useState('info');
  const [form, setForm] = useState(null);
  const [busy, setBusy] = useState(false);
  const firstLoad = useRef(true);

  const reload = useCallback(async () => {
    try {
      const [p, a] = await Promise.all([api.getProject(projectId), api.getActors(tenant.id)]);
      setProject(p);
      if (firstLoad.current) {  // başlamış projede İş Akışı sekmesiyle açılır
        firstLoad.current = false;
        if (['ACTIVE', 'PAUSED'].includes(p.status)) setTab('flow');
      }
      setForm(pickForm(p));
      setActors(a);
    } catch (e) {
      toast.error(e.message);
    }
  }, [projectId, tenant.id]);
  useEffect(() => { reload(); }, [reload]);
  useEffect(() => { api.getDepartments(tenant.id).then(setDepartments).catch(() => setDepartments([])); }, [tenant.id]);

  const loadDocs = useCallback(() => api.getProjectDocuments(projectId), [projectId]);
  const uploadDoc = useCallback((fd) => api.uploadProjectDocument(projectId, fd), [projectId]);

  const action = async (name, summary) => {
    if (CONFIRM[name] && !(await confirmDialog({ message: CONFIRM[name] }))) return;
    setBusy(true);
    try {
      await api.changeProjectStatus(project.id, name, summary);
      toast.success(DONE_MSG[name] || 'Güncellendi.');
      await reload();
    } catch (e) {
      toast.error(e.message);
    } finally {
      setBusy(false);
    }
  };

  const saveInfo = async () => {
    setBusy(true);
    try {
      const data = Object.fromEntries(Object.entries(form).map(([k, v]) => [k, v === '' ? null : v]));
      if (!data.manager_actor_id) delete data.manager_actor_id;
      await api.updateProject(project.id, data);
      toast.success('Proje bilgileri kaydedildi.');
      await reload();
    } catch (e) {
      toast.error(e.message);
    } finally {
      setBusy(false);
    }
  };

  if (!project || !form) return <div className="pj-page"><p className="pj-hint">Yükleniyor…</p></div>;

  const st = statusOf(project.status);
  const editable = project.can_manage && isEditable(project);
  const dirty = JSON.stringify(form) !== JSON.stringify(pickForm(project));
  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }));
  const humans = actors.filter((a) => a.actor_type === 'HUMAN' && a.status !== 'DISABLED');
  const agents = actors.filter((a) => a.actor_type === 'AI_AGENT' && !['DISABLED', 'DISMISSED'].includes(a.status));
  const manager = actors.find((a) => a.id === project.manager_actor_id);
  const counts = { docs: project.document_count, plan: project.plan?.steps?.length, team: project.members.length };

  return (
    <div className="pj-page">
      <div className="pj-head">
        <div className="pj-title">
          <button type="button" className="ui-btn ui-btn-ghost ui-btn-sm" onClick={onBack} style={{ alignSelf: 'flex-start' }}><ArrowLeft size={14} />Projeler</button>
          <h2>{project.name}</h2>
          <span className="pj-sub">
            <Badge tone={st.tone}>{st.label}</Badge>
            <span>{KIND[project.kind] || 'Proje'}</span>
            <span>Yönetici: {manager?.display_name || '—'}</span>
            <span>{fmtDay(project.start_date)} – {fmtDay(project.end_date)}</span>
          </span>
        </div>
        <div className="pj-actions">
          {project.can_manage && project.status === 'DRAFT' && (
            <Button onClick={() => action('start_planning')} disabled={busy}>Planlamaya başla</Button>
          )}
          {project.can_manage && project.status === 'READY' && <Button variant="success" icon={Play} onClick={() => action('start')} disabled={busy}>Başlat</Button>}
          {project.can_manage && project.status === 'ACTIVE' && <Button variant="secondary" icon={Pause} onClick={() => action('pause')} disabled={busy}>Duraklat</Button>}
          {project.can_manage && project.status === 'PAUSED' && <Button icon={Play} onClick={() => action('resume')} disabled={busy}>Devam ettir</Button>}
          {['ACTIVE', 'PAUSED', 'COMPLETED'].includes(project.status) && (
            <Button variant="secondary" icon={MessagesSquare} onClick={() => onOpenWork(project)}>Çalışma alanında aç</Button>
          )}
        </div>
      </div>

      <div className="pj-tabs" role="tablist">
        {TABS.map(([k, l]) => (
          <button key={k} type="button" role="tab" aria-selected={tab === k} className={`pj-tab ${tab === k ? 'active' : ''}`} onClick={() => setTab(k)}>
            {l}{counts[k] ? <small>{counts[k]}</small> : null}
          </button>
        ))}
      </div>

      {tab === 'info' && (
        <Card title="Bilgiler & İsterler" subtitle={editable ? 'Proje başlayana kadar düzenlenebilir.' : 'Başlamış veya kapanmış projenin temel bilgileri değiştirilemez.'}
          actions={editable && <Button icon={Save} onClick={saveInfo} disabled={busy || !dirty}>Kaydet</Button>}>
          <div className="pj-form">
            <ProjectFields form={form} set={set} humans={humans} departments={departments} disabled={!editable} />
          </div>
        </Card>
      )}
      {tab === 'docs' && (
        <Card title="Proje Ekleri" subtitle="Dosya ve görseller; onaylananlar yalnızca bu projedeki AI personel tarafından öğrenilir.">
          <DocumentLibrary load={loadDocs} upload={uploadDoc} canManage={project.can_manage && !['COMPLETED', 'CANCELLED'].includes(project.status)}
            intro="Şartname, örnek çıktı, ekran görüntüsü, çizim gibi ekleri yükleyin. Ekler KVKK maskelemesinden geçer, RECAi öğrenme kartı ve testi hazırlar, siz onaylayınca projenin bilgisine eklenir."
            emptyText="Proje kapanışında onaylı ekleri Kurum Hafızasına aktarabilirsiniz." />
        </Card>
      )}
      {tab === 'plan' && <PlanTab project={project} agents={agents} onChanged={reload} />}
      {tab === 'team' && <TeamSimTab project={project} actors={actors} onChanged={reload} />}
      {tab === 'ready' && <ReadinessTab project={project} onAction={action} busy={busy} />}
      {tab === 'flow' && <WorkflowTab project={project} />}
      {tab === 'close' && <CloseTab project={project} currentUser={currentUser} onAction={action} busy={busy} />}
    </div>
  );
}
