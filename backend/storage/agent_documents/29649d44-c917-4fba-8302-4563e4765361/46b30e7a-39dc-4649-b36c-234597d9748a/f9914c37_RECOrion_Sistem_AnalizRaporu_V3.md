# RECOrion (Operational Reasoning & Intelligence Orchestration Network)
## Sistem Analiz Raporu (Sürüm 3.0 – Nihai Konsolide Mimari)

**Tarih:** 06 Ekim 2026  
**Doküman Kodu:** REC-SYS-ANA-V3  
**Kapsam:** Genel Pazar, Çok Kiracılı (Multi-Tenant), NACE Uyumlu Hibrit Otonom İş ve Yazılım Fabrikası  

---

## 1. Sistemin Genel Yapısı ve Vizyonu

RECOrion; kurumsal şirketlerin iş süreçlerini, yazılım geliştirmelerini, analizlerini ve operasyonel iş akışlarını otonom yapay zeka ajanları ile insan personellerin hibrit uyumuyla yürüten devrimsel bir **Yapay Zeka Orkestrasyon ve İş Geliştirme Fabrikasıdır**.

### 1.1 Sektör Agnostik ve Genel Pazar Odaklı Vizyon
Sistem yalnızca yazılım firmalarına değil, sanayiden lojistiğe, hukuk bürolarından e-ticaret işletmelerine kadar her sektöre hizmet verebilecek genel pazar (B2B SaaS / PaaS) mimarisine sahiptir. Şirket sisteme tanımlanırken uluslararası **NACE faaliyet kodları** girilir. Sistem, işletmenin faaliyet alanını NACE kodlarından otomatik analiz ederek şirketin vizyonunu tanımlayan **Kurumsal Manifestoyu** ve sektörel iş tanımlarını otomatik üretir.

### 1.2 Rol Eşitliği Prensibi (Human-AI Parity)
Sistemde insanlar ve yapay zeka ajanları eşit aktör (`ActorType = {HUMAN, AI_AGENT}`) olarak konumlandırılmıştır. Bir insan yönetici bir AI ajanına görev atayabileceği gibi; bir "Proje Yöneticisi AI", iş akışı gereği bir "Yazılım Mimarı İnsana" onay görevi atayabilir. Hem insan hem de AI aktörler görev icra edebilir, onay makamı olabilir veya hakemlik yapabilir.

### 1.3 Sürekli Öğrenen İki Kademeli Kolektif Hafıza (Two-Tier Collective Memory)
RECOrion mimarisinde hafıza yapısı kesin olarak **2 seviyeli kolektif zekâ modeli** üzerine kuruludur:
1. **AI Personellerinin (Ajanlarının) Hafızası (`NS_AGENT`):** Şirket bünyesindeki her bir AI çalışanının kendi uzmanlık dokümanları, rol tecrübesi, tamamladığı görevlerin hafızası ve bireysel yetenek birikimidir.
2. **Şirket Kurum Hafızası (`NS_GLOBAL`):** Şirketteki tüm AI ajanlarının hafızalarının ve deneyimlerinin toplamı/sentezi olan merkezi kurumsal hafızadır. Bir ajanın projelerde kazandığı, doğrulanan ve insan onayından geçen tecrübeler doğrudan Kurum Hafızasına terfi ettirilir. Böylece tek bir ajanın öğrendiği know-how, şirketin tüm AI personellerinin ortak kolektif aklına dönüşür.
*(Sistemde bağımsız bir 3. katman olarak izole "Proje Hafızası" tutulmaz; projeler ilişkisel verilerle yönetilir ve bu iki hafıza havuzundan beslenir.)*

---

## 2. Sistemin Çalışma Düzlemleri ve Dağıtım Katmanları

Sistem, "Merkezi Yönetim, İzole Veri Katmanı ve Otonom Yürütme" disipliniyle üç ana düzlem üzerinde kurgulanmıştır. Başlangıçta tüm bileşenler yerel bilgisayarda izole Docker konteynerleri üzerinde çalışacak (Geliştirme/MVP Aşaması), ardından aynı altyapı Türkiye'deki güvenli sunucu altyapısına taşınacaktır.

```
┌────────────────────────────────────────────────────────────────────────┐
│                        KONTROL DÜZLEMİ (WEB UI)                        │
│   [Platform Admin Paneli] ── [Şirket Yönetimi] ── [WORK AREA UX]       │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
┌───────────────────────────────────┴────────────────────────────────────┐
│                    YÜRÜTME DÜZLEMİ (EXECUTION PLANE)                   │
│   [FastAPI Backend] ── [Temporal Engine] ── [Worker Daemons]           │
│   [LLM Gateway (13 Model)] ── [Sandbox Runner] ── [Artifact Store]     │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
┌───────────────────────────────────┴────────────────────────────────────┐
│                  HAFIZA VE VERİTABANI DÜZLEMİ (DARK DB)                │
│   [PostgreSQL 16 + pgvector] ── [Qdrant Vektör DB] ── [MinIO] ── [Gitea]│
└────────────────────────────────────────────────────────────────────────┘
```

### 2.1 Kontrol Düzlemi (Web UI & Work Area)
Yönetim merkezi, React + Vite + TypeScript ile geliştirilen modern Web arayüzüdür:
1. **Platform Ana Admini:** Sisteme NACE kataloğunu tanımlar, LLM sağlayıcılarını (`llm_providers`) ve modellerini (`llm_models`) yönetir, abonelik paketlerini ve sektörel standart unvanları belirler. Müşteri firmalar için **Tenant (Ana Şirket)** açar ve o şirkete bir **Süper Admin** atar.
2. **Şirket Süper Admini:** Kendi şirketinin NACE kodlarını seçer. Sistemin ürettiği Kurumsal Manifestoyu inceler, gerekirse düzenleyip onaylar. Şirket içi kullanıcıları (insan personelleri), AI personellerini ve yetki onay gruplarını (Örn: "Yazılım Mimarları Onay Kurulu", "Finans Kontrol Grubu") tanımlar.
3. **Merkezi Çalışma Alanı (Work Area):** Antigravity tamamen kaldırılarak yerine tüm işin, sohbetlerin, çıktının ve onayın tek ekrandan yönetildiği 3 bölmeli modern bir operasyon merkezi getirilmiştir (§3 detay).

### 2.2 Hafıza ve Veritabanı Düzlemi (İki Seviyeli Hafıza & Dark DB)
- **İlişkisel Katman (PostgreSQL 16 + pgvector):** Şirketler, kullanıcılar, roller, projeler, backlog/görevler, iş akışları (DAG), olaylar ve denetim logları tutulur. Çok kiracılı izolasyon PostgreSQL Row-Level Security (RLS) ile veritabanı çekirdeğinde kilitlenir.
- **Vektörel Zihin (Qdrant):** Yapay zekanın arama ve anlamsal hafızasıdır. Tek bir koleksiyon üzerinde zorunlu payload filtreleme (`tenant_id`, `scope`) ile iki seviyeli kolektif model olarak yönetilir:
  - `NS_GLOBAL` (Şirket Kurum Hafızası): Şirketteki tüm AI ajanlarının tecrübe ve birikimlerinin toplamı; kurumsal standartlar, NACE manifestosu, şirket politikaları ve ortak kolektif know-how.
  - `NS_AGENT` (AI Personelleri Hafızası): Her bir ajanın kendi uzmanlık dokümanları (PDF, Word, Excel), rol tecrübeleri ve geçmiş görev hafızası.
  *(Ayrı bir proje vektör katmanı tutulmaz; proje görevleri kurumun kolektif aklı ve görevli personelin uzmanlık hafızası taranarak yürütülür.)*
- **Çıktı Nesne Deposu (MinIO):** Dokümanlar, Excel tabloları, analiz raporları ve ikili dosyalar sürümlü nesne deposunda saklanır.
- **Dahili Git Deposu (Gitea):** Yazılım geliştiren projeler için yerel, hafif, kapalı devre Git sunucusu.

### 2.3 Yürütme Düzlemi (Temporal, Worker & LLM Gateway)
- **İş Akışı Motoru (Temporal):** Dağıtık ve dayanıklı iş akışı yönetimi sağlar. Ajan adımları çökmelere karşı dayanıklıdır (durable execution); onay bekleme (Human-in-the-Loop) sinyallerle yönetilir.
- **Worker Daemon & Sandbox:** Görevleri icra eden arka plan işçileridir. Kod çalıştırma gerektiren yazılım görevlerinde efemeral, rootless ve ağ bağlantısı kapalı konteynerler (sandbox) ayağa kaldırılarak güvenli çalıştırma sağlanır.
- **LLM Gateway:** Tüm model trafiğini tek çatı altında toplayan merkezi kurumsal geçittir.

---

## 3. Çalışma Alanı (Work Area) Mimarisi ve Kullanıcı Deneyimi (UX)

Work Area, sistemin kalbidir. Kullanıcının farklı pencereler arasında dağılmadan tüm proje operasyonunu tek ekrandan yürüttüğü **3 Bölmeli Ergonomik Yerleşim (Tri-Pane Layout)** mantığıyla tasarlanmıştır:

```
┌────────────────────┬───────────────────────────────────────┬────────────────────────┐
│ SOL: GEZİNTİ & INBOX│ ORTA: CANLI İŞ AKIŞI & DİYALOG        │ SAĞ: ÇIKTI & KALİTE    │
│                    │                                       │                        │
│ 🔴 Onayımı         │ 🤖 Ajan: "Gereksinim analizini        │ 📄 ÇIKTI ÖNİZLEME      │
│    Bekleyenler (3) │          tamamladım. AST kuralları    │ [v1.2] Diff Görünümü   │
│                    │          ve şema hazır."              │                        │
│ 📁 Projelerim      │                                       │ 🛡️ KALİTE KAPISI      │
│   ├── E-Fatura Ent.│ ⚙️ CANLI YÜRÜTME AKIŞI:                │ - Test: 24/24 Başarılı │
│   └── Mobil API    │ [Düşünüyor] ➔ [Kod Derliyor] ➔ [Test] │ - SAST: 0 Açık         │
│                    │                                       │ - Kapsam: %86          │
│ 📋 Backlog / Kanban│ 💬 Multi-Modal Sürükle-Bırak          │                        │
│ ⏳ Deadline Sayacı │   (Figma, Şema Görseli, PDF Ekranı)   │ 🔘 [ONAYLA]            │
│ 👥 Ajan Havuzu     │ ⚔️ DEBATE ARENA (İstişare Thread'i)   │ 🔘 [REVİZYON İSTE]     │
│                    │   Coder vs QA Tartışma Paneli         │ 🔘 [REDDET]            │
└────────────────────┴───────────────────────────────────────┴────────────────────────┘
```

1. **Sol Bölme (Gezinti & Inbox):**
   - **"Onayımı Bekleyenler" Kutusu:** Kullanıcının onay vermesi gereken görevler kırmızı/turuncu aciliyet sayaçlarıyla en tepede karşılar.
   - **Backlog & Proje Gezgini:** Görevlerin durumunu, deadline geri sayımını ve projeye atanmış personellerin durumunu (`IDLE`, `WORKING`, `WAITING_APPROVAL`) gösterir.
2. **Orta Bölme (Canlı Etkileşim & İş Akışı Akışı):**
   - **Canlı Yürütme Akışı (Live Stream):** Ajanın arka plandaki düşünce zinciri ve eylemleri anlık akar. Kullanıcı ajan çalışırken süreci canlı izleyebilir, istediği an "Duraklat" veya "Müdahale Et" diyebilir.
   - **Multi-Modal Girdi:** Figma tasarım linkleri, veritabanı şema çizimleri, arayüz ekran görüntüleri veya şartname dokümanları doğrudan alana sürüklenir; vision ve OCR modelleri görseli anında teknik isterlere dönüştürür.
   - **Debate Arena (İstişare Thread'i):** İki ajan (örneğin Coder ve QA) mimari bir konuda uyuşmazlığa düştüğünde, sohbet içinde katlanabilir bir alt başlık açılır. İki yapay zeka teknik argümanlarıyla tartışırken insan yönetici tartışmayı izleyip hakem kararı verir.
3. **Sağ Bölme (Bağlam, Çıktı & Kalite Kapısı):**
   - **Çıktı Önizleyici (Artifact Viewer):** Üretilen kodun, sözleşme taslağının veya analiz raporunun önceki sürümlerle olan fark (diff) görünümü canlı sunulur.
   - **Kalite Kapısı ve Onay Paketi (Evidence-Based Card):** Karar vericiye "Bu çıktının 28 testi geçtiği, güvenlik taramasından temiz çıktığı ve kurumsal şablona %100 uyduğu" kanıtlarla özetlenir.
   - **Hızlı Karar:** Tek tıkla [Onayla], [Düzeltme İste] veya [Reddet] butonları işletilir.
   - **Efor & Kredi Göstergesi:** O görevin tükettiği model bazlı kredi ve harcanan süre anlık gösterilir.

---

## 4. LLM ve Model Altyapısı (EVREN Ekosistemi & Dinamik Katalog)

Sistem modelleri koda gömülü değildir; veritabanında `llm_providers` ve `llm_models` tablolarından yönetilir.

### 4.1 Tek Kurumsal Hesap & LLM Gateway
Müşteriler dış LLM platformlarına veya e-Devlet'e doğrudan giriş yapmaz. RECOrion kurucusunun kurumsal hesabı üzerinden alınan API bağlantısı, arka plandaki **LLM Gateway** tarafından yönetilir. Gateway; kiracı bazlı kota takibi, hız sınırlaması (rate limit), devre kesici (circuit breaker), token ölçümü ve PII maskeleme işlemlerini icra eder.

### 4.2 Seed Olarak Tanımlanan 13 Model Kataloğu
Sistem kurulumunda kullanıma hazır 13 model dinamik kataloğa yüklenir:

| # | Model Kodu | Model Türü | Platformdaki Görev ve Sorumluluğu |
|---|---|---|---|
| 1 | `qwen3-asr-1.7b` | AUDIO | Sesli komutlar, mülakat, toplantı ve ses dökümleri (Speech-to-Text) |
| 2 | `deepseek-ocr-2` | OCR | Doküman, fatura, şartname ve taranmış PDF metin çıkarımı |
| 3 | `dots-ocr` | OCR | Karmaşık mali tablolar, matbu evraklar ve form ayrıştırma |
| 4 | `qwen3-guard-4b` | GUARD | İçerik güvenliği, prompt injection ve jailbreak savunma kalkanı |
| 5 | `qwen3-reranker-8b` | RERANKER | Vektör arama ve RAG bağlam yeniden sıralama |
| 6 | `qwen3-embedding-8b` | EMBEDDING | Şirket Kurum Hafızası (Kolektif) ve AI Personel Hafızası vektörizasyonu |
| 7 | `qwen3-vl-30b` | VISION | Figma tasarımları, UI ekranları, mimari şemaların görsel analizi |
| 8 | `glm-5.3` | CHAT | İleri düzey akıl yürütme, sistem mimarı ve ajan orkestrasyonu |
| 9 | `qwen3.8-flash-next` | CHAT | Düşük gecikmeli hızlı çıkarım, genel asistanlık ve operasyonel işler |
| 10 | `deepseek-v4.1-flash` | CHAT | Gelişmiş kodlama, hata ayıklama, refactoring ve birim testler |
| 11 | `mimo-v2.6-pro` | CHAT | Karmaşık muhakeme, stratejik planlama ve çok adımlı problem çözme |
| 12 | `gemma-4-31b` | CHAT | Hafif görevler, PR, pazarlama metinleri, duyuru ve dokümantasyon |
| 13 | `deepseek-v4-flash` | CHAT | Hızlı kod üretimi, QA kontrolü ve statik kod gözden geçirme |

---

## 5. Çıktı Deposu (Artifact Store) ve Git Mimarisi

RECOrion yalnızca yazılım geliştiren bir sistem değildir. Bu nedenle mimarinin merkezinde salt bir "Git Deposu" değil, **Çıktı Deposu (Artifact Store)** yer alır.

```
┌────────────────────────────────────────────────────────────────────────┐
│                        ÇIKTI DEPOSU (ARTIFACT STORE)                    │
│  - Tipler: KOD_REPO, DOKÜMAN, TABLO/EXCEL, ANALİZ_RAPORU, ŞEMA, GÖRSEL │
│  - Ortak Özellikler: Değişmez Sürümleme (v1..vn), Hash, Diff, Onay    │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
           ┌────────────────────────┴────────────────────────┐
           ▼                                                 ▼
┌────────────────────────┐                        ┌──────────────────────┐
│  YAZILIM PROJELERİ     │                        │  GENEL SEKTÖR/OFİS   │
│  Bağlayıcı: Gitea/Git  │                        │  Bağlayıcı: MinIO/DB │
│  - Kod Branch/Commit   │                        │  - Sözleşme Taslağı  │
│  - CI Test Koşumu      │                        │  - Mali Mizan Tablosu│
│  - Sandbox Çalıştırma  │                        │  - İK Teklif Mektubu │
└────────────────────────┘                        └──────────────────────┘
```

1. **Çekirdek Çıktı Mantığı:** Her görev tamamlandığında bir "Artifact" üretir. Bu çıktı yazılım projesinde bir git commit'i iken; hukuk projesinde sürümlenmiş bir Word sözleşmesi, finans projesinde formülleri doğrulanmış bir Excel tablosudur.
2. **Dahili Git (Gitea):** Yazılım geliştiren projelerde kapalı devre, yerel Gitea sunucusu devreye girer. GitHub/GitLab bağlantıları opsiyonel birer dış bağlayıcıdır.
3. **Alan Paketleri (Domain Packs):** Her sektörün araçları ve kalite kapıları ayrıştırılmıştır:
   - **Yazılım Paketi:** Git, Sandbox, Birim Test, SAST taraması.
   - **Hukuk Paketi:** Doküman motoru, OCR, Kanun/Mevzuat şablon kontrolü, Riskli ifade filtresi.
   - **Mali İşler Paketi:** Excel motoru, Çapraz toplam doğrulama, ERP bağlayıcısı.

---

## 6. Uçtan Uca Detaylı İş Akışı ve Operasyon

Sistemin uçtan uca çalışması deterministik 7 aşamada gerçekleşir:

```
[1. Şirket & NACE Tanımı] ➔ [2. Auto-HR & Personel Havuzu] ➔ [3. Proje & İş Analisti Backlog]
                                                                        │
┌───────────────────────────────────────────────────────────────────────┘
▼
[4. Atomik DAG Provisioning] ➔ [5. Work Area Görev Çevrimi] ➔ [6. Maker-Checker Onay]
                                                                        │
┌───────────────────────────────────────────────────────────────────────┘
▼
[7. Bilgi Terfisi & L1-L3 Ajan Kademesi]
```

### Aşama 1: Şirket Kurulumu ve NACE Manifestosu (Web UI)
Admin şirketi kurar ve NACE kodunu/kodlarını seçer. Sistem `glm-5.3` modelini tetikleyerek şirkete özel **Kurumsal Manifestoyu** ve departman unvanlarını yazar. Şirket Süper Admini manifestoyu onayladığında metin, Qdrant'ta o şirketin `NS_GLOBAL` kök hafızasına indekslenir.

### Aşama 2: Dijital İK & Auto-HR (Personel Havuzu Kurulumu)
Sistem seçilen sektöre göre tek tıkla **İdeal AI Personel Kadrosunu** önerir (Örn: 1 Analist, 2 Coder, 1 QA, 1 PR). İstenirse manuel ajanlar eklenir. Ajanlara uzmanlık dokümanları yüklenir; dokümanlar `dots-ocr` ve `qwen3-embedding-8b` ile vektörize edilerek ajanın `NS_AGENT` hafızasına yazılır. İnsan kullanıcılar ve AI ajanlar yetki gruplarına (onay kurullarına) atanır.

### Aşama 3: Projelendirme & İş Analisti Backlog Üretimi
Proje Yöneticisi yeni bir proje açar, isterleri ve deadline tarihini girer. **İş Analisti Ajanı**, isterleri tarayarak otomatik olarak bir Backlog (Epic'ler, Kabul Kriterli Görevler, Tahmini Efor) önerir. İnsan yönetici backlog'u onaylar. Ajanlar arası iş akış sırası (DAG) görsel editör üzerinden bağlanır.

### Aşama 4: Otonom Provisioning (Atomik Kurulum)
"Projeyi Başlat" dendiğinde sistem paralel olarak:
- PostgreSQL'de proje ve görev kayıtlarını açar.
- Projede görev alacak AI personellerinin hafızalarını (`NS_AGENT`) ve Şirket Kurum Hafızasını (`NS_GLOBAL`) proje görev bağlamına bağlar (Ayrı bir proje vektör koleksiyonu açılmaz; 2 seviyeli kolektif hafıza kullanılır).
- Eğer proje bir yazılım projesi ise Gitea üzerinde izole bir repo açar.
Tüm adımlar bir Saga modeliyle yönetilir; bir adım başarısız olursa sistem kendini güvenli duruma geri alır.

### Aşama 5: Work Area Üzerinde Görev Yürütme
Kullanıcı veya AI aktör Work Area'ya girer. Görev tetiklendiğinde:
- Görevli ajan Şirket Kurum Hafızası (`NS_GLOBAL` - tüm personelin ortak aklı) ve AI Personel Hafızası (`NS_AGENT` - ajanın kendi uzmanlığı) katmanlarından RAG ile bağlamı çeker (`qwen3-reranker-8b` ile en doğru parçaları sıralar).
- Ajan kod yazacaksa izole Sandbox konteynerinde kodunu derler ve testlerini koşar.
- Eğer QA ile Coder arasında mimari uyuşmazlık çıkarsa **Debate Arena** alt paneli devreye girer; ajanlar tartışır ve hakem kararıyla uzlaşırlar.

### Aşama 6: Kanıta Dayalı Hibrit Onay (Maker-Checker & SLA)
Görev bittiğinde sistem duraklar (`WAITING_APPROVAL`). Sağ bölmede karar vericiye Onay Paketi (test sonuçları, diff, kontrol listesi) sunulur.
- **Maker-Checker Kuralı:** Görevi üreten ajan veya aynı model ailesi onay mercii olamaz. Kritik yayınlama düğümlerinde en az bir **İnsan Onayı** zorunludur.
- **Yarış Durumu Koruması:** Onay grubundaki ilk geçerli karar veritabanı kilidiyle işlenir.
- **Karantina:** Bir ajan üst üste 3 kez ret alırsa (`RetryCount >= 3`), sistem ajanı `QUARANTINED` durumuna alır ve Süper Admin'e eskalasyon fırlatır.

### Aşama 7: Bilgi Terfisi ve Güven Tabanlı Ajan Kademesi
Proje başarıyla tamamlandığında:
- Projedeki teknik kazanımlar taranır, müşteri sırları ve kişisel veriler ayıklanır.
- İnsan denetim kuyruğundan onay alan soyut know-how, şirketin Kurum Hafızasına (`NS_GLOBAL`) yazılır; böylece bir ajanın başarısı tüm şirketin AI personellerinin ortak aklına (kolektif hafızaya) dahil edilir.
- **Özerklik Seviyesi Terfisi (L1 → L2 → L3):** 10 projeyi başarıyla bitiren ve ret oranı <%5 olan ajanların yetki seviyesi yükseltilir; L2/L3 seviyesindeki kıdemli ajanların rutin görevleri için insan onay yükü otomatik azaltılır.

---

## 7. Güvenlik, Savunma ve İzolasyon Yapısı (Zero Trust)

RECOrion, kurumsal verilerin sızmasını ve kötüye kullanımını engellemek için çok katmanlı savunma mimarisine sahiptir:

1. **Ağ ve Konteyner İzolasyonu:** Docker servisleri rootless modda çalışır. Veritabanları dış ağa kapalı "Dark DB" olarak izole Docker bridge ağında tutulur.
2. **Prompt Injection & İçerik Kalkanı:** Sisteme dışarıdan giren tüm veriler (yüklenen dosyalar, görsel içerikler, kullanıcı girdileri) doğrudan "veri" olarak etiketlenir, talimat olarak algılanması engellenir. Tüm girdi ve çıktılar `qwen3-guard-4b` güvenlik kalkanı üzerinden filtrelenir.
3. **İzole Kod Çalıştırma (Sandbox):** Yazılım görevlerinde ajanların ürettiği kodlar, ana sistemden ve dış internetten tamamen yalıtılmış, CPU/RAM/zaman limitli efemeral sandbox konteynerlerinde çalıştırılır.
4. **Değiştirilemez Denetim İzi (Append-Only Audit Log):** Sistemde kimin hangi kararı verdiği, hangi ajanın hangi modeli kullandığı ve onay süreçleri silinemez log tablolarına anlık yazılır.
5. **Veri Emniyeti:** Çok kiracılı izolasyon PostgreSQL Row-Level Security (RLS) ile sağlanır; bir şirketin ajanı asla başka bir şirketin veritabanına veya vektör uzayına erişemez.

---

## 8. Kiralama ve Paketleme Stratejisi (Abonelik Modeli)

Platform, kurumsal şirketlere kiralama modeliyle sunulur. Fiyatlandırma "Sabit Paket Ücreti + Pakete Dahil RECOrion Kredisi + Ek Kullanım" hibrit modeline dayanır. Kullanıcı karmaşık token hesapları görmez; tek bir kurumsal **Kredi** birimi üzerinden harcama yapar.

| Paket Özelliği | Deneme (Pilot) | Başlangıç | Profesyonel | Kurumsal (Enterprise) |
|---|---|---|---|---|
| **Hedef Kitle** | 14 Günlük Deneme | Küçük Ölçekli Ekipler | Büyüyen Şirketler | Büyük Kurumlar |
| **İnsan Kullanıcı** | 3 Kullanıcı | 5 Kullanıcı | 25 Kullanıcı | Sınırsız / Sözleşmeli |
| **AI Personel Kadrosu**| 2 Ajan | 5 Ajan | 20 Ajan | Özel Kadro |
| **Aktif Proje Limiti** | 1 Proje | 3 Proje | 20 Proje | Sınırsız Proje |
| **Aylık Kredi Hacmi** | Başlangıç Hibesi | Temel Kredi Paketi | Genişletilmiş Kredi | Özel Ayrılmış Kapasite |
| **Çıktı Deposu** | Sınırlı Kota | 10 GB MinIO | 100 GB MinIO | 1 TB+ Özel Depolama |
| **Dahili Git (Gitea)** | 1 Repo | 5 Repo | 50 Repo | Sınırsız Repo |
| **Dış Git (BYO)** | GitHub / GitLab | GitHub / GitLab | GitHub / GitLab | GitHub / GitLab / On-Prem |
| **Debate Arena** | Kapalı | Kısıtlı Tur | Tam Erişim | Öncelikli Çıkarım |
| **Multi-Modal Girdi** | Kapalı | Temel Görsel | Tam Vision + OCR | Öncelikli Vision + Ses |
| **Entegrasyonlar** | Kapalı | Kapalı | Webhook / API / Jira | Tam Özel Entegrasyon |
| **Kurumsal Güvenlik** | Standart | Standart | Audit Trail Dışa Aktar | SSO / SAML / Özel SLA |

---

## 9. Sonuç ve Katma Değer Özeti

RECOrion Sürüm 3.0; Antigravity bağımlılığını tamamen ortadan kaldırarak bağımsız bir **Work Area** arayüzü, 13 güçlü yerli/açık kaynak modelden oluşan **EVREN LLM Kataloğu**, salt koda bağımlı olmayan evrensel **Çıktı Deposu (Artifact Store)** ve deterministik **Temporal iş akışı motoru** ile kurumsal düzeyde bir "Otonom İş Fabrikası" kimliğine kavuşmuştur.

NACE entegrasyonu sayesinde her sektöre dakikalar içinde uyarlanabilen, rol eşitliğiyle yönetişimi sağlayan ve sürekli öğrenen kurumsal hafızasıyla günden güne akıllanan RECOrion; piyasadaki tek boyutlu kod asistanlarının ve basit workflow araçlarının fersah fersah ötesinde, tam teşekküllü bir kurumsal dijital dönüşüm platformudur.
