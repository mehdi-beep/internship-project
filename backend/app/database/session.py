from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from config import get_settings

settings = get_settings()

# SQLite's DBAPI doesn't accept connect_timeout (a psycopg/Postgres kwarg) and
# instead needs check_same_thread=False under FastAPI's threaded request handling
# — the same flag run_dev_sqlite.py already passes when constructing its own engine.
# client_encoding is forced explicitly because some production hosts run very old
# Postgres servers (9.6) whose text-encoding negotiation with psycopg3 falls back
# to returning raw bytes instead of str for query results, which breaks
# SQLAlchemy's own str-based server-version regex on first connect.
connect_args = (
    {"check_same_thread": False} if settings.is_sqlite else {"connect_timeout": 5, "client_encoding": "UTF8"}
)

engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    connect_args=connect_args,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
