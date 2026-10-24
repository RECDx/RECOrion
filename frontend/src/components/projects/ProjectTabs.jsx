import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { BellRing, CalendarRange, CheckCircle2, Circle, Library, Play, Send, Trash2, UserPlus } from 'lucide-react';
import { api } from '../../api';
import { Badge, Button, Card, EmptyState } from '../../ui/components';
import { confirmDialog, toast } from '../../ui/feedback';
import { ProjectTransfers } from '../integrations/Transfers';
import { fmtDay, isEditable } from './projectMeta';

const ROLE = { MANAGER: 'Proje yöneticisi', MEMBER: 'Ekip üyesi', AGENT: 'AI personel' };
const fmtTl = (n) => (n == null ? '—' : `${Number(n).toLocaleString('tr-TR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} ₺`);
const fmtNum = (n) => Number(n || 0).toLocaleString('tr-TR', { maximumFractionDigits: 0 });

/** Ekip & Simülasyon (ADIM 6.4): insan/AI ekip, tarih, süre, kredi ve risk simülasyonu. */
export function TeamSimTab({ project, actors, onChanged }) {
  const editable = project.can_manage && isEditable(project);
  const [pick, setPick] = useState('');
  const [start, setStart] = useState(project.start_date || '');
  const [busy, setBusy] = useState('');
  const sim = project.simulation;
  const inTeam = new Set(project.members.map((m) => m.actor_id));
  const candidates = actors.filter((a) => !inTeam.has(a.id) && a.status !== 'DISABLED' && a.status !== 'DISMISSED');

  const run = async (label, fn) => {
    setBusy(label);
    try { await fn(); onChanged(); } catch (e) { toast.error(e.message); } finally { setBusy(''); }
  };
  const addMember = () => pick && run('add', async () => { await api.addProjectMember(project.id, pick); setPick(''); toast.success('Ekibe eklendi.'); });
  const removeMember = (m) => run('rm', async () => {
    if (!(await confirmDialog({ message: `${m.display_name} ekipten çıkarılsın mı?` }))) return;
    await api.removeProjectMember(project.id, m.actor_id);
  });
  const simulate = () => run('sim', async () => {
    const r = await api.simulateProject(project.id, start || null);
    toast.success(`Tahmini bitiş ${fmtDay(r.end_date)} (${r.workdays} iş günü).`);
  });
  const applyDates = () => run('dates', async () => {
    await api.updateProject(project.id, { start_date: sim.start_date, end_date: sim.end_date });
    toast.success('Simülasyon tarihleri projeye uygulandı.');
  });

  const range = useMemo(() => {
    if (!sim?.timeline?.length) return null;
    const a = new Date(sim.start_date).getTime();
    const b = new Date(sim.end_date).getTime() + 86400000;
    return { a, span: Math.max(b - a, 86400000) };
  }, [sim]);

  return (
    <div className="pj-split">
      <Card title="Proje ekibi" subtitle="İnsan personel ve AI personel. AI personel plan onayında atanan adımlara göre eklenir.">
        <ul className="pj-list">
          {project.members.map((m) => (
            <li key={m.actor_id}>
              <span><strong>{m.display_name}</strong><br /><small className="pj-hint">{ROLE[m.role] || m.role}{m.email ? ` · ${m.email}` : ''}</small></span>
              <Badge tone={m.actor_type === 'AI_AGENT' ? 'info' : 'neutral'}>{m.actor_type === 'AI_AGENT' ? 'AI' : 'İnsan'}</Badge>
              {project.can_manage && m.role !== 'MANAGER' && (
                <button type="button" className="ui-icon-btn" aria-label="Ekipten çıkar" onClick={() => removeMember(m)}><Trash2 size={14} /></button>
              )}
            </li>
          ))}
        </ul>
        {project.can_manage && (
          <div className="pj-actions" style={{ marginTop: 10 }}>
            <select className="ui-input" style={{ flex: 1, minWidth: 180 }} aria-label="Eklenecek personel" value={pick} onChange={(e) => setPick(e.target.value)}>
              <option value="">Personel seçin…</option>
              <optgroup label="İnsan personel">
                {candidates.filter((a) => a.actor_type === 'HUMAN').map((a) => <option key={a.id} value={a.id}>{a.display_name}</option>)}
              </optgroup>
              <optgroup label="AI personel">
                {candidates.filter((a) => a.actor_type === 'AI_AGENT').map((a) => <option key={a.id} value={a.id}>{a.display_name} · {a.role}</option>)}
              </optgroup>
            </select>
            <Button variant="secondary" icon={UserPlus} onClick={addMember} disabled={!pick || !!busy}>Ekle</Button>
          </div>
        )}
      </Card>

      <Card title="Simülasyon" subtitle="İş günü takvimi, bağımlılıklar ve personel kapasitesiyle tarih, süre ve kredi tahmini."
        actions={editable && (
          <div className="pj-actions">
            <input type="date" className="ui-input" aria-label="Başlangıç tarihi" value={start} onChange={(e) => setStart(e.target.value)} />
            <Button icon={CalendarRange} onClick={simulate} disabled={!!busy || !project.tasks.length}>{busy === 'sim' ? 'Hesaplanıyor…' : 'Simüle et'}</Button>
          </div>
        )}>
        {!project.tasks.length ? (
          <EmptyState icon={CalendarRange} title="İş adımı yok" description="Simülasyon için önce Beyin AI Planlama sekmesinde planı onaylayın." />
        ) : !sim ? (
          <p className="pj-hint">Henüz simülasyon yapılmadı. Başlangıç tarihini seçip "Simüle et"e basın.</p>
        ) : (
          <div className="pj-steps">
            <div className="pj-stats">
              <div className="pj-stat"><span>Başlangıç</span><strong>{fmtDay(sim.start_date)}</strong></div>
              <div className="pj-stat"><span>Tahmini bitiş</span><strong>{fmtDay(sim.end_date)}</strong></div>
              <div className="pj-stat"><span>Süre</span><strong>{sim.workdays} iş günü</strong></div>
              <div className="pj-stat"><span>Tahmini kredi</span><strong>{fmtNum(sim.estimated_credits)}</strong></div>
            </div>
            {sim.risks.length === 0 ? <div className="pj-note info">Belirgin bir risk görülmedi.</div>
              : sim.risks.map((r) => <div key={r.text} className={`pj-note ${r.level}`}>{r.text}</div>)}
            <div className="pj-gantt" aria-label="Zaman çizelgesi">
              {sim.timeline.map((t) => {
                const left = ((new Date(t.start).getTime() - range.a) / range.span) * 100;
                const width = Math.max(((new Date(t.end).getTime() + 86400000 - new Date(t.start).getTime()) / range.span) * 100, 2);
                return (
                  <div className="pj-gantt-row" key={t.task_id}>
                    <span title={t.title}>{t.title}<br /><small className="pj-hint">{t.assignee || 'Atanmadı'}</small></span>
                    <div className="pj-gantt-track">
                      <div className="pj-gantt-bar" style={{ left: `${left}%`, width: `${width}%` }} title={`${fmtDay(t.start)} – ${fmtDay(t.end)} · ${fmtNum(t.credits)} kredi`}>
                        {new Date(t.start).toLocaleDateString('tr-TR', { day: '2-digit', month: 'short' })}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
            {editable && (sim.start_date !== project.start_date || sim.end_date !== project.end_date) && (
              <div className="pj-actions">
                <Button variant="secondary" onClick={applyDates} disabled={!!busy}>Bu tarihleri projeye uygula</Button>
                <span className="pj-hint">Hedef: {fmtDay(project.start_date)} – {fmtDay(project.end_date)}</span>
              </div>
            )}
          </div>
        )}
      </Card>
    </div>
  );
}

/** Hazırlık & Bildirim (ADIM 6.5): hazırlık kontrol listesi, hazır yapma/başlatma ve Telegram bağlantısı. */
export function ReadinessTab({ project, onAction, busy }) {
  const tasks = project.tasks;
  const checks = [
    [!!(project.requirements || '').trim(), 'İsterler yazıldı'],
    [!!project.planning_approved_at && tasks.length > 0, `Plan onaylandı (${tasks.length} iş adımı)`],
    [tasks.length > 0 && tasks.every((t) => t.assignee_actor_id), 'Her iş adımına personel atandı'],
    [!!project.simulation, 'Simülasyon yapıldı'],
    [!!(project.start_date && project.end_date), `Tarihler belirlendi (${fmtDay(project.start_date)} – ${fmtDay(project.end_date)})`],
  ];
  const required = [checks[0], checks[1], checks[2], checks[4]];
  return (
    <div className="pj-split">
      <Card title="Hazırlık kontrol listesi" subtitle="Başlamaya hazır olan projenin başlangıç günü gelince size e-posta ve Telegram bildirimi gönderilir.">
        <ul className="pj-check">
          {checks.map(([ok, label]) => (
            <li key={label}>{ok ? <CheckCircle2 size={16} className="ok" /> : <Circle size={16} className="no" />}{label}</li>
          ))}
        </ul>
        {project.can_manage && (
          <div className="pj-actions" style={{ marginTop: 14 }}>
            {project.status === 'PLANNING' && (
              <Button icon={CheckCircle2} onClick={() => onAction('mark_ready')} disabled={busy || !required.every(([ok]) => ok)}>Başlamaya hazır yap</Button>
            )}
            {project.status === 'READY' && (
              <>
                <Button variant="success" icon={Play} onClick={() => onAction('start')} disabled={busy}>Projeyi şimdi başlat</Button>
                <Button variant="secondary" onClick={() => onAction('reopen_planning')} disabled={busy}>Planlamaya geri al</Button>
              </>
            )}
          </div>
        )}
        {project.status === 'READY' && (
          <p className="pj-note info" style={{ marginTop: 12 }}>
            Proje {fmtDay(project.start_date)} tarihinde başlamaya hazır. O gün hâlâ başlatılmamışsa proje yöneticisine hatırlatma gönderilir.
          </p>
        )}
      </Card>
      <div className="pj-steps">
        <TelegramCard />
        <NotificationPrefsCard />
      </div>
    </div>
  );
}

function NotificationPrefsCard() {
  const [prefs, setPrefs] = useState(null);
  useEffect(() => { api.getNotificationPrefs().then(setPrefs).catch(() => setPrefs(null)); }, []);
  const toggle = async (key) => {
    const next = { ...prefs, [key]: !prefs[key] };
    try { setPrefs(await api.setNotificationPrefs(next)); toast.success('Bildirim tercihiniz kaydedildi.'); } catch (e) { toast.error(e.message); }
  };
  if (!prefs) return null;
  return (
    <Card title="Bildirim tercihlerim" subtitle="Onay istekleri, revizyonlar, duran adımlar ve proje bitişi bu kanallardan gelir.">
      <ul className="pj-check">
        {[['email', 'E-posta (onay isteklerinde tek tıkla karar bağlantısı)'], ['telegram', 'Telegram (Onayla / Revizyon iste butonları)']].map(([k, l]) => (
          <li key={k}><label style={{ display: 'flex', gap: 8, alignItems: 'center', cursor: 'pointer' }}>
            <input type="checkbox" checked={prefs[k]} onChange={() => toggle(k)} />{l}
          </label></li>
        ))}
      </ul>
    </Card>
  );
}

function TelegramCard() {
  const [st, setSt] = useState(null);
  const [link, setLink] = useState(null);
  const load = () => api.getTelegramStatus().then(setSt).catch(() => setSt({ enabled: false }));
  useEffect(() => { load(); }, []);

  const connect = async () => {
    try { setLink(await api.linkTelegram()); } catch (e) { toast.error(e.message); }
  };
  const disconnect = async () => {
    if (!(await confirmDialog({ message: 'Telegram bildirimleri kapatılsın mı?' }))) return;
    try { await api.unlinkTelegram(); setLink(null); load(); } catch (e) { toast.error(e.message); }
  };

  return (
    <Card title="Telegram bildirimleri" subtitle="Proje başlangıç hatırlatmalarını Telegram'dan da alın." actions={<BellRing size={18} />}>
      {!st ? <p className="pj-hint">Yükleniyor…</p> : !st.enabled ? (
        <p className="pj-note medium">Telegram bildirimleri bu kurulumda henüz etkin değil. Bildirimler e-posta ile gönderilir.</p>
      ) : st.linked ? (
        <div className="pj-steps">
          <p className="pj-note info">Telegram hesabınız bağlı{st.linked_at ? ` (${fmtDay(st.linked_at)})` : ''}.</p>
          <div className="pj-actions"><Button variant="secondary" onClick={disconnect}>Bağlantıyı kaldır</Button></div>
        </div>
      ) : link ? (
        <div className="pj-steps">
          <p className="pj-hint">Aşağıdaki bağlantıyı açın veya botta <strong>/start {link.code}</strong> yazın. Bağlandıktan sonra durumu yenileyin.</p>
          <div className="pj-actions">
            {link.deep_link && <a className="ui-btn ui-btn-primary ui-btn-md" href={link.deep_link} target="_blank" rel="noreferrer"><Send size={16} />Telegram'da aç</a>}
            <Button variant="secondary" onClick={load}>Durumu yenile</Button>
          </div>
        </div>
      ) : (
        <div className="pj-actions"><Button icon={Send} onClick={connect}>Telegram hesabımı bağla</Button></div>
      )}
    </Card>
  );
}

/** Kapanış: projeyi tamamlama/iptal ve onaylı proje eklerini Kurum Hafızasına aktarma. */
export function CloseTab({ project, currentUser, onAction, busy }) {
  const [cost, setCost] = useState(null);
  useEffect(() => {
    if (project.can_manage) api.getProjectCosts(project.id).then(setCost).catch(() => setCost(null));
  }, [project.id, project.can_manage]);
  const [summary, setSummary] = useState(project.close_summary || '');
  const [docs, setDocs] = useState(null);
  const [picked, setPicked] = useState([]);
  const canPromote = (currentUser?.permissions || []).includes('memory:promote') || ['COMPANY_ADMIN', 'PROJECT_MANAGER'].includes(currentUser?.role);
  const open = ['ACTIVE', 'PAUSED'].includes(project.status);
  const closed = ['COMPLETED', 'CANCELLED'].includes(project.status);

  const loadDocs = useCallback(() => api.getProjectDocuments(project.id).then((d) => setDocs(d.filter((x) => x.status === 'APPROVED'))).catch(() => setDocs([])), [project.id]);
  useEffect(() => { loadDocs(); }, [loadDocs]);

  const promote = async () => {
    try {
      const r = await api.promoteProjectKnowledge(project.id, picked);
      toast.success(`${r.promoted.length} ek Kurum Hafızasına aktarıldı; artık şirketin tüm AI personeli yararlanır.`);
      setPicked([]);
      loadDocs();
    } catch (e) { toast.error(e.message); }
  };

  return (
    <div className="pj-split">
      {['ACTIVE', 'PAUSED', 'COMPLETED'].includes(project.status) && <ProjectTransfers project={project} />}
      <Card title="Projeyi kapat" subtitle={closed ? `Kapanış: ${fmtDay(project.closed_at)}` : 'Proje tamamlandığında ya da vazgeçildiğinde kapatın.'}>
        <div className="pj-field">
          <label htmlFor="pj-close">Kapanış özeti</label>
          <textarea id="pj-close" className="ui-input" rows={5} value={summary} disabled={closed || !project.can_manage}
            onChange={(e) => setSummary(e.target.value)} placeholder="Ne teslim edildi, öğrenilenler, açık kalan konular…" />
        </div>
        {project.can_manage && !closed && (
          <div className="pj-actions" style={{ marginTop: 10 }}>
            {open && <Button variant="success" icon={CheckCircle2} onClick={() => onAction('complete', summary)} disabled={busy}>Projeyi tamamla</Button>}
            <Button variant="danger" onClick={() => onAction('cancel', summary)} disabled={busy}>İptal et</Button>
          </div>
        )}
      </Card>
      {cost && (
        <Card title="Maliyet özeti" subtitle="TL, KDV hariç. Ayrıntılar Maliyet sekmesinde."
          actions={<Button size="sm" variant="secondary" onClick={() => api.downloadProjectCostReport(project.id).catch((e) => toast.error(e.message))}>Excel raporu</Button>}>
          <div className="pj-stats">
            <div className="pj-stat"><span>Gerçekleşen</span><strong>{fmtTl(cost.totals.actual)}</strong></div>
            <div className="pj-stat"><span>Bütçe</span><strong>{fmtTl(cost.budget.amount)}</strong></div>
            <div className="pj-stat"><span>Fark</span><strong>{fmtTl(cost.totals.budget_variance)}</strong></div>
            <div className="pj-stat"><span>Kredi</span><strong>{Number(cost.totals.credits || 0).toLocaleString('tr-TR')}</strong></div>
          </div>
          <p className="pj-hint" style={{ marginTop: 8 }}>Personel {fmtTl(cost.totals.labor)} · Token (LLM) {fmtTl(cost.totals.token)} · Diğer {fmtTl(cost.totals.other)}
            {cost.totals.unpriced_calls ? ` · ${cost.totals.unpriced_calls} çağrının TL fiyatı tanımsız` : ''}</p>
        </Card>
      )}
      <Card title="Kurum Hafızasına aktar" subtitle="Seçilen onaylı proje ekleri şirketin tüm AI personelinin bilgisine eklenir." actions={<Library size={18} />}>
        {!docs ? <p className="pj-hint">Yükleniyor…</p> : docs.length === 0 ? (
          <p className="pj-hint">Aktarılabilecek onaylı proje eki yok.</p>
        ) : (
          <>
            <ul className="pj-list">
              {docs.map((d) => (
                <li key={d.id}>
                  <span>{d.original_name}</span>
                  {d.promoted_at ? <Badge tone="success">Aktarıldı</Badge> : canPromote && (
                    <input type="checkbox" aria-label={`${d.original_name} seç`} checked={picked.includes(d.id)}
                      onChange={(e) => setPicked((p) => (e.target.checked ? [...p, d.id] : p.filter((x) => x !== d.id)))} />
                  )}
                </li>
              ))}
            </ul>
            {canPromote ? (
              <Button style={{ marginTop: 10 }} onClick={promote} disabled={!picked.length}>Seçilenleri Kurum Hafızasına aktar ({picked.length})</Button>
            ) : <p className="pj-hint" style={{ marginTop: 10 }}>Aktarma için kurum hafızası onay yetkisi gerekir.</p>}
          </>
        )}
      </Card>
    </div>
  );
}
