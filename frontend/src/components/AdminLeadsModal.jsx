import React, { useState, useEffect } from 'react';
import { X, CheckCircle, Clock, RefreshCw, ShieldCheck, ShoppingCart, Mail, Phone, Building } from 'lucide-react';
import { api } from '../api';

export default function AdminLeadsModal({ isOpen, onClose }) {
  const [leads, setLeads] = useState([]);
  const [loading, setLoading] = useState(false);
  const [processingId, setProcessingId] = useState(null);
  const [feedback, setFeedback] = useState(null);

  const loadLeads = async () => {
    try {
      setLoading(true);
      setFeedback(null);
      const data = await api.getLeads();
      setLeads(data || []);
    } catch (err) {
      console.error("Leads yükleme hatası:", err);
      setFeedback({ type: 'error', text: 'Başvurular yüklenirken hata oluştu: ' + (err.message || '') });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen) {
      loadLeads();
    }
  }, [isOpen]);

  const handleApprove = async (lead) => {
    try {
      setProcessingId(lead.id);
      setFeedback(null);
      const res = await api.approveLead(lead.id);
      setFeedback({
        type: 'success',
        text: `✓ '${lead.company_name}' onaylandı! Odoo siparişi kesinleştirildi ve ${lead.contact_email} adresine kullanıcı adı/şifre içeren aktivasyon maili gönderildi.`
      });
      // Listeyi yenile
      await loadLeads();
    } catch (err) {
      console.error("Onaylama hatası:", err);
      setFeedback({ type: 'error', text: 'Onay işlemi başarısız: ' + (err.message || '') });
    } finally {
      setProcessingId(null);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="modal-backdrop" style={{
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      background: 'rgb(var(--rgb-sf-050810) / 0.85)',
      backdropFilter: 'blur(10px)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 9999,
      padding: '20px'
    }}>
      <div style={{
        background: 'var(--sf-0d131f)',
        border: '1px solid rgba(99, 102, 241, 0.35)',
        borderRadius: '16px',
        width: '100%',
        maxWidth: '960px',
        maxHeight: '90vh',
        display: 'flex',
        flexDirection: 'column',
        boxShadow: '0 25px 60px rgb(var(--rgb-shade) / calc(0.9 * var(--shade-k)))',
        overflow: 'hidden'
      }}>
        {/* Header */}
        <div style={{
          padding: '18px 24px',
          borderBottom: '1px solid rgb(var(--rgb-ov) / 0.08)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          background: 'linear-gradient(90deg, rgba(99, 102, 241, 0.12) 0%, rgba(6, 182, 212, 0.08) 100%)'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <div style={{
              width: '36px',
              height: '36px',
              borderRadius: '10px',
              background: 'linear-gradient(135deg, #f59e0b 0%, #d97706 100%)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#ffffff'
            }}>
              👑
            </div>
            <div>
              <h3 style={{ margin: 0, fontSize: '1.1rem', fontWeight: '700', color: 'var(--nt-f8fafc)' }}>
                RECDx Süper Admin - Müşteri Başvuruları & Odoo Onay Masası
              </h3>
              <p style={{ margin: '2px 0 0 0', fontSize: '0.78rem', color: 'var(--nt-94a3b8)' }}>
                Gelen paket taleplerini inceleyin; ödeme teyidinden sonra satışı onaylayıp müşteriye giriş bilgilerini gönderin.
              </p>
            </div>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <button 
              onClick={loadLeads} 
              disabled={loading}
              title="Yenile"
              style={{
                background: 'rgb(var(--rgb-ov) / 0.06)',
                border: '1px solid rgb(var(--rgb-ov) / 0.15)',
                color: 'var(--nt-cbd5e1)',
                padding: '6px 12px',
                borderRadius: '8px',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                fontSize: '0.8rem'
              }}
            >
              <RefreshCw size={14} className={loading ? 'spin-icon' : ''} />
              {loading ? 'Yükleniyor...' : 'Yenile'}
            </button>
            <button 
              onClick={onClose}
              style={{
                background: 'transparent',
                border: 'none',
                color: 'var(--nt-94a3b8)',
                cursor: 'pointer',
                padding: '6px'
              }}
            >
              <X size={20} />
            </button>
          </div>
        </div>

        {/* Feedback Alert */}
        {feedback && (
          <div style={{
            margin: '16px 24px 0 24px',
            padding: '12px 16px',
            borderRadius: '10px',
            background: feedback.type === 'success' ? 'rgba(16, 185, 129, 0.15)' : 'rgba(239, 68, 68, 0.15)',
            border: feedback.type === 'success' ? '1px solid rgba(16, 185, 129, 0.4)' : '1px solid rgba(239, 68, 68, 0.4)',
            color: feedback.type === 'success' ? 'var(--ac-34d399)' : 'var(--ac-f87171)',
            fontSize: '0.875rem'
          }}>
            {feedback.text}
          </div>
        )}

        {/* Body List */}
        <div style={{ padding: '20px 24px', overflowY: 'auto', flex: 1 }}>
          {leads.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '40px 20px', color: 'var(--nt-64748b)' }}>
              <ShoppingCart size={40} style={{ opacity: 0.3, marginBottom: '12px' }} />
              <p style={{ margin: 0, fontSize: '0.95rem' }}>Henüz bekleyen satın alma veya kiralama başvurusu bulunmuyor.</p>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
              {leads.map((lead) => {
                const isApproved = lead.status === 'APPROVED';
                const isProcessing = processingId === lead.id;

                return (
                  <div 
                    key={lead.id}
                    style={{
                      background: 'rgb(var(--rgb-sf-111827) / 0.7)',
                      border: isApproved ? '1px solid rgba(16, 185, 129, 0.3)' : '1px solid rgba(245, 158, 11, 0.3)',
                      borderRadius: '12px',
                      padding: '16px 20px',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      gap: '16px'
                    }}
                  >
                    <div style={{ flex: 1 }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '6px' }}>
                        <span style={{ fontSize: '1.05rem', fontWeight: '700', color: 'var(--nt-f8fafc)' }}>
                          {lead.company_name}
                        </span>
                        <span style={{
                          padding: '2px 8px',
                          borderRadius: '6px',
                          fontSize: '0.72rem',
                          fontWeight: '600',
                          background: isApproved ? 'rgba(16, 185, 129, 0.2)' : 'rgba(245, 158, 11, 0.2)',
                          color: isApproved ? 'var(--ac-34d399)' : 'var(--ac-fbbf24)',
                          border: isApproved ? '1px solid rgba(16, 185, 129, 0.4)' : '1px solid rgba(245, 158, 11, 0.4)'
                        }}>
                          {isApproved ? '✓ AKTİF / ONAYLANDI' : '⏳ ÖDEME BEKLİYOR'}
                        </span>
                        {lead.odoo_order_name && (
                          <span style={{
                            padding: '2px 8px',
                            borderRadius: '6px',
                            fontSize: '0.72rem',
                            fontWeight: '600',
                            background: 'rgba(99, 102, 241, 0.15)',
                            color: 'var(--ac-a5b4fc)',
                            border: '1px solid rgba(99, 102, 241, 0.3)'
                          }}>
                            Odoo Ref: {lead.odoo_order_name}
                          </span>
                        )}
                      </div>

                      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '14px', fontSize: '0.8rem', color: 'var(--nt-94a3b8)' }}>
                        <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                          <Mail size={13} color="var(--ac-60a5fa)" /> {lead.contact_email}
                        </span>
                        {lead.phone && (
                          <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                            <Phone size={13} color="var(--ac-34d399)" /> {lead.phone}
                          </span>
                        )}
                        {lead.tax_id && (
                          <span>VKN: {lead.tax_id}</span>
                        )}
                        <span style={{ color: 'var(--nt-64748b)' }}>
                          Tarih: {new Date(lead.created_at).toLocaleString('tr-TR')}
                        </span>
                      </div>
                    </div>

                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                      {!isApproved ? (
                        <button
                          onClick={() => handleApprove(lead)}
                          disabled={isProcessing}
                          style={{
                            background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
                            border: 'none',
                            color: '#ffffff',
                            padding: '8px 16px',
                            borderRadius: '8px',
                            fontSize: '0.825rem',
                            fontWeight: '600',
                            cursor: isProcessing ? 'wait' : 'pointer',
                            display: 'flex',
                            alignItems: 'center',
                            gap: '6px',
                            boxShadow: '0 4px 12px rgba(16, 185, 129, 0.3)'
                          }}
                        >
                          <CheckCircle size={15} />
                          {isProcessing ? 'Onaylanıyor...' : '✓ Ödeme Alındı - Onayla ve Aktif Et'}
                        </button>
                      ) : (
                        <div style={{
                          display: 'flex',
                          alignItems: 'center',
                          gap: '6px',
                          color: 'var(--ac-34d399)',
                          fontSize: '0.825rem',
                          fontWeight: '600',
                          background: 'rgba(16, 185, 129, 0.1)',
                          padding: '6px 12px',
                          borderRadius: '8px',
                          border: '1px solid rgba(16, 185, 129, 0.25)'
                        }}>
                          <ShieldCheck size={16} />
                          Üyelik & Odoo Aktif
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Footer */}
        <div style={{
          padding: '14px 24px',
          borderTop: '1px solid rgb(var(--rgb-ov) / 0.08)',
          background: 'rgb(var(--rgb-shade) / calc(0.2 * var(--shade-k)))',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          fontSize: '0.8rem',
          color: 'var(--nt-64748b)'
        }}>
          <span>
            💡 <b>A.9 İş Akışı:</b> 'Onayla ve Aktif Et' butonuna tıklandığında Odoo 19 üzerindeki teklif resmileştirilir, şirket tenant ortamı oluşturulur ve müşteriye kullanıcı adı/şifre e-postası gönderilir.
          </span>
          <button 
            onClick={onClose}
            className="btn-secondary"
            style={{ padding: '6px 14px', fontSize: '0.8rem' }}
          >
            Kapat
          </button>
        </div>
      </div>
    </div>
  );
}
