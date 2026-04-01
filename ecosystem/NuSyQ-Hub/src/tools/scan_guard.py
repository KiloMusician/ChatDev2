import logging
import os
from pathlib import Path

import psutil

logger = logging.getLogger(__name__)


def scans_disabled(repo_root: Path | None = None) -> tuple[bool, str]:
    """Global guard to quickly disable repository-wide scans.

    Checks for either a sentinel file in the repository root (recommended) or
    an environment variable. This lets developers stop aggressive scanning
    immediately across the codebase by creating a file named
    `.disable_scans` (or `.no_repo_scans`) in the repository root, or by
    exporting `NU_SYQ_DISABLE_SCANS=1` in the environment.

    Returns (True, reason) when scans are disabled, otherwise (False, "").
    """
    repo_root = Path(repo_root or Path.cwd())
    sentinel_files = [repo_root / ".disable_scans", repo_root / ".no_repo_scans"]
    for sf in sentinel_files:
        if sf.exists():
            return True, f"Found sentinel file: {sf.name}"

    # Environment override
    env_val = os.environ.get("NU_SYQ_DISABLE_SCANS")
    if env_val and env_val.strip() not in ("", "0", "false", "False"):
        return True, "NU_SYQ_DISABLE_SCANS environment variable set"

    return False, ""


def check_scan_safety(force: bool = False) -> tuple[bool, str]:
    r"""Quick safety checks before running a heavy scan.

    - Checks for low free RAM (<2GB)
    - Heuristic: single-user laptop (Windows: only one user profile in C:\\Users)
    Returns (True, reason) if unsafe, (False, "") if safe.
    If force=True, always returns (False, "").
    """
    if force:
        return False, ""
    # Check free RAM
    try:
        mem = psutil.virtual_memory()
        if mem.available < 2 * 1024 * 1024 * 1024:  # 2GB
            return True, f"Low free RAM: {mem.available // (1024 * 1024)} MB available"
    except (AttributeError, OSError) as e:
        # If psutil fails, be conservative
        return True, f"Could not determine free RAM: {e}"

    # Heuristic: single-user laptop (Windows only)
    if os.name == "nt":
        try:
            user_dirs = [
                d
                for d in Path("C:/Users").iterdir()
                if d.is_dir() and not d.name.lower().startswith("public")
            ]
            if len(user_dirs) <= 1:
                return (
                    True,
                    "Single-user Windows system detected (C:/Users has <=1 profile)",
                )
        except (OSError, PermissionError):
            logger.debug("Suppressed OSError/PermissionError", exc_info=True)
    # Could add more heuristics for other OSes if needed
    return False, ""


def ensure_scan_allowed(
    repo_root: Path | None = None,
    force: bool = False,
    raise_on_block: bool = True,
) -> tuple[bool, str]:
    """Convenience helper to ensure scans are allowed for a given repo root.

    - Checks sentinel files / env var via `scans_disabled`.
    - Runs `check_scan_safety` unless `force=True`.

    If `raise_on_block` is True this will raise RuntimeError when blocked.
    Returns (True, "") when allowed, otherwise (False, reason).
    """
    repo_root = Path(repo_root) if repo_root is not None else Path.cwd()
    disabled, reason = scans_disabled(repo_root)
    if disabled:
        msg = f"Repository scans are disabled for {repo_root}: {reason}"
        if raise_on_block:
            raise RuntimeError(msg)
        return False, msg

    unsafe, reason2 = check_scan_safety(force=force)
    if unsafe:
        msg2 = f"Scan safety check failed: {reason2}"
        if raise_on_block:
            raise RuntimeError(msg2)
        return False, msg2

    return True, ""
