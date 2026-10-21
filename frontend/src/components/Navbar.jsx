import React, { useState } from 'react';
import ThemeToggle from '../ui/ThemeToggle';
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

export default function Navbar({ health, tenant, onGoToOfficialSite, currentUser, onGoToAdminConsole, onGoToCompanyAdmin, onLogout }) {
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
      <div className="navbar-center" style={{ display: 'flex', alignItems: 'center', gap: '20px' }}>
        {/* Active Company / Tenant */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          padding: '6px 14px',
          borderRadius: '20px',
          background: 'rgb(var(--rgb-ov) / 0.04)',
          border: '1px solid var(--border-subtle)',
          fontSize: '0.825rem'
        }}>
          <Layers size={14} color="#06b6d4" />
          <span style={{ color: 'var(--text-muted)' }}>Kurum:</span>
          <span style={{ fontWeight: '600', color: 'var(--nt-f8fafc)' }}>
            {tenant?.name || 'RECOrion Teknoloji A.Ş.'}
          </span>
        </div>

        {/* Live Cluster Health Status */}
        <div className="ui-hide-tablet" style={{ display: 'flex', alignItems: 'center', gap: '12px', fontSize: '0.775rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '5px', color: 'var(--text-muted)' }} title="Dark DB: PostgreSQL 16">
            <Database size={13} color="var(--ac-60a5fa)" />
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

      {/* Right: User Profile */}
      <div className="navbar-actions" style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
        <ThemeToggle compact />

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
              color: 'var(--ac-a5b4fc)',
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
              color: 'var(--ac-fbbf24)',
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

        {/* Company Admin Console Button */}
        {(currentUser?.role === 'COMPANY_ADMIN' || currentUser?.role === 'SUPER_ADMIN') && onGoToCompanyAdmin && (
          <button
            onClick={onGoToCompanyAdmin}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              padding: '6px 12px',
              borderRadius: '8px',
              background: 'linear-gradient(135deg, rgba(113, 52, 226, 0.2) 0%, rgba(20, 108, 235, 0.2) 100%)',
              border: '1px solid rgba(113, 52, 226, 0.5)',
              color: 'var(--ac-c084fc)',
              fontSize: '0.775rem',
              fontWeight: '700',
              cursor: 'pointer',
              transition: 'all 0.2s ease'
            }}
            title="Şirket Departmanları ve Organizasyon Yönetim Konsoluna Git"
          >
            🏢 Şirket Yönetimi
          </button>
        )}

        {/* Human Admin Profile */}
        <div className="ui-hide-mobile" style={{
          display: 'flex',
          alignItems: 'center',
          gap: '10px',
          padding: '4px 10px',
          borderRadius: '8px',
          background: 'rgb(var(--rgb-ov) / 0.03)',
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
            <div style={{ fontSize: '0.675rem', color: currentUser?.role === 'SUPER_ADMIN' ? 'var(--ac-38bdf8)' : 'var(--text-muted)' }}>
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
              color: 'var(--ac-f87171)',
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
