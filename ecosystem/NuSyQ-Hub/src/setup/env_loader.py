"""Lightweight .env loader used by NuSyQ-Hub.

Tries to use python-dotenv if available; falls back to a safe parser that sets os.environ for non-empty values.
This module is intentionally minimal and side-effect free except for setting os.environ.
# ruff: noqa: E501
# flake8: noqa: E501.
"""

import os
from pathlib import Path


def load_dotenv(path: str | None = None) -> int:
    """Load environment variables from a .env file.

    Returns the number of variables loaded.
    """
    env_path = Path(path) if path else Path(".env")
    if not env_path.exists():
        return 0

    # Prefer python-dotenv if available
    try:
        from dotenv import load_dotenv as _load_dotenv

        _load_dotenv(str(env_path))
        # python-dotenv doesn't report count; do a simple scan for non-empty lines
        count = 0
        with open(env_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                if v.strip():
                    count += 1
        return count
    except (FileNotFoundError, UnicodeDecodeError, OSError):
        # Simple fallback parser: set only vars that are non-empty and not already set
        count = 0
        try:
            with open(env_path, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#") or "=" not in line:
                        continue
                    k, v = line.split("=", 1)
                    k = k.strip()
                    v = v.strip().strip('"').strip("'")
                    if not v:
                        continue
                    # Don't override existing environment variables
                    if os.environ.get(k):
                        continue
                    os.environ[k] = v
                    count += 1
        except (FileNotFoundError, UnicodeDecodeError, OSError):
            return 0
        return count
