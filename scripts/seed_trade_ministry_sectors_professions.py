"""
Türkiye Ticaret Bakanlığı Sektör ve Meslek Tanımları Veri Aktarım Scripti
Excel Kaynağı: documents/Sektör Meslek Nace Kodları_2026.03.xlsx
"""
import asyncio
import os
import openpyxl
import asyncpg

EXCEL_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "documents", "Sektör Meslek Nace Kodları_2026.03.xlsx")

DB_USER = os.getenv("POSTGRES_USER", "recorion_admin")
DB_PASS = os.getenv("POSTGRES_PASSWORD", "recorion_secret_pass_2026")
DB_NAME = os.getenv("POSTGRES_DB", "recorion_db")
DB_HOST = os.getenv("POSTGRES_HOST", "localhost")
DB_PORT = int(os.getenv("POSTGRES_PORT", "5432"))


async def main():
    print(f"Reading Excel: {EXCEL_PATH}")
    wb = openpyxl.load_workbook(EXCEL_PATH, data_only=True)
    ws = wb.active

    sectors = {}
    professions = {}

    for row in ws.iter_rows(min_row=2, values_only=True):
        if not row or row[0] is None:
            continue
        sec_code = str(row[0]).strip()
        sec_name = str(row[1]).strip() if row[1] is not None else ""
        prof_code = str(row[2]).strip() if len(row) > 2 and row[2] is not None else ""
        prof_name = str(row[3]).strip() if len(row) > 3 and row[3] is not None else ""

        if sec_code and sec_name:
            sectors[sec_code] = sec_name
        if prof_code and prof_name:
            professions[prof_code] = {
                "code": prof_code,
                "sector_code": sec_code,
                "name": prof_name
            }

    print(f"Parsed {len(sectors)} unique sectors and {len(professions)} unique professions from Excel.")

    conn = await asyncpg.connect(
        user=DB_USER,
        password=DB_PASS,
        database=DB_NAME,
        host=DB_HOST,
        port=DB_PORT
    )

    try:
        # 1. Insert/Update Sectors
        print("Inserting sectors into database...")
        sector_insert_sql = """
            INSERT INTO sectors (code, name, is_active, created_at, updated_at)
            VALUES ($1, $2, TRUE, NOW(), NOW())
            ON CONFLICT (code) DO UPDATE
            SET name = EXCLUDED.name, is_active = TRUE, updated_at = NOW()
        """
        for code, name in sorted(sectors.items()):
            await conn.execute(sector_insert_sql, code, name)
        print(f"✓ {len(sectors)} sectors inserted/updated successfully.")

        # 2. Insert/Update Professions
        print("Inserting professions into database...")
        prof_insert_sql = """
            INSERT INTO professions (code, sector_code, name, is_active, created_at, updated_at)
            VALUES ($1, $2, $3, TRUE, NOW(), NOW())
            ON CONFLICT (code) DO UPDATE
            SET sector_code = EXCLUDED.sector_code, name = EXCLUDED.name, is_active = TRUE, updated_at = NOW()
        """
        for p in professions.values():
            await conn.execute(prof_insert_sql, p["code"], p["sector_code"], p["name"])
        print(f"✓ {len(professions)} professions inserted/updated successfully.")

        # Check final count in DB
        sec_count = await conn.fetchval("SELECT COUNT(*) FROM sectors")
        prof_count = await conn.fetchval("SELECT COUNT(*) FROM professions")
        print(f"VERIFIED IN DATABASE: {sec_count} sectors, {prof_count} professions.")

    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(main())
