"""One-off diagnostic: tests whether explicitly setting client_encoding
fixes psycopg3 returning bytes instead of str against this old Postgres
9.6 server (which breaks SQLAlchemy's version-string regex). Delete
after use.
"""

import psycopg

from config import get_settings

settings = get_settings()
raw_url = settings.database_url.replace("postgresql+psycopg://", "postgresql://")

print("--- without client_encoding ---")
conn = psycopg.connect(raw_url)
print(type(conn.execute("SELECT version()").fetchone()[0]))
conn.close()

print("--- with client_encoding=UTF8 ---")
conn2 = psycopg.connect(raw_url, client_encoding="UTF8")
result = conn2.execute("SELECT version()").fetchone()[0]
print(type(result), result)
conn2.close()
