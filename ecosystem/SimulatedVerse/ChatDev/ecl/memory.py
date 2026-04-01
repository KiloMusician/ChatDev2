"""
Lightweight placeholder for ChatDev memory helpers in SimulatedVerse.

Keeps syntax clean while the actual retrieval stack is rebuilt.
"""


def retrieve_experiences(query: str, limit: int = 1) -> list[str]:
    """Return placeholder references for the requested query."""
    return [f"simulated-memory-{query}-{idx}" for idx in range(1, limit + 1)]


def store_experience(data: dict[str, str]) -> None:
    """No-op storage path for now."""
    del data  # intentionally unused; placeholder only


def describe() -> str:
    """Describe the placeholder for audit tools."""
    return "SimulatedVerse ChatDev memory placeholder (syntax cleared)."
