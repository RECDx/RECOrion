import { api } from '../../api';
import { confirmDialog } from '../../ui/feedback';

/**
 * İş adımını onaylar. Kabul kapısı (#734) uyarı verirse — uygulama gerçekten açılıp denenmedi, testler/duman testi kaldı,
 * README eksik — onaylayıcıya gösterir; "Yine de onayla" derse onay verilir ve akış geçmişine yazılır.
 */
export async function approveTask(taskId) {
  try {
    return await api.decideTask(taskId, true);
  } catch (e) {
    if (e.code !== 'TEST_GATE') throw e;
    const ok = await confirmDialog({
      title: 'Kabul öncesi denetim',
      message: `${e.message}\n\nYine de onaylamak istiyor musunuz? Bu karar akış geçmişine yazılır.`,
      confirmText: 'Yine de onayla',
      cancelText: 'Vazgeç',
    });
    if (!ok) throw new Error('Onay verilmedi. Testler sekmesinden testleri ve duman testini çalıştırabilirsiniz.');
    return api.decideTask(taskId, true, null, true);
  }
}
