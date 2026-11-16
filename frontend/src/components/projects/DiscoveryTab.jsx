import React, { useCallback, useEffect, useState } from 'react';
import { Brain, CheckCircle2, FileText, Send, SkipForward } from 'lucide-react';
import { api } from '../../api';
import { Badge, Button, Card, EmptyState } from '../../ui/components';
import { promptDialog, toast } from '../../ui/feedback';
import { isPlanning } from './projectMeta';

const STATUS = { NOT_STARTED: ['Başlamadı', 'neutral'], IN_PROGRESS: ['Görüşme sürüyor', 'warning'], APPROVED: ['Onaylandı', 'success'], SKIPPED: ['Atlandı', 'neutral'] };
const LIST_KEYS = [
  ['success_criteria', 'Başarı ölçütleri'], ['stakeholders', 'Paydaşlar'], ['users_roles', 'Kullanıcılar ve roller'],
  ['scope_in', 'Kapsam içi'], ['scope_out', 'Kapsam dışı'], ['constraints', 'Kısıtlar'], ['workflows', 'Kullanıcı / iş akışları'],
  ['risks', 'Riskler'], ['assumptions', 'Varsayımlar'], ['open_questions', 'Açık sorular'],
];

/**
 * İSTEK #749: Beyin AI keşif görüşmesi. Beyin AI soru sorar, yanıtlarla Proje Tanım Belgesini ve olgunluk puanını günceller.
 * Belge onaylanınca (ya da keşif gerekçeyle atlanınca) Beyin AI plan önerebilir.
 */
export default function DiscoveryTab({ project, onChanged, onGoPlan }) {
  const [d, setD] = useState(null);
  const [answers, setAnswers] = useState({});
  const [note, setNote] = useState('');
  const [busy, setBusy] = useState('');
  const editable = project.can_manage && (project.status === 'DRAFT' || isPlanning(project));

  const load = useCallback(() => api.getProjectDiscovery(project.id).then(setD).catch((e) => toast.error(e.message)), [project.id]);
  useEffect(() => { load(); }, [load]);

  const run = async (label, fn) => {
    setBusy(label);
    try { return await fn(); } catch (e) { toast.error(e.message); return null; } finally { setBusy(''); }
  };

  const round = () => run('round', async () => {
    toast.info('Beyin AI yanıtlarınızı işliyor; bu bir iki dakika sürebilir.');
    const r = await api.discoveryRound(project.id, Object.entries(answers).map(([id, answer]) => ({ id, answer })), note || null);
    setD(r); setAnswers({}); setNote('');
    toast.success(`Tanım belgesi güncellendi: olgunluk %${r.maturity.score}.`);
    onChanged();
  });

  const approve = () => run('approve', async () => {
    let reason = null;
    if (d.maturity.score < d.threshold) {
      reason = await promptDialog({ title: 'Eksiklere rağmen onayla', confirmText: 'Onayla', required: true,
        message: `Olgunluk %${d.maturity.score}, eşik %${d.threshold}. Eksikler planı zayıflatabilir. Onay gerekçesini yazın (kayda geçer).` });
      if (!reason) return;
    }
    setD(await api.discoveryApprove(project.id, reason));
    toast.success('Proje Tanım Belgesi onaylandı; Beyin AI artık bu belgeye göre plan önerebilir.');
    onChanged();
  });

  const skip = () => run('skip', async () => {
    const reason = await promptDialog({ title: 'Keşfi atla', confirmText: 'Atla', required: true,
      message: 'Keşif atlanırsa plan yalnız isterlerden kurulur. Gerekçeyi yazın (kayda geçer).' });
    if (!reason) return;
    setD(await api.discoverySkip(project.id, reason));
    toast.success('Keşif atlandı.');
    onChanged();
  });

  if (!d) return <Card title="Keşif & Tanım"><p className="pj-hint">Yükleniyor…</p></Card>;
  const [stLabel, stTone] = STATUS[d.status] || STATUS.NOT_STARTED;
  const score = d.maturity?.score || 0;
  const c = d.charter || {};
  const hasCharter = Object.keys(c).length > 0;
  const done = ['APPROVED', 'SKIPPED'].includes(d.status);
  const noReq = !(project.requirements || '').trim();

  return (
    <div className="pj-split">
      <div className="pj-steps">
        <Card title="Beyin AI keşif görüşmesi" subtitle="Plan yapılmadan önce işin ne olduğu netleşir; Beyin AI sizin düşünmediğiniz konuları sorar."
          actions={<Badge tone={stTone}>{stLabel}</Badge>}>
          {noReq && <p className="pj-note medium">Önce Bilgiler & İsterler sekmesinde projenin isterlerini (kısa brif) yazın.</p>}
          {d.status === 'SKIPPED' && <p className="pj-note info">Keşif atlandı: {d.skipped_reason}</p>}
          {d.status === 'APPROVED' && (
            <p className="pj-note info">Tanım belgesi onaylandı{d.approve_reason ? ` (gerekçe: ${d.approve_reason})` : ''}. Plan bu belgeye göre kurulur.</p>
          )}
          {(d.reminders || []).length > 0 && !done && (
            <div className="pj-steps">{d.reminders.map((r) => <div key={r} className="pj-note medium">{r}</div>)}</div>
          )}
          {(d.pending || []).length > 0 && !done ? (
            <div className="pj-steps" style={{ marginTop: 10 }}>
              {d.pending.map((q) => (
                <div className="pj-field" key={q.id}>
                  <label htmlFor={`dq-${q.id}`}><Badge tone="info">{q.topic || 'Soru'}</Badge> {q.text}</label>
                  {q.why && <small className="pj-hint">Neden önemli: {q.why}</small>}
                  <textarea id={`dq-${q.id}`} className="ui-input" rows={2} disabled={!editable} value={answers[q.id] || ''}
                    onChange={(e) => setAnswers((a) => ({ ...a, [q.id]: e.target.value }))} placeholder="Yanıtınız (boş bırakılan soru atlanır)" />
                </div>
              ))}
            </div>
          ) : d.status === 'NOT_STARTED' ? (
            <EmptyState icon={Brain} title="Keşfe başlayın" description="Beyin AI isterlerinizi okur, kapsam, paydaş, teslimat ve kabul gibi konularda ilk sorularını sorar." />
          ) : !done && <p className="pj-hint">Beyin AI'nın açık sorusu kalmadı; tanım belgesini inceleyip onaylayabilirsiniz.</p>}
          {editable && !done && (
            <div className="pj-field" style={{ marginTop: 10 }}>
              <label htmlFor="dq-note">Ek not (isteğe bağlı)</label>
              <textarea id="dq-note" className="ui-input" rows={2} value={note} onChange={(e) => setNote(e.target.value)}
                placeholder="Örn. ödeme entegrasyonu ikinci fazda, mobil uygulama kapsam dışı…" />
              <div className="pj-actions">
                <Button icon={d.status === 'NOT_STARTED' ? Brain : Send} onClick={round} disabled={!!busy || noReq}>
                  {busy === 'round' ? 'Beyin AI düşünüyor…' : d.status === 'NOT_STARTED' ? 'Keşfe başla' : 'Yanıtları gönder'}
                </Button>
                {hasCharter && <Button variant="success" icon={CheckCircle2} onClick={approve} disabled={!!busy}>Tanım belgesini onayla</Button>}
                <Button variant="ghost" icon={SkipForward} onClick={skip} disabled={!!busy}>Keşfi atla</Button>
              </div>
            </div>
          )}
          {done && onGoPlan && isPlanning(project) && (
            <div className="pj-actions" style={{ marginTop: 10 }}><Button icon={Brain} onClick={onGoPlan}>Beyin AI Planlamaya geç</Button></div>
          )}
        </Card>
        {(d.rounds || []).length > 0 && (
          <Card title="Görüşme geçmişi" subtitle={`${d.rounds.length} tur`}>
            <div className="pj-steps">
              {d.rounds.map((r, i) => (
                <details key={r.at}>
                  <summary>Tur {i + 1} · olgunluk %{r.score}{r.model_code ? ` · ${r.model_code}` : ''}</summary>
                  <ul className="pj-list">
                    {(r.qa || []).map((x) => <li key={x.id}><span><strong>{x.question}</strong><br />{x.answer || <em>yanıtlanmadı</em>}</span></li>)}
                    {r.note && <li><span><strong>Not:</strong> {r.note}</span></li>}
                  </ul>
                </details>
              ))}
            </div>
          </Card>
        )}
      </div>

      <div className="pj-steps">
        <Card title="Proje Tanım Belgesi" subtitle={`Olgunluk %${score} · onay eşiği %${d.threshold}`}>
          <div className="pj-meter" role="progressbar" aria-label="Olgunluk puanı" aria-valuenow={score} aria-valuemin={0} aria-valuemax={100}>
            <div className={`pj-meter-fill ${score >= d.threshold ? '' : 'warn'}`} style={{ width: `${score}%` }} />
          </div>
          {(d.maturity?.missing || []).length > 0 && (
            <div className="pj-steps" style={{ marginTop: 10 }}>{d.maturity.missing.map((m) => <div key={m} className="pj-note medium">Eksik: {m}</div>)}</div>
          )}
          {!hasCharter ? (
            <EmptyState icon={FileText} title="Belge henüz yok" description="İlk keşif turundan sonra Beyin AI belgeyi isterlerinizden ve yanıtlarınızdan oluşturur." />
          ) : (
            <div className="pj-steps" style={{ marginTop: 10 }}>
              {c.goal && <div><strong>Amaç</strong><p>{c.goal}</p></div>}
              {(c.deliverables || []).length > 0 && (
                <div><strong>Teslimatlar ve kabul</strong>
                  <ul className="pj-list">
                    {c.deliverables.map((x) => (
                      <li key={x.name}><span><strong>{x.name}</strong>{x.acceptance ? <><br />Kabul: {x.acceptance}</> : null}
                        {x.verification ? <><br /><small className="pj-hint">Doğrulama: {x.verification}</small></> : null}</span></li>
                    ))}
                  </ul>
                </div>
              )}
              {LIST_KEYS.filter(([k]) => (c[k] || []).length).map(([k, l]) => (
                <div key={k}><strong>{l}</strong><ul className="pj-list">{c[k].map((x) => <li key={x}><span>{x}</span></li>)}</ul></div>
              ))}
            </div>
          )}
        </Card>
      </div>
    </div>
  );
}
