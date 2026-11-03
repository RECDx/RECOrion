import React from 'react';
import { Card } from '../../ui/components';
import { TenantLogoEditor } from './TenantLogo';

/** Şirket Yönetimi › Şirket Profili: resmi logo (şirket yöneticisi değiştirir) ve kayıtlı kurum bilgileri. */
export default function CompanyProfile({ tenant, onLogoChanged }) {
  if (!tenant) return <p className="pj-hint">Yükleniyor…</p>;
  const rows = [
    ['Ünvan', tenant.name], ['Vergi no / dairesi', [tenant.tax_id, tenant.tax_office].filter(Boolean).join(' · ')],
    ['Telefon', tenant.phone], ['E-posta', tenant.contact_email], ['Web sitesi', tenant.website], ['Adres', tenant.address],
  ];
  return (
    <div className="pj-steps" style={{ maxWidth: 900 }}>
      <Card title="Şirket logosu" subtitle="Resmi logonuz Work Space ve Şirket Yönetimi ekranlarında şirketinizi temsil eder.">
        <TenantLogoEditor tenantId={tenant.id} url={tenant.logo_url} name={tenant.name} onChanged={onLogoChanged} />
      </Card>
      <Card title="Kurum bilgileri" subtitle="Değişiklik için RECDx ile iletişime geçin.">
        <ul className="pj-list" aria-label="Kurum bilgileri">
          {rows.map(([k, v]) => <li key={k}><span>{k}</span><strong>{v || '—'}</strong></li>)}
        </ul>
      </Card>
    </div>
  );
}
