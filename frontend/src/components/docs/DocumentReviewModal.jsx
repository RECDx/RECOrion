import React, { useCallback, useEffect, useRef, useState } from 'react';
import { CheckCircle2, Download, FlaskConical, RefreshCw, ShieldAlert, Trash2, Upload, XCircle } from 'lucide-react';
import { api } from '../../api';
import { Badge, Button, Modal } from '../../ui/components';
import { confirmDialog, promptDialog, toast } from '../../ui/feedback';
import { ACCEPT, fmtSize, isBusy, piiText, statusOf } from './docMeta';
import './docs.css';

const toLines = (v) => v.split('\n').map((x) => x.trim()).filter(Boolean);

/**
 * Öğrenme dokümanı inceleme: işlem sonucu (KVKK maskeleme, içerik güvenliği, görsel/OCR), öğrenme kartı
 * (özet + anahtar bilgiler düzenlenebilir, test soruları), test, onay/ret, yeni sürüm, indirme ve silme.
 * AI personel dokümanı ancak onaydan sonra öğrenir.
 */
export default function DocumentReviewModal({ documentId, onClose, onChanged, canManage = true }) {
  const [doc, setDoc] = useState(null);
  const [summary, setSummary] = useState('');
  const [points, setPoints] = useState('');
  const [busy, setBusy] = useState('');
  const versionRef = useRef(null);

  const load = useCallback(async () => {
    try {
      const d = await api.getDocument(documentId);
      setDoc(d);
      setSummary(d.learning_card?.summary || d.summary || '');
      setPoints((d.learning_card?.key_points || []).join('\n'));
    } catch (e) {
      toast.error(e.message);
    }
  }, [documentId]);
  useEffect(() => { if (documentId) load(); }, [documentId, load]);

  // İşlenirken birkaç saniyede bir yenile
  useEffect(() => {
    if (!doc || !isBusy(doc)) return undefined;
    const t = setInterval(load, 4000);
    return () => clearInterval(t);
  }, [doc, load]);

  const run = async (key, fn, okText) => {
    setBusy(key);
    try {
      await fn();
      if (okText) toast.success(okText);
      onChanged?.();
      await load();
    } catch (e) {
      toast.error(e.message);
    } finally {
      setBusy('');
    }
  };

  const approve = () => run('approve', () => api.approveDocument(doc.id, { summary, key_points: toLines(points) }),
    'Doküman onaylandı; AI personel artık bu bilgiyi kullanıyor.');
  const reject = async () => {
    const reason = await promptDialog({ message: 'Ret gerekçesi (isteğe bağlı):', defaultValue: '' });
    if (reason === null) return;
    run('reject', () => api.rejectDocument(doc.id, reason), 'Doküman reddedildi; öğrenilmeyecek.');
  };
  const remove = async () => {
    if (!(await confirmDialog({ message: `"${doc.original_name}" silinsin mi? AI personel bu dokümandan öğrendiklerini de unutur.`, danger: true }))) return;
    setBusy('delete');
    try {
      await api.deleteDocument(doc.id);
      toast.success('Doküman silindi.');
      onChanged?.();
      onClose();
    } catch (e) {
      toast.error(e.message);
      setBusy('');
    }
  };
  const uploadVersion = (e) => {
    const file = e.target.files?.[0];
    e.target.value = '';
    if (!file) return;
    const fd = new FormData();
    fd.append('file', file);
    setBusy('version');
    api.uploadDocumentVersion(doc.id, fd)
      .then(() => {
        toast.success('Yeni sürüm yüklendi; işlendikten sonra onayınıza sunulacak. Mevcut sürüm onaylanana kadar kullanılmaya devam eder.');
        onChanged?.();
        onClose();
      })
      .catch((err) => { toast.error(err.message); setBusy(''); });
  };

  const card = doc?.learning_card;
  const st = doc ? statusOf(doc.status) : null;
  const pending = doc?.status === 'PENDING_APPROVAL';

  const footer = doc && canManage && (
    <>
      <Button variant="ghost" icon={Trash2} onClick={remove} disabled={!!busy}>Sil</Button>
      <Button variant="ghost" icon={Download} onClick={() => api.downloadDocument(doc.id, doc.original_name).catch((e) => toast.error(e.message))}>İndir</Button>
      {['FAILED', 'QUARANTINED'].includes(doc.status) && <Button variant="secondary" icon={RefreshCw} onClick={() => run('re', () => api.reprocessDocument(doc.id), 'Doküman yeniden işleniyor.')} disabled={!!busy}>Yeniden işle</Button>}
      {doc.status === 'APPROVED' && (
        <>
          <input ref={versionRef} type="file" accept={ACCEPT} hidden onChange={uploadVersion} />
          <Button variant="secondary" icon={Upload} onClick={() => versionRef.current?.click()} disabled={!!busy}>Yeni sürüm yükle</Button>
        </>
      )}
      {['PENDING_APPROVAL', 'QUARANTINED', 'FAILED'].includes(doc.status) && <Button variant="danger" icon={XCircle} onClick={reject} disabled={!!busy}>Reddet</Button>}
      {pending && <Button variant="success" icon={CheckCircle2} onClick={approve} disabled={!!busy}>{busy === 'approve' ? 'Öğreniliyor…' : 'Onayla ve öğret'}</Button>}
    </>
  );

  return (
    <Modal open={!!documentId} onClose={onClose} size="lg" title={doc ? `${doc.original_name} · sürüm ${doc.version}` : 'Doküman'} footer={footer}>
      {!doc ? <p className="doc-hint">Yükleniyor…</p> : (
        <div className="doc-review">
          <div className="doc-facts">
            <Badge tone={st.tone}>{st.label}</Badge>
            <span>{(doc.file_type || '').toUpperCase()} · {fmtSize(doc.file_size)}</span>
            {doc.page_count ? <span>{doc.page_count} sayfa</span> : null}
            {doc.ocr_pages ? <span>{doc.ocr_pages} sayfa OCR ile okundu</span> : null}
            {doc.image_count ? <span>{doc.image_count} görsel açıklandı</span> : null}
            {doc.chunk_count ? <span>{doc.chunk_count} bilgi parçası</span> : null}
          </div>

          {isBusy(doc) && <div className="doc-note info">Doküman işleniyor: metin ve görseller okunuyor, kişisel veriler maskeleniyor, öğrenme kartı hazırlanıyor…</div>}
          {doc.error && <div className={`doc-note ${doc.status === 'PENDING_APPROVAL' ? 'warning' : 'danger'}`}>{doc.status === 'QUARANTINED' && <ShieldAlert size={15} />} {doc.error}</div>}
          {doc.pii_findings && Object.keys(doc.pii_findings).length > 0 && (
            <div className="doc-note info">KVKK: {piiText(doc.pii_findings)} maskelendi. AI personel bu verileri görmez; asıl dosya erişim kontrollü depoda kalır.</div>
          )}
          {doc.guard_result?.level === 'Unchecked' && <div className="doc-note warning">İçerik güvenliği kontrolü şu an yapılamadı; lütfen içeriği kendiniz gözden geçirin.</div>}

          {(pending || doc.status === 'APPROVED' || card) && (
            <>
              <div className="doc-field">
                <label htmlFor="doc-sum">Özet</label>
                <textarea id="doc-sum" className="ui-input" rows={4} value={summary} readOnly={!pending || !canManage} onChange={(e) => setSummary(e.target.value)} />
              </div>
              <div className="doc-field">
                <label htmlFor="doc-points">Öğrenilecek anahtar bilgiler (her satır bir bilgi)</label>
                <textarea id="doc-points" className="ui-input" rows={6} value={points} readOnly={!pending || !canManage} onChange={(e) => setPoints(e.target.value)} />
                {pending && <span className="doc-hint">Onaydan önce düzeltebilirsiniz. Dokümanın tamamı da parçalar halinde öğrenilir.</span>}
              </div>
            </>
          )}

          {card?.quiz?.length > 0 && (
            <div className="doc-field">
              <div className="doc-quiz-head">
                <label>Test soruları ({card.quiz.length})</label>
                {canManage && ['PENDING_APPROVAL', 'APPROVED'].includes(doc.status) && (
                  <Button size="sm" variant="secondary" icon={FlaskConical} onClick={() => run('test', () => api.testDocument(doc.id))} disabled={!!busy}>
                    {busy === 'test' ? 'Test ediliyor…' : 'AI personeli test et'}
                  </Button>
                )}
              </div>
              {doc.test_result && (
                <div className={`doc-note ${doc.test_result.percent >= 80 ? 'success' : 'warning'}`}>
                  Test sonucu: {doc.test_result.score}/{doc.test_result.total} doğru (%{doc.test_result.percent}) · {doc.test_result.model_code}
                </div>
              )}
              <ol className="doc-quiz">
                {card.quiz.map((q, i) => {
                  const res = doc.test_result?.details?.[i];
                  return (
                    <li key={i}>
                      <strong>{q.question}</strong>
                      <ul>
                        {q.options.map((o, j) => (
                          <li key={j} className={j === q.answer ? 'right' : ''}>{String.fromCharCode(65 + j)}) {o}{j === q.answer ? ' ✓' : ''}</li>
                        ))}
                      </ul>
                      {res && <span className={res.correct ? 'doc-ok' : 'doc-bad'}>AI personelin cevabı: {res.given || '—'} {res.correct ? '(doğru)' : '(yanlış)'}</span>}
                    </li>
                  );
                })}
              </ol>
            </div>
          )}

          {doc.chunk_preview?.length > 0 && (
            <details className="doc-field">
              <summary>Öğrenilecek metinden örnek (KVKK maskeli)</summary>
              {doc.chunk_preview.map((c, i) => <pre key={i} className="doc-chunk">{c}…</pre>)}
            </details>
          )}

          {doc.previous_versions?.length > 0 && (
            <div className="doc-hint">Önceki sürümler: {doc.previous_versions.map((v) => `v${v.version} (${statusOf(v.status).label})`).join(' · ')}</div>
          )}
        </div>
      )}
    </Modal>
  );
}
