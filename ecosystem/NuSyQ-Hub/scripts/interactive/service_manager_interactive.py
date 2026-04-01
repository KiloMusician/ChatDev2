# %%
"""Service Manager Interactive Probe

Use this module in the VS Code interactive window to inspect the PID locks, service state,
and any duplicate guards without spinning up a fresh service run.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scripts.service_manager import ServiceManager

# %%
manager = ServiceManager(ROOT)
state = manager.load_state()
print(json.dumps(state, indent=2))
# state


# %%
pid_dir = ROOT / "state" / "services" / "pids"
summary = []
for service in ("cross_sync", "guild_renderer", "pu_queue_runner"):
    summary.append(
        {
            "service": service,
            "pid": manager._read_pid(service),
            "pid_file": str(pid_dir / f"{service}.pid") if pid_dir.exists() else "missing dir",
        }
    )
print(json.dumps(summary, indent=2))
# summary
