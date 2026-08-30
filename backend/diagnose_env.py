"""One-off diagnostic: lists what actually exists in the target Postgres
database right now (tables, types, alembic version), to find out why
'type role_name already exists' persists even after recreating the
database. Delete after use.
"""

import psycopg

from config import get_settings

settings = get_settings()
raw_url = settings.database_url.replace("postgresql+psycopg://", "postgresql://")

conn = psycopg.connect(raw_url, client_encoding="UTF8")

print("--- current_database() ---")
print(conn.execute("SELECT current_database()").fetchone())

print("--- tables in public schema ---")
for row in conn.execute(
    "SELECT tablename FROM pg_tables WHERE schemaname = 'public'"
).fetchall():
    print(row)

print("--- custom types in public schema ---")
for row in conn.execute(
    "SELECT typname FROM pg_type t JOIN pg_namespace n ON t.typnamespace = n.oid "
    "WHERE n.nspname = 'public' AND t.typtype = 'e'"
).fetchall():
    print(row)

conn.close()
