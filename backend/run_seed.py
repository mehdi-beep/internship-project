"""One-off seed runner for cPanel's Execute python script box.
Runs the same seed logic dev.db was built from — safe to re-run,
since app.database.seed.run() checks whether the database is already
seeded and skips the demo-data section if so.
"""

import sys

from app.database.seed import run

try:
    run()
except Exception as exc:
    print(f"Seeding failed: {exc!r}")
    sys.exit(1)
