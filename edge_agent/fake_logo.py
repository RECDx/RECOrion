"""
Sahte Logo Tiger veritabanı (SQLite) — Edge Connector'ı gerçek müşteri ortamı olmadan sınamak için (ADIM 10.5).

Logo'nun tablo adlandırması taklit edilir: LG_<firma>_CLCARD (cari kartlar), LG_<firma>_ITEMS (stok kartları),
LG_<firma>_<dönem>_CLFLINE (cari hareketler; SIGN 0 = borç, 1 = alacak), LG_<firma>_<dönem>_GNTOTST (ambar toplamları;
INVENNO -1 = tüm ambarlar). Firma 001, dönem 01. Veriler uydurmadır.

    python fake_logo.py sahte_logo.db
"""
import sqlite3
import sys

CARDS = [(1, "120.01.001", "ABC Makine Sanayi Ltd. Şti.", "İstanbul"), (2, "120.01.002", "Deniz Gıda A.Ş.", "İzmir"),
         (3, "120.01.003", "Anadolu Yapı Market", "Ankara"), (4, "320.01.001", "Kuzey Lojistik A.Ş.", "Kocaeli")]
LINES = [(1, 1, "2026-09-02", 125000.00, 0), (2, 1, "2026-09-20", 40000.00, 1), (3, 1, "2026-10-05", 18500.50, 0),
         (4, 2, "2026-09-11", 72000.00, 0), (5, 2, "2026-10-01", 72000.00, 1), (6, 3, "2026-10-12", 9800.00, 0),
         (7, 4, "2026-10-03", 30000.00, 1)]
ITEMS = [(1, "STK-001", "Rulman 6204", "ADET"), (2, "STK-002", "Hidrolik Pompa HP-40", "ADET"), (3, "STK-003", "Çelik Profil 40x40", "MT")]
TOTALS = [(1, 1, -1, 1240), (2, 1, 0, 800), (3, 1, 1, 440), (4, 2, -1, 6), (5, 3, -1, 315.5)]


def build(path: str) -> None:
    con = sqlite3.connect(path)
    con.executescript("""
        DROP TABLE IF EXISTS LG_001_CLCARD; DROP TABLE IF EXISTS LG_001_01_CLFLINE;
        DROP TABLE IF EXISTS LG_001_ITEMS; DROP TABLE IF EXISTS LG_001_01_GNTOTST; DROP TABLE IF EXISTS RECORION_NOTLAR;
        CREATE TABLE LG_001_CLCARD (LOGICALREF INTEGER PRIMARY KEY, CODE TEXT UNIQUE, DEFINITION_ TEXT, CITY TEXT, ACTIVE INTEGER DEFAULT 0);
        CREATE TABLE LG_001_01_CLFLINE (LOGICALREF INTEGER PRIMARY KEY, CLIENTREF INTEGER, DATE_ TEXT, AMOUNT REAL, SIGN INTEGER);
        CREATE TABLE LG_001_ITEMS (LOGICALREF INTEGER PRIMARY KEY, CODE TEXT UNIQUE, NAME TEXT, UNIT TEXT);
        CREATE TABLE LG_001_01_GNTOTST (LOGICALREF INTEGER PRIMARY KEY, STOCKREF INTEGER, INVENNO INTEGER, ONHAND REAL);
        CREATE TABLE RECORION_NOTLAR (ID INTEGER PRIMARY KEY AUTOINCREMENT, CARI_KODU TEXT, NOT_ TEXT, TARIH TEXT DEFAULT CURRENT_TIMESTAMP);
    """)
    con.executemany("INSERT INTO LG_001_CLCARD (LOGICALREF, CODE, DEFINITION_, CITY) VALUES (?,?,?,?)", CARDS)
    con.executemany("INSERT INTO LG_001_01_CLFLINE VALUES (?,?,?,?,?)", LINES)
    con.executemany("INSERT INTO LG_001_ITEMS VALUES (?,?,?,?)", ITEMS)
    con.executemany("INSERT INTO LG_001_01_GNTOTST VALUES (?,?,?,?)", TOTALS)
    con.commit()
    con.close()


if __name__ == "__main__":
    build(sys.argv[1] if len(sys.argv) > 1 else "sahte_logo.db")
    print("Sahte Logo veritabanı hazır.")
