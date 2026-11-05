// RECOrion marka logosu (public/brand). Simge: yazısız; Logo: simge + RECOrion yazısı + ORION açılımı. Şeffaf, iki temada da çalışır.
import React from 'react';

export function RecorionMark({ size = 36, title = 'RECOrion', className = '' }) {
  const src = size <= 32 ? '/brand/recorion-mark-64.webp' : size <= 64 ? '/brand/recorion-mark-128.webp' : '/brand/recorion-mark-256.webp';
  return <img src={src} width={size} height={size} alt={title} title={title} className={`rx-mark ${className}`} draggable="false" />;
}

export function RecorionLogo({ height = 48, className = '', alt = 'RECOrion' }) {
  // Tam yazılı logo (ORION açılımı dahil, en/boy ~3:1); 2x ekran için genişliğe göre dosya seçilir
  const w = height * 3;
  const src = w <= 320 ? '/brand/recorion-logo-full-640.webp' : w <= 640 ? '/brand/recorion-logo-full-1280.webp' : '/brand/recorion-logo-full-1980.webp';
  return <img src={src} height={height} style={{ height, width: 'auto' }} alt={alt} className={`rx-logo ${className}`} draggable="false" />;
}
