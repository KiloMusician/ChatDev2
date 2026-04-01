#!/usr/bin/env python3
"""
Check AI coordinator status and write a small status report JSON.

Writes `state/coordinator_status.json` and prints a brief human summary.
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path


def get_status() -> dict:
    try:
        # Import local coordinator
        from src.ai.ai_coordinator import get_coordinator

        coordinator = get_coordinator()

        # call get_system_status (synchronous)
        status = coordinator.get_system_status()

        # include registry snapshot if available
        try:
            llm_registry = coordinator.llm_registry
            status["llm_registry"] = {
                "all": list(llm_registry.all().keys()),
                "available": list(llm_registry.available().keys()),
            }
        except (AttributeError, TypeError, ValueError):
            status["llm_registry"] = {"all": [], "available": []}

        # include performance metrics (already present)
        status["performance_metrics"] = getattr(coordinator, "performance_metrics", {})

        return status
    except (ImportError, AttributeError, OSError, RuntimeError, ValueError) as e:
        return {"error": str(e)}


def main() -> None:
    out = Path("state") / "coordinator_status.json"
    out.parent.mkdir(parents=True, exist_ok=True)

    status = get_status()
    with open(out, "w", encoding="utf-8") as f:
        json.dump(status, f, indent=2, ensure_ascii=False)

    # Print summary
    if "error" in status:
        print("Coordinator status: ERROR")
        print(status["error"])
        return

    providers = status.get("providers", {})
    print("Coordinator providers:")
    for name, info in providers.items():
        print(
            f" - {name}: available={info.get('available')} capabilities={info.get('capabilities')}"
        )


if __name__ == "__main__":
    # Run in event loop in case imports expect asyncio
    try:
        asyncio.run(asyncio.to_thread(main))
    except (RuntimeError, OSError, ValueError):
        main()
