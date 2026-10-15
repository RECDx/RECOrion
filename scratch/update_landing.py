with open('frontend/src/components/OfficialLanding.jsx', 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Comment
text = text.replace(
    '// 1: Şirket Bilgileri, 2: NACE Kodları, 3: Yetkili & Şifre, 4: Başarı',
    '// 1: Şirket Bilgileri, 2: Sektör & Meslek Grupları, 3: Yetkili & Şifre, 4: Başarı'
)

# 2. Stats and badges
text = text.replace('<span className="stat-label">NACE Faaliyet Alanı</span>', '<span className="stat-label">Sektör & Meslek Grubu</span>')
text = text.replace('<span>Otomatik AI NACE Manifestosu</span>', '<span>Otomatik Kurumsal AI Manifestosu</span>')
text = text.replace('<span><b>{selectedNaces.length} NACE Kodu</b> Odaklı AI Manifestosu</span>', '<span><b>{selectedSectors.length} Sektör & {selectedProfessions.length} Meslek</b> Odaklı AI Manifestosu</span>')
text = text.replace('<span>← Geri: NACE Seçimi</span>', '<span>← Geri: Sektör & Meslek Seçimi</span>')

# 3. Replace Step 2
start_marker = '{/* ADIM 2: NACE FAALİYET ALANLARI */}'
end_marker = '{/* ADIM 3: YETKİLİ HESAP & ŞİFRE */}'

idx_start = text.find(start_marker)
idx_end = text.find(end_marker)

if idx_start == -1 or idx_end == -1:
    print('ERROR: markers not found')
    exit(1)

new_step2 = '''{/* ADIM 2: SEKTÖR & MESLEK GRUPLARI */}
            {step === 2 && (
              <div style={{ display: 'flex', flexDirection: 'column', flex: 1, overflow: 'hidden' }}>
                <div className="purchase-form-scroll-3d">
                  <div className="purchase-section-card-3d">
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 8 }}>
                      <div className="purchase-section-title-3d">
                        <Briefcase style={{ width: 16, height: 16, color: '#818cf8' }} />
                        <span>1. Faaliyet Sektörleri (T.C. Ticaret Bakanlığı)</span>
                      </div>
                      <span style={{ fontSize: '0.75rem', color: '#94a3b8' }}>
                        Seçilen Sektör: <strong style={{ color: '#38bdf8' }}>{selectedSectors.length}</strong>
                      </span>
                    </div>

                    <p style={{ fontSize: '0.78rem', color: '#94a3b8', margin: 0, lineHeight: 1.5 }}>
                      Şirketinizin faaliyet gösterdiği ana sektörü/sektörleri seçiniz. Seçtiğiniz sektörlere ait resmi meslek grupları aşağıda otomatik filtrelenecektir.
                    </p>

                    {/* Sektör Seçim Butonları Grid */}
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: 8, marginTop: 4 }}>
                      {sectors.map((sec) => {
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
                              background: isSelected ? 'rgba(99, 102, 241, 0.25)' : 'rgba(255, 255, 255, 0.03)',
                              border: isSelected ? '1px solid rgba(129, 140, 248, 0.8)' : '1px solid rgba(255, 255, 255, 0.08)',
                              color: isSelected ? '#ffffff' : '#cbd5e1',
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
                              background: isSelected ? '#10b981' : 'rgba(255,255,255,0.1)',
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
                    <div style={{ marginTop: 14, paddingTop: 14, borderTop: '1px solid rgba(255,255,255,0.08)' }}>
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 6 }}>
                        <div className="purchase-section-title-3d">
                          <GraduationCap style={{ width: 16, height: 16, color: '#38bdf8' }} />
                          <span>2. Meslek Grupları (Seçili Sektörlere Göre Filtrelenmiş)</span>
                        </div>
                        <span style={{ fontSize: '0.75rem', color: '#94a3b8' }}>
                          Seçilen Meslek: <strong style={{ color: '#38bdf8' }}>{selectedProfessions.length}</strong>
                        </span>
                      </div>

                      {selectedSectors.length === 0 ? (
                        <div style={{ padding: '16px', borderRadius: 10, background: 'rgba(234, 179, 8, 0.06)', border: '1px dashed rgba(234, 179, 8, 0.3)', color: '#fde047', textAlign: 'center', fontSize: '0.8rem', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8 }}>
                          <AlertCircle style={{ width: 16, height: 16 }} />
                          <span>Lütfen önce yukarıdan en az bir <strong>Faaliyet Sektörü</strong> seçiniz. İlgili resmi meslek grupları burada listelenecektir.</span>
                        </div>
                      ) : (
                        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                          <p style={{ fontSize: '0.75rem', color: '#94a3b8', margin: 0 }}>
                            Seçili sektör(ler)e bağlı <strong>{professions.filter(pr => selectedSectors.includes(pr.sector_code)).length} meslek grubu</strong> bulundu. Şirketiniz bünyesindeki meslek alanlarını işaretleyiniz:
                          </p>

                          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, maxHeight: 180, overflowY: 'auto', padding: 8, borderRadius: 8, background: 'rgba(0,0,0,0.3)', border: '1px solid rgba(255,255,255,0.06)' }}>
                            {professions
                              .filter(pr => selectedSectors.includes(pr.sector_code))
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
                                      background: isAdded ? 'rgba(56, 189, 248, 0.25)' : 'rgba(255, 255, 255, 0.03)',
                                      border: isAdded ? '1px solid rgba(56, 189, 248, 0.6)' : '1px solid rgba(255, 255, 255, 0.08)',
                                      color: isAdded ? '#38bdf8' : '#cbd5e1',
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
                        alert("Lütfen en az bir faaliyet sektörü seçiniz.");
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

            '''

text = text[:idx_start] + new_step2 + text[idx_end:]

with open('frontend/src/components/OfficialLanding.jsx', 'w', encoding='utf-8') as f:
    f.write(text)

print('OfficialLanding.jsx successfully updated!')
