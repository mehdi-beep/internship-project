from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from app.database import Base
from app.models import *  # noqa: F401,F403  ensures models are registered on Base.metadata
from config import get_settings

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

settings = get_settings()
config.set_main_option("sqlalchemy.url", settings.database_url)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    # client_encoding is forced explicitly for the same reason as in
    # app/database/session.py: some production hosts run Postgres 9.6, whose
    # text-encoding negotiation with psycopg3 can return raw bytes instead of
    # str, which breaks SQLAlchemy's own str-based server-version regex on
    # first connect. Skipped for SQLite, which doesn't accept this kwarg.
    connect_args = {} if settings.is_sqlite else {"client_encoding": "UTF8"}
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        connect_args=connect_args,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
