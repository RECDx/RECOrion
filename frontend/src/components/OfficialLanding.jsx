import React, { useState, useEffect } from 'react';
import { api } from '../api';
import AdminLeadsModal from './AdminLeadsModal';
import { 
  Building2, 
  Hash, 
  Landmark, 
  Mail, 
  Phone, 
  Globe, 
  MapPin, 
  User, 
  Lock, 
  Sparkles, 
  CheckCircle2, 
  ChevronRight, 
  ChevronLeft, 
  ArrowRight, 
  X, 
  Copy, 
  Check, 
  RefreshCw, 
  ShieldCheck, 
  Zap, 
  Layers, 
  AlertCircle, 
  Package, 
  Eye, 
  EyeOff,
  Search,
  KeyRound
} from 'lucide-react';

export default function OfficialLanding({ onEnterWorkspace, currentUser, onLogout }) {
  const [plans, setPlans] = useState([]);
  const [loadingPlans, setLoadingPlans] = useState(true);
  const [isLeadsModalOpen, setIsLeadsModalOpen] = useState(false);
  
  // Satın Alma Modalı State'leri
  const [isPurchaseModalOpen, setIsPurchaseModalOpen] = useState(false);
  const [selectedPlan, setSelectedPlan] = useState(null);
  const [step, setStep] = useState(1); // 1: Şirket Bilgileri, 2: NACE Kodları, 3: Yetkili/Şifre, 4: Başarı & Manifesto
  
  // Form Bilgileri (Süper Admin Tanımı ile Birebir Eşleşen)
  const [companyName, setCompanyName] = useState('');
  const [taxId, setTaxId] = useState('');
  const [taxOffice, setTaxOffice] = useState('');
  const [phone, setPhone] = useState('');
  const [website, setWebsite] = useState('');
  const [address, setAddress] = useState('');
  const [contactName, setContactName] = useState('');
  const [contactEmail, setContactEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [copiedKey, setCopiedKey] = useState(null);
  
  // NACE Arama ve Seçim State'leri
  const [naceQuery, setNaceQuery] = useState('');
  const [naceResults, setNaceResults] = useState([]);
  const [selectedNaces, setSelectedNaces] = useState([]);
  const [isSearchingNace, setIsSearchingNace] = useState(false);

  // İşlem Sonucu
  const [submitting, setSubmitting] = useState(false);
  const [purchaseResult, setPurchaseResult] = useState(null);
  const [errorMessage, setErrorMessage] = useState('');

  // Giriş Yap Modalı
  const [isLoginModalOpen, setIsLoginModalOpen] = useState(false);
  const [loginEmail, setLoginEmail] = useState('');
  const [loginPassword, setLoginPassword] = useState('');
  const [loginError, setLoginError] = useState('');
  const [isLoggingIn, setIsLoggingIn] = useState(false);

  const POPULAR_NACE_PRESETS = [
    { title: '💻 Bilişim & Yazılım', code: '620101', name: 'Bilgisayar Programlama Faaliyetleri' },
    { title: '🛡️ Savunma & Havacılık', code: '303001', name: 'Hava ve Uzay Araçları İmalatı' },
    { title: '📊 Yönetim Danışmanlığı', code: '702202', name: 'İşletme ve İdari Danışmanlık' },
    { title: '🏦 Finans & Sigorta', code: '641901', name: 'Parasal Aracı Kurumlar' },
    { title: '🏭 Sanayi & İmalat', code: '289901', name: 'Özel Amaçlı Makine İmalatı' },
    { title: '🛒 E-Ticaret & Perakende', code: '479101', name: 'İnternet Üzerinden Perakende Ticaret' }
  ];

  const handleGenerateStrongPassword = () => {
    const chars = 'ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz23456789!@#$%&*';
    let newPass = '';
    for (let i = 0; i < 14; i++) {
      newPass += chars.charAt(Math.floor(Math.random() * chars.length));
    }
    setPassword(newPass);
    copyToClipboard(newPass, 'wizardpass');
  };

  const copyToClipboard = (text, key) => {
    if (!text) return;
    navigator.clipboard.writeText(text);
    setCopiedKey(key);
    setTimeout(() => setCopiedKey(null), 2500);
  };

  // ESC Tuşu ile Modal Kapatma
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape' || e.keyCode === 27) {
        if (isPurchaseModalOpen) setIsPurchaseModalOpen(false);
        if (isLoginModalOpen) setIsLoginModalOpen(false);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isPurchaseModalOpen, isLoginModalOpen]);

  // 1. Paketleri Backend'den Yükle
  useEffect(() => {
    async function loadPlans() {
      try {
        setLoadingPlans(true);
        const data = await api.getPlans();
        setPlans(data);
      } catch (err) {
        console.error("Paketleri yükleme hatası:", err);
      } finally {
        setLoadingPlans(false);
      }
    }
    loadPlans();
  }, []);

  // 2. NACE Arama Efekti
  useEffect(() => {
    if (!naceQuery.trim()) {
      setNaceResults([]);
      return;
    }
    const timer = setTimeout(async () => {
      try {
        setIsSearchingNace(true);
        const res = await api.searchNace(naceQuery.trim(), 15);
        setNaceResults(res);
      } catch (err) {
        console.error("NACE arama hatası:", err);
      } finally {
        setIsSearchingNace(false);
      }
    }, 300);
    return () => clearTimeout(timer);
  }, [naceQuery]);

  const handleOpenPurchase = (plan) => {
    setSelectedPlan(plan);
    setStep(1);
    setPurchaseResult(null);
    setErrorMessage('');
    setIsPurchaseModalOpen(true);
  };

  const handleAddNace = (nace) => {
    if (!selectedNaces.some(n => n.code === nace.code)) {
      setSelectedNaces([...selectedNaces, nace]);
    }
    setNaceQuery('');
    setNaceResults([]);
  };

  const handleRemoveNace = (code) => {
    setSelectedNaces(selectedNaces.filter(n => n.code !== code));
  };

  const handleSubmitPurchase = async (e) => {
    e.preventDefault();
    setErrorMessage('');
    setSubmitting(true);

    try {
      const payload = {
        plan_code: selectedPlan.code,
        company_name: companyName,
        tax_id: taxId || null,
        tax_office: taxOffice || null,
        phone: phone,
        website: website || null,
        address: address || null,
        contact_name: contactName,
        contact_email: contactEmail,
        password: password,
        nace_codes: selectedNaces.map(n => n.code),
      };

      const result = await api.submitPurchaseRequest(payload);
      setPurchaseResult(result);
      setStep(4); // Başarı ve Manifesto ekranına geç
    } catch (err) {
      setErrorMessage(err.message || 'Satın alma talebi iletilirken bir hata oluştu.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleRealLogin = async (e) => {
    e.preventDefault();
    setLoginError('');
    setIsLoggingIn(true);
    try {
      let email = loginEmail.trim();
      if (email.toLowerCase() === 'cuneyterdil@recdx.' || email.toLowerCase() === 'cuneyterdil@recdx') {
        email = 'cuneyterdil@recdx.com';
      }
      const user = await api.login({
        email: email,
        password: loginPassword,
      });
      localStorage.setItem('recorion_user', JSON.stringify(user));
      setIsLoginModalOpen(false);
      onEnterWorkspace(user);
    } catch (err) {
      setLoginError(err.message || 'Giriş yapılamadı. Kullanıcı adı veya şifreyi kontrol ediniz.');
    } finally {
      setIsLoggingIn(false);
    }
  };

  const fillSuperAdmin = () => {
    setLoginEmail('cuneyterdil@recdx.com');
    setLoginPassword('RECDx_SuperAdmin_2026!');
    setLoginError('');
  };

  return (
    <div className="official-landing-container">
      {/* ÜST HEADER / NAVBAR */}
      <header className="landing-header">
        <div className="landing-brand">
          <div className="brand-logo-icon">🪐</div>
          <div>
            <h1 className="brand-title">RECOrion</h1>
            <span className="brand-subtitle">Powered by RECDx Bilişim</span>
          </div>
        </div>
        <div className="landing-nav-actions">
          {currentUser ? (
            <>
              <button 
                className="btn-primary" 
                onClick={() => onEnterWorkspace(currentUser)}
                style={{ display: 'flex', alignItems: 'center', gap: '6px' }}
              >
                {currentUser.role === 'SUPER_ADMIN' ? '👑 Süper Admin Konsolu →' : '💻 Çalışma Alanına Git →'}
              </button>
              <button 
                className="btn-secondary" 
                onClick={onLogout}
                style={{ borderColor: 'rgba(239, 68, 68, 0.4)', color: '#f87171' }}
              >
                Çıkış Yap
              </button>
            </>
          ) : (
            <button 
              className="btn-login-header-3d" 
              onClick={() => setIsLoginModalOpen(true)}
            >
              🔑 Giriş Yap
            </button>
          )}
        </div>
      </header>

      {/* HERO SECTION */}
      <section className="landing-hero">
        <div className="hero-badge">🚀 Yeni Nesil Kurumsal Otonom Ekosistem</div>
        <h2 className="hero-title">
          Yapay Zeka Personellerinizle <br />
          <span className="gradient-text">Şirketinizi Otonom Yönetin</span>
        </h2>
        <p className="hero-desc">
          RECOrion, 13 uzman EVREN modeli ve 40 kurumsal iş ünvanı ile donatılmış,
          sıfır veri sızıntılı Dark DB altyapısında çalışan deterministik yapay zeka işletim sistemidir.
        </p>

        <div className="hero-stats-row">
          <div className="stat-card">
            <span className="stat-value">13</span>
            <span className="stat-label">EVREN LLM Modeli</span>
          </div>
          <div className="stat-card">
            <span className="stat-value">40</span>
            <span className="stat-label">Kurumsal AI Ünvanı</span>
          </div>
          <div className="stat-card">
            <span className="stat-value">2.164</span>
            <span className="stat-label">NACE Faaliyet Alanı</span>
          </div>
          <div className="stat-card">
            <span className="stat-value">%100</span>
            <span className="stat-label">Dark DB Veri Yalıtımı</span>
          </div>
        </div>
      </section>

      {/* PAKETLER BÖLÜMÜ */}
      <section className="landing-plans-section">
        <div className="section-header">
          <h3 className="section-title">Abonelik & Kiralama Paketleri</h3>
          <p className="section-desc">
            Şirketinizin ölçeğine ve hedeflerine en uygun yapay zeka operasyon gücünü seçin.
          </p>
        </div>

        {loadingPlans ? (
          <div className="loading-state">Paket bilgileri getiriliyor...</div>
        ) : (
          <div className="plans-grid">
            {plans.map((p) => {
              const isPopular = p.code === 'PRO';
              return (
                <div key={p.id} className={`plan-card ${isPopular ? 'popular' : ''}`}>
                  {isPopular && <div className="popular-badge">⭐ En Çok Tercih Edilen</div>}
                  <div className="plan-header">
                    <h4 className="plan-name">{p.name}</h4>
                    <p className="plan-desc">{p.description}</p>
                    <div className="plan-price-box">
                      <span className="price-amount">{Number(p.monthly_price).toLocaleString('tr-TR')}</span>
                      <span className="price-currency">₺ / Ay</span>
                    </div>
                  </div>

                  <div className="plan-specs-list">
                    <div className="spec-item">
                      <span className="spec-icon">🤖</span>
                      <span><b>{p.max_agents} AI Ajan Personeli</b></span>
                    </div>
                    <div className="spec-item">
                      <span className="spec-icon">👥</span>
                      <span><b>{p.max_humans} İnsan Kullanıcı</b></span>
                    </div>
                    <div className="spec-item">
                      <span className="spec-icon">📁</span>
                      <span><b>{p.max_projects} Eşzamanlı Proje</b></span>
                    </div>
                    <div className="spec-item">
                      <span className="spec-icon">⚡</span>
                      <span>{Number(p.monthly_credits).toLocaleString('tr-TR')} İşlem Kredisi</span>
                    </div>
                    <div className="spec-item">
                      <span className="spec-icon">💾</span>
                      <span>{p.storage_gb} GB MinIO Yalıtımlı Depolama</span>
                    </div>
                    <div className="spec-item">
                      <span className="spec-icon">📜</span>
                      <span>Otomatik AI NACE Manifestosu</span>
                    </div>
                  </div>

                  <div className="plan-models-box">
                    <span className="models-title">Erişilebilir Modeller ({p.allowed_models?.length}):</span>
                    <div className="model-tags-wrap">
                      {p.allowed_models?.map(m => (
                        <span key={m} className="model-mini-tag">{m}</span>
                      ))}
                    </div>
                  </div>

                  <button 
                    id={`btn-purchase-${p.code.toLowerCase()}`}
                    className={`btn-plan-action ${isPopular ? 'btn-popular' : ''}`}
                    onClick={() => handleOpenPurchase(p)}
                  >
                    🚀 Bu Paketi Kirala / Satın Al
                  </button>
                </div>
              );
            })}
          </div>
        )}
      </section>

      {/* ======================================================== */}
      {/* 3D MODERN PAKET SATIN ALMA / KİRALAMA WIZARD MODALI      */}
      {/* ======================================================== */}
      {isPurchaseModalOpen && selectedPlan && (
        <div className="purchase-modal-backdrop-3d">
          <div className="purchase-modal-card-3d">
            {/* 3D Modal Başlığı */}
            <div className="purchase-modal-header-3d">
              <div style={{ display: 'flex', alignItems: 'center', gap: 14, flexWrap: 'wrap' }}>
                <div style={{
                  width: 44,
                  height: 44,
                  borderRadius: 12,
                  background: 'linear-gradient(135deg, #7134e2 0%, #146ceb 100%)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  boxShadow: '0 0 16px rgba(113, 52, 226, 0.5)',
                  border: '1px solid rgba(255,255,255,0.2)'
                }}>
                  <Package style={{ width: 22, height: 22, color: '#fff' }} />
                </div>
                <div>
                  <h3 className="purchase-modal-header-title">
                    <span>{selectedPlan.name} Kiralama Başvurusu</span>
                  </h3>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginTop: 3, flexWrap: 'wrap' }}>
                    <span className="purchase-plan-badge-3d">
                      <Sparkles style={{ width: 12, height: 12, color: '#38bdf8' }} />
                      <span>Kurumsal Bulut Paket</span>
                    </span>
                    <span className="purchase-price-tag-3d">
                      {Number(selectedPlan.monthly_price).toLocaleString('tr-TR')} ₺ / Ay
                    </span>
                  </div>
                </div>
              </div>

              <button 
                type="button" 
                className="purchase-btn-close-3d" 
                onClick={() => setIsPurchaseModalOpen(false)}
                title="Kapat (ESC)"
              >
                <X style={{ width: 18, height: 18 }} />
              </button>
            </div>

            {/* 3D Adım Çubuğu (Stepper) */}
            <div className="purchase-stepper-3d">
              <div 
                className={`stepper-step-pill-3d ${step === 1 ? 'active' : ''} ${step > 1 ? 'completed' : ''}`}
                onClick={() => setStep(1)}
              >
                <div className="stepper-circle-3d">
                  {step > 1 ? <Check style={{ width: 14, height: 14 }} /> : 1}
                </div>
                <div className="stepper-title-3d">
                  <span className="stepper-step-num">Adım 1</span>
                  <span className="stepper-step-name">1. Kurumsal Bilgiler</span>
                </div>
              </div>

              <div 
                className={`stepper-step-pill-3d ${step === 2 ? 'active' : ''} ${step > 2 ? 'completed' : ''}`}
                onClick={() => {
                  if (companyName.trim()) setStep(2);
                }}
              >
                <div className="stepper-circle-3d">
                  {step > 2 ? <Check style={{ width: 14, height: 14 }} /> : 2}
                </div>
                <div className="stepper-title-3d">
                  <span className="stepper-step-num">Adım 2</span>
                  <span className="stepper-step-name">2. NACE Faaliyetleri</span>
                </div>
              </div>

              <div 
                className={`stepper-step-pill-3d ${step === 3 ? 'active' : ''} ${step > 3 ? 'completed' : ''}`}
                onClick={() => {
                  if (companyName.trim() && selectedNaces.length > 0) setStep(3);
                }}
              >
                <div className="stepper-circle-3d">
                  {step > 3 ? <Check style={{ width: 14, height: 14 }} /> : 3}
                </div>
                <div className="stepper-title-3d">
                  <span className="stepper-step-num">Adım 3</span>
                  <span className="stepper-step-name">3. Yönetici & Güvenlik</span>
                </div>
              </div>

              <div className={`stepper-step-pill-3d ${step === 4 ? 'active' : ''}`}>
                <div className="stepper-circle-3d">
                  {step === 4 ? '🎉' : 4}
                </div>
                <div className="stepper-title-3d">
                  <span className="stepper-step-num">Adım 4</span>
                  <span className="stepper-step-name">4. Onay & AI Manifesto</span>
                </div>
              </div>
            </div>

            {/* Hata Bildirimi */}
            {errorMessage && (
              <div style={{
                margin: '14px 26px 0 26px',
                padding: '12px 16px',
                borderRadius: 12,
                background: 'rgba(239, 68, 68, 0.15)',
                border: '1px solid rgba(239, 68, 68, 0.35)',
                color: '#fca5a5',
                fontSize: '0.8rem',
                display: 'flex',
                alignItems: 'center',
                gap: 8
              }}>
                <AlertCircle style={{ width: 16, height: 16, color: '#f87171', flexShrink: 0 }} />
                <span>{errorMessage}</span>
              </div>
            )}

            {/* ADIM 1: ŞİRKET VE İLETİŞİM BİLGİLERİ */}
            {step === 1 && (
              <form 
                onSubmit={(e) => { 
                  e.preventDefault(); 
                  if (!companyName.trim()) {
                    setErrorMessage('Lütfen şirket ünvanını giriniz.');
                    return;
                  }
                  if (!phone.trim()) {
                    setErrorMessage('Lütfen iletişim telefon numarasını giriniz.');
                    return;
                  }
                  setErrorMessage('');
                  setStep(2); 
                }} 
                style={{ display: 'flex', flexDirection: 'column', flex: 1, overflow: 'hidden' }}
              >
                <div className="purchase-form-scroll-3d">
                  <div className="purchase-section-card-3d">
                    <div className="purchase-section-title-3d">
                      <Building2 style={{ width: 15, height: 15, color: '#38bdf8' }} />
                      <span>Kurumsal Kimlik ve Vergi Bilgileri</span>
                    </div>

                    <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 1fr 1fr', gap: 12 }}>
                      <div>
                        <label className="purchase-label-3d">
                          <Building2 style={{ width: 13, height: 13, color: '#38bdf8' }} />
                          <span>Şirket Ünvanı *</span>
                        </label>
                        <input 
                          id="input-company-name"
                          type="text" 
                          required 
                          placeholder="Örn: Atlas Teknoloji ve Bilişim A.Ş." 
                          value={companyName}
                          onChange={(e) => setCompanyName(e.target.value)}
                          className="purchase-input-field-3d"
                        />
                      </div>

                      <div>
                        <label className="purchase-label-3d">
                          <Hash style={{ width: 13, height: 13, color: '#a78bfa' }} />
                          <span>Vergi Kimlik No (VKN / TCKN) *</span>
                        </label>
                        <input 
                          id="input-tax-id"
                          type="text" 
                          required
                          placeholder="10 veya 11 Haneli Vergi No" 
                          value={taxId}
                          onChange={(e) => setTaxId(e.target.value)}
                          className="purchase-input-field-3d"
                        />
                      </div>

                      <div>
                        <label className="purchase-label-3d">
                          <Landmark style={{ width: 13, height: 13, color: '#34d399' }} />
                          <span>Vergi Dairesi</span>
                        </label>
                        <input 
                          id="input-tax-office"
                          type="text" 
                          placeholder="Örn: Maslak V.D. / Kadıköy V.D." 
                          value={taxOffice}
                          onChange={(e) => setTaxOffice(e.target.value)}
                          className="purchase-input-field-3d"
                        />
                      </div>
                    </div>
                  </div>

                  <div className="purchase-section-card-3d">
                    <div className="purchase-section-title-3d">
                      <Phone style={{ width: 15, height: 15, color: '#fbbf24' }} />
                      <span>İletişim ve Resmi Adres</span>
                    </div>

                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 12 }}>
                      <div>
                        <label className="purchase-label-3d">
                          <Mail style={{ width: 13, height: 13, color: '#f43f5e' }} />
                          <span>Kurumsal İletişim E-Posta *</span>
                        </label>
                        <input 
                          id="input-corporate-email"
                          type="email" 
                          required 
                          placeholder="info@sirketiniz.com" 
                          value={contactEmail}
                          onChange={(e) => {
                            setContactEmail(e.target.value);
                          }}
                          className="purchase-input-field-3d"
                        />
                      </div>

                      <div>
                        <label className="purchase-label-3d">
                          <Phone style={{ width: 13, height: 13, color: '#fbbf24' }} />
                          <span>Telefon Numarası *</span>
                        </label>
                        <input 
                          id="input-phone"
                          type="tel" 
                          required 
                          placeholder="+90 532 000 00 00" 
                          value={phone}
                          onChange={(e) => setPhone(e.target.value)}
                          className="purchase-input-field-3d"
                        />
                      </div>

                      <div>
                        <label className="purchase-label-3d">
                          <Globe style={{ width: 13, height: 13, color: '#60a5fa' }} />
                          <span>Web Sitesi</span>
                        </label>
                        <input 
                          id="input-website"
                          type="url" 
                          placeholder="https://sirketiniz.com" 
                          value={website}
                          onChange={(e) => setWebsite(e.target.value)}
                          className="purchase-input-field-3d"
                        />
                      </div>
                    </div>

                    <div>
                      <label className="purchase-label-3d">
                        <MapPin style={{ width: 13, height: 13, color: '#c084fc' }} />
                        <span>Şirket Resmi Adresi</span>
                      </label>
                      <textarea 
                        id="input-address"
                        rows={2} 
                        placeholder="Şirket genel merkez adresi..." 
                        value={address}
                        onChange={(e) => setAddress(e.target.value)}
                        className="purchase-input-field-3d"
                        style={{ resize: 'vertical' }}
                      />
                    </div>
                  </div>
                </div>

                <div className="purchase-footer-3d">
                  <button 
                    type="button" 
                    className="purchase-btn-back-3d" 
                    onClick={() => setIsPurchaseModalOpen(false)}
                  >
                    Vazgeç / İptal
                  </button>
                  <button id="btn-step1-next" type="submit" className="purchase-btn-next-3d">
                    <span>Devam Et: NACE Faaliyet Seçimi</span>
                    <ArrowRight style={{ width: 16, height: 16 }} />
                  </button>
                </div>
              </form>
            )}

            {/* ADIM 2: NACE FAALİYET ALANLARI */}
            {step === 2 && (
              <div style={{ display: 'flex', flexDirection: 'column', flex: 1, overflow: 'hidden' }}>
                <div className="purchase-form-scroll-3d">
                  <div className="purchase-section-card-3d">
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 8 }}>
                      <div className="purchase-section-title-3d">
                        <Sparkles style={{ width: 15, height: 15, color: '#c084fc' }} />
                        <span>2.164 Kod Kataloğunda Canlı NACE Araması</span>
                      </div>
                      <span style={{ fontSize: '0.75rem', color: '#94a3b8' }}>
                        Seçilen Kod: <strong style={{ color: '#38bdf8' }}>{selectedNaces.length}</strong>
                      </span>
                    </div>

                    <p style={{ fontSize: '0.78rem', color: '#94a3b8', margin: 0, lineHeight: 1.5 }}>
                      Şirketinizin ana ve yan faaliyet alanlarını seçiniz. RECOrion, bu kodlara göre kurumunuza özel 
                      <strong style={{ color: '#6ee7b7' }}> Yapay Zeka Operasyon Manifestosu</strong> ve uzman ajan becerileri yapılandıracaktır.
                    </p>

                    {/* Arama Input */}
                    <div style={{ position: 'relative' }}>
                      <input 
                        id="input-nace-search"
                        type="text" 
                        placeholder="Sektör veya NACE kodu arayın (Örn: yazılım, danışmanlık, 6201, sanayi, finans...)" 
                        value={naceQuery}
                        onChange={(e) => setNaceQuery(e.target.value)}
                        className="purchase-input-field-3d"
                        style={{ paddingLeft: 38 }}
                      />
                      <Search style={{ width: 16, height: 16, color: '#94a3b8', position: 'absolute', left: 12, top: 12 }} />
                      {isSearchingNace && (
                        <RefreshCw style={{ width: 14, height: 14, color: '#38bdf8', position: 'absolute', right: 12, top: 13 }} className="animate-spin" />
                      )}
                    </div>

                    {/* Canlı Arama Sonuçları */}
                    {naceResults.length > 0 && (
                      <div className="nace-search-dropdown-3d" id="nace-search-results" style={{
                        maxHeight: 180,
                        overflowY: 'auto',
                        borderRadius: 12,
                        background: '#090e1c',
                        border: '1px solid rgba(113, 52, 226, 0.4)',
                        boxShadow: '0 10px 30px rgba(0,0,0,0.8)',
                        padding: 6,
                        display: 'flex',
                        flexDirection: 'column',
                        gap: 4
                      }}>
                        {naceResults.map((n) => {
                          const isAdded = selectedNaces.some(sn => sn.code === n.code);
                          return (
                            <div 
                              key={n.code} 
                              onClick={() => handleAddNace(n)}
                              style={{
                                padding: '8px 12px',
                                borderRadius: 8,
                                cursor: isAdded ? 'default' : 'pointer',
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'space-between',
                                fontSize: '0.785rem',
                                background: isAdded ? 'rgba(255,255,255,0.03)' : 'rgba(255,255,255,0.01)',
                                color: isAdded ? '#64748b' : '#cbd5e1',
                                transition: 'background 0.15s ease'
                              }}
                              onMouseEnter={(e) => { if (!isAdded) e.currentTarget.style.background = 'rgba(113, 52, 226, 0.2)'; }}
                              onMouseLeave={(e) => { if (!isAdded) e.currentTarget.style.background = 'rgba(255,255,255,0.01)'; }}
                            >
                              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                                <span style={{ fontFamily: 'monospace', fontWeight: 800, color: '#38bdf8' }}>{n.code}</span>
                                <span>{n.title}</span>
                              </div>
                              <span>{isAdded ? '✓ Eklendi' : '+ Ekle'}</span>
                            </div>
                          );
                        })}
                      </div>
                    )}

                    {/* Hızlı Sektör Önerileri */}
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 6, marginTop: 4 }}>
                      <span style={{ fontSize: '0.72rem', fontWeight: 700, color: '#64748b', textTransform: 'uppercase' }}>
                        Hızlı Sektör Seçimi (Tek Tıkla Ekle):
                      </span>
                      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                        {POPULAR_NACE_PRESETS.map((preset) => {
                          const isAdded = selectedNaces.some(sn => sn.code === preset.code);
                          return (
                            <button
                              key={preset.code}
                              type="button"
                              onClick={() => {
                                if (!isAdded) {
                                  handleAddNace({ code: preset.code, title: preset.name });
                                }
                              }}
                              className="nace-preset-btn-3d"
                              style={{
                                background: isAdded ? 'rgba(56, 189, 248, 0.15)' : 'rgba(255,255,255,0.03)',
                                borderColor: isAdded ? '#38bdf8' : 'rgba(255,255,255,0.08)',
                                color: isAdded ? '#38bdf8' : '#cbd5e1'
                              }}
                            >
                              <span>{preset.title}</span>
                              {isAdded && <span>✓</span>}
                            </button>
                          );
                        })}
                      </div>
                    </div>

                    {/* Seçilen NACE Kodları Çipleri */}
                    <div style={{ marginTop: 6, display: 'flex', flexDirection: 'column', gap: 8 }}>
                      <span style={{ fontSize: '0.725rem', fontWeight: 700, color: '#94a3b8' }}>
                        Seçilen Faaliyet Alanları ({selectedNaces.length}):
                      </span>
                      {selectedNaces.length === 0 ? (
                        <div style={{ padding: '14px', borderRadius: 10, background: 'rgba(255,255,255,0.02)', border: '1px dashed rgba(255,255,255,0.1)', textAlign: 'center', fontSize: '0.775rem', color: '#64748b' }}>
                          Henüz faaliyet alanı eklenmedi. Yukarıdaki arama kutusundan arayabilir veya hızlı sektör butonlarını tıklayabilirsiniz.
                        </div>
                      ) : (
                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
                          {selectedNaces.map((n) => (
                            <div key={n.code} className="nace-chip-3d">
                              <span style={{ fontFamily: 'monospace', fontWeight: 800, color: '#38bdf8' }}>{n.code}</span>
                              <span style={{ maxWidth: 240, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{n.title}</span>
                              <button 
                                type="button" 
                                className="nace-chip-remove-btn" 
                                onClick={() => handleRemoveNace(n.code)}
                                title="Kaldır"
                              >
                                ✕
                              </button>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                </div>

                <div className="purchase-footer-3d">
                  <button type="button" className="purchase-btn-back-3d" onClick={() => setStep(1)}>
                    <ChevronLeft style={{ width: 16, height: 16 }} />
                    <span>← Geri: Şirket Bilgileri</span>
                  </button>
                  <button 
                    id="btn-step2-next"
                    type="button" 
                    className="purchase-btn-next-3d" 
                    onClick={() => {
                      if (selectedNaces.length === 0) {
                        alert("Lütfen en az bir NACE faaliyet alanı seçiniz.");
                        return;
                      }
                      setErrorMessage('');
                      setStep(3);
                    }}
                  >
                    <span>Devam Et: Yetkili Hesap & Şifre</span>
                    <ArrowRight style={{ width: 16, height: 16 }} />
                  </button>
                </div>
              </div>
            )}

            {/* ADIM 3: YETKİLİ HESAP & ŞİFRE */}
            {step === 3 && (
              <form onSubmit={handleSubmitPurchase} style={{ display: 'flex', flexDirection: 'column', flex: 1, overflow: 'hidden' }}>
                <div className="purchase-form-scroll-3d">
                  <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 1fr', gap: 16 }}>
                    {/* Sol: Yetkili Kullanıcı ve Şifre */}
                    <div className="purchase-section-card-3d">
                      <div className="purchase-section-title-3d">
                        <User style={{ width: 15, height: 15, color: '#38bdf8' }} />
                        <span>Yetkili Yönetici ve Hesap Bilgileri</span>
                      </div>

                      <div>
                        <label className="purchase-label-3d">
                          <User style={{ width: 13, height: 13, color: '#cbd5e1' }} />
                          <span>Yetkili Adı Soyadı *</span>
                        </label>
                        <input 
                          id="input-contact-name"
                          type="text" 
                          required 
                          placeholder="Örn: Cüneyt Erdil" 
                          value={contactName}
                          onChange={(e) => setContactName(e.target.value)}
                          className="purchase-input-field-3d"
                        />
                      </div>

                      <div>
                        <label className="purchase-label-3d">
                          <Mail style={{ width: 13, height: 13, color: '#cbd5e1' }} />
                          <span>Giriş E-Posta Adresi (Yönetim Paneli Girişi) *</span>
                        </label>
                        <input 
                          id="input-contact-email"
                          type="email" 
                          required 
                          placeholder="yonetici@sirketiniz.com" 
                          value={contactEmail}
                          onChange={(e) => setContactEmail(e.target.value)}
                          className="purchase-input-field-3d"
                        />
                      </div>

                      {/* Şifre ve Güçlü Şifre Oluşturucu */}
                      <div>
                        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 5 }}>
                          <label className="purchase-label-3d" style={{ margin: 0 }}>
                            <Lock style={{ width: 13, height: 13, color: '#cbd5e1' }} />
                            <span>Giriş Şifresi *</span>
                          </label>
                          <button
                            type="button"
                            onClick={handleGenerateStrongPassword}
                            className="super-admin-btn-corporate"
                            style={{
                              padding: '3px 9px',
                              fontSize: '0.7rem',
                              background: 'linear-gradient(135deg, #0284c7 0%, #0369a1 100%)',
                              gap: 4
                            }}
                            title="Rastgele 14 karakterli güçlü şifre ata"
                          >
                            <Sparkles style={{ width: 11, height: 11 }} />
                            <span>✨ Güçlü Şifre Oluştur</span>
                          </button>
                        </div>

                        <div style={{ position: 'relative' }}>
                          <input 
                            id="input-password"
                            type={showPassword ? 'text' : 'password'} 
                            required 
                            placeholder="Güçlü bir şifre belirleyin..." 
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            className="purchase-input-field-3d"
                            style={{ paddingRight: 74, fontFamily: showPassword ? 'inherit' : 'monospace' }}
                          />
                          <div style={{ position: 'absolute', right: 8, top: 8, display: 'flex', alignItems: 'center', gap: 4 }}>
                            {password && (
                              <button
                                type="button"
                                onClick={() => copyToClipboard(password, 'wizardpass')}
                                style={{
                                  background: 'rgba(255,255,255,0.08)',
                                  border: 'none',
                                  borderRadius: 6,
                                  padding: '4px 6px',
                                  color: '#cbd5e1',
                                  cursor: 'pointer',
                                  display: 'flex',
                                  alignItems: 'center',
                                  gap: 3,
                                  fontSize: '0.68rem'
                                }}
                                title="Şifreyi panoya kopyala"
                              >
                                {copiedKey === 'wizardpass' ? <Check style={{ width: 12, height: 12, color: '#34d399' }} /> : <Copy style={{ width: 12, height: 12 }} />}
                              </button>
                            )}
                            <button
                              type="button"
                              onClick={() => setShowPassword(!showPassword)}
                              style={{
                                background: 'transparent',
                                border: 'none',
                                color: '#94a3b8',
                                cursor: 'pointer',
                                padding: 4,
                                display: 'flex',
                                alignItems: 'center'
                              }}
                            >
                              {showPassword ? <EyeOff style={{ width: 15, height: 15 }} /> : <Eye style={{ width: 15, height: 15 }} />}
                            </button>
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* Sağ: 3D Seçilen Paket & Başvuru Özeti */}
                    <div className="purchase-section-card-3d" style={{
                      background: 'linear-gradient(180deg, rgba(113,52,226,0.12) 0%, rgba(14,165,233,0.08) 100%)',
                      borderColor: 'rgba(113,52,226,0.35)',
                      justifyContent: 'space-between'
                    }}>
                      <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                          <span style={{ fontSize: '0.72rem', fontWeight: 800, textTransform: 'uppercase', color: '#c084fc', letterSpacing: '0.05em' }}>
                            SEÇİLEN KURUMSAL PAKET
                          </span>
                          <span className="purchase-plan-badge-3d">
                            👑 {selectedPlan.name}
                          </span>
                        </div>

                        <div style={{ display: 'flex', alignItems: 'baseline', gap: 6, padding: '10px 14px', borderRadius: 12, background: 'rgba(0,0,0,0.3)', border: '1px solid rgba(255,255,255,0.06)' }}>
                          <span style={{ fontSize: '1.4rem', fontWeight: 900, color: '#38bdf8', fontFamily: 'Outfit, sans-serif' }}>
                            {Number(selectedPlan.monthly_price).toLocaleString('tr-TR')} ₺
                          </span>
                          <span style={{ fontSize: '0.775rem', color: '#94a3b8' }}>/ Ay (Yıllık Kurumsal Sözleşme)</span>
                        </div>

                        {/* Paket Değiştirme Opsiyonu */}
                        {plans.length > 1 && (
                          <div>
                            <label style={{ display: 'block', fontSize: '0.68rem', fontWeight: 700, color: '#94a3b8', marginBottom: 4 }}>
                              Farklı Bir Paket Seçmek İster misiniz?
                            </label>
                            <select
                              value={selectedPlan.id}
                              onChange={(e) => {
                                const newP = plans.find(p => p.id === e.target.value);
                                if (newP) setSelectedPlan(newP);
                              }}
                              className="super-admin-select"
                              style={{ fontSize: '0.775rem', padding: '6px 10px' }}
                            >
                              {plans.map(p => (
                                <option key={p.id} value={p.id}>{p.name} — {Number(p.monthly_price).toLocaleString('tr-TR')} ₺/Ay</option>
                              ))}
                            </select>
                          </div>
                        )}

                        <div style={{ display: 'flex', flexDirection: 'column', gap: 6, fontSize: '0.75rem', color: '#cbd5e1' }}>
                          <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                            <CheckCircle2 style={{ width: 14, height: 14, color: '#34d399' }} />
                            <span><b>{selectedPlan.max_agents} AI Ajan</b> ve <b>{selectedPlan.max_humans} İnsan</b> Kullanıcı</span>
                          </div>
                          <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                            <CheckCircle2 style={{ width: 14, height: 14, color: '#34d399' }} />
                            <span><b>{selectedPlan.storage_gb} GB</b> İzole MinIO Bulut Depolama</span>
                          </div>
                          <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                            <CheckCircle2 style={{ width: 14, height: 14, color: '#34d399' }} />
                            <span><b>{selectedNaces.length} NACE Kodu</b> Odaklı AI Manifestosu</span>
                          </div>
                        </div>
                      </div>

                      <div style={{ padding: '10px 12px', borderRadius: 10, background: 'rgba(2,132,199,0.1)', border: '1px solid rgba(2,132,199,0.25)', fontSize: '0.72rem', color: '#7dd3fc', lineHeight: 1.4, marginTop: 10 }}>
                        📌 Başvuru tamamlandığında Odoo 19 sipariş kaydınız açılacak ve <b>{contactEmail || 'kurumsal adresinize'}</b> onay ve aktivasyon mektubu iletilecektir.
                      </div>
                    </div>
                  </div>
                </div>

                <div className="purchase-footer-3d">
                  <button type="button" className="purchase-btn-back-3d" onClick={() => setStep(2)} disabled={submitting}>
                    <ChevronLeft style={{ width: 16, height: 16 }} />
                    <span>← Geri: NACE Seçimi</span>
                  </button>
                  <button 
                    id="btn-submit-purchase" 
                    type="submit" 
                    className="purchase-btn-next-3d" 
                    disabled={submitting}
                    style={{ background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)', boxShadow: '0 4px 0 #064e3b, 0 8px 24px rgba(16,185,129,0.45)' }}
                  >
                    {submitting ? (
                      <>
                        <RefreshCw style={{ width: 16, height: 16 }} className="animate-spin" />
                        <span>AI Manifestoyu Yazıyor & Odoo Siparişi Oluşturuluyor...</span>
                      </>
                    ) : (
                      <>
                        <CheckCircle2 style={{ width: 16, height: 16 }} />
                        <span>Kiralama Başvurusunu Tamamla →</span>
                      </>
                    )}
                  </button>
                </div>
              </form>
            )}

            {/* ADIM 4: BAŞARI VE MANİFESTO GÖSTERİMİ */}
            {step === 4 && purchaseResult && (
              <div style={{ display: 'flex', flexDirection: 'column', flex: 1, overflow: 'hidden' }}>
                <div className="purchase-form-scroll-3d" style={{ alignItems: 'center' }}>
                  <div className="purchase-section-card-3d" style={{ textAlign: 'center', padding: '26px 20px', alignItems: 'center', gap: 14, width: '100%' }}>
                    <div style={{
                      width: 60,
                      height: 60,
                      borderRadius: 18,
                      background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontSize: '1.8rem',
                      boxShadow: '0 0 25px rgba(16,185,129,0.5)',
                      border: '1px solid rgba(255,255,255,0.3)'
                    }}>
                      🎉
                    </div>

                    <div>
                      <h3 style={{ fontSize: '1.25rem', fontWeight: 800, color: '#fff', margin: 0 }}>
                        Kiralama Talebiniz Başarıyla Alındı!
                      </h3>
                      <p style={{ fontSize: '0.8rem', color: '#94a3b8', marginTop: 4 }}>
                        '{companyName}' kurumu için sipariş kaydı oluşturuldu ve şirket ortamınız hazırlandı.
                      </p>
                    </div>

                    {/* Bildirim Durumları */}
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10, width: '100%', maxWidth: 650 }}>
                      <div style={{ padding: '10px 14px', borderRadius: 10, background: 'rgba(16,185,129,0.1)', border: '1px solid rgba(16,185,129,0.25)', display: 'flex', alignItems: 'center', gap: 8, fontSize: '0.75rem', color: '#6ee7b7' }}>
                        <CheckCircle2 style={{ width: 16, height: 16, color: '#34d399', flexShrink: 0 }} />
                        <span><b>info@recdx.com</b> adresine Süper Admin bildirimi gönderildi.</span>
                      </div>
                      <div style={{ padding: '10px 14px', borderRadius: 10, background: 'rgba(16,185,129,0.1)', border: '1px solid rgba(16,185,129,0.25)', display: 'flex', alignItems: 'center', gap: 8, fontSize: '0.75rem', color: '#6ee7b7' }}>
                        <CheckCircle2 style={{ width: 16, height: 16, color: '#34d399', flexShrink: 0 }} />
                        <span><b>{purchaseResult.contact_email}</b> adresinize kurumsal karşılama iletildi.</span>
                      </div>
                    </div>

                    {/* AI Manifestosu Önizleme */}
                    <div style={{ width: '100%', maxWidth: 760, borderRadius: 14, background: '#080c18', border: '1px solid rgba(113,52,226,0.3)', overflow: 'hidden', textAlign: 'left' }}>
                      <div style={{ padding: '10px 14px', background: 'rgba(255,255,255,0.03)', borderBottom: '1px solid rgba(255,255,255,0.06)', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: '0.785rem', fontWeight: 700, color: '#c084fc' }}>
                          <Sparkles style={{ width: 14, height: 14 }} />
                          <span>RECOrion AI Tarafından Üretilen Kurumsal Manifesto</span>
                        </div>
                        <span style={{ fontSize: '0.7rem', padding: '2px 8px', borderRadius: 999, background: 'rgba(56,189,248,0.2)', color: '#38bdf8' }}>
                          {purchaseResult.assigned_skills?.length || 0} Yetenek Atandı
                        </span>
                      </div>
                      <pre style={{ margin: 0, padding: '12px 14px', fontSize: '0.75rem', color: '#94a3b8', lineHeight: 1.6, maxHeight: 160, overflowY: 'auto', whiteSpace: 'pre-wrap', fontFamily: 'monospace' }}>
                        {purchaseResult.generated_manifesto}
                      </pre>
                    </div>

                    {/* Atanan Sektörel Yetenekler */}
                    {purchaseResult.assigned_skills?.length > 0 && (
                      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, justifyContent: 'center', maxWidth: 760 }}>
                        {purchaseResult.assigned_skills.map(s => (
                          <span key={s} style={{ padding: '3px 10px', borderRadius: 999, background: 'rgba(113,52,226,0.2)', border: '1px solid rgba(113,52,226,0.4)', color: '#d8b4fe', fontSize: '0.72rem', fontWeight: 600 }}>
                            ✦ {s}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                </div>

                <div className="purchase-footer-3d" style={{ justifyContent: 'center' }}>
                  <button 
                    id="btn-go-to-workspace" 
                    className="purchase-btn-next-3d" 
                    style={{ background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)', boxShadow: '0 4px 0 #064e3b, 0 8px 24px rgba(16,185,129,0.5)' }}
                    onClick={() => {
                      setIsPurchaseModalOpen(false);
                      setIsLoginModalOpen(true);
                    }}
                  >
                    <KeyRound style={{ width: 16, height: 16 }} />
                    <span>🔑 Yönetim Paneline / Giriş Ekranına Git →</span>
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* GİRİŞ YAP MODALI */}
      {/* GİRİŞ YAP MODALI (3D & EŞİT HİZALAMA) */}
      {isLoginModalOpen && (
        <div className="modal-backdrop">
          <div className="login-modal-card-3d">
            <div className="modal-header" style={{ padding: '20px 24px', borderBottom: '1px solid rgba(255, 255, 255, 0.08)' }}>
              <div>
                <h3 className="modal-title" style={{ fontSize: '1.2rem', fontWeight: 800, color: '#fff', display: 'flex', alignItems: 'center', gap: 8 }}>
                  <span>🔐 RECOrion Şirket Girişi</span>
                </h3>
                <p style={{ fontSize: '0.75rem', color: '#94a3b8', margin: '4px 0 0 0' }}>
                  Yönetim veya çalışma alanı paneline güvenli erişim sağlayın.
                </p>
              </div>
              <button className="btn-close" onClick={() => setIsLoginModalOpen(false)}>✕</button>
            </div>

            <form onSubmit={handleRealLogin} noValidate style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '18px' }}>
              {loginError && (
                <div style={{ padding: '10px 14px', borderRadius: '12px', background: 'rgba(239, 68, 68, 0.15)', border: '1px solid rgba(239, 68, 68, 0.4)', color: '#fca5a5', fontSize: '0.825rem', display: 'flex', alignItems: 'center', gap: 8 }}>
                  <span>⚠️</span>
                  <span>{loginError}</span>
                </div>
              )}

              {/* Kurumsal E-Posta */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: 6, width: '100%' }}>
                <label style={{ fontSize: '0.8rem', fontWeight: 700, color: '#cbd5e1', display: 'flex', alignItems: 'center', gap: 6 }}>
                  <span>✉️ Kurumsal E-Posta Adresi</span>
                </label>
                <input 
                  type="email" 
                  required 
                  placeholder="ornek: cuneyterdil@recdx.com"
                  value={loginEmail}
                  onChange={(e) => setLoginEmail(e.target.value)}
                  className="login-input-3d"
                />
              </div>

              {/* Şifre */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: 6, width: '100%' }}>
                <label style={{ fontSize: '0.8rem', fontWeight: 700, color: '#cbd5e1', display: 'flex', alignItems: 'center', gap: 6 }}>
                  <span>🔑 Güvenli Şifre</span>
                </label>
                <input 
                  type="password" 
                  required 
                  placeholder="••••••••••••"
                  value={loginPassword}
                  onChange={(e) => setLoginPassword(e.target.value)}
                  className="login-input-3d"
                />
              </div>

              {/* Hızlı Demo / Süper Admin Doldur Butonu */}
              <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: -4 }}>
                <button 
                  type="button" 
                  onClick={fillSuperAdmin}
                  style={{
                    background: 'rgba(113, 52, 226, 0.12)',
                    border: '1px solid rgba(113, 52, 226, 0.35)',
                    color: '#c084fc',
                    cursor: 'pointer',
                    fontSize: '0.775rem',
                    fontWeight: 600,
                    padding: '6px 12px',
                    borderRadius: '8px',
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: 6,
                    transition: 'all 0.2s'
                  }}
                  onMouseEnter={(e) => e.currentTarget.style.background = 'rgba(113, 52, 226, 0.25)'}
                  onMouseLeave={(e) => e.currentTarget.style.background = 'rgba(113, 52, 226, 0.12)'}
                >
                  <span>👑 Süper Admin Bilgilerini Doldur</span>
                </button>
              </div>

              {/* Giriş Butonu */}
              <div style={{ marginTop: 8 }}>
                <button type="submit" className="login-btn-submit-3d" disabled={isLoggingIn}>
                  {isLoggingIn ? (
                    <>
                      <span className="spinner-border spinner-border-sm" role="status" aria-hidden="true" style={{ width: 16, height: 16, border: '2px solid rgba(255,255,255,0.3)', borderTopColor: '#fff', borderRadius: '50%', display: 'inline-block', animation: 'spin 0.8s linear infinite' }}></span>
                      <span>Giriş Yapılıyor...</span>
                    </>
                  ) : (
                    <span>Giriş Yap →</span>
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* SÜPER ADMİN ODOO ONAY MODALI */}
      <AdminLeadsModal 
        isOpen={isLeadsModalOpen} 
        onClose={() => setIsLeadsModalOpen(false)} 
      />
    </div>
  );
}
