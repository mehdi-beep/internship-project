"""One-off installer for cPanel's Python App 'Execute python script' box,
which only runs a .py file path (not arbitrary shell commands like
`pip install ...`). Delete after the deploy's dependencies are installed.
"""

import subprocess
import sys
from pathlib import Path

requirements = Path(__file__).parent / "requirements.txt"
result = subprocess.run(
    [sys.executable, "-m", "pip", "install", "-r", str(requirements)],
    capture_output=True,
    text=True,
)
print(result.stdout)
print(result.stderr)
sys.exit(result.returncode)
