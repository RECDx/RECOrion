# Veritabanı Migrasyonları (Alembic)

Şema ve referans verisi bu klasördeki migrasyonlarla yönetilir. Backend container'ı
her açılışta `alembic upgrade head` ve ardından `python -m app.bootstrap` çalıştırır.

| Sürüm | İçerik |
|---|---|
| 0001 | Başlangıç şeması (`sql/0001_baseline_schema.sql`). Tablolar zaten varsa atlanır. |
| 0002 | Referans verisi: EVREN modelleri, paketler, 11 sektör / 184 meslek, izinler, mail şablonları, zamanlamalar, RECDx ana şirketi. Yalnızca boş tablolar doldurulur. |

## Yeni migrasyon eklemek

1. `app/db/models.py` içinde modeli değiştir.
2. Container içinde: `alembic revision --autogenerate -m "kisa_aciklama"`
3. Üretilen dosyayı gözden geçir (autogenerate her şeyi yakalamaz).
4. `pytest -q` ile temiz kurulum ve ORM-veritabanı uyum testlerini çalıştır.

## Sıfırdan kurulumda süper adminler

`.env` içine `RECORION_SUPERADMIN_EMAILS` ve `RECORION_SUPERADMIN_INITIAL_PASSWORD`
yazılırsa bootstrap bu kullanıcıları RECDx ana şirketine ekler. Mevcut kullanıcılara dokunmaz.
