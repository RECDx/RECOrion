import React from 'react';
import { Monitor, Moon, Sun } from 'lucide-react';
import { useThemePreference } from '../theme/theme';

const OPTIONS = [
  { value: 'dark', label: 'Koyu', Icon: Moon },
  { value: 'light', label: 'Açık', Icon: Sun },
  { value: 'system', label: 'Sistem', Icon: Monitor },
];

/**
 * Tema seçici. compact=true: tek düğme, tıklandıkça Koyu → Açık → Sistem.
 * Varsayılan: üç seçenekli segment kontrol.
 */
export default function ThemeToggle({ compact = false, className = '' }) {
  const [pref, setPref] = useThemePreference();

  if (compact) {
    const idx = OPTIONS.findIndex((o) => o.value === pref);
    const current = OPTIONS[idx] || OPTIONS[0];
    const next = OPTIONS[(idx + 1) % OPTIONS.length];
    return (
      <button
        type="button"
        className={`ui-icon-btn ui-theme-compact ${className}`}
        onClick={() => setPref(next.value)}
        title={`Tema: ${current.label} (tıklayın: ${next.label})`}
        aria-label={`Tema: ${current.label}. ${next.label} temaya geç`}
      >
        <current.Icon size={16} />
      </button>
    );
  }

  return (
    <div className={`ui-segmented ${className}`} role="radiogroup" aria-label="Tema seçimi">
      {OPTIONS.map(({ value, label, Icon }) => (
        <button
          key={value}
          type="button"
          role="radio"
          aria-checked={pref === value}
          className={`ui-segmented-item ${pref === value ? 'active' : ''}`}
          onClick={() => setPref(value)}
          title={`${label} tema`}
        >
          <Icon size={14} />
          <span className="ui-segmented-label">{label}</span>
        </button>
      ))}
    </div>
  );
}
