import { api } from '../../api';
import { confirmDialog, promptDialog } from '../../ui/feedback';

/**
 * İş adımını onaylar. F93: önce onay penceresi açılır (isteğe bağlı onay notu; kalan küçük kusurlar/koşullar yazılır,
 * akış geçmişine kaydedilir). Kabul kapısı (#734) uyarı verirse — uygulama gerçekten açılıp denenmedi, testler/duman testi
 * kaldı, README eksik — onaylayıcıya gösterir; "Yine de onayla" derse onay verilir ve geçmişe yazılır.
 * Vazgeçilirse { cancelled: true } döner.
 */
export async function approveTask(taskId, title) {
  const note = await promptDialog({
    title: 'Onayla',
    message: `${title ? `'${title}' onaylanacak; kod varsa ana dala birleşir.\n\n` : ''}Onay notu (isteğe bağlı — kalan küçük kusurlar, koşullar):`,
    confirmText: 'Onayla',
  });
  if (note === null) return { cancelled: true };
  try {
    return await api.decideTask(taskId, true, note.trim() || null);
  } catch (e) {
    if (e.code !== 'TEST_GATE') throw e;
    const ok = await confirmDialog({
      title: 'Kabul öncesi denetim',
      message: `${e.message}\n\nYine de onaylamak istiyor musunuz? Bu karar akış geçmişine yazılır.`,
      confirmText: 'Yine de onayla',
      cancelText: 'Vazgeç',
    });
    if (!ok) throw new Error('Onay verilmedi. Testler sekmesinden testleri ve duman testini çalıştırabilirsiniz.');
    return api.decideTask(taskId, true, note.trim() || null, true);
  }
}
