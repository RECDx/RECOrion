/**
 * Bildirim (toast) ve onay penceresi altyapısı.
 * Tarayıcının alert/confirm/prompt pencereleri yerine kullanılır:
 *   notify('Kaydedildi')                       -> tür metinden tahmin edilir
 *   toast.success('...'), toast.error('...')
 *   if (!(await confirmDialog({ message: 'Silinsin mi?', danger: true }))) return;
 *   const value = await promptDialog({ message: 'Yeni ad', defaultValue: 'x' });
 * <FeedbackHost /> uygulamada bir kez render edilir.
 */

let listeners = [];
let toasts = [];
let dialog = null;
let nextId = 1;

function emit() {
  for (const l of listeners) l({ toasts, dialog });
}

export function subscribeFeedback(listener) {
  listeners.push(listener);
  listener({ toasts, dialog });
  return () => { listeners = listeners.filter((l) => l !== listener); };
}

function guessType(message) {
  const m = String(message || '').toLowerCase();
  if (/❌|hata|başarısız|basarisiz|bulunamadı|geçersiz|reddedildi|yetkiniz|error|failed|alınamadı|yapılamadı|gönderilemedi|silinemedi|kaydedilemedi/.test(m)) return 'error';
  if (/⚠️|uyarı|dikkat|lütfen|zorunlu|önce /.test(m)) return 'warning';
  if (/✅|✓|başarı|kaydedildi|güncellendi|oluşturuldu|silindi|gönderildi|eklendi|tamamlandı|onaylandı|aktive/.test(m)) return 'success';
  return 'info';
}

export function dismissToast(id) {
  toasts = toasts.filter((t) => t.id !== id);
  emit();
}

function push(type, message, { duration } = {}) {
  const id = nextId++;
  const text = String(message ?? '');
  toasts = [...toasts.slice(-4), { id, type, message: text }];
  emit();
  const ms = duration ?? (type === 'error' ? 7000 : Math.min(9000, 3500 + text.length * 25));
  window.setTimeout(() => dismissToast(id), ms);
  return id;
}

export const toast = {
  success: (m, o) => push('success', m, o),
  error: (m, o) => push('error', m, o),
  warning: (m, o) => push('warning', m, o),
  info: (m, o) => push('info', m, o),
};

/** alert() yerine: türü mesajdan tahmin eder. */
export function notify(message) {
  return push(guessType(message), message);
}

function openDialog(config) {
  return new Promise((resolve) => {
    dialog = { ...config, resolve: (value) => { dialog = null; emit(); resolve(value); } };
    emit();
  });
}

/** confirm() yerine: Promise<boolean> döner. */
export function confirmDialog(options) {
  const o = typeof options === 'string' ? { message: options } : options;
  return openDialog({ kind: 'confirm', title: 'Onay', confirmText: 'Onayla', cancelText: 'Vazgeç', ...o });
}

/** prompt() yerine: Promise<string|null> döner. */
export function promptDialog(options) {
  const o = typeof options === 'string' ? { message: options } : options;
  return openDialog({ kind: 'prompt', title: 'Bilgi Girişi', confirmText: 'Tamam', cancelText: 'Vazgeç', defaultValue: '', ...o });
}
