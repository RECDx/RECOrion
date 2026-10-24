# RECOrion Edge Connector

Şirket sunucusundaki sistemleri (Logo Tiger/GO, Mikro ve benzeri SQL Server veritabanları) RECOrion AI personeline
güvenli biçimde açar. Ajan şirketin kendi sunucusunda çalışır; RECOrion bulutta kalır.

## Nasıl çalışır

```
 Şirket ağı                                         RECOrion
 ┌──────────────────────────────┐   HTTPS (yalnızca  ┌──────────────────────────────────┐
 │ Logo / Mikro SQL Server      │   dışa doğru)      │ AI personel → araç çağrısı       │
 │        ▲                     │ ─────────────────► │   okuma: anında                  │
 │        │ izinli şablon       │  yoklama + sonuç   │   yazma: insan onayı             │
 │ RECOrion Edge ajanı          │ ◄───────────────── │ iş kuyruğu (edge_jobs)           │
 │ templates.json (SQL burada)  │   iş: şablon adı   │ kayıt: tool_calls (silinemez)    │
 └──────────────────────────────┘   + parametreler   └──────────────────────────────────┘
```

1. AI personel bir aracı (ör. `cari_bakiye`) çağırır; RECOrion işi kuyruğa yazar.
2. Ajan RECOrion'a 25 saniyelik uzun yoklama yapar, işi alır.
3. Ajan şablonu kendi dosyasından bulur, parametreleri denetler, sorguyu çalıştırır, sonucu gönderir.

## Güvenlik ilkeleri

| İlke | Uygulama |
|---|---|
| Port açılmaz | Ajan yalnızca dışa (RECOrion'a) HTTPS bağlantısı kurar. Güvenlik duvarında gelen bağlantı izni gerekmez. |
| SQL dışarıdan gelmez | SQL yalnızca bu sunucudaki `templates.json` dosyasındadır. RECOrion'a yalnızca şablon adı, açıklaması ve parametreleri bildirilir. |
| Enjeksiyon yok | Parametreler türüne (metin, tam sayı, sayı, tarih, doğru/yanlış) ve uzunluğuna göre denetlenir, sorguya **bağlanır** (birleştirilmez). Bilinmeyen parametre reddedilir. |
| Sınırlı sonuç | Her şablonda `max_rows` (üst sınır 1000). Okumalar salt okunur bağlantıda veya geri alınan işlemde çalışır. |
| Yazma kapalı | Yazma şablonları `allow_write: true` olmadan RECOrion'a hiç bildirilmez. Açıksa RECOrion'da her yazma insan onayından geçer. |
| Anahtar | Ajan anahtarı Entegrasyonlar ekranında bir kez gösterilir; RECOrion yalnızca özetini saklar. Yeni anahtar eskisini geçersiz kılar. Bağlantı devre dışı bırakılınca ajan durur. |
| Denetim kaydı | Her iş yerel `edge_audit.log` dosyasına yazılır (şablon, parametreler, satır sayısı, süre; sonuç verisi yazılmaz). RECOrion'da da araç çağrı kaydı tutulur. |

**Öneri:** Veritabanında yalnızca gereken tablolara SELECT yetkisi olan ayrı bir kullanıcı açın (ör. `recorion_okuma`).
Yazma şablonu kullanılacaksa Logo/Mikro'nun kendi tablolarına doğrudan yazmak yerine ayrı bir ara tabloya yazın
(örnekteki `RECORION_NOTLAR` gibi); ERP'ye aktarımı ERP'nin kendi aracıyla yapın.

## Kurulum

1. Python 3.9+ ve `pip install httpx` (SQL Server için ayrıca `pip install pyodbc` ve Microsoft ODBC Driver 18).
2. RECOrion › Şirket Yönetimi › Entegrasyonlar › **Bağlantı ekle › Edge Connector**, ardından **Ajan anahtarı**.
3. `edge_config.example.json` ve `templates.example.json` dosyalarını kopyalayıp düzenleyin:
   - SQL Server: `"database": {"driver": "odbc", "connection_string_env": "RECORION_EDGE_DB"}` ve ortam değişkeni
     `RECORION_EDGE_DB=Driver={ODBC Driver 18 for SQL Server};Server=...;Database=...;UID=recorion_okuma;PWD=...;Encrypt=yes`
4. Ortam değişkenleri: `RECORION_URL` (https), `RECORION_EDGE_TOKEN`.
5. Deneme: `python recorion_edge.py --config edge_config.json --once` → "Bağlantı başarılı".
6. Sürekli çalıştırma: Windows Hizmeti (ör. NSSM) veya Görev Zamanlayıcı ile `python recorion_edge.py --config edge_config.json`.
7. Entegrasyonlar ekranında **Dene**: "Ajan çevrimiçi · <sunucu> · N izinli şablon". Ardından **Araçlar ve yetkiler** ile
   hangi AI personelin hangi şablonu kullanacağını seçin.

## Şablon biçimi

```json
{
  "name": "cari_bakiye",
  "description": "Cari kartın bakiyesini döner",
  "kind": "READ",
  "max_rows": 1,
  "params": [{"name": "cari_kodu", "type": "string", "max_length": 30, "description": "Cari kodu"}],
  "sql": "SELECT ... WHERE C.CODE = :cari_kodu"
}
```

- `name`: küçük harf, rakam, `_`. `kind`: `READ` veya `WRITE`.
- `params[].type`: `string`, `integer`, `number`, `date` (YYYY-AA-GG), `boolean`; `"like": true` içerir araması yapar
  (joker karakterler kaçırılır; SQL'de `LIKE :ad ESCAPE '\'` kullanın).
- SQL'deki `:ad` yer tutucuları ile `params` listesi birebir aynı olmalı (ajan açılışta denetler).
- Logo tablo adları firma ve dönem numarası içerir (`LG_001_CLCARD`, `LG_001_01_CLFLINE`); şirketinize göre düzenleyin.

## Sahte Logo ile deneme

```
python fake_logo.py sahte_logo.db
python recorion_edge.py --config edge_config.example.json --once
```

Sahte veritabanı Logo tablo adlandırmasını taklit eder (cari kartlar, cari hareketler, stok kartları, ambar toplamları);
veriler uydurmadır. Gerçek şablonlar müşteri ortamında, müşterinin Logo/Mikro sürümüne göre yazılır.

## REST şablonları: Logo'ya Logo'nun kendi servisiyle yazma (sürüm 0.2.0, ADIM 12.5)

Logo/Mikro tablolarına doğrudan `INSERT` yapmak (ör. malzeme veya cari kartı) programın iç bütünlüğünü bozabilir
(referans numaraları, bağlı tablolar). Kayıt açma ve güncelleme için ürünün kendi programlama arayüzünü kullanın:
Logo için şirket ağındaki **Logo REST servisi**. Ajan bu servisi şirket ağının içinden çağırır; servisin internete
açılması gerekmez.

Yapılandırmaya `http_api` ekleyin (adres ve kimlik yalnızca bu sunucuda; parolalar ortam değişkeninde):

```json
"http_api": {
  "base_url": "http://logo-sunucu:32001",
  "auth": {"type": "oauth_password", "token_path": "/api/v1/token",
           "username_env": "LOGO_USER", "password_env": "LOGO_PASSWORD",
           "client_id_env": "LOGO_CLIENT_ID", "client_secret_env": "LOGO_CLIENT_SECRET",
           "form": {"firmno": "1"}}
}
```

`auth.type`: `none`, `bearer` (`token_env`), `basic` (`username_env`, `password_env`) veya `oauth_password` (yukarıdaki).
Oturum düşerse ajan bir kez yeniden giriş yapar.

Şablon (`sql` yerine `http`):

```json
{"name": "logo_malzeme_ekle", "kind": "WRITE", "result_id": "INTERNAL_REFERENCE",
 "params": [{"name": "kod", "type": "string", "max_length": 25}, {"name": "ad", "type": "string", "max_length": 51}],
 "http": {"method": "POST", "path": "/api/v1/items", "body": {"CODE": ":kod", "NAME": ":ad"}}}
```

- Yol `/` ile başlar; adres, `..` ve `?` içeremez. Yol parametresi `{ad}`, sorgu ve gövdede yer tutucu yalnızca tam değer
  olarak `":ad"` yazılır (metin birleştirme yok; değer türüyle yerleşir). Boş bırakılan isteğe bağlı parametrenin alanı
  gövdeye hiç konmaz.
- Okuma şablonu `GET`, yazma şablonu `POST/PUT/PATCH` olmalı. `result_list` liste yanıtın içindeki alanı, `result_id`
  kayıt kimliği alanını gösterir. Yazma şablonları `allow_write: true` olmadıkça bildirilmez ve çalışmaz.
- RECOrion'da eşleştirme için bir okuma şablonu (ör. `logo_malzeme_bul`) ve güncelleme için bir yazma şablonu
  (`logo_malzeme_guncelle`, `id` parametresiyle) tanımlanırsa aynı stok koduyla ikinci kart açılmaz, mevcut kart güncellenir.

`templates.logo_rest.example.json` malzeme ve cari kartı için **örnek** şablonlar içerir. Uç ve alan adları Logo REST servis
sürümüne göre değişebilir: kendi Logo REST servis belgenize göre doğrulayıp düzenleyin. Örnekler, gerçek Logo ile değil,
`fake_logo_rest.py` sahte servisiyle denenmiştir:

```
python fake_logo_rest.py 32001
set LOGO_USER=LOGO& set LOGO_PASSWORD=sahte-parola& set LOGO_CLIENT_ID=recorion& set LOGO_CLIENT_SECRET=sahte-istemci
python recorion_edge.py --config edge_config.json --once
```
