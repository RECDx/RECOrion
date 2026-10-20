export const PURPOSE_LABELS = {
  AGENT_CHAT: 'AI personel sohbeti',
  BRAIN: 'Beyin AI',
  PLATFORM_ASSISTANT: 'Süper Yönetici asistanı',
  MANIFESTO: 'Manifesto üretimi',
  ROLE_PROMPT: 'Rol promptu üretimi',
  TITLE_REVIEW: 'Ünvan incelemesi',
  DEEP_SEARCH: 'Derin araştırma',
  LEARNING: 'Öğrenme',
  EMBEDDING: 'Hafıza vektörleme',
  RERANK: 'Hafıza sıralama',
  CHAT: 'Sohbet',
};

export const ENTRY_LABELS = {
  MONTHLY_GRANT: 'Aylık kredi hakkı',
  TOPUP: 'Ek kredi',
  EXPIRE: 'Süresi dolan kredi',
  ADJUSTMENT: 'Düzeltme',
  USAGE: 'Kullanım',
};

const nf = new Intl.NumberFormat('tr-TR', { maximumFractionDigits: 1 });
const nf2 = new Intl.NumberFormat('tr-TR', { maximumFractionDigits: 2 });

export const fmtCredits = (v) => nf.format(Number(v || 0));
export const fmtPrecise = (v) => nf2.format(Number(v || 0));
export const fmtTokens = (v) => {
  const n = Number(v || 0);
  return n >= 1_000_000 ? `${nf.format(n / 1_000_000)} M` : n >= 1000 ? `${nf.format(n / 1000)} B` : String(n);
};
export const fmtDate = (v) => (v ? new Date(v).toLocaleString('tr-TR', { dateStyle: 'short', timeStyle: 'short' }) : '—');
export const purposeLabel = (p) => PURPOSE_LABELS[p] || p || '—';
