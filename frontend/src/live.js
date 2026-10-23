import { useEffect, useRef, useState } from 'react';
import { api } from './api';

/**
 * Proje canlı akışı (Adım 8.2): mesaj, iş akışı olayı ve AI düşünce adımları anında gelir.
 * Kısa ömürlü bilet alınır, WebSocket açılır; kopan bağlantı artan bekleme ile yeniden kurulur.
 * onEvent her olayda çağrılır; dönen durum: 'connecting' | 'live' | 'offline'.
 */
export function useProjectLive(projectId, onEvent) {
  const [status, setStatus] = useState('offline');
  const handler = useRef(onEvent);
  handler.current = onEvent;

  useEffect(() => {
    if (!projectId) return undefined;
    let ws = null;
    let timer = null;
    let stopped = false;
    let attempt = 0;

    const connect = async () => {
      if (stopped) return;
      setStatus('connecting');
      try {
        const { ticket } = await api.getLiveTicket(projectId);
        if (stopped) return;
        const proto = window.location.protocol === 'https:' ? 'wss' : 'ws';
        ws = new WebSocket(`${proto}://${window.location.host}/ws/projects/${projectId}?ticket=${encodeURIComponent(ticket)}`);
        ws.onmessage = (e) => {
          let data;
          try { data = JSON.parse(e.data); } catch { return; }
          if (data.type === 'ready') { attempt = 0; setStatus('live'); }
          if (data.type === 'ready' || data.type === 'ping' || data.type === 'pong') return;
          handler.current?.(data);
        };
        ws.onclose = (e) => {
          ws = null;
          if (stopped) return;
          setStatus('offline');
          // 4403: yetki yok (ekipten çıkarıldı vb.); tekrar denemenin anlamı yok
          if (e.code !== 4403) schedule();
        };
      } catch {
        setStatus('offline');
        schedule();
      }
    };
    const schedule = () => {
      attempt += 1;
      timer = setTimeout(connect, Math.min(30000, 1000 * 2 ** Math.min(attempt, 5)));
    };
    // Sekme arka plandan dönünce bağlantı kopmuşsa hemen yeniden bağlan
    const onVisible = () => {
      if (document.visibilityState === 'visible' && !ws && !stopped) { clearTimeout(timer); attempt = 0; connect(); }
    };
    document.addEventListener('visibilitychange', onVisible);
    connect();
    return () => {
      stopped = true;
      clearTimeout(timer);
      document.removeEventListener('visibilitychange', onVisible);
      if (ws) ws.close();
    };
  }, [projectId]);

  return status;
}

/**
 * Mesaj listesine kimliğe göre ekleme: canlı akış ve gönderim yanıtı aynı mesajı iki kez getirebilir.
 * Zaten olan mesaj yeni alanlarla (ör. kaynak kartları) güncellenir.
 */
export function mergeMessages(list, incoming) {
  const byId = new Map(list.map((m) => [m.id, m]));
  let changed = false;
  for (const m of incoming) {
    if (!m?.id) continue;
    byId.set(m.id, { ...byId.get(m.id), ...m });
    changed = true;
  }
  if (!changed) return list;
  return [...byId.values()].sort((a, b) => String(a.created_at).localeCompare(String(b.created_at)));
}
