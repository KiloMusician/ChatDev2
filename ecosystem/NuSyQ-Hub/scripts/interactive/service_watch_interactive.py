# %%
"""Service Watch Interactive Notebook

Open this file in VS Code and run each cell in the Python Interactive window to inspect ports, duplicates,
latest ChatDev receipts, and the log output without leaving the editor.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scripts.service_watch import interactive_status_dump

# %%
status = interactive_status_dump()
# status

# Run the CLI version and capture the JSON output.
result = subprocess.run(
    [sys.executable, "scripts/service_watch.py", "--json"],
    stdout=subprocess.PIPE,
    text=True,
    check=True,
)
print(json.dumps(json.loads(result.stdout), indent=2))

# %%
log_path = Path("data/terminal_logs/service_watch.log")
if log_path.exists():
    tail = log_path.read_text().splitlines()[-5:]
    print("\n".join(tail))
else:
    print("Log file missing:", log_path)
