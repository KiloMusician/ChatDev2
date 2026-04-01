"""Lightweight rosetta runner helper.

Attempts to call `scripts/start_nusyq.py suggest` and persist a evolve suggestion
artifact. Falls back to generating a simple suggestion if the script cannot be
invoked.
"""

from __future__ import annotations

import json
import logging
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

logger = logging.getLogger(__name__)


def _now():
    return datetime.now(UTC).isoformat()


def run_suggest(prompt: str | None = None, timeout: int = 60) -> dict:
    repo_root = Path(__file__).resolve().parents[2]
    scripts_start = repo_root / "scripts" / "start_nusyq.py"
    rosetta_dir = repo_root / "Reports" / "rosetta"
    rosetta_dir.mkdir(parents=True, exist_ok=True)

    # Try to run the suggest subcommand; many environments may not support it,
    # so catch failures and fall back to a simple generator.
    if scripts_start.exists():
        cmd = [sys.executable, str(scripts_start), "suggest"]
        if prompt:
            cmd += ["--prompt", str(prompt)]
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
            output = (proc.stdout or "").strip()
            # Prefer JSON output if available
            try:
                parsed = json.loads(output)
                suggestion_text = parsed.get("suggestion") or parsed.get("message") or output
            except Exception:
                suggestion_text = output or "Generated suggestion from start_nusyq.suggest"

            suggestion = {
                "id": str(uuid4()),
                "prompt": prompt or "Auto evolve suggestion",
                "suggestion": suggestion_text,
                "timestamp": _now(),
            }
            fname = rosetta_dir / f"evolve_suggestion_{int(datetime.now().timestamp())}.json"
            with fname.open("w", encoding="utf-8") as fh:
                json.dump(suggestion, fh, indent=2)
            return {"file": str(fname), "content": suggestion}
        except Exception:
            # fall through to fallback
            logger.debug("Suppressed Exception", exc_info=True)

    # Fallback suggestion
    suggestion = {
        "id": str(uuid4()),
        "prompt": prompt or "Auto evolve suggestion",
        "suggestion": "Refactor and modernize the target module. Add tests and CI checks.",
        "timestamp": _now(),
    }
    fname = rosetta_dir / f"evolve_suggestion_{int(datetime.now().timestamp())}.json"
    with fname.open("w", encoding="utf-8") as fh:
        json.dump(suggestion, fh, indent=2)
    return {"file": str(fname), "content": suggestion}
