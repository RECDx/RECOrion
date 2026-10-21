import React, { useCallback, useEffect, useState } from 'react';
import { Brain, ShieldCheck } from 'lucide-react';
import { api } from '../../api';
import { Button, Card, EmptyState } from '../../ui/components';
import { toast } from '../../ui/feedback';
import ChatPanel from './ChatPanel';
import MemoryApprovalQueue from '../docs/MemoryApprovalQueue';
import { fmtPrecise } from './format';
import './ai.css';

const SUGGESTIONS = [
  'Şirketimizin mevcut AI personel yapısını değerlendirir misin?',
  'Hangi departmanlarda eksik ünvan görüyorsun?',
  'Bu ay öncelik vermemiz gereken işleri planlayalım.',
];

/**
 * Beyin AI: şirketin organizatör yapay zekası. Manifesto, departman, ünvan, AI personel ve kurum hafızasını
 * bilerek yanıt verir. Konuşmalar şirket içeriğidir: RECDx yöneticileri başka şirketin Beyin AI'sını açamaz (KVKK).
 */
export default function BrainPanel({ tenantId, currentUser, canManage }) {
  const [settings, setSettings] = useState(null);
  const [choice, setChoice] = useState('');
  const [saving, setSaving] = useState(false);
  const contentBlocked = currentUser?.tenant_id && String(currentUser.tenant_id) !== String(tenantId);

  useEffect(() => {
    api.getBrainSettings(tenantId)
      .then((s) => { setSettings(s); setChoice(s.brain_model_code || ''); })
      .catch((e) => toast.error(e.message));
  }, [tenantId]);

  const save = async () => {
    setSaving(true);
    try {
      const s = await api.updateBrainSettings(tenantId, choice);
      setSettings(s);
      toast.success('Beyin AI modeli kaydedildi.');
    } catch (e) {
      toast.error(e.message);
    } finally {
      setSaving(false);
    }
  };

  const loadHistory = useCallback(() => api.getBrainHistory(tenantId), [tenantId]);
  const send = useCallback((content) => api.sendBrainMessage(tenantId, content), [tenantId]);
  const options = settings?.available_models || [];
  const defaultAvailable = options.some((m) => m.model_code === settings?.platform_default);

  return (
    <div className="ai-stack">
      <Card
        title="Beyin AI Modeli"
        subtitle="Beyin AI, şirketinizin organizatör yapay zekasıdır. Paketinizin izin verdiği modellerden birini seçebilirsiniz."
        actions={canManage && <Button size="sm" onClick={save} disabled={saving || !settings || choice === (settings.brain_model_code || '')}>Kaydet</Button>}
      >
        <div className="ai-field">
          <label htmlFor="brain-model">Model</label>
          <select id="brain-model" className="ui-input" value={choice} disabled={!canManage || !settings} onChange={(e) => setChoice(e.target.value)}>
            <option value="">
              Platform varsayılanı{settings?.platform_default ? ` (${settings.platform_default}${defaultAvailable ? '' : ' — paketinizde yok, paketteki ilk uygun model kullanılır'})` : ''}
            </option>
            {options.map((m) => (
              <option key={m.model_code} value={m.model_code}>{m.display_name} ({m.model_code}) · katsayı {fmtPrecise(m.effort_coefficient)}</option>
            ))}
          </select>
          <span className="ai-dim">Katsayı yükseldikçe model daha güçlü ama işlem başına daha çok kredi harcar.</span>
        </div>
      </Card>

      {!contentBlocked && <MemoryApprovalQueue tenantId={tenantId} canManage={canManage} />}

      <Card title="Beyin AI ile konuş" subtitle="Konuşmalarınız yalnızca size görünür. Her yanıt şirketinizin kredisinden düşer.">
        {contentBlocked ? (
          <EmptyState
            icon={ShieldCheck}
            title="KVKK Koruma Modu"
            description="Beyin AI konuşmaları şirket içeriğidir. RECDx yöneticileri müşteri şirketlerin Beyin AI konuşmalarını görüntüleyemez."
          />
        ) : (
          <ChatPanel
            loadHistory={loadHistory}
            send={send}
            icon={Brain}
            emptyTitle="Beyin AI hazır"
            emptyText="Şirketinizin manifestosunu, departmanlarını, AI personelini ve kurum hafızasını bilerek yanıt verir."
            suggestions={SUGGESTIONS}
            placeholder="Beyin AI'ya bir soru sorun… (Enter gönderir, Shift+Enter yeni satır)"
          />
        )}
      </Card>
    </div>
  );
}
