"""Policy / safety preflight helpers (Phase 7).

Lightweight checks for PII/secrets and risk scoring of commands.
"""

from __future__ import annotations

import re

from src.config.feature_flag_manager import is_feature_enabled

PII_PATTERNS = [
    re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),  # SSN-like
    re.compile(r"\b\d{16}\b"),  # credit-card-ish
    re.compile(r"sk-[A-Za-z0-9]{20,}"),  # api keys
]


def detect_pii(text: str) -> list[str]:
    issues = []
    for pat in PII_PATTERNS:
        if pat.search(text):
            issues.append(pat.pattern)
    return issues


def safety_preflight(command: list[str]) -> dict[str, str]:
    """Very light command risk check."""
    risky = {"rm", "shutdown", "reboot", "format"}
    risk = any(cmd in risky for cmd in command)
    return {"risky": str(risk).lower()}


def enforce_policy(text: str) -> dict[str, str]:
    if not is_feature_enabled("policy_audit_enabled"):
        return {"policy": "skipped"}
    issues = detect_pii(text)
    if issues:
        return {"policy": "blocked", "issues": issues}
    return {"policy": "passed"}
