import React, { useCallback, useEffect, useState } from 'react';
import { KeyRound, LogIn, LogOut, Plug, Plus, RefreshCw, Save, ShieldCheck, Wand2 } from 'lucide-react';
import { api } from '../../api';
import { Badge, Button, Card, EmptyState, Modal } from '../../ui/components';
import { confirmDialog, toast } from '../../ui/feedback';
import '../projects/projects.css';
import './integrations.css';
import { CatalogGallery, SetupSteps } from './Catalog';
import MappingStudio from './MappingStudio';
import { TransferAdmin } from './Transfers';
import CompanyRecdxApps from './CompanyRecdxApps';

const STATUS = { EXECUTED: ['Çalıştı', 'success'], PENDING_APPROVAL: ['Onay bekliyor', 'warning'], REJECTED: ['Reddedildi', 'neutral'],
  FAILED: ['Hata', 'danger'], DENIED: ['Yetkisiz', 'danger'] };
const fmt = (d) => (d ? new Date(d).toLocaleString('tr-TR', { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' }) : '');

/** Servisin giriş ekranına gider (ADIM 12.1); dönüşte Entegrasyonlar sekmesi açılır ve sonuç bildirilir. */
export async function startOAuth(tenantId, conn) {
  const r = await api.startIntegrationOAuth(tenantId, conn.id);
  window.location.assign(r.authorize_url);
}

/** OAuth dönüşü (?oauth=ok|error&msg=...): bildirim gösterilir, adres temizlenir. */
function useOAuthReturn() {
  useEffect(() => {
    const q = new URLSearchParams(window.location.search);
    if (!q.get('oauth')) return;
    if (q.get('oauth') === 'ok') toast.success('Giriş tamamlandı; bağlantı hazır. Şimdi AI personele araç yetkisi verin.');
    else toast.error(q.get('msg') || 'Giriş tamamlanamadı.');
    window.history.replaceState(null, '', window.location.pathname + window.location.hash);
  }, []);
}

/** Entegrasyonlar (ADIM 10.1, 12.1): bağlantı kataloğu, dış sistem bağlantıları, AI personel araç yetkileri, araç çağrı kaydı. */
export default function IntegrationsPanel({ tenantId }) {
  const [catalog, setCatalog] = useState(null);
  const [systems, setSystems] = useState(null);
  const [gallery, setGallery] = useState(false);
  const [studio, setStudio] = useState(null);
  const [conns, setConns] = useState(null);
  const [calls, setCalls] = useState([]);
  const [agents, setAgents] = useState([]);
  const [editing, setEditing] = useState(null);
  const [open, setOpen] = useState(null);
  const [token, setToken] = useState(null);
  const load = useCallback(() => Promise.all([
    api.getConnectors().then(setCatalog), api.getIntegrationCatalog().then(setSystems),
    api.getIntegrations(tenantId).then(setConns), api.getToolCalls(tenantId).then(setCalls),
    api.getCompanyAIAgents(tenantId).then((a) => setAgents(Array.isArray(a) ? a : a.agents || [])),
  ]).catch((e) => toast.error(e.message)), [tenantId]);
  useEffect(() => { if (tenantId) load(); }, [tenantId, load]);
  useOAuthReturn();

  if (!catalog || !conns || !systems) return <p className="pj-hint">Yükleniyor…</p>;
  const pick = (entry) => {
    if (entry.method === 'PLANNED') return toast.info(`${entry.title}: ${entry.description || 'planlanıyor.'}`);
    setGallery(false);
    setEditing({ entry });
  };
  const login = async (c) => { try { await startOAuth(tenantId, c); } catch (e) { toast.error(e.message); } };
  const logout = async (c) => {
    if (!(await confirmDialog({ message: `'${c.name}' oturumu kapatılsın mı? AI personel bu bağlantıyı yeniden giriş yapılana kadar kullanamaz.` }))) return;
    try { await api.disconnectIntegrationOAuth(tenantId, c.id); toast.success('Oturum kapatıldı.'); load(); } catch (e) { toast.error(e.message); }
  };
  const test = async (c) => {
    try {
      const r = await api.testIntegration(tenantId, c.id);
      r.ok ? toast.success(r.detail) : toast.error(r.detail);
      load();
    } catch (e) { toast.error(e.message); }
  };
  const toggle = async (c) => {
    const next = c.status === 'ACTIVE' ? 'DISABLED' : 'ACTIVE';
    if (next === 'DISABLED' && !(await confirmDialog({ message: `'${c.name}' devre dışı bırakılsın mı? AI personel bu bağlantının araçlarını kullanamaz.` }))) return;
    try { await api.updateIntegration(tenantId, c.id, { status: next }); load(); } catch (e) { toast.error(e.message); }
  };
  const newToken = async (c) => {
    if (c.agent?.has_token && !(await confirmDialog({ message: 'Yeni ajan anahtarı oluşturulsun mu? Eski anahtar hemen geçersiz olur; sunucudaki ajanın ayarı yenilenmeli.' }))) return;
    try { setToken({ conn: c, ...(await api.newEdgeAgentToken(tenantId, c.id)) }); load(); } catch (e) { toast.error(e.message); }
  };

  return (
    <div className="pj-steps">
      <Card title="Entegrasyonlar" subtitle="AI personelin dış sistemleri (ERP, mesajlaşma, iş takibi, kod deposu) kullanması. Okumalar anında; yazma işlemleri her zaman insan onayından geçer ve her çağrı kaydedilir."
        actions={<Button icon={Plus} disabled={!catalog.vault_ready} onClick={() => setGallery(true)}>Bağlantı ekle</Button>}>
        {!catalog.vault_ready && <p className="ui-text-danger">Kimlik kasası yapılandırılmamış; bağlantı eklenemez. RECDx ile iletişime geçin.</p>}
        {conns.length === 0 ? <EmptyState icon={Plug} title="Henüz bağlantı yok" description="Bağlantı ekleyip AI personele araç yetkisi verin." /> : (
          <ul className="pj-list">
            {conns.map((c) => (
              <li key={c.id} style={{ flexWrap: 'wrap' }}>
                <span><strong>{c.name}</strong> <Badge tone="neutral">{c.connector_title}</Badge>{c.config?.access === 'READ_ONLY' && <> <Badge tone="info">Yalnızca okuma</Badge></>}<br />
                  <small className="pj-hint">{c.last_test_at ? `Son deneme ${fmt(c.last_test_at)}: ${c.last_test_ok ? 'başarılı' : c.last_error || 'başarısız'}` : 'Henüz denenmedi'}</small>
                  {c.agent && <><br /><small className="pj-hint">{c.agent.online
                    ? `Ajan çevrimiçi · ${c.agent.hostname || 'sunucu'} · ${c.agent.templates} izinli şablon`
                    : c.agent.seen_at ? `Ajan çevrimdışı (son görülme ${fmt(c.agent.seen_at)})` : c.agent.has_token ? 'Ajan henüz bağlanmadı' : 'Ajan anahtarı oluşturulmadı'}</small></>}</span>
                <Badge tone={c.status === 'ACTIVE' ? 'success' : 'neutral'}>{c.status === 'ACTIVE' ? 'Etkin' : 'Devre dışı'}</Badge>
                {c.oauth && <Badge tone={c.oauth.connected ? 'success' : 'warning'}>{c.oauth.connected ? 'Giriş yapıldı' : 'Giriş gerekli'}</Badge>}
                {c.oauth && c.status === 'ACTIVE' && <Button size="sm" icon={LogIn} onClick={() => login(c)}>{c.oauth.connected ? 'Yeniden giriş' : 'Giriş yap'}</Button>}
                {c.oauth?.connected && <Button size="sm" variant="ghost" icon={LogOut} onClick={() => logout(c)}>Oturumu kapat</Button>}
                {c.agent && <Badge tone={c.agent.online ? 'success' : 'warning'}>{c.agent.online ? 'Ajan çevrimiçi' : 'Ajan çevrimdışı'}</Badge>}
                <Button size="sm" variant="secondary" icon={RefreshCw} onClick={() => test(c)}>Dene</Button>
                {c.connector === 'edge' && <Button size="sm" variant="secondary" icon={KeyRound} onClick={() => newToken(c)}>Ajan anahtarı</Button>}
                <Button size="sm" variant="secondary" onClick={() => setEditing(c)}>Düzenle</Button>
                <Button size="sm" variant="ghost" onClick={() => toggle(c)}>{c.status === 'ACTIVE' ? 'Devre dışı bırak' : 'Etkinleştir'}</Button>
                <Button size="sm" icon={ShieldCheck} onClick={() => setOpen(open === c.id ? null : c.id)}>Araçlar ve yetkiler</Button>
                {['odoo', 'mcp', 'edge'].includes(c.connector) && <Button size="sm" variant="secondary" icon={Wand2} onClick={() => setStudio(c)}>Eşlemeler</Button>}
                {open === c.id && <div style={{ flexBasis: '100%' }}><GrantsEditor tenantId={tenantId} conn={c} agents={agents} onSaved={load} /></div>}
              </li>
            ))}
          </ul>
        )}
      </Card>

      <CompanyRecdxApps tenantId={tenantId} onChanged={load} />
      <TransferAdmin tenantId={tenantId} />
      <Card title="Araç çağrı kaydı" subtitle="Silinemez kayıt: kim, hangi araç, hangi argümanla, sonuç ve onay.">
        {calls.length === 0 ? <p className="pj-hint">Henüz araç çağrısı yok.</p> : (
          <div className="ui-table-scroll">
            <table className="ui-table">
              <thead><tr><th>Zaman</th><th>Kim</th><th>Bağlantı</th><th>Araç</th><th>Tür</th><th>Durum</th><th>Süre</th><th>Ayrıntı</th></tr></thead>
              <tbody>{calls.map((c) => {
                const [label, tone] = STATUS[c.status] || [c.status, 'neutral'];
                return (
                  <tr key={c.id}>
                    <td data-label="Zaman">{fmt(c.created_at)}</td><td data-label="Kim">{c.actor_name}</td><td data-label="Bağlantı">{c.connection_name || '—'}</td>
                    <td data-label="Araç" style={{ fontFamily: 'var(--font-mono)' }}>{c.tool}</td>
                    <td data-label="Tür">{c.kind === 'WRITE' ? 'Yazma' : 'Okuma'}</td>
                    <td data-label="Durum"><Badge tone={tone}>{label}</Badge></td>
                    <td data-label="Süre">{c.latency_ms != null ? `${c.latency_ms} ms` : '—'}</td>
                    <td data-label="Ayrıntı" style={{ maxWidth: 320, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}
                      title={c.error || JSON.stringify(c.result ?? c.arguments)}>{c.error || JSON.stringify(c.result ?? c.arguments)}</td>
                  </tr>
                );
              })}</tbody>
            </table>
          </div>
        )}
      </Card>
      {studio && <MappingStudio tenantId={tenantId} conn={studio} onClose={() => setStudio(null)} />}
      {gallery && <CatalogGallery tenantId={tenantId} catalog={systems} onClose={() => setGallery(false)} onPick={pick} />}
      {editing && <ConnectionModal tenantId={tenantId} catalog={catalog.connectors} conn={editing.id ? editing : null}
        entry={editing.entry || systems.entries.find((e) => e.code === editing.catalog_code)} redirectUri={systems.redirect_uri}
        onClose={() => setEditing(null)} onSaved={async (saved) => {
          setEditing(null);
          await load();
          if (saved?.oauth && !saved.oauth.connected && saved.status === 'ACTIVE'
            && await confirmDialog({ message: `'${saved.name}' kaydedildi. Şimdi servisin giriş ekranına gidip izin verelim mi?`, confirmText: 'Giriş yap' })) login(saved);
        }} />}
      {token && <AgentTokenModal data={token} onClose={() => setToken(null)} />}
    </div>
  );
}

/** Edge ajan anahtarı (ADIM 10.5): bir kez gösterilir; RECOrion'da yalnızca özeti saklanır. */
function AgentTokenModal({ data, onClose }) {
  const copy = () => navigator.clipboard?.writeText(data.token).then(() => toast.success('Anahtar kopyalandı.'), () => toast.error('Kopyalanamadı; elle seçin.'));
  const origin = window.location.origin.replace(':5173', ':8000');
  return (
    <Modal open onClose={onClose} title={`${data.conn.name} · ajan anahtarı`} size="md"
      footer={<><Button variant="secondary" onClick={copy}>Kopyala</Button><Button onClick={onClose}>Kaydettim, kapat</Button></>}>
      <p className="ui-text-danger">Bu anahtar bir daha gösterilmez. Kaybolursa yeni anahtar oluşturun (eskisi geçersiz olur).</p>
      <pre aria-label="Ajan anahtarı" className="ig-code">{data.token}</pre>
      <p className="pj-hint">Şirket sunucusunda (Logo/Mikro veritabanının yanında) ajanı şu ayarlarla başlatın:</p>
      <pre className="ig-code">{`set RECORION_URL=${origin}\nset RECORION_EDGE_TOKEN=<yukarıdaki anahtar>\npython recorion_edge.py --config edge_config.json`}</pre>
      <p className="pj-hint">Ajan yalnızca dışa bağlanır (sunucunuza port açmanız gerekmez) ve yalnızca templates.json dosyasındaki izinli sorguları çalıştırır.</p>
    </Modal>
  );
}

// MCP kimlik yöntemine göre görünen alanlar (ADIM 12.1)
const MCP_FIELDS = { token: ['token', 'auth_header'], oauth: ['client_id', 'client_secret'], none: [] };
const visible = (code, config, key) => {
  if (code !== 'mcp' || !['token', 'auth_header', 'client_id', 'client_secret'].includes(key)) return true;
  return MCP_FIELDS[config.auth_mode || 'token'].includes(key);
};

function ConnectionModal({ tenantId, catalog, conn, entry, redirectUri, onClose, onSaved }) {
  const [code, setCode] = useState(conn?.connector || entry?.connector || catalog[0]?.code);
  const [name, setName] = useState(conn?.name || entry?.title || '');
  const [config, setConfig] = useState(conn?.config || entry?.preset || {});
  const [secrets, setSecrets] = useState({});
  const [busy, setBusy] = useState(false);
  const connector = catalog.find((c) => c.code === code);
  const save = async () => {
    setBusy(true);
    try {
      const saved = conn ? await api.updateIntegration(tenantId, conn.id, { name, config, secrets })
        : await api.createIntegration(tenantId, { connector: code, name, config, secrets, catalog_code: entry?.code || null });
      toast.success(conn ? 'Bağlantı güncellendi.' : 'Bağlantı eklendi. Şimdi deneyip AI personele araç yetkisi verin.');
      onSaved(saved);
    } catch (e) { toast.error(e.message); } finally { setBusy(false); }
  };
  return (
    <Modal open onClose={onClose} title={conn ? `${conn.name} · düzenle` : 'Bağlantı ekle'} size="md"
      footer={<><Button variant="secondary" onClick={onClose}>Vazgeç</Button><Button icon={Save} disabled={busy || name.trim().length < 2} onClick={save}>{busy ? 'Kaydediliyor…' : 'Kaydet'}</Button></>}>
      <SetupSteps entry={entry} redirectUri={redirectUri} />
      <div className="pj-form">
        {!conn && !entry && (
          <div className="pj-field full">
            <label htmlFor="ig-connector">Sistem</label>
            <select id="ig-connector" className="ui-input" value={code} onChange={(e) => { setCode(e.target.value); setConfig({}); setSecrets({}); }}>
              {catalog.map((c) => <option key={c.code} value={c.code}>{c.title}</option>)}
            </select>
            <p className="pj-hint">{connector?.description}</p>
          </div>
        )}
        <div className="pj-field full">
          <label htmlFor="ig-name">Bağlantı adı</label>
          <input id="ig-name" className="ui-input" value={name} maxLength={120} onChange={(e) => setName(e.target.value)} placeholder={`${connector?.title || ''} (şirket)`} />
        </div>
        {connector?.config_fields.filter((f) => visible(code, config, f.key)).map((f) => (
          <div className="pj-field full" key={f.key}>
            <label htmlFor={`ig-c-${f.key}`}>{f.label}{f.required ? ' *' : ''}</label>
            {f.options?.length ? (
              <select id={`ig-c-${f.key}`} className="ui-input" value={config[f.key] || f.options[0][0]}
                onChange={(e) => setConfig((c) => ({ ...c, [f.key]: e.target.value }))}>
                {f.options.map(([v, label]) => <option key={v} value={v}>{label}</option>)}
              </select>
            ) : (
              <input id={`ig-c-${f.key}`} className="ui-input" value={config[f.key] || ''} placeholder={f.placeholder}
                onChange={(e) => setConfig((c) => ({ ...c, [f.key]: e.target.value }))} />
            )}
            {f.help && <p className="pj-hint">{f.help}</p>}
          </div>
        ))}
        {connector?.secret_fields.filter((f) => visible(code, config, f.key)).map((f) => (
          <div className="pj-field full" key={f.key}>
            <label htmlFor={`ig-s-${f.key}`}>{f.label}{f.required && !conn ? ' *' : ''}</label>
            <input id={`ig-s-${f.key}`} className="ui-input" type="password" autoComplete="new-password" value={secrets[f.key] || ''}
              placeholder={conn?.secrets_set?.[f.key] ? '•••••• (kayıtlı; değiştirmek için yazın)' : f.placeholder}
              onChange={(e) => setSecrets((s) => ({ ...s, [f.key]: e.target.value }))} />
            <p className="pj-hint">{f.help || 'Kimlik kasasında şifreli saklanır; bir daha gösterilmez.'}</p>
          </div>
        ))}
      </div>
    </Modal>
  );
}

function GrantsEditor({ tenantId, conn, agents, onSaved }) {
  const [tools, setTools] = useState(null);
  const [grants, setGrants] = useState(new Set());
  const [busy, setBusy] = useState(false);
  useEffect(() => {
    Promise.all([api.getIntegrationTools(tenantId, conn.id), api.getIntegrationGrants(tenantId, conn.id)])
      .then(([t, g]) => { setTools(t); setGrants(new Set(g.map((x) => `${x.actor_id}|${x.tool}`))); })
      .catch((e) => { toast.error(e.message); setTools([]); });
  }, [tenantId, conn.id]);
  if (!tools) return <p className="pj-hint">Araçlar yükleniyor…</p>;
  const key = (a, t) => `${a}|${t}`;
  const flip = (k) => setGrants((g) => { const n = new Set(g); n.has(k) ? n.delete(k) : n.add(k); return n; });
  const save = async () => {
    setBusy(true);
    try {
      await api.setIntegrationGrants(tenantId, conn.id, [...grants].map((k) => { const [actor_id, tool] = k.split('|'); return { actor_id, tool }; }));
      toast.success('Araç yetkileri kaydedildi.');
      onSaved?.();
    } catch (e) { toast.error(e.message); } finally { setBusy(false); }
  };
  const ai = agents.filter((a) => (a.actor_type || 'AI_AGENT') === 'AI_AGENT');
  return (
    <div style={{ marginTop: 10 }}>
      {ai.length === 0 ? <p className="pj-hint">Şirkette AI personel yok.</p> : (
        <div className="ui-table-scroll">
          <table className="ui-table">
            <thead><tr><th>AI personel</th><th>Tümü</th>{tools.map((t) => <th key={t.name} title={t.description}>{t.name}<br /><small className="pj-hint">{t.kind === 'WRITE' ? 'yazma · onaylı' : 'okuma'}</small></th>)}</tr></thead>
            <tbody>{ai.map((a) => (
              <tr key={a.id}>
                <td data-label="AI personel">{a.display_name}</td>
                <td data-label="Tümü"><input type="checkbox" aria-label={`${a.display_name}: tüm araçlar`} checked={grants.has(key(a.id, '*'))} onChange={() => flip(key(a.id, '*'))} /></td>
                {tools.map((t) => (
                  <td key={t.name} data-label={t.name}>
                    <input type="checkbox" aria-label={`${a.display_name}: ${t.name}`} disabled={grants.has(key(a.id, '*'))}
                      checked={grants.has(key(a.id, '*')) || grants.has(key(a.id, t.name))} onChange={() => flip(key(a.id, t.name))} />
                  </td>
                ))}
              </tr>
            ))}</tbody>
          </table>
        </div>
      )}
      <div className="pj-actions" style={{ marginTop: 8 }}><Button size="sm" icon={Save} disabled={busy} onClick={save}>Yetkileri kaydet</Button></div>
    </div>
  );
}
