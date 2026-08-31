"""One-off diagnostic: confirms the full seed actually landed correctly
by checking real row counts and that a login-relevant user exists.
Delete after use.
"""

import psycopg

from config import get_settings

settings = get_settings()
raw_url = settings.database_url.replace("postgresql+psycopg://", "postgresql://")
conn = psycopg.connect(raw_url, client_encoding="UTF8")

tables = [
    "roles", "users", "clients", "client_sites", "contracts", "projects",
    "travaux", "interventions", "planning", "point_rules", "notifications",
]
for t in tables:
    count = conn.execute(f"SELECT count(*) FROM {t}").fetchone()[0]
    print(f"{t}: {count}")

print("--- role names ---")
print(conn.execute("SELECT name FROM roles ORDER BY id").fetchall())

print("--- sample usernames per role ---")
print(
    conn.execute(
        "SELECT u.username, r.name FROM users u JOIN roles r ON u.role_id = r.id ORDER BY r.name, u.username"
    ).fetchall()
)

conn.close()
