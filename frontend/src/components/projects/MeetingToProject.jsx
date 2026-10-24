import React, { useEffect, useRef, useState } from 'react';
import { Mic, Square, Upload } from 'lucide-react';
import { api } from '../../api';
import { Badge, Button, Modal } from '../../ui/components';
import { toast } from '../../ui/feedback';

const PII = { TCKN: 'T.C. kimlik no', IBAN: 'IBAN', CARD: 'kart no', EMAIL: 'e-posta', PHONE: 'telefon' };
const mmss = (s) => `${String(Math.floor(s / 60)).padStart(2, '0')}:${String(Math.floor(s % 60)).padStart(2, '0')}`;

/** Toplantı kaydından proje taslağı (ADIM 11.3): dosya yükle veya tarayıcıda kaydet → yazıya → KVKK maskeleme → Beyin AI taslağı → proje. */
export default function MeetingToProject({ tenant, onClose, onCreated }) {
  const [mode, setMode] = useState('UPLOAD');
  const [title, setTitle] = useState('');
  const [file, setFile] = useState(null);
  const [rec, setRec] = useState(null);
  const [busy, setBusy] = useState(false);
  const [recording, setRecording] = useState(false);
  const [elapsed, setElapsed] = useState(0);
  const [form, setForm] = useState(null);
  const recorder = useRef(null);
  const timer = useRef(null);

  // İşlenen kaydın durumunu izle (arka planda yazıya çevirme ve taslak)
  useEffect(() => {
    if (!rec || rec.status !== 'PROCESSING') return undefined;
    const t = setInterval(async () => {
      try {
        const r = await api.getMeeting(tenant.id, rec.id);
        setRec(r);
        if (r.status === 'READY') setForm({ name: r.draft.name, kind: r.draft.kind, description: r.draft.description, requirements: r.draft.requirements, include_steps: true });
      } catch (e) { toast.error(e.message); }
    }, 2500);
    return () => clearInterval(t);
  }, [rec, tenant.id]);
  useEffect(() => () => { clearInterval(timer.current); recorder.current?.stream?.getTracks().forEach((tr) => tr.stop()); }, []);

  const send = async (blob, name, source) => {
    setBusy(true);
    try {
      const fd = new FormData();
      fd.append('file', blob, name);
      fd.append('title', title.trim() || name);
      fd.append('source', source);
      setRec(await api.uploadMeeting(tenant.id, fd));
    } catch (e) { toast.error(e.message); } finally { setBusy(false); }
  };

  const startRec = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mr = new MediaRecorder(stream);
      const parts = [];
      mr.ondataavailable = (e) => e.data.size && parts.push(e.data);
      mr.onstop = () => {
        stream.getTracks().forEach((tr) => tr.stop());
        send(new Blob(parts, { type: mr.mimeType || 'audio/webm' }), `toplanti-kaydi.${(mr.mimeType || '').includes('ogg') ? 'ogg' : 'webm'}`, 'BROWSER');
      };
      mr.start(1000);
      recorder.current = mr;
      setElapsed(0);
      timer.current = setInterval(() => setElapsed((s) => s + 1), 1000);
      setRecording(true);
    } catch {
      toast.error('Mikrofona erişilemedi. Tarayıcı izinlerini kontrol edin veya kaydı dosya olarak yükleyin.');
    }
  };
  const stopRec = () => { clearInterval(timer.current); setRecording(false); recorder.current?.stop(); };

  const create = async () => {
    if ((form.name || '').trim().length < 2) return toast.warning('Proje adını yazın.');
    setBusy(true);
    try {
      const r = await api.meetingToProject(tenant.id, rec.id, { ...form, name: form.name.trim() });
      toast.success(`'${r.name}' oluşturuldu${r.steps ? `; ${r.steps} adımlık plan taslağını inceleyip onaylayın` : ''}.`);
      onCreated(r);
    } catch (e) { toast.error(e.message); } finally { setBusy(false); }
  };

  const ready = rec?.status === 'READY' && form;
  const footer = ready
    ? <><Button variant="secondary" onClick={onClose}>Vazgeç</Button><Button onClick={create} disabled={busy}>{busy ? 'Oluşturuluyor…' : 'Projeyi oluştur'}</Button></>
    : rec?.status === 'FAILED'
      ? <><Button variant="secondary" onClick={onClose}>Kapat</Button><Button onClick={() => { setRec(null); setFile(null); }}>Yeniden dene</Button></>
      : !rec && mode === 'UPLOAD'
        ? <><Button variant="secondary" onClick={onClose}>Vazgeç</Button><Button icon={Upload} disabled={!file || busy} onClick={() => send(file, file.name, 'UPLOAD')}>{busy ? 'Yükleniyor…' : 'Yükle ve işle'}</Button></>
        : <Button variant="secondary" onClick={onClose} disabled={recording}>Kapat</Button>;

  return (
    <Modal open onClose={recording ? undefined : onClose} title="Toplantıdan proje oluştur" size="lg" footer={footer}>
      {!rec && (
        <>
          <div className="ui-segmented" role="tablist" style={{ marginBottom: 12 }}>
            {[['UPLOAD', 'Dosya yükle'], ['RECORD', 'Tarayıcıda kaydet']].map(([k, l]) => (
              <button key={k} type="button" disabled={recording} className={`ui-segmented-item ${mode === k ? 'active' : ''}`} onClick={() => setMode(k)}>{l}</button>
            ))}
          </div>
          <div className="pj-field" style={{ marginBottom: 12 }}>
            <label htmlFor="mt-title">Toplantı adı</label>
            <input id="mt-title" className="ui-input" value={title} maxLength={200} placeholder="ör. Depo sayım uygulaması ön görüşmesi" onChange={(e) => setTitle(e.target.value)} />
          </div>
          {mode === 'UPLOAD' ? (
            <div className="pj-field">
              <label htmlFor="mt-file">Ses veya video dosyası</label>
              <input id="mt-file" type="file" accept="audio/*,video/*,.m4a,.mp3,.wav,.webm,.mp4,.ogg" onChange={(e) => setFile(e.target.files?.[0] || null)} />
              <p className="pj-hint">En fazla 300 MB ve 3 saat. Kayıt yazıya çevrildikten sonra silinir; yalnızca kişisel verileri maskelenmiş metin saklanır.</p>
            </div>
          ) : (
            <div className="pj-actions" style={{ alignItems: 'center' }}>
              {!recording
                ? <Button icon={Mic} onClick={startRec} disabled={busy}>Kaydı başlat</Button>
                : <><Badge tone="danger">● Kaydediliyor {mmss(elapsed)}</Badge><Button icon={Square} variant="secondary" onClick={stopRec}>Kaydı bitir</Button></>}
              <p className="pj-hint">Toplantıdakilere kayıt alındığını bildirin. Kayıt yazıya çevrildikten sonra silinir.</p>
            </div>
          )}
        </>
      )}
      {rec?.status === 'PROCESSING' && (
        <p className="pj-hint" role="status">{rec.stage || 'İşleniyor…'}{rec.duration_sec ? ` · kayıt ${mmss(rec.duration_sec)}` : ''}</p>
      )}
      {rec?.status === 'FAILED' && <p className="ui-text-danger" role="alert">{rec.error}</p>}
      {ready && (
        <>
          <div className="pj-form">
            <div className="pj-field"><label htmlFor="mt-name">Proje adı *</label>
              <input id="mt-name" className="ui-input" value={form.name} maxLength={255} onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))} /></div>
            <div className="pj-field"><label htmlFor="mt-kind">Tür</label>
              <select id="mt-kind" className="ui-input" value={form.kind} onChange={(e) => setForm((f) => ({ ...f, kind: e.target.value }))}>
                <option value="PROJECT">Proje</option><option value="CASE">Case</option></select></div>
            <div className="pj-field" style={{ gridColumn: '1 / -1' }}><label htmlFor="mt-desc">Açıklama</label>
              <textarea id="mt-desc" className="ui-input" rows={2} value={form.description} onChange={(e) => setForm((f) => ({ ...f, description: e.target.value }))} /></div>
            <div className="pj-field" style={{ gridColumn: '1 / -1' }}><label htmlFor="mt-req">İsterler</label>
              <textarea id="mt-req" className="ui-input" rows={5} value={form.requirements} onChange={(e) => setForm((f) => ({ ...f, requirements: e.target.value }))} /></div>
          </div>
          {rec.draft.plan?.steps?.length > 0 && (
            <>
              <label className="pj-hint" style={{ display: 'flex', gap: 8, margin: '10px 0 6px' }}>
                <input type="checkbox" checked={form.include_steps} onChange={(e) => setForm((f) => ({ ...f, include_steps: e.target.checked }))} />
                Önerilen {rec.draft.plan.steps.length} iş adımını plan taslağı olarak ekle
              </label>
              <ol className="pj-list" aria-label="Önerilen adımlar">
                {rec.draft.plan.steps.map((s) => <li key={s.key}><span><strong>{s.title}</strong>{s.job_title ? <small className="pj-hint"> · {s.job_title}</small> : null}</span></li>)}
              </ol>
            </>
          )}
          {rec.draft.plan?.questions?.length > 0 && (
            <p className="pj-hint" style={{ marginTop: 8 }}>Açık sorular: {rec.draft.plan.questions.join(' · ')}</p>
          )}
          <details style={{ marginTop: 10 }}>
            <summary className="pj-hint">Toplantı metni ({mmss(rec.duration_sec || 0)}){Object.keys(rec.pii || {}).length > 0 && ` · maskelenen: ${Object.entries(rec.pii).map(([k, n]) => `${n} ${PII[k] || k}`).join(', ')}`}</summary>
            <p className="pj-note" style={{ whiteSpace: 'pre-wrap' }}>{rec.transcript}</p>
          </details>
        </>
      )}
    </Modal>
  );
}
