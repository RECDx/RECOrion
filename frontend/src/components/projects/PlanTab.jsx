import React, { useCallback, useEffect, useState } from 'react';
import { ArrowDown, ArrowUp, Brain, CheckCircle2, Plus, RefreshCw, Save, Trash2, UserPlus } from 'lucide-react';
import { api } from '../../api';
import { Badge, Button, Card, EmptyState } from '../../ui/components';
import { confirmDialog, toast } from '../../ui/feedback';
import ChatPanel from '../ai/ChatPanel';
import HireWizard from '../catalog/HireWizard';
import { PRIORITY, isPlanning } from './projectMeta';

const emptyStep = (n) => ({ key: `S${n}`, title: '', description: '', acceptance_criteria: '', department: '', job_title: '',
  agent_id: '', estimated_days: 1, depends_on: [], priority: 'MEDIUM' });

/**
 * Beyin AI planlama (ADIM 6.3): planlama sohbeti + iş adımı taslağı.
 * Yönetici öneriyi düzenler, kaydeder ve onaylar; onayda adımlar iş adımlarına (görevlere) dönüşür.
 */
export default function PlanTab({ project, agents, onChanged }) {
  const editable = project.can_manage && isPlanning(project);
  const [plan, setPlan] = useState(project.plan);
  const [dirty, setDirty] = useState(false);
  const [busy, setBusy] = useState('');
  const [feedback, setFeedback] = useState('');
  const [hireOpen, setHireOpen] = useState(false);

  useEffect(() => { setPlan(project.plan); setDirty(false); }, [project.plan]);

  const loadChat = useCallback(() => api.getProjectPlanChat(project.id), [project.id]);
  const sendChat = useCallback(async (content) => {
    const res = await api.sendProjectPlanChat(project.id, content);
    return { message: { id: `a-${Date.now()}`, role: 'assistant', content: res.content, created_at: new Date().toISOString() },
      model_code: res.model_code, credits: res.credits };
  }, [project.id]);

  const run = async (label, fn) => {
    setBusy(label);
    try { return await fn(); } catch (e) { toast.error(e.message); return null; } finally { setBusy(''); }
  };

  const suggest = (useChat) => run(useChat ? 'chat' : 'suggest', async () => {
    if (dirty && !(await confirmDialog({ message: 'Kaydedilmemiş düzenlemeleriniz yeni öneriyle değiştirilecek. Devam edilsin mi?' }))) return;
    toast.info('RECAi isterleri inceliyor; bu işlem bir iki dakika sürebilir.');
    const p = await api.suggestProjectPlan(project.id, feedback, useChat);
    setPlan(p); setDirty(false); setFeedback('');
    toast.success(`Beyin AI ${p.steps.length} iş adımı önerdi.`);
    onChanged();
  });

  const save = () => run('save', async () => {
    const p = await api.saveProjectPlan(project.id, { ...plan, steps: plan.steps.map(normalize) });
    setPlan(p); setDirty(false);
    toast.success('Plan taslağı kaydedildi.');
    onChanged();
    return p;
  });

  const approve = () => run('approve', async () => {
    if (dirty) {
      const p = await api.saveProjectPlan(project.id, { ...plan, steps: plan.steps.map(normalize) });
      setPlan(p); setDirty(false);
    }
    if (!(await confirmDialog({ title: 'Planı onayla', confirmText: 'Onayla',
      message: 'Adımlar iş adımlarına dönüşür ve atanan AI personel ekibe eklenir. Daha önce onaylanmış ama başlamamış adımlar yeniden oluşturulur.' }))) return;
    const r = await api.approveProjectPlan(project.id);
    toast.success(`${r.task_count} iş adımı oluşturuldu${r.unassigned ? `; ${r.unassigned} adıma henüz personel atanmadı` : ''}.`);
    onChanged();
  });

  const update = (i, patch) => { setPlan((p) => ({ ...p, steps: p.steps.map((s, j) => (j === i ? { ...s, ...patch } : s)) })); setDirty(true); };
  const move = (i, d) => {
    setPlan((p) => {
      const steps = [...p.steps];
      [steps[i], steps[i + d]] = [steps[i + d], steps[i]];
      return { ...p, steps };
    });
    setDirty(true);
  };
  const remove = (i) => {
    setPlan((p) => {
      const key = p.steps[i].key;
      return { ...p, steps: p.steps.filter((_, j) => j !== i).map((s) => ({ ...s, depends_on: (s.depends_on || []).filter((d) => d !== key) })) };
    });
    setDirty(true);
  };
  const add = () => {
    setPlan((p) => {
      const steps = p?.steps || [];
      let n = steps.length + 1;
      while (steps.some((s) => s.key === `S${n}`)) n += 1;
      return { ...(p || { summary: '', hire_suggestions: [], risks: [], questions: [] }), steps: [...steps, emptyStep(n)] };
    });
    setDirty(true);
  };

  const steps = plan?.steps || [];
  const approved = plan?.approved && project.planning_approved_at;

  return (
    <div className="pj-split">
      <Card title="Beyin AI ile planlama sohbeti" subtitle="İsterleri netleştirin; ardından planı bu konuşmaya göre güncelletin.">
        <div className="pj-plan-chat">
          <ChatPanel loadHistory={loadChat} send={editable ? sendChat : async () => { throw new Error('Plan yalnızca planlama aşamasında konuşulabilir.'); }}
            icon={Brain} emptyTitle="Planlamaya başlayın"
            emptyText="Beyin AI projenizin isterlerini ve onaylı proje eklerini bilir. Eksikleri sorar, iş adımları ve personel önerir."
            suggestions={editable ? ['İsterlerde eksik gördüğün noktalar neler?', 'Bu proje için hangi unvanlarda personel gerekir?', 'En riskli adımlar hangileri?'] : []}
            placeholder="Beyin AI'ya yazın…" />
        </div>
        {editable && (
          <div className="pj-actions" style={{ marginTop: 10 }}>
            <Button variant="secondary" icon={RefreshCw} onClick={() => suggest(true)} disabled={!!busy}>
              {busy === 'chat' ? 'Güncelleniyor…' : 'Planı bu konuşmaya göre güncelle'}
            </Button>
          </div>
        )}
      </Card>

      <div className="pj-steps">
        <Card title="İş adımları" subtitle={plan?.model_code ? `Öneren model: ${plan.model_code}${dirty ? ' · kaydedilmemiş değişiklik var' : ''}` : 'Henüz plan yok'}
          actions={approved ? <Badge tone="success">Onaylandı</Badge> : plan ? <Badge tone="warning">Onay bekliyor</Badge> : null}>
          {editable && (
            <div className="pj-field" style={{ marginBottom: 10 }}>
              <label htmlFor="pj-fb">Beyin AI'ya not (isteğe bağlı)</label>
              <textarea id="pj-fb" className="ui-input" rows={2} value={feedback} onChange={(e) => setFeedback(e.target.value)}
                placeholder="Örn. test adımını ayrı tut, tasarım için iki gün yeterli…" />
              <div className="pj-actions">
                <Button icon={Brain} onClick={() => suggest(false)} disabled={!!busy}>{busy === 'suggest' ? 'Öneri hazırlanıyor…' : plan ? 'Yeniden öner' : 'Beyin AI plan önersin'}</Button>
                {plan && <Button variant="secondary" icon={Save} onClick={save} disabled={!!busy || !dirty}>Kaydet</Button>}
                {plan && <Button variant="success" icon={CheckCircle2} onClick={approve} disabled={!!busy || !steps.length}>Onayla ve iş adımlarına dönüştür</Button>}
              </div>
            </div>
          )}
          {plan?.summary && <p className="pj-note info">{plan.summary}</p>}
        </Card>

        {!plan ? (
          <EmptyState icon={Brain} title="Plan bekleniyor" description="İsterleri yazdıktan sonra Beyin AI'dan iş adımı önerisi isteyin." />
        ) : steps.map((s, i) => (
          <div className="pj-step" key={s.key}>
            <div className="pj-step-key">{s.key}</div>
            <div className="pj-step-body">
              <input className="ui-input half" aria-label="Adım adı" value={s.title} disabled={!editable} onChange={(e) => update(i, { title: e.target.value })} placeholder="Adım adı" />
              <select className="ui-input half" aria-label="AI personel" value={s.agent_id || ''} disabled={!editable} onChange={(e) => update(i, { agent_id: e.target.value })}>
                <option value="">Personel atanmadı</option>
                {agents.map((a) => <option key={a.id} value={a.id}>{a.display_name}{a.role ? ` · ${a.role}` : ''}</option>)}
              </select>
              <textarea className="ui-input wide" rows={2} aria-label="Açıklama" value={s.description || ''} disabled={!editable} onChange={(e) => update(i, { description: e.target.value })} placeholder="Ne yapılacak" />
              <textarea className="ui-input wide" rows={1} aria-label="Kabul ölçütü" value={s.acceptance_criteria || ''} disabled={!editable} onChange={(e) => update(i, { acceptance_criteria: e.target.value })} placeholder="Tamam sayılma ölçütü" />
              <label className="pj-mini"><span>Departman</span>
                <input className="ui-input" value={s.department || ''} disabled={!editable} onChange={(e) => update(i, { department: e.target.value })} />
              </label>
              <label className="pj-mini"><span>Gereken unvan</span>
                <input className="ui-input" value={s.job_title || ''} disabled={!editable} onChange={(e) => update(i, { job_title: e.target.value })} />
              </label>
              <label className="pj-mini"><span>Süre (iş günü)</span>
                <input className="ui-input" type="number" min={0.5} max={60} step={0.5} value={s.estimated_days} disabled={!editable}
                  onChange={(e) => update(i, { estimated_days: e.target.value })} />
              </label>
              <label className="pj-mini"><span>Öncelik</span>
                <select className="ui-input" value={s.priority} disabled={!editable} onChange={(e) => update(i, { priority: e.target.value })}>
                  {Object.entries(PRIORITY).map(([k, l]) => <option key={k} value={k}>{l}</option>)}
                </select>
              </label>
              <div className="wide pj-sub">
                <span>Önce bitmesi gereken adımlar:</span>
                {steps.filter((o) => o.key !== s.key).map((o) => (
                  <label key={o.key} style={{ display: 'inline-flex', gap: 4, alignItems: 'center' }}>
                    <input type="checkbox" disabled={!editable} checked={(s.depends_on || []).includes(o.key)}
                      onChange={(e) => update(i, { depends_on: e.target.checked ? [...(s.depends_on || []), o.key] : s.depends_on.filter((d) => d !== o.key) })} />
                    {o.key}
                  </label>
                ))}
              </div>
              {editable && (
                <div className="pj-step-tools">
                  <button type="button" className="ui-icon-btn" aria-label="Yukarı taşı" disabled={i === 0} onClick={() => move(i, -1)}><ArrowUp size={14} /></button>
                  <button type="button" className="ui-icon-btn" aria-label="Aşağı taşı" disabled={i === steps.length - 1} onClick={() => move(i, 1)}><ArrowDown size={14} /></button>
                  <button type="button" className="ui-icon-btn" aria-label="Adımı sil" onClick={() => remove(i)}><Trash2 size={14} /></button>
                </div>
              )}
            </div>
          </div>
        ))}
        {editable && plan && <Button variant="ghost" icon={Plus} onClick={add}>Adım ekle</Button>}

        {(plan?.hire_suggestions?.length > 0) && (
          <Card title="İşe alım önerileri" subtitle="Havuzda uygun AI personel bulunmayan unvanlar.">
            <ul className="pj-list">
              {plan.hire_suggestions.map((h) => (
                <li key={h.job_title}>
                  <span><strong>{h.job_title}</strong>{h.department ? ` · ${h.department}` : ''}<br /><small className="pj-hint">{h.reason}{h.catalog_title ? ` Katalogda: ${h.catalog_title}.` : ''}</small></span>
                </li>
              ))}
            </ul>
            {project.can_manage && <Button variant="secondary" icon={UserPlus} style={{ marginTop: 10 }} onClick={() => setHireOpen(true)}>AI personel işe al</Button>}
          </Card>
        )}
        {(plan?.risks?.length > 0 || plan?.questions?.length > 0) && (
          <Card title="Beyin AI notları">
            <div className="pj-steps">
              {(plan.risks || []).map((r) => <div key={r} className="pj-note medium">Risk: {r}</div>)}
              {(plan.questions || []).map((q) => <div key={q} className="pj-note info">Soru: {q}</div>)}
            </div>
          </Card>
        )}
      </div>
      {hireOpen && <HireWizard tenantId={project.tenant_id} open onClose={() => setHireOpen(false)} onHired={() => { toast.success('Yeni personel havuza eklendi; adımlara atayabilirsiniz.'); onChanged(); }} />}
    </div>
  );
}

function normalize(s) {
  return { ...s, estimated_days: Number(s.estimated_days) || 1, agent_id: s.agent_id || null };
}
