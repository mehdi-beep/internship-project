"""One-off migration runner for cPanel's Execute python script box,
which only runs a .py file path (not shell commands like `alembic
upgrade head`). Re-run this any time a new migration needs applying.
"""

import subprocess
import sys
from pathlib import Path

backend_dir = Path(__file__).parent
result = subprocess.run(
    [sys.executable, "-m", "alembic", "upgrade", "head"],
    cwd=str(backend_dir),
    capture_output=True,
    text=True,
)
print(result.stdout)
print(result.stderr)
sys.exit(result.returncode)
