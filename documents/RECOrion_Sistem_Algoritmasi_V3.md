# RECOrion (Operational Reasoning & Intelligence Orchestration Network)
## Sistem Algoritması (Sürüm 3.0 – Deterministik İşleyiş)

**Tarih:** 06 Ekim 2026  
**Doküman Kodu:** REC-SYS-ALG-V3  
**Standart:** Deterministik Durum Makineleri, Saga Modeli ve Olay Kaynaklı Yürütme  

---

## BÖLÜM 1: MİMARİ VE SİSTEM VARLIK MODELİ (DATA SCHEMA & STATE MACHINES)

Sistemin deterministik, hatasız ve çok kiracılı (multi-tenant) çalışabilmesi için ilişkisel veritabanı (PostgreSQL) ve vektör uzayı (Qdrant) varlık durumları kesin olarak tanımlanmıştır:

### 1.1 Varlık Hiyerarşisi
$$\text{Platform} \longrightarrow \text{NACE Kataloğu} \longrightarrow \text{Tenant (Ana Şirket)} \longrightarrow \{\text{Kullanıcılar}, \text{AI Personel Havuzu}, \text{Roller/Onay Grupları}\} \longrightarrow \text{Projeler} \longrightarrow \text{Backlog (Epic/Görev)} \longrightarrow \text{DAG İş Akışı}$$

### 1.2 Rol Eşitliği Prensibi (Actor Parity)
Sistemde iki tür aktör tanımlıdır: $\text{ActorType} \in \{\text{HUMAN}, \text{AI\_AGENT}\}$.  
Her iki aktör türü de ortak bir `actors` tablosuna bağlıdır; görev icracısı, onay mercii veya proje yöneticisi rolünü üstlenebilir.

### 1.3 Ayrıştırılmış Durum Makineleri (State Machines)

```
[GÖREV DURUMU]
BACKLOG ➔ READY ➔ IN_PROGRESS ➔ WAITING_APPROVAL ➔ (IN_DEBATE) ➔ REVISION ➔ DONE
  └─► BLOCKED / QUARANTINED / CANCELLED / FAILED / TIMED_OUT

[PROJE DURUMU]
DRAFT ➔ PROVISIONING ➔ READY ➔ ACTIVE ➔ RELEASE_PENDING ➔ RELEASED
  └─► PROVISION_FAILED / PAUSED / CANCELLED

[AJAN DURUMU]
IDLE ➔ WORKING ➔ WAITING ➔ QUARANTINED / DISABLED  (PROMOTED bir durum değil, olaydır)

[ARTIFACT SÜRÜMÜ]
DRAFT ➔ SUBMITTED ➔ APPROVED / REJECTED ➔ SUPERSEDED
```

### 1.4 Hafıza Kapsamları (İki Kademeli Kolektif Hafıza Modeli)
RECOrion mimarisinde hafıza yapısı kesin olarak **2 seviyeli kolektif zekâ modeli** üzerine kuruludur. Tek bir Qdrant koleksiyonu üzerinde payload bazlı zorunlu filtreleme (`tenant_id`, `scope`) uygulanır:
1. **AI Personelleri (Ajanları) Hafızası (`NS_AGENT`):** Şirket bünyesindeki her bir AI personelinin bireysel hafızasıdır. Ajanın kendi uzmanlık dokümanları (PDF, Word, Excel, teknik kılavuzlar), rolüne özel tecrübeleri, görev başarımları ve kişisel uzmanlık birikimidir.
2. **Şirket Kurum Hafızası (`NS_GLOBAL`):** Şirketin tüm AI personellerinin hafızalarının, deneyimlerinin ve uzmanlıklarının toplamı/sentezi olan merkezi kolektif kurum hafızasıdır (Kurumsal manifesto, şirket standartları, onaylanmış mimari kararlar, kurumsal politikalar ve tüm personelin ortak aklı).
*(Not: Sistemde bağımsız bir 3. katman olarak izole "Proje Hafızası" tutulmaz. Proje süreçleri doğrudan Şirket Kurum Hafızası (`NS_GLOBAL`) ve projede görev alan AI personellerinin hafızalarından (`NS_AGENT`) beslenir; projelerde üretilen ve onaylanan yeni bilgi/deneyimler ise doğrudan Şirket Kurum Hafızasına terfi ettirilerek şirketin tüm AI personellerinin ortak aklına katılır.)*

---

## FAZ 0: YEREL DOCKER BOOTSTRAP VE İZOLASYON ALGORİTMASI

**Amaç:** Sistem bileşenlerinin yerel bilgisayarda, dış dünyaya bağımlı olmadan, tam izole Docker konteynerleri üzerinde deterministik olarak ayağa kaldırılmasıdır.

```
┌────────────────────────────────────────────────────────────────────────┐
│               DOCKER BRIDGE AĞI (DARK DB & INTERNAL SERVICES)          │
│                                                                        │
│  [PostgreSQL 16 + pgvector] ◄──► [Qdrant] ◄──► [Redis Streams]         │
│               ▲                     ▲                  ▲               │
│               │                     │                  │               │
│  [Temporal Server] ◄────────► [MinIO] ◄────────► [Gitea]               │
│               ▲                     ▲                  ▲               │
│               │                     │                  │               │
│  [FastAPI Backend] ◄────────► [Worker Daemons] ◄──► [LLM Gateway]      │
│               ▲                                        │               │
│               │ (İç REST / gRPC)                       ▼               │
│  [React Web UI & Work Area]                  [Mock LLM / EVREN API]    │
│  (Host Port: 3000)                                                     │
└────────────────────────────────────────────────────────────────────────┘
```

### Adım 0.1: Ağ ve Konteyner İzolasyonu (Dark DB Kuralı)
1. Docker Compose üzerinde iki ağ katmanı tanımlanır: `recorion-edge` (yalnızca Web UI ve API dışa bakar) ve `recorion-internal` (veritabanları ve kuyruklar dış internete ve host portlarına tamamen kapalıdır).
2. PostgreSQL ve Qdrant servisleri host portlarına (`0.0.0.0`) bind edilmez; yalnızca konteynerler arası iç DNS ile erişilir.
3. Konteynerler rootless ve salt okunur (read-only) dosya sistemi güvenlik bayraklarıyla başlatılır.

### Adım 0.2: Otomatik Migrasyon ve Model Kataloğu Seed Yüklemesi
1. PostgreSQL ayağa kalktığında Alembic migrasyonu tetiklenir: `tenants`, `actors`, `llm_providers`, `llm_models`, `plans`, `domain_packs` tabloları oluşturulur ve Row-Level Security (RLS) politikaları kilitlenir.
2. `llm_providers` tablosuna `EVREN` sağlayıcısı ve geliştirme modu için `MOCK` sağlayıcısı eklenir.
3. `llm_models` tablosuna 13 EVREN modeli başlangıç kaydı (seed) olarak basılır:
   - `qwen3-asr-1.7b` (AUDIO)
   - `deepseek-ocr-2`, `dots-ocr` (OCR)
   - `qwen3-guard-4b` (GUARD)
   - `qwen3-reranker-8b` (RERANKER)
   - `qwen3-embedding-8b` (EMBEDDING)
   - `qwen3-vl-30b` (VISION)
   - `glm-5.3`, `qwen3.8-flash-next`, `deepseek-v4.1-flash`, `mimo-v2.6-pro`, `gemma-4-31b`, `deepseek-v4-flash` (CHAT)

---

## FAZ 1: ŞİRKET ONTOJİSİ VE NACE MANİFESTOSU ALGORİTMASI

**Girdi:** Şirket unvanı, NACE faaliyet kodları listesi (birincil ve ikincil kodlar).  
**Çıktı:** Kurumsal Manifesto, Şirket Ontolojisi ve `NS_GLOBAL` Kök Vektörü.

```
ALGORİTMA: Sirket_Ontolojisi_ve_Manifesto_Uretimi
GİRDİ: SirketAdi, NaceKodlariListesi[], SuperAdminBilgisi
ÇIKTI: TenantContext, GlobalMemoryRoot

1. Platform Admin, 'tenants' tablosuna müşteri şirket kaydını açar.
2. NaceKodlariListesi içerisindeki her bir NACE kodu 'tenant_nace' tablosuna kaydedilir.
3. LLM Gateway tetiklenir (Model: 'glm-5.3' veya 'mimo-v2.6-pro'):
     Prompt: "Şirket: {SirketAdi}, Faaliyet NACE Kodları: {NaceKodlariListesi}. 
              Bu şirketin kurumsal vizyonunu, iş yapış ahlakını, sektör standartlarını 
              ve operasyonel çerçevesini belirleyen 'Kurumsal Manifesto' metnini oluştur."
4. Üretilen taslak Manifesto metni Şirket Süper Admininin onay ekranına düşer.
5. Süper Admin metni inceler, gerekirse düzenler ve 'ONAYLA' komutunu verir.
6. Onaylanan Manifesto metni:
     a. 'tenants.manifesto_content' alanına kaydedilir.
     b. 'qwen3-embedding-8b' modeli ile vektörize edilir.
     c. Qdrant'ta o şirkete ait 'NS_GLOBAL' koleksiyonuna 'ROOT_MANIFESTO' etiketiyle indekslenir.
7. Artık şirkette çalışacak tüm yapay zeka personelleri bu kurumsal kimliğe bağlıdır.
```

---

## FAZ 2: DİJİTAL İK & HİBRİT KAYNAK HAVUZU ALGORİTMASI (AUTO-HR)

**Girdi:** Onaylanmış NACE kodları, kurumsal manifesto, yüklenen uzmanlık dokümanları.  
**Çıktı:** İşe alınmış AI Personelleri, İnsan Kullanıcılar ve Eşleştirilmiş Onay Rolleri.

```
ALGORİTMA: Auto_HR_ve_Personel_Provizyonu
GİRDİ: TenantID, NaceKodlari[], DokumanDosyalari[]
ÇIKTI: PersonelHavuzu, OnayKurullari

1. Sistem 'domain_packs' tablosundan ilgili NACE kodlarına uyan ideal kadro şablonunu çeker.
2. EĞER Süper Admin 'Auto-HR Önerisi Uygula' derse:
     Örnek Kadro:
       - 1x Sistem/İş Analisti (Model: 'glm-5.3', Profil: 'reasoning')
       - 2x Yazılım Geliştirici (Model: 'deepseek-v4.1-flash', Profil: 'code-strong')
       - 1x Kalite Güvence / QA (Model: 'deepseek-v4-flash', Profil: 'code-review')
       - 1x İletişim / PR (Model: 'gemma-4-31b', Profil: 'light-chat')
3. Her ajan için 'actors' ve 'agents' tablolarına kayıt açılır; 'autonomy_level = L1' atanır.
4. Doküman Yükleme ve Vektörizasyon:
     Yüklenen her bir dosya için (PDF, Word, Excel, Taranmış Evrak):
       a. Dosya uzantısına göre motor seçilir:
            - Taranmış / Karmaşık Tablo ise: 'dots-ocr' veya 'deepseek-ocr-2' ile metin çıkarılır.
            - Kod veya metin ise: doğrudan ayrıştırılır.
       b. Parçalama (Chunking):
            - Kod dosyaları: AST / Fonksiyon sınırlarına göre parçalanır.
            - Metin dosyaları: 512 token uzunluk, 64 token örtüşme ile parçalanır.
       c. Metin parçaları 'qwen3-embedding-8b' ile vektörleştirilir.
       d. Qdrant'a 'tenant_id={TenantID}', 'scope=NS_AGENT', 'agent_id={AjanID}' payload etiketiyle yazılır.
5. Onay Gruplarının Kurulumu:
     a. 'approval_groups' tablosuna kurullar açılır (Örn: 'Mimarlar Onay Kurulu', 'Mali Kontrol Grubu').
     b. 'group_members' tablosuna insan kullanıcılar ve yetkili AI ajanlar eşit haklarla atanır.
```

---

## FAZ 3: PROJELENDİRME, İŞ ANALİSTİ BACKLOG & ATOMİK PROVISIONING

**Girdi:** Proje adı, üst düzey isterler dokümanı, deadline tarihi, seçilen ajan kadrosu.  
**Çıktı:** Otomatik Backlog (Epic/Görevler), Doğrulanmış DAG ve İzole Proje Ortamı.

```
ALGORİTMA: Proje_Baslatma_ve_Atomik_Provizyon
GİRDİ: ProjeAdi, IsterlerMetni, Deadline, Kadro, CizilenDAG
ÇIKTI: ProjeContext, BacklogGorevleri[], GiteaRepo

1. Proje Yöneticisi projeyi 'STATUS=DRAFT' olarak açar.
2. İş Analisti Ajanının Tetiklenmesi (Autonomous Backlog Generation):
     a. İş Analisti Ajanı ('glm-5.3' / 'mimo-v2.6-pro') devreye girer.
     b. İsterler metnini ve kurumsal hafızayı analiz eder.
     c. Sisteme hiyerarşik Backlog önerisi sunar:
          - Epic'ler (Ana Modüller)
          - Kabul Kriterleri (Acceptance Criteria) tanımlı Görevler (Tasks)
          - Tahmini Efor ve Bağımlılıklar
     d. İnsan yönetici önerilen Backlog'u inceler, revize eder ve ONAYLAR.
3. DAG Doğrulama (Topological Sort):
     İş akışı grafı taranır:
     EĞER Graf içinde döngüsel kenar (Cycle) varsa:
       Hata: "DAG döngüsüz olmalıdır. Ret/revizyon döngüleri kenar değil, düğüm özelliğidir."
     DEĞİLSE:
       Topolojik sıra hesaplanır ve 'workflow.json' sözleşmesine derlenir.
4. Atomik Provizyonlama (Saga Pattern ile Hata Korumalı Kurulum):
     Proje durumu 'STATUS=PROVISIONING' yapılır.
     ADIM_A: PostgreSQL'de proje, görevler ve iş akışı kaydedilir.
     ADIM_B: Projede görev alacak AI personellerinin hafızaları (`NS_AGENT`) ile Şirket Kurum Hafızası (`NS_GLOBAL`) proje bağlamına bağlanır (Ayrı bir proje vektör koleksiyonu açılmaz; 2 seviyeli kolektif hafıza kullanılır).
     ADIM_C: EĞER AlanPaketi == 'YAZILIM' ise:
               Gitea API'ye bağlanılır, 'recorion-{tenant_slug}/{project_slug}' private reposu açılır,
               README.md ve başlangıç iskeleti commit edilir.
     EĞER herhangi bir adım başarısız olursa:
       Tüm önceki adımlar telafi edilir (Rollback); proje durumu 'PROVISION_FAILED' yapılır.
     DEĞİLSE:
       Proje durumu 'STATUS=ACTIVE' olarak güncellenir.
```

---

## FAZ 4: WORK AREA YÜRÜTME & ÇOKLU AJAN GÖREV ÇEVRİMİ

**Amaç:** Kullanıcının 3 bölmeli Work Area üzerinden ajanların görev icrasını anlık takip ettiği, gerektiğinde müdahale ettiği ve tartışmaları (Debate Arena) izlediği merkezi çalışma çevrimidir.

```
ALGORİTMA: Work_Area_Gorev_Yurutumu
GİRDİ: AktifGorev, AjanContext, KurumsalBaglam
ÇIKTI: UretilenArtifact, KaliteKarti

1. Görev sırası gelen Ajan 'STATUS=WORKING' durumuna geçer.
2. Bağlam Toplama (Hybrid RAG - İki Kademeli Kolektif Hafıza Taraması):
     a. Görev açıklaması ve kabul kriterleri embedding modeline iletilir.
     b. Qdrant'tan zorunlu 'tenant_id' filtresiyle sistemdeki 2 hafıza taranır:
          - 1. Şirket Kurum Hafızası (`NS_GLOBAL`: Şirketteki tüm AI ajanlarının hafıza toplamı, kurumsal manifesto, standartlar ve ortak know-how)
          - 2. Görevli AI Personelinin Hafızası (`NS_AGENT`: İlgili ajanın uzmanlık dokümanları, geçmiş görev deneyimleri ve rol birikimi)
     c. Çıkan aday metinler 'qwen3-reranker-8b' modelinden geçirilerek en alakalı ilk 5 parça seçilir.
3. Multi-Modal Girdi Denetimi:
     EĞER kullanıcı sohbet alanına Figma linki, ekran görüntüsü veya şema görseli bırakmışsa:
       'qwen3-vl-30b' modeli görseli ayrıştırır ve teknik ister bağlamına enjekte eder.
4. Güvenlik Ön Filtresi:
     Görev istemi ve bağlam 'qwen3-guard-4b' modeline iletilir.
     EĞER Prompt Injection veya zararlı içerik tespit edilirse:
       Görev durdurulur, güvenlik alarmı üretilir.
5. Görev İcrası ve Araç Çağırma (Sandbox Execution):
     Ajan kendisine tanımlı araçları (Tools) kullanır:
     EĞER görev kod derleme/test çalıştırma gerektiriyorsa:
       Sandbox Runner servisi rootless, ağ bağlantısız efemeral bir Docker konteyneri açar.
       Kod konteynerde derlenir, test koşulur, çıktı yakalanır ve konteyner yok edilir.
6. Tartışma Arenası (Debate Arena Algoritması):
     EĞER QA Ajanı ('deepseek-v4-flash'), Coder Ajanının ('deepseek-v4.1-flash') çıktısında mimari çelişki bulursa:
       a. Work Area içinde 'Debate_Thread' alt başlığı açılır.
       b. Ajanlar karşılıklı teknik argümanlarını paylaşır (Maksimum Tur: 4).
       c. Proje Yöneticisi aktör (İnsan veya AI) tartışmayı canlı izler.
       d. Hakem aktör uzlaşı kararını açıklar; bu karar bir Mimari Karar Kaydı (ADR) olarak kaydedilir.
7. Görev tamamlanır; üretilen çıktı 'Artifact Store' servisine teslim edilir.
```

---

## FAZ 5: HİBRİT ONAY (MAKER-CHECKER & SLA) VE HATA YÖNETİMİ

**Girdi:** Ajan tarafından üretilen Artifact, Kalite Kapısı test sonuçları, Onay Grubu.  
**Çıktı:** Görevin sonraki adıma akışı, revizyon döngüsü veya karantina.

```
ALGORİTMA: Onay_ve_Hata_Yonetimi
GİRDİ: GorevID, ArtifactSurumu, ApprovalGroup, RetryCount
ÇIKTI: DAG_Status

1. Görev 'WAITING_APPROVAL' durumuna alınır.
2. Kalite Kapısı (Quality Gate) Özet Paketi üretilir:
     - Yazılım Projesi: "Birim Test: 24/24 Geçti, SAST: Temiz, Kapsam: %86"
     - Hukuk/Ofis Projesi: "Şablon Uyumu: %100, Riskli Madde: 0, Atıf Doğruluğu: Onaylı"
3. Onay Bildirimi:
     Work Area'daki 'Onayımı Bekleyenler' kutusuna görev düşer; grup üyelerine bildirim iletilir.
4. Karar Verme ve Yarış Durumu (Race Condition) Kilidi:
     İlk karar veren yetkili aktörün işlemi veritabanı düzeyinde kilitlenir (Locking):
     
     DURUM_A: ONAYLANDI (Approve):
       - Maker-Checker Kontrolü:
           EĞER KararVeren == UretenAjan VEYA KararVeren.ModelAilesi == UretenAjan.ModelAilesi ise:
             İşlem Reddedilir: "Üreten aktör kendi çıktısını onaylayamaz."
           EĞER Gorev.Kritiklik == 'RELEASE' VE KararVeren.ActorType != 'HUMAN' ise:
             İşlem Reddedilir: "Nihai canlıya alma adımlarında en az bir İnsan Onayı zorunludur."
       - Onay geçerli ise: Artifact 'STATUS=APPROVED' yapılır, DAG motoru sonraki düğümü tetikler.

     DURUM_B: REVİZYON İSTENDİ (Revise):
       - RetryCount = RetryCount + 1.
       - EĞER RetryCount >= 3 ise:
           * Ajan 'STATUS=QUARANTINED' moduna alınır.
           * Şirket Süper Adminine acil eskalasyon fırlatılır: "Ajan 3 kez ardışık ret aldı."
           * Saga Geri Alma: Geçersiz kodlar için 'git revert' atılır veya artifact sürümü iptal edilir.
       - DEĞİLSE:
           * Düzeltme notu ajana iletilir, ajan aynı görev için yeniden çalıştırılır.

5. SLA Zaman Aşımı (Timeout) Algoritması:
     EĞER görev Onay Bekleme SLA süresini (Örn: 24 saat) aşarsa:
       - Onay talebi otomatik olarak bir üst hiyerarşik kurula (Süper Admin) eskalasyon yapılır.
```

---

## FAZ 6: BİLGİ TERFİSİ VE GÜVEN TABANLI AJAN SEVİYELENDİRME

**Amaç:** Başarıyla tamamlanan projelerden elde edilen tecrübelerin Şirket Kurum Hafızasına (tüm AI ajanlarının kolektif ortak aklına) kazandırılması ve güvenilirliği kanıtlanan ajanların kademe terfisi (L1 → L2 → L3) almasıdır.

```
ALGORİTMA: Kurumsal_Hafiza_Terfisi_ve_Ajan_Kademesi
GİRDİ: TamamlananProje, AjanMetrikleri[]
ÇIKTI: GlobalHafizaGuncelleme, AjanKademeArtisi

1. Proje Genel Yöneticisi 'RELEASE' onayını verir.
2. Bilgi Ayıklama ve Anonimleştirme:
     a. Projedeki tüm onaylanmış artifact'ler ve ADR kayıtları taranır.
     b. AST kuralları ve PII temizleyici çalıştırılarak müşteri sırları, kişi isimleri ve kurum kimlikleri silinir.
     c. Yalnızca soyut teknik 'know-how' ve iş algoritmaları çıkartılır.
3. İnsan Onaylı Bilgi Terfisi (Kolektif Kurum Hafızasına Aktarım):
     - Ayıklanan bilgi doğrudan hafızaya yazılmaz; 'memory_items' tablosuna 'STATUS=CANDIDATE', 'scope=GLOBAL' olarak eklenir.
     - Şirket Bilgi Yöneticisi (Human Admin) onay kutusundan inceleyip "Onayla" dediği anda:
         'qwen3-embedding-8b' ile vektörize edilerek Qdrant 'NS_GLOBAL' katmanına yazılır.
     - Böylece tek bir ajanın projede edindiği doğrulanmış tecrübe, şirketin tüm AI personellerinin ortak Kurum Hafızasına katılarak kolektif zekâya dönüşür.
4. Güven Tabanlı Otonom Kademe Terfisi (L1 - L3 Autonomy Promotion):
     Ajanın tüm projelerdeki geçmiş metrikleri analiz edilir:
     (Hesaplamada yalnızca İNSAN aktörler tarafından verilen onaylar geçerli sayılır.)
     
     EĞER BasariliProjeSayisi >= 10 VE InsanRetOrani < %5 ise:
       - Ajan Seviyesi: 'L1' ➔ 'L2' (Rutin işlerde örnekleme onayına geçiş).
     EĞER BasariliProjeSayisi >= 25 VE InsanRetOrani < %2 ise:
       - Ajan Seviyesi: 'L2' ➔ 'L3' (Yalnızca kritik düğümlerde insan onayı, diğer adımlarda tam özerklik).
     
     TERSİ DURUMDA (Ceza / İndirgeme):
       EĞER L2/L3 seviyesindeki bir ajan üst üste 2 kez insan reddi alırsa:
         - Ajan Seviyesi otomatik olarak 'L1' seviyesine düşürülür (Demotion); tam denetime geri alınır.
```

---

## FAZ 7: TELEMETRİ VE TOKEN BAZLI KREDİ/EFOR ANALİTİĞİ

**Amaç:** Klasik dolar/saat faturası yerine, model yetenek katsayılarına dayalı şeffaf **RECOrion Kredisi** tüketimini ve proje sağlık metriklerini hesaplamaktır.

### 7.1 Formül ve Kredi Tüketim Modeli
Her bir LLM/Vision/Embedding çağrısı için kredi hesabı token bazlı ve deterministik hesaplanır:

$$\text{Kredi} = \sum_{i=1}^{n} \left[ \text{EffortCoefficient}(\text{Model}_i) \times \left( \frac{\text{Giriş Token}}{1000} \times 1.0 + \frac{\text{Çıkış Token}}{1000} \times 2.0 \right) \right]$$

*Effort Katsayıları:* `glm-5.3` = 3.5, `mimo-v2.6-pro` = 3.0, `deepseek-v4.1-flash` = 1.8, `qwen3.8-flash-next` = 1.0, `qwen3-vl-30b` = 2.5, `qwen3-embedding-8b` = 0.2.

### 7.2 Otonomluk Oranı Formülü
Projedeki insan müdahalesiz tamamlanan iş hacmini ölçer:

$$\text{Otonomluk Oranı (\%)} = \left( \frac{\text{İnsan Müdahalesi Olmadan Onaylanan Düğümler}}{\text{Toplam DAG Düğüm Sayısı}} \right) \times 100$$

### 7.3 Proje Sağlık ve Kaynak Raporu (Project Health Card)
Proje tamamlandığında Work Area panosunda otomatik üretilir:
1. Hangi ajanın hangi görevde kaç token ve kredi harcadığı,
2. Yaşanan Debate Arena oturum sayısı ve varılan ADR uzlaşıları,
3. Hedeflenen deadline ile gerçekleşen teslim tarihi arasındaki varyans analizi,
4. Projenin genel Otonomluk Skoru.

---

## BÖLÜM 8: ÖZET ALGORİTMA DURUM TABLOSU

| Faz | Temel Görev | Girdi | Çıktı | Çekirdek Güvenlik / Doğrulama |
|---|---|---|---|---|
| **Faz 0** | Docker Altyapı Ayağa Kaldırma | Compose YAML | PostgreSQL, Qdrant, MinIO, Gitea, Temporal | Dark DB, Host Port İzolasyonu, Rootless |
| **Faz 1** | NACE & Manifesto Kurulumu | NACE Kodları | Kurumsal Manifesto & NS_GLOBAL (Kolektif Hafıza Kökü) | Süper Admin Onayı, Model Bağımsız Prompt |
| **Faz 2** | Auto-HR & Personel Havuzu | Şirket Dokümanları | AI Ajan Kadrosu & NS_AGENT (Personel Hafızası) | OCR, Vektör İzolasyonu, Rol Eşitliği |
| **Faz 3** | Backlog & DAG Provizyonu | İsterler & Deadline | Backlog & workflow.json | Topolojik Sıralama (Döngüsüzlük), Saga Rollback |
| **Faz 4** | Work Area Görev Çevrimi | Backlog Görevi | Artifact (Kod/Belge/Tablo) | Sandbox İzolasyonu, Guard Filtresi, Debate Arena |
| **Faz 5** | Hibrit Onay & Hata Yönetimi | Çıktı & Kalite Kartı | Onaylanmış Görev / Revizyon | Maker-Checker Kuralı, 3x Karantina, Kilit |
| **Faz 6** | Bilgi Terfisi & L1-L3 Terfi | Proje Çıktıları | NS_GLOBAL Kolektif Know-How & Ajan Seviyesi | PII Filtresi, İnsan Onaylı Terfi, Demotion |
| **Faz 7** | Telemetri & Kredi Hesabı | Çağrı İstatistikleri | Kredi Tüketimi & Sağlık Raporu | Sert Kota Limiti, Token Bazlı Formül |

Bu 7 fazlı algoritma omurgası; RECOrion Sürüm 3.0'ın yerel Docker üzerinde deterministik, izole ve yüksek verimle çalışmasını sağlayan değişmez mühendislik şartnamesidir.
