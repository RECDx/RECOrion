/** Proje/Case durum ve tür etiketleri (ADIM 6). */
export const STATUS = {
  DRAFT: { label: 'Taslak', tone: 'neutral' },
  PLANNING: { label: 'Planlama', tone: 'info' },
  READY: { label: 'Başlamaya hazır', tone: 'warning' },
  ACTIVE: { label: 'Aktif', tone: 'success' },
  PAUSED: { label: 'Duraklatıldı', tone: 'neutral' },
  COMPLETED: { label: 'Tamamlandı', tone: 'success' },
  CANCELLED: { label: 'İptal edildi', tone: 'danger' },
  RELEASED: { label: 'Yayınlandı', tone: 'success' },
};
export const statusOf = (s) => STATUS[s] || { label: s || '—', tone: 'neutral' };
export const KIND = { PROJECT: 'Proje', CASE: 'Case' };
export const PRIORITY = { HIGH: 'Yüksek', MEDIUM: 'Orta', LOW: 'Düşük' };
export const fmtDay = (d) => (d ? new Date(d).toLocaleDateString('tr-TR', { day: '2-digit', month: 'short', year: 'numeric' }) : '—');
export const isEditable = (p) => ['DRAFT', 'PLANNING', 'READY'].includes(p?.status);
export const isPlanning = (p) => ['DRAFT', 'PLANNING'].includes(p?.status);
