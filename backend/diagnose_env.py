"""One-off diagnostic: checks whether tech01's stored password hash on
production actually verifies against "Password123!", to rule in/out a
seeding or hashing issue vs. a stale backend process. Delete after use.
"""

import psycopg

from app.authentication.password import verify_password
from config import get_settings

settings = get_settings()
raw_url = settings.database_url.replace("postgresql+psycopg://", "postgresql://")
conn = psycopg.connect(raw_url, client_encoding="UTF8")

row = conn.execute("SELECT username, password_hash, active FROM users WHERE username = 'tech01'").fetchone()
print("row exists:", row is not None)
if row:
    username, password_hash, active = row
    print("username:", username)
    print("active:", active)
    print("verifies against 'Password123!':", verify_password("Password123!", password_hash))

conn.close()
