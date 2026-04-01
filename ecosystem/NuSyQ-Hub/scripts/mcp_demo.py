"""Simple MCP demo: send a handoff to a terminal channel and poll for recent entries.

Usage: python scripts/mcp_demo.py

This script posts a small handoff to the MCP terminal send endpoint and
polls the recent endpoint for the channel to confirm the entry appears.
"""

from __future__ import annotations

import json
import os
import time
from typing import Any

import requests

BASE_URL = os.environ.get("MCP_URL", "http://127.0.0.1:8001")
CHANNEL = os.environ.get("MCP_CHANNEL", "nusyq-demo")


def send_handoff(session: requests.Session, payload: dict[str, Any]) -> dict[str, Any]:
    """Send a handoff to MCP terminal send endpoint."""
    url = f"{BASE_URL}/api/terminals/send"
    resp = session.post(url, json=payload, timeout=10)
    resp.raise_for_status()
    return resp.json()


def fetch_recent(session: requests.Session, channel: str) -> dict[str, Any]:
    """Fetch recent entries from MCP terminal channel."""
    url = f"{BASE_URL}/api/terminals/{channel}/recent"
    resp = session.get(url, timeout=10)
    resp.raise_for_status()
    return resp.json()


def _create_handoff_payload() -> dict[str, Any]:
    """Create the handoff payload for MCP terminal."""
    return {
        "channel": CHANNEL,
        "level": "info",
        "message": "mcp-demo-handoff",
        "meta": {
            "handoff_summary": {
                "model": "demo-model",
                "max_tokens": 20000,
                "temperature": 0.2,
                "instructions": "This is a short demo handoff to verify MCP terminal integration.",
            }
        },
    }


def _send_handoff_and_get_response(session: requests.Session, payload: dict[str, Any]) -> dict[str, Any] | None:
    """Send handoff to MCP and return response, handling errors gracefully."""
    print("Sending handoff to MCP terminal send endpoint...")
    try:
        resp = send_handoff(session, payload)
        print("Send response:")
        print(json.dumps(resp, indent=2))
        return resp
    except Exception as exc:  # pragma: no cover - operational script
        print(f"Failed to send handoff: {exc}")
        return None


def _find_handoff_in_entries(entries: list[dict[str, Any]]) -> dict[str, Any] | None:
    """Search entries list for our handoff message.

    Args:
        entries: List of entry dicts from recent endpoint

    Returns:
        The matching entry dict or None
    """
    for e in entries:
        msg = e.get("message") if isinstance(e, dict) else None
        if msg == "mcp-demo-handoff":
            return e
    return None


def _poll_for_handoff_entry(
    session: requests.Session, channel: str, timeout_secs: float = 20.0
) -> dict[str, Any] | None:
    """Poll recent entries until handoff entry found or timeout.

    Args:
        session: Requests session
        channel: Terminal channel to poll
        timeout_secs: Maximum polling duration

    Returns:
        Found entry dict or None if timeout
    """
    start = time.time()
    deadline = start + timeout_secs

    while time.time() < deadline:
        try:
            recent = fetch_recent(session, channel)
            entries = recent.get("entries") or recent.get("data") or []
            found = _find_handoff_in_entries(entries)
            if found:
                return found
        except Exception as exc:  # pragma: no cover - operational script
            print(f"Error fetching recent entries: {exc}")

        time.sleep(1.0)

    return None


def _print_polling_results(found: dict[str, Any] | None, recent: dict[str, Any] | None) -> None:
    """Print results of polling operation."""
    if found:
        print("Found handoff entry:")
        print(json.dumps(found, indent=2))
    else:
        print("Did not find handoff entry within timeout. Last recent response:")
        try:
            print(json.dumps(recent, indent=2))
        except Exception:
            print(recent)


def main() -> None:
    """Main demo function."""
    session = requests.Session()

    # Create and send handoff
    payload = _create_handoff_payload()
    if _send_handoff_and_get_response(session, payload) is None:
        return

    # Poll for handoff entry
    print(f"Polling recent entries for channel {CHANNEL}")
    found = _poll_for_handoff_entry(session, CHANNEL, timeout_secs=20.0)

    # Display results
    recent = None
    if not found:
        try:
            recent = fetch_recent(session, CHANNEL)
        except Exception:
            pass

    _print_polling_results(found, recent)


if __name__ == "__main__":
    main()
