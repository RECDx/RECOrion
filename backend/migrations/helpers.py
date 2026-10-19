"""Migrasyonlarda ortak kullanılan yardımcılar."""
from pathlib import Path

from alembic import op
import sqlalchemy as sa

SQL_DIR = Path(__file__).parent / "sql"
DATA_DIR = Path(__file__).parent / "data"


def run_sql_file(name: str) -> None:
    """SQL dosyasını olduğu gibi çalıştırır.

    Ham DBAPI imleci kullanılır: SQLAlchemy text() HTML/CSS içindeki ':isim'
    kalıplarını parametre sanar, psycopg2 ise parametresiz çağrıda metne dokunmaz.
    """
    sql = (SQL_DIR / name).read_text(encoding="utf-8")
    cursor = op.get_bind().connection.cursor()
    try:
        cursor.execute(sql)
    finally:
        cursor.close()


def table_exists(name: str) -> bool:
    return sa.inspect(op.get_bind()).has_table(name)


def table_is_empty(name: str) -> bool:
    return op.get_bind().execute(sa.text(f'SELECT NOT EXISTS (SELECT 1 FROM "{name}")')).scalar()
