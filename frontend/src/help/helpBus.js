// Yardım (ADIM 15): bulunulan ekranın anahtarı ve Yardım panelini açma/gezinme olayları.
// Anahtarlar: super/<SEKME>, company/<SEKME>, workspace/<MOD>, workspace/project/<sekme> (backend/app/services/help_center.py).
let current = '';

export const setHelpScreen = (key) => { current = key || ''; };
export const getHelpScreen = () => current;

/** Açık pencerenin başlığı (F1 o pencerenin anlatımına gitsin). */
export function openDialogTitle() {
  const dlg = [...document.querySelectorAll('[role="dialog"][aria-modal="true"], [role="alertdialog"]')].pop();
  if (dlg) return dlg.getAttribute('aria-label') || dlg.querySelector('h2, h3')?.textContent || '';
  const sa = [...document.querySelectorAll('.super-admin-modal-box')].pop();
  return sa?.querySelector('h3')?.textContent || '';
}

/** Yardım panelini açar: { tab: 'screen'|'toc'|'ask', slug?, question? } */
export const openHelp = (detail = {}) => window.dispatchEvent(new CustomEvent('recorion:help', { detail }));
/** RECAi'nin önerdiği ekrana gider (App dinler). */
export const navigateTo = (key) => window.dispatchEvent(new CustomEvent('recorion:navigate', { detail: { key } }));

/** Başlık -> sayfa içi bağlantı (backend slugify ile aynı). */
export function slugify(s) {
  return (s || '').replace(/ı/g, 'i').replace(/İ/g, 'I').normalize('NFKD').replace(/[̀-ͯ]/g, '')
    .toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '').slice(0, 60) || 'sayfa';
}
