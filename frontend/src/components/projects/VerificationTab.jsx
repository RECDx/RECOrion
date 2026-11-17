import React, { useCallback, useEffect, useState } from 'react';
import { ClipboardCheck, Link2, Paperclip, Ruler, StickyNote } from 'lucide-react';
import { api } from '../../api';
import { Badge, Button, Card, EmptyState, Modal } from '../../ui/components';
import { toast } from '../../ui/feedback';
import { VERIFY_TONE } from './projectMeta';

/**
 * Doğrulama sekmesi (#752): kapsam raporu — "N teslimattan M tanesi doğrulandı" — ve adım bazında kanıt, ölçüm, kontrol listesi.
 * Kayıtları adımın sorumlusu, onaylayıcısı, kontrol personeli ya da proje yöneticisi girer (sunucu denetler).
 */
export default function VerificationTab({ project }) {
  const [cov, setCov] = useState(null);
  const [editing, setEditing] = useState(null);
  const load = useCallback(() => api.getProjectVerification(project.id).then(setCov).catch((e) => toast.error(e.message)), [project.id]);
  useEffect(() => { load(); }, [load]);

  if (!cov) return <Card title="Teslimat doğrulaması"><p className="pj-hint">Yükleniyor…</p></Card>;
  const c = cov.counts;
  return (
    <div className="pj-steps">
      <Card title="Teslimat doğrulaması" subtitle="Her adımın teslimatı, planda yazılan yöntemle doğrulanır; doğrulanmayan adım onaya gelince uyarı görünür, eksikle kabul gerekçe ister.">
        <p className="pj-note info" role="status" aria-label="Kapsam özeti" style={{ margin: 0 }}><strong>{cov.summary}</strong></p>
        <div className="pj-stats" style={{ marginTop: 10 }}>
          <div className="pj-stat"><span>Doğrulandı</span><strong>{c.VERIFIED}</strong></div>
          <div className="pj-stat"><span>Eksik</span><strong>{c.MISSING}</strong></div>
          <div className="pj-stat"><span>Gerekçeyle kabul</span><strong>{c.WAIVED}</strong></div>
          <div className="pj-stat"><span>Bekliyor</span><strong>{c.PENDING}</strong></div>
        </div>
      </Card>
      {cov.rows.length === 0 ? (
        <EmptyState icon={ClipboardCheck} title="Teslimat yok" description="Plan onaylandığında adımların teslimatları burada listelenir." />
      ) : (
        <Card title="Teslimatlar">
          <ul className="pj-list" aria-label="Teslimatlar">
            {cov.rows.map((r) => (
              <li key={r.task_id} style={{ flexWrap: 'wrap' }}>
                <span style={{ flex: 1, minWidth: 240 }}>
                  <strong>{r.deliverable || r.title}</strong> <Badge tone={VERIFY_TONE[r.status] || 'neutral'}>{r.status_label}</Badge><br />
                  <small className="pj-hint">Adım: {r.title} · {r.type_label}{r.method ? ` — ${r.method}` : ''}</small><br />
                  <small className="pj-hint">{r.reason}</small>
                  {r.evidence.length > 0 && (
                    <ul className="pj-list" aria-label={`${r.title}: kanıtlar`}>
                      {r.evidence.map((e, i) => (
                        <li key={i}><span>{e.kind === 'link' ? <a href={e.url} target="_blank" rel="noreferrer">{e.text || e.url}</a> : e.name || e.text}</span></li>
                      ))}
                    </ul>
                  )}
                </span>
                {r.type && r.task_status !== 'DONE' && r.task_status !== 'CANCELLED' && (
                  <Button size="sm" variant="secondary" onClick={() => setEditing(r)}>
                    {r.type === 'MEASURE' ? 'Ölçüm gir' : r.type === 'CHECKLIST' ? 'Kontrol listesi' : 'Kanıt ekle'}
                  </Button>
                )}
              </li>
            ))}
          </ul>
        </Card>
      )}
      {editing && <RecordModal project={project} row={editing} onClose={() => setEditing(null)} onSaved={() => { setEditing(null); load(); }} />}
    </div>
  );
}

function RecordModal({ project, row, onClose, onSaved }) {
  const [kind, setKind] = useState('note');
  const [text, setText] = useState('');
  const [url, setUrl] = useState('');
  const [doc, setDoc] = useState('');
  const [docs, setDocs] = useState([]);
  const [measure, setMeasure] = useState({ value: row.measure?.value || '', unit: row.measure?.unit || '', note: row.measure?.note || '' });
  const [items, setItems] = useState((row.checklist || []).map((i) => !!i.ok));
  const [busy, setBusy] = useState(false);
  useEffect(() => {
    if (row.type !== 'MEASURE' && row.type !== 'CHECKLIST') api.getProjectDocuments(project.id).then(setDocs).catch(() => setDocs([]));
  }, [project.id, row.type]);

  const save = async () => {
    setBusy(true);
    try {
      let r;
      if (row.type === 'MEASURE') r = await api.setVerificationMeasure(row.task_id, measure);
      else if (row.type === 'CHECKLIST') r = await api.setVerificationChecklist(row.task_id, items);
      else r = await api.addVerificationEvidence(row.task_id, { kind, text: text || null, url: kind === 'link' ? url : null, document_id: kind === 'document' ? doc : null });
      toast.success(r.status === 'VERIFIED' ? 'Teslimat doğrulandı.' : `Kaydedildi. ${r.reason}`);
      onSaved();
    } catch (e) { toast.error(e.message); } finally { setBusy(false); }
  };

  return (
    <Modal open onClose={onClose} title={`${row.deliverable || row.title} · doğrulama`} size="md"
      footer={<><Button variant="secondary" onClick={onClose}>Vazgeç</Button><Button onClick={save} disabled={busy}>{busy ? 'Kaydediliyor…' : 'Kaydet'}</Button></>}>
      <p className="pj-hint">{row.type_label}{row.method ? `: ${row.method}` : ''}</p>
      {row.type === 'MEASURE' && (
        <div className="pj-form">
          <label className="pj-field">Ölçülen değer *<input id="vf-value" className="ui-input" value={measure.value} maxLength={60}
            onChange={(e) => setMeasure((m) => ({ ...m, value: e.target.value }))} placeholder="62" /></label>
          <label className="pj-field">Birim<input className="ui-input" value={measure.unit} maxLength={30}
            onChange={(e) => setMeasure((m) => ({ ...m, unit: e.target.value }))} placeholder="%" /></label>
          <label className="pj-field" style={{ gridColumn: '1 / -1' }}>Not<textarea className="ui-input" rows={2} value={measure.note} maxLength={500}
            onChange={(e) => setMeasure((m) => ({ ...m, note: e.target.value }))} placeholder="Nasıl ve ne zaman ölçüldü" /></label>
        </div>
      )}
      {row.type === 'CHECKLIST' && (
        <div className="pj-steps" role="group" aria-label="Kontrol listesi">
          {(row.checklist || []).map((it, i) => (
            <label key={i} className="pj-hint" style={{ display: 'flex', gap: 8 }}>
              <input type="checkbox" checked={!!items[i]} onChange={(e) => setItems((x) => x.map((v, j) => (j === i ? e.target.checked : v)))} />
              {it.item}
            </label>
          ))}
        </div>
      )}
      {row.type !== 'MEASURE' && row.type !== 'CHECKLIST' && (
        <div className="pj-form">
          <div className="pj-actions" role="radiogroup" aria-label="Kanıt türü" style={{ gridColumn: '1 / -1' }}>
            <Button size="sm" variant={kind === 'note' ? 'primary' : 'ghost'} icon={StickyNote} onClick={() => setKind('note')}>Not</Button>
            <Button size="sm" variant={kind === 'link' ? 'primary' : 'ghost'} icon={Link2} onClick={() => setKind('link')}>Bağlantı</Button>
            <Button size="sm" variant={kind === 'document' ? 'primary' : 'ghost'} icon={Paperclip} onClick={() => setKind('document')}>Proje Eki</Button>
          </div>
          {kind === 'link' && <label className="pj-field" style={{ gridColumn: '1 / -1' }}>Adres *<input id="vf-url" className="ui-input" value={url}
            onChange={(e) => setUrl(e.target.value)} placeholder="https://…" /></label>}
          {kind === 'document' && (
            <label className="pj-field" style={{ gridColumn: '1 / -1' }}>Proje Eki *
              <select id="vf-doc" className="ui-input" value={doc} onChange={(e) => setDoc(e.target.value)}>
                <option value="">Seçin</option>
                {docs.map((d) => <option key={d.id} value={d.id}>{d.original_name || d.name}</option>)}
              </select>
            </label>
          )}
          <label className="pj-field" style={{ gridColumn: '1 / -1' }}>{kind === 'note' ? 'Kanıt notu *' : 'Açıklama'}
            <textarea id="vf-text" className="ui-input" rows={3} value={text} maxLength={1000} onChange={(e) => setText(e.target.value)}
              placeholder="Ne kontrol edildi, sonuç ne" /></label>
        </div>
      )}
      {row.type === 'MEASURE' && <p className="pj-hint"><Ruler size={13} /> Değer, planda yazılan hedefle onaylayıcı tarafından karşılaştırılır.</p>}
    </Modal>
  );
}
