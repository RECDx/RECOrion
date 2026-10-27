import React, { useCallback, useEffect, useState } from 'react';
import { Archive, FlaskConical, History, KeyRound, Pause, Play, Plus, Save, Sparkles, Trash2, Wand2, Zap } from 'lucide-react';
import { api } from '../../api';
import { Badge, Button, Card, EmptyState, Modal } from '../../ui/components';
import { confirmDialog, toast } from '../../ui/feedback';
import '../projects/projects.css';
import './integrations.css';

const TRIGGERS = { WEBHOOK: 'Anlık bildirim', POLL: 'İzleme', SCHEDULE: 'Zamanlayıcı' };
const STATUS = { ACTIVE: ['Etkin', 'success'], PAUSED: ['Duraklatıldı', 'neutral'] };
export const OUTCOMES = {
  DRAFTED: ['Taslak açıldı', 'success'], STARTED: ['Başlatıldı', 'success'], NOTIFIED: ['Bildirildi', 'success'],
  IGNORED: ['Koşul tutmadı', 'neutral'], DUPLICATE: ['Tekrar (işlenmişti)', 'neutral'], LOOP: ['Döngü engellendi', 'warning'],
  RATE_LIMITED: ['Hız sınırı', 'warning'], FAILED: ['Hata', 'danger'], REJECTED: ['İmza reddedildi', 'danger'], TEST: ['Deneme', 'info'],
};
const SOURCES = { WEBHOOK: 'anlık bildirim', POLL: 'izleme', SCHEDULE: 'zamanlayıcı', TEST: 'deneme' };
const OPS = [['eq', '='], ['ne', '≠'], ['contains', 'içerir'], ['in', 'şunlardan biri'], ['gt', '>'], ['gte', '≥'], ['lt', '<'], ['lte', '≤'], ['exists', 'dolu']];
const WEEKDAYS = ['Pazartesi', 'Salı', 'Çarşamba', 'Perşembe', 'Cuma', 'Cumartesi', 'Pazar'];
const APPS = [{ code: 'recqmind', title: 'RECQmind', hint: 'Helpdesk biletlerinden iade, iptal, kargo ve ürün sorusu Case\'leri; Case sonucu bilete yazılır.' },
  { code: 'recslip', title: 'RECSlip', hint: 'Sorunlu masraf fişinden Case; ay sonu masraf kapanışı; karar masraf kaydına iç not olarak yazılır.' }];
const fmt = (d) => (d ? new Date(d).toLocaleString('tr-TR', { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' }) : '');
const projectLink = (id) => `#/workspace?project=${id}&view=work`;

/** Kuralın tetik özeti: ne olunca çalışır. */
function whenText(r) {
  if (r.trigger === 'WEBHOOK') return `Anlık bildirim${r.event_type ? ` (${r.event_type})` : ''}`;
  if (r.trigger === 'POLL') return `${r.connection_name || 'bağlantı'} · ${r.poll?.args?.model || r.poll?.tool} her ${r.poll?.interval_minutes} dk izlenir`;
  const s = r.schedule || {};
  const day = s.every === 'WEEK' ? `her ${WEEKDAYS[s.weekday ?? 0]}` : s.every === 'MONTH' ? (s.day === -1 ? 'her ay sonu' : `her ayın ${s.day}.`) : 'her gün';
  return `${day} ${s.time}${s.summary === 'expense_month' ? ' · masraf özetiyle' : ''}`;
}

/** Örnek olay: kuralın türüne göre doldurulmuş JSON (deneme hiçbir şey açmaz). */
function sampleFor(r) {
  if (r.poll?.enrich === 'helpdesk_ticket') return { id: 900, name: 'İade talebi: ürün kutusu hasarlı geldi', description: '<p>İade etmek istiyorum.</p>', tag_ids: [], priority: '2' };
  if (r.poll?.enrich === 'hr_expense') return { id: 900, name: 'Taksi', date: new Date().toISOString().slice(0, 10), total_amount: 480, currency_id: [1, 'TRY'], nb_attachment: 0, rec_fld_vkn_tckn: '', rec_fld_is_mukerrer: false };
  if (r.trigger === 'SCHEDULE') return { date: new Date().toISOString().slice(0, 10), period: new Date().toISOString().slice(0, 7), is_month_end: true };
  return { id: 1, name: 'Örnek kayıt' };
}

/** Otomasyonlar (ADIM 13.5): kurallar, hazır kurallar, örnek olayla deneme, çalışma günlüğü. */
export default function Automations({ tenantId }) {
  const [rules, setRules] = useState(null);
  const [log, setLog] = useState([]);
  const [presets, setPresets] = useState({});
  const [people, setPeople] = useState([]);
  const [templates, setTemplates] = useState([]);
  const [conns, setConns] = useState([]);
  const [editing, setEditing] = useState(null);
  const [testing, setTesting] = useState(null);
  const [logOf, setLogOf] = useState(null);
  const [installing, setInstalling] = useState(null);
  const [secret, setSecret] = useState(null);
  const load = useCallback(() => Promise.all([
    api.getAutomations(tenantId).then(setRules), api.getCompanyAutomationLog(tenantId).then(setLog),
    ...APPS.map((a) => api.getAutomationPresets(tenantId, a.code).then((p) => setPresets((x) => ({ ...x, [a.code]: p })))),
  ]).catch((e) => { toast.error(e.message); setRules((r) => r || []); }), [tenantId]);
  useEffect(() => {
    if (!tenantId) return;
    load();
    api.getCompanyUsers(tenantId, { status: 'ACTIVE' }).then((u) => setPeople((u || []).filter((x) => x.actor_type === 'HUMAN'))).catch(() => setPeople([]));
    api.getProjectTemplates().then(setTemplates).catch(() => setTemplates([]));
    api.getIntegrations(tenantId).then(setConns).catch(() => setConns([]));
  }, [tenantId, load]);

  const act = async (fn, ok) => { try { const r = await fn(); if (ok) toast.success(typeof ok === 'function' ? ok(r) : ok); load(); return r; } catch (e) { toast.error(e.message); return null; } };
  const setStatus = async (r, status) => {
    if (status === 'ARCHIVED' && !(await confirmDialog({ message: `'${r.name}' arşivlensin mi? Kural çalışmaz; günlüğü saklanır.`, danger: true }))) return;
    act(() => api.setAutomationStatus(tenantId, r.id, status), { ACTIVE: 'Kural etkinleştirildi.', PAUSED: 'Kural duraklatıldı.', ARCHIVED: 'Kural arşivlendi.' }[status]);
  };
  const runNow = (r) => act(() => api.runAutomation(tenantId, r.id), (res) => {
    if (res.baseline) return 'İlk tur: mevcut kayıtlar başlangıç noktası olarak not edildi (eski kayıtlar için iş açılmaz).';
    const h = res.handled || [];
    const made = h.filter((x) => ['DRAFTED', 'STARTED', 'NOTIFIED'].includes(x.outcome)).length;
    return h.length ? `${h.length} olay işlendi; ${made} iş açıldı/bildirildi. Ayrıntı günlükte.` : 'Yeni veya değişen kayıt yok.';
  });
  const rotate = async (r) => {
    if (!(await confirmDialog({ message: 'Yeni imza anahtarı oluşturulsun mu? Eski anahtarla gelen bildirimler hemen reddedilir.' }))) return;
    const res = await act(() => api.rotateAutomationSecret(tenantId, r.id));
    if (res?.webhook_secret) setSecret({ rule: res, secret: res.webhook_secret });
  };

  if (!rules) return <Card title="Otomasyonlar"><p className="pj-hint">Yükleniyor…</p></Card>;
  return (
    <>
      <Card title="Otomasyonlar" subtitle="Dış sistemde bir şey olunca (yeni kayıt, değişiklik, zaman) RECOrion'da Case veya proje taslağı açılır. Açılan iş yöneticisinin onayını bekler; her olay silinemez günlüğe yazılır."
        actions={<Button icon={Plus} onClick={() => setEditing({})}>Yeni kural</Button>}>
        <div className="ui-grid-2" style={{ marginBottom: 12 }}>
          {APPS.map((a) => {
            const p = presets[a.code];
            const installed = (p?.categories || []).filter((c) => c.installed_on.length).length;
            return (
              <div key={a.code} className="ig-steps" aria-label={`${a.title} hazır kuralları`}>
                <p><strong>{a.title} hazır kuralları</strong> {p?.available ? <Badge tone="success">Kullanılabilir</Badge> : <Badge tone="neutral">Kapalı</Badge>}
                  {installed > 0 && <> <Badge tone="info">{installed}/{p.categories.length} kurulu</Badge></>}</p>
                <p className="pj-hint">{p?.available ? a.hint : p?.reason || 'Yükleniyor…'}</p>
                {p?.available && <Button size="sm" icon={Wand2} onClick={() => setInstalling({ app: a, preset: p })}>Hazır kuralları kur</Button>}
              </div>
            );
          })}
        </div>
        {rules.length === 0 ? <EmptyState icon={Zap} title="Henüz kural yok" description="Hazır kuralları kurun veya yeni kural ekleyin (RECAi anlatımınızdan taslak çıkarır)." /> : (
          <ul className="pj-list" aria-label="Otomasyon kuralları">
            {rules.map((r) => {
              const [label, tone] = STATUS[r.status] || [r.status, 'neutral'];
              return (
                <li key={r.id} style={{ flexWrap: 'wrap' }} aria-label={`Kural: ${r.name}`}>
                  <span><strong>{r.name}</strong> <Badge tone="neutral">{TRIGGERS[r.trigger]}</Badge> <Badge tone={tone}>{label}</Badge><br />
                    <small className="pj-hint">{whenText(r)}{r.conditions.length ? ` · ${r.conditions.length} koşul` : ''} · {r.action?.type === 'NOTIFY' ? 'bildirim' : r.action?.kind === 'PROJECT' ? 'proje açar' : 'Case açar'}
                      {r.next_run_at && r.status === 'ACTIVE' ? ` · sıradaki ${fmt(r.next_run_at)}` : ''}
                      {r.last_fired_at ? ` · son iş ${fmt(r.last_fired_at)} (${r.fire_count})` : ''}</small>
                    {r.last_error && <><br /><small className="ui-text-danger">{r.last_error}</small></>}
                    {r.trigger === 'WEBHOOK' && <><br /><code className="ig-inline">{r.webhook_url}</code></>}</span>
                  <Button size="sm" variant="secondary" icon={FlaskConical} onClick={() => setTesting(r)}>Dene</Button>
                  {['POLL', 'SCHEDULE'].includes(r.trigger) && r.status === 'ACTIVE' && <Button size="sm" variant="secondary" icon={Play} onClick={() => runNow(r)}>Hemen çalıştır</Button>}
                  <Button size="sm" variant="secondary" icon={History} onClick={() => setLogOf(r)}>Günlük</Button>
                  <Button size="sm" variant="secondary" onClick={() => setEditing(r)}>Düzenle</Button>
                  {r.trigger === 'WEBHOOK' && <Button size="sm" variant="ghost" icon={KeyRound} onClick={() => rotate(r)}>İmza anahtarı</Button>}
                  <Button size="sm" variant="ghost" icon={r.status === 'ACTIVE' ? Pause : Play} onClick={() => setStatus(r, r.status === 'ACTIVE' ? 'PAUSED' : 'ACTIVE')}>{r.status === 'ACTIVE' ? 'Duraklat' : 'Etkinleştir'}</Button>
                  <Button size="sm" variant="ghost" icon={Archive} onClick={() => setStatus(r, 'ARCHIVED')}>Arşivle</Button>
                </li>
              );
            })}
          </ul>
        )}
      </Card>
      <Card title="Otomasyon günlüğü" subtitle="Silinemez kayıt: hangi olay geldi, hangi kural ne yaptı (iş açıldı, koşul tutmadı, tekrar, döngü veya hız sınırı).">
        <LogTable rows={log} />
      </Card>
      {editing && <RuleModal tenantId={tenantId} rule={editing.id ? editing : null} conns={conns} people={people} templates={templates}
        onClose={() => setEditing(null)} onSaved={(saved) => { setEditing(null); load(); if (saved?.webhook_secret) setSecret({ rule: saved, secret: saved.webhook_secret }); }} />}
      {testing && <TestModal tenantId={tenantId} rule={testing} onClose={() => { setTesting(null); load(); }} />}
      {logOf && <RuleLogModal tenantId={tenantId} rule={logOf} onClose={() => setLogOf(null)} />}
      {installing && <PresetModal tenantId={tenantId} {...installing} people={people} onClose={() => setInstalling(null)} onDone={() => { setInstalling(null); load(); }} />}
      {secret && <SecretModal data={secret} onClose={() => setSecret(null)} />}
    </>
  );
}

function LogTable({ rows, withPayload = false }) {
  const [open, setOpen] = useState(null);
  if (!rows?.length) return <p className="pj-hint">Henüz olay yok.</p>;
  return (
    <div className="ui-table-scroll">
      <table className="ui-table" aria-label="Otomasyon olayları">
        <thead><tr><th>Zaman</th>{!withPayload && <th>Kural</th>}<th>Kaynak</th><th>Sonuç</th><th>Ayrıntı</th><th>İş</th></tr></thead>
        <tbody>{rows.map((r) => {
          const [label, tone] = OUTCOMES[r.outcome] || [r.outcome, 'neutral'];
          return (
            <React.Fragment key={r.id}>
              <tr>
                <td data-label="Zaman">{fmt(r.created_at)}</td>
                {!withPayload && <td data-label="Kural">{r.rule_name || '—'}</td>}
                <td data-label="Kaynak">{SOURCES[r.source] || r.source}{r.external_ref ? <><br /><small className="pj-hint">{r.external_ref}</small></> : null}</td>
                <td data-label="Sonuç"><Badge tone={tone}>{label}</Badge></td>
                <td data-label="Ayrıntı">{r.detail || '—'}{withPayload && r.payload && <> <Button size="sm" variant="ghost" onClick={() => setOpen(open === r.id ? null : r.id)}>{open === r.id ? 'Veriyi gizle' : 'Veri'}</Button></>}</td>
                <td data-label="İş">{r.project_id ? <a className="ig-link" href={projectLink(r.project_id)}>Aç</a> : '—'}</td>
              </tr>
              {open === r.id && <tr><td colSpan={5}><pre className="ig-code">{JSON.stringify(r.payload, null, 1)}</pre></td></tr>}
            </React.Fragment>
          );
        })}</tbody>
      </table>
    </div>
  );
}

function RuleLogModal({ tenantId, rule, onClose }) {
  const [rows, setRows] = useState(null);
  useEffect(() => { api.getAutomationLog(tenantId, rule.id).then(setRows).catch((e) => { toast.error(e.message); setRows([]); }); }, [tenantId, rule.id]);
  return (
    <Modal open onClose={onClose} title={`${rule.name} · günlük`} size="lg" footer={<Button variant="secondary" onClick={onClose}>Kapat</Button>}>
      {!rows ? <p className="pj-hint">Yükleniyor…</p> : <LogTable rows={rows} withPayload />}
    </Modal>
  );
}

/** Örnek olayla deneme: koşullar, döngü engeli değerlendirilir; hiçbir şey açılmaz. */
function TestModal({ tenantId, rule, onClose }) {
  const [text, setText] = useState(JSON.stringify(sampleFor(rule), null, 1));
  const [eventType, setEventType] = useState(rule.event_type || '');
  const [res, setRes] = useState(null);
  const [busy, setBusy] = useState(false);
  const run = async () => {
    let payload;
    try { payload = JSON.parse(text || '{}'); } catch { toast.warning('Örnek olay geçerli JSON olmalı.'); return; }
    setBusy(true);
    try { setRes(await api.testAutomation(tenantId, rule.id, payload, eventType)); } catch (e) { toast.error(e.message); } finally { setBusy(false); }
  };
  const [label, tone] = res ? OUTCOMES[res.outcome] || [res.outcome, 'neutral'] : [];
  return (
    <Modal open onClose={onClose} title={`${rule.name} · örnek olayla dene`} size="md"
      footer={<><Button variant="secondary" onClick={onClose}>Kapat</Button><Button icon={FlaskConical} disabled={busy} onClick={run}>{busy ? 'Deneniyor…' : 'Dene'}</Button></>}>
      <p className="pj-hint">Örnek veriyle kuralın ne yapacağı söylenir; iş açılmaz, dış sisteme yazılmaz. Deneme günlüğe "deneme" olarak yazılır.</p>
      <div className="pj-form">
        {rule.trigger === 'WEBHOOK' && (
          <div className="pj-field full">
            <label htmlFor="at-event">Olay türü</label>
            <input id="at-event" className="ui-input" value={eventType} onChange={(e) => setEventType(e.target.value)} placeholder="ör. order.created" />
          </div>
        )}
        <div className="pj-field full">
          <label htmlFor="at-sample">Örnek olay (JSON)</label>
          <textarea id="at-sample" className="ui-input ig-inline" rows={10} value={text} onChange={(e) => setText(e.target.value)} />
        </div>
      </div>
      {res && <div className="ig-advice" aria-label="Deneme sonucu"><p><Badge tone={tone}>{label}</Badge></p><p>{res.detail}</p></div>}
    </Modal>
  );
}

/** RECDx uygulamasının hazır kurallarını kurma: bağlantı, iş yöneticisi, kurallar. */
function PresetModal({ tenantId, app, preset, people, onClose, onDone }) {
  const [conn, setConn] = useState(preset.connections[0]?.id || '');
  const [manager, setManager] = useState(people[0]?.id || '');
  const [cats, setCats] = useState(new Set(preset.categories.filter((c) => c.template_ready).map((c) => c.code)));
  const [interval, setInterval_] = useState(app.code === 'recqmind' ? 10 : 15);
  const [busy, setBusy] = useState(false);
  const flip = (c) => setCats((s) => { const n = new Set(s); n.has(c) ? n.delete(c) : n.add(c); return n; });
  const install = async () => {
    setBusy(true);
    try {
      const r = await api.installAutomationPresets(tenantId, app.code, { connection_id: conn, manager_actor_id: manager, categories: [...cats], interval_minutes: Number(interval) });
      toast.success(`${r.rules.length} kural kuruldu.`);
      (r.notes || []).forEach((n) => toast.info(n));
      onDone();
    } catch (e) { toast.error(e.message); } finally { setBusy(false); }
  };
  return (
    <Modal open onClose={onClose} title={`${app.title} hazır kuralları`} size="md"
      footer={<><Button variant="secondary" onClick={onClose}>Vazgeç</Button><Button icon={Wand2} disabled={busy || !conn || !manager || !cats.size} onClick={install}>{busy ? 'Kuruluyor…' : 'Kur'}</Button></>}>
      <p className="pj-hint">{app.hint} Açılan Case'ler taslakta kalır ve yöneticisine bildirilir. Odoo'ya yazma her zaman önizleme ve onayla yapılır.</p>
      <div className="pj-form">
        <div className="pj-field">
          <label htmlFor="ap-conn">Odoo bağlantısı</label>
          <select id="ap-conn" className="ui-input" value={conn} onChange={(e) => setConn(e.target.value)}>
            {preset.connections.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
          </select>
        </div>
        <div className="pj-field">
          <label htmlFor="ap-manager">Case yöneticisi</label>
          <select id="ap-manager" className="ui-input" value={manager} onChange={(e) => setManager(e.target.value)}>
            {people.map((p) => <option key={p.id} value={p.id}>{p.display_name}</option>)}
          </select>
        </div>
        <div className="pj-field">
          <label htmlFor="ap-interval">İzleme sıklığı (dk)</label>
          <input id="ap-interval" className="ui-input" type="number" min={5} max={1440} value={interval} onChange={(e) => setInterval_(e.target.value)} />
        </div>
        <fieldset className="pj-field full ig-steps">
          <legend className="pj-hint">Kurulacak kurallar</legend>
          {preset.categories.map((c) => {
            const here = c.installed_on.includes(conn);
            return (
              <label key={c.code} style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
                <input type="checkbox" disabled={!c.template_ready || here} checked={cats.has(c.code) && !here} onChange={() => flip(c.code)} />
                {c.label} <small className="pj-hint">· {c.rule_name}{here ? ' · bu bağlantıda kurulu' : ''}{c.template_ready ? '' : ' · şablon yok'}</small>
              </label>
            );
          })}
        </fieldset>
      </div>
    </Modal>
  );
}

function SecretModal({ data, onClose }) {
  const copy = () => navigator.clipboard?.writeText(data.secret).then(() => toast.success('Anahtar kopyalandı.'), () => toast.error('Kopyalanamadı; elle seçin.'));
  return (
    <Modal open onClose={onClose} title={`${data.rule.name} · imza anahtarı`} size="md"
      footer={<><Button variant="secondary" onClick={copy}>Kopyala</Button><Button onClick={onClose}>Kaydettim, kapat</Button></>}>
      <p className="ui-text-danger">Bu anahtar bir daha gösterilmez. Kaybolursa yeni anahtar oluşturun (eskisi geçersiz olur).</p>
      <pre aria-label="İmza anahtarı" className="ig-code">{data.secret}</pre>
      <p className="pj-hint">Dış sistem bildirimi şu adrese gönderir: <code className="ig-inline">{data.rule.webhook_url}</code></p>
      <p className="pj-hint">Başlıklar: X-RECOrion-Timestamp (Unix saniye) ve X-RECOrion-Signature = "sha256=" + HMAC-SHA256(anahtar, zaman + "." + gövde). 5 dakikadan eski istek reddedilir.</p>
    </Modal>
  );
}

/** Kural ekle/düzenle: ne olunca + koşul + ne yapılsın. RECAi anlatımdan taslak çıkarabilir. */
function RuleModal({ tenantId, rule, conns, people, templates, onClose, onSaved }) {
  const a0 = rule?.action || {};
  const [f, setF] = useState({
    name: rule?.name || '', description: rule?.description || '', trigger: rule?.trigger || 'WEBHOOK', connection_id: rule?.connection_id || '',
    event_type: rule?.event_type || '', model: rule?.poll?.args?.model || '', interval: rule?.poll?.interval_minutes || 15,
    version_field: rule?.poll?.version_field || '', every: rule?.schedule?.every || 'DAY', time: rule?.schedule?.time || '09:00',
    weekday: rule?.schedule?.weekday ?? 0, day: rule?.schedule?.day ?? 1, type: a0.type || 'CREATE_CASE', manager: a0.manager_actor_id || people[0]?.id || '',
    template: a0.template_id || '', caseName: a0.name || '', notify: (a0.notify_actor_ids || [])[0] || '', message: a0.message || '',
    autoStart: !!a0.auto_start, requirements: rule?.requirements || '', rate: rule?.rate_limit_per_hour || 20,
  });
  const [conds, setConds] = useState(rule?.conditions || []);
  const [story, setStory] = useState('');
  const [busy, setBusy] = useState(false);
  const set = (k) => (e) => setF((x) => ({ ...x, [k]: e.target.type === 'checkbox' ? e.target.checked : e.target.value }));
  const kind = f.type === 'CREATE_PROJECT' ? 'PROJECT' : 'CASE';
  const tpls = templates.filter((t) => t.kind === kind && t.status !== 'ARCHIVED');
  const suggest = async () => {
    setBusy(true);
    try {
      const s = await api.suggestAutomation(tenantId, story);
      setF((x) => ({ ...x, name: s.name || x.name, event_type: s.event_type || x.event_type, caseName: s.case_name || x.caseName,
        type: s.kind === 'PROJECT' ? 'CREATE_PROJECT' : 'CREATE_CASE', requirements: s.requirements || x.requirements }));
      if (Array.isArray(s.conditions)) setConds(s.conditions);
      toast.success('RECAi taslağı doldurdu; kontrol edip kaydedin.');
      if (s.notes) toast.info(s.notes);
    } catch (e) { toast.error(e.message); } finally { setBusy(false); }
  };
  const save = async () => {
    const body = { name: f.name.trim(), description: f.description || null, trigger: f.trigger, connection_id: f.connection_id || null,
      event_type: f.trigger === 'WEBHOOK' ? f.event_type || null : null, conditions: conds.filter((c) => c.field),
      requirements: f.requirements || null, rate_limit_per_hour: Number(f.rate) || 20 };
    if (f.trigger === 'POLL') {
      const old = rule?.poll || {};  // hazır kuralın zenginleştirme/alan ayarları korunur
      body.poll = { ...old, tool: old.tool || 'search_records', args: { order: 'id desc', limit: 50, domain: [], ...(old.args || {}), model: f.model },
        id_field: old.id_field || 'id', version_field: f.version_field || null, interval_minutes: Number(f.interval) || 15 };
    }
    if (f.trigger === 'SCHEDULE') body.schedule = { ...(rule?.schedule || {}), every: f.every, time: f.time, weekday: Number(f.weekday), day: Number(f.day) };
    body.action = f.type === 'NOTIFY' ? { type: 'NOTIFY', notify_actor_ids: f.notify ? [f.notify] : [], message: f.message }
      : { ...a0, type: f.type, manager_actor_id: f.manager, template_id: f.template || null, name: f.caseName, auto_start: f.autoStart };
    setBusy(true);
    try {
      const saved = rule ? await api.updateAutomation(tenantId, rule.id, body) : await api.createAutomation(tenantId, body);
      toast.success(rule ? 'Kural güncellendi.' : 'Kural eklendi.');
      onSaved(saved);
    } catch (e) { toast.error(e.message); } finally { setBusy(false); }
  };
  const odoo = conns.filter((c) => c.status === 'ACTIVE');
  return (
    <Modal open onClose={onClose} title={rule ? `${rule.name} · düzenle` : 'Yeni otomasyon kuralı'} size="lg"
      footer={<><Button variant="secondary" onClick={onClose}>Vazgeç</Button><Button icon={Save} disabled={busy || f.name.trim().length < 2} onClick={save}>{busy ? 'Kaydediliyor…' : 'Kaydet'}</Button></>}>
      {!rule && (
        <div className="ig-advisor">
          <label htmlFor="ar-story"><Sparkles size={14} /> RECAi ile taslak</label>
          <textarea id="ar-story" className="ui-input" rows={2} value={story} onChange={(e) => setStory(e.target.value)}
            placeholder="ör. Odoo'da 50.000 TL üzeri satış siparişi onaylanınca sevkiyat planlama Case'i açılsın" />
          <div className="pj-actions" style={{ marginTop: 6 }}><Button size="sm" variant="secondary" icon={Sparkles} disabled={busy || story.trim().length < 10} onClick={suggest}>Taslak çıkar</Button></div>
        </div>
      )}
      <div className="pj-form" style={{ marginTop: 12 }}>
        <div className="pj-field full"><label htmlFor="ar-name">Kural adı</label><input id="ar-name" className="ui-input" value={f.name} maxLength={160} onChange={set('name')} /></div>
        <div className="pj-field">
          <label htmlFor="ar-trigger">Ne olunca</label>
          <select id="ar-trigger" className="ui-input" value={f.trigger} onChange={set('trigger')}>
            {Object.entries(TRIGGERS).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
          </select>
        </div>
        {f.trigger !== 'WEBHOOK' && (
          <div className="pj-field">
            <label htmlFor="ar-conn">Bağlantı{f.trigger === 'POLL' ? ' *' : ''}</label>
            <select id="ar-conn" className="ui-input" value={f.connection_id} onChange={set('connection_id')}>
              <option value="">—</option>
              {odoo.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
            </select>
          </div>
        )}
        {f.trigger === 'WEBHOOK' && <div className="pj-field"><label htmlFor="ar-event">Olay türü (isteğe bağlı)</label><input id="ar-event" className="ui-input" value={f.event_type} onChange={set('event_type')} placeholder="ör. order.created" /></div>}
        {f.trigger === 'POLL' && <>
          <div className="pj-field"><label htmlFor="ar-model">İzlenen model</label><input id="ar-model" className="ui-input" value={f.model} onChange={set('model')} placeholder="ör. sale.order" /></div>
          <div className="pj-field"><label htmlFor="ar-interval">Sıklık (dk)</label><input id="ar-interval" className="ui-input" type="number" min={5} max={1440} value={f.interval} onChange={set('interval')} /></div>
          <div className="pj-field"><label htmlFor="ar-version">Değişiklik alanı (isteğe bağlı)</label><input id="ar-version" className="ui-input" value={f.version_field} onChange={set('version_field')} placeholder="ör. write_date; boşsa yalnızca yeni kayıt" /></div>
        </>}
        {f.trigger === 'SCHEDULE' && <>
          <div className="pj-field">
            <label htmlFor="ar-every">Sıklık</label>
            <select id="ar-every" className="ui-input" value={f.every} onChange={set('every')}><option value="DAY">Her gün</option><option value="WEEK">Her hafta</option><option value="MONTH">Her ay</option></select>
          </div>
          <div className="pj-field"><label htmlFor="ar-time">Saat</label><input id="ar-time" className="ui-input" type="time" value={f.time} onChange={set('time')} /></div>
          {f.every === 'WEEK' && <div className="pj-field"><label htmlFor="ar-wd">Gün</label><select id="ar-wd" className="ui-input" value={f.weekday} onChange={set('weekday')}>{WEEKDAYS.map((d, i) => <option key={d} value={i}>{d}</option>)}</select></div>}
          {f.every === 'MONTH' && <div className="pj-field"><label htmlFor="ar-day">Ayın günü</label><select id="ar-day" className="ui-input" value={f.day} onChange={set('day')}><option value={-1}>Ay sonu</option>{Array.from({ length: 28 }, (_, i) => <option key={i + 1} value={i + 1}>{i + 1}</option>)}</select></div>}
        </>}
        <fieldset className="pj-field full ig-steps" aria-label="Koşullar">
          <legend className="pj-hint">Koşullar (hepsi sağlanmalı; iç alan için nokta: ör. ticket.category)</legend>
          {conds.map((c, i) => (
            <div key={i} className="pj-actions" style={{ marginBottom: 6 }}>
              <input aria-label="Alan" className="ui-input" style={{ flex: 2 }} value={c.field} onChange={(e) => setConds((x) => x.map((y, j) => (j === i ? { ...y, field: e.target.value } : y)))} placeholder="alan" />
              <select aria-label="İşlem" className="ui-input" style={{ flex: 1 }} value={c.op} onChange={(e) => setConds((x) => x.map((y, j) => (j === i ? { ...y, op: e.target.value } : y)))}>
                {OPS.map(([k, v]) => <option key={k} value={k}>{v}</option>)}
              </select>
              {c.op !== 'exists' && <input aria-label="Değer" className="ui-input" style={{ flex: 2 }} value={c.value ?? ''} onChange={(e) => setConds((x) => x.map((y, j) => (j === i ? { ...y, value: e.target.value } : y)))} placeholder="değer" />}
              <Button size="sm" variant="ghost" icon={Trash2} aria-label="Koşulu sil" onClick={() => setConds((x) => x.filter((_, j) => j !== i))} />
            </div>
          ))}
          <Button size="sm" variant="secondary" icon={Plus} onClick={() => setConds((x) => [...x, { field: '', op: 'eq', value: '' }])}>Koşul ekle</Button>
        </fieldset>
        <div className="pj-field">
          <label htmlFor="ar-type">Ne yapılsın</label>
          <select id="ar-type" className="ui-input" value={f.type} onChange={set('type')}><option value="CREATE_CASE">Case aç</option><option value="CREATE_PROJECT">Proje aç</option><option value="NOTIFY">Yalnızca bildir</option></select>
        </div>
        {f.type === 'NOTIFY' ? <>
          <div className="pj-field"><label htmlFor="ar-notify">Bildirilecek kişi</label><select id="ar-notify" className="ui-input" value={f.notify} onChange={set('notify')}><option value="">—</option>{people.map((p) => <option key={p.id} value={p.id}>{p.display_name}</option>)}</select></div>
          <div className="pj-field full"><label htmlFor="ar-msg">Mesaj ({'{{alan}}'} yer tutucuları kullanılabilir)</label><textarea id="ar-msg" className="ui-input" rows={2} value={f.message} onChange={set('message')} /></div>
        </> : <>
          <div className="pj-field"><label htmlFor="ar-manager">İşin yöneticisi</label><select id="ar-manager" className="ui-input" value={f.manager} onChange={set('manager')}>{people.map((p) => <option key={p.id} value={p.id}>{p.display_name}</option>)}</select></div>
          <div className="pj-field"><label htmlFor="ar-tpl">Şablon (isteğe bağlı)</label><select id="ar-tpl" className="ui-input" value={f.template} onChange={set('template')}><option value="">— şablonsuz (RECAi planlar)</option>{tpls.map((t) => <option key={t.id} value={t.id}>{t.name}</option>)}</select></div>
          <div className="pj-field full"><label htmlFor="ar-case">Açılacak işin adı ({'{{alan}}'} ile)</label><input id="ar-case" className="ui-input" value={f.caseName} onChange={set('caseName')} placeholder="ör. Sevkiyat: {{name}}" /></div>
          <div className="pj-field full"><label htmlFor="ar-req">İsterler</label><textarea id="ar-req" className="ui-input" rows={4} value={f.requirements} onChange={set('requirements')} /></div>
          <label className="pj-field full" style={{ flexDirection: 'row', alignItems: 'center', gap: 6 }}>
            <input type="checkbox" checked={f.autoStart} onChange={set('autoStart')} disabled={!f.template} /> Şablon planıyla otomatik başlat (adımlara AI personel atanabilirse; yoksa taslakta kalır)
          </label>
        </>}
        <div className="pj-field"><label htmlFor="ar-rate">Saatlik en fazla iş</label><input id="ar-rate" className="ui-input" type="number" min={1} max={200} value={f.rate} onChange={set('rate')} /></div>
      </div>
    </Modal>
  );
}
