#!/usr/bin/env python3
"""Smoke test for policy/PII detection."""

from __future__ import annotations

import sys

sys.path.insert(0, ".")

from src.system.policy import detect_pii, safety_preflight


def main() -> None:
    print("pii:", detect_pii("my key sk-abc1234567890123456 and 123-45-6789"))
    print("safety:", safety_preflight(["rm", "-rf", "/"]))


if __name__ == "__main__":
    main()
