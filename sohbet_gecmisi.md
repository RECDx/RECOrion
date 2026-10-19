# RECOrion Projesi - Geliştirme, Mimari Kararlar ve Değişiklik Geçmişi (sohbet_gecmisi.md)

Bu doküman, bu oturum boyunca gerçekleştirilen tüm sistem revizyonlarını, alınan mimari kararları, veritabanı DDL/DML operasyonlarını, backend API ve frontend değişikliklerini, hata tespit ve çözüm süreçlerini en ince ayrıntısına kadar içermektedir.

---

## 1. GENEL KAPSAM VE KULLANICI TALEPLERİ

Oturum süresince üç temel aşama halinde geliştirme ve revizyon talepleri alınmış ve eksiksiz uygulanmıştır:

### 1. Aşama: Şirket Yapılandırması, Süper Admin Hesapları ve Kurumsal E-posta Zorunluluğu
1. **Tek Ana Şirket Kuralı:** Sistemde yalnızca **"RECDx Teknoloji & Dijital Dönüşüm Danışmanlığı LTD. Şirketi"** tanımlı kalacak. Bu şirket ana şirket (Master Tenant) olup sistemden silinemez.
2. **Süper Admin Kullanıcıları:**
   - `cuneyterdil@recx.com` (Şifre: `mce*1501`)
   - `rehaerdag@recdx.com` (Şifre: `samil+2011`)
3. **Eski/Gereksiz Şirketlerin Silinmesi:**
   - `RECDx Bilişim Teknolojileri ve Yapay Zeka A.Ş.`
   - `RECOrion Teknoloji A.Ş.`
4. **Resmi/Kurumsal E-posta Doğrulama Kuralı:**
   - Süper yönetici manuel müşteri eklerken resmi şirket e-posta adresi zorunlu olacak. Public uzantılar (`gmail.com`, `hotmail.com`, `yahoo.com`, `outlook.com` vb.) engellenecek.
   - Müşteri adayı web sitesi üzerinden paket satın alırken / kayıt olurken aynı şekilde kurumsal e-posta adresi girmek zorunda olacak.

### 2. Aşama: NACE Kodlarının Kaldırılması ve T.C. Ticaret Bakanlığı Sektör/Meslek Modeline Geçiş
1. **Köklü Mimari Değişiklik:** Müşteriler artık NACE Kodları ile takip edilmeyecektir.
   - NACE tabloları (`nace_catalog`), eski sektör tanımları (`sector_definitions`), unvanlar (`job_titles`) ve departmanlar (`departments`) veritabanından tamamen temizlenecek.
   - Tüm NACE referansları sistem kodundan, API uçlarından, manifesto üreticisinden ve arayüzlerden kaldırılacak.
2. **Yeni Tanımlama Modülleri:**
   - **Sektör Tanımlama Modülü:** Sektör Kodu (`code`), Sektör Adı (`name`), Açıklama, İkon, Durum.
   - **Meslek Tanımı Modülü:** Meslek Kodu (`code`), Bağlı Olduğu Sektör Kodu (`sector_code`), Meslek Tanım Adı (`name`), Açıklama, Durum.
   - Müşteri oluşturma ve düzenleme ekranlarında sektör seçilecek ve seçilen sektöre bağlı meslek grupları dinamik filtrelenecek.
3. **T.C. Ticaret Bakanlığı Excel Kataloğunun Yüklenmesi:**
   - Kaynak: `documents/Sektör Meslek Nace Kodları_2026.03.xlsx`
   - Excel taranarak resmi sektörlerin ve meslek gruplarının veritabanına aktarılması.
4. **Giriş (Login) Ekranı Revizyonu:**
   - Hızlı Giriş butonları (`cuneyterdil@recdx.com`, `info@recdx.com`) modalden kaldırılacak.
   - "Beni Hatırla" (Remember Me) onay kutusu eklenecek.
   - Tarayıcı (Chrome) şifre yöneticisinin şifreyi kaydetmeyi önerebilmesi için W3C standartlarına uygun form ve input yapıları kurulacak.

### 3. Aşama: Verilerin Temizlenmesi, Yeniden Yükleme ve YAPI SANATLARI Doğrulaması
1. **Veri Sıfırlama:** Sektör ve meslek grubu tabloları tamamen boşaltılacak.
2. **İki Aşamalı Veri Yükleme:**
   - Önce Excel'deki tüm sektörler (A'dan K'ya 11 sektör) eksiksiz alınacak.
   - Ardından tüm meslek grupları (184 meslek tanımı) ilişkili sektör kodlarıyla birlikte aktarılacak.
3. **YAPI SANATLARI (K) Özel Kontrolü:** K sektörüne bağlı 15 meslek grubunun veritabanında, API'de ve arayüzde eksiksiz listelenmesi sağlanacak.

---

## 2. ALINAN MİMARİ KARARLAR

### 2.1. NACE'den Ticaret Bakanlığı Hiyerarşisine Geçiş
- **Sorun:** 6 haneli Avrupa NACE kodları (Rev. 2) çok karmaşık, şirket faaliyetlerini sınıflandırmada pratiklikten uzak ve yapay zeka ajanlarının şirket departman/meslek rollerini doğrudan modellemesinde gereksiz dallanmaya yol açıyordu.
- **Karar:** T.C. Ticaret Bakanlığı'nın Esnaf ve Sanatkarlar ile Meslek Kuruluşları için yayınladığı resmi **11 Ana Sektör (`A`-`K`)** ve **184 Meslek Grubu (`A.01`-`K.15`)** hiyerarşisi RECOrion'un çekirdek faaliyet modeli olarak kabul edildi.
- **İlişki Yapısı:**
  - `Sector` (PK: `code`, VARCHAR(32)) 1 — ∞ `Profession` (PK: `code`, VARCHAR(32), FK: `sector_code` -> `sectors.code`).
  - `Tenant` ve `TenantLead` tablolarında `sectors` (JSONB dizi) ve `professions` (JSONB dizi) alanları kullanılarak çoklu sektör ve çoklu meslek grubu seçimi desteklendi.

### 2.2. Kurumsal Manifesto Üretimi (Manifesto Service)
- Manifesto servisindeki AI istemi (prompt), NACE kodları yerine şirketin seçtiği `sectors` ve `professions` verilerini alacak şekilde güncellendi.
- Böylece üretilen kurumsal vizyon metinleri, doğrudan Türkiye Ticaret Bakanlığı'nın resmi meslek ve faaliyet tanımlarını referans alır hale geldi.

### 2.3. Frontend İki Kademeli Filtreleme (Cascading Filter)
- Müşteri kayıt formlarında (hem Süper Admin konsolunda hem de Landing Page paket satın alma modalinde):
  - Üst alanda sektörler listelenir.
  - Sektör seçilmediğinde Meslek Grupları alanı kullanıcıyı uyarır ("Lütfen önce en az bir faaliyet sektörü seçiniz").
  - Bir veya birden fazla sektör seçildiğinde, meslek listesi anında `selectedSectors.includes(p.sector_code)` mantığıyla filtrelenir.

### 2.4. Tarayıcı Otomatik Tamamlama ve Şifre Saklama Standartları
- Modern tarayıcıların (Chrome, Edge vb.) şifre yöneticileri `fetch` veya `axios` çağrısı yapan butonları çoğu zaman algılayamaz.
- Tarayıcı güvenliği için giriş alanları standart `<form onSubmit={handleLogin}>` içine alındı:
  - E-posta inputu: `name="username"`, `id="login-username"`, `autoComplete="username"`
  - Şifre inputu: `name="password"`, `id="login-password"`, `autoComplete="current-password"`
  - Form submit edildiğinde tarayıcı native olarak "Şifre Kaydedilsin mi?" diyaloğunu tetikler.

---

## 3. VERİTABANI MODEL VE DDL DEĞİŞİKLİKLERİ

### 3.1. Tablo Oluşturma DDL'leri (PostgreSQL)

```sql
-- 1. Sektörler Tablosu
CREATE TABLE IF NOT EXISTS sectors (
    code VARCHAR(32) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    icon VARCHAR(64),
    image_url VARCHAR(512),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2. Meslek Grupları Tablosu
CREATE TABLE IF NOT EXISTS professions (
    code VARCHAR(32) PRIMARY KEY,
    sector_code VARCHAR(32) NOT NULL REFERENCES sectors(code) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_professions_sector_code ON professions(sector_code);

-- 3. Tenants ve Tenant Leads Tablolarına professions Kolonu Eklenmesi
ALTER TABLE tenants ADD COLUMN IF NOT EXISTS professions JSONB DEFAULT '[]'::jsonb;
ALTER TABLE tenant_leads ADD COLUMN IF NOT EXISTS professions JSONB DEFAULT '[]'::jsonb;
```

### 3.2. SQLAlchemy Modelleri (`backend/app/db/models.py`)

```python
class Sector(Base):
    __tablename__ = "sectors"

    code = Column(String(32), primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    icon = Column(String(64), nullable=True)
    image_url = Column(String(512), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    professions = relationship("Profession", back_populates="sector", cascade="all, delete-orphan")


class Profession(Base):
    __tablename__ = "professions"

    code = Column(String(32), primary_key=True, index=True)
    sector_code = Column(String(32), ForeignKey("sectors.code", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    sector = relationship("Sector", back_populates="professions")
```

---

## 4. BACKEND API GELİŞTİRMELERİ

### 4.1. Sektörler API (`backend/app/api/v1/sectors.py`)
- `GET /api/v1/sectors/`: Tüm sektörleri, bağlı meslek sayısını (`prof_count`) hesaplayan `outerjoin` ile listeler. Arama (`q`) ve aktiflik (`is_active`) filtresi destekler.
- `GET /api/v1/sectors/{code}`: Tekil sektör detayını ve bağlı meslek listesini getirir.
- `POST /api/v1/sectors/`: Yeni sektör tanımı ekler.
- `PUT /api/v1/sectors/{code}`: Sektör bilgilerini günceller.
- `DELETE /api/v1/sectors/{code}`: Sektörü ve cascade olarak bağlı mesleklerini siler.

### 4.2. Meslek Grupları API (`backend/app/api/v1/professions.py`)
- `GET /api/v1/professions/`:
  - `sector_code` filtresi (Örn: `?sector_code=K`)
  - Arama filtresi `q` (Kod veya isimde büyük/küçük harf duyarsız arama)
  - `is_active` filtresi
  - `limit` (varsayılan: 500) ve `offset` sayfalaması
- `GET /api/v1/professions/{code}`: Tekil meslek detayını getirir.
- `POST /api/v1/professions/`: Yeni meslek tanımı ekler (Bağlı sektörün varlığını kontrol eder).
- `PUT /api/v1/professions/{code}`: Meslek tanımını günceller.
- `DELETE /api/v1/professions/{code}`: Meslek tanımını siler.

### 4.3. Router Entegrasyonu (`backend/app/api/router.py`)
```python
from app.api.v1.sectors import router as sectors_router
from app.api.v1.professions import router as professions_router

api_router.include_router(sectors_router, tags=["Sektör Tanımları (Ticaret Bakanlığı)"])
api_router.include_router(professions_router, tags=["Meslek Tanımı Modülü"])
```

### 4.4. Müşteri Oluşturma ve Satın Alma Endpoint Güncellemeleri (`tenants.py`)
- `admin_create_tenant`: `payload.nace_codes` yerine `payload.sectors` ve `payload.professions` kaydedilir.
- `generate_company_manifesto_endpoint`: NACE yerine seçilen sektör ve meslek gruplarını kullanarak LLM manifestosu üretir.
- `PurchaseRequest` ve `submit_purchase_request`: Web sitesi üzerinden gelen satın alma taleplerinde sektör ve meslek gruplarını JSONB olarak saklar.

---

## 5. VERİ ENTEGRASYONU VE EXCEL AKTARIM SÜRECİ

### 5.1. Excel Dosyası Analizi
- **Dosya Yolu:** `documents/Sektör Meslek Nace Kodları_2026.03.xlsx`
- **Sayfa:** `Sheet0` (2.141 satır, 8 sütun)
- **Sütun Yapısı:**
  - Sütun 1: `SEKTOR KODU` (A, B, C, D, E, F, G, H, I, J, K -> 11 benzersiz kod)
  - Sütun 2: `SEKTOR TANIM` (Örn: "YAPI SANATLARI", "ELEKTRİK, ELEKTRONİK, BİLGİSAYAR")
  - Sütun 3: `MESLEK KODU` (A.01'den K.15'e kadar 184 benzersiz kod)
  - Sütun 4: `MESLEK TANIM` (Örn: "Boya, kimyasal ürünlerin imalatı", "Bilgisayar kurulumu...")
  - Sütun 5-8: Eski NACE Rev. 2.1 kodları ve güncel metinler (Bu alanlar atlandı).

### 5.2. Yeniden Yükleme Scripti (`backend/reseed_trade_data.py`)
Veritabanı sıfırlanıp iki aşamalı olarak veriler aktarılmıştır:

```python
# ADIM 1: Tabloları Boşalt
await conn.execute("DELETE FROM professions;")
await conn.execute("DELETE FROM sectors;")

# ADIM 2: Sektörleri Ekle (11 Adet)
for s in sectors:
    await conn.execute("""
        INSERT INTO sectors (code, name, icon, is_active, created_at, updated_at)
        VALUES ($1, $2, $3, TRUE, NOW(), NOW())
    """, s["code"], s["name"], s.get("icon", "📁"))

# ADIM 3: Meslek Gruplarını Ekle (184 Adet)
for p in professions:
    await conn.execute("""
        INSERT INTO professions (code, sector_code, name, is_active, created_at, updated_at)
        VALUES ($1, $2, $3, TRUE, NOW(), NOW())
    """, p["code"], p["sector_code"], p["name"])
```

### 5.3. Yüklenen Sektör ve Meslek Dağılım Tablosu

| Sektör Kodu | Sektör Adı | İkon | Meslek Grubu Sayısı | Örnek Meslekler |
| :---: | :--- | :---: | :---: | :--- |
| **A** | AĞAÇ İŞLERİ | 🌲 | **8** | Kerestecilik, Marangozluk, Mobilya imalatı |
| **B** | EĞLENCE, DİNLENME, ORGANİZASYON | 🎭 | **10** | Düğün salonu, Ajans & organizasyon, Kahvehanecilik |
| **C** | ELEKTRİK, ELEKTRONİK, BİLGİSAYAR | 💻 | **17** | Bilgisayar & Yazılım, E-ticaret, Güvenlik sistemleri |
| **D** | GIDA, TARIM | 🌾 | **25** | Fırıncılık, Kasaplık, Lokantacılık, Arıcılık |
| **E** | GİYİM, DERİ ÜRÜN, EV TEKSTİLİ, DOKUMA | 👗 | **16** | Ayakkabıcılık, Konfeksiyonculuk, Terzilik |
| **F** | HEDİYELİK EŞYA, EĞİTİM, BASIM, ÇEŞİTLİ | 🎁 | **22** | Matbaacılık, Reklamcılık, Danışmanlık, Kırtasiye |
| **G** | KUAFÖR, BERBER, TEMİZLİK, KOZMETİK | ✂️ | **17** | Erkek berberliği, Kadın kuaförlüğü, Genel temizlik |
| **H** | METAL, OTOMOTİV, MAKİNE | 🚗 | **32** | Oto servis, Torna, Kaynak, Makine imalatı, Kuyumculuk |
| **I** | PAZAR, SEYYAR | 🛒 | **6** | Pazarda tekstil, Sebze-meyve, Seyyar satıcılık |
| **J** | ULAŞTIRMA HİZMETLERİ | 🚚 | **16** | Yük taşımacılığı, Taksicilik, Minibüsçülük, Akaryakıt |
| **K** | **YAPI SANATLARI** | 🏗️ | **15** | İnşaatçılık, Sıhhi tesisat, Emlakçılık, Boya imalatı |
| **TOPLAM** | **11 Resmi Sektör** | - | **184** | **184 Resmi Meslek Grubu** |

---

## 6. [K] YAPI SANATLARI SEKTÖRÜ DETAYI

Özel olarak incelenen ve doğrulanan **YAPI SANATLARI** meslek grubu listesi:

1. `K.01` - Boya, kimyasal ürünlerin imalatı
2. `K.02` - Boya, kimyasal ürünlerin ticareti
3. `K.03` - Camcılık
4. `K.04` - Çevre düzenleme, peyzaj faaliyetleri
5. `K.05` - Emlakçılık
6. `K.06` - Hırdavatçılık
7. `K.07` - İnşaat malzemeleri imalatı
8. `K.08` - İnşaat malzemeleri ticareti
9. `K.09` - İnşaatçılık
10. `K.10` - Mermer, taş, kum ocakçılığı
11. `K.11` - Prefabrik yapıların imalatı, kurulumu, ticareti
12. `K.12` - PVC ürün imalatı
13. `K.13` - PVC ürün ticareti
14. `K.14` - Sıhhi tesisatçılık
15. `K.15` - Sondajcılık

---

## 7. FRONTEND GELİŞTİRMELERİ VE HATA ÇÖZÜMLERİ

### 7.1. API İstemcisi (`frontend/src/api.js`) Düzeltmesi
- **Tespit Edilen Kritik Hata:** `OfficialLanding.jsx` içinde `api.getProfessions(null, true)` çağrısı yapılıyordu. JavaScript'te `params = {}` varsayılan değeri yalnızca `undefined` için çalışır; `null` geçtiğinde `params.sector_code` okunurken `TypeError` fırlatılıyor ve `catch(() => [])` nedeniyle meslek listesi sessizce boş diziye düşüyordu.
- **Çözüm:** `getProfessions` fonksiyonu her türlü girdiye karşı dayanıklı hale getirildi, `limit` varsayılan 500 olarak ayarlandı:

```javascript
// Türkiye Ticaret Bakanlığı Meslek Tanımları (Madde 1)
getProfessions: (params = {}) => {
  const p = (params && typeof params === 'object') ? params : {};
  const qs = new URLSearchParams();
  if (p.sector_code) qs.append('sector_code', p.sector_code);
  if (p.search) qs.append('q', p.search);
  if (p.q) qs.append('q', p.q);
  if (p.is_active !== undefined) qs.append('is_active', p.is_active);
  if (p.active_only !== undefined) qs.append('is_active', p.active_only);
  qs.append('limit', p.limit || 500);
  if (p.offset) qs.append('offset', p.offset);
  const query = qs.toString();
  return request(`/professions/${query ? `?${query}` : ''}`);
},
```

### 7.2. Landing Page (`frontend/src/components/OfficialLanding.jsx`)
1. **Adım 2 Revizyonu:**
   - Eski NACE arama kutusu ve etiketleri kaldırıldı.
   - Ticaret Bakanlığı 11 sektör seçici gridi eklendi (İkonlar ve aktif seçim göstergeleri ile).
   - Sektör seçildiğinde yalnızca o sektöre ait meslek gruplarının dinamik olarak listelendiği açılır alan kuruldu.
2. **Giriş Modalı ve Beni Hatırla:**
   - Hızlı Giriş butonları (`cuneyterdil@recdx.com` ve `info@recdx.com`) kaldırıldı.
   - "Beni Hatırla" (Remember Me) checkbox'ı eklendi (`localStorage.setItem('recorion_remember_login', ...)`).
   - Form `<form onSubmit={handleRealLogin}>`, `<input name="username" type="email" autoComplete="username" />` ve `<input name="password" type="password" autoComplete="current-password" />` standartlarına kavuşturuldu.

### 7.3. Süper Admin Konsolu (`frontend/src/components/SuperAdminConsole.jsx`)
1. **Navigasyon:**
   - Eski `NACE` ve `TITLES` sekmeleri kaldırıldı.
   - Yerine `SECTORS` ("Sektör Tanımları") ve `PROFESSIONS` ("Meslek Grubu Tanımları") sekmeleri eklendi.
2. **Sektörler Sekmesi:**
   - Kanban ve Tablo görünüm modları.
   - Her sektör kartında bağlı meslek sayısı göstergesi (`{profCount} Meslek Tanımı →`).
   - Butona tıklandığında meslekler sekmesine geçip ilgili sektörü otomatik filtreleyen ve aramaları sıfırlayan akış.
3. **Meslekler Sekmesi:**
   - Sektör filtreleme barı (`TÜM SEKTÖRLER (184)`, `A - AĞAÇ İŞLERİ (8)`, `K - YAPI SANATLARI (15)` vb.).
   - Arama kutusu (Meslek adı veya kodunda anlık filtreleme).
   - Yeni meslek ekleme, düzenleme ve silme modalleri.
4. **Yeni Müşteri & Şirket Düzenleme Modalleri:**
   - Sektör açılır listesi ve hızlı sektör butonları.
   - Sektöre bağlı meslek gruplarının dinamik dropdown seçimi ve chip etiketleri.

---

## 8. SİSTEM DOĞRULAMA VE TEST ÇIKTILARI

1. **Frontend Derleme Testi:**
   - `npm run build` komutu çalıştırıldı.
   - 1.906 modül başarıyla dönüştürüldü, `dist/` çıktıları 0 hata ile üretildi.
2. **Backend API Testi:**
   - `/api/v1/sectors/` -> 11 sektörün tamamı ve meslek sayıları doğrulandı.
   - `/api/v1/professions/?sector_code=K` -> YAPI SANATLARI'na ait 15 mesleğin tamamı doğrulandı.
   - `/api/v1/professions/?limit=500` -> 184 mesleğin tamamı doğrulandı.
3. **Veritabanı Kayıt Sayıları:**
   - `SELECT count(*) FROM sectors;` -> **11**
   - `SELECT count(*) FROM professions;` -> **184**
   - `SELECT count(*) FROM professions WHERE sector_code = 'K';` -> **15**

---

*Bu belge, RECOrion projesinin mimari bütünlüğünü ve yapılan tüm teknik adımları kayıt altına almak amacıyla hazırlanmıştır.*
