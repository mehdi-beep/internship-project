"""One-off migration runner for cPanel's Execute python script box,
which only runs a .py file path (not shell commands like `alembic
upgrade head`). Re-run this any time a new migration needs applying.
"""

import subprocess
import sys
from pathlib import Path

import psycopg

from config import get_settings

backend_dir = Path(__file__).parent

settings = get_settings()
raw_url = settings.database_url.replace("postgresql+psycopg://", "postgresql://")
conn = psycopg.connect(raw_url, client_encoding="UTF8")
print("[pre-check] current_database():", conn.execute("SELECT current_database()").fetchone())
print(
    "[pre-check] tables:",
    conn.execute("SELECT tablename FROM pg_tables WHERE schemaname = 'public'").fetchall(),
)
print(
    "[pre-check] custom types:",
    conn.execute(
        "SELECT typname FROM pg_type t JOIN pg_namespace n ON t.typnamespace = n.oid "
        "WHERE n.nspname = 'public' AND t.typtype = 'e'"
    ).fetchall(),
)
conn.close()

result = subprocess.run(
    [sys.executable, "-m", "alembic", "upgrade", "head"],
    cwd=str(backend_dir),
    capture_output=True,
    text=True,
)
print(result.stdout)
print(result.stderr)
sys.exit(result.returncode)
