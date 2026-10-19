"""
Türkiye Ticaret Bakanlığı Sektör ve Meslek Tanımları Veritabanı Yeniden Yükleme Scripti
1. Sektör ve Meslek Grubu tablolarını boşaltır.
2. trade_ministry_catalog.json dosyasından önce Sektör bilgilerinin tamamını yükler.
3. Sonra bütün Meslek Grubu tanımlarını yükler.
4. Doğrulama ve detaylı rapor çıktısı verir.
"""
import asyncio
import json
import os
import asyncpg

CATALOG_JSON_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "trade_ministry_catalog.json")

DB_USER = os.getenv("POSTGRES_USER", "recorion_admin")
DB_PASS = os.getenv("POSTGRES_PASSWORD", "")
DB_NAME = os.getenv("POSTGRES_DB", "recorion_db")
DB_HOST = os.getenv("POSTGRES_HOST", "recorion_postgres")
DB_PORT = int(os.getenv("POSTGRES_PORT", "5432"))

async def reseed():
    print(f"Reading catalog JSON: {CATALOG_JSON_PATH}")
    with open(CATALOG_JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    sectors = data.get("sectors", [])
    professions = data.get("professions", [])

    print(f"Found {len(sectors)} sectors and {len(professions)} professions in JSON.")

    print(f"Connecting to database at {DB_HOST}:{DB_PORT}/{DB_NAME} as {DB_USER}...")
    conn = await asyncpg.connect(
        user=DB_USER,
        password=DB_PASS,
        database=DB_NAME,
        host=DB_HOST,
        port=DB_PORT
    )

    try:
        # ADIM 1: Sektör ve Meslek Grubu tablolarını tamamen boşalt
        print("\n[ADIM 1] Tablolar boşaltılıyor...")
        del_p = await conn.execute("DELETE FROM professions;")
        print(f"  - professions tablosu boşaltıldı: {del_p}")
        del_s = await conn.execute("DELETE FROM sectors;")
        print(f"  - sectors tablosu boşaltıldı: {del_s}")

        # Tablo sayaçlarını kontrol et
        cnt_p = await conn.fetchval("SELECT count(*) FROM professions;")
        cnt_s = await conn.fetchval("SELECT count(*) FROM sectors;")
        print(f"  Kontrol: DB'de şu an {cnt_s} sektör ve {cnt_p} meslek grubu mevcut (tamamen boşaltıldı).")

        # ADIM 2: Önce Sektör bilgilerinin hepsini al ve ekle
        print("\n[ADIM 2] Sektör bilgilerinin tümü ekleniyor...")
        sec_sql = """
            INSERT INTO sectors (code, name, icon, is_active, created_at, updated_at)
            VALUES ($1, $2, $3, TRUE, NOW(), NOW())
        """
        for s in sectors:
            await conn.execute(sec_sql, s["code"], s["name"], s.get("icon", "📁"))
            print(f"  + Sektör [{s['code']}] {s['name']} kaydedildi.")

        total_sec = await conn.fetchval("SELECT count(*) FROM sectors;")
        print(f"  -> {total_sec} sektör veritabanına başarıyla yazıldı.")

        # ADIM 3: Sonra bütün meslek grup tanım bilgilerini al ve ekle
        print("\n[ADIM 3] Meslek grubu tanımlarının tümü ekleniyor...")
        prof_sql = """
            INSERT INTO professions (code, sector_code, name, is_active, created_at, updated_at)
            VALUES ($1, $2, $3, TRUE, NOW(), NOW())
        """
        for p in professions:
            await conn.execute(prof_sql, p["code"], p["sector_code"], p["name"])

        total_prof = await conn.fetchval("SELECT count(*) FROM professions;")
        print(f"  -> {total_prof} meslek grubu veritabanına başarıyla yazıldı.")

        # ADIM 4: Sektör bazında meslek sayıları dökümü
        print("\n[ADIM 4] Sektör Bazında Meslek Grubu Dağılımı:")
        rows = await conn.fetch("""
            SELECT s.code, s.name, count(p.code) as p_count
            FROM sectors s
            LEFT JOIN professions p ON s.code = p.sector_code
            GROUP BY s.code, s.name
            ORDER BY s.code;
        """)
        for r in rows:
            print(f"  Sektör [{r['code']}] {r['name']}: {r['p_count']} Meslek Grubu")

        # YAPI SANATLARI (K) meslek tanımları listesi
        k_profs = await conn.fetch("""
            SELECT code, name FROM professions WHERE sector_code = 'K' ORDER BY code;
        """)
        print(f"\n[YAPI SANATLARI (K) Meslek Tanımları]: Toplam {len(k_profs)} meslek")
        for kp in k_profs:
            print(f"    * [{kp['code']}] {kp['name']}")

    finally:
        await conn.close()
        print("\nİşlem başarıyla tamamlandı.")

if __name__ == "__main__":
    asyncio.run(reseed())
