# RECOrion Merkez Yönetim Kılavuzu (RECDx Ana Kontrol Merkezi)

> **Dikkat:** Bu kılavuz **yalnızca RECDx içinde kullanılır**. Müşterilere gönderilmez. İçinde yapay zeka altyapısının (EVREN) ve model adlarının geçtiği bölümler vardır; bu bilgiler müşteri kılavuzlarında yer almaz.

Sürüm: 03.11.2026 · Kaynak: RECOrion'un güncel ekranları

# Bu kılavuz hakkında

## Kimin için?

Bu kılavuz, RECOrion'un **Merkez Yönetim** bölümünü (ekranda adı **Ana Kontrol Merkezi**, sol menünün üstünde RECOrion logosu) kullanacak RECDx çalışanları içindir. Bu bölümü yalnızca **RECDx süper yöneticileri** açabilir. Müşteri şirketlerinin çalışanları bu ekranları hiç görmez.

Merkez Yönetim'de şunları yaparsınız:

- Resmi siteden gelen müşteri başvurularını onaylar ya da reddedersiniz.
- Müşteri şirketlerini (kiracıları) ekler, düzenler, pasife alır, siler; kredi yüklersiniz.
- Tüm müşterilerin kullandığı ortak katalogları (sektör, meslek, departman, unvan, proje şablonu, mevzuat, bağlantı) yönetirsiniz.
- Satılan paketleri, izinleri ve sistem rollerini tanımlarsınız.
- Sistemin gönderdiği e-postaları ve otomatik hatırlatmaları düzenlersiniz.
- Yapay zeka altyapısını (RECAi adlarının arkasındaki modeller, model yönlendirme, fiyatlar) yönetirsiniz.

## Nasıl okunur?

- Kılavuz sol menünün sırasını izler: önce **Genel düzen** ve **Menü ağacı**, sonra her menü için bir bölüm.
- Her ekran bölümünde sırasıyla şunlar vardır: ekranın amacı, kimlerin gördüğü, ekranın bölümleri, alanlar tablosu, düğmeler tablosu, durumlar ve hata mesajları, adım adım örnek, ipuçları ve sık sorulan sorular.
- Bir işi hangi ekranda yapacağınızı bilmiyorsanız en sondaki **Hızlı başvuru** tablosuna bakın.
- Ekranda yazan düğme ve alan adları **kalın** yazılmıştır. Ekranda gördüğünüz metinle kılavuzdaki metin aynıdır.
- Çift köşeli parantezle başlayan "EKRAN" satırları ekran görüntüsü yerleridir; görüntüler sonradan eklenecektir.

## Örneklerde kullanılan kurgusal kişiler

Örneklerde gerçek müşteri adı kullanılmaz. Tüm örnekler aşağıdaki kurgusal şirket ve kişilerle anlatılır:

| Kişi | Görevi |
|---|---|
| **Örnek Lojistik A.Ş.** | Kurgusal müşteri şirket (alan adı: orneklojistik.com.tr) |
| Ayşe Yılmaz | Örnek Lojistik'in şirket yöneticisi |
| Mehmet Demir | Örnek Lojistik'te proje yöneticisi |
| Zeynep Kaya | Örnek Lojistik'te muhasebeci |
| Can Öztürk | Örnek Lojistik'te uzman |
| "RECDx süper yöneticisi" | Bu kılavuzu kullanan siz |

> **Dikkat:** Canlı sistemde deneme yaparken yalnızca **RECOrion Canlı Test A.Ş.** şirketini kullanın. Gerçek müşteri şirketlerine deneme amaçlı dokunmayın. RECDx ana şirketi ve RECDx süper yönetici hesapları hiçbir koşulda silinmez.

## Simgeler, rozetler ve renkler

| Görünüm | Anlamı |
|---|---|
| Yeşil rozet (**AKTİF**, **Aktif**, **Yayında**, **● Çalışıyor**, **Öğrenildi**) | Kayıt kullanımda, her şey yolunda |
| Gri rozet (**PASİF**, **Pasif**, **Arşivde**, **○ Kapalı**) | Kayıt kullanım dışı ya da kapalı |
| Sarı / turuncu rozet (**⏳ Onay Bekliyor**, **▲ Yavaş**, **Taslak · uzman kontrolü bekliyor**, **Fiyat yok**) | Sizin bir işlem yapmanız ya da dikkat etmeniz gerekiyor |
| Kırmızı rozet (**✕ Reddedildi**, **✕ Erişilemiyor**, **Hata**, **3 Ay Kaldı**) | Sorun var ya da süre bitiyor |
| Mavi rozet (**Bilgi**, **CRM fırsatı**, **Yayımlanmamış değişiklik var**) | Bilgi amaçlı durum |
| 🛡️ | Korunan kayıt (RECDx ana şirketi, sistem rolü) |
| 🔑 | Sistem kimliği (şirketin adres kısaltması) |
| ↻ | Yenile / yeniden ölç |
| Çöp kutusu simgesi | Sil |

Renk tek başına anlam taşımaz; her rozetin üzerinde yazı da vardır.

## Kavramlar sözlüğü

| Kavram | Anlamı |
|---|---|
| **Şirket (kiracı)** | RECOrion'u kullanan müşteri kurum. Her şirketin verisi diğerlerinden ayrıdır. |
| **RECDx ana şirketi** | RECOrion'u işleten RECDx'in kendi şirket kaydı. Silinemez; kredisi sınırsızdır, yalnızca ölçülür. |
| **Başvuru** | Resmi sitede paket satın alma formunu dolduran ya da sizin **Yeni Müşteri Ekle** ile açtığınız şirket kaydının onay bekleyen hâli. |
| **Sistem kimliği** | Şirket adından otomatik üretilen kısa, tekil ad (ör. "ornek_lojistik"). Kartlarda **🔑 Sistem Kimliği / URL** olarak görünür. |
| **Kiralama paketi** | Müşterinin satın aldığı abonelik: fiyat, kullanıcı ve AI personel sınırı, aylık kredi, dahil RECAi adları. |
| **Kredi** | Yapay zeka kullanım birimi. Her işlem şu kadar kredi harcar: model katsayısı × (giriş token/1000 + 2 × çıkış token/1000). |
| **Aylık kredi hakkı** | Paketle her ay verilen kredi. Ay sonunda kullanılmayan kısmı silinir. |
| **Ek kredi** | Sizin yüklediğiniz kredi. Ay sonunda silinmez, sonraki aylara devreder. |
| **Token** | Yapay zekanın metni ölçtüğü küçük parça (kabaca bir kelimenin bir kısmı). Maliyet ve kredi token sayısına göre hesaplanır. |
| **AI personel** | Şirketin işe aldığı yapay zeka çalışanı. Bir unvanı ve departmanı vardır. |
| **RECAi** | RECOrion'un yapay zekasının adı. Müşteri hiçbir yerde gerçek model adını görmez, yalnızca RECAi adını görür. |
| **RECAi adları** | Müşterinin seçebildiği yapay zeka seviyeleri: **RECAi Mergen** (genel işler), **RECAi Hızlı** (kısa ve hızlı yanıtlar), **RECAi Derin** (derin analiz ve uzun metin). |
| **RECAi yetenekleri** | Pakete göre açılan ek yetenekler: **RECAi Görsel** (görsel okuma), **RECAi Ses** (ses kaydını yazıya dökme), **RECAi Okur** (taranmış belge okuma). |
| **EVREN** | TÜBİTAK BİLGEM'in yapay zeka model altyapısı. RECAi adlarının arkasında EVREN modelleri çalışır. |
| **Model** | EVREN'deki tek bir yapay zeka modeli. Türleri: sohbet (CHAT), kod (CODE), görsel (VISION), metin vektörü (EMBEDDING), sıralama (RERANKER), belge okuma (OCR), ses (AUDIO). |
| **Efor katsayısı** | Modelin kredi formülündeki çarpanı. Güçlü (pahalı) modelde büyük, hafif modelde küçük olur. |
| **CR** | EVREN'in kendi kredi birimi. RECDx'in EVREN'e ödediği maliyet CR ile ölçülür. |
| **Yedek model** | Ana model meşgulken kullanılan ikinci model. |
| **Beyin AI** | Şirketin projelerini planlayan, iş adımlarını çıkaran RECAi. |
| **Proje / Case** | Şirketin AI personel ve insanlarla yürüttüğü iş. Case, belirli bir olay için açılan kısa süreli iştir (ör. aylık masraf süreci). |
| **İş adımı** | Bir projenin ya da Case'in tek bir görevi. Sorumlu unvanı, süresi ve onay ihtiyacı vardır. |
| **Onay** | Bir iş adımının ya da kaydın bir insan tarafından kabul edilmesi. |
| **Manifesto** | Şirketin faaliyet alanını ve yapay zekadan beklentisini anlatan metin. AI personeller bu metni bağlam olarak kullanır. |
| **Sektör / meslek grubu** | T.C. Ticaret Bakanlığı sınıflamasına göre şirketin faaliyet alanı. Meslek grupları bir sektöre bağlıdır. |
| **Departman / unvan kataloğu** | Tüm müşterilerin AI personel işe alırken seçtiği hazır departman ve unvanlar (Platform Unvan Bilgisi). |
| **İzin** | Bir kullanıcının sistemde yapabildiği tek bir iş (ör. "Kullanıcı Ekleme"). |
| **Rol** | İzinlerin adlandırılmış bir paketi (ör. "Proje Yöneticisi"). Kullanıcıya rol atanır. |
| **Sistem rolü** | RECDx'in tanımladığı, tüm şirketlerde hazır gelen rol. Toplam 11 sistem rolü vardır. |
| **Temel rol** | Bir rolün sistemdeki ana davranışı (Şirket Yöneticisi, Proje Yöneticisi, Uzman Kullanıcı). Ör. temel rolü Şirket Yöneticisi olan rol, Şirket Yönetimi konsolunu açar. |
| **Odoo** | RECDx'in satış ve muhasebe sistemi. Başvurular Odoo'da müşteri ve satış siparişi olarak açılır. Ayrıca müşterilerin kendi Odoo'ları da olabilir. |
| **Mevzuat paketi** | Yasal bilgileri özetleyen kartlar. Uzman kontrolünden sonra yayımlanır; AI personel kaynak göstererek kullanır. |
| **Bağlantı kataloğu** | Müşterilerin bağlanabileceği dış sistemlerin (ERP, CRM vb.) kartları. |
| **MCP** | Yapay zekanın dış sistemlerle konuşması için kullanılan açık bağlantı standardı. |
| **Edge** | Müşterinin kendi sunucusuna kurulan küçük bağlantı programı. Kapalı ağdaki sistemlere erişim sağlar. |
| **RECSlip** | RECDx'in Odoo üzerinde çalışan masraf fişi ve ön muhasebe uygulaması. |
| **RECQmind** | RECDx'in pazar yeri e-postalarından Odoo Helpdesk bileti açan destek uygulaması. |
| **KVKK** | Kişisel Verilerin Korunması Kanunu. Bu kanun gereği RECDx süper yöneticisi müşterinin içeriğini (proje, görev, sohbet, kurum hafızası, doküman, entegrasyon bağlantıları, otomasyon kuralları) göremez. |

> **Dikkat (KVKK):** Merkez Yönetim'de yalnızca **yönetim verisi** (şirket kartı, paket, kullanıcı sayısı, kredi ve kullanım sayıları) vardır. Müşterinin projeleri, sohbetleri, kurum hafızası, dokümanları, bağlantı bilgileri, otomasyon kuralları (ör. RECSlip v2 aylık süreç kurulumu) ve kişisel erişim anahtarları size hiçbir ekranda gösterilmez. Bunları görmeniz gerekirse müşteriden ekran paylaşımı isteyin.

# Genel düzen

## Merkez Yönetim'e giriş

**Bu ekran ne işe yarar?** RECOrion'a e-posta ve şifrenizle girersiniz. Süper yönetici olduğunuz için sistem sizi doğrudan Merkez Yönetim'e götürür.

**Kimler görür?** Herkes giriş penceresini görür; Merkez Yönetim'e yalnızca süper yönetici hesapları yönlenir. Süper yönetici olmayan biri Merkez Yönetim adresini elle yazarsa resmi siteye geri gönderilir.

[[EKRAN: sy-giris | Resmi sitede açılmış "🔐 RECOrion Şirket Girişi" penceresi | Tarayıcıda RECOrion resmi sitesini açın, sağ üstteki 🔑 Giriş Yap düğmesine tıklayın]]

| Alan | Ne işe yarar | Nasıl doldurulur / seçenekler | Örnek | Zorunlu |
|---|---|---|---|---|
| **✉️ Kurumsal E-Posta Adresi** | Hesabınızı tanır | RECDx e-posta adresiniz | ad.soyad@recdx.com | Evet |
| **🔑 Güvenli Şifre** | Kimliğinizi doğrular | Şifreniz | — | Evet |
| **Beni Hatırla** | E-postanızı bu tarayıcıda hatırlar, oturumu uzun tutar | İşaretleyin ya da boş bırakın | işaretli | Hayır |

| Düğme | Ne yapar | Dikkat |
|---|---|---|
| **Giriş Yap →** | Girişi yapar; çalışırken **Giriş Yapılıyor...** yazar | Bilgi yanlışsa pencerede ⚠️ ile hata yazar |
| **Şifremi unuttum** | "Şifremi Unuttum" penceresini açar; e-postanızı yazıp **Bağlantı Gönder** dersiniz, şifre belirleme bağlantısı e-postanıza gelir | Bağlantı kayıtlı e-postaya gider |
| **✕** | Pencereyi kapatır | — |

Girişten sonra Merkez Yönetim **Dashboard (Genel Bakış)** ekranıyla açılır. Daha önce giriş yaptıysanız resmi sitenin sağ üstünde **👑 Süper Admin Konsolu →** düğmesi görünür; tıklayınca doğrudan Merkez Yönetim'e girersiniz.

> **İpucu:** Her menünün tarayıcı adres çubuğunda kendi adresi vardır. Bir ekranın adresini yer imlerine ekleyebilir, tarayıcının Geri/İleri düğmeleriyle menüler arasında gezebilirsiniz. Sayfayı yenilediğinizde aynı menü açık kalır.

## Ekranın genel yapısı

[[EKRAN: sy-genel-duzen | Merkez Yönetim'in tamamı: solda menü, üstte çubuk, ortada Dashboard | Süper yönetici olarak giriş yapın; Dashboard açılır, menü açık hâldeyken tam ekran görüntü alın]]

Ekran üç parçadan oluşur:

1. **Sol menü** (kenar çubuğu): tüm ekranlara buradan geçersiniz.
2. **Üst çubuk**: bulunduğunuz yeri, tema, yenileme ve profil düğmelerini gösterir.
3. **İçerik alanı**: seçtiğiniz menünün ekranı.

## Sol menü

Sol menünün en üstünde yazılı RECOrion logosu vardır; menü daraltılınca yalnız logonun simgesi kalır.

Menü altı gruba ayrılır: **Genel**, **Müşteriler**, **Katalog**, **Ticari & Yetki**, **İletişim & Otomasyon**, **Yapay Zeka**. Grup başlığına tıklayınca grup kapanır ya da açılır. Hangi grupları kapattığınız bu tarayıcıda hatırlanır.

Bazı menülerin sağında sayı görünür:

| Menü | Sağdaki sayı |
|---|---|
| Başvuru Onay Durum | Onay bekleyen başvuru sayısı (turuncu rozet; bekleyen yoksa görünmez) |
| Kayıtlı Şirketler | Toplam şirket sayısı |
| Sektör Tanımları / Meslek Tanımları | Tanımlı sektör / meslek sayısı |
| Kiralama Paketleri | Paket sayısı |
| İzin Kataloğu (RBAC) | İzin sayısı |
| Yetki Rolleri | Sistem rolü sayısı |
| E-Posta Şablonları / Zamanlayıcılar (Schedules) | Şablon / kural sayısı |
| RECAi ve EVREN Modelleri | Tanımlı model sayısı |
| Genel AI Modelleri | Sayı yerine **ÇEKİRDEK** etiketi (sistemin temel ayarı olduğunu hatırlatır) |

Menünün altında iki düğme vardır:

| Düğme | Ne yapar | Dikkat |
|---|---|---|
| **www.recdx.com** | RECDx resmi web sitesini yeni sekmede açar | Merkez Yönetim açık kalır |
| **Güvenli Çıkış** | Oturumu kapatır, resmi siteye döner | Onay sormaz |

### Menüyü daraltma

| Düğme | Ne yapar |
|---|---|
| Menünün sağ üstündeki ok (üzerine gelince "Menüyü Sola Doğru Kapat") | Menüyü daraltır; yalnızca simgeler kalır, içerik alanı genişler |
| Daraltılmış menüdeki ok ("Menüyü Genişlet (Aç)") | Menüyü yeniden açar |

Daraltılmış menüde menü adları görünmez; fareyle simgenin üzerine gelince adı çıkar. Daraltılmış hâlde tüm gruplar açık gösterilir.

[[EKRAN: sy-sol-menu-daraltilmis | Daraltılmış sol menü: yalnızca simgeler | Sol menünün sağ üstündeki "Menüyü Sola Doğru Kapat" okuna tıklayın]]

### Telefonda ve tablette menü

Dar ekranda sol menü gizlenir. Üst çubuğun solundaki **Menü** simgesine (üç çizgi) dokunduğunuzda menü yandan çekmece gibi açılır. Bir menüye dokunduğunuzda ya da menü dışındaki karartılmış alana dokunduğunuzda çekmece kapanır.

[[EKRAN: sy-telefon-cekmece | Telefon genişliğinde açılmış menü çekmecesi | Tarayıcıyı telefon genişliğine küçültün (ya da telefondan girin), üst soldaki Menü simgesine dokunun]]

## Üst çubuk

| Öğe | Ne işe yarar |
|---|---|
| **Ana Kontrol Merkezi / <ekran adı>** | Bulunduğunuz ekranı gösterir (ör. "Ana Kontrol Merkezi / Kayıtlı Kurumlar & Şirket Yönetimi"). Yetki Rolleri ekranında "/" işaretinden sonrası boş görünür. |
| **Tema düğmesi** (ay / güneş / ekran simgesi) | Her tıklamada temayı değiştirir: Koyu → Açık → Sistem. Üzerine gelince "Tema: <şu anki> (tıklayın: <sonraki>)" yazar. "Sistem" seçeneği bilgisayarınızın ayarını izler. |
| **↻ Verileri Yenile** | Başvuru, şirket, izin, rol, model, paket, e-posta şablonu, zamanlayıcı, sektör ve meslek listelerini sunucudan yeniden yükler. Başka bir RECDx çalışanının yaptığı değişikliği görmek için kullanın. |
| **Profil kartı** (baş harfler, adınız ve e-postanız) | **Süper Admin Profil Bilgileri** penceresini açar |

## Ortak davranışlar

- **Kanban / Liste seçici:** Birçok ekranda kayıtları kart (**Kanban**) ya da tablo (**Liste**) olarak gösterebilirsiniz. Seçtiğiniz görünüm sayfa yenilenene kadar kalır.
- **Arama kutusu:** Yazdıkça liste süzülür. Başka bir menüye geçtiğinizde arama temizlenir.
- **Bildirimler:** İşlem sonucu ekranın köşesinde kısa bir mesajla görünür (yeşil başarı, kırmızı hata, sarı uyarı). İçinde şifre geçen mesajlar okuyup kopyalayabilmeniz için 30 saniye ekranda kalır.
- **Onay penceresi:** Geri alınması zor işlemlerde başlığı **Onay** olan bir pencere açılır; **Onayla** (bazı silmelerde **Evet, devam et**) ya da **Vazgeç** seçersiniz.
- **Bilgi girişi penceresi:** Sistem sizden kısa bir bilgi isterse (ör. test e-postası adresi) başlığı **Bilgi Girişi** olan pencere açılır; **Tamam** ya da **Vazgeç** seçersiniz.
- **ESC tuşu:** Açık düzenleme penceresini kaydetmeden kapatır.
- **Zorunlu alanlar:** Alan adının yanında **\*** varsa doldurmadan kaydedemezsiniz; tarayıcı boş alanı işaretler.

## Profil penceresi: Süper Admin Profil Bilgileri

**Bu pencere ne işe yarar?** Kendi adınızı, telefonunuzu, e-postanızı, adresinizi ve şifrenizi değiştirirsiniz.

**Ne zaman kullanırım?** Şifrenizi değiştirmek ya da iletişim bilgilerinizi güncellemek istediğinizde.

**Nasıl açılır?** Üst çubuğun sağındaki profil kartına (adınızın yazdığı yer) tıklayın. Alt başlık: "Ad, telefon, e-posta, adres ve şifre güncelleyin."

[[EKRAN: sy-m-profil | Süper Admin Profil Bilgileri penceresi | Üst çubuğun sağındaki ad/e-posta kartına tıklayın]]

| Alan | Ne işe yarar | Nasıl doldurulur / seçenekler | Örnek | Zorunlu |
|---|---|---|---|---|
| **Ad Soyad** | Ekranlarda görünen adınız | Ad ve soyadınız | Ali Veli | Evet |
| **Telefon** | İletişim telefonunuz | Uluslararası biçim önerilir | +90 5XX XXX XX XX | Hayır |
| **E-posta** | Giriş e-postanız | Geçerli e-posta | ad.soyad@recdx.com | Evet |
| **Adres** | Adresiniz | Serbest metin | Maslak Teknopark, Sarıyer / İstanbul | Hayır |
| **Yeni Şifre (İsteğe Bağlı)** | Şifrenizi değiştirir | Boş bırakırsanız şifre değişmez | — | Hayır |

| Düğme | Ne yapar | Dikkat |
|---|---|---|
| **Vazgeç** / **✕** | Kaydetmeden kapatır | — |
| **Bilgilerimi Güncelle** | Bilgileri kaydeder; "✓ Sayın <ad>, profil bilgileriniz başarıyla güncellendi!" mesajı çıkar | Onay sormaz. E-postanızı değiştirirseniz bir sonraki girişte yeni e-postayı kullanın. |

> **Dikkat:** E-posta adresinizi değiştirmeden önce yeni adresin size ait ve çalışır olduğundan emin olun. Şifrenizi unutursanız şifre belirleme bağlantısı bu adrese gider.

## Yardım ve RECAi'ye sor

**Bu ne işe yarar?** Bu kılavuzun tamamı RECOrion'un içinde de vardır. Bir ekranda takıldığınızda kılavuzu aramanıza gerek kalmaz: **F1** tuşuna basın veya üst çubuktaki **Yardım** düğmesine tıklayın. Sağdan bir yardım paneli açılır; çalıştığınız ekran kapanmaz.

**Kimler görür?** Giriş yapmış herkes. Panelde yalnız sizin yetkiniz dahilindeki ekranların anlatımı görünür. Merkez Yönetim sayfaları yalnız RECDx yöneticilerine görünür; müşteri kullanıcıları bu sayfaları ve görsellerini göremez, RECAi de onlara bu konularda yanıt vermez.

**Panelin sekmeleri:**

| Sekme | Ne işe yarar |
|---|---|
| **RECAi'ye sor** | Sorunuzu kendi cümlenizle yazarsınız; RECAi kılavuzdan, adım adım yanıt verir. Yanıtın altında dayandığı yardım sayfaları ve gerekiyorsa **Ekrana git** düğmesi çıkar. Aynı konuda ek soru sorabilirsiniz; RECAi önceki soruları hatırlar. |
| **Bu ekran** | Bulunduğunuz ekranın anlatımını açar. Bir pencere açıkken F1'e basarsanız o pencerenin bölümüne gider. **Bu ekranı aç** düğmesi anlatılan ekrana götürür. |
| **İçindekiler** | Görebildiğiniz kılavuzların bölüm ve sayfa listesi. Bir sayfaya tıklayınca açılır; sayfadaki görselleri büyütmek için üzerine tıklayın. |

**Düğmeler:**

| Düğme | Ne yapar | Dikkat |
|---|---|---|
| **Yardım** (üst çubuk) / **F1** | Paneli bulunduğunuz ekranın anlatımıyla açar. | Telefonda panel tam ekran açılır. |
| **Sor** | Sorunuzu RECAi'ye gönderir (Enter da gönderir; Shift+Enter yeni satır). | Yanıt birkaç saniye ile birkaç dakika sürebilir; yoğunlukta RECAi yedek modelle yanıtlar. |
| **Ekrana git** / **Bu ekranı aç** | Yanıtın veya sayfanın anlattığı ekranı açar. | Yalnız yetkiniz olan ekranlara götürür. |
| **Genişlet** / **Daralt** | Paneli genişletir veya daraltır. | — |
| **✕** | Paneli kapatır (Esc de kapatır). | — |

**RECAi ne zaman yanıt vermez?**

- **Yetkiniz dışındaki konular:** Sorduğunuz konu göremediğiniz bir ekranla ilgiliyse RECAi "Bu konu yetkiniz dahilindeki modüllerin dışında kaldığı için cevap veremiyorum" der. O ekranın içeriğini RECAi de görmez; bilgi sızmaz. Gerekirse şirket yöneticinizden yetki isteyin.
- **Kılavuzda olmayan konular:** RECAi uydurmaz; "Kılavuzda bu soruyla ilgili bir bölüm bulamadım" der. Soruyu menü veya ekran adıyla yeniden sorun.
- **RECAi meşgulse:** "RECAi şu anda yanıt veremiyor" uyarısıyla birlikte sorunuzla ilgili yardım sayfaları listelenir; bu sayfalardan okuyabilirsiniz.

> **Örnek:** Ali Kaya **Kayıtlı Şirketler** ekranındayken F1'e basar; panel o ekranın anlatımıyla açılır. **RECAi'ye sor** sekmesine "Bir şirketin paket bitiş tarihini nasıl uzatırım?" yazar. RECAi **Detay & Yönetim** penceresindeki **Paket Kira Bitiş Tarihi** alanını adım adım anlatır ve **Ekrana git** düğmesini gösterir.

> **İpucu:** RECAi yardım soruları kılavuz bilgisiyle yanıtlanır; projelerinizin, fişlerinizin veya kullanıcılarınızın verisini okumaz. "Kaç projem var?" gibi veri soruları için ilgili ekranı açın.

# Menü ağacı

Aşağıdaki tablo Merkez Yönetim'in tam haritasıdır. Tüm menüleri yalnızca RECDx süper yöneticileri görür ve değiştirebilir.

| Menü grubu | Menü (sol menüdeki ad) | Üst çubuktaki ekran adı | Ekrandan açılan pencereler |
|---|---|---|---|
| Genel | **Dashboard (Genel Bakış)** | Sistem Genel Bakış & Dashboard | — |
| Müşteriler | **Başvuru Onay Durum** | Başvuru Onay Durum Masası | Başvuruyu Onayla, Başvuruyu Reddet |
| Müşteriler | **Kayıtlı Şirketler** | Kayıtlı Kurumlar & Şirket Yönetimi | Yeni Müşteri & Şirket Ekle; Şirket Detayları (Detay & Yönetim, iki sekme); <Şirket> · Kredi |
| Katalog | **Sektör Tanımları** | Sektör Tanımları (Ticaret Bakanlığı) | Yeni Sektör Tanımla / Sektörü Düzenle |
| Katalog | **Meslek Tanımları** | Meslek Grubu Tanımları (Ticaret Bakanlığı) | Yeni Meslek Grubu Tanımla / Meslek Tanımını Düzenle |
| Katalog | **Departman & Unvan** | Departman & Unvan Kataloğu | Katalog Departmanı, Katalog Unvanı, Platform Bilgi Dokümanları |
| Katalog | **Proje Şablonları** | Proje Şablonları | Yeni RECDx şablonu / Şablonu düzenle |
| Katalog | **Mevzuat Paketleri** | Mevzuat Paketleri | Taslak kartlar, Yayımla |
| Katalog | **Bağlantı Kataloğu** | Bağlantı Kataloğu | Kart ekle / Kartı düzenle |
| Katalog | **Uygulama Talepleri** | Uygulama Talepleri (RECQmind, RECSlip) | Not penceresi |
| Ticari & Yetki | **Kiralama Paketleri** | Kiralama Paketleri Yönetimi | Yeni Kiralama Paketi Tanımla / Paketi Düzenle |
| Ticari & Yetki | **İzin Kataloğu (RBAC)** | Sistem Yetki Kataloğu (RBAC) | Yeni İzin Tanımla / İzin Tanımını Düzenle |
| Ticari & Yetki | **Yetki Rolleri** | (boş) | Yeni Yetki Rolü Tanımla / Yetki Rolünü Düzenle |
| İletişim & Otomasyon | **E-Posta Şablonları** | Kurumsal E-Posta Şablonları & HTML Editörü | Yeni E-Posta Şablonu Tasarla / Şablonu Düzenle |
| İletişim & Otomasyon | **Zamanlayıcılar (Schedules)** | Otomatik Zamanlayıcılar (Schedules) | Yeni Bildirim Zamanlayıcısı Tanımla / Kuralı Düzenle |
| Yapay Zeka | **Model Yönlendirici** | Model Yönlendirici ve Kalite Testi | — |
| Yapay Zeka | **Genel AI Modelleri** | Genel AI Modelleri & Yapay Zeka Kullanımı | — |
| Yapay Zeka | **Yönetici Asistanı** | Süper Yönetici Asistanı | — |
| Yapay Zeka | **RECAi ve EVREN Modelleri** | RECAi Adları ve EVREN Model Kataloğu | Yeni EVREN Modeli Ekle / EVREN Modelini Düzenle |
| Yapay Zeka | **LLM TL Fiyatları** | LLM TL Fiyatları | <Model> · TL fiyatı |
| Üst çubuk | Profil kartı | — | Süper Admin Profil Bilgileri |

Ayrıca **Kayıtlı Şirketler** ekranından bir şirketin **Şirket Yönetim Paneli**ne ve **Çalışma Alanı**na (Work Space) geçebilirsiniz. Bu iki geçiş Şirket Yönetimi ve Work Space kılavuzlarında anlatılan ekranları açar; KVKK sınırları için bkz. "Şirketin paneline ve çalışma alanına geçiş".


# Genel

## Dashboard (Genel Bakış)

### Süper Yönetim Kontrol Paneli

**Bu ekran ne işe yarar?** Platformun durumunu tek bakışta gösterir: bekleyen başvurular, kayıtlı ve aktif şirketler, tanımlı yapay zeka modelleri, altyapının sağlığı, yapay zeka çağrı sayıları ve şirketlerin kredi kullanımı.

**Ne zaman kullanırım?** Her gün işe başlarken. Bekleyen başvuru var mı, sistemde arıza var mı, hangi şirketin paketi bitiyor; buradan görürsünüz.

**Kimler görür / değiştirebilir?** Yalnızca RECDx süper yöneticileri. Bu ekranda değiştirilecek bir ayar yoktur; yalnızca izlenir.

[[EKRAN: sy-dashboard | Dashboard'un üst yarısı: başlık, durum rozeti, 4 gösterge kartı, bekleyen başvurular ve altyapı paneli | Süper yönetici olarak girin; sol menüde Genel › Dashboard (Genel Bakış)]]

**Ekranın bölümleri (yukarıdan aşağı):**

1. Başlık **Süper Yönetim Kontrol Paneli (Dashboard)**, altında "RECOrion platformunun kurumsal başvuru, şirket, yapay zeka modelleri ve altyapı metrikleri." Sağda **genel durum rozeti**.
2. Dört **gösterge kartı**.
3. Solda **Onay Bekleyen Son Başvurular**, sağda **Altyapı ve entegrasyon durumu**.
4. **Platform kullanımı ve LLM sağlığı** bölümü (grafikler ve tablolar).

**Genel durum rozeti** gerçek ölçüme dayanır ve dakikada bir kendiliğinden yenilenir:

| Rozet | Anlamı | Ne yapmalı |
|---|---|---|
| **Tüm sistemler çalışıyor** (yeşil) | Tüm bileşenler yanıt veriyor | — |
| **Bazı bileşenlerde sorun var** (sarı) | Bir bileşen yavaş ya da erişilemiyor, ama çekirdek çalışıyor | Altyapı panelinde sarı/kırmızı satırı bulun |
| **Çekirdek bileşen erişilemiyor** (kırmızı) | Veritabanı ya da oturum sunucusu yanıt vermiyor; kullanıcılar sistemi kullanamaz | Hemen teknik ekibe haber verin |
| **Durum ölçülüyor…** | İlk ölçüm sürüyor | Birkaç saniye bekleyin |

**Gösterge kartları** (karta tıklayınca ilgili ekran açılır):

| Kart | Gösterdiği sayı | Alt bilgi | Tıklayınca |
|---|---|---|---|
| **Bekleyen Başvurular** — Aktif Edilmemiş Yeni Müşteriler | Onay bekleyen başvuru sayısı ("Başvuru Onay Bekliyor") | — | **Onay Listesine Git**: Başvuru Onay Durum ekranı, onaylanmamışlar süzülü |
| **Kurumsal Portföy** — Kayıtlı Şirketlerin Toplamı | Tüm şirketler ("Kayıtlı Kurum / Şirket") | "N Onaylı • N Onay Bekliyor" | **Şirketler Listesini Aç**: Kayıtlı Şirketler |
| **Onaylanmış Portföy** — Odoo & Sistemde Aktif | Aktif şirketler ("Aktif / Onaylı Müşteri") | "N Web Başvurusu • N Doğrudan Kurumsal" (web başvurusuyla gelen ve sizin doğrudan eklediğiniz aktif şirketler) | **Aktif Portföyü Gör**: Kayıtlı Şirketler |
| **Yapay Zeka Altyapısı** — Tanımlı EVREN Modelleri | Model kataloğundaki model sayısı ("LLM Muhakeme Motoru") | — | **Model Kataloğuna Git**: RECAi ve EVREN Modelleri |

**Onay Bekleyen Son Başvurular** bölümü en fazla 4 başvuruyu (şirket adı, e-posta, paket) gösterir.

| Düğme | Ne yapar | Dikkat |
|---|---|---|
| **Tümünü Gör (N)** | Başvuru Onay Durum ekranını onaylanmamışlar süzülü açar | — |
| **İncele / Onayla** (her başvuruda) | Aynı ekrana götürür | Bu düğme kendisi onaylamaz; onay başvuru ekranında yapılır |

Bekleyen başvuru yoksa "Şu anda onay bekleyen yeni başvuru bulunmuyor. Tüm müşteri talepleri işleme alındı." yazar.

**Altyapı ve entegrasyon durumu** paneli her bileşeni bir satırda gösterir. Alt başlıkta son ölçüm saati yazar ("Ölçüm: 09:42:10").

| Bileşen | Ne işe yarar |
|---|---|
| PostgreSQL (veritabanı) | Tüm kayıtların tutulduğu ana veritabanı (çekirdek) |
| Redis (canlı akış, oturum güvenliği) | Canlı ekran güncellemeleri ve oturum güvenliği (çekirdek) |
| Qdrant (hafıza vektörleri) | Kurum hafızasında anlam bazlı arama |
| MinIO (belge ve çıktı deposu) | Dosya ve çıktı deposu |
| Temporal (iş akışı motoru) | Projelerdeki iş adımlarını sırayla yürüten motor |
| Gitea (proje kod depoları) | Yazılım projelerinin kod depoları |
| EVREN LLM Gateway | Yapay zeka model altyapısı |
| Odoo ERP | RECDx'in satış sistemi |

Her satırda gecikme süresi (ms ya da sn) ve durum rozeti vardır: **● Çalışıyor**, **▲ Yavaş**, **✕ Erişilemiyor**, **○ Kapalı** (bu ortamda kullanılmıyor). Satırın altındaki küçük yazı ayrıntıyı verir (ör. erişilememe nedeni).

| Düğme | Ne yapar | Dikkat |
|---|---|---|
| **↻** (üzerine gelince "Yeniden ölç") | Tüm bileşenleri hemen yeniden ölçer | Onay sormaz |

[[EKRAN: sy-dashboard-kullanim | Dashboard'un alt yarısı: Platform kullanımı ve LLM sağlığı (sayı kutuları, grafikler, model sağlığı tablosu, şirket başına kredi) | Dashboard'da sayfayı aşağı kaydırın]]

**Platform kullanımı ve LLM sağlığı** bölümü yalnızca sayıları gösterir; başlığın yanında "Yalnızca sayılar; müşteri içeriği gösterilmez (KVKK)" yazar.

| Öğe | Anlamı |
|---|---|
| **7 gün / 30 gün / 90 gün** | Grafiklerin ve sayıların dönemini seçer (varsayılan 7 gün) |
| **LLM çağrısı** | Dönemde yapılan yapay zeka çağrısı sayısı |
| **Hata oranı** | Başarısız çağrıların oranı; %10'un üstündeyse kırmızı görünür. Altında başarısız çağrı sayısı yazar |
| **EVREN bakiyesi** | RECDx'in EVREN'de kalan kredisi (CR) |
| **Süresi 30 günde dolan paket** | Paketi 30 gün içinde bitecek şirket sayısı |
| **Günlük LLM çağrısı** | Günlere göre çağrı grafiği |
| **Günlük başarısız çağrı** | Günlere göre hata grafiği ("Zaman aşımı, model dolu (503), bağlantı hatası") |
| **Model sağlığı** tablosu | Her model için **Çağrı**, **Hata**, **Gecikme p50** (çağrıların yarısının bu sürede bittiği süre), **Gecikme p95** (yavaş çağrıların süresi), **Çıktı hızı** (token/sn), **Çıktı token**. "EVREN kapasite (GPU) talebi için girdi." |
| **Şirket başına kredi kullanımı** | En çok kredi harcayan ilk 10 şirket; her satırda paket adı (yoksa "Paketsiz") ve çağrı sayısı |
| **Aktif şirketlerin paket dağılımı** | Hangi paketten kaç aktif şirket olduğu; alt başlıkta "N aktif · N pasif · dönemde N yeni" |

> **Örnek:** Sabah Dashboard'u açtınız. **Bekleyen Başvurular** kartında "1" yazıyor ve **Onay Bekleyen Son Başvurular** listesinde "Örnek Lojistik A.Ş." görünüyor. **İncele / Onayla** düğmesine tıklayın; Başvuru Onay Durum ekranında başvuruyu inceleyip onaylarsınız (bkz. sonraki bölüm).

> **İpucu:** **Süresi 30 günde dolan paket** sayısı sıfırdan büyükse Kayıtlı Şirketler'de kırmızı kenarlı kartlara bakın ve gerekirse **Hatırlatıcı Mail** gönderin.

**Sık sorulan sorular**

- *Dashboard'da bir şirketin hangi projeleri yürüttüğünü görebilir miyim?* Hayır. KVKK gereği yalnızca sayılar görünür.
- *Bir bileşen "○ Kapalı" görünüyor, sorun mu?* Hayır. O bileşen bu kurulumda kullanılmıyor demektir. "✕ Erişilemiyor" ise sorundur.
- *Sayılar güncel mi?* Durum rozeti dakikada bir yenilenir. Kartlardaki sayılar için üst çubuktaki **↻ Verileri Yenile** düğmesine basın.

# Müşteriler

## Başvuru Onay Durum

### Başvuru Onay Durum Masası

**Bu ekran ne işe yarar?** Müşteri başvurularını onayladığınız ya da reddettiğiniz yerdir. İki tür başvuru buraya düşer:

- Resmi sitede paket satın alma formunu dolduran şirketler.
- Sizin **Kayıtlı Şirketler › + Yeni Müşteri Ekle** ile açtığınız şirketler.

Onay, şirketi 1 yıllık paketle aktifleştirir, Odoo'daki satış siparişini onaylar ve şirket yöneticisine aktivasyon e-postası gönderir (e-postada şifre yoktur; yönetici bağlantıdan şifresini belirler ya da başvuruda belirlediği şifreyle girer).

**Ne zaman kullanırım?** Sol menüde **Başvuru Onay Durum** yanında turuncu sayı gördüğünüzde, ödemesi ya da sözleşmesi tamamlanan müşteriyi açmak için.

**Kimler görür / değiştirebilir?** Yalnızca RECDx süper yöneticileri.

[[EKRAN: sy-basvurular | Başvuru Onay Durum Masası, Liste görünümü, "Başvurusu Onaylanmamışlar" seçili | Sol menüde Müşteriler › Başvuru Onay Durum]]

**Ekranın bölümleri:**

1. Başlık **Başvuru Onay Durum Masası**, altında "Resmi siteden paket kiralayan müşterilerin Odoo 19 siparişleri ve onay süreçleri."
2. Durum düğmeleri: **Başvurusu Onaylanmamışlar (N)**, **Başvurusu Onaylanmışlar (N)**, **Reddedilenler (N)**.
3. **Kanban / Liste** seçici (varsayılan Liste) ve arama kutusu.
4. Başvuru listesi.

| Alan | Ne işe yarar | Nasıl doldurulur / seçenekler | Örnek | Zorunlu |
|---|---|---|---|---|
| **Şirket veya e-posta ara...** | Listeyi süzer | Şirket adı, e-posta, telefon ya da paket kodundan bir parça yazın (Kanban'da yalnız şirket adı ve e-posta) | orneklojistik | Hayır |

**Liste görünümünün sütunları:** **Şirket Ünvanı & Yetkili** (şirket adı ve yetkili e-postası) · **İletişim** (telefon) · **Seçilen Paket** · **Odoo Sipariş No** · **Durum** · **Aksiyon**.

**Kanban görünümü** iki sütundur: **Onay Bekleyen Başvurular** ve **Onaylanan ve Aktif Başvurular**. Reddedilenler Kanban'da gösterilmez; **Reddedilenler** düğmesine basınca görünüm kendiliğinden Liste'ye geçer.

**Durum rozetleri:**

| Rozet | Anlamı |
|---|---|
| **⏳ Onay Bekliyor** | Başvuru sizin kararınızı bekliyor; şirket henüz pasif |
| **✓ Onaylandı & Aktif** (Kanban'da **✓ Aktif**) | Onaylandı; şirket aktif. Aksiyon sütununda **Aktivasyon Tamamlandı** yazar |
| **✕ Reddedildi** | Reddedildi; fareyle üzerine gelince ret gerekçesi görünür, Aksiyon sütununda gerekçe yazar |

**Odoo sütunu:**

| Görünen | Anlamı | Ne yapmalı |
|---|---|---|
| Sipariş numarası (altında "Odoo: <müşteri adı>") | Odoo'da müşteri ve satış siparişi açıldı | — |
| **Odoo: işleniyor…** | Odoo'ya aktarım arka planda sürüyor | Biraz sonra **↻ Verileri Yenile** |
| **Odoo: kapalı** | Bu başvuru Odoo'ya gönderilmedi (Odoo bağlantısı kapalı ya da paket seçilmemiş) | Gerekirse siparişi Odoo'da elle açın |
| **⚠ Yeniden dene** | Odoo aktarımı başarısız oldu; üzerine gelince hata metni görünür | Düğmeye tıklayın |

**Düğmeler:**

| Düğme | Ne yapar | Dikkat (onay ister mi, geri alınır mı) |
|---|---|---|
| **Onayla & Aktif Et** | **Başvuruyu Onayla** penceresini açar: "'<şirket>' şirketi 1 yıllık paketle aktifleştirilecek, Odoo siparişi onaylanacak ve <e-posta> adresine aktivasyon e-postası gönderilecek. Devam edilsin mi?" **Onayla ve Aktif Et** ile onaylarsınız | Onay ister. Geri alınmaz; gerekirse şirketi Kayıtlı Şirketler'den pasife alırsınız |
| **Reddet** | **Başvuruyu Reddet** penceresini açar; yazdığınız gerekçe müşteriye e-postayla gider, Odoo teklifi iptal edilir | Gerekçe en az 5 karakter olmalı. Geri alınmaz |
| **⚠ Yeniden dene** | Başarısız Odoo aktarımını tekrar dener; sonuç "Odoo senkronizasyonu tamamlandı: <sipariş no>." ya da hata metni | Onay sormaz |

#### Başvuruyu Reddet penceresi

[[EKRAN: sy-m-basvuru-reddet | "Başvuruyu Reddet" penceresi, gerekçe kutusu dolu | Başvuru Onay Durum › Başvurusu Onaylanmamışlar › bir test başvurusunda Reddet (göndermeden Vazgeç ile kapatın)]]

| Alan | Ne işe yarar | Nasıl doldurulur / seçenekler | Örnek | Zorunlu |
|---|---|---|---|---|
| Gerekçe kutusu | Müşteriye gidecek ret e-postasındaki açıklama | Kibar ve anlaşılır bir cümle yazın; en az 5 karakter | Vergi numaranız doğrulanamadı; lütfen bizimle iletişime geçin. | Evet |

| Düğme | Ne yapar | Dikkat |
|---|---|---|
| **Reddet** | Başvuruyu reddeder; mesajda e-postanın gidip gitmediği yazar ("Müşteriye e-posta gönderildi." / "E-posta gönderilemedi.") | Geri alınmaz |
| **Vazgeç** | Hiçbir şey yapmadan kapatır | — |

**Hata ve uyarı mesajları:**

| Mesaj | Anlamı | Ne yapmalı |
|---|---|---|
| "Lütfen müşteriye iletilecek en az 5 karakterlik bir gerekçe yazın." | Gerekçe çok kısa | Daha açıklayıcı yazın |
| "Bu başvuru zaten onaylanmış." | Başka biri sizden önce onayladı | **↻ Verileri Yenile** |
| "Onaylanmış bir başvuru reddedilemez; şirketi pasife alabilirsiniz." | Onaylı başvuru geri çevrilmez | Kayıtlı Şirketler › **Pasife Al** |
| "Başvuruya bağlı şirket kaydı bulunamadı; şirketi 'Yeni Müşteri Ekle' ile oluşturun." / "Başvuruya bağlı şirket kaydı silinmiş." | Başvurunun şirketi yok | Şirketi Kayıtlı Şirketler'den yeniden ekleyin |
| "… Aktivasyon e-postası gönderilemedi; şirket kartından tekrar gönderebilirsiniz." (sarı) | Şirket aktif oldu ama e-posta gitmedi | Kayıtlı Şirketler › **Hoş Geldin Maili** |

> **Dikkat:** **Zamanlayıcılar** ekranındaki "Müşteri Kayıt Olduğunda (Tek Sefer)" kuralı pasife alınmışsa onaydan sonra aktivasyon e-postası gönderilmez. Müşteri e-posta almadığını söylerse önce bu kuralın aktif olduğunu kontrol edin.

**Adım adım örnek: Örnek Lojistik A.Ş. başvurusunu onaylamak**

1. Sol menüde **Başvuru Onay Durum**'a tıklayın. **Başvurusu Onaylanmamışlar** seçili gelir.
2. Arama kutusuna "orneklojistik" yazın. Satırda **⏳ Onay Bekliyor** ve Odoo sütununda sipariş numarasını görün.
3. Ödemenin alındığını muhasebeden teyit edin.
4. **Onayla & Aktif Et**'e tıklayın, açılan pencerede **Onayla ve Aktif Et**'i seçin.
5. "'Örnek Lojistik A.Ş.' şirketi aktifleştirildi. Aktivasyon e-postası gönderildi." mesajını görün. Başvuru **Başvurusu Onaylanmışlar** listesine geçer.
6. Ayşe Yılmaz e-postadaki bağlantıyla şifresini belirler ve Şirket Yönetimi'ne girer.

**Adım adım örnek: başvuruyu reddetmek**

1. Satırda **Reddet**'e tıklayın.
2. Gerekçeyi yazın (ör. "Vergi numaranız doğrulanamadı; lütfen bizimle iletişime geçin.") ve **Reddet**'e tıklayın.
3. Başvuru **Reddedilenler (N)** listesine geçer.

**Sık sorulan sorular**

- *Onaylamadan önce başvurunun ayrıntılarını nereden görürüm?* Başvurunun şirket kartı Kayıtlı Şirketler'de **PASİF** olarak durur; **Detay & Yönetim** ile şirket bilgilerini açabilirsiniz.
- *Reddettiğim başvuruyu geri alabilir miyim?* Hayır. Müşteri yeniden başvurmalı ya da siz **Yeni Müşteri Ekle** ile şirketi açmalısınız.
- *Onay, paketi ne zamana kadar açar?* Onay gününden itibaren 1 yıl (365 gün). Şirketin ileri tarihli geçerli bir bitiş tarihi zaten varsa o tarih korunur.
- *"Reddedilenler" listesi boşken neden "Henüz onaylanmış müşteri başvurusu bulunmuyor." yazıyor?* Bu ekranda boş liste için aynı metin kullanılır; reddedilmiş başvuru olmadığı anlamına gelir.

## Kayıtlı Şirketler

### Kayıtlı Kurumlar ve Şirketler

**Bu ekran ne işe yarar?** RECOrion'daki tüm müşteri şirketlerini yönettiğiniz ana ekrandır. Buradan:

- yeni müşteri şirketi eklersiniz,
- şirket kartını, logosunu ve şirket yöneticisini düzenlersiniz,
- şirketi pasife alır ya da tekrar aktif edersiniz,
- ek kredi yüklersiniz,
- aktivasyon (hoş geldin) ve paket süresi hatırlatma e-postası gönderirsiniz,
- boş bir şirketi silersiniz,
- şirketin Şirket Yönetim Paneli'ne ya da Çalışma Alanı'na geçersiniz.

**Ne zaman kullanırım?** Müşteri bilgisi değiştiğinde, müşteri şifresini unuttuğunda, ek kredi satıldığında, paket yenilendiğinde, sözleşmesi biten müşteriyi durdurmanız gerektiğinde.

**Kimler görür / değiştirebilir?** Yalnızca RECDx süper yöneticileri.

[[EKRAN: sy-kayitli-sirketler | Kayıtlı Şirketler, Kanban görünümü: logolu şirket kartları, AKTİF/PASİF rozetleri, bir kartta 3 ay uyarısı | Sol menüde Müşteriler › Kayıtlı Şirketler]]

**Ekranın bölümleri:**

1. Başlık **Kayıtlı Kurumlar ve Şirketler (Tenants)**, altında "Kayıtlı kurumlar, paket süreleri, 3 ay bitim alarmları, yönetici hesapları ve sözleşme durumları."
2. **+ Yeni Müşteri Ekle** düğmesi.
3. Durum süzgeci: **Tümü (N)**, **Aktif (N)**, **Pasif / Bekleyen (N)**.
4. **Kanban / Liste** seçici (varsayılan Kanban) ve arama kutusu.
5. Şirket kartları ya da tablo.

| Alan | Ne işe yarar | Nasıl doldurulur / seçenekler | Örnek | Zorunlu |
|---|---|---|---|---|
| **Şirket adı veya VKN ara...** | Listeyi süzer | Şirket adı, e-posta, sistem kimliği ya da vergi numarasından bir parça | Örnek Lojistik | Hayır |
| Durum süzgeci | Hangi şirketlerin görüneceğini seçer | **Tümü**, **Aktif** (girişleri açık), **Pasif / Bekleyen** (pasife alınmış ya da onay bekleyen) | Aktif | — |

**Şirket kartı (Kanban)** yukarıdan aşağı şunları gösterir:

| Kart öğesi | Anlamı |
|---|---|
| Logo | Şirketin yüklediği ya da sizin yüklediğiniz logo. Logo yoksa şirket adının ilk iki harfi görünür |
| **AKTİF** / **PASİF** rozeti | Şirketin kullanıcıları giriş yapabiliyor mu |
| Şirket adı | Resmi ünvan |
| **🔑 Sistem Kimliği / URL:** | Şirketin sistemdeki tekil kısa adı |
| Sektör etiketleri | Şirketin faaliyet sektörleri (simgeleriyle) |
| **Paket:** | Şirketin paketi (yoksa "Standart Kiralama") |
| **Kira Bitiş:** | Paket bitiş tarihi; şirket pasifse "Onay Bekliyor / Pasif" |
| **⚠️ Paket Bitimine 3 Aydan Az Kaldı! (Kalan: N gün)** | Paketin bitmesine 90 gün ya da daha az kaldı; kartın kenarı kırmızılaşır |
| **⏸️ Şirket Kartı Pasif Durumda (Girişler Kapalı)** | Şirket pasif; kullanıcıları giremez |
| E-posta, telefon, **VKN: … (… V.D.)** | İletişim ve vergi bilgileri ("E-posta yok", "Telefon yok" boş olduğunu gösterir) |
| Kartın altındaki düğmeler | Aşağıdaki tabloya bakın |

[[EKRAN: sy-kayitli-sirketler-liste | Kayıtlı Şirketler, Liste görünümü: logolu firma adı, 3 Ay Uyarısı sütunu, İşlemler simgeleri | Kayıtlı Şirketler ekranında Liste düğmesine tıklayın]]

**Liste görünümünün sütunları:** **Durum** (Aktif/Pasif) · **Firma Adı & Kimlik** (küçük logo, ad, "URL: <sistem kimliği>", sektör etiketleri) · **Vergi No / Dairesi** · **Telefon** · **Web Adres** (tıklanabilir) · **Yönetici Adı** · **Email** · **Aldığı Paket** · **Kira Bitiş Tarihi** · **3 Ay Uyarısı** · **İşlemler**.

**3 Ay Uyarısı** sütunu: **3 Ay Kaldı (Ng)** (kırmızı; satır da kırmızımsı olur), **Normal (Ng)**, **Pasif Durumda**. Arama sonucu yoksa "Aramaya uygun şirket kaydı bulunamadı." yazar.

**Her şirket için düğmeler** (Kanban'da yazılı, Liste'de simge; fareyle üzerine gelince adı çıkar):

| Düğme | Ne yapar | Dikkat (onay ister mi, geri alınır mı) |
|---|---|---|
| **Kredi** | **<Şirket> · Kredi** penceresini açar (kredi durumu ve ek kredi yükleme) | — |
| **Pasife Al** (Liste'de **Pasif**) | Şirket kartını pasife alır: şirket yöneticisi ve tüm kullanıcılar giriş yapamaz | Onay ister: "…PASİFE almak istediğinize emin misiniz? Pasife alındığında şirket yöneticisi ve kullanıcıları sisteme giriş yapamayacaktır." **Aktife Al** ile geri alınır |
| **Aktife Al** (Liste'de **Aktif**) | Pasif şirketin girişlerini yeniden açar | Onay ister. Paket süresini başlatmaz, Odoo siparişini onaylamaz, e-posta göndermez |
| **Sil** | Şirketi kalıcı olarak siler | Onay ister: "…kalıcı olarak SİLMEK istediğinize emin misiniz? ⚠️ Dikkat: Bu işlem geri alınamaz!" Şirkette departman, AI personel ya da proje varsa silinmez. **Geri alınamaz** |
| **🛡️ Ana Şirket** | RECDx ana şirketinde **Sil** yerine görünür; ana şirket silinemez | — |
| **Detay & Yönetim** (Liste'de **Detay**) | Şirket detay penceresini açar (kurumsal bilgiler, logo, paket, sektörler, manifesto, şirket yöneticisi) | — |
| **Hoş Geldin Maili** | Şirket yöneticisine aktivasyon e-postasını yeniden gönderir; e-postada şifre yoktur, 72 saat geçerli bir şifre belirleme bağlantısı vardır | **Onay sormaz**. Giden e-posta geri alınmaz |
| **Hatırlatıcı Mail** (yalnız aktif şirkette) | Paket süresi dolum hatırlatma e-postasını hemen gönderir | Onay ister. Giden e-posta geri alınmaz |
| Bina simgesi ("Şirket Yönetim Paneline Geç (Departmanlar, Ünvanlar, AI Ajanlar)") | O şirketin Şirket Yönetimi ekranına geçer | KVKK sınırları geçerlidir (aşağıya bakın) |
| Sağ ok simgesi ("Şirket Çalışma Alanına Geç") | O şirketin Work Space ekranına **KVKK Koruma Modu**nda geçer | İçerik görünmez |

**Hata mesajları:**

| Mesaj | Anlamı | Ne yapmalı |
|---|---|---|
| "⚠️ Şirket Silinemedi! Sebep: '<şirket>' şirketine ait N adet tanımlı departman bulunmaktadır. Şirket silinmeden önce tüm departmanlar silinmelidir." | Şirket kullanılmış | Silmek yerine **Pasife Al** kullanın |
| "…N adet tanımlı Yapay Zeka Ajanı bulunmaktadır…" / "…N adet proje bulunmaktadır…" | Aynı | Aynı |
| "⚠️ RECDx Teknoloji & Dijital Dönüşüm Danışmanlığı LTD. Şirketi sistemin ana şirketidir ve SİLİNEMEZ!" | Ana şirket korunur | — |
| "⚠️ E-Posta Gönderilemedi! … Aktivasyon e-postası gönderilemedi. E-posta ayarlarını ve ACCOUNT_ACTIVATED şablonunu kontrol ediniz." | E-posta sunucusu ya da şablon sorunu | E-Posta Şablonları'nda şablonun aktif olduğunu kontrol edin; sorun sürerse teknik ekibe bildirin |
| "…Hatırlatıcı e-postası gönderilemedi. E-posta ayarlarını ve PACKAGE_EXPIRATION_REMINDER şablonunu kontrol ediniz." | Aynı, hatırlatma şablonu için | Aynı |
| "Şirket yöneticisinin geçerli bir e-posta adresi bulunamadı." | Şirketin yöneticisi ya da e-postası yok | **Detay & Yönetim › 2. Şirket Yöneticisi Tanımlaması** ile yönetici tanımlayın |

> **Dikkat:** **Sil** yalnızca hiç kullanılmamış (departmanı, AI personeli ve projesi olmayan) şirketleri siler; silinen şirketle birlikte yöneticisi, başvuru kaydı, unvan ve rol kayıtları da silinir. Sözleşmesi biten bir müşteriyi silmeyin, **Pasife Al** kullanın.

#### Yeni Müşteri & Şirket Ekle

**Bu pencere ne işe yarar?** Resmi siteden başvurmayan bir müşteriyi (ör. doğrudan satışla gelen) sizin açmanızı sağlar. Tek adımda şirket kartı, şirket yöneticisi kullanıcısı ve bir başvuru kaydı oluşur; paket seçildiyse Odoo'da müşteri ve satış teklifi arka planda açılır.

**Nasıl açılır?** Kayıtlı Şirketler › **+ Yeni Müşteri Ekle**. Başlık: **Yeni Müşteri & Şirket Ekle (Süper Admin Kaydı)**.

[[EKRAN: sy-m-yeni-musteri | Yeni Müşteri & Şirket Ekle penceresi: kurumsal bilgiler, logo alanı, paket ve yönetici, sektör seçimi | Kayıtlı Şirketler › + Yeni Müşteri Ekle; örnek bilgilerle doldurun (kaydetmeyin)]]

| Alan | Ne işe yarar | Nasıl doldurulur / seçenekler | Örnek | Zorunlu |
|---|---|---|---|---|
| **Şirket Ünvanı \*** | Şirketin resmi adı; sistem kimliği bundan üretilir | Ticaret sicilindeki tam ünvan | Örnek Lojistik A.Ş. | Evet |
| **Vergi No (VKN) \*** | Şirketin vergi numarası; Odoo'da müşteri eşleştirmesi bununla yapılır | 10 haneli VKN (şahıs şirketinde 11 haneli TC kimlik no). Kontrol hanesi doğrulanır; aynı numara başka şirkette kayıtlı olamaz | 1234567890 | Evet |
| **Vergi Dairesi** | Vergi dairesi | Daire adı | Kadıköy V.D. | Hayır |
| **Kurumsal / Official E-posta \*** | Şirket yöneticisinin giriş e-postası ve şirketin iletişim e-postası | Şirketin kendi alan adıyla bir e-posta. Gmail, Hotmail, Outlook, Yahoo, Yandex, iCloud, Proton, Zoho, GMX, AOL gibi ücretsiz adresler kabul edilmez. Bu e-posta başka bir şirkette kullanıcı olarak kayıtlı olamaz | ayse.yilmaz@orneklojistik.com.tr | Evet |
| **Telefon** | Şirket telefonu | — | +90 216 XXX XX XX | Hayır |
| **Web Sitesi** | Şirketin web adresi; manifesto yazılırken de kullanılır | https ile | https://orneklojistik.com.tr | Hayır |
| **Şirket Logosu (isteğe bağlı)** | Şirketin logosu; Kayıtlı Şirketler'de, Şirket Yönetimi'nin sol üstünde ve Work Space üst çubuğunda görünür | **Logo seç** ile dosya seçin; önizleme çıkar, **Kaldır** ile vazgeçersiniz. PNG, JPG ya da WEBP, en fazla 2 MB; SVG kabul edilmez. Kare ya da yatay, saydam arka planlı PNG önerilir. Sistem logoyu en uzun kenarı 512 piksel olacak şekilde küçültür | ornek-lojistik-logo.png | Hayır |
| **Kiralama Paketi (1 Yıl Başlatılır)** | Şirketin paketi | Listeden seçin ("<Paket adı> (<fiyat> TRY/ay)"). İlk paket önceden seçili gelir | Kurumsal Paket (25.000 TRY/ay) | Hayır |
| **Yönetici Adı Soyadı** | Şirket yöneticisi kullanıcısının adı | Boş bırakılırsa "<Şirket adı> Yöneticisi" olur | Ayşe Yılmaz | Hayır |
| **Yönetici Şifresi (Opsiyonel)** | Yöneticinin ilk şifresi | En az 8 karakter. Boş bırakırsanız yönetici şifresini aktivasyon e-postasındaki bağlantıdan kendisi belirler (önerilen) | — | Hayır |
| **Faaliyet Sektörleri (T.C. Ticaret Bakanlığı) \*** | Şirketin faaliyet alanları; AI personel önerileri ve manifesto buna göre şekillenir | "+ Açılır Listeden Sektör Seçiniz..." kutusundan ya da altındaki sektör düğmelerinden (+ / ✓) seçin. Seçilenler etiket olarak görünür; etiketteki **×** ile tek tek, **Temizle ✕** ile hepsini kaldırırsınız | [J] ULAŞTIRMA HİZMETLERİ | Ekranda yıldızlı; en az bir sektör seçin |
| **Meslek Grupları (Seçili Sektörlere Göre Filtrelenir)** | Şirketin daha ayrıntılı faaliyet grupları | Önce sektör seçin; "+ Seçili Sektörlere Bağlı Meslek Grubu Ekle (N meslek mevcut)..." kutusundan seçin. Sektörü kaldırırsanız o sektörün meslekleri de kalkar | [J.05] Kara yolu ile yük taşımacılığı | Hayır |
| **RECOrion Ana LLM Tarafından Otomatik Yazılan Şirket Manifestosu** | Şirketin faaliyet alanını ve yapay zekadan beklentisini anlatan metin | **✨ RECAi ile Manifesto Üret** ile yazdırın, sonra dilediğiniz gibi düzeltin. Boş bırakırsanız sistem kayıtta kendisi üretir | — | Hayır |
| **Adres** | Resmi adres | — | Şirket resmi adresi | Hayır |

| Düğme | Ne yapar | Dikkat |
|---|---|---|
| **✨ RECAi ile Manifesto Üret** | Şirket adı, sektörler, meslekler ve web sitesine göre manifesto yazar; çalışırken **LLM Yazıyor...** | Önce şirket adını yazın ("Lütfen önce şirket adını giriniz.") |
| **Vazgeç** / **✕** | Kaydetmeden kapatır | Girilen bilgiler kaybolur |
| **Müşteriyi ve Yöneticiyi Kaydet** | Şirketi, yöneticiyi ve başvuruyu oluşturur; "✓ '<şirket>' kurumu ve yetkili yöneticisi (<ad> - <e-posta>) başarıyla sisteme kaydedildi." | Onay sormaz. Şirket **PASİF** olarak oluşur |

> **Dikkat:** Pencerenin alt başlığında "…1 yıllık kira paketi tanımlanır ve Hoş Geldiniz e-postası otomatik iletilir." yazsa da kayıt sırasında **paket başlatılmaz ve e-posta gönderilmez**. Şirket PASİF olarak açılır, başvurusu **Başvuru Onay Durum** ekranına **⏳ Onay Bekliyor** olarak düşer. Paket ve aktivasyon e-postası, başvuruyu orada onayladığınızda başlar.

**Hata mesajları:**

| Mesaj | Anlamı | Ne yapmalı |
|---|---|---|
| "Lütfen şirket adı ve e-posta adresini doldurunuz." | Zorunlu alan boş | Doldurun |
| "⚠️ Kurumsal / Official E-Posta Zorunluluğu! …" | Ücretsiz e-posta sağlayıcısı yazıldı | Şirket alan adlı e-posta isteyin |
| "Vergi numarası 10 haneli VKN veya 11 haneli TCKN olmalıdır." | Hane sayısı yanlış | Numarayı kontrol edin |
| "Lütfen gerçek vergi numaranızı girin (ardışık veya tekrar eden rakamlar kabul edilmez)." | 1111111111 gibi deneme numarası | Gerçek numara girin |
| "Vergi numarası geçersiz (kontrol hanesi tutmuyor). Lütfen numarayı kontrol edin." | Numara hatalı yazılmış | Müşteriden teyit edin |
| "'<VKN>' Vergi Numarası ve '<daire>' Vergi Dairesi ile kayıtlı bir şirket ('<şirket>') zaten mevcuttur. Mükerrer kayıt oluşturulamaz." | Şirket zaten kayıtlı | Arama kutusuyla mevcut şirketi bulun |
| "'<e-posta>' e-posta adresi ile kayıtlı bir kullanıcı … zaten mevcuttur. Lütfen farklı bir yönetici e-posta adresi giriniz." | E-posta başka bir hesapta | Farklı bir şirket e-postası kullanın |
| "Yönetici şifresi en az 8 karakter olmalıdır." | Şifre kısa | Şifreyi uzatın ya da boş bırakın |
| "Logo PNG, JPG veya WEBP olmalı (SVG kabul edilmez)." / "Logo en fazla 2 MB olabilir." | Logo dosyası uygun değil | Dosyayı dönüştürün ya da küçültün |

**Adım adım örnek: Örnek Lojistik A.Ş.'yi doğrudan eklemek**

1. Kayıtlı Şirketler › **+ Yeni Müşteri Ekle**.
2. **Şirket Ünvanı**: "Örnek Lojistik A.Ş.", **Vergi No**: müşterinin VKN'si, **Vergi Dairesi**: "Kadıköy V.D.".
3. **Kurumsal / Official E-posta**: "ayse.yilmaz@orneklojistik.com.tr", **Web Sitesi**: "https://orneklojistik.com.tr".
4. **Logo seç** ile müşterinin gönderdiği PNG logoyu seçin.
5. **Kiralama Paketi**'nden satılan paketi seçin; **Yönetici Adı Soyadı**: "Ayşe Yılmaz"; şifreyi boş bırakın.
6. Sektör listesinden "[J] ULAŞTIRMA HİZMETLERİ"ni, meslek listesinden "[J.05] Kara yolu ile yük taşımacılığı" ve "[J.16] Yük taşımacılığını destekleyici faaliyetler"i seçin.
7. **✨ RECAi ile Manifesto Üret**'e tıklayın; metni okuyup gerekiyorsa düzeltin.
8. **Müşteriyi ve Yöneticiyi Kaydet**. Şirket listede **PASİF** görünür.
9. **Başvuru Onay Durum**'a gidin, Örnek Lojistik başvurusunda **Onayla & Aktif Et**. Ayşe Yılmaz'a aktivasyon e-postası gider.

#### Şirket Detayları (Detay & Yönetim)

**Bu pencere ne işe yarar?** Şirketin tüm kart bilgilerini, logosunu, paketini, sektörlerini, manifestosunu ve şirket yöneticisinin kullanıcı bilgilerini düzenlersiniz.

**Nasıl açılır?** Şirket kartında **Detay & Yönetim** (Liste'de **Detay**). Pencere başlığı şirketin adıdır; alt başlık "Şirket bilgileri, onaylama ve Şirket Admin kullanıcısı."

Pencerenin üstünde iki sekme vardır: **1. Kurumsal Bilgiler & Paket** ve **2. Şirket Yöneticisi Tanımlaması**.

[[EKRAN: sy-m-sirket-detay-kurumsal | Şirket Detayları penceresi, "1. Kurumsal Bilgiler & Paket" sekmesi: durum şeridi, kurumsal alanlar, Şirket Logosu, paket ve bitiş tarihi | Kayıtlı Şirketler › RECOrion Canlı Test A.Ş. kartında Detay & Yönetim]]

**Sekme 1 — Kurumsal Bilgiler & Paket**

Sekmenin üstünde "1. Kurumsal Bilgiler & Durum:" başlığı, **AKTİF** / **PASİF** rozeti ve "Sistem Kimliği: <kimlik>" yazar. Sağda **Şirketi Sil** düğmesi (ana şirkette **🛡️ Ana Şirket (Silinemez)**) bulunur. Altındaki şerit "Şirket Kartı Durumu: AKTİF/PASİF (Aktif / Pasif yapma işlemi yalnızca Kayıtlı Müşteri Listesinden yapılabilir)" ve **✓ Sistem Girişleri Açık** / **⏸️ Girişler Kapalı** bilgisini verir.

| Alan | Ne işe yarar | Nasıl doldurulur / seçenekler | Örnek | Zorunlu |
|---|---|---|---|---|
| **Şirket Ünvanı** | Resmi ad | — | Örnek Lojistik A.Ş. | Evet |
| **Vergi No (VKN)** | Vergi numarası | 10 ya da 11 hane; yeni müşteri penceresindeki kurallar geçerlidir | 1234567890 | Hayır |
| **Vergi Dairesi (V.D.)** | Vergi dairesi | — | Kadıköy V.D. | Hayır |
| **Telefon** | Şirket telefonu | — | +90 216 XXX XX XX | Hayır |
| **İletişim E-posta** | Şirketin iletişim e-postası (hatırlatma e-postaları buraya gider) | — | info@orneklojistik.com.tr | Hayır |
| **Web Sitesi** | Web adresi | — | https://orneklojistik.com.tr | Hayır |
| **Şirket Logosu** | Şirketin resmi logosu | **Logo seç** / **Logoyu değiştir** ile dosya seçtiğiniz anda logo **hemen kaydedilir** ("Şirket logosu kaydedildi."). **Kaldır** onay sorar ("<şirket> logosu kaldırılsın mı?"). PNG, JPG, WEBP; en fazla 2 MB; SVG yok; 512 piksele küçültülür | — | Hayır |
| **Tanımlı Paket** | Şirketin paketi | "Paket Seçiniz..." listesinden | Kurumsal Paket (25.000 TRY/ay) | Hayır |
| **Paket Kira Bitiş Tarihi** | Paketin bitiş günü; 3 ay uyarısı ve hatırlatmalar bu tarihe göre hesaplanır | Takvimden seçin. Paket yenilendiğinde yeni bitiş tarihini buraya yazın | 31.10.2027 | Hayır |
| **Faaliyet Sektörleri (T.C. Ticaret Bakanlığı)** | Faaliyet alanları | Yeni müşteri penceresindeki gibi | — | Hayır |
| **Meslek Grupları (Seçili Sektörlere Göre Filtrelenir)** | Meslek grupları | Yeni müşteri penceresindeki gibi | — | Hayır |
| **RECOrion Ana LLM Tarafından Üretilen Kurumsal Manifesto** | Şirket manifestosu | Elle düzeltebilir ya da yeniden yazdırabilirsiniz | — | Hayır |
| **Adres** | Resmi adres | — | — | Hayır |

| Düğme | Ne yapar | Dikkat |
|---|---|---|
| **Şirketi Sil** | Şirketi kalıcı siler (Kayıtlı Şirketler'deki **Sil** ile aynı kurallar) | Onay ister; geri alınamaz |
| **Hoş Geldin Maili Gönder** | Aktivasyon e-postasını (şifre belirleme bağlantısıyla) yeniden gönderir | Onay sormaz |
| **Hatırlatıcı Mail Gönder** | Paket süresi hatırlatmasını gönderir | Onay ister |
| **✨ AI ile Manifestoyu Yaz / Yenile** | RECAi manifestoyu yeniden yazar; çalışırken **LLM Yazıyor...** | Mevcut metnin yerine geçer; **Şirket Bilgilerini Kaydet** demezseniz kalıcı olmaz |
| **Kapat** / **✕** | Kaydetmeden kapatır | Logo değişikliği zaten kaydedilmiştir |
| **Şirket Bilgilerini Kaydet** | Bilgileri kaydeder ve pencereyi kapatır; "✓ '<şirket>' şirket bilgileri başarıyla kaydedildi!" | Onay sormaz |
| **Yönetici Tanımlamasına Geç →** | Sekme 2'ye geçer | Sekme 1'deki değişiklikleri önce kaydedin |

[[EKRAN: sy-m-sirket-detay-yonetici | Şirket Detayları penceresi, "2. Şirket Yöneticisi Tanımlaması" sekmesi; üretilmiş güçlü şifre kutusu görünür | Detay & Yönetim penceresinde "2. Şirket Yöneticisi Tanımlaması" sekmesine tıklayın (yalnız test şirketinde Güçlü Şifre Oluştur'a basın)]]

**Sekme 2 — Şirket Yöneticisi Tanımlaması**

Başlık "2. Şirket Admin Kullanıcı Tanımlaması", açıklama "Şirketin sisteme ilk giriş yapacak yöneticisinin (Admin) kullanıcı bilgileri ve şifresi." Bu sekme şirketin ilk şirket yöneticisini gösterir; şirkette hiç yönetici yoksa kaydettiğinizde yeni bir yönetici oluşur.

| Alan | Ne işe yarar | Nasıl doldurulur / seçenekler | Örnek | Zorunlu |
|---|---|---|---|---|
| **Yönetici Adı Soyadı** | Yöneticinin adı | — | Ayşe Yılmaz | Evet |
| **Giriş E-postası** | Yöneticinin giriş e-postası | Başka bir şirkette kayıtlı olamaz. Kaydedince şirket kartının **İletişim E-posta**sı da bu adres olur | ayse.yilmaz@orneklojistik.com.tr | Evet |
| **Telefon** | Yöneticinin telefonu; şirket kartındaki telefon da güncellenir | — | +90 5XX XXX XX XX | Hayır |
| **Manuel Şifre Ata** | Yöneticiye elle şifre vermek için | En az 6 karakter yazarsanız kaydedince şifre değişir; daha kısa yazılan şifre dikkate alınmaz. Boş bırakılırsa şifre değişmez | — | Hayır |

| Düğme | Ne yapar | Dikkat |
|---|---|---|
| **← Şirket Bilgilerine Dön** | Sekme 1'e döner | — |
| **Güçlü Şifre Oluştur** | 14 karakterlik (büyük/küçük harf, rakam, sembol) bir şifre üretir ve **hemen** yöneticinin şifresi yapar. Şifre "Yeni Oluşturulan Güçlü Şifre:" kutusunda ve 30 saniye kalan bildirimde görünür | Onay sormaz. Yöneticinin eski şifresi o anda geçersiz olur; geri alınamaz |
| **Kopyala** | Üretilen şifreyi panoya kopyalar | Şifreyi müşteriye güvenli bir kanaldan iletin |
| **Kapat** | Kapatır | — |
| **Yönetici Bilgilerini Kaydet** | Yönetici kullanıcısını ve şirket kartının iletişim bilgilerini günceller, pencereyi kapatır ("✓ Yönetici ve Müşteri Kartı Güncellendi!") | Onay sormaz |

> **İpucu:** Müşteri şifresini unuttuysa **Güçlü Şifre Oluştur** yerine **Hoş Geldin Maili** göndermeyi tercih edin. Böylece şifreyi siz görmezsiniz, yönetici bağlantıdan kendi şifresini belirler. Müşteri giriş penceresindeki **Şifremi unuttum** bağlantısını da kendisi kullanabilir.

> **Dikkat:** Detay penceresinde şirketi aktif ya da pasif yapamazsınız; bu işlem yalnızca Kayıtlı Şirketler listesindeki **Pasife Al / Aktife Al** düğmesiyle yapılır.

#### Kredi penceresi

**Bu pencere ne işe yarar?** Şirketin bu ayki kredi durumunu gösterir ve ek kredi yüklemenizi sağlar.

**Nasıl açılır?** Şirket kartında **Kredi**. Başlık "<Şirket> · Kredi".

[[EKRAN: sy-m-kredi | "<Şirket> · Kredi" penceresi: kredi göstergeleri ve Ek kredi / Açıklama alanları | Kayıtlı Şirketler › RECOrion Canlı Test A.Ş. kartında Kredi]]

| Gösterge | Anlamı |
|---|---|
| **Kullanılabilir kredi** | Şu an harcanabilecek toplam kredi (aylık + ek kredi) |
| **Bu ay kullanılan** | Bu dönem harcanan kredi ve aylık hakkın yüzdesi |
| **Aylık hak** | Paketin aylık kredisi; altında kalan miktar ve "ay sonunda silinir" |
| **Ek kredi** | Yüklenmiş ek kredi bakiyesi; "Sonraki aylara devreder" |
| İlerleme çubuğu | Aylık hakkın ne kadarının kullanıldığı (%80'de sarı, %100'de kırmızı) |
| **Kredi tükendi: AI personeller yeni işlem yapamaz** | Kredi sıfırlandı; şirketin AI personelleri durur |
| **Aylık kredinin %N'i kullanıldı** | %80 eşiği aşıldı |

| Alan | Ne işe yarar | Nasıl doldurulur / seçenekler | Örnek | Zorunlu |
|---|---|---|---|---|
| **Ek kredi** | Yüklenecek miktar | Sıfırdan büyük sayı (ondalık için virgül kullanılabilir). "Ek krediler ay sonunda silinmez, sonraki aylara devreder." | 5000 | Evet |
| **Açıklama** | Kredi hareketinin notu | En fazla 200 karakter | Kasım ek kredi satışı, fatura no 2026-118 | Hayır |

| Düğme | Ne yapar | Dikkat |
|---|---|---|
| **Kredi Yükle** | Krediyi yükler: "<şirket> şirketine N kredi yüklendi."; göstergeler yenilenir | Onay sormaz. Bu ekranda geri alma yoktur; miktarı dikkatle kontrol edin |

RECDx ana şirketinde yükleme alanı yoktur; göstergede "RECDx platformu: sınırsız, yalnızca ölçülür" yazar. Geçersiz miktarda "Geçerli bir kredi miktarı girin." uyarısı çıkar.

> **Örnek:** Örnek Lojistik ayın 20'sinde krediyi bitirdi ve 5.000 ek kredi satın aldı. Kayıtlı Şirketler'de Örnek Lojistik kartında **Kredi** › **Ek kredi**: 5000, **Açıklama**: "Kasım ek kredi, fatura 2026-118" › **Kredi Yükle**. AI personeller hemen çalışmaya devam eder.

#### Şirketin paneline ve çalışma alanına geçiş

Kart üzerindeki bina simgesi şirketin **Şirket Yönetim Paneli**ni, sağ ok simgesi şirketin **Çalışma Alanı**nı (Work Space) açar.

- **Şirket Yönetim Paneli:** Şirketin yönetim verilerini (kullanıcılar, departmanlar, unvanlar, AI personel listesi, kredi) görürsünüz. KVKK gereği içerikler (projeler, sohbetler, kurum hafızası, dokümanlar), entegrasyon bağlantıları ve otomasyon kuralları size gösterilmez. Örneğin bir müşterinin **Otomasyonlar › RECSlip.App v2 aylık süreç** kurulumunu, Odoo bağlantısını ve kullanıcıların **Bağlantılarım**'daki kişisel API anahtarlarını göremez, değiştiremezsiniz. Merkez Yönetim'e üstteki **👑 Süper Admin Konsoluna Dön** düğmesiyle dönersiniz.
- **Çalışma Alanı:** Ekranın üstünde "🔒 **KVKK Koruma Modu:** <şirket> şirketinin Work Space alanını görüntülüyorsunuz. Kişisel verilerin korunması gereği bu şirketin projeleri, görevleri, sohbetleri ve kurum hafızası RECDx yöneticilerine gösterilmez." şeridi çıkar. Merkez Yönetim'e üst çubuktaki **👑 Süper Admin Konsolu** düğmesiyle dönersiniz.

[[EKRAN: sy-kvkk-workspace | KVKK Koruma Modu şeridi açık Work Space | Kayıtlı Şirketler › RECOrion Canlı Test A.Ş. kartında sağ ok simgesi (Şirket Çalışma Alanına Geç)]]

> **Dikkat (KVKK):** Bir müşteri "RECSlip kurulumumu kontrol eder misiniz?" derse kurulum ekranlarını size göstermesini (ekran paylaşımı) isteyin. Sistem, RECDx personelinin müşteri sistemine kişisel anahtar tanımlamasına da izin vermez ("KVKK gereği RECDx personeli müşteri sistemine kişisel anahtar tanımlayamaz.").

**Sık sorulan sorular (Kayıtlı Şirketler)**

- *Müşteri sözleşmeyi bitirdi, ne yapmalıyım?* **Pasife Al**. Veriler korunur, kullanıcılar giremez. Silme yalnızca hiç kullanılmamış şirketler içindir.
- *Pasif şirketi tekrar açtım ama paketi bitmiş görünüyor.* **Aktife Al** paket süresini başlatmaz. **Detay & Yönetim**'de **Paket Kira Bitiş Tarihi**'ni yeni tarihle kaydedin.
- *Paket yenilendi; ne güncellemeliyim?* **Detay & Yönetim › Paket Kira Bitiş Tarihi**. Paket değiştiyse **Tanımlı Paket**'i de değiştirin.
- *Logo neden kendiliğinden kaydedildi?* Detay penceresinde logo dosyayı seçtiğiniz anda kaydedilir; **Şirket Bilgilerini Kaydet** gerekmez.
- *Müşteri logosu Şirket Yönetimi'nde de görünür mü?* Evet. Müşteri de logosunu kendi **Şirket Yönetimi › Şirket Profili** ekranından değiştirebilir; iki taraf aynı logoyu görür.
- *3 ay uyarısı ne zaman çıkar?* Aktif şirketin paket bitişine 90 gün ya da daha az kaldığında.


# Katalog

Katalog menüleri **tüm müşterilerin ortak kullandığı** bilgileri yönetir. Burada yaptığınız değişiklik bütün şirketleri etkiler. Kataloğa hiçbir zaman belirli bir şirkete ait bilgi yazmayın.

## Sektör Tanımları

### Sektör Tanımları (Ticaret Bakanlığı)

**Bu ekran ne işe yarar?** T.C. Ticaret Bakanlığı'nın resmi ana sektör listesini yönetir. Şirketler kayıtta ve şirket kartında **Faaliyet Sektörleri**'ni bu listeden seçer; meslek grupları ve katalog departmanları da sektöre bağlıdır. Sistem 11 resmi sektörle (A–K) gelir.

**Ne zaman kullanırım?** Bakanlık listesi değiştiğinde, bir sektörün adını, açıklamasını ya da simgesini düzeltmek istediğinizde.

**Kimler görür / değiştirebilir?** Yalnızca RECDx süper yöneticileri değiştirir. Müşteriler listeyi kayıt ve şirket profili ekranlarında yalnızca seçim için görür.

[[EKRAN: sy-sektorler | Sektör Tanımları, Liste görünümü: kod, ad ve simge, bağlı meslek sayısı | Sol menüde Katalog › Sektör Tanımları]]

**Ekranın bölümleri:** Başlık ve "T.C. Ticaret Bakanlığı resmi sektör kataloğu ve bağlı meslek grupları yönetim modülü." açıklaması; **Yeni Sektör Ekle** düğmesi; **Kanban / Liste** seçici (varsayılan Liste); arama kutusu; sektör listesi.

| Alan | Ne işe yarar | Nasıl doldurulur / seçenekler | Örnek | Zorunlu |
|---|---|---|---|---|
| **Sektör kodu veya adı ara...** | Listeyi süzer | Kod, ad ya da açıklamadan bir parça | ULAŞTIRMA | Hayır |

**Liste sütunları:** **Sektör Kodu** · **Sektör Adı & İkon** · **Açıklama** · **Bağlı Meslek Sayısı** · **Durum** (Aktif / Pasif) · **İşlemler**. Kanban kartında simge ya da görsel, "Sektör Kodu: J", **● Aktif** / **○ Pasif**, ad, açıklama (boşsa "T.C. Ticaret Bakanlığı ana sektör tanımı.") ve "Bağlı Meslek Sayısı:" vardır.

| Düğme | Ne yapar | Dikkat |
|---|---|---|
| **Yeni Sektör Ekle** | Sektör penceresini boş açar | — |
| **N Meslek Tanımı →** | Meslek Tanımları ekranını bu sektörle süzülmüş açar | — |
| **Düzenle** | Sektör penceresini dolu açar | — |
| **Sil** (çöp kutusu, "Sektörü Sil") | "'<kod> - <ad>' sektörünü ve bağlı meslek tanımlarını silmek istediğinize emin misiniz?" sorusundan sonra siler | Onay ister (**Evet, devam et**). Geri alınamaz. Şirketlerde kullanılan sektörü silmeyin; **Sektör Aktif** işaretini kaldırarak pasife alın |

#### Yeni Sektör Tanımla / Sektörü Düzenle

Başlık "Yeni Sektör Tanımla" ya da "'<kod> - <ad>' Sektörünü Düzenle"; alt başlık "T.C. Ticaret Bakanlığı resmi sektör kataloğu ana sektör tanımı."

[[EKRAN: sy-m-sektor | Sektör penceresi: kod, ad, açıklama, simge önizlemesi, Hızlı Seçim emojileri | Sektör Tanımları › bir sektörde Düzenle]]

| Alan | Ne işe yarar | Nasıl doldurulur / seçenekler | Örnek | Zorunlu |
|---|---|---|---|---|
| **Sektör Kodu \*** | Sektörün tekil kodu | Kısa harf kodu; yazdığınız harfler büyük harfe çevrilir. Kayıttan sonra değiştirilemez | J | Evet |
| **Sektör Adı \*** | Resmi sektör adı | Bakanlık listesindeki ad | ULAŞTIRMA HİZMETLERİ | Evet |
| **Sektör Açıklaması (Opsiyonel)** | Sektörün kapsamı | Serbest metin | Yük ve yolcu taşımacılığı, otopark, kiralama | Hayır |
| **Sektör İkonu / Görseli (Eski Usül İkon / Resim)** — ikon kutusu | Listede görünen simge | Bir emoji yazın ("İkon / Emoji (Örn: 🌲, 💻, 🌾)") ya da **Hızlı Seçim:** satırındaki emojilerden birine tıklayın | 🚚 | Hayır |
| **Resim Yükle** / **Resmi Değiştir** | Simge yerine resim kullanmak için | PNG, JPG ya da SVG; en fazla 2 MB | — | Hayır |
| "Veya Harici Resim Linki (https://...)" | İnternetteki bir resmi kullanmak için | https ile başlayan adres | — | Hayır |
| **Sektör Aktif** | Sektörün seçimlerde görünmesi | İşaretli = aktif | işaretli | — |

Pencerede seçtiğiniz simge ya da resmin canlı önizlemesi görünür.

| Düğme | Ne yapar | Dikkat |
|---|---|---|
| **İkon ve Görseli Temizle ✕** | Simgeyi ve resmi kaldırır | Kaydetmeden kalıcı olmaz |
| **Resmi Kaldır** | Yalnızca resmi kaldırır | Aynı |
| **Vazgeç** / **✕** | Kaydetmeden kapatır | — |
| **Sektörü Kaydet** (düzenlemede **Değişiklikleri Kaydet**) | Kaydeder: "✓ '<kod>' yeni sektör oluşturuldu." / "✓ '<kod>' sektörü güncellendi." | — |

**Hata mesajları:** "Lütfen Sektör Kodu ve Sektör Adı alanlarını doldurunuz." · "'<kod>' kodlu sektör zaten tanımlıdır." · "Resim dosyası 2MB'den küçük olmalıdır."

> **Örnek:** J sektörünün simgesi eksik. **Sektör Tanımları** › J satırında **Düzenle** › **Hızlı Seçim**'den 🚚 › **Değişiklikleri Kaydet**.

## Meslek Tanımları

### Meslek Grubu Tanımları (Ticaret Bakanlığı)

**Bu ekran ne işe yarar?** Sektörlere bağlı resmi meslek gruplarını yönetir (sistem 184 resmi meslek grubuyla gelir). Şirketler kayıtta ve şirket kartında meslek gruplarını bu listeden seçer; katalog departman ve unvanları da meslek gruplarıyla eşleşir.

**Ne zaman kullanırım?** Yeni bir meslek grubu eklemek, adını düzeltmek ya da kullanımdan kaldırmak istediğinizde.

**Kimler görür / değiştirebilir?** Yalnızca RECDx süper yöneticileri.

[[EKRAN: sy-meslekler | Meslek Tanımları, Liste görünümü, Sektör Filtresi'nde J seçili | Sol menüde Katalog › Meslek Tanımları; Sektör Filtresi satırında "J - ULAŞTIRMA HİZMETLERİ" düğmesine tıklayın]]

**Ekranın bölümleri:** Başlık ve "T.C. Ticaret Bakanlığı sektörlerine bağlı 184 resmi meslek grubu tanımı ve yönetimi." açıklaması; **Yeni Meslek Ekle**; **Kanban / Liste** seçici; arama kutusu; **Sektör Filtresi:** satırı; liste.

| Alan | Ne işe yarar | Nasıl doldurulur / seçenekler | Örnek | Zorunlu |
|---|---|---|---|---|
| **Meslek kodu veya adı ara...** | Listeyi süzer | Kod, ad, sektör kodu ya da açıklamadan bir parça | taşımacılık | Hayır |
| **Sektör Filtresi:** | Yalnızca bir sektörün mesleklerini gösterir | **TÜM SEKTÖRLER (N)** ya da "<kod> - <ad> (N)" düğmelerinden biri | J - ULAŞTIRMA HİZMETLERİ (16) | Hayır |

**Liste sütunları:** **Meslek Kodu** · **Sektör Kodu** · **Sektör Adı** · **Meslek Tanım Adı** · **Açıklama** · **Durum** (Aktif / Pasif) · **İşlemler**.

| Düğme | Ne yapar | Dikkat |
|---|---|---|
| **Yeni Meslek Ekle** | Meslek penceresini açar; Sektör Filtresi'nde bir sektör seçiliyse o sektör önceden dolar | — |
| **Düzenle** | Meslek penceresini dolu açar | — |
| **Sil** | "'<kod> - <ad>' meslek tanımını silmek istediğinize emin misiniz?" sorusundan sonra siler | Onay ister (**Evet, devam et**). Geri alınamaz |

#### Yeni Meslek Grubu Tanımla / Meslek Tanımını Düzenle

Alt başlık "T.C. Ticaret Bakanlığı resmi meslek grubu tanımı."

[[EKRAN: sy-m-meslek | Meslek penceresi | Meslek Tanımları › bir meslekte Düzenle]]

| Alan | Ne işe yarar | Nasıl doldurulur / seçenekler | Örnek | Zorunlu |
|---|---|---|---|---|
| **Meslek Kodu \*** | Tekil kod | Sektör harfi, nokta ve sıra numarası. Kayıttan sonra değiştirilemez | J.17 | Evet |
| **Bağlı Olduğu Sektör \*** | Mesleğin ana sektörü | "-- Sektör Seçiniz --" listesinden | J - ULAŞTIRMA HİZMETLERİ | Evet |
| **Meslek Tanım Adı \*** | Mesleğin adı | — | Depolama ve antrepoculuk | Evet |
| **Açıklama (Opsiyonel)** | Kapsam | — | — | Hayır |
| **Meslek Tanımı Aktif** | Seçimlerde görünmesi | İşaretli = aktif | işaretli | — |

| Düğme | Ne yapar | Dikkat |
|---|---|---|
| **Vazgeç** / **✕** | Kaydetmeden kapatır | — |
| **Meslek Tanımını Kaydet** (düzenlemede **Değişiklikleri Kaydet**) | Kaydeder: "✓ '<kod>' yeni meslek tanımı eklendi." / "✓ '<kod>' meslek tanımı güncellendi." | — |

**Hata mesajları:** "Lütfen Meslek Kodu, Sektör Kodu ve Meslek Tanım Adı alanlarını doldurunuz." · "'<kod>' kodlu meslek tanımı zaten mevcuttur." · "'<kod>' kodlu ana sektör bulunamadı."

> **İpucu:** Sektör Tanımları ekranındaki **N Meslek Tanımı →** düğmesi sizi doğrudan o sektörün mesleklerine götürür.

## Departman & Unvan

### Departman & Unvan Kataloğu

**Bu ekran ne işe yarar?** Tüm müşterilerin AI personel işe alırken ve departman kurarken seçtiği hazır **departman** ve **unvan** kataloğunu yönetir. Bir unvanın iş tanımı, sorumlulukları, yetkinlikleri, rol promptu ve bilgi dokümanları, o unvanla işe alınan tüm AI personellere (bütün şirketlerde) aktarılır. Buna **Platform Unvan Bilgisi** denir.

**Ne zaman kullanırım?** Yeni bir unvan eklemek, bir unvanın rol promptunu iyileştirmek, unvana genel mesleki doküman öğretmek istediğinizde.

**Kimler görür / değiştirebilir?** Yalnızca RECDx süper yöneticileri değiştirir. Müşteriler kataloğu **AI Personel İşe Al** sihirbazında ve departman eklerken seçim için görür.

[[EKRAN: sy-katalog | Departman & Unvan Kataloğu: solda sektör listesi, ortada Departmanlar kartı, altında Unvanlar tablosu | Sol menüde Katalog › Departman & Unvan; soldan bir sektör seçin]]

**Ekranın bölümleri:**

1. Üst kart: "N departman · N unvan. Katalog tüm müşterilere açık genel bilgidir (Platform Unvan Bilgisi); şirkete özel bilgi yazmayın." Sağda **Yeni Departman** ve **Yeni Unvan** düğmeleri.
2. Sol: **sektör listesi**. Genel kayıtlar (tüm sektörlere uygun) ve "<kod> · <sektör adı>" satırları. Her satırda "departman / unvan" sayıları.
3. **Departmanlar** kartı: "Bir departman seçerek unvanlarını süzün. Üzeri çizili olanlar pasif." **Tümü** ve departman düğmeleri (yanında unvan sayısı). Bir departman seçince altında kodu, açıklaması, meslek grupları ve **Düzenle** / **Sil** düğmeleri çıkar.
4. **Unvanlar (N)** tablosu.

| Alan | Ne işe yarar | Nasıl doldurulur / seçenekler | Örnek | Zorunlu |
|---|---|---|---|---|
| **Unvan, kod veya iş tanımı ara…** | Unvan tablosunu süzer | Bir parça yazın | planlama | Hayır |

**Unvanlar tablosu sütunları:** **Unvan** · **Departman** · **Kıdem** · **Meslek grupları** ("Tümü" = kısıt yok) · **Model** ("—" = platform varsayılanı) · **Durum** (Aktif / Pasif). Satıra tıklayınca unvan penceresi açılır. Boşsa "Bu seçimde unvan yok."

| Düğme | Ne yapar | Dikkat |
|---|---|---|
| **Yeni Departman** | Katalog departmanı penceresini açar (seçili sektörle) | — |
| **Yeni Unvan** | Katalog unvanı penceresini açar | Seçili sektörde departman yoksa pasiftir |
| **Düzenle** (seçili departman) | Departman penceresini dolu açar | — |
| **Sil** (seçili departman) | "'<ad>' katalog departmanı silinsin mi?" sorusundan sonra siler | Onay ister. Departmanda unvan varsa silinmez |

#### Yeni Katalog Departmanı / Katalog Departmanını Düzenle

[[EKRAN: sy-m-katalog-departman | Katalog departmanı penceresi | Departman & Unvan › bir sektör seçin › Yeni Departman]]

| Alan | Ne işe yarar | Nasıl doldurulur / seçenekler | Örnek | Zorunlu |
|---|---|---|---|---|
| **Kod** | Tekil kod | Yalnızca büyük harf, rakam ve alt çizgi; 2–64 karakter (yazdığınız harfler büyük harfe çevrilir) | J_OPERASYON | Evet |
| **Ad** | Departman adı | — | Operasyon ve Sevkiyat | Evet |
| **Sektör** | Departmanın uygun olduğu sektör | "Genel (tüm sektörler)" ya da bir sektör. Sektör değişince meslek seçimi sıfırlanır | J · ULAŞTIRMA HİZMETLERİ | Hayır |
| **Sıra** | Listedeki sırası | Küçük sayı önce gelir | 10 | Hayır |
| **Açıklama** | Departmanın görevi | — | Taşıma planlama, sevkiyat ve filo takibi | Hayır |
| **Tipik meslek grupları** | Bu departmanın hangi meslek gruplarında olduğu | Sektörün meslek düğmelerine tıklayın. Genel departmanda "Genel kayıtlar tüm meslek gruplarına uygundur." yazar | J.05, J.16 | Hayır |
| **Aktif** | Seçimlerde görünmesi | — | işaretli | — |

Düğmeler: **Vazgeç**, **Kaydet** ("Departman kaydedildi.").

**Hata mesajları:** "Kod yalnızca büyük harf, rakam ve alt çizgi içerebilir (2-64 karakter)." · "'<kod>' kodlu departman zaten var." · "Bu departmanda N unvan var. Önce unvanları taşıyın ya da departmanı pasife alın."

#### Yeni Katalog Unvanı / Unvanı düzenle

Pencere başlığı yeni unvanda "Yeni Katalog Unvanı", kayıtlı unvanda unvanın adıdır.

[[EKRAN: sy-m-katalog-unvan | Katalog unvanı penceresi: unvan, kod, departman, kıdem, önerilen model, otonomi, iş tanımı, rol promptu | Departman & Unvan › Unvanlar tablosunda bir satıra tıklayın]]

| Alan | Ne işe yarar | Nasıl doldurulur / seçenekler | Örnek | Zorunlu |
|---|---|---|---|---|
| **Unvan** | Unvanın adı | — | Sevkiyat Planlama Uzmanı | Evet |
| **Kod** | Tekil kod | Büyük harf, rakam, alt çizgi | J_SEVKIYAT_PLANLAMA | Evet |
| **Departman** | Unvanın bağlı olduğu katalog departmanı | "Liste seçili sektörün departmanlarını gösterir." | Operasyon ve Sevkiyat | Evet |
| **Kıdem** | Unvanın seviyesi | Uzman Yardımcısı / Uzman / Kıdemli Uzman / Takım Lideri / Yönetici | Uzman | Hayır |
| **Önerilen model** | Bu unvanın AI personeline önerilen model | "Platform varsayılanı" ya da etkin bir sohbet modeli. Müşteri yine yalnızca RECAi adını görür | Platform varsayılanı | Hayır |
| **Otonomi** | AI personelin ne kadar bağımsız çalışacağı | **L1 · öneri + insan onayı** / **L2 · rutin işleri kendisi yapar** / **L3 · tam otonom** | L1 · öneri + insan onayı | Hayır |
| **İş tanımı** | Unvanın kısa tanımı | 1–3 cümle | Günlük sevkiyatları planlar, araç ve rota önerir. | Hayır |
| **Sorumluluklar (her satır bir madde)** | Görev listesi | Her satıra bir görev | Günlük sevkiyat planı hazırlamak | Hayır |
| **Yetkinlikler (her satır bir madde)** | Gerekli bilgi ve beceriler | Her satıra bir yetkinlik | Rota optimizasyonu | Hayır |
| **Başarı ölçütleri (her satır bir madde)** | Performans göstergeleri | Her satıra bir ölçüt | Zamanında teslim oranı | Hayır |
| **Rol promptu** | AI personelin temel talimatı | Serbest metin. "{{company_name}} ve {{department_name}} işe alımda şirket ve departman adıyla doldurulur." | Sen {{company_name}} şirketinin {{department_name}} departmanında … | Hayır |
| **Uygun meslek grupları (boş: departmanın tüm meslek grupları)** | Unvanın hangi meslek gruplarına önerileceği | Meslek düğmelerine tıklayın; boş bırakırsanız departmanın meslekleri geçerlidir | J.05 | Hayır |
| **Aktif (pasif unvanlar yeni işe alımlarda görünmez)** | Yeni işe alımlarda görünmesi | — | işaretli | — |

| Düğme | Ne yapar | Dikkat |
|---|---|---|
| **Sil** (yalnız kayıtlı unvanda) | "'<unvan>' unvanı silinsin mi? Şirketlerde kullanılıyorsa pasife alınır." sorusundan sonra siler | Onay ister. Unvan bir şirkette kullanılıyorsa silinmez, pasife alınır: "Unvan N şirkette kullanıldığı için silinmedi, pasife alındı." |
| **Bilgi Dokümanları** (yalnız kayıtlı unvanda) | **<unvan> · Platform Bilgi Dokümanları** penceresini açar | — |
| **Vazgeç** | Kaydetmeden kapatır | — |
| **Kaydet** | Kaydeder ("Unvan kaydedildi.") | Değişiklik bu unvanı kullanan tüm şirketlerin AI personeline yansır |

**Hata mesajları:** "'<kod>' kodlu unvan zaten var." · "Seçilen katalog departmanı bulunamadı." · "Geçersiz kıdem." · "Geçersiz otonomi seviyesi."

#### Platform Bilgi Dokümanları

**Bu pencere ne işe yarar?** Bir katalog unvanına genel mesleki doküman (yönetmelik özeti, meslek el kitabı, iyi uygulama rehberi) yüklersiniz. Onayladığınız dokümanı tüm şirketlerdeki o unvanın AI personelleri öğrenir.

Pencerenin üstünde şu uyarı yazar: "Onaylanan dokümanları tüm müşterilerdeki bu unvanın AI personelleri öğrenir (Platform Unvan Bilgisi). Yalnızca genel mesleki bilgi yükleyin; hiçbir şirkete ait veri içermemelidir."

[[EKRAN: sy-m-unvan-dokumanlari | Platform Bilgi Dokümanları penceresi: yükleme alanı ve doküman listesi durum rozetleriyle | Departman & Unvan › bir unvanı açın › Bilgi Dokümanları]]

| Alan / öğe | Ne işe yarar | Nasıl kullanılır |
|---|---|---|
| **Doküman veya görsel yükleyin (tıklayın ya da sürükleyin)** | Dosya yükler | Tıklayıp seçin ya da dosyayı sürükleyip bırakın. Birden fazla dosya seçebilirsiniz. Kabul edilenler: PDF, Word, Excel, PowerPoint (eski .doc/.xls/.ppt dahil), metin dosyaları ve görseller (PNG, JPG, WEBP, TIFF); en fazla 50 MB |
| Doküman satırı | Dosya adı, türü, boyutu, sürümü, görsel sayısı ve maskelenen kişisel veriler ("KVKK: 2 Telefon maskelendi") | — |

**Doküman durumları:** **Yüklendi** · **İşleniyor** (metin ve görseller okunuyor, kişisel veriler maskeleniyor) · **Onay bekliyor** · **Öğrenildi** · **Reddedildi** · **Karantinada** (içerik güvenliği denetiminden geçmedi) · **İşlenemedi** · **Eski sürüm**.

| Düğme | Ne yapar | Dikkat |
|---|---|---|
| **İncele ve onayla** (Onay bekliyor durumunda) / **Aç** | İnceleme penceresini açar: özet, "Öğrenilecek anahtar bilgiler (her satır bir bilgi)" ve KVKK maskeli metin örneği. Anahtar bilgileri onaydan önce düzeltebilirsiniz | — |
| **Onayla ve öğret** | Dokümanı onaylar; AI personeller öğrenir | Tüm şirketleri etkiler |
| **Reddet** | Dokümanı reddeder (isteğe bağlı gerekçe) | — |
| **Sil**, **İndir**, **Yeniden işle**, **Yeni sürüm yükle** | Adlarındaki işi yapar | Sil geri alınamaz |

> **Dikkat:** Bu pencereye bir müşteriden gelen dosyayı (fatura, sözleşme, müşteri listesi) asla yüklemeyin. Doküman bütün müşterilerin AI personeline açılır.

**Adım adım örnek: yeni bir unvan eklemek**

1. **Departman & Unvan** › soldan "J · ULAŞTIRMA HİZMETLERİ" sektörünü seçin.
2. **Departmanlar** kartında "Operasyon ve Sevkiyat" departmanını seçin (yoksa önce **Yeni Departman** ile ekleyin).
3. **Yeni Unvan** › **Unvan**: "Sevkiyat Planlama Uzmanı", **Kod**: "J_SEVKIYAT_PLANLAMA", **Kıdem**: Uzman, **Otonomi**: L1.
4. İş tanımı, sorumluluklar, yetkinlikler ve rol promptunu yazın › **Kaydet**.
5. Unvanı yeniden açın › **Bilgi Dokümanları** › genel bir "Kara yolu taşımacılığı mevzuatı özeti" PDF'i yükleyin.
6. Durum **Onay bekliyor** olunca **İncele ve onayla** › anahtar bilgileri kontrol edin › **Onayla ve öğret**.

Artık Örnek Lojistik'te Ayşe Yılmaz AI personel işe alırken bu unvanı seçebilir.

## Proje Şablonları

### RECDx proje şablonları

**Bu ekran ne işe yarar?** RECDx'in tüm şirketlere açık **proje** ve **Case** şablonlarını yönetir. Şablonlar şirketlerin "Şablondan oluştur" ekranında görünür; şirket bir şablonla tek tıkla adımları hazır bir proje açar. Sistemle gelen şablonlardan bazıları: Kurumsal web sitesi yenileme, KVKK uyum projesi, Yeni ürün lansmanı, ERP entegrasyonu, Pozisyon için işe alım süreci, Müşteri şikâyeti vakası ve RECQmind Case'leri (İade talebi, Sipariş iptali, Kargo problemi, Ürün sorusu).

**Ne zaman kullanırım?** Birçok müşterinin tekrar tekrar yaptığı bir iş için hazır plan sunmak istediğinizde.

**Kimler görür / değiştirebilir?** Yalnızca RECDx süper yöneticileri. Şirketlerin kendi şablonları KVKK gereği burada görünmez.

[[EKRAN: sy-proje-sablonlari | Proje Şablonları tablosu: şablon, kategori, adım, süre, kullanım, durum | Sol menüde Katalog › Proje Şablonları]]

Kartın alt başlığı: "Tüm şirketlerin 'Şablondan oluştur' ekranında görünür. Şirketlerin kendi şablonları KVKK gereği burada listelenmez."

**Tablo sütunları:** **Şablon** (Case türündeyse **Case** rozeti) · **Kategori** · **Adım** (adım sayısı) · **Süre** (~N gün) · **Kullanım** (kaç kez proje açıldığı) · **Durum** (**Yayında** / **Arşivde**). Şablon yoksa "Şablon yok — İlk RECDx şablonunu ekleyin."

| Düğme | Ne yapar | Dikkat |
|---|---|---|
| **Yeni şablon** | Boş şablon düzenleyicisini açar | — |
| **Düzenle** | Şablonu düzenler | — |
| **Arşivle** | "'<ad>' arşivlensin mi? Şirketler artık bu şablonla proje açamaz; açılmış projeler etkilenmez." | Onay ister. **Yayımla** ile geri alınır |
| **Yayımla** | Arşivdeki şablonu yeniden yayına alır | Onay sormaz |

#### Yeni RECDx şablonu / Şablonu düzenle

[[EKRAN: sy-m-sablon | Şablon düzenleyicisi: ad, kategori, tür, açıklama, plan özeti ve iş adımları | Proje Şablonları › bir şablonda Düzenle]]

| Alan | Ne işe yarar | Nasıl doldurulur / seçenekler | Örnek | Zorunlu |
|---|---|---|---|---|
| **Ad \*** | Şablonun adı | En az 2, en fazla 200 karakter | Depo sayımı | Evet |
| **Kategori** | Şablonun grubu | En fazla 80 karakter | Operasyon | Hayır |
| **Tür** (yalnız yeni şablonda) | Proje mi Case mi | **Proje** (uzun soluklu iş) / **Case** (bir olaya karşılık açılan kısa iş) | Proje | — |
| **Açıklama** | Şablonun ne işe yaradığı | En fazla 2000 karakter | — | Hayır |
| **Plan özeti** | Projenin genel planı | En fazla 3000 karakter | — | Hayır |

**İş adımları** bölümünde her adım S1, S2… diye numaralanır:

| Adım alanı | Ne işe yarar | Örnek |
|---|---|---|
| **Başlık** | Adımın adı (başlığı boş adımlar kaydedilmez) | Sayım planını hazırla |
| **Unvan (rol)** | Adımı yapacak unvan | Depo Sorumlusu |
| **Departman** | Adımın departmanı | Operasyon |
| **Süre (gün)** | Tahmini süre (0,5'er artar) | 1 |
| **Açıklama** | Adımın ayrıntısı | — |
| **Önce bitmesi gereken** | Bu adımdan önce tamamlanması gereken adımlar (çoklu seçim; Ctrl ile birden fazla seçilir) | S1 |
| **Onay** — **gerekli** | Adımın çıktısı bir insan tarafından onaylanmalı mı | işaretli |

| Düğme | Ne yapar | Dikkat |
|---|---|---|
| **Adım ekle** | Yeni boş adım ekler | — |
| Çöp kutusu ("<S1> adımını sil") | Adımı siler; diğer adımlardaki bağımlılığı da kaldırır | Kaydetmeden kalıcı olmaz |
| **Vazgeç** | Kaydetmeden kapatır | — |
| **Kaydet** | Kaydeder: yeni şablonda "Şablon yayımlandı; tüm şirketler görebilir.", düzenlemede "Şablon güncellendi." | Yeni şablon kaydedildiği anda tüm şirketlere açılır |

**Hata mesajları:** "Şablon adı ve en az bir adım gerekli." · "Şablonda en az bir iş adımı olmalı."

> **İpucu:** Şablonu önce **RECOrion Canlı Test A.Ş.** şirketinde deneyin: şablondan proje açın, adımların sırasını ve sürelerini kontrol edin.

## Mevzuat Paketleri

### Mevzuat bilgi paketleri

**Bu ekran ne işe yarar?** AI personelin ilgili işlerde kaynak ve sürüm göstererek kullandığı **mevzuat özet kartlarını** düzenler ve uzman kontrolü beyanıyla yayımlarsınız. Sistemde beş paket vardır: KVKK — Kişisel Verilerin Korunması; SGK — Sosyal Güvenlik ve İşe Giriş-Çıkış; Vergi — Temel Yükümlülükler; e-Fatura, e-Arşiv ve e-Defter; İSG — İş Sağlığı ve Güvenliği.

Taslaklar yalnızca burada görünür. Şirketler ve AI personeller yalnızca **yayımlanan** sürümü görür; şirket yöneticileri paketleri kendi **Şirket Yönetimi › Mevzuat Paketleri** ekranında açıp kapatır.

**Ne zaman kullanırım?** Mevzuat değiştiğinde, bir kartta hata bulunduğunda ya da uzman kontrolü tamamlandığında.

**Kimler görür / değiştirebilir?** Yalnızca RECDx süper yöneticileri.

[[EKRAN: sy-mevzuat | Mevzuat bilgi paketleri listesi: Yayında / Taslak rozetleri | Sol menüde Katalog › Mevzuat Paketleri]]

Kartın alt başlığı: "Taslaklar yalnızca burada görünür. Şirketler ve AI personel yalnızca uzman kontrolünden geçip yayımlanan sürümü görür."

**Paket satırı:** paket adı, rozet ve alt bilgi ("N taslak kart · son yayın: <tarih>, kontrol eden <ad>").

| Rozet | Anlamı |
|---|---|
| **Yayında · sürüm N** | Paketin N. sürümü şirketlere açık |
| **Taslak · uzman kontrolü bekliyor** | Paket hiç yayımlanmadı |
| **Yayımlanmamış değişiklik var** | Taslakta yayındaki sürümden farklı değişiklik var |

| Düğme | Ne yapar | Dikkat |
|---|---|---|
| **Kartları düzenle** | Taslak kart penceresini açar | Yayındaki sürüm değişmez |
| **Uzman kontrolüyle yayımla** | Yayımlama penceresini açar | Taslak kart yoksa ya da yayından beri değişiklik yoksa pasiftir |

#### Taslak kartlar

[[EKRAN: sy-m-mevzuat-kartlar | "<paket> · taslak kartlar" penceresi | Mevzuat Paketleri › bir pakette Kartları düzenle]]

| Alan (her kart için) | Ne işe yarar | Nasıl doldurulur | Örnek | Zorunlu |
|---|---|---|---|---|
| **Başlık** | Kartın konusu | Kısa | İşe giriş bildirgesi süresi | Evet |
| **Yasal dayanak** | Kanun ve madde | — | 5510 sayılı Kanun md. 8 | Hayır |
| **Metin** | Kuralın sade özeti | Birkaç cümle | — | Evet |
| **Etiketler (virgülle)** | AI personelin kartı bulmasına yardım eden anahtar kelimeler | Virgülle ayırın | sgk, işe giriş, bildirge | Hayır |
| **Resmi kaynaklar (her satır: başlık \| https://…)** | Kartın resmi kaynağı | Her satıra "başlık \| adres" | SGK Mevzuat \| https://... | Hayır |

| Düğme | Ne yapar | Dikkat |
|---|---|---|
| **Kartı çıkar** | Kartı taslaktan çıkarır ("Kart taslaktan çıkarılsın mı?") | Onay ister; kaydetmeden kalıcı olmaz |
| **Kart ekle** | Boş kart ekler | — |
| **Vazgeç** | Kaydetmeden kapatır | — |
| **Taslağı kaydet** | Taslağı kaydeder; yayındaki pakette "Taslak kaydedildi; yayındaki sürüm değişmedi. Uzman kontrolünden sonra yeniden yayımlayın." | — |

#### Yayımla

Pencerede şu not yazar: "Kartların ilk sürümü Claude tarafından hazırlandı. Yayından önce bir hukuk/mali müşavirlik uzmanının güncel mevzuata göre kontrol etmesi zorunludur; yayımlanan sürüm tüm şirketlerin AI personeli tarafından kullanılabilir."

[[EKRAN: sy-m-mevzuat-yayimla | "<paket> · yayımla" penceresi: uzman beyanı, uzman adı, kontrol tarihi | Mevzuat Paketleri › bir pakette Uzman kontrolüyle yayımla (yayımlamadan Vazgeç ile kapatın)]]

| Alan | Ne işe yarar | Nasıl doldurulur / seçenekler | Örnek | Zorunlu |
|---|---|---|---|---|
| **Kartlar bir uzman tarafından güncel mevzuata göre kontrol edildi.** | Uzman kontrolü beyanı | Kontrol gerçekten yapıldıysa işaretleyin | işaretli | Evet |
| **Kontrol eden uzman \*** | Uzmanın adı ve unvanı | En az 3 karakter ("Ad Soyad, unvan") | Av. Deniz Arslan | Evet |
| **Kontrol tarihi \*** | Kontrolün yapıldığı gün | İleri tarih seçilemez; varsayılan bugün | 03.11.2026 | Evet |
| **Not** | Ek açıklama | — | 2026 değişiklikleri işlendi | Hayır |

| Düğme | Ne yapar | Dikkat |
|---|---|---|
| **Yayımla** | Yeni sürümü yayımlar: "'<paket>' sürüm N yayımlandı." | Beyan işaretli ve uzman adı en az 3 karakter değilse pasiftir. Yayımlanan sürüm hemen tüm şirketlere açılır |
| **Vazgeç** | Kapatır | — |

> **Dikkat:** Kartlar genel bilgilendirme içindir; şirketlerin ekranında "hukuki veya mali danışmanlık yerine geçmez" uyarısı görünür. Uzman kontrolü yapılmadan beyan kutusunu işaretlemeyin.

## Bağlantı Kataloğu

### Bağlantı kataloğu

**Bu ekran ne işe yarar?** Şirketlerin **Entegrasyonlar › Bağlantı ekle** galerisinde gördüğü sistem kartlarını (ERP, CRM, iş takibi, doküman vb.) ve her sisteme nasıl bağlanılacağını yönetir. Kartlar kimlik bilgisi (şifre, anahtar) içermez; müşteri kendi bilgisini kendi ekranında girer ve siz bu bilgiyi göremezsiniz.

**Ne zaman kullanırım?** Galeriye yeni bir sistem eklemek, "Yakında" olan bir sistemi açmak, kurulum adımlarını düzeltmek ya da bir kartı arşivlemek istediğinizde.

**Kimler görür / değiştirebilir?** Yalnızca RECDx süper yöneticileri.

[[EKRAN: sy-baglanti-katalogu | Bağlantı kataloğu tablosu: sistem, kategori, bağlanma yolu rozetleri, durum | Sol menüde Katalog › Bağlantı Kataloğu]]

Kartın alt başlığı: "Şirketlerin bağlanabileceği sistemler ve bağlanma yolları. Kartlar kimlik bilgisi içermez; ön ayar yalnızca düz alanlardır (ör. MCP adresi)."

**Tablo sütunları:** **Sistem** (ad; altında kod ve üretici) · **Kategori** · **Bağlanma yolu** · **Bağlayıcı** · **Durum** (**Yayında** / **Arşivde**).

**Bağlanma yolları:**

| Yol | Anlamı | Örnek sistemler |
|---|---|---|
| **Doğrudan bağlantı** | RECOrion'un kendi yerleşik bağlayıcısıyla bağlanır | Odoo, RECQmind, RECSlip, GitHub, Trello, Telegram |
| **Tek tık giriş (MCP)** | Müşteri sistemin kendi giriş ekranından onay verir (MCP üzerinden) | HubSpot, Jira ve Confluence, Notion, Figma |
| **MCP sunucusu** | Müşteri bir MCP sunucu adresi ve anahtarıyla bağlanır | DeepWiki, Diğer MCP sunucusu |
| **Şirket sunucusu (Edge)** | Müşterinin kendi sunucusuna kurulan Edge programıyla bağlanır | Logo, Mikro, Netsis |
| **Yakında** | Henüz bağlanamaz; galeride bilgi kartı olarak görünür | SAP, Salesforce, Nebim |

| Düğme | Ne yapar | Dikkat |
|---|---|---|
| **Kart ekle** | Boş kart penceresini açar | — |
| **Düzenle** | Kartı düzenler | Aşağıdaki RECSlip / RECQmind uyarısına bakın |

#### Kart ekle / Kartı düzenle

[[EKRAN: sy-m-baglanti-karti | Bağlantı kartı penceresi: kod, sistem adı, kategori, bağlanma yolu, bağlayıcı, ön ayar, kurulum adımları | Bağlantı Kataloğu › Kart ekle (kaydetmeden Vazgeç ile kapatın)]]

| Alan | Ne işe yarar | Nasıl doldurulur / seçenekler | Örnek | Zorunlu |
|---|---|---|---|---|
| **Kod \*** | Kartın tekil kodu | Küçük harfle başlar; küçük harf, rakam, alt çizgi; 2–64 karakter. Kayıttan sonra değiştirilemez | logo_tiger | Evet |
| **Sistem adı \*** | Galeride görünen ad | En az 2, en fazla 120 karakter | Logo Tiger 3 | Evet |
| **Üretici** | Yazılım firması | — | Logo Yazılım | Hayır |
| **Kategori** | Galerideki grup | ERP, CRM, İş takibi, Doküman, Yazılım, Müşteri destek, Mesajlaşma, Finans, Tasarım, Diğer | ERP | Evet |
| **Bağlanma yolu** | Bağlantı türü | Yukarıdaki beş yol | Şirket sunucusu (Edge) | Evet |
| **Bağlayıcı** (Yakında'da gizli) | Bağlantıyı yapan teknik bileşen | MCP yollarında MCP bağlayıcısı, Edge yolunda Edge bağlayıcısı seçilmelidir | Edge | Evet (Yakında hariç) |
| **Açıklama** | Galerideki tanıtım metni | En fazla 2000 karakter | — | Hayır |
| **Ön ayar (JSON; kimlik bilgisi yazmayın)** | Bağlantı formuna önceden doldurulacak düz ayarlar | Süslü parantezli JSON. Yalnızca bağlayıcının tanıdığı alanlar. **Asla** şifre ya da anahtar yazmayın | {"url": "https://mcp.ornek.com"} | Hayır |
| **Kurulum adımları (her satır bir adım)** | Müşteriye gösterilecek kurulum talimatı | Her satıra bir adım; en fazla 12 adım | Edge programını şirket sunucusuna kurun | Hayır |
| **Arama kelimeleri** | Galeride aramada bulunmasını sağlar | Virgülle | logo, tiger, muhasebe | Hayır |
| **Sıra** | Galerideki sıra | Küçük sayı önce | 100 | Hayır |

| Düğme | Ne yapar | Dikkat |
|---|---|---|
| **Vazgeç** | Kaydetmeden kapatır | — |
| **Arşivle** / **Yayına al** (kayıtlı kartta) | Kartı galeriden kaldırır ya da geri koyar | Arşivlenen kart yeni bağlantılarda görünmez |
| **Kaydet** | Kartı kaydeder ("Kart kaydedildi.") | Sistem adı 2 karakterden kısaysa pasiftir |

**Hata mesajları:** "Ön ayar geçerli JSON olmalı, ör. {"url": "https://..."}" · "Ön ayarda bilinmeyen alan: …" · "Bağlanma yolu ile bağlayıcı uyuşmuyor." · "Bağlayıcı geçersiz." · "Kategori geçersiz."

> **Dikkat:** **RECQmind (Odoo Helpdesk)** ve **RECSlip (Odoo masraf fişleri)** kartları yalnızca o uygulamayı kullanan ve Odoo'su olan şirketlere görünür. Bu düzenleme penceresinde bu kısıtı gösteren bir alan yoktur ve kartı bu pencereden kaydetmek kısıtı kaldırabilir (kart tüm şirketlere görünür hâle gelebilir). Bu iki kartta değişiklik gerekiyorsa önce teknik ekibe danışın.

## Uygulama Talepleri

### Uygulama talepleri (RECQmind, RECSlip)

**Bu ekran ne işe yarar?** Müşterilerin RECDx uygulamaları (**RECQmind** ve **RECSlip**) için yaptığı seçimleri izlersiniz. Müşteri bu seçimi iki yerden yapar: resmi sitede paket satın alırken ya da sonradan kendi **Şirket Yönetimi** ekranından.

Müşterinin dört seçeneği vardır:

| Müşterinin seçimi | Sonucu |
|---|---|
| **Zaten kullanıyorum** | Satış yok; şirketin Odoo'su varsa yalnızca entegrasyon açılır |
| **Paketime ekle** | Paket tanımındaki teklife göre Odoo satış siparişine satır eklenir (dahilse 0 fiyat, indirimliyse indirimli fiyat) |
| **Teklif istiyorum** | Odoo'da CRM fırsatı açılır; satış ekibi arar |
| **Hayır** | Bir şey yapılmaz |

Odoo'su olmayan şirket **Zaten kullanıyorum** ya da **Paketime ekle** seçemez; seçimi teklife döner.

**Ne zaman kullanırım?** Her gün; yeni talepleri satış ve kurulum ekibine yönlendirmek, kurulumu biten talebi kapatmak, Odoo hatası olanları yeniden denemek için.

**Kimler görür / değiştirebilir?** Yalnızca RECDx süper yöneticileri.

[[EKRAN: sy-uygulama-talepleri | Uygulama talepleri tablosu: şirket, uygulama, seçim, paket teklifi, fiyat, Odoo, durum | Sol menüde Katalog › Uygulama Talepleri]]

Kartın alt başlığı: "Müşterilerin RECQmind ve RECSlip seçimleri. 'Paketime ekle' Odoo siparişine satır, 'teklif istiyorum' Odoo CRM fırsatı olur; 'zaten kullanıyorum' yalnızca entegrasyon açar."

**Süzgeç düğmeleri:** **Tümü** · **Yeni** · **Siparişte** · **CRM fırsatı** · **Zaten kullanıyor** · **Hata** · **Tamamlandı**.

**Tablo sütunları:**

| Sütun | Anlamı |
|---|---|
| **Şirket** | Şirket adı; altında kaynak: "satın almada" ya da "Şirket Yönetimi" |
| **Uygulama** | RECQmind ya da RECSlip |
| **Seçim** | Müşterinin seçimi |
| **Paket teklifi** | Şirketin paketindeki teklif: "pakette yok", "indirimli %N", "pakete dahil" |
| **Fiyat** | Yalnız "Paketime ekle"de: "<uygulanan fiyat> (liste <liste fiyatı>)" |
| **Odoo** | Satış siparişi numarası ya da "Fırsat #N" |
| **Durum** | Aşağıdaki rozetler; altında varsa hata ya da not |
| **Tarih** | Talebin tarihi |

**Durumlar:** **Yeni** · **Siparişte** (Odoo siparişine eklendi) · **CRM fırsatı** · **Zaten kullanıyor** · **Tamamlandı** · **İptal** · **Hata** (Odoo işlemi başarısız) · **Odoo kapalı** (Odoo bağlantısı kapalıyken gelen talep).

| Düğme | Ne yapar | Dikkat |
|---|---|---|
| **Yeniden dene** (Hata ve Odoo kapalı satırlarında; "Zaten kullanıyorum" hariç) | Odoo işlemini tekrar dener: "Odoo işlemi yapıldı." ya da hata metni | Onay sormaz |
| **Tamamlandı** | Talebi kapatır; önce "İsteğe bağlı not (ör. kurulum yapıldı):" sorusu gelir | Not penceresinde **Vazgeç** derseniz durum değişmez |
| **İptal** | Talebi iptal eder; not sorulur | Aynı |

Talep yoksa "Talep yok — Müşteriler satın almada veya Şirket Yönetimi'nden seçim yaptıkça burada görünür." yazar.

> **Dikkat (KVKK):** Bu ekran yalnızca **talep kaydını** gösterir. Müşterinin RECSlip.App v2 kurulumu (Şirket Yönetimi › Otomasyonlar › "RECSlip.App v2 aylık süreç" kartı), Odoo bağlantısı, onaylayıcıların **Bağlantılarım**'a eklediği kişisel Odoo API anahtarları, aylık "RECSlip masraf süreci" Case'leri ve fiş onay kararları size görünmez. RECSlip kurulumu müşteri tarafında, müşterinin kendi kullanıcılarıyla yapılır.

**Adım adım örnek: RECSlip "Paketime ekle" talebi**

1. **Uygulama Talepleri** › **Siparişte** süzgeci. Örnek Lojistik'in RECSlip satırında **Seçim**: "Paketime ekle", **Paket teklifi**: "indirimli %50", **Odoo**: sipariş numarası görünür.
2. Satış ekibi Odoo'da siparişi onaylar; kurulum ekibi Örnek Lojistik'in Odoo'suna RECSlip.App v2'yi (en az 20.0.2.34.0) kurar.
3. Örnek Lojistik'te Zeynep Kaya (muhasebeci) ve Ayşe Yılmaz kendi Odoo API anahtarlarını **Bağlantılarım**'a ekler, Ayşe Yılmaz **Otomasyonlar**'da aylık süreci kurar (bu adımlar müşteri tarafındadır; Şirket Yönetimi ve Work Space kılavuzlarında anlatılır).
4. Müşteri kurulumun bittiğini bildirince satırda **Tamamlandı** › not: "RECSlip v2 kuruldu, müşteri onayladı." › **Tamam**.

**Sık sorulan sorular**

- *"Hata" durumundaki talebi neden yeniden deneyemiyorum?* "Zaten kullanıyorum" seçimlerinde Odoo işlemi olmadığından **Yeniden dene** çıkmaz.
- *Fiyat nereden geliyor?* Kiralama Paketleri'ndeki **RECDx uygulamaları (Odoo)** teklifinden ve seçilen Odoo ürününün fiyatından.


# Ticari & Yetki

## Kiralama Paketleri

### Kiralama Paketleri Yönetimi

**Bu ekran ne işe yarar?** Müşterilere satılan abonelik paketlerini tanımlarsınız: aylık fiyat, insan kullanıcı / AI personel / proje sınırları, aylık kredi, depolama, pakete dahil RECAi adları ve yetenekleri, paket izinleri, Odoo satış ürünü ve RECDx uygulama (RECQmind, RECSlip) teklifleri. Resmi sitedeki paket seçenekleri ve şirket kartlarındaki **Tanımlı Paket** listesi buradan gelir.

**Ne zaman kullanırım?** Yeni bir paket satışa çıkarken, fiyat ya da sınır değiştiğinde, bir paketi satıştan kaldırırken.

**Kimler görür / değiştirebilir?** Yalnızca RECDx süper yöneticileri.

[[EKRAN: sy-paketler | Kiralama Paketleri, Kanban görünümü: paket kartları (kod, durum, fiyat, sınırlar) | Sol menüde Ticari & Yetki › Kiralama Paketleri]]

**Ekranın bölümleri:** Başlık ve "Abonelik paketlerinin detayları, fiyatlandırma, kotalar ve model yetkileri." açıklaması; **Yeni Paket Tanımla** düğmesi; **Kanban / Liste** seçici (varsayılan Kanban). Bu ekranda arama kutusu yoktur.

**Paket kartı (Kanban):** paket kodu, **AKTİF** / **PASİF**, ad, açıklama, "<fiyat> TRY / ay", **İnsan Kullanıcı**, **AI Ajan Personel**, **Aylık Kredi**, **Özel AI Ünvan Tanımlama** (Evet / Hayır).

**Liste sütunları:** **Paket Kodu & Adı** · **Aylık Fiyat** · **Limitler (İnsan / Ajan / Kredi)** · **Depolama** (GB) · **Özel Ünvan** (✓ İzinli / ✗ Kapalı) · **Durum** · **İşlemler**.

| Düğme | Ne yapar | Dikkat |
|---|---|---|
| **Yeni Paket Tanımla** | Paket penceresini önerilen değerlerle açar | — |
| **Düzenle** | Paket penceresini dolu açar | Değişiklik bu paketi kullanan tüm şirketleri etkiler |
| **Sil** (çöp kutusu) | "'<ad>' (<kod>) kiralama paketini silmek istediğinize emin misiniz? Not: Bu paket hiçbir müşteri tarafından alınmamışsa silinebilir." | Onay ister (**Evet, devam et**). Bir şirket ya da başvuru paketi kullanıyorsa silinmez. Geri alınamaz |

Silinemeyen pakette "⚠️ KİRALAMA PAKETİ SİLİNEMEZ! '<ad>' (<kod>) kiralama paketini kullanan veya talep eden N müşteri (N kayıtlı şirket, N başvuru) bulunmaktadır! …" mesajı çıkar. Satıştan kaldırmak için paketi silmek yerine **Paket Aktif** işaretini kaldırın.

#### Yeni Kiralama Paketi Tanımla / Paketi Düzenle

[[EKRAN: sy-m-paket | Paket penceresi: kod, ad, fiyat, sınırlar, Pakete dahil RECAi, Paket İzinleri, Odoo satış ürünü, RECDx uygulamaları | Kiralama Paketleri › bir pakette Düzenle; pencereyi aşağı kaydırarak iki görüntü alın]]

| Alan | Ne işe yarar | Nasıl doldurulur / seçenekler | Örnek | Zorunlu |
|---|---|---|---|---|
| **Paket Kodu** | Paketin tekil kodu | Büyük harf ve alt çizgi önerilir. Kayıttan sonra değiştirilemez | LOJISTIK_PRO | Evet |
| **Paket Adı** | Satışta ve şirket kartında görünen ad | — | Kurumsal Paket | Evet |
| **Aylık Fiyat (TRY)** | Aylık fiyat (KDV hariç) | Sayı; yeni pakette 25000 önerilir | 25000 | Hayır |
| **Aylık Kredi** | Her ay verilen kredi (ay sonunda kullanılmayan kısmı silinir) | Sayı; yeni pakette 3000 | 3000 | Hayır |
| **AI Ajan Personel** | Şirketin işe alabileceği en fazla AI personel | Sayı; yeni pakette 10 | 10 | Hayır |
| **İnsan Kullanıcı** | Şirketin tanımlayabileceği en fazla insan kullanıcı | Sayı; yeni pakette 10 | 10 | Hayır |
| **Eşzamanlı Proje** | Aynı anda açık olabilecek proje sayısı | Sayı; yeni pakette 5 | 5 | Hayır |
| **İşlem Kredisi** | **Aylık Kredi** alanıyla aynı değerdir; birini değiştirince diğeri de değişir | — | 3000 | Hayır |
| **MinIO Depolama (GB)** | Şirketin dosya depolama kotası | Sayı; yeni pakette 25 | 25 | Hayır |
| **Pakete dahil RECAi (N ad seçili)** | Şirketin AI personellerine seçebileceği RECAi adları | **RECAi Mergen** (Genel işler), **RECAi Hızlı** (Kısa ve hızlı yanıtlar), **RECAi Derin** (Derin analiz ve uzun metin). Yeni pakette Mergen ve Hızlı seçili gelir | RECAi Mergen, RECAi Hızlı | En az bir önerilir |
| **Dahil yetenekler** | Pakete dahil ek yetenekler | **RECAi Görsel** (Görsel ve ekran görüntüsü okuma), **RECAi Ses** (Toplantı ve ses kaydını yazıya dökme), **RECAi Okur** (Taranmış belge ve PDF okuma (OCR)) | RECAi Okur | Hayır |
| **Açıklama** | Paketin tanıtım metni | — | Orta ölçekli şirketler için | Hayır |
| **Özel AI Ünvan Tanımlama İzni Ver** | Şirket katalog dışında kendi unvanını oluşturabilir mi | İşaretli = evet | işaretli | — |
| **Paket Aktif** | Paket satışta mı | İşaretsiz paket satışa sunulmaz | işaretli | — |
| **Paket İzinleri** | Pakete göre açılan ek haklar | **AI personelin RECAi adını değiştirebilir** · **Ünvan rol promptunu değiştirebilir** · **Ünvanlara bilgi dokümanı yükleyebilir** | — | — |
| **AI personel başına en fazla öğrenme kaynağı** | Bir AI personele yüklenebilecek doküman ve kaynak sınırı | Sayı (0 ve üstü); varsayılan 20 | 20 | Hayır |
| **Odoo satış ürünü** | Bu paketle gelen başvuruda Odoo'daki satış kaydının hangi ürünle açılacağı | "Odoo ürünlerinde ara…" kutusuyla arayın, listeden "#<no> · <ürün> · <fiyat>" seçin. **↻** ("Odoo ürün listesini yenile") listeyi yeniler. Boş: "— Odoo ürünü bağlı değil —" | #12 · RECOrion Kurumsal · 25.000 TRY | Önerilir |
| **RECDx uygulamaları (Odoo)** — RECQmind / RECSlip | Müşteri "Paketime ekle" derse uygulamanın nasıl satılacağı | Her uygulama için **Teklif**: **Yok** / **İndirimli** / **Pakete dahil**. İndirimlide **İndirim (%)** (1–99, varsayılan 50). Yok dışındaki seçimlerde "<uygulama> için Odoo ürünü" seçilir | RECSlip: İndirimli, %50 | Hayır |

**Odoo satış ürünü altındaki bilgiler:**

- Ürün seçilmezse: "Ürün seçilmezse bu paketle gelen başvurular için Odoo'da satış kaydı açılamaz."
- Ürün seçilince: "Satış kaydı "<ürün>" ürünüyle açılır; satır fiyatı paketin aylık fiyatından alınır." Odoo fiyatı paket fiyatından farklıysa "Odoo liste fiyatı (…) paket fiyatından farklı." uyarısı eklenir.
- Ürün Odoo'da bulunamazsa listede "#<no> (Odoo listesinde bulunamadı)" görünür.

**RECDx uygulamaları açıklaması (ekranda):** "Müşteri "paketime ekle" derse Odoo siparişine seçilen ürün eklenir: indirimliyse ürünün Odoo fiyatından yüzde düşülür, dahilse 0 fiyatla. "Zaten kullanıyorum" diyen müşteriye yalnızca entegrasyon açılır."

| Düğme | Ne yapar | Dikkat |
|---|---|---|
| **Vazgeç** / **✕** | Kaydetmeden kapatır | — |
| **Paketi Kaydet** | Kaydeder: "✓ '<ad>' paketi oluşturuldu." / "✓ '<ad>' paketi güncellendi." | Düzenleme hemen bu paketteki tüm şirketlere uygulanır |

**Hata mesajları:**

| Mesaj | Anlamı | Ne yapmalı |
|---|---|---|
| "'<kod>' kodlu paket zaten mevcut." | Kod kullanılmış | Başka kod seçin |
| "Odoo'da <no> ID'li satılabilir bir ürün bulunamadı." | Seçilen ürün Odoo'da yok ya da satılamaz | Odoo'da ürünü kontrol edin, listeyi **↻** ile yenileyin |
| "Odoo'ya ulaşılamadığı için ürün doğrulanamadı. Lütfen daha sonra tekrar deneyin." | Odoo'ya bağlanılamadı | Dashboard'da Odoo durumunu kontrol edin |
| "En az bir RECAi adı seçin (seçilmezse RECAi Mergen kullanılır)." | Hiç RECAi adı seçili değil | En az bir ad işaretleyin |

**Adım adım örnek: yeni paket tanımlamak**

1. **Kiralama Paketleri** › **Yeni Paket Tanımla**.
2. **Paket Kodu**: "LOJISTIK_PRO", **Paket Adı**: "Lojistik Pro", **Aylık Fiyat**: 30000, **Aylık Kredi**: 4000.
3. Sınırlar: AI Ajan Personel 15, İnsan Kullanıcı 20, Eşzamanlı Proje 8, Depolama 50.
4. **Pakete dahil RECAi**: Mergen, Hızlı, Derin; **Dahil yetenekler**: RECAi Okur.
5. **Odoo satış ürünü**'nde "Lojistik Pro" ürününü arayıp seçin.
6. **RECDx uygulamaları**'nda RECSlip için **İndirimli**, %50 ve RECSlip'in Odoo ürününü seçin.
7. **Paketi Kaydet**. Paket resmi sitede ve şirket kartlarında seçilebilir olur.

> **Dikkat:** Paketten bir RECAi adını ya da yeteneği kaldırırsanız bu paketteki şirketler o adı ve yeteneği hemen kaybeder.

## İzin Kataloğu (RBAC)

### Sistem Yetki ve İzin Kataloğu

**Bu ekran ne işe yarar?** Sistemdeki tüm izinleri (kullanıcının yapabildiği tek tek işleri) listeler. Roller bu katalogdaki izinlerden oluşur. İzinler müşterinin menülerine göre 12 modüle ayrılır; Şirket Yönetimi menüleri kullanıcının izinlerine göre görünür, izni olmayan menüyü kullanıcı hiç görmez.

**Ne zaman kullanırım?** Bir iznin adını ya da açıklamasını müşterinin anlayacağı dille düzeltmek, hangi iznin hangi rollerde olduğunu görmek istediğinizde.

**Kimler görür / değiştirebilir?** Yalnızca RECDx süper yöneticileri. Şirket yöneticileri izinleri kendi rol tanımlama ekranlarında seçim için görür.

[[EKRAN: sy-izin-katalogu | İzin Kataloğu, Liste görünümü; modül süzgeci düğmeleri görünür | Sol menüde Ticari & Yetki › İzin Kataloğu (RBAC)]]

**Ekranın bölümleri:** Başlık ve "Modül bazlı yetkiler. Detayları inceleyebilir, güncelleyebilir veya yeni yetki tanımlayabilirsiniz." açıklaması; **Yeni İzin Tanımla**; **Kanban / Liste** seçici (varsayılan Liste); arama kutusu; modül süzgeci; liste.

| Alan | Ne işe yarar | Nasıl doldurulur / seçenekler | Örnek | Zorunlu |
|---|---|---|---|---|
| **İzin kodu veya adı ara...** | Listeyi süzer | Kod, ad ya da açıklamadan bir parça | kullanıcı | Hayır |
| Modül süzgeci | Yalnızca bir modülün izinlerini gösterir | **TÜM MODÜLLER**, Şirket & Platform, Genel Bakış & Raporlar, Kullanıcılar & Roller, AI Personel, Organizasyon, Kurum Zekâsı, Entegrasyon & Otomasyon, Kredi & Kullanım, Projeler & İş Akışı, Sohbet & İletişim, Kurum Hafızası, Bağlantılarım | AI Personel | Hayır |

**Liste sütunları:** **Yetki Kodu** (iznin teknik kodu) · **Modül** · **İzin Adı & Açıklama** · **Varsayılan Roller** (bu izni içeren sistem rollerinin adları) · **İşlemler**. Kanban kartında ayrıca, kodda henüz kullanılmayan izinler için "Henüz bir işleme bağlı değil: rol listesinde görünür, sistemde bir şeyi açmaz." uyarısı çıkar.

**Sistemle gelen izinler:**

| Modül | İzin | Ne sağlar | İşleme bağlı mı |
|---|---|---|---|
| Şirket & Platform | Tam Sistem Yönetimi | Yalnızca RECDx süper yöneticileri. Müşteri şirketlere verilemez. | Evet |
| Şirket & Platform | Şirket Bilgilerini Görüntüleme | Şirket, departman, ünvan, kullanıcı ve AI personel listelerini görme. Her kullanıcıda bulunur. | Evet |
| Şirket & Platform | Şirket Ayarlarını Yönetme | RECDx uygulama tercihleri ve genel şirket ayarları (Şirket Profili dahil). Şirket yöneticisinin temel izni. | Evet |
| Genel Bakış & Raporlar | Şirket Geneli Pano | Şirket Yönetimi > Genel Bakış: tüm şirketin proje, adım, kredi ve AI personel göstergeleri. | Evet |
| Genel Bakış & Raporlar | Departman Panosu | Yalnızca kendi departmanının panosunu görme (Work Space > Pano). | Evet |
| Genel Bakış & Raporlar | Maliyet ve Bütçe Bilgilerini Görme | Panolardaki parasal göstergeler: token maliyeti, maliyet dağılımı, tahmini tasarruf, bütçe ve gerçekleşen. | Evet |
| Kullanıcılar & Roller | Kullanıcı Ekleme | Kullanıcı Yönetimi'nde yeni kullanıcı tanımlama (şifre belirleme e-postası gider). | Evet |
| Kullanıcılar & Roller | Kullanıcı Düzenleme ve Silme | Kullanıcının departman, ünvan, rol, ek izin ve durumunu değiştirme, silme; kişi günlük maliyetini görme. | Evet |
| Kullanıcılar & Roller | Şirkete Özel Rol Tanımlama | Şirkete özel yetki rolü oluşturma. | Evet |
| Kullanıcılar & Roller | Rol Düzenleme | Şirkete özel rollerin adını, açıklamasını ve izinlerini değiştirme. | Evet |
| Kullanıcılar & Roller | Rol Silme | Şirkete özel rolleri silme (rol atanmış kullanıcı yoksa). | Evet |
| AI Personel | AI Personel İşe Alma | AI Personel İşe Al sihirbazı ve RECAi ile ünvan araştırması. | Evet |
| AI Personel | AI Personel Ayarları ve Bilgi Kaynakları | AI personelin bilgilerini, rol promptunu düzenleme; bilgi dokümanı, web ve video kaynağı ekleme, onaylama. | Evet |
| AI Personel | AI Personeli İşten Çıkarma | AI personeli işten çıkarma, yeniden işe alma ve silme. | Evet |
| AI Personel | Ünvan Tanımlama | Şirket ünvanlarını ve rol promptlarını oluşturma, düzenleme, silme. | Evet |
| Organizasyon | Departman Yönetimi | Departman oluşturma, katalogdan ekleme, düzenleme ve silme. | Evet |
| Kurum Zekâsı | Sektörel Manifesto Yönetimi | Şirketin sektör ve meslek bilgilerini ve kurumsal manifestoyu düzenleme, RECAi'ye yazdırma. | Evet |
| Kurum Zekâsı | Beyin AI Ayarları | Planlamada kullanılacak RECAi kademesini seçme. | Evet |
| Kurum Zekâsı | Mevzuat Paketlerini Açma/Kapatma | Şirkete mevzuat bilgi paketlerini açma ve kapatma. | Evet |
| Entegrasyon & Otomasyon | Bağlantı Yönetimi | Dış sistem bağlantısı ekleme, deneme, AI personele araç yetkisi verme, aktarım kurallarını belirleme (RECSlip v2 aylık süreç kurulumu da bu izni ister). | Evet |
| Entegrasyon & Otomasyon | Eşleme Stüdyosu | Ortak kayıtların dış sistem alanlarına eşlemesini hazırlama, deneme ve onaylama. | Evet |
| Entegrasyon & Otomasyon | Otomasyon Kuralları | Otomasyon kuralı ve hazır kural kurma, sınama, durdurma, çalışma günlüğü. | Evet |
| Entegrasyon & Otomasyon | Dış Sisteme Yazma Onayı | Aktarım ve araç çağrısı onayı (ikinci onay dahil), aktarım günlüğü, başarısız aktarımı yeniden deneme. | Evet |
| Kredi & Kullanım | Kredi ve Kullanımı Görme | Kredi ve Kullanım ekranı: aylık hak, kullanılan, ek kredi bakiyesi, kullanım dökümü. | Evet |
| Projeler & İş Akışı | Proje / Case Açma | Yeni proje veya Case; şablondan ve toplantıdan proje oluşturma. | Evet |
| Projeler & İş Akışı | Tüm Projeleri Yönetme | Şirketin bütün projelerini görme ve yönetme (yönetici olmadığı projeler dahil): planlama, ekip, başlatma, kapanış. | Evet |
| Projeler & İş Akışı | Şirket Şablonlarını Yönetme | Projeyi şablon olarak kaydetme ve başkasının şirket şablonunu düzenleme. | Evet |
| Projeler & İş Akışı | İş Adımı Ekleme | Erişebildiği projelere yeni iş akışı görevi ekleme. | Evet |
| Projeler & İş Akışı | İş Adımı Onaylama (Vekâleten) | Erişebildiği projelerde, onaylayıcısı olmasa da onay bekleyen adımı onaylama. | Evet |
| Projeler & İş Akışı | Revizyon İsteme (Vekâleten) | Erişebildiği projelerde, onaylayıcısı olmasa da adım için revizyon isteme. | Evet |
| Sohbet & İletişim | Sohbet ve Görev İletişimi | Görev sohbetine ve Beyin AI sohbetine yazma, dosya ekleme. | Evet |
| Sohbet & İletişim | Ajanlar Arası Konuşmaları İzleme | AI personelin kendi aralarındaki konuşmaları görme (Çalışma Alanı'ndaki "Ajanlar arası" görünümü). | Evet |
| Kurum Hafızası | Kurum Hafızasında Arama | Onaylı kurum hafızasında arama. | Evet |
| Kurum Hafızası | Kurum Hafızasına Ekleme ve Onaylama | Onaylanan çıktı ve proje bilgisini kurum hafızasına aktarma, bekleyenleri onaylama veya reddetme. | Evet |
| Kurum Hafızası | Kurum Hafızasından Geri Alma | Onaylanmış kurum hafızası bilgisini geri alma. | Evet |
| Bağlantılarım | Kişisel Erişim Anahtarı | Bağlantılarım: Claude, Cursor gibi MCP istemcileri için kişisel erişim anahtarı oluşturma. | Evet |

Katalogdaki bütün izinler bir işleme bağlıdır. Yeni bir izin eklenirse kodda denetlenene kadar "İşleme bağlı: Hayır" olarak görünür ve sistemde bir şeyi açmaz.

| Düğme | Ne yapar | Dikkat |
|---|---|---|
| **Yeni İzin Tanımla** | İzin penceresini açar | Yeni iznin bir işe yaraması için yazılımda karşılığının geliştirilmesi gerekir |
| **Düzenle** | İzin penceresini dolu açar | — |
| **Sil** (çöp kutusu) | "'<ad>' (<kod>) iznini silmek istediğinize emin misiniz?" sonrası siler | Onay ister (**Evet, devam et**). Geri alınamaz. Sistemle gelen izinleri silmeyin |

#### Yeni İzin Tanımla / İzin Tanımını Düzenle

[[EKRAN: sy-m-izin | İzin penceresi: Yetki Kodu, Modül, İzin Adı, Açıklama | İzin Kataloğu › bir izinde Düzenle]]

| Alan | Ne işe yarar | Nasıl doldurulur / seçenekler | Örnek | Zorunlu |
|---|---|---|---|---|
| **Yetki Kodu** | İznin teknik kodu (yazılım bu kodu denetler) | "konu:işlem" biçiminde kısa teknik ad (ekrandaki örnek: agent:deploy). Kayıttan sonra değiştirilemez | agent:deploy | Evet |
| **Modül** | İznin görüneceği modül | 12 modülden biri | AI Personel | Evet |
| **İzin Adı** | Ekranlarda görünen ad | Müşterinin anlayacağı dille | AI Personeli Başlatma | Evet |
| **Açıklama** | İznin ne sağladığı | Bir iki cümle | Bu yetkiye sahip roller yapay zeka personellerini devreye alabilir. | Hayır |

Düğmeler: **Vazgeç**, **Kaydet** ("✓ '<ad>' yetkisi eklendi." / "✓ '<ad>' güncellendi."). Aynı kod varsa "'<kod>' kodlu izin zaten mevcut." hatası çıkar.

> **Dikkat:** İzin Kataloğu yazılımla birlikte gelen bir listedir. Yeni kod eklemek tek başına hiçbir menüyü ya da düğmeyi açmaz. Yeni bir yetki ihtiyacını Odoo'da İSTEK olarak açın; geliştirme ekibi izni yazılıma bağlar.

## Yetki Rolleri

### Yetki Rolleri Yönetimi

**Bu ekran ne işe yarar?** Tüm şirketlerde hazır gelen **sistem rollerini** tanımlar ve her rolün hangi izinlerden oluştuğunu belirlersiniz. Şirket yöneticileri kullanıcılarına bu rollerden birini atar (ayrıca kendi şirketlerine özel rol de tanımlayabilirler; şirkete özel roller burada görünmez).

**Ne zaman kullanırım?** Bir sistem rolüne izin eklemek ya da çıkarmak, rol açıklamasını düzeltmek ya da tüm müşterilere yeni bir hazır rol sunmak istediğinizde.

**Kimler görür / değiştirebilir?** Yalnızca RECDx süper yöneticileri. Müşteriler RECDx'e ait süper yönetici rolünü ve rollerin şirket başına kullanıcı sayılarını görmez.

[[EKRAN: sy-yetki-rolleri | Yetki Rolleri, Kanban görünümü: dört sayı kutusu ve rol kartları (SİSTEM ROLÜ rozeti, izin sayısı) | Sol menüde Ticari & Yetki › Yetki Rolleri]]

**Ekranın bölümleri:**

1. Başlık **Yetki Rolleri Yönetimi (RBAC Roles)** ve "Kullanıcı ve aktörlerin sistem üzerindeki Yetki Rollerini tanımlayın, İzin Kataloğundan yetkileri çoklu olarak eşleştirin." açıklaması.
2. **Yeni Rol Tanımla**, **Kanban / Liste** seçici (varsayılan Kanban), arama kutusu ("Rol adı veya izin ara...").
3. Dört sayı kutusu: **Tanımlı Yetki Rolü**, **Sistem / Global Roller**, **İzin Kataloğu Havuzu** (N İzin), **Atanmış Aktör / Personel** (tüm şirketlerde bu rollere atanmış kullanıcı sayısı).
4. Rol kartları ya da tablo.

**Rol kartı:** **🛡️ SİSTEM ROLÜ** / **🏢 ÖZEL ROL** rozeti, "N Aktör" ya da "Atanmamış", rol adı, açıklama, **İzin Kataloğu Yetkileri** ("N İzin Seçili", ilk 6 izin, "+N diğer izin").

**Liste sütunları:** **Rol Adı & Kapsam** · **Rol Açıklaması** · **Seçili İzin Kataloğu Yetkileri** · **Bağlı Aktörler** · **Oluşturulma Tarihi** · **İşlemler**.

**Sistemle gelen 11 rol:**

| Rol | Temel rol | Ne için | İzinleri |
|---|---|---|---|
| **Süper Yönetici (Platform Admin)** | Süper Yönetici | RECDx süper yöneticisi. Yalnızca RECDx ana şirketinde kullanılır; müşterilere görünmez | Tüm izinler. Bu rolün izinleri ve temel rolü değiştirilemez |
| **Şirket Yöneticisi** | Şirket Yöneticisi | Şirketin tüm yönetim ve çalışma yetkileri. Şirkette en az bir aktif şirket yöneticisi bulunmalıdır | Müşteriye verilebilen tüm izinler |
| **Proje Yöneticisi** | Proje Yöneticisi | Proje ve Case açar, RECAi ile planlar, ekip kurar, AI personel işe alır, adımları onaylar, kurum hafızasına aktarır | Temel izinler (aşağıda) + Departman Panosu, AI Personel İşe Alma, Proje / Case Açma, Tüm Projeleri Yönetme, Şirket Şablonlarını Yönetme, İş Adımı Onaylama (Vekâleten), Revizyon İsteme (Vekâleten), Ajanlar Arası Konuşmaları İzleme, Kurum Hafızasına Ekleme ve Onaylama, Kurum Hafızasından Geri Alma |
| **Uzman Kullanıcı** | Uzman Kullanıcı | Ekibinde olduğu projelerde çalışır: atanan adımlar, sohbet, hafızada arama, kişisel erişim anahtarı | Yalnızca temel izinler |
| **Personel ve Organizasyon Yöneticisi** | Yok | İnsan kullanıcıları, AI personeli, departman ve ünvanları yönetir | Temel izinler + Departman Panosu, Kullanıcı Ekleme, Kullanıcı Düzenleme ve Silme, AI Personel İşe Alma, AI Personel Ayarları ve Bilgi Kaynakları, AI Personeli İşten Çıkarma, Ünvan Tanımlama, Departman Yönetimi |
| **Yapay Zeka ve Ajan Lideri** | Yok | AI personelin işe alımı, eğitimi ve kalitesinden; manifesto, Beyin AI ve mevzuat ayarlarından sorumludur | Temel izinler + AI Personel İşe Alma, AI Personel Ayarları ve Bilgi Kaynakları, AI Personeli İşten Çıkarma, Ünvan Tanımlama, Sektörel Manifesto Yönetimi, Beyin AI Ayarları, Mevzuat Paketlerini Açma/Kapatma, Tüm Projeleri Yönetme, Ajanlar Arası Konuşmaları İzleme, Kurum Hafızasına Ekleme ve Onaylama, Kurum Hafızasından Geri Alma |
| **Entegrasyon Yöneticisi** | Yok | Dış sistem bağlantıları, eşlemeler, otomasyon kuralları ve dış sisteme yazma onaylarından sorumludur (BT) | Temel izinler + Bağlantı Yönetimi, Eşleme Stüdyosu, Otomasyon Kuralları, Dış Sisteme Yazma Onayı |
| **Finans ve Raporlama Sorumlusu** | Yok | Şirket panosu, maliyet ve bütçe, kredi kullanımı; tutar eşiğini aşan aktarımların onayı (muhasebe ekibi için) | Temel izinler + Şirket Geneli Pano, Departman Panosu, Maliyet ve Bütçe Bilgilerini Görme, Kredi ve Kullanımı Görme, Dış Sisteme Yazma Onayı |
| **Kalite ve Onay Sorumlusu** | Yok | Erişebildiği projelerde adım çıktılarını onaylar veya revizyon ister; kurum hafızasını denetler | Temel izinler + İş Adımı Onaylama (Vekâleten), Revizyon İsteme (Vekâleten), Ajanlar Arası Konuşmaları İzleme, Kurum Hafızasına Ekleme ve Onaylama, Kurum Hafızasından Geri Alma |
| **Operasyon Yöneticisi** | Yok | Şirket ayarları, pano, kredi ve operasyonel projelerin genel yönetimi | Temel izinler + Şirket Ayarlarını Yönetme, Şirket Geneli Pano, Departman Panosu, Maliyet ve Bütçe Bilgilerini Görme, Kredi ve Kullanımı Görme, Sektörel Manifesto Yönetimi, Mevzuat Paketlerini Açma/Kapatma, Departman Yönetimi, Proje / Case Açma, Tüm Projeleri Yönetme |
| **Güvenlik ve Uyum Denetçisi** | Yok | Salt okunur denetim: panolar, maliyet ve kredi, ajanlar arası konuşmalar | Şirket Bilgilerini Görüntüleme, Kurum Hafızasında Arama, Şirket Geneli Pano, Departman Panosu, Maliyet ve Bütçe Bilgilerini Görme, Kredi ve Kullanımı Görme, Ajanlar Arası Konuşmaları İzleme |

**Temel izinler** (Güvenlik ve Uyum Denetçisi dışındaki tüm müşteri rollerinde bulunur): Şirket Bilgilerini Görüntüleme, İş Adımı Ekleme, Sohbet ve Görev İletişimi, Kurum Hafızasında Arama, Kişisel Erişim Anahtarı.

| Düğme | Ne yapar | Dikkat |
|---|---|---|
| **Yeni Rol Tanımla** | Boş rol penceresini açar | — |
| **Düzenle & İzinler** | Rol penceresini dolu açar | Değişiklik bu role bağlı tüm şirketlerdeki kullanıcıları hemen etkiler |
| **Sil** (çöp kutusu, "Rolü Sil") | "'<ad>' yetki rolünü silmek istediğinize emin misiniz?" sonrası siler | Onay ister (**Evet, devam et**). Role atanmış kullanıcı varsa silinmez. Geri alınamaz |

#### Yeni Yetki Rolü Tanımla / Yetki Rolünü Düzenle

Başlık "Yeni Yetki Rolü Tanımla (RBAC)" ya da "Yetki Rolünü Düzenle: <ad>"; alt başlık "Kullanıcı ve aktör yetki sınırlarını belirleyin, İzin Kataloğundan çoklu yetkileri seçin."

[[EKRAN: sy-m-rol | Rol penceresi: Rol Adı, Sistem Rolü kutusu, Temel Rol, açıklama, izin seçim listesi ve seçilen izin etiketleri | Yetki Rolleri › "Entegrasyon Yöneticisi" kartında Düzenle & İzinler]]

| Alan | Ne işe yarar | Nasıl doldurulur / seçenekler | Örnek | Zorunlu |
|---|---|---|---|---|
| **Rol Adı \*** | Rolün adı (müşteriler bu adı görür) | Tekil ad | Depo ve Sevkiyat Sorumlusu | Evet |
| **Rol Türü / Kapsamı** — **Sistem / Global Rol Olarak Tanımla** | Rolün sistem rolü olarak işaretlenmesi | İşaretli = SİSTEM ROLÜ rozeti; işaretsiz = ÖZEL ROL | işaretli | — |
| **Temel Rol** | Rolün sistemdeki ana davranışı | **Yok (yalnızca seçilen izinler)** / **Şirket Yöneticisi (konsol açılır, son yönetici korunur)** / **Proje Yöneticisi** / **Uzman Kullanıcı**. Süper Yönetici rolünde bu alan kilitlidir | Yok (yalnızca seçilen izinler) | Hayır |
| **Rol Açıklaması** | Rolün sorumlulukları | — | Depo ve sevkiyat projelerini izler | Hayır |
| **İzin Kataloğu Yetkileri (Çoklu Seçim)** — "N / N İzin Seçildi" | Rolün izinleri | Listede izne tıklayarak işaretleyin. Üstte arama kutusu ("İzin ara (örn: role:create, agent, chat)...") ve modül düğmeleri (**TÜMÜ** ve 12 modül) vardır. Seçilenler etiket olarak görünür, **×** ile çıkarılır | 9 izin | Hayır |

| Düğme | Ne yapar | Dikkat |
|---|---|---|
| **✓ Listelenenleri Seç** | Arama ve modül süzgecine uyan tüm izinleri ekler | — |
| **Tümünü Seç (N)** | Tüm izinleri ekler | Müşteri rolüne "Tam Sistem Yönetimi" iznini vermeyin |
| **Temizle** | Tüm seçimleri kaldırır | — |
| **Vazgeç** / **✕** | Kaydetmeden kapatır | — |
| **Yetki Rolünü Oluştur** (düzenlemede **Değişiklikleri Kaydet**) | Kaydeder: "✓ '<ad>' yetki rolü oluşturuldu." / "… güncellendi." | Temel rol değişirse bu role bağlı kullanıcıların sistemdeki ana rolü de değişir |

**Hata mesajları:**

| Mesaj | Anlamı | Ne yapmalı |
|---|---|---|
| "Lütfen rol adını giriniz." | Ad boş | Ad yazın |
| "'<ad>' adında bir yetki rolü zaten mevcut." / "…başka bir rol mevcut." | Ad kullanılmış | Farklı ad seçin |
| "RECDx süper yönetici rolünün izinleri değiştirilemez." | Süper yönetici rolü korunur | — |
| "Bu yetki rolüne atanmış N adet aktif kullanıcı/aktör bulunmaktadır. Silmeden önce kullanıcıların rollerini değiştiriniz." | Rol kullanılıyor | Şirketlerden rol değişikliğini isteyin ya da rolü silmeyin |
| "Temel rol Şirket Yöneticisi, Proje Yöneticisi, Uzman Kullanıcı veya boş olabilir." | Geçersiz temel rol | Listeden seçin |

> **Örnek:** Birçok müşteri muhasebecisinin dış sisteme yazma onayı vermesi gerekiyor ama kredi ekranını görmemesi isteniyor. Yeni bir sistem rolü açmak yerine önce mevcut **Finans ve Raporlama Sorumlusu** rolünü inceleyin; ihtiyaç farklıysa şirket yöneticisi kendi şirketine özel rol tanımlayabilir.

> **Dikkat:** Sistem rolündeki her değişiklik bütün müşterilerde o role sahip kullanıcıları etkiler. Bir izni kaldırmadan önce müşterilerin bu izne bağlı menüyü kaybedeceğini unutmayın (izni olmayan kullanıcı o menüyü hiç görmez).


# İletişim & Otomasyon

## E-Posta Şablonları

### HTML E-Posta Şablonları & Canlı Editör

**Bu ekran ne işe yarar?** Sistemin müşterilere gönderdiği tüm e-postaların (aktivasyon, paket hatırlatma, başvuru alındı/reddedildi, şifre sıfırlama, doğrulama kodu vb.) görünümünü ve metnini yönetirsiniz. Şablonları sürükle-bırak görsel editörle ya da HTML koduyla düzenler, önizler ve kendinize test olarak gönderirsiniz.

**Ne zaman kullanırım?** Bir e-postanın metnini, logosunu ya da düğmesini değiştirmek; yeni bir kampanya e-postası hazırlamak; müşteri "e-posta bozuk görünüyor" dediğinde kontrol etmek için.

**Kimler görür / değiştirebilir?** Yalnızca RECDx süper yöneticileri.

[[EKRAN: sy-eposta-sablonlari | E-Posta Şablonları, Kanban görünümü: şablon kartları, değişken rozetleri ve küçük önizleme | Sol menüde İletişim & Otomasyon › E-Posta Şablonları]]

**Ekranın bölümleri:** Başlık **HTML E-Posta Şablonları & Canlı Editör** ve "RECDx kurumsal logosunu içeren Hoş Geldiniz, 3 Ay Bitiş Hatırlatıcı ve özel e-posta şablonları." açıklaması; **+ Yeni Şablon Oluştur**; **Kanban / Liste** seçici (varsayılan Kanban); arama kutusu; şablonlar.

| Alan | Ne işe yarar | Nasıl doldurulur / seçenekler | Örnek | Zorunlu |
|---|---|---|---|---|
| **Şablon kodu veya konu ara...** | Listeyi süzer | Şablon adı, kodu ya da konusundan bir parça | hatırlat | Hayır |

**Şablon kartı:** şablon kodu, **AKTİF** / **PASİF**, ad, **Konu:**, **DİNAMİK DEĞİŞKENLER:** (ör. {{company_name}}) ve e-postanın küçük önizlemesi.

**Liste sütunları:** **Şablon Kodu** · **Şablon Adı** · **E-Posta Konusu (Subject)** · **Dinamik Değişkenler** (ilk 4 ve "+N") · **Durum** · **İşlemler**.

**Sistemin temel şablonları** (silinemez):

| Şablon kodu | Ne zaman gönderilir |
|---|---|
| WELCOME_CUSTOMER | Hoş geldiniz e-postası |
| ACCOUNT_ACTIVATED | Başvuru onaylandığında ve **Hoş Geldin Maili** düğmesiyle (şifre belirleme bağlantılı aktivasyon e-postası) |
| PACKAGE_EXPIRATION_REMINDER | Paket bitişi yaklaşınca (zamanlayıcı ve **Hatırlatıcı Mail** düğmesi) |
| EMAIL_VERIFICATION_CODE | Resmi sitede başvuru sırasında e-posta doğrulama kodu |
| LEAD_RECEIVED | Başvuru alındığında müşteriye |
| LEAD_REJECTED | Başvuru reddedildiğinde müşteriye (gerekçeyle) |
| PASSWORD_RESET | **Şifremi unuttum** ile şifre belirleme bağlantısı |
| ADMIN_NEW_LEAD | Yeni başvuru geldiğinde RECDx'e bildirim |

**Dinamik değişkenler** e-posta gönderilirken gerçek bilgiyle doldurulan yer tutuculardır. Örneğin {{company_name}} şirket adına, {{contact_name}} yetkili adına, {{plan_name}} paket adına, {{package_expiry_date}} bitiş tarihine, {{days_remaining}} kalan güne, {{login_email}} giriş e-postasına, {{password_instruction}} şifre açıklamasına, {{action_url}} ve {{login_url}} bağlantılara dönüşür.

| Düğme | Ne yapar | Dikkat |
|---|---|---|
| **+ Yeni Şablon Oluştur** | Editörü hazır bloklarla (başlık, karşılama, açıklama, paket özeti, giriş bilgileri, düğme, ayırıcı, alt bilgi) açar; konu "RECDx \| RECOrion Kurumsal Bildirim" gelir | — |
| **Düzenle & Önizle** | Şablonu editörde açar | — |
| **Test** (Liste'de gönder simgesi; "Test E-postası Gönder") | Alıcı adresi sorar (varsayılan kendi e-postanız) ve kayıtlı şablonu örnek verilerle gönderir | Gerçek bir e-posta gönderir; yalnız kendi ya da test adresinize gönderin |
| **Sil** (çöp kutusu) | "'<ad>' (<kod>) e-posta şablonunu silmek istediğinize emin misiniz? Not: Bu şablon aktif zamanlayıcılarda veya sistem akışında kullanılmıyorsa silinebilir." | Onay ister (**Evet, devam et**). Temel şablonlar ve zamanlayıcıda kullanılan şablonlar silinemez. Geri alınamaz |

**Hata mesajları:**

| Mesaj | Anlamı | Ne yapmalı |
|---|---|---|
| "⚠️ E-POSTA ŞABLONU SİLİNEMEZ! '<ad>' (<kod>) sistemin temel e-posta şablonudur…" | Temel şablon | Silmek yerine düzenleyin |
| "…şablonu şu anda aktif zamanlayıcılar ('<kural>') tarafından kullanılmaktadır! …" | Zamanlayıcıda kullanılıyor | Önce zamanlayıcıyı değiştirin ya da silin |
| "⚠️ Test E-Postası Gönderilemedi! … test e-postası '<adres>' adresine iletilemedi. Lütfen sunucu SMTP ayarlarını kontrol ediniz." | E-posta sunucusu sorunu | Teknik ekibe bildirin |
| "'<kod>' kodlu e-posta şablonu zaten mevcut." | Kod kullanılmış | Başka kod seçin |

#### Yeni E-Posta Şablonu Tasarla / Şablonu Düzenle

Başlık "Yeni E-Posta Şablonu Tasarla" ya da "'<ad>' Şablonunu Düzenle"; alt başlık "Sürükle-bırak görsel blok editörü, canlı e-posta önizlemesi ve modal içi test gönderim altyapısı." Üstte iki sekme: **🎨 Görsel Sürükle-Bırak** ve **💻 HTML Kaynak Kodu**.

[[EKRAN: sy-m-eposta-gorsel | Şablon editörü, Görsel Sürükle-Bırak sekmesi: solda Bloklar, ortada tuval, sağda Blok ayarları | E-Posta Şablonları › bir şablonda Düzenle & Önizle]]

**Üst alanlar:**

| Alan | Ne işe yarar | Nasıl doldurulur / seçenekler | Örnek | Zorunlu |
|---|---|---|---|---|
| **Şablon Kodu \*** | Şablonun tekil kodu (büyük harfe çevrilir) | Büyük harf ve alt çizgi. Kayıttan sonra değiştirilemez | KASIM_KAMPANYA | Evet |
| **Şablon Adı \*** | Listede görünen ad | — | Kasım Ek Kredi Kampanyası | Evet |
| **E-Posta Konusu (Subject) \*** | Gelen kutusunda görünen konu | Değişken kullanabilirsiniz | {{company_name}} için Kasım'a özel ek kredi | Evet |
| **Dinamik Değişkenler:** | Değişken düğmeleri | Görsel sekmede tıklayınca değişken panoya kopyalanır ("'{{…}}' panoya kopyalandı! …"); HTML sekmesinde HTML'in sonuna eklenir | {{company_name}} | — |
| **Şablon Aktif** | Şablonun kullanımda olması | İşaretli = aktif | işaretli | — |

**Görsel editör üç bölümdür:**

1. **Bloklar** ("tıkla veya sürükle"). Bloğa tıklarsanız seçili bloğun altına eklenir; sürüklerseniz bıraktığınız yere eklenir. Gruplar:
   - *Başlık ve metin:* **Kurumsal Başlık & Logo**, **Başlık**, **Karşılama Metni**, **Açıklama / Duyuru Paragrafı (Body)**, **Bilgi / Uyarı Kutusu**
   - *Bilgi kartları:* **Doğrulama Kodu Kutusu**, **Paket & Süre Özeti**, **Yönetici Giriş Bilgileri Kartı**
   - *Buton ve görsel:* **Aksiyon Butonu (CTA)**, **Özel Görsel / Logo / Banner**, **Ayırıcı Çizgi**
   - *Alt bilgi ve gelişmiş:* **Kurumsal Alt Bilgi & İmza**, **Serbest HTML Bölümü**
2. **Şablon (N blok)** tuvali. Bloklar sırayla görünür; tutamaktan sürükleyerek sıralarsınız. Her blokta **Yukarı taşı**, **Aşağı taşı**, **Çoğalt**, **Sil** simgeleri; üstte **Geri al** ve **Yinele**. Tuval boşsa "Soldan bir blok sürükleyip buraya bırakın veya tıklayarak ekleyin."
3. Sağ panel: **Blok ayarları** ve **Önizleme** sekmeleri.

**Blok ayarları** seçili bloğa göre değişir:

| Blok | Ayarlar |
|---|---|
| Kurumsal Başlık & Logo | Alt başlık, Logo adresi (URL), Yazı rengi, Arka plan, Yazı boyutu |
| Başlık | Başlık, Hizalama (Sola / Ortaya), Yazı rengi, Yazı boyutu |
| Karşılama Metni | Karşılama metni, Yazı rengi, Arka plan, Yazı boyutu |
| Açıklama / Duyuru Paragrafı (Body) | Paragraf, Görsel adresi (isteğe bağlı), renk ve boyut |
| Bilgi / Uyarı Kutusu | Metin, Tür (Bilgi / Uyarı / Başarılı / Kritik) |
| Doğrulama Kodu Kutusu | Kod (değişken), Not |
| Paket & Süre Özeti | Paket, Bitiş tarihi, Kalan gün |
| Yönetici Giriş Bilgileri Kartı | Kullanıcı e-postası, Şifre açıklaması (açık şifre yazmayın) |
| Aksiyon Butonu (CTA) | Buton yazısı, Bağlantı (URL veya değişken) |
| Özel Görsel / Logo / Banner | Görsel adresi (URL), Açıklama |
| Ayırıcı Çizgi | Ayarı yok ("Bu bloğun ayarı yok.") |
| Kurumsal Alt Bilgi & İmza | Alt bilgi metni, Görsel adresi (isteğe bağlı), renk ve boyut |
| Serbest HTML Bölümü | HTML |

Ayarlar panelinin altındaki **Değişken ekle** düğmeleri değişkeni imlecin bulunduğu metin alanına ekler ("Önce bir metin alanına tıklayın; değişken imlecin olduğu yere eklenir."). Renk alanlarında renk seçici ve "Varsayılan" seçeneği vardır.

**Önizleme** sekmesinde e-postanın son hâli görünür; **Masaüstü** ve **Telefon** simgeleriyle iki genişlikte bakarsınız.

[[EKRAN: sy-m-eposta-html | Şablon editörü, HTML Kaynak Kodu sekmesi: solda HTML Kod Editörü, sağda Canlı E-Posta Önizlemesi | Şablon editöründe "💻 HTML Kaynak Kodu" sekmesine tıklayın]]

**HTML Kaynak Kodu** sekmesinde **HTML Kod Editörü** (e-postanın ham HTML'i; zorunlu) ve yanında **Canlı E-Posta Önizlemesi (True Render)** bulunur. HTML'i elle değiştirip görsel sekmeye dönerseniz bloklar güncel HTML'den yeniden oluşturulur.

| Düğme | Ne yapar | Dikkat |
|---|---|---|
| **Test E-postası Gönder** | Alıcı adresi sorar; kayıtlı şablonda pencerede şu an gördüğünüz konu ve içerikle (kaydetmeden) gönderir. Yeni şablonda önce şablonu kaydeder, sonra gönderir | Yeni şablonda kod, ad ve konu dolu olmalı ("Lütfen önce şablon kodu, adı ve konusunu doldurunuz.") |
| **Vazgeç** / **✕** | Kaydetmeden kapatır | Değişiklikler kaybolur |
| **Şablonu Kaydet** | Kaydeder: "✓ '<ad>' e-posta şablonu oluşturuldu." / "… güncellendi." | Kaydedilen şablon bir sonraki gönderimden itibaren kullanılır |

Test e-postasında değişkenler örnek verilerle doldurulur (ör. şirket "Örnek Teknoloji A.Ş.", yetkili "Ayşe Yılmaz", paket "RECOrion Kurumsal Pro", kod "123456").

**Adım adım örnek: hatırlatma e-postasının metnini değiştirmek**

1. **E-Posta Şablonları** › PACKAGE_EXPIRATION_REMINDER kartında **Düzenle & Önizle**.
2. Tuvalde **Açıklama / Duyuru Paragrafı (Body)** bloğuna tıklayın; sağda **Paragraf**'ı düzeltin. Kalan günü göstermek için metne tıklayıp **Değişken ekle** › {{days_remaining}}.
3. **Önizleme** › **Telefon** ile dar ekranda bakın.
4. **Test E-postası Gönder** › kendi e-postanızı yazın › **Tamam**. Gelen kutunuzu kontrol edin.
5. **Şablonu Kaydet**.

> **Dikkat:** **Yönetici Giriş Bilgileri Kartı**'na asla açık şifre yazmayın. Sistem e-postayla şifre göndermez; yönetici şifresini bağlantıdan belirler.

## Zamanlayıcılar (Schedules)

### Otomatik Bildirim Zamanlayıcıları

**Bu ekran ne işe yarar?** Otomatik e-posta kurallarını yönetirsiniz. İki tür kural çalışır:

- **Müşteri Kayıt Olduğunda (Tek Sefer):** Başvuru onaylanınca aktivasyon e-postasının gönderilip gönderilmeyeceğini belirler. Bu kural pasifse aktivasyon e-postası gitmez.
- **Paket Bitişine 3 Ay Kala (Periyodik):** Paket bitişine belirlenen gün sayısı (varsayılan 90) kalan aktif şirketlere, belirlenen sıklıkta (varsayılan 15 günde bir) hatırlatma e-postası gönderir. Sistem bu kuralları her gün kendiliğinden çalıştırır.

**Ne zaman kullanırım?** Hatırlatma sıklığını ya da gönderilen şablonu değiştirmek, aktivasyon e-postalarını geçici olarak durdurmak, bir kuralı hemen çalıştırmak istediğinizde.

**Kimler görür / değiştirebilir?** Yalnızca RECDx süper yöneticileri.

[[EKRAN: sy-zamanlayicilar | Zamanlayıcılar, Kanban görünümü: kural kartları (tetikleyici türü, bağlı şablon, çalışma mantığı, son gönderim) | Sol menüde İletişim & Otomasyon › Zamanlayıcılar (Schedules)]]

**Ekranın bölümleri:** Başlık **Otomatik Bildirim Zamanlayıcıları (Notification Schedules)** ve "Kayıt sonrası tek seferlik gönderim ve paket bitişine 3 ay kala 15 günde bir periyodik hatırlatma kuralları." açıklaması; **+ Yeni Zamanlama Kuralı**; **Kanban / Liste** seçici (varsayılan Kanban). Arama kutusu yoktur.

**Kural kartı:** tetikleyici türü (teknik adıyla), **AKTİF** / **PASİF**, ad, **Bağlı Şablon:**, **Çalışma Mantığı:** ("Kayıt anında tek sefer gönder" ya da "90 gün kala, her 15 günde bir"), **Son Gönderim:** ("Henüz tetiklenmedi").

**Liste sütunları:** **Tetikleyici Türü** · **Kural Adı** · **Bağlı Şablon** · **Çalışma Mantığı & Periyot** · **Son Tetikleme** ("Henüz çalışmadı") · **Durum** · **İşlemler**.

| Düğme | Ne yapar | Dikkat |
|---|---|---|
| **+ Yeni Zamanlama Kuralı** | Kural penceresini açar | — |
| **Şimdi Tetikle** (Liste'de şimşek simgesi) | Kuralı hemen çalıştırır: paket bitimine belirtilen gün kalan ve son N günde hatırlatma almamış aktif şirketlere e-posta gönderir; sonuç "'<kural>' çalıştırıldı. N kuruma hatırlatıcı iletildi." | **Onay sormaz**. Gerçek müşterilere e-posta gider; geri alınamaz. Yalnızca "Paket Bitişine 3 Ay Kala" kurallarında çalışır |
| **Düzenle** | Kural penceresini dolu açar | — |
| **Sil** | "'<kural>' zamanlama kuralını silmek istediğinize emin misiniz?" | Onay ister (**Evet, devam et**). Geri alınamaz |

#### Yeni Bildirim Zamanlayıcısı Tanımla / Kuralı Düzenle

Alt başlık "Kayıt anında veya paket bitimine 3 ay kala periyodik e-posta gönderim kuralı."

[[EKRAN: sy-m-zamanlayici | Zamanlayıcı penceresi: Kural Adı, Tetikleme Senaryosu, İletilecek Şablon, gün alanları | Zamanlayıcılar › bir kuralda Düzenle]]

| Alan | Ne işe yarar | Nasıl doldurulur / seçenekler | Örnek | Zorunlu |
|---|---|---|---|---|
| **Kural Adı \*** | Kuralın adı | — | Paket Bitimine 3 Ay Kala 15 Günde Bir Hatırlatıcı | Evet |
| **Tetikleme Senaryosu \*** | Kuralın ne zaman çalışacağı | **Müşteri Kayıt Olduğunda (Tek Sefer)** / **Paket Bitişine 3 Ay Kala (Periyodik)** / **Özel Gün Sıklığı** | Paket Bitişine 3 Ay Kala (Periyodik) | Evet |
| **İletilecek Şablon \*** | Gönderilecek e-posta şablonu | "WELCOME_CUSTOMER (Hoş Geldiniz Şablonu)", "PACKAGE_EXPIRATION_REMINDER (3 Ay Bitiş Hatırlatıcı)" ya da diğer şablonlar ("<kod> - <ad>") | PACKAGE_EXPIRATION_REMINDER | Evet |
| **Kaç Gün Kala Başlasın?** (kayıt senaryosunda gizli) | Paket bitişine kaç gün kala hatırlatma başlasın | Sayı. "Varsayılan: 90 gün (3 ay)" | 90 | Hayır |
| **Gönderim Sıklığı (Gün)?** (kayıt senaryosunda gizli) | Aynı şirkete kaç günde bir hatırlatma gitsin | Sayı. "Varsayılan: 15 günde bir" | 15 | Hayır |
| **Zamanlayıcı Aktif** | Kuralın çalışması | İşaretsizse kural çalışmaz | işaretli | — |

Düğmeler: **Vazgeç**, **Zamanlayıcıyı Kaydet** ("✓ '<kural>' zamanlama kuralı oluşturuldu." / "… güncellendi.").

> **Dikkat:** **Özel Gün Sıklığı** seçeneği şu an otomatik olarak çalıştırılmaz ve **Şimdi Tetikle** ile de çalışmaz ("Bu zamanlama türü elle çalıştırılamaz; şirket aktivasyonunda otomatik kullanılır."). Hatırlatma için "Paket Bitişine 3 Ay Kala (Periyodik)" seçin.

> **Dikkat:** "Müşteri Kayıt Olduğunda (Tek Sefer)" kuralını pasife alırsanız, başvuru onaylarında aktivasyon e-postası gönderilmez. Bu, müşterinin şifre belirleme bağlantısını alamaması demektir.

**Adım adım örnek: hatırlatmaları 30 günde bir yapmak**

1. **Zamanlayıcılar** › "Paket Bitişine 3 Ay Kala …" kartında **Düzenle**.
2. **Gönderim Sıklığı (Gün)?**: 30 › **Zamanlayıcıyı Kaydet**.
3. Ertesi günden itibaren sistem aynı şirkete en fazla 30 günde bir hatırlatma gönderir.

# Yapay Zeka

Bu grup RECAi'nin arkasındaki altyapıyı yönetir. Buradaki değişiklikler **tüm müşterileri hemen etkiler**. Müşteriler bu ekranlardaki model adlarını hiçbir zaman görmez; yalnızca RECAi adlarını görür.

## Model Yönlendirici

### Akıllı model yönlendirici

**Bu ekran ne işe yarar?** İşin türüne göre (kod yazma, analiz, özetleme, Türkçe yazım, yapılandırılmış çıktı) hangi modelin kullanılacağını kalite testine dayanarak seçersiniz. Sistem modelleri hazır bir test setiyle sınar, puanlar ve her iş türü için bir model önerir. **Onayınız olmadan hiçbir şey değişmez.**

**Ne zaman kullanırım?** EVREN'e yeni bir model geldiğinde, bir modelin yavaşladığı ya da hata verdiği görüldüğünde, ayda bir kalite kontrolü için.

**Kimler görür / değiştirebilir?** Yalnızca RECDx süper yöneticileri.

[[EKRAN: sy-model-yonlendirici | Model Yönlendirici: iş türü tablosu, kalite test seti ve kalite matrisi | Sol menüde Yapay Zeka › Model Yönlendirici]]

**Ekranın bölümleri:**

1. **Akıllı model yönlendirici** kartı. Alt başlık öneri formülünü verir: "İş türüne göre platform varsayılan modeli. Öneri: kalite ×0.6 + hız ×0.2 + güvenilirlik ×0.2; kalite %70 altı önerilmez. Onayınız olmadan hiçbir şey değişmez."
2. **Kalite test seti** kartı.
3. **Canlı ölçümler (son 7 gün)** kartı.
4. **Karar geçmişi** kartı (karar varsa).

**İş türleri tablosu:**

| Sütun | Anlamı |
|---|---|
| **İş türü** | Kod yazma · Analiz ve planlama · Özetleme · Türkçe yazım · Yapılandırılmış çıktı (JSON) |
| **Şu an** | Bu iş türünde kullanılan model; seçim yoksa "platform varsayılanı" |
| **Öneri (son test)** | Son testin önerdiği model; "eşiği geçen model yok" ya da "test yok" |
| **Puan** | Önerilen modelin kalite, hız ve güvenilirlik yüzdeleri; güvenilirliğin kaynağı (canlı ölçüm ya da test) |

| Düğme | Ne yapar | Dikkat |
|---|---|---|
| **Önerileni onayla** | İş türünün platform modelini önerilen modele çevirir: "<iş türü> işleri için platform varsayılanı '<model>' olsun mu? AI personelin seçili modeli olan şirketler etkilenmez." | Onay ister. Model kalite eşiğinin altındaysa "Eşik altı model" penceresi gerekçe ister. **Kaldır** ile geri alınır |
| **Kaldır** | Yönlendirmeyi kaldırır: "<iş türü> yönlendirmesi kaldırılsın mı? Platform varsayılan modeline dönülür." | Onay ister |

**Kalite test seti** kartı: "Sürüm N · iş türü başına N vaka · çıktılar kuralla puanlanır (JSON alanları, kod sözdizimi, kelime/madde sınırı, zorunlu ifadeler); kod çalıştırılmaz."

| Alan / öğe | Ne işe yarar | Nasıl kullanılır |
|---|---|---|
| Model onay kutuları | Teste girecek modeller | Sınamak istediğiniz modelleri işaretleyin (yalnız etkin sohbet modelleri sınanabilir) |
| **Kalite testini çalıştır** | Testi başlatır: "Kalite testi N modelde çalıştırılsın mı? (N vaka × N model; EVREN kredisi harcanır)" | Onay ister. Test sürerken düğme **Test sürüyor…** olur, ekran 5 saniyede bir kendini yeniler |
| "Son koşu: <tarih> · …" | Son testin durumu: ilerleme, "tamamlandı" ya da "hata: …" | — |
| Kalite matrisi | Model × iş türü puanları | Yeşil %85 ve üstü, mavi %70 ve üstü, sarı %50 ve üstü, kırmızı %50 altı |

**Canlı ölçümler (son 7 gün):** "Gerçek kullanım: çağrı sayısı, hata oranı ve ortanca yanıt süresi (kalite testi çağrıları hariç)." Sütunlar **Model**, **Çağrı**, **Hata oranı** (%3 altı yeşil, %10'a kadar sarı, üstü kırmızı), **Ortanca süre**. Ölçüm yoksa "Ölçüm yok — Son 7 günde sohbet modeli çağrısı yapılmamış."

**Karar geçmişi:** "<iş türü>: <eski model> → <yeni model>", tarih ve not.

**Hata mesajları:** "Süren bir kalite testi var; bitmesini bekleyin." · "Yalnızca etkin sohbet modelleri sınanabilir." · "Bu model kalite eşiğinin altında; yine de onaylamak için gerekçe yazın."

**Adım adım örnek:**

1. **Model Yönlendirici** › **Kalite test seti**'nde yeni gelen modeli ve mevcut modelleri işaretleyin.
2. **Kalite testini çalıştır** › **Onayla**. Test bitene kadar bekleyin.
3. Kalite matrisinde puanlara bakın. "Özetleme" satırında öneri değiştiyse **Önerileni onayla**.
4. Bir hafta sonra **Canlı ölçümler**'de modelin hata oranını kontrol edin; sorun varsa **Kaldır**.

> **İpucu:** Kalite testi EVREN kredisi harcar. Gereksiz modelleri işaretlemeyin.

## Genel AI Modelleri

### Genel AI Modelleri & Yapay Zeka Kullanımı

**Bu ekran ne işe yarar?** Bir işlem için ayrıca model seçilmemişse kullanılacak **platform varsayılan modellerini** belirlersiniz ve bu ayın yapay zeka kullanımını (müşteri kredisi ve EVREN maliyeti) izlersiniz. Sol menüde **ÇEKİRDEK** etiketiyle işaretlidir; sistemin temel ayarıdır.

**Ne zaman kullanırım?** Yeni bir model varsayılan yapılacaksa, bir model kapatılacaksa, aylık maliyet kontrolünde.

**Kimler görür / değiştirebilir?** Yalnızca RECDx süper yöneticileri.

[[EKRAN: sy-genel-ai-modelleri | Platform Varsayılan Modelleri kartı ve altında Yapay Zeka Kullanımı kartı | Sol menüde Yapay Zeka › Genel AI Modelleri]]

**Bölüm 1 — Platform Varsayılan Modelleri.** Alt başlık: "Bir işlem için model seçilmemişse bu modeller kullanılır. Müşterinin paketinde olmayan bir model seçilirse paketindeki ilk uygun sohbet modeline düşülür."

Her alan bir seçim kutusudur; yalnızca etkin ve uygun türdeki modeller listelenir ("<ad> (<kod>) · katsayı N").

| Alan | Ne işe yarar | Uygun model türü |
|---|---|---|
| **Varsayılan sohbet modeli** | AI personellerin sohbet ve iş adımları | Sohbet |
| **Varsayılan Beyin AI modeli** | Proje planlayan Beyin AI | Sohbet |
| **Süper Yönetici asistanı modeli** | Yönetici Asistanı ekranı | Sohbet |
| **Manifesto, rol promptu ve ünvan inceleme modeli** | Şirket manifestosu, rol promptu ve unvan metinleri | Sohbet |
| **Hafıza vektörleme modeli** | Kurum hafızasında anlam bazlı arama için metni vektöre çevirir | Embedding |
| **Hafıza yeniden sıralama modeli** | Hafıza arama sonuçlarını sıralar | Reranker |
| **Taranmış belge / görsel metin okuma (OCR) modeli** | Taranmış belge okuma | OCR |
| **Görsel açıklama modeli (fotoğraf, şema, çizim)** | Görsel yorumlama | Vision |
| **Doküman içerik güvenliği modeli** | Yüklenen dokümanların güvenlik denetimi (Karantina kararı) | Guard |

| Düğme | Ne yapar | Dikkat |
|---|---|---|
| **Kaydet** | Değişen ayarları kaydeder ("Model ayarları kaydedildi.") | Yalnız değişiklik varsa etkin. Tüm şirketleri hemen etkiler |

**Hata mesajları:** "<ayar>: '<model>' aktif bir model değil." · "<ayar>: '<model>' bu amaç için uygun bir model türü değil (…)."

**Bölüm 2 — Yapay Zeka Kullanımı (<dönem>).** Alt başlık: "Müşteri kredisi RECOrion formülüyle, EVREN maliyeti EVREN'in bildirdiği kredi (CR) ile tutulur."

| Gösterge | Anlamı |
|---|---|
| **İşlem** | Bu dönem yapılan yapay zeka işlemi; altında başarısız sayısı |
| **Müşteri kredisi** | Müşterilerin harcadığı toplam kredi ("RECDx hariç tüm şirketler dahil") |
| **EVREN maliyeti** | RECDx'in EVREN'e harcadığı CR ("Çağrı başına ayrılan") |
| **EVREN kalan kredi** | EVREN'de kalan CR ve son ölçüm tarihi |
| **Şirketlere göre** | En çok kullanan ilk 10 şirket (kredi ve işlem sayısı; RECDx "(platform)" olarak görünür) |
| **Modellere göre** | En çok kullanılan ilk 10 model (token ve işlem sayısı) |

Düğme: **Yenile** (göstergeleri yeniden yükler).

> **Dikkat:** Müşteriye gösterilen AI personel seçimleri RECAi adları üzerinden çalışır. Bir RECAi adının arkasındaki modeli değiştirmek için **RECAi ve EVREN Modelleri** ekranını kullanın; bu ekran yalnızca "model seçilmemiş" durumlar içindir.

## Yönetici Asistanı

### Süper Yönetici Asistanı

**Bu ekran ne işe yarar?** Müşteriler, paketler, başvurular ve kredi kullanımı hakkında RECAi'ye günlük dille soru sorarsınız. Asistan platformun güncel yönetim verilerini kullanır. KVKK gereği müşteri içeriklerine (proje, sohbet, hafıza, doküman) erişmez. Sağ üstteki rozet: **Platform kullanımı · kredi düşülmez**.

**Ne zaman kullanırım?** Hızlı bir rapor istediğinizde (ör. "paket süresi yaklaşan müşteriler", "bu ay en çok kredi harcayanlar").

**Kimler görür / değiştirebilir?** Yalnızca RECDx süper yöneticileri.

[[EKRAN: sy-yonetici-asistani | Süper Yönetici Asistanı: öneri düğmeleri ve bir soru-yanıt | Sol menüde Yapay Zeka › Yönetici Asistanı; "Paket süresi yaklaşan müşteriler var mı?" önerisine tıklayın]]

Sohbet boşken "Asistan hazır — Platformun güncel yönetim verilerini kullanarak yanıt verir." yazar ve üç öneri düğmesi çıkar: "Bu ay en çok kredi harcayan şirketler hangileri?", "Paket süresi yaklaşan müşteriler var mı?", "Bekleyen başvuruları özetler misin?".

| Alan | Ne işe yarar | Nasıl doldurulur / seçenekler | Örnek | Zorunlu |
|---|---|---|---|---|
| "Asistana bir soru sorun… (Enter gönderir)" | Sorunuz | Günlük dille yazın; Enter gönderir | Örnek Lojistik'in paketi ne zaman bitiyor? | Evet |

| Düğme | Ne yapar | Dikkat |
|---|---|---|
| Öneri düğmeleri | Hazır soruyu gönderir | — |
| **Gönder** | Soruyu gönderir; yanıt beklenirken "Yanıt hazırlanıyor…" | Kredi düşülmez |

> **İpucu:** Asistanın yanıtı yönetim verisine dayanır; önemli kararlardan önce sayıları ilgili ekranda (Kayıtlı Şirketler, Dashboard) doğrulayın.

## RECAi ve EVREN Modelleri

### RECAi Adları ve EVREN Model Kataloğu

**Bu ekran ne işe yarar?** İki iş yaparsınız:

1. **RECAi Adları:** Müşterinin gördüğü RECAi adlarının (RECAi Mergen, RECAi Hızlı, RECAi Derin; yetenekler RECAi Görsel, RECAi Ses, RECAi Okur) arkasında hangi EVREN modelinin ve yedek modelin çalışacağını seçersiniz. Bir adın modelini değiştirdiğinizde o adı kullanan tüm müşterilerin AI personelleri kendiliğinden yeni modele geçer; müşteri tarafında ad değişmez.
2. **EVREN Modelleri Kataloğu:** EVREN'deki modelleri listeler, yeni modelleri ekler, katsayı ve durumlarını düzenlersiniz.

Gerçek model adları yalnızca bu ekranda (ve Merkez Yönetim'in diğer yapay zeka ekranlarında) görünür.

**Ne zaman kullanırım?** EVREN yeni model yayımladığında, bir model kapatıldığında, bir RECAi adının kalitesini ya da hızını değiştirmek istediğinizde.

**Kimler görür / değiştirebilir?** Yalnızca RECDx süper yöneticileri.

[[EKRAN: sy-recai-evren | Üstte RECAi Adları tablosu (Model, Yedek model, Kaydet), altında EVREN Modelleri Kataloğu | Sol menüde Yapay Zeka › RECAi ve EVREN Modelleri]]

**Bölüm 1 — RECAi Adları.** Alt başlık: "Müşteri yalnızca RECAi adını görür; arkasındaki EVREN modelini buradan değiştirirsiniz. Değişiklik denetim kaydına yazılır."

| Sütun / alan | Ne işe yarar | Nasıl doldurulur |
|---|---|---|
| **Ad** | RECAi adı ve açıklaması; rozet **Seçilebilir ad** (Mergen, Hızlı, Derin) ya da **Yetenek** (Görsel, Ses, Okur) | — |
| **Model** | Bu adın arkasındaki ana model | Listeden seçin. Seçilebilir adlarda sohbet modelleri, Görsel'de görsel modelleri, Ses'te ses modelleri, Okur'da OCR modelleri listelenir (yalnız etkin olanlar) |
| **Yedek model** | Ana model meşgulken kullanılacak model | Listeden seçin ya da "Yok" |

| Düğme | Ne yapar | Dikkat |
|---|---|---|
| **Kaydet** (her satırda) | "<ad> artık <model> ile çalışacak. Bu adı kullanan tüm müşterilerin AI personelleri hemen yeni modele geçer. Onaylıyor musunuz?" sonrası kaydeder ("<ad> güncellendi.") | Onay ister. Yalnız değişiklik varsa etkin. Tüm müşterileri hemen etkiler; eski modeli seçip yeniden kaydederek geri alınır |

**Bölüm 2 — EVREN Modelleri Kataloğu.** Alt başlık: "TÜBİTAK BİLGEM EVREN modelleri ve sisteme yeni eklenebilecek modellerin yönetimi."

| Alan | Ne işe yarar | Nasıl doldurulur / seçenekler | Örnek | Zorunlu |
|---|---|---|---|---|
| **Model ara...** | Listeyi süzer | Model kodu, adı ya da türü | CHAT | Hayır |

**Liste sütunları (varsayılan Liste):** **Model Kodu** · **Görünen İsim** · **Tür** · **Bağlam (Token)** (modelin bir seferde okuyabileceği metin miktarı) · **Efor Katsayısı** (Nx) · **Durum** (**ACTIVE** / **INACTIVE**) · **İşlemler**. Kanban kartında aynı bilgiler bulunur.

| Düğme | Ne yapar | Dikkat |
|---|---|---|
| **EVREN'den Modelleri Çek** | EVREN'in model listesini çeker: bağlam, çıktı sınırı ve fiyat bilgilerini günceller, yeni modelleri **PASİF** ekler. Sonuç: "N model güncellendi · N yeni model PASİF olarak eklendi (…); katsayısını belirleyip aktifleştirin · EVREN'de artık bulunmayan: …" | Onay sormaz. Yeni model siz aktifleştirene kadar kullanılmaz |
| **Yeni Model Ekle** | Model penceresini boş açar | — |
| **Düzenle** | Model penceresini dolu açar | — |
| **Sil** | "'<ad>' modelini silmek istediğinize emin misiniz?" | Onay ister (**Evet, devam et**). Geri alınamaz. Bir RECAi adının ya da varsayılanın kullandığı modeli silmeyin; pasife alın |

#### Yeni EVREN Modeli Ekle / EVREN Modelini Düzenle

[[EKRAN: sy-m-evren-model | EVREN model penceresi: Model Kodu, Görünen İsim, Tür, Bağlam, Efor Katsayısı, Durum | RECAi ve EVREN Modelleri › katalogda bir modelde Düzenle]]

| Alan | Ne işe yarar | Nasıl doldurulur / seçenekler | Örnek | Zorunlu |
|---|---|---|---|---|
| **Model Kodu** | EVREN'deki teknik model adı | EVREN'deki adla birebir. Kayıttan sonra değiştirilemez | deepseek-r1 | Evet |
| **Görünen İsim** | Merkez Yönetim ekranlarındaki ad | — | DeepSeek R1 (Muhakeme) | Evet |
| **Tür** | Modelin türü | CHAT (sohbet), CODE (kod), VISION (görsel), EMBEDDING (vektör), RERANKER (sıralama), OCR (belge okuma), AUDIO (ses) | CHAT | Evet |
| **Bağlam (Token)** | Modelin bağlam penceresi | Sayı; varsayılan 131072 | 131072 | Hayır |
| **Efor Katsayısı** | Kredi formülündeki çarpan: katsayı × (giriş token/1000 + 2 × çıkış token/1000) | 0,1 adımlı sayı; varsayılan 1,0. Pahalı modelde büyük verin | 1.5 | Hayır |
| **Durum** | Model kullanımda mı | **ACTIVE (Aktif)** / **INACTIVE (Pasif)**. Pasif modeller seçim listelerinde görünmez | ACTIVE (Aktif) | — |

Düğmeler: **Vazgeç**, **Modeli Kaydet** ("✓ '<ad>' modeli eklendi." / "✓ '<ad>' güncellendi.").

**Adım adım örnek: EVREN'e gelen yeni modeli devreye almak**

1. **EVREN'den Modelleri Çek**. Mesajda yeni modelin PASİF eklendiğini görün.
2. Yeni modelde **Düzenle** › **Efor Katsayısı**'nı belirleyin › **Durum**: ACTIVE › **Modeli Kaydet**.
3. **LLM TL Fiyatları**'nda modelin TL fiyatını girin.
4. **Model Yönlendirici**'de kalite testine sokun.
5. Sonuç iyiyse **RECAi Adları** tablosunda örneğin RECAi Hızlı'nın **Model**'ini yeni modele çevirip **Kaydet**.

> **Dikkat:** Efor katsayısını değiştirmek müşterilerin kredi tüketimini hemen değiştirir.

## LLM TL Fiyatları

### LLM TL Fiyatları

**Bu ekran ne işe yarar?** Her model için 1 milyon girdi ve 1 milyon çıktı token'ının TL fiyatını (KDV hariç) tanımlarsınız. Proje maliyet raporlarında her yapay zeka çağrısı, yapıldığı andaki fiyatla hesaplanır. Yeni fiyat eskisini silmez; fiyat geçmişi tutulur.

**Ne zaman kullanırım?** EVREN fiyatı değiştiğinde, yeni model devreye alındığında, CR/TL kuru güncellendiğinde.

**Kimler görür / değiştirebilir?** Yalnızca RECDx süper yöneticileri. Müşteriler fiyatları değil, proje maliyet raporlarındaki sonuçları görür.

[[EKRAN: sy-llm-fiyatlari | LLM TL Fiyatları tablosu: kur alanı, model satırları, Fiyat yok rozetleri | Sol menüde Yapay Zeka › LLM TL Fiyatları]]

Kartın alt başlığı: "Model başına 1 milyon girdi ve 1 milyon çıktı token'ının TL fiyatı (KDV hariç). Proje maliyet raporlarında her çağrı, yapıldığı andaki fiyatla hesaplanır; yeni fiyat eskisini silmez."

Fiyatı olmayan aktif sohbet modeli varsa üstte uyarı çıkar: "N aktif sohbet modelinin TL fiyatı tanımlı değil; bu modellerin çağrıları maliyet raporunda fiyatsız görünür."

| Alan | Ne işe yarar | Nasıl doldurulur / seçenekler | Örnek | Zorunlu |
|---|---|---|---|---|
| **EVREN 1 CR = ? TL (öneri için)** | EVREN kredisinin TL karşılığı; fiyat önerisi bununla hesaplanır | Sayı (4 ondalık); **Kuru kaydet** ile kaydedin ("CR > TL kuru kaydedildi.") | 0,85 | Hayır |
| **Altyapı modellerini de göster (embedding, OCR, guard…)** | Tabloya sohbet dışı modelleri de ekler | İşaretleyin | — | Hayır |

**Tablo sütunları:** **Model** (görünen ad ve kod) · **Tür** · **Girdi / 1M** · **Çıktı / 1M** · **Geçerli** (fiyatın başlangıcı ya da **Fiyat yok**) · **EVREN** (EVREN'in fiyatı ya da **Ücretsiz · <tarih>**) · **Öneri** (EVREN fiyatı × CR kuru).

| Düğme | Ne yapar | Dikkat |
|---|---|---|
| **Kuru kaydet** | CR/TL kurunu kaydeder | Önerileri değiştirir; kayıtlı fiyatları değiştirmez |
| **Fiyat gir** / **Fiyat / geçmiş** | Modelin fiyat penceresini açar | — |

#### Model · TL fiyatı

[[EKRAN: sy-m-llm-fiyat | "<model> · TL fiyatı" penceresi: fiyat alanları ve Fiyat geçmişi tablosu | LLM TL Fiyatları › bir modelde Fiyat / geçmiş]]

| Alan | Ne işe yarar | Nasıl doldurulur / seçenekler | Örnek | Zorunlu |
|---|---|---|---|---|
| **1M girdi token (₺)** | 1 milyon girdi token'ının fiyatı | Sayı; öneri varsa önceden dolar | 12,50 | Evet |
| **1M çıktı token (₺)** | 1 milyon çıktı token'ının fiyatı | Sayı | 37,50 | Evet |
| **Geçerlilik başlangıcı (boş: şimdi)** | Fiyatın geçerli olduğu an | Tarih ve saat; boşsa şimdi | 01.11.2026 00:00 | Hayır |
| **Not** | Fiyatın kaynağı | En fazla 500 karakter | EVREN Kasım fiyat listesi | Hayır |

Pencerede iki bilgi notu vardır: "Alanlar EVREN fiyatı × CR kuru önerisiyle dolduruldu; kontrol edip kaydedin." (öneri varsa) ve "Geçmiş bir başlangıç tarihi verirseniz, o aralıkta henüz fiyatlanmamış çağrılar bu fiyatla hesaplanır; daha önce fiyatlanmış çağrılar değişmez." Altta **Fiyat geçmişi** tablosu (**Başlangıç**, **Girdi / 1M**, **Çıktı / 1M**, **Not**) bulunur; boşsa "Henüz fiyat girilmedi."

| Düğme | Ne yapar | Dikkat |
|---|---|---|
| **Vazgeç** | Kapatır | — |
| **Yeni fiyatı kaydet** | Yeni fiyat satırı ekler: "Fiyat kaydedildi; N fiyatlanmamış çağrı bu fiyatla hesaplandı." | Fiyatlar silinmez ya da düzeltilmez; yanlış fiyat için yeni bir doğru fiyat girin. Eksikte "Girdi ve çıktı fiyatını yazın." |

> **Örnek:** EVREN 1 Kasım'dan geçerli yeni fiyat listesi yayımladı. **LLM TL Fiyatları** › kuru güncelleyip **Kuru kaydet** › modelde **Fiyat / geçmiş** › önerilen değerleri kontrol edin › **Geçerlilik başlangıcı**: 01.11.2026 00:00 › **Not**: "EVREN Kasım fiyat listesi" › **Yeni fiyatı kaydet**.


# Sık karşılaşılan durumlar ve çözümleri

| Durum | Neden olabilir | Ne yapmalı |
|---|---|---|
| Müşteri aktivasyon e-postasının gelmediğini söylüyor | E-posta gereksiz klasörüne düştü; onay sırasında e-posta gönderilemedi; "Müşteri Kayıt Olduğunda" zamanlayıcısı pasif | Müşteriye gereksiz klasörünü kontrol ettirin. Zamanlayıcılar'da kuralın **AKTİF** olduğuna bakın. Kayıtlı Şirketler › **Hoş Geldin Maili** ile yeniden gönderin |
| Müşteri şifresini unuttu | — | Müşteri giriş penceresindeki **Şifremi unuttum**'u kullanabilir. Siz de **Hoş Geldin Maili** ile şifre belirleme bağlantısı gönderebilirsiniz. Son çare: **Detay & Yönetim › Güçlü Şifre Oluştur** |
| Şirket kullanıcıları giriş yapamıyor | Şirket pasif; paket süresi bitmiş | Kayıtlı Şirketler'de rozet **PASİF** ise **Aktife Al**. Paket bitmişse **Detay & Yönetim › Paket Kira Bitiş Tarihi**'ni güncelleyin |
| AI personeller "kredi tükendi" uyarısı veriyor | Aylık kredi ve ek kredi bitti | Kayıtlı Şirketler › **Kredi** › ek kredi yükleyin (satış sonrası) |
| Şirket silinemiyor | Şirkette departman, AI personel ya da proje var | Silmeyin; **Pasife Al** kullanın |
| Başvuruda "⚠ Yeniden dene" görünüyor | Odoo'ya aktarım başarısız | Dashboard'da Odoo durumunu kontrol edin; **⚠ Yeniden dene**'ye tıklayın. Sürerse Odoo'da elle açın |
| Başvuru "Odoo: kapalı" | Pakette Odoo ürünü yok ya da Odoo bağlantısı kapalı | Kiralama Paketleri'nde paketin **Odoo satış ürünü**'nü seçin; mevcut başvuru için Odoo'da sipariş açın |
| Yeni müşteri eklerken e-posta reddediliyor | Ücretsiz e-posta (Gmail vb.) ya da e-posta başka hesapta kayıtlı | Şirket alan adlı, başka hesapta olmayan bir e-posta isteyin |
| Vergi numarası kabul edilmiyor | Hane sayısı, kontrol hanesi ya da aynı VKN başka şirkette | Numarayı müşteriden teyit edin; zaten kayıtlıysa mevcut şirketi bulun |
| Logo yüklenmiyor | SVG dosyası ya da 2 MB üstü | PNG, JPG ya da WEBP'ye çevirip küçültün |
| Bir müşteri RECSlip kurulumunun kontrol edilmesini istiyor | Kurulum KVKK gereği size görünmez | Müşteriden ekran paylaşımı isteyin; kurulumu müşterinin şirket yöneticisi ya da Bağlantı Yönetimi izni olan kullanıcısı yapar |
| Dashboard'da "Bazı bileşenlerde sorun var" | Bir bileşen yavaş ya da erişilemiyor | Altyapı panelinde kırmızı/sarı satırı bulun, **↻ Yeniden ölç**; sürerse teknik ekibe bildirin |
| Dashboard'da "Çekirdek bileşen erişilemiyor" | Veritabanı ya da oturum sunucusu çalışmıyor | Hemen teknik ekibe bildirin; müşteriler sistemi kullanamaz |
| Hata oranı yükseldi | Model dolu (503), zaman aşımı | Model Yönlendirici › Canlı ölçümler'de modeli bulun; RECAi Adları'nda yedek model tanımlı olduğundan emin olun |
| Maliyet raporunda çağrılar fiyatsız | Modelin TL fiyatı yok | LLM TL Fiyatları'nda fiyat girin; geçmiş tarih verirseniz fiyatsız çağrılar da hesaplanır |
| Paket silinemiyor | Paketi kullanan şirket ya da başvuru var | **Paket Aktif** işaretini kaldırarak satıştan çekin |
| Rol silinemiyor | Role atanmış kullanıcı var | Silmeyin; gerekirse rolün açıklamasını güncelleyin |
| E-posta şablonu silinemiyor | Temel şablon ya da zamanlayıcıda kullanılıyor | Şablonu düzenleyin; zamanlayıcıdaysa önce zamanlayıcıyı değiştirin |
| Yeni izin ekledim ama hiçbir şey değişmedi | İznin yazılımda karşılığı yok | Odoo'da İSTEK açın; geliştirme ekibi izni yazılıma bağlar |
| **Şimdi Tetikle** "elle çalıştırılamaz" diyor | Kural "Paket Bitişine 3 Ay Kala" türünde değil | Yalnızca bu türde elle çalıştırma vardır |
| Müşteri RECSlip kartını Bağlantı galerisinde göremiyor | Şirketin RECSlip talebi ya da Odoo'su yok | Uygulama Talepleri'nde talebin durumunu kontrol edin |
| Bir şirketin Work Space'ine geçtim, projeler görünmüyor | KVKK Koruma Modu | Bu beklenen davranıştır; içerik RECDx'e gösterilmez |

# Hızlı başvuru

| Yapmak istediğim iş | Menü | Ekran / düğme |
|---|---|---|
| Bekleyen başvuruları görmek | Genel › Dashboard (Genel Bakış) | **Bekleyen Başvurular** kartı |
| Başvuruyu onaylamak | Müşteriler › Başvuru Onay Durum | **Onayla & Aktif Et** |
| Başvuruyu reddetmek | Müşteriler › Başvuru Onay Durum | **Reddet** |
| Başarısız Odoo aktarımını tekrarlamak | Müşteriler › Başvuru Onay Durum | **⚠ Yeniden dene** |
| Doğrudan satışla gelen müşteriyi açmak | Müşteriler › Kayıtlı Şirketler | **+ Yeni Müşteri Ekle**, sonra Başvuru Onay Durum'da onay |
| Şirket bilgisini, paketini, bitiş tarihini değiştirmek | Müşteriler › Kayıtlı Şirketler | **Detay & Yönetim** › sekme 1 |
| Şirket logosu yüklemek / değiştirmek | Müşteriler › Kayıtlı Şirketler | **Detay & Yönetim** › **Şirket Logosu** |
| Şirket yöneticisini değiştirmek | Müşteriler › Kayıtlı Şirketler | **Detay & Yönetim** › **2. Şirket Yöneticisi Tanımlaması** |
| Müşteriye şifre belirleme bağlantısı göndermek | Müşteriler › Kayıtlı Şirketler | **Hoş Geldin Maili** |
| Paket süresi hatırlatması göndermek | Müşteriler › Kayıtlı Şirketler | **Hatırlatıcı Mail** |
| Ek kredi yüklemek | Müşteriler › Kayıtlı Şirketler | **Kredi** › **Kredi Yükle** |
| Müşteriyi durdurmak | Müşteriler › Kayıtlı Şirketler | **Pasife Al** |
| Kullanılmamış şirketi silmek | Müşteriler › Kayıtlı Şirketler | **Sil** |
| Sektör / meslek eklemek | Katalog › Sektör Tanımları / Meslek Tanımları | **Yeni Sektör Ekle** / **Yeni Meslek Ekle** |
| Tüm müşterilere yeni unvan sunmak | Katalog › Departman & Unvan | **Yeni Unvan** |
| Unvana genel doküman öğretmek | Katalog › Departman & Unvan | Unvan › **Bilgi Dokümanları** |
| Hazır proje / Case şablonu eklemek | Katalog › Proje Şablonları | **Yeni şablon** |
| Mevzuat kartını güncelleyip yayımlamak | Katalog › Mevzuat Paketleri | **Kartları düzenle**, **Uzman kontrolüyle yayımla** |
| Bağlantı galerisine sistem eklemek | Katalog › Bağlantı Kataloğu | **Kart ekle** |
| RECSlip / RECQmind taleplerini izlemek | Katalog › Uygulama Talepleri | Süzgeçler, **Tamamlandı** |
| Yeni paket tanımlamak | Ticari & Yetki › Kiralama Paketleri | **Yeni Paket Tanımla** |
| Pakete RECAi adı / yeteneği eklemek | Ticari & Yetki › Kiralama Paketleri | **Düzenle** › **Pakete dahil RECAi** |
| Pakette RECSlip indirimi tanımlamak | Ticari & Yetki › Kiralama Paketleri | **Düzenle** › **RECDx uygulamaları (Odoo)** |
| İznin adını / açıklamasını düzeltmek | Ticari & Yetki › İzin Kataloğu (RBAC) | **Düzenle** |
| Sistem rolünün izinlerini değiştirmek | Ticari & Yetki › Yetki Rolleri | **Düzenle & İzinler** |
| E-posta metnini değiştirmek | İletişim & Otomasyon › E-Posta Şablonları | **Düzenle & Önizle** |
| Test e-postası göndermek | İletişim & Otomasyon › E-Posta Şablonları | **Test** |
| Hatırlatma sıklığını değiştirmek | İletişim & Otomasyon › Zamanlayıcılar (Schedules) | **Düzenle** |
| İş türüne göre model seçmek | Yapay Zeka › Model Yönlendirici | **Kalite testini çalıştır**, **Önerileni onayla** |
| Varsayılan modelleri değiştirmek | Yapay Zeka › Genel AI Modelleri | **Kaydet** |
| Aylık yapay zeka maliyetini görmek | Yapay Zeka › Genel AI Modelleri | **Yapay Zeka Kullanımı** kartı |
| Yönetim sorusu sormak | Yapay Zeka › Yönetici Asistanı | Soru kutusu |
| RECAi adının modelini değiştirmek | Yapay Zeka › RECAi ve EVREN Modelleri | **RECAi Adları** › **Kaydet** |
| EVREN'in yeni modellerini almak | Yapay Zeka › RECAi ve EVREN Modelleri | **EVREN'den Modelleri Çek** |
| Model TL fiyatı girmek | Yapay Zeka › LLM TL Fiyatları | **Fiyat gir** / **Fiyat / geçmiş** |
| Kendi şifremi değiştirmek | Üst çubuk › profil kartı | **Bilgilerimi Güncelle** |

