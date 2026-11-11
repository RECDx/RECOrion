# RECOrion — Şirket Yönetimi Kılavuzu

Şirketinizin RECOrion yönetim konsolu için kullanım kılavuzu. Sürüm: Kasım 2026.

# Bu kılavuz hakkında

## Kimin için?

Bu kılavuz, şirketinizde RECOrion'u kuran ve yöneten kişiler içindir: şirket yöneticisi, insan kaynakları ve organizasyon sorumlusu, bilgi işlem (entegrasyon) sorumlusu, finans sorumlusu ve muhasebe müdürü. Sistemi daha önce hiç görmemiş olmanız sorun değildir. Her ekranı yukarıdan aşağıya, alan alan ve düğme düğme anlatıyoruz.

Günlük işlerin yürüdüğü ekranlar (projeler, Case'ler, iş adımları, sohbet, Onaylarım, Bağlantılarım) ayrı bir kılavuzda anlatılır: **Work Area Kılavuzu**. Bu kılavuzda o ekranlara yalnızca Şirket Yönetimi ile bağlantılı oldukları yerde kısaca değiniyoruz.

## Nasıl okunur?

- İlk kez kuruyorsanız sırayla okuyun: önce **Genel düzen** ve **Menü ağacı**, sonra **Organizasyon** (departman ve ünvan), **Personel** (kullanıcı ve AI personel), **Kurum Zekâsı** ve **Kullanım**. Kurulum sırası için **İlk kurulum sırası** bölümüne bakın.
- Belirli bir işi arıyorsanız kılavuzun sonundaki **Hızlı başvuru** tablosuna bakın.
- RECSlip.App v2 ile aylık masraf sürecini kuracaksanız doğrudan **RECSlip.App v2 ile aylık masraf süreci** bölümüne geçin; bölüm kendi başına okunabilir.
- Her ekranda aynı düzen kullanılır: ne işe yarar, kimler görür, ekranın bölümleri, alanlar tablosu, düğmeler tablosu, durumlar ve mesajlar, adım adım örnek, ipuçları ve sık sorulan sorular.
- Ekrandaki düğme ve alan adları **kalın** yazılmıştır ve ekranda gördüğünüz gibidir.

## Örneklerdeki kurgusal şirket

Örneklerde kurgusal bir şirket kullanıyoruz: **Örnek Lojistik A.Ş.** Kişiler:

| Kişi | Görevi | RECOrion'daki rolü |
|---|---|---|
| Ayşe Yılmaz | Şirket yöneticisi | Şirket Yöneticisi |
| Mehmet Demir | Proje yöneticisi | Proje Yöneticisi |
| Zeynep Kaya | Muhasebeci | Uzman Kullanıcı (RECSlip sürecinde Case yöneticisi) |
| Can Öztürk | Uzman (operasyon) | Uzman Kullanıcı |

## Simgeler, kutular ve rozet renkleri

| Gördüğünüz | Anlamı |
|---|---|
| > **İpucu:** | İşinizi kolaylaştıran öneri. |
| > **Dikkat:** | Geri alınamayan veya veri kaybına yol açabilecek işlem; dikkatle okuyun. |
| > **Örnek:** | Örnek Lojistik A.Ş.'den somut bir örnek. |
| Yeşil rozet | Olumlu durum: Etkin, Aktif, Onaylı, Başarılı, Çalışıyor. |
| Sarı rozet | Dikkat isteyen durum: Onay bekliyor, Taslak, süresi yaklaşan anahtar. |
| Kırmızı rozet | Hata veya engel: Hata, Geçersiz, Süresi doldu, Pasif, Yetkisiz. |
| Mavi rozet | Bilgi: Deneme, Teklif istendi, sayaç. |
| Gri rozet | Nötr veya kapalı durum: Kapalı, Devre dışı, Duraklatıldı, Kurulmadı. |
| Sağ altta kısa süreli kutu (bildirim) | Yaptığınız işlemin sonucu: yeşil başarı, kırmızı hata, sarı uyarı, mavi bilgi. Birkaç saniye sonra kendiliğinden kaybolur. |
| `*` (yıldız) | Alan adının sonundaysa alan zorunludur. |
| 🔒 (kilit) | Alan paketiniz veya yetkiniz nedeniyle değiştirilemez. |

## Kavramlar sözlüğü

| Kavram | Açıklama |
|---|---|
| **RECOrion** | RECDx'in, işleri ve projeleri yapay zekâ personeliyle birlikte yürüten platformu. |
| **RECAi** | RECOrion'un yapay zekâsı. Kademeleri: **RECAi Mergen** (genel, varsayılan), **RECAi Hızlı**, **RECAi Derin**; ek yetenekleri **RECAi Görsel** (resim anlama), **RECAi Ses** (konuşma), **RECAi Okur** (belge okuma). |
| **Kademe katsayısı** | RECAi kademesinin kredi çarpanı. Katsayı yükseldikçe RECAi daha güçlü çalışır ama aynı iş için daha çok kredi harcar. |
| **Beyin AI** | Şirketinizin organizatör yapay zekâsı. Manifestonuzu, departmanlarınızı, ünvanlarınızı, AI personelinizi ve kurum hafızanızı bilerek soru yanıtlar ve planlama önerir. |
| **AI personel (AI ajan)** | Şirketinizde bir ünvanla çalışan yapay zekâ çalışanı. Ekranlarda "AI Ajan" ve "AI personel" aynı anlamda kullanılır. |
| **İnsan personel (kullanıcı)** | Sisteme e-posta ve şifreyle giriş yapan çalışanınız. |
| **Departman** | Şirketinizin birimi (Satış, Muhasebe, Operasyon...). Ünvanlar, kullanıcılar ve AI personel departmana bağlanır. |
| **Ünvan** | Bir görevin tanımı: departmanı, önerilen RECAi kademesi, otonomi seviyesi ve rol promptu. AI personel ünvanından bunları devralır. Ekranlarda "ünvan" ve "unvan" aynı anlamda geçer. |
| **Rol promptu** | AI personele "sen kimsin, ne yaparsın, hangi kurallara uyarsın" diye verilen yazılı talimat. |
| **Otonomi seviyesi** | AI personelin ne kadar kendi başına çalışacağı: **L1** her adımda insan onayı, **L2** rutin işleri kendisi yapar, kritik adımlarda onay ister, **L3** tam otonom, yalnızca nihai onay ister. |
| **Proje** | Birden çok iş adımından oluşan, başı ve sonu olan iş. |
| **Case** | Tek bir olaydan veya döneme bağlı bir süreçten doğan, odaklı iş (ör. bir iade talebi, bir aylık masraf kapanışı). Proje ile aynı ekranlarda yürür. |
| **İş adımı** | Proje veya Case'in bir parçası. Bir insana veya AI personele atanır; gerekirse onaylanır. |
| **Onay** | Bir iş adımının çıktısının, bir dış sisteme yazma işleminin veya bir kararın yetkili kişi tarafından kabul edilmesi. |
| **Kurum hafızası** | Şirketinizin onaylı bilgi deposu. Onaylanan bilgiyi bütün AI personel kullanır. |
| **Sektörel manifesto** | Şirketinizin sektörlerini, faaliyet kodlarını ve kurumsal ilkelerini anlatan metin. Bütün AI personel kararlarında bunu referans alır. |
| **NACE kodu** | Resmî faaliyet sınıflandırma kodu (ör. 52.29 Taşımacılığı destekleyici diğer faaliyetler). |
| **Entegrasyon (bağlantı)** | RECOrion'un şirketinizin başka bir sistemine (Odoo, Logo, Trello, GitHub...) bağlanması. |
| **Araç** | Bir bağlantının AI personele sunduğu tek bir işlem (ör. kayıt arama, kayıt oluşturma). Okuma araçları anında çalışır, yazma araçları her zaman insan onayına düşer. |
| **Eşleme** | RECAi'nin hazırladığı bir kaydın (ürün kartı, cari, teklif...) dış sistemde hangi alanlara yazılacağını belirleyen kurallar. |
| **Aktarım** | Bir iş çıktısının eşleme kullanılarak dış sisteme yazılması. Her aktarım önizleme ve onaydan geçer. |
| **Otomasyon** | Dış sistemde bir olay olunca (yeni kayıt, değişiklik, belirli bir zaman) RECOrion'da otomatik olarak Case veya proje açan ya da bildirim gönderen kural. |
| **Kredi** | RECAi kullanımının ölçü birimi. Paketinizle her ay belirli bir kredi gelir; ek kredi de alınabilir. |
| **Paket (kota)** | RECDx ile yaptığınız sözleşmenin kapsamı: kullanıcı sayısı, AI personel sayısı, kullanılabilir RECAi kademeleri, aylık kredi. |
| **İzin** | Bir kullanıcının yapabileceği tek bir işlem türü (ör. "Kullanıcı Ekleme"). |
| **Sistem yetki rolü** | RECDx'in hazırladığı izin paketi (ör. Şirket Yöneticisi, Entegrasyon Yöneticisi). Kullanıcıya bir rol ve gerekirse ek izinler atanır. |
| **Kişisel anahtar** | Bir kişinin şirket sistemindeki (ör. Odoo) kendi kullanıcısına ait API anahtarı. AI personel o kişi adına yalnızca bu anahtarla işlem yapar. |
| **API anahtarı** | Bir programın başka bir sisteme şifre yerine kullandığı uzun gizli metin. |
| **RECSlip.App v2** | RECDx'in Odoo 20 üzerinde çalışan masraf fişi uygulaması. Fişleri okur, hesap kodunu seçer, onaydan geçirir, muhasebe programına aktarım dosyası hazırlar. |
| **KVKK** | Kişisel Verilerin Korunması Kanunu. RECOrion'da şirketinizin içeriği (proje, sohbet, hafıza, entegrasyon bağlantıları) yalnızca şirketinize aittir; RECDx yöneticileri dahil şirketiniz dışından kimse bu içeriği göremez. |

# Genel düzen

## Konsola giriş

Şirket Yönetimi, şirketinizin yönetim konsoludur. Burada organizasyonu kurar, kullanıcı ve AI personel tanımlar, şirketinizin yapay zekâsını ayarlar, dış sistem bağlantılarını ve otomasyonları yönetir, kredi kullanımını izlersiniz. Günlük işler ise **Work Space** (Çalışma Alanı) ekranlarında yürür.

Konsola iki yoldan girilir:

1. **Doğrudan giriş:** Rolü **Şirket Yöneticisi** olan bir kullanıcı RECOrion'a giriş yaptığında doğrudan Şirket Yönetimi açılır.
2. **Work Space'ten geçiş:** Diğer kullanıcılar girişte Work Space'e gelir. Şirket Yönetimi'nden en az bir menüyü görme izinleri varsa üst çubukta **🏢 Şirket Yönetimi** düğmesi görünür (üzerine gelince "Şirket Departmanları ve Organizasyon Yönetim Konsoluna Git"). Bu düğmeye tıklayınca konsol açılır. Hiçbir yönetim izni olmayan kullanıcı (ör. Uzman Kullanıcı) bu düğmeyi görmez.

Konsoldan Work Space'e dönmek için konsolun üst çubuğundaki **💻 Çalışma Alanı (Work Area)** düğmesine tıklarsınız.

[[EKRAN: ca-giris-workspace-dugmesi | Work Space üst çubuğunda "🏢 Şirket Yönetimi" düğmesi işaretli | Entegrasyon Yöneticisi rolündeki bir kullanıcıyla giriş yapın; Work Space açılınca üst çubuğun sağ tarafındaki "🏢 Şirket Yönetimi" düğmesini çerçeveyle gösterin]]

**Açılış ekranı:** Konsol açılınca **Genel Bakış** gelir. Genel Bakış'ı görme izniniz yoksa size açık olan ilk menü açılır. Bir servise tek tık girişle (ör. bir CRM'e "giriş yap") bağlanıp geri döndüğünüzde konsol doğrudan **Entegrasyonlar** ekranında açılır.

**Kendi şirketiniz:** Konsol her zaman yalnızca kendi şirketinizin verileriyle çalışır. Başka şirketlerin hiçbir verisini göremezsiniz.

> **Dikkat:** Menüler izinlerinize göre görünür. İzniniz olmayan bir menü sol menüde hiç görünmez. Bir menüyü görüp bir işlemi yapamıyorsanız (ör. düğmeye bastığınızda "Bu işlem için yetkiniz yok." uyarısı) o işlemin izni sizde yoktur; şirket yöneticinizden izin isteyin. Hangi rolün hangi menüleri gördüğü aşağıdaki **Roller ve menüler** tablosundadır.

## Ekran düzeni

[[EKRAN: ca-genel-duzen | Şirket Yönetimi'nin tamamı: solda menü, üstte yol göstergesi ve düğmeler, ortada Genel Bakış | Şirket Yöneticisi ile giriş yapın; konsol açılınca tam ekran görüntü alın; sol menüdeki grupları ve üst çubuk öğelerini numarayla işaretleyin]]

Ekran üç parçadan oluşur:

1. **Sol menü:** Üstte şirket logonuz (yüklediyseniz; yoksa bina simgesi), şirket adınız ve altında "Şirket Yönetimi" yazısı. Altında menü grupları. En altta veri gizliliği kutusu ve RECOrion logosu (menü daraltılınca yalnız simgesi).
2. **Üst çubuk:** Hangi ekranda olduğunuz, tema seçici, Çalışma Alanı'na geçiş, site bağlantısı, kullanıcı bilginiz ve çıkış.
3. **Ana alan:** Seçtiğiniz menünün ekranı.

### Sol menü

| Öğe | Ne yapar |
|---|---|
| Şirket logosu ve adı | Şirketinizi gösterir. Logo **Genel › Şirket Profili** ekranından yüklenir. |
| **Menüyü daralt** (sol üstteki panel simgesi) | Menüyü yalnızca simgelere indirir, ana alana daha çok yer kalır. Daraltılmış menüde grup başlıkları gizlenir; bir simgenin üzerine gelince menünün adı görünür. |
| **Menüyü genişlet** | Daraltılmış menüyü yeniden açar. |
| Grup başlığı (ör. **Personel**) | Tıklayınca grup kapanır veya açılır. Hangi grupları kapattığınız bu tarayıcıda hatırlanır. |
| Menü öğesi | Tıklayınca o ekran açılır. Açık olan öğe vurgulu görünür. Bazı öğelerin sağında sayaç vardır (aşağıda). |
| **Şirket Veri İzolasyonu Aktif** kutusu | "Başka şirketler ve RECDx yöneticileri proje, sohbet ve hafıza içeriğinize erişemez (KVKK)." Bilgi amaçlıdır. |

Menü sayaçları: **Kullanıcı Yönetimi** yanında aktif kullanıcı sayısı ve paketinizdeki azami sayı (ör. `3 / 5`), **Departmanlar** yanında departman sayısı, **Ünvan Tanımları** yanında ünvan sayısı.

**Tablet ve telefonda:** Sol menü gizlenir ve çekmece olur. Üst çubuğun solundaki **Menüyü aç** (üç çizgi) düğmesiyle açılır. Bir menü öğesine veya menünün dışına tıklayınca kapanır.

[[EKRAN: ca-genel-duzen-telefon | Telefon genişliğinde açılmış menü çekmecesi | Tarayıcıyı telefon genişliğine (yaklaşık 390 piksel) küçültün; Şirket Yönetimi'nde üst çubuğun solundaki üç çizgi düğmesine tıklayın; çekmece açıkken görüntü alın]]

### Üst çubuk

| Öğe | Ne yapar | Dikkat |
|---|---|---|
| Yol göstergesi: `Şirket Yönetimi / <ekranın adı>` | Hangi ekranda olduğunuzu gösterir. | Tıklanmaz. |
| Tema seçici: **Koyu**, **Açık**, **Sistem** | Ekran renklerini değiştirir. **Sistem**, bilgisayarınızın veya telefonunuzun temasını izler. | Telefonda tek düğmedir; her tıklamada Koyu → Açık → Sistem sırasıyla değişir. |
| **💻 Çalışma Alanı (Work Area)** | Work Space'e geçer (projeler, Case'ler, sohbet, AI personel ile çalışma). Üzerine gelince "3 Bölmeli Canlı Çalışma Alanına (Work Area) Geçiş Yap". | Konsolda kaydetmediğiniz değişiklik varsa kaybolur. |
| **🌐 Site** | RECOrion'un tanıtım sitesine gider. | — |
| Kullanıcı kutusu | Adınızın baş harfi, adınız ve rolünüzün adı (ör. "Şirket Yöneticisi", "Entegrasyon Yöneticisi"). | Tıklanmaz. |
| **Çıkış** (üzerine gelince "Güvenli Çıkış Yap") | Oturumunuzu kapatır. | Onay sormaz. |

### Bildirimler ve onay pencereleri

- Her işlemin sonucu sağ altta kısa bir bildirimle gösterilir (yeşil başarı, kırmızı hata, sarı uyarı, mavi bilgi).
- Geri alınamayan işlemlerde (silme, devre dışı bırakma, anahtar yenileme, arşivleme) önce bir onay penceresi açılır. Pencerede ne olacağı yazar; **Vazgeç** ile iptal eder, onay düğmesiyle (ör. **Evet, Sil**) devam edersiniz.
- **Esc** tuşu açık pencereyi kaydetmeden kapatır. Sıra şöyledir: önce açık bir açılır liste, sonra onay penceresi, en son düzenleme penceresi kapanır.
- Bir pencerede **✕**, **Kapat**, **Vazgeç** veya **İptal** düğmeleri de kaydetmeden kapatır.

## İlk kurulum sırası

Şirketinizi RECOrion'da ilk kez kuruyorsanız şu sırayı öneririz:

1. **Şirket Profili:** logonuzu yükleyin.
2. **Sektörel Manifesto:** sektörlerinizi ve NACE kodlarınızı seçin, manifestonuzu yazın. Departman ve ünvan önerileri bu bilgiye göre gelir.
3. **Departmanlar:** **Katalogdan Ekle** ile önerilen departmanları ekleyin, eksikleri elle tanımlayın.
4. **Ünvan Tanımları:** AI personelin ve çalışanların ünvanlarını tanımlayın.
5. **Kullanıcı Yönetimi:** çalışanlarınızı ekleyin, rollerini seçin.
6. **AI Ajan İşe Alım:** AI personelinizi işe alın, dokümanlarınızı öğretin.
7. **Beyin AI:** Beyin AI'nın kademesini seçin.
8. **Entegrasyonlar** ve **Otomasyonlar:** dış sistemlerinizi bağlayın, gerekiyorsa otomasyon ve RECSlip.App v2 sürecini kurun.
9. **Mevzuat Paketleri:** ilgili paketleri açın.
10. **Kredi ve Kullanım:** ilk haftadan sonra kredi tüketimini kontrol edin.

## Yardım ve RECAi'ye sor

**Bu ne işe yarar?** Bu kılavuzun tamamı RECOrion'un içinde de vardır. Bir ekranda takıldığınızda kılavuzu aramanıza gerek kalmaz: **F1** tuşuna basın veya üst çubuktaki **Yardım** düğmesine tıklayın. Sağdan bir yardım paneli açılır; çalıştığınız ekran kapanmaz.

**Kimler görür?** Giriş yapmış herkes. Panelde yalnız sizin yetkiniz dahilindeki ekranların anlatımı görünür. Örneğin Kullanıcı Yönetimi izni olmayan bir uzman, Kullanıcı Yönetimi sayfasını içindekilerde görmez ve RECAi ona bu konuda yanıt vermez.

**Panelin sekmeleri:**

| Sekme | Ne işe yarar |
|---|---|
| **RECAi'ye sor** | Sorunuzu kendi cümlenizle yazarsınız; RECAi kılavuzdan, adım adım yanıt verir. Yanıtın altında dayandığı yardım sayfaları ve gerekiyorsa **Ekrana git** düğmesi çıkar. Aynı konuda ek soru sorabilirsiniz; RECAi önceki soruları hatırlar. |
| **Bu ekran** | Bulunduğunuz ekranın anlatımını açar. Bir pencere açıkken F1'e basarsanız o pencerenin bölümüne gider. **Bu ekranı aç** düğmesi anlatılan ekrana götürür. |
| **İçindekiler** | Görebildiğiniz kılavuzların bölüm ve sayfa listesi. Bir sayfaya tıklayınca açılır; sayfadaki görselleri büyütmek için üzerine tıklayın. |

[[EKRAN: ca-yardim-recai | Otomasyonlar ekranında açılmış Yardım paneli: RECAi'ye sor sekmesinde soru, adım adım yanıt, Ekrana git düğmesi ve dayandığı yardım sayfaları | Herhangi bir Şirket Yönetimi ekranında F1'e basın veya üst çubuktaki Yardım düğmesine tıklayın; RECAi'ye sor sekmesine sorunuzu yazıp Sor'a basın]]

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

> **Örnek:** Ayşe Yılmaz **Otomasyonlar** ekranında F1'e basar; panelde Otomasyonlar ekranının anlatımı açılır. Ardından **RECAi'ye sor** sekmesine "RECSlip aylık sürecini nasıl kurarım?" yazar. RECAi kurulum adımlarını ve ön koşulları sıralar, kaynak olarak **Şirket Yönetimi Kılavuzu › Otomasyonlar** sayfasını gösterir ve **Ekrana git** düğmesiyle Otomasyonlar ekranını açar.

> **İpucu:** RECAi yardım soruları kılavuz bilgisiyle yanıtlanır; projelerinizin, fişlerinizin veya kullanıcılarınızın verisini okumaz. "Kaç projem var?" gibi veri soruları için ilgili ekranı açın.

# Menü ağacı

## Menüler ve ekranlar

| Grup | Menü | Ekran ve pencereleri | Kimler görür (bu izinlerden biri yeterli) |
|---|---|---|---|
| **Genel** | Genel Bakış | Şirket panosu: proje, adım, kredi, maliyet, AI personel karnesi | Şirket Geneli Pano |
| | Şirket Profili | Şirket logosu, kurum bilgileri | Şirket Ayarlarını Yönetme |
| **Personel** | Kullanıcı Yönetimi | Kullanıcı listesi; Kullanıcı Tanımlama / Düzenleme; Kullanıcıyı Sil | Kullanıcı Ekleme, Kullanıcı Düzenleme ve Silme |
| | AI Ajan İşe Alım | AI personel listesi; AI Personel İşe Al sihirbazı; AI Ajan Bilgilerini Düzenle; İşten Çıkar; Sil; Uzmanlık Dokümanları; Doküman İnceleme | AI Personel İşe Alma, AI Personel Ayarları ve Bilgi Kaynakları, AI Personeli İşten Çıkarma |
| **Organizasyon** | Departmanlar | Departman listesi; Yeni Departman / Düzenle; Katalogdan Departman Ekle; Sil | Departman Yönetimi |
| | Ünvan Tanımları | Ünvan listesi; Şirket Ünvanı Tanımla / Düzenle; Bilgi Dokümanları; Sil | Ünvan Tanımlama |
| **Kurum Zekâsı** | Sektörel Manifesto | Sektörler, NACE kodları, kurumsal manifesto | Sektörel Manifesto Yönetimi |
| | Beyin AI | Beyin AI kademesi, Kurum Hafızası Onay Kuyruğu, Beyin AI ile konuş | Beyin AI Ayarları |
| | Entegrasyonlar | Bağlantılar; Bağlantı ekle (katalog); bağlantı formu; ajan anahtarı; araç yetkileri; eşleme stüdyosu; RECDx uygulamaları; aktarım onay kuralları; aktarım günlüğü; araç çağrı kaydı | Bağlantı Yönetimi, Eşleme Stüdyosu, Dış Sisteme Yazma Onayı |
| | Otomasyonlar | Hazır kurallar; RECSlip.App v2 aylık süreç kartı ve kurulum penceresi; kural listesi; yeni kural; örnek olayla dene; günlük; imza anahtarı; otomasyon günlüğü | Otomasyon Kuralları |
| | Mevzuat Paketleri | Paket listesi; paket kartları | Mevzuat Paketlerini Açma/Kapatma |
| **Kullanım** | Kredi ve Kullanım | Kredi bakiyesi, dağılımlar, son işlemler, kredi hareketleri | Kredi ve Kullanımı Görme |

## İzinler

İzinler RECDx tarafından tanımlanır. Siz kullanıcıya bir **sistem yetki rolü** seçersiniz; gerekirse **ek izin** eklersiniz (bkz. Kullanıcı Yönetimi). İzinler, ekranda da gördüğünüz modül adlarıyla gruplanır:

| Modül | İzin | Ne sağlar |
|---|---|---|
| Şirket & Platform | Şirket Bilgilerini Görüntüleme | Şirket, departman, ünvan, kullanıcı ve AI personel listelerini görme. Her kullanıcıda bulunur. |
| | Şirket Ayarlarını Yönetme | Şirket Profili, RECDx uygulama tercihleri ve genel şirket ayarları. Şirket yöneticisinin temel izni. |
| Genel Bakış & Raporlar | Şirket Geneli Pano | Genel Bakış: tüm şirketin göstergeleri. |
| | Departman Panosu | Yalnızca kendi departmanının panosunu görme (Work Space › Pano). |
| | Maliyet ve Bütçe Bilgilerini Görme | Panolardaki parasal göstergeler: token maliyeti, maliyet dağılımı, tahmini tasarruf, bütçe ve gerçekleşen. |
| Kullanıcılar & Roller | Kullanıcı Ekleme | Yeni kullanıcı tanımlama. |
| | Kullanıcı Düzenleme ve Silme | Departman, ünvan, rol, ek izin ve durum değiştirme, silme; kişinin günlük maliyetini görme. |
| | Şirkete Özel Rol Tanımlama, Rol Düzenleme, Rol Silme | Kullanıcı Yönetimi ekranının altındaki **Şirkete özel roller** kartında rol oluşturma, düzenleme ve silme. |
| AI Personel | AI Personel İşe Alma | İşe alım sihirbazı; işe alınan personel için sektör ve ünvan Deep Search araştırması (Kaynaklar sekmesi). |
| | AI Personel Ayarları ve Bilgi Kaynakları | AI personelin bilgilerini ve rol promptunu düzenleme; doküman, web ve video kaynağı ekleme, onaylama. |
| | AI Personeli İşten Çıkarma | İşten çıkarma, yeniden işe alma ve silme. |
| | Ünvan Tanımlama | Ünvan ve rol promptu oluşturma, düzenleme, silme. |
| Organizasyon | Departman Yönetimi | Departman oluşturma, katalogdan ekleme, düzenleme, silme. |
| Kurum Zekâsı | Sektörel Manifesto Yönetimi | Sektör ve meslek bilgileri ile manifestoyu düzenleme, RECAi'ye yazdırma. |
| | Beyin AI Ayarları | Beyin AI'nın RECAi kademesini seçme. |
| | Mevzuat Paketlerini Açma/Kapatma | Mevzuat paketlerini şirkete açma ve kapatma. |
| Entegrasyon & Otomasyon | Bağlantı Yönetimi | Bağlantı ekleme, deneme, AI personele araç yetkisi verme, aktarım kuralları; RECSlip.App v2 sürecini kurma ve hemen çalıştırma. |
| | Eşleme Stüdyosu | Eşleme hazırlama, deneme ve onaylama. |
| | Otomasyon Kuralları | Otomasyon kuralı ve hazır kural kurma, sınama, durdurma, günlük. |
| | Dış Sisteme Yazma Onayı | Aktarım ve araç çağrısı onayı (ikinci onay dahil), aktarım günlüğü, başarısız aktarımı yeniden deneme. |
| Kredi & Kullanım | Kredi ve Kullanımı Görme | Kredi ve Kullanım ekranı. |
| Projeler & İş Akışı | Proje / Case Açma; Tüm Projeleri Yönetme; Şirket Şablonlarını Yönetme; İş Adımı Ekleme; İş Adımı Onaylama (Vekâleten); Revizyon İsteme (Vekâleten) | Work Space işleri (Work Area Kılavuzu). |
| Sohbet & İletişim | Sohbet ve Görev İletişimi; Ajanlar Arası Konuşmaları İzleme | Görev sohbeti ve Beyin AI sohbeti. Çalışma Alanı'ndaki "Ajanlar arası" görünümü ve AI personelin kendi aralarındaki mesajları yalnız Ajanlar Arası Konuşmaları İzleme izni olana görünür. |
| Kurum Hafızası | Kurum Hafızasında Arama; Kurum Hafızasına Ekleme ve Onaylama; Kurum Hafızasından Geri Alma | Hafıza işlemleri. Beyin AI ekranındaki onay kuyruğu "Ekleme ve Onaylama" izniyle kullanılır. |
| Bağlantılarım | Kişisel Erişim Anahtarı | Work Space › Bağlantılarım'da kişisel erişim anahtarı oluşturma. |

> **Dikkat:** Bir kullanıcı, kendisinde olmayan bir izni başkasına veremez. Örneğin Personel ve Organizasyon Yöneticisi, kendisinde bulunmayan "Bağlantı Yönetimi" iznini bir kullanıcıya ek izin olarak eklemek isterse "Sahip olmadığınız izinleri atayamazsınız: ..." uyarısı alır.

## Roller ve menüler

Şirketinizde atayabileceğiniz 10 sistem rolü vardır (RECDx'in kendi süper yönetici rolü müşterilere görünmez ve atanamaz). Aşağıdaki tabloda ✓ o rolün menüyü gördüğünü gösterir.

| Rol | Genel Bakış | Şirket Profili | Kullanıcı Yönetimi | AI Ajan İşe Alım | Departmanlar | Ünvan Tanımları | Sektörel Manifesto | Beyin AI | Entegrasyonlar | Otomasyonlar | Mevzuat Paketleri | Kredi ve Kullanım |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Şirket Yöneticisi | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Proje Yöneticisi | – | – | – | ✓ | – | – | – | – | – | – | – | – |
| Uzman Kullanıcı | – | – | – | – | – | – | – | – | – | – | – | – |
| Personel ve Organizasyon Yöneticisi | – | – | ✓ | ✓ | ✓ | ✓ | – | – | – | – | – | – |
| Yapay Zeka ve Ajan Lideri | – | – | – | ✓ | – | ✓ | ✓ | ✓ | – | – | ✓ | – |
| Entegrasyon Yöneticisi | – | – | – | – | – | – | – | – | ✓ | ✓ | – | – |
| Finans ve Raporlama Sorumlusu | ✓ | – | – | – | – | – | – | – | ✓ | – | – | ✓ |
| Kalite ve Onay Sorumlusu | – | – | – | – | – | – | – | – | – | – | – | – |
| Operasyon Yöneticisi | ✓ | ✓ | – | – | ✓ | – | ✓ | – | – | – | ✓ | ✓ |
| Güvenlik ve Uyum Denetçisi | ✓ | – | – | – | – | – | – | – | – | – | – | ✓ |

Uzman Kullanıcı ve Kalite ve Onay Sorumlusu Şirket Yönetimi'ni hiç görmez; bu kişiler yalnızca Work Space'te çalışır.

Rollerin kısa tanımı (ekrandaki açıklamalar):

| Rol | Ne yapar |
|---|---|
| **Şirket Yöneticisi** | Şirketin tüm yönetim ve çalışma yetkileri. Şirkette en az bir aktif şirket yöneticisi bulunmalıdır. |
| **Proje Yöneticisi** | Proje ve Case açar, RECAi ile planlar, ekip kurar, AI personel işe alır, adımları onaylar, kurum hafızasına aktarır. |
| **Uzman Kullanıcı** | Ekibinde olduğu projelerde çalışır: atanan adımlar, sohbet, hafızada arama, kişisel erişim anahtarı. Yeni kullanıcıda önceden seçili gelen roldür. |
| **Personel ve Organizasyon Yöneticisi** | İnsan kullanıcıları, AI personeli, departman ve ünvanları yönetir. |
| **Yapay Zeka ve Ajan Lideri** | AI personelin işe alımı, eğitimi ve kalitesinden; manifesto, Beyin AI ve mevzuat ayarlarından sorumludur. |
| **Entegrasyon Yöneticisi** | Dış sistem bağlantıları, eşlemeler, otomasyon kuralları ve dış sisteme yazma onaylarından sorumludur (bilgi işlem). |
| **Finans ve Raporlama Sorumlusu** | Şirket panosu, maliyet ve bütçe, kredi kullanımı; tutar eşiğini aşan aktarımların onayı. |
| **Kalite ve Onay Sorumlusu** | Erişebildiği projelerde adım çıktılarını onaylar veya revizyon ister; kurum hafızasını denetler. |
| **Operasyon Yöneticisi** | Şirket ayarları, pano, kredi ve operasyonel projelerin genel yönetimi. |
| **Güvenlik ve Uyum Denetçisi** | Salt okunur denetim: panolar, maliyet ve kredi, ajanlar arası konuşmalar, sohbet dışa aktarma. |

> **Örnek:** Örnek Lojistik A.Ş.'de bilgi işlemden sorumlu bir çalışana **Entegrasyon Yöneticisi** rolü verilir. Bu kişi Work Space'te **🏢 Şirket Yönetimi** düğmesini görür; konsolda yalnızca **Kurum Zekâsı** grubunda **Entegrasyonlar** ve **Otomasyonlar** menüleri vardır. Kullanıcı Yönetimi'ni hiç görmez.

> **İpucu:** Bir role ek olarak tek bir menüyü açmak isterseniz rolü değiştirmek yerine **ek izin** verin. Örneğin Mehmet Demir'e (Proje Yöneticisi) "Şirket Geneli Pano" ek izni verirseniz konsolda **Genel Bakış**'ı da görür.

# Genel

## Genel Bakış

### Genel Bakış ekranı

**Bu ekran ne işe yarar?** Şirketinizin projelerini, iş adımlarını, RECAi kredi tüketimini, maliyetlerini ve AI personel başarısını tek panoda gösterir. Dönem ve departman seçerek panonun tamamını süzebilirsiniz. Bütün tutarlar TL ve KDV hariçtir.

**Ne zaman kullanırım?** Haftalık veya aylık durum kontrolünde, yönetim toplantısından önce, kredinin nereye gittiğini veya AI personelin ne kadar iyi çalıştığını merak ettiğinizde.

**Kimler görür?** "Şirket Geneli Pano" izni olanlar (Şirket Yöneticisi, Finans ve Raporlama Sorumlusu, Operasyon Yöneticisi, Güvenlik ve Uyum Denetçisi). Parasal kartlar yalnızca "Maliyet ve Bütçe Bilgilerini Görme" izni olanlara görünür; bu izin yoksa o kartlar ve AI personel karnesindeki **Maliyet** sütunu hiç çıkmaz. Ekranda değiştirilecek bir ayar yoktur; yalnızca görüntülenir.

[[EKRAN: ca-genel-bakis | Genel Bakış panosu: üstte dönem düğmeleri ve departman listesi, altında proje ve adım sayaçları, kredi ve maliyet kartları | Şirket Yöneticisi ile giriş yapın; sol menüden Genel › Genel Bakış; "30 gün" seçili olsun; sayfanın üst yarısının görüntüsünü alın]]

**Ekranın bölümleri (yukarıdan aşağı):**

1. **Süzgeç satırı:** başlık **Genel Bakış**, dönem düğmeleri (**7 gün**, **30 gün**, **90 gün**, **1 yıl**), **Departman** listesi ve "TL, KDV hariç · grafikler son N gün" notu.
2. **Proje sayaçları:** **Aktif proje** (yürüyen ve duraklatılmış), **Tamamlanan** (altında "zamanında X · geç Y"), **İptal edilen**, **Hazırlıkta** (taslak, planlamada ve başlamaya hazır).
3. **Adım sayaçları:** **Tamamlanan adım** (X / toplam), **Onay bekleyen adım** (insan onayı bekleyen AI çıktıları), **Revizyondaki adım** (düzeltme istenmiş), **Karantinadaki adım** (güvenlik veya kalite nedeniyle durdurulmuş; sıfırdan büyükse kırmızı).
4. **Kredi** kartı ("Dönem AAAA-AA"): **Bu ay kullanılan**, **Aylık hak**, **Kalan aylık**, **Ek kredi bakiyesi**.
5. **Günlük kredi tüketimi** kartı: gün gün kredi sütun grafiği.
6. **Günlük token maliyeti** kartı (parasal): yapay zekâ çağrılarının günlük TL karşılığı. Alt başlıkta "N çağrının TL fiyatı tanımsız (0 sayıldı)" yazıyorsa bazı çağrıların fiyatı henüz RECDx tarafından girilmemiştir.
7. **LLM bazında** kartı: RECAi kademesine göre kullanım ("N çağrı · X kredi"). Fiyat tanımlıysa TL, değilse kredi gösterir.
8. **Maliyet dağılımı** kartı (parasal): **Personel**, **Token (LLM)**, **Diğer kalemler**, **Toplam**; bütçesi tanımlı projelerin toplam bütçesi; **Diğer maliyet kalemleri** listesi. Personel maliyeti kişi kişi değil, yalnızca toplam olarak gösterilir.
9. **Tahmini tasarruf (ROI)** kartı (parasal): AI personelin tamamladığı adımları insan yapsaydı ne tutacağı, AI maliyeti ve aradaki fark; varsayım açıklaması.
10. **İlk seferde onay** kartı: AI personel başına, revizyon istenmeden onaylanan adım yüzdesi.
11. **AI personel karnesi** tablosu.
12. **Ekip iş durumu** tablosu (insan personel; ücret bilgisi içermez).
13. **Projeler: bütçe ve gerçekleşen** kartı (parasal): proje başına bütçe ve gerçekleşen çubukları ("Gerçekleşen = personel + token + diğer kalemler").

**Alanlar:**

| Alan | Ne işe yarar | Nasıl doldurulur / seçenekler | Örnek | Zorunlu |
|---|---|---|---|---|
| Dönem | Sayaçların ve grafiklerin kapsadığı geriye dönük süre | **7 gün**, **30 gün** (varsayılan), **90 gün**, **1 yıl** düğmelerinden biri | 90 gün | Hayır |
| Departman | Panoyu tek bir departmana daraltır | "Tüm şirket" (varsayılan) veya bir departman. Departman tanımlı değilse liste görünmez. Yalnızca departman panosu izniniz varsa liste yerine "Departman: <ad>" etiketi çıkar ve değiştirilemez. | Operasyon | Hayır |

**Tablolar:**

| Tablo | Sütunlar |
|---|---|
| AI personel karnesi | **AI personel** (ad ve ünvan), **Tamamlanan** (tamamlanan / atanan), **İlk seferde onay** (%), **Otonomi** (insan revizyonu istenmeden tamamlanan adım payı, %), **Revizyon**, **Karantina**, **Ort. süre** (dakika veya saat), **Kredi**, **Maliyet** (yalnızca parasal izinle). "—" hesaplanacak veri olmadığını gösterir. |
| Ekip iş durumu | **Personel**, **Açık**, **Çalışılıyor**, **Onay bekliyor**, **Tamamlanan**, **Geciken** |

**Düğmeler:**

| Düğme | Ne yapar | Dikkat |
|---|---|---|
| **7 gün / 30 gün / 90 gün / 1 yıl** | Dönemi değiştirir, panoyu yeniden yükler. | Serbestçe değiştirilir. |
| **Departman** listesi | Kapsamı daraltır veya "Tüm şirket"e döndürür. | — |

**Boş ekran ve uyarılar:**

| Metin | Anlamı | Ne yapmalı |
|---|---|---|
| "Bu dönemde kredi tüketimi yok." / "Bu dönemde LLM çağrısı yok." | Seçili dönemde yapay zekâ kullanılmamış. | Daha uzun bir dönem seçin. |
| "Bu kapsamda iş almış AI personel yok." | Seçili departmanda iş atanmış AI personel yok. | "Tüm şirket"i seçin veya AI personele iş atayın. |
| "Bu kapsamda iş atanmış insan personel yok." | Seçili kapsamda insanlara iş atanmamış. | — |
| "Bu dönemde TL maliyeti oluşmadı. LLM TL fiyatları RECDx tarafından girildiğinde burada görünür." | Fiyatlar henüz girilmemiş. | RECDx ile görüşün. |
| ROI kartında "Tahmini tasarruf için en az N insan personelin günlük maliyeti … tanımlı olmalı" | Karşılaştırma için insan maliyeti bilinmiyor. | **Kullanıcı Yönetimi**'nde insan personele **Günlük maliyet** girin. |

**Adım adım örnek:**

> **Örnek:** Ayşe Yılmaz aylık yönetim toplantısından önce durumu kontrol ediyor.
> 1. Sol menüden **Genel › Genel Bakış**'a tıklar. **30 gün** seçilidir.
> 2. **Onay bekleyen adım** sayacında 7 görür. Bunların Work Space'te kimi beklediğini **Ekip iş durumu** tablosunun **Onay bekliyor** sütunundan bulur.
> 3. **Departman** listesinden "Operasyon"u seçer; **AI personel karnesi**nde bir AI personelin **İlk seferde onay** oranının %40 olduğunu görür. Bu personelin ünvanının rol promptunu ve bilgi dokümanlarını gözden geçirmeye karar verir.
> 4. **1 yıl**'ı seçip **Tahmini tasarruf (ROI)** kartındaki tutarı sunumuna ekler.

**Sık sorulan sorular:**

- *Neden maliyet kartlarını göremiyorum?* "Maliyet ve Bütçe Bilgilerini Görme" izniniz yok. Şirket yöneticinizden isteyin.
- *Bir çalışanın maliyetini kişi bazında görebilir miyim?* Panoda hayır; kişisel veri olduğu için yalnızca toplam gösterilir. Kişinin günlük maliyetini **Kullanıcı Yönetimi**'nde, kullanıcı düzenleme izniniz varsa görürsünüz.
- *Tutarlar KDV dahil mi?* Hayır, bütün tutarlar KDV hariçtir.

## Şirket Profili

### Şirket Profili ekranı

**Bu ekran ne işe yarar?** Şirketinizin resmî logosunu yükler, değiştirir veya kaldırırsınız; RECDx'te kayıtlı kurum bilgilerinizi görürsünüz. Logo, Şirket Yönetimi'nin sol üst köşesinde ve Work Space üst çubuğundaki **Kurum:** alanında şirketinizi temsil eder.

**Ne zaman kullanırım?** Kurulumda logonuzu eklemek için, logonuz değiştiğinde veya kurum bilgilerinizi kontrol etmek istediğinizde.

**Kimler görür / değiştirir?** "Şirket Ayarlarını Yönetme" izni olanlar (Şirket Yöneticisi, Operasyon Yöneticisi). Logoyu bu kişiler değiştirir. Kurum bilgilerini bu ekrandan kimse değiştiremez; değişiklik için RECDx ile iletişime geçilir. Logo kayıt sırasında da (isteğe bağlı) eklenebilir.

[[EKRAN: ca-sirket-profili | Şirket Profili: üstte "Şirket logosu" kartı (logo önizlemesi, "Logoyu değiştir" ve "Kaldır" düğmeleri), altta "Kurum bilgileri" listesi | Şirket Yöneticisi ile giriş yapın; sol menüden Genel › Şirket Profili; logosu yüklenmiş bir şirkette görüntü alın]]

**Ekranın bölümleri:**

1. **Şirket logosu** kartı — "Resmi logonuz Work Space ve Şirket Yönetimi ekranlarında şirketinizi temsil eder." Logo önizlemesi (logo yoksa bina simgesi), düğmeler ve dosya kuralı notu: "PNG, JPG veya WEBP · en fazla 2 MB · kare ya da yatay; saydam arka planlı PNG önerilir."
2. **Kurum bilgileri** kartı — "Değişiklik için RECDx ile iletişime geçin." Salt okunur liste.

**Alanlar (Kurum bilgileri, salt okunur):**

| Alan | Ne işe yarar | Nasıl doldurulur | Örnek | Zorunlu |
|---|---|---|---|---|
| Ünvan | Şirketin resmî adı | RECDx kaydından gelir | Örnek Lojistik A.Ş. | — |
| Vergi no / dairesi | Vergi kimlik numarası ve vergi dairesi | RECDx kaydından gelir | 1234567890 · Kozyatağı | — |
| Telefon | Şirket telefonu | RECDx kaydından gelir | 0216 000 00 00 | — |
| E-posta | Şirketin iletişim e-postası | RECDx kaydından gelir | info@orneklojistik.com.tr | — |
| Web sitesi | Şirketin sitesi | RECDx kaydından gelir | www.orneklojistik.com.tr | — |
| Adres | Şirket adresi | RECDx kaydından gelir | Ataşehir / İstanbul | — |

Boş bilgiler "—" olarak görünür.

**Düğmeler:**

| Düğme | Ne yapar | Dikkat |
|---|---|---|
| **Logo seç** (logo yoksa) / **Logoyu değiştir** (logo varsa) | Bilgisayarınızdan bir görsel seçtirir; seçtiğiniz anda yüklenir ("Şirket logosu kaydedildi."). | Ayrıca kaydetmeye gerek yoktur. Eski logonun yerine geçer. |
| **Kaldır** | Logoyu siler. | Onay sorar: "<şirket adı> logosu kaldırılsın mı?". Geri almak için logoyu yeniden yüklersiniz. |

**Logo kuralları:**

- Kabul edilen biçimler: PNG, JPG, WEBP. SVG ve diğer biçimler kabul edilmez.
- En fazla 2 MB; en az 16×16 piksel.
- Logo sunucuda en uzun kenarı 512 piksel olacak şekilde küçültülür ve PNG'ye çevrilir; saydamlık korunur, dosyadaki gizli bilgiler (kamera, konum gibi) silinir.
- Logo şirketinizin herkese açık kimliğidir; giriş ekranı gerektirmeden gösterilebilir. Logoya gizli bilgi koymayın.

**Hata mesajları:**

| Mesaj | Anlamı | Ne yapmalı |
|---|---|---|
| "Logo PNG, JPG veya WEBP olmalı (SVG kabul edilmez)." | Dosya biçimi uygun değil. | Logoyu PNG olarak kaydedip yeniden seçin. |
| "Logo en fazla 2 MB olabilir." | Dosya büyük. | Görseli küçültün veya sıkıştırın. |
| "Logo çok küçük (en az 16×16 piksel)." | Görsel çok küçük. | Daha büyük bir görsel kullanın. |
| "Logo şu anda kaydedilemedi. Lütfen biraz sonra tekrar deneyin." | Geçici depolama sorunu. | Birkaç dakika sonra tekrar deneyin. |

**Adım adım örnek:**

> **Örnek:** Ayşe Yılmaz, Örnek Lojistik A.Ş.'nin logosunu ekliyor.
> 1. **Genel › Şirket Profili**'ne tıklar.
> 2. **Logo seç**'e tıklar, bilgisayarından `ornek-lojistik-logo.png` dosyasını seçer.
> 3. "Şirket logosu kaydedildi." bildirimi gelir; sol üstte bina simgesinin yerine logo görünür.
> 4. Work Space'e geçtiğinde üst çubuktaki **Kurum:** alanında da logo görünür.

**RECAi model geliştirmeye katkı kartı:** RECAi, RECDx'in yerli ve milli yapay zekâ modelidir. İşaret açıkken AI personelinizin onaylanan ve reddedilen işlerinden çıkan örnekler, kişisel ve şirkete özgü bilgiler (ad, kimlik/vergi no, IBAN, telefon, e-posta, adres, firma adı, tutar) **geri çevrilemez biçimde maskelendikten sonra** RECAi'nin geliştirilmesinde kullanılır. İşaret varsayılan olarak açıktır; Şirket Yöneticisi istediği an kaldırabilir (onay sorar). Kaldırınca verileriniz sonraki eğitim setlerine girmez; önceden eğitilmiş bir modelden geri çıkarılamaz. Şirketinizin hafızası ve AI personelinizin öğrenmesi bu izinden bağımsız çalışmaya devam eder. RECDx personeli bu işareti değiştiremez.

**RECDx destek erişimi kartı:** KVKK gereği RECDx şirketinizin içeriğini göremez. Bir sorunun incelenmesini istediğinizde **Süre** (1 saat – 1 hafta) ve isteğe bağlı **Neden** seçip **Erişim ver**'e tıklayın. Süre boyunca RECDx'in Merkez Beyin AI'sı iş durumunuzu (proje ve adım durumları, karantinadaki adımlar, kredi, öğrenme özeti) görebilir. Her okuma kartın altındaki **Erişim kayıtları** listesine düşer (tarih, kim, ne sordu). **Erişimi şimdi kapat** ile süre dolmadan kapatırsınız. Erişimi yalnız şirketinizin yöneticisi verir; RECDx kendine veremez.

**Sık sorulan sorular:**

- *Şirket adresimiz değişti, nereden düzeltirim?* Bu ekrandan değil; RECDx ile iletişime geçin.
- *Logo neden bulanık görünüyor?* Küçük bir görsel yüklemiş olabilirsiniz. En az 256 piksel genişliğinde, saydam arka planlı bir PNG yükleyin.

# Personel

## Kullanıcı Yönetimi

### Kullanıcı Yönetimi ekranı

**Bu ekran ne işe yarar?** Şirketinizin insan personelini, yani RECOrion'a giriş yapacak kişileri tanımlarsınız. Her kişiye departman, ünvan, sistem yetki rolü ve gerekirse ek izin atanır. Paketinizin insan kullanıcı kotası da burada izlenir. Ekrandaki alt başlık: "Şirketinizin insan personellerini tanımlayın, departman/ünvan atayın, Süper Yöneticinin rollerini ve ek izinlerini belirleyin."

**Ne zaman kullanırım?** Yeni bir çalışan sisteme katılacağında, birinin görevi veya yetkisi değiştiğinde, işten ayrılan birinin girişini kapatmak istediğinizde.

**Kimler görür / değiştirir?** "Kullanıcı Ekleme" veya "Kullanıcı Düzenleme ve Silme" izni olanlar (Şirket Yöneticisi, Personel ve Organizasyon Yöneticisi). Yalnızca "Kullanıcı Ekleme" izni olan kişi yeni kullanıcı tanımlar ama mevcut kullanıcıyı düzenleyemez veya silemez. Kişinin günlük maliyetini yalnızca düzenleme izni olanlar görür.

[[EKRAN: ca-kullanici-yonetimi | Kullanıcı Yönetimi: üstte kota kartı, altında arama ve süzgeçler, kart görünümünde kullanıcılar | Şirket Yöneticisi ile giriş yapın; sol menüden Personel › Kullanıcı Yönetimi; "Kartlar" görünümünde en az üç kullanıcılı bir şirkette görüntü alın]]

**Ekranın bölümleri:**

1. Başlık ve düğmeler: **Yenile**, **+ Yeni Kullanıcı Tanımla**.
2. **Paket kota kartı:** paket adı (yoksa "Kurumsal Paket") ve "İnsan Kullanıcı Kotası"; `<aktif> / <azami> Kullanıcı (Kalan Kontenjan: N)`; ilerleme çubuğu; sağda durum kutusu: **Kota Uygun** (yeşil, "… N adet daha kullanıcı tanımlayabilirsiniz.") veya **Azami Kota Doldu** (kırmızı, "… Yeni kullanıcı eklemek için paketinizi yükseltin veya mevcut bir hesabı pasife alın.").
3. **Süzgeç çubuğu:** arama kutusu, durum düğmeleri, departman listesi, görünüm seçici.
4. **Kullanıcı listesi:** **Kartlar** veya **Liste** görünümü.

**Alanlar (süzgeç çubuğu):**

| Alan | Ne işe yarar | Nasıl doldurulur / seçenekler | Örnek | Zorunlu |
|---|---|---|---|---|
| "Ad soyad veya e-posta ile ara..." | Listeyi ada veya e-postaya göre süzer | Yazdıkça uygulanır; sağdaki **✕** aramayı temizler | zeynep | Hayır |
| **Tümü (N) / Aktif (N) / Pasif (N)** | Duruma göre süzer | Birine tıklayın; parantezde sayı | Pasif (1) | Hayır |
| **Tüm Departmanlar** | Departmana göre süzer | Listeden seçin; departman tanımlı değilse görünmez | Muhasebe | Hayır |
| **Kartlar / Liste** | Görünümü değiştirir | Birine tıklayın | Liste | — |

**Listede görünenler:**

- **Kart görünümü:** baş harf simgesi, ad, e-posta (yanında **E-postayı Kopyala** simgesi), durum rozeti **Aktif** / **Pasif**; "Departman:", "Ünvan:" (yoksa "Atanmamış"), "Sistem Rolü:"; "İzin Kataloğu Ek İzinleri" bölümünde ek izin rozetleri veya "Ek izin tanımlanmadı (Rol izinleri geçerli)".
- **Liste görünümü sütunları:** **KULLANICI**, **E-POSTA**, **DEPARTMAN**, **ÜNVAN**, **SİSTEM ROLÜ**, **EK İZİNLER** (`+N İzin` veya `-`), **DURUM**, **İŞLEMLER**.

**Durumlar:**

| Durum | Anlamı |
|---|---|
| **Aktif** (yeşil) | Kişi giriş yapabilir; paket kotasından bir kişi düşer. |
| **Pasif** (kırmızı) | Kişinin girişi engellenir; kota harcamaz. Bilgileri ve geçmişi korunur. |

**Düğmeler:**

| Düğme | Ne yapar | Dikkat |
|---|---|---|
| **Yenile** | Listeyi ve kotayı yeniden yükler. | — |
| **+ Yeni Kullanıcı Tanımla** / **+ İlk Kullanıcıyı Tanımla** | **Kullanıcı Tanımlama** penceresini açar. | Kota doluysa yalnızca pasif kullanıcı ekleyebilirsiniz. |
| **Düzenle** | **Kullanıcıyı Düzenle** penceresini açar. | — |
| **Sil** | **Kullanıcıyı Sil** onay penceresini açar. | **Geri alınamaz.** Geçici kapatmak için silmek yerine **Pasif** yapın. |
| **E-postayı Kopyala** (simge) | E-postayı panoya kopyalar ("✓ E-posta panoya kopyalandı!"). | — |

**Boş ekran:** "Henüz Tanımlı İnsan Personel Yok" (düğme **+ İlk Kullanıcıyı Tanımla**) veya "Filtreye Uygun Kullanıcı Bulunamadı" (süzgeçleri temizleyin). Yüklenirken "Kullanıcılar yükleniyor...".

#### Kullanıcı Tanımlama / Kullanıcıyı Düzenle penceresi

Alt başlık: "Personel kimlik, rol, şifre ve ek izinler". Sağ üstteki **✕** kaydetmeden kapatır.

[[EKRAN: ca-m-kullanici-tanimlama | Kullanıcı Tanımlama penceresi: kimlik alanları, şifre, durum kartları, Sistem Yetki Rolü ve İzin Kataloğundan Ek İzinler listesi | Kullanıcı Yönetimi ekranında "+ Yeni Kullanıcı Tanımla"ya tıklayın; Sistem Yetki Rolü olarak "Entegrasyon Yöneticisi"ni seçin ki rol açıklama kutusu görünsün; pencerenin tamamının görüntüsünü alın]]

| Alan | Ne işe yarar | Nasıl doldurulur / seçenekler | Örnek | Zorunlu |
|---|---|---|---|---|
| **Adı Soyadı \*** | Kişinin ekranlarda görünen adı | Ad ve soyad yazın | Zeynep Kaya | Evet |
| **Email (Kullanıcı Adı) \*** | Kişinin giriş adı | Geçerli bir e-posta yazın; küçük harfe çevrilir. RECOrion'da başka bir kullanıcıda kayıtlı olmamalıdır. | zeynep.kaya@orneklojistik.com.tr | Evet |
| **Günlük maliyet (₺, KDV hariç, isteğe bağlı)** | Proje maliyeti ve tasarruf hesabı | Kişinin bir iş gününe düşen maliyetini yazın. Proje maliyetinde bu kişinin yürüttüğü adımlara "gerçekleşen iş günü × günlük maliyet" olarak yansır. Boş bırakılırsa kaldırılır. | 2500 | Hayır |
| **Departman** | Kişinin birimi | "Departman Seçiniz..." listesinden seçin; yeni kayıtta ilk departman önceden seçilidir | Muhasebe | Hayır |
| **Ünvan** | Kişinin görevi | "Ünvan Seçiniz..." listesinden seçin; yeni kayıtta ilk ünvan önceden seçilidir | Muhasebe Uzmanı | Hayır |
| **Giriş Şifresi** | Kişinin ilk şifresi | En az 6 karakter. Düzenlemede boş bırakırsanız şifre değişmez. Göz simgesi (**Göster** / **Gizle**) şifreyi gösterir. | — | Yeni kayıtta evet |
| **🔑 Güçlü Şifre Oluştur** | Güvenli şifre üretir | Tıklayın; 14 karakterli, büyük-küçük harf, rakam ve simge içeren şifre üretilir ("🔑 Güçlü şifre üretildi!"). Ardından "✓ Şifre hazır" ve **Şifreyi Kopyala** görünür. | — | — |
| **Kullanıcı Durumu** | Girişe açık mı | İki kart: **Aktif** ("Sisteme giriş yapabilir, oturum açabilir") veya **Pasif** ("Girişi engellenir, kota harcamaz"). Varsayılan Aktif. | Aktif | Evet |
| **Sistem Yetki Rolü (Süper Yöneticinin Tanımladığı)** | Kişinin izin paketi | Listeden bir rol seçin (sistem rollerinin yanında "(Sistem Rolü)" yazar). Boş seçenek "Standart Kullanıcı Rolü..." temel izinleri verir. Yeni kayıtta **Uzman Kullanıcı** önceden seçilir. Seçince altında "Rol Tanımı: <ad>", "N adet temel yetki", rolün açıklaması ve ilk 8 iznin kısa kodu (fazlası "+N daha...") görünür. | Uzman Kullanıcı | Hayır |
| **İzin Kataloğundan Ek İzinler** | Rolün dışında tek tek izin vermek | "Seçilen rolün dışındaki özel yetkileri bu alandan personele doğrudan atayabilirsiniz." Sayaç "N Ek İzin Seçili". "İzin ara..." kutusu ve modül listesi (**Tüm Modüller** ve izin modülleri: Şirket & Platform, Genel Bakış & Raporlar, Kullanıcılar & Roller, AI Personel, Organizasyon, Kurum Zekâsı, Entegrasyon & Otomasyon, Kredi & Kullanım, Projeler & İş Akışı, Sohbet & İletişim, Kurum Hafızası, Bağlantılarım). Her satırda izin adı, kısa kodu ve açıklaması vardır; satıra tıklamak işaretler veya kaldırır. | Şirket Geneli Pano | Hayır |

**Pencere düğmeleri:**

| Düğme | Ne yapar | Dikkat |
|---|---|---|
| **Vazgeç** | Kaydetmeden kapatır. | — |
| **Kullanıcıyı Tanımla** (yeni) / **Güncelle** (düzenleme) | Kaydeder ("Kaydediliyor..."). Başarıda "'<Ad>' kullanıcısı başarıyla tanımlandı." | Şifre e-postayla gönderilmez; şifreyi kişiye siz güvenli bir yoldan iletirsiniz. |

> **Dikkat:** Rolü seçilen kullanıcı yalnızca o rolün izinlerini ve işaretlediğiniz ek izinleri alır. Bir kullanıcıya **Şirket Yöneticisi** rolü verirseniz o kişi bütün yönetim yetkilerine sahip olur; dikkatli verin.

#### Kullanıcıyı Sil penceresi

Başlık altında "Bu işlem geri alınamaz". Metin: "<Ad> (<e-posta>) kullanıcısını silmek istediğinize emin misiniz? Bu kullanıcı sisteme giriş yapamayacak ve açtığı oturumlar sonlandırılacaktır." Düğmeler: **Vazgeç**, **Evet, Sil** ("Siliniyor...").

[[EKRAN: ca-m-kullanici-sil | Kullanıcıyı Sil onay penceresi | Kullanıcı Yönetimi'nde bir test kullanıcısının kartında "Sil"e tıklayın; açılan pencerenin görüntüsünü alın, "Vazgeç" ile kapatın]]

**Hata ve uyarı mesajları:**

| Mesaj | Anlamı | Ne yapmalı |
|---|---|---|
| "Adı Soyadı alanı zorunludur." | Ad boş. | Adı yazın. |
| "Geçerli bir e-posta adresi giriniz." | E-posta hatalı (ör. `@` yok). | E-postayı düzeltin. |
| "Yeni kullanıcı için en az 6 karakterli bir şifre belirleyiniz veya "Güçlü Şifre Oluştur" butonunu kullanınız." | Şifre kısa veya boş. | **🔑 Güçlü Şifre Oluştur**'a tıklayın. |
| "'<e-posta>' e-posta adresine sahip bir kullanıcı zaten kayıtlı." | Bu e-posta başka bir kullanıcıda. | Başka bir e-posta kullanın veya mevcut kaydı düzenleyin. |
| "… e-posta adresi başka bir kullanıcı tarafından kullanılmaktadır." | Düzenlemede başka birinin e-postasını yazdınız. | E-postayı düzeltin. |
| "Satın aldığınız '<paket>' paketinin azami İnsan Kullanıcı kotası (N Kullanıcı) dolmuştur. …" | Kota dolu, aktif kullanıcı eklenemez. | Kişiyi **Pasif** ekleyin, başka bir hesabı pasife alın veya paketinizi yükseltin. |
| "Paket kotanız doludur. Pasif kullanıcıyı aktifleştiremezsiniz." | Kota dolu. | Önce başka bir hesabı pasife alın. |
| "Şirketin başka aktif Şirket Yöneticisi kalmıyor. Önce başka bir kullanıcıya Şirket Yöneticisi rolünü atayın." | Son şirket yöneticisini silmek, pasife almak veya rolünü değiştirmek istediniz. | Önce başka birine Şirket Yöneticisi rolü verin. |
| "Sahip olmadığınız izinleri atayamazsınız: …" | Kendinizde olmayan bir izni vermeye çalıştınız. | O izni şirket yöneticisine verdirin. |

**Adım adım örnek: yeni kullanıcı**

> **Örnek:** Ayşe Yılmaz, muhasebeci Zeynep Kaya'yı sisteme ekliyor.
> 1. **Personel › Kullanıcı Yönetimi**'ne tıklar; kota kartında "Kalan Kontenjan: 2" görür.
> 2. **+ Yeni Kullanıcı Tanımla**'ya tıklar.
> 3. **Adı Soyadı**: Zeynep Kaya; **Email (Kullanıcı Adı)**: zeynep.kaya@orneklojistik.com.tr.
> 4. **Departman**: Muhasebe; **Ünvan**: Muhasebe Uzmanı; **Günlük maliyet**: 2500.
> 5. **🔑 Güçlü Şifre Oluştur**'a, sonra **Şifreyi Kopyala**'ya tıklar ve şifreyi Zeynep'e şirket içi güvenli kanaldan iletir.
> 6. **Sistem Yetki Rolü** olarak **Uzman Kullanıcı** seçili kalır.
> 7. **Kullanıcıyı Tanımla**'ya tıklar. Kota sayacı `4 / 5` olur.

**Adım adım örnek: işten ayrılan kişiyi pasife alma**

> **Örnek:** Can Öztürk başka bir şirkete geçti.
> 1. Can'ın kartında **Düzenle**'ye tıklayın.
> 2. **Kullanıcı Durumu**'nda **Pasif**'i seçin; şifre alanını boş bırakın.
> 3. **Güncelle**'ye tıklayın. Can artık giriş yapamaz; kota bir kişi boşalır. Geçmiş işleri ve kayıtları korunur.

**İpucu, dikkat ve sık sorulan sorular:**

> **İpucu:** İşten ayrılanı silmek yerine **Pasif** yapın. Böylece geçmiş kayıtlarda kimin ne yaptığı görünmeye devam eder; gerekirse tekrar **Aktif** yaparsınız.

> **Dikkat:** Günlük maliyet kişisel veridir (KVKK). Kişi bazında yalnızca kullanıcı düzenleme izni olanlar görür; panolarda yalnızca toplam görünür.

- *Kullanıcı şifresini unuttu, ne yaparım?* Kişinin kartında **Düzenle** → **🔑 Güçlü Şifre Oluştur** → **Güncelle**; yeni şifreyi kişiye iletin.
- *Bir kişiye yalnızca bir menüyü nasıl açarım?* Rolünü değiştirmeden **İzin Kataloğundan Ek İzinler**'de o menünün iznini işaretleyin (menü-izin eşlemesi **Menü ağacı** bölümündedir).
- *Kendi şirketimize özel rol tanımlayabilir miyim?* Evet; ekranın altındaki **Şirkete özel roller** kartını kullanın (aşağıda).

### Şirkete özel roller

**Bu bölüm ne işe yarar?** Sistem rolleri ihtiyacınızı tam karşılamadığında şirketinize özel bir izin paketi (ör. "Muhasebe Onaylayıcı") tanımlarsınız. Tanımladığınız rol, kullanıcı formundaki rol listesinde **Şirkete özel roller** başlığı altında görünür ve kullanıcıya atanır.

**Kimler görür / değiştirir?** Kart Kullanıcı Yönetimi ekranının altındadır. **Yeni rol** için "Şirkete Özel Rol Tanımlama", düzenleme (kalem simgesi) için "Rol Düzenleme", silme (çöp kutusu simgesi) için "Rol Silme" izni gerekir. Varsayılan olarak üçü de yalnız Şirket Yöneticisi'ndedir.

| Alan | Ne işe yarar | Nasıl doldurulur | Örnek | Zorunlu |
|---|---|---|---|---|
| **Rol adı** | Listede görünen ad | En fazla 64 karakter; şirket rolleri ve sistem rolleri arasında benzersiz (büyük/küçük harf fark etmez) | Muhasebe Onaylayıcı | Evet |
| **Açıklama** | Rolün amacı | Kısa bir cümle | RECSlip ve iş adımı onayları | Hayır |
| **İzinler** | Rolün açtığı işlemler | Modüllere göre gruplanmış listeden işaretleyin | İş Adımı Onaylama (Vekâleten), Kredi ve Kullanımı Görme | Hayır |

> **Dikkat:** Şirket Yöneticisi olmayan biri, kendisinde olmayan bir izni role ekleyemez; o izinler listede soluk ve seçilemez görünür ("Sizde olmayan izinleri role ekleyemezsiniz"). RECDx'e özel izinler hiçbir şirket rolüne verilemez.

> **Dikkat:** Atanmış kullanıcısı olan rol silinmez ("Bu role atanmış N kullanıcı var. Silmeden önce kullanıcıların rolünü değiştirin."). Rolün izinlerini değiştirdiğinizde role bağlı kullanıcıların izinleri bir sonraki işlemlerinde yeni hâline göre hesaplanır.

**Mesajlar:** **"Rol oluşturuldu."** · **"Rol güncellendi."** · **"Rol silindi."** · **"'<ad>' adında bir rol zaten var."**

## AI Ajan İşe Alım

### AI Ajan İşe Alım ekranı

**Bu ekran ne işe yarar?** Şirketinizde çalışacak AI personeli işe alır, düzenler, işten çıkarır, yeniden işe alır ve silersiniz. Her AI personelin bir ünvanı, departmanı, RECAi kademesi, otonomi seviyesi ve rol promptu vardır. Ayrıca her AI personele öğrenme kaynağı (doküman, web sayfası, video, araştırma) eklersiniz. Ekrandaki başlık "AI Ajanlarının İşe Alım / Tanımlama", alt başlık "Şirketiniz bünyesinde görev yapacak otonom yapay zeka personellerini işe alın, ünvan atayın ve çalışma durumlarını yönetin."

**Ne zaman kullanırım?** Bir işi yapay zekâya devretmek istediğinizde (ör. teklif hazırlayan bir satış asistanı), bir AI personele şirket prosedürlerini öğretmek istediğinizde, bir AI personelin ayarlarını değiştirmek veya onu durdurmak istediğinizde.

**Kimler görür / değiştirir?** "AI Personel İşe Alma", "AI Personel Ayarları ve Bilgi Kaynakları" veya "AI Personeli İşten Çıkarma" izni olanlar (Şirket Yöneticisi, Proje Yöneticisi, Personel ve Organizasyon Yöneticisi, Yapay Zeka ve Ajan Lideri). Ekranı görenler her işlemi yapamaz: işe alma, düzenleme ve işten çıkarma/silme ayrı izinlerdir. Örneğin Proje Yöneticisi işe alabilir ama düzenleme veya işten çıkarma denediğinde "Bu işlem için yetkiniz yok." uyarısı alır.

[[EKRAN: ca-ai-ajan-ise-alim | AI Ajan İşe Alım: üstte kota rozeti ve "+ Yeni AI Ajan İşe Al", dört sayaç kartı, kart görünümünde AI personeller | Şirket Yöneticisi ile giriş yapın; Personel › AI Ajan İşe Alım; "3D Kartlar" görünümünde, aktif ve pasif personeli olan bir şirkette görüntü alın]]

**Ekranın bölümleri:**

1. Başlık, **Yenile**, kota rozeti ("📊 Paket Kotası: A / M Ajan (<paket>)" veya kota doluysa "⚠️ Paket Kotası Doldu: …"), **+ Yeni AI Ajan İşe Al**.
2. Dört sayaç: **Toplam AI Ajan Kadrosu**, **Aktif Görevde**, **Pasif / İşten Çıkarılan**, **Kullanılabilir Şirket Ünvanı**.
3. Arama, durum süzgeci ve görünüm seçici.
4. Ünvan yoksa uyarı: "**Şirketinize henüz bir ünvan tanımlanmamış:** AI Ajan işe alabilmek için ajana atanacak en az bir şirket ünvanı bulunmalıdır." ve **Ünvan Tanımlarına Git →** düğmesi.
5. AI personel kartları veya tablo.

**Alanlar (süzgeçler):**

| Alan | Ne işe yarar | Nasıl doldurulur / seçenekler | Örnek | Zorunlu |
|---|---|---|---|---|
| "AI Ajan adı, model, ünvan veya departmanda ara..." | Listeyi süzer | Ad, RECAi kademesi, ünvan, departman veya açıklamada arar | analist | Hayır |
| **Tümü (N) / Aktif (N) / Pasif / Çıkarılan (N)** | Duruma göre süzer | Birine tıklayın | Aktif | Hayır |
| **3D Kartlar / Liste** | Görünüm | Birine tıklayın | Liste | — |

**Listede görünenler:**

- **Kart:** robot simgesi (aktifse yeşil, pasifse kırmızı), ad, kısa kimlik ("ID: xxxxxxxx..."), durum rozeti **AKTİF GÖREVDE** / **PASİF (ÇIKARILDI)**, "🤖 <RECAi kademesi>", ünvan (yoksa "Ünvan Atanmamış"), departman, otonomi (L1/L2/L3), açıklama (yoksa "Açıklama belirtilmemiş."), "İşe Alım Tarihi:", "İşten Çıkma Tarihi:" (aktifse "— (Görevde)").
- **Liste sütunları:** **AI AJAN ADI** (altında açıklamanın başı), **RECAi**, **ŞİRKET ÜNVANI**, **DEPARTMAN** (yoksa "Genel"), **İŞE ALIM TARİHİ**, **İŞTEN ÇIKMA TARİHİ** ("— (Aktif)" veya "🚪 tarih"), **DURUM**, **İŞLEMLER**.

**Düğmeler:**

| Düğme | Ne yapar | Dikkat |
|---|---|---|
| **Yenile** | Listeyi yeniden yükler. | — |
| **+ Yeni AI Ajan İşe Al** / **+ İlk AI Ajanınızı İşe Alın** | **AI Personel İşe Al** sihirbazını açar. | Kota doluysa pasiftir. |
| **Ünvan Tanımlarına Git →** | Ünvan Tanımları ekranına geçer. | — |
| **Düzenle** | **AI Ajan Bilgilerini Düzenle** penceresini açar. | — |
| **İşten Çıkar** (üzerine gelince "AI Ajanını Pasife Çek / İşten Çıkar") | İşten çıkarma penceresini açar. | Onay ister. **Tekrar İşe Al** ile geri alınır. |
| **Tekrar İşe Al** (kartta) / **İşe Al** (listede) | Pasif AI personeli hemen aktifleştirir ("'<ad>' yeniden işe alındı ve aktifleştirildi."). | Onay sormaz. Kota doluysa yapılamaz. |
| **📚 Kaynaklar (N)** | AI personelin **Uzmanlık Dokümanları** penceresini açar (N = kaynak sayısı). | — |
| Çöp kutusu simgesi ("Tamamen Sil") | Silme onay penceresini açar. | **Geri alınamaz.** Durdurmak için **İşten Çıkar**'ı kullanın. |

**Otonomi seviyeleri:**

| Seviye | Anlamı | Ne zaman seçilir |
|---|---|---|
| **L1** | Öneri + insan onayı: her adımda onay ister. | Yeni işe alınan, henüz güvenilirliği bilinmeyen AI personel. |
| **L2** | Rutin işleri kendisi yapar, kritik adımlarda onay ister. | Bir süre iyi sonuç vermiş AI personel. |
| **L3** | Tam otonom; yalnızca nihai onay. Sihirbazda yoktur, düzenleme penceresinden verilir. | Riskin düşük, tekrarı çok işler. |

**Boş ekran:** "Henüz İşe Alınmış AI Ajan Bulunmuyor" (**+ İlk AI Ajanınızı İşe Alın**) veya "Aramaya Uygun AI Ajan Bulunamadı".

#### AI Personel İşe Al sihirbazı

Dört adımlı bir penceredir. Üstteki adım çubuğu: **1 Departman → 2 Unvan → 3 RECAi ve Rol → 4 Kimlik**. Geçtiğiniz bir adıma tıklayarak geri dönebilirsiniz. Altında özet şeridi: "Sektör: …" (manifestodaki sektörlerinizden; yoksa "Tanımlı değil"), "Departman: …", "Unvan: …", "Kota: A / M". Kota doluysa kırmızı uyarı: "'<paket>' paketinizin AI personel kotası dolu. İşe almak için paket yükseltin veya bir personeli pasife alın." Alt düğmeler: **Geri**, **İleri** (adım tamamlanmadan pasif), son adımda **İşe Al**; sağ üstte **Kapat**.

[[EKRAN: ca-m-ise-alim-sihirbazi | AI Personel İşe Al sihirbazının 1. adımı: departman grupları ve arama kutusu | AI Ajan İşe Alım ekranında "+ Yeni AI Ajan İşe Al"a tıklayın; Departman adımında görüntü alın]]

[[EKRAN: ca-m-ise-alim-recai-rol | Sihirbazın 3. adımı: RECAi seçimi, RECAi yetenekleri, otonomi, sorumluluklar ve rol promptu | Sihirbazda bir departman ve unvan seçip "İleri" ile 3. adıma geçin; görüntü alın]]

| Adım / Alan | Ne işe yarar | Nasıl doldurulur / seçenekler | Örnek | Zorunlu |
|---|---|---|---|---|
| 1 · "Departman ara…" | Departman listesini süzer | Yazın | operasyon | Hayır |
| 1 · Departman seçimi | AI personelin çalışacağı birim | Gruplardan birini seçin: **Şirketinizin departmanları**, **Meslek grubunuza özel (katalog)**, **Sektörünüze özel (katalog)**, **Genel departmanlar (katalog)**. Satırda ad, varsa "Meslek grubunuz" rozeti, açıklama ve "· N uygun unvan"; katalog departmanlarında "· işe alımda şirketinize eklenir". | Operasyon | Evet |
| 2 · "Unvan ara…" | Unvanları süzer | Yazın | — | Hayır |
| 2 · Unvan seçimi | AI personelin görevi | Seçili departmandaki unvanlardan birini seçin. Rozetler: kıdem (Uzman Yardımcısı, Uzman, Kıdemli Uzman, Takım Lideri, Yönetici), **Şirketinizde tanımlı** veya **Meslek grubunuza uygun**. Uygun unvan yoksa "Bu departmanda uygun unvan yok". | Sevkiyat Planlama Uzmanı | Evet |
| 3 · RECAi | AI personelin çalışacağı kademe | Paketinizdeki kademeler "ad — açıklama · katsayı N" olarak listelenir; paketinizde olmayanlar "(paketinizde yok)" ile seçilemez. Altında "Bu unvan için önerilen: RECAi …". Paketiniz değiştirmeye izin vermiyorsa 🔒 kilitli: "'<paket>' paketiniz RECAi değiştirmeye izin vermiyor; bu unvan için RECAi … kullanılır." | RECAi Mergen | Evet |
| 3 · RECAi Yetenekleri | Görsel, ses ve belge okuma yetenekleri | **RECAi Görsel**, **RECAi Ses**, **RECAi Okur** kutularını açın veya kapatın; varsayılan açıktır. Paketinizde olmayan kilitli: "🔒 Paketinizde yok — paketinizi yükseltin". | Görsel açık | Hayır |
| 3 · Otonomi | Ne kadar kendi başına çalışacağı | "L1 · öneri + insan onayı" veya "L2 · rutin işleri kendisi yapar" | L1 | Evet |
| 3 · Sorumluluklar | Unvanın katalogdaki sorumlulukları | Salt okunur liste | — | — |
| 3 · Rol promptu | AI personelin talimatı | Unvanın hazır rol promptu gelir; "Şirketinize göre düzenleyebilirsiniz." Paketiniz izin vermiyorsa kilitli: "… RECOrion kataloğundaki hazır rol promptu kullanılır." | — | — |
| 4 · AI personel adı | Görünen ad | En çok 128 karakter | Sevkiyat Asistanı Deniz | Evet |
| 4 · İşe alım tarihi | Kadroya giriş tarihi | Tarih seçin; varsayılan bugün | 03.11.2026 | Hayır |
| 4 · Açıklama | Özel görev notu | Unvan açıklaması önceden dolar; şirkete özel notu ekleyin | Günlük sevkiyat planını hazırlar | Hayır |

4\. adımdaki bilgi notu: "İşe alımdan sonra AI Ajan İşe Alım sekmesinden personele öğrenme dokümanı ekleyebilir veya sektör ve unvan araştırması yaptırabilirsiniz." Başarıda: "'<ad>' <departman> departmanında <unvan> olarak işe alındı." Katalogdan seçtiğiniz departman ve unvan işe alımda şirketinize kendiliğinden eklenir.

#### AI Ajan Bilgilerini Düzenle penceresi

Alt başlık: "Ajan adı, RECAi, şirket ünvanı ve işe alım tarihi". **✕** kapatır.

[[EKRAN: ca-m-ai-ajan-duzenle | AI Ajan Bilgilerini Düzenle penceresi: ad, ünvan, kilitli departman, RECAi, otonomi, tarih, maliyet, açıklama ve rol promptu ile Deep Search düğmesi | AI Ajan İşe Alım ekranında bir kartta "Düzenle"ye tıklayın; pencerenin tamamını kaydırarak iki parça görüntü alın]]

| Alan | Ne işe yarar | Nasıl doldurulur / seçenekler | Örnek | Zorunlu |
|---|---|---|---|---|
| **AI Ajan Adı \*** | Görünen ad | Yazın | Sevkiyat Asistanı Deniz | Evet |
| **Şirket Ünvanı \*** | Görevi | "-- Ünvan Seçiniz --" listesinden "<ünvan> (<kategori>)" seçin. Değiştirince departman, önerilen RECAi, otonomi ve rol promptu ünvandan gelir. | Sevkiyat Planlama Uzmanı (OPERASYON) | Evet |
| **Bağlı Departman (🔒 Ünvandan Otomatik Gelir)** | Birimi | Değiştirilemez; ünvanın departmanıdır | Operasyon | — |
| **RECAi \*** (rozet "Değiştirilebilir" veya "Paketinizde sabit") | Kademe | "Varsayılan (paketteki ilk RECAi)" veya paketteki kademeler. Paket izin vermiyorsa kilitli. | RECAi Derin | Evet (izin varsa) |
| **Otonomi Seviyesi (Değiştirilebilir)** | Kendi başına çalışma | **L1 - Standart (Onaylı)**, **L2 - Yarı Otonom**, **L3 - Tam Otonom** | L2 | Evet |
| **RECAi Yetenekleri** | Görsel, ses, belge okuma | Sihirbazdaki gibi | — | Hayır |
| **📅 AI Ajan İşe Alım Tarihi (Tanımlama Tarihi) \*** | Kadroya giriş | Tarih seçin | 03.11.2026 | Evet |
| **Günlük sabit maliyet (₺, KDV hariç, isteğe bağlı)** | Lisans, kiralama gibi sabit gider | "Boş: yalnızca token maliyeti". AI personelin asıl maliyeti kullandığı yapay zekânın TL karşılığıdır; sabit bir gider varsa yazın. | 150 | Hayır |
| **AI Ajan Açıklaması / Özel Görev Notu** | Şirketteki özel rolü | Yazın | — | Hayır |
| **Sistem Rol Promptu (Persona & Talimatlar) \*** | Talimat | Ünvandan gelir; düzenleyebilirsiniz. Paketiniz izin vermiyorsa salt okunur: "'<paket>' paketinizde ünvanın hazır rol promptu kullanılır ve değiştirilemez. Deep Search bulguları yine personelin hafızasına kaydedilir." | — | — |

**Pencere düğmeleri:**

| Düğme | Ne yapar | Dikkat |
|---|---|---|
| **🌐 Sektör & Ünvan Deep Search ile Eğit ve Prompt Yaz** | Şirketinizin sektörünü ve bu ünvanın sektörde ne iş yaptığını internette araştırır. Sürerken "Şirket Sektörü & Ünvan Dinamikleri İnternette Derinlemesine Taranıyor..." ve üç aşama görünür. Sonunda "Sektör & Ünvan Deep Search Analiz Raporu" kartı ("N Bilgi Maddesi Hazır", "ŞİRKET SEKTÖRÜ: …", "SEKTÖREL ÜNVAN: …", "Tespit Edilen Temel Yetkinlik & Kural Maddeleri:") çıkar ve rol promptu zenginleşir; bulgular AI personelin hafızasına hemen işlenir. | Kredi harcar; birkaç dakika sürebilir. |
| **✨ Hızlı Prompt** | Seçili RECAi ile hızlıca rol promptu taslağı yazar. | Önce ad ve ünvan girilmiş olmalı. Kredi harcar. |
| **İptal** | Kaydetmeden kapatır. | — |
| **Değişiklikleri Kaydet** | Kaydeder ("Kaydediliyor..."). | — |

#### AI Ajanını İşten Çıkar / Pasife Al penceresi

Metin: "'<ad>' adlı AI ajanının şirket içindeki aktif görevi sonlandırılacaktır."

| Alan | Ne işe yarar | Nasıl doldurulur | Örnek | Zorunlu |
|---|---|---|---|---|
| **🚪 İşten Çıkma / Pasife Çekilme Tarihi \*** | Görevin bittiği tarih | Tarih seçin; varsayılan bugün | 03.11.2026 | Evet |
| **İşten Çıkarma / Pasife Çekme Nedeni** | Kayıt için gerekçe | Yazın | Proje tamamlandı | Hayır |

Düğmeler: **Vazgeç**, **Evet, İşten Çıkar ve Pasife Al** ("İşleniyor..."). Pasif AI personel kotaya sayılmaz ve iş almaz.

#### AI Ajanını Silmek İstiyor musunuz? penceresi

Metin: "'<ad>' AI ajanı sistemden kalıcı olarak silinecektir." Düğmeler: **Vazgeç**, **Evet, Sil**.

> **Dikkat:** Silme geri alınamaz. AI personelin geçmişini korumak istiyorsanız silmek yerine **İşten Çıkar**'ı kullanın.

#### Uzmanlık Dokümanları penceresi

Başlık "<Ad> — Uzmanlık Dokümanları", rozet "RAG / Kolektif Hafıza", altında ünvan • RECAi kademesi. **✕** ve alttaki **Kapat** kapatır. Bu pencerede AI personele öğreteceğiniz kaynakları yönetirsiniz.

[[EKRAN: ca-m-uzmanlik-dokumanlari | Uzmanlık Dokümanları penceresi: "Nasıl öğrenir" bilgi kutusu, Bilgi katmanları paneli, kaynak sekmeleri ve kütüphane listesi | AI Ajan İşe Alım ekranında bir kartta "📚 Kaynaklar (N)"e tıklayın; en az bir doküman yüklenmiş bir AI personelde görüntü alın]]

**Pencerenin bölümleri:**

1. **Nasıl öğrenir** kutusu: "Yüklediğiniz doküman ve görseller arka planda okunur (OCR ve görsel açıklama dahil), kişisel veriler maskelenir ve size bir öğrenme kartı sunulur. Siz onayladıktan sonra AI personel bu bilgiyi kullanır; onaylanmayan doküman öğrenilmez."
2. **Bilgi katmanları** paneli: "Bu personel bir soruyu cevaplarken şu kaynakları birlikte kullanır; projede çalışırken proje ekleri de eklenir." Katman kutuları (ad, belge sayısı, onaylı doküman veya bilgi): personelin kendi dokümanları, ünvan bilgisi, şirket ortak bilgisi, RECOrion katalog bilgisi. Altında sınama kutusu.
3. Kaynak sekmeleri: **Dosya Yükle**, **Web Sayfası Ekle**, **YouTube / Video**, **Deep Search**.
4. **📚 Ajanın Öğrenme & Hafıza Kütüphanesi** ("N Kaynak").

| Sekme / Alan | Ne işe yarar | Nasıl doldurulur | Örnek | Zorunlu |
|---|---|---|---|---|
| Bilgi katmanları · "Bilgisini sınayın: örn. fire oranı nasıl hesaplanır?" + **Sına** | AI personelin bir konuda bilgisi olup olmadığını dener | En az 2 karakterlik bir soru yazıp **Sına**'ya tıklayın. Her katmanda bulunan parçalar listelenir; hiç yoksa "Bu soru için hiçbir katmanda bilgi bulunamadı; personel bu konuda bilgisi olmadığını söyler." | Hasarlı teslimatta tutanak nasıl tutulur? | — |
| Dosya Yükle · "Doküman veya Görsel Yüklemek İçin Tıklayın ya da Sürükleyin" | Dosya öğretir | PDF, Word, Excel, PowerPoint (eski biçimler dahil), metin dosyaları (TXT, CSV, MD, JSON, XML, HTML) ve görseller (PNG, JPG, WEBP, BMP, TIFF); en fazla 50 MB. Birden çok dosya seçilebilir. Görsellerdeki şema ve çizimler de açıklanıp öğrenilir. | teslimat_proseduru.pdf | — |
| Web Sayfası Ekle · **Web Sayfası URL'si \*** | Bir web sayfasını öğretir | "Araştırma İçin Web Sayfası Tanımla": sayfa adresini yazın | https://… | Evet |
| Web Sayfası Ekle · **Konu / Kaynak Başlığı (Opsiyonel)** | Listede görünecek başlık | Yazın | Taşıma yönetmeliği | Hayır |
| YouTube / Video · **YouTube Video URL'si \*** | Bir videoyu öğretir | "İzleyerek & Dinleyerek Öğrenme": başlık, kanal ve altyazı/konuşma metni hafızaya alınır | https://youtu.be/… | Evet |
| YouTube / Video · **Video Başlığı / Konu Notu (Opsiyonel)** | Listede görünecek başlık | Yazın | Forklift güvenliği | Hayır |
| Deep Search · **Sektör & Ünvan Deep Search Başlat** | Sektör ve ünvan araştırması | "Şirket Sektörü & Ünvan Uzmanlık Araştırması": şirket sektörü ve personelin ünvanı internette araştırılır, hafızaya kaydedilir, rol promptu güncellenir | — | — |
| Deep Search · **Araştırma Konusu / Pazar Sorusu \*** | Özel konuda araştırma | "Özel Konulu Deep Search & Öğrenme Motoru": konuyu yazın; web'de araştırılır, özetlenir, hafızaya kaydedilir | 2026 e-irsaliye değişiklikleri | Evet |

Sekme düğmeleri: **Web Sayfasını İncele ve Hafızaya Kaydet**, **Videoyu ve Transkripti Hafızaya Kaydet**, **İnternette Araştır, Sentezle ve Hafızaya Kaydet**.

**Kütüphane satırı:** ad, tür rozeti (PDF, DOCX… / WEB SAYFASI / YOUTUBE VİDEO / 🔍 DEEP SEARCH), boyut veya tür açıklaması ("Web Sayfası İçeriği", "Video Transkripti", "Araştırma & Sentez Raporu"), tarih, durum rozeti, "N görsel açıklandı", "KVKK: … maskelendi".

**Doküman durumları:**

| Durum | Anlamı | Ne yapmalı |
|---|---|---|
| **Yüklendi** | Dosya alındı. | Bekleyin. |
| **İşleniyor** | Metin ve görseller okunuyor, kişisel veriler maskeleniyor. Liste 4 saniyede bir kendini yeniler. | Bekleyin. |
| **Onay bekliyor** | Öğrenme kartı hazır. | **İncele ve onayla**'ya tıklayın. |
| **Öğrenildi** | AI personel bu bilgiyi kullanıyor. | — |
| **Reddedildi** | Siz reddettiniz; öğrenilmedi. | Gerekirse silin. |
| **Karantinada** | İçerik güvenliği sorunu bulundu. | İnceleyin; **Yeniden işle** veya silin. |
| **İşlenemedi** | Dosya okunamadı. | **Yeniden işle** veya farklı biçimde yükleyin. |
| **Eski sürüm** | Yerine yeni sürüm yüklendi. | — |
| **Hafızada** / **Eklendi** | Web, video ve araştırma kaynakları hafızaya kaydedildi. | — |

**Satır düğmeleri:** **İncele ve onayla** (Onay bekliyor) veya **Aç** (yalnızca dosyalarda) Doküman İnceleme penceresini açar; **Önizle** / **Kapat** ("Ayrıştırılan Metin ve Hafıza Önizlemesi:"); **Sayfayı Aç** / **Videoyu Aç** (yeni sekmede); **Raporu İndir** (Deep Search); **İndir** (orijinal dosya); çöp kutusu ("Dokümanı ve Hafıza Kaydını Sil") onay sorar: "… dokümanı ve bu dokümandan oluşturulan ajanın kolektif hafıza (vektör RAG) kayıtları kalıcı olarak silinecektir." **Vazgeç** / **Evet, Sil**.

#### Doküman İnceleme penceresi

Başlık "<dosya adı> · sürüm N". Üstte durum rozeti, tür · boyut, "N sayfa", "N sayfa OCR ile okundu", "N görsel açıklandı", "N bilgi parçası". İşlenirken "Doküman işleniyor: metin ve görseller okunuyor, kişisel veriler maskeleniyor, öğrenme kartı hazırlanıyor…". KVKK notu: "KVKK: … maskelendi. AI personel bu verileri görmez; asıl dosya erişim kontrollü depoda kalır."

[[EKRAN: ca-m-dokuman-inceleme | Doküman İnceleme penceresi: özet, anahtar bilgiler, test soruları ve alt düğmeler | Uzmanlık Dokümanları penceresinde durumu "Onay bekliyor" olan bir dokümanın "İncele ve onayla" düğmesine tıklayın]]

| Alan | Ne işe yarar | Nasıl doldurulur | Örnek | Zorunlu |
|---|---|---|---|---|
| **Özet** | Öğrenme kartının özeti | Yalnızca "Onay bekliyor" durumunda düzenlenir | — | — |
| **Öğrenilecek anahtar bilgiler (her satır bir bilgi)** | AI personelin öğreneceği maddeler | "Onaydan önce düzeltebilirsiniz. Dokümanın tamamı da parçalar halinde öğrenilir." | Hasarlı teslimatta tutanak 24 saat içinde tutulur. | — |
| **Test soruları (N)** | Öğrenmeyi sınama | Çoktan seçmeli sorular, doğru şık ✓ ile. **AI personeli test et**'e tıklayınca personel sınanır: "Test sonucu: X/Y doğru (%Z) · <RECAi>", her soruda "AI personelin cevabı: …". | — | — |
| **Öğrenilecek metinden örnek (KVKK maskeli)** | Maskelenmiş metni gösterir | Açılır bölüm | — | — |

**Pencere düğmeleri:**

| Düğme | Ne yapar | Dikkat |
|---|---|---|
| **Sil** | Dokümanı siler. | Onay sorar: "… silinsin mi? AI personel bu dokümandan öğrendiklerini de unutur." Geri alınamaz. |
| **İndir** | Orijinal dosyayı indirir. | — |
| **Yeniden işle** | İşlenemedi veya Karantinada durumundaki dokümanı yeniden işler. | — |
| **Yeni sürüm yükle** | Öğrenilmiş dokümanın yeni sürümünü yükler. | Yeni sürüm onaylanana kadar mevcut sürüm kullanılır. |
| **Reddet** | Dokümanı öğretmeden reddeder. | İsteğe bağlı gerekçe sorar. |
| **Onayla ve öğret** | Öğrenme kartını onaylar ("Doküman onaylandı; AI personel artık bu bilgiyi kullanıyor."). | — |

**Hata mesajları (AI Ajan İşe Alım):**

| Mesaj | Anlamı | Ne yapmalı |
|---|---|---|
| "Lütfen AI Ajan adını giriniz." | Ad boş. | Adı yazın. |
| "Lütfen AI Ajan için bir şirket ünvanı seçiniz." | Ünvan seçilmedi. | Ünvan seçin; ünvan yoksa önce **Ünvan Tanımları**'nda oluşturun. |
| "Paketinizin azami AI Ajan kotası (N Ajan) dolmuştur. Bu ajanı tekrar aktif edebilmek için paketinizi yükseltiniz." | Kota dolu. | Başka bir AI personeli işten çıkarın veya paketinizi yükseltin. |
| "Ajanın atanmış bir ünvanı bulunmuyor." | Ünvansız personelde sektör ve ünvan araştırması. | Önce ünvan atayın. |
| "… dosya boyutu 50 MB sınırını aşıyor." | Dosya büyük. | Dosyayı bölün veya küçültün. |
| "Web sayfası içeriği alınamadı veya erişilemedi: …" / "Video bilgisi veya transkripti alınamadı: …" | Kaynak okunamadı. | Adresi kontrol edin; sayfa giriş gerektiriyorsa dosya olarak yükleyin. |
| "Bu adres öğrenme kaynağı olarak kullanılamaz: …" | Güvenlik nedeniyle izin verilmeyen adres. | Başka bir kaynak kullanın. |

**Adım adım örnek: AI personel işe alma**

> **Örnek:** Mehmet Demir, sevkiyat planlarını hazırlayacak bir AI personel işe alıyor.
> 1. **Personel › AI Ajan İşe Alım**'a tıklar; kota rozetinde "📊 Paket Kotası: 2 / 5 Ajan" görür.
> 2. **+ Yeni AI Ajan İşe Al**'a tıklar.
> 3. **Departman** adımında "Operasyon"u seçer, **İleri**.
> 4. **Unvan** adımında "Sevkiyat Planlama Uzmanı"nı seçer, **İleri**.
> 5. **RECAi ve Rol** adımında **RECAi Mergen** ve otonomi **L1** seçili kalır; rol promptunu okur, **İleri**.
> 6. **Kimlik** adımında ad olarak "Sevkiyat Asistanı Deniz" yazar, **İşe Al**'a tıklar. Kart "AKTİF GÖREVDE" olarak görünür.

**Adım adım örnek: AI personele prosedür öğretme**

> **Örnek:** Ayşe Yılmaz, Deniz'e teslimat prosedürünü öğretiyor.
> 1. Deniz'in kartında **📚 Kaynaklar (0)**'a tıklar.
> 2. **Dosya Yükle** sekmesinde `teslimat_proseduru.pdf` dosyasını sürükler. "1 dosya yüklendi. İşlendikten sonra onayınıza sunulacak; AI personel onaydan sonra öğrenir." bildirimi gelir.
> 3. Durum **Onay bekliyor** olunca **İncele ve onayla**'ya tıklar; anahtar bilgilerde bir maddeyi düzeltir.
> 4. **AI personeli test et** ile sınar: "Test sonucu: 4/5 doğru (%80)".
> 5. **Onayla ve öğret**'e tıklar; durum **Öğrenildi** olur.
> 6. **Bilgi katmanları**'nda "Hasarlı teslimatta ne yapılır?" yazıp **Sına** ile bilginin bulunduğunu doğrular.

**İpucu, dikkat ve sık sorulan sorular:**

> **İpucu:** Bir bilgiyi aynı ünvandaki bütün AI personele öğretmek istiyorsanız tek tek yüklemek yerine **Ünvan Tanımları** ekranındaki **Bilgi Dokümanları**'nı kullanın.

> **Dikkat:** KVKK: Yüklenen dokümanlardaki T.C. kimlik numarası, IBAN, kart numarası, e-posta ve telefon maskelenir; AI personel maskelenmiş metni görür. Dokümanlar şirketinize özeldir; RECDx yöneticileri dahil kimse göremez. Onaylamadığınız doküman öğrenilmez.

- *RECAi kademesini neden değiştiremiyorum?* Paketiniz buna izin vermiyordur (alan 🔒 kilitli görünür). Paket yükseltmek için RECDx ile görüşün.
- *Pasife aldığım AI personel kredi harcar mı?* Hayır; iş almaz ve kotaya sayılmaz.
- *Deep Search ne kadar kredi harcar?* İnternette araştırma ve rol promptu yazma kredi harcar; ne kadar harcandığını **Kredi ve Kullanım** ekranında "Derin araştırma" ve "Rol promptu üretimi" satırlarında görürsünüz.

# Organizasyon

## Departmanlar

### Departmanlar ekranı

**Bu ekran ne işe yarar?** Şirketinizin operasyonel, idari ve teknik departmanlarını tanımlarsınız. Ünvanlar, kullanıcılar ve AI personel bu departmanlara bağlanır. Departmanları elle tanımlayabilir veya RECOrion kataloğundan sektörünüze uygun olanları tek seferde ekleyebilirsiniz. Ekrandaki başlık "Şirket Departmanları Tanımlama", alt başlık "Sistemi kullanacak operasyonel, idari ve teknik departmanları tanımlayın ve yönetin."

**Ne zaman kullanırım?** İlk kurulumda, yeni bir birim kurulduğunda, bir birimin adı veya görevi değiştiğinde.

**Kimler görür / değiştirir?** "Departman Yönetimi" izni olanlar (Şirket Yöneticisi, Personel ve Organizasyon Yöneticisi, Operasyon Yöneticisi).

[[EKRAN: ca-departmanlar | Departmanlar: üstte "Katalogdan Ekle" ve "+ Yeni Departman Tanımla", üç sayaç kartı, kart görünümünde departmanlar | Şirket Yöneticisi ile giriş yapın; Organizasyon › Departmanlar; "Kart Görünümü"nde görüntü alın]]

**Ekranın bölümleri:**

1. Başlık ve düğmeler: **Yenile**, **Katalogdan Ekle**, **+ Yeni Departman Tanımla**.
2. Sayaç kartları: **Tanımlı Departman**, **Atanmış Aktif Personel / Ajan**, **Sistem Entegrasyon Durumu**.
3. Arama ve görünüm: arama kutusu, **Kart Görünümü** / **Liste Görünümü**.
4. Departman kartları veya tablo.

**Alanlar:**

| Alan | Ne işe yarar | Nasıl doldurulur | Örnek | Zorunlu |
|---|---|---|---|---|
| "Departman adı veya açıklama ile ara..." | Listeyi süzer | Yazdıkça uygulanır | sevkiyat | Hayır |
| **Kart Görünümü / Liste Görünümü** | Görünüm | Birine tıklayın | Liste Görünümü | — |

**Listede görünenler:** Kartta departman adı, "N Aktör" rozeti (bağlı aktif insan personel ve AI personel sayısı), açıklama (yoksa "Bu departman için henüz özel açıklama girilmedi."), oluşturulma tarihi. Liste sütunları: **Departman Adı**, **Açıklama**, **Aktör Sayısı**, **Oluşturulma Tarihi**, **İşlemler**.

**Düğmeler:**

| Düğme | Ne yapar | Dikkat |
|---|---|---|
| **Yenile** | Listeyi yeniler. | — |
| **Katalogdan Ekle** (üzerine gelince "Sektörünüze uygun RECOrion departmanlarını ekleyin") | **Katalogdan Departman Ekle** penceresini açar. | Öneriler manifestodaki sektör ve NACE bilgisine dayanır. |
| **+ Yeni Departman Tanımla** / **+ İlk Departmanı Tanımla** | **Yeni Departman Tanımla** penceresini açar. | — |
| **Düzenle** ("Departmanı Düzenle") | **Departmanı Düzenle** penceresini açar. | — |
| **Sil** ("Departmanı Sil") | Silme onayını açar. | **Geri alınamaz.** Bağlı ünvan ve personelin departman bağı boşa çıkabilir. |

**Boş ekran:** "Henüz Tanımlı Departman Yok" (**+ İlk Departmanı Tanımla**) veya "Eşleşen Departman Bulunamadı".

#### Yeni Departman Tanımla / Departmanı Düzenle penceresi

Alt başlık: "Departman adı ve açıklama bilgileri".

[[EKRAN: ca-m-departman-tanimla | Yeni Departman Tanımla penceresi | Departmanlar ekranında "+ Yeni Departman Tanımla"ya tıklayın; ad ve açıklama doldurulmuş hâliyle görüntü alın]]

| Alan | Ne işe yarar | Nasıl doldurulur | Örnek | Zorunlu |
|---|---|---|---|---|
| **Departman Adı \*** | Birimin adı | En çok 128 karakter; şirkette benzersiz olmalı | Sevkiyat Planlama | Evet |
| **Departman Açıklaması** | Görevi, sorumluluk alanı, hedefleri | Yazın; AI personel bu açıklamayı bağlam olarak kullanır | Günlük araç ve rota planlaması | Hayır |

Düğmeler: **İptal**, **Departmanı Tanımla** (yeni) / **Değişiklikleri Kaydet** (düzenleme).

#### Katalogdan Departman Ekle penceresi

Metin: "Şirketinizin sektör ve meslek gruplarına göre önerilen RECOrion departmanları. Eklenen departmanlara ait unvanlar AI personel işe alımında önerilir."

[[EKRAN: ca-m-katalogdan-departman | Katalogdan Departman Ekle penceresi: gruplar, onay kutuları ve "Ekli" rozetleri | Departmanlar ekranında "Katalogdan Ekle"ye tıklayın; sektörleri seçilmiş bir şirkette görüntü alın]]

| Alan | Ne işe yarar | Nasıl doldurulur | Örnek | Zorunlu |
|---|---|---|---|---|
| **Tümünü seç (N departman)** | Hepsini seçer veya bırakır | Kutuyu işaretleyin | — | — |
| Gruplar: **Meslek grubunuza özel**, **Sektörünüze özel**, **Genel departmanlar** | Önerileri gruplar | Her grupta **Bu grubu seç** / **Bu grubun seçimini kaldır** | — | — |
| Departman satırı | Eklenecek departman | Onay kutusunu işaretleyin. Satırda ad, açıklama ve "N uygun unvan" yazar. Şirketinizde zaten varsa **Ekli** rozeti çıkar ve seçilemez. | Depo Yönetimi | En az 1 |

İlk iki grup açılışta seçili gelir. Düğmeler: **Vazgeç**, **N Departmanı Ekle** ("N departman eklendi."). Uygun departman yoksa: "Uygun departman bulunamadı — Şirketinizin sektör ve meslek grubu bilgilerini Sektörel Manifesto sekmesinden kontrol edin."

#### Departmanı Silmek İstiyor musunuz? penceresi

Metin: "'<ad>' departmanı silinecektir." Düğmeler: **Vazgeç**, **Evet, Sil**.

**Hata mesajları:**

| Mesaj | Anlamı | Ne yapmalı |
|---|---|---|
| "Lütfen departman adını giriniz." | Ad boş. | Adı yazın. |
| "'<ad>' adında bir departman zaten tanımlı." | Aynı adlı departman var. | Farklı bir ad verin veya mevcut olanı düzenleyin. |

**Adım adım örnek:**

> **Örnek:** Ayşe Yılmaz, Örnek Lojistik A.Ş.'nin departmanlarını kuruyor.
> 1. **Organizasyon › Departmanlar**'a tıklar.
> 2. **Katalogdan Ekle**'ye tıklar. **Sektörünüze özel** grubunda "Depo Yönetimi", "Filo Yönetimi", "Gümrük İşlemleri" seçili gelir. **Genel departmanlar** grubundan "Muhasebe" ve "İnsan Kaynakları"nı da işaretler.
> 3. **5 Departmanı Ekle**'ye tıklar; "5 departman eklendi." bildirimi gelir.
> 4. Katalogda olmayan "Sevkiyat Planlama" için **+ Yeni Departman Tanımla**'ya tıklar, adı ve açıklamayı yazıp **Departmanı Tanımla**'ya tıklar.

**İpucu ve sık sorulan sorular:**

> **İpucu:** Katalogdan eklemeden önce **Sektörel Manifesto**'da sektörlerinizi ve NACE kodlarınızı seçin; öneriler çok daha isabetli olur.

- *Departmanı silersem çalışanlar ne olur?* Kullanıcılar ve AI personel silinmez; yalnızca departman bağları boşa çıkar. Silmeden önce ünvanları ve kişileri başka bir departmana taşıyın.
- *Katalogdan eklediğim departmanı değiştirebilir miyim?* Evet; **Düzenle** ile adını ve açıklamasını değiştirebilirsiniz.

## Ünvan Tanımları

### Ünvan Tanımları ekranı

**Bu ekran ne işe yarar?** AI personel ve çalışanlar için ünvanları (rolleri) tanımlarsınız. Her ünvanın bir departmanı, sektörü, önerilen RECAi kademesi, otonomi seviyesi ve rol promptu vardır; ünvana atanan AI personel bunları devralır. Ünvana **Bilgi Dokümanları** yükleyerek o ünvandaki bütün AI personele aynı bilgiyi öğretirsiniz. Ekrandaki başlık "Şirket Ünvanları ve Rol Tanımları", alt başlık "RECOrion kataloğundan sektörünüze uygun unvanı seçin veya şirketinize özel unvan tanımlayın. RECAi yeni tanımları inceleyip ekosisteme kazandırır."

**Ne zaman kullanırım?** AI personel işe almadan önce, yeni bir görev tanımı gerektiğinde, bir ünvandaki bütün AI personelin davranışını değiştirmek istediğinizde.

**Kimler görür / değiştirir?** "Ünvan Tanımlama" izni olanlar (Şirket Yöneticisi, Personel ve Organizasyon Yöneticisi, Yapay Zeka ve Ajan Lideri). Şirkete özel ünvan tanımlamak paketinize de bağlıdır.

[[EKRAN: ca-unvan-tanimlari | Ünvan Tanımları: üç sayaç, arama ve ünvan kartları (RECAi değerlendirme kutusu ve rol promptu bölümüyle) | Şirket Yöneticisi ile giriş yapın; Organizasyon › Ünvan Tanımları; "Kart Görünümü"nde görüntü alın]]

**Ekranın bölümleri:**

1. Başlık ve düğmeler: **Yenile**, **+ Yeni Ünvan Tanımla**.
2. Sayaçlar: **Şirkete Tanımlı Ünvan**, **RECAi: Ana Şablona Eklenen**, **Ünvanı Taşıyan Aktör Sayısı**.
3. Arama ("Ünvan adı, kategori veya açıklama ara...") ve **Kart Görünümü** / **Liste Görünümü**.
4. Ünvan kartları veya tablo.

**Listede görünenler:**

- **Kart:** kategori (sektör), "🤖 <RECAi kademesi>", otonomi (L1/L2/L3), "🏢 <departman>", "N Aktör", ünvan adı, açıklama; RECAi değerlendirme kutusu: **RECAi: Ana Şablona Eklendi** (ünvan sistem genelinde faydalı bulunup ortak şablona eklendi) veya **Şirkete Özel Yerel Ünvan**, altında RECAi'nin geri bildirimi ve fayda puanı; **Sistem Rol Promptu** bölümü (**Tamamını Gör** / **Gizle**); en çok 5 yetenek etiketi (fazlası `+N`); "Kod: <KOD>".
- **Liste sütunları:** **Ünvan Adı & Kod**, **Kategori**, **RECAi Değerlendirmesi** (Ana Şablona Eklendi / Şirkete Özel), **Önerilen Model** (RECAi kademesi), **Aktör**, **İşlemler**.

**Düğmeler:**

| Düğme | Ne yapar | Dikkat |
|---|---|---|
| **Yenile** | Listeyi yeniler. | — |
| **+ Yeni Ünvan Tanımla** / **+ İlk Ünvanı Tanımla** | **Şirket Ünvanı Tanımla** penceresini açar. | Paketiniz izin vermiyorsa uyarı: "'<paket>' paketiniz şirkete özel ünvan tanımlamaya izin vermiyor. Sistem ünvanlarından seçebilir veya paketinizi yükseltebilirsiniz." |
| **Bilgi Dokümanları** (listede simge) | **<Ünvan> · Bilgi Dokümanları** penceresini açar. | — |
| **Düzenle** | **Ünvanı Düzenle** penceresini açar. | — |
| **Sil** | Silme onayını açar. | **Geri alınamaz.** |

**Boş ekran:** "Henüz Şirketinize Tanımlı Ünvan Yok" (**+ İlk Ünvanı Tanımla**) veya "Eşleşen Ünvan Bulunamadı".

#### Şirket Ünvanı Tanımla / Ünvanı Düzenle penceresi

Alt başlık: "Sektörel şablon seçimi ve otomatik rol promptu". Üstteki bilgi: "**RECAi Otonom Denetim Motoru:** Tanımlayacağınız ünvan ve Sistem Rol Promptu, kaydettiğiniz anda RECAi modeli tarafından incelenecek; sistem geneli ve sektör için faydalı görülenler otomatik olarak Ana Sistem Şablonuna eklenecektir."

[[EKRAN: ca-m-unvan-tanimla | Şirket Ünvanı Tanımla penceresi: departman, ünvan kaynağı seçimi, şablon listesi, ünvan bilgileri ve rol promptu | Ünvan Tanımları ekranında "+ Yeni Ünvan Tanımla"ya tıklayın; "Sistem Tanımlamalarından Seçin" seçiliyken şablon listesini açıp görüntü alın]]

| Alan | Ne işe yarar | Nasıl doldurulur / seçenekler | Örnek | Zorunlu |
|---|---|---|---|---|
| **🏢 Bağlı Departman \*** | Ünvanın birimi | "-- Şirket Departmanı Seçiniz --" listesinden seçin. Departman yoksa: "Henüz tanımlı bir departmanınız yok. Lütfen önce Departmanlar sekmesinden bir departman oluşturunuz." | 📁 Operasyon | Evet |
| **Ünvan Kaynağı ve Tanımlama Yöntemi:** (yalnızca yeni ünvanda) | Nasıl tanımlayacağınız | **Sistem Tanımlamalarından Seçin** (hazır şablon) veya **Sektör Seçerek Kendi Ünvanını Yaz** (serbest) | — | — |
| **Sektörel Şablon Ünvanları (Seçilince Rol Promptu Otomatik Yüklenir)** | Hazır şablon seçer | Süzgeçler: **🏢 Şirket Sektörlerim (…)**, her sektör adı, **Tüm Sektörler (N)**. "Şablon seçmek için tıklayın …" kutusuna tıklayıp "Şablon ünvanlarda ara..." ile arayın; sektörünüze uygun olanlarda "📁 Sektörünüz" rozeti. Seçince ad, kod, kategori, açıklama, rol promptu, yetenekler, RECAi ve otonomi forma gelir. Sonuç yoksa "Eşleşen sistem şablonu bulunamadı. Filtreyi 'Tüm Sektörler' olarak değiştirebilirsiniz." | Depo Sorumlusu | Şablon yönteminde evet |
| **Ünvan Adı \*** | Ünvanın adı | Yazın | Sevkiyat Planlama Uzmanı | Evet |
| **Sektör / Kategori** | Ünvanın sektörü | "🏢 Şirketinizin Sektörleri" (⭐) ve "Diğer Sektörler & Kategoriler" (TEKSTIL, YAZILIM, ANALİZ, FİNANS, HUKUK, TASARIM, OPERASYON, ÜRETİM / İMALAT, GENEL) | OPERASYON | Evet |
| **Ünvan Açıklaması / Görev Tanımı** | Temel sorumluluk | Yazın | Günlük rota ve araç planı | Hayır |
| **Önerilen RECAi (Paket Kapsamında)** | Bu ünvandaki AI personelin varsayılan kademesi | "Varsayılan (paketteki ilk RECAi)" veya paketteki kademeler; pakette olmayanlar "(paketinizde yok)" ile seçilemez | RECAi Hızlı | Hayır |
| **Otonomi Seviyesi** | Varsayılan otonomi | **L1 - Standart (Her adımda onay)**, **L2 - Yarı Otonom (Kritik adımlarda onay)**, **L3 - Tam Otonom (Yalnızca nihai onay)** | L1 | Evet |
| **Sistem Rol Promptu (Persona & Talimatlar) \*** | AI personelin talimatı | Rolün kimliğini, görev tanımını, kalite kurallarını ve çıktı standartlarını yazın. **✨ <RECAi kademesi> ile Prompt Yazdır** düğmesi ünvan bilgisinden otomatik yazar (önce **Ünvan Adı** girilmeli; kredi harcar). | — | Evet |
| **Gerekli Yetenekler (Virgülle ayırınız)** | Yetenek etiketleri | Virgülle ayırarak yazın | Rota planlama, Excel, ADR | Hayır |

**RECAi ile sohbetle tanımla** (rol promptu başlığının yanında): ünvanı kendi cümlelerinizle anlatırsınız (ne iş yapacak, hangi çıktıları üretecek, kime teslim edecek, neyi asla yapmamalı). RECAi eksikleri kısa sorularla sorar ve sağ tarafta taslağı (ünvan, iş tanımı, sorumluluklar, yetkinlikler, başarı ölçütleri, rol promptu) her turda günceller; taslak hazır olunca "hazır" rozeti çıkar. **Forma al** ile taslak forma aktarılır (sorumluluklar ve başarı ölçütleri açıklamaya eklenir); kayıt formdaki düğmeyle yapılır. Sohbet hiçbir şeyi kendiliğinden kaydetmez ve şirketinizin kredisini kullanır. Her sektör için çalışır.

Düğmeler: **İptal**, **Ünvanı Tanımla & AI Kontrolünden Geçir** (yeni; sürerken "RECAi İnceliyor & Kaydediyor...") veya **Değişiklikleri Kaydet** (düzenleme). Başarıda "'<ad>' ünvanı şirketinize özel olarak başarıyla tanımlandı." veya "🌟 RECAi: '<ad>' ünvanı sistem geneli için faydalı bulundu ve ana şablona otomatik eklendi!"

> **Dikkat:** RECAi, sistem geneli için faydalı bulduğu ünvanı (ad, kategori, açıklama, rol promptu, yetenekler) **diğer şirketlerin de kullanabileceği ortak şablona** ekler. Rol promptuna şirkete özel gizli bilgi, kişi adı veya müşteri verisi yazmayın. Bu tür bilgileri **Bilgi Dokümanları** ile verin; dokümanlar yalnızca şirketinize aittir.

#### Ünvan · Bilgi Dokümanları penceresi

Başlık "<Ünvan> · Bilgi Dokümanları". Metin: "Bu unvandaki tüm AI personeller, onayladığınız dokümanları ve görselleri öğrenir (Şirket Unvan Bilgisi). Şirketinize özel bilgidir; RECDx dahil başka kimse göremez."

[[EKRAN: ca-m-unvan-bilgi-dokumanlari | Ünvan Bilgi Dokümanları penceresi: yükleme alanı ve doküman listesi | Ünvan Tanımları ekranında "Liste Görünümü"ne geçin; bir ünvan satırındaki "Bilgi dokümanları" simgesine tıklayın]]

| Öğe | Ne yapar |
|---|---|
| "Doküman veya görsel yükleyin (tıklayın ya da sürükleyin)" | Dosya yükler; kabul edilen biçimler AI personel dokümanlarıyla aynıdır. |
| Doküman satırı | Ad, tür · boyut · sürüm ve durum rozeti. Durumlar AI personel dokümanlarıyla aynıdır. |
| **İncele ve onayla** / **Aç** | **Doküman İnceleme** penceresini açar (AI Ajan İşe Alım bölümünde anlatıldı). |
| **Kapat** | Pencereyi kapatır. |

Boşsa: "Bu unvana henüz bilgi dokümanı eklenmedi."

#### Ünvanı Silmek İstiyor musunuz? penceresi

Metin: "'<ad>' ünvanı silinecektir. Bu ünvana atanmış AI personelleri veya çalışanların ünvan bağı boşa çıkacaktır." Düğmeler: **Vazgeç**, **Evet, Sil**.

**Hata mesajları:**

| Mesaj | Anlamı | Ne yapmalı |
|---|---|---|
| "Lütfen ünvan adını giriniz." | Ad boş. | Adı yazın. |
| "Lütfen ünvanın bağlı olacağı departmanı seçiniz." | Departman seçilmedi. | Departman seçin. |
| "Sistem Rol Promptu boş bırakılamaz. Lütfen bir şablon seçin veya kendi rol promptunuzu yazın." | Prompt boş. | Şablon seçin veya **✨ … ile Prompt Yazdır**'a tıklayın. |
| "AI Rol Promptu oluşturulurken hata: …" | Prompt yazdırılamadı. | Biraz sonra tekrar deneyin; krediniz bitmiş olabilir. |

Aynı ünvan kodu şirketinizde varsa koda otomatik bir ek konur.

**Adım adım örnek: şablondan ünvan**

> **Örnek:** Ayşe Yılmaz bir depo ünvanı tanımlıyor.
> 1. **Organizasyon › Ünvan Tanımları** → **+ Yeni Ünvan Tanımla**.
> 2. **🏢 Bağlı Departman**: Depo Yönetimi. **Sistem Tanımlamalarından Seçin** seçili kalır.
> 3. Şablon kutusuna tıklar, "depo" yazar, "Depo Sorumlusu" şablonunu seçer; form dolar.
> 4. **Önerilen RECAi**'yi **RECAi Hızlı** yapar.
> 5. **Ünvanı Tanımla & AI Kontrolünden Geçir**'e tıklar ve kartta RECAi değerlendirmesini okur.

**Adım adım örnek: kendi ünvanınızı yazma**

> **Örnek:**
> 1. **Sektör Seçerek Kendi Ünvanını Yaz**'ı seçin; **Ünvan Adı**: "Sevkiyat Planlama Uzmanı", **Sektör / Kategori**: OPERASYON, **Ünvan Açıklaması** yazın.
> 2. **✨ RECAi Mergen ile Prompt Yazdır**'a tıklayın; gelen promptu okuyup şirketinize göre düzeltin.
> 3. **Gerekli Yetenekler**'i yazıp kaydedin.

**Adım adım örnek: ünvana ortak bilgi yükleme**

> **Örnek:**
> 1. Liste görünümünde "Sevkiyat Planlama Uzmanı" satırındaki **Bilgi Dokümanları** simgesine tıklayın, `rota_kurallari.pdf` dosyasını yükleyin.
> 2. Durum **Onay bekliyor** olunca **İncele ve onayla** → **Onayla ve öğret**. Bu ünvandaki bütün AI personel bilgiyi kullanır.

**Sık sorulan sorular:**

- *Ünvanın rol promptunu değiştirirsem mevcut AI personel etkilenir mi?* Ünvan, yeni atamalarda varsayılanları belirler. Mevcut bir AI personelin promptunu değiştirmek için **AI Ajan İşe Alım** › **Düzenle**'de ünvanı yeniden seçebilir veya promptu düzenleyebilirsiniz.
- *"RECAi: Ana Şablona Eklendi" ne demek?* RECAi ünvanınızı genel olarak faydalı buldu ve ortak şablona ekledi. Bu yüzden rol promptuna gizli bilgi yazmayın.

# Kurum Zekâsı

## Sektörel Manifesto

### Sektörel Manifesto ekranı

**Bu ekran ne işe yarar?** Şirketinizin sektörlerini, NACE faaliyet kodlarını ve kurumsal manifestosunu (ilkeleriniz, etik kurallarınız, yapay zekâ vizyonunuz) yönetirsiniz. Bütün AI personel kararlarında bu bilgiyi referans alır. Katalog departman ve ünvan önerileri, işe alım sihirbazı ve ünvan şablonu süzgeci de sektörünüze göre şekillenir. Manifestoyu elle yazabilir veya RECAi'ye yazdırabilirsiniz. Ekrandaki başlık "Kurumsal Manifesto & Stratejik Vizyon", alt başlık "Şirketinizin anayasasını, etik ilkelerini ve AI vizyonunu yönetin; manifestoyu RECAi'ye düzenletin."

**Ne zaman kullanırım?** İlk kurulumda (departmanlardan önce), şirket yeni bir faaliyet alanına girdiğinde, ilke ve önceliklerinizi AI personele anlatmak istediğinizde.

**Kimler görür / değiştirir?** "Sektörel Manifesto Yönetimi" izni olanlar (Şirket Yöneticisi, Yapay Zeka ve Ajan Lideri, Operasyon Yöneticisi).

[[EKRAN: ca-sektorel-manifesto | Sektörel Manifesto: sektör etiketleri, NACE kodları, RECAi ile düzenleme kartı ve manifesto metni | Şirket Yöneticisi ile giriş yapın; Kurum Zekâsı › Sektörel Manifesto; en az bir sektör ve iki NACE kodu seçili hâlde görüntü alın]]

**Ekranın bölümleri:**

1. Başlık ve düğmeler: **Değişiklikleri Sıfırla**, **💾 Kurumsal Manifestoyu Kaydet**.
2. **Şirket Sektörleri & NACE Faaliyet Alanları Düzenleme** kartı (rozet "Tüm AI Ajanlarının Karar Referansı"): **Faaliyet Sektörleri** ve **NACE Rev.2 Faaliyet Kodları** bölümleri.
3. **RECAi ile Kurumsal Manifestoyu Düzenle veya Baştan Üret** kartı ("Müşteri paketinizde izin verilen modeller kullanılır").
4. **Kurumsal Manifesto Metni (Doğrudan Düzenlenebilir)**: karakter ve kelime sayacı, metin alanı, altta ikinci kaydet düğmesi.

**Alanlar:**

| Alan | Ne işe yarar | Nasıl doldurulur / seçenekler | Örnek | Zorunlu |
|---|---|---|---|---|
| **Faaliyet Sektörleri (N seçili)** | Şirketinizin sektörleri | Seçili sektörler "📁 <ad>" etiketi olarak görünür; **×** ("Sektörü Kaldır") çıkarır, **Temizle** hepsini kaldırır. Boşsa "Henüz sektör eklenmedi. …" | LOJİSTİK | Hayır |
| **+ Sistem Sektör Kataloğundan Ekle...** | Katalogdan sektör ekler | Listeden seçin; seçili olanlar "(Zaten Seçili)" yazar. Sektörün varsayılan NACE kodları da otomatik eklenir. | Lojistik | Hayır |
| "Örn: YENİLENEBİLİR ENERJİ..." + **+ Ekle** | Katalogda olmayan sektör ekler | Yazıp **+ Ekle**'ye tıklayın veya Enter'a basın; büyük harfe çevrilir | SOĞUK ZİNCİR | Hayır |
| **NACE Rev.2 Faaliyet Kodları (N kod seçili)** | Faaliyet kodlarınız | "kod - açıklama" etiketleri; **×** ("Kodu Kaldır"), **Tümünü Temizle** | 52.29 - Taşımacılığı destekleyici diğer faaliyetler | Hayır |
| "NACE kodu veya sektör ara (Örn: 13.20, Dokuma, Yazılım, 62.01)..." | Kod arar | En az 2 karakter yazın; sonuçlarda kod, ad, sektör grubu ve **+ Ekle** / **✓ Seçili**. Satıra tıklayınca eklenir; Enter yazdığınızı doğrudan kod olarak ekler. | 49.41 | Hayır |
| **Kullanılacak RECAi** | Manifestoyu yazacak kademe | "Varsayılan (paketteki ilk RECAi)" veya paketteki kademeler | RECAi Derin | Hayır |
| **Özel Vurgu veya Düzenleme Notu (Opsiyonel)** | RECAi'ye talimat | Ne vurgulanmasını istediğinizi yazın | Zamanında teslim ve iş güvenliğini öne çıkar | Hayır |
| **Kurumsal Manifesto Metni** | Manifestonun kendisi | Doğrudan yazın veya RECAi'ye yazdırın | — | Hayır |

**Düğmeler:**

| Düğme | Ne yapar | Dikkat |
|---|---|---|
| **✨ Seçili AI ile Manifestoyu Düzenle** | Mevcut metni, sektörleri, NACE kodlarını ve notunuzu kullanarak RECAi'ye manifesto yazdırır ("AI Hazırlıyor..."). Sonuç metin alanına gelir. | **Kaydedilmez**; okuyup **💾 Kurumsal Manifestoyu Kaydet** ile kaydedin. Kredi harcar. |
| **Değişiklikleri Sıfırla** | Metni, sektörleri ve NACE kodlarını son kaydedilmiş hâline döndürür ("Tüm değişiklikler kaydedilmiş orijinal değerlere sıfırlandı."). | Değişiklik yoksa pasiftir. Onay sormaz. |
| **💾 Kurumsal Manifestoyu Kaydet** (üstte ve altta) | Metni, sektörleri ve NACE kodlarını kaydeder ("Kurumsal manifesto, sektörler ve NACE kodları başarıyla kaydedildi!"). | Önceki metne dönüş yoktur; önemli bir metni değiştirmeden önce kopyasını alın. |

**Adım adım örnek:**

> **Örnek:** Ayşe Yılmaz manifestoyu hazırlıyor.
> 1. **Kurum Zekâsı › Sektörel Manifesto**'ya tıklar.
> 2. **+ Sistem Sektör Kataloğundan Ekle...** listesinden "Lojistik"i seçer; NACE kodları otomatik gelir. Arama kutusuna "49.41" yazıp karayolu taşımacılığı kodunu da ekler.
> 3. **Kullanılacak RECAi**: RECAi Derin; **Özel Vurgu**: "Zamanında teslim, iş güvenliği ve müşteri bilgisinin gizliliği".
> 4. **✨ Seçili AI ile Manifestoyu Düzenle**'ye tıklar; gelen metni okuyup bir paragrafı elle düzeltir.
> 5. **💾 Kurumsal Manifestoyu Kaydet**'e tıklar.

**Sık sorulan sorular:**

- *Kaydetmeden başka menüye geçersem ne olur?* Değişiklikleriniz kaybolabilir. Önce kaydedin.
- *Sektör değiştirince ne etkilenir?* Katalog departman önerileri, işe alım sihirbazının önerileri ve ünvan şablonu süzgeci.

## Beyin AI

### Beyin AI ekranı

**Bu ekran ne işe yarar?** Beyin AI'nın hangi RECAi kademesiyle çalışacağını seçer, AI personelin sohbetlerden çıkardığı şirket geneli bilgileri onaylar veya reddeder ve Beyin AI ile konuşursunuz. Ekrandaki başlık "Beyin AI — RECAi".

**Ne zaman kullanırım?** Kurulumda kademe seçmek için; onay kuyruğunda bekleyen bilgi olduğunda; şirketinizle ilgili bir planlama sorusuna yanıt aradığınızda (ör. "Hangi departmanda eksik ünvan var?").

**Kimler görür / değiştirir?** Menüyü "Beyin AI Ayarları" izni olanlar görür (Şirket Yöneticisi, Yapay Zeka ve Ajan Lideri). **RECAi** listesi ve **Kaydet** düğmesi yalnızca Şirket Yöneticisinde ve "Şirket Ayarlarını Yönetme" izni olanlarda etkindir; diğerlerinde liste kilitli görünür. Onay kuyruğundaki **Onayla** / **Reddet** düğmeleri "Kurum Hafızasına Ekleme ve Onaylama" izni olanlarda (varsayılan olarak Şirket Yöneticisi ve Proje Yöneticisi) görünür. Sohbet herkese açıktır ama her yanıt kredi harcar.

[[EKRAN: ca-beyin-ai | Beyin AI ekranı: RECAi seçimi, Kurum Hafızası Onay Kuyruğu ve Beyin AI ile konuş kartı | Şirket Yöneticisi ile giriş yapın; Kurum Zekâsı › Beyin AI; onay kuyruğunda en az bir bilgi ve sohbette bir soru-yanıt varken görüntü alın]]

**Ekranın bölümleri:**

1. **Beyin AI — RECAi** kartı: "Beyin AI, şirketinizin organizatör yapay zekasıdır. Paketinizdeki RECAi adlarından birini seçebilirsiniz." Sağ üstte **Kaydet**.
2. **Kurum Hafızası Onay Kuyruğu (N)** kartı: "AI personelin sohbetlerden çıkardığı şirket geneli bilgiler. Onaylanan bilgiyi şirketin tüm AI personeli kullanır."
3. **Beyin AI ile konuş** kartı: "Konuşmalarınız yalnızca size görünür. Her yanıt şirketinizin kredisinden düşer."

**Alanlar:**

| Alan | Ne işe yarar | Nasıl doldurulur / seçenekler | Örnek | Zorunlu |
|---|---|---|---|---|
| **RECAi** | Beyin AI'nın kademesi | İlk seçenek **Platform varsayılanı (<ad>)**; paketinizde yoksa "— paketinizde yok, paketteki ilk uygun RECAi kullanılır". Diğerleri "<kademe> — <açıklama> · katsayı X"; paketinizde olmayanlar seçilemez. Not: "Katsayı yükseldikçe RECAi daha güçlü ama işlem başına daha çok kredi harcar." | RECAi Derin | Hayır |
| Mesaj kutusu | Beyin AI'ya sorunuz | "Beyin AI'ya bir soru sorun… (Enter gönderir, Shift+Enter yeni satır)"; en çok 8000 karakter | Bu ay hangi projelere öncelik verelim? | Göndermek için evet |

**Beyin AI neleri bilir?** Yalnız şirketinizi: manifesto, departmanlar, ünvanlar, AI personel, kurum hafızası ve güncel iş durumu (projeler ve adım durumları, onayınızı bekleyen adımlar, karantinadaki adımlar). İş durumu **konuşan kullanıcının yetkisiyle** sınırlıdır: proje yönetim yetkisi olmayan kullanıcı yalnız ekibinde olduğu projeleri, "Kredi ve Kullanım" izni olmayan kullanıcı kredi bilgisini göremez. "Sistemde X nasıl yapılır?" sorularında kılavuzdan yanıt verir; yanıtın altında **Kılavuz:** bağlantıları (sayfayı açar) ve varsa **Ekrana git** çıkar. Kılavuzda olmayan bir konuyu uydurmaz; şirket yöneticinize ya da RECDx desteğine başvurmanızı önerir. Başka şirketler hakkında hiçbir şey bilmez. Sohbetten çıkan şirket geneli kurallar onay kuyruğuna düşer.

**Rapor isteme (tablo, grafik, pivot):** Beyin AI'ya rapor isteyebilirsiniz; ör. "Son 3 ayda AI maliyetini aylık göster", "Projelere göre adım durumlarını pivot tablo yap", "Hangi AI personel en çok ret aldı?". Beyin AI sayıları kendisi yazmaz; isteğinizi onaylı rapor kataloğundan bir rapora çevirir ve rapor **sizin yetkinizle** sunucuda çalışır. Yanıtın altında rapor kartı çıkar: **Çubuk** / **Sütun** / **Tablo** (iki boyutlu raporda **Pivot** / **Tablo**) görünümleri ve **Excel/CSV** indirme (Excel'de açılır). Raporlar: Projeler, İş adımları (proje, durum, atanan, ünvan, departman, ay; adım sayısı, ret sayısı, ortalama süre), RECAi kullanımı ve maliyeti ("Kredi ve Kullanım" izni gerekir), Öğrenme kayıtları ("Kurum Hafızasına Ekleme ve Onaylama" izni), Sisteme aktarımlar (entegrasyon izinleri). Yetkiniz olmayan rapor Beyin AI'ya hiç önerilmez; proje yönetim yetkiniz yoksa raporlar yalnız ekibinde olduğunuz projeleri sayar. Eski bir sohbeti açtığınızda rapor güncel verilerle yeniden çalışır. Pasta grafiği yerine çubuk gösterilir (karşılaştırma daha doğru okunur).

**Görünenler:** Onay kuyruğu satırında bilgi metni, altında "<kategori veya Bilgi> · güven %NN · tarih" ve **Onay bekliyor** rozeti. Sohbette her yanıtın altında tarih-saat · RECAi kademesi · "X kredi". Yanıt beklenirken "Yanıt hazırlanıyor…". Boş kuyrukta "Onay bekleyen bilgi yok."; boş sohbette **Beyin AI hazır** başlığı ve üç öneri düğmesi.

**Düğmeler:**

| Düğme | Ne yapar | Dikkat |
|---|---|---|
| **Kaydet** | Seçilen kademeyi kaydeder ("Beyin AI için RECAi kaydedildi."). | Seçim değişmeden pasiftir. |
| **Onayla** (kuyrukta) | Bilgiyi kurum hafızasına ekler ("Bilgi Kurum Hafızasına eklendi; tüm AI personel kullanacak."). | Ek onay sormaz. Onaylanan bilgi bütün AI personeli etkiler. |
| **Reddet** (kuyrukta) | Bilgiyi reddeder ("Bilgi reddedildi."). | Ek onay sormaz; geri alınamaz. |
| Öneri düğmeleri: "Şirketimizin mevcut AI personel yapısını değerlendirir misin?", "Hangi departmanlarda eksik ünvan görüyorsun?", "Bu ay öncelik vermemiz gereken işleri planlayalım." | Metni doğrudan Beyin AI'ya gönderir. | Kredi harcar. |
| **Gönder** (veya Enter) | Mesajı gönderir. | Kredi harcar. Yanıt alınamazsa soru kaydedilmez ve metin kutuya geri konur. |

**Adım adım örnek:**

> **Örnek:**
> 1. Ayşe Yılmaz **Kurum Zekâsı › Beyin AI**'ya tıklar; **RECAi** listesinden **RECAi Mergen**'i seçip **Kaydet**'e tıklar.
> 2. Kuyrukta "Müşteri X'e teslimatlar yalnızca hafta içi 09:00-17:00 arası yapılır." bilgisini görür; doğru ve şirket geneli olduğu için **Onayla**'ya tıklar.
> 3. "Hangi departmanlarda eksik ünvan görüyorsun?" öneri düğmesine tıklar; yanıtın altındaki kredi miktarını not eder.

> **Dikkat:** KVKK: Beyin AI konuşmaları ve onay kuyruğu şirketinizin içeriğidir; RECDx yöneticileri dahil şirketiniz dışından kimse göremez. Konuşmalar yalnızca yazan kullanıcıya görünür. Kredi bittiğinde Beyin AI yanıt veremez.

**Sık sorulan sorular:**

- *Kuyruğa kişisel bir bilgi düştü, ne yapayım?* **Reddet**'e tıklayın. Kurum hafızasına yalnızca şirket genelini ilgilendiren, doğru bilgileri alın.
- *Onayladığım bir bilgiyi geri alabilir miyim?* Bu ekranda değil. Kurum hafızasından geri alma Work Space'teki hafıza ekranından, "Kurum Hafızasından Geri Alma" izniyle yapılır (Work Area Kılavuzu).

## Öğrenme

### Öğrenme ekranı

**Bu ekran ne işe yarar?** AI personelinizin **hem sohbetten hem iş akışından** öğrendiklerini gösterir. Her karar bir öğrenme kaydı olur: onaylanan sürüm (**Doğru**), kontrol personelinin ya da yöneticinin reddettiği sürüm (**Yanlış**), test koşusu sonucu, sisteme aktarımın onayı/reddi/geri alınması, çıktısı olan adımın iptali (**Belirsiz**) ve sohbette söylediğiniz kurallar. Yanlışlar silinmez, etiketlenir; reddedilen sürüm sonradan onaylanan sürüme bağlanır ("çift").

**Ne zaman kullanırım?** AI personelin neyi öğrendiğini görmek, haksız bir retten yanlış ders çıkmasını önlemek ve kurumsal dersleri onaylamak için.

**Kimler görür / değiştirir?** "Kurum Hafızasına Ekleme ve Onaylama" izni olanlar (Şirket Yöneticisi, Proje Yöneticisi). Şirket içeriğidir; RECDx göremez.

**Neden sınıfı:** Her **Yanlış** kaydın bir nedeni vardır: **AI personelin hatası**, **Ortam / altyapı**, **Değerlendirme hatası** (ret haksız ya da gerekçesiz), **Kapsam değişikliği**, **Belirsiz**. Nedeni önce sistem kuralı (ör. test ortamı hatası), sonra RECAi önerir; siz satırdaki listeden düzeltebilirsiniz. **Yalnız "AI personelin hatası" olan retlerden ders çıkar.** Nedeni başka bir şeye çevirirseniz o retten çıkan ders AI personelin hafızasından geri alınır; "AI personelin hatası"na çevirirseniz ders çıkarılır.

**Dersler:** Sıradan bir onaydan ders çıkarılmaz; reddedilip sonra onaylanan işten "böyle yap", AI hatası olan retten "bunu yapma, doğrusu şu" dersi çıkar. Ders genel yazılır (kişi, müşteri, tutar, tarih içermez). Personele özgü ders doğrudan o AI personelin hafızasına girer; şirket geneli (kurumsal) ders onayınıza düşer: sağ panel › **Hafıza** › **Onay bekliyor** (ekranın üstünde bekleyen sayısı yazar).

**Ekranın bölümleri:** üstte özet (Doğru / Yanlış / Belirsiz sayıları, çift sayısı, hafızaya yazılan ders, onay bekleyen kurumsal ders); süzgeç (Tümü, Yanlış, Doğru, Belirsiz); tablo: Tarih, AI personel, Adım, Kaynak, Etiket, Neden, Ders, **Ayrıntı** (iş, çıktı, geri bildirim ve ders).

> **Dikkat:** Öğrenme kayıtları ayrıca şirket kartındaki "RECAi model geliştirmeye katkı" izni açıksa, maskelendikten sonra RECAi'nin geliştirilmesinde kullanılır (Şirket Profili). İzin kapalıyken de öğrenme ve hafıza çalışır.

## Entegrasyonlar

### Entegrasyonlar ekranı

**Bu ekran ne işe yarar?** AI personelin şirketinizin dış sistemlerini (ERP, CRM, iş takibi, doküman, kod deposu, mesajlaşma) kullanmasını sağlar. Bağlantı ekler, dener, AI personele araç yetkisi verirsiniz. Odoo, MCP sunucusu ve şirket sunucusu (Edge) bağlantılarında iş çıktısını hedef sisteme yazmak için **eşleme** hazırlar; aktarımların onay kurallarını ve günlüklerini izlersiniz. Okumalar anında yapılır; **yazma işlemleri her zaman insan onayından geçer** ve her çağrı silinemez şekilde kaydedilir.

**Ne zaman kullanırım?** AI personelin bir sistemden bilgi okumasını veya bir sisteme kayıt hazırlamasını istediğinizde; RECSlip.App v2 sürecinden veya otomasyonlardan önce (Odoo bağlantısı için); bir aktarımı düzeltmek veya geri almak istediğinizde.

**Kimler görür / değiştirir?** Menüyü "Bağlantı Yönetimi", "Eşleme Stüdyosu" veya "Dış Sisteme Yazma Onayı" izni olanlar görür. Ekranın bağlantı bölümü "Bağlantı Yönetimi" izni ister (Şirket Yöneticisi, Entegrasyon Yöneticisi); bu izin olmadan açıldığında "Entegrasyonları yalnızca entegrasyon yönetimi yetkisi olanlar yönetebilir." uyarısı çıkar. Eşlemeler "Eşleme Stüdyosu" izni ister ("Eşlemeleri yalnızca eşleme stüdyosu yetkisi olanlar yönetebilir."). Aktarım günlüğü "Bağlantı Yönetimi" veya "Dış Sisteme Yazma Onayı" izni ister. Finans ve Raporlama Sorumlusu gibi yalnızca onay izni olan kişiler aktarım onaylarını **Work Space › Onaylarım**'da verir.

[[EKRAN: ca-entegrasyonlar | Entegrasyonlar ekranının üst kısmı: "Bağlantı ekle" düğmesi ve rozetleriyle bağlantı listesi | Şirket Yöneticisi ile giriş yapın; Kurum Zekâsı › Entegrasyonlar; en az bir Odoo bağlantısı olan bir şirkette görüntü alın]]

**Ekranın bölümleri (yukarıdan aşağı):**

1. **Entegrasyonlar** kartı ("AI personelin dış sistemleri (ERP, mesajlaşma, iş takibi, kod deposu) kullanması. Okumalar anında; yazma işlemleri her zaman insan onayından geçer ve her çağrı kaydedilir."), sağ üstte **Bağlantı ekle**; altında bağlantı listesi.
2. **RECDx uygulamaları (Odoo)** kartı.
3. **Aktarım onay kuralları** kartı.
4. **Aktarım günlüğü** kartı.
5. **Araç çağrı kaydı** kartı.

**Bağlantı satırında görünenler:**

| Görünen | Anlamı |
|---|---|
| Bağlantı adı ve gri rozet | Sistem türü (ör. Odoo, MCP sunucusu, Edge Connector, Telegram, Trello, GitHub, Gitea). Yalnızca okuma ayarlıysa **Yalnızca okuma** rozeti. |
| "Son deneme <tarih>: başarılı / <hata>" veya "Henüz denenmedi" | Son **Dene** sonucu. |
| **Etkin** (yeşil) / **Devre dışı** (gri) | Bağlantı açık mı. Devre dışı bağlantıyı AI personel kullanamaz. |
| **Giriş yapıldı** (yeşil) / **Giriş gerekli** (sarı) | Tek tık girişli servislerde oturum durumu. |
| **Ajan çevrimiçi** / **Ajan çevrimdışı**; "Ajan çevrimiçi · <sunucu> · N izinli şablon", "Ajan çevrimdışı (son görülme …)", "Ajan henüz bağlanmadı", "Ajan anahtarı oluşturulmadı" | Şirket sunucusu (Edge) bağlantılarında sunucunuzdaki küçük programın durumu. |

**Boş ekran ve uyarılar:** "Henüz bağlantı yok — Bağlantı ekleyip AI personele araç yetkisi verin." Gizli bilgilerin saklandığı kasa kurulmamışsa: "Kimlik kasası yapılandırılmamış; bağlantı eklenemez. RECDx ile iletişime geçin." (**Bağlantı ekle** pasif olur).

**Bağlantı satırı düğmeleri:**

| Düğme | Ne yapar | Dikkat |
|---|---|---|
| **Bağlantı ekle** | **Bağlantı ekle** katalog penceresini açar. | — |
| **Giriş yap** / **Yeniden giriş** | (Tek tık girişli servis, etkinken) servisin giriş ekranına gider. Dönüşte "Giriş tamamlandı; bağlantı hazır. Şimdi AI personele araç yetkisi verin." | Servis sizden izin ister. |
| **Oturumu kapat** | Tek tık giriş oturumunu kapatır. | Onay sorar: "'<ad>' oturumu kapatılsın mı? AI personel bu bağlantıyı yeniden giriş yapılana kadar kullanamaz." Yeniden giriş ile geri alınır. |
| **Dene** | Bağlantıyı sınar; sonuç bildirimi gelir ve "Son deneme" satırı güncellenir. | Sisteme bir şey yazmaz. |
| **Ajan anahtarı** | (Yalnızca Edge) yeni ajan anahtarı üretir ve **ajan anahtarı** penceresini açar. | Önceden anahtar varsa onay sorar: "Yeni ajan anahtarı oluşturulsun mu? Eski anahtar hemen geçersiz olur; sunucudaki ajanın ayarı yenilenmeli." Geri alınamaz. |
| **Düzenle** | **<ad> · düzenle** penceresini açar. | — |
| **Devre dışı bırak** / **Etkinleştir** | Bağlantıyı kapatır veya açar. | Kapatırken onay sorar: "'<ad>' devre dışı bırakılsın mı? AI personel bu bağlantının araçlarını kullanamaz." |
| **Araçlar ve yetkiler** | Satırın altında araç yetkisi tablosunu açar veya kapatır. | — |
| **Eşlemeler** | (Odoo, MCP sunucusu, Edge) **<ad> · eşlemeler** penceresini açar. | "Eşleme Stüdyosu" izni gerekir. |

#### Araçlar ve yetkiler tablosu

Bağlantı satırının altında açılır. AI personelin bu bağlantının hangi araçlarını kullanabileceğini belirlersiniz.

[[EKRAN: ca-arac-yetkileri | Bir Odoo bağlantısının altında açılmış araç yetkisi tablosu | Entegrasyonlar ekranında bir Odoo bağlantısının "Araçlar ve yetkiler" düğmesine tıklayın; tablo açıkken görüntü alın]]

| Öğe | Ne işe yarar |
|---|---|
| **AI personel** sütunu | Şirketinizdeki AI personel. Yoksa "Şirkette AI personel yok." |
| **Tümü** sütunu | İşaretlenince o AI personel bütün araçları kullanır; tek tek kutular kilitlenir. |
| Araç sütunları | Bağlantının her aracı; adın altında "okuma" veya "yazma · onaylı". Üzerine gelince aracın açıklaması görünür. |
| **Yetkileri kaydet** | Kaydeder ("Araç yetkileri kaydedildi."). |

> **İpucu:** AI personele önce yalnızca okuma araçlarını verin. Yazma araçları zaten her seferinde insan onayına düşer ve elle denenemez ("Yazma araçları elle denenemez; AI personel kullandığında onaya düşer."). Odoo bağlantısı kayıt silmez.

#### E-posta ve Web/RSS bağlantıları (İSTEK #740)

**E-posta** kategorisinde **Gmail / Google Workspace**, **Outlook / Hotmail / Microsoft 365**, **iCloud Mail**, **Yandex Mail** ve **Şirket e-posta sunucusu (IMAP/SMTP)** kartları vardır. Bağlanınca AI personel (araç izni verdiğiniz) e-postaları **arar** (gönderen, konu, metin, son N gün, okunmamış), **okur** (okunmadı işareti değişmez; ek adlarını görür) ve özetler. **Gönderme her zaman onayınızdan geçer** (Onay Kutusu / Telegram düğmesi); bağlantıyı **Yalnızca okuma** yaparsanız AI personel hiç e-posta gönderemez.

- **Giriş yöntemi:** Gmail, iCloud ve Yandex'te normal şifre çalışmaz; hesabınızın güvenlik ayarlarından **uygulama şifresi** oluşturup girin. **Outlook/Hotmail** için **Hesapla giriş** gerekir (Microsoft şifreyle girişi kapattı): bağlantıyı kaydedip **Giriş yap**'a basın, Microsoft hesabınızla izin verin. Gmail'de de hesapla giriş seçilebilir. Hesapla giriş RECDx tarafından henüz açılmadıysa "Hesapla giriş henüz RECDx tarafından açılmadı" uyarısı çıkar; o durumda uygulama şifresi kullanın.
- **Sunucu adresleri** yalnız "Diğer (IMAP/SMTP)" sağlayıcısında sorulur (genelde IMAP 993, SMTP 587). İç ağdaki sunuculara bağlanılmaz.
- E-posta içeriği **dış veridir**: AI personel içindeki talimatları uygulamaz, yalnız bilgi olarak kullanır.

**Web sayfası / RSS kaynağı** kartı: AI personel bir sayfanın metnini ya da RSS/Atom akışının son maddelerini okur (ör. Resmi Gazete, sektör haberleri). Yalnız okuma; iç ağ adresleri ve XML varlık tanımı içeren akışlar reddedilir.

**Otomasyonla kullanım:** **Otomasyonlar** › kural › tetik **Yoklama** › bağlantı olarak e-posta kutusunu seçin: yeni gelen her e-posta (isteğe bağlı gönderen/konu süzgeciyle) bir iş açar; e-postanın gönderen, konu ve tarih bilgisi işe eklenir. RSS bağlantısını seçerseniz akışa eklenen her yeni madde bir iş açar. İlk turda mevcut iletiler/maddeler taban alınır; yalnız sonradan gelenler iş açar. Günlük özet için tetik **Zamanlı** (ör. her gün 08:00) seçip isterlere "Dün gelen e-postaları özetle" yazın.

**Sonucu gönderme:** Kural formundaki **İş bitince sonucu yöneticiye ve bildirilecek kişiye gönder** işaretlenirse iş bittiğinde son onaylı çıktı yöneticiye ve seçilen kişiye, her birinin bildirim tercihine göre **e-posta** ("<iş> — sonuç") ve/veya **Telegram** ile gider. WhatsApp kanalı sonraki sürümde eklenecek.

#### Bağlantı ekle (katalog) penceresi

[[EKRAN: ca-m-baglanti-katalog | Bağlantı ekle katalog penceresi: arama, kategori sekmeleri, yöntem rozetli sistem kartları ve "RECAi'ye sorun" kutusu | Entegrasyonlar ekranında "Bağlantı ekle"ye tıklayın; "Tümü" sekmesindeyken görüntü alın]]

| Alan | Ne işe yarar | Nasıl doldurulur / seçenekler | Örnek | Zorunlu |
|---|---|---|---|---|
| Sistem ara | Kartları süzer | Ad, üretici, anahtar kelime veya açıklama yazın | Logo | Hayır |
| Kategori sekmeleri | Kartları kategoriye göre süzer | **Tümü**, ERP, CRM, İş takibi, Doküman, Yazılım, Müşteri destek, Mesajlaşma, Finans, Tasarım, Diğer (yalnızca dolu olanlar) | ERP | Hayır |
| **Aradığınız sistem yok mu? RECAi'ye sorun** | Bağlanma yolu önerisi | Kullandığınız sistemi en az 3 karakterle anlatın (en çok 1500) | Logo Tiger 3 kullanıyoruz, sunucu şirketin içinde | Hayır |

**Kartlar:** Üstte yöntem rozeti ve kategori, altta sistem adı ve açıklama. Yöntem rozetleri:

| Rozet | Anlamı |
|---|---|
| **Doğrudan bağlantı** (yeşil) | RECOrion sisteme kendi adresi ve anahtarıyla bağlanır (ör. Odoo, Trello, GitHub, Gitea, Telegram). |
| **Tek tık giriş (MCP)** / **MCP sunucusu** (mavi) | Servisin kendi giriş ekranından izin verirsiniz veya servisin yapay zekâ bağlantı noktasına bağlanılır (ör. HubSpot, Jira, Notion, Figma). |
| **Şirket sunucusu (Edge)** (sarı) | Sistem şirketinizin içindeki bir sunucudadır (ör. Logo, Mikro, Netsis). Sunucunuza küçük bir program kurulur; bu program yalnızca dışa bağlanır. |
| **Yakında** (gri) | Henüz bağlanamaz; tıklayınca yalnızca bilgi verilir (ör. SAP, Microsoft Dynamics, Salesforce). |

Düğmeler: karta tıklama → bağlantı formu; **Nasıl bağlanırım?** (RECAi önerisi: özet, numaralı adımlar, notlar; "RECAi düşünüyor…"; kredi harcar); öneride uygun kart varsa **<sistem> ile devam et**; **Vazgeç**. Kısa soru yazarsanız: "Kullandığınız sistemi kısaca yazın."

#### Bağlantı ekle / düzenle penceresi (bağlantı formu)

Üstte seçilen kartın yöntem rozeti, açıklaması ve **Kurulum adımları** listesi; tek tık girişli servislerde "Yönlendirme adresi (servis isterse): …".

[[EKRAN: ca-m-baglanti-formu-odoo | Odoo bağlantı formu: kurulum adımları, Odoo adresi, veritabanı, kullanıcı, API türü, izinli modeller ve API anahtarı alanları | Bağlantı ekle penceresinde Odoo kartına tıklayın; alanlar boşken görüntü alın]]

**Ortak alanlar:**

| Alan | Ne işe yarar | Nasıl doldurulur | Örnek | Zorunlu |
|---|---|---|---|---|
| **Sistem** | Bağlantı türü | Yalnızca katalog kartı seçmeden açılırsa görünür | Odoo | Evet |
| **Bağlantı adı** | Listede görünecek ad | En az 2, en çok 120 karakter; şirkette benzersiz | Odoo (şirket) | Evet |

**Odoo alanları:**

| Alan | Ne işe yarar | Nasıl doldurulur | Örnek | Zorunlu |
|---|---|---|---|---|
| **Odoo adresi \*** | Odoo'nuzun adresi | Tarayıcıda Odoo'ya girdiğiniz adres | https://orneklojistik.odoo.com | Evet |
| **Veritabanı adı \*** | Odoo veritabanı | Odoo yöneticinizden öğrenin | orneklojistik | Evet |
| **Kullanıcı (e-posta)** | API anahtarının sahibi | Ayrı, kısıtlı yetkili bir entegrasyon kullanıcısı önerilir. Odoo 19 ve sonrasında boş bırakılabilir. | entegrasyon@orneklojistik.com.tr | Eski sürümlerde evet |
| **API türü** | Bağlantı biçimi | **Otomatik** ("Odoo 19+ ise JSON-2, değilse JSON-RPC."), **JSON-2 (Odoo 19+)**, **JSON-RPC (eski sürümler)** | Otomatik | Hayır |
| **İzinli modeller** | AI personelin erişeceği Odoo bölümleri | Virgülle yazın; boşsa kullanıcının erişebildiği her şey | res.partner, sale.order | Hayır |
| **API anahtarı veya parola \*** | Giriş anahtarı | Odoo › Tercihler › Hesap Güvenliği › API Anahtarları'ndan oluşturun. Şifreli saklanır. | •••••• | Yeni kayıtta evet |

**Diğer sistemlerin alanları:**

| Sistem | Alanlar |
|---|---|
| MCP sunucusu | Sunucu adresi \*; Kimlik yöntemi (**Erişim anahtarı (token)**, **Tek tık giriş (OAuth)**, **Kimlik gerekmez**); Kimlik başlığı (token yönteminde); Okuma sayılacak araçlar; gizli alanlar: Erişim token'ı (token yönteminde), istemci kimliği ve istemci gizli anahtarı (tek tık girişte). Seçtiğiniz yönteme göre alanlar görünür veya gizlenir. |
| Telegram | Varsayılan sohbet / grup kimliği; gizli Bot token (Telegram'daki @BotFather'dan alınır). |
| Trello | Varsayılan pano kimliği; gizli API anahtarı ve Token. |
| GitHub | GitHub kullanıcı adı; gizli Erişim token'ı. |
| Gitea | Sunucu adresi \*, Kullanıcı adı; gizli Erişim token'ı. |
| Şirket sunucusu (Edge Connector) | Form alanı yoktur; kayıttan sonra **Ajan anahtarı** üretilir. |

Kayıtlı gizli alanlarda yer tutucu "•••••• (kayıtlı; değiştirmek için yazın)" görünür; boş bırakırsanız eski değer korunur. Gizli bilgiler bir daha gösterilmez.

Düğmeler: **Vazgeç**, **Kaydet** ("Bağlantı eklendi. Şimdi deneyip AI personele araç yetkisi verin." veya "Bağlantı güncellendi."). Tek tık girişli bağlantı kaydedilince: "'<ad>' kaydedildi. Şimdi servisin giriş ekranına gidip izin verelim mi?" → **Giriş yap**.

| Hata | Anlamı | Ne yapmalı |
|---|---|---|
| "Bu adla bir bağlantı zaten var." | Aynı ad kullanılmış. | Farklı bir ad verin. |
| "Kimlik kasası yapılandırılmamış; RECDx ile iletişime geçin." | Gizli bilgi kasası hazır değil. | RECDx ile görüşün. |
| **Dene** sonrası hata ayrıntısı | Adres, veritabanı veya anahtar yanlış. | **Düzenle** ile düzeltip yeniden deneyin. |

#### Ajan anahtarı penceresi (Edge)

Başlık "<ad> · ajan anahtarı". Anahtar bir kez gösterilir: "Bu anahtar bir daha gösterilmez. Kaybolursa yeni anahtar oluşturun (eskisi geçersiz olur)." Pencerede şirket sunucunuzdaki programın başlatma bilgisi yer alır; bunu bilgi işlem ekibiniz kullanır. "Ajan yalnızca dışa bağlanır (sunucunuza port açmanız gerekmez) ve yalnızca izin verdiğiniz sorgu şablonlarını çalıştırır." Düğmeler: **Kopyala**, **Kaydettim, kapat**.

[[EKRAN: ca-m-ajan-anahtari | Edge ajan anahtarı penceresi (anahtar kısmı bulanıklaştırılmış) | Test şirketinde bir "Şirket sunucusu (Edge)" bağlantısının "Ajan anahtarı" düğmesine tıklayın; görüntüde anahtarı mutlaka bulanıklaştırın]]

#### Eşlemeler penceresi (eşleme stüdyosu)

Başlık "<ad> · eşlemeler". Eşleme, RECAi'nin ürettiği ortak bir kaydın (ürün kartı, cari, teklif…) hedef sistemde hangi alanlara yazılacağını belirler. Onaylanan eşleme aktarımlarda kullanılır; her aktarım yine önizleme ve onaydan geçer.

[[EKRAN: ca-m-eslemeler | Eşlemeler listesi: Taslak ve Onaylı rozetli eşlemeler | Entegrasyonlar ekranında Odoo bağlantısının "Eşlemeler" düğmesine tıklayın]]

| Görünen / Düğme | Ne yapar |
|---|---|
| Eşleme satırı | Ad, rozet **Taslak** (sarı) veya **Onaylı** (yeşil), "<nesne> → <hedef> · N kural · sürüm V · son deneme: hatasız/hatalı", **Aç** düğmesi. |
| Boş liste | "Henüz eşleme yok — RECDx hazır eşlemesinden başlayın veya RECAi'ye önerdirin." |
| **Yeni eşleme** | **Yeni eşleme** penceresini açar. |
| **Kapat** | Pencereyi kapatır. |

**Yeni eşleme penceresi:**

| Alan | Ne işe yarar | Nasıl doldurulur / seçenekler | Örnek | Zorunlu |
|---|---|---|---|---|
| **Nesne** | Aktarılacak kayıt türü | Ürün / hizmet kartı, Cari (müşteri / tedarikçi), Teklif / sipariş, Görev, Destek kaydı, Masraf fişi, Doküman | Cari (müşteri / tedarikçi) | Evet |
| **Odoo modeli** (Odoo) / **Araç / şablon** (MCP, Edge) | Hedef | Odoo'da nesneye göre önerilen hedef kendiliğinden gelir; MCP ve Edge'de yazma araçlarından seçilir | res.partner | Evet |

Hazır eşleme varsa "RECDx hazır eşlemesinden başlayın…" listesinde her satırda **Bununla başla**. Düğmeler: **Vazgeç**, **Boş eşleme oluştur** (eşleme düzenleyicisi açılır).

**Eşleme düzenleyicisi:** Üstte durum rozeti, "<nesne> → <hedef>", "sürüm V".

[[EKRAN: ca-m-esleme-editoru | Eşleme düzenleyicisi: kural tablosu, tekrar aktarımda eşleştirme alanları ve Denetle / Dene / Onayla düğmeleri | Eşlemeler penceresinde bir eşlemenin "Aç" düğmesine tıklayın; "Dene (yazmadan)" sonucu görünürken görüntü alın]]

| Öğe | Ne işe yarar | Nasıl doldurulur / seçenekler |
|---|---|---|
| **Hedef alan** | Hedef sistemdeki alan | Listeden seçin; zorunlular "* " ile başlar; hedefte bulunmayan "(hedefte yok)" |
| **Dönüşüm** | Değerin nasıl üretileceği | **Kopyala**, **Sabit değer**, **Değer eşle**, **Listede varsa**, **Metin şablonu**, **Hedefte ara (Odoo)**, **Kalemler (Odoo)** |
| **Kaynak** | Ortak kaydın alanı | Kopyala, Değer eşle, Listede varsa, Hedefte ara ve Kalemler için seçilir |
| **Parametre** | Dönüşümün ayarı | Sabit değer için değer; Metin şablonu için örneğin `{name} ({code})`; diğerlerinde bilgi işlem ekibinizin hazırlayacağı yapılandırılmış metin. Kopyala'da yoktur. |
| **Kural N sil** | Kuralı kaldırır | — |
| **Tekrar aktarımda eşleştir: kaynak** ve **hedef alan** | Aynı kayıt ikinci kez gelirse yeni kayıt yerine mevcut kaydı günceller | "Yok (her aktarım yeni kayıt)" veya bir kaynak ve hedef alan seçin (ör. vergi numarası) |

| Düğme | Ne yapar | Dikkat |
|---|---|---|
| **RECAi önersin** | Kuralları RECAi'ye önerdirir. | Mevcut kurallar varsa onay sorar: "RECAi önerisi mevcut kuralların yerine geçecek. Devam edilsin mi?" Kredi harcar. |
| **Kural ekle** | Boş bir kural satırı ekler. | — |
| **Kaydet** | Değişiklikleri kaydeder. | Onaylı eşleme değiştirilirse yeniden **Taslak** olur ("Kaydedildi; onay için yeniden deneyin."). |
| **Denetle** | Kuralları doğrular ("Denetim: hata yok / N hata"). | — |
| **Dene (yazmadan)** | Örnek bir kayıtla hedefe gidecek değerleri gösterir: "Deneme (yazılmadı): yeni kayıt açılacak / mevcut kayıt #N güncellenecek / hatalı"; tablo **Hedef alan / Değer / Kaynak**. | Hedef sisteme hiçbir şey yazmaz. |
| **Onayla** | Eşlemeyi onaylar ("Eşleme onaylandı; aktarımlarda kullanılacak."). | Yalnızca kaydedilmemiş değişiklik yokken ve aynı sürümün son denemesi hatasızken etkindir. |
| **Kapat** | Kapatır. | Kaydedilmemiş değişiklikler kaybolur. |

| Hata | Ne yapmalı |
|---|---|
| "Parametre alanı geçerli JSON olmalı." | Parametreyi bilgi işlem ekibinize kontrol ettirin. |
| "Önce bu sürümü örnek kayıtla deneyin (Dene)." | **Dene (yazmadan)**'a tıklayın. |
| "Son denemede hata var; düzeltip yeniden deneyin." | Hatalı kuralı düzeltip yeniden deneyin. |
| "Arşivlenmiş eşleme düzenlenemez." | Yeni eşleme oluşturun. |
| "Bu sistem türü için eşleme desteklenmiyor (Odoo, MCP sunucusu veya Edge Connector)." | Eşleme yalnızca bu üç türde kullanılır. |

### RECDx uygulamaları (Odoo) kartı

**Bu kart ne işe yarar?** RECDx'in Odoo üzerinde çalışan uygulamaları RECQmind (destek biletleri) ve RECSlip (masraf fişleri) için tercihinizi bildirirsiniz. Alt başlık: "RECQmind ve RECSlip, Odoo'nuzda çalışır ve RECOrion ile birlikte iş yürütür. Paketiniz: <paket>."

[[EKRAN: ca-recdx-uygulamalari | RECDx uygulamaları (Odoo) kartı: uygulama durum rozetleri, "Şirketinizde Odoo kullanıyor musunuz?" sorusu ve uygulama seçimleri | Entegrasyonlar ekranında aşağı kaydırıp "RECDx uygulamaları (Odoo)" kartının görüntüsünü alın]]

| Alan | Ne işe yarar | Nasıl doldurulur / seçenekler | Örnek | Zorunlu |
|---|---|---|---|---|
| Durum satırı (**RECQmind:**, **RECSlip:**) | Uygulamanın durumu | Rozet: **Entegrasyon açık** (yeşil), **Odoo bağlantısı gerekli** (sarı), **Teklif istendi** (mavi), **Kapalı** (gri); varsa talep durumu: işleniyor, Odoo siparişine eklendi, RECDx satış ekibine iletildi, zaten kullanıyorsunuz, tamamlandı, iptal, RECDx ekibi ilgileniyor | — | — |
| **Şirketinizde Odoo kullanıyor musunuz?** | Seçenekleri belirler | **Evet** / **Hayır**. Hayır seçilirse uygulama seçimleri "Teklif istiyorum"a çevrilir. | Evet | Hayır |
| Uygulama seçimi (RECQmind, RECSlip) | Ne istediğiniz | Açıklama, "RECOrion ile: …", **Ayrıntı** bağlantısı ve teklif rozeti (**Paketinize dahil**, **Paketinizde %X indirimli: …**, **Bu pakette yok; teklif isteyebilirsiniz**). Seçenekler: **Zaten kullanıyorum (yalnızca entegrasyon)** (Odoo = Evet ise), **Paketime ekle** (Odoo = Evet ve pakette teklif varsa), **Teklif istiyorum** ("RECDx ekibi size teklif hazırlar. Dilerseniz Odoo Apps üzerinden de satın alabilirsiniz."), **Hayır** | Zaten kullanıyorum (yalnızca entegrasyon) | Hayır |

Düğme **Kaydet** ("Tercihiniz kaydedildi."). **Paketime ekle** RECDx'e sipariş, **Teklif istiyorum** satış talebi olarak iletilir. İletilen talep bu ekrandan geri çekilemez; RECDx ile iletişime geçin.

> **İpucu:** RECSlip.App v2 aylık masraf sürecini kurmak için bu kartta seçim yapmanız şart değildir; süreç **Otomasyonlar** ekranındaki ayrı kartla kurulur (bkz. **RECSlip.App v2 ile aylık masraf süreci**).

### Aktarım onay kuralları kartı

Alt başlık: "İş çıktısından sisteme her aktarım önizleme ve onaydan geçer. Aşağıdakiler ikinci bir onay (entegrasyon yöneticisi, farklı kişi) ister." Yalnızca "Bağlantı Yönetimi" izni olanlar görür ve değiştirir.

[[EKRAN: ca-aktarim-onay-kurallari | Aktarım onay kuralları kartı: nesne kutuları ve tutar eşiği | Entegrasyonlar ekranında aşağı kaydırıp "Aktarım onay kuralları" kartının görüntüsünü alın]]

| Alan | Ne işe yarar | Nasıl doldurulur | Örnek | Zorunlu |
|---|---|---|---|---|
| **Her zaman çift onay:** nesne kutuları (Ürün / hizmet kartı, Cari, Teklif / sipariş, Görev, Destek kaydı, Masraf fişi, Doküman) | İşaretli türlerin aktarımı iki farklı kişinin onayını ister | Kutuyu işaretleyin; hemen kaydedilir | Teklif / sipariş | Hayır |
| **Tutar eşiği (₺; üzeri çift onay)** | Bu tutarın üzerindeki aktarımlar çift onay ister | Tutar yazın; alandan çıkınca kaydedilir; boş = eşik yok | 50000 | Hayır |

Kayıtta "Aktarım kuralları kaydedildi."

### Aktarım günlüğü kartı

Alt başlık: "Silinemez kayıt: ne, nereye, kimin onayıyla aktarıldı; geri alınanlar dahil." Son 50 aktarım gösterilir. Boşsa "Henüz aktarım yok."

[[EKRAN: ca-aktarim-gunlugu | Aktarım günlüğü: bir aktarım kartı, hedefe gidecek değerler tablosu ve onaylayanlar | Entegrasyonlar ekranında aşağı kaydırıp "Aktarım günlüğü" kartında en az bir "Aktarıldı" kaydının görüntüsünü alın]]

**Aktarım kartında görünenler:** "<nesne>: <ad>" ve durum rozeti; alt satır "<bağlantı> · yeni kayıt açar / mevcut kaydı günceller · tutar · tetik (elle / adım bitince / proje kapanınca) · tarih · çift onay (x/y)"; **Hedefe gidecek değerler** tablosu (**Hedef alan / Değer**); hata ve uyarı maddeleri; onaylayanlar (✓/✗ ad · tarih · not); tamamlananlarda hedef kayda bağlantı.

| Durum | Anlamı |
|---|---|
| **RECAi hazırlıyor** | RECAi kaydı iş çıktısından hazırlıyor. |
| **Düzeltme gerekli** | Zorunlu alan eksik veya hatalı. |
| **Onay bekliyor** | Önizleme hazır; onaylayıcı bekleniyor. |
| **Kuyrukta** / **Yazılıyor** | Onaylandı; hedefe yazılıyor. |
| **Aktarıldı** | Hedef sisteme yazıldı. |
| **Hata** | Yazılamadı. |
| **Reddedildi** | Onaylayıcı reddetti. |
| **Geri alındı** | Aktarım geri alındı. |

| Düğme | Ne yapar | Dikkat |
|---|---|---|
| **Düzelt** | (Düzeltme gerekli, Onay bekliyor) **<nesne> · düzelt** penceresini açar: kaydın alanları (zorunlular \*); **Kaydet ve önizle** → "Düzeltildi; önizleme yenilendi ve onaya gönderildi." veya "Hâlâ eksik veya hatalı alan var." | — |
| **Geri al** | (Aktarıldı) Güncellemede eski değerleri geri yazar; yeni kayıtta kaydı arşivler (siparişte iptal eder). | Onay sorar. |
| **Yeniden dene** | (Hata, onaylar tamamsa) aktarımı yeniden sıraya alır ("Yeniden kuyruğa alındı."). | — |

**Onayla ve aktar** / **Reddet** düğmeleri onaylayıcının kendi ekranlarında (**Work Space › Onaylarım**, proje kapanışı) görünür; Reddet'te isteğe bağlı gerekçe sorulur.

[[EKRAN: ca-m-aktarim-duzelt | Aktarım düzeltme penceresi | Aktarım günlüğünde "Düzeltme gerekli" durumundaki bir kartın "Düzelt" düğmesine tıklayın]]

### Araç çağrı kaydı kartı

Alt başlık: "Silinemez kayıt: kim, hangi araç, hangi argümanla, sonuç ve onay." AI personelin bağlantı araçlarını her kullanışı burada listelenir.

[[EKRAN: ca-arac-cagri-kaydi | Araç çağrı kaydı tablosu: Çalıştı, Onay bekliyor ve Yetkisiz rozetli satırlar | Entegrasyonlar ekranının en altındaki "Araç çağrı kaydı" kartının görüntüsünü alın]]

| Sütun | Anlamı |
|---|---|
| **Zaman** | Çağrı zamanı |
| **Kim** | Aracı kullanan AI personel |
| **Bağlantı** | Hangi bağlantı |
| **Araç** | Hangi araç |
| **Tür** | **Okuma** veya **Yazma** |
| **Durum** | **Çalıştı** (yeşil), **Onay bekliyor** (sarı), **Reddedildi** (gri), **Hata** (kırmızı), **Yetkisiz** (kırmızı: AI personelin bu araca yetkisi yok) |
| **Süre** | Milisaniye |
| **Ayrıntı** | Hata veya sonuç özeti; üzerine gelince tamamı |

Boşsa "Henüz araç çağrısı yok." Kayıtlar silinemez.

**Adım adım örnek: Odoo bağlama**

> **Örnek:** Örnek Lojistik A.Ş.'nin bilgi işlem sorumlusu (Entegrasyon Yöneticisi) Odoo'yu bağlıyor.
> 1. Odoo'da ayrı, kısıtlı yetkili bir entegrasyon kullanıcısı açar; o kullanıcıyla **Tercihler › Hesap Güvenliği › Yeni API Anahtarı** oluşturur.
> 2. RECOrion'da **Entegrasyonlar** → **Bağlantı ekle** → **Odoo** kartına tıklar.
> 3. **Bağlantı adı**: "Odoo (şirket)", **Odoo adresi**, **Veritabanı adı**, **Kullanıcı (e-posta)** ve **API anahtarı veya parola** alanlarını doldurur → **Kaydet**.
> 4. Bağlantı satırında **Dene**'ye tıklar; "Son deneme …: başarılı" görünür.
> 5. **Araçlar ve yetkiler**'e tıklar; "Sevkiyat Asistanı Deniz" satırında okuma araçlarını işaretler → **Yetkileri kaydet**.

**Adım adım örnek: cari eşlemesi**

> **Örnek:**
> 1. Odoo bağlantısında **Eşlemeler** → **Yeni eşleme**.
> 2. Hazır eşleme varsa **Bununla başla**; yoksa **Nesne**: Cari (müşteri / tedarikçi) → **Boş eşleme oluştur**.
> 3. Düzenleyicide **RECAi önersin**'e tıklar.
> 4. **Tekrar aktarımda eşleştir: kaynak** olarak vergi numarasını, **hedef alan** olarak Odoo'daki vergi numarası alanını seçer.
> 5. **Kaydet** → **Denetle** → **Dene (yazmadan)**; önizlemeyi kontrol eder → **Onayla**. Rozet **Onaylı** olur.

**Adım adım örnek: projeden Odoo'ya satın alma siparişi açma**

Bir projede (ör. "Ofis malzemesi tedariki") AI personelin hazırladığı siparişin Odoo Satın Alma'ya kayıt olarak düşmesi için:

> **Örnek:**
> 1. **Odoo'da hazırlık:** AI personel için ayrı bir entegrasyon kullanıcısı açın; bu kullanıcıya Satın Alma (purchase) uygulamasında
>    sipariş oluşturma yetkisi verin, API anahtarını bu kullanıcıyla üretin.
> 2. **Bağlantı:** Entegrasyonlar → **Bağlantı ekle** → **Odoo** (ya da var olan Odoo bağlantınızı **Düzenle**). **İzinli modeller**'e
>    şunları ekleyin: `purchase.order, purchase.order.line, res.partner, product.product, account.tax`. **Dene** ile doğrulayın.
> 3. **Eşleme:** Bağlantıda **Eşlemeler** → **Yeni eşleme** → hazır **Odoo satın alma siparişi** eşlemesiyle başlayın
>    (Nesne: Sipariş, yön: satın alma). Tedarikçi vergi numarası veya adıyla, ürün stok koduyla bulunur; KDV satın alma vergisinden
>    alınır. **Dene (yazmadan)** ile önizleyin → **Onayla**.
> 4. **Projede:** İş Akışı'nda siparişi hazırlayan adımın altında **Sisteme aktar** → eşlemeyi seçin. RECAi adım çıktısından sipariş
>    önizlemesini çıkarır (tedarikçi, kalemler, miktar, fiyat). Kontrol edip onaya gönderin. İsterseniz adıma "Bu adım bitince
>    otomatik öner" işaretini koyun; adım onaylanınca aktarım önerisi kendiliğinden gelir.
> 5. **Onay:** Sipariş aktarımı varsayılan olarak iki onay ister (diğer kayıt türlerinde 100.000 ₺ üstü tutarlar iki onaya çıkar).
>    Onaylar **Onaylarım** ekranından verilir; onaydan sonra kayıt Odoo'da **Taslak teklif (RFQ)** olarak açılır.
> 6. **Kontrol ve geri alma:** Aktarım kaydında Odoo'daki sipariş numarası görünür. Yanlış açıldıysa aktarım kaydından geri
>    alınabilir (siparişi iptal eder); silme yapılmaz.

İpucu: AI personele Odoo **yazma** aracını (create_record) doğrudan vermek de mümkündür; ama satın alma gibi parasal kayıtlarda
eşleme + Sisteme aktar yolu önerilir, çünkü önizleme, çift onay ve geri alma yalnız bu yolda vardır.

**Sık sorulan sorular:**

- *AI personel izinsiz bir şey yazabilir mi?* Hayır. Yazma araçları ve aktarımlar her zaman insan onayına düşer; her çağrı kayda geçer.
- *RECDx bağlantılarımızı görebilir mi?* Hayır. Bağlantılar ve kayıtlar şirketinizin içeriğidir (KVKK); gizli bilgiler şifreli kasada tutulur ve ekrana bir daha gelmez.
- *Araç çağrı kaydında "Yetkisiz" görüyorum.* AI personel yetkisi olmayan bir aracı kullanmaya çalıştı. Gerekliyse **Araçlar ve yetkiler**'den yetki verin.

## Otomasyonlar

### Otomasyonlar ekranı

**Bu ekran ne işe yarar?** Dış sistemde bir şey olunca (yeni kayıt, değişiklik veya belirli bir zaman) RECOrion'da otomatik olarak Case veya proje açar ya da bir kişiye bildirim gönderirsiniz. Açılan iş yöneticisinin onayını bekler; her olay silinemez günlüğe yazılır. RECQmind için hazır kurallar tek tıkla kurulur; RECSlip.App v2 aylık masraf süreci ayrı bir kartla kurulur; kendi kuralınızı RECAi'ye anlatarak taslak çıkarabilirsiniz.

**Ne zaman kullanırım?** Tekrarlayan bir işi otomatik başlatmak istediğinizde (ör. büyük bir sipariş gelince sevkiyat planlama Case'i açılsın), destek biletlerini Case'e dönüştürmek istediğinizde, aylık masraf sürecini kurmak istediğinizde.

**Kimler görür / değiştirir?** "Otomasyon Kuralları" izni olanlar (Şirket Yöneticisi, Entegrasyon Yöneticisi). İzin olmadan işlem yapılırsa "Otomasyonları yalnızca otomasyon kuralları yetkisi olanlar yönetebilir." uyarısı çıkar. RECSlip.App v2 kartındaki **Kur** ve **Şimdi çalıştır** ayrıca "Bağlantı Yönetimi" izni ister.

[[EKRAN: ca-otomasyonlar | Otomasyonlar ekranı: RECQmind hazır kuralları kutusu, RECSlip.App v2 aylık süreç kartı, kural listesi | Şirket Yöneticisi ile giriş yapın; Kurum Zekâsı › Otomasyonlar; en az bir kuralı olan bir şirkette görüntü alın]]

**Ekranın bölümleri:**

1. **Otomasyonlar** kartı ("Dış sistemde bir şey olunca (yeni kayıt, değişiklik, zaman) RECOrion'da Case veya proje taslağı açılır. Açılan iş yöneticisinin onayını bekler; her olay silinemez günlüğe yazılır."), sağ üstte **Yeni kural**. İçinde:
   - **RECQmind hazır kuralları** kutusu: rozet **Kullanılabilir** veya **Kapalı**; kuruluysa **x/y kurulu**; açıklama "Helpdesk biletlerinden iade, iptal, kargo ve ürün sorusu Case'leri; Case sonucu bilete yazılır." (kapalıysa nedeni); düğme **Hazır kuralları kur**.
   - **RECSlip.App v2 aylık süreç** kartı (aşağıda ayrı anlatılır).
   - **Otomasyon kuralları** listesi.
2. **Otomasyon günlüğü** kartı ("Silinemez kayıt: hangi olay geldi, hangi kural ne yaptı (iş açıldı, koşul tutmadı, tekrar, döngü veya hız sınırı).").

> **Dikkat:** Eski "RECSlip hazır kuralları" (sorunlu masraf fişi ve ay sonu kapanışı) kaldırılmıştır. Daha önce kurulmuş bu kurallar duraklatılmıştır ve satırında "RECSlip v1 kuralı: RECSlip.App v2 aylık sürecine geçildi" hatası görünür. Bunları **Arşivle** ile kaldırıp **RECSlip.App v2 aylık süreç** kartını kullanın.

**Kural satırında görünenler:** ad; tetik rozeti (**Anlık bildirim**, **İzleme**, **Zamanlayıcı**); durum (**Etkin** / **Duraklatıldı**); özet: ne zaman çalışır (ör. "Odoo · sale.order her 15 dk izlenir", "her Pazartesi 09:00", "her ay sonu 18:00"), koşul sayısı, eylem (Case açar / proje açar / bildirim), "sıradaki <tarih>", "son iş <tarih> (sayı)", varsa son hata; anlık bildirim kurallarında bildirimin gönderileceği adres.

**Kural satırı düğmeleri:**

| Düğme | Ne yapar | Dikkat |
|---|---|---|
| **Yeni kural** | **Yeni otomasyon kuralı** penceresini açar. | — |
| **Hazır kuralları kur** | **RECQmind hazır kuralları** penceresini açar. | Yalnızca kullanılabilirse görünür. |
| **Dene** | **<kural> · örnek olayla dene** penceresini açar. | İş açmaz, dış sisteme yazmaz. |
| **Hemen çalıştır** | (İzleme ve Zamanlayıcı, etkinken) kuralı beklemeden çalıştırır. İlk turda: "İlk tur: mevcut kayıtlar başlangıç noktası olarak not edildi (eski kayıtlar için iş açılmaz)."; sonra "N olay işlendi; M iş açıldı/bildirildi. Ayrıntı günlükte." veya "Yeni veya değişen kayıt yok." | Açılan işler taslakta kalır. |
| **Günlük** | **<kural> · günlük** penceresini açar. | — |
| **Düzenle** | **<kural> · düzenle** penceresini açar. | — |
| **İmza anahtarı** | (Anlık bildirim) yeni imza anahtarı üretir. | Onay sorar: "Yeni imza anahtarı oluşturulsun mu? Eski anahtarla gelen bildirimler hemen reddedilir." Geri alınamaz. |
| **Duraklat** / **Etkinleştir** | Kuralı durdurur veya çalıştırır ("Kural duraklatıldı." / "Kural etkinleştirildi."). | Geri alınabilir. |
| **Arşivle** | Kuralı arşivler; listeden kalkar, günlüğü saklanır ("Kural arşivlendi."). | Onay sorar: "'<ad>' arşivlensin mi? Kural çalışmaz; günlüğü saklanır." Ekrandan geri alınamaz. |

**Boş ekran:** "Henüz kural yok — Hazır kuralları kurun veya yeni kural ekleyin (RECAi anlatımınızdan taslak çıkarır)."

#### Yeni otomasyon kuralı / kural düzenle penceresi

[[EKRAN: ca-m-yeni-kural | Yeni otomasyon kuralı penceresi: RECAi ile taslak kutusu, tetik seçimi, koşullar ve eylem alanları | Otomasyonlar ekranında "Yeni kural"a tıklayın; "Ne olunca" = İzleme ve "Ne yapılsın" = Case aç seçiliyken görüntü alın]]

| Alan | Ne işe yarar | Nasıl doldurulur / seçenekler | Örnek | Zorunlu |
|---|---|---|---|---|
| **RECAi ile taslak** (yalnızca yeni kuralda) | Kuralı düz Türkçe anlatıp formu doldurtur | En az 10 karakter yazıp **Taslak çıkar**'a tıklayın; ad, olay türü, koşullar, iş adı ve isterler dolar (kredi harcar) | Odoo'da 50.000 TL üzeri satış siparişi onaylanınca sevkiyat planlama Case'i açılsın | Hayır |
| **Kural adı** | Listede görünen ad | En az 2, en çok 160 karakter | Büyük sipariş → sevkiyat | Evet |
| **Ne olunca** | Tetik | **Anlık bildirim** (dış sistem RECOrion'a haber gönderir), **İzleme** (RECOrion bağlantıyı belirli aralıkla tarar), **Zamanlayıcı** (belirli gün ve saatte çalışır) | İzleme | Evet |
| **Bağlantı** | İzlenecek veya verisi okunacak sistem | Etkin bağlantılardan seçin | Odoo (şirket) | İzleme'de evet |
| **Olay türü (isteğe bağlı)** | (Anlık bildirim) yalnızca bu türdeki bildirimler | Dış sistemin olay adını yazın | order.created | Hayır |
| **İzlenen model** | (İzleme) taranacak Odoo bölümü | Bilgi işlem ekibinizden öğrenin | sale.order | Evet |
| **Sıklık (dk)** | (İzleme) tarama aralığı | 5–1440; varsayılan 15 | 15 | Evet |
| **Değişiklik alanı (isteğe bağlı)** | (İzleme) değişiklikleri de yakalamak | "ör. write_date; boşsa yalnızca yeni kayıt" | write_date | Hayır |
| **Sıklık** | (Zamanlayıcı) | **Her gün**, **Her hafta**, **Her ay** | Her ay | Evet |
| **Saat** | (Zamanlayıcı) | Varsayılan 09:00 | 18:00 | Evet |
| **Gün** | (Her hafta) | Pazartesi … Pazar | Pazartesi | Evet |
| **Ayın günü** | (Her ay) | **Ay sonu** veya 1–28 | Ay sonu | Evet |
| **Koşullar (hepsi sağlanmalı; iç alan için nokta: ör. ticket.category)** | Hangi olaylarda iş açılacağı | Her satır: **Alan**, **İşlem** (=, ≠, içerir, şunlardan biri, >, ≥, <, ≤, dolu), **Değer**. **Koşul ekle** / "Koşulu sil". | amount_total ≥ 50000 | Hayır |
| **Ne yapılsın** | Eylem | **Case aç**, **Proje aç**, **Yalnızca bildir** | Case aç | Evet |
| **Bildirilecek kişi** | (Yalnızca bildir) | İnsan personelden seçin | Ayşe Yılmaz | Evet |
| **Mesaj ({{alan}} yer tutucuları kullanılabilir)** | (Yalnızca bildir) bildirim metni | Olaydaki bir alanı `{{alan}}` biçiminde yazabilirsiniz | Yeni sipariş: {{name}} | Evet |
| **İşin yöneticisi** | (Case/Proje) açılan işin sorumlusu ve onaylayıcısı | İnsan personelden seçin | Mehmet Demir | Evet |
| **Şablon (isteğe bağlı)** | Açılacak işin adım planı | "— şablonsuz (RECAi planlar)" veya Case/proje şablonları | Sevkiyat planlama | Hayır |
| **Açılacak işin adı ({{alan}} ile)** | İşin adı | Yer tutucuyla yazın | Sevkiyat: {{name}} | Önerilir |
| **İsterler** | İşin hedefi | RECAi planlarken kullanır | Müşteriye teslim tarihi bildirilsin | Hayır |
| **Şablon planıyla otomatik başlat** | (Şablon seçiliyse) | İşaretlerseniz, adımlara AI personel atanabiliyorsa iş onay beklemeden başlar; yoksa taslakta kalır | işaretsiz | Hayır |
| **Saatlik en fazla iş** | Hız sınırı | 1–200; varsayılan 20. Aşılınca **Hız sınırı** sonucu yazılır. | 20 | Evet |

Düğmeler: **Taslak çıkar**, **Vazgeç**, **Kaydet** ("Kural eklendi." / "Kural güncellendi."). Anlık bildirim kuralı ilk kaydedildiğinde imza anahtarı penceresi açılır.

#### Örnek olayla dene penceresi

Başlık "<kural> · örnek olayla dene". Metin: "Örnek veriyle kuralın ne yapacağı söylenir; iş açılmaz, dış sisteme yazılmaz. Deneme günlüğe "deneme" olarak yazılır." Alanlar: **Olay türü** (anlık bildirimde), **Örnek olay (JSON)** (kural türüne göre hazır örnekle dolu; isterseniz değerleri değiştirin). Düğmeler **Kapat**, **Dene** → sonuç rozeti ve açıklama. Hata: "Örnek olay geçerli JSON olmalı." (yapıyı bozmadan yalnızca değerleri değiştirin).

[[EKRAN: ca-m-kural-dene | Örnek olayla dene penceresi ve "Taslak açıldı" sonucu | Otomasyonlar ekranında bir kuralın "Dene" düğmesine tıklayın; "Dene"ye basıp sonuç görünürken görüntü alın]]

#### RECQmind hazır kuralları penceresi

Metin: "Açılan Case'ler taslakta kalır ve yöneticisine bildirilir. Odoo'ya yazma her zaman önizleme ve onayla yapılır."

[[EKRAN: ca-m-hazir-kurallar | RECQmind hazır kuralları penceresi | Otomasyonlar ekranında RECQmind kutusundaki "Hazır kuralları kur"a tıklayın]]

| Alan | Ne işe yarar | Nasıl doldurulur | Örnek | Zorunlu |
|---|---|---|---|---|
| **Odoo bağlantısı** | Kuralların izleyeceği Odoo | Listeden seçin | Odoo (şirket) | Evet |
| **Case yöneticisi** | Açılan Case'lerin yöneticisi | İnsan personelden seçin | Mehmet Demir | Evet |
| **İzleme sıklığı (dk)** | Tarama aralığı | 5–1440; varsayılan 10 | 10 | Evet |
| **Kurulacak kurallar** | Kurulacak kurallar | "kategori · kural adı" kutularını işaretleyin; bu bağlantıda kurulu olanlar "· bu bağlantıda kurulu", şablonu olmayanlar "· şablon yok" ile kilitli | İade, İptal | En az 1 |

Düğmeler **Vazgeç**, **Kur** ("N kural kuruldu.").

#### İmza anahtarı penceresi

Başlık "<kural> · imza anahtarı". Anlık bildirim kuralının güvenlik anahtarı bir kez gösterilir ("Bu anahtar bir daha gösterilmez. Kaybolursa yeni anahtar oluşturun (eskisi geçersiz olur)."). Pencerede dış sistemin bildirimi göndereceği adres ve imzalama kuralı yazar; bunu bilgi işlem ekibiniz dış sisteme tanımlar. 5 dakikadan eski bildirimler reddedilir. Düğmeler **Kopyala**, **Kaydettim, kapat**.

[[EKRAN: ca-m-imza-anahtari | İmza anahtarı penceresi (anahtar bulanıklaştırılmış) | Test şirketinde bir "Anlık bildirim" kuralının "İmza anahtarı" düğmesine tıklayın; görüntüde anahtarı bulanıklaştırın]]

#### Kural günlüğü penceresi

Başlık "<kural> · günlük". Yalnızca bu kuralın olayları; **Veri** / **Veriyi gizle** ile olayın verisi görülür. **Kapat**.

### Otomasyon günlüğü kartı

[[EKRAN: ca-otomasyon-gunlugu | Otomasyon günlüğü tablosu ve sonuç rozetleri | Otomasyonlar ekranında aşağı kaydırıp "Otomasyon günlüğü" kartının görüntüsünü alın]]

| Sütun | Anlamı |
|---|---|
| **Zaman** | Olayın zamanı |
| **Kural** | Hangi kural |
| **Kaynak** | anlık bildirim / izleme / zamanlayıcı / deneme ve dış kayıt numarası |
| **Sonuç** | Aşağıdaki rozetlerden biri |
| **Ayrıntı** | Açıklama |
| **İş** | **Aç** bağlantısı açılan Case'e veya projeye gider |

| Sonuç | Anlamı |
|---|---|
| **Taslak açıldı**, **Başlatıldı**, **Bildirildi** (yeşil) | İş açıldı veya bildirim gitti. |
| **Koşul tutmadı**, **Tekrar (işlenmişti)** (gri) | Koşullar sağlanmadı veya aynı olay daha önce işlendi. |
| **Döngü engellendi**, **Hız sınırı** (sarı) | RECOrion'un kendi yazdığı kayıttan tekrar iş açılmadı; veya saatlik sınır aşıldı. |
| **Hata**, **İmza reddedildi** (kırmızı) | Kural çalışamadı; veya bildirim yanlış anahtarla geldi. |
| **Deneme** (mavi) | **Dene** ile yapılan sınama. |

Boşsa "Henüz olay yok." Günlük silinemez.

**Hata mesajları (Otomasyonlar):** "Hemen çalıştırma izleme ve zamanlayıcı kurallarında vardır; diğerlerini örnek olayla deneyin.", "Kural duraklatılmış.", "İmza anahtarı yalnızca anlık bildirim kurallarında vardır.", "Bu uygulamanın hazır kuralı yok.", "Odoo bağlantısı bulunamadı veya etkin değil.", anlık bildirimlerde "İstek gövdesi çok büyük (en fazla 256 KB).", "Gövde geçerli JSON olmalı.", "Çok fazla istek; biraz sonra yeniden deneyin."

**Adım adım örnek: büyük siparişte Case açan kural**

> **Örnek:**
> 1. **Otomasyonlar** → **Yeni kural**. **RECAi ile taslak** kutusuna "Odoo'da 50.000 TL üzeri satış siparişi gelince sevkiyat planlama Case'i açılsın, yöneticisi Mehmet Demir olsun" yazıp **Taslak çıkar**'a tıklayın.
> 2. Formu kontrol edin: **Ne olunca** = İzleme, **Bağlantı** = Odoo (şirket), **İzlenen model** = sale.order, koşul `amount_total ≥ 50000`, **Ne yapılsın** = Case aç, **İşin yöneticisi** = Mehmet Demir.
> 3. **Kaydet**'e tıklayın. Satırda **Dene** ile örnek olayda "Taslak açıldı" sonucunu görün.
> 4. **Hemen çalıştır**'a tıklayın. İlk tur başlangıç noktasıdır; mevcut siparişler için iş açılmaz. Sonraki yeni siparişlerde Case açılır.

**Sık sorulan sorular:**

- *Otomasyon açtığı işleri kendisi başlatır mı?* Hayır; varsayılan olarak taslakta kalır ve yöneticisinin onayını bekler. Yalnızca şablonlu ve AI personel atanabilen işlerde "otomatik başlat" seçilebilir.
- *Aynı kayıttan iki kez iş açılır mı?* Hayır; aynı olay ikinci kez işlenmez (**Tekrar (işlenmişti)**). RECOrion'un kendi yazdığı kayıtlardan da iş açılmaz (**Döngü engellendi**).
- Açılan işlerdeki RECAi çalışması şirket kredisinden düşer.

### RECSlip.App v2 aylık süreç kartı

**Bu kart ne işe yarar?** RECSlip.App v2 ile aylık masraf sürecini kurarsınız. Kart Otomasyonlar ekranında, RECQmind kutusunun yanındadır. Sürecin tamamı (ön koşullar, takvim, kriterler, sık sorulan sorular) ayrı bölümde anlatılır: **RECSlip.App v2 ile aylık masraf süreci**.

[[EKRAN: ca-recslip-karti | RECSlip.App v2 aylık süreç kartı: "Kurulmadı" rozeti ve "Kur" düğmesi | Şirket Yöneticisi ile giriş yapın; Kurum Zekâsı › Otomasyonlar; RECSlip süreci kurulmamış, Odoo bağlantısı olan bir test şirketinde kartın görüntüsünü alın]]

[[EKRAN: ca-recslip-karti-calisiyor | RECSlip.App v2 aylık süreç kartı kurulmuş hâlde: "Çalışıyor" rozeti, Case bağlantısı, aktarım tarihi ve "Şimdi çalıştır" | RECSlip süreci kurulmuş test şirketinde (RECOrion Canlı Test A.Ş.) Otomasyonlar ekranında kartın görüntüsünü alın]]

**Kartta görünenler:**

| Görünen | Anlamı |
|---|---|
| **RECSlip.App v2 aylık süreç** ve rozet **Çalışıyor** (yeşil) / **Kurulmadı** (gri) | Bu ay yürüyen bir RECSlip Case'i var mı. |
| Açıklama | "Fişler v2'de okunup onaya gönderilince onay adımlarını kişilerin AI personeli kriterlere göre yürütür; her ay bir Case açılır, ay sonu kesim ve aktarım dosyası Case'te. Onaylayanlar kendi Odoo anahtarlarını Bağlantılarım'dan ekler (N kişi ekledi)." Parantezdeki sayı, kullanılabilir anahtar tanımlamış kişi sayısıdır. |
| Case bağlantısı (kuruluysa) | "RECSlip masraf süreci AAAA-AA"; tıklayınca Work Space'te Case açılır. Yanında "aktarım <tarih>": bu ayın aktarım dosyası tarihi. |
| "Önce Entegrasyonlar'da RECSlip.App v2 kurulu Odoo'yu bağlayın." | Şirkette Odoo bağlantısı yok; **Kur** pasiftir. |

| Düğme | Ne yapar | Dikkat |
|---|---|---|
| **Kur** (kurulmamışsa) | Bağlantıları yeniden okuyup **RECSlip.App v2 aylık süreç** kurulum penceresini açar. | Odoo bağlantısı yoksa pasiftir. |
| **Şimdi çalıştır** (kuruluysa) | Takip süresini beklemeden bekleyen onay adımlarını işler ve Case'i ilerletir. Sonuç: "RECSlip: N bekleyen adım · AI onayı N · insana N · hata N". | "Bağlantı Yönetimi" izni ister. Odoo'da onay işlemi yapar (kişilerin kendi anahtarlarıyla). |

#### RECSlip.App v2 aylık süreç kurulum penceresi

[[EKRAN: ca-m-recslip-kurulum | RECSlip.App v2 aylık süreç kurulum penceresi: dört seçim alanı ve "Kur ve bu ayın Case'ini aç" düğmesi | Otomasyonlar ekranında RECSlip kartındaki "Kur"a tıklayın; alanlar seçilmiş hâlde görüntü alın]]

| Alan | Ne işe yarar | Nasıl doldurulur | Örnek | Zorunlu |
|---|---|---|---|---|
| **RECSlip.App v2 kurulu Odoo** | Fişlerin bulunduğu Odoo | Entegrasyonlar'daki Odoo bağlantılarından seçin; ilk bağlantı önceden seçilidir. Bağlantı etkin olmalı ve o Odoo'da RECSlip.App v2 (20.0.2.34.0 veya sonrası) kurulu olmalı. | Odoo (şirket) | Evet |
| **Case yöneticisi (muhasebeci; aktarım dosyası onun anahtarıyla oluşturulur)** | Aylık Case'in sorumlusu | İnsan personelden seçin. Bu kişi **Bağlantılarım**'da bu Odoo için kendi anahtarını önceden tanımlamış olmalı. | Zeynep Kaya | Evet |
| **Kapanış raporunu yazacak AI personel** | Ay sonu raporunu yazan AI personel | AI personelden seçin | Muhasebe Asistanı Ada | Evet |
| **Kapanış raporunu onaylayacak kişi (muhasebe müdürü)** | Raporu onaylayan kişi | İnsan personelden seçin | Ayşe Yılmaz | Evet |

Not: "Ayarlar ve onay kriterleri önerilen varsayılanlarla gelir; Case'in RECSlip sekmesinden değiştirilir."

Düğmeler: **Vazgeç**, **Kur ve bu ayın Case'ini aç** (dört alan seçilmeden pasif; sürerken "Kuruluyor…"). Başarıda "RECSlip aylık süreci kuruldu; bu ayın Case'i açıldı."

| Hata | Anlamı | Ne yapmalı |
|---|---|---|
| "Odoo bağlantısı bulunamadı veya etkin değil." | Seçilen bağlantı devre dışı. | **Entegrasyonlar**'da bağlantıyı etkinleştirin. |
| "Bu Odoo'da RECSlip.App v2 (20.0.2.34 veya sonrası) kurulu değil (kurulu: …)." | Odoo'da v2 yok veya sürümü eski. | Odoo yöneticinize RECSlip.App v2'yi kurdurun veya güncelletin. |
| "Case yöneticisinin (muhasebecinin) bu bağlantıda kişisel Odoo anahtarı yok; önce Bağlantılarım'dan tanımlamalı (aktarım dosyası onun anahtarıyla oluşturulur)." | Muhasebeci anahtarını eklememiş. | Muhasebeci Work Space › **Bağlantılarım**'dan anahtarını eklemeli. |
| "<alan> bu şirkette uygun bir kişi değil." | Seçilen kişi pasif veya yanlış türde. | Aktif bir kişi veya AI personel seçin. |
| "RECSlip sürecini entegrasyon yöneticisi kurar." | "Bağlantı Yönetimi" izniniz yok. | Entegrasyon Yöneticisine kurdurun. |

## Mevzuat Paketleri

### Mevzuat Paketleri ekranı

**Bu ekran ne işe yarar?** RECDx'te bir uzman tarafından kontrol edilip yayımlanan mevzuat özet kartlarını (ör. vergi, iş hukuku, KVKK) şirketiniz için açar veya kapatırsınız. Açık paketlerdeki kartları AI personel ilgili işlerde kaynak ve sürüm göstererek kullanır. Ekrandaki başlık "Mevzuat bilgi paketleri".

**Ne zaman kullanırım?** Kurulumda şirketinizi ilgilendiren paketleri açmak için; yeni bir paket yayımlandığında.

**Kimler görür / değiştirir?** Menüyü "Mevzuat Paketlerini Açma/Kapatma" izni olanlar görür (Şirket Yöneticisi, Yapay Zeka ve Ajan Lideri, Operasyon Yöneticisi). **Aç** / **Kapat** düğmeleri Şirket Yöneticisinde ve "Şirket Ayarlarını Yönetme" izni olanlarda görünür; diğerleri yalnızca **Kartları gör**'ü kullanır.

[[EKRAN: ca-mevzuat-paketleri | Mevzuat Paketleri: uyarı notu ve Açık/Kapalı rozetli paket listesi | Şirket Yöneticisi ile giriş yapın; Kurum Zekâsı › Mevzuat Paketleri; en az iki paketin göründüğü hâlde görüntü alın]]

**Ekranın bölümleri:** **Mevzuat bilgi paketleri** kartı ("Açtığınız paketlerdeki özet kartları AI personel ilgili işlerde kaynak ve sürüm göstererek kullanır. Kartlar RECDx'te bir uzman tarafından kontrol edilip yayımlanır."); uyarı notu ("Bu paketler genel bilgilendirme amaçlıdır; hukuki veya mali danışmanlık yerine geçmez. Oran, tutar ve süre gibi değişebilen bilgiler için resmi kaynağa bakın."); paket listesi. Giriş alanı yoktur.

**Paket satırı:** ad ve rozet **Açık** (yeşil) / **Kapalı** (gri); "Sürüm V · N kart · kontrol: <tarih> (<uzman>)". Boşsa "Henüz yayımlanmış paket yok — RECDx uzman kontrolünü tamamladığında paketler burada görünür."

| Düğme | Ne yapar | Dikkat |
|---|---|---|
| **Kartları gör** | **<paket> · sürüm V** penceresini açar. | — |
| **Aç** | Paketi şirketiniz için açar ("'<paket>' açıldı; AI personel ilgili işlerde bu kartları kaynak göstererek kullanır."). | **Kapat** ile geri alınır. |
| **Kapat** | Paketi kapatır ("'<paket>' kapatıldı."). | **Aç** ile geri alınır. |

#### Paket kartları penceresi

Başlık "<paket adı> · sürüm V"; "Kontrol eden: <uzman> · <tarih>"; her kartta başlık, "Dayanak: …", metin ve "Resmi kaynak: …" bağlantıları; altta sorumluluk notu. Düğme **Kapat**.

[[EKRAN: ca-m-mevzuat-kartlari | Bir mevzuat paketinin kartları penceresi | Mevzuat Paketleri ekranında bir paketin "Kartları gör" düğmesine tıklayın]]

**Adım adım örnek:**

> **Örnek:** Ayşe Yılmaz "İş Hukuku" paketinin **Kartları gör** düğmesiyle içeriği ve kontrol tarihini inceler, **Kapat** ile pencereyi kapatır ve satırda **Aç**'a tıklar. Rozet **Açık** olur.

**Sık sorulan sorular:**

- *Kartları düzenleyebilir miyim?* Hayır; kartlar RECDx uzman kontrolüyle yayımlanır. Şirketiniz her zaman yayımlanmış son sürümü görür.
- *Kartlar hukuki danışmanlık yerine geçer mi?* Hayır; genel bilgilendirme amaçlıdır.

# Kullanım

## Kredi ve Kullanım

### Kredi ve Kullanım ekranı

**Bu ekran ne işe yarar?** Şirketinizin bu dönemki RECAi kredi bakiyesini, kullanımını ve kredinin nereye harcandığını (RECAi kademesi, AI personel, işlem türü) gösterir; son işlemleri ve kredi hareketlerini listeler. Kredi biterse AI personel yeni işlem yapamaz; bu ekran tükenmeyi önceden görmenizi sağlar. Ekrandaki başlık "RECOrion Kredisi".

**Ne zaman kullanırım?** Haftalık kontrolde, sarı veya kırmızı kredi uyarısı gördüğünüzde, hangi AI personelin çok kredi harcadığını merak ettiğinizde.

**Kimler görür?** "Kredi ve Kullanımı Görme" izni olanlar (Şirket Yöneticisi, Finans ve Raporlama Sorumlusu, Operasyon Yöneticisi, Güvenlik ve Uyum Denetçisi). Ekranda yalnızca kullanım verisi vardır; konuşma metni gibi içerik yer almaz.

[[EKRAN: ca-kredi-kullanim | Kredi ve Kullanım: dört sayaç, kullanım çubuğu, modele / AI personele / işlem türüne göre kartlar ve son işlemler tablosu | Şirket Yöneticisi ile giriş yapın; Kullanım › Kredi ve Kullanım; görüntü alın]]

**Ekranın bölümleri:**

1. **RECOrion Kredisi** kartı ("Her yapay zeka işlemi model katsayısı × (giriş token/1000 + 2 × çıkış token/1000) kredi harcar."), sağ üstte **Yenile**. Sayaçlar: **Kullanılabilir kredi** ("Aylık + ek kredi"), **Bu ay kullanılan** ("%NN · dönem AAAA-AA"), **Aylık hak** ("Kalan X · ay sonunda silinir"), **Ek kredi** ("Sonraki aylara devreder") ve kullanım çubuğu.
2. Üç kart: **Modele göre** (RECAi kademesine göre), **AI personele göre**, **İşlem türüne göre**; en çok kullanan 8 satır, "X kredi · N işlem".
3. **Son işlemler** tablosu (sayfa başına 10). Bu dönem başarısız işlem varsa alt başlıkta "Bu dönem N işlem başarısız oldu (kredi düşülmedi)."
4. **Kredi hareketleri** kartı (hareket varsa).

Token, yapay zekânın okuduğu ve yazdığı metnin ölçü birimidir (kabaca bir kelimenin parçası). Formül şunu söyler: RECAi'nin yazdığı metin, okuduğu metnin iki katı kredi tutar ve kademe katsayısıyla çarpılır.

**Görünenler:**

| Öğe | Anlamı |
|---|---|
| **Kredi tükendi: AI personeller yeni işlem yapamaz** (kırmızı) | Bakiye sıfır veya altında. |
| **Aylık kredinin %NN'i kullanıldı** (sarı) | Aylık hakkın %80'i veya fazlası kullanıldı. |
| **Son işlemler** sütunları | **Zaman**, **İşlem**, **Model** (RECAi kademesi), **AI Personel**, **Token (giriş/çıkış)** (B = bin, M = milyon), **Kredi**, **Durum** (**Başarılı** yeşil / **Başarısız** kırmızı, kredi düşülmez). Token dışındaki sütun başlıklarına tıklayarak sıralanır. |
| **İşlem** türleri | AI personel sohbeti, Beyin AI, Manifesto üretimi, Rol promptu üretimi, Ünvan incelemesi, Derin araştırma, Öğrenme, Hafıza vektörleme, Hafıza sıralama, Sohbet |
| **Kredi hareketleri** türleri | Aylık kredi hakkı (+), Ek kredi (+), Süresi dolan kredi (−), Düzeltme (±), Kullanım (−); satırda "<tür> · dönem · not" ve tutar |
| Boş ekran | "Bu dönem kullanım yok.", "Henüz yapay zeka işlemi yapılmadı." |
| Hata | **Kredi bilgisi alınamadı** ve **Tekrar dene** |

| Düğme | Ne yapar | Dikkat |
|---|---|---|
| **Yenile** | Kredi verisini yeniden yükler. | — |
| **Tekrar dene** | (Hata durumunda) yeniden yükler. | — |

Ek kredi satın alma bu ekranda yoktur; RECDx üzerinden yapılır.

**Adım adım örnek:**

> **Örnek:** Ayşe Yılmaz ayın 20'sinde sarı "Aylık kredinin %85'i kullanıldı" uyarısını görür.
> 1. **AI personele göre** kartında en çok krediyi "Sevkiyat Asistanı Deniz"in harcadığını görür.
> 2. **Modele göre** kartında Deniz'in RECAi Derin kullandığını fark eder; **AI Ajan İşe Alım** › **Düzenle**'den Deniz'i RECAi Mergen'e geçirir.
> 3. Ay sonuna kadar yetmeyecekse ek kredi için RECDx ile görüşür.

**Sık sorulan sorular:**

- *Ay sonunda kalan kredi ne olur?* Aylık hak ay sonunda silinir; ek kredi sonraki aylara devreder.
- *Başarısız işlemden kredi düşer mi?* Hayır.
- *Kredi bitince ne çalışmaz?* AI personel, Beyin AI ve RECAi önerileri (prompt yazma, eşleme önerisi, taslak çıkarma) çalışmaz.

# RECSlip.App v2 ile aylık masraf süreci

Bu bölüm, RECSlip.App v2 kullanan şirketlerin masraf fişi onaylarını RECOrion'daki AI personele yürütmesini ve her ayın kapanışını RECOrion'da bir Case olarak izlemesini uçtan uca anlatır. Kurulum Şirket Yönetimi'nde, günlük kullanım Work Space'te yapılır.

## Ne işe yarar?

Çalışanlarınız masraf fişlerini RECSlip.App v2'ye (Odoo) yükler. RECSlip fişi okur, hesap kodunu seçer ve çalışan fişi onaya gönderir. Fiş, RECSlip'teki onay zincirine girer: onay kuralı varsa kurala göre, yoksa normal sırayla önce **yönetici**, sonra **muhasebe** onayı.

RECOrion bu noktadan sonra devreye girer:

1. Her onay adımında, o adımın onaylayıcısının (ör. yöneticinin) RECOrion'daki **AI personeli** fişi sizin belirlediğiniz **kriterlere** göre inceler.
2. Fiş kriterlere uyuyorsa AI personel fişi **onaylayıcının kendi Odoo anahtarıyla** onaylar. RECSlip'te fiş "RECAi onaylı" olarak işaretlenir; onaylayan "<AI personel> (RECAi, <kişi> adına)" diye yazılır.
3. Fiş kriterlere uymuyorsa AI personel karar vermez; fiş gerekçesi ve varsa hesap düzeltme önerisiyle kişinin **Work Space › Onaylarım** ekranına düşer. Kişi **Onayla** veya **Reddet** der.
4. Muhasebe adımında AI personel kalem hesaplarını da kontrol eder; yanlış hesabı düzeltip onaylayabilir.
5. Her ay bir **"RECSlip masraf süreci AAAA-AA"** Case'i açılır. Ay sonu kesimi, geç gelen fişler, muhasebe programına aktarım dosyası, dosyanın işlenip işlenmediğinin takibi ve kapanış raporu bu Case'in adımlarıdır.

Sonuç: Kriterlere uyan rutin fişler insan beklemeden onaylanır; yöneticiler ve muhasebe yalnızca dikkat isteyen fişlere bakar; ay sonu kapanışı takvime göre kendiliğinden ilerler.

> **Örnek:** Örnek Lojistik A.Ş.'de Can Öztürk 480 TL'lik bir taksi fişi yükler. Yöneticisinin AI personeli fişi inceler: tutar sınırın altında, risk yok, hafta içi, mükerrer değil. Fişi yönetici adına onaylar. Muhasebe adımında Zeynep Kaya'nın AI personeli kalemin hesabının onaylı hafızadan geldiğini görür ve fişi Zeynep adına onaylar. Kimse hiçbir şeye tıklamadan fiş **Tamamlandı** olur. Aynı gün gelen 7.200 TL'lik bir otel fişi ise tutar sınırını aştığı için yöneticinin **Onaylarım** ekranına düşer.

## Ön koşullar

| Ön koşul | Nerede yapılır | Kim yapar |
|---|---|---|
| Odoo 20 üzerinde **RECSlip.App v2** kurulu olmalı (sürüm 20.0.2.34.0 veya sonrası). Eski RECSlip v1 bu süreçte kullanılmaz. | Odoo › Uygulamalar | Odoo yöneticiniz |
| RECSlip'te onay zinciri hazır olmalı: yöneticiler ve muhasebeciler Odoo kullanıcısı olmalı; gerekiyorsa onay kuralları tanımlı olmalı. | RECSlip.App v2 (kendi kılavuzu, "Onay süreci ve onay kuralları") | Odoo yöneticiniz |
| RECOrion **Entegrasyonlar**'da bu Odoo için etkin bir bağlantı olmalı. | Şirket Yönetimi › Kurum Zekâsı › Entegrasyonlar | Entegrasyon Yöneticisi |
| Her onaylayıcının (yönetici, ek onaylayıcı, muhasebeci) RECOrion'da bir kullanıcısı olmalı. | Şirket Yönetimi › Personel › Kullanıcı Yönetimi | Şirket yöneticisi |
| Onaylayıcıların adına çalışacak **AI personel** işe alınmış olmalı (ör. "Masraf Onay Asistanı", "Muhasebe Asistanı"). Kapanış raporunu yazacak bir AI personel de gerekir. | Şirket Yönetimi › Personel › AI Ajan İşe Alım | Şirket yöneticisi |
| Her onaylayıcı **kendi Odoo kullanıcısının API anahtarını** RECOrion'a eklemeli. Muhasebecinin (Case yöneticisi) anahtarı kurulumdan önce şarttır. | Work Space › Bağlantılarım › Şirket sistemlerindeki anahtarlarım | Her onaylayıcı kendisi |

> **Dikkat:** AI personel yalnızca anahtarını ekleyen kişinin onay adımlarını yürütür. Anahtar eklemeyen onaylayıcının fişleri eskisi gibi Odoo'da kendisini bekler; RECOrion bu adımlara dokunmaz.

### Kişisel anahtar nasıl oluşturulur ve eklenir?

Bu işi her onaylayıcı kendisi yapar. Anahtar kişinin kendi Odoo kullanıcısına aittir; AI personel o kişinin Odoo'daki yetkileriyle sınırlıdır ve Odoo'daki kayıtlarda o kişi görünür.

1. **Odoo'da:** Sağ üstteki adınıza tıklayın › **Tercihler** › **Hesap Güvenliği** › **Yeni API Anahtarı**. Anahtara bir ad verin (ör. "RECOrion") ve bir bitiş tarihi seçin (Odoo 20'de bitiş tarihi zorunludur). Odoo anahtarı bir kez gösterir; kopyalayın.
2. **RECOrion'da:** Work Space'te **Bağlantılarım**'a geçin. **Şirket sistemlerindeki anahtarlarım** kartında **Anahtar ekle**'ye tıklayın.
3. **Sistem** olarak RECSlip'in kurulu olduğu Odoo bağlantısını seçin, **API anahtarı** alanına anahtarı yapıştırın.
4. **Adınıza çalışacak AI personel**'i seçin (ör. yöneticiyseniz "Masraf Onay Asistanı").
5. **Anahtarın bitiş tarihi**'ne Odoo'da seçtiğiniz tarihi yazın.
6. **Dene ve kaydet**'e tıklayın. RECOrion anahtarı dener; çalışırsa "Kaydedildi: <Odoo giriş adınız>" bildirimi gelir ve kart **Etkin** olur.

### Bağlantılarım › Şirket sistemlerindeki anahtarlarım (Work Space, kısaca)

Ayrıntısı Work Area Kılavuzu'ndadır. Kartın alt başlığı: "AI personeliniz sizin adınıza (ör. RECSlip'te masraf onayı) yalnızca kendi kullanıcı anahtarınızla işlem yapar; kayıtlarda siz ve 'RECAi' görünür."

[[EKRAN: wa-baglantilarim-anahtarlar | Work Space › Bağlantılarım: "Şirket sistemlerindeki anahtarlarım" kartında Etkin rozetli bir anahtar | Muhasebeci kullanıcısıyla (test şirketi) giriş yapın; Work Space üst menüsünden "Bağlantılarım"a tıklayın; anahtar eklenmiş hâlde görüntü alın]]

[[EKRAN: wa-m-anahtar-ekle | Anahtar ekle penceresi: Sistem, API anahtarı, Adınıza çalışacak AI personel, Anahtarın bitiş tarihi | Bağlantılarım'da "Anahtar ekle"ye tıklayın; anahtar alanı boşken görüntü alın]]

| Alan (Anahtar ekle / Anahtarı düzenle) | Ne işe yarar | Nasıl doldurulur | Örnek | Zorunlu |
|---|---|---|---|---|
| **Sistem** | Anahtarın ait olduğu bağlantı | Şirketin etkin Odoo bağlantılarından seçin (yalnızca yeni anahtarda) | Odoo (şirket) | Evet |
| **API anahtarı** / **Yeni API anahtarı (değiştirmeyecekseniz boş bırakın)** | Odoo anahtarınız | Yapıştırın (en az 8 karakter). "Odoo › sağ üst › Tercihler › Hesap Güvenliği › Yeni API Anahtarı. Anahtar denenir, şifreli saklanır, bir daha gösterilmez." | •••••• | Yeni anahtarda evet |
| **Adınıza çalışacak AI personel** | Sizin adınıza karar verecek AI personel | Listeden seçin. Boş bırakırsanız RECSlip'te karar veren olarak "RECAi Masraf Onay Asistanı" (yönetici adımı) veya "RECAi Muhasebe Kontrol Personeli" (muhasebe adımı) yazar. | Masraf Onay Asistanı | Hayır |
| **Anahtarın bitiş tarihi** | Anahtarın Odoo'daki bitişi | "Odoo'da verdiğiniz bitiş; yaklaşınca hatırlatılır." | 31.12.2026 | Hayır |

| Düğme / rozet | Anlamı |
|---|---|
| **Etkin** (yeşil) | Anahtar çalışıyor. |
| **N gün kaldı** (sarı) | Bitiş tarihine 14 gün veya daha az kaldı; yenileyin. |
| **Süresi doldu** (kırmızı) | Bitiş tarihi geçti; AI personeliniz adınıza işlem yapmaz. |
| **Geçersiz** (kırmızı) | Odoo anahtarı reddetti (ör. Odoo'da silindi). |
| **Dene** | Anahtarı yeniden dener ("Anahtar çalışıyor: <giriş adı>" veya hata). |
| **Düzenle** | AI personeli, bitiş tarihini veya anahtarı değiştirir. |
| **Sil** | Onay sorar: "<bağlantı> anahtarınız silinsin mi? AI personeliniz bu sistemde sizin adınıza işlem yapamaz." |

Boş kart: "Henüz anahtar yok" ve "Odoo kullanıcınızın API anahtarını ekleyin (Odoo › Tercihler › Hesap Güvenliği › Yeni API Anahtarı)." Şirkette Odoo bağlantısı yoksa: "Şirketinizde kişisel anahtar kullanılan bir bağlantı (Odoo) yok." Anahtar yanlışsa: "Anahtar denenemedi: …".

> **Dikkat:** Anahtar RECOrion'da şifreli saklanır, ekranda, kayıtlarda ve hata mesajlarında bir daha görünmez. RECDx yöneticileri dahil kimse göremez (KVKK). Anahtarı e-postayla veya mesajla kimseye göndermeyin; her kişi kendisi ekler.

## Kurulum adımları

Kurulumu "Bağlantı Yönetimi" ve "Otomasyon Kuralları" izni olan bir kişi (Şirket Yöneticisi veya Entegrasyon Yöneticisi) yapar.

1. Ön koşulları tamamlayın; özellikle muhasebecinin (Case yöneticisi olacak kişi) **Bağlantılarım**'dan anahtarını eklediğinden emin olun.
2. **Şirket Yönetimi › Kurum Zekâsı › Otomasyonlar**'a gidin. **RECSlip.App v2 aylık süreç** kartında rozet **Kurulmadı**'dır.
3. **Kur**'a tıklayın. Kurulum penceresi açılır.
4. Alanları doldurun:

| Alan | Ne seçilir | Neden önemli |
|---|---|---|
| **RECSlip.App v2 kurulu Odoo** | RECSlip'in çalıştığı Odoo bağlantısı | Fişler ve onay adımları bu Odoo'dan okunur. Kurulumda bu Odoo'da RECSlip.App v2'nin sürümü kontrol edilir. |
| **Case yöneticisi (muhasebeci; aktarım dosyası onun anahtarıyla oluşturulur)** | Muhasebeci | Aylık Case'in sorumlusu olur; S1–S6 adımları ona atanır; ayarları ve kriterleri değiştirir; hatırlatmalar ona gider. Aktarım dosyası onun Odoo anahtarıyla oluşturulur. |
| **Kapanış raporunu yazacak AI personel** | Muhasebe tarafında çalışan bir AI personel | Ay sonunda S7 kapanış raporunu yazar. |
| **Kapanış raporunu onaylayacak kişi (muhasebe müdürü)** | Raporu onaylayacak kişi | S7'yi onaylar; onaylayınca ayın Case'i kapanabilir. |

5. **Kur ve bu ayın Case'ini aç**'a tıklayın. "RECSlip aylık süreci kuruldu; bu ayın Case'i açıldı." bildirimi gelir; kart **Çalışıyor** olur ve Case bağlantısı görünür.
6. Case'i açıp **RECSlip** sekmesinde ayarları ve kriterleri kontrol edin (aşağıda). Varsayılanlar çoğu şirket için iyi bir başlangıçtır.
7. İsterseniz kartta **Şimdi çalıştır**'a tıklayarak bekleyen onay adımlarını hemen işletin. Sonra süreç kendiliğinden, **Fiş ve onay takibi** sıklığında (varsayılan 15 dakika) çalışır.

> **Örnek:** Ayşe Yılmaz kurulum penceresinde **RECSlip.App v2 kurulu Odoo**: Odoo (şirket); **Case yöneticisi**: Zeynep Kaya; **Kapanış raporunu yazacak AI personel**: Muhasebe Asistanı Ada; **Kapanış raporunu onaylayacak kişi**: kendisi. **Kur ve bu ayın Case'ini aç**'a tıklar. "RECSlip masraf süreci 2026-11" Case'i açılır.

Kurulumdan sonra her ayın ilk gününde yeni dönemin Case'i kendiliğinden açılır; önceki ayın ayarları, kriterleri ve kişileri yeni Case'e kopyalanır.

## Aylık takvim ve Case adımları (S1–S7)

Her ayın Case'inde yedi adım vardır. S1–S6 Case yöneticisine (muhasebeciye) atanır ama elle yapılmaz: koşulu oluşunca RECOrion adımı kendisi teslim eder ve teslim notuna özet yazar. S7'yi AI personel yazar, seçilen kişi onaylar.

| Adım | Ad | Ne olur | Ne zaman tamamlanır |
|---|---|---|---|
| S1 | **Fiş takibi ve AI onay yürütme** | Okunan fişlerin onay adımları izlenir; kişisel anahtarı tanımlı onaylayıcıların AI personeli kriterlere göre onaylar; kriter dışı fişler kişinin Onaylarım ekranına gerekçeyle düşer. Teslim notunda yönetici ve muhasebe karar sayıları yazar. | Ay sonu kesiminde |
| S2 | **Yönetici onayları** | Yönetici ve ek onaylayıcı adımları: AI onayları ve insan kararları. | Geç gelen fişler için son günün sonunda; karar bekleyen fiş varsa notta "sonraki dönemde de izlenir" yazar |
| S3 | **Muhasebe onayları** | Muhasebe adımları: hesap planı kontrolü, RECAi Mergen ikinci görüşü, AI düzeltmeleri ve insan kararları. Notta AI'ın hesap düzelttiği fiş sayısı ve AI–insan uyum oranı yazar. | Geç gelen fişler için son günün sonunda |
| S4 | **Ay sonu kesim** | Kesim anında onaya gönderilmemiş fişler, onayda bekleyen fişler ve tamamlanan fişler sayılır. Onaya gönderilmemiş fiş varsa Case yöneticisine "çalışanlara hatırlatın" bildirimi gider. | Ay sonu kesiminde |
| S5 | **Aktarım dosyası** | Tamamlanan fişlerden, şirketinizin RECSlip'te seçili muhasebe programına göre (Luka 1./2. sınıf, Logo 4 Web) aktarım dosyası RECSlip.App v2'de oluşturulur ve Case'e eklenir. Dönem sonuna kadarki bütün tamamlanmış fişler girer; önceki aylardan devredenler dahil. Case yöneticisine "dosya hazır" bildirimi gider. | Aktarım zamanında (S2, S3 ve S4 bittikten sonra) |
| S6 | **Muhasebe programına işleme** | Dosyanın muhasebe programına işlenmesi beklenir (RECRobo ile, şimdilik elle). RECSlip'te dosya "Muhasebeye işlendi" olarak işaretlenince adım tamamlanır. İşlenmezse hatırlatılır; tekrar sayısı dolunca aktarım iptal edilir ve fişler sonraki ayın dosyasına devreder. Bu dönemde aktarılacak fiş yoksa adım "işlenecek dosya yok" notuyla kapanır. | Dosya işlenince veya devredilince |
| S7 | **Kapanış raporu** | Dönem özeti: fiş sayıları, AI ve insan onayları, AI düzeltmeleri, AI–insan uyum oranı, aktarım sonucu. AI personel raporu yalnızca dönem verisine dayanarak yazar; seçilen kişi onaylar. | Rapor onaylanınca |

**Varsayılan ayarlarla örnek takvim (dönem 2026-11):**

| Olay | Zaman |
|---|---|
| Ay sonu kesim (S1 ve S4 tamamlanır) | 30.11.2026 18:00 |
| Geç gelen fişler için son (S2 ve S3 tamamlanır) | 03.12.2026 23:59 |
| Aktarım dosyası (S5) | 05.12.2026 10:00 |
| "Henüz işlenmedi" hatırlatmaları (S6) | Dosyadan 2 gün sonra başlar, 24 saatte bir, en çok 3 kez (07.12, 08.12, 09.12) |
| Hâlâ işlenmediyse aktarım iptali ve fişlerin devri (S6) | 10.12.2026 |
| Kapanış raporu (S7) | S6 tamamlanınca |

Saatler İstanbul saatidir. RECOrion süreci dakikada bir kontrol ettiği için olaylar belirtilen saatten birkaç dakika sonra görünebilir.

> **İpucu:** "Geç gelen fiş", ayın son günlerinde harcanıp sonraki ayın ilk günlerinde yüklenen fiştir. **Geç fiş toleransı** sayesinde bu fişler de ait oldukları ayın dosyasına girer.

## Case › RECSlip sekmesi (Work Space, kısaca)

Aylık Case Work Space'te diğer projeler gibi açılır; yalnızca RECSlip Case'lerinde ek bir **RECSlip** sekmesi vardır. Ayrıntısı Work Area Kılavuzu'ndadır. Sekmede üç kart bulunur.

[[EKRAN: wa-case-recslip-sekmesi | Case › RECSlip sekmesi: "Dönem AAAA-AA" takvim kartı | Case yöneticisi (muhasebeci) ile giriş yapın; Work Space'te "RECSlip masraf süreci 2026-11" Case'ini açın; "RECSlip" sekmesine tıklayın; üst kartın görüntüsünü alın]]

**Dönem AAAA-AA kartı (Takvim ve durum):**

| Satır | Anlamı |
|---|---|
| **Ay sonu kesim** | Kesim tarihi ve saati |
| **Geç gelen fişler için son** | Geç fişlerin beklendiği son an |
| **Aktarım dosyası** | Aktarım dosyasının oluşturulacağı zaman |
| **Yönetici adımları** / **Muhasebe adımları** | Karar sayıları (ör. "AI onayladı: 42 · İnsan kararı bekliyor: 3") veya "karar yok" |
| **AI–insan uyumu** | İnsanın verdiği kararların AI önerisiyle uyum oranı; insan kararı yoksa "henüz insan kararı yok" |
| **Aktarım** | Dosya adı · fiş sayısı · toplam tutar · durum rozeti (PENDING: bekliyor, CREATED: dosya oluşturuldu, POSTED: muhasebe programına işlendi, FAILED: oluşturulamadı veya iptal edildi) ve varsa son hata; dosya yoksa "henüz yok" |

### Ayarlar ve onay kriterleri

Alt başlık: "Sonraki ayın Case'i bu ayarlarla açılır." Değişiklikleri yalnızca Case yöneticisi ve "Tüm Projeleri Yönetme" izni olanlar yapar; diğerleri için alanlar kilitlidir ve alt başlık "Yalnızca Case yöneticisi değiştirebilir." olur. Sağ üstte **Kaydet** ("RECSlip ayarları kaydedildi.").

[[EKRAN: wa-case-recslip-ayarlar | Ayarlar ve onay kriterleri kartı: süre ayarları, yönetici ve muhasebe kriterleri | Case › RECSlip sekmesinde aşağı kaydırıp "Ayarlar ve onay kriterleri" kartının tamamını görüntüleyin (gerekirse iki parça)]]

**Süreç ayarları:**

| Alan | Ne işe yarar | Seçenekler / sınırlar | Varsayılan |
|---|---|---|---|
| **Fiş ve onay takibi (dakika)** | Bekleyen onay adımlarının ne sıklıkla inceleneceği | 5–1440 | 15 |
| **Onaya gönderilmemiş fiş hatırlatması (gün)** | Onaya gönderilmemiş fişler için hatırlatma süresi | 0–60. Bu sürümde onaya gönderilmemiş fişler için hatırlatma, ay sonu kesiminde (S4) Case yöneticisine bir kez gider. | 2 |
| **Kesim günü (-1: ayın son günü)** | Ayın hangi günü kesim yapılacağı | -1 (ayın son günü) veya 1–28 | -1 |
| **Kesim saati** | Kesim saati | SS:DD | 18:00 |
| **Geç fiş toleransı (sonraki ayın günü)** | Önceki ayın fişleri sonraki ayın kaçına kadar beklenir (o gün 23:59'a kadar) | 0–27. 0 yazarsanız tolerans olmaz (ayın son günü 23:59). | 3 |
| **Aktarım günü (sonraki ay)** | Aktarım dosyasının sonraki ayın kaçında oluşturulacağı | 1–28 | 5 |
| **Aktarım saati** | Aktarım saati | SS:DD | 10:00 |
| **Tekrar sayısı** | Dosya oluşturulamazsa veya işlenmezse kaç kez tekrar/hatırlatma yapılacağı | 0–10 | 3 |
| **Tekrar aralığı (saat)** | Hatırlatmalar arası süre | 1–168 | 24 |
| **İşlenmedi hatırlatması (gün)** | Dosya oluşturulduktan kaç gün sonra "henüz işlenmedi" hatırlatmasının başlayacağı | 0–60 | 2 |

**Yönetici / yetkili AI onayı** (yönetici ve ek onaylayıcı adımları):

| Kriter | Ne işe yarar | Varsayılan |
|---|---|---|
| **Tümünü AI onaylasın (eşikler aranmaz)** | İşaretlenirse tutar, risk, hafta sonu ve aylık sınır kontrolleri yapılmaz. "Mükerrer şüphesi insana" işaretliyse mükerrer şüpheli fiş yine insana gider. | Kapalı |
| **En yüksek fiş tutarı** | Bu tutarın üzerindeki fiş insana gider | 2500 |
| **Çalışan başına aylık sınır** | Çalışanın o ayki toplam masrafı bu sınırı aşıyorsa fiş insana gider (0 = sınır yok) | 15000 |
| **İzinli risk** (**Yok**, **Düşük**, **Yüksek**) | RECSlip'in fişe verdiği risk seviyesi işaretli seviyelerden biri değilse fiş insana gider | Yalnızca **Yok** |
| **Hafta sonu harcaması insana** | Cumartesi veya pazar tarihli fiş insana gider | Açık |
| **Mükerrer şüphesi insana** | RECSlip'in mükerrer şüphesi bulduğu fiş insana gider | Açık |

**Muhasebe AI onayı** (muhasebe adımı):

| Kriter | Ne işe yarar | Varsayılan |
|---|---|---|
| **Tümünü AI onaylasın (eşikler aranmaz; düzeltmeler yine yapılır)** | Tutar, risk, güven ve KKEG kontrolleri yapılmaz. Şu durumlarda fiş yine insana gider: ön muhasebe özeti dengede değilse, mükerrer şüphesi varsa, fişte kalem yoksa, RECAi Mergen ikinci görüşü alınamazsa. | Kapalı |
| **En yüksek fiş tutarı** | Bu tutarın üzerindeki fiş insana gider | 5000 |
| **En düşük fiş güveni** | RECSlip'in fişi okuma güveni bu değerin altındaysa fiş insana gider (0–100) | 85 |
| **AI düzeltmesi için en düşük güven** | RECAi Mergen farklı bir hesap öneriyorsa, güveni bu değer veya üzeriyse AI hesabı düzeltir; altındaysa fiş insana gider (0–100) | 90 |
| **İzinli risk** (**Yok**, **Düşük**, **Yüksek**) | Risk seviyesi işaretlilerden biri değilse fiş insana gider | **Yok** ve **Düşük** |
| **Güvenli sayılan eşleşme kaynakları (diğerleri RECAi:Mergen ikinci görüşüne gider)** | Kalemin hesabı bu kaynaklardan geldiyse güvenilir sayılır: **Kural**, **Tedarikçi hafızası**, **Tam eşleşme**, **Onaylı hafıza**, **Elle (muhasebeci)** | Kural, Tedarikçi hafızası, Tam eşleşme, Onaylı hafıza |
| **KKEG'li fiş insana** | "Gider değil" (kanunen kabul edilmeyen gider) işaretli kalemi olan fiş insana gider | Açık |

Muhasebe tarafında **Tümünü AI onaylasın** kapalıyken, RECSlip'in "belge değil" veya "yurt dışı belgesi" olarak sınıfladığı fişler de her zaman insana gider (bu kural ekranda yoktur, değiştirilemez).

### AI kararları kartı

Alt başlık "N adım". Bu dönemde değerlendirilen her onay adımı listelenir: fiş adı · tutar · adım (Yönetici, Ek onaylayıcı, Muhasebe) · onaylayıcı; altında gerekçeler, yapılan düzeltmeler ("düzeltme: <kalem> → <yeni hesap>") ve varsa hata; sağda durum rozeti. Boşsa "Henüz değerlendirilen onay adımı yok."

[[EKRAN: wa-case-recslip-ai-kararlari | AI kararları kartı: AI onayladı, İnsan kararı bekliyor ve Odoo'dan karar verildi rozetli satırlar | Case › RECSlip sekmesinin en altındaki "AI kararları" kartının görüntüsünü alın]]

| Durum | Anlamı |
|---|---|
| **AI onayladı** (yeşil) | Fiş kriterlere uydu; AI personel kişinin anahtarıyla onayladı. |
| **İnsan kararı bekliyor** (sarı) | Fiş kriter dışı; kişinin Onaylarım ekranında. |
| **İnsan onayladı** (yeşil) | Kişi Onaylarım'dan onayladı. |
| **İnsan reddetti** (kırmızı) | Kişi Onaylarım'dan reddetti. |
| **Odoo'dan karar verildi** (gri) | Fiş Onaylarım'da beklerken kişi kararını doğrudan Odoo'da (RECSlip'te) verdi. |
| **Hata** (kırmızı) | AI onaylamaya karar verdi ama Odoo işlemi yapamadı (ör. anahtar reddedildi). Adım bir sonraki turda yeniden değerlendirilir. |

## Onay kararı nasıl verilir?

### AI onayı

Her turda RECOrion, RECSlip'te bekleyen onay adımlarını okur. Bir adımın onaylayıcısı RECOrion'da bu Odoo için kullanılabilir bir anahtar tanımladıysa, o kişinin seçtiği AI personel fişi değerlendirir:

- **Yönetici ve ek onaylayıcı adımı:** tutar, risk, mükerrer şüphesi, hafta sonu ve çalışanın aylık toplamı kontrol edilir.
- **Muhasebe adımı:** fiş düzeyinde ön muhasebe özetinin dengesi, mükerrer, kalem varlığı, tutar, risk, okuma güveni, belge türü ve KKEG kontrol edilir; ayrıca her kalemin hesabı kontrol edilir (aşağıda).

Bütün kontrollerden geçen fiş, kişinin kendi anahtarıyla onaylanır. RECSlip'teki kayıt şöyle görünür:

- Fişin **Onay** sekmesinde adımın **RECAi Kararı** sütunu işaretlidir; **RECAi Personeli** ve gerekçe görünür.
- Fiş geçmişinde onaylayan "<AI personelin adı> (RECAi, <onaylayıcı> adına)" olarak yazılır.
- Fiş listelerinde **RECAi Onaylı** sütunu ve süzgeci vardır.

**"RECAi onaylı" bayrağının anlamı:** Bu fişin o adımı bir insan tarafından değil, o insanın yetkisiyle ve onun adına AI personel tarafından, sizin belirlediğiniz kriterlere göre onaylandı. Sorumluluk ve yetki yine o kişinindir; AI personel kişinin Odoo'da yapamayacağı bir şeyi yapamaz. Kişi Onaylarım'dan kendisi karar verdiğinde bu bayrak konmaz; karar insanındır.

### İnsana düşme

Kriterlerden biri tutmazsa fiş AI tarafından onaylanmaz ve reddedilmez; kişinin önüne gelir:

1. Kişiye bildirim gider: "RECSlip: '<fiş>' (<tutar>) <yönetici/muhasebe> onayınızı bekliyor. AI önerisi: …" ve Onaylarım bağlantısı.
2. Fiş kişinin **Work Space › Onaylarım** ekranında **RECSlip masraf fişleri** başlığı altında görünür.

### Onaylarım › RECSlip masraf fişleri (Work Space, kısaca)

Ayrıntısı Work Area Kılavuzu'ndadır. Liste 15 saniyede bir kendini yeniler.

[[EKRAN: wa-onaylarim-recslip | Work Space › Onaylarım: "RECSlip masraf fişleri" bölümünde gerekçeli ve hesap düzeltme önerili bir fiş | Yönetici veya muhasebeci kullanıcısıyla (test şirketi) giriş yapın; Work Space'te "Onaylarım"a tıklayın; kriter dışı bir fiş varken görüntü alın]]

| Görünen | Anlamı |
|---|---|
| Fiş adı · tutar · çalışan · rozet "<Yönetici/Ek onaylayıcı/Muhasebe> onayı" | Hangi fiş, hangi adım |
| "<AI personel>: <gerekçeler>" | AI personelin neden insana bıraktığı (ör. "Tutar 7.200,00 sınırı (2.500,00) aşıyor.") |
| **Önerilen hesap düzeltmeleri** | (Muhasebe) "'<kalem>': <eski hesap> → **<yeni hesap>** (güven N) <gerekçe>" |
| **Onaylarken düzeltmeleri uygula** | İşaretliyse (varsayılan) onaylarken önerilen hesaplar uygulanır |
| **Onayla** | Fişi kişinin anahtarıyla onaylar ("Fiş onaylandı (RECSlip)."). |
| **Reddet** | "Fişi reddet" penceresi: "Red gerekçesi (çalışana ve RECSlip geçmişine yazılır):". Gerekçe zorunludur ("Red gerekçesi yazın."). Sonuç "Fiş reddedildi (RECSlip)." |

### RECAi Mergen ikinci görüşü ve hesap düzeltme (muhasebe adımı)

RECSlip her kalemin hesabını farklı kaynaklardan seçer. Muhasebe AI personeli şöyle ilerler:

1. Kalemin hesabı **güvenli sayılan bir kaynaktan** geldiyse (varsayılan: kural, tedarikçi hafızası, tam eşleşme, onaylı hafıza; yani şirketinizin hesap kuralları ve muhasebecinin önceki onayları) hesap doğru kabul edilir.
2. Gelmediyse AI personel **RECAi Mergen**'den ikinci görüş alır. RECAi Mergen, RECSlip'in hesap kodu seçerken kullandığı etkin talimatın aynısını, fişin kalemlerini, RECSlip'in o kalem için bulduğu aday hesapları ve onaylı örnekleri kullanır; yalnızca aday hesaplardan birini seçebilir.
3. Sonuca göre:
   - RECAi Mergen aynı hesabı öneriyorsa ve emin ise: sorun yok.
   - Farklı bir hesap öneriyor ve güveni **AI düzeltmesi için en düşük güven** değerinin (varsayılan 90) üzerindeyse: AI personel hesabı düzeltir ve fişi onaylar. Düzeltme RECSlip'te "eski hesap → yeni hesap" olarak kayda geçer.
   - Farklı hesap öneriyor ama güveni düşükse, emin değilse veya ikinci görüş alınamazsa: fiş öneriyle birlikte muhasebecinin Onaylarım ekranına düşer.

RECAi'nin onayladığı ve düzelttiği fişlerden öğrenilenler RECSlip'in **Onaylı Hafıza** ekranına "RECAi Onayı" / "RECAi Düzeltmesi" kaynağıyla yazılır; muhasebecinin kendi kararlarından ayrı izlenir.

### AI–insan uyumu

Kişi Onaylarım'dan karar verdiğinde bu karar AI önerisiyle karşılaştırılır. Örneğin muhasebeci AI'ın önerdiği hesap düzeltmesini kabul edip onaylarsa bu "uyum" sayılır. Oran Case'in **RECSlip** sekmesinde **AI–insan uyumu** satırında ve kapanış raporunda görünür. Oran yükseldikçe kriterleri güvenle gevşetebilirsiniz.

## Aktarım dosyası, tekrar ve devretme

- Aktarım zamanında RECOrion, Case yöneticisinin (muhasebecinin) anahtarıyla RECSlip.App v2'de aktarım dosyası oluşturur. Dosyaya dönem sonuna kadarki bütün **Tamamlandı** durumundaki fişler girer (önceki aylardan devredenler dahil). Biçim, RECSlip'te şirketiniz için seçili muhasebe programına göredir (Luka 1. sınıf, Luka 2. sınıf, Logo 4 Web).
- Dosya Case'in S5 adımına eklenir; Case yöneticisine "aktarım dosyası hazır … RECRobo ile muhasebe programına işleyin, sonra RECSlip'te 'Muhasebeye işlendi' işaretleyin" bildirimi gider. RECOrion dosyayı yalnızca üretir; muhasebe programına işleme RECRobo ile (şimdilik elle) yapılır.
- Dosya oluşturulamazsa (ör. muhasebecinin anahtarının süresi dolmuşsa) yeniden denenir; tekrar sayısı dolunca Case yöneticisine "aktarım dosyası N denemede oluşturulamadı" bildirimi gider.
- Dosya oluşturulduktan sonra **İşlenmedi hatırlatması** süresi kadar beklenir; RECSlip'te dosya işlendi olarak işaretlenmezse **Tekrar aralığı**nda bir, **Tekrar sayısı** kadar hatırlatma gider ("<dosya> henüz muhasebe programına işlenmedi (N. hatırlatma)").
- Hatırlatmalar bittiği hâlde dosya işlenmezse aktarım RECSlip'te iptal edilir ve fişler **sonraki ayın dosyasına devreder**. S6 bu notla kapanır ve Case yöneticisine bildirim gider.

## Kapanış raporu

S6 tamamlanınca S7 başlar. Kurulumda seçtiğiniz AI personel, dönem verisine dayanarak kapanış raporunu yazar: yönetici ve muhasebe adımlarının karar sayıları, AI–insan uyum oranı, aktarım dosyası ve durumu, AI'ın yaptığı hesap düzeltmeleri. Rapor, seçtiğiniz onaylayıcının **Onaylarım** ekranına iş adımı olarak düşer; onaylayıcı Work Space'te adımı inceleyip onaylar veya revizyon ister (Work Area Kılavuzu).

## Sık sorulan sorular

**Anahtarımın süresi dolarsa ne olur?**
Bağlantılarım'da rozet 14 gün kala **N gün kaldı** (sarı), bitişte **Süresi doldu** (kırmızı) olur. Süresi dolmuş veya geçersiz anahtarla AI personeliniz sizin adınıza karar vermez; onay adımlarınız Odoo'da sizi bekler. Onaylarım'dan karar vermek istediğinizde "Odoo anahtarınız geçersiz veya süresi dolmuş; Bağlantılarım'dan yenileyin." uyarısı alırsınız. Case yöneticisinin anahtarı biterse aktarım dosyası oluşturulamaz. Çözüm: Odoo'da yeni bir API anahtarı oluşturun → **Bağlantılarım** › **Düzenle** → **Yeni API anahtarı** alanına yapıştırın, **Anahtarın bitiş tarihi**'ni güncelleyin → **Dene ve kaydet**.

**Kriterleri nasıl gevşetirim? "Tümünü AI onaylasın" ne yapar?**
Case'in **RECSlip** sekmesinde **Ayarlar ve onay kriterleri**'ni Case yöneticisi değiştirir. Gevşetmek için tutar sınırlarını yükseltin, **İzinli risk**'e **Düşük** ekleyin veya **Hafta sonu harcaması insana** kutusunu kaldırın. **Tümünü AI onaylasın** işaretlenirse eşikler aranmaz; ancak yönetici tarafında mükerrer şüphesi (kutu açıksa), muhasebe tarafında dengesiz ön muhasebe özeti, mükerrer şüphesi, kalemsiz fiş ve ikinci görüşün alınamaması yine insana gider. Muhasebe tarafında hesap düzeltmeleri yine yapılır. Değişiklik bu ayın kalan adımlarında hemen uygulanır ve sonraki ayın Case'ine kopyalanır.

> **Dikkat:** "Tümünü AI onaylasın"ı açmadan önce birkaç ay **AI–insan uyumu** oranını izleyin. Uyum yüksekse gevşetin.

**Yanlış bir AI kararını nasıl görürüm, ne yaparım?**
1. Case'in **RECSlip** sekmesindeki **AI kararları** kartında **AI onayladı** satırlarının gerekçelerini ve düzeltmelerini okuyun.
2. RECSlip.App v2'de **RECAi Onaylı** süzgeciyle AI'ın onayladığı fişleri, fişin **Onay** sekmesinde **RECAi Kararı**nı görün.
3. Yanlış bir hesap öğrenildiyse RECSlip'in **Onaylı Hafıza** ekranında **Kaynak**'a göre gruplayın ve yanlış satırı **Aktif** anahtarıyla kapatın. Fişin kendisini RECSlip.App v2'de, kendi kılavuzundaki muhasebeci işlemleriyle düzeltin.
4. Tekrarlanmaması için ilgili kriteri sıkılaştırın (ör. **En yüksek fiş tutarı**nı düşürün veya güvenli eşleşme kaynaklarından birini kaldırın).

**Odoo'dan doğrudan onaylarsam ne olur?**
Sorun olmaz. Fiş Onaylarım'da beklerken kararınızı RECSlip'te verirseniz RECOrion bunu bir sonraki turda görür; fiş Onaylarım'dan kalkar ve AI kararları kartında **Odoo'dan karar verildi** olarak görünür. Bu arada RECOrion'dan karar vermeye çalışırsanız "Bu fiş artık karar beklemiyor." uyarısı alırsınız. AI personel henüz incelemeden önce Odoo'da karar verdiyseniz o adım RECOrion'a hiç gelmez.

**Bir onaylayıcı anahtar eklemezse ne olur?**
O kişinin onay adımlarına RECOrion dokunmaz; adımlar RECSlip'te her zamanki gibi (RECSlip'in kendi hatırlatmaları ve vekâlet kurallarıyla) kişiyi bekler.

**Bir adımda birden çok onaylayıcı varsa?**
RECSlip'te birinin onayı yeterlidir. RECOrion, adımın onaylayıcılarından kullanılabilir anahtarı olan ilk kişinin AI personeliyle değerlendirir; fiş insana düşerse o kişinin Onaylarım ekranına gider.

**AI personel fişi reddedebilir mi?**
Hayır. AI personel ya onaylar ya da kararı insana bırakır. Reddi her zaman bir insan, gerekçe yazarak verir.

**Kurulumu kim yapar, ayarları kim değiştirir?**
Kurulumu ve **Şimdi çalıştır**'ı "Bağlantı Yönetimi" izni olanlar yapar (Otomasyonlar ekranı ayrıca "Otomasyon Kuralları" izni ister). Ayarları ve kriterleri Case yöneticisi ve "Tüm Projeleri Yönetme" izni olanlar değiştirir.

**Kişisel anahtarım RECDx'e veya başka çalışanlara görünür mü?**
Hayır. Anahtar şifreli saklanır, kimseye gösterilmez (sizin dahil). Kayıtlarda yalnızca Odoo giriş adınız görünür.

**Eski RECSlip (v1) hazır kurallarımız ne oldu?**
Kaldırıldı; kurulu olanlar duraklatıldı. Otomasyonlar ekranında **Arşivle** ile temizleyip bu bölümdeki aylık süreci kurun.

# Sık karşılaşılan durumlar ve çözümleri

| Durum | Neden | Çözüm |
|---|---|---|
| Work Space'te **🏢 Şirket Yönetimi** düğmesi yok. | Hiçbir yönetim izniniz yok (ör. Uzman Kullanıcı). | Şirket yöneticinizden uygun rolü veya ek izni isteyin. |
| Sol menüde bir menü görünmüyor. | O menünün izni sizde yok. | **Menü ağacı** tablosundaki izni şirket yöneticinizden isteyin. |
| Bir düğmeye basınca "Bu işlem için yetkiniz yok." uyarısı geliyor. | Menüyü görüyorsunuz ama o işlemin izni yok (ör. Proje Yöneticisi AI personeli düzenlemeye çalışıyor). | İlgili izni (ör. "AI Personel Ayarları ve Bilgi Kaynakları") ek izin olarak isteyin. |
| Entegrasyonlar ekranında "Entegrasyonları yalnızca entegrasyon yönetimi yetkisi olanlar yönetebilir." | "Bağlantı Yönetimi" izniniz yok (ör. Finans ve Raporlama Sorumlusu). | Aktarım onaylarınızı **Work Space › Onaylarım**'dan verin; bağlantı işleri için Entegrasyon Yöneticisine başvurun. |
| Yeni kullanıcı eklenemiyor: "… İnsan Kullanıcı kotası … dolmuştur." | Paket kotası dolu. | Kişiyi **Pasif** ekleyin, ayrılan birini pasife alın veya paketinizi yükseltin. |
| Son şirket yöneticisi silinemiyor veya pasife alınamıyor. | Şirkette en az bir aktif Şirket Yöneticisi olmalı. | Önce başka birine **Şirket Yöneticisi** rolü verin. |
| **+ Yeni AI Ajan İşe Al** pasif. | AI personel kotası dolu. | Bir AI personeli **İşten Çıkar** veya paketinizi yükseltin. |
| AI personel işe alımında ünvan seçilemiyor. | Şirkette ünvan yok veya departmanda uygun ünvan yok. | **Ünvan Tanımları**'nda ünvan tanımlayın ya da sihirbazda katalog departmanından seçin. |
| Doküman **İşleniyor**'da uzun süre kalıyor. | Büyük veya çok sayfalı dosya. | Bekleyin; liste kendini yeniler. Uzun sürerse dosyayı bölüp yeniden yükleyin. |
| Doküman **Karantinada** veya **İşlenemedi**. | İçerik güvenliği sorunu veya okunamayan dosya. | **Aç** → **Yeniden işle**; olmazsa farklı biçimde (ör. PDF) yükleyin. |
| Katalogdan departman eklerken "Uygun departman bulunamadı". | Sektör ve NACE bilgisi eksik. | **Sektörel Manifesto**'da sektörlerinizi seçip kaydedin. |
| Genel Bakış'ta maliyet kartları yok. | "Maliyet ve Bütçe Bilgilerini Görme" izni yok. | İzni isteyin. |
| ROI kartı "veri yok" diyor. | İnsan personelin günlük maliyeti girilmemiş. | **Kullanıcı Yönetimi**'nde **Günlük maliyet** girin. |
| Beyin AI'da **RECAi** listesi kilitli. | "Şirket Ayarlarını Yönetme" izniniz yok. | Şirket yöneticisine seçtirin. |
| Odoo bağlantısında **Dene** hata veriyor. | Adres, veritabanı adı, kullanıcı veya anahtar yanlış. | **Düzenle** ile düzeltin; Odoo'da anahtarın geçerli olduğunu kontrol edin. |
| Araç çağrı kaydında **Yetkisiz**. | AI personelin o araca yetkisi yok. | **Araçlar ve yetkiler**'den yetki verin. |
| Eşlemede **Onayla** pasif. | Kaydedilmemiş değişiklik var veya son deneme hatalı. | **Kaydet** → **Dene (yazmadan)**; hata yoksa **Onayla**. |
| Otomasyon iş açmıyor; günlükte **Koşul tutmadı**. | Koşullar sağlanmıyor. | Koşulları **Dene** ile örnek olayda sınayın. |
| Otomasyon günlüğünde **Hız sınırı**. | Saatlik iş sınırı aşıldı. | **Saatlik en fazla iş** değerini artırın. |
| Eski RECSlip kuralında "RECSlip v1 kuralı: RECSlip.App v2 aylık sürecine geçildi" hatası. | v1 kuralları kaldırıldı. | Kuralı **Arşivle**'yin; **RECSlip.App v2 aylık süreç** kartını kurun. |
| RECSlip kartında **Kur** pasif. | Odoo bağlantısı yok. | **Entegrasyonlar**'da RECSlip.App v2 kurulu Odoo'yu bağlayın. |
| RECSlip kurulumunda "… kişisel Odoo anahtarı yok …". | Muhasebeci anahtarını eklememiş. | Muhasebeci Work Space › **Bağlantılarım**'dan anahtarını eklesin. |
| RECSlip kurulumunda "Bu Odoo'da RECSlip.App v2 … kurulu değil". | Odoo'da v2 yok veya sürüm eski. | RECSlip.App v2'yi kurdurun veya güncelletin. |
| Fişler AI tarafından onaylanmıyor, hep Odoo'da bekliyor. | Onaylayıcının anahtarı yok, süresi dolmuş veya geçersiz. | Onaylayıcı **Bağlantılarım**'da anahtarını ekleyip **Dene** ile sınasın. |
| Fişlerin çoğu Onaylarım'a düşüyor. | Kriterler sıkı. | Case › **RECSlip** › **Ayarlar ve onay kriterleri**'nde tutar sınırlarını ve izinli riski gözden geçirin. |
| Onaylarım'da "Odoo anahtarınız geçersiz veya süresi dolmuş; Bağlantılarım'dan yenileyin." | Kişisel anahtar kullanılamıyor. | Odoo'da yeni anahtar oluşturup **Bağlantılarım** › **Düzenle**'den girin. |
| Onaylarım'da "Bu fiş artık karar beklemiyor." | Karar Odoo'da verilmiş. | Bir şey yapmanız gerekmez. |
| Aktarım dosyası oluşmadı; bildirimde "… denemede oluşturulamadı". | Case yöneticisinin anahtarı geçersiz veya Odoo'da sorun var. | Muhasebeci anahtarını yenilesin; sonra **Otomasyonlar** › RECSlip kartında **Şimdi çalıştır**. |
| Kredi bitti; AI personel çalışmıyor. | Aylık hak ve ek kredi tükendi. | Ek kredi için RECDx ile görüşün; **Kredi ve Kullanım**'da en çok harcayanı bulun. |
| Logo yüklenmiyor: "Logo PNG, JPG veya WEBP olmalı (SVG kabul edilmez)." | Dosya biçimi uygun değil. | Logoyu PNG olarak kaydedip yeniden yükleyin. |

# Hızlı başvuru

| Yapmak istediğim | Menü / ekran | Gereken izin |
|---|---|---|
| Şirketin genel durumunu görmek | Genel › Genel Bakış | Şirket Geneli Pano |
| Logomuzu yüklemek | Genel › Şirket Profili | Şirket Ayarlarını Yönetme |
| Kurum bilgilerimizi değiştirmek | RECDx ile iletişim (Şirket Profili'nde yalnızca görüntülenir) | — |
| Yeni çalışan eklemek | Personel › Kullanıcı Yönetimi › **+ Yeni Kullanıcı Tanımla** | Kullanıcı Ekleme |
| Çalışanın rolünü veya iznini değiştirmek | Personel › Kullanıcı Yönetimi › **Düzenle** | Kullanıcı Düzenleme ve Silme |
| Ayrılan çalışanın girişini kapatmak | Personel › Kullanıcı Yönetimi › **Düzenle** › **Pasif** | Kullanıcı Düzenleme ve Silme |
| AI personel işe almak | Personel › AI Ajan İşe Alım › **+ Yeni AI Ajan İşe Al** | AI Personel İşe Alma |
| AI personele doküman öğretmek | Personel › AI Ajan İşe Alım › **📚 Kaynaklar** | AI Personel Ayarları ve Bilgi Kaynakları |
| AI personelin kademesini veya otonomisini değiştirmek | Personel › AI Ajan İşe Alım › **Düzenle** | AI Personel Ayarları ve Bilgi Kaynakları |
| AI personeli durdurmak | Personel › AI Ajan İşe Alım › **İşten Çıkar** | AI Personeli İşten Çıkarma |
| Departman eklemek | Organizasyon › Departmanlar › **Katalogdan Ekle** / **+ Yeni Departman Tanımla** | Departman Yönetimi |
| Ünvan ve rol promptu tanımlamak | Organizasyon › Ünvan Tanımları › **+ Yeni Ünvan Tanımla** | Ünvan Tanımlama |
| Bir ünvandaki bütün AI personele bilgi vermek | Organizasyon › Ünvan Tanımları › **Bilgi Dokümanları** | Ünvan Tanımlama |
| Sektörümüzü ve manifestomuzu yazmak | Kurum Zekâsı › Sektörel Manifesto | Sektörel Manifesto Yönetimi |
| Beyin AI kademesini seçmek | Kurum Zekâsı › Beyin AI | Şirket Ayarlarını Yönetme |
| Kurum hafızasına gelen bilgiyi onaylamak | Kurum Zekâsı › Beyin AI › **Kurum Hafızası Onay Kuyruğu** | Kurum Hafızasına Ekleme ve Onaylama |
| Odoo veya başka bir sistemi bağlamak | Kurum Zekâsı › Entegrasyonlar › **Bağlantı ekle** | Bağlantı Yönetimi |
| AI personele sistem araç yetkisi vermek | Kurum Zekâsı › Entegrasyonlar › **Araçlar ve yetkiler** | Bağlantı Yönetimi |
| İş çıktısının sisteme nasıl yazılacağını belirlemek | Kurum Zekâsı › Entegrasyonlar › **Eşlemeler** | Eşleme Stüdyosu |
| Büyük aktarımlara çift onay koymak | Kurum Zekâsı › Entegrasyonlar › **Aktarım onay kuralları** | Bağlantı Yönetimi |
| Bir aktarımı geri almak | Kurum Zekâsı › Entegrasyonlar › **Aktarım günlüğü** › **Geri al** | Bağlantı Yönetimi |
| Otomatik Case açan kural kurmak | Kurum Zekâsı › Otomasyonlar › **Yeni kural** | Otomasyon Kuralları |
| RECQmind destek biletlerini Case'e çevirmek | Kurum Zekâsı › Otomasyonlar › **RECQmind hazır kuralları** › **Hazır kuralları kur** | Otomasyon Kuralları |
| RECSlip.App v2 aylık masraf sürecini kurmak | Kurum Zekâsı › Otomasyonlar › **RECSlip.App v2 aylık süreç** › **Kur** | Otomasyon Kuralları ve Bağlantı Yönetimi |
| Kendi Odoo anahtarımı eklemek | Work Space › Bağlantılarım › **Şirket sistemlerindeki anahtarlarım** | Herkes |
| RECSlip onay kriterlerini değiştirmek | Work Space › Case › **RECSlip** sekmesi › **Ayarlar ve onay kriterleri** | Case yöneticisi veya Tüm Projeleri Yönetme |
| Kriter dışı RECSlip fişine karar vermek | Work Space › Onaylarım › **RECSlip masraf fişleri** | Fişin onaylayıcısı |
| Mevzuat paketini açmak | Kurum Zekâsı › Mevzuat Paketleri › **Aç** | Şirket Ayarlarını Yönetme |
| Kredi kullanımını görmek | Kullanım › Kredi ve Kullanım | Kredi ve Kullanımı Görme |
| Ek kredi almak | RECDx ile iletişim | — |
