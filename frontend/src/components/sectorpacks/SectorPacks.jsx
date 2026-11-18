import React, { useCallback, useEffect, useState } from 'react';
import { Layers, Plus } from 'lucide-react';
import { api } from '../../api';
import { Badge, Button, Card, EmptyState, Modal } from '../../ui/components';
import { promptDialog, toast } from '../../ui/feedback';
import '../projects/projects.css';

const fmtDate = (d) => (d ? new Date(d).toLocaleDateString('tr-TR', { day: '2-digit', month: 'long', year: 'numeric' }) : '—');
const SPLIT = { AI: 'AI personel', HUMAN: 'İnsan', 'AI+HUMAN': 'AI hazırlar, insan onaylar' };

// Satır biçimi: düzenleyici her listeyi düz metin olarak gösterir ("|" ile ayrılmış alanlar), kayıtta yapıya çevrilir
const cut = (l) => l.split('|').map((x) => x.trim());
const lines = (t) => (t || '').split('\n').map((l) => l.trim()).filter(Boolean);
export const questionsToText = (qs) => (qs || []).map((q) => [q.topic, q.text, q.why].filter((x, i) => i < 2 || x).join(' | ')).join('\n');
export const textToQuestions = (t) => lines(t).map(cut).map(([topic, text, why]) => (text ? { topic, text, why: why || '' } : { topic: 'Soru', text: topic, why: '' }));
const phasesToText = (ps) => (ps || []).map((p) => [`${p.name} | ${p.split}`, ...(p.deliverables || []).map((d) => `  - ${d.name} | ${d.acceptance} | ${d.verification}`)].join('\n')).join('\n');
const textToPhases = (t) => {
  const out = [];
  (t || '').split('\n').forEach((raw) => {
    const l = raw.trim();
    if (!l) return;
    if (l.startsWith('-') && out.length) {
      const [name, acceptance, verification] = cut(l.replace(/^-\s*/, ''));
      out[out.length - 1].deliverables.push({ name, acceptance: acceptance || '', verification: verification || '' });
    } else {
      const [name, split] = cut(l);
      out.push({ name, split: (split || 'AI+HUMAN').toUpperCase(), deliverables: [] });
    }
  });
  return out;
};
const rolesToText = (rs) => (rs || []).map((r) => `${r.role} | ${r.side} | ${r.note || ''}`).join('\n');
const textToRoles = (t) => lines(t).map(cut).map(([role, side, note]) => ({ role, side: (side || 'HUMAN').toUpperCase(), note: note || '' }));
const stdToText = (ss) => (ss || []).map((s) => `${s.title}${s.note ? ` | ${s.note}` : ''}`).join('\n');
const textToStd = (t) => lines(t).map(cut).map(([title, note]) => ({ title, note: note || '' }));

const toForm = (p) => {
  const c = p.draft_content || {};
  return { title: p.title, description: p.description || '', sector_codes: (p.sector_codes || []).join(', '), keywords: (p.keywords || []).join(', '),
    questions: questionsToText(c.questions), phases: phasesToText(c.phases), roles: rolesToText(c.roles), missed: (c.missed || []).join('\n'),
    risks: (c.risks || []).join('\n'), kpis: (c.kpis || []).join('\n'), standards: stdToText(c.standards) };
};
const fromForm = (f) => ({
  title: f.title, description: f.description, sector_codes: f.sector_codes.split(',').map((x) => x.trim()).filter(Boolean),
  keywords: f.keywords.split(',').map((x) => x.trim()).filter(Boolean),
  content: { questions: textToQuestions(f.questions), phases: textToPhases(f.phases), roles: textToRoles(f.roles), missed: lines(f.missed),
    risks: lines(f.risks), kpis: lines(f.kpis), standards: textToStd(f.standards) },
});

function PackView({ content }) {
  const c = content || {};
  return (
    <div className="pj-steps">
      {(c.questions || []).length > 0 && <div><strong>Keşif soru bankası</strong>
        <ul className="pj-list">{c.questions.map((q) => <li key={q.text}><span><Badge tone="info">{q.topic}</Badge> {q.text}{q.why && <><br /><small className="pj-hint">Neden: {q.why}</small></>}</span></li>)}</ul></div>}
      {(c.phases || []).length > 0 && <div><strong>Standart aşamalar ve teslimatlar</strong>
        <ul className="pj-list">{c.phases.map((p) => (
          <li key={p.name}><span><strong>{p.name}</strong> <Badge tone="neutral">{SPLIT[p.split] || p.split}</Badge>
            {(p.deliverables || []).map((d) => <React.Fragment key={d.name}><br />{d.name}<small className="pj-hint"> · kabul: {d.acceptance || '—'} · doğrulama: {d.verification || '—'}</small></React.Fragment>)}</span></li>
        ))}</ul></div>}
      {(c.roles || []).length > 0 && <div><strong>Roller ve iş bölümü</strong>
        <ul className="pj-list">{c.roles.map((r) => <li key={r.role}><span>{r.role} <Badge tone={r.side === 'HUMAN' ? 'warning' : 'info'}>{r.side === 'HUMAN' ? 'İnsan' : 'AI'}</Badge>{r.note && <small className="pj-hint"> · {r.note}</small>}</span></li>)}</ul></div>}
      {[['missed', 'Sık atlanan gereksinimler'], ['risks', 'Tipik riskler'], ['kpis', "KPI'lar"]].filter(([k]) => (c[k] || []).length).map(([k, l]) => (
        <div key={k}><strong>{l}</strong><ul className="pj-list">{c[k].map((x) => <li key={x}><span>{x}</span></li>)}</ul></div>
      ))}
      {(c.standards || []).length > 0 && <div><strong>Mevzuat ve standartlar</strong>
        <ul className="pj-list">{c.standards.map((s) => <li key={s.title}><span>{s.title}{s.note && <small className="pj-hint"> · {s.note}</small>}</span></li>)}</ul></div>}
    </div>
  );
}

/** Merkez › Sektör Paketleri (#751): taslak düzenleme, uzman kontrolü beyanıyla yayımlama, yayından geri çekme. */
export function SectorPackAdmin() {
  const [list, setList] = useState(null);
  const [editing, setEditing] = useState(null);
  const [publishing, setPublishing] = useState(null);
  const load = useCallback(() => api.getSectorPacksAdmin().then(setList).catch((e) => toast.error(e.message)), []);
  useEffect(() => { load(); }, [load]);
  const create = async () => {
    const code = await promptDialog({ title: 'Yeni sektör paketi', message: 'Paket kodu (küçük harf, rakam, tire; ör. saglik-klinik).', required: true, confirmText: 'Devam' });
    if (!code) return;
    const title = await promptDialog({ title: 'Yeni sektör paketi', message: 'Paket adı (ör. Sağlık — klinik ve poliklinik).', required: true, confirmText: 'Oluştur' });
    if (!title) return;
    try { const p = await api.createSectorPack({ code: code.trim(), title: title.trim() }); load(); setEditing(p); } catch (e) { toast.error(e.message); }
  };
  const withdraw = async (p) => {
    try { await api.withdrawSectorPack(p.id); toast.success(`'${p.title}' yayından çekildi; şirketler ve Beyin AI artık kullanmaz.`); load(); } catch (e) { toast.error(e.message); }
  };

  return (
    <Card title="Sektör bilgi paketleri" subtitle="Beyin AI keşif, plan ve doğrulamada bu paketleri kullanır. Taslaklar yalnız burada görünür; şirketler yalnız uzman kontrolünden geçip yayımlanan sürümü görür."
      actions={<Button size="sm" icon={Plus} onClick={create}>Yeni paket</Button>}>
      {!list ? <p className="pj-hint">Yükleniyor…</p> : (
        <ul className="pj-list" aria-label="Sektör paketleri (yönetim)">
          {list.map((p) => {
            const live = p.published && !p.published.withdrawn;
            const c = p.draft_content || {};
            return (
              <li key={p.id} style={{ flexWrap: 'wrap' }}>
                <span><strong>{p.title}</strong>{' '}
                  {live ? <Badge tone="success">Yayında · sürüm {p.published.version}</Badge>
                    : p.published ? <Badge tone="neutral">Yayından çekildi · son sürüm {p.published.version}</Badge>
                      : <Badge tone="warning">Taslak · uzman kontrolü bekliyor</Badge>}
                  {p.published && p.changed_since_publish && <> <Badge tone="info">Yayımlanmamış değişiklik var</Badge></>}<br />
                  <small className="pj-hint">{(c.questions || []).length} soru · {(c.phases || []).length} aşama · {(c.missed || []).length} sık atlanan
                    {p.published ? ` · son yayın: ${fmtDate(p.published.published_at)}, kontrol eden ${p.published.reviewer_name}` : ''}</small></span>
                <Button size="sm" variant="secondary" onClick={() => setEditing(p)}>Düzenle</Button>
                <Button size="sm" disabled={!((c.questions || []).length || (c.phases || []).length) || (live && !p.changed_since_publish)}
                  onClick={() => setPublishing(p)}>Uzman kontrolüyle yayımla</Button>
                {live && <Button size="sm" variant="ghost" onClick={() => withdraw(p)}>Yayından çek</Button>}
              </li>
            );
          })}
        </ul>
      )}
      {editing && <PackEditor pack={editing} onClose={() => setEditing(null)} onSaved={() => { setEditing(null); load(); }} />}
      {publishing && <PublishModal pack={publishing} onClose={() => setPublishing(null)} onDone={() => { setPublishing(null); load(); }} />}
    </Card>
  );
}

const FIELDS = [
  ['questions', 'Keşif soru bankası', 'Her satır: Konu | Soru | Neden önemli', 8],
  ['phases', 'Standart aşamalar ve teslimatlar', 'Aşama satırı: Aşama adı | AI, HUMAN ya da AI+HUMAN. Altındaki teslimatlar "-" ile: - Teslimat | Kabul ölçütü | Doğrulama yöntemi', 10],
  ['roles', 'Tipik roller ve iş bölümü', 'Her satır: Rol | AI ya da HUMAN | Not', 5],
  ['missed', 'Sık atlanan gereksinimler', 'Her satıra bir madde', 5],
  ['risks', 'Tipik riskler', 'Her satıra bir madde', 4],
  ['kpis', "KPI'lar", 'Her satıra bir madde', 3],
  ['standards', 'Mevzuat ve standartlar', 'Her satır: Ad | Kısa not', 3],
];

function PackEditor({ pack, onClose, onSaved }) {
  const [f, setF] = useState(toForm(pack));
  const [busy, setBusy] = useState(false);
  const set = (k) => (e) => setF((x) => ({ ...x, [k]: e.target.value }));
  const save = async () => {
    setBusy(true);
    try {
      await api.updateSectorPack(pack.id, fromForm(f));
      toast.success(pack.published ? 'Taslak kaydedildi; yayındaki sürüm değişmedi. Uzman kontrolünden sonra yeniden yayımlayın.' : 'Taslak kaydedildi.');
      onSaved();
    } catch (e) { toast.error(e.message); } finally { setBusy(false); }
  };
  return (
    <Modal open onClose={onClose} title={`${pack.title} · taslak`} size="lg"
      footer={<><Button variant="secondary" onClick={onClose}>Vazgeç</Button><Button onClick={save} disabled={busy}>{busy ? 'Kaydediliyor…' : 'Taslağı kaydet'}</Button></>}>
      <PackSuggestions pack={pack} />
      <div className="pj-form">
        <label className="pj-field">Paket adı<input className="ui-input" value={f.title} onChange={set('title')} /></label>
        <label className="pj-field">Sektör kodları (virgülle; şirket kartındaki sektörler)<input className="ui-input" value={f.sector_codes} onChange={set('sector_codes')} placeholder="C, H" /></label>
        <label className="pj-field" style={{ gridColumn: '1 / -1' }}>Açıklama<textarea className="ui-input" rows={2} value={f.description} onChange={set('description')} /></label>
        <label className="pj-field" style={{ gridColumn: '1 / -1' }}>Anahtar kelimeler (virgülle; Beyin AI projeye paket önerirken isterlerde arar)
          <input className="ui-input" value={f.keywords} onChange={set('keywords')} /></label>
        {FIELDS.map(([k, l, hint, rows]) => (
          <label key={k} className="pj-field" style={{ gridColumn: '1 / -1' }}>{l}<small className="pj-hint">{hint}</small>
            <textarea className="ui-input" rows={rows} value={f[k]} onChange={set(k)} /></label>
        ))}
      </div>
    </Modal>
  );
}

/**
 * #753: şirketlerin bu paketle yapılan Beyin planlarına sık eklediği / çıkardığı adımlar. Yalnız en az k şirkette görülen ve
 * tek şirketin baskın olmadığı örüntüler gelir (KVKK k-anonimlik); tekil kayıt ve şirket adı yoktur. Uzman uygun bulursa
 * taslağa elle ekler; paket ancak uzman kontrolüyle yeniden yayımlanınca şirketlere ulaşır.
 */
function PackSuggestions({ pack }) {
  const [s, setS] = useState(null);
  useEffect(() => { api.getSectorPackSuggestions(pack.id).then(setS).catch(() => setS(null)); }, [pack.id]);
  if (!s) return null;
  const empty = !s.added.length && !s.removed.length;
  return (
    <section className="pj-note info" aria-label="Şirketlerden gelen öneriler" style={{ marginBottom: 12 }}>
      <strong>Şirketlerden gelen öneriler (anonim)</strong>
      <p className="pj-hint" style={{ margin: '4px 0' }}>
        Bu paketle yapılan {s.plans} onaylı planda yöneticilerin Beyin AI önerisine yaptığı değişiklikler. Yalnız en az {s.k_min} şirkette
        görülen ve tek şirketin payı %{s.dominance_pct}'i aşmayan örüntüler gösterilir{s.hidden ? ` (${s.hidden} örüntü eşiğin altında kaldı)` : ''}.
      </p>
      {empty ? <p className="pj-hint" style={{ margin: 0 }}>Henüz eşiği geçen örüntü yok.</p> : (
        <div className="pj-split">
          {[['added', 'Sık eklenen adımlar'], ['removed', 'Sık çıkarılan adımlar']].map(([k, t]) => (
            <div key={k}><small><strong>{t}</strong></small>
              <ul className="pj-list" aria-label={t}>
                {s[k].length ? s[k].map((x) => <li key={x.title}><span>{x.title} <small className="pj-hint">· {x.companies} şirket</small></span></li>)
                  : <li><span className="pj-hint">—</span></li>}
              </ul>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}

function PublishModal({ pack, onClose, onDone }) {
  const today = new Date().toISOString().slice(0, 10);
  const [form, setForm] = useState({ expert_confirmed: false, reviewer_name: '', checked_at: today, note: '' });
  const [busy, setBusy] = useState(false);
  const publish = async () => {
    setBusy(true);
    try {
      const r = await api.publishSectorPack(pack.id, form);
      toast.success(`'${pack.title}' sürüm ${r.published.version} yayımlandı.`);
      onDone();
    } catch (e) { toast.error(e.message); } finally { setBusy(false); }
  };
  return (
    <Modal open onClose={onClose} title={`${pack.title} · yayımla`} size="md"
      footer={<><Button variant="secondary" onClick={onClose}>Vazgeç</Button>
        <Button onClick={publish} disabled={busy || !form.expert_confirmed || form.reviewer_name.trim().length < 3}>{busy ? 'Yayımlanıyor…' : 'Yayımla'}</Button></>}>
      <p className="pj-note" role="note">İlk dalga paketlerin içeriği Claude tarafından hazırlandı. Yayından önce bu iş kolunda deneyimli bir uzmanın soruları,
        aşamaları ve standartları kontrol etmesi zorunludur; yayımlanan sürümü tüm şirketlerin Beyin AI'sı kullanır.</p>
      <label className="pj-hint" style={{ display: 'flex', gap: 8, margin: '10px 0' }}>
        <input type="checkbox" checked={form.expert_confirmed} onChange={(e) => setForm((x) => ({ ...x, expert_confirmed: e.target.checked }))} />
        Paket bu iş kolunda yetkin bir uzman tarafından kontrol edildi.
      </label>
      <div className="pj-form">
        <label className="pj-field">Kontrol eden uzman *<input id="sp-reviewer" className="ui-input" value={form.reviewer_name} maxLength={120}
          onChange={(e) => setForm((x) => ({ ...x, reviewer_name: e.target.value }))} placeholder="Ad Soyad, unvan" /></label>
        <label className="pj-field">Kontrol tarihi *<input className="ui-input" type="date" max={today} value={form.checked_at}
          onChange={(e) => setForm((x) => ({ ...x, checked_at: e.target.value }))} /></label>
        <label className="pj-field" style={{ gridColumn: '1 / -1' }}>Not<textarea className="ui-input" rows={2} value={form.note} maxLength={2000}
          onChange={(e) => setForm((x) => ({ ...x, note: e.target.value }))} /></label>
      </div>
    </Modal>
  );
}

/** Şirket Yönetimi › Sektör paketleri (#751): yayımlanmış paketleri okuma; şirkete özel ek sorular ve sık atlanan maddeler. */
export function CompanySectorPacks({ tenantId, canManage }) {
  const [list, setList] = useState(null);
  const [viewing, setViewing] = useState(null);
  const [extras, setExtras] = useState(null);
  const load = useCallback(() => api.getCompanySectorPacks(tenantId).then(setList).catch((e) => toast.error(e.message)), [tenantId]);
  useEffect(() => { if (tenantId) load(); }, [tenantId, load]);
  const saveExtras = async () => {
    try {
      await api.setCompanySectorPackExtras(tenantId, extras.code, { questions: textToQuestions(extras.questions), missed: lines(extras.missed) });
      toast.success('Şirketinize özel ekler kaydedildi; Beyin AI bu paketi kullanan projelerin keşfinde önce bunları sorar.');
      setExtras(null); load();
    } catch (e) { toast.error(e.message); }
  };

  return (
    <Card title="Sektör bilgi paketleri" subtitle="Beyin AI, projenin iş koluna uygun paketteki soruları, aşamaları ve sık atlanan gereksinimleri keşif ve planda kullanır. Paketler RECDx'te bir uzman tarafından kontrol edilip yayımlanır.">
      {!list ? <p className="pj-hint">Yükleniyor…</p> : list.length === 0 ? (
        <EmptyState icon={Layers} title="Henüz yayımlanmış paket yok" description="RECDx uzman kontrolünü tamamladığında paketler burada görünür." />
      ) : (
        <ul className="pj-list" aria-label="Sektör paketleri">
          {list.map((p) => (
            <li key={p.id} style={{ flexWrap: 'wrap' }}>
              <span><strong>{p.title}</strong> <Badge tone="success">Sürüm {p.version}</Badge>
                {(p.extras.questions.length + p.extras.missed.length) > 0 && <> <Badge tone="info">Şirket eki: {p.extras.questions.length} soru, {p.extras.missed.length} madde</Badge></>}<br />
                <small className="pj-hint">{p.counts.questions} soru · {p.counts.phases} aşama · kontrol: {fmtDate(p.checked_at)} ({p.reviewer_name})</small></span>
              <Button size="sm" variant="secondary" onClick={() => setViewing(p)}>İçeriği gör</Button>
              {canManage && <Button size="sm" variant="ghost" onClick={() => setExtras({ code: p.code, title: p.title, questions: questionsToText(p.extras.questions), missed: p.extras.missed.join('\n') })}>Şirket ekleri</Button>}
            </li>
          ))}
        </ul>
      )}
      {viewing && (
        <Modal open onClose={() => setViewing(null)} title={`${viewing.title} · sürüm ${viewing.version}`} size="lg" footer={<Button onClick={() => setViewing(null)}>Kapat</Button>}>
          <p className="pj-hint">{viewing.description}</p>
          <PackView content={viewing.content} />
        </Modal>
      )}
      {extras && (
        <Modal open onClose={() => setExtras(null)} title={`${extras.title} · şirketinize özel ekler`} size="lg"
          footer={<><Button variant="secondary" onClick={() => setExtras(null)}>Vazgeç</Button><Button onClick={saveExtras}>Kaydet</Button></>}>
          <p className="pj-hint">Bu ekler yalnız sizin şirketinizde geçerlidir; RECDx ve diğer şirketler göremez.</p>
          <div className="pj-form">
            <label className="pj-field" style={{ gridColumn: '1 / -1' }}>Ek keşif soruları<small className="pj-hint">Her satır: Konu | Soru | Neden önemli</small>
              <textarea id="sp-extra-q" className="ui-input" rows={6} value={extras.questions} onChange={(e) => setExtras((x) => ({ ...x, questions: e.target.value }))} /></label>
            <label className="pj-field" style={{ gridColumn: '1 / -1' }}>Sık atlanan gereksinimler<small className="pj-hint">Her satıra bir madde</small>
              <textarea id="sp-extra-m" className="ui-input" rows={4} value={extras.missed} onChange={(e) => setExtras((x) => ({ ...x, missed: e.target.value }))} /></label>
          </div>
        </Modal>
      )}
    </Card>
  );
}

/** Keşif & Tanım › Sektör paketi seçimi (#751). */
export function ProjectSectorPack({ project, editable }) {
  const [d, setD] = useState(null);
  const load = useCallback(() => api.getProjectSectorPack(project.id).then(setD).catch(() => setD({ options: [] })), [project.id]);
  useEffect(() => { load(); }, [load]);
  if (!d || !d.options.length) return null;
  const change = async (e) => {
    try {
      setD(await api.setProjectSectorPack(project.id, e.target.value || null));
      toast.success(e.target.value ? 'Sektör paketi seçildi; sonraki keşif turu ve plan önerisi bu paketi kullanır.' : 'Bu projede sektör paketi kullanılmayacak.');
    } catch (err) { toast.error(err.message); }
  };
  return (
    <div className="pj-field" style={{ marginBottom: 10 }}>
      <label htmlFor="sp-project">Sektör paketi</label>
      <select id="sp-project" className="ui-input" value={d.code || ''} onChange={change} disabled={!editable}>
        <option value="">Paket yok (yalnız genel sorular)</option>
        {d.options.map((o) => <option key={o.code} value={o.code}>{o.title} · sürüm {o.version}</option>)}
      </select>
      <small className="pj-hint">{d.code ? (d.auto ? 'Beyin AI isterlere ve şirketin sektörüne göre önerdi; değiştirebilirsiniz.' : 'Proje yöneticisi seçti.')
        : d.auto ? 'Beyin AI bu projeye uyan bir paket bulamadı; uygun olanı seçebilirsiniz.' : 'Proje yöneticisi paket kullanmamayı seçti.'}</small>
    </div>
  );
}
