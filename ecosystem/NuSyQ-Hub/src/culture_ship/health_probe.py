"""Culture Ship Health Probe.

Performs lightweight checks for Culture Ship readiness and writes a structured
JSON receipt under state/receipts/culture-ship/.
"""

from __future__ import annotations

import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Ensure repository root is on sys.path so imports like `src.*` resolve when
# this file is executed directly (python src/culture_ship/health_probe.py)
try:
    repo_root = Path(__file__).resolve().parents[2]
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))
except Exception:
    # Non-fatal; import checks below will reflect any resolution problems
    logger.debug("Suppressed Exception", exc_info=True)


def _load_workspace_env() -> None:
    """Load .env.workspace if the culture-ship path vars aren't already in the environment.

    Avoids importing python-dotenv at module level — only loads when the probe
    detects that the workspace hasn't been sourced yet.
    """
    _required = ("NUSYQ_HUB_PATH", "SIMULATEDVERSE_PATH", "NUSYQ_ROOT_PATH")
    if all(os.environ.get(v) for v in _required):
        return  # Already sourced — nothing to do

    try:
        from dotenv import load_dotenv

        env_file = Path(__file__).resolve().parents[2] / ".env.workspace"
        if env_file.exists():
            load_dotenv(env_file, override=False)
    except Exception:
        pass  # dotenv not installed — env vars simply remain unset


def check_dependencies() -> dict[str, Any]:
    deps: dict[str, Any] = {}

    # Load .env.workspace so path vars resolve even when probe is run stand-alone
    _load_workspace_env()

    # Environment variables
    deps["env"] = {
        "NUSYQ_HUB_PATH": bool(os.environ.get("NUSYQ_HUB_PATH")),
        "SIMULATEDVERSE_PATH": bool(os.environ.get("SIMULATEDVERSE_PATH")),
        "NUSYQ_ROOT_PATH": bool(os.environ.get("NUSYQ_ROOT_PATH")),
    }

    # Python modules
    deps["python_modules"] = {}
    for mod in [
        "src.culture_ship_real_action",
        "src.culture_ship.plugins.ruff_fixer",
        "src.culture_ship.plugins.black_formatter",
    ]:
        try:
            __import__(mod)
            deps["python_modules"][mod] = True
        except Exception:
            deps["python_modules"][mod] = False

    # Tools availability
    from shutil import which

    deps["tools"] = {"ruff": bool(which("ruff")), "black": bool(which("black"))}

    return deps


def generate_recommendations(health: dict[str, Any]) -> list[str]:
    recs: list[str] = []
    if not health["tools"].get("ruff"):
        recs.append("Install ruff for lint-based analysis and auto-fixes")
    if not health["tools"].get("black"):
        recs.append("Install black for code formatting")
    if not health["python_modules"].get("src.culture_ship.plugins.ruff_fixer"):
        recs.append("Ensure ruff_fixer plugin is present under src/culture_ship/plugins")
    return recs


def run(receipt_dir: Path | None = None) -> int:
    health = check_dependencies()
    ready = all(health["tools"].values()) and all(health["python_modules"].values())

    receipt = {
        "timestamp": datetime.now().isoformat(),
        "repo": "NuSyQ-Hub",
        "command": "culture_ship_health",
        "health_status": health,
        "ready_for_automation": bool(ready),
        "recommendations": generate_recommendations(health),
    }

    base = receipt_dir or (Path("state") / "receipts" / "culture-ship")
    base.mkdir(parents=True, exist_ok=True)
    path = base / f"health_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    path.write_text(json.dumps(receipt, indent=2), encoding="utf-8")

    logger.info(f"Health check: {'READY' if ready else 'DEGRADED'} → {path}")

    try:
        from src.system.agent_awareness import emit as _emit

        _status = "READY" if ready else "DEGRADED"
        _lvl = "INFO" if ready else "WARNING"
        _recs = len(receipt.get("recommendations", []))
        _emit(
            "culture_ship",
            f"Health probe: status={_status} recommendations={_recs}",
            level=_lvl,
            source="culture_ship_health_probe",
        )
    except Exception:
        pass

    return 0 if ready else 1


if __name__ == "__main__":
    raise SystemExit(run())
