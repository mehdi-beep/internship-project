"""One-off diagnostic: checks for a connection pooler (PgBouncer etc.)
sitting between us and real Postgres, and opens TWO separate
connections back-to-back to see if they report different backend PIDs
or different visible state -- the smoking gun for "one script sees an
empty DB, the other sees pre-existing objects" despite identical
connection strings. Delete after use.
"""

import psycopg

from config import get_settings

settings = get_settings()
raw_url = settings.database_url.replace("postgresql+psycopg://", "postgresql://")


def snapshot(label: str) -> None:
    conn = psycopg.connect(raw_url, client_encoding="UTF8")
    pid = conn.execute("SELECT pg_backend_pid()").fetchone()
    version = conn.execute("SHOW server_version").fetchone()
    types = conn.execute(
        "SELECT typname FROM pg_type t JOIN pg_namespace n ON t.typnamespace = n.oid "
        "WHERE n.nspname = 'public' AND t.typtype = 'e'"
    ).fetchall()
    print(f"[{label}] backend_pid={pid} server_version={version} custom_types={types}")
    conn.close()


snapshot("connection 1")
snapshot("connection 2")
snapshot("connection 3")
