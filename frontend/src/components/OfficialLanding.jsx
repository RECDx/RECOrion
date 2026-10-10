import React, { useState, useEffect } from 'react';
import { api } from '../api';
import AdminLeadsModal from './AdminLeadsModal';

export default function OfficialLanding({ onEnterWorkspace, currentUser, onLogout }) {
  const [plans, setPlans] = useState([]);
  const [loadingPlans, setLoadingPlans] = useState(true);
  const [isLeadsModalOpen, setIsLeadsModalOpen] = useState(false);
  
  // Satın Alma Modalı State'leri
  const [isPurchaseModalOpen, setIsPurchaseModalOpen] = useState(false);
  const [selectedPlan, setSelectedPlan] = useState(null);
  const [step, setStep] = useState(1); // 1: Şirket Bilgileri, 2: NACE Kodları, 3: Yetkili/Şifre, 4: Başarı & Manifesto
  
  // Form Bilgileri
  const [companyName, setCompanyName] = useState('');
  const [taxId, setTaxId] = useState('');
  const [taxOffice, setTaxOffice] = useState('');
  const [phone, setPhone] = useState('');
  const [website, setWebsite] = useState('');
  const [address, setAddress] = useState('');
  const [contactName, setContactName] = useState('');
  const [contactEmail, setContactEmail] = useState('');
  const [password, setPassword] = useState('');
  
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

      {/* SATIN ALMA / KİRALAMA WIZARD MODALI */}
      {isPurchaseModalOpen && selectedPlan && (
        <div className="modal-backdrop">
          <div className="purchase-modal-card">
            <div className="modal-header">
              <div>
                <h3 className="modal-title">
                  {selectedPlan.name} Kiralama Başvurusu
                </h3>
                <span className="modal-subtitle">
                  {Number(selectedPlan.monthly_price).toLocaleString('tr-TR')} ₺/Ay — Adım {step} / 3
                </span>
              </div>
              <button className="btn-close" onClick={() => setIsPurchaseModalOpen(false)}>✕</button>
            </div>

            {errorMessage && (
              <div className="alert-error-box">
                ⚠️ {errorMessage}
              </div>
            )}

            {/* ADIM 1: ŞİRKET BİLGİLERİ */}
            {step === 1 && (
              <form onSubmit={(e) => { e.preventDefault(); setStep(2); }} className="wizard-form-body">
                <h4 className="form-step-title">1. Şirket ve İletişim Bilgileri</h4>
                <div className="form-group">
                  <label>Şirket Ünvanı *</label>
                  <input 
                    id="input-company-name"
                    type="text" 
                    required 
                    placeholder="Örn: Atlas Teknoloji ve Bilişim A.Ş." 
                    value={companyName}
                    onChange={(e) => setCompanyName(e.target.value)}
                  />
                </div>

                <div className="form-row-2">
                  <div className="form-group">
                    <label>Telefon Numarası *</label>
                    <input 
                      id="input-phone"
                      type="tel" 
                      required 
                      placeholder="+90 532 ..." 
                      value={phone}
                      onChange={(e) => setPhone(e.target.value)}
                    />
                  </div>
                  <div className="form-group">
                    <label>Vergi Dairesi</label>
                    <input 
                      id="input-tax-office"
                      type="text" 
                      placeholder="Örn: Kadıköy V.D." 
                      value={taxOffice}
                      onChange={(e) => setTaxOffice(e.target.value)}
                    />
                  </div>
                </div>

                <div className="form-group">
                  <label>Vergi Numarası (VKN / TCKN)</label>
                  <input 
                    id="input-tax-id"
                    type="text" 
                    placeholder="10 veya 11 Haneli Vergi No" 
                    value={taxId}
                    onChange={(e) => setTaxId(e.target.value)}
                  />
                </div>

                <div className="form-group">
                  <label>Web Sitesi</label>
                  <input 
                    id="input-website"
                    type="url" 
                    placeholder="https://..." 
                    value={website}
                    onChange={(e) => setWebsite(e.target.value)}
                  />
                </div>

                <div className="form-group">
                  <label>Şirket Adresi</label>
                  <textarea 
                    id="input-address"
                    rows={2} 
                    placeholder="Şirket merkezi adresi..." 
                    value={address}
                    onChange={(e) => setAddress(e.target.value)}
                  />
                </div>

                <div className="wizard-footer">
                  <button type="button" className="btn-secondary" onClick={() => setIsPurchaseModalOpen(false)}>
                    İptal
                  </button>
                  <button id="btn-step1-next" type="submit" className="btn-primary">
                    Devam Et: NACE Faaliyet Seçimi →
                  </button>
                </div>
              </form>
            )}

            {/* ADIM 2: NACE FAALİYET ALANLARI */}
            {step === 2 && (
              <div className="wizard-form-body">
                <h4 className="form-step-title">2. NACE Faaliyet Alanları Seçimi</h4>
                <p className="step-hint">
                  Şirketinizin faaliyet alanını seçin. RECOrion, bu kodlara göre şirketinize özel 
                  <b> Yapay Zeka Operasyon Manifestosu</b> oluşturacaktır.
                </p>

                <div className="form-group">
                  <label>NACE Kodu veya Faaliyet Adı ile Ara (2.164 Kod)</label>
                  <input 
                    id="input-nace-search"
                    type="text" 
                    placeholder="Örn: yazılım, bilgisayar, danışmanlık, 621000..." 
                    value={naceQuery}
                    onChange={(e) => setNaceQuery(e.target.value)}
                  />
                </div>

                {isSearchingNace && <div className="searching-text">Aranıyor...</div>}

                {naceResults.length > 0 && (
                  <div className="nace-search-dropdown" id="nace-search-results">
                    {naceResults.map((n) => (
                      <div key={n.code} className="nace-search-item" onClick={() => handleAddNace(n)}>
                        <span className="nace-item-code">{n.code}</span>
                        <span className="nace-item-title">{n.title}</span>
                      </div>
                    ))}
                  </div>
                )}

                <div className="selected-naces-section">
                  <label>Seçilen NACE Faaliyet Kodları ({selectedNaces.length}):</label>
                  {selectedNaces.length === 0 ? (
                    <div className="empty-nace-hint">Henüz NACE kodu seçilmedi. Yukarıdaki arama kutusunu kullanın.</div>
                  ) : (
                    <div className="nace-tags-container">
                      {selectedNaces.map((n) => (
                        <div key={n.code} className="nace-tag-chip">
                          <span className="tag-code">{n.code}</span>
                          <span className="tag-title">{n.title.substring(0, 40)}...</span>
                          <button className="tag-remove" onClick={() => handleRemoveNace(n.code)}>✕</button>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                <div className="wizard-footer">
                  <button type="button" className="btn-secondary" onClick={() => setStep(1)}>
                    ← Geri: Şirket Bilgileri
                  </button>
                  <button 
                    id="btn-step2-next"
                    type="button" 
                    className="btn-primary" 
                    onClick={() => {
                      if (selectedNaces.length === 0) {
                        alert("Lütfen en az bir NACE faaliyet alanı seçiniz.");
                        return;
                      }
                      setStep(3);
                    }}
                  >
                    Devam Et: Yetkili Hesap & Şifre →
                  </button>
                </div>
              </div>
            )}

            {/* ADIM 3: YETKİLİ HESAP & ŞİFRE */}
            {step === 3 && (
              <form onSubmit={handleSubmitPurchase} className="wizard-form-body">
                <h4 className="form-step-title">3. Yetkili Kullanıcı ve Şifre Oluşturma</h4>
                <p className="step-hint">
                  Belirleyeceğiniz şifre ile satın alma sonrasında şirketinize tahsis edilecek panele giriş yapabileceksiniz.
                </p>

                <div className="form-group">
                  <label>Yetkili Adı Soyadı *</label>
                  <input 
                    id="input-contact-name"
                    type="text" 
                    required 
                    placeholder="Örn: Cüneyt Özdemir" 
                    value={contactName}
                    onChange={(e) => setContactName(e.target.value)}
                  />
                </div>

                <div className="form-group">
                  <label>Yetkili E-Posta Adresi (Giriş İçin Kullanılacak) *</label>
                  <input 
                    id="input-contact-email"
                    type="email" 
                    required 
                    placeholder="ornek@sirketiniz.com" 
                    value={contactEmail}
                    onChange={(e) => setContactEmail(e.target.value)}
                  />
                </div>

                <div className="form-group">
                  <label>Giriş Şifresi *</label>
                  <input 
                    id="input-password"
                    type="password" 
                    required 
                    placeholder="Güçlü bir şifre belirleyin" 
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                  />
                </div>

                <div className="summary-alert-box">
                  <p><b>Seçilen Paket:</b> {selectedPlan.name} ({Number(selectedPlan.monthly_price).toLocaleString('tr-TR')} ₺/Ay)</p>
                  <p><b>Faaliyet Alanları:</b> {selectedNaces.map(n => n.code).join(', ')}</p>
                  <p className="notification-note">
                    📌 Başvurunuz tamamlandığında <b>info@recdx.com</b> adresine bildirim gidecek ve <b>{contactEmail || 'e-posta adresinize'}</b> onay mektubu iletilecektir.
                  </p>
                </div>

                <div className="wizard-footer">
                  <button type="button" className="btn-secondary" onClick={() => setStep(2)} disabled={submitting}>
                    ← Geri: NACE Seçimi
                  </button>
                  <button id="btn-submit-purchase" type="submit" className="btn-primary btn-submit-purchase" disabled={submitting}>
                    {submitting ? '⏳ AI Manifestoyu Yazıyor & İletiliyor...' : '✅ Satın Alma Talebini Tamamla'}
                  </button>
                </div>
              </form>
            )}

            {/* ADIM 4: BAŞARI VE MANİFESTO GÖSTERİMİ */}
            {step === 4 && purchaseResult && (
              <div className="wizard-form-body success-step-body">
                <div className="success-icon-banner">🎉</div>
                <h4 className="success-title">Kiralama Talebiniz Başarıyla Alındı!</h4>
                <p className="success-subtitle">
                  Talebiniz işleme alınmış ve ilgili birimlere iletilmiştir.
                </p>

                <div className="notifications-status-card">
                  <div className="notify-row">
                    <span className="notify-badge ok">✓ İletildi</span>
                    <span><b>info@recdx.com</b> adresine RECDx yönetim bildirimi gönderildi.</span>
                  </div>
                  <div className="notify-row">
                    <span className="notify-badge ok">✓ İletildi</span>
                    <span><b>{purchaseResult.contact_email}</b> adresinize kurumsal karşılama e-postası gönderildi.</span>
                  </div>
                </div>

                <div className="manifesto-preview-box">
                  <div className="manifesto-box-header">
                    <span>📜 AI Tarafından Üretilen Kurumsal Yapay Zeka Manifestosu</span>
                    <span className="badge-sector">{purchaseResult.assigned_skills?.length} Yetenek Tanımlandı</span>
                  </div>
                  <pre className="manifesto-code-text">
                    {purchaseResult.generated_manifesto}
                  </pre>
                </div>

                <div className="assigned-skills-row">
                  <span className="skills-label">Şirketinize Atanan Sektörel Beceriler:</span>
                  <div className="skills-wrap">
                    {purchaseResult.assigned_skills?.map(s => (
                      <span key={s} className="skill-chip">{s}</span>
                    ))}
                  </div>
                </div>

                <div className="wizard-footer success-footer">
                  <button 
                    id="btn-go-to-workspace" 
                    className="btn-primary" 
                    onClick={() => {
                      setIsPurchaseModalOpen(false);
                      setIsLoginModalOpen(true);
                    }}
                  >
                    🔑 Giriş Ekranına Git →
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
