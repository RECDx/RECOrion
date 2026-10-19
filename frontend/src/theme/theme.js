/**
 * Tema yönetimi: 'dark' (varsayılan), 'light' veya 'system'.
 * Tercih localStorage'da saklanır; ilk boyamadan önce index.html içindeki küçük
 * betik aynı mantıkla <html data-theme> değerini ayarlar (yanıp sönmeyi önler).
 */
import { useEffect, useState } from 'react';

const STORAGE_KEY = 'recorion_theme';
export const THEMES = ['dark', 'light', 'system'];

export function getThemePreference() {
  try {
    const v = localStorage.getItem(STORAGE_KEY);
    return THEMES.includes(v) ? v : 'dark';
  } catch {
    return 'dark';
  }
}

function resolve(pref) {
  if (pref !== 'system') return pref;
  return window.matchMedia?.('(prefers-color-scheme: light)').matches ? 'light' : 'dark';
}

export function applyTheme(pref, { animate = false } = {}) {
  const root = document.documentElement;
  if (animate) {
    root.classList.add('theme-transition');
    window.setTimeout(() => root.classList.remove('theme-transition'), 300);
  }
  root.setAttribute('data-theme', resolve(pref));
  window.dispatchEvent(new CustomEvent('recorion:theme', { detail: pref }));
}

export function setThemePreference(pref) {
  try {
    localStorage.setItem(STORAGE_KEY, pref);
  } catch {
    /* depolama erişilemiyor: tercih yalnızca bu oturumda geçerli */
  }
  applyTheme(pref, { animate: true });
}

/** Uygulama açılışında çağrılır: sistem teması değişince 'system' tercihini izler. */
export function initTheme() {
  applyTheme(getThemePreference());
  window.matchMedia?.('(prefers-color-scheme: light)').addEventListener?.('change', () => {
    if (getThemePreference() === 'system') applyTheme('system');
  });
}

export function useThemePreference() {
  const [pref, setPref] = useState(getThemePreference);
  useEffect(() => {
    const onChange = (e) => setPref(e.detail);
    window.addEventListener('recorion:theme', onChange);
    return () => window.removeEventListener('recorion:theme', onChange);
  }, []);
  return [pref, setThemePreference];
}
