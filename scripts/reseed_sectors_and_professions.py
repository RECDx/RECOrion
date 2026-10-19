"""
Türkiye Ticaret Bakanlığı Sektör ve Meslek Tanımları Veri Aktarımı (Temizleme ve Yeniden Yükleme)
Excel Kaynağı: documents/Sektör Meslek Nace Kodları_2026.03.xlsx

Adımlar:
1. Sektör ve Meslek Grubu tablolarını tamamen boşalt.
2. Excel'deki bütün Sektör tanımlarını (Sektör Kodu, Sektör Adı) al ve veritabanına ekle.
3. Excel'deki bütün Meslek Grubu tanımlarını (Meslek Kodu, Sektör Kodu, Meslek Tanım Adı) al ve veritabanına ekle.
4. Doğrulama yap ve özet rapor ver.
"""
import asyncio
import os
import openpyxl
import asyncpg

EXCEL_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "documents", "Sektör Meslek Nace Kodları_2026.03.xlsx")

DB_USER = os.getenv("POSTGRES_USER", "recorion_admin")
DB_PASS = os.getenv("POSTGRES_PASSWORD", "")
DB_NAME = os.getenv("POSTGRES_DB", "recorion_db")
DB_HOST = os.getenv("POSTGRES_HOST", "localhost")
DB_PORT = int(os.getenv("POSTGRES_PORT", "5432"))

SECTOR_ICONS = {
    "A": "🌲",  # Ağaç İşleri
    "B": "🎭",  # Eğlence, Dinlenme, Organizasyon
    "C": "💻",  # Elektrik, Elektronik, Bilgisayar
    "D": "🌾",  # Gıda, Tarım
    "E": "👗",  # Giyim, Deri Ürün, Ev Tekstili, Dokuma
    "F": "🎁",  # Hediyelik Eşya, Eğitim, Basım, Fotoğraf, Çeşitli Mallar
    "G": "✂️",  # Kuaför, Berber, Temizlik, Spor, Kozmetik, Sağlık
    "H": "🚗",  # Metal, Otomotiv, Makine
    "I": "🛒",  # Pazar, Seyyar
    "J": "🚚",  # Ulaştırma Hizmetleri
    "K": "🏗️",  # Yapı Sanatları
}

async def main():
    print(f"Excel Dosyası Okunuyor: {EXCEL_PATH}")
    if not os.path.exists(EXCEL_PATH):
        raise FileNotFoundError(f"Excel dosyası bulunamadı: {EXCEL_PATH}")

    wb = openpyxl.load_workbook(EXCEL_PATH, data_only=True)
    ws = wb['Sheet0']
    print(f"Toplam Satır: {ws.max_row}, Sütun: {ws.max_column}")

    # 1. Sektörleri Çıkar
    sectors_map = {}
    for r in range(2, ws.max_row + 1):
        c0 = ws.cell(r, 1).value
        c1 = ws.cell(r, 2).value
        if c0 is not None and c1 is not None:
            sec_code = str(c0).strip()
            sec_name = str(c1).strip()
            if sec_code and sec_name and sec_code not in sectors_map:
                sectors_map[sec_code] = sec_name

    # 2. Meslek Gruplarını Çıkar
    professions_map = {}
    for r in range(2, ws.max_row + 1):
        c0 = ws.cell(r, 1).value
        c2 = ws.cell(r, 3).value
        c3 = ws.cell(r, 4).value
        if c0 is not None and c2 is not None and c3 is not None:
            sec_code = str(c0).strip()
            prof_code = str(c2).strip()
            prof_name = str(c3).strip()
            if sec_code and prof_code and prof_name:
                if prof_code not in professions_map:
                    professions_map[prof_code] = {
                        "code": prof_code,
                        "sector_code": sec_code,
                        "name": prof_name
                    }

    print(f"\n[EXCEL ANALİZİ]")
    print(f"-> Tespit Edilen Sektör Sayısı: {len(sectors_map)}")
    print(f"-> Tespit Edilen Meslek Grubu Sayısı: {len(professions_map)}")

    # Veritabanı Bağlantısı
    conn = await asyncpg.connect(
        user=DB_USER,
        password=DB_PASS,
        database=DB_NAME,
        host=DB_HOST,
        port=DB_PORT
    )

    try:
        # ADIM 1: Sektör ve Meslek Grubu Bilgilerini Tamamen Boşalt
        print("\n--- ADIM 1: Veritabanındaki Sektör ve Meslek Grubu Bilgileri Boşaltılıyor ---")
        del_prof = await conn.execute("DELETE FROM professions;")
        print(f"✓ professions tablosu temizlendi ({del_prof}).")
        del_sec = await conn.execute("DELETE FROM sectors;")
        print(f"✓ sectors tablosu temizlendi ({del_sec}).")

        # ADIM 2: Önce Sektör Bilgilerinin Hepsini Ekle
        print("\n--- ADIM 2: Sektör Bilgilerinin Hepsi Ekleniyor ---")
        sector_insert_sql = """
            INSERT INTO sectors (code, name, icon, is_active, created_at, updated_at)
            VALUES ($1, $2, $3, TRUE, NOW(), NOW())
        """
        for sc in sorted(sectors_map.keys()):
            sname = sectors_map[sc]
            icon = SECTOR_ICONS.get(sc, "📁")
            await conn.execute(sector_insert_sql, sc, sname, icon)
            print(f"  + Sektör [{sc}] {sname} eklendi.")

        sec_count = await conn.fetchval("SELECT count(*) FROM sectors;")
        print(f"✓ Toplam {sec_count} sektör başarıyla kaydedildi.")

        # ADIM 3: Sonra Bütün Meslek Grup Tanım Bilgilerini Ekle
        print("\n--- ADIM 3: Bütün Meslek Grup Tanım Bilgileri Ekleniyor ---")
        prof_insert_sql = """
            INSERT INTO professions (code, sector_code, name, is_active, created_at, updated_at)
            VALUES ($1, $2, $3, TRUE, NOW(), NOW())
        """
        for pc in sorted(professions_map.keys()):
            p_data = professions_map[pc]
            await conn.execute(prof_insert_sql, p_data["code"], p_data["sector_code"], p_data["name"])

        prof_count = await conn.fetchval("SELECT count(*) FROM professions;")
        print(f"✓ Toplam {prof_count} meslek grubu başarıyla kaydedildi.")

        # ADIM 4: Detaylı Doğrulama ve Sektör Bazında Meslek Sayısı Kontrolü
        print("\n--- ADIM 4: Doğrulama ve Kontrol ---")
        sector_breakdown = await conn.fetch("""
            SELECT s.code, s.name, count(p.code) as prof_count
            FROM sectors s
            LEFT JOIN professions p ON s.code = p.sector_code
            GROUP BY s.code, s.name
            ORDER BY s.code;
        """)
        for sb in sector_breakdown:
            print(f"  [{sb['code']}] {sb['name']} -> {sb['prof_count']} Meslek Grubu")

        # YAPI SANATLARI (K) Özel Kontrol
        k_profs = await conn.fetch("""
            SELECT code, name FROM professions WHERE sector_code = 'K' ORDER BY code;
        """)
        print(f"\n[ÖZEL KONTROL: YAPI SANATLARI (K) Meslek Grupları ({len(k_profs)} adet)]:")
        for kp in k_profs:
            print(f"    - [{kp['code']}] {kp['name']}")

    finally:
        await conn.close()
        print("\nVeritabanı bağlantısı kapatıldı. İşlem başarıyla tamamlandı.")

if __name__ == "__main__":
    asyncio.run(main())
