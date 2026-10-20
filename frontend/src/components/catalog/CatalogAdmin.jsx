import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { Building2, Pencil, Plus, Trash2 } from 'lucide-react';
import { api } from '../../api';
import { Badge, Button, Card, DataTable, Modal } from '../../ui/components';
import { confirmDialog, toast } from '../../ui/feedback';
import './catalog.css';

const SENIORITY = { JUNIOR: 'Uzman Yardımcısı', MID: 'Uzman', SENIOR: 'Kıdemli Uzman', LEAD: 'Takım Lideri', MANAGER: 'Yönetici' };
const AUTONOMY = { L1: 'L1 · öneri + insan onayı', L2: 'L2 · rutin işleri kendisi yapar', L3: 'L3 · tam otonom' };
const lines = (v) => (Array.isArray(v) ? v.join('\n') : '');
const toList = (v) => v.split('\n').map((x) => x.trim()).filter(Boolean);

const emptyDept = (sector) => ({ code: '', name: '', description: '', sector_code: sector || '', profession_codes: [], sort_order: 0, is_active: true });
const emptyTitle = (deptId) => ({
  code: '', title: '', catalog_department_id: deptId || '', description: '', responsibilities: '', required_skills: '', kpis: '',
  seniority: 'MID', profession_codes: [], recommended_model_code: '', autonomy_level: 'L1', base_role_prompt: '', is_active: true,
});

function ProfessionPicker({ value, onChange, professions }) {
  if (!professions.length) return <span className="cat-hint">Genel kayıtlar tüm meslek gruplarına uygundur.</span>;
  return (
    <div className="cat-depts">
      {professions.map((p) => {
        const on = value.includes(p.code);
        return (
          <button type="button" key={p.code} className={`cat-dept ${on ? 'active' : ''}`} title={p.name}
            onClick={() => onChange(on ? value.filter((c) => c !== p.code) : [...value, p.code])}>
            {p.code} {p.name}
          </button>
        );
      })}
    </div>
  );
}

/** Süper Admin: platform departman ve unvan kataloğu (Platform Unvan Bilgisi). */
export default function CatalogAdmin() {
  const [summary, setSummary] = useState(null);
  const [sector, setSector] = useState('GENERAL');
  const [departments, setDepartments] = useState([]);
  const [deptId, setDeptId] = useState('');
  const [titles, setTitles] = useState({ total: 0, items: [] });
  const [professions, setProfessions] = useState([]);
  const [models, setModels] = useState([]);
  const [deptForm, setDeptForm] = useState(null);
  const [titleForm, setTitleForm] = useState(null);
  const [saving, setSaving] = useState(false);

  const loadSummary = useCallback(() => api.getCatalogSummary().then(setSummary).catch((e) => toast.error(e.message)), []);
  const loadDepartments = useCallback(() => api.getCatalogDepartments({ sector_code: sector, include_inactive: true })
    .then(setDepartments).catch((e) => toast.error(e.message)), [sector]);
  const loadTitles = useCallback(() => api.getCatalogTitles({ sector_code: deptId ? '' : sector, catalog_department_id: deptId, include_inactive: true, limit: 1000 })
    .then(setTitles).catch((e) => toast.error(e.message)), [sector, deptId]);

  useEffect(() => {
    loadSummary();
    api.getProfessions().then(setProfessions).catch(() => {});
    api.getModels().then((m) => setModels(m.filter((x) => x.status === 'ACTIVE' && ['CHAT', 'VISION', 'DECISION'].includes(x.model_type)))).catch(() => {});
  }, [loadSummary]);
  useEffect(() => { loadDepartments(); }, [loadDepartments]);
  useEffect(() => { loadTitles(); }, [loadTitles]);

  const deptById = useMemo(() => Object.fromEntries(departments.map((d) => [d.id, d])), [departments]);
  const sectorProfessions = (code) => professions.filter((p) => code && code !== 'GENERAL' && p.sector_code === code);
  const refreshAll = () => { loadSummary(); loadDepartments(); loadTitles(); };

  const openTitle = async (row) => {
    try {
      const t = await api.getCatalogTitle(row.id);
      setTitleForm({ ...t, responsibilities: lines(t.responsibilities), required_skills: lines(t.required_skills), kpis: lines(t.kpis), recommended_model_code: t.recommended_model_code || '' });
    } catch (e) { toast.error(e.message); }
  };

  const saveDept = async () => {
    setSaving(true);
    try {
      const data = { ...deptForm, sector_code: deptForm.sector_code || null, sort_order: Number(deptForm.sort_order) || 0 };
      if (deptForm.id) await api.updateCatalogDepartment(deptForm.id, data); else await api.createCatalogDepartment(data);
      toast.success('Departman kaydedildi.');
      setDeptForm(null); refreshAll();
    } catch (e) { toast.error(e.message); } finally { setSaving(false); }
  };

  const deleteDept = async (d) => {
    if (!(await confirmDialog({ message: `"${d.name}" katalog departmanı silinsin mi?`, danger: true }))) return;
    try { await api.deleteCatalogDepartment(d.id); toast.success('Departman silindi.'); setDeptId(''); refreshAll(); } catch (e) { toast.error(e.message); }
  };

  const saveTitle = async () => {
    setSaving(true);
    try {
      const data = {
        ...titleForm, responsibilities: toList(titleForm.responsibilities), required_skills: toList(titleForm.required_skills),
        kpis: toList(titleForm.kpis), recommended_model_code: titleForm.recommended_model_code || null,
      };
      if (titleForm.id) await api.updateCatalogTitle(titleForm.id, data); else await api.createCatalogTitle(data);
      toast.success('Unvan kaydedildi.');
      setTitleForm(null); refreshAll();
    } catch (e) { toast.error(e.message); } finally { setSaving(false); }
  };

  const deleteTitle = async () => {
    if (!(await confirmDialog({ message: `"${titleForm.title}" unvanı silinsin mi? Şirketlerde kullanılıyorsa pasife alınır.`, danger: true }))) return;
    try {
      const r = await api.deleteCatalogTitle(titleForm.id);
      toast.success(r.message || 'Unvan silindi.');
      setTitleForm(null); refreshAll();
    } catch (e) { toast.error(e.message); }
  };

  const selectedDept = deptById[deptId];
  const titleDeptSector = titleForm ? deptById[titleForm.catalog_department_id]?.sector_code || (sector !== 'GENERAL' ? sector : null) : null;
  const deptOptions = departments;

  return (
    <div className="cat-main">
      <Card
        title="Departman & Unvan Kataloğu"
        subtitle={summary ? `${summary.total_departments} departman · ${summary.total_titles} unvan. Katalog tüm müşterilere açık genel bilgidir (Platform Unvan Bilgisi); şirkete özel bilgi yazmayın.` : 'Yükleniyor…'}
        actions={(
          <>
            <Button variant="secondary" size="sm" icon={Building2} onClick={() => setDeptForm(emptyDept(sector === 'GENERAL' ? '' : sector))}>Yeni Departman</Button>
            <Button size="sm" icon={Plus} disabled={!departments.length} onClick={() => setTitleForm(emptyTitle(deptId || departments[0]?.id))}>Yeni Unvan</Button>
          </>
        )}
      />

      <div className="cat-layout">
        <nav className="cat-sectors" aria-label="Sektörler">
          {(summary?.sectors || []).map((s) => {
            const key = s.sector_code || 'GENERAL';
            return (
              <button key={key} type="button" className={`cat-sector ${sector === key ? 'active' : ''}`} onClick={() => { setSector(key); setDeptId(''); }}>
                <span>{s.sector_code ? `${s.sector_code} · ` : ''}{s.sector_name}</span>
                <small>{s.departments} / {s.titles}</small>
              </button>
            );
          })}
        </nav>

        <div className="cat-main">
          <Card title="Departmanlar" subtitle="Bir departman seçerek unvanlarını süzün. Üzeri çizili olanlar pasif.">
            <div className="cat-depts">
              <button type="button" className={`cat-dept ${!deptId ? 'active' : ''}`} onClick={() => setDeptId('')}>Tümü</button>
              {departments.map((d) => (
                <button type="button" key={d.id} className={`cat-dept ${deptId === d.id ? 'active' : ''} ${d.is_active ? '' : 'inactive'}`} onClick={() => setDeptId(d.id)}>
                  {d.name} <small>{d.title_count}</small>
                </button>
              ))}
            </div>
            {selectedDept && (
              <div style={{ marginTop: 12, display: 'flex', gap: 8, flexWrap: 'wrap', alignItems: 'center' }}>
                <span className="cat-hint" style={{ flex: 1 }}>{selectedDept.code} · {selectedDept.description || 'Açıklama yok'}{selectedDept.profession_codes.length ? ` · Meslek grupları: ${selectedDept.profession_codes.join(', ')}` : ''}</span>
                <Button variant="ghost" size="sm" icon={Pencil} onClick={() => setDeptForm({ ...selectedDept, sector_code: selectedDept.sector_code || '' })}>Düzenle</Button>
                <Button variant="ghost" size="sm" icon={Trash2} onClick={() => deleteDept(selectedDept)}>Sil</Button>
              </div>
            )}
          </Card>

          <Card title={`Unvanlar (${titles.total})`}>
            <DataTable
              rows={titles.items}
              pageSize={25}
              onRowClick={openTitle}
              searchPlaceholder="Unvan, kod veya iş tanımı ara…"
              columns={[
                { key: 'title', label: 'Unvan', render: (r) => <span style={{ fontWeight: 600 }}>{r.title}</span>, searchValue: (r) => `${r.title} ${r.code} ${r.description || ''}` },
                { key: 'category', label: 'Departman', hideOnMobile: true },
                { key: 'seniority', label: 'Kıdem', render: (r) => SENIORITY[r.seniority] || '—' },
                { key: 'profession_codes', label: 'Meslek grupları', hideOnMobile: true, sortable: false, render: (r) => (r.profession_codes.length ? r.profession_codes.join(', ') : 'Tümü') },
                { key: 'recommended_model_code', label: 'Model', hideOnMobile: true, render: (r) => r.recommended_model_code || '—' },
                { key: 'is_active', label: 'Durum', render: (r) => <Badge tone={r.is_active ? 'success' : 'neutral'}>{r.is_active ? 'Aktif' : 'Pasif'}</Badge> },
              ]}
              emptyText="Bu seçimde unvan yok."
            />
          </Card>
        </div>
      </div>

      <Modal open={!!deptForm} onClose={() => setDeptForm(null)} title={deptForm?.id ? 'Katalog Departmanını Düzenle' : 'Yeni Katalog Departmanı'} size="lg"
        footer={<><Button variant="secondary" onClick={() => setDeptForm(null)}>Vazgeç</Button><Button onClick={saveDept} disabled={saving}>Kaydet</Button></>}>
        {deptForm && (
          <div className="cat-form">
            <div className="cat-field"><label htmlFor="cd-code">Kod</label><input id="cd-code" className="ui-input" value={deptForm.code} onChange={(e) => setDeptForm({ ...deptForm, code: e.target.value.toUpperCase() })} placeholder="Örn. A_URETIM" /></div>
            <div className="cat-field"><label htmlFor="cd-name">Ad</label><input id="cd-name" className="ui-input" value={deptForm.name} onChange={(e) => setDeptForm({ ...deptForm, name: e.target.value })} /></div>
            <div className="cat-field"><label htmlFor="cd-sector">Sektör</label>
              <select id="cd-sector" className="ui-input" value={deptForm.sector_code} onChange={(e) => setDeptForm({ ...deptForm, sector_code: e.target.value, profession_codes: [] })}>
                <option value="">Genel (tüm sektörler)</option>
                {(summary?.sectors || []).filter((s) => s.sector_code).map((s) => <option key={s.sector_code} value={s.sector_code}>{s.sector_code} · {s.sector_name}</option>)}
              </select>
            </div>
            <div className="cat-field"><label htmlFor="cd-order">Sıra</label><input id="cd-order" type="number" className="ui-input" value={deptForm.sort_order} onChange={(e) => setDeptForm({ ...deptForm, sort_order: e.target.value })} /></div>
            <div className="cat-field full"><label htmlFor="cd-desc">Açıklama</label><textarea id="cd-desc" className="ui-input" rows={2} value={deptForm.description || ''} onChange={(e) => setDeptForm({ ...deptForm, description: e.target.value })} /></div>
            <div className="cat-field full"><label>Tipik meslek grupları</label><ProfessionPicker value={deptForm.profession_codes} professions={sectorProfessions(deptForm.sector_code)} onChange={(v) => setDeptForm({ ...deptForm, profession_codes: v })} /></div>
            <label className="cat-field full" style={{ flexDirection: 'row', alignItems: 'center', gap: 8 }}>
              <input type="checkbox" checked={deptForm.is_active} onChange={(e) => setDeptForm({ ...deptForm, is_active: e.target.checked })} /> Aktif
            </label>
          </div>
        )}
      </Modal>

      <Modal open={!!titleForm} onClose={() => setTitleForm(null)} title={titleForm?.id ? titleForm.title : 'Yeni Katalog Unvanı'} size="lg"
        footer={(
          <>
            {titleForm?.id && <Button variant="danger" icon={Trash2} onClick={deleteTitle}>Sil</Button>}
            <Button variant="secondary" onClick={() => setTitleForm(null)}>Vazgeç</Button>
            <Button onClick={saveTitle} disabled={saving}>Kaydet</Button>
          </>
        )}>
        {titleForm && (
          <div className="cat-form">
            <div className="cat-field"><label htmlFor="ct-title">Unvan</label><input id="ct-title" className="ui-input" value={titleForm.title} onChange={(e) => setTitleForm({ ...titleForm, title: e.target.value })} /></div>
            <div className="cat-field"><label htmlFor="ct-code">Kod</label><input id="ct-code" className="ui-input" value={titleForm.code} onChange={(e) => setTitleForm({ ...titleForm, code: e.target.value.toUpperCase() })} /></div>
            <div className="cat-field"><label htmlFor="ct-dept">Departman</label>
              <select id="ct-dept" className="ui-input" value={titleForm.catalog_department_id} onChange={(e) => setTitleForm({ ...titleForm, catalog_department_id: e.target.value })}>
                {(deptOptions.some((d) => d.id === titleForm.catalog_department_id) ? [] : [<option key="cur" value={titleForm.catalog_department_id}>{titleForm.category || 'Mevcut departman'}</option>])}
                {deptOptions.map((d) => <option key={d.id} value={d.id}>{d.name}</option>)}
              </select>
              <span className="cat-hint">Liste seçili sektörün departmanlarını gösterir.</span>
            </div>
            <div className="cat-field"><label htmlFor="ct-sen">Kıdem</label>
              <select id="ct-sen" className="ui-input" value={titleForm.seniority || ''} onChange={(e) => setTitleForm({ ...titleForm, seniority: e.target.value || null })}>
                {Object.entries(SENIORITY).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
              </select>
            </div>
            <div className="cat-field"><label htmlFor="ct-model">Önerilen model</label>
              <select id="ct-model" className="ui-input" value={titleForm.recommended_model_code} onChange={(e) => setTitleForm({ ...titleForm, recommended_model_code: e.target.value })}>
                <option value="">Platform varsayılanı</option>
                {models.map((m) => <option key={m.model_code} value={m.model_code}>{m.display_name} ({m.model_code})</option>)}
              </select>
            </div>
            <div className="cat-field"><label htmlFor="ct-aut">Otonomi</label>
              <select id="ct-aut" className="ui-input" value={titleForm.autonomy_level} onChange={(e) => setTitleForm({ ...titleForm, autonomy_level: e.target.value })}>
                {Object.entries(AUTONOMY).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
              </select>
            </div>
            <div className="cat-field full"><label htmlFor="ct-desc">İş tanımı</label><textarea id="ct-desc" className="ui-input" rows={3} value={titleForm.description || ''} onChange={(e) => setTitleForm({ ...titleForm, description: e.target.value })} /></div>
            <div className="cat-field"><label htmlFor="ct-resp">Sorumluluklar (her satır bir madde)</label><textarea id="ct-resp" className="ui-input" rows={6} value={titleForm.responsibilities} onChange={(e) => setTitleForm({ ...titleForm, responsibilities: e.target.value })} /></div>
            <div className="cat-field"><label htmlFor="ct-skill">Yetkinlikler (her satır bir madde)</label><textarea id="ct-skill" className="ui-input" rows={6} value={titleForm.required_skills} onChange={(e) => setTitleForm({ ...titleForm, required_skills: e.target.value })} /></div>
            <div className="cat-field full"><label htmlFor="ct-kpi">Başarı ölçütleri (her satır bir madde)</label><textarea id="ct-kpi" className="ui-input" rows={3} value={titleForm.kpis} onChange={(e) => setTitleForm({ ...titleForm, kpis: e.target.value })} /></div>
            <div className="cat-field full"><label htmlFor="ct-prompt">Rol promptu</label>
              <textarea id="ct-prompt" className="ui-input" rows={10} value={titleForm.base_role_prompt} onChange={(e) => setTitleForm({ ...titleForm, base_role_prompt: e.target.value })} />
              <span className="cat-hint">{'{{company_name}}'} ve {'{{department_name}}'} işe alımda şirket ve departman adıyla doldurulur.</span>
            </div>
            <div className="cat-field full"><label>Uygun meslek grupları (boş: departmanın tüm meslek grupları)</label>
              <ProfessionPicker value={titleForm.profession_codes} professions={sectorProfessions(titleDeptSector)} onChange={(v) => setTitleForm({ ...titleForm, profession_codes: v })} />
            </div>
            <label className="cat-field full" style={{ flexDirection: 'row', alignItems: 'center', gap: 8 }}>
              <input type="checkbox" checked={titleForm.is_active} onChange={(e) => setTitleForm({ ...titleForm, is_active: e.target.checked })} /> Aktif (pasif unvanlar yeni işe alımlarda görünmez)
            </label>
          </div>
        )}
      </Modal>
    </div>
  );
}

