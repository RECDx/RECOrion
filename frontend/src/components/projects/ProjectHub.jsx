import React, { useCallback, useEffect, useState } from 'react';
import { FolderKanban, Plus } from 'lucide-react';
import { api } from '../../api';
import { Badge, Button, EmptyState, Modal } from '../../ui/components';
import { toast } from '../../ui/feedback';
import { KIND, fmtDay, statusOf } from './projectMeta';
import './projects.css';

const canSeeAll = (u) => (u?.permissions || []).includes('project:manage') || u?.role === 'COMPANY_ADMIN';
const canCreate = (u) => (u?.permissions || []).includes('project:create') || ['COMPANY_ADMIN', 'PROJECT_MANAGER'].includes(u?.role);

/** Work Space proje/Case listesi ve "Yeni Proje/Case" oluşturma (ADIM 6.2). */
export default function ProjectHub({ tenant, currentUser, actors = [], onOpen }) {
  const [scope, setScope] = useState('mine');
  const [projects, setProjects] = useState(null);
  const [creating, setCreating] = useState(false);

  const refresh = useCallback(() => {
    if (!tenant?.id) return;
    api.getProjects(tenant.id, scope).then(setProjects).catch((e) => { setProjects([]); toast.error(e.message); });
  }, [tenant?.id, scope]);
  useEffect(() => { refresh(); }, [refresh]);

  return (
    <div className="pj-page">
      <div className="pj-head">
        <div className="pj-title">
          <h2>Projeler ve Case'ler</h2>
          <span className="pj-sub">İsterleri yazın, Beyin AI ile planlayın, AI personel ekibinizi kurun ve başlatın.</span>
        </div>
        <div className="pj-actions">
          {canSeeAll(currentUser) && (
            <div className="ui-segmented" role="tablist">
              {[['mine', 'Benim projelerim'], ['all', 'Tüm projeler']].map(([k, l]) => (
                <button key={k} type="button" className={`ui-segmented-item ${scope === k ? 'active' : ''}`} onClick={() => setScope(k)}>{l}</button>
              ))}
            </div>
          )}
          {canCreate(currentUser) && <Button icon={Plus} onClick={() => setCreating(true)}>Yeni Proje / Case</Button>}
        </div>
      </div>

      {!projects ? <p className="pj-hint">Yükleniyor…</p> : projects.length === 0 ? (
        <EmptyState icon={FolderKanban} title="Henüz proje yok"
          description="İlk projenizi veya Case'inizi oluşturun; isterlerinizden Beyin AI iş adımlarını ve ekibi önersin."
          action={canCreate(currentUser) && <Button icon={Plus} onClick={() => setCreating(true)}>Yeni Proje / Case</Button>} />
      ) : (
        <div className="pj-grid">
          {projects.map((p) => {
            const st = statusOf(p.status);
            const manager = actors.find((a) => a.id === p.manager_actor_id);
            return (
              <button key={p.id} type="button" className="pj-card" onClick={() => onOpen(p)}>
                <div className="pj-sub"><Badge tone={st.tone}>{st.label}</Badge><span>{KIND[p.kind] || 'Proje'}</span></div>
                <h3>{p.name}</h3>
                {p.description && <p>{p.description}</p>}
                <div className="pj-meta">
                  <span>Yönetici: {manager?.display_name || '—'}</span>
                  <span>{p.task_count || 0} iş adımı</span>
                  <span>{fmtDay(p.start_date)} – {fmtDay(p.end_date)}</span>
                </div>
              </button>
            );
          })}
        </div>
      )}

      {creating && (
        <CreateProjectModal tenant={tenant} currentUser={currentUser} actors={actors}
          onClose={() => setCreating(false)} onCreated={(p) => { setCreating(false); refresh(); onOpen(p); }} />
      )}
    </div>
  );
}

function CreateProjectModal({ tenant, currentUser, actors, onClose, onCreated }) {
  const [form, setForm] = useState({ name: '', kind: 'PROJECT', field_package: 'GENEL', manager_actor_id: currentUser?.actor_id || '',
    department_id: '', start_date: '', end_date: '', description: '', requirements: '' });
  const [departments, setDepartments] = useState([]);
  const [busy, setBusy] = useState(false);
  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }));
  const humans = actors.filter((a) => a.actor_type === 'HUMAN' && a.status !== 'DISABLED');

  useEffect(() => { api.getDepartments(tenant.id).then(setDepartments).catch(() => setDepartments([])); }, [tenant.id]);

  const submit = async () => {
    if (form.name.trim().length < 2) return toast.warning('Proje adını yazın.');
    setBusy(true);
    try {
      const data = Object.fromEntries(Object.entries(form).map(([k, v]) => [k, v === '' ? null : v]));
      const created = await api.createProject({ ...data, tenant_id: tenant.id, name: form.name.trim() });
      toast.success(`'${created.name}' oluşturuldu. Şimdi ekleri yükleyip Beyin AI ile planlayabilirsiniz.`);
      onCreated(created);
    } catch (e) {
      toast.error(e.message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <Modal open onClose={onClose} title="Yeni Proje / Case" size="lg"
      footer={<><Button variant="secondary" onClick={onClose}>Vazgeç</Button><Button onClick={submit} disabled={busy}>{busy ? 'Oluşturuluyor…' : 'Oluştur'}</Button></>}>
      <div className="pj-form">
        <ProjectFields form={form} set={set} humans={humans} departments={departments} />
      </div>
      <p className="pj-hint" style={{ marginTop: 12 }}>
        Dosya ve görselleri (Proje Ekleri) oluşturduktan sonra yükleyebilirsiniz; onaylanan ekler bu projedeki AI personel tarafından öğrenilir.
      </p>
    </Modal>
  );
}

/** Oluşturma ve "Bilgiler & İsterler" sekmesinin ortak alanları. */
export function ProjectFields({ form, set, humans, departments, disabled = false }) {
  return (
    <>
      <div className="pj-field">
        <label htmlFor="pj-name">Adı</label>
        <input id="pj-name" className="ui-input" value={form.name} onChange={set('name')} maxLength={255} disabled={disabled} />
      </div>
      <div className="pj-field">
        <label htmlFor="pj-kind">Türü</label>
        <select id="pj-kind" className="ui-input" value={form.kind} onChange={set('kind')} disabled={disabled}>
          <option value="PROJECT">Proje (çok adımlı, takvimli iş)</option>
          <option value="CASE">Case (tek bir konu / vaka çözümü)</option>
        </select>
      </div>
      <div className="pj-field">
        <label htmlFor="pj-manager">Proje yöneticisi</label>
        <select id="pj-manager" className="ui-input" value={form.manager_actor_id || ''} onChange={set('manager_actor_id')} disabled={disabled}>
          {humans.map((h) => <option key={h.id} value={h.id}>{h.display_name}{h.email ? ` (${h.email})` : ''}</option>)}
        </select>
      </div>
      <div className="pj-field">
        <label htmlFor="pj-dept">Sorumlu departman</label>
        <select id="pj-dept" className="ui-input" value={form.department_id || ''} onChange={set('department_id')} disabled={disabled}>
          <option value="">Belirtilmedi</option>
          {departments.map((d) => <option key={d.id} value={d.id}>{d.name}</option>)}
        </select>
      </div>
      <div className="pj-field">
        <label htmlFor="pj-start">Hedef başlangıç</label>
        <input id="pj-start" type="date" className="ui-input" value={form.start_date || ''} onChange={set('start_date')} disabled={disabled} />
      </div>
      <div className="pj-field">
        <label htmlFor="pj-end">Hedef bitiş</label>
        <input id="pj-end" type="date" className="ui-input" value={form.end_date || ''} onChange={set('end_date')} disabled={disabled} />
      </div>
      <div className="pj-field">
        <label htmlFor="pj-field">Alan</label>
        <select id="pj-field" className="ui-input" value={form.field_package} onChange={set('field_package')} disabled={disabled}>
          <option value="GENEL">Genel</option>
          <option value="YAZILIM">Yazılım</option>
        </select>
      </div>
      <div className="pj-field full">
        <label htmlFor="pj-desc">Kısa açıklama</label>
        <textarea id="pj-desc" className="ui-input" rows={2} value={form.description || ''} onChange={set('description')} disabled={disabled} />
      </div>
      <div className="pj-field full">
        <label htmlFor="pj-req">İsterler</label>
        <textarea id="pj-req" className="ui-input" rows={8} value={form.requirements || ''} onChange={set('requirements')} disabled={disabled}
          placeholder="Ne yapılmasını istiyorsunuz? Hedefler, kapsam, kısıtlar, beklenen çıktılar, teslim ölçütleri…" />
        <p className="pj-hint">Beyin AI iş adımlarını ve gereken personeli bu metinden ve onaylı proje eklerinden çıkarır.</p>
      </div>
    </>
  );
}
