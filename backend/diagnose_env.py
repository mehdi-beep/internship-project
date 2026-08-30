"""One-off diagnostic: prints exactly what DATABASE_URL config the app
sees, with the password redacted, plus where it's actually reading
from. Delete after use.
"""

import os
import re
from pathlib import Path

import psycopg
import sqlalchemy

print("cwd:", os.getcwd())
print("script dir:", Path(__file__).parent.resolve())
print(".env exists at script dir:", (Path(__file__).parent / ".env").exists())
print("DATABASE_URL in raw os.environ:", "DATABASE_URL" in os.environ)
print("sqlalchemy version:", sqlalchemy.__version__)
print("psycopg version:", psycopg.__version__)

from config import get_settings

settings = get_settings()
redacted = re.sub(r"://([^:]+):[^@]*@", r"://\1:***@", settings.database_url)
print("settings.database_url (redacted):", redacted)

conn = psycopg.connect(settings.database_url.replace("postgresql+psycopg://", "postgresql://"))
print("raw psycopg server version banner:", conn.execute("SELECT version()").fetchone())
conn.close()
