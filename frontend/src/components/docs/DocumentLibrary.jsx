import React, { useCallback, useEffect, useRef, useState } from 'react';
import { FileText, Image as ImageIcon, UploadCloud } from 'lucide-react';
import { Badge, Button, EmptyState } from '../../ui/components';
import { toast } from '../../ui/feedback';
import DocumentReviewModal from './DocumentReviewModal';
import { ACCEPT, ACCEPT_HINT, IMAGE_TYPES, fmtSize, isBusy, piiText, statusOf } from './docMeta';
import './docs.css';

/**
 * Genel öğrenme dokümanı kütüphanesi (şirket unvanı ve platform katalog unvanı için).
 * load(): Promise<doc[]>; upload(FormData): Promise<doc>
 */
export default function DocumentLibrary({ load, upload, intro, canManage = true, emptyText }) {
  const [docs, setDocs] = useState(null);
  const [uploading, setUploading] = useState(0);
  const [reviewId, setReviewId] = useState(null);
  const [dragOver, setDragOver] = useState(false);
  const inputRef = useRef(null);

  const refresh = useCallback(() => load().then(setDocs).catch((e) => toast.error(e.message)), [load]);
  useEffect(() => { refresh(); }, [refresh]);
  useEffect(() => {
    if (!docs?.some(isBusy)) return undefined;
    const t = setInterval(refresh, 4000);
    return () => clearInterval(t);
  }, [docs, refresh]);

  const send = async (files) => {
    const list = [...(files || [])];
    if (!list.length) return;
    setUploading(list.length);
    for (const file of list) {
      const fd = new FormData();
      fd.append('file', file);
      try {
        await upload(fd);
        toast.success(`'${file.name}' yüklendi; işlendikten sonra onayınıza sunulacak.`);
      } catch (e) {
        toast.error(`${file.name}: ${e.message}`);
      }
      setUploading((n) => n - 1);
    }
    refresh();
  };

  return (
    <div className="doc-lib">
      {intro && <p className="doc-hint">{intro}</p>}
      {canManage && (
        <button
          type="button"
          className={`doc-drop ${dragOver ? 'over' : ''}`}
          onClick={() => inputRef.current?.click()}
          onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
          onDragLeave={() => setDragOver(false)}
          onDrop={(e) => { e.preventDefault(); setDragOver(false); send(e.dataTransfer.files); }}
          disabled={uploading > 0}
        >
          <UploadCloud size={22} />
          <strong>{uploading ? `${uploading} dosya yükleniyor…` : 'Doküman veya görsel yükleyin (tıklayın ya da sürükleyin)'}</strong>
          <span>{ACCEPT_HINT}. Birden fazla dosya seçebilirsiniz.</span>
          <input ref={inputRef} type="file" multiple accept={ACCEPT} hidden onChange={(e) => { send(e.target.files); e.target.value = ''; }} />
        </button>
      )}

      {!docs ? <p className="doc-hint">Yükleniyor…</p> : docs.length === 0 ? (
        <EmptyState icon={FileText} title="Henüz doküman yok" description={emptyText || 'Yüklenen dokümanlar onaylandıktan sonra öğrenilir.'} />
      ) : (
        <ul className="doc-list">
          {docs.map((d) => {
            const st = statusOf(d.status);
            const Icon = IMAGE_TYPES.includes(d.file_type) ? ImageIcon : FileText;
            return (
              <li key={d.id}>
                <Icon size={18} className="doc-icon" />
                <div className="doc-main">
                  <strong title={d.original_name}>{d.original_name}</strong>
                  <span>
                    {(d.file_type || '').toUpperCase()} · {fmtSize(d.file_size)}{d.version > 1 ? ` · sürüm ${d.version}` : ''}
                    {d.image_count ? ` · ${d.image_count} görsel` : ''}{d.pii_findings && Object.keys(d.pii_findings).length ? ` · KVKK: ${piiText(d.pii_findings)} maskelendi` : ''}
                  </span>
                  {d.error && <span className="doc-err">{d.error}</span>}
                </div>
                <Badge tone={st.tone}>{st.label}</Badge>
                <Button size="sm" variant={d.status === 'PENDING_APPROVAL' ? 'primary' : 'secondary'} onClick={() => setReviewId(d.id)} disabled={isBusy(d)}>
                  {d.status === 'PENDING_APPROVAL' ? 'İncele ve onayla' : 'Aç'}
                </Button>
              </li>
            );
          })}
        </ul>
      )}

      {reviewId && <DocumentReviewModal documentId={reviewId} canManage={canManage} onClose={() => setReviewId(null)} onChanged={refresh} />}
    </div>
  );
}
