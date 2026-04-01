"""Legacy redirect for ArchitectureWatcher utilities.

Canonical implementation:
    src/core/ArchitectureWatcher.py
"""

from src.core.ArchitectureWatcher import (ArchitectureWatcher,
                                          KILOArchitectureWatcher)

__all__ = ["ArchitectureWatcher", "KILOArchitectureWatcher"]


def main() -> None:
    """Entry point wrapper for legacy CLI usage."""
    watcher = KILOArchitectureWatcher()
    watcher.start_watching()


if __name__ == "__main__":
    main()
