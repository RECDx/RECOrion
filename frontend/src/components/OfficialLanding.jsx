import React, { useState, useEffect } from 'react';
import { api, session } from '../api';
import RecdxAppsChoice from './integrations/RecdxAppsChoice';
import AdminLeadsModal from './AdminLeadsModal';
import ThemeToggle from '../ui/ThemeToggle';
import { notify, promptDialog, toast } from '../ui/feedback';
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
  KeyRound,
  Briefcase,
  GraduationCap
} from 'lucide-react';

export default function OfficialLanding({ onEnterWorkspace, currentUser, onLogout }) {
  const [plans, setPlans] = useState([]);
  const [loadingPlans, setLoadingPlans] = useState(true);
  const [isLeadsModalOpen, setIsLeadsModalOpen] = useState(false);
  
  // Satın Alma Modalı State'leri
  const [isPurchaseModalOpen, setIsPurchaseModalOpen] = useState(false);
  const [selectedPlan, setSelectedPlan] = useState(null);
  const [recdxApps, setRecdxApps] = useState(null);  // ADIM 13.1: Odoo ve RECDx uygulamaları (paketin teklifiyle)
  const [appChoice, setAppChoice] = useState({ has_odoo: null, apps: {} });
  const [step, setStep] = useState(1);
  useEffect(() => {
    if (!selectedPlan?.code) return;
    api.getPublicRecdxApps(selectedPlan.code).then((d) => setRecdxApps(d.apps)).catch(() => setRecdxApps(null));
  }, [selectedPlan?.code]); // 1: Şirket Bilgileri, 2: NACE Kodları, 3: Yetkili/Şifre, 4: Başarı & Manifesto
  
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
  // E-posta doğrulama kodu (başvuru göndermeden önce zorunlu)
  const [emailCode, setEmailCode] = useState('');
  const [codeSentTo, setCodeSentTo] = useState('');
  const [codeCooldown, setCodeCooldown] = useState(0);
  const [sendingCode, setSendingCode] = useState(false);
  const [companyFax, setCompanyFax] = useState(''); // bot tuzağı (görünmez alan)
  const [copiedKey, setCopiedKey] = useState(null);
  
  // Sektör ve Meslek Grubu Seçim State'leri (Madde 2 - T.C. Ticaret Bakanlığı)
  const [sectors, setSectors] = useState([]);
  const [professions, setProfessions] = useState([]);
  const [sectorSearch, setSectorSearch] = useState('');
  const [professionSearch, setProfessionSearch] = useState('');
  const [llmModelCount, setLlmModelCount] = useState(null);
  const [selectedSectors, setSelectedSectors] = useState([]);
  const [selectedProfessions, setSelectedProfessions] = useState([]);

  // İşlem Sonucu
  const [submitting, setSubmitting] = useState(false);
  const [purchaseResult, setPurchaseResult] = useState(null);
  const [errorMessage, setErrorMessage] = useState('');

  // Giriş Yap Modalı
  const [isLoginModalOpen, setIsLoginModalOpen] = useState(false);
  const [loginEmail, setLoginEmail] = useState(() => localStorage.getItem('recorion_remembered_email') || '');
  const [loginPassword, setLoginPassword] = useState('');
  const [rememberMe, setRememberMe] = useState(() => localStorage.getItem('recorion_remember_me') === 'true');
  const [loginError, setLoginError] = useState('');
  const [isLoggingIn, setIsLoggingIn] = useState(false);
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

  const resetPurchaseForm = () => {
    setCompanyName('');
    setTaxId('');
    setTaxOffice('');
    setPhone('');
    setWebsite('');
    setAddress('');
    setContactName('');
    setContactEmail('');
    setPassword('');
    setShowPassword(false);
    setEmailCode('');
    setCodeSentTo('');
    setCompanyFax('');
    setCopiedKey(null);
    setSelectedSectors([]);
    setSelectedProfessions([]);
    setPurchaseResult(null);
    setErrorMessage('');
    setStep(1);
  };

  const handleClosePurchaseModal = () => {
    setIsPurchaseModalOpen(false);
    resetPurchaseForm();
  };

  // ESC Tuşu ile Modal Kapatma
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape' || e.keyCode === 27) {
        if (isPurchaseModalOpen) handleClosePurchaseModal();
        if (isLoginModalOpen) setIsLoginModalOpen(false);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isPurchaseModalOpen, isLoginModalOpen]);

  // 1. Paketleri, Sektörleri ve Meslekleri Backend'den Yükle (Madde 2 - Ticaret Bakanlığı)
  useEffect(() => {
    async function loadInitialData() {
      try {
        setLoadingPlans(true);
        const [plansData, sectorsData, professionsData] = await Promise.all([
          api.getPlans(true).catch(() => []),
          api.getSectors(true).catch(() => []),
          api.getProfessions({ is_active: true, limit: 500 }).catch(() => [])
        ]);
        const activePlans = (plansData || []).filter(p => p.is_active !== false);
        setPlans(activePlans);
        setSectors(sectorsData || []);
        setProfessions(professionsData || []);
        api.getPublicStats().then((st) => setLlmModelCount(st.llm_models)).catch(() => {});
      } catch (err) {
        console.error("Paketleri, sektörleri ve meslekleri yükleme hatası:", err);
      } finally {
        setLoadingPlans(false);
      }
    }
    loadInitialData();
  }, []);

  const handleToggleSector = (sectorCode) => {
    setSelectedSectors((prev) => {
      const isSelected = prev.includes(sectorCode);
      const updatedSectors = isSelected ? prev.filter(s => s !== sectorCode) : [...prev, sectorCode];
      if (isSelected) {
        setSelectedProfessions(profPrev => profPrev.filter(pCode => {
          const profObj = professions.find(pr => pr.code === pCode);
          return profObj ? profObj.sector_code !== sectorCode : true;
        }));
      }
      return updatedSectors;
    });
  };

  const handleToggleProfession = (profCode) => {
    // Aramayla başka bir sektörün meslek grubu seçilirse o sektör de seçilir
    const prof = professions.find(pr => pr.code === profCode);
    if (prof && !selectedSectors.includes(prof.sector_code)) {
      setSelectedSectors(prev => [...prev, prof.sector_code]);
    }
    setSelectedProfessions((prev) => {
      return prev.includes(profCode) ? prev.filter(p => p !== profCode) : [...prev, profCode];
    });
  };

  // Arama: Türkçe büyük/küçük harf duyarsız; sektör araması o sektörün meslek gruplarında da arar
  const trLower = (v) => String(v || '').toLocaleLowerCase('tr');
  const sectorQuery = trLower(sectorSearch.trim());
  const professionQuery = trLower(professionSearch.trim());
  const visibleSectors = sectors.filter(sec => !sectorQuery || selectedSectors.includes(sec.code)
    || trLower(`${sec.code} ${sec.name}`).includes(sectorQuery)
    || professions.some(pr => pr.sector_code === sec.code && trLower(pr.name).includes(sectorQuery)));
  const visibleProfessions = professions.filter(pr => (professionQuery
    ? trLower(`${pr.code} ${pr.name}`).includes(professionQuery)
    : selectedSectors.includes(pr.sector_code)));

  const handleOpenPurchase = (plan) => {
    resetPurchaseForm();
    setSelectedPlan(plan);
    setIsPurchaseModalOpen(true);
  };

  useEffect(() => {
    if (codeCooldown <= 0) return undefined;
    const t = setTimeout(() => setCodeCooldown((c) => c - 1), 1000);
    return () => clearTimeout(t);
  }, [codeCooldown]);

  const handleSendEmailCode = async () => {
    setErrorMessage('');
    const email = contactEmail.trim().toLowerCase();
    if (!email || !email.includes('@')) {
      setErrorMessage('Lütfen önce kurumsal e-posta adresinizi yazın.');
      return;
    }
    setSendingCode(true);
    try {
      const res = await api.sendPurchaseEmailCode(email);
      setCodeSentTo(email);
      setCodeCooldown(60);
      toast.success(res.message || 'Doğrulama kodu gönderildi.');
    } catch (err) {
      setErrorMessage(err.message || 'Doğrulama kodu gönderilemedi.');
    } finally {
      setSendingCode(false);
    }
  };

  const handleSubmitPurchase = async (e) => {
    e.preventDefault();
    setErrorMessage('');

    // Madde 3: Kurumsal / Official e-posta zorunluluğu (Gmail, Hotmail vb. engelleme)
    const publicMailDomains = [
      'gmail.com', 'googlemail.com', 'hotmail.com', 'hotmail.com.tr', 'outlook.com', 
      'outlook.com.tr', 'live.com', 'msn.com', 'yahoo.com', 'yahoo.com.tr', 'ymail.com', 
      'yandex.com', 'yandex.com.tr', 'ya.ru', 'icloud.com', 'mail.ru', 'proton.me', 
      'protonmail.com', 'zoho.com', 'gmx.com', 'aol.com'
    ];
    const emailParts = (contactEmail || '').trim().toLowerCase().split('@');
    const domain = (emailParts[1] || '').trim();
    if (!domain || publicMailDomains.includes(domain) || publicMailDomains.some(d => domain.endsWith('.' + d))) {
      setErrorMessage(`⚠️ Kurumsal / Official E-Posta Zorunluluğu: RECOrion kurumsal abonelik başvurularında şirket uzantılı resmi (official) e-posta adresi zorunludur. Genel ve ücretsiz sağlayıcılar (${domain || 'geçersiz e-posta'}) kabul edilmemektedir. Lütfen 'info@sirketiniz.com' veya 'yonetici@sirketiniz.com' gibi kurumsal bir alan adı giriniz.`);
      return;
    }

    if (password.trim().length < 8) {
      setErrorMessage('Giriş şifresi en az 8 karakter olmalıdır.');
      return;
    }
    // Kodun doğruluğunu backend kontrol eder; burada yalnızca biçim kontrolü yapılır
    // (pencere yeniden açılsa da e-postadaki kod 10 dakika geçerlidir)
    if (emailCode.trim().length !== 6) {
      setErrorMessage('Lütfen e-posta adresinize gönderilen 6 haneli doğrulama kodunu girin.');
      return;
    }

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
        email_code: emailCode.trim(),
        company_fax: companyFax || null,
        sectors: selectedSectors,
        professions: selectedProfessions,
        nace_codes: [],
        ...(appChoice.has_odoo !== null || Object.keys(appChoice.apps).length ? { recdx_apps: appChoice } : {})
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

  const handleForgotPassword = async () => {
    const email = await promptDialog({
      title: 'Şifremi Unuttum',
      message: 'Hesabınıza kayıtlı e-posta adresini yazın. Şifre belirleme bağlantısı gönderilecektir.',
      defaultValue: loginEmail,
      confirmText: 'Bağlantı Gönder',
    });
    if (!email || !email.trim()) return;
    try {
      const res = await api.requestPasswordReset(email.trim());
      toast.success(res.message);
    } catch (err) {
      toast.error(err.message || 'Talep iletilemedi.');
    }
  };

  const handleRealLogin = async (e) => {
    e.preventDefault();
    setLoginError('');
    setIsLoggingIn(true);
    try {
      let email = loginEmail.trim();
      const { access_token: accessToken, token_type: _tokenType, expires_at: _expiresAt, ...user } = await api.login({
        email: email,
        password: loginPassword,
        remember_me: rememberMe,
      });
      session.setToken(accessToken, rememberMe);

      if (rememberMe) {
        localStorage.setItem('recorion_remember_me', 'true');
        localStorage.setItem('recorion_remembered_email', email);
      } else {
        localStorage.removeItem('recorion_remember_me');
        localStorage.removeItem('recorion_remembered_email');
      }

      localStorage.setItem('recorion_user', JSON.stringify(user));
      setIsLoginModalOpen(false);
      onEnterWorkspace(user);
    } catch (err) {
      setLoginError(err.message || 'Giriş yapılamadı. Kullanıcı adı veya şifreyi kontrol ediniz.');
    } finally {
      setIsLoggingIn(false);
    }
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
          <ThemeToggle compact />
          {currentUser ? (
            <>
              <button
                className="btn-login-header-3d"
                onClick={() => onEnterWorkspace(currentUser)}
              >
                {currentUser.role === 'SUPER_ADMIN' ? '👑 Süper Admin Konsolu →' : (currentUser.role === 'COMPANY_ADMIN' ? '🏢 Şirket Yönetim Paneli →' : '💻 Çalışma Alanına Git →')}
              </button>
              <button
                className="btn btn-secondary"
                onClick={onLogout}
                style={{ borderColor: 'rgba(239, 68, 68, 0.4)', color: 'var(--ac-f87171)', borderRadius: '12px', padding: '10px 18px' }}
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
          RECOrion, yerli EVREN yapay zeka modelleriyle çalışan, T.C. Ticaret Bakanlığı'nın resmi sektör ve
          meslek grubu yapısıyla şirketinizi tanıyan, sıfır veri sızıntılı Dark DB altyapısında çalışan
          deterministik yapay zeka işletim sistemidir.
        </p>

        <div className="hero-stats-row">
          <div className="stat-card">
            <span className="stat-value">{llmModelCount ?? '…'}</span>
            <span className="stat-label">Yerli EVREN LLM Modeli</span>
          </div>
          <div className="stat-card">
            <span className="stat-value">{sectors.length || '…'}</span>
            <span className="stat-label">Resmi Faaliyet Sektörü</span>
          </div>
          <div className="stat-card">
            <span className="stat-value">{professions.length || '…'}</span>
            <span className="stat-label">Meslek Grubu (T.C. Ticaret Bakanlığı)</span>
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
              const isPopular = p.features?.is_popular || p.code === 'PRO';
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
                      <span>Otomatik Kurumsal AI Manifestosu</span>
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
                  border: '1px solid rgb(var(--rgb-ov) / 0.2)'
                }}>
                  <Package style={{ width: 22, height: 22, color: 'var(--nt-ffffff)' }} />
                </div>
                <div>
                  <h3 className="purchase-modal-header-title">
                    <span>{selectedPlan.name} Kiralama Başvurusu</span>
                  </h3>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginTop: 3, flexWrap: 'wrap' }}>
                    <span className="purchase-plan-badge-3d">
                      <Sparkles style={{ width: 12, height: 12, color: 'var(--ac-38bdf8)' }} />
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
                onClick={handleClosePurchaseModal}
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
                  <span className="stepper-step-name">2. Sektör & Meslek Grupları</span>
                </div>
              </div>

              <div 
                className={`stepper-step-pill-3d ${step === 3 ? 'active' : ''} ${step > 3 ? 'completed' : ''}`}
                onClick={() => {
                  if (companyName.trim() && selectedSectors.length > 0) setStep(3);
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
                color: 'var(--ac-fca5a5)',
                fontSize: '0.8rem',
                display: 'flex',
                alignItems: 'center',
                gap: 8
              }}>
                <AlertCircle style={{ width: 16, height: 16, color: 'var(--ac-f87171)', flexShrink: 0 }} />
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
                      <Building2 style={{ width: 15, height: 15, color: 'var(--ac-38bdf8)' }} />
                      <span>Kurumsal Kimlik ve Vergi Bilgileri</span>
                    </div>

                    <div className="ui-grid-3" style={{ display: 'grid', gridTemplateColumns: '1.2fr 1fr 1fr', gap: 12 }}>
                      <div>
                        <label className="purchase-label-3d">
                          <Building2 style={{ width: 13, height: 13, color: 'var(--ac-38bdf8)' }} />
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
                          <Hash style={{ width: 13, height: 13, color: 'var(--ac-a78bfa)' }} />
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
                          <Landmark style={{ width: 13, height: 13, color: 'var(--ac-34d399)' }} />
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
                      <Phone style={{ width: 15, height: 15, color: 'var(--ac-fbbf24)' }} />
                      <span>İletişim ve Resmi Adres</span>
                    </div>

                    <div className="ui-grid-3" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 12 }}>
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
                        <div style={{ fontSize: '0.68rem', color: 'var(--nt-94a3b8)', marginTop: 4 }}>
                          * Kurumsal official şirket alan adı zorunludur (Gmail, Hotmail vb. kabul edilmez).
                        </div>
                      </div>

                      <div>
                        <label className="purchase-label-3d">
                          <Phone style={{ width: 13, height: 13, color: 'var(--ac-fbbf24)' }} />
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
                          <Globe style={{ width: 13, height: 13, color: 'var(--ac-60a5fa)' }} />
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
                        <MapPin style={{ width: 13, height: 13, color: 'var(--ac-c084fc)' }} />
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
                    onClick={handleClosePurchaseModal}
                  >
                    Vazgeç / İptal
                  </button>
                  <button id="btn-step1-next" type="submit" className="purchase-btn-next-3d">
                    <span>Devam Et: Sektör & Meslek Grupları</span>
                    <ArrowRight style={{ width: 16, height: 16 }} />
                  </button>
                </div>
              </form>
            )}

            {/* ADIM 2: SEKTÖR & MESLEK GRUPLARI */}
            {step === 2 && (
              <div style={{ display: 'flex', flexDirection: 'column', flex: 1, overflow: 'hidden' }}>
                <div className="purchase-form-scroll-3d">
                  <div className="purchase-section-card-3d">
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 8 }}>
                      <div className="purchase-section-title-3d">
                        <Briefcase style={{ width: 16, height: 16, color: 'var(--ac-818cf8)' }} />
                        <span>1. Faaliyet Sektörleri (T.C. Ticaret Bakanlığı)</span>
                      </div>
                      <span style={{ fontSize: '0.75rem', color: 'var(--nt-94a3b8)' }}>
                        Seçilen Sektör: <strong style={{ color: 'var(--ac-38bdf8)' }}>{selectedSectors.length}</strong>
                      </span>
                    </div>

                    <p style={{ fontSize: '0.78rem', color: 'var(--nt-94a3b8)', margin: 0, lineHeight: 1.5 }}>
                      Şirketinizin faaliyet gösterdiği ana sektörü/sektörleri seçiniz. Seçtiğiniz sektörlere ait resmi meslek grupları aşağıda otomatik filtrelenecektir.
                    </p>

                    <label className="purchase-search">
                      <Search style={{ width: 15, height: 15 }} />
                      <input type="search" value={sectorSearch} onChange={(e) => setSectorSearch(e.target.value)}
                        placeholder="Sektör veya meslek ara (örn. mobilya, kuaför, nakliye)…" aria-label="Sektör ara" />
                    </label>

                    {/* Sektör Seçim Butonları Grid */}
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(min(100%, 200px), 1fr))', gap: 8, marginTop: 4 }}>
                      {visibleSectors.length === 0 && (
                        <span style={{ fontSize: '0.78rem', color: 'var(--nt-94a3b8)' }}>"{sectorSearch}" ile eşleşen sektör bulunamadı.</span>
                      )}
                      {visibleSectors.map((sec) => {
                        const isSelected = selectedSectors.includes(sec.code);
                        return (
                          <button
                            key={sec.code}
                            type="button"
                            onClick={() => handleToggleSector(sec.code)}
                            style={{
                              display: 'flex',
                              alignItems: 'center',
                              justifyContent: 'space-between',
                              padding: '8px 12px',
                              borderRadius: 10,
                              background: isSelected ? 'rgba(99, 102, 241, 0.25)' : 'rgb(var(--rgb-ov) / 0.03)',
                              border: isSelected ? '1px solid rgba(129, 140, 248, 0.8)' : '1px solid rgb(var(--rgb-ov) / 0.08)',
                              color: isSelected ? 'var(--nt-ffffff)' : 'var(--nt-cbd5e1)',
                              cursor: 'pointer',
                              transition: 'all 0.15s ease',
                              textAlign: 'left'
                            }}
                          >
                            <div style={{ display: 'flex', alignItems: 'center', gap: 8, overflow: 'hidden' }}>
                              <span style={{ fontSize: '1.2rem' }}>{sec.icon || '🏢'}</span>
                              <div style={{ display: 'flex', flexDirection: 'column' }}>
                                <span style={{ fontSize: '0.75rem', fontWeight: 700, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                                  [{sec.code}] {sec.name}
                                </span>
                              </div>
                            </div>
                            <span style={{
                              width: 18,
                              height: 18,
                              borderRadius: '50%',
                              background: isSelected ? '#10b981' : 'rgb(var(--rgb-ov) / 0.1)',
                              color: '#fff',
                              display: 'flex',
                              alignItems: 'center',
                              justifyContent: 'center',
                              fontSize: '0.7rem',
                              fontWeight: 800,
                              flexShrink: 0
                            }}>
                              {isSelected ? '✓' : '+'}
                            </span>
                          </button>
                        );
                      })}
                    </div>

                    {/* 2. MESLEK GRUPLARI (Filtreli) */}
                    <div style={{ marginTop: 14, paddingTop: 14, borderTop: '1px solid rgb(var(--rgb-ov) / 0.08)' }}>
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 6 }}>
                        <div className="purchase-section-title-3d">
                          <GraduationCap style={{ width: 16, height: 16, color: 'var(--ac-38bdf8)' }} />
                          <span>2. Meslek Grupları (Seçili Sektörlere Göre Filtrelenmiş)</span>
                        </div>
                        <span style={{ fontSize: '0.75rem', color: 'var(--nt-94a3b8)' }}>
                          Seçilen Meslek: <strong style={{ color: 'var(--ac-38bdf8)' }}>{selectedProfessions.length}</strong>
                        </span>
                      </div>

                      <label className="purchase-search">
                        <Search style={{ width: 15, height: 15 }} />
                        <input type="search" value={professionSearch} onChange={(e) => setProfessionSearch(e.target.value)}
                          placeholder="Tüm meslek gruplarında ara (seçtiğiniz grubun sektörü otomatik eklenir)…" aria-label="Meslek grubu ara" />
                      </label>

                      {selectedSectors.length === 0 && !professionQuery ? (
                        <div style={{ padding: '16px', borderRadius: 10, background: 'rgba(234, 179, 8, 0.06)', border: '1px dashed rgba(234, 179, 8, 0.3)', color: '#fde047', textAlign: 'center', fontSize: '0.8rem', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8 }}>
                          <AlertCircle style={{ width: 16, height: 16 }} />
                          <span>Lütfen önce yukarıdan en az bir <strong>Faaliyet Sektörü</strong> seçiniz. İlgili resmi meslek grupları burada listelenecektir.</span>
                        </div>
                      ) : (
                        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                          <p style={{ fontSize: '0.75rem', color: 'var(--nt-94a3b8)', margin: 0 }}>
                            {professionQuery
                              ? <>Aramanızla eşleşen <strong>{visibleProfessions.length} meslek grubu</strong> bulundu.</>
                              : <>Seçili sektör(ler)e bağlı <strong>{visibleProfessions.length} meslek grubu</strong> bulundu. Şirketiniz bünyesindeki meslek alanlarını işaretleyiniz:</>}
                          </p>

                          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, maxHeight: 180, overflowY: 'auto', padding: 8, borderRadius: 8, background: 'rgb(var(--rgb-shade) / calc(0.3 * var(--shade-k)))', border: '1px solid rgb(var(--rgb-ov) / 0.06)' }}>
                            {visibleProfessions
                              .map((pr) => {
                                const isAdded = selectedProfessions.includes(pr.code);
                                return (
                                  <button
                                    key={pr.code}
                                    type="button"
                                    onClick={() => handleToggleProfession(pr.code)}
                                    style={{
                                      padding: '4px 9px',
                                      borderRadius: 6,
                                      fontSize: '0.72rem',
                                      fontWeight: isAdded ? 700 : 500,
                                      cursor: 'pointer',
                                      display: 'inline-flex',
                                      alignItems: 'center',
                                      gap: 6,
                                      background: isAdded ? 'rgba(56, 189, 248, 0.25)' : 'rgb(var(--rgb-ov) / 0.03)',
                                      border: isAdded ? '1px solid rgba(56, 189, 248, 0.6)' : '1px solid rgb(var(--rgb-ov) / 0.08)',
                                      color: isAdded ? 'var(--ac-38bdf8)' : 'var(--nt-cbd5e1)',
                                      transition: 'all 0.15s ease'
                                    }}
                                  >
                                    <span style={{ fontFamily: 'monospace', fontWeight: 800 }}>[{pr.code}]</span>
                                    <span>{pr.name}</span>
                                    <span>{isAdded ? '✓' : '+'}</span>
                                  </button>
                                );
                              })}
                          </div>
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
                      if (selectedSectors.length === 0) {
                        notify("Lütfen en az bir faaliyet sektörü seçiniz.");
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
                  <div className="ui-grid-2" style={{ display: 'grid', gridTemplateColumns: '1.2fr 1fr', gap: 16 }}>
                    {/* Sol: Yetkili Kullanıcı ve Şifre */}
                    <div className="purchase-section-card-3d">
                      <div className="purchase-section-title-3d">
                        <User style={{ width: 15, height: 15, color: 'var(--ac-38bdf8)' }} />
                        <span>Yetkili Yönetici ve Hesap Bilgileri</span>
                      </div>

                      <div>
                        <label className="purchase-label-3d">
                          <User style={{ width: 13, height: 13, color: 'var(--nt-cbd5e1)' }} />
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
                          <Mail style={{ width: 13, height: 13, color: 'var(--nt-cbd5e1)' }} />
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
                        <div style={{ fontSize: '0.68rem', color: 'var(--nt-94a3b8)', marginTop: 4 }}>
                          * Kurumsal official şirket alan adı zorunludur (Gmail, Hotmail vb. kabul edilmez).
                        </div>
                      </div>

                      {/* E-posta doğrulama kodu */}
                      <div>
                        <label className="purchase-label-3d" htmlFor="input-email-code">
                          <ShieldCheck style={{ width: 13, height: 13, color: 'var(--nt-cbd5e1)' }} />
                          <span>E-Posta Doğrulama Kodu *</span>
                        </label>
                        <div style={{ display: 'flex', gap: 8 }}>
                          <input
                            id="input-email-code"
                            type="text"
                            inputMode="numeric"
                            autoComplete="one-time-code"
                            maxLength={6}
                            required
                            placeholder="6 haneli kod"
                            value={emailCode}
                            onChange={(e) => setEmailCode(e.target.value.replace(/\D/g, ''))}
                            className="purchase-input-field-3d"
                            style={{ letterSpacing: '0.3em', fontFamily: 'var(--font-mono)', flex: 1, minWidth: 0 }}
                          />
                          <button
                            type="button"
                            onClick={handleSendEmailCode}
                            disabled={sendingCode || codeCooldown > 0}
                            className="ui-btn ui-btn-secondary"
                            style={{ flexShrink: 0 }}
                          >
                            {sendingCode ? 'Gönderiliyor…' : codeCooldown > 0 ? `Tekrar (${codeCooldown} sn)` : (codeSentTo ? 'Kodu Tekrar Gönder' : 'Kod Gönder')}
                          </button>
                        </div>
                        <div style={{ fontSize: '0.68rem', color: 'var(--nt-94a3b8)', marginTop: 4 }}>
                          {codeSentTo === contactEmail.trim().toLowerCase() && codeSentTo
                            ? `Kod ${codeSentTo} adresine gönderildi; 10 dakika geçerlidir.`
                            : 'Başvurunuzu tamamlamak için e-posta adresinizi doğrulayın.'}
                        </div>
                        {/* Bot tuzağı: ekranda görünmez, gerçek kullanıcılar doldurmaz */}
                        <input
                          type="text"
                          name="company_fax"
                          tabIndex={-1}
                          autoComplete="off"
                          aria-hidden="true"
                          value={companyFax}
                          onChange={(e) => setCompanyFax(e.target.value)}
                          style={{ position: 'absolute', left: '-10000px', width: 1, height: 1, opacity: 0 }}
                        />
                      </div>

                      {/* Şifre ve Güçlü Şifre Oluşturucu */}
                      <div>
                        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 5 }}>
                          <label className="purchase-label-3d" style={{ margin: 0 }}>
                            <Lock style={{ width: 13, height: 13, color: 'var(--nt-cbd5e1)' }} />
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
                            placeholder="En az 8 karakter..." 
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
                                  background: 'rgb(var(--rgb-ov) / 0.08)',
                                  border: 'none',
                                  borderRadius: 6,
                                  padding: '4px 6px',
                                  color: 'var(--nt-cbd5e1)',
                                  cursor: 'pointer',
                                  display: 'flex',
                                  alignItems: 'center',
                                  gap: 3,
                                  fontSize: '0.68rem'
                                }}
                                title="Şifreyi panoya kopyala"
                              >
                                {copiedKey === 'wizardpass' ? <Check style={{ width: 12, height: 12, color: 'var(--ac-34d399)' }} /> : <Copy style={{ width: 12, height: 12 }} />}
                              </button>
                            )}
                            <button
                              type="button"
                              onClick={() => setShowPassword(!showPassword)}
                              style={{
                                background: 'transparent',
                                border: 'none',
                                color: 'var(--nt-94a3b8)',
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
                          <span style={{ fontSize: '0.72rem', fontWeight: 800, textTransform: 'uppercase', color: 'var(--ac-c084fc)', letterSpacing: '0.05em' }}>
                            SEÇİLEN KURUMSAL PAKET
                          </span>
                          <span className="purchase-plan-badge-3d">
                            👑 {selectedPlan.name}
                          </span>
                        </div>

                        <div style={{ display: 'flex', alignItems: 'baseline', gap: 6, padding: '10px 14px', borderRadius: 12, background: 'rgb(var(--rgb-shade) / calc(0.3 * var(--shade-k)))', border: '1px solid rgb(var(--rgb-ov) / 0.06)' }}>
                          <span style={{ fontSize: '1.4rem', fontWeight: 900, color: 'var(--ac-38bdf8)', fontFamily: 'Outfit, sans-serif' }}>
                            {Number(selectedPlan.monthly_price).toLocaleString('tr-TR')} ₺
                          </span>
                          <span style={{ fontSize: '0.775rem', color: 'var(--nt-94a3b8)' }}>/ Ay (Yıllık Kurumsal Sözleşme)</span>
                        </div>

                        {/* Paket Değiştirme Opsiyonu */}
                        {plans.length > 1 && (
                          <div>
                            <label style={{ display: 'block', fontSize: '0.68rem', fontWeight: 700, color: 'var(--nt-94a3b8)', marginBottom: 4 }}>
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

                        <div style={{ display: 'flex', flexDirection: 'column', gap: 6, fontSize: '0.75rem', color: 'var(--nt-cbd5e1)' }}>
                          <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                            <CheckCircle2 style={{ width: 14, height: 14, color: 'var(--ac-34d399)' }} />
                            <span><b>{selectedPlan.max_agents} AI Ajan</b> ve <b>{selectedPlan.max_humans} İnsan</b> Kullanıcı</span>
                          </div>
                          <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                            <CheckCircle2 style={{ width: 14, height: 14, color: 'var(--ac-34d399)' }} />
                            <span><b>{selectedPlan.storage_gb} GB</b> İzole MinIO Bulut Depolama</span>
                          </div>
                          <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                            <CheckCircle2 style={{ width: 14, height: 14, color: 'var(--ac-34d399)' }} />
                            <span><b>{selectedSectors.length} Sektör & {selectedProfessions.length} Meslek</b> Odaklı AI Manifestosu</span>
                          </div>
                        </div>
                      </div>

                      <div style={{ padding: '10px 12px', borderRadius: 10, background: 'rgba(2,132,199,0.1)', border: '1px solid rgba(2,132,199,0.25)', fontSize: '0.72rem', color: 'var(--ac-7dd3fc)', lineHeight: 1.4, marginTop: 10 }}>
                        📌 Başvurunuz RECDx ekibi tarafından incelendikten sonra hesabınız aktifleştirilecek ve <b>{contactEmail || 'kurumsal adresinize'}</b> aktivasyon e-postası gönderilecektir.
                      </div>
                    </div>
                  </div>

                  {/* ADIM 13.1: Odoo ve RECDx uygulamaları (isteğe bağlı) */}
                  {recdxApps && (
                    <div className="purchase-section-card-3d" style={{ marginTop: 16 }}>
                      <div className="purchase-section-title-3d"><span>Odoo ve RECDx uygulamaları (isteğe bağlı)</span></div>
                      <RecdxAppsChoice apps={recdxApps} value={appChoice} onChange={setAppChoice} idPrefix="buy" />
                    </div>
                  )}
                </div>

                <div className="purchase-footer-3d">
                  <button type="button" className="purchase-btn-back-3d" onClick={() => setStep(2)} disabled={submitting}>
                    <ChevronLeft style={{ width: 16, height: 16 }} />
                    <span>← Geri: Sektör & Meslek Seçimi</span>
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
                        <span>Kayıt Tamamlanıyor...</span>
                      </>
                    ) : (
                      <>
                        <CheckCircle2 style={{ width: 16, height: 16 }} />
                        <span>KAYIT TAMAMLA</span>
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
                      border: '1px solid rgb(var(--rgb-ov) / 0.3)'
                    }}>
                      🎉
                    </div>

                    <div>
                      <h3 style={{ fontSize: '1.25rem', fontWeight: 800, color: 'var(--nt-ffffff)', margin: 0 }}>
                        Kiralama Talebiniz Başarıyla Alındı!
                      </h3>
                      <p style={{ fontSize: '0.8rem', color: 'var(--nt-94a3b8)', marginTop: 4 }}>
                        '{companyName}' kurumu için sipariş kaydı oluşturuldu ve şirket ortamınız hazırlandı.
                      </p>
                    </div>

                    {/* Bildirim Durumları */}
                    <div className="ui-grid-2" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10, width: '100%', maxWidth: 650 }}>
                      <div style={{ padding: '10px 14px', borderRadius: 10, background: 'rgba(16,185,129,0.1)', border: '1px solid rgba(16,185,129,0.25)', display: 'flex', alignItems: 'center', gap: 8, fontSize: '0.75rem', color: 'var(--ac-6ee7b7)' }}>
                        <CheckCircle2 style={{ width: 16, height: 16, color: 'var(--ac-34d399)', flexShrink: 0 }} />
                        <span><b>info@recdx.com</b> adresine Süper Admin bildirimi gönderildi.</span>
                      </div>
                      <div style={{ padding: '10px 14px', borderRadius: 10, background: 'rgba(16,185,129,0.1)', border: '1px solid rgba(16,185,129,0.25)', display: 'flex', alignItems: 'center', gap: 8, fontSize: '0.75rem', color: 'var(--ac-6ee7b7)' }}>
                        <CheckCircle2 style={{ width: 16, height: 16, color: 'var(--ac-34d399)', flexShrink: 0 }} />
                        <span><b>{purchaseResult.contact_email}</b> adresinize kurumsal karşılama iletildi.</span>
                      </div>
                    </div>

                    {/* AI Manifestosu Önizleme */}
                    <div style={{ width: '100%', maxWidth: 760, borderRadius: 14, background: 'var(--sf-080c18)', border: '1px solid rgba(113,52,226,0.3)', overflow: 'hidden', textAlign: 'left' }}>
                      <div style={{ padding: '10px 14px', background: 'rgb(var(--rgb-ov) / 0.03)', borderBottom: '1px solid rgb(var(--rgb-ov) / 0.06)', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: '0.785rem', fontWeight: 700, color: 'var(--ac-c084fc)' }}>
                          <Sparkles style={{ width: 14, height: 14 }} />
                          <span>RECAi Tarafından Üretilen Kurumsal Manifesto</span>
                        </div>
                        <span style={{ fontSize: '0.7rem', padding: '2px 8px', borderRadius: 999, background: 'rgba(56,189,248,0.2)', color: 'var(--ac-38bdf8)' }}>
                          {purchaseResult.assigned_skills?.length || 0} Yetenek Atandı
                        </span>
                      </div>
                      <pre style={{ margin: 0, padding: '12px 14px', fontSize: '0.75rem', color: 'var(--nt-94a3b8)', lineHeight: 1.6, maxHeight: 160, overflowY: 'auto', whiteSpace: 'pre-wrap', fontFamily: 'monospace' }}>
                        {purchaseResult.generated_manifesto}
                      </pre>
                    </div>

                    {/* Atanan Sektörel Yetenekler */}
                    {purchaseResult.assigned_skills?.length > 0 && (
                      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, justifyContent: 'center', maxWidth: 760 }}>
                        {purchaseResult.assigned_skills.map(s => (
                          <span key={s} style={{ padding: '3px 10px', borderRadius: 999, background: 'rgba(113,52,226,0.2)', border: '1px solid rgba(113,52,226,0.4)', color: 'var(--ac-d8b4fe)', fontSize: '0.72rem', fontWeight: 600 }}>
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
                      handleClosePurchaseModal();
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
            <div className="modal-header" style={{ padding: '20px 24px', borderBottom: '1px solid rgb(var(--rgb-ov) / 0.08)' }}>
              <div>
                <h3 className="modal-title" style={{ fontSize: '1.2rem', fontWeight: 800, color: 'var(--nt-ffffff)', display: 'flex', alignItems: 'center', gap: 8 }}>
                  <span>🔐 RECOrion Şirket Girişi</span>
                </h3>
                <p style={{ fontSize: '0.75rem', color: 'var(--nt-94a3b8)', margin: '4px 0 0 0' }}>
                  Yönetim veya çalışma alanı paneline güvenli erişim sağlayın.
                </p>
              </div>
              <button className="btn-close" onClick={() => setIsLoginModalOpen(false)}>✕</button>
            </div>

            <form onSubmit={handleRealLogin} method="post" autoComplete="on" style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '18px' }}>
              {loginError && (
                <div style={{ padding: '10px 14px', borderRadius: '12px', background: 'rgba(239, 68, 68, 0.15)', border: '1px solid rgba(239, 68, 68, 0.4)', color: 'var(--ac-fca5a5)', fontSize: '0.825rem', display: 'flex', alignItems: 'center', gap: 8 }}>
                  <span>⚠️</span>
                  <span>{loginError}</span>
                </div>
              )}

              {/* Kurumsal E-Posta */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: 6, width: '100%' }}>
                <label htmlFor="login-username" style={{ fontSize: '0.8rem', fontWeight: 700, color: 'var(--nt-cbd5e1)', display: 'flex', alignItems: 'center', gap: 6 }}>
                  <span>✉️ Kurumsal E-Posta Adresi</span>
                </label>
                <input 
                  type="email" 
                  id="login-username"
                  name="username"
                  autoComplete="username"
                  required 
                  placeholder="ornek: cuneyterdil@recx.com"
                  value={loginEmail}
                  onChange={(e) => setLoginEmail(e.target.value)}
                  className="login-input-3d"
                />
              </div>

              {/* Şifre */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: 6, width: '100%' }}>
                <label htmlFor="login-password" style={{ fontSize: '0.8rem', fontWeight: 700, color: 'var(--nt-cbd5e1)', display: 'flex', alignItems: 'center', gap: 6 }}>
                  <span>🔑 Güvenli Şifre</span>
                </label>
                <input 
                  type="password" 
                  id="login-password"
                  name="password"
                  autoComplete="current-password"
                  required 
                  placeholder="••••••••••••"
                  value={loginPassword}
                  onChange={(e) => setLoginPassword(e.target.value)}
                  className="login-input-3d"
                />
              </div>

              {/* Beni Hatırla (Remember Me) */}
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '2px 0' }}>
                <label style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer', fontSize: '0.82rem', color: 'var(--nt-cbd5e1)', userSelect: 'none' }}>
                  <input
                    type="checkbox"
                    name="remember"
                    id="login-remember-me"
                    checked={rememberMe}
                    onChange={(e) => setRememberMe(e.target.checked)}
                    style={{ width: 16, height: 16, accentColor: '#7134e2', cursor: 'pointer' }}
                  />
                  <span>Beni Hatırla</span>
                </label>
                <button
                  type="button"
                  onClick={handleForgotPassword}
                  style={{ background: 'none', border: 'none', color: 'var(--ac-818cf8)', fontSize: '0.8rem', fontWeight: 600, cursor: 'pointer', padding: 0 }}
                >
                  Şifremi unuttum
                </button>
              </div>

              {/* Giriş Butonu */}
              <div style={{ marginTop: 4 }}>
                <button type="submit" className="login-btn-submit-3d" disabled={isLoggingIn}>
                  {isLoggingIn ? (
                    <>
                      <span className="spinner-border spinner-border-sm" role="status" aria-hidden="true" style={{ width: 16, height: 16, border: '2px solid rgb(var(--rgb-ov) / 0.3)', borderTopColor: '#fff', borderRadius: '50%', display: 'inline-block', animation: 'spin 0.8s linear infinite' }}></span>
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
