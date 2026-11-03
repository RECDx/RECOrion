import React, { useRef, useState } from 'react';
import { Building2, ImagePlus, Trash2 } from 'lucide-react';
import { api } from '../../api';
import { Button } from '../../ui/components';
import { confirmDialog, toast } from '../../ui/feedback';

// Şirketin resmi logosu (İSTEK): kayıt formu, Şirket Yönetimi › Şirket Profili, Ana Merkez (liste, düzenleme, kurum ekleme)
export const LOGO_TYPES = ['image/png', 'image/jpeg', 'image/webp'];
export const LOGO_MAX_BYTES = 2 * 1024 * 1024;
const HINT = 'PNG, JPG veya WEBP · en fazla 2 MB · kare ya da yatay; saydam arka planlı PNG önerilir.';

/** Dosyayı tarayıcıda denetler; uygunsa hata yerine null döner. Asıl denetim sunucudadır. */
export function logoFileError(file) {
  if (!file) return 'Dosya seçilmedi.';
  if (!LOGO_TYPES.includes(file.type)) return 'Logo PNG, JPG veya WEBP olmalı (SVG kabul edilmez).';
  if (file.size > LOGO_MAX_BYTES) return 'Logo en fazla 2 MB olabilir.';
  return null;
}

export const readAsDataUrl = (file) => new Promise((resolve, reject) => {
  const r = new FileReader();
  r.onload = () => resolve(r.result);
  r.onerror = () => reject(new Error('Dosya okunamadı.'));
  r.readAsDataURL(file);
});

/** Logo ya da yoksa şirket simgesi. */
export function TenantLogoMark({ url, name, size = 32, className = '' }) {
  const [broken, setBroken] = useState(false);
  const style = { width: size, height: size };
  if (!url || broken) {
    return <span className={`tl-mark tl-mark-empty ${className}`} style={style} title={name || ''}><Building2 size={Math.round(size * 0.5)} /></span>;
  }
  return <img className={`tl-mark ${className}`} style={style} src={url} alt={name ? `${name} logosu` : 'Şirket logosu'} onError={() => setBroken(true)} />;
}

/** Önizleme + "Logo seç" + "Kaldır". onFile(file) seçilen geçerli dosyayla çağrılır. */
export function LogoPicker({ url, name, onFile, onRemove, busy, id = 'tenant-logo-file' }) {
  const input = useRef(null);
  const pick = (e) => {
    const file = e.target.files?.[0];
    e.target.value = '';
    if (!file) return;
    const err = logoFileError(file);
    if (err) { toast.error(err); return; }
    onFile(file);
  };
  return (
    <div className="tl-picker" aria-label="Şirket logosu">
      <TenantLogoMark url={url} name={name} size={72} />
      <div className="tl-picker-actions">
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
          <Button size="sm" variant="secondary" icon={ImagePlus} disabled={busy} onClick={() => input.current?.click()}>
            {url ? 'Logoyu değiştir' : 'Logo seç'}
          </Button>
          {url && onRemove && <Button size="sm" variant="ghost" icon={Trash2} disabled={busy} onClick={onRemove}>Kaldır</Button>}
        </div>
        <small className="pj-hint">{HINT}</small>
        <input id={id} ref={input} type="file" accept={LOGO_TYPES.join(',')} hidden onChange={pick} />
      </div>
    </div>
  );
}

/** Kayıtlı şirketin logosunu hemen yükler/kaldırır (Şirket Yönetimi ve Ana Merkez). */
export function TenantLogoEditor({ tenantId, url, name, onChanged }) {
  const [busy, setBusy] = useState(false);
  const upload = async (file) => {
    setBusy(true);
    try {
      const r = await api.uploadTenantLogo(tenantId, file);
      toast.success(r.message || 'Şirket logosu kaydedildi.');
      onChanged?.(r.logo_url);
    } catch (e) { toast.error(e.message); } finally { setBusy(false); }
  };
  const remove = async () => {
    if (!(await confirmDialog({ message: `${name || 'Şirket'} logosu kaldırılsın mı?`, danger: true }))) return;
    setBusy(true);
    try {
      const r = await api.deleteTenantLogo(tenantId);
      toast.success(r.message || 'Şirket logosu kaldırıldı.');
      onChanged?.(null);
    } catch (e) { toast.error(e.message); } finally { setBusy(false); }
  };
  return <LogoPicker url={url} name={name} busy={busy} onFile={upload} onRemove={remove} />;
}

/** Henüz kaydedilmemiş şirket için (kayıt formu, kurum ekleme): seçilen logo data URL olarak forma eklenir. */
export function NewTenantLogoField({ value, onChange, id }) {
  return (
    <LogoPicker id={id} url={value} busy={false}
      onFile={async (file) => { try { onChange(await readAsDataUrl(file)); } catch (e) { toast.error(e.message); } }}
      onRemove={() => onChange(null)} />
  );
}
