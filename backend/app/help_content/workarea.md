**RECOrion — Work Area (Şirket Çalışma Ekranları) Kullanım Kılavuzu**

Sürüm: Kasım 2026 · Hazırlayan: RECDx Bilişim

# Bu kılavuz hakkında

## Kimin için?

Bu kılavuz, RECOrion'u kullanan müşteri şirketlerdeki şu kişiler içindir:

- **Proje yöneticisi:** Proje veya Case açar, RECAi ile planlar, ekibi kurar, işi başlatır ve kapatır.
- **Uzman kullanıcı (ekip üyesi):** Ekibinde olduğu projelerde AI personelle sohbet eder, kendisine verilen işi teslim eder.
- **Onaylayıcı:** Muhasebeci, departman müdürü, kalite sorumlusu gibi kararı veren kişi. İş adımı çıktılarını, AI personelin dış sistemde yapmak istediği işlemleri ve RECSlip masraf fişlerini onaylar veya reddeder.

Sistemi hiç görmemiş olmanız sorun değildir. Kılavuz, girişten önceki ekranlardan başlar ve Work Space'in (şirket çalışma alanı) her ekranını, her alanını ve her düğmesini sırayla anlatır.

Şirket ayarları (kullanıcılar, AI personel işe alma ayrıntıları, entegrasyonlar, otomasyonlar, kredi) bu kılavuzun konusu değildir; onlar **Şirket Yönetimi Kılavuzu**'nda anlatılır.

## Nasıl okunur?

- Baştan sona okumak zorunda değilsiniz. **Menü ağacı** bölümünden aradığınız ekranı bulun, ilgili bölüme gidin.
- Her ekranda aynı sıra izlenir: ekran ne işe yarar, kimler görür, ekranın bölümleri, alanlar tablosu, düğmeler tablosu, durumlar ve mesajlar, adım adım örnek, ipuçları ve sık sorulan sorular.
- Ekranda yazan etiketler ve düğme adları **kalın** yazılmıştır. Ekranda nasıl görüyorsanız öyledir.
- Örneklerde kurgusal bir şirket kullanılır: **Örnek Lojistik A.Ş.** Kişiler: **Ayşe Yılmaz** (şirket yöneticisi), **Mehmet Demir** (proje yöneticisi), **Zeynep Kaya** (muhasebeci), **Can Öztürk** (uzman).
- RECSlip masraf fişleriyle ilgili her şey ayrıca tek bir bölümde toplanmıştır: **"RECSlip fişleri: onaylayıcı olarak ne yaparım?"**

## Uyarı kutuları

> **İpucu:** İşinizi kolaylaştıran kısa yol veya öneri.

> **Dikkat:** Geri alınamayan işlem, veri kaybı veya sık yapılan hata.

> **Örnek:** Örnek Lojistik A.Ş. üzerinden somut kullanım.

## Rozet renkleri

Ekranlarda durumlar küçük renkli etiketlerle (rozet) gösterilir. Renklerin genel anlamı:

| Renk | Genel anlamı | Örnek rozetler |
|---|---|---|
| Yeşil | Tamam, etkin, başarılı | **Aktif**, **Tamamlandı**, **Onaylandı**, **Etkin**, **AI onayladı** |
| Sarı / turuncu | Dikkat, sizden bir şey bekleniyor | **Onay bekliyor**, **Başlamaya hazır**, **İnsan kararı bekliyor**, **14 gün kaldı** |
| Kırmızı | Sorun, durdu, reddedildi | **Karantinada**, **İptal edildi**, **Süresi doldu**, **Geçersiz**, **Hata** |
| Mavi | Bilgi, süren iş | **Planlama**, **Muhasebe onayı**, **Yönetici onayı** |
| Gri | Nötr, pasif, başlamamış | **Taslak**, **Duraklatıldı**, **İptal edildi** (anahtar), **Odoo'dan karar verildi** |

## Kavramlar sözlüğü

| Kavram | Anlamı |
|---|---|
| **Work Space** | Şirketinizin günlük çalışma alanı: projeler, onaylar, görev sohbeti, pano ve kişisel bağlantılar. Bu kılavuzda "Work Area" ile aynı anlamdadır. |
| **Proje** | Çok adımlı, takvimli iş (ör. yeni depo yönetim uygulaması). |
| **Case** | Tek bir konu veya vaka çözümü (ör. bir müşteri şikâyeti, aylık masraf süreci). Ekranda "Case" olarak görünür. |
| **İş adımı (görev)** | Projenin bir parçası (ör. "Veri modeli tasarımı"). Her adımı bir AI personel veya insan yürütür. Kısa kodu S1, S2… biçimindedir. |
| **AI personel** | Şirketinizde işe alınmış yapay zeka çalışanı. Bir unvanı (ör. İş Analisti) ve departmanı vardır; adımları yürütür, sohbette yanıt verir. |
| **RECAi** | RECOrion'un yapay zekası. AI personel RECAi ile düşünür ve yazar. RECAi'nin farklı güçte kademeleri vardır (ör. **RECAi Mergen**, **RECAi Hızlı**, **RECAi Derin**). |
| **Beyin AI** | RECAi'nin planlama işlevi. İsterlerinizden iş adımlarını, sürelerini ve gereken personeli önerir. Ekranda "Beyin AI" adıyla görünür. |
| **İsterler** | Projeden ne beklediğinizin yazılı hâli: hedef, kapsam, kısıtlar, teslim ölçütleri. Beyin AI planı buradan çıkarır. |
| **Proje ekleri** | Projeye yüklenen şartname, örnek, görsel gibi dosyalar. Onaylananları yalnız o projedeki AI personel öğrenir. |
| **Onay / onaylayıcı** | Bir adımın çıktısını kabul etme kararı ve bu kararı veren kişi. Onaylayıcı ayrıca seçilmemişse karar proje yöneticisinindir. |
| **Revizyon** | Onaylayıcının "düzelt" demesi. Gerekçe AI personele gider, AI düzeltip yeniden teslim eder. |
| **Ret sınırı / karantina** | Bir adım belirli sayıda (varsayılan 3) revizyona düşerse veya personel çalışamazsa "karantinaya" alınır ve proje yöneticisinin kararını bekler. |
| **Kontrol personeli** | Çıktıyı onaya gitmeden önce değerlendiren ikinci AI personel. İsteğe bağlıdır. |
| **Kalite kapısı** | Çalışma Alanı'nın sağ bölmesinde adımın onay durumunu ve karar düğmelerini gösteren kart. |
| **Kurum hafızası** | Şirketin tüm AI personelinin yararlandığı onaylı bilgi. Bilgi buraya ancak yetkili kişi onaylayınca girer. |
| **Kredi** | RECAi kullanımının ölçüsü. Paketinizle her ay belirli miktarda kredi gelir. |
| **Aktarım** | Bir adım çıktısından çıkarılan kaydın şirket sistemine (ör. Odoo) yazılması. Hiçbir kayıt onaysız yazılmaz. |
| **Araç işlemi** | AI personelin bir dış sistemde (ör. Odoo) yapmak istediği yazma işlemi. Onay gerektiren işlemler Onaylarım'a düşer. |
| **RECSlip.App v2** | RECDx'in Odoo üzerinde çalışan masraf fişi uygulaması. Çalışanlar fişi yükler, RECSlip okur ve onaya gönderir. |
| **RECSlip Case'i** | RECSlip kurulu şirkette her ay kendiliğinden açılan "RECSlip masraf süreci <dönem>" Case'i. |
| **Kişisel anahtar** | Bu kılavuzda iki türü vardır: (1) Claude, Cursor gibi araçların RECOrion'a bağlanması için **kişisel erişim anahtarı**; (2) AI personelinizin sizin adınıza şirket sisteminde (Odoo) işlem yapabilmesi için kendi Odoo kullanıcınızın **API anahtarı**. |
| **KVKK** | Kişisel Verilerin Korunması Kanunu. RECOrion kişisel verileri maskeleyerek işler; RECDx yöneticileri bile şirketinizin projelerini, sohbetlerini, hafızasını ve bağlantılarını göremez. |

## Roller: kim neyi görür?

RECOrion'da ne görebileceğiniz, size verilen **role** ve **izinlere** bağlıdır. Rolleri şirket yöneticiniz Şirket Yönetimi › Kullanıcı Yönetimi'nden verir. Work Space için önemli olanlar:

| Rol | Girişten sonra açılan ekran | Work Space'te neler yapabilir |
|---|---|---|
| **Şirket Yöneticisi** | Şirket Yönetimi konsolu (Work Space'e konsoldaki geçiş düğmesiyle gelinir) | Her şey: proje açma, şirketin tüm projelerini görme ve yönetme, vekâleten onay/revizyon, kurum hafızası kararları, Pano. |
| **Proje Yöneticisi** | Work Space › Projeler | Proje/Case açma, tüm projeleri yönetme, AI personel işe alma, şablon kaydetme, vekâleten onay/revizyon, kurum hafızası kararları, kendi departmanının panosu. |
| **Uzman Kullanıcı** | Work Space › Projeler | Yalnız ekibinde olduğu projeleri görür. Sohbete yazar, dosya ekler, kendisine atanan adımı teslim eder, onaylayıcısı olduğu adıma karar verir, kurum hafızasında arar, kişisel anahtar oluşturur. Proje açamaz. |
| Diğer roller (ör. **Kalite ve Onay Sorumlusu**, **Finans ve Raporlama Sorumlusu**, **Entegrasyon Yöneticisi**, **Operasyon Yöneticisi**) | Rolün izinlerine göre | Örneğin Kalite ve Onay Sorumlusu, onaylayıcısı olmasa da erişebildiği projelerde adım onaylayabilir; Finans ve Raporlama Sorumlusu panoda parasal bilgileri görür. |

Ayrıca bir projenin **Proje yöneticisi** alanına atanan herkes, rolü ne olursa olsun, o projede yönetici işlemlerini (planlama, ekip, başlatma, maliyet, kapanış, karantina kararı) yapar.

Work Space için önemli izinlerin ekrandaki adları: **Proje / Case Açma**, **Tüm Projeleri Yönetme**, **Şirket Şablonlarını Yönetme**, **İş Adımı Ekleme**, **İş Adımı Onaylama (Vekâleten)**, **Revizyon İsteme (Vekâleten)**, **Sohbet ve Görev İletişimi**, **Kurum Hafızasında Arama**, **Kurum Hafızasına Ekleme ve Onaylama**, **Kurum Hafızasından Geri Alma**, **Departman Panosu**, **Şirket Geneli Pano**, **Maliyet ve Bütçe Bilgilerini Görme**, **Kişisel Erişim Anahtarı**.

> **Dikkat:** Ekranda bir düğmeyi görmüyorsanız büyük olasılıkla o işlem için izniniz yoktur. Şirket yöneticinizden izin isteyin.

# Genel düzen

## Giriş ve ilk açılış

1. Tarayıcıda RECOrion adresini açın. **Resmi site** gelir.
2. Sağ üstte **🔑 Giriş Yap** düğmesine basın, e-posta ve şifrenizi yazın.
3. Rolünüze göre şu ekran açılır: Şirket Yöneticisi için **Şirket Yönetimi** konsolu; diğer roller için **Work Space › Projeler**.

Oturum süresi: **Beni Hatırla** işaretliyse 30 gün, değilse 12 saattir. Süre dolunca **"Oturumunuzun süresi doldu. Lütfen tekrar giriş yapın."** uyarısı çıkar ve resmi siteye dönülür.

## Work Space'in yerleşimi

Work Space'te Şirket Yönetimi'ndeki gibi bir sol menü yoktur. Ekran yukarıdan aşağı üç parçadan oluşur:

1. **Üst çubuk:** RECOrion markası, şirketiniz (logosuyla), sistem sağlık noktaları, tema düğmesi, panel geçişleri, kullanıcı kartı, **Çıkış**.
2. **Mod çubuğu:** Work Space'in beş ana bölümü arasında geçiş yapan düğmeler: **Projeler**, **Onaylarım**, **Çalışma Alanı**, **Pano** (yetkiliyse), **Bağlantılarım**.
3. **İçerik alanı:** Seçtiğiniz modun ekranı.

Ayrıntılar için Work Space bölümündeki **Üst çubuk ve mod çubuğu** başlığına bakın.

## Tema

Üst çubuktaki tema düğmesi **Koyu**, **Açık** ve **Sistem** (bilgisayarınızın ayarını izler) arasında döner. Seçiminiz bu tarayıcıda hatırlanır.

## Telefonda ve tablette

- Üst çubuktaki sistem sağlık noktaları yalnız geniş ekranlarda görünür; kullanıcı kartı dar ekranlarda baş harfe iner, telefonda gizlenir.
- Çalışma Alanı'ndaki üç bölme aynı anda sığmaz. Üstte bir bölme seçici çıkar: **Proje & Görevler**, **Sohbet**, **Çıktı & Hafıza**. Bunlara dokunarak bölmeler arasında geçersiniz.
- Tablolar telefonda kart görünümüne geçer; her satırın başlığı solda yazar.

## Bildirimler ve onay pencereleri

- **Kısa bildirimler:** Bir işlem başarılı olunca ekranın köşesinde yeşil, uyarı gerektiğinde sarı, hata olduğunda kırmızı kısa bir mesaj belirir ve birkaç saniye sonra kaybolur. Örnek: **"Proje bilgileri kaydedildi."**
- **Onay pencereleri:** Geri alınamayan veya önemli işlemlerden önce bir soru penceresi açılır (ör. **"Proje iptal edilsin mi? Bu işlem geri alınamaz."**). **Tamam**/onay düğmesiyle işlem yapılır, **Vazgeç** ile hiçbir şey değişmez. Tehlikeli işlemlerde onay düğmesi kırmızıdır.
- **Not/gerekçe pencereleri:** Revizyon, ret veya teslimde bir metin kutusu açılır. Kutuya yazıp onaylarsınız. Gerekçenin zorunlu olduğu yerde boş bırakırsanız işlem yapılmaz.
- **E-posta ve Telegram:** Onay istekleri, revizyonlar, duran adımlar, proje bitişi ve RECSlip kararları için size e-posta ve (bağladıysanız) Telegram mesajı gelir. Hangi kanaldan alacağınızı proje ekranının **Hazırlık & Bildirim** sekmesinde seçersiniz.

## Doğrudan bağlantılar

E-posta ve Telegram bildirimlerindeki bağlantılar ilgili projenin ekranını veya Çalışma Alanını doğrudan açar. Oturumunuz yoksa önce resmi siteye yönlendirilirsiniz; giriş yapıp bağlantıyı yeniden açın. Çalışma Alanındayken adres çubuğundaki adres de paylaşılabilir: ekip arkadaşınız açınca aynı projenin Çalışma Alanı gelir.

Ekibinde olmadığınız bir projenin bağlantısını açarsanız **"Bağlantıdaki projeyi göremiyorsunuz (ekibinde değilsiniz veya proje kaldırıldı)."** uyarısı çıkar.

## KVKK koruması

RECDx yöneticileri, destek amacıyla şirketinizin Work Space'ine geçse bile projelerinizi, görevlerinizi, sohbetlerinizi, kurum hafızanızı ve kişisel anahtarlarınızı göremez. Bu durumda ekranın üstünde sarı bir **"KVKK Koruma Modu"** şeridi görünür ve mod düğmeleri kapalıdır. Siz bu şeridi normalde görmezsiniz.

## Yardım ve RECAi'ye sor

**Bu ne işe yarar?** Bu kılavuzun tamamı RECOrion'un içinde de vardır. Bir ekranda takıldığınızda kılavuzu aramanıza gerek kalmaz: **F1** tuşuna basın veya üst çubuktaki **Yardım** düğmesine tıklayın. Sağdan bir yardım paneli açılır; çalıştığınız ekran kapanmaz.

**Kimler görür?** Giriş yapmış herkes. Panelde yalnız sizin yetkiniz dahilindeki ekranların anlatımı görünür. Şirket Yönetimi sayfaları yalnız o menüleri görebilen kullanıcılara görünür; RECDx'in Merkez Yönetim sayfaları müşteri kullanıcılarına hiç görünmez.

**Panelin sekmeleri:**

| Sekme | Ne işe yarar |
|---|---|
| **RECAi'ye sor** | Sorunuzu kendi cümlenizle yazarsınız; RECAi kılavuzdan, adım adım yanıt verir. Yanıtın altında dayandığı yardım sayfaları ve gerekiyorsa **Ekrana git** düğmesi çıkar. Aynı konuda ek soru sorabilirsiniz; RECAi önceki soruları hatırlar. |
| **Bu ekran** | Bulunduğunuz ekranın anlatımını açar. Bir pencere açıkken F1'e basarsanız o pencerenin bölümüne gider. **Bu ekranı aç** düğmesi anlatılan ekrana götürür. |
| **İçindekiler** | Görebildiğiniz kılavuzların bölüm ve sayfa listesi. Bir sayfaya tıklayınca açılır; sayfadaki görselleri büyütmek için üzerine tıklayın. |

[[EKRAN: wa-yardim-icindekiler | Work Space'te açılmış Yardım paneli, İçindekiler sekmesi: kullanıcının görebildiği kılavuzlar ve sayfa listesi | Work Space'te F1'e basın veya üst çubuktaki Yardım simgesine tıklayın; panelde İçindekiler sekmesini seçin]]

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

> **Örnek:** Can Öztürk **Onaylarım** ekranında bir RECSlip fişi görür ve F1'e basar; panel Onaylarım ekranının anlatımını açar. "Önerilen hesap düzeltmesini nasıl uygularım?" diye sorar; RECAi **Onaylarken düzeltmeleri uygula** kutusunu ve **Onayla** düğmesini anlatır. Can sonra "Kayıtlı şirketleri nasıl pasife alırım?" diye sorar; bu RECDx'in yönetim ekranı olduğu için RECAi "cevap veremiyorum" der.

> **İpucu:** RECAi yardım soruları kılavuz bilgisiyle yanıtlanır; projelerinizin, fişlerinizin veya kullanıcılarınızın verisini okumaz. "Kaç projem var?" gibi veri soruları için ilgili ekranı açın.

# Menü ağacı

Aşağıdaki harita, girişten önceki ekranları ve Work Space'in tamamını tek bakışta gösterir. Parantez içinde kimlerin gördüğü yazılıdır.

| Bölüm | Menü / mod | Ekran ve pencereler | Kimler görür |
|---|---|---|---|
| Giriş öncesi | Resmi site | Tanıtım, paket kartları | Herkes |
| Giriş öncesi | Paket kiralama başvurusu | Adım 1 Kurumsal Bilgiler (logo dahil) · Adım 2 Sektör & Meslek Grupları · Adım 3 Yönetici & Güvenlik · Adım 4 Onay & AI Manifesto | Herkes |
| Giriş öncesi | Giriş | Giriş penceresi · Şifremi Unuttum penceresi | Herkes |
| Giriş öncesi | E-postadaki bağlantılar | Şifre belirleme sayfası · Onay bağlantısı sayfası | Bağlantıyı alan kişi |
| Work Space | Üst çubuk | Kurum (logo), Resmi Web & Paketler, Şirket Yönetimi, kullanıcı kartı, Çıkış | Herkes (Şirket Yönetimi düğmesi yalnız yönetim izni olanlarda) |
| Work Space | **Projeler** | Projeler ve Case'ler listesi · Yeni Proje / Case · Şablondan proje oluştur · Toplantıdan proje oluştur | Herkes (oluşturma düğmeleri yalnız **Proje / Case Açma** izni olanlarda) |
| Work Space | Projeler › Proje ekranı | Bilgiler & İsterler · Proje Ekleri · Beyin AI Planlama · Ekip & Simülasyon · Hazırlık & Bildirim · İş Akışı · Maliyet · Kod Deposu · Testler · RECSlip · Kapanış · Şablon olarak kaydet | Projenin ekibi; **Maliyet** yalnız proje yöneticisi ve **Tüm Projeleri Yönetme** izni olanlar; **RECSlip** yalnız RECSlip Case'lerinde |
| Work Space | **Onaylarım** | RECSlip masraf fişleri · Dış sisteme aktarımlar · Araç işlemleri (yazma) · İş adımı onayları ve karantinadakiler | Herkes (yalnız kendi kararını bekleyenler) |
| Work Space | **Çalışma Alanı** | Sol: Proje & Görevler · Orta: Sohbet · Sağ: Kalite Kapısı & Kurum Hafızası · Yeni İş Akışı Görevi Oluştur | Herkes (yalnız ekibinde olduğu projeler) |
| Work Space | **Pano** | Şirket veya departman göstergeleri | **Şirket Geneli Pano** veya **Departman Panosu** izni olanlar |
| Work Space | **Bağlantılarım** | Kişisel erişim anahtarları · Şirket sistemlerindeki anahtarlarım | Herkes |

# Giriş öncesi ekranlar

## Resmi site

[[EKRAN: wa-resmi-site | RECOrion resmi sitesinin üst kısmı: başlık, tanıtım metni, dört sayaç kartı ve paket kartları | Oturum açmadan RECOrion adresini açın; oturum açıksa Work Space'te üst çubuktaki "🌐 Resmi Web & Paketler" düğmesine basın]]

**Bu ekran ne işe yarar?** RECOrion'u tanıtır ve abonelik paketlerini listeler. Şirketinizin başvurusu ve girişiniz buradan yapılır.

**Ne zaman kullanırım?** Şirketiniz RECOrion'a ilk kez abone olacaksa; giriş yapacaksanız; oturumunuz açıkken paketleri incelemek istiyorsanız.

**Kimler görür?** Herkes. Giriş gerekmez.

**Ekranın bölümleri (yukarıdan aşağı):**

1. **Üst başlık:** solda yazılı RECOrion logosu, sağda tema düğmesi ve giriş/oturum düğmeleri.
2. **Tanıtım:** "🚀 Yeni Nesil Kurumsal Otonom Ekosistem" rozeti, "Yapay Zeka Personellerinizle Şirketinizi Otonom Yönetin" başlığı ve kısa açıklama.
3. **Sayaç kartları:** Yerli yapay zeka modeli sayısı, **Resmi Faaliyet Sektörü** sayısı, **Meslek Grubu (T.C. Ticaret Bakanlığı)** sayısı ve **%100 Dark DB Veri Yalıtımı** (verilerinizin diğer şirketlerden tamamen ayrı tutulduğu).
4. **Abonelik & Kiralama Paketleri:** "Şirketinizin ölçeğine ve hedeflerine en uygun yapay zeka operasyon gücünü seçin." Her paket bir karttır.

**Paket kartında neler yazar?**

| Bilgi | Anlamı |
|---|---|
| Paket adı ve açıklaması | Paketin kime uygun olduğu. |
| **<fiyat> ₺ / Ay** | Aylık ücret. |
| **⭐ En Çok Tercih Edilen** | En çok seçilen paket rozeti. |
| **<n> AI Ajan Personeli** | İşe alabileceğiniz en fazla AI personel sayısı. |
| **<n> İnsan Kullanıcı** | Tanımlayabileceğiniz en fazla insan kullanıcı sayısı. |
| **<n> Eşzamanlı Proje** | Aynı anda açık tutabileceğiniz proje/Case sayısı. Tamamlanan ve iptal edilenler sayılmaz. |
| **<n> İşlem Kredisi** | Her ay gelen RECAi kullanım kredisi. |
| **<n> GB MinIO Yalıtımlı Depolama** | Dosyalarınız için ayrılan, diğer şirketlerden yalıtılmış depolama alanı. |
| **Otomatik Kurumsal AI Manifestosu** | Başvuruda seçtiğiniz sektör ve mesleklere göre RECAi'nin şirketiniz için yazdığı tanıtım ve yetenek metni. |
| **RECAi (<n>):** | Pakette kullanılabilen RECAi kademeleri (ör. RECAi Mergen, RECAi Hızlı, RECAi Derin) ve varsa ek yetenekler (ör. RECAi Görsel, RECAi Ses, RECAi Okur). |

**Düğmeler:**

| Düğme | Ne yapar | Dikkat |
|---|---|---|
| Tema düğmesi | Koyu, Açık ve Sistem görünümü arasında geçer. | — |
| **🔑 Giriş Yap** (oturum yoksa) | Giriş penceresini açar. | — |
| **💻 Çalışma Alanına Git →** veya **🏢 Şirket Yönetim Paneli →** (oturum varsa) | Rolünüze göre panelinize döner. | Oturum açık kalır. |
| **Çıkış Yap** (oturum varsa) | Oturumu kapatır. | Onay istemez. |
| **🚀 Bu Paketi Kirala / Satın Al** | O paket için kiralama başvurusu penceresini açar. | Bkz. sonraki bölüm. |

**Durumlar:** Paketler yüklenirken **"Paket bilgileri getiriliyor..."** yazar.

## Paket kiralama başvurusu

[[EKRAN: wa-basvuru-adim1 | "<Paket> Kiralama Başvurusu" penceresi, Adım 1: Kurumsal Bilgiler formu ve isteğe bağlı Şirket Logosu alanı | Resmi sitede bir paket kartındaki "🚀 Bu Paketi Kirala / Satın Al" düğmesine basın]]

**Bu ekran ne işe yarar?** Şirketinizin RECOrion aboneliğine başvurmasını sağlar. Şirket bilgileri, faaliyet sektörleri, meslek grupları ve ilk yönetici hesabı alınır; e-posta adresi doğrulanır. RECDx başvurunuzu onaylayınca hesabınız etkinleşir.

**Ne zaman kullanırım?** Şirketiniz için ilk kez abonelik açarken. Bir kez yapılır.

**Kimler görür?** Herkes. Başvuruyu genellikle şirket yöneticisi olacak kişi yapar.

**Pencerenin bölümleri:**

- **Başlık:** "<Paket adı> Kiralama Başvurusu", **Kurumsal Bulut Paket** rozeti ve aylık fiyat. Sağda kapatma düğmesi (klavyede **ESC** de kapatır).
- **Adım çubuğu:** **1. Kurumsal Bilgiler**, **2. Sektör & Meslek Grupları**, **3. Yönetici & Güvenlik**, **4. Onay & AI Manifesto**. Tamamlanan adımlara tıklayarak geri dönebilirsiniz. İleri gitmek için önceki adımın zorunlu bilgileri gerekir (Adım 2 için şirket ünvanı, Adım 3 için en az bir sektör).
- **Hata kutusu:** Bir sorun olduğunda formun üstünde kırmızı kutuda yazar.

> **Dikkat:** Pencereyi kapatma düğmesiyle, **Vazgeç / İptal** ile veya ESC tuşuyla kapatırsanız girdiğiniz tüm bilgiler silinir.

### Adım 1 — Kurumsal Bilgiler

İki bölümden oluşur: **Kurumsal Kimlik ve Vergi Bilgileri** ve **İletişim ve Resmi Adres**.

| Alan | Ne işe yarar | Nasıl doldurulur / seçenekler | Örnek | Zorunlu |
|---|---|---|---|---|
| **Şirket Ünvanı** | Şirketinizin resmi adı; sistemde her yerde bu ad görünür. | Ticaret sicilindeki ünvanı yazın. | Örnek Lojistik A.Ş. | Evet |
| **Vergi Kimlik No (VKN / TCKN)** | Şirketin tekil kimliği; aynı numarayla ikinci başvuru yapılamaz. | 10 haneli VKN veya 11 haneli TCKN. Kontrol hanesi denetlenir; ardışık veya tekrar eden rakamlar kabul edilmez. | 1234567890 | Evet |
| **Vergi Dairesi** | Fatura ve resmi kayıtlar için. | Serbest metin. | Kadıköy V.D. | Hayır |
| **Kurumsal İletişim E-Posta** | Şirketle iletişim adresi. Adım 3'teki giriş e-postasıyla aynı alandır; birini değiştirince diğeri de değişir. | Şirket alan adlı adres olmalı. Gmail, Hotmail, Outlook, Yahoo, Yandex, iCloud gibi ücretsiz adresler kabul edilmez. | ayse.yilmaz@orneklojistik.com.tr | Evet |
| **Telefon Numarası** | Şirketin iletişim telefonu. | Ülke koduyla yazabilirsiniz. | +90 216 000 00 00 | Evet |
| **Web Sitesi** | Şirketin web adresi. | https:// ile başlayan tam adres. | https://orneklojistik.com.tr | Hayır |
| **Şirket Logosu (isteğe bağlı)** | Şirketinizin resmi logosu. Work Space üst çubuğunda (Kurum alanında) ve Şirket Yönetimi'nin sol üstünde görünür. | **Logo seç** ile dosya seçin; önizleme çıkar. Değiştirmek için **Logoyu değiştir**, vazgeçmek için **Kaldır**. PNG, JPG veya WEBP · en fazla 2 MB · kare ya da yatay; saydam arka planlı PNG önerilir. SVG kabul edilmez. Sistem logoyu en uzun kenarı 512 piksel olacak şekilde küçültür. | orneklojistik-logo.png | Hayır |
| **Şirket Resmi Adresi** | Genel merkez adresi. | Çok satırlı metin. | Atatürk Cad. No:1 Kadıköy/İstanbul | Hayır |

**Düğmeler:**

| Düğme | Ne yapar | Dikkat |
|---|---|---|
| **Logo seç** / **Logoyu değiştir** | Bilgisayarınızdan logo dosyası seçtirir. | Uygun olmayan dosyada uyarı çıkar, logo eklenmez. |
| **Kaldır** (logo) | Seçilen logoyu formdan çıkarır. | Başvuru gönderilmeden önce istediğiniz kadar değiştirebilirsiniz. |
| **Vazgeç / İptal** | Pencereyi kapatır. | Girilen bilgiler silinir. |
| **Devam Et: Sektör & Meslek Grupları** | Adım 2'ye geçer. | Ünvan ve telefon boşsa ilerlemez. |

**Hata mesajları ve anlamları:**

| Mesaj | Ne demek, ne yapmalı |
|---|---|
| **"Lütfen şirket ünvanını giriniz."** | Ünvan boş. Doldurun. |
| **"Lütfen iletişim telefon numarasını giriniz."** | Telefon boş. Doldurun. |
| **"Logo PNG, JPG veya WEBP olmalı (SVG kabul edilmez)."** | Dosya türü uygun değil. Logonuzu PNG olarak kaydedip yeniden seçin. |
| **"Logo en fazla 2 MB olabilir."** | Dosya çok büyük. Daha küçük bir sürüm seçin. |
| **"Logo çok küçük (en az 16×16 piksel)."** veya **"Logo görseli okunamadı."** | Dosya bozuk ya da çok küçük. Başka bir dosya deneyin. |

> **İpucu:** Logonuz hazır değilse boş bırakın. Hesabınız açıldıktan sonra Şirket Yönetimi › Şirket Profili'nden istediğiniz zaman ekleyebilirsiniz.

### Adım 2 — Sektör & Meslek Grupları

[[EKRAN: wa-basvuru-adim2 | Adım 2: üstte faaliyet sektörü düğmeleri ve arama kutusu, altta seçili sektörlere göre süzülmüş meslek grupları | Başvuru penceresinde Adım 1'i doldurup "Devam Et: Sektör & Meslek Grupları" düğmesine basın]]

Bu adımda şirketinizin ne iş yaptığını seçersiniz. RECAi, kurumsal manifestonuzu, AI personel önerilerini ve yetenekleri bu seçime göre hazırlar. Liste T.C. Ticaret Bakanlığı'nın resmi sektör ve meslek grubu yapısıdır.

Bölümler: **1. Faaliyet Sektörleri (T.C. Ticaret Bakanlığı)** (sağında "Seçilen Sektör: n") ve **2. Meslek Grupları (Seçili Sektörlere Göre Filtrelenmiş)** (sağında "Seçilen Meslek: n").

| Alan | Ne işe yarar | Nasıl doldurulur / seçenekler | Örnek | Zorunlu |
|---|---|---|---|---|
| **Sektör ara** kutusu | Uzun sektör listesini daraltır. | Sektör adı, kodu veya o sektördeki bir meslek adı yazın. Türkçe büyük/küçük harf fark etmez. | nakliye | Hayır |
| Sektör düğmeleri **[kod] ad** | Şirketin faaliyet sektörleri. | Düğmeye basınca seçilir (✓), yeniden basınca kalkar (+). Birden çok seçilebilir. Bir sektörü kaldırırsanız ona bağlı seçili meslekler de kalkar. | [H] Ulaştırma ve Depolama | En az 1 |
| **Meslek grubu ara** kutusu | Tüm meslek gruplarında arar. | Yazdığınız metne uyan meslekler listelenir. Seçtiğiniz grubun sektörü otomatik eklenir. | depo | Hayır |
| Meslek düğmeleri | Şirketinizdeki meslek alanları. | Sektör seçince o sektörün meslekleri listelenir; uygun olanları işaretleyin. | Depolama hizmetleri | Hayır |

Sektör seçmeden meslek listesi yerine şu yazı görünür: **"Lütfen önce yukarıdan en az bir Faaliyet Sektörü seçiniz. İlgili resmi meslek grupları burada listelenecektir."**

| Düğme | Ne yapar | Dikkat |
|---|---|---|
| **← Geri: Şirket Bilgileri** | Adım 1'e döner. | Bilgiler korunur. |
| **Devam Et: Yetkili Hesap & Şifre** | Adım 3'e geçer. | Sektör seçilmemişse **"Lütfen en az bir faaliyet sektörü seçiniz."** uyarısı çıkar. |

### Adım 3 — Yönetici & Güvenlik

[[EKRAN: wa-basvuru-adim3 | Adım 3: solda yetkili yönetici, doğrulama kodu ve şifre alanları; sağda seçilen paket özeti; altta Odoo ve RECDx uygulamaları seçimi | Başvuru penceresinde Adım 2'de en az bir sektör seçip "Devam Et: Yetkili Hesap & Şifre" düğmesine basın]]

Bu adımda şirketinizin ilk **Şirket Yöneticisi** hesabını oluşturursunuz.

Bölümler: solda **Yetkili Yönetici ve Hesap Bilgileri**; sağda **SEÇİLEN KURUMSAL PAKET** özeti (paket adı, fiyat "/ Ay", AI ve insan kullanıcı sayısı, depolama, seçtiğiniz sektör ve meslek sayısı); altta isteğe bağlı **Odoo ve RECDx uygulamaları** bölümü.

| Alan | Ne işe yarar | Nasıl doldurulur / seçenekler | Örnek | Zorunlu |
|---|---|---|---|---|
| **Yetkili Adı Soyadı** | Şirket yöneticisi hesabının sahibi. | Ad ve soyad. | Ayşe Yılmaz | Evet |
| **Giriş E-Posta Adresi (Yönetim Paneli Girişi)** | Giriş yaparken kullanacağınız kullanıcı adı. Adım 1'deki kurumsal e-postayla aynı alandır. | Kurumsal alan adlı adres. | ayse.yilmaz@orneklojistik.com.tr | Evet |
| **E-Posta Doğrulama Kodu** | E-posta adresinin size ait olduğunu kanıtlar. | **Kod Gönder**'e basın, e-postanıza gelen 6 haneli kodu yazın. Kod 10 dakika geçerlidir. Altta "Kod <adres> adresine gönderildi; 10 dakika geçerlidir." yazar. | 482913 | Evet |
| **Giriş Şifresi** | Hesabınızın şifresi. | En az 8 karakter. Göz simgesiyle gösterir/gizler, kopyala simgesiyle panoya kopyalar. | — | Evet |
| **Farklı Bir Paket Seçmek İster misiniz?** | Başvurduğunuz paketi değiştirir. | Açılır listeden başka paket seçin (birden fazla paket varsa görünür). | — | Hayır |
| **Şirketinizde Odoo kullanıyor musunuz?** | RECDx'in Odoo uygulamaları için seçenekleri belirler. | **Evet** / **Hayır**. "RECDx'in Odoo uygulamaları (Odoo Enterprise, Odoo.sh veya kendi sunucunuz) RECOrion ile birlikte çalışır." | Evet | Hayır |
| Her RECDx uygulaması için seçim | O uygulamayı isteyip istemediğiniz. | **Zaten kullanıyorum (yalnızca entegrasyon)** (Odoo varsa), **Paketime ekle** (Odoo varsa ve pakette sunuluyorsa), **Teklif istiyorum**, **Hayır**. Kartta paketle ilişki rozeti çıkar: **Paketinize dahil**, **Paketinizde %n indirimli…** veya **Bu pakette yok; teklif isteyebilirsiniz**. **Ayrıntı** bağlantısı uygulamanın tanıtımını açar. | RECSlip.App: Teklif istiyorum | Hayır |

**Düğmeler:**

| Düğme | Ne yapar | Dikkat |
|---|---|---|
| **Kod Gönder** / **Kodu Tekrar Gönder** | E-postanıza doğrulama kodu gönderir. | Gönderimden sonra 60 saniye bekletir ("Tekrar (n sn)"). Gönderilirken "Gönderiliyor…". |
| **✨ Güçlü Şifre Oluştur** | 14 karakterli rastgele şifre üretir ve panoya kopyalar. | Şifreyi güvenli bir yere kaydedin. |
| **← Geri: Sektör & Meslek Seçimi** | Adım 2'ye döner. | — |
| **KAYIT TAMAMLA** | Başvuruyu gönderir ("Kayıt Tamamlanıyor..."). | Başarılıysa Adım 4 açılır. |

Bilgi notu: **"📌 Başvurunuz RECDx ekibi tarafından incelendikten sonra hesabınız aktifleştirilecek ve <e-posta> aktivasyon e-postası gönderilecektir."**

**Hata mesajları:**

| Mesaj | Ne demek, ne yapmalı |
|---|---|
| **"Lütfen önce kurumsal e-posta adresinizi yazın."** | Kod istemeden önce e-postayı yazın. |
| **"⚠️ Kurumsal / Official E-Posta Zorunluluğu: …"** | Ücretsiz bir e-posta adresi yazdınız. Şirket alan adlı adresinizi kullanın. |
| **"Giriş şifresi en az 8 karakter olmalıdır."** | Şifreyi uzatın. |
| **"Lütfen e-posta adresinize gönderilen 6 haneli doğrulama kodunu girin."** | Kod eksik. |
| **"E-posta doğrulama kodu hatalı veya süresi dolmuş. Lütfen yeni kod isteyin."** | Kod yanlış ya da 10 dakika geçti. **Kodu Tekrar Gönder**'e basın. |
| **"Çok fazla doğrulama kodu istendi. Lütfen daha sonra tekrar deneyin."** | Kısa sürede çok kod istendi. Biraz bekleyin. |
| **"Vergi numarası 10 haneli VKN veya 11 haneli TCKN olmalıdır."** / **"Vergi numarası geçersiz (kontrol hanesi tutmuyor)…"** | Vergi numarasını kontrol edin (Adım 1). |
| **"'<VKN>' Vergi Numarası ile kayıtlı bir şirket (…) zaten mevcuttur. Mükerrer kayıt oluşturulamaz."** | Şirketiniz daha önce başvurmuş. RECDx ile iletişime geçin. |
| **"'<e-posta>' e-posta adresi ile kayıtlı bir kullanıcı… zaten mevcuttur…"** | Bu e-postayla hesap var. Başka adres kullanın veya giriş yapın. |

### Adım 4 — Onay & AI Manifesto

[[EKRAN: wa-basvuru-adim4 | Adım 4: "Kiralama Talebiniz Başarıyla Alındı!" başlığı, bildirim kutuları, RECAi'nin ürettiği kurumsal manifesto ve atanan yetenek etiketleri | Başvuru penceresinde Adım 3'ü doldurup "KAYIT TAMAMLA" düğmesine basın]]

Başvuru alınınca bu ekran açılır:

- **"Kiralama Talebiniz Başarıyla Alındı!"** ve "'<şirket>' kurumu için sipariş kaydı oluşturuldu ve şirket ortamınız hazırlandı."
- Bildirim kutuları: RECDx'e bildirim gittiği ve e-posta adresinize karşılama iletildiği.
- **RECAi Tarafından Üretilen Kurumsal Manifesto:** Seçtiğiniz sektör ve mesleklere göre şirketinizin tanıtım ve çalışma ilkeleri metni. Yanında **"<n> Yetenek Atandı"** rozeti ve altta "✦" ile başlayan yetenek etiketleri.

| Düğme | Ne yapar | Dikkat |
|---|---|---|
| **🔑 Yönetim Paneline / Giriş Ekranına Git →** | Başvuru penceresini kapatıp giriş penceresini açar. | Başvurunuz onaylanmadan giriş yapamazsınız. |

> **Örnek:** Ayşe Yılmaz, Örnek Lojistik A.Ş. için "Kurumsal" paketin kartında **🚀 Bu Paketi Kirala / Satın Al**'a basar. Adım 1'de ünvan, VKN, kurumsal e-posta ve telefonu yazar, şirket logosunu (PNG, 300 KB) seçer. Adım 2'de "nakliye" araması yapıp Ulaştırma ve Depolama sektörünü ve depolama meslek gruplarını işaretler. Adım 3'te adını yazar, **Kod Gönder** ile gelen kodu girer, **✨ Güçlü Şifre Oluştur**'a basıp şifreyi şifre yöneticisine kaydeder. Odoo kullandıkları için **Evet**'i, RECSlip.App için **Teklif istiyorum**'u seçer ve **KAYIT TAMAMLA**'ya basar. RECDx onayından sonra gelen aktivasyon e-postasıyla giriş yapar.

**Sık sorulan sorular**

- **Başvurudan hemen sonra giriş yapabilir miyim?** Hayır. RECDx başvurunuzu inceleyip onaylayınca hesabınız etkinleşir ve e-posta alırsınız. Önce denerseniz **"'<şirket>' için satın alma başvurunuz henüz Süper Yönetici tarafından onaylanmamıştır…"** uyarısı çıkar.
- **Logoyu yanlış yükledim, değiştirebilir miyim?** Evet. Giriş yaptıktan sonra Şirket Yönetimi › Genel › Şirket Profili'nden değiştirir veya kaldırırsınız.
- **Sektörü sonradan değiştirebilir miyim?** Evet, Şirket Yönetimi'nde (yetkiliyseniz). Ayrıntı Şirket Yönetimi Kılavuzu'ndadır.

## Giriş penceresi

[[EKRAN: wa-giris | "🔐 RECOrion Şirket Girişi" penceresi: e-posta, şifre, Beni Hatırla, Şifremi unuttum ve Giriş Yap düğmesi | Resmi sitede sağ üstteki "🔑 Giriş Yap" düğmesine basın]]

**Bu ekran ne işe yarar?** Şirket kullanıcılarının sisteme girişini sağlar. Alt başlık: "Yönetim veya çalışma alanı paneline güvenli erişim sağlayın."

**Kimler görür?** Hesabı olan herkes.

| Alan | Ne işe yarar | Nasıl doldurulur / seçenekler | Örnek | Zorunlu |
|---|---|---|---|---|
| **✉️ Kurumsal E-Posta Adresi** | Kullanıcı adınız. | Hesabınızın e-postası. **Beni Hatırla** işaretliyse bir dahaki girişte dolu gelir. | mehmet.demir@orneklojistik.com.tr | Evet |
| **🔑 Güvenli Şifre** | Şifreniz. | — | — | Evet |
| **Beni Hatırla** | Oturumun ne kadar açık kalacağı. | İşaretliyse 30 gün, değilse 12 saat. Ortak bilgisayarda işaretlemeyin. | — | Hayır |

| Düğme | Ne yapar | Dikkat |
|---|---|---|
| **✕** | Pencereyi kapatır (ESC de kapatır). | — |
| **Şifremi unuttum** | Şifremi Unuttum penceresini açar. | — |
| **Giriş Yap →** | Giriş yapar ("Giriş Yapılıyor..."), rolünüze göre panelinize götürür. | — |

**Hata mesajları:**

| Mesaj | Ne demek, ne yapmalı |
|---|---|
| **"Geçersiz kullanıcı adı veya şifre."** | E-posta veya şifre yanlış. Kontrol edin ya da şifrenizi sıfırlayın. |
| **"Çok fazla hatalı giriş denemesi. Lütfen 15 dakika sonra tekrar deneyin."** | 5 hatalı denemeden sonra hesabınız 15 dakika kilitlenir. Bekleyin veya şifrenizi sıfırlayın. |
| **"Kullanıcı hesabınız pasife alınmıştır. Sisteme giriş yapamazsınız."** | Şirket yöneticiniz hesabınızı kapatmış. Ona başvurun. |
| **"'<şirket>' şirket hesabı pasife alınmıştır…"** | Şirketinizin hesabı kapalı. Şirket yöneticiniz RECDx ile görüşmeli. |
| **"'<şirket>' için satın alma başvurunuz henüz Süper Yönetici tarafından onaylanmamıştır…"** | Başvurunuz incelemede. Onay e-postasını bekleyin. |
| **"'<şirket>' için yapılan satın alma başvurusu reddedilmiştir."** | Başvuru kabul edilmedi. RECDx ile iletişime geçin. |
| **"'<şirket>' şirketinin abonelik paketi henüz Süper Yönetici tarafından onaylanıp aktif edilmemiştir."** | Paketiniz etkinleştirilmeyi bekliyor. |

#### Şifremi Unuttum penceresi

[[EKRAN: wa-sifremi-unuttum | "Şifremi Unuttum" penceresi: açıklama metni, e-posta kutusu, Bağlantı Gönder ve Vazgeç | Giriş penceresinde "Şifremi unuttum" bağlantısına basın]]

Metin: "Hesabınıza kayıtlı e-posta adresini yazın. Şifre belirleme bağlantısı gönderilecektir." Kutu, giriş penceresine yazdığınız e-postayla dolu gelir.

| Düğme | Ne yapar | Dikkat |
|---|---|---|
| **Bağlantı Gönder** | E-postanıza şifre belirleme bağlantısı gönderir. | Güvenlik gereği hesap olsa da olmasa da aynı mesaj çıkar: **"Bu e-posta adresiyle kayıtlı bir hesap varsa şifre belirleme bağlantısı gönderildi."** Bağlantı 1 saat geçerlidir. |
| **Vazgeç** | Pencereyi kapatır. | — |

## Şifre belirleme sayfası

[[EKRAN: wa-sifre-belirle | "Şifrenizi belirleyin" kartı: Yeni şifre ve Yeni şifre (tekrar) alanları, Şifremi Kaydet düğmesi | E-postanıza gelen şifre belirleme (davet veya "Şifremi unuttum") bağlantısını açın]]

**Bu ekran ne işe yarar?** E-postanıza gelen tek kullanımlık bağlantıyla yeni şifre belirlersiniz. Yeni kullanıcı davetinde ve "Şifremi unuttum" sonrasında kullanılır. Giriş gerektirmez.

**Ekranın bölümleri:** "Şifrenizi belirleyin" başlığı, "RECOrion hesabınız için yeni bir şifre oluşturun." alt başlığı, iki şifre alanı; sağ üstte tema düğmesi.

| Alan | Ne işe yarar | Nasıl doldurulur | Örnek | Zorunlu |
|---|---|---|---|---|
| **Yeni şifre** | Yeni şifreniz. | En az 8 karakter. | — | Evet |
| **Yeni şifre (tekrar)** | Yazım hatasını önler. | Aynı şifreyi yeniden yazın. | — | Evet |

| Düğme | Ne yapar | Dikkat |
|---|---|---|
| **Şifremi Kaydet** | Şifreyi kaydeder ("Kaydediliyor…"). Başarıda başlık **"Şifreniz belirlendi"** olur: "<e-posta> hesabı için yeni şifreniz kaydedildi." | Bağlantı tek kullanımlıktır. |
| **Giriş Sayfasına Git** | Resmi siteye döner; oradan giriş yaparsınız. | — |

**Mesajlar:** **"Şifre en az 8 karakter olmalıdır."** · **"Şifreler birbiriyle aynı değil."** · **"Bağlantı geçersiz veya süresi dolmuş. Lütfen yeni bağlantı isteyin."** (1 saat geçtiyse veya bağlantı kullanıldıysa) · Bağlantı eksikse: **"Bağlantı eksik veya hatalı. Giriş ekranındaki "Şifremi unuttum" ile yeni bağlantı isteyebilirsiniz."**

## Onay bağlantısı sayfası

[[EKRAN: wa-onay-baglantisi | "RECOrion · İş adımı onayı" sayfası: adım bilgileri kartı, "Çıktı · sürüm n" kartı ve "Kararınız" kartı | Onaylayıcısı olduğunuz bir adım teslim edildiğinde gelen e-postadaki bağlantıyı veya Telegram mesajındaki "🔎 İncele" düğmesini açın]]

**Bu ekran ne işe yarar?** Bir iş adımının onaylayıcısıysanız, size gelen bağlantıyla **giriş yapmadan** adımın çıktısını okuyup onaylamanızı veya revizyon istemenizi sağlar.

**Ne zaman kullanırım?** Telefonda veya bilgisayar başında değilken hızlıca karar vermek istediğinizde.

**Ekranın bölümleri:**

1. **Adım kartı:** Başlıkta adım adı, altında "<proje> · teslim: <tarih>", revizyon varsa **"Ret: n / m"** rozeti; **Personel**, **Onaylayıcı**, **Bağlantı geçerliliği**; adımın açıklaması ve **Kabul ölçütü**.
2. **Çıktı · sürüm n:** AI personelin teslim ettiği çıktı (başlıklar, tablolar biçimlendirilmiş olarak).
3. **Kararınız:** Not kutusu ve karar düğmeleri.

| Alan | Ne işe yarar | Nasıl doldurulur | Örnek | Zorunlu |
|---|---|---|---|---|
| **Not (revizyon için gerekçe zorunlu)** | Revizyonda personele ne düzelteceğini söyler; onayda isteğe bağlı not. | "Neyin düzeltilmesi gerektiğini yazın…" | Tablodaki toplamlar hatalı; kaynak ekleyin. | Revizyonda evet |

| Düğme | Ne yapar | Dikkat |
|---|---|---|
| **Onayla** | Adımı tamamlar; ona bağlı sonraki adımlar başlar. Sonuç: **"Onaylandı"** — "Kararınız iş akışına iletildi; sonraki adımlar başlayacak." | Onay penceresi yoktur; geri alınamaz. |
| **Revizyon iste** | Adımı revizyona gönderir. Sonuç: **"Revizyon istendi"** — "Gerekçeniz personele iletildi; düzeltilmiş sürüm yeniden onayınıza gelecek." | Gerekçe zorunludur. |
| **RECOrion'a git** | Oturumunuz varsa Work Space'e, yoksa resmi siteye gider. | — |

Sayfanın altında: **"Bu bağlantı yalnızca size özeldir ve tek kullanımlıktır."** Bağlantı 7 gün geçerlidir.

**Mesajlar ("Bağlantı kullanılamıyor" kartı):**

| Mesaj | Ne demek, ne yapmalı |
|---|---|
| **"Onay bağlantısı geçersiz."** | Bağlantı bozuk. Kararı Work Space › Onaylarım'dan verin. |
| **"Bu onay bağlantısı daha önce kullanıldı."** | Kararı zaten verdiniz. |
| **"Onay bağlantısının süresi doldu. Kararı RECOrion Work Space'ten verebilirsiniz."** | 7 gün geçti. Onaylarım'dan karar verin. |
| **"Bu iş adımı artık karar beklemiyor."** / **"Bu iş adımı için karar zaten verilmiş veya yeni bir teslim yapılmış."** | Başkası karar verdi veya yeni sürüm geldi. Yeni bağlantıyı bekleyin ya da Onaylarım'a bakın. |
| **"Bu iş adımının onaylayıcısı değişti; bağlantı geçersiz."** | Proje yöneticisi onaylayıcıyı değiştirdi. |
| **"Revizyon isterken gerekçeyi yazın; personel buna göre düzeltecek."** | Not kutusu boş. Gerekçe yazın. |

> **İpucu:** Telegram mesajındaki **✅ Onayla** ve **↩️ Revizyon iste** düğmeleri de aynı kararı verir.

# Work Space

## Üst çubuk ve mod çubuğu

[[EKRAN: wa-ust-cubuk | Work Space üst çubuğu (marka, Kurum alanında şirket logosu ve adı, sağlık noktaları, tema, Resmi Web & Paketler, Şirket Yönetimi, kullanıcı kartı, Çıkış) ve altındaki mod çubuğu | Proje yöneticisi olarak giriş yapın; Work Space açılınca ekranın en üstünü alın. Logolu görünüm için şirkete önceden logo yüklenmiş olmalı]]

**Bu ekran ne işe yarar?** Work Space'in her ekranında üstte durur. Hangi şirkette olduğunuzu, sistemin sağlığını ve kim olarak giriş yaptığınızı gösterir; paneller ve modlar arasında geçirir.

**Kimler görür?** Work Space'e giren herkes.

**Üst çubuğun bölümleri (soldan sağa):**

| Bölüm | Ne gösterir |
|---|---|
| Marka | Yazılı RECOrion logosu ve altında ORION'un açılımı (Operational Reasoning Intelligence Orchestration Network). |
| **Kurum:** | Şirketinizin logosu ve adı. Logo yüklenmemişse yerinde küçük bir simge görünür. Logoyu şirket yöneticiniz Şirket Yönetimi › Genel › Şirket Profili'nden yükler. Dar ekranlarda "Kurum:" etiketi gizlenir, uzun şirket adı kısaltılır; tam ad üzerine gelince görünür. |
| Sağlık noktaları | **Postgres** (veritabanı), **Qdrant** (hafıza arama altyapısı), **Redis** (canlı akış altyapısı). Yeşil nokta sağlıklı, kırmızı nokta sorun var demektir. Yalnız geniş ekranlarda (1600 pikselden geniş) görünür. |
| Tema düğmesi | Koyu / Açık / Sistem görünümü. |
| Kullanıcı kartı | Adınızın baş harfi, adınız ve rolünüz (ör. "Proje Yöneticisi"). Dizüstü gibi dar ekranlarda yalnız baş harf görünür; telefonda gizlenir. |

**Düğmeler:**

| Düğme | Ne yapar | Dikkat |
|---|---|---|
| **🌐 Resmi Web & Paketler** | Resmi siteye gider. | Oturumunuz açık kalır; oradan **💻 Çalışma Alanına Git →** ile dönersiniz. |
| **🏢 Şirket Yönetimi** | Şirket Yönetimi konsolunu açar. | Yalnız Şirket Yöneticisi ve Şirket Yönetimi'nin en az bir menüsüne izni olanlar görür. |
| **Çıkış** | Oturumu kapatır, resmi siteye döner. | Onay istemez. |

**Mod çubuğu düğmeleri:**

| Düğme | Ne açar | Kimler görür |
|---|---|---|
| **Projeler** | Projeler ve Case'ler listesi. Bir proje ekranındayken de bu düğme seçili görünür. | Herkes |
| **Onaylarım** / **Onaylarım (n)** | Kararınızı bekleyen işler. Parantezdeki sayı kendiliğinden güncellenir. | Herkes |
| **Çalışma Alanı · <proje adı>** | Seçili projenin üç bölmeli görev sohbeti ekranı. | Herkes |
| **Pano** | Şirket veya departman göstergeleri. | **Şirket Geneli Pano** veya **Departman Panosu** izni olanlar |
| **Bağlantılarım** | Kişisel erişim anahtarları ve şirket sistemlerindeki anahtarlarınız. | Herkes |

> **İpucu:** **Onaylarım (n)** sayacı iş adımı onaylarını ve AI personelin onay bekleyen araç işlemlerini sayar. RECSlip fişleri ve dış sisteme aktarımlar Onaylarım ekranını açtığınızda görünür; onaylayıcıysanız Onaylarım'ı düzenli açın.

## Projeler

Bu mod, projelerin ve Case'lerin açıldığı, planlandığı, yürütüldüğü ve kapatıldığı yerdir. Önce projelerin geçtiği durumları öğrenmek, ekranları anlamayı kolaylaştırır.

### Proje ve iş adımı durumları

**Bu bölüm ne işe yarar?** Bir projenin baştan sona hangi aşamalardan geçtiğini ve hangi düğmenin projeyi hangi duruma taşıdığını gösterir. Kendi başına bir ekran değildir; proje kartlarında ve proje ekranında rozet olarak görünür.

**Proje türleri:** **Proje** ("çok adımlı, takvimli iş") ve **Case** ("tek bir konu / vaka çözümü"). İkisi aynı ekranlarla yönetilir.

**Proje durumları:**

| Rozet | Anlamı | Bu durumda ne yaparsınız |
|---|---|---|
| **Taslak** | Proje yeni açıldı; bilgiler ve isterler yazılıyor. | İsterleri yazın, ekleri yükleyin, planlamaya başlayın. |
| **Planlama** | Beyin AI ile plan hazırlanıyor. Plan kaydedilince taslak proje kendiliğinden Planlama'ya geçer. | Planı düzenleyin, onaylayın, ekibi kurun. |
| **Başlamaya hazır** | Plan onaylı, her adıma personel atanmış, tarihler belli. Başlangıç günü gelince proje yöneticisine e-posta ve Telegram hatırlatması gider. | Projeyi başlatın. |
| **Aktif** | İş akışı yürüyor; bağımlılıkları biten adımlar AI ve insan personele açılır. | Çıktıları izleyin, onaylayın. |
| **Duraklatıldı** | Süren adımlar devam eder, yeni adım açılmaz. | Devam ettirin veya kapatın. |
| **Tamamlandı** | Proje kapandı; yazışma kaydı salt okunur. | Ekleri kurum hafızasına aktarın, şablon olarak kaydedin. |
| **İptal edildi** | Proje kapandı; başlamamış adımlar da iptal edildi. Geri alınamaz. | — |

**Durum geçişleri** (yalnız projenin yöneticisi veya **Tüm Projeleri Yönetme** izni olan yapar):

| Geçiş | Düğme (nerede) | Ön koşul | Onay penceresi |
|---|---|---|---|
| Taslak → Planlama | **Planlamaya başla** (proje başlığı) | İsterler yazılmış olmalı. Yoksa: **"Planlamaya geçmeden önce projenin isterlerini yazın."** | Yok |
| Planlama → Başlamaya hazır | **Başlamaya hazır yap** (Hazırlık & Bildirim) | Plan onaylı ve adım var (**"Önce iş adımlarını onaylayın."**), başlangıç ve bitiş tarihi var (**"Başlangıç ve bitiş tarihlerini belirleyin."**), bitiş başlangıçtan önce değil, her adıma personel atanmış (**"Atanmamış iş adımları var: …"**). Koşullar sağlanmadan düğme pasiftir. | Yok |
| Başlamaya hazır → Planlama | **Planlamaya geri al** (Hazırlık & Bildirim) | Proje Başlamaya hazır durumunda. | **"Proje yeniden planlamaya alınsın mı?"** |
| Başlamaya hazır → Aktif | **Başlat** (başlık) veya **Projeyi şimdi başlat** (Hazırlık & Bildirim) | Proje Başlamaya hazır durumunda. | **"Proje başlatılsın mı? Bağımlılığı olmayan iş adımları AI personele açılır."** |
| Aktif → Duraklatıldı | **Duraklat** (başlık) | Proje Aktif. | **"Proje duraklatılsın mı?"** |
| Duraklatıldı → Aktif | **Devam ettir** (başlık) | Proje Duraklatıldı. | Yok |
| Aktif / Duraklatıldı → Tamamlandı | **Projeyi tamamla** (Kapanış) | Proje Aktif veya Duraklatıldı. | **"Proje tamamlandı olarak kapatılsın mı?"** |
| Açık herhangi bir durum → İptal edildi | **İptal et** (Kapanış) | Proje kapanmamış. | **"Proje iptal edilsin mi? Bu işlem geri alınamaz."** |

Başarı bildirimleri: **"Planlamaya alındı."** · **"Proje başlamaya hazır."** · **"Proje başlatıldı."** · **"Proje duraklatıldı."** · **"Proje devam ediyor."** · **"Proje tamamlandı."** · **"Proje iptal edildi."** · **"Proje planlamaya geri alındı."** İşlem o an tamamlanamazsa durum değişmez ve hata gösterilir; yeniden deneyebilirsiniz.

> **Dikkat:** Paketinizin **Eşzamanlı Proje** sınırı vardır. Sınır doluysa yeni proje açılamaz: **"'<paket>' paketinizde aynı anda en fazla N açık proje olabilir. Tamamlanan veya iptal edilen projeler sayılmaz."** Biten projelerinizi kapatın veya paketinizi büyütün.

**İş adımı (görev) durumları:**

| Rozet | Anlamı |
|---|---|
| **Sırada** | Önce bitmesi gereken adımlar henüz bitmedi. |
| **Başlayabilir** | Bağımlılıkları kapandı, açılmayı bekliyor. |
| **Çalışılıyor** | Personel çalışıyor. AI personelse "<ad> çalışıyor…" yazar. |
| **Onay bekliyor** | Çıktı teslim edildi; onaylayıcının kararı bekleniyor. Onaylayıcıya e-posta ve Telegram ile istek gider. |
| **Revizyonda** | Onaylayıcı veya kontrol personeli düzeltme istedi; personel gerekçeye göre düzeltiyor. |
| **Karantinada** | Ret sınırına ulaştı (varsayılan 3) veya personel çalışamadı (ör. kredi yetersiz, RECAi hizmetine ya da bir bağlantıya erişilemedi). Proje yöneticisinin kararı bekleniyor. |
| **Tamamlandı** | Onaylandı (veya onay gerekmiyordu). |
| **İptal** / **İptal edildi** | Adım iptal edildi; ona bağlı adımlar beklemeden devam eder. |

**Bir adımın akışı:** Sırada / Başlayabilir → Çalışılıyor → (kontrol personeli varsa değerlendirme: **"Kontrolden geçti"** veya **"Kontrol personeli düzeltme istedi"**) → teslim → Onay bekliyor → **Onayla** ile Tamamlandı, **Revizyon iste** ile Revizyonda → düzeltilmiş sürüm yeniden onaya gelir → ret sınırı dolarsa Karantinada → proje yöneticisi **Yeniden dene** (ret sayacı sıfırlanır) veya **Adımı iptal et**.

"İnsan onayı gerekli" ayarı kapalı olan adım, teslimden (ve varsa kontrolden) sonra doğrudan Tamamlandı olur.

**Plan durumu rozetleri** (Beyin AI Planlama sekmesindeki "İş adımları" kartında): **Onay bekliyor** (plan taslağı var, onaylanmadı) · **Onaylandı** (plan onaylandı, iş adımları oluşturuldu). Plan yeniden kaydedilirse onay düşer; yeniden onaylamanız gerekir.

### Projeler ve Case'ler ekranı

[[EKRAN: wa-projeler | "Projeler ve Case'ler" ekranı: başlık, Benim projelerim / Tüm projeler seçici, Toplantıdan oluştur, Şablondan oluştur, Yeni Proje / Case düğmeleri ve proje kartları | Proje yöneticisi olarak giriş yapın; mod çubuğunda "Projeler"e basın. Ekranda en az üç farklı durumda proje olsun]]

**Bu ekran ne işe yarar?** Görebildiğiniz tüm projeleri ve Case'leri kartlar hâlinde listeler. Yeni proje açmanın üç yolunu sunar: boş form, hazır şablon, toplantı kaydı. Alt başlık: "İsterleri yazın, Beyin AI ile planlayın, AI personel ekibinizi kurun ve başlatın."

**Ne zaman kullanırım?** Her gün; bir projeye girmek veya yeni proje açmak için.

**Kimler görür / kimler değiştirebilir?** Herkes görür; ancak yalnız ekibinde olduğu veya yöneticisi olduğu projeleri. **Tüm Projeleri Yönetme** izni olanlar şirketin tüm projelerini görebilir. Oluşturma düğmeleri yalnız **Proje / Case Açma** izni olanlarda görünür.

**Ekranın bölümleri:** Başlık ve düğmeler; kapsam seçici; proje kartları. Hiç proje yoksa **"Henüz proje yok"** ve "İlk projenizi veya Case'inizi oluşturun; isterlerinizden Beyin AI iş adımlarını ve ekibi önersin." yazar (yetkiliyse ortada **Yeni Proje / Case** düğmesi çıkar).

**Proje kartında neler yazar?** Durum rozeti ve tür (Proje/Case), proje adı, kısa açıklama, "Yönetici: <ad>", "<n> iş adımı", "<başlangıç> – <bitiş>", varsa "Kaynak: …" (proje şablondan, toplantıdan veya başka bir yoldan açıldıysa).

| Düğme | Ne yapar | Kim görür |
|---|---|---|
| **Benim projelerim** / **Tüm projeler** | Ekibinde olduğunuz projeler / şirketin tüm projeleri. | **Tüm Projeleri Yönetme** izni olanlar |
| **Toplantıdan oluştur** | Toplantıdan proje oluştur penceresini açar. | **Proje / Case Açma** izni olanlar |
| **Şablondan oluştur** | Şablondan proje oluştur penceresini açar. | **Proje / Case Açma** izni olanlar |
| **Yeni Proje / Case** | Boş proje formunu açar. | **Proje / Case Açma** izni olanlar |
| Proje kartı | Proje ekranını açar. | Herkes (gördüğü projeler) |

#### Yeni Proje / Case penceresi

[[EKRAN: wa-yeni-proje | "Yeni Proje / Case" penceresi: Adı, Türü, Proje yöneticisi, Sorumlu departman, tarihler, Kısa açıklama ve İsterler alanları | Projeler ekranında "Yeni Proje / Case" düğmesine basın]]

| Alan | Ne işe yarar | Nasıl doldurulur / seçenekler | Örnek | Zorunlu |
|---|---|---|---|---|
| **Adı** | Proje/Case adı; sistem buradan kısa bir kod da üretir. | En az 2, en çok 255 karakter. | Depo Sayım Uygulaması | Evet |
| **Türü** | Projenin niteliği. | **Proje (çok adımlı, takvimli iş)** / **Case (tek bir konu / vaka çözümü)** | Proje | Evet |
| **Proje yöneticisi** | Projeden sorumlu kişi; projede tüm yönetici işlemlerini yapar. | Şirketin etkin insan kullanıcılarından biri. Varsayılan: siz. | Mehmet Demir | Evet |
| **Sorumlu departman** | Projenin bağlı olduğu birim; departman panosunda bu projeyi gösterir. | **Belirtilmedi** veya şirket departmanlarından biri. | Bilgi İşlem | Hayır |
| **Hedef başlangıç** | Planlanan başlangıç tarihi. | Tarih seçin. Başlamaya hazır yapmak için gerekir. | 10.11.2026 | Hayır |
| **Hedef bitiş** | Planlanan bitiş tarihi. | Başlangıçtan önce olamaz. Başlamaya hazır yapmak için gerekir. | 05.12.2026 | Hayır |
| **Kısa açıklama** | Proje kartında görünen özet. | Bir iki cümle. | Depolardaki stok sayımını mobil cihazla yapmak. | Hayır |
| **İsterler** | Projeden ne beklediğiniz. Beyin AI iş adımlarını ve gereken personeli bu metinden ve onaylı proje eklerinden çıkarır. | "Ne yapılmasını istiyorsunuz? Hedefler, kapsam, kısıtlar, beklenen çıktılar, teslim ölçütleri…" | Bkz. aşağıdaki örnek | Planlama için evet |

Pencerede not: "Dosya ve görselleri (Proje Ekleri) oluşturduktan sonra yükleyebilirsiniz; onaylanan ekler bu projedeki AI personel tarafından öğrenilir."

| Düğme | Ne yapar | Dikkat |
|---|---|---|
| **Vazgeç** | Pencereyi kapatır. | Bilgiler kaydedilmez. |
| **Oluştur** | Projeyi Taslak olarak açar ("Oluşturuluyor…"). Başarı: **"'<ad>' oluşturuldu. Şimdi ekleri yükleyip Beyin AI ile planlayabilirsiniz."** Proje ekranı açılır. | Paket sınırı doluysa açılmaz. |

**Hata mesajları:** **"Proje adını yazın."** · **"Proje yöneticisi şirketinizin insan kullanıcılarından biri olmalıdır."** · **"Departman bulunamadı."** · paket sınırı mesajı.

> **Örnek:** Mehmet Demir, isterlere şunu yazar: "Depo personeli el terminaliyle raf barkodunu okutup sayım girecek. Sayım farkları günlük rapor olarak depo müdürüne gidecek. Odoo stok modülüyle uyumlu olacak. Teslim: çalışan prototip ve kullanım kılavuzu. Kısıt: internet kesildiğinde de sayım alınabilmeli." Beyin AI bu metinden analiz, tasarım, geliştirme, test ve kılavuz adımlarını önerir.

> **İpucu:** İsterleri ne kadar açık yazarsanız plan o kadar isabetli olur. Hedef, kapsam dışı konular, kısıtlar ve "bitti" sayılma ölçütünü mutlaka yazın.

#### Şablondan proje oluştur penceresi

[[EKRAN: wa-sablondan-proje | "Şablondan proje oluştur" penceresi: Tümü / Şirketimizin / RECDx hazır seçici ve şablon kartları; bir şablon seçilince adım listesi ve form | Projeler ekranında "Şablondan oluştur" düğmesine basın]]

**Bu pencere ne işe yarar?** Şirketinizin veya RECDx'in hazır proje şablonundan; adımları, rolleri, süreleri ve bağımlılıkları hazır gelen bir proje açar.

**Bölümler:** Kapsam seçici **Tümü** / **Şirketimizin** / **RECDx hazır**; şablon kartları. Kartta: **RECDx** veya **Şirket** rozeti, kategori, (Case şablonuysa) **Case**, ad, açıklama, "<n> adım", "~<n> iş günü", "<n> kez kullanıldı". Bir şablon seçince açıklaması, form ve **Şablon adımları** listesi görünür (her adımda unvan · departman · "n gün" · "önce: S1, S2" · gerekiyorsa "onaysız").

| Alan | Ne işe yarar | Nasıl doldurulur | Örnek | Zorunlu |
|---|---|---|---|---|
| **Proje adı** | Yeni projenin adı. | Varsayılan şablon adıdır; değiştirebilirsiniz (en az 2 karakter). | Kasım Kampanyası | Evet |
| **Başlangıç tarihi** | Projenin başlangıcı. | Tarih seçin. | 17.11.2026 | Hayır |

| Düğme | Ne yapar | Dikkat |
|---|---|---|
| **Vazgeç** | Pencereyi kapatır. | — |
| **Şablonlara dön** | Şablon listesine döner. | — |
| **Projeyi oluştur** | Projeyi açar ("Oluşturuluyor…"). Sonuç: **"'<ad>' oluşturuldu; planı inceleyip onaylayın."** veya **"'<ad>' oluşturuldu. <n> adıma AI personel atandı; şirkette olmayan roller: …"**. Proje **Beyin AI Planlama** sekmesiyle açılır. | Paket sınırı geçerlidir. |

Pencerede not: "Plan taslak olarak gelir: unvanı uyan AI personel adımlara atanır, onaylayıcılar boş gelir (proje yöneticisi). Planı inceleyip Beyin AI ile düzenleyebilir, sonra onaylarsınız." Şablon yoksa: **"Şablon yok"** — "Biten bir projenizin planını 'Şablon olarak kaydet' ile şirket şablonu yapabilirsiniz."

> **İpucu:** "Şirkette olmayan roller" uyarısı çıkarsa o adımlar için Beyin AI Planlama sekmesindeki **İşe alım önerileri** kartından AI personel işe alın veya mevcut bir personeli atayın.

#### Toplantıdan proje oluştur penceresi

[[EKRAN: wa-toplantidan-proje | "Toplantıdan proje oluştur" penceresi: Dosya yükle / Tarayıcıda kaydet seçici, ilerleme durumu ve hazırlanan proje taslağı formu | Projeler ekranında "Toplantıdan oluştur" düğmesine basın; görüntü için bir ses dosyası yükleyip taslağın hazırlanmasını bekleyin]]

**Bu pencere ne işe yarar?** Toplantının ses veya video kaydını yazıya çevirir, kişisel verileri maskeler ve Beyin AI ile bir proje taslağı (ad, tür, açıklama, isterler, önerilen adımlar) çıkarır.

**Ne zaman kullanırım?** Bir iş toplantıda konuşulduysa ve isterleri baştan yazmak istemiyorsanız.

**1. aşama — kayıt:** Üstte **Dosya yükle** / **Tarayıcıda kaydet** seçici.

| Alan | Ne işe yarar | Nasıl doldurulur | Örnek | Zorunlu |
|---|---|---|---|---|
| **Toplantı adı** | Kaydın adı. | En çok 200 karakter; boşsa dosya adı kullanılır. | Depo sayım uygulaması ön görüşmesi | Hayır |
| **Ses veya video dosyası** | İşlenecek kayıt. | mp3, m4a, wav, webm, mp4, ogg…; en fazla 300 MB ve 3 saat. | toplanti.m4a | "Dosya yükle"de evet |

**Tarayıcıda kaydet** modunda: **Kaydı başlat** → "● Kaydediliyor mm:ss" rozeti → **Kaydı bitir**. Kayıt sürerken pencere kapanmaz. Uyarı: "Toplantıdakilere kayıt alındığını bildirin. Kayıt yazıya çevrildikten sonra silinir."

İşleme sırasında ekranda sırayla: **"Ses hazırlanıyor…"** → **"Yazıya çevriliyor (i/n)…"** → **"Beyin AI proje taslağını hazırlıyor…"**. Hata olursa kırmızı mesaj ve **Yeniden dene** düğmesi çıkar.

**2. aşama — taslak hazır:**

| Alan | Ne işe yarar | Nasıl doldurulur | Örnek | Zorunlu |
|---|---|---|---|---|
| **Proje adı** | Taslaktan gelir. | Düzenleyebilirsiniz. | Depo Sayım Uygulaması | Evet |
| **Tür** | Proje / Case. | Listeden seçin. | Proje | Evet |
| **Açıklama** | Kısa özet. | Düzenleyebilirsiniz. | — | Hayır |
| **İsterler** | Toplantıdan çıkarılan isterler. | Kontrol edip düzeltin. | — | Hayır |
| **Önerilen <n> iş adımını plan taslağı olarak ekle** | Önerilen adımları plana koyar. | Varsayılan işaretli. | — | Hayır |

**Açık sorular: …** satırı, RECAi'nin netleşmesini istediği konulardır. **Toplantı metni (mm:ss) · maskelenen: …** açılır bölümünde yazıya çevrilmiş ve maskelenmiş metni okuyabilirsiniz.

| Düğme | Ne yapar | Dikkat |
|---|---|---|
| **Vazgeç** / **Kapat** | Pencereyi kapatır. | Kayıt sürerken kapanmaz. |
| **Yükle ve işle** | Dosyayı yükleyip işler ("Yükleniyor…"). | — |
| **Yeniden dene** | Hatadan sonra işlemi yineler. | — |
| **Projeyi oluştur** | Taslaktan projeyi açar. Sonuç: **"'<ad>' oluşturuldu; <n> adımlık plan taslağını inceleyip onaylayın."** Proje **Beyin AI Planlama** sekmesiyle açılır. | — |

**Mesajlar:** **"RECAi Ses (toplantıyı yazıya çevirme) paketinizde yer almıyor."** (paketinizde bu özellik yok) · **"Yalnızca ses veya video dosyası yüklenebilir (mp3, m4a, wav, webm, mp4…)."** · **"Dosya boş."** · **"Mikrofona erişilemedi. Tarayıcı izinlerini kontrol edin veya kaydı dosya olarak yükleyin."** · **"Bu kayıttan proje oluşturulamaz (taslak hazır değil veya zaten kullanıldı)."**

> **Dikkat:** Ses kaydı yazıya çevrildikten sonra silinir; yalnız kişisel verileri maskelenmiş metin saklanır. Maskelenenler: T.C. kimlik numarası, IBAN, kart numarası, e-posta, telefon.

### Proje ekranı

[[EKRAN: wa-proje-ekrani | Proje ekranının üst kısmı: "← Projeler", proje adı, durum rozeti, tür, yönetici, tarih aralığı, sağda durum düğmeleri ve altında sekme çubuğu | Projeler ekranında Aktif durumdaki bir proje kartına tıklayın]]

**Bu ekran ne işe yarar?** Bir projenin veya Case'in tüm yaşamı buradan yönetilir: bilgiler, ekler, planlama, ekip, hazırlık, canlı iş akışı, maliyet, kod deposu, (RECSlip Case'lerinde) RECSlip süreci ve kapanış.

**Kimler görür / değiştirebilir?** Projenin ekibi görür. Yönetici işlemlerini projenin yöneticisi ve **Tüm Projeleri Yönetme** izni olanlar yapar; diğerleri çoğu alanı salt okunur görür.

**Ekranın bölümleri:**

1. **Başlık:** **← Projeler** (listeye döner), proje adı, durum rozeti, tür, "Yönetici: <ad>", tarih aralığı.
2. **Durum düğmeleri** (sağda; duruma göre değişir).
3. **Sekme çubuğu:** **Bilgiler & İsterler** · **Proje Ekleri** · **Beyin AI Planlama** · **Ekip & Simülasyon** · **Hazırlık & Bildirim** · **İş Akışı** · **Maliyet** · **Kod Deposu** · **Testler** · **RECSlip** · **Kapanış**. Bazı sekmelerin yanında sayı vardır: Proje Ekleri = ek sayısı, Beyin AI Planlama = plandaki adım sayısı, Ekip & Simülasyon = ekip üye sayısı.

Hangi sekmeyle açılır? Aktif veya Duraklatıldı projede **İş Akışı**; şablondan veya toplantıdan gelmiş, planı henüz onaylanmamış projede **Beyin AI Planlama**; diğerlerinde **Bilgiler & İsterler**.

Sekmelerin görünürlüğü: **Maliyet** yalnız proje yöneticisi ve **Tüm Projeleri Yönetme** izni olanlarda; **RECSlip** yalnız RECSlip aylık Case'lerinde görünür.

| Düğme | Ne zaman görünür | Ne yapar | Dikkat |
|---|---|---|---|
| **← Projeler** | Her zaman | Listeye döner. | — |
| **Planlamaya başla** | Yönetici, proje Taslak | Planlama'ya alır. | İsterler yazılmış olmalı. |
| **Başlat** | Yönetici, proje Başlamaya hazır | Projeyi başlatır. | Onay penceresi açılır. |
| **Duraklat** | Yönetici, proje Aktif | Projeyi duraklatır. | Onay penceresi açılır. |
| **Devam ettir** | Yönetici, proje Duraklatıldı | Yeniden Aktif yapar. | — |
| **Çalışma alanında aç** | Proje Aktif, Duraklatıldı veya Tamamlandı | Bu projeyi Çalışma Alanı'nda açar. | — |
| **Şablon olarak kaydet** | Yönetici, planda en az bir adım var | Şablon olarak kaydet penceresini açar. | — |

#### Şablon olarak kaydet penceresi

[[EKRAN: wa-sablon-kaydet | "Şablon olarak kaydet" penceresi: Şablon adı, Kategori, Açıklama ve "Adım açıklamalarını ve kabul ölçütlerini de al" onay kutusu | Planında adım olan bir projenin ekranında "Şablon olarak kaydet" düğmesine basın]]

| Alan | Ne işe yarar | Nasıl doldurulur | Örnek | Zorunlu |
|---|---|---|---|---|
| **Şablon adı** | Şablonun listedeki adı. | Varsayılan proje adı; en az 2, en çok 200 karakter. | Depo Uygulaması Geliştirme | Evet |
| **Kategori** | Şablonları gruplamak için. | En çok 80 karakter. | Yazılım | Hayır |
| **Açıklama** | Şablonun ne zaman kullanılacağı. | Serbest metin. | — | Hayır |
| **Adım açıklamalarını ve kabul ölçütlerini de al (projeye özgü bilgi içeriyorsa işareti kaldırın)** | Adım metinlerinin şablona girip girmeyeceği. | Varsayılan işaretli. | — | Hayır |

Pencerede not: "Şablona adımlar, roller, süreler, bağımlılıklar ve onay ayarları girer. Atanan kişiler, çıktılar, ekler ve yazışmalar girmez. Şablon yalnızca şirketinizde görünür."

| Düğme | Ne yapar | Dikkat |
|---|---|---|
| **Vazgeç** | Pencereyi kapatır. | — |
| **Kaydet** | Şablonu kaydeder: **"Şablon kaydedildi; şirketinizdeki herkes Yeni Proje › Şablondan oluştur ile kullanabilir."** | **Şirket Şablonlarını Yönetme** izni gerekir. |

### Bilgiler & İsterler sekmesi

[[EKRAN: wa-bilgiler-isterler | "Bilgiler & İsterler" kartı: proje alanları ve sağ üstte Kaydet düğmesi | Taslak durumdaki bir projeyi açın; "Bilgiler & İsterler" sekmesi seçili gelir]]

**Bu ekran ne işe yarar?** Projenin temel bilgilerini ve isterlerini gösterir ve düzenletir. Alt başlık: "Proje başlayana kadar düzenlenebilir." veya "Başlamış veya kapanmış projenin temel bilgileri değiştirilemez."

**Kimler değiştirebilir?** Proje yöneticisi ve **Tüm Projeleri Yönetme** izni olanlar; proje Taslak, Planlama veya Başlamaya hazır durumundayken. Diğerleri salt okunur görür.

**Alanlar:** Yeni Proje / Case penceresiyle aynıdır: **Adı**, **Türü**, **Proje yöneticisi**, **Sorumlu departman**, **Hedef başlangıç**, **Hedef bitiş**, **Kısa açıklama**, **İsterler**. İsterler alanının altında: "Beyin AI iş adımlarını ve gereken personeli bu metinden ve onaylı proje eklerinden çıkarır."

| Düğme | Ne yapar | Dikkat |
|---|---|---|
| **Kaydet** | Değişiklikleri kaydeder: **"Proje bilgileri kaydedildi."** | Değişiklik yoksa pasiftir. |

**Hata mesajları:** **"Başlamış veya kapanmış projenin temel bilgileri değiştirilemez."** · **"Bitiş tarihi başlangıçtan önce olamaz."** · **"Geçersiz tür."**

> **İpucu:** Proje yöneticisini değiştirmek için **Proje yöneticisi** alanından yeni kişiyi seçip **Kaydet**'e basın.

### Proje Ekleri sekmesi

[[EKRAN: wa-proje-ekleri | "Proje Ekleri" kartı: yükleme alanı ve durum rozetli doküman listesi | Bir projeyi açın, "Proje Ekleri" sekmesine basın; listede en az bir "Onay bekliyor" ve bir "Öğrenildi" dosya olsun]]

**Bu ekran ne işe yarar?** Şartname, örnek çıktı, ekran görüntüsü, çizim gibi dosyaları yükleyip onaylarsınız. Onaylanan ekleri **yalnız bu projedeki** AI personel öğrenir. Kartta açıklama: "Ekler KVKK maskelemesinden geçer, RECAi öğrenme kartı ve testi hazırlar, siz onaylayınca projenin bilgisine eklenir."

**Kimler değiştirebilir?** Yükleme ve onay kararları proje yöneticisindedir (proje kapanmamışsa). Ekip üyeleri dosyayı görev sohbetinden ekleyebilir; yönetici onaylayınca öğrenilir.

**Ekranın bölümleri:**

1. **Yükleme alanı:** "Doküman veya görsel yükleyin (tıklayın ya da sürükleyin)". Kabul edilenler: PDF, Word, Excel, PowerPoint (eski .doc/.xls/.ppt dahil), metin dosyaları ve görseller (PNG, JPG, WEBP, TIFF) · en fazla 50 MB. Birden fazla dosya seçebilirsiniz. Yüklenirken "<n> dosya yükleniyor…", sonra **"'<dosya>' yüklendi; işlendikten sonra onayınıza sunulacak."**
2. **Doküman listesi:** Her satırda dosya adı, "TÜR · boyut · sürüm n · n görsel · KVKK: … maskelendi", varsa hata metni, durum rozeti ve düğme. Boşsa **"Henüz doküman yok"** — "Proje kapanışında onaylı ekleri Kurum Hafızasına aktarabilirsiniz."

**Doküman durumları:**

| Rozet | Anlamı |
|---|---|
| **Yüklendi** | Dosya alındı, işlenmeyi bekliyor. |
| **İşleniyor** | Metin ve görseller okunuyor, kişisel veriler maskeleniyor, öğrenme kartı hazırlanıyor. Liste kendiliğinden güncellenir. |
| **Onay bekliyor** | Sizin incelemeniz bekleniyor. |
| **Öğrenildi** | Onaylandı; AI personel bu bilgiyi kullanıyor. |
| **Reddedildi** | Öğrenilmeyecek. |
| **Karantinada** | İçerik güvenliği kontrolünde sorun bulundu. |
| **İşlenemedi** | Dosya okunamadı. **Yeniden işle** deneyin. |
| **Eski sürüm** | Yerine yeni sürüm yüklendi. |
| **Hafızada** | Kurum Hafızasına aktarıldı. |
| **Eklendi** | Sohbet mesajına eklenmiş dosya. |

| Düğme | Ne yapar | Dikkat |
|---|---|---|
| **İncele ve onayla** (Onay bekliyor) / **Aç** (diğer durumlar) | Doküman inceleme penceresini açar. | Dosya işlenirken pasiftir. |

#### Doküman inceleme penceresi

[[EKRAN: wa-dokuman-inceleme | Doküman inceleme penceresi: bilgi şeridi, Özet, Öğrenilecek anahtar bilgiler, Test soruları ve alttaki karar düğmeleri | Proje Ekleri'nde "Onay bekliyor" durumdaki bir dokümanda "İncele ve onayla" düğmesine basın]]

Başlık: "<dosya adı> · sürüm n". Üstte bilgi şeridi: durum rozeti, "TÜR · boyut", "n sayfa", "n sayfa OCR ile okundu", "n görsel açıklandı", "n bilgi parçası".

Olası notlar: "Doküman işleniyor: metin ve görseller okunuyor, kişisel veriler maskeleniyor, öğrenme kartı hazırlanıyor…" · "KVKK: … maskelendi. AI personel bu verileri görmez; asıl dosya erişim kontrollü depoda kalır." · "İçerik güvenliği kontrolü şu an yapılamadı; lütfen içeriği kendiniz gözden geçirin."

| Alan | Ne işe yarar | Nasıl doldurulur | Örnek | Zorunlu |
|---|---|---|---|---|
| **Özet** | RECAi'nin hazırladığı özet. | Yalnız "Onay bekliyor" durumunda düzenlenir. | — | Hayır |
| **Öğrenilecek anahtar bilgiler (her satır bir bilgi)** | AI personelin öncelikle bileceği maddeler. | Onaydan önce düzeltebilirsiniz. "Dokümanın tamamı da parçalar halinde öğrenilir." | Sayım farkı %2'yi geçerse depo müdürüne bildirilir. | Hayır |
| **Test soruları (n)** | AI personelin dokümanı anlayıp anlamadığını ölçen çoktan seçmeli sorular. | Salt okunur; doğru şık "✓" ile işaretli. Testten sonra "AI personelin cevabı: … (doğru/yanlış)". | — | — |
| **Öğrenilecek metinden örnek (KVKK maskeli)** | AI'ın göreceği metnin bir parçası. | Açılır bölüm. | — | — |
| **Önceki sürümler** | Dokümanın geçmiş sürümleri. | "v1 (Öğrenildi) · …" | — | — |

| Düğme | Ne yapar | Dikkat |
|---|---|---|
| **Sil** | Dokümanı siler; AI personel öğrendiklerini unutur. **"Doküman silindi."** | **"\"<ad>\" silinsin mi? AI personel bu dokümandan öğrendiklerini de unutur."** Geri alınamaz. |
| **İndir** | Asıl dosyayı indirir. | — |
| **Yeniden işle** | İşlenemedi veya Karantinada dosyayı yeniden işler. | — |
| **Yeni sürüm yükle** | Öğrenilmiş dokümana yeni sürüm yükler. **"Yeni sürüm yüklendi; işlendikten sonra onayınıza sunulacak. Mevcut sürüm onaylanana kadar kullanılmaya devam eder."** | — |
| **Reddet** | Dokümanı reddeder (gerekçe isteğe bağlı). **"Doküman reddedildi; öğrenilmeyecek."** | Gerekçe penceresi açılır. |
| **AI personeli test et** | Test sorularını AI personele sorar. Sonuç: "Test sonucu: x/y doğru (%z) · <RECAi kademesi>". %80'in altı uyarı rengiyle gösterilir. | Kredi harcar. |
| **Onayla ve öğret** | Özet ve bilgilerle onaylar ("Öğreniliyor…"). **"Doküman onaylandı; AI personel artık bu bilgiyi kullanıyor."** | — |

> **Dikkat:** Paketinizin depolama kotası doluysa yükleme reddedilir. Gereksiz eski sürümleri silin veya paketinizi büyütün.

### Beyin AI Planlama sekmesi

[[EKRAN: wa-beyin-ai-planlama | Beyin AI Planlama sekmesi: üstte planlama sohbeti, altında "İş adımları" kartı (Liste görünümü), adım kartları, İşe alım önerileri ve Beyin AI notları | Planlama durumundaki bir projeyi açın, "Beyin AI Planlama" sekmesine basın; planda en az dört adım olsun]]

[[EKRAN: wa-akis-semasi | Beyin AI Planlama sekmesinin Akış şeması görünümü: adım kutuları, bağımlılık okları ve sağda seçili adımın "<Sn> · adım ayarları" kartı | Beyin AI Planlama sekmesinde "Akış şeması" düğmesine basın ve bir adım kartına tıklayın]]

**Bu ekran ne işe yarar?** İsterlerden RECAi (Beyin AI) ile iş adımı planı çıkarırsınız; planı sohbetle netleştirir, adımları düzenler ve onaylayıp gerçek iş adımlarına dönüştürürsünüz.

**Kimler değiştirebilir?** Proje yöneticisi ve **Tüm Projeleri Yönetme** izni olanlar; yalnız proje Taslak veya Planlama durumundayken. Diğerleri salt okunur görür ve sohbete yazamaz ("Plan yalnızca planlama aşamasında konuşulabilir.").

**Ekranın bölümleri:**

1. **Beyin AI ile planlama sohbeti** ("İsterleri netleştirin; ardından planı bu konuşmaya göre güncelletin."). Boşken: "Planlamaya başlayın — Beyin AI projenizin isterlerini ve onaylı proje eklerini bilir. Eksikleri sorar, iş adımları ve personel önerir." Hazır sorular: **"İsterlerde eksik gördüğün noktalar neler?"**, **"Bu proje için hangi unvanlarda personel gerekir?"**, **"En riskli adımlar hangileri?"**. Her yanıtın altında tarih, RECAi kademesi ve harcanan kredi yazar.
2. **İş adımları** kartı: alt başlıkta "Öneren model: <RECAi kademesi>" (kaydedilmemiş değişiklik varsa "· kaydedilmemiş değişiklik var") ya da "Henüz plan yok"; **Liste** / **Akış şeması** görünüm seçici; plan rozeti (**Onay bekliyor** / **Onaylandı**); plan özeti.
3. **Adım kartları** (Liste görünümünde) veya **akış şeması** ve seçili adımın **"<Sn> · adım ayarları"** kartı (Akış şeması görünümünde).
4. **İşe alım önerileri:** "Havuzda uygun AI personel bulunmayan unvanlar."
5. **Beyin AI notları:** "Risk: …" ve "Soru: …" maddeleri.

Plan yoksa: **"Plan bekleniyor"** — "İsterleri yazdıktan sonra Beyin AI'dan iş adımı önerisi isteyin."

**Alanlar (sohbet ve Liste görünümü):**

| Alan | Ne işe yarar | Nasıl doldurulur / seçenekler | Örnek | Zorunlu |
|---|---|---|---|---|
| Mesaj kutusu ("Beyin AI'ya yazın…") | Beyin AI ile konuşma. | En çok 8000 karakter. Enter gönderir, Shift+Enter yeni satır. | Test adımını geliştirmeden ayrı tutalım mı? | — |
| **Beyin AI'ya not (isteğe bağlı)** | Öneri isterken yön verir. | Serbest metin. | Test adımını ayrı tut, tasarım için iki gün yeterli. | Hayır |
| Adım anahtarı (S1, S2…) | Adımın kısa kodu; bağımlılıklarda kullanılır. | Salt okunur. | S3 | — |
| Adım adı | Adımın adı. | Kısa ve açık. | Veri modeli tasarımı | Evet |
| **AI personel** | Adımı yürütecek personel. | **Personel atanmadı** veya havuzdaki AI personel ("Ad · Unvan"). | Orion Analist · İş Analisti | Başlamaya hazır için evet |
| Açıklama ("Ne yapılacak") | Adımın içeriği. | Serbest metin. | — | Hayır |
| Kabul ölçütü ("Tamam sayılma ölçütü") | Onaylayıcının bakacağı ölçüt. | Ölçülebilir yazın. | Tüm tablolar ilişki şemasıyla verilmiş olmalı. | Hayır |
| **Departman** | Adımın ait olduğu birim. | Metin. | Bilgi İşlem | Hayır |
| **Gereken unvan** | Adım için gereken uzmanlık. | Metin. | Yazılım Mimarı | Hayır |
| **Süre (iş günü)** | Tahmini süre; simülasyonda kullanılır. | 0,5–60 arası, 0,5'lik adımlarla. | 2 | Evet |
| **Öncelik** | Adımın önemi. | **Yüksek** / **Orta** / **Düşük** | Orta | Evet |
| **Kontrol personeli (çıktıyı değerlendirir)** | Çıktıyı onaya gitmeden önce değerlendiren ikinci AI personel. | **Kontrol yok (doğrudan onaya)** veya işi yapan dışındaki bir AI personel. | Orion Denetçi | Hayır |
| **Önce bitmesi gereken adımlar:** | Bağımlılıklar. | S1, S2… onay kutuları. | S1, S2 | Hayır |

**Akış şeması görünümü:** Adımlar kutular ve oklarla görünür. Ekrandaki ipucu: "Kartları sürükleyerek yerleştirin; bir kartın alt noktasından sonraki adımın üst noktasına çekerek "önce bitmesi gereken" bağlantısı kurun; bağlantıyı seçip Delete ile silin. Ayarlar için karta tıklayın." Kartta: anahtar, ad (adsızsa "Adsız adım"), personel veya "Personel atanmadı", "Kontrol: <ad>", "Onay: <ad veya Proje yöneticisi> · ret sınırı n" ya da "Onay gerekmez".

**"<Sn> · adım ayarları" kartı** ("İşi yapan, kontrol eden ve onaylayan; onay kuralları."):

| Alan | Ne işe yarar | Nasıl doldurulur / seçenekler | Örnek | Zorunlu |
|---|---|---|---|---|
| **Adım adı** | Adımın adı. | Metin. | Güvenlik testi | Evet |
| **Personel (işi yapan)** | Adımı yürüten AI personel. | Havuzdan seçin. | Orion Test Uzmanı | Başlamaya hazır için evet |
| **Kontrol personeli** | Çıktıyı önce değerlendiren AI personel. | İşi yapan dışında bir AI personel veya kontrol yok. | — | Hayır |
| **Onaylayıcı** | Çıktıyı onaylayacak kişi. | **Proje yöneticisi** veya şirketin bir insan kullanıcısı. | Zeynep Kaya | Hayır (boşsa proje yöneticisi) |
| **Ret sınırı (sonra karantina)** | Kaç revizyondan sonra adımın karantinaya alınacağı. | **1 ret** … **5 ret**; varsayılan 3. | 3 ret | Evet |
| **İnsan onayı gerekli (kapalıysa teslim/kontrolden sonra adım doğrudan tamamlanır)** | Adımın insan onayı isteyip istemediği. | Onay kutusu. | İşaretli | — |

> **Dikkat:** Onaylayıcı, ret sınırı ve insan onayı ayarları **yalnız Akış şeması görünümündeki adım ayarları kartında** bulunur. Liste görünümünde bu alanlar yoktur.

| Düğme | Ne yapar | Dikkat |
|---|---|---|
| **Gönder** (sohbet) | Mesajı Beyin AI'ya gönderir ("Yanıt hazırlanıyor…"). | Yanıt alınamazsa yazdığınız metin kutuya geri döner. |
| **Planı bu konuşmaya göre güncelle** | Sohbeti geri bildirim olarak kullanıp yeni plan önerir ("Güncelleniyor…"). | Kaydedilmemiş düzenleme varsa: **"Kaydedilmemiş düzenlemeleriniz yeni öneriyle değiştirilecek. Devam edilsin mi?"** |
| **Beyin AI plan önersin** / **Yeniden öner** | İsterlerden ve onaylı eklerden plan üretir ("Öneri hazırlanıyor…", "RECAi isterleri inceliyor; bu işlem bir iki dakika sürebilir."). Sonuç: **"Beyin AI n iş adımı önerdi."** | Aynı uyarı. Kredi harcar. |
| **Kaydet** | Plan taslağını kaydeder: **"Plan taslağı kaydedildi."** Plan onayı düşer; Taslak proje Planlama'ya geçer. | — |
| **Onayla ve iş adımlarına dönüştür** | Kaydedilmemiş değişiklikleri kaydeder, planı onaylar, adımları gerçek iş adımlarına çevirir, atanan AI personeli ekibe ekler: **"n iş adımı oluşturuldu; m adıma henüz personel atanmadı."** | **Planı onayla** penceresi: "Adımlar iş adımlarına dönüşür ve atanan AI personel ekibe eklenir. Daha önce onaylanmış ama başlamamış adımlar yeniden oluşturulur." (**Onayla** / **Vazgeç**) |
| **Liste** / **Akış şeması** | Görünümü değiştirir. | — |
| **Yukarı taşı** / **Aşağı taşı** / **Adımı sil** (simgeler) | Sırayı değiştirir / adımı siler. Silinen adım diğerlerinin bağımlılıklarından da çıkar. | Onay sormaz; **Kaydet**'e basmadan kalıcı olmaz. |
| **Adım ekle** | Boş bir adım (S<n>) ekler. | — |
| Akışta kart sürükleme, bağlantı çekme, bağlantıyı seçip Delete | Kart konumu / bağımlılık ekleme / silme. | Döngü engellenir: **"Bu bağlantı döngü oluşturur: bir adım kendisine dolaylı olarak bağlı olamaz."** |
| **AI personel işe al** (İşe alım önerileri) | **AI Personel İşe Al** sihirbazını açar (adımlar: **Departman**, **Unvan**, **RECAi ve Rol**, **Kimlik**; düğmeler **Geri**, **İleri**, **İşe Al**). Sonuç: **"Yeni personel havuza eklendi; adımlara atayabilirsiniz."** | **AI Personel İşe Alma** izni gerekir. Sihirbazın ayrıntısı Şirket Yönetimi Kılavuzu'ndadır. |

**Uyarı mesajları:** **"Önce projenin isterlerini yazın."** · **"Plan yalnızca taslak veya planlama aşamasında oluşturulabilir."** · **"Plan yalnızca planlama aşamasında onaylanabilir."** · **"Onaylanacak iş adımı yok."** · **"Başlamış iş adımları olan projede plan yeniden onaylanamaz."** · **"'<adım>' adımında yazışma var; mesaj kaydı silinemediği için plan …"** (yazışması olan adım varken plan yeniden onaylanamaz).

> **İpucu:** Başlamaya hazır projede planı değiştirmek için önce Hazırlık & Bildirim sekmesinde **Planlamaya geri al**'a basın.

> **Örnek:** Mehmet Demir **Beyin AI plan önersin**'e basar; Beyin AI beş adım önerir. Sohbette "Test ve kılavuz ayrı adımlar olsun, kılavuzu Can Öztürk onaylasın" yazar, **Planı bu konuşmaya göre güncelle**'ye basar. **Akış şeması**'nda "Kullanım kılavuzu" adımını seçip **Onaylayıcı**'yı Can Öztürk yapar, **Kaydet** ve **Onayla ve iş adımlarına dönüştür**'e basar.

### Ekip & Simülasyon sekmesi

[[EKRAN: wa-ekip-simulasyon | Ekip & Simülasyon sekmesi: Proje ekibi kartı ve personel ekleme alanı, Simülasyon kartı (istatistikler, risk notları, zaman çizelgesi) | Planı onaylanmış, Planlama durumundaki bir projeyi açın; "Ekip & Simülasyon" sekmesinde bir tarih seçip "Simüle et"e basın]]

**Bu ekran ne işe yarar?** Proje ekibini (insan ve AI) yönetir; iş günü takvimi, bağımlılıklar ve personel kapasitesiyle bitiş tarihi, süre ve kredi tahmini yapar.

**Kimler değiştirebilir?** Ekip yönetimini proje yöneticisi yapar; simülasyon yalnız proje başlamadan önce yapılır.

**Ekranın bölümleri:**

- **Proje ekibi** ("İnsan personel ve AI personel. AI personel plan onayında atanan adımlara göre eklenir."): her üyenin adı, rolü (**Proje yöneticisi** / **Ekip üyesi** / **AI personel**), e-postası ve **AI** / **İnsan** rozeti.
- **Simülasyon** ("İş günü takvimi, bağımlılıklar ve personel kapasitesiyle tarih, süre ve kredi tahmini."): **Başlangıç**, **Tahmini bitiş**, **Süre** (n iş günü), **Tahmini kredi**; risk notları (yoksa "Belirgin bir risk görülmedi."); **Zaman çizelgesi** (adım, personel veya "Atanmadı", çubuk üzerinde tarih ve kredi). Henüz yapılmadıysa: "Henüz simülasyon yapılmadı. Başlangıç tarihini seçip "Simüle et"e basın."

| Alan | Ne işe yarar | Nasıl doldurulur | Örnek | Zorunlu |
|---|---|---|---|---|
| Eklenecek personel ("Personel seçin…") | Ekibe yeni üye ekler. | Gruplar: **İnsan personel**, **AI personel**. Yalnız ekipte olmayan etkin personel listelenir. | Can Öztürk | — |
| **Başlangıç tarihi** | Simülasyonun başlangıcı. | Boşsa proje başlangıcı kullanılır. | 10.11.2026 | Hayır |

| Düğme | Ne yapar | Dikkat |
|---|---|---|
| **Ekle** | Seçilen kişiyi ekibe ekler: **"Ekibe eklendi."** Eklenen insan kullanıcı projeyi görmeye başlar. | — |
| **Ekipten çıkar** (çöp simgesi) | Üyeyi ekipten çıkarır. | **"<ad> ekipten çıkarılsın mı?"** Proje yöneticisinde bu düğme yoktur. |
| **Simüle et** | Simülasyon yapar, adım tarihlerini hesaplar ("Hesaplanıyor…"): **"Tahmini bitiş <tarih> (n iş günü)."** | — |
| **Bu tarihleri projeye uygula** | Simülasyon tarihlerini projenin hedef tarihlerine yazar: **"Simülasyon tarihleri projeye uygulandı."** | — |

**Mesajlar:** **"Simülasyon yalnızca proje başlamadan önce yapılabilir."** · İş adımı yoksa **"İş adımı yok"** — "Simülasyon için önce Beyin AI Planlama sekmesinde planı onaylayın." · **"Proje yöneticisi ekipten çıkarılamaz; önce başka bir yönetici atayın."** · **"Bu personele atanmış açık iş adımları var; önce başka birine atayın."** · **"İşten çıkarılmış AI personel projeye eklenemez."**

### Hazırlık & Bildirim sekmesi

[[EKRAN: wa-hazirlik-bildirim | Hazırlık & Bildirim sekmesi: Hazırlık kontrol listesi (✓/○ maddeler ve Başlamaya hazır yap düğmesi), Telegram bildirimleri kartı ve Bildirim tercihlerim kartı | Planı onaylanmış, tarihleri girilmiş bir projeyi açın; "Hazırlık & Bildirim" sekmesine basın]]

**Bu ekran ne işe yarar?** Başlamadan önceki kontrol listesini gösterir, projeyi hazır yapar ve başlatır. Ayrıca kişisel bildirim kanallarınızı (Telegram, e-posta) burada ayarlarsınız.

**Kimler görür / değiştirebilir?** Kontrol listesini herkes görür; hazır yapma ve başlatma yalnız proje yöneticisindedir. **Telegram bildirimleri** ve **Bildirim tercihlerim** kartları her kullanıcı için kişiseldir; uzman kullanıcı da kendi ayarını yapar. Bu ayarlar projeye değil size aittir; hangi projenin sekmesinden yaparsanız yapın tüm bildirimleriniz için geçerlidir.

**Ekranın bölümleri:**

1. **Hazırlık kontrol listesi** ("Başlamaya hazır olan projenin başlangıç günü gelince size e-posta ve Telegram bildirimi gönderilir."). Maddeler (✓ tamam, ○ eksik): **İsterler yazıldı**, **Plan onaylandı (n iş adımı)**, **Her iş adımına personel atandı**, **Simülasyon yapıldı** (zorunlu değil), **Tarihler belirlendi (<başlangıç> – <bitiş>)**. Hazır projede: "Proje <tarih> tarihinde başlamaya hazır. O gün hâlâ başlatılmamışsa proje yöneticisine hatırlatma gönderilir."
2. **Telegram bildirimleri** ("Proje başlangıç hatırlatmalarını Telegram'dan da alın.").
3. **Bildirim tercihlerim** ("Onay istekleri, revizyonlar, duran adımlar ve proje bitişi bu kanallardan gelir.").

| Alan | Ne işe yarar | Nasıl doldurulur | Örnek | Zorunlu |
|---|---|---|---|---|
| **E-posta (onay isteklerinde tek tıkla karar bağlantısı)** | Bildirimlerin e-postayla gelmesi. | Onay kutusu; değişince hemen kaydedilir: **"Bildirim tercihiniz kaydedildi."** | İşaretli | — |
| **Telegram (Onayla / Revizyon iste butonları)** | Bildirimlerin Telegram'dan gelmesi. | Aynı. Telegram hesabınız bağlı olmalı. | İşaretli | — |

| Düğme | Ne yapar | Dikkat |
|---|---|---|
| **Başlamaya hazır yap** | Projeyi Başlamaya hazır yapar. | Zorunlu dört madde ✓ olmadan pasiftir. |
| **Projeyi şimdi başlat** | Projeyi başlatır. | Onay penceresi açılır. |
| **Planlamaya geri al** | Başlamaya hazır projeyi Planlama'ya döndürür. | **"Proje yeniden planlamaya alınsın mı?"** |
| **Telegram hesabımı bağla** | Bağlantı kodu üretir: "Aşağıdaki bağlantıyı açın veya botta /start <kod> yazın. Bağlandıktan sonra durumu yenileyin." | — |
| **Telegram'da aç** | RECOrion botunu Telegram'da açar. | Telegram'da botu başlatın. |
| **Durumu yenile** | Bağlantı durumunu yeniler: **"Telegram hesabınız bağlı (<tarih>)."** | — |
| **Bağlantıyı kaldır** | Telegram bildirimlerini kapatır. | **"Telegram bildirimleri kapatılsın mı?"** |

Telegram kurulumda etkin değilse: **"Telegram bildirimleri bu kurulumda henüz etkin değil. Bildirimler e-posta ile gönderilir."**

> **Örnek:** Zeynep Kaya, onay isteklerini telefonundan almak ister. Ekibinde olduğu herhangi bir projenin **Hazırlık & Bildirim** sekmesinde **Telegram hesabımı bağla** → **Telegram'da aç** → Telegram'da botu başlatır → RECOrion'da **Durumu yenile**. "Telegram hesabınız bağlı" yazısını görünce **Telegram (Onayla / Revizyon iste butonları)** kutusunu işaretler.

### İş Akışı sekmesi

[[EKRAN: wa-is-akisi | İş Akışı sekmesi: üstte istatistikler ve canlı şerit, Liste görünümünde adım kartları (durum rozetleri, düğmeler), altta Akış geçmişi | Aktif bir projeyi açın (İş Akışı sekmesi seçili gelir); adımlardan biri "Onay bekliyor", biri "Çalışılıyor" durumunda olsun]]

**Bu ekran ne işe yarar?** Başlamış projenin adımlarını canlı izlersiniz. Çıktıları görür, insan adımlarını teslim eder, onaylar veya revizyon ister, karantina kararı verir, çıktıyı şirket sistemine aktarır ve silinemez akış geçmişini okursunuz.

**Ne zaman kullanırım?** Proje Aktif veya Duraklatıldı durumundayken her gün.

**Kimler görür / değiştirebilir?** Ekip görür. Onay kararını adımın onaylayıcısı (seçilmemişse proje yöneticisi) ve **İş Adımı Onaylama (Vekâleten)** / **Revizyon İsteme (Vekâleten)** izni olanlar verir. Karantina kararını ve aktarımı proje yöneticisi verir. İnsan adımını atanan kişi veya proje yöneticisi teslim eder.

**Ekranın bölümleri:**

1. **İstatistikler:** **Çalışılıyor**, **Onay bekliyor**, **Karantina**, **Tamamlandı** (n / toplam).
2. **Canlı şerit:** **Canlı** veya **Bağlanıyor…** ve o an RECAi'nin yaptığı iş ("<adım>: <düşünce>"); iş yoksa "Adımlar ilerledikçe bu ekran kendiliğinden güncellenir."
3. **Liste** / **Akış şeması** seçici. Proje duraklatıldıysa: "Proje duraklatıldı: süren adımlar devam eder, yeni adım açılmaz."
4. **Adım kartları:** sıra no, ad, durum rozeti; "Personel: <ad> (AI)", "Kontrol: <ad>", "Onaylayıcı: <ad>", "Ret: n / m", "Önce: <adımlar>", "Bitiş: <tarih>". AI çalışıyorsa "<ad> çalışıyor (geri bildirime göre düzeltiyor)…". Karantinadaysa "n kez reddedildi. Yeniden denemek ret sayacını sıfırlar; gerekirse önce Ekip sekmesinden başka personel ekleyin."
5. **Akış geçmişi** ("Silinemez kayıt: her teslim, onay, ret ve karar."): olay · adım · not · zaman · kişi.

Proje başlamadıysa: **"İş akışı henüz başlamadı"** — "Proje başlatıldığında iş adımları bağımlılık sırasına göre burada ilerler."

**Akış geçmişindeki olaylar:** **Proje akışı başladı**, **Adım başladı**, **Teslim edildi**, **Onaylandı**, **Revizyon istendi**, **Karantinaya alındı**, **Yeniden denemeye açıldı**, **Tamamlandı**, **İptal edildi**, **Tüm adımlar tamamlandı**, **AI personel çıktı üretti**, **Kontrolden geçti**, **Kontrol personeli düzeltme istedi**, **Kontrol yapılamadı (karar onaylayıcıda)**, **Adım durdu**, **Kod deposu açıldı**, **Kod deposuna commit edildi**, **Ana dala birleştirildi**, **Kod deposu işlemi yapılamadı**, **Kod deposu yansıtması kuruldu**, **Kod deposu yansıtması kaldırıldı**.

| Düğme | Kim / ne zaman | Ne yapar | Dikkat |
|---|---|---|---|
| **Çıktıyı gör (sürüm n)** | Çıktısı olan adım; ekip | Çıktı penceresini açar. | — |
| **Sisteme aktar** | Proje yöneticisi; adım Tamamlandı veya Onay bekliyor ve çıktı var | "<adım> · sisteme aktar" penceresini açar. | — |
| **Çıktıyı teslim et** / **AI çıktısını teslim et** | Adım Çalışılıyor veya Revizyonda ve personel insan (ya da atanmamış); atanan kişi veya proje yöneticisi | Teslim notu ister (isteğe bağlı), adımı onaya gönderir: **"Teslim edildi."** | **Çıktıyı teslim et** penceresi: "'<adım>' için teslim notu (isteğe bağlı):" |
| **Onayla** | Adım Onay bekliyor; karar yetkisi olan | Adımı tamamlar: **"Onaylandı."** | Onay penceresi yoktur; geri alınamaz. Kod deposu açıksa değişiklikler ana dala birleştirilir. |
| **Revizyon iste** | Aynı | Gerekçeyle revizyona gönderir: **"Revizyon istendi."** | **Revizyon iste** penceresi: "Gerekçe (personel buna göre düzeltecek):" Boş gerekçe gönderilmez. |
| **Yeniden dene** | Adım Karantinada; proje yöneticisi | Ret sayacını sıfırlayıp yeniden çalıştırır: **"Adım yeniden denemeye açıldı."** | — |
| **Adımı iptal et** | Adım Karantinada; proje yöneticisi | Adımı iptal eder: **"Adım iptal edildi."** | **"'<adım>' iptal edilsin mi? Bu adıma bağlı adımlar beklemeden devam eder."** Geri alınamaz. |

**Mesajlar:** **"İş akışı yalnızca aktif projelerde yürür."** · **"Bu adımı AI personel yürütüyor; çıktısını kendisi teslim eder."** · **"Bu iş adımını yalnızca onaylayıcısı onaylayabilir."** · **"Karantina kararını proje yöneticisi verir."** · **"Bu iş adımını yalnızca atanan personel veya proje yöneticisi teslim edebilir."**

#### Çıktı penceresi

[[EKRAN: wa-cikti-penceresi | "<adım> · çıktı" penceresi: biçimlendirilmiş çıktı metni ve altta Sürüm listesi | İş Akışı sekmesinde çıktısı olan bir adımda "Çıktıyı gör" düğmesine basın]]

Başlık "<adım> · çıktı". AI personelin ürettiği çıktı başlıklar, listeler ve tablolarla biçimlendirilmiş olarak gösterilir. Altta **Sürüm** listesi ("Sürüm n · tarih") vardır; revizyonlardan önceki sürümleri de açabilirsiniz.

#### Sisteme aktar penceresi

[[EKRAN: wa-sisteme-aktar | "<adım> · sisteme aktar" penceresi: Eşleme listesi, "Bu adım bitince otomatik öner" kutuları, "RECAi ile hazırla" düğmesi ve altta aktarım kartları | Proje yöneticisi olarak tamamlanmış bir adımda "Sisteme aktar" düğmesine basın; şirkette onaylı bir eşleme olmalı]]

**Ne işe yarar?** Adımın çıktısından şirket sistemine (ör. Odoo satış veya satın alma siparişi; satın alma için adım adım anlatım Şirket Yönetimi › Entegrasyonlar yardımında) gidecek kaydı RECAi'ye çıkartır ve önizleme hazırlar. Pencerede: "RECAi adımın çıktısından kayıtları çıkarır ve önizleme hazırlar. Hiçbir kayıt onaysız yazılmaz."

| Alan | Ne işe yarar | Nasıl doldurulur | Örnek | Zorunlu |
|---|---|---|---|---|
| **Eşleme** | Çıktının hangi sistem kaydına dönüşeceği. | Şirketin onaylı eşlemelerinden biri ("<eşleme> · <bağlantı>"). | Satış siparişi · Odoo | Evet |
| **Bu adım bitince otomatik öner** | İşaretli eşlemeler adım tamamlanınca kendiliğinden önerilir. | Onay kutuları. Sonuç: **"Bu adım bitince seçili aktarımlar önerilecek."** / **"Otomatik aktarım kapatıldı."** | — | Hayır |

| Düğme | Ne yapar | Dikkat |
|---|---|---|
| **RECAi ile hazırla** | Önizlemeyi hazırlar ("Başlatılıyor…", "RECAi çıktıyı okuyup kayıtları hazırlıyor…"). Sonuç aşağıda aktarım kartı olarak çıkar. | Kredi harcar. |
| **Kapat** | Pencereyi kapatır. | — |

Eşleme yoksa: **"Onaylı eşleme yok"** — "Şirket yöneticiniz Entegrasyonlar > Eşlemeler'den bir eşleme hazırlayıp onaylamalı."

#### Aktarım kartı

[[EKRAN: wa-aktarim-karti | Bir aktarım kartı: başlık ve durum rozeti, alt satırda bağlantı ve tutar bilgisi, "Hedefe gidecek değerler" tablosu ve Onayla ve aktar / Reddet / Düzelt düğmeleri | Sisteme aktar penceresinde "RECAi ile hazırla"ya basıp önizleme oluşturun; aynı kart Onaylarım'da ve Kapanış sekmesinde de görünür]]

Aktarım kartı İş Akışı'ndaki pencerede, Kapanış sekmesinde ve Onaylarım'da aynıdır.

- **Başlık:** "<nesne>: <kayıt adı>" ve durum rozeti.
- **Alt satır:** bağlantı · "mevcut kaydı günceller" veya "yeni kayıt açar" · tutar · tetikleyici ("elle", "adım bitince", "proje kapanınca") · tarih · çift onay gerekiyorsa "(x/y)".
- **Hedefe gidecek değerler** tablosu (**Hedef alan**, **Değer**), varsa hata/uyarı maddeleri, onay geçmişi ("✓/✗ ad · tarih · not").

**Durumlar:** **RECAi hazırlıyor**, **Düzeltme gerekli**, **Onay bekliyor**, **Kuyrukta**, **Yazılıyor**, **Aktarıldı**, **Hata**, **Reddedildi**, **Geri alındı**.

| Düğme | Ne yapar | Dikkat |
|---|---|---|
| **Onayla ve aktar** | Aktarımı onaylar ve kuyruğa alır: **"Onaylandı; aktarım kuyruğa alındı."** | Onaylayıcıya (Onaylarım'da) görünür. Çift onay kuralı varsa ikinci, farklı bir onaylayıcı gerekir. |
| **Reddet** | Aktarımı reddeder: **"Reddedildi; aktarım yapılmayacak."** | Gerekçe penceresi açılır. |
| **Düzelt** | "<nesne> · düzelt" penceresini açar: alanlar ve kalemler; **Vazgeç**, **Kaydet ve önizle**. Sonuç: **"Düzeltildi; önizleme yenilendi ve onaya gönderildi."** | Hâlâ eksik varsa: **"Hâlâ eksik veya hatalı alan var."** |
| **Geri al** | Aktarılmış kaydı geri alır: **"Geri alındı."** | Onay sorar: **"Kaydın eski değerleri geri yazılsın mı?"** veya **"Açılan kayıt arşivlensin (siparişte iptal edilsin) mi?"** |
| **Yeniden dene** | Hata almış aktarımı yineler. | — |
| Dış kayıt bağlantısı | Aktarılan kaydı şirket sisteminde açar. | — |

### Maliyet sekmesi

[[EKRAN: wa-maliyet | Maliyet sekmesi: üstte Gerçekleşen, Bütçe, Fark, Plan (öneri) istatistikleri; Bütçe kartı, Kategori dağılımı, İş adımları tablosu, Maliyet kalemleri ve LLM kırılımı | Proje yöneticisi olarak Aktif bir projeyi açın, "Maliyet" sekmesine basın]]

**Bu ekran ne işe yarar?** Projenin bütçesini ve gerçekleşen maliyetini (personel, RECAi kullanımı, diğer kalemler) TL ve KDV hariç izlersiniz; diğer giderleri belgesiyle kaydeder, Excel raporu alırsınız.

**Kimler görür?** Yalnız projenin yöneticisi ve **Tüm Projeleri Yönetme** izni olanlar. Diğer kullanıcılar bu sekmeyi görmez.

**Ekranın bölümleri:**

1. **İstatistikler:** **Gerçekleşen**, **Bütçe**, **Fark** (eksi ise kırmızı), **Plan (öneri)**.
   RECAi kullanımının TL karşılığı **harcanan kredi × paketinizin kredi birim fiyatı** ile hesaplanır (ör. PRO paketinde 39.900 TL ÷ 25.000 kredi ≈ 1,60 TL/kredi).
3. **AI ile insan karşılaştırması:** aynı işi insan personel yapsaydı tahmini süre ve maliyet ile AI'ın gerçek süresi ve maliyeti yan yana:
   **İnsanla tahmini süre** (planlanan iş günleri), **İnsan eşdeğeri maliyet**, **AI maliyeti** (kredi × birim fiyat), **Fark / tasarruf** ve adım tablosu
   (Adım · Ünvan · İnsan gün/TL · AI süre/kredi/TL). İnsan eşdeğeri = adımı yapacak ünvanın referans aylık brüt maaşı × işveren maliyet katsayısı (1,25)
   ÷ aylık iş günü (22) × planlanan gün. Referans maaşlar RECDx tarafından 2026 Türkiye maaş verilerine göre kıdem ve meslek ailesine
   (Yazılım/BT, Genel) göre belirlenir; ünvanı atanmamış adımda "genel varsayılan" kullanılır. Bu bir tahmindir, kişisel maaş bilgisi içermez.
2. **Uyarılar:** Ör. "n LLM çağrısının TL fiyatı tanımlı değil; token maliyeti bu çağrılar için 0 sayılıyor…", "Plan önerisi eksik olabilir: … insan personelin günlük maliyeti girilmemiş" veya "… AI adımının modeline fiyat tanımlı değil".
3. **Bütçe** ("TL, KDV hariç. Plan önerisi: planlanan personel maliyeti + planlanan token maliyeti.").
4. **Kategori dağılımı** (diğer maliyet kalemleri).
5. **İş adımları** ("Personel maliyeti gerçekleşen iş günü × günlük maliyet; tamamlanan adımda kayda geçer."): sütunlar **#**, **İş adımı**, **Personel**, **Gün** (Gerçekleşen / Sürüyor / Plan (tahmin)), **Personel** (tutar), **Token (LLM)**, **Diğer**, **Toplam**. Ayrıca **Proje geneli (Beyin AI planlama)** satırı (personel: RECAi).
6. **Maliyet kalemleri** ("Materyal, danışmanlık, eğitim, lisans, seyahat, donanım ve diğer giderler. Belgeler (fatura vb.) öğrenmeye girmez."). Boşsa **"Henüz maliyet kalemi yok."**
7. **LLM kırılımı** ("Model bazında çağrı, token ve TL maliyeti (çağrı anındaki fiyatla)."): **Model** (kullanılan RECAi kademesi), **Çağrı**, **Girdi token**, **Çıktı token**, **TL**, **Fiyatsız**, **Kredi**. Boşsa **"Henüz LLM çağrısı yok."**

| Alan | Ne işe yarar | Nasıl doldurulur | Örnek | Zorunlu |
|---|---|---|---|---|
| **Bütçe (₺)** | Projenin KDV hariç bütçesi. | Sayı. Kutuda plan önerisi soluk yazıyla görünür. | 150000 | Hayır |
| **Not** | Bütçeyle ilgili açıklama. | En çok 2000 karakter. | Kasım yönetim kurulu onaylı bütçe | Hayır |

| Düğme | Ne yapar | Dikkat |
|---|---|---|
| **Bütçeyi kaydet** | Bütçeyi kaydeder: **"Bütçe kaydedildi."** | — |
| **Plan önerisini kullan** | Öneriyi bütçe kutusuna yazar. | Ardından **Bütçeyi kaydet**'e basın. |
| **Excel** | Maliyet raporunu indirir. | — |
| **Kalem ekle** | Maliyet kalemi ekle penceresini açar. | — |
| Kalem satırında **Belgeyi indir** / **Düzenle** / **Sil** (simgeler) | Belgeyi indirir / kalemi düzenler / siler. | Sil: **"'<açıklama>' kalemi silinsin mi? (Belgesi de silinir.)"** |

#### Maliyet kalemi ekle / düzenle penceresi

[[EKRAN: wa-maliyet-kalemi | "Maliyet kalemi ekle" penceresi: Kategori, Tarih, Açıklama, Miktar, Birim, Birim fiyat, İş adımı ve Belge alanları; altta Tutar | Maliyet sekmesinde "Kalem ekle" düğmesine basın]]

| Alan | Ne işe yarar | Nasıl doldurulur / seçenekler | Örnek | Zorunlu |
|---|---|---|---|---|
| **Kategori** | Giderin türü. | **Materyal**, **Danışmanlık**, **Eğitim**, **Lisans / yazılım**, **Seyahat**, **Donanım**, **Diğer** | Donanım | Evet |
| **Tarih** | Giderin tarihi. | Varsayılan bugün. | 12.11.2026 | Evet |
| **Açıklama** | Giderin ne olduğu. | En az 2, en çok 500 karakter. | 10 adet el terminali | Evet |
| **Miktar** | Adet, gün, saat vb. | Sayı; varsayılan 1. | 10 | Evet |
| **Birim** | Miktarın birimi. | En çok 24 karakter (adet, gün, saat…). | adet | Hayır |
| **Birim fiyat (₺, KDV hariç)** | Birim başına tutar. | Sayı. | 4500 | Evet |
| **İş adımı (isteğe bağlı)** | Giderin hangi adıma ait olduğu. | **Proje geneli** veya bir adım. | 4. Pilot uygulama | Hayır |
| **Belge (fatura vb., isteğe bağlı)** | Gider belgesi. | **Belge seç** / **Değiştir (…)**. PDF, PNG, JPG, XLSX veya DOCX · en fazla 20 MB. Belgeler AI personele öğretilmez. | fatura.pdf | Hayır |

Altta **Tutar: <miktar × birim fiyat>** hesaplanır. Düğmeler: **Vazgeç**, **Kaydet** (düzenlemede sonuç **"Kalem güncellendi."**). Hatalar: **"Açıklama yazın."** · **"Birim fiyatı yazın."**

> **Dikkat:** Kapanmış projede bütçe ve kalemler salt okunurdur.

### Kod Deposu sekmesi

[[EKRAN: wa-kod-deposu | Kod Deposu sekmesi: Kod deposu kartı (RECOrion deposu açık rozeti), Şirket hesabına yansıtma kartı ve adım bazında commit kartları | Yazılım üreten Aktif bir projeyi açın, "Kod Deposu" sekmesine basın; depo açılmış ve en az bir adım commit edilmiş olsun]]

**Bu ekran ne işe yarar?** Yazılım üreten projelerde AI personelin kod çıktılarını RECOrion'un Git deposunda her adım için ayrı bir dala kaydetmesini (commit), adım onaylanınca ana dala (main) birleştirilmesini ve isteğe bağlı olarak şirketinizin GitHub/Gitea hesabına yansıtılmasını yönetir.

**Ne zaman kullanırım?** Proje kod üretiyorsa. Kod üretmeyen projelerde bu sekmeyi kullanmanız gerekmez.

**Kimler değiştirebilir?** Depoyu yalnız proje yöneticisi açar ve kapatır ("Depoyu proje yöneticisi açar."). Ekip dosyaları görür.

**Ekranın bölümleri:**

1. **Kod deposu** ("AI personel her iş adımında kendi dalına çalışır; adım onaylanınca değişiklikler ana dala (main) birleştirilir."): **RECOrion deposu açık** rozeti ve depo adresi ya da **Depo yok**. Açıklama: kod dosyaları AI çıktısında yolu belirtilmiş kod bloklarından oluşur; her adımın dokümanı ayrı bir klasöre yazılır. "Depo özeldir; dosyalar bu ekrandan görüntülenir".
2. **Şirket hesabına yansıtma** ("Ana depo RECOrion'da kalır; her commit şirketin GitHub/Gitea deposuna da gönderilir."): **Yansıtılıyor** / **Gönderim hatası** rozeti, "Son gönderim: …". Yansıtma yoksa: "Yansıtma yok. Proje yöneticisi şirketin GitHub/Gitea bağlantısıyla kurabilir."
3. **Görünüm seçimi:** **Kod Gezgini** (varsayılan) | **Adımlar**.
4. **Kod Gezgini** (VS Code benzeri, salt okuma): solda deponun dosya ağacı; ortada açılan dosyalar sekmeler hâlinde, renklendirilmiş kod, satır numarası ve küçük harita. Üstte **Dal** seçimi (ana dal veya bir iş adımının dalı, adım adıyla), **Depoda ara** kutusu (dosya adı ve kod içinde arar; sonuca tıklayınca dosya o satırda açılır) ve **Zip indir** (seçili dalın tüm dosyaları). Tema RECOrion'un açık/koyu seçimini izler.
5. **Adımlar:** "<n>. <adım>", "<dal> → main · istek #n", rozet **Onay bekliyor** / **Ana dala birleşti** / **Kapatıldı**, "Birleştirildi: …", dosya listesi (yol, "eklendi/değişti/silindi · +n"). Her dosyada **Farkı gör** (adım başlamadan önceki hâl ile adımın son hâli yan yana) ve **Kod Gezgini'nde aç** simgeleri vardır.

[[EKRAN: wa-kod-gezgini | Kod Deposu sekmesinde Kod Gezgini: solda dosya ağacı, ortada renklendirilmiş kod, üstte dal seçimi, arama ve Zip indir | Deposu açık bir projede "Kod Deposu" sekmesine basın; Kod Gezgini görünümünde bir dosya açın]]

> **İpucu:** Kod Gezgini salt okunurdur; kod yalnız AI personelin iş adımlarıyla değişir. Böylece hangi kodu hangi adımın yazdığı izlenebilir.

Commit yoksa: **"Henüz commit yok"** — "AI personel bir iş adımının çıktısını ürettiğinde değişiklikler burada görünür."

| Alan | Ne işe yarar | Nasıl doldurulur | Örnek | Zorunlu |
|---|---|---|---|---|
| **Bağlantı** | Yansıtma yapılacak Git hesabı. | Şirketin GitHub/Gitea bağlantılarından biri. | Örnek Lojistik GitHub | Evet (yansıtmada) |
| **Hedef depo** | Kodun gönderileceği depo. | "sahip/depo" biçiminde. "Depo hedef hesapta önceden açılmış ve boş olmalı." | orneklojistik/depo-sayim | Evet (yansıtmada) |

| Düğme | Ne yapar | Dikkat |
|---|---|---|
| **RECOrion deposunu aç** | Depoyu açar ("Açılıyor…"): **"Kod deposu açıldı; AI personelin kod çıktıları adım dallarına commit edilecek."** | — |
| **Kullanma** | Depo kullanımını kapatır: **"Kod deposu kullanımı kapatıldı."** | **"Kod deposu kullanılmasın mı? Depo ve geçmişi silinmez; yeni çıktılar artık commit edilmez."** |
| **Yansıt** | Yansıtmayı kurar ("Kuruluyor…"): **"Yansıtma kuruldu; her commit hedef depoya da gönderilir."** | — |
| **Kaldır** | Yansıtmayı kaldırır: **"Yansıtma kaldırıldı."** | **"Yansıtma kaldırılsın mı? Hedef depodaki kod silinmez; yeni commitler artık gönderilmez."** |
| **<yol> farkını gör** (simge, Adımlar) | **Fark: <yol>** penceresini açar: solda adım başlamadan önceki, sağda adımın son hâli. | Yeni eklenen dosyada sol taraf boştur. |
| **<yol> dosyasını Kod Gezgini'nde aç** (simge, Adımlar) | Dosyayı Kod Gezgini'nde, adımın dalında (birleştiyse ana dalda) açar. | — |
| **Zip indir** (Kod Gezgini) | Seçili dalın tüm dosyalarını zip olarak indirir. | 25 MB üstü depolar indirilemez. |
| **Ana dala birleştir** | Tamamlanmış ama birleşmemiş adımı ana dala birleştirir: **"Ana dala birleştirildi."** Kartta: "Bu adım onay gerektirmediği veya birleştirme yapılamadığı için bekliyor." | **"'<adım>' adımının değişiklikleri ana dala (main) birleştirilsin mi?"** |

**Mesajlar:** **"Kod deposu sunucusu bu kurulumda yapılandırılmamış. RECDx ile iletişime geçin."** · **"Şirketin GitHub/Gitea bağlantısı yok. Şirket yöneticisi Şirket Yönetimi › Entegrasyonlar ekranından ekler."**

### Testler sekmesi

[[EKRAN: wa-testler | Testler sekmesi: Kod Çalıştırma Ortamı kartı (Dal seçimi, Testleri çalıştır) ve bir test koşusu: Kaldı rozeti, "2 geçti · 1 kaldı", kalan testin adı ve mesajı | Deposu açık ve testleri olan bir projede "Testler" sekmesine basın; Testleri çalıştır'a basıp sonucun gelmesini bekleyin, Ayrıntı'yı açın]]

**Bu ekran ne işe yarar?** AI personelin yazdığı kodu RECOrion içinde gerçekten çalıştırır. Kod, her koşuda yeniden açılan yalıtılmış bir kapta (Kod Çalıştırma Ortamı) kurulur ve testleri çalışır; sonuç burada ve iş adımının çıktısında görünür. Kod RECOrion'un verilerine ve gizli bilgilerine erişemez; bağımlılıklar kurulduktan sonra internet bağlantısı kesilir; koşu bitince kap silinir.

**Ne zaman kullanırım?** Yazılım projelerinde. **AI Test Uzmanı** (unvanında "Test", "QA" veya "Kalite Güvence" geçen AI personel) deposu açık bir projede iş adımını teslim ettiğinde testler **kendiliğinden** çalışır: test uzmanı önce test kodunu yazar, sistem adımın dalını çalıştırır, sonuç ("Gerçek test koşusu") ve test uzmanının bu sonuca göre yazdığı değerlendirme ("Karar: Kabul" / "Karar: Düzeltme gerekli") adımın çıktısına ve görev sohbetine eklenir. Proje yöneticisi istediği dalda testleri elle de çalıştırabilir.

**Testler kalınca ne olur? (geri gönderme döngüsü)** Sistem iş akışına kendiliğinden iki adım ekler:
1. **Test düzeltmesi <n>: <kod adımı>**: kodu yazan AI personele (test adımından önceki, depoya kod yazmış son AI personel adımı) atanır; kalan testler ve hata mesajları açıklamasındadır. Test adımını onayladığınızda başlar.
2. **Yeniden test <n>: <test adımı>**: düzeltme onaylanınca test uzmanına açılır; testler yeniden çalışır.

Döngü en fazla **2 tur** döner. Sonrasında yeni adım açılmaz, çıktıda "karar proje yöneticisinde" yazar. Proje yöneticisine bildirim gider; İş Akışı geçmişinde **"Testler kaldı: düzeltme ve yeniden test adımı açıldı"** olayı görünür. İstemediğiniz düzeltme adımını iptal edebilirsiniz.

**Kimler görür / çalıştırır?** Projenin ekibi sonuçları görür. **Testleri çalıştır** düğmesini yalnız proje yöneticisi ve **Tüm Projeleri Yönetme** izni olanlar görür ("Testleri elle proje yöneticisi başlatır; AI Test Uzmanı'nın koşuları kendiliğinden yapılır.").

**Hangi testler çalışır?** Depoda kökte veya en fazla iki alt klasörde bulunan projeler:
- **Python** (requirements.txt veya pyproject.toml): bağımlılıklar kurulur, **pytest** çalışır.
- **JavaScript** (package.json): `npm install`, ardından package.json'daki **test** betiği (`npm test`).
- Kökte **scripts/recorion_test.sh** varsa o da çalışır.
Her aşamanın üst süresi 5 dakikadır.

**Ekranın bölümleri:**

1. **Kod Çalıştırma Ortamı** kartı: **Dal** seçimi (ana dal ve birleşmemiş adım dalları) ve **Testleri çalıştır**. Koşu sürerken düğme "Koşu sürüyor…" olur.
2. **Koşu kartları** (en yeni üstte): dal · commit, tarih, "AI Test Uzmanı adımı" veya "elle başlatıldı", sonuç rozeti ve "<n> geçti · <n> kaldı · <n> atlandı · <süre> sn". **Ayrıntı** ile her alt proje için sonuç, kalan testlerin adı ve hata mesajı, kurulum hatası ve **Test çıktısı** açılır.

| Rozet | Anlamı |
|---|---|
| **Çalışıyor** | Kod kuruluyor veya testler çalışıyor; ekran 5 saniyede bir yenilenir. |
| **Geçti** | Bütün testler geçti. |
| **Kaldı** | En az bir test kaldı, süre doldu veya bağımlılıklar kurulamadı. |
| **Test bulunamadı** | Depoda çalıştırılacak test yok. |
| **Çalıştırılamadı** | Dal bulunamadı veya çalıştırma ortamına ulaşılamadı (kartta nedeni yazar). |

**Mesajlar:** **"Test koşusu başladı; sonuç birkaç dakika içinde burada görünür."** · **"Bu projede süren bir test koşusu var; bitmesini bekleyin."** · **"Önce projenin kod deposunu açın."** · **"Kod çalıştırma ortamı bu kurulumda yapılandırılmamış; RECDx ile iletişime geçin."**

> **Örnek:** Diş kliniği CRM projesinde Yazılım Geliştirici (Backend) randevu modülünü yazar, adım onaylanınca kod ana dala birleşir. Test Uzmanı adımında AI, çakışan randevuları sınayan pytest testleri yazar; sistem testleri çalıştırır: "3 geçti · 1 kaldı — test_randevu_cakisma: çakışan randevu kabul edildi". Test uzmanı değerlendirmesinde hatanın uygulamada olduğunu yazar ve "Karar: Düzeltme gerekli" der. Sistem "Test düzeltmesi 1: Randevu modülü" adımını Yazılım Geliştirici'ye, ardından "Yeniden test 1" adımını test uzmanına açar; proje yöneticisi test adımını onaylayınca düzeltme başlar.

### RECSlip sekmesi

[[EKRAN: wa-recslip-sekmesi | RECSlip Case'inin RECSlip sekmesi: "Dönem AAAA-AA" takvim ve durum kartı, "Ayarlar ve onay kriterleri" kartı (genel ayarlar, Yönetici / yetkili AI onayı, Muhasebe AI onayı) ve "AI kararları" listesi | Muhasebeci (Case yöneticisi) olarak giriş yapın; Projeler'de "RECSlip masraf süreci <dönem>" Case'ini açın ve "RECSlip" sekmesine basın]]

**Bu ekran ne işe yarar?** RECSlip.App v2 aylık masraf sürecinin o ayki durumunu gösterir: takvim (kesim, geç fiş sonu, aktarım), yönetici ve muhasebe onay adımlarının sayıları, AI ile insan kararlarının uyumu, aktarım dosyasının durumu ve AI personelin tek tek verdiği kararlar. Case yöneticisi buradan sürecin ayarlarını ve AI'ın onay kriterlerini değiştirir.

**Ne zaman kullanırım?** Ay içinde sürecin nasıl gittiğine bakmak, ay sonu ve aktarım tarihlerini görmek, AI'ın neden bir fişi insana bıraktığını anlamak veya kriterleri sıkılaştırıp gevşetmek istediğinizde.

**Kimler görür / değiştirebilir?** Sekme yalnız RECSlip aylık Case'lerinde ("RECSlip masraf süreci <dönem>") görünür; Case'in ekibi görür. **Ayarlar ve onay kriterleri**ni yalnız Case yöneticisi (kurulumda seçilen muhasebeci) ve **Tüm Projeleri Yönetme** izni olanlar değiştirir. Diğerleri alanları gri (salt okunur) görür ve kartın alt başlığında "Yalnızca Case yöneticisi değiştirebilir." yazar.

> **İpucu:** RECSlip süreci Şirket Yönetimi › Otomasyonlar ekranındaki **RECSlip.App v2 aylık süreç** kartından kurulur. Kurulum ve ön koşullar Şirket Yönetimi Kılavuzu'nda anlatılır. Kurulduktan sonra her ay yeni Case kendiliğinden açılır.

**Ekranın bölümleri:**

**1. Dönem <AAAA-AA> — Takvim ve durum**

| Satır | Ne gösterir |
|---|---|
| **Ay sonu kesim** | Dönemin kapandığı an (varsayılan ayın son günü 18:00). Bu andan sonra açık fişler listelenir. |
| **Geç gelen fişler için son** | Önceki ayın fişlerinin hâlâ kabul edildiği son gün (varsayılan sonraki ayın 3'ü, 23:59). |
| **Aktarım dosyası** | Muhasebe aktarım dosyasının oluşturulacağı an (varsayılan sonraki ayın 5'i, 10:00). |
| **Yönetici adımları** | Bu dönemde yönetici ve ek onaylayıcı adımlarının durum sayıları (ör. "AI onayladı: 42 · İnsan kararı bekliyor: 3"). Hiç yoksa "karar yok". |
| **Muhasebe adımları** | Muhasebe onay adımlarının durum sayıları. |
| **AI–insan uyumu** | İnsanın karar verdiği fişlerde, insanın kararının AI önerisiyle ne kadar örtüştüğü (yüzde). Henüz insan kararı yoksa "henüz insan kararı yok". |
| **Aktarım** | Aktarım dosyasının adı · fiş sayısı · toplam tutar · durum rozeti (ve varsa hata). Henüz yoksa "henüz yok". |

Aktarım durum rozetinde sistem kodu görünür: **PENDING** (bekliyor / yeniden denenecek), **CREATED** (dosya oluşturuldu, Case'e eklendi), **POSTED** (muhasebe programına işlendi), **FAILED** (oluşturulamadı veya işlenmediği için iptal edildi).

**2. Ayarlar ve onay kriterleri** (alt başlık: "Sonraki ayın Case'i bu ayarlarla açılır." veya "Yalnızca Case yöneticisi değiştirebilir.")

Genel ayarlar:

| Alan | Ne işe yarar | Nasıl doldurulur / sınırlar | Varsayılan | Zorunlu |
|---|---|---|---|---|
| **Fiş ve onay takibi (dakika)** | RECOrion'un RECSlip'teki bekleyen onay adımlarına kaç dakikada bir bakacağı. Kısaltırsanız AI daha çabuk karar verir. | 5–1440 | 15 | Evet |
| **Onaya gönderilmemiş fiş hatırlatması (gün)** | Okunmuş ama onaya gönderilmemiş fişler için hatırlatma süresi ayarı. | 0–60 | 2 | Evet |
| **Kesim günü (-1: ayın son günü)** | Dönemin hangi gün kapanacağı. -1 her zaman ayın son günüdür. | -1 veya 1–28 | -1 | Evet |
| **Kesim saati** | Kesimin saati. | SS:DD | 18:00 | Evet |
| **Geç fiş toleransı (sonraki ayın günü)** | Önceki aya ait fişlerin sonraki ayın kaçına kadar bekleneceği. 0 yazarsanız tolerans yoktur. | 0–27 | 3 | Evet |
| **Aktarım günü (sonraki ay)** | Aktarım dosyasının sonraki ayın hangi günü oluşturulacağı. | 1–28 | 5 | Evet |
| **Aktarım saati** | Aktarım dosyasının saati. | SS:DD | 10:00 | Evet |
| **Tekrar sayısı** | Aktarım dosyası oluşturulamazsa kaç kez yeniden deneneceği; dosya muhasebe programına işlenmezse kaç kez hatırlatılacağı. | 0–10 | 3 | Evet |
| **Tekrar aralığı (saat)** | İki deneme veya iki hatırlatma arasındaki süre. | 1–168 | 24 | Evet |
| **İşlenmedi hatırlatması (gün)** | Aktarım dosyası oluştuktan kaç gün sonra "henüz muhasebe programına işlenmedi" hatırlatmasının başlayacağı. | 0–60 | 2 | Evet |

**Yönetici / yetkili AI onayı** (yönetici ve ek onaylayıcı adımlarında AI personelin kriterleri):

| Alan | Ne işe yarar | Seçenekler | Varsayılan | Zorunlu |
|---|---|---|---|---|
| **Tümünü AI onaylasın (eşikler aranmaz)** | İşaretliyse tutar, risk, hafta sonu ve aylık sınır bakılmaz; AI tüm fişleri onaylar. Mükerrer şüphesi kuralı yine geçerlidir. | Onay kutusu | Kapalı | — |
| **En yüksek fiş tutarı** | Bu tutarı aşan fiş insana gider. | Sayı | 2500 | Evet |
| **Çalışan başına aylık sınır** | Çalışanın o ayki fiş toplamı bunu aşarsa fiş insana gider. 0 sınır yok demektir. | Sayı | 15000 | Evet |
| **İzinli risk** | RECSlip'in fişe verdiği risk seviyesi bu listede yoksa fiş insana gider. | **Yok**, **Düşük**, **Yüksek** (birden çok seçilebilir) | Yok | — |
| **Hafta sonu harcaması insana** | Cumartesi veya pazar tarihli fişleri insana bırakır. | Onay kutusu | Açık | — |
| **Mükerrer şüphesi insana** | RECSlip'in "mükerrer olabilir" dediği fişleri insana bırakır. | Onay kutusu | Açık | — |

**Muhasebe AI onayı** (muhasebe adımlarında AI personelin kriterleri):

| Alan | Ne işe yarar | Seçenekler | Varsayılan | Zorunlu |
|---|---|---|---|---|
| **Tümünü AI onaylasın (eşikler aranmaz; düzeltmeler yine yapılır)** | İşaretliyse tutar, risk, güven ve KKEG eşiklerine bakılmaz; hesap düzeltmeleri yine yapılır. Dengesiz ön muhasebe, mükerrer şüphesi ve kalemsiz fiş yine insana gider. | Onay kutusu | Kapalı | — |
| **En yüksek fiş tutarı** | Bu tutarı aşan fiş insana gider. | Sayı | 5000 | Evet |
| **En düşük fiş güveni** | RECSlip'in fişi okurken verdiği güven puanı bunun altındaysa fiş insana gider. | 0–100 | 85 | Evet |
| **AI düzeltmesi için en düşük güven** | AI bir kalemin hesabını değiştirmek istediğinde güveni en az bu kadar olmalı; değilse karar insana kalır. | 0–100 | 90 | Evet |
| **İzinli risk** | Fişin risk seviyesi bu listede yoksa insana gider. | **Yok**, **Düşük**, **Yüksek** | Yok, Düşük | — |
| **Güvenli sayılan eşleşme kaynakları (diğerleri RECAi:Mergen ikinci görüşüne gider)** | Kalemin muhasebe hesabı bu kaynaklardan geldiyse AI doğru kabul eder; diğer kaynaklardan gelen kalemler için RECAi Mergen'den ikinci görüş alınır. | **Kural**, **Tedarikçi hafızası**, **Tam eşleşme**, **Onaylı hafıza**, **Elle (muhasebeci)** | Kural, Tedarikçi hafızası, Tam eşleşme, Onaylı hafıza | — |
| **KKEG'li fiş insana** | Kalemlerinden biri KKEG (kanunen kabul edilmeyen gider) işaretliyse fişi insana bırakır. | Onay kutusu | Açık | — |

| Düğme | Ne yapar | Dikkat |
|---|---|---|
| **Kaydet** | Ayarları kaydeder: **"RECSlip ayarları kaydedildi."** | Yalnız Case yöneticisinde görünür. Sınır dışı değerler en yakın izinli değere çekilir. Yeni kriterler bir sonraki takipten itibaren uygulanır; sonraki ayın Case'i bu ayarlarla açılır. |

**3. AI kararları** (alt başlık: "<n> adım"): AI personelin değerlendirdiği her onay adımı bir satırdır: fiş adı · tutar · rol (Yönetici / Ek onaylayıcı / Muhasebe) · onaylayıcının adı; altında gerekçe, varsa "düzeltme: <kalem> → <yeni hesap>" ve hata. Sağda durum rozeti. Boşsa "Henüz değerlendirilen onay adımı yok."

| Rozet | Anlamı |
|---|---|
| **AI onayladı** | Fiş kriterlere uydu; AI personel, onaylayıcının kendi anahtarıyla onayladı. |
| **İnsan kararı bekliyor** | Fiş kriter dışı; onaylayıcının Onaylarım ekranında bekliyor. |
| **İnsan onayladı** | Onaylayıcı Onaylarım'dan onayladı. |
| **İnsan reddetti** | Onaylayıcı Onaylarım'dan reddetti. |
| **Odoo'dan karar verildi** | Karar RECOrion yerine doğrudan RECSlip'te (Odoo'da) verildi. |
| **Hata** | Onay RECSlip'e yazılamadı (ör. anahtar geçersiz). Bir sonraki takipte yeniden denenir. |

**RECSlip Case'inin adımları:** Case açılınca plan hazır ve başlamış gelir. İş Akışı sekmesinde şu adımları görürsünüz:

| Adım | Ne olur | Kim yürütür |
|---|---|---|
| **S1 Fiş takibi ve AI onay yürütme** | Dönem kesimine kadar onay adımları izlenir; kişisel anahtarı tanımlı onaylayıcıların AI personeli kriterlere göre onaylar, kriter dışı fişler kişinin Onaylarım ekranına gerekçeyle düşer. | Sistem (Case yöneticisi adına) |
| **S2 Yönetici onayları** | Yönetici ve ek onaylayıcı adımları kapanır; bekleyenler not edilir. Geç fiş sonuna kadar sürer. | Sistem |
| **S3 Muhasebe onayları** | Muhasebe adımları, RECAi Mergen ikinci görüşü, AI düzeltmeleri ve uyum oranı not edilir. Geç fiş sonuna kadar sürer. | Sistem |
| **S4 Ay sonu kesim** | Kesim anında onaya gönderilmemiş ve onayda bekleyen fişler listelenir; onaya gönderilmemiş fiş varsa Case yöneticisine "çalışanlara hatırlatın" bildirimi gider. | Sistem |
| **S5 Aktarım dosyası** | Tamamlanan fişlerden şirketin aktarım tipine göre (Luka 1./2. sınıf, Logo 4 Web) dosya RECSlip'te oluşturulur ve Case'e eklenir. Oluşmazsa tekrar ayarlarına göre yeniden denenir. | Sistem (Case yöneticisinin anahtarıyla) |
| **S6 Muhasebe programına işleme** | Dosya muhasebe programına işlenir (şimdilik elle) ve RECSlip'te **Muhasebeye işlendi** işaretlenir. İşlenmezse hatırlatma gider; tekrar sayısı dolunca aktarım iptal edilir ve fişler sonraki ayın dosyasına devreder. | Muhasebeci (işaretleme), sistem (takip) |
| **S7 Kapanış raporu** | Dönem özeti: fiş sayıları, AI ve insan onayları, AI düzeltmeleri, uyum oranı, aktarım sonucu. | Kurulumda seçilen AI personel yazar; seçilen kişi (muhasebe müdürü) onaylar. |

> **İpucu:** S1–S6 adımlarını sistem, koşulu oluşunca kendisi teslim eder; sizin bu adımlarda bir düğmeye basmanız gerekmez. Size düşen iş: Onaylarım'daki fişlere karar vermek, aktarım dosyasını muhasebe programına işleyip RECSlip'te işaretlemek ve (onaylayıcıysanız) S7 kapanış raporunu onaylamak.

### Kapanış sekmesi

[[EKRAN: wa-kapanis | Kapanış sekmesi: Dış sistem kayıtları, Projeyi kapat (kapanış özeti, Projeyi tamamla, İptal et), Maliyet özeti ve Kurum Hafızasına aktar kartları | Tüm adımları tamamlanmış Aktif bir projeyi açın, "Kapanış" sekmesine basın]]

**Bu ekran ne işe yarar?** Projeyi tamamlar veya iptal edersiniz; kapanış özetini yazar, maliyet özetini görür, dış sisteme aktarılan kayıtları izler ve onaylı proje eklerini şirketin tüm AI personelinin kullanacağı Kurum Hafızasına aktarırsınız.

**Kimler değiştirebilir?** Proje yöneticisi ve **Tüm Projeleri Yönetme** izni olanlar. Kurum hafızasına aktarma için ayrıca **Kurum Hafızasına Ekleme ve Onaylama** izni gerekir.

**Ekranın bölümleri:**

1. **Dış sistem kayıtları** (proje Aktif, Duraklatıldı veya Tamamlandı iken; "Bu projenin çıktılarından şirket sistemlerine aktarılan kayıtlar (önizleme ve onayla)."): aktarım kartları, aktarılmış kayıtların bağlantıları ve (proje açıkken) **Proje tamamlanınca otomatik öner** kutuları. Yoksa "Henüz aktarım yok."
2. **Projeyi kapat** (alt başlık "Kapanış: <tarih>" ya da "Proje tamamlandığında ya da vazgeçildiğinde kapatın.").
3. **Maliyet özeti** (yalnız yönetici; "TL, KDV hariç. Ayrıntılar Maliyet sekmesinde."): **Gerçekleşen**, **Bütçe**, **Fark**, **Kredi**; "Personel … · Token (LLM) … · Diğer …".
4. **Kurum Hafızasına aktar** ("Seçilen onaylı proje ekleri şirketin tüm AI personelinin bilgisine eklenir.").

| Alan | Ne işe yarar | Nasıl doldurulur | Örnek | Zorunlu |
|---|---|---|---|---|
| **Kapanış özeti** | Projenin sonucu ve öğrenilenler. | "Ne teslim edildi, öğrenilenler, açık kalan konular…" Kapanınca salt okunur olur. | Prototip 3 depoda denendi; sayım süresi %40 kısaldı. | Hayır |
| Ek seçimi (her onaylı ek için onay kutusu) | Kurum hafızasına aktarılacak ekler. | İşaretleyin. Aktarılmışlarda **Aktarıldı** rozeti görünür. | Depo sayım prosedürü.pdf | — |
| **Proje tamamlanınca otomatik öner** | Kapanışta önerilecek aktarımlar. | Onay kutuları. | — | Hayır |

| Düğme | Ne yapar | Dikkat |
|---|---|---|
| **Projeyi tamamla** | Projeyi Tamamlandı yapar; kapanışta önerilecek aktarımlar onaya düşer. | **"Proje tamamlandı olarak kapatılsın mı?"** Geri alınamaz. |
| **İptal et** | Projeyi İptal edildi yapar; başlamamış adımlar da iptal edilir. | **"Proje iptal edilsin mi? Bu işlem geri alınamaz."** |
| **Excel raporu** | Maliyet raporunu indirir. | — |
| **Seçilenleri Kurum Hafızasına aktar (n)** | Seçilen ekleri şirket geneline taşır: **"n ek Kurum Hafızasına aktarıldı; artık şirketin tüm AI personeli yararlanır."** | Onay sormaz. |

**Mesajlar:** **"Aktarma için kurum hafızası onay yetkisi gerekir."** · **"Aktarılabilecek onaylı proje eki yok."**

> **Dikkat:** Tüm adımlar bitince proje kendiliğinden kapanmaz. Proje yöneticisine "… tüm iş adımları tamamlandı. Kapanış özetini yazıp projeyi kapatabilirsiniz." bildirimi gelir; kapatmayı siz yaparsınız. Açık kalan proje paketinizin eşzamanlı proje sınırından yer tutar.

## Onaylarım

[[EKRAN: wa-onaylarim | Onaylarım ekranı: üstte "RECSlip masraf fişleri" bölümü (bir fiş kartı, gerekçe, önerilen hesap düzeltmeleri, Onayla / Reddet), altında "Dış sisteme aktarımlar", "Araç işlemleri (yazma)" ve iş adımı listesi | Muhasebeci (Zeynep Kaya rolünde, kişisel Odoo anahtarı tanımlı) olarak giriş yapın; mod çubuğunda "Onaylarım"a basın. Ekranda en az bir RECSlip fişi ve bir iş adımı onayı bekliyor olsun]]

**Bu ekran ne işe yarar?** Tüm projelerde ve şirket sistemlerinde **sizin kararınızı** bekleyen işleri tek yerde toplar: RECSlip masraf fişleri, dış sisteme aktarımlar, AI personelin onay bekleyen yazma işlemleri, onay bekleyen iş adımları ve (proje yöneticisiyseniz) karantinadaki adımlar. Alt başlık: "Kararınızı bekleyen iş adımları. E-postadaki bağlantıdan veya Telegram butonlarından da karar verebilirsiniz."

**Ne zaman kullanırım?** Her gün; özellikle size bildirim geldiğinde.

**Kimler görür?** Herkes; ancak yalnız kendi kararını bekleyen işleri görür. Liste 15 saniyede bir kendiliğinden yenilenir.

**Ekranın bölümleri (yukarıdan aşağı):** Bir bölümde bekleyen iş yoksa o bölüm hiç görünmez.

1. **RECSlip masraf fişleri** — AI personelinizin kriter dışı bulduğu ve sizin kararınızı bekleyen fişler.
2. **Dış sisteme aktarımlar** — onayınızı bekleyen aktarım kartları.
3. **Araç işlemleri (yazma)** — AI personelin bir dış sistemde yapmak istediği işlemler.
4. **İş adımları** — onay bekleyen ve karantinadaki adımlar. Hiç yoksa **"Bekleyen karar yok"** — "Onayınızı bekleyen bir iş adımı olduğunda burada görünür."

### RECSlip masraf fişleri kartı

[[EKRAN: wa-onaylarim-recslip-fis | Onaylarım'daki tek bir RECSlip fiş kartının yakın görünümü: fiş adı, tutar, çalışan, "Muhasebe onayı" rozeti, AI gerekçesi, "Önerilen hesap düzeltmeleri" listesi, "Onaylarken düzeltmeleri uygula" kutusu, Onayla ve Reddet | Onaylarım ekranında hesap düzeltme önerisi olan bir muhasebe fişine yaklaşın]]

**Ne işe yarar?** RECSlip'te onayınıza gelen bir fiş, sizin adınıza çalışan AI personelin kriterlerine uymadıysa burada gerekçesiyle durur. Kararı siz verirsiniz; karar sizin kendi Odoo anahtarınızla RECSlip'e yazılır.

**Kartta neler yazar?**

| Bilgi | Anlamı | Örnek |
|---|---|---|
| Fiş adı · tutar · çalışan | Hangi fiş, ne kadar, kimin. | Akaryakıt alımı · 3.250,00 TRY · Ali Veli |
| Rol rozeti | Hangi onay adımında olduğunuz: **Yönetici onayı**, **Ek onaylayıcı onayı** veya **Muhasebe onayı**. | Muhasebe onayı |
| Gerekçe satırı | "<AI personel adı>: <gerekçeler>" (AI personel seçilmemişse "RECAi: …"). AI'ın fişi neden size bıraktığı. | Defne: Tutar 3.250,00 sınırı (2.500,00) aşıyor. Hafta sonu harcaması. |
| **Önerilen hesap düzeltmeleri:** | (Muhasebe fişlerinde) AI'ın kalem hesabını değiştirmeyi önerdiği satırlar: "'<kalem>': <eski hesap> → **<yeni hesap>** (güven N) <gerekçe>". | 'Benzin': 770.01 → **760.01** (güven 93) Satış aracına ait yakıt. |
| **Onaylarken düzeltmeleri uygula** | İşaretliyse onaylarken önerilen hesap düzeltmeleri de RECSlip'e yazılır. Varsayılan işaretli. Yalnız düzeltme önerisi varsa görünür. | İşaretli |

**Gerekçede görebileceğiniz ifadeler ve anlamları:**

| Gerekçe | Anlamı |
|---|---|
| "Tutar X sınırı (Y) aşıyor." | Fiş tutarı Case'teki **En yüksek fiş tutarı**nı aşıyor. |
| "Risk seviyesi: …" | RECSlip fişe izinli olmayan bir risk seviyesi vermiş (notu parantez içinde). |
| "Hafta sonu harcaması." | Fiş cumartesi veya pazar tarihli. |
| "Mükerrer şüphesi var." | RECSlip aynı fişin daha önce yüklenmiş olabileceğini düşünüyor. |
| "Çalışanın bu ayki toplamı X sınırı (Y) aşıyor." | Çalışanın aylık fiş toplamı sınırı geçti. |
| "Kategori (…) izinli listede değil." | Fişin masraf kategorisi izinli kategorilerde yok. |
| "Ön muhasebe özeti dengede değil." | Fişin borç-alacak özeti tutmuyor. |
| "Fişte kalem yok." | Fişin satırı yok. |
| "Fiş güveni N (en az M)." | RECSlip fişi okurken yeterince emin olamamış. |
| "Belge türü (…) insan kontrolü istiyor." | Belge fiş/fatura değil veya yurt dışı belgesi. |
| "KKEG (gider değil) işaretli kalem var." | Kanunen kabul edilmeyen gider kalemi var. |
| "'<kalem>': RECAi:Mergen farklı hesap öneriyor (…, güven N); insan kararı gerekli." | İkinci görüş farklı hesap önerdi ama güveni düzeltme eşiğinin altında. |
| "'<kalem>': RECAi:Mergen emin değil." / "'<kalem>': hesap aynı ama güven düşük (N)." | İkinci görüş net değil. |
| "N kalemin hesabı onaylı kaynaktan gelmiyor." | Hesap güvenli bir kaynaktan gelmedi ve ikinci görüş alınmadı. |
| "RECAi:Mergen ikinci görüşü alınamadı (…)." | İkinci görüş o an alınamadı; karar size bırakıldı. |
| "Fiş okunamadı: …" | RECSlip'ten fiş bilgisi okunamadı. |

| Düğme | Ne yapar | Dikkat |
|---|---|---|
| **Onayla** | Fişi sizin adınıza RECSlip'te onaylar; **Onaylarken düzeltmeleri uygula** işaretliyse önerilen hesapları da yazar. Sonuç: **"Fiş onaylandı (RECSlip)."** | Onay penceresi yoktur. Karar RECSlip'te sizin adınıza kaydedilir (AI onayı olarak işaretlenmez). |
| **Reddet** | **Fişi reddet** penceresini açar: "Red gerekçesi (çalışana ve RECSlip geçmişine yazılır):". Sonuç: **"Fiş reddedildi (RECSlip)."** | Gerekçe zorunludur; boşsa **"Red gerekçesi yazın."** |

**Hata mesajları:**

| Mesaj | Ne demek, ne yapmalı |
|---|---|
| **"Bu fiş artık karar beklemiyor."** | Fişe başka yerden (ör. doğrudan RECSlip'ten) karar verilmiş. Liste yenilenince kart kaybolur. |
| **"Bu fişin onaylayıcısı siz değilsiniz."** | Fiş başka bir onaylayıcıya ait. |
| **"Odoo anahtarınız geçersiz veya süresi dolmuş; Bağlantılarım'dan yenileyin."** | Bağlantılarım › Şirket sistemlerindeki anahtarlarım'dan anahtarınızı yenileyin, sonra yeniden deneyin. |
| **"Odoo: …"** | RECSlip işlemi reddetti (ör. yetkiniz yok, fiş kilitli). Mesajı okuyun; gerekirse RECSlip'te kontrol edin. |

> **Örnek:** Zeynep Kaya Onaylarım'ı açar. "Akaryakıt alımı · 3.250,00 TRY · Ali Veli · Muhasebe onayı" kartında gerekçe olarak "Defne: Fiş güveni 78 (en az 85)." yazar; altında "Önerilen hesap düzeltmeleri: 'Benzin': 770.01 → 760.01 (güven 93)" önerisi vardır. Zeynep Hanım fişin görselini RECSlip'te kontrol eder, öneriyi doğru bulur ve **Onaylarken düzeltmeleri uygula** işaretliyken **Onayla**'ya basar. Fiş RECSlip'te Zeynep Hanım'ın adıyla onaylanır, hesap düzeltilir; RECSlip sekmesinde bu karar "İnsan onayladı" olarak görünür.

### Dış sisteme aktarımlar

Her satır bir **aktarım kartı**dır (bkz. İş Akışı › Aktarım kartı). Burada kartta **Onayla ve aktar** ve **Reddet** düğmeleri bulunur.

| Düğme | Ne yapar | Dikkat |
|---|---|---|
| **Onayla ve aktar** | Aktarımı onaylar ve kuyruğa alır: **"Onaylandı; aktarım kuyruğa alındı."** | Önce **Hedefe gidecek değerler** tablosunu kontrol edin. Çift onay kuralı varsa ikinci, farklı bir onaylayıcı da onaylamalıdır. |
| **Reddet** | Aktarımı reddeder: **"Reddedildi; aktarım yapılmayacak."** | Gerekçe penceresi açılır. |

### Araç işlemleri (yazma)

Her satır: "<AI personel> · <bağlantı> · <işlem adı>", altında işlemin parametrelerinin ilk 160 karakteri (üzerine gelince tamamı) ve zaman; **Onay bekliyor** rozeti.

| Düğme | Ne yapar | Dikkat |
|---|---|---|
| **Onayla ve çalıştır** | AI personelin istediği yazma işlemini şirket sisteminde çalıştırır: **"Onaylandı ve çalıştırıldı."** Çalışmazsa hata mesajı çıkar. | Onay penceresi yoktur; işlem dış sistemde hemen yapılır. Parametreleri okumadan onaylamayın. |
| **Reddet** | İşlemi reddeder: **"Reddedildi."** | **Reddet** penceresi: "Ret gerekçesi (isteğe bağlı):" |

### İş adımları

Her satır: adım adı; "<proje> · <personel> · teslim <tarih> · ret n"; rozet **Onay bekliyor** veya **Karantinada**.

| Düğme | Ne yapar | Dikkat |
|---|---|---|
| **İncele** | İlgili proje ekranını açar (Aktif projede İş Akışı sekmesiyle). Kararı orada **Çıktıyı gör** → **Onayla** / **Revizyon iste** ile verirsiniz. | Karantinadaki adım için **Yeniden dene** / **Adımı iptal et** yine İş Akışı'ndadır. |

**Sık sorulan sorular**

- **Onaylarım'daki sayı ile ekrandaki kart sayısı neden farklı?** Mod çubuğundaki sayı iş adımlarını ve araç işlemlerini sayar; RECSlip fişleri ve aktarımlar Onaylarım'ı açınca sayıya eklenir.
- **E-postadaki bağlantıdan da karar verebilir miyim?** İş adımları için evet (Onay bağlantısı sayfası). RECSlip fişleri için gelen bildirim sizi RECOrion'a yönlendirir; kararı Onaylarım'dan verirsiniz.
- **Bir karar verdim, geri alabilir miyim?** Hayır. İş adımında yanlışlıkla onay verdiyseniz proje yöneticinizle konuşun; RECSlip'te verilen kararlar için RECSlip'in kendi işlemlerini kullanın.

## Çalışma Alanı

[[EKRAN: wa-calisma-alani | Üç bölmeli Çalışma Alanı: solda Proje & Görevler (ilerleme, sohbet görünümü, iş adımları, ekip), ortada görev sohbeti (AI yanıtı, düşünce süreci, hafıza kaynakları), sağda Kalite Kapısı & Kurum Hafızası | Uzman kullanıcı (Can Öztürk) olarak giriş yapın; mod çubuğunda "Çalışma Alanı"na basın, solda Çalışılıyor durumundaki bir adımı seçin]]

**Bu ekran ne işe yarar?** Proje yöneticisinin ve uzmanların her gün kullandığı görev sohbeti ekranıdır. Bir iş adımını seçer, o adımın AI personeliyle konuşur, dosya ekler, çıktıyı görür, kalite kapısında karar verir ve kurum hafızasını yönetirsiniz.

**Ne zaman kullanırım?** AI personele talimat vermek, soru sormak, kendi adımınızı teslim etmek veya hafızaya giren bilgileri onaylamak istediğinizde.

**Kimler görür?** Herkes; yalnız ekibinde olduğu projeleri seçebilir. Proje ekranındaki **Çalışma alanında aç** düğmesi de bu ekranı o projeyle açar. Adres çubuğundaki bağlantıyı ekip arkadaşlarınıza gönderebilirsiniz.

**Ekranın bölümleri:** Üç bölme. Tablet ve telefonda üstte bölme seçici: **Proje & Görevler**, **Sohbet**, **Çıktı & Hafıza**.

### Sol bölme — Proje & Görevler

[[EKRAN: wa-sol-bolme | Çalışma Alanı sol bölmesi: proje seçici, İlerleme, Sohbet görünümü düğmeleri, İş adımları listesi ve Yeni adım düğmesi, Proje ekibi | Çalışma Alanı'nda sol bölmeyi alın; telefonda "Proje & Görevler"e dokunun]]

| Bölüm | Ne gösterir / ne yapar |
|---|---|
| Proje seçici | Birden fazla projeniz varsa "<proje> · <durum>" seçenekleriyle liste; yoksa proje adı veya "Henüz proje yok". Altında tür · kısa kod · durum rozeti. |
| **İlerleme** | "n / m adım tamamlandı", ilerleme çubuğu, "Çalışılıyor: n", "Onay bekliyor: n", "Karantina: n". |
| **Sohbet görünümü** | **Tüm ekip** (adımın tüm mesajları), **Benim** (yalnız sizin mesajlarınız), **Ajanlar arası** (projedeki AI personellerin kendi aralarındaki konuşmaları). |
| **İş adımları (n)** | Adım satırları: "<sıra>. <ad>", durum rozeti, personel (AI/insan simgesi) veya "Atanmadı", "· AI çalışıyor", "· sürüm n". Bir satıra tıklayınca sohbet o adıma geçer. Boşsa: "Bu projede henüz iş adımı yok. Plan Projeler ekranında onaylanınca adımlar burada görünür." |
| **Yeni adım** | Yeni İş Akışı Görevi Oluştur penceresini açar. Yalnız proje yöneticisinde ve proje Taslak, Planlama, Başlamaya hazır, Aktif veya Duraklatıldı iken görünür. |
| **Proje ekibi (n)** | Üyelerin adı ve rolü (**Proje yöneticisi**, **Ekip üyesi**, **AI personel**). |

#### Yeni İş Akışı Görevi Oluştur penceresi

[[EKRAN: wa-yeni-gorev | "Yeni İş Akışı Görevi Oluştur" penceresi: Görev Başlığı, Açıklama / İster Detayı, Atanan AI Personeli, Öncelik ve Görevi Başlat düğmesi | Proje yöneticisi olarak Çalışma Alanı'nda sol bölmedeki "Yeni adım" düğmesine basın]]

**Ne işe yarar?** Plan dışında projeye ek bir iş adımı ekler. Adım "Sırada" durumunda listeye girer.

| Alan | Ne işe yarar | Nasıl doldurulur / seçenekler | Örnek | Zorunlu |
|---|---|---|---|---|
| **Görev Başlığı** | Adımın adı. | Kısa ve açık. | Pilot depo eğitimi sunumu | Evet |
| **Açıklama / İster Detayı** | Ne yapılacağı ve kabul ölçütü. | "Görevin teknik isterlerini ve kabul kriterlerini yazın..." | 10 slaytlık eğitim sunumu, ekran görüntüleriyle. | Hayır |
| **Atanan AI Personeli** | Adımı yürütecek AI personel. | "<ad> (<rol>)" listesi; ilk AI personel seçili gelir. | Orion Eğitmen | Hayır |
| **Öncelik** | Adımın önemi. | **HIGH (Yüksek)**, **MEDIUM (Normal)**, **LOW (Düşük)**; varsayılan Yüksek. | MEDIUM (Normal) | Evet |

| Düğme | Ne yapar | Dikkat |
|---|---|---|
| **İptal** / kapat (X) | Pencereyi kapatır. | — |
| **Görevi Başlat** | Adımı ekler. | Bağımlılık, onaylayıcı ve kontrol personeli bu pencerede seçilmez; bunlar gerekiyorsa adımı Beyin AI Planlama'da plana ekleyin. Hata olursa: "Görev oluşturulamadı: …" |

### Orta bölme — Sohbet

[[EKRAN: wa-sohbet | Çalışma Alanı orta bölmesi: üstte adım adı, personel rozeti, Canlı göstergesi ve "RECAi: <kademe>"; ortada mesajlar, açılmış "Düşünce Süreci" ve "2 Kademeli Kolektif Hafıza Kaynakları"; altta mesaj kutusu, Özel mesaj kutusu, ataç ve Gönder | Çalışma Alanı'nda bir adım seçip AI personele bir soru gönderin ve yanıtın düşünce sürecini açın]]

**Üst kısım:** Adım adı (seçili değilse "Lütfen sol panelden bir görev seçin"), atanan personel rozeti (yoksa "Atanmadı"), **Canlı** / **Bağlanıyor…** göstergesi ("Canlı: yeni mesajlar ve AI adımları anında görünür"), "Durum: <durum> · Onaylayıcı: <ad> · Yanıtlar proje ekleri, personel bilgisi ve kurum hafızasıyla verilir". Adımı AI personel yürütüyorsa sağda **RECAi: <kademe>** yazar; kademe sohbetten değiştirilmez ("Model, AI personelin ayarlarından Şirket Yönetimi'nde değiştirilir.").

**Mesaj akışı:**

- Boşken: "RECOrion Otonom Çalışma Alanı — Bu görevde atanan AI personeli ile mesajlaşmaya başlayabilirsiniz…"
- Sizin mesajınız "<ad> (siz)" başlığıyla; AI yanıtı personel adıyla (veya "RECAi") ve biçimlendirilmiş metinle gelir.
- **🤖 Ajanlar Arası Müzakere** başlıklı mesajlar AI personellerin birbirine yazdıklarıdır.
- **Yalnızca siz görüyorsunuz** rozeti: özel mesaj.
- **Düşünce Süreci (Thought Process)** açılır bölümü: AI'ın yanıta nasıl vardığı.
- Ek çipleri: tıklayınca dosya iner ("<ad> dosyasını indir").
- **2 Kademeli Kolektif Hafıza Kaynakları:** yanıtın dayandığı bilgiler ("[kapsam]: alıntı"); kapsam proje ekleri, AI personelin kendi bilgisi veya kurum hafızası olabilir.
- Canlı düşünce balonu: RECAi'nin o an yaptığı iş veya "Mesaj gönderiliyor…".

| Alan | Ne işe yarar | Nasıl doldurulur | Örnek | Zorunlu |
|---|---|---|---|---|
| Mesaj kutusu ("<adım> hakkında AI personeline talimat verin...") | AI personele talimat veya soru. | Enter gönderir, Shift+Enter yeni satır. Gönderilemezse yazdığınız metin kaybolmaz. | Rapora bölge kırılımını da ekle. | Evet |
| **Özel mesaj (soru ve yanıtı yalnızca siz görürsünüz)** | Soruyu ve yanıtı ekipten gizler. | Onay kutusu. | — | Hayır |
| **Dosya veya görsel ekle** (ataç simgesi) | Mesaja dosya ekler. Dosya Proje Eklerine de yüklenir; AI o mesajda metnini okur, yönetici onaylarsa kalıcı öğrenilir. | Bir mesaja en fazla 5 dosya. Bekleyen ekler çip olarak görünür; "<ad> ekini kaldır" ile çıkarılır. | sayim_formu.xlsx | Hayır |

| Düğme | Ne yapar | Dikkat |
|---|---|---|
| **Gönder** | Mesajı gönderir. | Metin yoksa, dosya yüklenirken veya adım seçili değilken pasiftir. |

Proje kapanmışsa yazma alanı yerine: "Proje iptal edildi/tamamlandı; yazışma kaydı salt okunurdur ve değiştirilemez."

**Mesajlar:** **"Kapanmış projeye mesaj yazılamaz; yazışma kaydı salt okunurdur."** · **"Bir mesaja en fazla 5 dosya eklenebilir."** · **"Ek bulunamadı veya bu projenin eki değil."** · **"Mesaj gönderilemedi: …"**

### Sağ bölme — Kalite Kapısı & Kurum Hafızası

[[EKRAN: wa-sag-bolme | Çalışma Alanı sağ bölmesi: Görev kalite kapısı (rozet, Onayla & İlerlet, Revizyon İste), Adımın çıktısı (Çıktıyı gör) ve Hafıza (Onaylı / Onay bekliyor / Reddedilen sekmeleri, bilgi kartları) | Onaylayıcı olarak Çalışma Alanı'nda "Onay bekliyor" durumundaki bir adımı seçin; telefonda "Çıktı & Hafıza"ya dokunun]]

**1. Görev kalite kapısı:** Adımın durum rozeti (**Onay bekliyor**, **Onaylandı**, **Revizyonda**, **Karantinada**, **Çalışılıyor**, **İptal**, **Sırada**); "Çıktı önce kontrol personeli <ad> tarafından değerlendirilir." ve "Bu adım insan onayı gerektirmez." ya da "Onaylayıcı: <ad / proje yöneticisi>."

**2. Adımın çıktısı:** çıktı adı, "Sürüm n · tarih", **Çıktıyı gör** / **Çıktıyı gör (sürümler)**. Yoksa "Henüz çıktı yok. AI personel çalışıyor; çıktı hazır olunca burada görünür." veya "Bir iş adımı seçin."

**3. Hafıza:** **Onaylı**, **Onay bekliyor (n)**, **Reddedilen** sekmeleri (son ikisi yalnız **Kurum Hafızasına Ekleme ve Onaylama** izni olanlarda). Kartta: **Kurum hafızası** rozeti veya AI personel adı (o personele özel bilgi), zaman, içerik, "Onaylayan/Karar: <ad> · tarih · "not"". Boş metinler: "Henüz onaylı bilgi yok." · "Onay bekleyen bilgi yok." · "Reddedilen veya geri alınan bilgi yok."

| Düğme | Kim / ne zaman | Ne yapar | Dikkat |
|---|---|---|---|
| **Onayla & İlerlet** | Adım Onay bekliyor; karar yetkisi olan | Adımı onaylar: **"Onaylandı; iş akışı sonraki adıma geçiyor."** | Onay penceresi yoktur; geri alınamaz. |
| **Revizyon İste** | Aynı | "Revizyon gerekçesi (personel buna göre düzeltecek):" penceresi; sonuç **"Revizyon istendi."** | Boş gerekçe gönderilmez. |
| (metin) "Karar <onaylayıcı> tarafından verilecek." | Karar yetkiniz yoksa | — | — |
| **Çıktıyı teslim et** | İnsan personelin çalıştığı adım; atanan kişi veya proje yöneticisi | "Teslim notu (isteğe bağlı):" → **"Teslim edildi; onaya gönderiliyor."** | — |
| (metin) "Bu adım n kez reddedildi. Kararı proje yöneticisi Projeler > İş Akışı ekranından verir." | Adım Karantinada | — | — |
| **Çıktıyı gör** | Çıktı varsa | Çıktı penceresini açar. | — |
| **Onayla** (hafıza) | Onay bekliyor sekmesi; **Kurum Hafızasına Ekleme ve Onaylama** izni | Bilgiyi Kurum Hafızasına ekler: **"Bilgi Kurum Hafızasına eklendi; tüm AI personel kullanır."** | **Kurum hafızasına ekle** penceresi: "Bu bilgi şirketin tüm AI personelinin bilgisine eklenecek: …" |
| **Reddet** (hafıza) | Aynı | Bilgiyi reddeder: **"Bilgi reddedildi; öğrenilmeyecek."** | **Bilgiyi reddet** penceresi; gerekçe isteğe bağlı. |
| **Kurum hafızasına taşı** | Onaylı sekmesinde AI personele özel bilgi; aynı izin | Bilgiyi o personelin hafızasından şirket geneline taşır. | **Kurum hafızasına ekle** penceresi. |
| **Geri al** | Onaylı sekmesi; **Kurum Hafızasından Geri Alma** izni | AI personel bilgiyi artık kullanmaz: **"Bilgi geri alındı; AI personel artık kullanmayacak."** | **Bilgiyi geri al** penceresi; gerekçe zorunlu (**"Geri alma gerekçesini yazın."**). |

> **Örnek:** Can Öztürk "Kullanım kılavuzu" adımının onaylayıcısıdır. Çalışma Alanı'nda adımı seçer, sağda **Çıktıyı gör** ile kılavuzu okur. Ekran görüntüleri eksik olduğu için **Revizyon İste**'ye basıp "Her adım için ekran görüntüsü ekleyin" yazar. AI personel düzeltilmiş sürümü teslim edince **Onayla & İlerlet** ile onaylar.

> **İpucu:** AI personelin yanıtında yanlış bir bilgiye dayandığını görürseniz yanıtın altındaki **2 Kademeli Kolektif Hafıza Kaynakları**'na bakın. Kaynak kurum hafızasındaysa, yetkiniz varsa **Hafıza › Onaylı**'dan **Geri al** ile kaldırın.

## Bağlantılarım

[[EKRAN: wa-baglantilarim | Bağlantılarım ekranı: üstte "Kişisel erişim anahtarları" kartı (MCP sunucu adresi, anahtar listesi, Anahtar oluştur), altında "Şirket sistemlerindeki anahtarlarım" kartı (Odoo anahtarı satırı, durum rozeti, Dene / Düzenle / Sil, Anahtar ekle) | Muhasebeci (Zeynep Kaya) olarak giriş yapın; mod çubuğunda "Bağlantılarım"a basın. Şirkette RECSlip v2 kurulu bir Odoo bağlantısı ve kişinin bir anahtarı olsun]]

**Bu ekran ne işe yarar?** Size özel iki tür anahtarı yönetirsiniz:

1. **Kişisel erişim anahtarları:** Claude, Cursor veya şirketinizin kendi sisteminden RECOrion'a bağlanmak için. Ekrandaki açıklama: "Claude, Cursor veya şirketinizin kendi sisteminden RECOrion'a MCP ile bağlanın: proje durumunu sorun, proje/Case açın, plan taslağına adım ekleyin. Anahtar sizin yetkilerinizle çalışır; onaylar yine RECOrion'da verilir." (MCP, yapay zeka araçlarının başka sistemlere bağlanmak için kullandığı ortak bağlantı yöntemidir.)
2. **Şirket sistemlerindeki anahtarlarım:** AI personelinizin şirketinizin sisteminde (bugün için Odoo; ör. RECSlip'te masraf onayı) **sizin adınıza** işlem yapabilmesi için kendi kullanıcınızın API anahtarı.

**Kimler görür?** Herkes. Her kullanıcı yalnız kendi anahtarlarını görür. Şirket yöneticisi ve entegrasyon yöneticisi, Şirket Yönetimi'nde kimin anahtarı olduğunu ve bitiş tarihlerini görebilir; anahtarın kendisini kimse göremez. KVKK gereği RECDx personeli müşteri sistemine kişisel anahtar tanımlayamaz.

> **Dikkat:** Telegram bağlama ve bildirim tercihleri bu ekranda değildir. Onlar herhangi bir projenin **Hazırlık & Bildirim** sekmesindeki **Telegram bildirimleri** ve **Bildirim tercihlerim** kartlarındadır ve tüm projeleriniz için geçerlidir.

### Kişisel erişim anahtarları

Kart alt başlığı: "MCP sunucu adresi: <adres>". Liste: her anahtarın adı, başlangıç karakterleri ("…"), "Okuma (+ Proje açma / plana adım) · son kullanım <tarih> (n istek) · bitiş <tarih>", durum rozeti. Boşsa **"Henüz anahtar yok"** — "Bir anahtar oluşturup kullandığınız araca ekleyin."

| Rozet | Anlamı |
|---|---|
| **Etkin** | Anahtar kullanılabilir. |
| **İptal edildi** | Siz iptal ettiniz; kullanılamaz. |
| **Süresi doldu** | Geçerlilik süresi bitti; yenisini oluşturun. |

| Düğme | Ne yapar | Dikkat |
|---|---|---|
| **Anahtar oluştur** | Anahtar oluştur penceresini açar. | **Kişisel Erişim Anahtarı** izni gerekir (tüm standart rollerde vardır). |
| **İptal et** | Etkin anahtarı iptal eder: **"Anahtar iptal edildi."** | **"'<ad>' anahtarı iptal edilsin mi? Bu anahtarı kullanan araçlar hemen bağlanamaz."** Geri alınamaz. |

#### Anahtar oluştur penceresi

[[EKRAN: wa-anahtar-olustur | "Anahtar oluştur" penceresi: Ad, Okuma (sabit işaretli) ve Yazma onay kutuları, Geçerlilik (gün) | Bağlantılarım'da "Kişisel erişim anahtarları" kartındaki "Anahtar oluştur" düğmesine basın]]

| Alan | Ne işe yarar | Nasıl doldurulur | Örnek | Zorunlu |
|---|---|---|---|---|
| **Ad (nerede kullanacaksınız)** | Anahtarı listede tanımanız için. | En az 2, en çok 80 karakter; varsayılan "Claude". | Cursor - dizüstü | Evet |
| **Okuma: projeler, adımlar, çıktılar, onayımı bekleyenler** | Her anahtarda bulunan okuma yetkisi. | Sabit işaretli, değiştirilemez. | — | — |
| **Yazma: proje/Case açma ve plan taslağına adım ekleme (onay ve aktarım yapılamaz)** | Araca proje açma ve plana adım ekleme izni verir. | Onay kutusu. Proje açabilmek için hesabınızda **Proje / Case Açma** izni de olmalı. | İşaretli | Hayır |
| **Geçerlilik (gün)** | Anahtarın kaç gün geçerli olacağı. | 1–365; varsayılan 90. | 90 | Evet |

Düğmeler: **Vazgeç**, **Oluştur**.

#### Anahtar gösterim penceresi

[[EKRAN: wa-anahtar-goster | "<ad> · anahtar" penceresi: kırmızı uyarı, anahtar, Claude Code komutu, Cursor ayarı ve kendi sisteminiz için açıklama | Anahtar oluştur penceresinde "Oluştur"a basın]]

Başlık "<ad> · anahtar". Kırmızı uyarı: **"Bu anahtar bir daha gösterilmez. Kaybolursa iptal edip yenisini oluşturun."** Altında anahtar, **Claude Code:** için hazır komut, **Cursor (.cursor/mcp.json) veya üstbilgi destekleyen diğer MCP istemcileri:** için hazır ayar metni ve **Kendi sisteminiz:** açıklaması.

| Düğme | Ne yapar | Dikkat |
|---|---|---|
| **Anahtarı kopyala** | Anahtarı panoya kopyalar: **"Kopyalandı."** | Kopyalanamazsa **"Kopyalanamadı; elle seçin."** |
| **Kaydettim, kapat** | Pencereyi kapatır. | Kapattıktan sonra anahtar bir daha görünmez. |

> **Dikkat:** Anahtar sizin yetkilerinizle çalışır. Yazma yetkisi olsa bile anahtarla onay ve aktarım yapılamaz; onaylar her zaman RECOrion'da verilir. Anahtarı kimseyle paylaşmayın.

### Şirket sistemlerindeki anahtarlarım

[[EKRAN: wa-sirket-anahtarlarim | "Şirket sistemlerindeki anahtarlarım" kartı: Odoo bağlantı adı, Odoo kullanıcı adı ve girişi, "Adınıza çalışan AI personel", bitiş tarihi, durum rozeti ve Dene / Düzenle / Sil düğmeleri | Bağlantılarım ekranında aşağı kaydırın; kişinin "14 gün kaldı" rozetli bir anahtarı olsun]]

**Bu kart ne işe yarar?** Kart alt başlığı: "AI personeliniz sizin adınıza (ör. RECSlip'te masraf onayı) yalnızca kendi kullanıcı anahtarınızla işlem yapar; kayıtlarda siz ve 'RECAi' görünür." Yani AI personel, şirketin ortak bağlantı şifresini değil **sizin** Odoo kullanıcınızı kullanır. Odoo'da sizin yetkileriniz ve sizin adınız geçerlidir; kayıtta onayın sizin adınıza RECAi tarafından verildiği görünür.

**Ne zaman kullanırım?** RECSlip.App v2'de masraf onaylayıcısıysanız (yönetici, ek onaylayıcı, muhasebeci) veya RECSlip sürecinin Case yöneticisiyseniz. Anahtarınızı tanımlamazsanız AI personel sizin adınıza karar veremez; fişler RECSlip'te (Odoo'da) sizin elle onaylamanızı bekler.

**Ekranın bölümleri:**

- Kart başlığı ve sağda **Anahtar ekle** düğmesi (yalnız şirketinizde kişisel anahtar kullanılan etkin bir Odoo bağlantısı varsa görünür).
- Anahtar listesi. Her satır: **<bağlantı adı>** · <Odoo'daki adınız> <Odoo giriş adınız>; altında "Adınıza çalışan AI personel: <ad veya seçilmedi> · bitiş <tarih>" ve varsa son hata; sağda durum rozeti ve **Dene**, **Düzenle**, **Sil**.
- Boşsa **"Henüz anahtar yok"** ve: "Odoo kullanıcınızın API anahtarını ekleyin (Odoo › Tercihler › Hesap Güvenliği › Yeni API Anahtarı)." Şirkette uygun bağlantı yoksa: "Şirketinizde kişisel anahtar kullanılan bir bağlantı (Odoo) yok."

**Durum rozetleri:**

| Rozet | Anlamı | Ne yapmalı |
|---|---|---|
| **Etkin** (yeşil) | Anahtar çalışıyor, bitişe 14 günden fazla var (veya bitiş girilmemiş). | — |
| **N gün kaldı** (sarı) | Bitişe 14 gün veya daha az kaldı. | Odoo'da yeni anahtar alıp **Düzenle** ile yenileyin. |
| **Süresi doldu** (kırmızı) | Bitiş tarihi geçti; AI personel bu anahtarı kullanmaz. | Yeni anahtar alıp **Düzenle** ile girin. |
| **Geçersiz** (kırmızı) | Son denemede veya bir işlem sırasında Odoo anahtarı reddetti (ör. Odoo'da silindi). AI personel kullanmaz. | Satırdaki hata metnini okuyun; yeni anahtar girin. |

| Düğme | Ne yapar | Dikkat |
|---|---|---|
| **Anahtar ekle** | Anahtar ekle penceresini açar. | Her bağlantı için kişi başına tek anahtar tutulur; aynı bağlantıya yeniden eklerseniz eskisinin yerine geçer. |
| **Dene** | Kayıtlı anahtarla Odoo'ya bağlanıp kullanıcınızı okur: **"Anahtar çalışıyor: <giriş adı>"**. Çalışmazsa hata mesajı ve rozet **Geçersiz** olur. | Çalışan anahtar yeniden **Etkin** olur. |
| **Düzenle** | Anahtarı düzenle penceresini açar (yeni anahtar, AI personel, bitiş tarihi). | — |
| **Sil** | Anahtarı siler: **"Anahtar silindi."** | **"<bağlantı> anahtarınız silinsin mi? AI personeliniz bu sistemde sizin adınıza işlem yapamaz."** Geri alınamaz. Case yöneticisiyseniz aktarım dosyası da oluşturulamaz. |

#### Anahtar ekle / Anahtarı düzenle penceresi

[[EKRAN: wa-anahtar-ekle | "Anahtar ekle" penceresi: Sistem, API anahtarı (gizli), Adınıza çalışacak AI personel ve Anahtarın bitiş tarihi alanları; Dene ve kaydet düğmesi | Bağlantılarım'da "Şirket sistemlerindeki anahtarlarım" kartındaki "Anahtar ekle" düğmesine basın]]

| Alan | Ne işe yarar | Nasıl doldurulur / seçenekler | Örnek | Zorunlu |
|---|---|---|---|---|
| **Sistem** | Anahtarın hangi şirket bağlantısına ait olduğu. | Şirketin etkin Odoo bağlantıları. Yalnız eklemede görünür; düzenlemede değişmez. | Örnek Lojistik Odoo | Evet |
| **API anahtarı** (düzenlemede: **Yeni API anahtarı (değiştirmeyecekseniz boş bırakın)**) | Odoo'da kendi kullanıcınız için oluşturduğunuz anahtar. | Odoo'dan kopyalayıp yapıştırın; yazılanlar gizli görünür. En az 8 karakter. İpucu: "Odoo › sağ üst › Tercihler › Hesap Güvenliği › Yeni API Anahtarı. Anahtar denenir, şifreli saklanır, bir daha gösterilmez." | (gizli) | Eklemede evet |
| **Adınıza çalışacak AI personel** | Kriterlere bakıp sizin adınıza karar verecek AI personel; kararlarda bu adla görünür. | **Seçin** veya şirketin AI personelinden biri. Seçmezseniz kararlar "RECAi Masraf Onay Asistanı" (yönetici adımı) veya "RECAi Muhasebe Kontrol Personeli" (muhasebe adımı) adıyla verilir. | Defne (Muhasebe Uzmanı) | Hayır |
| **Anahtarın bitiş tarihi** | Odoo'da anahtara verdiğiniz bitiş tarihi. İpucu: "Odoo'da verdiğiniz bitiş; yaklaşınca hatırlatılır." | Odoo'da seçtiğiniz tarihin aynısını girin. Bu tarihten sonra AI personel anahtarı kullanmaz; son 14 günde rozet sarıya döner. | 31.10.2027 | Hayır (girilmesi önerilir) |

| Düğme | Ne yapar | Dikkat |
|---|---|---|
| **Vazgeç** | Pencereyi kapatır. | — |
| **Dene ve kaydet** | Anahtarı önce Odoo'da dener ("Deneniyor…"), çalışıyorsa şifreli kaydeder: **"Kaydedildi: <Odoo giriş adı>"**. | Eklemede sistem seçilmemişse veya anahtar 8 karakterden kısaysa pasiftir. Anahtar çalışmazsa kaydedilmez. |

**Hata mesajları:**

| Mesaj | Ne demek, ne yapmalı |
|---|---|
| **"Anahtar denenemedi: …"** | Odoo anahtarı kabul etmedi (yanlış kopyalandı, süresi geçti, başka veritabanına ait). Odoo'da yeni anahtar oluşturup tekrar deneyin. |
| **"API anahtarını girin."** | İlk eklemede anahtar boş. |
| **"Bağlantı bulunamadı veya etkin değil."** | Seçilen Odoo bağlantısı kapatılmış. Şirket yöneticinize başvurun. |
| **"Bu bağlantı türünde kişisel anahtar kullanılmıyor."** | Kişisel anahtar yalnız Odoo bağlantılarında kullanılır. |
| **"Seçilen AI personel bu şirkette yok."** | Seçtiğiniz AI personel işten çıkarılmış olabilir. Başka birini seçin. |
| **"KVKK gereği RECDx personeli müşteri sistemine kişisel anahtar tanımlayamaz."** | RECDx yöneticileri müşteri adına anahtar giremez. Anahtarı kişinin kendisi girmelidir. |

#### Odoo'da API anahtarı nasıl alınır? (adım adım)

[[EKRAN: wa-odoo-api-anahtari | Odoo'da kullanıcı Tercihler penceresinin Hesap Güvenliği sekmesi ve "Yeni API Anahtarı" düğmesi; ardından açıklama ve süre/bitiş seçilen pencere ve bir kez gösterilen anahtar | RECSlip v2 kurulu test Odoo'suna onaylayıcı kullanıcıyla girin; sağ üstte kullanıcı adına tıklayıp Tercihler'i açın, Hesap Güvenliği sekmesine geçin]]

Anahtarı **RECSlip'te onaylayıcı olarak tanımlı olduğunuz kendi Odoo kullanıcınızla** oluşturun. RECOrion, RECSlip'teki onay adımının kime ait olduğunu bu anahtarın Odoo kullanıcısından anlar; başka birinin kullanıcısıyla oluşturulan anahtar sizin adımlarınızla eşleşmez.

1. Şirketinizin Odoo'suna kendi kullanıcı adınız ve şifrenizle girin.
2. Sağ üst köşede adınıza veya profil resminize tıklayın, **Tercihler**'i (Odoo sürümüne göre "Tercihlerim") seçin.
3. Açılan pencerede **Hesap Güvenliği** sekmesine geçin.
4. **Yeni API Anahtarı** düğmesine basın. Odoo güvenlik için şifrenizi yeniden sorabilir; girip onaylayın.
5. Anahtar için bir açıklama yazın (ör. "RECOrion RECSlip onayları"). Bu açıklama yalnız Odoo'daki listede görünür.
6. Süreyi veya bitiş tarihini seçin. Odoo 20'de bitiş tarihi zorunludur. Örneğin bir yıl seçin ve tarihi not edin.
7. Odoo anahtarı **yalnız bir kez** gösterir. Kopyalayın (ekrandan kapatmadan önce).
8. RECOrion'da **Work Space › Bağlantılarım › Şirket sistemlerindeki anahtarlarım › Anahtar ekle**'ye basın.
9. **Sistem**'de şirketinizin Odoo bağlantısını seçin, **API anahtarı**'na kopyaladığınız anahtarı yapıştırın.
10. **Adınıza çalışacak AI personel**'i seçin (ör. muhasebe için muhasebe AI personeli, yönetici onayları için departmanınızın AI personeli).
11. **Anahtarın bitiş tarihi**'ne 6. adımda seçtiğiniz tarihi girin.
12. **Dene ve kaydet**'e basın. "Kaydedildi: <Odoo giriş adınız>" mesajını ve **Etkin** rozetini görün.

> **Dikkat:** Odoo'daki pencereyi kapattıktan sonra anahtarı Odoo da bir daha göstermez. Kopyalamayı unuttuysanız Odoo'da o anahtarı silip yenisini oluşturun.

> **İpucu:** Anahtarın süresi dolmadan önce aynı adımlarla Odoo'da yeni anahtar alın, RECOrion'da **Düzenle** ile **Yeni API anahtarı** ve yeni **Anahtarın bitiş tarihi**'ni girin. Eski anahtarı Odoo'da silebilirsiniz.

**Sık sorulan sorular**

- **Anahtarımı RECOrion'da kim görebilir?** Kimse. Anahtar şifreli saklanır ve bir daha gösterilmez; ekranda yalnız Odoo kullanıcı adınız görünür.
- **AI personel benim adıma her şeyi yapabilir mi?** Hayır. Bugün yalnız RECSlip masraf onayı/reddi ve (Case yöneticisiyseniz) aktarım dosyası işlemleri için kullanılır. Odoo'da yetkiniz olmayan bir işlemi anahtarla da yapamaz.
- **AI bir fişi yanlış onayladı; Odoo'da kim onaylamış görünür?** Onay sizin kullanıcınızla, "<AI personel> (RECAi, <adınız> adına)" bilgisiyle ve RECAi onaylı işaretiyle kaydedilir. Hangi kriterle onaylandığını Case'in RECSlip sekmesindeki **AI kararları** listesinde görürsünüz.
- **Anahtarımı silersem ne olur?** AI personel sizin adınıza karar veremez; fişler RECSlip'te elle onayınızı bekler. Onaylarım'da bekleyen RECSlip fişlerine de karar veremezsiniz.

## Pano

[[EKRAN: wa-pano | Work Space Pano ekranı: dönem seçici (7 gün / 30 gün / 90 gün / 1 yıl), departman rozeti, proje ve adım istatistikleri, Kredi kartı, günlük grafikler, AI personel karnesi ve Ekip iş durumu tabloları | Departman Panosu izni olan bir kullanıcıyla (ör. Proje Yöneticisi) giriş yapın; mod çubuğunda "Pano"ya basın]]

**Bu ekran ne işe yarar?** Şirketin veya kendi departmanınızın proje, iş adımı, kredi, AI personel performansı ve (yetkiliyseniz) maliyet göstergelerini tek ekranda gösterir. Tutarlar TL ve KDV hariçtir.

**Kimler görür?** **Şirket Geneli Pano** veya **Departman Panosu** izni olanlar. Yalnız Departman Panosu izni olan kullanıcı kendi departmanını görür; üstte **Departman: <ad>** rozeti çıkar. Parasal kartlar (token maliyeti, maliyet dağılımı, tahmini tasarruf, bütçe) yalnız **Maliyet ve Bütçe Bilgilerini Görme** izni olanlarda görünür.

**Ekranın bölümleri:**

| Bölüm | Ne gösterir |
|---|---|
| Üst satır | **Pano** başlığı, dönem seçici **7 gün** / **30 gün** / **90 gün** / **1 yıl** (varsayılan 30 gün), varsa departman rozeti, "TL, KDV hariç · grafikler son n gün". |
| Proje istatistikleri | **Aktif proje** (aktif + duraklatılmış), **Tamamlanan** (zamanında / geç), **İptal edilen**, **Hazırlıkta** (taslak + planlama + başlamaya hazır). |
| Adım istatistikleri | **Tamamlanan adım** (n / toplam), **Onay bekleyen adım**, **Revizyondaki adım**, **Karantinadaki adım** (varsa kırmızı). |
| **Kredi** | **Bu ay kullanılan**, **Aylık hak**, **Kalan aylık**, **Ek kredi bakiyesi**. |
| **Günlük kredi tüketimi** | Günlere göre RECOrion kredisi grafiği. |
| **Günlük token maliyeti** | Günlere göre RECAi kullanımının TL karşılığı (parasal izin gerekir). |
| **LLM bazında** | RECAi kademelerine göre maliyet veya kredi; her satırda "n çağrı · n kredi". |
| **Maliyet dağılımı** | **Personel**, **Token (LLM)**, **Diğer kalemler**, **Toplam** ve diğer maliyet kalemleri grafiği (parasal izin gerekir). |
| **Tahmini tasarruf (ROI)** | AI personelin tamamladığı adımlar insanla yapılsaydı ne tutardı (**İnsanla yapılsaydı**) ile **AI maliyeti** karşılaştırması (parasal izin gerekir). |
| **İlk seferde onay** | AI personel başına, revizyon istenmeden onaylanan adımların payı. |
| **AI personel karnesi** | Tablo: **AI personel**, **Tamamlanan**, **İlk seferde onay**, **Otonomi** (insan revizyonu istenmeden tamamlanan adımların payı), **Revizyon**, **Karantina**, **Ort. süre**, **Kredi**, (parasal izinle) **Maliyet**. |
| **Ekip iş durumu** | İnsan personel tablosu (ücret bilgisi içermez): **Personel**, **Açık**, **Çalışılıyor**, **Onay bekliyor**, **Tamamlanan**, **Geciken** (varsa kırmızı). |
| **Projeler: bütçe ve gerçekleşen** | Her projenin bütçesi ve gerçekleşeni ("Gerçekleşen = personel + token + diğer kalemler"); parasal izin gerekir. |

**Boş durumlar:** "Bu dönemde kredi tüketimi yok." · "Bu dönemde LLM çağrısı yok." · "Bu dönemde TL maliyeti oluşmadı. LLM TL fiyatları RECDx tarafından girildiğinde burada görünür." · "Bu dönemde tamamlanan AI adımı yok." · "Bu kapsamda iş almış AI personel yok." · "Bu kapsamda iş atanmış insan personel yok."

**Mesajlar:** **"Departmanınız tanımlı değil; departman panosu için şirket yöneticinize başvurun."** — kullanıcı kaydınıza departman atanmamış.

> **İpucu:** "n çağrının TL fiyatı tanımsız" uyarısı, bazı RECAi kullanımlarının TL fiyatının henüz girilmediğini gösterir; bu kullanımlar maliyete 0 olarak yansır, krediye yansır.


# RECSlip fişleri: onaylayıcı olarak ne yaparım?

Bu bölüm, RECSlip.App v2 masraf süreciyle ilgili Work Space'te yapacağınız her şeyi tek yerde toplar. Ekranların ayrıntıları ilgili bölümlerde (Bağlantılarım, Onaylarım, RECSlip sekmesi) de anlatılmıştır.

## Süreç nasıl işler?

RECSlip.App v2, şirketinizin Odoo'sunda çalışan masraf fişi uygulamasıdır. RECOrion bu uygulamayla birlikte çalışarak onayların büyük kısmını AI personele yaptırır:

1. Çalışan fişini RECSlip'e yükler. RECSlip fişi okur (tutar, tarih, tedarikçi, kalemler, muhasebe hesapları, güven puanı, risk) ve onaya gönderir.
2. RECSlip onay zincirini kurar: şirketinizde bir onay kuralı varsa ona göre, yoksa sırayla **yönetici** ve **muhasebe** onay adımları.
3. RECOrion bekleyen onay adımlarını düzenli aralıklarla (varsayılan 15 dakikada bir) kontrol eder.
4. Adımın onaylayıcısı RECOrion'da kendi Odoo anahtarını tanımladıysa, o kişinin seçtiği **AI personel** fişi Case'teki kriterlere göre değerlendirir:
   - **Kriterlere uyuyorsa:** AI personel fişi **sizin anahtarınızla** onaylar. RECSlip'te fiş "RECAi onaylı" olarak işaretlenir; onaylayan "<AI personel> (RECAi, <adınız> adına)" görünür.
   - **Uymuyorsa:** Fiş gerekçesiyle ve (muhasebede) önerilen hesap düzeltmesiyle sizin **Onaylarım** ekranınıza düşer; size bildirim gelir. Kararı siz verirsiniz.
5. Onaylayıcı anahtar tanımlamadıysa RECOrion o adıma dokunmaz; adım RECSlip'te (Odoo'da) sizin elle karar vermenizi bekler.
6. Muhasebe adımında AI personel, kalemlerin hesabının güvenli bir kaynaktan (kural, tedarikçi hafızası, tam eşleşme, onaylı hafıza) gelip gelmediğine bakar. Gelmediyse RECAi Mergen'den ikinci görüş alır. İkinci görüş farklı bir hesap öneriyor ve güveni yeterliyse (varsayılan en az 90) hesabı düzeltip onaylar; değilse karar size kalır.
7. İnsan kararları AI önerisiyle karşılaştırılır; RECSlip sekmesinde **AI–insan uyumu** oranı olarak görünür.
8. Her ay bir **"RECSlip masraf süreci <dönem>"** Case'i açılır: ay sonu kesim, geç gelen fişler, aktarım dosyası, muhasebe programına işleme ve kapanış raporu bu Case'te yürür.

> **İpucu:** Süreç Şirket Yönetimi › Otomasyonlar ekranındaki **RECSlip.App v2 aylık süreç** kartından **Kur** ile kurulur (Odoo bağlantısı, Case yöneticisi = muhasebeci, kapanış raporunu yazacak AI personel, raporu onaylayacak kişi). Ön koşul, şirketin Odoo'sunda RECSlip.App v2'nin kurulu ve Entegrasyonlar'da bu Odoo'nun bağlı olmasıdır. Ayrıntılar Şirket Yönetimi Kılavuzu'ndadır. Kurulum için Case yöneticisinin (muhasebecinin) önce kendi anahtarını tanımlamış olması gerekir.

## Kim ne yapar?

| Kişi | Work Space'te yapacakları |
|---|---|
| **Yönetici / ek onaylayıcı** (ör. departman müdürü) | Bağlantılarım'da anahtarını ekler; Onaylarım'da kriter dışı fişlere karar verir. |
| **Muhasebeci** | Aynısı; ayrıca muhasebe fişlerinde AI'ın hesap düzeltme önerilerini değerlendirir. |
| **Case yöneticisi** (kurulumda seçilen muhasebeci) | Yukarıdakilere ek olarak Case'in RECSlip sekmesinden ayarları ve kriterleri değiştirir; aktarım dosyasını muhasebe programına işleyip RECSlip'te **Muhasebeye işlendi** olarak işaretler. Aktarım dosyası onun anahtarıyla oluşturulur. |
| **Kapanış raporu onaylayıcısı** (ör. muhasebe müdürü) | Ay sonunda S7 Kapanış raporu adımını onaylar veya revizyon ister (iş adımı onayı gibi). |

## Önce anahtarınızı ekleyin (bir kez)

1. Odoo'da kendi kullanıcınızla **Tercihler › Hesap Güvenliği › Yeni API Anahtarı** ile anahtar oluşturun, bitiş tarihini not edin, anahtarı kopyalayın.
2. RECOrion'da **Bağlantılarım › Şirket sistemlerindeki anahtarlarım › Anahtar ekle**.
3. **Sistem**, **API anahtarı**, **Adınıza çalışacak AI personel**, **Anahtarın bitiş tarihi** alanlarını doldurup **Dene ve kaydet**.
4. Rozetin **Etkin** olduğunu görün.

Adım adım anlatım için Bağlantılarım bölümündeki **"Odoo'da API anahtarı nasıl alınır?"** başlığına bakın.

> **Dikkat:** Rozet sarıya (**N gün kaldı**) dönünce anahtarınızı yenileyin. **Süresi doldu** veya **Geçersiz** olan anahtarla AI personel sizin adınıza karar veremez ve Onaylarım'daki fişlere de karar veremezsiniz.

## Onaylarım'da karar verin

1. RECSlip size bir fiş bıraktığında e-posta (ve bağladıysanız Telegram) bildirimi alırsınız: "RECSlip: '<fiş>' (<tutar>) <rol> onayınızı bekliyor. AI önerisi: …".
2. RECOrion'da **Onaylarım**'ı açın. En üstte **RECSlip masraf fişleri** bölümü vardır.
3. Kartta fişin adını, tutarını, çalışanı ve rolünüzü (**Yönetici onayı**, **Ek onaylayıcı onayı**, **Muhasebe onayı**) görün.
4. **Gerekçe** satırını okuyun: AI fişi neden size bıraktı? (Gerekçe ifadelerinin anlamı için Onaylarım › RECSlip masraf fişleri kartı tablosuna bakın.)
5. Muhasebe fişinde **Önerilen hesap düzeltmeleri** varsa her satırı kontrol edin: hangi kalem, eski hesap, önerilen yeni hesap, güven ve gerekçe.
6. Karar verin:
   - Uygunsa **Onayla**. Düzeltmeleri istemiyorsanız önce **Onaylarken düzeltmeleri uygula** işaretini kaldırın.
   - Uygun değilse **Reddet**, gerekçeyi yazın (çalışana ve RECSlip geçmişine yazılır).

Kararınız sizin adınıza, sizin Odoo kullanıcınızla RECSlip'e yazılır; AI onayı olarak işaretlenmez. Fişe doğrudan RECSlip'ten karar verirseniz RECOrion bunu fark eder ve kart Onaylarım'dan kalkar (AI kararları listesinde **Odoo'dan karar verildi**).

> **Örnek:** Örnek Lojistik'te Mehmet Demir Bilgi İşlem müdürüdür ve ekibinin masraflarını onaylar. Can Öztürk cumartesi günü 1.200 TL'lik bir kablo alımı fişi yükler. Mehmet Bey'in AI personeli fişi **Hafta sonu harcaması insana** kriteri nedeniyle Onaylarım'a bırakır: "Orion Asistan: Hafta sonu harcaması." Mehmet Bey bunun acil bir arıza için olduğunu bilir ve **Onayla**'ya basar. Fiş muhasebe adımına geçer; muhasebeci Zeynep Kaya'nın AI personeli kalem hesabının tedarikçi hafızasından geldiğini görür, tutar 5.000 TL'nin altında olduğu için fişi Zeynep Hanım'ın adına onaylar.

## Case'in RECSlip sekmesini okuyun

**Projeler** ekranında **"RECSlip masraf süreci <dönem>"** Case'ini açın (ekibinde değilseniz Case yöneticisinden sizi ekibe eklemesini isteyin) ve **RECSlip** sekmesine geçin.

| Neye bakarım | Ne anlarım |
|---|---|
| **Ay sonu kesim**, **Geç gelen fişler için son**, **Aktarım dosyası** | Bu ayın takvimi. Fişlerin en geç ne zamana kadar onaylanması gerektiğini buradan görürsünüz. |
| **Yönetici adımları**, **Muhasebe adımları** | Kaç fişi AI onayladı, kaçı insan kararı bekliyor, kaçında hata oldu. |
| **AI–insan uyumu** | İnsanların AI önerisine ne kadar katıldığı. Yüksek uyum, kriterlerin gevşetilebileceğini; düşük uyum, kriterlerin sıkılaştırılması gerektiğini düşündürür. |
| **Aktarım** | Aktarım dosyasının adı, fiş sayısı, toplamı ve durumu (**PENDING**, **CREATED**, **POSTED**, **FAILED**). |
| **AI kararları** | Her fişte AI'ın ne dediği, gerekçesi, yaptığı düzeltmeler ve son durum. |

İş Akışı sekmesinde S1–S7 adımlarını izleyebilirsiniz. Aktarım dosyası oluşunca S5 adımının çıktısı olarak Case'e eklenir; Case yöneticisine "aktarım dosyası hazır" bildirimi gider. Dosyayı muhasebe programına işleyip RECSlip'te **Muhasebeye işlendi** olarak işaretleyince S6 kendiliğinden tamamlanır ve S7 kapanış raporu başlar.

## Ayarları ve kriterleri değiştirin (Case yöneticisi)

Yalnız Case yöneticisi (ve **Tüm Projeleri Yönetme** izni olanlar) **Ayarlar ve onay kriterleri** kartını değiştirebilir. Değişikliği yapıp kartın sağ üstündeki **Kaydet**'e basın. Yeni ayarlar bir sonraki takipten itibaren uygulanır ve **sonraki ayın Case'i bu ayarlarla açılır**.

**Tüm ayarlar, anlamları ve varsayılanları:**

| Bölüm | Alan | Anlamı | Varsayılan | Ne zaman değiştiririm? |
|---|---|---|---|---|
| Genel | **Fiş ve onay takibi (dakika)** | Bekleyen onaylara kaç dakikada bir bakılacağı. | 15 | Daha hızlı karar istiyorsanız kısaltın (en az 5). |
| Genel | **Onaya gönderilmemiş fiş hatırlatması (gün)** | Onaya gönderilmemiş fişler için hatırlatma süresi. | 2 | — |
| Genel | **Kesim günü (-1: ayın son günü)** | Dönemin kapandığı gün. | -1 | Şirketiniz ayın belli bir gününde kesim yapıyorsa. |
| Genel | **Kesim saati** | Kesim saati. | 18:00 | Mesai bitişiniz farklıysa. |
| Genel | **Geç fiş toleransı (sonraki ayın günü)** | Önceki ayın fişlerinin sonraki ayın kaçına kadar bekleneceği. | 3 | Çalışanlar fişleri geç getiriyorsa uzatın. |
| Genel | **Aktarım günü (sonraki ay)** | Aktarım dosyasının oluşturulacağı gün. | 5 | Muhasebe kapanış takviminize göre. |
| Genel | **Aktarım saati** | Aktarım dosyasının saati. | 10:00 | — |
| Genel | **Tekrar sayısı** | Aktarım dosyası oluşmazsa yeniden deneme ve "işlenmedi" hatırlatması sayısı. | 3 | — |
| Genel | **Tekrar aralığı (saat)** | Denemeler / hatırlatmalar arası süre. | 24 | — |
| Genel | **İşlenmedi hatırlatması (gün)** | Dosya oluştuktan kaç gün sonra "işlenmedi" hatırlatmasının başlayacağı. | 2 | — |
| Yönetici | **Tümünü AI onaylasın (eşikler aranmaz)** | AI tüm yönetici adımlarını onaylar (mükerrer şüphesi hariç). | Kapalı | Masraflarınız düşük riskliyse ve uyum oranı yüksekse. |
| Yönetici | **En yüksek fiş tutarı** | Bunu aşan fiş insana. | 2500 | Şirketinizin harcama yetki sınırına göre. |
| Yönetici | **Çalışan başına aylık sınır** | Çalışanın aylık toplamı bunu aşarsa insana (0 = sınır yok). | 15000 | — |
| Yönetici | **İzinli risk** | Bu risk seviyeleri dışındaki fiş insana. | Yok | Düşük riskli fişleri de AI onaylasın istiyorsanız **Düşük**'ü işaretleyin. |
| Yönetici | **Hafta sonu harcaması insana** | Hafta sonu fişleri insana. | Açık | Saha ekibiniz hafta sonu çalışıyorsa kapatın. |
| Yönetici | **Mükerrer şüphesi insana** | Mükerrer olabilecek fişler insana. | Açık | Açık bırakmanız önerilir. |
| Muhasebe | **Tümünü AI onaylasın (eşikler aranmaz; düzeltmeler yine yapılır)** | AI tüm muhasebe adımlarını onaylar; dengesiz, mükerrer ve kalemsiz fişler yine insana gider. | Kapalı | Uyum oranı uzun süre yüksekse. |
| Muhasebe | **En yüksek fiş tutarı** | Bunu aşan fiş insana. | 5000 | — |
| Muhasebe | **En düşük fiş güveni** | RECSlip'in okuma güveni bunun altındaysa insana. | 85 | Okuma hataları çoksa yükseltin. |
| Muhasebe | **AI düzeltmesi için en düşük güven** | AI'ın hesap düzeltmesi için gereken en düşük güven. | 90 | Düzeltmeleri daha temkinli istiyorsanız yükseltin. |
| Muhasebe | **İzinli risk** | Bu risk seviyeleri dışındaki fiş insana. | Yok, Düşük | — |
| Muhasebe | **Güvenli sayılan eşleşme kaynakları** | Bu kaynaklardan gelen hesaplar doğru kabul edilir; diğerleri için RECAi Mergen ikinci görüşü alınır. | Kural, Tedarikçi hafızası, Tam eşleşme, Onaylı hafıza | Muhasebecinin elle girdiği hesaplara da güveniyorsanız **Elle (muhasebeci)**'yi ekleyin. |
| Muhasebe | **KKEG'li fiş insana** | KKEG kalemli fişler insana. | Açık | Açık bırakmanız önerilir. |

> **Dikkat:** Kriterleri gevşetmek (ör. **Tümünü AI onaylasın**) daha çok fişin insan görmeden onaylanması demektir. Önce birkaç ay **AI–insan uyumu** oranını ve **AI kararları** listesini izleyin.

## Sık sorulan sorular (RECSlip)

- **Onaylarım'da RECSlip fişi hiç görmüyorum, neden?** Ya AI personeliniz tüm fişleri kriterlere uygun bulup onaylamıştır (RECSlip sekmesinde **AI onayladı**), ya anahtarınız tanımlı değildir veya **Süresi doldu** / **Geçersiz** durumdadır (o zaman fişler RECSlip'te elle onayınızı bekler). Bağlantılarım'ı kontrol edin.
- **AI, kriterlere uyan bir fişi neden onaylamadı?** RECSlip sekmesindeki **AI kararları** listesinde fişin durumuna bakın. **Hata** ise onay RECSlip'e yazılamamıştır (ör. anahtar sorunu); bir sonraki takipte yeniden denenir.
- **Kriterleri ben değiştiremiyorum.** Ayarları yalnız Case yöneticisi değiştirir. Kartın alt başlığında "Yalnızca Case yöneticisi değiştirebilir." yazıyorsa Case yöneticisine başvurun.
- **Ay ortasında kriter değiştirirsem geçmiş kararlar değişir mi?** Hayır. Yeni kriterler bundan sonraki değerlendirmelere uygulanır; verilen kararlar değişmez.
- **Aktarım dosyası oluşmadı (FAILED).** Case yöneticisinin anahtarı geçersiz veya süresi dolmuş olabilir; ya da RECSlip dosyayı oluşturamamıştır. Aktarım satırındaki hata metnini okuyun, anahtarı yenileyin. Ayrıntı için Case yöneticisine bildirim de gider.
- **Dosyayı muhasebe programına işlemeyi unuttum.** İşlenmedi hatırlatmaları **Tekrar sayısı** kadar gelir. Sayı dolunca aktarım iptal edilir ve fişler sonraki ayın dosyasına devreder; kayıp olmaz.
- **Aktarım dosyası muhasebe programına kendiliğinden işleniyor mu?** Hayır. RECOrion şimdilik yalnız aktarım dosyasını üretir; dosyanın muhasebe programına işlenmesi elle yapılır.

# Sık karşılaşılan durumlar ve çözümleri

| Durum | Olası neden | Çözüm |
|---|---|---|
| Giriş yapamıyorum: "Geçersiz kullanıcı adı veya şifre." | E-posta veya şifre yanlış. | **Şifremi unuttum** ile yeni şifre belirleyin. |
| "Çok fazla hatalı giriş denemesi…" | 5 hatalı deneme. | 15 dakika bekleyin veya şifrenizi sıfırlayın. |
| Şifre belirleme bağlantısı çalışmıyor. | 1 saat geçti veya bağlantı kullanıldı. | Giriş penceresinde **Şifremi unuttum** ile yeni bağlantı isteyin. |
| Başvurudan sonra giriş yapamıyorum. | Başvuru RECDx onayında. | Aktivasyon e-postasını bekleyin. |
| Projeler ekranında yeni proje düğmeleri yok. | **Proje / Case Açma** izniniz yok. | Şirket yöneticinizden izin veya proje yöneticisinden proje açmasını isteyin. |
| Bir projeyi listede göremiyorum. | Ekibinde değilsiniz. | Proje yöneticisinden sizi **Ekip & Simülasyon**'dan eklemesini isteyin. |
| Yeni proje açılmıyor, paket sınırı uyarısı. | Eşzamanlı proje sınırı dolu. | Biten projeleri **Kapanış**'tan tamamlayın veya paketinizi büyütün. |
| **Planlamaya başla** uyarı veriyor. | İsterler boş. | **Bilgiler & İsterler**'de isterleri yazıp **Kaydet**. |
| **Başlamaya hazır yap** pasif. | Kontrol listesinde eksik madde var. | **Hazırlık & Bildirim**'de ○ olan maddeyi tamamlayın (plan onayı, personel ataması, tarihler). |
| Plan yeniden onaylanamıyor. | Başlamış adım veya yazışması olan adım var. | Planı değiştirmek yerine Çalışma Alanı'ndan **Yeni adım** ekleyin veya proje yöneticinizle görüşün. |
| Adım **Karantinada**. | Ret sınırı doldu veya personel çalışamadı (kredi, bağlantı). | Proje yöneticisi İş Akışı'nda nedeni okur; gerekirse başka personel ekler, **Yeniden dene** veya **Adımı iptal et**. Kredi yetersizse şirket yöneticinize haber verin. |
| E-postadaki onay bağlantısı "Bağlantı kullanılamıyor" diyor. | Süresi doldu, kullanıldı veya onaylayıcı değişti. | Kararı **Onaylarım**'dan verin. |
| Sohbete yazamıyorum. | Proje kapanmış veya adım seçili değil. | Kapanmış projede yazışma salt okunurdur; açık projede soldan bir adım seçin. |
| Dosya eklenmiyor. | 5 dosya sınırı, desteklenmeyen tür, 50 MB üstü veya depolama kotası dolu. | Dosya sayısını/boyutunu azaltın, desteklenen türe çevirin. |
| Maliyet sekmesini göremiyorum. | Proje yöneticisi değilsiniz. | Gerekirse proje yöneticisinden Excel raporu isteyin. |
| Panoda parasal kartlar yok. | **Maliyet ve Bütçe Bilgilerini Görme** izniniz yok. | Şirket yöneticinizden izin isteyin. |
| "Departmanınız tanımlı değil…" | Kullanıcı kaydınızda departman yok. | Şirket yöneticinizden departman atamasını isteyin. |
| Telegram bildirimi gelmiyor. | Hesap bağlı değil veya tercih kapalı. | Bir projenin **Hazırlık & Bildirim** sekmesinde **Telegram hesabımı bağla**, sonra **Telegram (Onayla / Revizyon iste butonları)** kutusunu işaretleyin. |
| Kişisel erişim anahtarımı kaybettim. | Anahtar bir kez gösterilir. | **Bağlantılarım**'da eskisini **İptal et**, yenisini oluşturun. |
| Odoo anahtarım **Geçersiz** veya **Süresi doldu**. | Odoo'da silindi ya da süresi bitti. | Odoo'da yeni API anahtarı alıp **Düzenle** ile girin, **Dene ve kaydet**. |
| **Anahtar ekle** düğmesi yok. | Şirkette etkin Odoo bağlantısı yok. | Şirket yöneticinizden Entegrasyonlar'da Odoo bağlantısını kurmasını isteyin. |
| "Anahtar denenemedi: …" | Anahtar yanlış kopyalandı veya başka bir Odoo'ya ait. | Odoo'da yeni anahtar oluşturup tam olarak kopyalayın. |
| RECSlip fişine karar verirken "Odoo anahtarınız geçersiz…" | Anahtar sorunu. | Bağlantılarım'dan anahtarı yenileyin, Onaylarım'da yeniden deneyin. |
| Üst çubukta şirket logosu görünmüyor. | Logo yüklenmemiş. | Şirket yöneticiniz Şirket Yönetimi › Şirket Profili'nden yükler. |
| Sağlık noktalarından biri kırmızı. | Altyapı bileşeninde geçici sorun. | Birkaç dakika sonra sayfayı yenileyin; sürerse RECDx destekle iletişime geçin. |

# Hızlı başvuru

| Ne yapmak istiyorum? | Nereye gidiyorum? |
|---|---|
| Şirketimiz için abonelik başvurusu yapmak | Resmi site › paket kartı › **🚀 Bu Paketi Kirala / Satın Al** |
| Başvuruda şirket logosu eklemek | Başvuru › Adım 1 › **Şirket Logosu (isteğe bağlı)** › **Logo seç** |
| Giriş yapmak / şifremi sıfırlamak | Resmi site › **🔑 Giriş Yap** / **Şifremi unuttum** |
| Yeni proje veya Case açmak | Work Space › **Projeler** › **Yeni Proje / Case** |
| Hazır şablondan proje açmak | **Projeler** › **Şablondan oluştur** |
| Toplantı kaydından proje açmak | **Projeler** › **Toplantıdan oluştur** |
| İsterleri düzenlemek | Proje ekranı › **Bilgiler & İsterler** |
| Şartname, örnek dosya yüklemek | Proje ekranı › **Proje Ekleri** |
| Plan önerisi almak, adımları düzenlemek | Proje ekranı › **Beyin AI Planlama** |
| Adımın onaylayıcısını, ret sınırını seçmek | **Beyin AI Planlama** › **Akış şeması** › adım kartı › adım ayarları |
| Ekibe kişi eklemek, tarih tahmini almak | Proje ekranı › **Ekip & Simülasyon** |
| Projeyi başlatmak | **Hazırlık & Bildirim** › **Başlamaya hazır yap** › **Başlat** |
| Telegram'ı bağlamak, bildirim kanalını seçmek | Herhangi bir proje › **Hazırlık & Bildirim** |
| Adım çıktısını görmek, onaylamak | Proje ekranı › **İş Akışı** veya **Onaylarım** veya **Çalışma Alanı** sağ bölme |
| Karantinadaki adıma karar vermek | Proje ekranı › **İş Akışı** › **Yeniden dene** / **Adımı iptal et** |
| Çıktıyı Odoo'ya aktarmak | **İş Akışı** › **Sisteme aktar** |
| Bütçe girmek, gider eklemek | Proje ekranı › **Maliyet** |
| Kod deposu açmak | Proje ekranı › **Kod Deposu** |
| AI'ın yazdığı kodu görmek | Proje ekranı › **Kod Deposu** › **Kod Gezgini** |
| Testleri çalıştırmak, sonuçlarını görmek | Proje ekranı › **Testler** |
| Projeyi kapatmak, ekleri kurum hafızasına aktarmak | Proje ekranı › **Kapanış** |
| Projeyi şablon yapmak | Proje ekranı › **Şablon olarak kaydet** |
| AI personelle görev üzerinde konuşmak | **Çalışma Alanı** › soldan adım seçin |
| Plan dışı adım eklemek | **Çalışma Alanı** › sol bölme › **Yeni adım** |
| Kurum hafızasına bilgi onaylamak / geri almak | **Çalışma Alanı** › sağ bölme › **Hafıza** |
| Kararımı bekleyen her şeyi görmek | **Onaylarım** |
| RECSlip fişine karar vermek | **Onaylarım** › **RECSlip masraf fişleri** |
| RECSlip için Odoo anahtarımı eklemek / yenilemek | **Bağlantılarım** › **Şirket sistemlerindeki anahtarlarım** |
| RECSlip ayı takvimini ve AI kararlarını görmek | **Projeler** › "RECSlip masraf süreci <dönem>" › **RECSlip** |
| RECSlip kriterlerini değiştirmek (Case yöneticisi) | **RECSlip** sekmesi › **Ayarlar ve onay kriterleri** › **Kaydet** |
| RECSlip sürecini kurmak | Şirket Yönetimi › **Otomasyonlar** › **RECSlip.App v2 aylık süreç** (Şirket Yönetimi Kılavuzu) |
| Claude / Cursor'dan RECOrion'a bağlanmak | **Bağlantılarım** › **Kişisel erişim anahtarları** › **Anahtar oluştur** |
| Departman veya şirket göstergelerini görmek | **Pano** |
| Şirket ayarlarına geçmek | Üst çubuk › **🏢 Şirket Yönetimi** |
