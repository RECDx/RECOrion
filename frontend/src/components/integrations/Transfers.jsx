import React, { useCallback, useEffect, useState } from 'react';
import { ExternalLink, RotateCcw, Send, Sparkles, Undo2, Wrench } from 'lucide-react';
import { api } from '../../api';
import { Badge, Button, Card, EmptyState, Modal } from '../../ui/components';
import { confirmDialog, promptDialog, toast } from '../../ui/feedback';
import './integrations.css';

export const TRANSFER_STATUS = {
  EXTRACTING: ['RECAi hazırlıyor', 'info'], NEEDS_FIX: ['Düzeltme gerekli', 'warning'], PENDING_APPROVAL: ['Onay bekliyor', 'warning'],
  APPROVED: ['Kuyrukta', 'info'], RUNNING: ['Yazılıyor', 'info'], DONE: ['Aktarıldı', 'success'], FAILED: ['Hata', 'danger'],
  REJECTED: ['Reddedildi', 'neutral'], ROLLED_BACK: ['Geri alındı', 'neutral'],
};
const TRIGGER = { MANUAL: 'elle', STEP_DONE: 'adım bitince', PROJECT_CLOSED: 'proje kapanınca' };
const fmt = (d) => (d ? new Date(d).toLocaleString('tr-TR', { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' }) : '');
const money = (n) => (n ? `${Number(n).toLocaleString('tr-TR', { maximumFractionDigits: 2 })} ₺` : '');
const titleOf = (tr) => tr.object?.name || tr.object?.title || tr.object?.partner_ref || tr.object?.code || tr.object_label;

let objectsCache = null;
const loadObjects = () => (objectsCache ||= api.getBusinessObjects().then((d) => d.objects).catch((e) => { objectsCache = null; throw e; }));

/** Tek aktarım: durum, önizleme (hedefe gidecek değerler), sorunlar ve eylemler. */
export function TransferCard({ tr, canManage, decide, onChange }) {
  const [fixing, setFixing] = useState(false);
  const [label, tone] = TRANSFER_STATUS[tr.status] || [tr.status, 'neutral'];
  const act = async (fn, ok) => { try { await fn(); toast.success(ok); onChange?.(); } catch (e) { toast.error(e.message); } };
  const rollback = async () => {
    if (!(await confirmDialog({ message: tr.action === 'UPDATE' ? 'Kaydın eski değerleri geri yazılsın mı?' : 'Açılan kayıt arşivlensin (siparişte iptal edilsin) mi?', danger: true }))) return;
    act(() => api.rollbackTransfer(tr.id), 'Geri alındı.');
  };
  const decideIt = async (approve) => {
    const note = approve ? '' : await promptDialog({ title: 'Reddet', message: 'Ret gerekçesi (isteğe bağlı):' });
    if (note === null) return;
    act(() => api.decideTransfer(tr.id, approve, note), approve ? 'Onaylandı; aktarım kuyruğa alındı.' : 'Reddedildi; aktarım yapılmayacak.');
  };
  const approvedCount = (tr.approvals || []).filter((a) => a.approve).length;
  return (
    <li className="ig-transfer" aria-label={`Aktarım: ${titleOf(tr)}`}>
      <div className="ig-transfer-head">
        <span><strong>{tr.object_label}: {titleOf(tr)}</strong> <Badge tone={tone}>{label}</Badge><br />
          <small className="pj-hint">{tr.connection_name} · {tr.action === 'UPDATE' ? 'mevcut kaydı günceller' : tr.action === 'CREATE' ? 'yeni kayıt açar' : ''}
            {tr.amount ? ` · ${money(tr.amount)}` : ''} · {TRIGGER[tr.trigger] || tr.trigger} · {fmt(tr.created_at)}
            {tr.required_approvals > 1 ? ` · çift onay (${approvedCount}/${tr.required_approvals})` : ''}</small></span>
        <span className="pj-actions">
          {tr.external_url && tr.status === 'DONE' && <a className="ig-link" href={tr.external_url} target="_blank" rel="noreferrer"><ExternalLink size={14} /> {tr.external_ref}</a>}
          {decide && <Button size="sm" onClick={() => decideIt(true)}>Onayla ve aktar</Button>}
          {decide && <Button size="sm" variant="secondary" onClick={() => decideIt(false)}>Reddet</Button>}
          {canManage && ['NEEDS_FIX', 'PENDING_APPROVAL'].includes(tr.status) && <Button size="sm" variant="secondary" icon={Wrench} onClick={() => setFixing(true)}>Düzelt</Button>}
          {canManage && tr.status === 'DONE' && tr.connection_name && <Button size="sm" variant="ghost" icon={Undo2} onClick={rollback}>Geri al</Button>}
          {canManage && tr.status === 'FAILED' && approvedCount >= tr.required_approvals && <Button size="sm" variant="secondary" icon={RotateCcw} onClick={() => act(() => api.retryTransfer(tr.id), 'Yeniden kuyruğa alındı.')}>Yeniden dene</Button>}
        </span>
      </div>
      {tr.preview?.length > 0 && tr.status !== 'DONE' && (
        <table className="ui-table" aria-label="Hedefe gidecek değerler">
          <thead><tr><th>Hedef alan</th><th>Değer</th></tr></thead>
          <tbody>{tr.preview.map((p) => <tr key={p.target}><td data-label="Hedef alan">{p.label} <small className="pj-hint">({p.target})</small></td><td data-label="Değer">{p.value}</td></tr>)}</tbody>
        </table>
      )}
      {(tr.problems?.errors || []).map((e, i) => <p key={`e${i}`} className="ui-text-danger">• {e}</p>)}
      {(tr.problems?.warnings || []).map((e, i) => <p key={`w${i}`} className="pj-hint">• {e}</p>)}
      {tr.error && <p className="ui-text-danger">• {tr.error}</p>}
      {(tr.approvals || []).map((a, i) => <p key={`a${i}`} className="pj-hint">{a.approve ? '✓' : '✗'} {a.name} · {fmt(a.at)}{a.note ? ` · “${a.note}”` : ''}</p>)}
      {fixing && <FixModal tr={tr} onClose={() => setFixing(false)} onSaved={() => { setFixing(false); onChange?.(); }} />}
    </li>
  );
}

/** Önerinin nesnesini düzeltme: ortak nesnenin alanları; kalemler JSON. */
function FixModal({ tr, onClose, onSaved }) {
  const [spec, setSpec] = useState(null);
  const [obj, setObj] = useState({ ...tr.object });
  const [lines, setLines] = useState(JSON.stringify(tr.object?.lines || [], null, 1));
  const [busy, setBusy] = useState(false);
  useEffect(() => { loadObjects().then((o) => setSpec(o.find((x) => x.code === tr.object_type))).catch((e) => toast.error(e.message)); }, [tr.object_type]);
  const save = async () => {
    const body = { ...obj };
    if (spec?.fields.some((f) => f.type === 'lines')) {
      try { body.lines = JSON.parse(lines || '[]'); } catch { toast.warning('Kalemler geçerli JSON olmalı.'); return; }
    }
    setBusy(true);
    try {
      const r = await api.fixTransfer(tr.id, body);
      r.status === 'PENDING_APPROVAL' ? toast.success('Düzeltildi; önizleme yenilendi ve onaya gönderildi.') : toast.warning('Hâlâ eksik veya hatalı alan var.');
      onSaved();
    } catch (e) { toast.error(e.message); } finally { setBusy(false); }
  };
  return (
    <Modal open onClose={onClose} title={`${tr.object_label} · düzelt`} size="md"
      footer={<><Button variant="secondary" onClick={onClose}>Vazgeç</Button><Button disabled={busy || !spec} onClick={save}>Kaydet ve önizle</Button></>}>
      {!spec ? <p className="pj-hint">Yükleniyor…</p> : (
        <div className="pj-form">
          {spec.fields.map((f) => (
            <div className={`pj-field ${['text', 'lines'].includes(f.type) ? 'full' : ''}`} key={f.key}>
              <label htmlFor={`tf-${f.key}`}>{f.label}{f.required ? ' *' : ''}</label>
              {f.type === 'lines' ? (
                <textarea id={`tf-${f.key}`} className="ui-input ig-inline" rows={5} value={lines} onChange={(e) => setLines(e.target.value)} />
              ) : f.type === 'enum' ? (
                <select id={`tf-${f.key}`} className="ui-input" value={obj[f.key] || ''} onChange={(e) => setObj((o) => ({ ...o, [f.key]: e.target.value || undefined }))}>
                  <option value="">—</option>
                  {f.options.map((o) => <option key={o} value={o}>{f.option_labels?.[o] || o}</option>)}
                </select>
              ) : f.type === 'list' ? (
                <input id={`tf-${f.key}`} className="ui-input" value={(obj[f.key] || []).join(', ')} placeholder={f.options.join(', ')}
                  onChange={(e) => setObj((o) => ({ ...o, [f.key]: e.target.value.split(',').map((x) => x.trim()).filter(Boolean) }))} />
              ) : f.type === 'text' ? (
                <textarea id={`tf-${f.key}`} className="ui-input" rows={3} value={obj[f.key] || ''} onChange={(e) => setObj((o) => ({ ...o, [f.key]: e.target.value }))} />
              ) : (
                <input id={`tf-${f.key}`} className="ui-input" type={f.type === 'number' ? 'number' : f.type === 'date' ? 'date' : 'text'} value={obj[f.key] ?? ''}
                  onChange={(e) => setObj((o) => ({ ...o, [f.key]: e.target.value === '' ? undefined : f.type === 'number' ? Number(e.target.value) : e.target.value }))} />
              )}
            </div>
          ))}
        </div>
      )}
    </Modal>
  );
}

/** Adım çıktısını dış sisteme aktarma (proje yöneticisi): eşleme seç → RECAi hazırlar → önizleme → onay. */
export function TaskTransferModal({ project, task, onClose }) {
  const [options, setOptions] = useState(null);
  const [mid, setMid] = useState('');
  const [rows, setRows] = useState([]);
  const [rules, setRules] = useState(new Set(task.transfer_mapping_ids || []));
  const [busy, setBusy] = useState(false);
  const load = useCallback(() => api.getProjectTransfers(project.id).then((r) => setRows(r.filter((x) => x.task_id === task.id))).catch((e) => toast.error(e.message)), [project.id, task.id]);
  useEffect(() => { api.getTransferOptions(project.id).then((o) => { setOptions(o); setMid(o[0]?.id || ''); }).catch((e) => { toast.error(e.message); setOptions([]); }); load(); }, [project.id, load]);
  useEffect(() => {
    if (!rows.some((r) => r.status === 'EXTRACTING' || r.status === 'APPROVED' || r.status === 'RUNNING')) return undefined;
    const t = setInterval(load, 2500);
    return () => clearInterval(t);
  }, [rows, load]);
  const start = async () => {
    setBusy(true);
    try { await api.proposeTaskTransfer(task.id, mid); toast.info('RECAi çıktıyı okuyup kayıtları hazırlıyor…'); load(); } catch (e) { toast.error(e.message); } finally { setBusy(false); }
  };
  const saveRules = async (next) => {
    setRules(next);
    try { await api.setTaskTransferRules(task.id, [...next]); toast.success(next.size ? 'Bu adım bitince seçili aktarımlar önerilecek.' : 'Otomatik aktarım kapatıldı.'); } catch (e) { toast.error(e.message); }
  };
  return (
    <Modal open onClose={onClose} title={`${task.title} · sisteme aktar`} size="lg" footer={<Button variant="secondary" onClick={onClose}>Kapat</Button>}>
      {!options ? <p className="pj-hint">Yükleniyor…</p> : options.length === 0 ? (
        <EmptyState icon={Send} title="Onaylı eşleme yok" description="Şirket yöneticiniz Entegrasyonlar > Eşlemeler'den bir eşleme hazırlayıp onaylamalı." />
      ) : (
        <>
          <p className="pj-hint">RECAi adımın çıktısından kayıtları çıkarır ve önizleme hazırlar. Hiçbir kayıt onaysız yazılmaz.</p>
          <div className="pj-form">
            <div className="pj-field full">
              <label htmlFor="tt-map">Eşleme</label>
              <select id="tt-map" className="ui-input" value={mid} onChange={(e) => setMid(e.target.value)}>
                {options.map((o) => <option key={o.id} value={o.id}>{o.name} · {o.connection_name}</option>)}
              </select>
            </div>
          </div>
          <div className="pj-actions"><Button icon={Sparkles} disabled={busy || !mid || !task.can_transfer} onClick={start}>{busy ? 'Başlatılıyor…' : 'RECAi ile hazırla'}</Button></div>
          <fieldset className="ig-steps" style={{ marginTop: 12 }}>
            <legend className="pj-hint">Bu adım bitince otomatik öner</legend>
            {options.map((o) => (
              <label key={o.id} style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
                <input type="checkbox" checked={rules.has(o.id)} onChange={() => { const n = new Set(rules); n.has(o.id) ? n.delete(o.id) : n.add(o.id); saveRules(n); }} />
                {o.name} · {o.connection_name}
              </label>
            ))}
          </fieldset>
        </>
      )}
      {rows.length > 0 && <ul className="pj-list" aria-label="Bu adımın aktarımları">{rows.map((r) => <TransferCard key={r.id} tr={r} canManage onChange={load} />)}</ul>}
    </Modal>
  );
}

/** Projenin dış sistem kayıtları (Kapanış sekmesi): aktarımlar, kapanışta otomatik öneri, proje çıktısından aktarım. */
export function ProjectTransfers({ project }) {
  const [rows, setRows] = useState(null);
  const [options, setOptions] = useState([]);
  const [onClose, setOnClose] = useState(new Set(project.transfer_on_close || []));
  const load = useCallback(() => api.getProjectTransfers(project.id).then(setRows).catch(() => setRows([])), [project.id]);
  useEffect(() => { load(); if (project.can_manage) api.getTransferOptions(project.id).then(setOptions).catch(() => setOptions([])); }, [load, project.id, project.can_manage]);
  const toggle = async (id) => {
    const n = new Set(onClose); n.has(id) ? n.delete(id) : n.add(id);
    setOnClose(n);
    try { await api.setProjectTransferOnClose(project.id, [...n]); } catch (e) { toast.error(e.message); }
  };
  const done = (rows || []).filter((r) => r.status === 'DONE');
  return (
    <Card title="Dış sistem kayıtları" subtitle="Bu projenin çıktılarından şirket sistemlerine aktarılan kayıtlar (önizleme ve onayla).">
      {!rows ? <p className="pj-hint">Yükleniyor…</p> : rows.length === 0 ? <p className="pj-hint">Henüz aktarım yok.</p> : (
        <>
          {done.length > 0 && <p className="pj-meta">{done.map((r) => <a key={r.id} className="ig-link" href={r.external_url || undefined} target="_blank" rel="noreferrer"><ExternalLink size={13} /> {r.connection_name}: {r.external_ref}</a>)}</p>}
          <ul className="pj-list" aria-label="Proje aktarımları">{rows.map((r) => <TransferCard key={r.id} tr={r} canManage={project.can_manage} onChange={load} />)}</ul>
        </>
      )}
      {project.can_manage && options.length > 0 && !['COMPLETED', 'CANCELLED'].includes(project.status) && (
        <fieldset className="ig-steps" style={{ marginTop: 10 }}>
          <legend className="pj-hint">Proje tamamlanınca otomatik öner</legend>
          {options.map((o) => (
            <label key={o.id} style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
              <input type="checkbox" checked={onClose.has(o.id)} onChange={() => toggle(o.id)} /> {o.name} · {o.connection_name}
            </label>
          ))}
        </fieldset>
      )}
    </Card>
  );
}

/** Şirketin aktarım kuralları ve günlüğü (Entegrasyonlar). */
export function TransferAdmin({ tenantId }) {
  const [policy, setPolicy] = useState(null);
  const [log, setLog] = useState([]);
  const [objects, setObjects] = useState([]);
  const load = useCallback(() => Promise.all([api.getTransferPolicy(tenantId).then(setPolicy), api.getCompanyTransfers(tenantId).then(setLog),
    loadObjects().then(setObjects)]).catch((e) => toast.error(e.message)), [tenantId]);
  useEffect(() => { load(); }, [load]);
  if (!policy) return null;
  const save = async (next) => {
    try { setPolicy(await api.setTransferPolicy(tenantId, next)); toast.success('Aktarım kuralları kaydedildi.'); } catch (e) { toast.error(e.message); }
  };
  const flip = (code) => {
    const s = new Set(policy.double_approval_objects || []); s.has(code) ? s.delete(code) : s.add(code);
    save({ ...policy, double_approval_objects: [...s] });
  };
  return (
    <>
      <Card title="Aktarım onay kuralları" subtitle="İş çıktısından sisteme her aktarım önizleme ve onaydan geçer. Aşağıdakiler ikinci bir onay (entegrasyon yöneticisi, farklı kişi) ister.">
        <div className="pj-form">
          <div className="pj-field full">
            <span className="pj-hint">Her zaman çift onay:</span>
            {objects.map((o) => (
              <label key={o.code} style={{ display: 'inline-flex', gap: 6, alignItems: 'center', marginRight: 14 }}>
                <input type="checkbox" checked={(policy.double_approval_objects || []).includes(o.code)} onChange={() => flip(o.code)} /> {o.label}
              </label>
            ))}
          </div>
          <div className="pj-field">
            <label htmlFor="tp-threshold">Tutar eşiği (₺; üzeri çift onay)</label>
            <input id="tp-threshold" className="ui-input" type="number" min={0} defaultValue={policy.amount_threshold ?? ''}
              onBlur={(e) => save({ ...policy, amount_threshold: e.target.value === '' ? null : Number(e.target.value) })} />
          </div>
        </div>
      </Card>
      <Card title="Aktarım günlüğü" subtitle="Silinemez kayıt: ne, nereye, kimin onayıyla aktarıldı; geri alınanlar dahil.">
        {log.length === 0 ? <p className="pj-hint">Henüz aktarım yok.</p> : (
          <ul className="pj-list" aria-label="Aktarım günlüğü">{log.slice(0, 50).map((r) => <TransferCard key={r.id} tr={r} canManage onChange={load} />)}</ul>
        )}
      </Card>
    </>
  );
}
