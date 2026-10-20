import React, { useCallback, useEffect, useState } from 'react';
import { Bot, Coins, RefreshCw, Save } from 'lucide-react';
import { api } from '../../api';
import { Badge, Button, Card, Modal } from '../../ui/components';
import { toast } from '../../ui/feedback';
import ChatPanel from './ChatPanel';
import CreditsPanel from './CreditsPanel';
import { fmtCredits, fmtDate, fmtPrecise, fmtTokens } from './format';
import './ai.css';

/** Süper Admin: amaç bazında platform varsayılan modelleri. */
export function ModelSettingsPanel() {
  const [rows, setRows] = useState([]);
  const [models, setModels] = useState([]);
  const [draft, setDraft] = useState({});
  const [saving, setSaving] = useState(false);

  const load = useCallback(async () => {
    try {
      const [settings, all] = await Promise.all([api.getModelSettings(), api.getModels()]);
      setRows(settings);
      setModels(all.filter((m) => m.status === 'ACTIVE'));
      setDraft(Object.fromEntries(settings.map((s) => [s.key, s.model_code || ''])));
    } catch (e) {
      toast.error(e.message);
    }
  }, []);
  useEffect(() => { load(); }, [load]);

  const changed = rows.filter((r) => (draft[r.key] || '') !== (r.model_code || '') && draft[r.key]);
  const save = async () => {
    setSaving(true);
    try {
      setRows(await api.updateModelSettings(Object.fromEntries(changed.map((r) => [r.key, draft[r.key]]))));
      toast.success('Model ayarları kaydedildi.');
    } catch (e) {
      toast.error(e.message);
    } finally {
      setSaving(false);
    }
  };

  return (
    <Card
      title="Platform Varsayılan Modelleri"
      subtitle="Bir işlem için model seçilmemişse bu modeller kullanılır. Müşterinin paketinde olmayan bir model seçilirse paketindeki ilk uygun sohbet modeline düşülür."
      actions={<Button size="sm" icon={Save} onClick={save} disabled={saving || changed.length === 0}>Kaydet</Button>}
    >
      <div className="ai-form-grid">
        {rows.map((r) => (
          <div className="ai-field" key={r.key}>
            <label htmlFor={`ms-${r.key}`}>{r.label}</label>
            <select id={`ms-${r.key}`} className="ui-input" value={draft[r.key] || ''} onChange={(e) => setDraft((d) => ({ ...d, [r.key]: e.target.value }))}>
              {!draft[r.key] && <option value="">Seçin…</option>}
              {models.filter((m) => r.model_types.includes(m.model_type)).map((m) => (
                <option key={m.model_code} value={m.model_code}>{m.display_name} ({m.model_code}) · katsayı {fmtPrecise(m.effort_coefficient)}</option>
              ))}
            </select>
          </div>
        ))}
      </div>
    </Card>
  );
}

/** Süper Admin: bu dönemin platform kullanımı ve EVREN kredisi. */
export function PlatformUsagePanel() {
  const [data, setData] = useState(null);
  const load = useCallback(() => api.getPlatformLLMUsage().then(setData).catch((e) => toast.error(e.message)), []);
  useEffect(() => { load(); }, [load]);
  if (!data) return null;
  const total = data.by_tenant.reduce((a, r) => ({
    calls: a.calls + r.calls, credits: a.credits + (r.is_platform ? 0 : r.credits), evren: a.evren + r.evren_credits,
  }), { calls: 0, credits: 0, evren: 0 });
  return (
    <Card
      title={`Yapay Zeka Kullanımı (${data.period})`}
      subtitle="Müşteri kredisi RECOrion formülüyle, EVREN maliyeti EVREN'in bildirdiği kredi (CR) ile tutulur."
      actions={<Button variant="ghost" size="sm" icon={RefreshCw} onClick={load}>Yenile</Button>}
    >
      <div className="ai-stack">
        <div className="ai-stats">
          <div className="ai-stat"><div className="ai-stat-label">İşlem</div><div className="ai-stat-value">{fmtCredits(total.calls)}</div><div className="ai-stat-note">{data.failed_calls} başarısız</div></div>
          <div className="ai-stat"><div className="ai-stat-label">Müşteri kredisi</div><div className="ai-stat-value">{fmtCredits(total.credits)}</div><div className="ai-stat-note">RECDx hariç tüm şirketler dahil</div></div>
          <div className="ai-stat"><div className="ai-stat-label">EVREN maliyeti</div><div className="ai-stat-value">{fmtPrecise(total.evren)} CR</div><div className="ai-stat-note">Çağrı başına ayrılan</div></div>
          <div className="ai-stat"><div className="ai-stat-label">EVREN kalan kredi</div><div className="ai-stat-value">{data.evren_balance ? `${fmtCredits(data.evren_balance.credits_remaining)} CR` : '—'}</div><div className="ai-stat-note">{data.evren_balance ? fmtDate(data.evren_balance.as_of) : 'Henüz çağrı yok'}</div></div>
        </div>
        <div className="ai-breakdowns" style={{ gridTemplateColumns: 'repeat(2, minmax(0, 1fr))' }}>
          <Card title="Şirketlere göre">
            <ul className="ai-list">{data.by_tenant.slice(0, 10).map((r) => <li key={r.key || 'x'}><span>{r.name}{r.is_platform ? ' (platform)' : ''}</span><span>{fmtCredits(r.credits)} kredi · {r.calls} işlem</span></li>)}</ul>
          </Card>
          <Card title="Modellere göre">
            <ul className="ai-list">{data.by_model.slice(0, 10).map((r) => <li key={r.key || 'x'}><span>{r.key}</span><span>{fmtTokens(r.tokens_in + r.tokens_out)} token · {r.calls} işlem</span></li>)}</ul>
          </Card>
        </div>
      </div>
    </Card>
  );
}

/** Süper Admin: şirkete ek kredi yükleme ve kredi durumu. */
export function TenantCreditsModal({ tenant, onClose }) {
  const [amount, setAmount] = useState('');
  const [note, setNote] = useState('');
  const [busy, setBusy] = useState(false);
  const [refreshKey, setRefreshKey] = useState(0);
  const isHQ = tenant?.slug === 'recdx_hq';

  const submit = async () => {
    const value = Number(String(amount).replace(',', '.'));
    if (!(value > 0)) { toast.error('Geçerli bir kredi miktarı girin.'); return; }
    setBusy(true);
    try {
      await api.topupCredits(tenant.id, { amount: value, note: note.trim() || null });
      toast.success(`${tenant.name} şirketine ${fmtCredits(value)} kredi yüklendi.`);
      setAmount(''); setNote(''); setRefreshKey((k) => k + 1);
    } catch (e) {
      toast.error(e.message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <Modal open={!!tenant} onClose={onClose} size="lg" title={`${tenant?.name || ''} · Kredi`}
      footer={!isHQ && <Button icon={Coins} onClick={submit} disabled={busy || !amount}>Kredi Yükle</Button>}>
      {tenant && (
        <div className="ai-stack">
          <CreditsPanel tenantId={tenant.id} compact refreshKey={refreshKey} />
          {!isHQ && (
            <div className="ai-form-grid">
              <div className="ai-field">
                <label htmlFor="topup-amount">Ek kredi</label>
                <input id="topup-amount" className="ui-input" inputMode="decimal" value={amount} onChange={(e) => setAmount(e.target.value)} placeholder="Örn. 5000" />
                <span className="ai-dim">Ek krediler ay sonunda silinmez, sonraki aylara devreder.</span>
              </div>
              <div className="ai-field">
                <label htmlFor="topup-note">Açıklama</label>
                <input id="topup-note" className="ui-input" maxLength={200} value={note} onChange={(e) => setNote(e.target.value)} placeholder="Örn. Ekim kampanyası, fatura no…" />
              </div>
            </div>
          )}
        </div>
      )}
    </Modal>
  );
}

const ASSISTANT_SUGGESTIONS = [
  'Bu ay en çok kredi harcayan şirketler hangileri?',
  'Paket süresi yaklaşan müşteriler var mı?',
  'Bekleyen başvuruları özetler misin?',
];

/** Süper Yönetici asistanı: yalnızca yönetim ve toplu veriyle çalışır (KVKK). */
export function PlatformAssistantPanel() {
  const loadHistory = useCallback(() => api.getAssistantHistory(), []);
  const send = useCallback((content) => api.sendAssistantMessage(content), []);
  return (
    <Card
      title="Süper Yönetici Asistanı"
      subtitle="Müşteriler, paketler, başvurular ve kredi kullanımı hakkında soru sorun. KVKK gereği müşteri içeriklerine (proje, sohbet, hafıza, doküman) erişmez."
      actions={<Badge tone="info">Platform kullanımı · kredi düşülmez</Badge>}
    >
      <ChatPanel
        loadHistory={loadHistory}
        send={send}
        icon={Bot}
        emptyTitle="Asistan hazır"
        emptyText="Platformun güncel yönetim verilerini kullanarak yanıt verir."
        suggestions={ASSISTANT_SUGGESTIONS}
        placeholder="Asistana bir soru sorun… (Enter gönderir)"
      />
    </Card>
  );
}

