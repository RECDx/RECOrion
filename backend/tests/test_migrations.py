"""Migrasyon ve temiz kurulum testleri."""
from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from sqlalchemy import create_engine

from tests.conftest import alembic_upgrade, drop_database, recreate_database, sync_connect

EXPECTED_TABLES = {
    "actors", "agent_documents", "approval_group_members", "approval_groups", "artifacts", "audit_events",
    "chat_messages", "debate_threads", "departments", "email_templates", "job_titles", "llm_calls",
    "llm_models", "llm_providers", "memory_items", "notification_schedules", "plans", "professions",
    "projects", "sectors", "system_permissions", "system_settings", "tasks", "tenant_leads",
    "tenant_roles", "tenants",
}


def _scalar(db, sql, *params):
    with db.cursor() as cur:
        cur.execute(sql, params)
        return cur.fetchone()[0]


def test_fresh_install_creates_all_tables(db):
    with db.cursor() as cur:
        cur.execute("SELECT tablename FROM pg_tables WHERE schemaname = 'public'")
        tables = {r[0] for r in cur.fetchall()}
    missing = EXPECTED_TABLES - tables
    assert not missing, f"Eksik tablolar: {missing}"
    assert _scalar(db, "SELECT version_num FROM alembic_version") is not None


def test_reference_data_seeded(db):
    assert _scalar(db, "SELECT count(*) FROM sectors") == 11
    assert _scalar(db, "SELECT count(*) FROM professions") == 184
    assert _scalar(db, "SELECT count(*) FROM professions WHERE sector_code = 'K'") == 15
    assert _scalar(db, "SELECT count(*) FROM llm_providers WHERE code = 'EVREN'") == 1
    assert _scalar(db, "SELECT count(*) FROM llm_models") == 15
    assert _scalar(db, "SELECT count(*) FROM plans") == 3
    assert _scalar(db, "SELECT count(*) FROM system_permissions") == 25
    assert _scalar(db, "SELECT count(*) FROM email_templates WHERE code IN ('WELCOME_CUSTOMER', 'PACKAGE_EXPIRATION_REMINDER')") == 2
    assert _scalar(db, "SELECT count(*) FROM notification_schedules") == 2
    assert _scalar(db, "SELECT count(*) FROM tenants WHERE slug = 'recdx_hq'") == 1


def test_upgrade_is_idempotent(test_db_url, db):
    before = _scalar(db, "SELECT count(*) FROM llm_models")
    result = alembic_upgrade(test_db_url)
    assert result.returncode == 0, result.stderr
    assert _scalar(db, "SELECT count(*) FROM llm_models") == before


def test_orm_models_match_database(test_db_url):
    """ORM'de tanımlı olup veritabanında olmayan tablo/kolon kalmamalı (şema kayması)."""
    from app.db.session import Base
    from app.db import models  # noqa: F401

    engine = create_engine(test_db_url.replace("+asyncpg", "+psycopg2"))
    try:
        with engine.connect() as conn:
            diffs = compare_metadata(MigrationContext.configure(conn), Base.metadata)
    finally:
        engine.dispose()

    def flatten(items):
        for d in items:
            if isinstance(d, list):
                yield from flatten(d)
            else:
                yield d

    missing = [d for d in flatten(diffs) if d[0] in ("add_table", "add_column")]
    assert not missing, f"ORM ile veritabanı uyuşmuyor: {missing}"


def test_existing_database_is_adopted_without_changes():
    """Tabloları önceden var olan (Alembic öncesi) bir veritabanı veri kaybı olmadan devralınır."""
    name = "recorion_adopt_test"
    url = recreate_database(name)
    try:
        conn = sync_connect(url)
        conn.autocommit = True
        from pathlib import Path
        sql = (Path(__file__).resolve().parent.parent / "migrations/sql/0001_baseline_schema.sql").read_text(encoding="utf-8")
        with conn.cursor() as cur:
            cur.execute(sql)
            cur.execute("INSERT INTO plans (code, name) VALUES ('CUSTOM', 'Elle Eklenmiş Paket')")

        result = alembic_upgrade(url)
        assert result.returncode == 0, result.stderr

        # Dolu tabloya seed eklenmemeli, boş tablolar doldurulmalı
        assert _scalar(conn, "SELECT count(*) FROM plans") == 1
        assert _scalar(conn, "SELECT count(*) FROM sectors") == 11
        conn.close()
    finally:
        drop_database(name)
