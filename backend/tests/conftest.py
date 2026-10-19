"""
Test altyapısı.

Testler ana veritabanına dokunmaz: her çalıştırmada aynı Postgres sunucusunda
`<ana_db>_test` veritabanı sıfırdan oluşturulur ve `alembic upgrade head` ile
kurulur. Böylece her test koşusu aynı zamanda "temiz kurulum" testidir.

Çalıştırma (backend container içinde):  pytest -q
"""
import os
import subprocess
from pathlib import Path

import psycopg2
import pytest
from sqlalchemy.engine import make_url

BACKEND_DIR = Path(__file__).resolve().parent.parent


def _base_url():
    from app.config import settings  # yalnızca ana bağlantı bilgisini okumak için
    return make_url(settings.get_database_url())


BASE_URL = _base_url()
TEST_DB_NAME = f"{BASE_URL.database}_test"
TEST_ASYNC_URL = BASE_URL.set(database=TEST_DB_NAME).render_as_string(hide_password=False)

# Uygulama modülleri import edilmeden önce test veritabanına yönlendir
os.environ["DATABASE_URL"] = TEST_ASYNC_URL
os.environ["DEBUG"] = "false"
from app.config import settings  # noqa: E402

settings.DATABASE_URL = TEST_ASYNC_URL
settings.DEBUG = False


def _admin_connect():
    conn = psycopg2.connect(
        host=BASE_URL.host, port=BASE_URL.port or 5432, user=BASE_URL.username,
        password=BASE_URL.password, dbname="postgres",
    )
    conn.autocommit = True
    return conn


def recreate_database(name: str) -> str:
    """Boş bir veritabanı oluşturur ve asyncpg URL'sini döner."""
    assert name.endswith("_test"), "Güvenlik: yalnızca *_test veritabanları silinebilir."
    conn = _admin_connect()
    try:
        with conn.cursor() as cur:
            cur.execute(f'DROP DATABASE IF EXISTS "{name}" WITH (FORCE)')
            cur.execute(f'CREATE DATABASE "{name}"')
    finally:
        conn.close()
    return BASE_URL.set(database=name).render_as_string(hide_password=False)


def drop_database(name: str) -> None:
    assert name.endswith("_test")
    conn = _admin_connect()
    try:
        with conn.cursor() as cur:
            cur.execute(f'DROP DATABASE IF EXISTS "{name}" WITH (FORCE)')
    finally:
        conn.close()


def alembic_upgrade(db_url: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["alembic", "-x", f"dburl={db_url}", "upgrade", "head"],
        cwd=BACKEND_DIR, capture_output=True, text=True,
    )


def sync_connect(db_url: str):
    u = make_url(db_url)
    return psycopg2.connect(host=u.host, port=u.port or 5432, user=u.username, password=u.password, dbname=u.database)


@pytest.fixture(scope="session")
def test_db_url():
    url = recreate_database(TEST_DB_NAME)
    result = alembic_upgrade(url)
    assert result.returncode == 0, f"alembic upgrade başarısız:\n{result.stderr}"
    yield url
    drop_database(TEST_DB_NAME)


@pytest.fixture(scope="session")
def db(test_db_url):
    conn = sync_connect(test_db_url)
    conn.autocommit = True
    yield conn
    conn.close()


@pytest.fixture(scope="session")
def client(test_db_url):
    from fastapi.testclient import TestClient
    from app.main import app

    with TestClient(app) as c:
        yield c
