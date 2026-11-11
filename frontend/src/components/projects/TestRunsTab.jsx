import React, { useCallback, useEffect, useState } from 'react';
import { FlaskConical, Play } from 'lucide-react';
import { api } from '../../api';
import { Badge, Button, Card, EmptyState } from '../../ui/components';
import { toast } from '../../ui/feedback';

const TONE = { RUNNING: 'info', PASSED: 'success', FAILED: 'danger', NO_TESTS: 'warning', ERROR: 'danger' };
const SUB = { PASSED: 'Geçti', FAILED: 'Kaldı', NO_TESTS: 'Test yok', TIMEOUT: 'Süre doldu', INSTALL_FAILED: 'Kurulum başarısız' };
const SMOKE = { PASSED: ['success', 'Geçti'], FAILED: ['danger', 'Kaldı'], ERROR: ['danger', 'Çalıştırılamadı'], NO_SMOKE: ['warning', 'Yapılmadı'] };
const fmt = (d) => (d ? new Date(d).toLocaleString('tr-TR', { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' }) : '');
const mono = { fontFamily: 'var(--font-mono)', fontSize: '0.75rem' };
const logStyle = { ...mono, whiteSpace: 'pre-wrap', background: 'var(--bg-dark)', border: '1px solid var(--border-subtle)', borderRadius: 8,
  padding: 10, maxHeight: 320, overflow: 'auto', margin: '6px 0 0' };

/** Testler (ADIM 16.2): AI Test Uzmanı'nın ve proje yöneticisinin Kod Çalıştırma Ortamı koşuları. */
export default function TestRunsTab({ project }) {
  const [data, setData] = useState(null);
  const [refs, setRefs] = useState(['main']);
  const [ref, setRef] = useState('main');
  const [open, setOpen] = useState(null);
  const [busy, setBusy] = useState(false);
  const closed = ['COMPLETED', 'CANCELLED'].includes(project.status);

  const load = useCallback(() => api.getTestRuns(project.id).then(setData).catch((e) => toast.error(e.message)), [project.id]);
  useEffect(() => { load(); }, [load]);
  useEffect(() => {
    api.getProjectRepository(project.id)
      .then((r) => setRefs(['main', ...new Set((r.steps || []).filter((s) => s.branch && s.state !== 'MERGED').map((s) => s.branch))]))
      .catch(() => {});
  }, [project.id]);
  const running = (data?.runs || []).some((r) => r.status === 'RUNNING');
  useEffect(() => {
    if (!running) return undefined;
    const t = setInterval(load, 5000);
    return () => clearInterval(t);
  }, [running, load]);

  const run = async () => {
    setBusy(true);
    try {
      await api.startTestRun(project.id, ref);
      toast.success('Test koşusu başladı; sonuç birkaç dakika içinde burada görünür.');
      load();
    } catch (e) { toast.error(e.message); } finally { setBusy(false); }
  };

  if (!data) return <p className="pj-hint">Yükleniyor…</p>;
  return (
    <div className="pj-steps">
      <Card title="Kod Çalıştırma Ortamı" actions={<FlaskConical size={18} />}
        subtitle="AI personelin yazdığı kod RECOrion içinde, her koşuda yeniden açılan yalıtılmış bir kapta kurulur ve testleri çalıştırılır. AI Test Uzmanı adımını teslim edince koşu kendiliğinden yapılır.">
        {!data.enabled ? (
          <p className="pj-hint">Testler için projenin kod deposu açık olmalı (Kod Deposu sekmesi) ve kod çalıştırma ortamı kurulu olmalı.</p>
        ) : data.can_run && !closed ? (
          <div className="pj-actions" style={{ alignItems: 'center' }}>
            <label htmlFor="tr-ref" className="pj-hint">Dal</label>
            <select id="tr-ref" className="ui-input" value={ref} onChange={(e) => setRef(e.target.value)} style={{ maxWidth: 320 }}>
              {refs.map((r) => <option key={r} value={r}>{r}</option>)}
            </select>
            <Button icon={Play} disabled={busy || running} onClick={run}>{running ? 'Koşu sürüyor…' : 'Testleri çalıştır'}</Button>
          </div>
        ) : (
          <p className="pj-hint">Testleri elle proje yöneticisi başlatır; AI Test Uzmanı'nın koşuları kendiliğinden yapılır.</p>
        )}
      </Card>

      {data.runs.length === 0 ? (
        <EmptyState icon={FlaskConical} title="Henüz test koşusu yok" description="AI Test Uzmanı test adımını teslim ettiğinde ya da testleri elle çalıştırdığınızda sonuçlar burada görünür." />
      ) : data.runs.map((r) => (
        <Card key={r.id} title={<span style={mono}>{r.ref}{r.commit_sha ? ` · ${r.commit_sha.slice(0, 10)}` : ''}</span>}
          subtitle={`${fmt(r.created_at)}${r.task_id ? ' · AI Test Uzmanı adımı' : ' · elle başlatıldı'}`}
          actions={<Badge tone={TONE[r.status] || 'neutral'}>{r.status_label}</Badge>}>
          {r.status !== 'RUNNING' && (
            <p className="pj-hint">{r.passed} geçti · {r.failed} kaldı · {r.skipped} atlandı{r.result?.seconds ? ` · ${r.result.seconds} sn` : ''}</p>
          )}
          {r.error && <p className="ui-text-danger" style={{ fontSize: '0.8rem' }}>{r.error}</p>}
          {r.result?.note && <p className="pj-hint">{r.result.note}</p>}
          {r.result?.smoke && (
            <div className="pj-actions" style={{ alignItems: 'center' }}>
              <span className="pj-hint">Duman testi (uygulamayı açıp deneme)</span>
              <Badge tone={(SMOKE[r.result.smoke.status] || ['neutral'])[0]}>{(SMOKE[r.result.smoke.status] || [null, r.result.smoke.status])[1]}</Badge>
              {r.result.smoke.readme && !r.result.smoke.readme.ok && <Badge tone="warning">README eksik</Badge>}
            </div>
          )}
          {((r.result?.projects || []).length > 0 || r.result?.smoke) && (
            <Button variant="ghost" size="sm" onClick={() => setOpen(open === r.id ? null : r.id)}>{open === r.id ? 'Ayrıntıyı gizle' : 'Ayrıntı'}</Button>
          )}
          {open === r.id && (r.result?.projects || []).map((p) => (
            <div key={`${p.dir}-${p.kind}`} style={{ marginTop: 10 }}>
              <div className="pj-actions" style={{ alignItems: 'center' }}>
                <span style={mono}>{p.dir === '.' ? 'kök klasör' : p.dir} ({p.kind === 'script' ? 'recorion_test.sh' : p.kind})</span>
                <Badge tone={p.test?.status === 'PASSED' ? 'success' : p.test?.status === 'NO_TESTS' ? 'warning' : 'danger'}>{SUB[p.test?.status] || p.test?.status}</Badge>
                {p.test?.command && <small className="pj-hint">{p.test.command} · {p.test.seconds} sn</small>}
              </div>
              {(p.test?.failures || []).length > 0 && (
                <ul className="pj-list">
                  {p.test.failures.map((f) => (
                    <li key={f.name}><span style={mono}>✗ {f.name}</span><small className="pj-hint">{f.message}</small></li>
                  ))}
                </ul>
              )}
              {p.install && !p.install.ok && <><p className="pj-hint">Bağımlılık kurulumu başarısız:</p><pre style={logStyle}>{p.install.log}</pre></>}
              {p.test?.log && <details><summary className="pj-hint">Test çıktısı</summary><pre style={logStyle}>{p.test.log}</pre></details>}
            </div>
          ))}
          {open === r.id && r.result?.smoke && <SmokeDetail smoke={r.result.smoke} />}
        </Card>
      ))}
    </div>
  );
}

/** Duman testi ayrıntısı (#734): hizmetler açıldı mı, denetimler, README. */
function SmokeDetail({ smoke }) {
  return (
    <div style={{ marginTop: 10 }}>
      <p className="pj-hint" style={{ margin: 0 }}>Duman testi{smoke.seconds ? ` · ${smoke.seconds} sn` : ''}</p>
      {smoke.note && <p className="pj-hint">{smoke.note}</p>}
      <ul className="pj-list">
        {(smoke.services || []).map((s) => (
          <li key={s.name}>
            <span style={mono}>{s.ready ? '✓' : '✗'} {s.name} · {s.dir} · port {s.port}</span>
            <small className="pj-hint">{s.ready ? `açıldı (HTTP ${s.ready_status})` : (s.error || 'açılmadı')}</small>
            {!s.ready && s.log && <pre style={logStyle}>{s.log}</pre>}
          </li>
        ))}
        {(smoke.checks || []).map((c, i) => (
          <li key={`${c.name}-${i}`}>
            <span style={mono}>{c.ok === true ? '✓' : c.ok === false ? '✗' : '–'} {c.name} ({c.type === 'browser' ? 'arayüz' : 'API'})</span>
            <small className="pj-hint">{c.detail}</small>
          </li>
        ))}
        {smoke.readme && (
          <li><span style={mono}>{smoke.readme.ok ? '✓' : '✗'} README</span>
            <small className="pj-hint">{smoke.readme.file ? `${smoke.readme.file} · ${smoke.readme.chars} karakter` : 'yok'}{smoke.readme.ok ? '' : ' — kurulum talimatı eksik/yetersiz'}</small></li>
        )}
      </ul>
    </div>
  );
}
