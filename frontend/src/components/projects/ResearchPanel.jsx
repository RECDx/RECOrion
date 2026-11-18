import React, { useCallback, useEffect, useState } from 'react';
import { ExternalLink, Globe, Square, ThumbsDown, ThumbsUp } from 'lucide-react';
import { api } from '../../api';
import { Badge, Button, Card, Modal } from '../../ui/components';
import { confirmDialog, toast } from '../../ui/feedback';

const STATUS = { RUNNING: ['Sürüyor', 'warning'], DONE: ['Tamamlandı', 'success'], FAILED: ['Başarısız', 'danger'], CANCELLED: ['Durduruldu', 'neutral'] };
const STAGE = { PLANNING: 'Alt sorular çıkarılıyor', SEARCHING: 'Web\'de aranıyor', READING: 'Kaynaklar okunuyor', SYNTHESIZING: 'Kaynaklar karşılaştırılıyor' };
const fmt = (n) => Number(n || 0).toLocaleString('tr-TR', { maximumFractionDigits: 1 });

/**
 * İSTEK #750: Beyin AI web derin araştırması. Yalnız yöneticinin talebiyle ve tahmini / en fazla kredi onaylanınca başlar.
 * Beyin AI keşifte konu önerebilir (suggestions); kendiliğinden başlatmaz.
 */
export default function ResearchPanel({ project, suggestions = [], onDone }) {
  const [data, setData] = useState(null);
  const [asking, setAsking] = useState(null);  // { question, origin }
  const canRun = project.can_manage && !['COMPLETED', 'CANCELLED'].includes(project.status);

  const load = useCallback(() => api.getProjectResearch(project.id).then(setData).catch((e) => toast.error(e.message)), [project.id]);
  useEffect(() => { load(); }, [load]);
  const running = data?.items?.some((r) => r.status === 'RUNNING');
  useEffect(() => {
    if (!running) return undefined;
    const t = setInterval(async () => {
      const before = data.items.filter((r) => r.status === 'RUNNING').map((r) => r.id);
      const next = await api.getProjectResearch(project.id).catch(() => null);
      if (!next) return;
      setData(next);
      if (next.items.some((r) => before.includes(r.id) && r.status === 'DONE')) {
        toast.success('Web araştırması tamamlandı; Beyin AI sonraki keşif turunda ve planda bu bulguları kullanır.');
        onDone?.();
      }
    }, 5000);
    return () => clearInterval(t);
  }, [running, data, project.id, onDone]);

  const stop = async (r) => {
    if (!(await confirmDialog({ title: 'Araştırmayı durdur', confirmText: 'Durdur', message: 'Araştırma durdurulsun mu? O ana kadar harcanan kredi geri gelmez.' }))) return;
    try { await api.cancelProjectResearch(project.id, r.id); load(); } catch (e) { toast.error(e.message); }
  };

  // #753: yöneticinin tek tık değerlendirmesi Beyin AI'nin öğrenme kaydına girer (araştırma önerilerini iyileştirir)
  const rate = async (r, rating) => {
    try { await api.rateProjectResearch(project.id, r.id, rating); toast.success('Değerlendirmeniz kaydedildi; Beyin AI bundan öğrenir.'); load(); }
    catch (e) { toast.error(e.message); }
  };

  if (!data) return null;
  return (
    <Card title="Web araştırması" subtitle="Beyin AI web'de çok adımlı araştırma yapar; yalnız sizin onayınızla başlar ve kredi harcar."
      actions={canRun && data.enabled && <Button size="sm" icon={Globe} onClick={() => setAsking({ question: '', origin: 'MANAGER' })} disabled={running}>Web'de araştır</Button>}>
      {!data.enabled && <p className="pj-note info">Web araştırması şirketinizde kapalı. Şirket yöneticisi Kredi ve Kullanım ekranından açabilir.</p>}
      {canRun && data.enabled && suggestions.length > 0 && (
        <div className="pj-steps" style={{ marginBottom: 10 }}>
          <small className="pj-hint">Beyin AI şu konularda araştırma öneriyor (başlatmak için seçin):</small>
          <div className="pj-actions">
            {suggestions.map((s) => (
              <Button key={s} size="sm" variant="ghost" icon={Globe} disabled={running} onClick={() => setAsking({ question: s, origin: 'BRAIN_SUGGESTION' })}>{s}</Button>
            ))}
          </div>
        </div>
      )}
      {data.items.length === 0 ? <p className="pj-hint">Henüz araştırma yok. Örnek: "Diş kliniklerinde randevu ve hasta kaydı için KVKK'da nelere dikkat edilmeli?"</p> : (
        <div className="pj-steps">
          {data.items.map((r) => <ResearchItem key={r.id} r={r} canStop={canRun} onStop={() => stop(r)}
            canRate={project.can_manage} onRate={(rating) => rate(r, rating)} />)}
        </div>
      )}
      {asking && <StartModal project={project} initial={asking} onClose={() => setAsking(null)} onStarted={() => { setAsking(null); load(); }} />}
    </Card>
  );
}

const RATINGS = [['USEFUL', 'Faydalı', ThumbsUp], ['PARTIAL', 'Kısmen', null], ['USELESS', 'Faydasız', ThumbsDown]];

function ResearchItem({ r, canStop, onStop, canRate, onRate }) {
  const [label, tone] = STATUS[r.status] || STATUS.RUNNING;
  const res = r.result || {};
  const src = Object.fromEntries((res.sources || []).map((s) => [s.n, s]));
  return (
    <details className="pj-research" open={r.status === 'RUNNING'}>
      <summary>
        <Badge tone={tone}>{label}</Badge> <strong>{r.question}</strong>
        <small className="pj-hint"> · {fmt(r.spent_credits)} / en fazla {fmt(r.max_credits)} kredi{r.origin === 'BRAIN_SUGGESTION' ? ' · Beyin AI önerisi' : ''}</small>
      </summary>
      {r.status === 'RUNNING' && (
        <div className="pj-actions">
          <span className="pj-hint">{STAGE[r.stage] || 'Hazırlanıyor'}{res.progress ? ` (${res.progress})` : ''}…</span>
          {canStop && <Button size="sm" variant="ghost" icon={Square} onClick={onStop}>Durdur</Button>}
        </div>
      )}
      {r.error && <p className="pj-note medium">{r.error}</p>}
      {r.status === 'DONE' && (
        <div className="pj-steps">
          {res.summary && <p>{res.summary}</p>}
          {res.skipped_subqueries > 0 && <p className="pj-note medium">Kredi üst sınırı nedeniyle {res.skipped_subqueries} alt soru atlandı.</p>}
          {(res.findings || []).length > 0 && (
            <div><strong>Bulgular</strong>
              <ul className="pj-list">
                {res.findings.map((f, i) => (
                  <li key={i}><span>{f.text} {f.verified ? f.sources.map((n) => (
                    <a key={n} href={src[n]?.url} target="_blank" rel="noopener noreferrer" title={src[n]?.title}>[{n}]</a>
                  )) : <Badge tone="warning">doğrulanmadı</Badge>}</span></li>
                ))}
              </ul>
            </div>
          )}
          {(res.contradictions || []).length > 0 && (
            <div><strong>Çelişkiler ve belirsizlikler</strong><ul className="pj-list">{res.contradictions.map((c) => <li key={c}><span>{c}</span></li>)}</ul></div>
          )}
          {(res.implications || []).length > 0 && (
            <div><strong>Projeye etkisi</strong><ul className="pj-list">{res.implications.map((c) => <li key={c}><span>{c}</span></li>)}</ul></div>
          )}
          {(res.sources || []).length > 0 && (
            <div><strong>Kaynaklar</strong>
              <ol className="pj-sources">
                {res.sources.map((s) => (
                  <li key={s.n} value={s.n}><a href={s.url} target="_blank" rel="noopener noreferrer">{s.title} <ExternalLink size={12} /></a></li>
                ))}
              </ol>
            </div>
          )}
          {canRate && (
            <div className="pj-actions" role="group" aria-label="Araştırma faydalı oldu mu?">
              <small className="pj-hint">Bu araştırma işinize yaradı mı?</small>
              {RATINGS.map(([code, text, icon]) => (
                <Button key={code} size="sm" variant={r.rating === code ? 'primary' : 'ghost'} icon={icon || undefined}
                  aria-pressed={r.rating === code} onClick={() => onRate(code)}>{text}</Button>
              ))}
            </div>
          )}
        </div>
      )}
    </details>
  );
}

function StartModal({ project, initial, onClose, onStarted }) {
  const [question, setQuestion] = useState(initial.question);
  const [depth, setDepth] = useState('STANDARD');
  const [est, setEst] = useState(null);
  const [max, setMax] = useState('');
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    let live = true;
    setEst(null);
    api.estimateProjectResearch(project.id, depth).then((e) => { if (live) { setEst(e); setMax(String(e.max_credits)); } }).catch((e) => toast.error(e.message));
    return () => { live = false; };
  }, [project.id, depth]);

  const start = async () => {
    setBusy(true);
    try {
      await api.startProjectResearch(project.id, { question, depth, max_credits: Number(max) || null, origin: initial.origin });
      toast.success('Web araştırması başladı; birkaç dakika sürebilir. Bu ekrandan izleyebilirsiniz.');
      onStarted();
    } catch (e) { toast.error(e.message); } finally { setBusy(false); }
  };

  return (
    <Modal open title="Web araştırması" onClose={onClose}
      footer={<>
        <Button variant="ghost" onClick={onClose}>Vazgeç</Button>
        <Button icon={Globe} onClick={start} disabled={busy || !est || question.trim().length < 8 || !(Number(max) > 0)}>
          {busy ? 'Başlatılıyor…' : 'Onayla ve başlat'}
        </Button>
      </>}>
      <div className="pj-form">
        <div className="pj-field full">
          <label htmlFor="wr-q">Araştırma sorusu</label>
          <textarea id="wr-q" className="ui-input" rows={3} value={question} onChange={(e) => setQuestion(e.target.value)}
            placeholder="Örn. Tur rezervasyon sitelerinde iptal ve iade süreçleri nasıl işliyor, mevzuat ne diyor?" />
          <small className="pj-hint">Soruda kişi veya müşteri bilgisi yazmayın; kişisel veriler maskelenir ve arama sorgularına gitmez.</small>
        </div>
        <div className="pj-field full">
          <label>Derinlik</label>
          <div className="ui-segmented" role="tablist" aria-label="Derinlik">
            {[['QUICK', 'Hızlı'], ['STANDARD', 'Standart'], ['DEEP', 'Derin']].map(([k, l]) => (
              <button key={k} type="button" className={`ui-segmented-item ${depth === k ? 'active' : ''}`} onClick={() => setDepth(k)}>{l}</button>
            ))}
          </div>
        </div>
        {est ? (
          <>
            <p className="pj-note info full">
              {est.subqueries} alt soru, en fazla {est.pages} kaynak sayfa. Tahmini maliyet <strong>~{fmt(est.estimated_credits)} kredi</strong>;
              kalan krediniz {fmt(est.balance)}. Harcama aşağıdaki üst sınırı aşmaz; sınıra gelinirse kalan alt sorular atlanır.
            </p>
            <div className="pj-field">
              <label htmlFor="wr-max">En fazla kredi</label>
              <input id="wr-max" className="ui-input" type="number" min={1} value={max} onChange={(e) => setMax(e.target.value)} />
            </div>
          </>
        ) : <p className="pj-hint full">Tahmini maliyet hesaplanıyor…</p>}
      </div>
    </Modal>
  );
}
