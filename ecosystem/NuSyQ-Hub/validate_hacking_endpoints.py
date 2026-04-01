#!/usr/bin/env python
"""Quick validation script for hacking game endpoints."""

import sys
import logging
from typing import Optional, List, Tuple, Dict, Any

import requests

BASE_URL = "http://localhost:8000"
ENDPOINTS: List[Tuple[str, str, Optional[Dict[str, Any]]]] = [
    ("POST", "/api/hack/nmap", {"component_name": "python"}),
    ("POST", "/api/hack/connect", {"component_name": "python"}),
    (
        "POST",
        "/api/hack/exploit",
        {"component_name": "python", "exploit_type": "SSH_CRACK", "xp_reward": 50},
    ),
    ("GET", "/api/hack/traces", None),
    ("POST", "/api/hack/patch", {"component_name": "python"}),
    ("GET", "/api/fl1ght?q=hack", None),
]


def test_endpoint(method: str, path: str, data: Optional[Dict[str, Any]]) -> tuple[bool, str]:
    """Test a single endpoint."""
    url = f"{BASE_URL}{path}"
    try:
        if method == "GET":
            resp = requests.get(url, timeout=5)
        elif method == "POST":
            resp = requests.post(url, json=data, timeout=5)
        else:
            return False, f"Unknown method: {method}"

        if resp.status_code == 200:
            return True, f"✅ {resp.status_code} OK"
        elif resp.status_code == 422:
            return False, f"❌ {resp.status_code} Validation Error: {resp.text[:100]}"
        else:
            return False, f"❌ {resp.status_code} {resp.reason}"
    except requests.exceptions.ConnectionError:
        return False, "❌ Connection refused (server not running?)"
    except requests.exceptions.Timeout:
        return False, "❌ Timeout (server slow?)"
    except Exception as e:
        return False, f"❌ Error: {e!s}"


def main() -> int:
    """Run all endpoint tests."""
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    logging.info("\n" + "=" * 70)
    logging.info("🎮 Hacking Game Endpoint Validation")
    logging.info("=" * 70 + "\n")

    passed = 0
    failed = 0

    for method, path, data in ENDPOINTS:
        status, msg = test_endpoint(method, path, data)
        success_emoji = "✅" if status else "❌"
        logging.info(f"{success_emoji} {method:6s} {path:30s} {msg}")

        if status:
            passed += 1
        else:
            failed += 1

    logging.info("\n" + "=" * 70)
    logging.info(f"Results: {passed} passed, {failed} failed")
    logging.info("=" * 70 + "\n")

    if failed == 0:
        logging.info("🎉 All endpoints operational! Ready for testing.")
        return 0
    else:
        logging.warning(f"⚠️  {failed} endpoint(s) failed. Check server logs.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
