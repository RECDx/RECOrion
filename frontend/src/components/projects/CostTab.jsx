import React, { useCallback, useEffect, useRef, useState } from 'react';
import { Download, FileSpreadsheet, Paperclip, Pencil, Plus, Save, Trash2 } from 'lucide-react';
import { api } from '../../api';
import { Badge, Button, Card, Modal } from '../../ui/components';
import { confirmDialog, toast } from '../../ui/feedback';

export const CATEGORIES = { MATERYAL: 'Materyal', DANISMANLIK: 'Danışmanlık', EGITIM: 'Eğitim', LISANS: 'Lisans / yazılım',
  SEYAHAT: 'Seyahat', DONANIM: 'Donanım', DIGER: 'Diğer' };
const BASIS = { ACTUAL: 'Gerçekleşen', RUNNING: 'Sürüyor', PLANNED: 'Plan (tahmin)' };
export const tl = (n) => (n == null ? '—' : `${Number(n).toLocaleString('tr-TR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} ₺`);
const tok = (n) => Number(n || 0).toLocaleString('tr-TR');

/** Proje maliyeti (ADIM 7.5.4): bütçe ve gerçekleşen, adım/kalem/LLM kırılımı, kalem yönetimi, Excel. TL, KDV hariç. */
export default function CostTab({ project, onSummary }) {
  const [c, setC] = useState(null);
  const [budget, setBudget] = useState({ amount: '', note: '' });
  const [editing, setEditing] = useState(null);
  // Kaydedilmemiş bütçe girişi yeniden yüklemede (kalem ekleme, geç gelen yanıt) sunucudaki değerle ezilmez
  const budgetDirty = useRef(false);
  const closed = ['COMPLETED', 'CANCELLED'].includes(project.status);
  const editBudget = (patch) => { budgetDirty.current = true; setBudget((b) => ({ ...b, ...patch })); };

  const load = useCallback(() => api.getProjectCosts(project.id).then((d) => {
    setC(d);
    if (!budgetDirty.current) setBudget({ amount: d.budget.amount ?? '', note: d.budget.note || '' });
    onSummary?.(d.totals);
  }).catch((e) => toast.error(e.message)), [project.id, onSummary]);
  useEffect(() => { load(); }, [load]);

  if (!c) return <p className="pj-hint">Yükleniyor…</p>;
  const t = c.totals;
  const saveBudget = async () => {
    try {
      await api.setProjectBudget(project.id, budget.amount === '' ? null : Number(budget.amount), budget.note);
      toast.success('Bütçe kaydedildi.');
      budgetDirty.current = false;
      load();
    } catch (e) { toast.error(e.message); }
  };
  const remove = async (item) => {
    if (!(await confirmDialog({ message: `'${item.description}' kalemi silinsin mi?${item.has_attachment ? ' Belgesi de silinir.' : ''}` }))) return;
    try { await api.deleteCostItem(project.id, item.id); toast.success('Kalem silindi.'); load(); } catch (e) { toast.error(e.message); }
  };
  const maxCat = Math.max(1, ...c.by_category.map((x) => x.amount));
  const variance = t.budget_variance;

  return (
    <div className="pj-steps">
      <div className="pj-stats">
        <div className="pj-stat"><span>Gerçekleşen</span><strong>{tl(t.actual)}</strong></div>
        <div className="pj-stat"><span>Bütçe</span><strong>{tl(c.budget.amount)}</strong></div>
        <div className="pj-stat"><span>Fark</span><strong className={variance == null ? undefined : variance < 0 ? 'ui-text-danger' : 'ui-text-success'}>{tl(variance)}</strong></div>
        <div className="pj-stat"><span>Plan (öneri)</span><strong>{tl(c.budget.suggested)}</strong></div>
      </div>
      {t.unpriced_calls > 0 && (
        <div className="pj-note medium">{t.unpriced_calls} LLM çağrısının TL fiyatı tanımlı değil; token maliyeti bu çağrılar için 0 sayılıyor. Fiyatlar RECDx tarafından LLM TL Fiyatları ekranında girilir.</div>
      )}
      {(c.planned.missing_daily_cost > 0 || c.planned.missing_llm_price > 0) && (
        <div className="pj-note info">Plan önerisi eksik olabilir: {c.planned.missing_daily_cost > 0 ? `${c.planned.missing_daily_cost} insan personelin günlük maliyeti girilmemiş` : ''}
          {c.planned.missing_daily_cost > 0 && c.planned.missing_llm_price > 0 ? '; ' : ''}{c.planned.missing_llm_price > 0 ? `${c.planned.missing_llm_price} AI adımının modeline fiyat tanımlı değil` : ''}.</div>
      )}

      <div className="pj-split">
        <Card title="Bütçe" subtitle="TL, KDV hariç. Plan önerisi: planlanan personel maliyeti + planlanan token maliyeti.">
          <div className="pj-form">
            <div className="pj-field">
              <label htmlFor="cost-budget">Bütçe (₺)</label>
              <input id="cost-budget" className="ui-input" type="number" min="0" step="0.01" value={budget.amount} disabled={closed}
                onChange={(e) => editBudget({ amount: e.target.value })} placeholder={c.budget.suggested ? String(c.budget.suggested) : ''} />
            </div>
            <div className="pj-field">
              <label htmlFor="cost-budget-note">Not</label>
              <input id="cost-budget-note" className="ui-input" value={budget.note} disabled={closed} maxLength={2000}
                onChange={(e) => editBudget({ note: e.target.value })} />
            </div>
          </div>
          {!closed && (
            <div className="pj-actions" style={{ marginTop: 10 }}>
              <Button icon={Save} onClick={saveBudget}>Bütçeyi kaydet</Button>
              {c.budget.suggested > 0 && <Button variant="ghost" onClick={() => editBudget({ amount: c.budget.suggested })}>Plan önerisini kullan</Button>}
            </div>
          )}
          <ul className="pj-check" style={{ marginTop: 12 }}>
            <li>Personel: {tl(t.labor)}{t.labor_planned ? ` (başlamamış adımlar için tahmin ${tl(t.labor_planned)})` : ''}</li>
            <li>Token (LLM): {tl(t.token)} · {tok(t.credits)} kredi</li>
            <li>Diğer kalemler: {tl(t.other)}</li>
          </ul>
        </Card>
        <Card title="Kategori dağılımı" subtitle="Diğer maliyet kalemleri" actions={
          <Button size="sm" variant="secondary" icon={FileSpreadsheet} onClick={() => api.downloadProjectCostReport(project.id).catch((e) => toast.error(e.message))}>Excel</Button>}>
          {c.by_category.length === 0 ? <p className="pj-hint">Henüz maliyet kalemi yok.</p> : (
            <div className="pj-gantt">
              {c.by_category.map((x) => (
                <div className="pj-gantt-row" key={x.category}>
                  <span>{x.label}<br /><small className="pj-hint">{tl(x.amount)}</small></span>
                  <div className="pj-gantt-track"><div className="pj-gantt-bar" style={{ left: 0, width: `${Math.max(3, (x.amount / maxCat) * 100)}%` }} /></div>
                </div>
              ))}
            </div>
          )}
        </Card>
      </div>

      <Card title="İş adımları" subtitle="Personel maliyeti gerçekleşen iş günü × günlük maliyet; tamamlanan adımda kayda geçer.">
        <div className="ui-table-scroll">
          <table className="ui-table">
            <thead><tr><th>#</th><th>İş adımı</th><th>Personel</th><th>Gün</th><th>Personel</th><th>Token (LLM)</th><th>Diğer</th><th>Toplam</th></tr></thead>
            <tbody>
              {c.tasks.map((x) => {
                const labor = x.labor.basis === 'PLANNED' ? 0 : x.labor.cost;
                return (
                  <tr key={x.task_id}>
                    <td data-label="#">{x.order_index}</td>
                    <td data-label="İş adımı">{x.title}</td>
                    <td data-label="Personel">{x.assignee || '—'}{x.assignee_type === 'AI_AGENT' ? ' (AI)' : ''}</td>
                    <td data-label="Gün">{x.labor.days} <small className="pj-hint">{BASIS[x.labor.basis]}</small></td>
                    <td data-label="Personel maliyeti">{x.labor.basis === 'PLANNED' ? <span className="pj-hint">{tl(x.labor.cost)} (tahmin)</span> : tl(x.labor.cost)}</td>
                    <td data-label="Token (LLM)">{tl(x.tokens.cost)}{x.tokens.unpriced_calls ? <small className="pj-hint"> · {x.tokens.unpriced_calls} fiyatsız</small> : ''}</td>
                    <td data-label="Diğer">{tl(x.other)}</td>
                    <td data-label="Toplam"><strong>{tl(labor + x.tokens.cost + x.other)}</strong></td>
                  </tr>
                );
              })}
              {c.project_level_tokens && (
                <tr>
                  <td data-label="#">—</td><td data-label="İş adımı">Proje geneli (Beyin AI planlama)</td><td data-label="Personel">RECAi</td><td data-label="Gün">—</td>
                  <td data-label="Personel maliyeti">—</td><td data-label="Token (LLM)">{tl(c.project_level_tokens.cost)}</td><td data-label="Diğer">—</td>
                  <td data-label="Toplam"><strong>{tl(c.project_level_tokens.cost)}</strong></td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </Card>

      <Card title="Maliyet kalemleri" subtitle="Materyal, danışmanlık, eğitim, lisans, seyahat, donanım ve diğer giderler. Belgeler (fatura vb.) öğrenmeye girmez."
        actions={!closed && <Button size="sm" icon={Plus} onClick={() => setEditing({})}>Kalem ekle</Button>}>
        {c.items.length === 0 ? <p className="pj-hint">Henüz kalem yok.</p> : (
          <ul className="pj-list">
            {c.items.map((i) => (
              <li key={i.id}>
                <span>
                  <strong>{i.description}</strong> <Badge tone="neutral">{i.category_label}</Badge><br />
                  <small className="pj-hint">{new Date(i.incurred_on).toLocaleDateString('tr-TR')} · {i.quantity} {i.unit || ''} × {tl(i.unit_price_try)}
                    {i.task_id ? ` · ${c.tasks.find((x) => x.task_id === i.task_id)?.title || ''}` : ''}</small>
                </span>
                <strong>{tl(i.amount_try)}</strong>
                {i.has_attachment && (
                  <button type="button" className="ui-icon-btn" aria-label="Belgeyi indir" title={i.attachment_name}
                    onClick={() => api.downloadCostAttachment(project.id, i.id, i.attachment_name).catch((e) => toast.error(e.message))}><Download size={14} /></button>
                )}
                {!closed && <>
                  <button type="button" className="ui-icon-btn" aria-label="Düzenle" onClick={() => setEditing(i)}><Pencil size={14} /></button>
                  <button type="button" className="ui-icon-btn" aria-label="Sil" onClick={() => remove(i)}><Trash2 size={14} /></button>
                </>}
              </li>
            ))}
          </ul>
        )}
      </Card>

      <Card title="LLM kırılımı" subtitle="Model bazında çağrı, token ve TL maliyeti (çağrı anındaki fiyatla).">
        {c.by_model.length === 0 ? <p className="pj-hint">Henüz LLM çağrısı yok.</p> : (
          <div className="ui-table-scroll">
            <table className="ui-table">
              <thead><tr><th>Model</th><th>Çağrı</th><th>Girdi token</th><th>Çıktı token</th><th>TL</th><th>Fiyatsız</th><th>Kredi</th></tr></thead>
              <tbody>{c.by_model.map((m) => (
                <tr key={m.model_code}>
                  <td data-label="Model" style={{ fontFamily: 'var(--font-mono)' }}>{m.model_code}</td><td data-label="Çağrı">{m.calls}</td>
                  <td data-label="Girdi token">{tok(m.tokens_in)}</td><td data-label="Çıktı token">{tok(m.tokens_out)}</td>
                  <td data-label="TL">{tl(m.cost)}</td><td data-label="Fiyatsız">{m.unpriced_calls}</td><td data-label="Kredi">{tok(m.credits)}</td>
                </tr>
              ))}</tbody>
            </table>
          </div>
        )}
      </Card>
      {editing && <ItemModal project={project} tasks={c.tasks} item={editing} onClose={() => setEditing(null)} onSaved={() => { setEditing(null); load(); }} />}
    </div>
  );
}

function ItemModal({ project, tasks, item, onClose, onSaved }) {
  const [f, setF] = useState({ category: item.category || 'MATERYAL', description: item.description || '', quantity: item.quantity ?? 1,
    unit: item.unit || '', unit_price_try: item.unit_price_try ?? '', incurred_on: item.incurred_on || new Date().toISOString().slice(0, 10),
    task_id: item.task_id || '' });
  const [file, setFile] = useState(null);
  const [busy, setBusy] = useState(false);
  const fileRef = useRef(null);
  const set = (k) => (e) => setF((x) => ({ ...x, [k]: e.target.value }));
  const amount = (Number(f.quantity) || 0) * (Number(f.unit_price_try) || 0);
  const save = async () => {
    if (f.description.trim().length < 2) return toast.warning('Açıklama yazın.');
    if (f.unit_price_try === '') return toast.warning('Birim fiyatı yazın.');
    setBusy(true);
    try {
      const data = { ...f, description: f.description.trim(), quantity: Number(f.quantity), unit_price_try: Number(f.unit_price_try),
        unit: f.unit || null, task_id: f.task_id || null };
      const saved = item.id ? await api.updateCostItem(project.id, item.id, data) : await api.addCostItem(project.id, data);
      if (file) {
        const fd = new FormData();
        fd.append('file', file);
        await api.uploadCostAttachment(project.id, saved.id, fd);
      }
      toast.success(item.id ? 'Kalem güncellendi.' : 'Kalem eklendi.');
      onSaved();
    } catch (e) { toast.error(e.message); } finally { setBusy(false); }
  };
  return (
    <Modal open onClose={onClose} title={item.id ? 'Maliyet kalemini düzenle' : 'Maliyet kalemi ekle'} size="md"
      footer={<><Button variant="secondary" onClick={onClose}>Vazgeç</Button><Button icon={Save} onClick={save} disabled={busy}>{busy ? 'Kaydediliyor…' : 'Kaydet'}</Button></>}>
      <div className="pj-form">
        <div className="pj-field">
          <label htmlFor="ci-cat">Kategori</label>
          <select id="ci-cat" className="ui-input" value={f.category} onChange={set('category')}>
            {Object.entries(CATEGORIES).map(([k, l]) => <option key={k} value={k}>{l}</option>)}
          </select>
        </div>
        <div className="pj-field">
          <label htmlFor="ci-date">Tarih</label>
          <input id="ci-date" className="ui-input" type="date" value={f.incurred_on} onChange={set('incurred_on')} />
        </div>
        <div className="pj-field full">
          <label htmlFor="ci-desc">Açıklama</label>
          <input id="ci-desc" className="ui-input" value={f.description} onChange={set('description')} maxLength={500} placeholder="Örn. Güvenlik danışmanlığı (2 gün)" />
        </div>
        <div className="pj-field">
          <label htmlFor="ci-qty">Miktar</label>
          <input id="ci-qty" className="ui-input" type="number" min="0.001" step="0.001" value={f.quantity} onChange={set('quantity')} />
        </div>
        <div className="pj-field">
          <label htmlFor="ci-unit">Birim</label>
          <input id="ci-unit" className="ui-input" value={f.unit} onChange={set('unit')} maxLength={24} placeholder="adet, gün, saat…" />
        </div>
        <div className="pj-field">
          <label htmlFor="ci-price">Birim fiyat (₺, KDV hariç)</label>
          <input id="ci-price" className="ui-input" type="number" min="0" step="0.01" value={f.unit_price_try} onChange={set('unit_price_try')} />
        </div>
        <div className="pj-field">
          <label htmlFor="ci-task">İş adımı (isteğe bağlı)</label>
          <select id="ci-task" className="ui-input" value={f.task_id} onChange={set('task_id')}>
            <option value="">Proje geneli</option>
            {tasks.map((x) => <option key={x.task_id} value={x.task_id}>{x.order_index}. {x.title}</option>)}
          </select>
        </div>
        <div className="pj-field full">
          <label>Belge (fatura vb., isteğe bağlı)</label>
          <div className="pj-actions">
            <Button variant="secondary" icon={Paperclip} onClick={() => fileRef.current?.click()}>{file ? file.name : item.attachment_name ? `Değiştir (${item.attachment_name})` : 'Belge seç'}</Button>
            <input ref={fileRef} type="file" hidden accept=".pdf,.png,.jpg,.jpeg,.xlsx,.docx" onChange={(e) => setFile(e.target.files?.[0] || null)} />
          </div>
          <p className="pj-hint">PDF, PNG, JPG, XLSX veya DOCX · en fazla 20 MB. Belgeler AI personele öğretilmez.</p>
        </div>
      </div>
      <p className="pj-note info" style={{ marginTop: 10 }}>Tutar: <strong>{tl(amount)}</strong></p>
    </Modal>
  );
}
