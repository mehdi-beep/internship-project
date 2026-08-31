"""One-off diagnostic: confirms the real travaux catalog and CEO
account actually landed on production. Delete after use.
"""

import psycopg

from config import get_settings

settings = get_settings()
raw_url = settings.database_url.replace("postgresql+psycopg://", "postgresql://")
conn = psycopg.connect(raw_url, client_encoding="UTF8")

print("--- travaux count ---")
print(conn.execute("SELECT count(*) FROM travaux").fetchone())
print("--- sample travaux codes ---")
print(conn.execute("SELECT travail_code, travail_name FROM travaux ORDER BY id LIMIT 5").fetchall())
print("--- CEO account ---")
print(
    conn.execute(
        "SELECT u.username, u.email, r.name FROM users u JOIN roles r ON u.role_id = r.id WHERE r.name = 'ceo'"
    ).fetchall()
)

conn.close()
