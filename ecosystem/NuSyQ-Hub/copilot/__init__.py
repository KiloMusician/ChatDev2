# Copilot package shim to make tests that run `python -m copilot.bridge_cli` work
# This package mirrors the implementation under src/copilot when running from
# the repository root (tests often spawn subprocesses without PYTHONPATH set).

__all__ = ["bridge_cli"]
