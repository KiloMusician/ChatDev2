#!/usr/bin/env python3
"""Legacy redirect for BrokenPathsAnalyzer.

Canonical implementation:
    src/analysis/broken_paths_analyzer.py
"""

from src.analysis.broken_paths_analyzer import BrokenPathsAnalyzer
from src.analysis.broken_paths_analyzer import main as broken_paths_main

__all__ = ["BrokenPathsAnalyzer", "broken_paths_main"]


def main() -> None:
    """Entry point wrapper for legacy CLI usage."""
    broken_paths_main()


if __name__ == "__main__":
    main()
