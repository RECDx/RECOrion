/** Öğrenme dokümanı durumları, KVKK bulgu etiketleri ve desteklenen dosya türleri. */
export const STATUS = {
  UPLOADED: { label: 'Yüklendi', tone: 'neutral', busy: true },
  PROCESSING: { label: 'İşleniyor', tone: 'info', busy: true },
  PENDING_APPROVAL: { label: 'Onay bekliyor', tone: 'warning' },
  APPROVED: { label: 'Öğrenildi', tone: 'success' },
  REJECTED: { label: 'Reddedildi', tone: 'neutral' },
  QUARANTINED: { label: 'Karantinada', tone: 'danger' },
  FAILED: { label: 'İşlenemedi', tone: 'danger' },
  SUPERSEDED: { label: 'Eski sürüm', tone: 'neutral' },
  INDEXED: { label: 'Hafızada', tone: 'success' },
  ATTACHED: { label: 'Eklendi', tone: 'neutral' },
};
export const statusOf = (s) => STATUS[s] || { label: s || '—', tone: 'neutral' };
export const isBusy = (d) => !!statusOf(d.status).busy;
export const isReviewable = (d) => ['PENDING_APPROVAL', 'QUARANTINED', 'FAILED', 'APPROVED', 'REJECTED', 'SUPERSEDED'].includes(d.status);

export const PII_LABELS = { TCKN: 'T.C. kimlik no', IBAN: 'IBAN', CARD: 'Kart no', EMAIL: 'E-posta', PHONE: 'Telefon' };
export const piiText = (f) => Object.entries(f || {}).map(([k, n]) => `${n} ${PII_LABELS[k] || k}`).join(', ');

/** Dosya seçicide kabul edilen türler (sunucu ayrıca doğrular). */
export const ACCEPT = '.pdf,.docx,.doc,.rtf,.odt,.xlsx,.xls,.ods,.pptx,.ppt,.odp,.txt,.csv,.md,.json,.xml,.html,.png,.jpg,.jpeg,.webp,.bmp,.tif,.tiff';
export const ACCEPT_HINT = 'PDF, Word, Excel, PowerPoint (eski .doc/.xls/.ppt dahil), metin dosyaları ve görseller (PNG, JPG, WEBP, TIFF) · en fazla 50 MB';

export const fmtSize = (b) => (b > 1024 * 1024 ? `${(b / 1024 / 1024).toFixed(1)} MB` : `${Math.max(1, Math.round((b || 0) / 1024))} KB`);
export const IMAGE_TYPES = ['png', 'jpg', 'jpeg', 'webp', 'bmp', 'tif', 'tiff'];
