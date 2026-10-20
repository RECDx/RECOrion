import React, { useState } from 'react';
import { KeyRound, CheckCircle2 } from 'lucide-react';
import { api } from '../api';
import { Button, Card } from '../ui/components';
import ThemeToggle from '../ui/ThemeToggle';

function tokenFromHash() {
  const query = (window.location.hash.split('?')[1] || '');
  return new URLSearchParams(query).get('token') || '';
}

/** E-postadaki tek kullanımlık bağlantıyla açılan şifre belirleme / sıfırlama sayfası. */
export default function ResetPassword({ onDone }) {
  const [token] = useState(tokenFromHash);
  const [password, setPassword] = useState('');
  const [confirm, setConfirm] = useState('');
  const [error, setError] = useState('');
  const [saving, setSaving] = useState(false);
  const [doneEmail, setDoneEmail] = useState('');

  const submit = async (e) => {
    e.preventDefault();
    setError('');
    if (password.length < 8) return setError('Şifre en az 8 karakter olmalıdır.');
    if (password !== confirm) return setError('Şifreler birbiriyle aynı değil.');
    setSaving(true);
    try {
      const res = await api.confirmPasswordReset(token, password);
      setDoneEmail(res.email || '');
    } catch (err) {
      setError(err.message || 'Şifre belirlenemedi.');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div style={{ minHeight: '100dvh', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 16 }}>
      <div style={{ position: 'fixed', top: 16, right: 16 }}><ThemeToggle compact /></div>
      <Card style={{ width: 'min(100%, 420px)' }} title={doneEmail ? 'Şifreniz belirlendi' : 'Şifrenizi belirleyin'}
            subtitle={doneEmail ? `${doneEmail} hesabı için yeni şifreniz kaydedildi.` : 'RECOrion hesabınız için yeni bir şifre oluşturun.'}>
        {doneEmail ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 16, alignItems: 'flex-start' }}>
            <CheckCircle2 size={36} color="#10b981" />
            <Button onClick={onDone}>Giriş Sayfasına Git</Button>
          </div>
        ) : !token ? (
          <p style={{ color: 'var(--text-muted)' }}>Bağlantı eksik veya hatalı. Giriş ekranındaki "Şifremi unuttum" ile yeni bağlantı isteyebilirsiniz.</p>
        ) : (
          <form onSubmit={submit} style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            <label style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-muted)' }}>
              Yeni şifre
              <input className="ui-input" type="password" autoComplete="new-password" value={password}
                     onChange={(e) => setPassword(e.target.value)} placeholder="En az 8 karakter" style={{ marginTop: 6 }} />
            </label>
            <label style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-muted)' }}>
              Yeni şifre (tekrar)
              <input className="ui-input" type="password" autoComplete="new-password" value={confirm}
                     onChange={(e) => setConfirm(e.target.value)} style={{ marginTop: 6 }} />
            </label>
            {error && <div className="ui-text-danger" style={{ fontSize: '0.85rem' }}>{error}</div>}
            <Button type="submit" icon={KeyRound} disabled={saving}>{saving ? 'Kaydediliyor…' : 'Şifremi Kaydet'}</Button>
          </form>
        )}
      </Card>
    </div>
  );
}
