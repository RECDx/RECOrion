import React, { useCallback, useEffect, useState } from 'react';
import { BookOpenCheck, Plus, Trash2 } from 'lucide-react';
import { api } from '../../api';
import { Badge, Button, Card, EmptyState, Modal } from '../../ui/components';
import { confirmDialog, toast } from '../../ui/feedback';
import '../projects/projects.css';
import './regulations.css';

const fmtDate = (d) => (d ? new Date(d).toLocaleDateString('tr-TR', { day: '2-digit', month: 'long', year: 'numeric' }) : '—');

function CardView({ c }) {
  return (
    <article className="rg-card">
      <h4>{c.title}</h4>
      {c.legal_basis && <p className="pj-hint">Dayanak: {c.legal_basis}</p>}
      <p className="rg-body">{c.body}</p>
      {c.sources?.length > 0 && (
        <p className="pj-hint">Resmi kaynak: {c.sources.map((s, i) => (
          <React.Fragment key={s.url}>{i > 0 && ' · '}<a href={s.url} target="_blank" rel="noopener noreferrer">{s.title}</a></React.Fragment>
        ))}</p>
      )}
    </article>
  );
}

/** Şirket Yönetimi › Mevzuat Paketleri (ADIM 11.2): RECDx uzman kontrolünden geçmiş paketleri açma/kapama ve okuma. */
export function CompanyRegulations({ tenantId, canManage }) {
  const [list, setList] = useState(null);
  const [viewing, setViewing] = useState(null);
  const load = useCallback(() => api.getCompanyRegulationPacks(tenantId).then(setList).catch((e) => toast.error(e.message)), [tenantId]);
  useEffect(() => { if (tenantId) load(); }, [tenantId, load]);
  const toggle = async (p) => {
    try {
      await api.setCompanyRegulationPack(tenantId, p.id, !p.enabled);
      toast.success(p.enabled ? `'${p.title}' kapatıldı.` : `'${p.title}' açıldı; AI personel ilgili işlerde bu kartları kaynak göstererek kullanır.`);
      load();
    } catch (e) { toast.error(e.message); }
  };
  const open = async (p) => { try { setViewing(await api.getCompanyRegulationPack(tenantId, p.id)); } catch (e) { toast.error(e.message); } };

  return (
    <Card title="Mevzuat bilgi paketleri" subtitle="Açtığınız paketlerdeki özet kartları AI personel ilgili işlerde kaynak ve sürüm göstererek kullanır. Kartlar RECDx'te bir uzman tarafından kontrol edilip yayımlanır.">
      <p className="pj-note" role="note">Bu paketler genel bilgilendirme amaçlıdır; hukuki veya mali danışmanlık yerine geçmez. Oran, tutar ve süre gibi değişebilen bilgiler için resmi kaynağa bakın.</p>
      {!list ? <p className="pj-hint">Yükleniyor…</p> : list.length === 0 ? (
        <EmptyState icon={BookOpenCheck} title="Henüz yayımlanmış paket yok" description="RECDx uzman kontrolünü tamamladığında paketler burada görünür." />
      ) : (
        <ul className="pj-list" aria-label="Mevzuat paketleri">
          {list.map((p) => (
            <li key={p.id} style={{ flexWrap: 'wrap' }}>
              <span><strong>{p.title}</strong> <Badge tone={p.enabled ? 'success' : 'neutral'}>{p.enabled ? 'Açık' : 'Kapalı'}</Badge><br />
                <small className="pj-hint">Sürüm {p.version} · {p.card_count} kart · kontrol: {fmtDate(p.checked_at)} ({p.reviewer_name})</small></span>
              <Button size="sm" variant="secondary" onClick={() => open(p)}>Kartları gör</Button>
              {canManage && <Button size="sm" variant={p.enabled ? 'ghost' : 'primary'} onClick={() => toggle(p)}>{p.enabled ? 'Kapat' : 'Aç'}</Button>}
            </li>
          ))}
        </ul>
      )}
      {viewing && (
        <Modal open onClose={() => setViewing(null)} title={`${viewing.title} · sürüm ${viewing.version}`} size="lg"
          footer={<Button onClick={() => setViewing(null)}>Kapat</Button>}>
          <p className="pj-hint">Kontrol eden: {viewing.reviewer_name} · {fmtDate(viewing.checked_at)}</p>
          {viewing.cards.map((c) => <CardView key={c.code} c={c} />)}
          <p className="pj-note" role="note">{viewing.disclaimer}</p>
        </Modal>
      )}
    </Card>
  );
}

/** Süper Admin › Mevzuat Paketleri (ADIM 11.2): taslak kartları düzenleme, uzman kontrolü beyanıyla yayımlama. */
export function RegulationAdmin() {
  const [list, setList] = useState(null);
  const [editing, setEditing] = useState(null);
  const [publishing, setPublishing] = useState(null);
  const load = useCallback(() => api.getRegulationPacksAdmin().then(setList).catch((e) => toast.error(e.message)), []);
  useEffect(() => { load(); }, [load]);

  return (
    <Card title="Mevzuat bilgi paketleri" subtitle="Taslaklar yalnızca burada görünür. Şirketler ve AI personel yalnızca uzman kontrolünden geçip yayımlanan sürümü görür.">
      {!list ? <p className="pj-hint">Yükleniyor…</p> : (
        <ul className="pj-list" aria-label="Mevzuat paketleri (yönetim)">
          {list.map((p) => (
            <li key={p.id} style={{ flexWrap: 'wrap' }}>
              <span><strong>{p.title}</strong>{' '}
                {p.published ? <Badge tone="success">Yayında · sürüm {p.published.version}</Badge> : <Badge tone="warning">Taslak · uzman kontrolü bekliyor</Badge>}
                {p.published && p.changed_since_publish && <> <Badge tone="info">Yayımlanmamış değişiklik var</Badge></>}<br />
                <small className="pj-hint">{p.draft_cards.length} taslak kart{p.published ? ` · son yayın: ${fmtDate(p.published.published_at)}, kontrol eden ${p.published.reviewer_name}` : ''}</small></span>
              <Button size="sm" variant="secondary" onClick={() => setEditing(p)}>Kartları düzenle</Button>
              <Button size="sm" disabled={!p.draft_cards.length || (p.published && !p.changed_since_publish)} onClick={() => setPublishing(p)}>Uzman kontrolüyle yayımla</Button>
            </li>
          ))}
        </ul>
      )}
      {editing && <PackEditor pack={editing} onClose={() => setEditing(null)} onSaved={() => { setEditing(null); load(); }} />}
      {publishing && <PublishModal pack={publishing} onClose={() => setPublishing(null)} onDone={() => { setPublishing(null); load(); }} />}
    </Card>
  );
}

const toForm = (c) => ({ ...c, tags: (c.tags || []).join(', '), sources: (c.sources || []).map((s) => `${s.title} | ${s.url}`).join('\n') });
const fromForm = (c) => ({ ...c, tags: c.tags.split(',').map((t) => t.trim()).filter(Boolean),
  sources: c.sources.split('\n').map((l) => l.split('|').map((x) => x.trim())).filter(([, u]) => u).map(([t, u]) => ({ title: t || u, url: u })) });

function PackEditor({ pack, onClose, onSaved }) {
  const [cards, setCards] = useState(pack.draft_cards.map(toForm));
  const [busy, setBusy] = useState(false);
  const set = (i, k) => (e) => setCards((all) => all.map((c, j) => (j === i ? { ...c, [k]: e.target.value } : c)));
  const save = async () => {
    setBusy(true);
    try {
      await api.updateRegulationPack(pack.id, { cards: cards.map(fromForm) });
      toast.success(pack.published ? 'Taslak kaydedildi; yayındaki sürüm değişmedi. Uzman kontrolünden sonra yeniden yayımlayın.' : 'Taslak kaydedildi.');
      onSaved();
    } catch (e) { toast.error(e.message); } finally { setBusy(false); }
  };
  const remove = async (i) => { if (await confirmDialog({ message: 'Kart taslaktan çıkarılsın mı?' })) setCards((all) => all.filter((_, j) => j !== i)); };
  return (
    <Modal open onClose={onClose} title={`${pack.title} · taslak kartlar`} size="lg"
      footer={<><Button variant="secondary" onClick={onClose}>Vazgeç</Button><Button onClick={save} disabled={busy}>{busy ? 'Kaydediliyor…' : 'Taslağı kaydet'}</Button></>}>
      {cards.map((c, i) => (
        <div className="rg-edit" key={c.code || i}>
          <div className="pj-form">
            <label className="pj-field">Başlık<input className="ui-input" value={c.title} onChange={set(i, 'title')} /></label>
            <label className="pj-field">Yasal dayanak<input className="ui-input" value={c.legal_basis || ''} onChange={set(i, 'legal_basis')} /></label>
            <label className="pj-field" style={{ gridColumn: '1 / -1' }}>Metin<textarea className="ui-input" rows={5} value={c.body} onChange={set(i, 'body')} /></label>
            <label className="pj-field">Etiketler (virgülle)<input className="ui-input" value={c.tags} onChange={set(i, 'tags')} /></label>
            <label className="pj-field">Resmi kaynaklar (her satır: başlık | https://…)<textarea className="ui-input" rows={2} value={c.sources} onChange={set(i, 'sources')} /></label>
          </div>
          <Button size="sm" variant="ghost" icon={Trash2} onClick={() => remove(i)}>Kartı çıkar</Button>
        </div>
      ))}
      <Button size="sm" variant="secondary" icon={Plus} onClick={() => setCards((all) => [...all, toForm({ code: '', title: '', body: '', legal_basis: '', tags: [], sources: [] })])}>Kart ekle</Button>
    </Modal>
  );
}

function PublishModal({ pack, onClose, onDone }) {
  const today = new Date().toISOString().slice(0, 10);
  const [form, setForm] = useState({ expert_confirmed: false, reviewer_name: '', checked_at: today, note: '' });
  const [busy, setBusy] = useState(false);
  const publish = async () => {
    setBusy(true);
    try {
      const r = await api.publishRegulationPack(pack.id, form);
      toast.success(`'${pack.title}' sürüm ${r.published.version} yayımlandı.`);
      onDone();
    } catch (e) { toast.error(e.message); } finally { setBusy(false); }
  };
  return (
    <Modal open onClose={onClose} title={`${pack.title} · yayımla`} size="md"
      footer={<><Button variant="secondary" onClick={onClose}>Vazgeç</Button>
        <Button onClick={publish} disabled={busy || !form.expert_confirmed || form.reviewer_name.trim().length < 3}>{busy ? 'Yayımlanıyor…' : 'Yayımla'}</Button></>}>
      <p className="pj-note" role="note">Kartların ilk sürümü Claude tarafından hazırlandı. Yayından önce bir hukuk/mali müşavirlik uzmanının güncel mevzuata
        göre kontrol etmesi zorunludur; yayımlanan sürüm tüm şirketlerin AI personeli tarafından kullanılabilir.</p>
      <label className="pj-hint" style={{ display: 'flex', gap: 8, margin: '10px 0' }}>
        <input type="checkbox" checked={form.expert_confirmed} onChange={(e) => setForm((f) => ({ ...f, expert_confirmed: e.target.checked }))} />
        Kartlar bir uzman tarafından güncel mevzuata göre kontrol edildi.
      </label>
      <div className="pj-form">
        <label className="pj-field">Kontrol eden uzman *<input id="rg-reviewer" className="ui-input" value={form.reviewer_name} maxLength={120}
          onChange={(e) => setForm((f) => ({ ...f, reviewer_name: e.target.value }))} placeholder="Ad Soyad, unvan" /></label>
        <label className="pj-field">Kontrol tarihi *<input className="ui-input" type="date" max={today} value={form.checked_at}
          onChange={(e) => setForm((f) => ({ ...f, checked_at: e.target.value }))} /></label>
        <label className="pj-field" style={{ gridColumn: '1 / -1' }}>Not<textarea className="ui-input" rows={2} value={form.note} maxLength={2000}
          onChange={(e) => setForm((f) => ({ ...f, note: e.target.value }))} /></label>
      </div>
    </Modal>
  );
}
