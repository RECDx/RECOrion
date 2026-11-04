// RECOrion marka logosu (public/brand). Simge: yazısız; Logo: simge + RECOrion yazısı. Şeffaf, iki temada da çalışır.
import React from 'react';

export function RecorionMark({ size = 36, title = 'RECOrion', className = '' }) {
  const src = size <= 32 ? '/brand/recorion-mark-64.webp' : size <= 64 ? '/brand/recorion-mark-128.webp' : '/brand/recorion-mark-256.webp';
  return <img src={src} width={size} height={size} alt={title} title={title} className={`rx-mark ${className}`} draggable="false" />;
}

export function RecorionLogo({ height = 48, className = '', alt = 'RECOrion' }) {
  const src = height <= 100 ? '/brand/recorion-logo-480.webp' : '/brand/recorion-logo-960.webp';
  return <img src={src} height={height} style={{ height, width: 'auto' }} alt={alt} className={`rx-logo ${className}`} draggable="false" />;
}
