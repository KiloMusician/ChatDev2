"""Utility helpers for path operations and other common tasks."""

from pathlib import Path


def join_path(*parts: str | Path) -> Path:
    """Join multiple path parts into a single Path object.

    Args:
        *parts: Strings or :class:`pathlib.Path` objects to join.

    Returns:
        Path: Joined path.

    """
    return Path(*parts)
