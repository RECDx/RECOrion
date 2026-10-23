import React, { useCallback, useEffect, useState } from 'react';
import { Plug, Plus, RefreshCw, Save, ShieldCheck } from 'lucide-react';
import { api } from '../../api';
import { Badge, Button, Card, EmptyState, Modal } from '../../ui/components';
import { confirmDialog, toast } from '../../ui/feedback';
import '../projects/projects.css';

const STATUS = { EXECUTED: ['Çalıştı', 'success'], PENDING_APPROVAL: ['Onay bekliyor', 'warning'], REJECTED: ['Reddedildi', 'neutral'],
  FAILED: ['Hata', 'danger'], DENIED: ['Yetkisiz', 'danger'] };
const fmt = (d) => (d ? new Date(d).toLocaleString('tr-TR', { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' }) : '');

/** Entegrasyonlar (ADIM 10.1): dış sistem bağlantıları, AI personel araç yetkileri, araç çağrı kaydı. */
export default function IntegrationsPanel({ tenantId }) {
  const [catalog, setCatalog] = useState(null);
  const [conns, setConns] = useState(null);
  const [calls, setCalls] = useState([]);
  const [agents, setAgents] = useState([]);
  const [editing, setEditing] = useState(null);
  const [open, setOpen] = useState(null);
  const load = useCallback(() => Promise.all([
    api.getConnectors().then(setCatalog), api.getIntegrations(tenantId).then(setConns), api.getToolCalls(tenantId).then(setCalls),
    api.getCompanyAIAgents(tenantId).then((a) => setAgents(Array.isArray(a) ? a : a.agents || [])),
  ]).catch((e) => toast.error(e.message)), [tenantId]);
  useEffect(() => { if (tenantId) load(); }, [tenantId, load]);

  if (!catalog || !conns) return <p className="pj-hint">Yükleniyor…</p>;
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

  return (
    <div className="pj-steps">
      <Card title="Entegrasyonlar" subtitle="AI personelin dış sistemleri (ERP, mesajlaşma, iş takibi, kod deposu) kullanması. Okumalar anında; yazma işlemleri her zaman insan onayından geçer ve her çağrı kaydedilir."
        actions={<Button icon={Plus} disabled={!catalog.vault_ready} onClick={() => setEditing({})}>Bağlantı ekle</Button>}>
        {!catalog.vault_ready && <p className="ui-text-danger">Kimlik kasası yapılandırılmamış; bağlantı eklenemez. RECDx ile iletişime geçin.</p>}
        {conns.length === 0 ? <EmptyState icon={Plug} title="Henüz bağlantı yok" description="Bağlantı ekleyip AI personele araç yetkisi verin." /> : (
          <ul className="pj-list">
            {conns.map((c) => (
              <li key={c.id} style={{ flexWrap: 'wrap' }}>
                <span><strong>{c.name}</strong> <Badge tone="neutral">{c.connector_title}</Badge><br />
                  <small className="pj-hint">{c.last_test_at ? `Son deneme ${fmt(c.last_test_at)}: ${c.last_test_ok ? 'başarılı' : c.last_error || 'başarısız'}` : 'Henüz denenmedi'}</small></span>
                <Badge tone={c.status === 'ACTIVE' ? 'success' : 'neutral'}>{c.status === 'ACTIVE' ? 'Etkin' : 'Devre dışı'}</Badge>
                <Button size="sm" variant="secondary" icon={RefreshCw} onClick={() => test(c)}>Dene</Button>
                <Button size="sm" variant="secondary" onClick={() => setEditing(c)}>Düzenle</Button>
                <Button size="sm" variant="ghost" onClick={() => toggle(c)}>{c.status === 'ACTIVE' ? 'Devre dışı bırak' : 'Etkinleştir'}</Button>
                <Button size="sm" icon={ShieldCheck} onClick={() => setOpen(open === c.id ? null : c.id)}>Araçlar ve yetkiler</Button>
                {open === c.id && <div style={{ flexBasis: '100%' }}><GrantsEditor tenantId={tenantId} conn={c} agents={agents} onSaved={load} /></div>}
              </li>
            ))}
          </ul>
        )}
      </Card>

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
      {editing && <ConnectionModal tenantId={tenantId} catalog={catalog.connectors} conn={editing.id ? editing : null}
        onClose={() => setEditing(null)} onSaved={() => { setEditing(null); load(); }} />}
    </div>
  );
}

function ConnectionModal({ tenantId, catalog, conn, onClose, onSaved }) {
  const [code, setCode] = useState(conn?.connector || catalog[0]?.code);
  const [name, setName] = useState(conn?.name || '');
  const [config, setConfig] = useState(conn?.config || {});
  const [secrets, setSecrets] = useState({});
  const [busy, setBusy] = useState(false);
  const connector = catalog.find((c) => c.code === code);
  const save = async () => {
    setBusy(true);
    try {
      if (conn) await api.updateIntegration(tenantId, conn.id, { name, config, secrets });
      else await api.createIntegration(tenantId, { connector: code, name, config, secrets });
      toast.success(conn ? 'Bağlantı güncellendi.' : 'Bağlantı eklendi. Şimdi deneyip AI personele araç yetkisi verin.');
      onSaved();
    } catch (e) { toast.error(e.message); } finally { setBusy(false); }
  };
  return (
    <Modal open onClose={onClose} title={conn ? `${conn.name} · düzenle` : 'Bağlantı ekle'} size="md"
      footer={<><Button variant="secondary" onClick={onClose}>Vazgeç</Button><Button icon={Save} disabled={busy || name.trim().length < 2} onClick={save}>{busy ? 'Kaydediliyor…' : 'Kaydet'}</Button></>}>
      <div className="pj-form">
        {!conn && (
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
        {connector?.config_fields.map((f) => (
          <div className="pj-field full" key={f.key}>
            <label htmlFor={`ig-c-${f.key}`}>{f.label}{f.required ? ' *' : ''}</label>
            <input id={`ig-c-${f.key}`} className="ui-input" value={config[f.key] || ''} placeholder={f.placeholder}
              onChange={(e) => setConfig((c) => ({ ...c, [f.key]: e.target.value }))} />
            {f.help && <p className="pj-hint">{f.help}</p>}
          </div>
        ))}
        {connector?.secret_fields.map((f) => (
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
