import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { Pencil, Plus, ShieldCheck, Trash2 } from 'lucide-react';
import { api } from '../../api';
import { can, PERMISSION_MODULES } from '../../permissions';
import { Badge, Button, Card, EmptyState, Modal } from '../../ui/components';
import { confirmDialog, toast } from '../../ui/feedback';

const PLATFORM_ONLY = new Set(['*', 'system:admin']);
const empty = { id: null, name: '', description: '', permissions: [] };

/**
 * Şirkete özel yetki rolleri (#612): Kullanıcı Yönetimi'nde listelenir; izni olan oluşturur (role:create), düzenler (role:edit),
 * siler (role:delete). Şirket yöneticisi olmayan kişi kendisinde olmayan izni role ekleyemez (seçenek kapalı görünür).
 */
export default function TenantRolesCard({ tenantId, currentUser, onChanged }) {
  const [roles, setRoles] = useState(null);
  const [perms, setPerms] = useState([]);
  const [form, setForm] = useState(null);
  const [busy, setBusy] = useState(false);
  const isAdmin = currentUser?.is_super_admin || currentUser?.role === 'COMPANY_ADMIN';
  const mayGrant = (code) => isAdmin || can(currentUser, code);

  const load = useCallback(() => {
    if (!tenantId) return;
    api.getRoles(tenantId).then(setRoles).catch((e) => toast.error(e.message));
  }, [tenantId]);
  useEffect(() => { load(); }, [load]);
  useEffect(() => { api.getPermissions().then((p) => setPerms((p || []).filter((x) => !PLATFORM_ONLY.has(x.code)))).catch(() => {}); }, []);

  const byModule = useMemo(() => PERMISSION_MODULES.map(([code, label]) => [label, perms.filter((p) => p.module === code)])
    .filter(([, list]) => list.length), [perms]);

  const save = async () => {
    setBusy(true);
    const body = { name: form.name, description: form.description, permissions: form.permissions };
    try {
      if (form.id) await api.updateRole(tenantId, form.id, body);
      else await api.createRole(tenantId, body);
      toast.success(form.id ? 'Rol güncellendi.' : 'Rol oluşturuldu.');
      setForm(null);
      load();
      onChanged?.();
    } catch (e) { toast.error(e.message); } finally { setBusy(false); }
  };
  const remove = async (r) => {
    if (!(await confirmDialog({ message: `'${r.name}' rolü silinsin mi? Role atanmış kullanıcı varsa silinmez.` }))) return;
    try { await api.deleteRole(tenantId, r.id); toast.success('Rol silindi.'); load(); onChanged?.(); } catch (e) { toast.error(e.message); }
  };
  const toggle = (code) => setForm((f) => ({ ...f, permissions: f.permissions.includes(code) ? f.permissions.filter((c) => c !== code) : [...f.permissions, code] }));

  return (
    <Card title="Şirkete özel roller" actions={<ShieldCheck size={18} />}
      subtitle="Sistem rolleri yetmediğinde şirketinize özel izin paketi tanımlayın; kullanıcıya rol olarak atayın.">
      {can(currentUser, 'role:create') && (
        <div className="pj-actions" style={{ marginBottom: 10 }}>
          <Button icon={Plus} size="sm" onClick={() => setForm({ ...empty })}>Yeni rol</Button>
        </div>
      )}
      {!roles ? <p className="pj-hint">Yükleniyor…</p> : roles.length === 0 ? (
        <EmptyState icon={ShieldCheck} title="Şirkete özel rol yok" description="Kullanıcılar sistem rolleriyle çalışıyor." />
      ) : (
        <ul className="pj-list" aria-label="Şirkete özel roller">
          {roles.map((r) => (
            <li key={r.id}>
              <span><strong>{r.name}</strong>{r.description ? <small className="pj-hint"> · {r.description}</small> : null}</span>
              <Badge tone="neutral">{(r.permissions || []).length} izin</Badge>
              {can(currentUser, 'role:edit') && (
                <button type="button" className="ui-icon-btn" aria-label={`${r.name} rolünü düzenle`}
                  onClick={() => setForm({ id: r.id, name: r.name, description: r.description || '', permissions: [...(r.permissions || [])] })}><Pencil size={14} /></button>
              )}
              {can(currentUser, 'role:delete') && (
                <button type="button" className="ui-icon-btn" aria-label={`${r.name} rolünü sil`} onClick={() => remove(r)}><Trash2 size={14} /></button>
              )}
            </li>
          ))}
        </ul>
      )}

      {form && (
        <Modal open onClose={() => setForm(null)} title={form.id ? 'Rolü düzenle' : 'Yeni şirket rolü'} size="lg"
          footer={<><Button variant="secondary" onClick={() => setForm(null)}>Vazgeç</Button>
            <Button onClick={save} disabled={busy || !form.name.trim()}>{busy ? 'Kaydediliyor…' : 'Kaydet'}</Button></>}>
          <div className="pj-form">
            <div className="pj-field">
              <label htmlFor="tr-name">Rol adı</label>
              <input id="tr-name" className="ui-input" maxLength={64} value={form.name} placeholder="ör. Muhasebe Onaylayıcı"
                onChange={(e) => setForm({ ...form, name: e.target.value })} />
            </div>
            <div className="pj-field">
              <label htmlFor="tr-desc">Açıklama</label>
              <input id="tr-desc" className="ui-input" maxLength={300} value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} />
            </div>
            <p className="pj-hint">{form.permissions.length} izin seçili. Her kullanıcıda bulunan temel izinler (şirket bilgilerini görme, sohbet vb.) rol seçilmese de geçerlidir.</p>
            {byModule.map(([label, list]) => (
              <fieldset key={label} className="pj-field" style={{ border: '1px solid var(--border-subtle)', borderRadius: 8, padding: '8px 12px' }}>
                <legend className="pj-hint">{label}</legend>
                {list.map((p) => {
                  const allowed = mayGrant(p.code);
                  return (
                    <label key={p.code} style={{ display: 'flex', gap: 8, alignItems: 'flex-start', padding: '3px 0', opacity: allowed ? 1 : 0.55 }}
                      title={allowed ? p.description : 'Sizde olmayan izni role ekleyemezsiniz.'}>
                      <input type="checkbox" checked={form.permissions.includes(p.code)} disabled={!allowed} onChange={() => toggle(p.code)} />
                      <span>{p.name}<small className="pj-hint" style={{ display: 'block' }}>{p.description}</small></span>
                    </label>
                  );
                })}
              </fieldset>
            ))}
          </div>
        </Modal>
      )}
    </Card>
  );
}
