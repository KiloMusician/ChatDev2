from __future__ import annotations

import asyncio
import os
import subprocess
from pathlib import Path
from typing import Any, Dict, AsyncIterator, List, Tuple

from .paths import CORE_DIR

SCRIPTS_DIR = CORE_DIR / "scripts"

# Allow-list mapping: "command" -> (script, fixed_args_prefix)
ALLOWLIST: Dict[str, Tuple[str, List[str]]] = {
    "start": ("devmentor_bootstrap.py", ["start"]),
    "next": ("devmentor_bootstrap.py", ["next"]),
    "diagnose": ("devmentor_bootstrap.py", ["diagnose"]),
    "validate": ("devmentor_validate.py", []),
    "export": ("devmentor_portable.py", ["export"]),
    "import": ("devmentor_portable.py", ["import"]),
    "status": ("devmentor_status.py", []),
    "ops": ("devmentor_ops.py", []),
    "ops-doctor": ("devmentor_ops.py", ["doctor"]),
    "ops-check": ("devmentor_ops.py", ["check"]),
    "ops-fix": ("devmentor_ops.py", ["fix"]),
    "ops-prune": ("devmentor_ops.py", ["prune"]),
    "ops-graph": ("devmentor_ops.py", ["graph"]),
    "ops-report": ("devmentor_ops.py", ["report"]),
    "ops-all": ("devmentor_ops.py", ["all"]),
    "git-push": ("git_auto_push.py", []),
    "git-push-dry": ("git_auto_push.py", ["--dry-run"]),
    "reflect": ("../reflect.py", []),
    "analyze-errors": ("../analyze_errors.py", []),
}


def _script_path(script: str) -> Path:
    p = (SCRIPTS_DIR / script).resolve()
    if p.exists():
        return p
    # Try root-level script (e.g. reflect.py at repo root)
    root_p = (CORE_DIR / script.lstrip("../")).resolve()
    if root_p.exists():
        return root_p
    raise FileNotFoundError(f"Missing script: {script}")


def run_allowlisted(command: str, args: List[str]) -> Dict[str, Any]:
    if command not in ALLOWLIST:
        return {"ok": False, "error": f"Command not allowed: {command}", "allowed": sorted(ALLOWLIST.keys())}
    script, prefix = ALLOWLIST[command]
    script_path = _script_path(script)

    cmd = ["python", str(script_path)] + prefix + args
    proc = subprocess.run(cmd, cwd=str(CORE_DIR), capture_output=True, text=True)  # nosec B603

    return {
        "ok": proc.returncode == 0,
        "command": command,
        "cmd": cmd,
        "returncode": proc.returncode,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
    }


async def stream_allowlisted(command: str, args: List[str]) -> AsyncIterator[Dict[str, Any]]:
    if command not in ALLOWLIST:
        yield {"type": "error", "message": f"Command not allowed: {command}", "allowed": sorted(ALLOWLIST.keys())}
        return

    script, prefix = ALLOWLIST[command]
    script_path = _script_path(script)
    cmd = ["python", str(script_path)] + prefix + args

    yield {"type": "start", "command": command, "cmd": cmd}

    proc = await asyncio.create_subprocess_exec(  # nosec B603
        *cmd,
        cwd=str(CORE_DIR),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    queue: asyncio.Queue[Dict[str, Any]] = asyncio.Queue()
    done_event = asyncio.Event()

    async def pump_stream(stream: asyncio.StreamReader, kind: str) -> None:
        while True:
            line = await stream.readline()
            if not line:
                break
            await queue.put({"type": kind, "data": line.decode("utf-8", errors="replace")})

    async def run_pumps() -> int:
        assert proc.stdout is not None and proc.stderr is not None
        await asyncio.gather(
            pump_stream(proc.stdout, "stdout"),
            pump_stream(proc.stderr, "stderr"),
        )
        done_event.set()
        return await proc.wait()

    pump_task = asyncio.create_task(run_pumps())

    while not done_event.is_set() or not queue.empty():
        try:
            event = await asyncio.wait_for(queue.get(), timeout=0.1)
            yield event
        except asyncio.TimeoutError:
            continue

    rc = await pump_task
    yield {"type": "end", "returncode": rc, "ok": rc == 0}
