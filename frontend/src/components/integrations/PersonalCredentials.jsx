import React, { useCallback, useEffect, useState } from 'react';
import { KeyRound, Plus } from 'lucide-react';
import { api } from '../../api';
import { Badge, Button, Card, EmptyState, Modal } from '../../ui/components';
import { confirmDialog, toast } from '../../ui/feedback';

const fmtDay = (d) => (d ? new Date(d).toLocaleDateString('tr-TR', { day: '2-digit', month: 'short', year: 'numeric' }) : '—');

/** Bağlantılarım › Şirket sistemlerindeki anahtarlarım (ADIM 14.2): AI personeliniz sizin adınıza yalnızca bu anahtarla işlem yapar
 * (ör. RECSlip.App v2'de masraf onayı). Anahtar bir kez girilir, denenir ve şifreli saklanır; bir daha gösterilmez. */
export default function PersonalCredentials() {
  const [data, setData] = useState(null);
  const [editing, setEditing] = useState(null);  // {} yeni, {cred} düzenle
  const load = useCallback(() => api.getMyCredentials().then(setData).catch((e) => toast.error(e.message)), []);
  useEffect(() => { load(); }, [load]);
  const test = async (c) => {
    try {
      const r = await api.testCredential(c.id);
      r.last_test_ok ? toast.success(`Anahtar çalışıyor: ${r.external_login}`) : toast.error(r.last_error || 'Anahtar çalışmıyor.');
      load();
    } catch (e) { toast.error(e.message); }
  };
  const remove = async (c) => {
    if (!(await confirmDialog({ message: `${c.connection_name} anahtarınız silinsin mi? AI personeliniz bu sistemde sizin adınıza işlem yapamaz.`, danger: true }))) return;
    try { await api.deleteCredential(c.id); toast.success('Anahtar silindi.'); load(); } catch (e) { toast.error(e.message); }
  };
  const status = (c) => (!c.usable ? (c.status === 'INVALID' ? ['Geçersiz', 'danger'] : ['Süresi doldu', 'danger'])
    : c.days_left != null && c.days_left <= 14 ? [`${c.days_left} gün kaldı`, 'warning'] : ['Etkin', 'success']);
  return (
    <Card title="Şirket sistemlerindeki anahtarlarım"
      subtitle="AI personeliniz sizin adınıza (ör. RECSlip'te masraf onayı) yalnızca kendi kullanıcı anahtarınızla işlem yapar; kayıtlarda siz ve 'RECAi' görünür."
      actions={data?.connections?.length ? <Button icon={Plus} onClick={() => setEditing({})}>Anahtar ekle</Button> : null}>
      {!data ? <p className="pj-hint">Yükleniyor…</p> : data.credentials.length === 0 ? (
        <EmptyState icon={KeyRound} title="Henüz anahtar yok"
          description={data.connections.length ? 'Odoo kullanıcınızın API anahtarını ekleyin (Odoo › Tercihler › Hesap Güvenliği › Yeni API Anahtarı).'
            : 'Şirketinizde kişisel anahtar kullanılan bir bağlantı (Odoo) yok.'} />
      ) : (
        <ul className="pj-list" aria-label="Kişisel bağlantı anahtarları">
          {data.credentials.map((c) => {
            const [label, tone] = status(c);
            return (
              <li key={c.id}>
                <span><strong>{c.connection_name}</strong> · {c.external_name || '—'} <code className="ig-inline">{c.external_login}</code><br />
                  <small className="pj-hint">Adınıza çalışan AI personel: {c.agent_name || 'seçilmedi'} · bitiş {fmtDay(c.expires_at)}
                    {c.last_error ? ` · ${c.last_error}` : ''}</small></span>
                <Badge tone={tone}>{label}</Badge>
                <Button size="sm" variant="ghost" onClick={() => test(c)}>Dene</Button>
                <Button size="sm" variant="ghost" onClick={() => setEditing({ cred: c })}>Düzenle</Button>
                <Button size="sm" variant="ghost" onClick={() => remove(c)}>Sil</Button>
              </li>
            );
          })}
        </ul>
      )}
      {editing && <CredentialForm data={data} cred={editing.cred} onClose={() => setEditing(null)} onSaved={() => { setEditing(null); load(); }} />}
    </Card>
  );
}

function CredentialForm({ data, cred, onClose, onSaved }) {
  const [conn, setConn] = useState(cred?.connection_id || data.connections[0]?.id || '');
  const [key, setKey] = useState('');
  const [agent, setAgent] = useState(cred?.agent_actor_id || '');
  const [expires, setExpires] = useState(cred?.expires_at ? cred.expires_at.slice(0, 10) : '');
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState('');  // F33: hata yalnız kısa bildirimde değil formda da kalır
  const save = async () => {
    setBusy(true);
    setErr('');
    const body = { api_key: key.trim() || null, agent_actor_id: agent || null, expires_at: expires ? `${expires}T23:59:00+03:00` : null };
    try {
      const r = cred ? await api.updateCredential(cred.id, body) : await api.addCredential({ connection_id: conn, ...body });
      toast.success(`Kaydedildi: ${r.external_login}`);
      onSaved();
    } catch (e) { setErr(e.message); toast.error(e.message); } finally { setBusy(false); }
  };
  return (
    <Modal open onClose={onClose} title={cred ? 'Anahtarı düzenle' : 'Anahtar ekle'} size="md"
      footer={<><Button variant="secondary" onClick={onClose}>Vazgeç</Button>
        <Button disabled={busy || (!cred && (!conn || key.trim().length < 8))} onClick={save}>{busy ? 'Deneniyor…' : 'Dene ve kaydet'}</Button></>}>
      <div className="pj-form">
        {err && <p className="ui-text-danger pj-field full" role="alert" style={{ fontSize: '0.82rem', margin: 0 }}>{err}</p>}
        {!cred && (
          <div className="pj-field full"><label htmlFor="pc-conn">Sistem</label>
            <select id="pc-conn" className="ui-input" value={conn} onChange={(e) => setConn(e.target.value)}>
              {data.connections.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
            </select></div>
        )}
        <div className="pj-field full"><label htmlFor="pc-key">{cred ? 'Yeni API anahtarı (değiştirmeyecekseniz boş bırakın)' : 'API anahtarı'}</label>
          <input id="pc-key" className="ui-input" type="password" autoComplete="off" value={key} onChange={(e) => setKey(e.target.value)} />
          <small className="pj-hint">Odoo › sağ üst › Tercihler › Hesap Güvenliği › Yeni API Anahtarı. Anahtar denenir, şifreli saklanır, bir daha gösterilmez.</small></div>
        <div className="pj-field"><label htmlFor="pc-agent">Adınıza çalışacak AI personel</label>
          <select id="pc-agent" className="ui-input" value={agent} onChange={(e) => setAgent(e.target.value)}>
            <option value="">Seçin</option>
            {data.agents.map((a) => <option key={a.id} value={a.id}>{a.name}</option>)}
          </select></div>
        <div className="pj-field"><label htmlFor="pc-exp">Anahtarın bitiş tarihi</label>
          <input id="pc-exp" className="ui-input" type="date" value={expires} onChange={(e) => setExpires(e.target.value)} />
          <small className="pj-hint">Odoo'da verdiğiniz bitiş; yaklaşınca hatırlatılır.</small></div>
      </div>
    </Modal>
  );
}
