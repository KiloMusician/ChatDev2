#!/usr/bin/env python3
"""Top-level health CLI wrapper for NuSyQ-Hub.

This module forwards execution to src.diagnostics.health_cli to avoid
duplicating logic in this top-level file and keep the implementation
compact and maintainable.
"""


# Helper removed; health CLI now delegates to src.diagnostics.health_cli

from src.diagnostics.health_cli import main as health_main

if __name__ == "__main__":
    health_main()
