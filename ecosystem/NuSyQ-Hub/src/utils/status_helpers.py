"""Status normalization utilities.

Provide canonical status values and helpers to normalize/check statuses.
"""

from typing import Final

CANONICAL_STATUSES = {
    "pending": "pending",
    "active": "active",
    "completed": "completed",
    "complete": "completed",
    "blocked": "blocked",
    "archived": "archived",
    "failed": "failed",
}

DEFAULT_STATUS: Final[str] = "pending"


def normalize_status(status: str | None) -> str:
    if not status:
        return DEFAULT_STATUS
    key = str(status).strip().lower()
    return CANONICAL_STATUSES.get(key, key)


def is_completed(status: str | None) -> bool:
    return normalize_status(status) == "completed"
