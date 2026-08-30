"""One-off diagnostic: confirms the migration actually built the full
schema, not just an empty alembic_version row. Delete after use.
"""

import psycopg

from config import get_settings

settings = get_settings()
raw_url = settings.database_url.replace("postgresql+psycopg://", "postgresql://")
conn = psycopg.connect(raw_url, client_encoding="UTF8")

tables = conn.execute(
    "SELECT tablename FROM pg_tables WHERE schemaname = 'public' ORDER BY tablename"
).fetchall()
print(f"--- {len(tables)} tables ---")
for row in tables:
    print(row[0])

print("--- alembic_version ---")
print(conn.execute("SELECT version_num FROM alembic_version").fetchone())

print("--- roles seeded? ---")
print(conn.execute("SELECT count(*) FROM roles").fetchone())
print("--- users seeded? ---")
print(conn.execute("SELECT count(*) FROM users").fetchone())

conn.close()
