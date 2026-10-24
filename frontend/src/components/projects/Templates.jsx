import React, { useEffect, useMemo, useState } from 'react';
import { LayoutTemplate } from 'lucide-react';
import { api } from '../../api';
import { Badge, Button, EmptyState, Modal } from '../../ui/components';
import { toast } from '../../ui/feedback';

/** Proje şablonu galerisi (ADIM 11.1): şirketin ve RECDx'in şablonları; seçilen şablondan yeni proje. */
export function TemplateGallery({ currentUser, onClose, onCreated }) {
  const [list, setList] = useState(null);
  const [scope, setScope] = useState('ALL');
  const [picked, setPicked] = useState(null);
  const [detail, setDetail] = useState(null);
  const [name, setName] = useState('');
  const [start, setStart] = useState('');
  const [busy, setBusy] = useState(false);

  useEffect(() => { api.getProjectTemplates().then(setList).catch((e) => { toast.error(e.message); setList([]); }); }, []);
  useEffect(() => {
    if (!picked) return;
    setDetail(null);
    api.getProjectTemplate(picked.id).then(setDetail).catch((e) => toast.error(e.message));
  }, [picked]);
  const shown = useMemo(() => (list || []).filter((t) => scope === 'ALL' || t.scope === scope), [list, scope]);

  const create = async () => {
    if (name.trim().length < 2) return toast.warning('Proje adını yazın.');
    setBusy(true);
    try {
      const r = await api.useProjectTemplate(picked.id, { name: name.trim(), manager_actor_id: currentUser?.actor_id || null, start_date: start || null });
      toast.success(r.unmatched_roles?.length
        ? `'${r.name}' oluşturuldu. ${r.matched_steps} adıma AI personel atandı; şirkette olmayan roller: ${r.unmatched_roles.join(', ')}.`
        : `'${r.name}' oluşturuldu; planı inceleyip onaylayın.`);
      onCreated(r);
    } catch (e) { toast.error(e.message); } finally { setBusy(false); }
  };

  return (
    <Modal open onClose={onClose} title={picked ? picked.name : 'Şablondan proje oluştur'} size="lg"
      footer={picked
        ? <><Button variant="secondary" onClick={() => setPicked(null)}>Şablonlara dön</Button><Button onClick={create} disabled={busy}>{busy ? 'Oluşturuluyor…' : 'Projeyi oluştur'}</Button></>
        : <Button variant="secondary" onClick={onClose}>Vazgeç</Button>}>
      {!picked ? (
        <>
          <div className="ui-segmented" role="tablist" style={{ marginBottom: 12 }}>
            {[['ALL', 'Tümü'], ['COMPANY', 'Şirketimizin'], ['PLATFORM', 'RECDx hazır']].map(([k, l]) => (
              <button key={k} type="button" className={`ui-segmented-item ${scope === k ? 'active' : ''}`} onClick={() => setScope(k)}>{l}</button>
            ))}
          </div>
          {!list ? <p className="pj-hint">Yükleniyor…</p> : shown.length === 0 ? (
            <EmptyState icon={LayoutTemplate} title="Şablon yok" description="Biten bir projenizin planını 'Şablon olarak kaydet' ile şirket şablonu yapabilirsiniz." />
          ) : (
            <div className="pj-grid" role="list" aria-label="Proje şablonları">
              {shown.map((t) => (
                <button key={t.id} type="button" role="listitem" className="pj-card" onClick={() => { setPicked(t); setName(t.name); }}>
                  <span className="pj-meta"><Badge tone={t.scope === 'PLATFORM' ? 'info' : 'neutral'}>{t.scope === 'PLATFORM' ? 'RECDx' : 'Şirket'}</Badge>
                    {t.category && <span>{t.category}</span>}{t.kind === 'CASE' && <span>Case</span>}</span>
                  <strong>{t.name}</strong>
                  {t.description && <span className="pj-hint">{t.description}</span>}
                  <span className="pj-meta"><span>{t.step_count} adım</span><span>~{t.total_days} iş günü</span>
                    {t.use_count > 0 && <span>{t.use_count} kez kullanıldı</span>}</span>
                </button>
              ))}
            </div>
          )}
        </>
      ) : (
        <>
          {picked.description && <p className="pj-hint">{picked.description}</p>}
          <div className="pj-form" style={{ margin: '12px 0' }}>
            <div className="pj-field">
              <label htmlFor="tpl-name">Proje adı *</label>
              <input id="tpl-name" className="ui-input" value={name} maxLength={255} onChange={(e) => setName(e.target.value)} />
            </div>
            <div className="pj-field">
              <label htmlFor="tpl-start">Başlangıç tarihi</label>
              <input id="tpl-start" className="ui-input" type="date" value={start} onChange={(e) => setStart(e.target.value)} />
            </div>
          </div>
          {!detail ? <p className="pj-hint">Yükleniyor…</p> : (
            <ol className="pj-list" aria-label="Şablon adımları">
              {detail.plan.steps.map((s) => (
                <li key={s.key}>
                  <span><strong>{s.title}</strong><br />
                    <small className="pj-hint">{[s.job_title, s.department, `${s.estimated_days} gün`, s.depends_on?.length ? `önce: ${s.depends_on.join(', ')}` : null,
                      s.requires_approval === false ? 'onaysız' : null].filter(Boolean).join(' · ')}</small></span>
                </li>
              ))}
            </ol>
          )}
          <p className="pj-hint" style={{ marginTop: 10 }}>Plan taslak olarak gelir: unvanı uyan AI personel adımlara atanır, onaylayıcılar boş gelir (proje yöneticisi).
            Planı inceleyip Beyin AI ile düzenleyebilir, sonra onaylarsınız.</p>
        </>
      )}
    </Modal>
  );
}

/** Projeden şirket şablonu (ADIM 11.1): kişi kimlikleri, çıktılar ve ekler şablona girmez. */
export function SaveTemplateModal({ project, onClose }) {
  const [form, setForm] = useState({ name: project.name, description: project.description || '', category: '', keep_descriptions: true });
  const [busy, setBusy] = useState(false);
  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.type === 'checkbox' ? e.target.checked : e.target.value }));
  const save = async () => {
    setBusy(true);
    try {
      await api.saveProjectAsTemplate(project.id, { ...form, name: form.name.trim(), category: form.category.trim() || null });
      toast.success('Şablon kaydedildi; şirketinizdeki herkes Yeni Proje › Şablondan oluştur ile kullanabilir.');
      onClose();
    } catch (e) { toast.error(e.message); } finally { setBusy(false); }
  };
  return (
    <Modal open onClose={onClose} title="Şablon olarak kaydet" size="md"
      footer={<><Button variant="secondary" onClick={onClose}>Vazgeç</Button><Button onClick={save} disabled={busy || form.name.trim().length < 2}>{busy ? 'Kaydediliyor…' : 'Kaydet'}</Button></>}>
      <div className="pj-form">
        <div className="pj-field">
          <label htmlFor="st-name">Şablon adı *</label>
          <input id="st-name" className="ui-input" value={form.name} maxLength={200} onChange={set('name')} />
        </div>
        <div className="pj-field">
          <label htmlFor="st-cat">Kategori</label>
          <input id="st-cat" className="ui-input" value={form.category} maxLength={80} placeholder="ör. Pazarlama" onChange={set('category')} />
        </div>
        <div className="pj-field" style={{ gridColumn: '1 / -1' }}>
          <label htmlFor="st-desc">Açıklama</label>
          <textarea id="st-desc" className="ui-input" rows={3} value={form.description} maxLength={2000} onChange={set('description')} />
        </div>
      </div>
      <label className="pj-hint" style={{ display: 'flex', gap: 8, marginTop: 10 }}>
        <input type="checkbox" checked={form.keep_descriptions} onChange={set('keep_descriptions')} />
        Adım açıklamalarını ve kabul ölçütlerini de al (projeye özgü bilgi içeriyorsa işareti kaldırın)
      </label>
      <p className="pj-hint" style={{ marginTop: 8 }}>Şablona adımlar, roller, süreler, bağımlılıklar ve onay ayarları girer. Atanan kişiler, çıktılar, ekler ve yazışmalar girmez.
        Şablon yalnızca şirketinizde görünür.</p>
    </Modal>
  );
}
