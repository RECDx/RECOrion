import React, { useCallback, useEffect, useState } from 'react';
import { LayoutTemplate, Plus, Trash2 } from 'lucide-react';
import { api } from '../../api';
import { Badge, Button, Card, EmptyState, Modal } from '../../ui/components';
import { confirmDialog, toast } from '../../ui/feedback';
import './projects.css';

/** Süper Admin › Proje Şablonları (ADIM 11.1): RECDx'in tüm şirketlere açık şablonları. Şirket şablonları burada görünmez (KVKK). */
export default function TemplatesAdmin() {
  const [list, setList] = useState(null);
  const [editing, setEditing] = useState(null);
  const load = useCallback(() => api.getPlatformTemplates().then(setList).catch((e) => toast.error(e.message)), []);
  useEffect(() => { load(); }, [load]);

  const toggle = async (t) => {
    const next = t.status === 'ACTIVE' ? 'ARCHIVED' : 'ACTIVE';
    if (next === 'ARCHIVED' && !(await confirmDialog({ message: `'${t.name}' arşivlensin mi? Şirketler artık bu şablonla proje açamaz; açılmış projeler etkilenmez.` }))) return;
    try { await api.updatePlatformTemplate(t.id, { status: next }); load(); } catch (e) { toast.error(e.message); }
  };

  return (
    <Card title="RECDx proje şablonları" subtitle="Tüm şirketlerin 'Şablondan oluştur' ekranında görünür. Şirketlerin kendi şablonları KVKK gereği burada listelenmez."
      actions={<Button icon={Plus} onClick={() => setEditing({ name: '', category: '', description: '', kind: 'PROJECT', plan: { summary: '', steps: [], risks: [] } })}>Yeni şablon</Button>}>
      {!list ? <p className="pj-hint">Yükleniyor…</p> : list.length === 0 ? <EmptyState icon={LayoutTemplate} title="Şablon yok" description="İlk RECDx şablonunu ekleyin." /> : (
        <div className="ui-table-scroll">
          <table className="ui-table">
            <thead><tr><th>Şablon</th><th>Kategori</th><th>Adım</th><th>Süre</th><th>Kullanım</th><th>Durum</th><th /></tr></thead>
            <tbody>{list.map((t) => (
              <tr key={t.id}>
                <td data-label="Şablon"><strong>{t.name}</strong>{t.kind === 'CASE' && <> <Badge tone="neutral">Case</Badge></>}</td>
                <td data-label="Kategori">{t.category || '—'}</td>
                <td data-label="Adım">{t.step_count}</td>
                <td data-label="Süre">~{t.total_days} gün</td>
                <td data-label="Kullanım">{t.use_count}</td>
                <td data-label="Durum"><Badge tone={t.status === 'ACTIVE' ? 'success' : 'neutral'}>{t.status === 'ACTIVE' ? 'Yayında' : 'Arşivde'}</Badge></td>
                <td data-label="">
                  <div className="pj-actions">
                    <Button size="sm" variant="secondary" onClick={() => setEditing(t)}>Düzenle</Button>
                    <Button size="sm" variant="ghost" onClick={() => toggle(t)}>{t.status === 'ACTIVE' ? 'Arşivle' : 'Yayımla'}</Button>
                  </div>
                </td>
              </tr>
            ))}</tbody>
          </table>
        </div>
      )}
      {editing && <TemplateEditor tpl={editing} onClose={() => setEditing(null)} onSaved={() => { setEditing(null); load(); }} />}
    </Card>
  );
}

const newStep = (i) => ({ key: `S${i}`, title: '', job_title: '', department: '', estimated_days: 1, depends_on: [], requires_approval: true, description: '' });

function TemplateEditor({ tpl, onClose, onSaved }) {
  const [form, setForm] = useState({ name: tpl.name, category: tpl.category || '', description: tpl.description || '', kind: tpl.kind || 'PROJECT' });
  const [steps, setSteps] = useState((tpl.plan?.steps || []).map((s) => ({ ...newStep(0), ...s })));
  const [summary, setSummary] = useState(tpl.plan?.summary || '');
  const [busy, setBusy] = useState(false);
  const setStep = (i, patch) => setSteps((all) => all.map((s, j) => (j === i ? { ...s, ...patch } : s)));
  const add = () => setSteps((all) => {
    const used = new Set(all.map((s) => s.key));
    let n = all.length + 1;
    while (used.has(`S${n}`)) n += 1;
    return [...all, newStep(n)];
  });
  const remove = (i) => setSteps((all) => {
    const key = all[i].key;
    return all.filter((_, j) => j !== i).map((s) => ({ ...s, depends_on: (s.depends_on || []).filter((d) => d !== key) }));
  });

  const save = async () => {
    const clean = steps.filter((s) => s.title.trim());
    if (form.name.trim().length < 2 || clean.length === 0) return toast.warning('Şablon adı ve en az bir adım gerekli.');
    const body = { ...form, name: form.name.trim(), category: form.category.trim() || null, plan: { summary, steps: clean, risks: tpl.plan?.risks || [] } };
    setBusy(true);
    try {
      if (tpl.id) await api.updatePlatformTemplate(tpl.id, body); else await api.createPlatformTemplate(body);
      toast.success(tpl.id ? 'Şablon güncellendi.' : 'Şablon yayımlandı; tüm şirketler görebilir.');
      onSaved();
    } catch (e) { toast.error(e.message); } finally { setBusy(false); }
  };

  return (
    <Modal open onClose={onClose} title={tpl.id ? `${tpl.name} · düzenle` : 'Yeni RECDx şablonu'} size="lg"
      footer={<><Button variant="secondary" onClick={onClose}>Vazgeç</Button><Button onClick={save} disabled={busy}>{busy ? 'Kaydediliyor…' : 'Kaydet'}</Button></>}>
      <div className="pj-form">
        <div className="pj-field"><label htmlFor="ta-name">Ad *</label>
          <input id="ta-name" className="ui-input" value={form.name} maxLength={200} onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))} /></div>
        <div className="pj-field"><label htmlFor="ta-cat">Kategori</label>
          <input id="ta-cat" className="ui-input" value={form.category} maxLength={80} onChange={(e) => setForm((f) => ({ ...f, category: e.target.value }))} /></div>
        {!tpl.id && <div className="pj-field"><label htmlFor="ta-kind">Tür</label>
          <select id="ta-kind" className="ui-input" value={form.kind} onChange={(e) => setForm((f) => ({ ...f, kind: e.target.value }))}>
            <option value="PROJECT">Proje</option><option value="CASE">Case</option></select></div>}
        <div className="pj-field" style={{ gridColumn: '1 / -1' }}><label htmlFor="ta-desc">Açıklama</label>
          <textarea id="ta-desc" className="ui-input" rows={2} value={form.description} maxLength={2000} onChange={(e) => setForm((f) => ({ ...f, description: e.target.value }))} /></div>
        <div className="pj-field" style={{ gridColumn: '1 / -1' }}><label htmlFor="ta-sum">Plan özeti</label>
          <textarea id="ta-sum" className="ui-input" rows={2} value={summary} maxLength={3000} onChange={(e) => setSummary(e.target.value)} /></div>
      </div>
      <h3 style={{ fontSize: '0.9rem', margin: '14px 0 8px' }}>İş adımları</h3>
      <div className="pj-steps" aria-label="Şablon adımları">
        {steps.map((s, i) => (
          <div className="pj-step" key={s.key}>
            <span className="pj-step-key">{s.key}</span>
            <div className="pj-step-body">
              <label className="pj-mini">Başlık<input className="ui-input" aria-label={`${s.key} başlık`} value={s.title} onChange={(e) => setStep(i, { title: e.target.value })} /></label>
              <label className="pj-mini">Unvan (rol)<input className="ui-input" value={s.job_title || ''} onChange={(e) => setStep(i, { job_title: e.target.value })} /></label>
              <label className="pj-mini">Departman<input className="ui-input" value={s.department || ''} onChange={(e) => setStep(i, { department: e.target.value })} /></label>
              <label className="pj-mini">Süre (gün)<input className="ui-input" type="number" min="0.5" step="0.5" value={s.estimated_days} onChange={(e) => setStep(i, { estimated_days: Number(e.target.value) || 1 })} /></label>
              <label className="pj-mini" style={{ gridColumn: '1 / 3' }}>Açıklama<input className="ui-input" value={s.description || ''} onChange={(e) => setStep(i, { description: e.target.value })} /></label>
              <label className="pj-mini">Önce bitmesi gereken<select className="ui-input" multiple value={s.depends_on || []} size={Math.min(3, Math.max(1, i))}
                onChange={(e) => setStep(i, { depends_on: [...e.target.selectedOptions].map((o) => o.value) })}>
                {steps.slice(0, i).map((o) => <option key={o.key} value={o.key}>{o.key} {o.title}</option>)}</select></label>
              <label className="pj-mini">Onay<span><input type="checkbox" checked={s.requires_approval !== false} onChange={(e) => setStep(i, { requires_approval: e.target.checked })} /> gerekli</span></label>
              <div className="pj-step-tools"><button type="button" className="ui-icon-btn" aria-label={`${s.key} adımını sil`} onClick={() => remove(i)}><Trash2 size={14} /></button></div>
            </div>
          </div>
        ))}
      </div>
      <Button variant="secondary" size="sm" icon={Plus} onClick={add} style={{ marginTop: 8 }}>Adım ekle</Button>
    </Modal>
  );
}
