"""One-off diagnostic: prints exactly what DATABASE_URL config the app
sees, with the password redacted, plus where it's actually reading
from. Delete after use.
"""

import os
import re
from pathlib import Path

print("cwd:", os.getcwd())
print("script dir:", Path(__file__).parent.resolve())
print(".env exists at script dir:", (Path(__file__).parent / ".env").exists())
print("DATABASE_URL in raw os.environ:", "DATABASE_URL" in os.environ)

from config import get_settings

settings = get_settings()
redacted = re.sub(r"://([^:]+):[^@]*@", r"://\1:***@", settings.database_url)
print("settings.database_url (redacted):", redacted)
