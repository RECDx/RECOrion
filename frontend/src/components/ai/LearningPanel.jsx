import React, { useCallback, useEffect, useState } from 'react';
import { GraduationCap } from 'lucide-react';
import { api } from '../../api';
import { Badge, Button, Card, EmptyState, Modal } from '../../ui/components';
import { toast } from '../../ui/feedback';
import '../projects/projects.css';

const LABEL_TONE = { DOGRU: 'success', YANLIS: 'danger', BELIRSIZ: 'neutral' };
const CAUSES = [['MODEL_HATASI', 'AI personelin hatası'], ['ORTAM', 'Ortam / altyapı'], ['DEGERLENDIRICI', 'Değerlendirme hatası'],
  ['KAPSAM', 'Kapsam değişikliği'], ['BELIRSIZ', 'Belirsiz']];
const LESSON_TR = { SAVED: 'Ders hafızada', PENDING: 'Ders çıkarılıyor', NONE: 'Ders yok', SKIPPED: '—', FAILED: 'Ders çıkarılamadı' };
const fmt = (d) => (d ? new Date(d).toLocaleString('tr-TR', { dateStyle: 'short', timeStyle: 'short' }) : '');

/**
 * İSTEK #742: Şirket Yönetimi › Öğrenme. AI personelin sohbetten ve iş akışından (onay, ret, kontrol, test, aktarım) öğrendikleri.
 * Yanlışlar atılmaz; etiketlenir. Yalnız "AI personelin hatası" olan retlerden ders çıkar; yönetici nedeni düzeltebilir.
 */
export default function LearningPanel({ tenantId }) {
  const [summary, setSummary] = useState(null);
  const [rows, setRows] = useState(null);
  const [label, setLabel] = useState('');
  const [detail, setDetail] = useState(null);
  const [busy, setBusy] = useState(null);

  const load = useCallback(() => {
    api.getLearningSummary(tenantId).then(setSummary).catch((e) => toast.error(e.message));
    api.getLearningRecords(tenantId, label ? { label } : {}).then(setRows).catch((e) => { toast.error(e.message); setRows([]); });
  }, [tenantId, label]);
  useEffect(() => { load(); }, [load]);

  const changeCause = async (r, cause) => {
    if (!cause || cause === r.cause) return;
    setBusy(r.id);
    try {
      await api.setLearningCause(tenantId, r.id, { cause });
      toast.success(cause === 'MODEL_HATASI' ? 'Neden güncellendi; ders çıkarılacak.' : 'Neden güncellendi; bu retten çıkan ders varsa hafızadan geri alındı.');
      load();
    } catch (e) { toast.error(e.message); } finally { setBusy(null); }
  };
  const open = async (r) => {
    try { setDetail(await api.getLearningRecord(tenantId, r.id)); } catch (e) { toast.error(e.message); }
  };

  const n = (o, k) => (o && o[k]) || 0;
  return (
    <Card title="Öğrenme" subtitle="AI personeliniz sohbetten ve iş akışından (onay, ret, kontrol, test, aktarım) öğrenir. Yanlışlar silinmez, etiketlenir; yalnız AI personelin kendi hatası olan retlerden ders çıkar.">
      {summary && (
        <div className="pj-meta" style={{ flexWrap: 'wrap', gap: 12, marginBottom: 12 }} aria-label="Özet">
          <span><Badge tone="success">Doğru {n(summary.labels, 'DOGRU')}</Badge></span>
          <span><Badge tone="danger">Yanlış {n(summary.labels, 'YANLIS')}</Badge></span>
          <span><Badge tone="neutral">Belirsiz {n(summary.labels, 'BELIRSIZ')}</Badge></span>
          <span>Yanlış → doğru çifti: <strong>{summary.pairs}</strong></span>
          <span>Hafızaya yazılan ders: <strong>{n(summary.lessons, 'SAVED')}</strong></span>
          <span>Onay bekleyen kurumsal ders: <strong>{summary.pending_corporate}</strong></span>
        </div>
      )}
      {summary?.pending_corporate > 0 && (
        <p className="pj-hint">Kurumsal dersler tüm AI personeli etkilediği için onayınızı bekler: sağ panel › <strong>Hafıza</strong> › <strong>Onay bekliyor</strong>.</p>
      )}
      <div className="ui-segmented" role="tablist" style={{ margin: '8px 0 12px' }}>
        {[['', 'Tümü'], ['YANLIS', 'Yanlış'], ['DOGRU', 'Doğru'], ['BELIRSIZ', 'Belirsiz']].map(([k, l]) => (
          <button key={k || 'all'} type="button" className={`ui-segmented-item ${label === k ? 'active' : ''}`} onClick={() => setLabel(k)}>{l}</button>
        ))}
      </div>
      {!rows ? <p className="pj-hint">Yükleniyor…</p> : rows.length === 0 ? (
        <EmptyState icon={GraduationCap} title="Henüz öğrenme kaydı yok" description="AI personelin işleri onaylandıkça, reddedildikçe ve test edildikçe kayıtlar burada birikir." />
      ) : (
        <div className="ui-table-scroll">
          <table className="ui-table">
            <thead><tr><th>Tarih</th><th>AI personel</th><th>Adım</th><th>Kaynak</th><th>Etiket</th><th>Neden</th><th>Ders</th><th /></tr></thead>
            <tbody>{rows.map((r) => (
              <tr key={r.id}>
                <td data-label="Tarih">{fmt(r.created_at)}</td>
                <td data-label="AI personel">{r.agent_name || '—'}<br /><small className="pj-hint">{r.job_title}</small></td>
                <td data-label="Adım">{r.task_title || '—'}</td>
                <td data-label="Kaynak">{r.source_label}</td>
                <td data-label="Etiket"><Badge tone={LABEL_TONE[r.label]}>{r.label_text}</Badge>{r.paired && <small className="pj-hint"> çift</small>}</td>
                <td data-label="Neden">
                  {r.label === 'YANLIS' ? (
                    <select className="ui-input" value={r.cause || 'BELIRSIZ'} disabled={busy === r.id} aria-label={`${r.task_title || 'Kayıt'} nedeni`}
                      title={r.cause_reason || (r.cause_by === 'HUMAN' ? 'Yönetici belirledi' : r.cause_by === 'AI' ? 'RECAi önerisi' : 'Sistem kuralı')}
                      onChange={(e) => changeCause(r, e.target.value)}>
                      {CAUSES.map(([k, l]) => <option key={k} value={k}>{l}</option>)}
                    </select>
                  ) : (r.cause_text || '—')}
                </td>
                <td data-label="Ders">{r.lesson ? <span title={r.lesson}>{r.lesson.length > 90 ? `${r.lesson.slice(0, 90)}…` : r.lesson}</span> : (LESSON_TR[r.lesson_status] || '—')}
                  {r.lesson_scope === 'GLOBAL' && <small className="pj-hint"> (kurumsal)</small>}</td>
                <td data-label=""><Button size="sm" variant="ghost" onClick={() => open(r)}>Ayrıntı</Button></td>
              </tr>
            ))}</tbody>
          </table>
        </div>
      )}
      <Modal open={!!detail} onClose={() => setDetail(null)} size="lg" title={detail ? `${detail.source_label} · ${detail.label_text}` : ''}>
        {detail && (
          <div className="pj-form" style={{ gridTemplateColumns: '1fr' }}>
            <p className="pj-hint">{detail.agent_name} · {detail.job_title} · {fmt(detail.created_at)}</p>
            {detail.cause_text && <p><strong>Neden:</strong> {detail.cause_text}{detail.cause_reason ? ` — ${detail.cause_reason}` : ''}</p>}
            {detail.feedback && <><strong>Geri bildirim</strong><pre className="pj-pre">{detail.feedback}</pre></>}
            {detail.lesson && <><strong>Çıkarılan ders{detail.lesson_scope === 'GLOBAL' ? ' (kurumsal)' : ''}</strong><p>{detail.lesson}</p></>}
            {detail.task_input && <><strong>İş</strong><pre className="pj-pre">{detail.task_input}</pre></>}
            {detail.output && <><strong>Çıktı</strong><pre className="pj-pre">{detail.output}</pre></>}
          </div>
        )}
      </Modal>
    </Card>
  );
}
