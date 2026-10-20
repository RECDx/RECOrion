# RECOrion Platform Departman ve Unvan Kataloğu

Bu klasördeki JSON dosyaları platform kataloğunun başlangıç verisidir (Odoo #271, ADIM 5.2).
Uygulama açılışında `app/services/catalog_seed.py` ile yüklenir; aynı `code` varsa Süper Admin'in
yaptığı düzenlemeler korunur (yalnızca yeni kayıtlar eklenir).

- `general.json`: her sektörde kullanılan genel departmanlar ve unvanlar (`scope: GENERAL`)
- `sector_<KOD>.json`: sektöre ve meslek gruplarına özel departmanlar ve unvanlar (`scope: SECTOR`)

Katalog bilgisi tüm müşterilere açık **Platform Unvan Bilgisi** katmanıdır: yalnızca genel, gizli
olmayan mesleki bilgi içerir; hiçbir şirkete ait veri içermez.

## Biçim

```json
{
  "scope": "SECTOR",                 // GENERAL veya SECTOR
  "sector_code": "A",                // GENERAL dosyasında null
  "departments": [
    {
      "code": "A_URETIM_ATOLYE",     // büyük harf, benzersiz; sektör dosyalarında "<SEKTÖR>_" ile başlar
      "name": "Üretim Atölyesi",
      "description": "1-2 cümle",
      "professions": ["A.03", "A.06"],   // bu departmanın tipik olduğu meslek grupları; [] = tüm sektör
      "titles": [
        {
          "code": "A_MOBILYA_URETIM_PLANLAMA_UZMANI",   // benzersiz, büyük harf
          "title": "Mobilya Üretim Planlama Uzmanı",
          "seniority": "MID",                 // JUNIOR, MID, SENIOR, LEAD, MANAGER
          "description": "İş tanımı, 2-3 cümle",
          "responsibilities": ["5-7 madde"],
          "skills": ["5-8 madde"],
          "kpis": ["3-5 madde"],
          "professions": ["A.06"],            // [] = departmanın tüm meslek grupları
          "recommended_model_code": "mimo-v2.6-pro",
          "autonomy_level": "L1",             // L1 öner+onay, L2 rutin işleri kendisi yapar, L3 tam otonom
          "role_prompt": "Türkçe sistem promptu, 150-300 kelime"
        }
      ]
    }
  ]
}
```

## Önerilen model kodları
- `mimo-v2.6-pro`: analiz, planlama, yönetim, hukuk, finans gibi akıl yürütme gerektiren işler
- `deepseek-v4.1-flash`: güçlü ve hızlı genel amaçlı işler, yazılım/teknik işler
- `deepseek-v4-flash`: rutin, yüksek hacimli işler (müşteri yanıtı, kayıt, sipariş takibi)
- `gemma-4-31b`: kısa metin, içerik ve yazışma işleri
- `qwen3-vl-30b`: görsel inceleme gerektiren işler (ürün fotoğrafı, kalite kontrol görseli, çizim)

## Rol promptu kuralları
AI personelin kim olduğunu, hangi şirket bağlamında çalıştığını ({{company_name}} ve {{department_name}}
yer tutucuları kullanılabilir), sorumluluklarını, çalışma biçimini (insan onayı gereken kararlar,
belirsizlikte soru sorma, uydurmama, kaynak gösterme), çıktı biçimini ve sınırlarını (KVKK, kişisel
veri, yetki dışı işlem yapmama) anlatır. Türkçe, "Sen ..." diye başlar.

## Genel departman kodları (general.json)
`GEN_YONETIM` Genel Yönetim · `GEN_FINANS` Finans · `GEN_MUHASEBE` Muhasebe · `GEN_IK` İnsan Kaynakları ·
`GEN_SATIS` Satış · `GEN_PAZARLAMA` Pazarlama ve Dijital Pazarlama · `GEN_MUSTERI` Müşteri Hizmetleri ·
`GEN_SATINALMA` Satın Alma · `GEN_LOJISTIK` Lojistik ve Depo · `GEN_BT` Bilgi Teknolojileri ·
`GEN_HUKUK` Hukuk ve Uyum · `GEN_KALITE` Kalite Yönetimi · `GEN_ISG` İş Sağlığı ve Güvenliği ·
`GEN_IDARI` İdari İşler · `GEN_ARGE` AR-GE ve İnovasyon · `GEN_OPERASYON` Operasyon

Sektör dosyasında `code` değeri `GEN_` ile başlayan bir departman yeni departman açmaz: içindeki
sektöre özel unvanlar o genel departmana eklenir (`name`/`description` verilmesi gerekmez).
