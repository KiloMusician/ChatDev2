"""Culture Ship Smoke Test - Simplified health check."""

import json
from datetime import datetime
from pathlib import Path
from typing import Any


def test_culture_ship_health() -> dict[str, Any]:
    """Run smoke test on Culture Ship components."""
    hub_path = Path(__file__).parent.parent

    result = {
        "timestamp": datetime.utcnow().isoformat(),
        "tests": [],
        "metrics": {"total": 0, "passed": 0, "failed": 0},
        "overall_status": "UNKNOWN",
        "receipt_path": None,
    }

    # Test 1: Health probe module
    probe_path = hub_path / "src" / "culture_ship" / "health_probe.py"
    result["metrics"]["total"] += 1
    if probe_path.exists():
        result["tests"].append({"name": "Health Probe", "status": "PASS"})
        result["metrics"]["passed"] += 1
    else:
        result["tests"].append({"name": "Health Probe", "status": "FAIL"})
        result["metrics"]["failed"] += 1

    # Test 2: Quest log
    quest_log_path = hub_path / "src" / "Rosetta_Quest_System" / "quest_log.jsonl"
    result["metrics"]["total"] += 1
    if quest_log_path.exists():
        with open(quest_log_path, "r") as f:
            lines = len(f.readlines())
        result["tests"].append({"name": "Quest Log", "status": "PASS", "lines": lines})
        result["metrics"]["passed"] += 1
    else:
        result["tests"].append({"name": "Quest Log", "status": "FAIL"})
        result["metrics"]["failed"] += 1

    # Test 3: ZETA tracker
    zeta_path = hub_path / "config" / "ZETA_PROGRESS_TRACKER.json"
    result["metrics"]["total"] += 1
    if zeta_path.exists():
        result["tests"].append({"name": "ZETA Tracker", "status": "PASS"})
        result["metrics"]["passed"] += 1
    else:
        result["tests"].append({"name": "ZETA Tracker", "status": "WARN"})

    # Determine overall status
    if result["metrics"]["failed"] == 0:
        result["overall_status"] = "READY"
    elif result["metrics"]["failed"] > result["metrics"]["passed"]:
        result["overall_status"] = "DEGRADED"
    else:
        result["overall_status"] = "PARTIAL"

    # Write receipt
    receipt_dir = hub_path / "state" / "receipts" / "culture-ship"
    receipt_dir.mkdir(parents=True, exist_ok=True)
    receipt_file = receipt_dir / f"smoke_test_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"

    with open(receipt_file, "w") as f:
        json.dump(result, f, indent=2, default=str)

    result["receipt_path"] = str(receipt_file)
    return result


if __name__ == "__main__":
    res = test_culture_ship_health()
    print(f"\n{'=' * 50}")
    print("CULTURE SHIP SMOKE TEST")
    print(f"Status: {res['overall_status']}")
    print(f"Results: {res['metrics']['passed']}/{res['metrics']['total']} passed")
    print(f"Receipt: {res['receipt_path']}")
    for t in res["tests"]:
        mark = "✓" if t["status"] == "PASS" else "⚠" if t["status"] == "WARN" else "✗"
        print(f"  {mark} {t['name']}: {t['status']}")
    print(f"{'=' * 50}\n")
