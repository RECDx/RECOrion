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
// #752 teslimat doğrulama türleri (sunucudaki verification.TYPES ile aynı)
export const VERIFY_TYPES = {
  TEST: 'Otomatik test', MEASURE: 'Ölçüm', EVIDENCE: 'Kanıt', CHECKLIST: 'Kontrol listesi', HUMAN: 'İnsan onayı',
};
export const VERIFY_HINT = {
  TEST: "Sistem dener; ör. 'Yurt dışı' seçilince yalnız yurt dışı turları görünür",
  MEASURE: 'Ölçülen değer ve hedef; ör. OEE ölçülür, hedef %65',
  EVIDENCE: 'Kanıt; ör. gönderim raporu, ekran görüntüsü, test kaydı',
  CHECKLIST: "Maddeleri ';' ile ayırın; ör. kontrol listesi tamam; uygunsuzluklar kapatıldı",
  HUMAN: 'Kimin onayı; ör. kilit kullanıcı imzası',
};
export const VERIFY_TONE = { VERIFIED: 'success', MISSING: 'danger', WAIVED: 'warning', PENDING: 'neutral' };

export const PRIORITY = { HIGH: 'Yüksek', MEDIUM: 'Orta', LOW: 'Düşük' };
export const fmtDay = (d) => (d ? new Date(d).toLocaleDateString('tr-TR', { day: '2-digit', month: 'short', year: 'numeric' }) : '—');
export const isEditable = (p) => ['DRAFT', 'PLANNING', 'READY'].includes(p?.status);
export const isPlanning = (p) => ['DRAFT', 'PLANNING'].includes(p?.status);
