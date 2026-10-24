import React, { useCallback, useEffect, useState } from 'react';
import { KeyRound, Plus } from 'lucide-react';
import { api } from '../../api';
import { Badge, Button, Card, EmptyState, Modal } from '../../ui/components';
import { confirmDialog, toast } from '../../ui/feedback';
import '../projects/projects.css';
import './integrations.css';

const fmt = (d) => (d ? new Date(d).toLocaleString('tr-TR', { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' }) : '—');
const SCOPE = { READ: 'Okuma', WRITE: 'Proje açma / plana adım' };

/** Bağlantılarım (ADIM 12.6): Claude, Cursor veya kendi sisteminizden RECOrion'a MCP ile bağlanmak için kişisel erişim anahtarları. */
export default function PersonalTokens() {
  const [data, setData] = useState(null);
  const [creating, setCreating] = useState(false);
  const [shown, setShown] = useState(null);
  const load = useCallback(() => api.getPersonalTokens().then(setData).catch((e) => toast.error(e.message)), []);
  useEffect(() => { load(); }, [load]);
  const revoke = async (t) => {
    if (!(await confirmDialog({ message: `'${t.name}' anahtarı iptal edilsin mi? Bu anahtarı kullanan araçlar hemen bağlanamaz.`, danger: true }))) return;
    try { await api.revokePersonalToken(t.id); toast.success('Anahtar iptal edildi.'); load(); } catch (e) { toast.error(e.message); }
  };
  return (
    <div className="pj-page">
      <div className="pj-head">
        <div className="pj-title">
          <h2>Bağlantılarım</h2>
          <span className="pj-sub">Claude, Cursor veya şirketinizin kendi sisteminden RECOrion'a MCP ile bağlanın: proje durumunu sorun, proje/Case açın,
            plan taslağına adım ekleyin. Anahtar sizin yetkilerinizle çalışır; onaylar yine RECOrion'da verilir.</span>
        </div>
      </div>
      <Card title="Kişisel erişim anahtarları" subtitle={data ? `MCP sunucu adresi: ${data.server_url}` : ''}
        actions={<Button icon={Plus} onClick={() => setCreating(true)}>Anahtar oluştur</Button>}>
        {!data ? <p className="pj-hint">Yükleniyor…</p> : data.tokens.length === 0 ? (
          <EmptyState icon={KeyRound} title="Henüz anahtar yok" description="Bir anahtar oluşturup kullandığınız araca ekleyin." />
        ) : (
          <ul className="pj-list" aria-label="Erişim anahtarları">
            {data.tokens.map((t) => (
              <li key={t.id}>
                <span><strong>{t.name}</strong> <code className="ig-inline">{t.prefix}…</code><br />
                  <small className="pj-hint">{t.scopes.map((s) => SCOPE[s] || s).join(' + ')} · son kullanım {fmt(t.last_used_at)} ({t.use_count} istek) · bitiş {fmt(t.expires_at)}</small></span>
                <Badge tone={t.active ? 'success' : 'neutral'}>{t.active ? 'Etkin' : t.revoked_at ? 'İptal edildi' : 'Süresi doldu'}</Badge>
                {t.active && <Button size="sm" variant="ghost" onClick={() => revoke(t)}>İptal et</Button>}
              </li>
            ))}
          </ul>
        )}
      </Card>
      {creating && <CreateToken onClose={() => setCreating(false)} onCreated={(t) => { setCreating(false); setShown(t); load(); }} />}
      {shown && <ShowToken data={shown} onClose={() => setShown(null)} />}
    </div>
  );
}

function CreateToken({ onClose, onCreated }) {
  const [name, setName] = useState('Claude');
  const [write, setWrite] = useState(false);
  const [days, setDays] = useState(90);
  const [busy, setBusy] = useState(false);
  const save = async () => {
    setBusy(true);
    try { onCreated(await api.createPersonalToken({ name: name.trim(), scopes: write ? ['READ', 'WRITE'] : ['READ'], days: Number(days) })); }
    catch (e) { toast.error(e.message); } finally { setBusy(false); }
  };
  return (
    <Modal open onClose={onClose} title="Anahtar oluştur" size="md"
      footer={<><Button variant="secondary" onClick={onClose}>Vazgeç</Button><Button disabled={busy || name.trim().length < 2} onClick={save}>Oluştur</Button></>}>
      <div className="pj-form">
        <div className="pj-field full"><label htmlFor="pt-name">Ad (nerede kullanacaksınız)</label>
          <input id="pt-name" className="ui-input" value={name} maxLength={80} onChange={(e) => setName(e.target.value)} /></div>
        <div className="pj-field full">
          <label style={{ display: 'flex', gap: 6, alignItems: 'center' }}><input type="checkbox" checked disabled /> Okuma: projeler, adımlar, çıktılar, onayımı bekleyenler</label>
          <label style={{ display: 'flex', gap: 6, alignItems: 'center' }}><input id="pt-write" type="checkbox" checked={write} onChange={(e) => setWrite(e.target.checked)} />
            Yazma: proje/Case açma ve plan taslağına adım ekleme (onay ve aktarım yapılamaz)</label>
        </div>
        <div className="pj-field"><label htmlFor="pt-days">Geçerlilik (gün)</label>
          <input id="pt-days" className="ui-input" type="number" min={1} max={365} value={days} onChange={(e) => setDays(e.target.value)} /></div>
      </div>
    </Modal>
  );
}

function ShowToken({ data, onClose }) {
  const copy = (text) => navigator.clipboard?.writeText(text).then(() => toast.success('Kopyalandı.'), () => toast.error('Kopyalanamadı; elle seçin.'));
  const claude = `claude mcp add --transport http recorion ${data.server_url} --header "Authorization: Bearer ${data.token}"`;
  const cursor = JSON.stringify({ mcpServers: { recorion: { url: data.server_url, headers: { Authorization: `Bearer ${data.token}` } } } }, null, 2);
  return (
    <Modal open onClose={onClose} title={`${data.name} · anahtar`} size="lg"
      footer={<><Button variant="secondary" onClick={() => copy(data.token)}>Anahtarı kopyala</Button><Button onClick={onClose}>Kaydettim, kapat</Button></>}>
      <p className="ui-text-danger">Bu anahtar bir daha gösterilmez. Kaybolursa iptal edip yenisini oluşturun.</p>
      <pre aria-label="Erişim anahtarı" className="ig-code">{data.token}</pre>
      <p className="pj-hint">Claude Code:</p>
      <pre className="ig-code" aria-label="Claude Code komutu">{claude}</pre>
      <p className="pj-hint">Cursor (.cursor/mcp.json) veya üstbilgi destekleyen diğer MCP istemcileri:</p>
      <pre className="ig-code">{cursor}</pre>
      <p className="pj-hint">Kendi sisteminiz: {data.server_url} adresine MCP (JSON-RPC) isteği, <code className="ig-inline">Authorization: Bearer …</code> üstbilgisiyle.</p>
    </Modal>
  );
}
