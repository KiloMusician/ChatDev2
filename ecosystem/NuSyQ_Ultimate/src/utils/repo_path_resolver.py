"""
Lightweight stub for repo_path_resolver when NuSyQ-Hub is not on disk.

Provides a get_repo_path() function that returns an environment override
or None so callers can fall back to hardcoded defaults without import errors.
"""

import os
from pathlib import Path
from typing import Optional


def get_repo_path(env_key: str) -> Optional[Path]:
    """Return Path from env var if set, otherwise None."""
    value = os.getenv(env_key)
    return Path(value) if value else None
