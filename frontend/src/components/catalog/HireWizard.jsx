import React, { useEffect, useMemo, useState } from 'react';
import { ArrowLeft, ArrowRight, Bot, Check, Lock, Search } from 'lucide-react';
import { api } from '../../api';
import { Badge, Button, EmptyState, Modal } from '../../ui/components';
import { toast } from '../../ui/feedback';
import { AUTONOMY, SENIORITY } from './labels';
import RecaiCapabilities from '../recai/RecaiCapabilities';
import './catalog.css';

const STEPS = ['Departman', 'Unvan', 'RECAi ve Rol', 'Kimlik'];
const DEPT_GROUPS = [
  [-1, 'Şirketinizin departmanları'],
  [0, 'Meslek grubunuza özel (katalog)'],
  [1, 'Sektörünüze özel (katalog)'],
  [2, 'Genel departmanlar (katalog)'],
];
const today = () => new Date().toISOString().split('T')[0];

/**
 * AI personel işe alım sihirbazı (ADIM 5.3): Sektör (şirket tanımından) > Departman > Unvan > LLM > Rol promptu.
 * Katalogdan seçilen departman ve unvan işe alımda şirkete eklenir. Paket izin vermiyorsa model ve rol promptu kilitlidir.
 */
export default function HireWizard({ tenantId, open, onClose, onHired }) {
  const [step, setStep] = useState(0);
  const [options, setOptions] = useState(null);
  const [query, setQuery] = useState('');
  const [dept, setDept] = useState(null);
  const [titles, setTitles] = useState(null);
  const [title, setTitle] = useState(null);
  const [preview, setPreview] = useState(null);
  const [form, setForm] = useState({ display_name: '', description: '', hired_at: today(), autonomy_level: 'L1', model_code: '', recai_capabilities: {}, system_prompt: '' });
  const [saving, setSaving] = useState(false);
  // #349: RECAi kodu (MERGEN/HIZLI/DERIN) → görünen ad
  const recaiName = (code) => options?.models?.find((m) => m.model_code === code)?.display_name || (code ? 'RECAi' : 'RECAi Mergen');

  useEffect(() => {
    if (!open) return;
    setStep(0); setDept(null); setTitle(null); setTitles(null); setPreview(null); setQuery(''); setOptions(null);
    setForm({ display_name: '', description: '', hired_at: today(), autonomy_level: 'L1', model_code: '', recai_capabilities: {}, system_prompt: '' });
    api.getHireOptions(tenantId).then(setOptions).catch((e) => toast.error(e.message));
  }, [open, tenantId]);

  useEffect(() => {
    if (!dept) return;
    setTitles(null); setTitle(null);
    api.getHireTitles(tenantId, { department_id: dept.department_id, catalog_department_id: dept.catalog_department_id })
      .then(setTitles).catch((e) => toast.error(e.message));
  }, [dept, tenantId]);

  useEffect(() => {
    if (!title || !dept) return;
    setPreview(null);
    api.getHirePreview(tenantId, title.id, dept.name).then((p) => {
      setPreview(p);
      setForm((f) => ({ ...f, model_code: p.model_code || '', system_prompt: p.role_prompt, autonomy_level: p.autonomy_level || 'L1', description: p.description || '' }));
    }).catch((e) => toast.error(e.message));
  }, [title, dept, tenantId]);

  const ent = options?.entitlements || {};
  const q = query.trim().toLocaleLowerCase('tr');
  const depts = useMemo(() => (options?.departments || []).filter((d) => !q || `${d.name} ${d.description || ''}`.toLocaleLowerCase('tr').includes(q)), [options, q]);
  const visibleTitles = useMemo(() => (titles || []).filter((t) => !q || `${t.title} ${t.description || ''}`.toLocaleLowerCase('tr').includes(q)), [titles, q]);
  const canNext = [!!dept, !!title, !!preview && (!!form.model_code || !ent.can_change_llm), !!form.display_name.trim()][step];

  const go = (n) => { setQuery(''); setStep(n); };

  const submit = async () => {
    setSaving(true);
    try {
      const payload = {
        display_name: form.display_name.trim(),
        description: form.description.trim() || null,
        hired_at: new Date(form.hired_at || today()).toISOString(),
        autonomy_level: form.autonomy_level,
        department_id: dept.department_id || null,
        catalog_department_id: dept.department_id ? null : dept.catalog_department_id,
        ...(title.kind === 'CATALOG' ? { catalog_title_id: title.id } : { job_title_id: title.id }),
        model_code: ent.can_change_llm ? form.model_code : undefined,
        recai_capabilities: form.recai_capabilities,
        system_prompt: ent.can_edit_role_prompt && form.system_prompt.trim() !== preview.role_prompt ? form.system_prompt.trim() : undefined,
      };
      const created = await api.hireAIAgent(tenantId, payload);
      toast.success(`'${created.display_name}' ${created.department_name || ''} departmanında ${created.job_title_name} olarak işe alındı.`);
      onHired?.(created);
      onClose();
    } catch (e) {
      toast.error(e.message);
    } finally {
      setSaving(false);
    }
  };

  const footer = (
    <>
      {step > 0 && <Button variant="secondary" icon={ArrowLeft} onClick={() => go(step - 1)}>Geri</Button>}
      {step < 3
        ? <Button icon={ArrowRight} onClick={() => go(step + 1)} disabled={!canNext}>İleri</Button>
        : <Button icon={Check} onClick={submit} disabled={!canNext || saving || options?.quota?.is_limit_reached}>İşe Al</Button>}
    </>
  );

  return (
    <Modal open={open} onClose={onClose} title="AI Personel İşe Al" size="lg" footer={footer}>
      {!options ? <p className="cat-hint">Yükleniyor…</p> : (
        <div className="cat-main" style={{ gap: 14 }}>
          <div className="hire-steps" role="list">
            {STEPS.map((s, i) => (
              <button type="button" role="listitem" key={s} className={`hire-step ${i === step ? 'active' : ''} ${i < step ? 'done' : ''}`}
                disabled={i > step} onClick={() => i < step && go(i)}>
                <span>{i < step ? <Check size={12} /> : i + 1}</span>{s}
              </button>
            ))}
          </div>

          <div className="hire-summary">
            <span>Sektör: <strong>{options.sectors.map((s) => s.name).join(', ') || 'Tanımlı değil'}</strong></span>
            {dept && <span>Departman: <strong>{dept.name}</strong></span>}
            {title && <span>Unvan: <strong>{title.title}</strong></span>}
            {options.quota.max_agents != null && <span>Kota: <strong>{options.quota.active_agents} / {options.quota.max_agents}</strong></span>}
          </div>
          {options.quota.is_limit_reached && <Badge tone="danger">'{ent.plan_name}' paketinizin AI personel kotası dolu. İşe almak için paket yükseltin veya bir personeli pasife alın.</Badge>}

          {step < 2 && (
            <label className="ui-search" style={{ maxWidth: 420, flex: '0 0 auto' }}>
              <Search size={15} />
              <input value={query} onChange={(e) => setQuery(e.target.value)} placeholder={step === 0 ? 'Departman ara…' : 'Unvan ara…'} aria-label="Ara" />
            </label>
          )}

          {step === 0 && (
            <div className="cat-pick">
              {DEPT_GROUPS.map(([rank, label]) => {
                const rows = depts.filter((d) => d.rank === rank);
                if (!rows.length) return null;
                return (
                  <React.Fragment key={rank}>
                    <strong style={{ fontSize: '0.8rem', marginTop: 6 }}>{label}</strong>
                    {rows.map((d) => (
                      <label key={d.key} className={dept?.key === d.key ? 'selected' : ''}>
                        <input type="radio" name="hire-dept" checked={dept?.key === d.key} onChange={() => setDept(d)} />
                        <span style={{ flex: 1 }}>
                          {d.name} {d.profession_match && <Badge tone="info">Meslek grubunuz</Badge>}
                          <p>{d.description || 'Açıklama yok'}{d.title_count ? ` · ${d.title_count} uygun unvan` : ''}{d.source === 'CATALOG' ? ' · işe alımda şirketinize eklenir' : ''}</p>
                        </span>
                      </label>
                    ))}
                  </React.Fragment>
                );
              })}
              {!depts.length && <EmptyState title="Departman bulunamadı" description="Aramanızı değiştirin." />}
            </div>
          )}

          {step === 1 && (
            <div className="cat-pick">
              {!titles ? <p className="cat-hint">Unvanlar yükleniyor…</p> : visibleTitles.length === 0 ? (
                <EmptyState icon={Bot} title="Bu departmanda uygun unvan yok" description="Başka bir departman seçin veya Ünvan Tanımları sekmesinden şirketinize özel unvan ekleyin." />
              ) : visibleTitles.map((t) => (
                <label key={t.id} className={title?.id === t.id ? 'selected' : ''}>
                  <input type="radio" name="hire-title" checked={title?.id === t.id} onChange={() => setTitle(t)} />
                  <span style={{ flex: 1 }}>
                    {t.title}{' '}
                    {t.seniority && <Badge tone="neutral">{SENIORITY[t.seniority]}</Badge>}{' '}
                    {t.kind === 'COMPANY' ? <Badge tone="success">Şirketinizde tanımlı</Badge> : t.profession_match && <Badge tone="info">Meslek grubunuza uygun</Badge>}
                    <p>{t.description}</p>
                  </span>
                </label>
              ))}
            </div>
          )}

          {step === 2 && (!preview ? <p className="cat-hint">Unvan bilgileri hazırlanıyor…</p> : (
            <div className="cat-form">
              <div className="cat-field">
                <label htmlFor="hw-model">RECAi {!ent.can_change_llm && <Lock size={12} />}</label>
                <select id="hw-model" className="ui-input" value={form.model_code} disabled={!ent.can_change_llm} onChange={(e) => setForm({ ...form, model_code: e.target.value })}>
                  {!form.model_code && <option value="">Seçin…</option>}
                  {options.models.map((m) => <option key={m.model_code} value={m.model_code} disabled={m.available === false}>{m.display_name}{m.description ? ` — ${m.description}` : ''} · katsayı {m.effort_coefficient}{m.available === false ? ' (paketinizde yok)' : ''}</option>)}
                </select>
                <span className="cat-hint">
                  {ent.can_change_llm
                    ? (preview.recommended_model_code ? `Bu unvan için önerilen: ${recaiName(preview.recommended_model_code)}` : 'Unvanın önerdiği RECAi paketinizde yok; listeden seçin.')
                    : `'${ent.plan_name}' paketiniz RECAi değiştirmeye izin vermiyor; bu unvan için ${recaiName(form.model_code)} kullanılır.`}
                </span>
              </div>
              <RecaiCapabilities capabilities={options.capabilities || []} value={form.recai_capabilities}
                                 onChange={(caps) => setForm({ ...form, recai_capabilities: caps })} />
              <div className="cat-field">
                <label htmlFor="hw-aut">Otonomi</label>
                <select id="hw-aut" className="ui-input" value={form.autonomy_level} onChange={(e) => setForm({ ...form, autonomy_level: e.target.value })}>
                  {['L1', 'L2'].map((k) => <option key={k} value={k}>{AUTONOMY[k]}</option>)}
                </select>
              </div>
              {preview.responsibilities.length > 0 && (
                <div className="cat-field full">
                  <label>Sorumluluklar</label>
                  <ul style={{ margin: 0, paddingLeft: 18, fontSize: '0.82rem', color: 'var(--text-muted)' }}>
                    {preview.responsibilities.map((r) => <li key={r}>{r}</li>)}
                  </ul>
                </div>
              )}
              <div className="cat-field full">
                <label htmlFor="hw-prompt">Rol promptu {!ent.can_edit_role_prompt && <Lock size={12} />}</label>
                <textarea id="hw-prompt" className="ui-input" rows={9} value={form.system_prompt} readOnly={!ent.can_edit_role_prompt}
                  onChange={(e) => setForm({ ...form, system_prompt: e.target.value })} />
                <span className="cat-hint">
                  {ent.can_edit_role_prompt ? 'Şirketinize göre düzenleyebilirsiniz.' : `'${ent.plan_name}' paketiniz rol promptunu değiştirmeye izin vermiyor; RECOrion kataloğundaki hazır rol promptu kullanılır.`}
                </span>
              </div>
            </div>
          ))}

          {step === 3 && (
            <div className="cat-form">
              <div className="cat-field">
                <label htmlFor="hw-name">AI personel adı</label>
                <input id="hw-name" className="ui-input" maxLength={128} value={form.display_name} onChange={(e) => setForm({ ...form, display_name: e.target.value })} placeholder={`Örn. ${title?.title?.split(' ')[0] || 'Orion'} Asistanı`} autoFocus />
              </div>
              <div className="cat-field">
                <label htmlFor="hw-date">İşe alım tarihi</label>
                <input id="hw-date" type="date" className="ui-input" value={form.hired_at} onChange={(e) => setForm({ ...form, hired_at: e.target.value })} />
              </div>
              <div className="cat-field full">
                <label htmlFor="hw-desc">Açıklama</label>
                <textarea id="hw-desc" className="ui-input" rows={3} value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} />
              </div>
              <span className="cat-hint full">
                İşe alımdan sonra AI Ajan İşe Alım sekmesinden personele öğrenme dokümanı ekleyebilir veya sektör ve unvan araştırması yaptırabilirsiniz.
              </span>
            </div>
          )}
        </div>
      )}
    </Modal>
  );
}
