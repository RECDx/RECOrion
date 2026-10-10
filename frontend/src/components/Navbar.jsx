import React, { useState } from 'react';
import { 
  Sparkles, 
  Activity, 
  Database, 
  Cpu, 
  Server, 
  ShieldCheck, 
  Layers,
  ChevronDown
} from 'lucide-react';
import AdminLeadsModal from './AdminLeadsModal';

export default function Navbar({ health, tenant, selectedModel, models, onSelectModel, onGoToOfficialSite, currentUser, onGoToAdminConsole, onLogout }) {
  const isHealthy = health?.status === 'healthy';
  const [isLeadsModalOpen, setIsLeadsModalOpen] = useState(false);

  return (
    <header className="top-navbar">
      {/* Brand & Logo */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
        <div style={{
          width: '36px',
          height: '36px',
          borderRadius: '10px',
          background: 'linear-gradient(135deg, #6366f1 0%, #06b6d4 100%)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          boxShadow: '0 0 15px rgba(99, 102, 241, 0.5)'
        }}>
          <Sparkles size={20} color="#ffffff" />
        </div>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ fontWeight: '800', fontSize: '1.15rem', letterSpacing: '-0.02em' }}>
              REC<span className="brand-gradient-text">Orion</span>
            </span>
            <span className="badge badge-ai" style={{ fontSize: '0.65rem' }}>v2.4 OTONOM</span>
          </div>
          <p style={{ fontSize: '0.72rem', color: 'var(--text-dim)', margin: 0 }}>
            Çoklu Ajan ve Kolektif Hafıza Platformu
          </p>
        </div>
      </div>

      {/* Center: Tenant & Infrastructure Indicators */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '20px' }}>
        {/* Active Company / Tenant */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          padding: '6px 14px',
          borderRadius: '20px',
          background: 'rgba(255, 255, 255, 0.04)',
          border: '1px solid var(--border-subtle)',
          fontSize: '0.825rem'
        }}>
          <Layers size={14} color="#06b6d4" />
          <span style={{ color: 'var(--text-muted)' }}>Kurum:</span>
          <span style={{ fontWeight: '600', color: '#f8fafc' }}>
            {tenant?.name || 'RECOrion Teknoloji A.Ş.'}
          </span>
          <span className="badge" style={{ background: 'rgba(6, 182, 212, 0.12)', color: '#22d3ee', fontSize: '0.65rem' }}>
            NACE 62.01
          </span>
        </div>

        {/* Live Cluster Health Status */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', fontSize: '0.775rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '5px', color: 'var(--text-muted)' }} title="Dark DB: PostgreSQL 16">
            <Database size={13} color="#60a5fa" />
            <span>Postgres</span>
            <span style={{ width: '7px', height: '7px', borderRadius: '50%', background: health?.services?.postgres === 'healthy' ? '#10b981' : '#f43f5e' }}></span>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '5px', color: 'var(--text-muted)' }} title="2-Tier Vektör: Qdrant">
            <Cpu size={13} color="#a855f7" />
            <span>Qdrant</span>
            <span style={{ width: '7px', height: '7px', borderRadius: '50%', background: health?.services?.qdrant === 'healthy' ? '#10b981' : '#f43f5e' }}></span>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '5px', color: 'var(--text-muted)' }} title="Stream & Cache: Redis 7">
            <Server size={13} color="#f59e0b" />
            <span>Redis</span>
            <span style={{ width: '7px', height: '7px', borderRadius: '50%', background: health?.services?.redis === 'healthy' ? '#10b981' : '#f43f5e' }}></span>
          </div>
        </div>
      </div>

      {/* Right: Active EVREN Model Selector & User Profile */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
        {/* EVREN Model Dropdown */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>Aktif Model:</span>
          <select 
            value={selectedModel}
            onChange={(e) => onSelectModel(e.target.value)}
            style={{
              background: 'rgba(17, 24, 39, 0.8)',
              color: '#38bdf8',
              border: '1px solid rgba(6, 182, 212, 0.35)',
              borderRadius: '8px',
              padding: '5px 10px',
              fontSize: '0.8rem',
              fontWeight: '600',
              fontFamily: 'var(--font-mono)',
              cursor: 'pointer',
              outline: 'none'
            }}
          >
            {models?.map((m) => (
              <option key={m.id || m.model_code} value={m.model_code}>
                {m.model_code} ({m.model_type})
              </option>
            ))}
          </select>
        </div>

        {/* Official Web & Paketler Butonu */}
        {onGoToOfficialSite && (
          <button
            onClick={onGoToOfficialSite}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              padding: '6px 12px',
              borderRadius: '8px',
              background: 'linear-gradient(135deg, rgba(99, 102, 241, 0.15) 0%, rgba(6, 182, 212, 0.15) 100%)',
              border: '1px solid rgba(99, 102, 241, 0.35)',
              color: '#a5b4fc',
              fontSize: '0.775rem',
              fontWeight: '600',
              cursor: 'pointer',
              transition: 'all 0.2s ease'
            }}
            title="Resmi Web Sitesi ve Paketler Sayfasına Dön"
          >
            🌐 Resmi Web & Paketler
          </button>
        )}

        {/* Super Admin Console Button */}
        {currentUser?.role === 'SUPER_ADMIN' && (
          <button
            onClick={onGoToAdminConsole || (() => setIsLeadsModalOpen(true))}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              padding: '6px 12px',
              borderRadius: '8px',
              background: 'linear-gradient(135deg, rgba(245, 158, 11, 0.25) 0%, rgba(217, 119, 6, 0.25) 100%)',
              border: '1px solid rgba(245, 158, 11, 0.6)',
              color: '#fbbf24',
              fontSize: '0.775rem',
              fontWeight: '700',
              cursor: 'pointer',
              transition: 'all 0.2s ease'
            }}
            title="RECDx Platform Süper Admin Yönetim Konsoluna Git"
          >
            👑 Süper Admin Konsolu
          </button>
        )}

        {/* Human Admin Profile */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '10px',
          padding: '4px 10px',
          borderRadius: '8px',
          background: 'rgba(255, 255, 255, 0.03)',
          border: '1px solid var(--border-subtle)'
        }}>
          <div style={{
            width: '28px',
            height: '28px',
            borderRadius: '50%',
            background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: '0.8rem',
            fontWeight: '700',
            color: '#ffffff'
          }}>
            {currentUser?.display_name?.charAt(0) || 'C'}
          </div>
          <div style={{ textAlign: 'left', lineHeight: 1.2 }}>
            <div style={{ fontSize: '0.8rem', fontWeight: '600' }}>
              {currentUser?.display_name || 'Cüneyt Admin'}
            </div>
            <div style={{ fontSize: '0.675rem', color: currentUser?.role === 'SUPER_ADMIN' ? '#38bdf8' : 'var(--text-muted)' }}>
              {currentUser?.role === 'SUPER_ADMIN' ? '👑 RECDx Süper Admin' : (currentUser?.role || 'Müşteri Şirket Yöneticisi')}
            </div>
          </div>
        </div>

        {/* Logout Button */}
        {onLogout && (
          <button
            onClick={onLogout}
            style={{
              background: 'rgba(239, 68, 68, 0.1)',
              border: '1px solid rgba(239, 68, 68, 0.3)',
              color: '#f87171',
              borderRadius: '8px',
              padding: '6px 10px',
              fontSize: '0.75rem',
              fontWeight: '600',
              cursor: 'pointer'
            }}
            title="Oturumu Kapat"
          >
            Çıkış
          </button>
        )}
      </div>

      {/* Admin Leads & Odoo Approval Modal */}
      <AdminLeadsModal 
        isOpen={isLeadsModalOpen} 
        onClose={() => setIsLeadsModalOpen(false)} 
      />
    </header>
  );
}
