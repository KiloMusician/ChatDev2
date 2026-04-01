#!/usr/bin/env python3
"""SimulatedVerse HTTP Client for cross-repo health integration.

Queries SimulatedVerse Culture Ship endpoints from NuSyQ-Hub.
"""

import json
import logging
import os
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

try:
    import httpx

    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False
    import urllib.error


class SimulatedVerseClient:
    """Client for SimulatedVerse Culture Ship API."""

    def __init__(self, base_url: str | None = None) -> None:
        """Initialize SimulatedVerseClient with base_url."""
        if base_url is None:
            env_base = os.getenv("SIMULATEDVERSE_BASE_URL")
            if env_base:
                base_url = env_base
            else:
                host = os.getenv("SIMULATEDVERSE_HOST")
                port = os.getenv("SIMULATEDVERSE_PORT")
                if host or port:
                    base_url = f"{host or 'http://localhost'}:{port or '5001'}"
                else:
                    try:
                        from src.config.service_config import ServiceConfig

                        base_url = ServiceConfig.get_simulatedverse_url()
                    except Exception:
                        host = "http://localhost"
                        port = "5001"
                        base_url = f"{host}:{port}"
        parsed = urlparse(base_url)
        if parsed.scheme not in {"http", "https"}:
            raise ValueError(f"Invalid SimulatedVerse base URL: {base_url}")
        self.base_url = base_url.rstrip("/")
        self.timeout = 5.0

    def get_health(self) -> dict[str, Any]:
        """Get SimulatedVerse health status."""
        endpoint = f"{self.base_url}/culture-ship/health"

        try:
            if HTTPX_AVAILABLE:
                response = httpx.get(endpoint, timeout=self.timeout)
                response.raise_for_status()
                return {
                    "status": "operational",
                    "endpoint": endpoint,
                    "response": response.json(),
                    "status_code": response.status_code,
                }
            else:
                # Fallback to urllib
                req = urllib.request.Request(endpoint)
                with urllib.request.urlopen(req, timeout=self.timeout) as response:  # nosemgrep
                    data = json.loads(response.read().decode())
                    return {
                        "status": "operational",
                        "endpoint": endpoint,
                        "response": data,
                        "status_code": response.status,
                    }
        except Exception as e:
            return {
                "status": "unreachable",
                "endpoint": endpoint,
                "error": str(e),
                "error_type": type(e).__name__,
            }

    def get_status(self) -> dict[str, Any]:
        """Get SimulatedVerse operational status."""
        endpoint = f"{self.base_url}/culture-ship/status"

        try:
            if HTTPX_AVAILABLE:
                response = httpx.get(endpoint, timeout=self.timeout)
                response.raise_for_status()
                return {
                    "status": "operational",
                    "endpoint": endpoint,
                    "response": response.json(),
                }
            else:
                req = urllib.request.Request(endpoint)
                with urllib.request.urlopen(req, timeout=self.timeout) as response:  # nosemgrep
                    data = json.loads(response.read().decode())
                    return {
                        "status": "operational",
                        "endpoint": endpoint,
                        "response": data,
                    }
        except Exception as e:
            return {
                "status": "unreachable",
                "endpoint": endpoint,
                "error": str(e),
            }

    def get_next_actions(self) -> dict[str, Any]:
        """Get suggested next actions from SimulatedVerse."""
        endpoint = f"{self.base_url}/culture-ship/next-actions"

        try:
            if HTTPX_AVAILABLE:
                response = httpx.get(endpoint, timeout=self.timeout)
                response.raise_for_status()
                return {
                    "status": "operational",
                    "endpoint": endpoint,
                    "actions": response.json().get("suggested_actions", []),
                }
            else:
                req = urllib.request.Request(endpoint)
                with urllib.request.urlopen(req, timeout=self.timeout) as response:  # nosemgrep
                    data = json.loads(response.read().decode())
                    return {
                        "status": "operational",
                        "endpoint": endpoint,
                        "actions": data.get("suggested_actions", []),
                    }
        except Exception as e:
            return {
                "status": "unreachable",
                "endpoint": endpoint,
                "error": str(e),
            }

    def check_connectivity(self) -> bool:
        """Quick connectivity check."""
        health = self.get_health()
        return health.get("status") == "operational"


def save_simverse_health_receipt(health_data: dict[str, Any]) -> None:
    """Save SimulatedVerse health data to receipt."""
    receipt_dir = Path.cwd() / "state" / "receipts" / "simulated_verse"
    receipt_dir.mkdir(parents=True, exist_ok=True)

    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    receipt_file = receipt_dir / f"health_{timestamp_str}.json"

    receipt = {
        "type": "simulated_verse_health",
        "timestamp": datetime.now().isoformat(),
        "health": health_data,
    }

    with open(receipt_file, "w") as f:
        json.dump(receipt, f, indent=2, default=str)

    logger.info(f"✓ SimulatedVerse health receipt: {receipt_file}")


if __name__ == "__main__":
    # Test the client
    client = SimulatedVerseClient()

    logger.info("Testing SimulatedVerse connectivity...")
    logger.info(f"Base URL: {client.base_url}")

    health = client.get_health()
    logger.info(f"\nHealth Check: {health.get('status')}")

    if health.get("status") == "operational":
        logger.info(f"  Status Code: {health.get('status_code')}")
        logger.info(f"  Response: {json.dumps(health.get('response'), indent=2)}")

        status = client.get_status()
        logger.info(f"\nOperational Status: {status.get('status')}")
        if status.get("response"):
            logger.info(
                f"  Consciousness: {status['response'].get('consciousness_level', 'unknown')}"
            )

        save_simverse_health_receipt(health)
    else:
        logger.error(f"  Error: {health.get('error')}")
        logger.warning("\n⚠ SimulatedVerse server not running on port 5002")
        logger.info("  To start: cd SimulatedVerse && npm run dev")
