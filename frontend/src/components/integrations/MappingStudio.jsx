import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { CheckCircle2, FlaskConical, Plus, Save, Sparkles, Trash2, Wand2 } from 'lucide-react';
import { api } from '../../api';
import { Badge, Button, EmptyState, Modal } from '../../ui/components';
import { confirmDialog, toast } from '../../ui/feedback';

const TRANSFORMS = [
  ['copy', 'Kopyala'], ['const', 'Sabit değer'], ['map', 'Değer eşle'], ['contains', 'Listede varsa'],
  ['template', 'Metin şablonu'], ['lookup', 'Hedefte ara (Odoo)'], ['lines', 'Kalemler (Odoo)'],
];
const NEEDS_SOURCE = ['copy', 'map', 'contains', 'lookup', 'lines'];
const JSON_PARAMS = ['map', 'contains', 'lookup', 'lines'];
const DEFAULT_MODEL = { PRODUCT: 'product.template', PARTNER: 'res.partner', ORDER: 'sale.order', TASK: 'project.task' };
const STATUS = { DRAFT: ['Taslak', 'warning'], ACTIVE: ['Onaylı', 'success'] };

/** Eşleme stüdyosu (ADIM 12.3): ortak iş nesnesi → bu bağlantıdaki hedef. Deneme yazmaz; onaydan sonra aktarımda kullanılır. */
export default function MappingStudio({ tenantId, conn, onClose }) {
  const [objects, setObjects] = useState(null);
  const [list, setList] = useState(null);
  const [templates, setTemplates] = useState([]);
  const [editing, setEditing] = useState(null);
  const [creating, setCreating] = useState(false);
  const load = useCallback(() => Promise.all([
    api.getBusinessObjects().then((d) => setObjects(d.objects)), api.getMappings(tenantId, conn.id).then(setList),
    api.getMappingTemplates(tenantId, conn.connector).then(setTemplates),
  ]).catch((e) => toast.error(e.message)), [tenantId, conn.id, conn.connector]);
  useEffect(() => { load(); }, [load]);

  if (editing) {
    return <MappingEditor tenantId={tenantId} conn={conn} mapping={editing} objects={objects}
      onClose={() => { setEditing(null); load(); }} />;
  }
  if (creating && objects) {
    return <NewMapping tenantId={tenantId} conn={conn} objects={objects} templates={templates}
      onClose={() => setCreating(false)} onCreated={(m) => { setCreating(false); setEditing(m); }} />;
  }
  return (
    <Modal open onClose={onClose} title={`${conn.name} · eşlemeler`} size="lg"
      footer={<><Button variant="secondary" onClick={onClose}>Kapat</Button><Button icon={Plus} onClick={() => setCreating(true)}>Yeni eşleme</Button></>}>
      <p className="pj-hint">Eşleme, RECAi'nin ürettiği ortak iş nesnesinin (ürün kartı, cari, teklif...) bu sistemde hangi alanlara yazılacağını belirler.
        Onaylanan eşleme, iş çıktısını bu sisteme aktarırken kullanılır; her aktarım yine önizleme ve onaydan geçer.</p>
      {!list ? <p className="pj-hint">Yükleniyor…</p> : list.length === 0 ? (
        <EmptyState icon={Wand2} title="Henüz eşleme yok" description="RECDx hazır eşlemesinden başlayın veya RECAi'ye önerdirin." />
      ) : (
        <ul className="pj-list" aria-label="Eşlemeler">
          {list.map((m) => {
            const [label, tone] = STATUS[m.status] || [m.status, 'neutral'];
            return (
              <li key={m.id}>
                <span><strong>{m.name}</strong> <Badge tone={tone}>{label}</Badge><br />
                  <small className="pj-hint">{m.object_label} → {m.target.model || m.target.tool} · {m.rules.length} kural · sürüm {m.version}
                    {m.last_dry_run ? ` · son deneme: ${m.last_dry_run.ok ? 'hatasız' : 'hatalı'}` : ''}</small></span>
                <Button size="sm" variant="secondary" onClick={() => setEditing(m)}>Aç</Button>
              </li>
            );
          })}
        </ul>
      )}
    </Modal>
  );
}

function NewMapping({ tenantId, conn, objects, templates, onClose, onCreated }) {
  const [objectType, setObjectType] = useState('PRODUCT');
  const [target, setTarget] = useState(conn.connector === 'odoo' ? DEFAULT_MODEL.PRODUCT : '');
  const [tools, setTools] = useState([]);
  const [busy, setBusy] = useState(false);
  useEffect(() => {
    if (conn.connector !== 'odoo') api.getIntegrationTools(tenantId, conn.id).then((t) => setTools(t.filter((x) => x.kind === 'WRITE'))).catch((e) => toast.error(e.message));
  }, [tenantId, conn.id, conn.connector]);
  const label = objects.find((o) => o.code === objectType)?.label;
  const create = async (body) => {
    setBusy(true);
    try { onCreated(await api.createMapping(tenantId, { connection_id: conn.id, ...body })); } catch (e) { toast.error(e.message); } finally { setBusy(false); }
  };
  return (
    <Modal open onClose={onClose} title="Yeni eşleme" size="md"
      footer={<><Button variant="secondary" onClick={onClose}>Vazgeç</Button>
        <Button disabled={busy || !target} onClick={() => create({ object_type: objectType, name: `${label} → ${target}`, target: conn.connector === 'odoo' ? { model: target } : { tool: target }, rules: [] })}>Boş eşleme oluştur</Button></>}>
      {templates.length > 0 && (
        <>
          <p className="pj-hint">RECDx hazır eşlemesinden başlayın (sonra şirketinize göre düzeltebilirsiniz):</p>
          <ul className="pj-list" aria-label="Hazır eşlemeler">
            {templates.map((t) => (
              <li key={t.id}>
                <span><strong>{t.name}</strong><br /><small className="pj-hint">{t.description}</small></span>
                <Button size="sm" disabled={busy} onClick={() => create({ object_type: t.object_type, name: t.name, template_id: t.id })}>Bununla başla</Button>
              </li>
            ))}
          </ul>
        </>
      )}
      <div className="pj-form" style={{ marginTop: 12 }}>
        <div className="pj-field">
          <label htmlFor="mp-object">Nesne</label>
          <select id="mp-object" className="ui-input" value={objectType} onChange={(e) => { setObjectType(e.target.value); if (conn.connector === 'odoo') setTarget(DEFAULT_MODEL[e.target.value] || ''); }}>
            {objects.map((o) => <option key={o.code} value={o.code}>{o.label}</option>)}
          </select>
        </div>
        <div className="pj-field">
          <label htmlFor="mp-target">{conn.connector === 'odoo' ? 'Odoo modeli' : 'Araç / şablon'}</label>
          {conn.connector === 'odoo' ? (
            <input id="mp-target" className="ui-input" value={target} onChange={(e) => setTarget(e.target.value.trim())} placeholder="ör. product.template" />
          ) : (
            <select id="mp-target" className="ui-input" value={target} onChange={(e) => setTarget(e.target.value)}>
              <option value="">Seçin</option>
              {tools.map((t) => <option key={t.name} value={t.name}>{t.name}</option>)}
            </select>
          )}
        </div>
      </div>
    </Modal>
  );
}

const paramText = (r) => {
  if (r.transform === 'const') return r.params?.value === undefined ? '' : JSON.stringify(r.params.value);
  if (r.transform === 'template') return r.params?.text || '';
  return JSON_PARAMS.includes(r.transform) && r.params && Object.keys(r.params).length ? JSON.stringify(r.params) : '';
};

function MappingEditor({ tenantId, conn, mapping, objects, onClose }) {
  const [m, setM] = useState(mapping);
  const [fields, setFields] = useState(null);
  const [rows, setRows] = useState(mapping.rules.map((r) => ({ ...r, ptext: paramText(r) })));
  const [match, setMatch] = useState(mapping.match || { source: '', target: '' });
  const [dirty, setDirty] = useState(false);
  const [check, setCheck] = useState(mapping.last_check);
  const [dry, setDry] = useState(mapping.last_dry_run);
  const [notes, setNotes] = useState('');
  const [busy, setBusy] = useState('');
  const obj = objects.find((o) => o.code === m.object_type);
  const sources = useMemo(() => obj?.fields || [], [obj]);
  useEffect(() => {
    api.getTargetFields(tenantId, conn.id, m.target).then(setFields).catch((e) => { toast.error(e.message); setFields([]); });
  }, [tenantId, conn.id, m.target]);

  const setRow = (i, patch) => { setRows((rs) => rs.map((r, j) => (j === i ? { ...r, ...patch } : r))); setDirty(true); };
  const rulesFromRows = () => rows.filter((r) => r.target).map((r) => {
    let params = {};
    if (r.transform === 'const') {
      try { params = { value: r.ptext === '' ? '' : JSON.parse(r.ptext) }; } catch { params = { value: r.ptext }; }
    } else if (r.transform === 'template') params = { text: r.ptext };
    else if (JSON_PARAMS.includes(r.transform) && r.ptext.trim()) params = JSON.parse(r.ptext);
    return { target: r.target, transform: r.transform, source: NEEDS_SOURCE.includes(r.transform) ? r.source || null : null, params };
  });
  const save = async () => {
    let rules;
    try { rules = rulesFromRows(); } catch { toast.warning('Parametre alanı geçerli JSON olmalı.'); return null; }
    setBusy('save');
    try {
      const saved = await api.updateMapping(tenantId, m.id, { rules, match: match.source && match.target ? match : null });
      setM(saved); setRows(saved.rules.map((r) => ({ ...r, ptext: paramText(r) }))); setDirty(false);
      toast.success(saved.status === 'DRAFT' ? 'Kaydedildi; onay için yeniden deneyin.' : 'Kaydedildi.');
      return saved;
    } catch (e) { toast.error(e.message); return null; } finally { setBusy(''); }
  };
  const runCheck = async () => {
    if (dirty && !(await save())) return;
    setBusy('check');
    try { setCheck(await api.checkMapping(tenantId, m.id)); } catch (e) { toast.error(e.message); } finally { setBusy(''); }
  };
  const runDry = async () => {
    if (dirty && !(await save())) return;
    setBusy('dry');
    try { setDry(await api.dryRunMapping(tenantId, m.id)); } catch (e) { toast.error(e.message); } finally { setBusy(''); }
  };
  const approve = async () => {
    setBusy('approve');
    try { setM(await api.approveMapping(tenantId, m.id)); toast.success('Eşleme onaylandı; aktarımlarda kullanılacak.'); } catch (e) { toast.error(e.message); } finally { setBusy(''); }
  };
  const suggest = async () => {
    if (rows.length && !(await confirmDialog({ message: 'RECAi önerisi mevcut kuralların yerine geçecek. Devam edilsin mi?' }))) return;
    setBusy('suggest');
    try {
      const s = await api.suggestMapping(tenantId, { connection_id: conn.id, object_type: m.object_type, target: m.target });
      setRows(s.rules.map((r) => ({ ...r, ptext: paramText(r) })));
      if (s.match) setMatch(s.match);
      setNotes(s.notes + (s.dropped ? ` (Hedefte olmayan ${s.dropped} alan önerisi atıldı.)` : ''));
      setDirty(true);
      toast.success('RECAi eşleme önerdi; inceleyip kaydedin.');
    } catch (e) { toast.error(e.message); } finally { setBusy(''); }
  };
  const [label, tone] = STATUS[m.status] || [m.status, 'neutral'];
  const canApprove = !dirty && dry?.ok && dry?.version === m.version && m.status !== 'ACTIVE';

  return (
    <Modal open onClose={onClose} title={m.name} size="lg"
      footer={<>
        <Button variant="secondary" onClick={onClose}>Kapat</Button>
        <Button variant="secondary" icon={Save} disabled={!!busy || !dirty} onClick={save}>Kaydet</Button>
        <Button variant="secondary" icon={CheckCircle2} disabled={!!busy} onClick={runCheck}>{busy === 'check' ? 'Denetleniyor…' : 'Denetle'}</Button>
        <Button variant="secondary" icon={FlaskConical} disabled={!!busy} onClick={runDry}>{busy === 'dry' ? 'Deneniyor…' : 'Dene (yazmadan)'}</Button>
        <Button icon={CheckCircle2} disabled={!!busy || !canApprove} onClick={approve}>Onayla</Button>
      </>}>
      <p className="pj-meta"><Badge tone={tone}>{label}</Badge><span>{obj?.label} → {m.target.model || m.target.tool}</span><span>sürüm {m.version}</span></p>
      <div className="pj-actions" style={{ margin: '8px 0' }}>
        <Button size="sm" icon={Sparkles} disabled={!!busy || !fields} onClick={suggest}>{busy === 'suggest' ? 'RECAi hazırlıyor…' : 'RECAi önersin'}</Button>
        <Button size="sm" variant="secondary" icon={Plus} onClick={() => { setRows((r) => [...r, { target: '', transform: 'copy', source: '', ptext: '' }]); setDirty(true); }}>Kural ekle</Button>
      </div>
      {notes && <p className="ig-advice">{notes}</p>}
      {!fields ? <p className="pj-hint">Hedef alanları okunuyor…</p> : (
        <div className="ui-table-scroll">
          <table className="ui-table" aria-label="Eşleme kuralları">
            <thead><tr><th>Hedef alan</th><th>Dönüşüm</th><th>Kaynak</th><th>Parametre</th><th /></tr></thead>
            <tbody>{rows.map((r, i) => (
              <tr key={i}>
                <td data-label="Hedef alan">
                  <select className="ui-input" aria-label={`Kural ${i + 1} hedef`} value={r.target} onChange={(e) => setRow(i, { target: e.target.value })}>
                    <option value="">Seçin</option>
                    {!fields.some((f) => f.name === r.target) && r.target && <option value={r.target}>{r.target} (hedefte yok)</option>}
                    {fields.map((f) => <option key={f.name} value={f.name}>{f.required ? '* ' : ''}{f.label} ({f.name})</option>)}
                  </select>
                </td>
                <td data-label="Dönüşüm">
                  <select className="ui-input" aria-label={`Kural ${i + 1} dönüşüm`} value={r.transform} onChange={(e) => setRow(i, { transform: e.target.value })}>
                    {TRANSFORMS.filter(([k]) => conn.connector === 'odoo' || !['lookup', 'lines'].includes(k)).map(([k, l]) => <option key={k} value={k}>{l}</option>)}
                  </select>
                </td>
                <td data-label="Kaynak">
                  {NEEDS_SOURCE.includes(r.transform) ? (
                    <select className="ui-input" aria-label={`Kural ${i + 1} kaynak`} value={r.source || ''} onChange={(e) => setRow(i, { source: e.target.value })}>
                      <option value="">Seçin</option>
                      {sources.map((f) => <option key={f.key} value={f.key}>{f.label}</option>)}
                    </select>
                  ) : <span className="pj-hint">—</span>}
                </td>
                <td data-label="Parametre">
                  {r.transform === 'copy' ? <span className="pj-hint">—</span> : (
                    <input className="ui-input ig-inline" aria-label={`Kural ${i + 1} parametre`} value={r.ptext} onChange={(e) => setRow(i, { ptext: e.target.value })}
                      placeholder={r.transform === 'const' ? 'ör. true, 1, "metin"' : r.transform === 'template' ? 'ör. {name} ({code})' : '{"values": {...}}'} />
                  )}
                </td>
                <td data-label=""><Button size="sm" variant="ghost" icon={Trash2} aria-label={`Kural ${i + 1} sil`} onClick={() => { setRows((rs) => rs.filter((_, j) => j !== i)); setDirty(true); }} /></td>
              </tr>
            ))}</tbody>
          </table>
        </div>
      )}
      <div className="pj-form" style={{ marginTop: 10 }}>
        <div className="pj-field">
          <label htmlFor="mp-match-s">Tekrar aktarımda eşleştir: kaynak</label>
          <select id="mp-match-s" className="ui-input" value={match.source || ''} onChange={(e) => { setMatch((x) => ({ ...x, source: e.target.value })); setDirty(true); }}>
            <option value="">Yok (her aktarım yeni kayıt)</option>
            {sources.filter((f) => f.type !== 'lines').map((f) => <option key={f.key} value={f.key}>{f.label}</option>)}
          </select>
        </div>
        <div className="pj-field">
          <label htmlFor="mp-match-t">hedef alan</label>
          <select id="mp-match-t" className="ui-input" value={match.target || ''} onChange={(e) => { setMatch((x) => ({ ...x, target: e.target.value })); setDirty(true); }}>
            <option value="">Seçin</option>
            {(fields || []).map((f) => <option key={f.name} value={f.name}>{f.label} ({f.name})</option>)}
          </select>
        </div>
      </div>
      {check && (
        <div className="ig-steps" aria-label="Denetim sonucu">
          <p><strong>Denetim:</strong> {check.ok ? 'hata yok' : `${check.errors.length} hata`}{check.version !== m.version ? ' (eski sürüm)' : ''}</p>
          {check.errors.map((e, i) => <p key={`e${i}`} className="ui-text-danger">• {e}</p>)}
          {check.warnings.map((e, i) => <p key={`w${i}`} className="pj-hint">• {e}</p>)}
        </div>
      )}
      {dry && (
        <div className="ig-steps" aria-label="Deneme sonucu">
          <p><strong>Deneme (yazılmadı):</strong> {dry.ok ? (dry.action === 'UPDATE' ? `mevcut kayıt #${dry.existing_id} güncellenecek` : 'yeni kayıt açılacak') : 'hatalı'}
            {dry.version !== m.version ? ' (eski sürüm; yeniden deneyin)' : ''}</p>
          {dry.preview.length > 0 && (
            <table className="ui-table" aria-label="Hedefe gidecek değerler">
              <thead><tr><th>Hedef alan</th><th>Değer</th><th>Kaynak</th></tr></thead>
              <tbody>{dry.preview.map((p) => <tr key={p.target}><td data-label="Hedef alan">{p.label} <small className="pj-hint">({p.target})</small></td>
                <td data-label="Değer">{p.value}</td><td data-label="Kaynak">{p.source || p.transform}</td></tr>)}</tbody>
            </table>
          )}
          {dry.errors.map((e, i) => <p key={`e${i}`} className="ui-text-danger">• {e}</p>)}
          {dry.warnings.map((e, i) => <p key={`w${i}`} className="pj-hint">• {e}</p>)}
        </div>
      )}
    </Modal>
  );
}
