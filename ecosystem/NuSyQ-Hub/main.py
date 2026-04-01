"""Compatibility wrapper: delegate to canonical `src.core.main`.

This file reduces duplication by running the canonical module as a script.
"""

import runpy


def _main():
    # Run the canonical module as a script
    # Use runpy.run_module so module-level CLI behavior is preserved
    runpy.run_module("src.core.main", run_name="__main__")


if __name__ == "__main__":
    _main()
