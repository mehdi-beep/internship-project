"""One-off diagnostic: full row counts across every table, to see
exactly how partially-seeded the production database currently is
before deciding how to get it to a genuinely complete state. Delete
after use.
"""

import psycopg

from config import get_settings

settings = get_settings()
raw_url = settings.database_url.replace("postgresql+psycopg://", "postgresql://")
conn = psycopg.connect(raw_url, client_encoding="UTF8")

tables = [
    "roles", "users", "clients", "client_sites", "contracts", "projects",
    "travaux", "interventions", "planning", "point_rules", "notifications",
    "approval_history", "audit_log", "attachments",
]
for t in tables:
    count = conn.execute(f"SELECT count(*) FROM {t}").fetchone()[0]
    print(f"{t}: {count}")

print("--- role names present ---")
print(conn.execute("SELECT name FROM roles ORDER BY id").fetchall())

conn.close()
