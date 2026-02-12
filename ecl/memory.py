"""
Lightweight placeholder for NuSyQ ChatDev memory helpers.

This stub mirrors the SimulatedVerse version to keep both repos aligned.
"""


def retrieve_experiences(query: str, limit: int = 1) -> list[str]:
    """Return placeholder references for the requested query."""
    return [f"nusyq-memory-{query}-{idx}" for idx in range(1, limit + 1)]


def store_experience(data: dict[str, str]) -> None:
    """No-op storage path (placeholder only)."""
    del data  # intentional no-op


def describe() -> str:
    """Explain the placeholder to auditing tools."""
    return "NuSyQ ChatDev memory placeholder (syntax cleared)."
