"""
Simplified placeholder for simple_touchdesigner.

Used to suppress invalid-syntax noise while the UI pipeline is rebuilt.
"""


def status() -> dict[str, str]:
    """Return placeholder status info."""
    return {"module": "simple_touchdesigner", "status": "placeholder"}


def describe() -> str:
    """Explain the placeholder to diagnostics."""
    return "simple_touchdesigner placeholder (syntax cleared)."
