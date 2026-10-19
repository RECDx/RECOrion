"""
RECOrion Alembic ortamı.

Uygulama asyncpg kullanır; migrasyonlar ise çoklu SQL ifadesi çalıştırabilmek için
aynı veritabanına senkron psycopg2 sürücüsüyle bağlanır.
Hedef veritabanı varsayılan olarak .env'deki DATABASE_URL'dir; testler
`alembic -x dburl=...` ile başka bir veritabanı verebilir.
"""
from alembic import context
from sqlalchemy import create_engine, pool

from app.config import settings
from app.db.session import Base
from app.db import models  # noqa: F401  (modelleri metadata'ya kaydeder)

config = context.config
target_metadata = Base.metadata


def get_sync_url() -> str:
    url = context.get_x_argument(as_dictionary=True).get("dburl") or settings.get_database_url()
    return url.replace("postgresql+asyncpg://", "postgresql+psycopg2://", 1)


def run_migrations_offline() -> None:
    context.configure(url=get_sync_url(), target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    engine = create_engine(get_sync_url(), poolclass=pool.NullPool)
    with engine.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
