#!/usr/bin/env python3
"""Phase 2B: Execute ONE real issue remediation (MsgX task)

Pick the safest issue: clean stale mesh agents from service registry
Convert to MsgX task, execute remediation, record to substrate registry
"""

import json
import sqlite3
import uuid
from datetime import UTC, datetime, timezone
from pathlib import Path

BASE = Path(__file__).parent.parent
SUBSTRATE_DIR = BASE / ".substrate"
STATE_DIR = BASE / "state"


def _now():
    return datetime.now(UTC).isoformat()


def safe_inspect_agents():
    """Inspect service_registry.db for stale agents (safe read-only)"""
    db_path = STATE_DIR / "service_registry.db"
    if not db_path.exists():
        return {"ok": False, "error": "service_registry.db not found"}

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Try to list tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [t[0] for t in cursor.fetchall()]

        conn.close()
        return {
            "ok": True,
            "db_exists": True,
            "tables": tables,
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}


def create_msgx_task(issue_id, action, service, reason):
    """Create an MsgX task packet"""
    return {
        "msgx_id": str(uuid.uuid4()),
        "version": "1.0",
        "timestamp": _now(),
        "source": "phase-2b-remediation",
        "target": "substrate-executor",
        "action": action,
        "payload": {
            "issue_id": issue_id,
            "service": service,
            "reason": reason,
            "priority": "P2",
            "safe_mode": True,
        },
        "decision_path": ["culture-ship", "phase-2b"],
        "expected_outcome": f"Cleaned stale agent references in {service}",
    }


def record_remediation(msgx_id, status, details):
    """Record remediation result to substrate registry"""
    entry = {
        "type": "remediation_executed",
        "timestamp": _now(),
        "msgx_id": msgx_id,
        "status": status,
        "details": details,
    }

    registry_path = SUBSTRATE_DIR / "registry.jsonl"
    try:
        with open(registry_path, "a") as f:
            f.write(json.dumps(entry) + "\n")
        return True
    except Exception as e:
        print(f"Error recording: {e}")
        return False


def main():
    print("\n=== Phase 2B: Remediation Execution ===\n")

    # Step 1: Inspect agents
    print("Step 1: Inspecting service registry...")
    inspection = safe_inspect_agents()
    print(f"  Result: {inspection}\n")

    # Step 2: Create MsgX task for agent cleanup
    issue_id = "stale-mesh-agents-cleanup"
    msgx = create_msgx_task(
        issue_id,
        "heal",
        "lattice-service-registry",
        "Remove stale agent entries that missed heartbeats",
    )
    print("Step 2: Created MsgX task")
    print(f"  MsgX ID: {msgx['msgx_id']}")
    print(f"  Action: {msgx['action']}")
    print(f"  Service: {msgx['payload']['service']}\n")

    # Step 3: Execute safe remediation (record task only, don't modify DB yet)
    print("Step 3: Executing remediation (safe mode)...")
    result = record_remediation(
        msgx["msgx_id"],
        "queued",
        {
            "action": "inspect_agents",
            "status": inspection,
        },
    )
    print(f"  Recorded to registry: {result}\n")

    # Step 4: Verify registry entry
    registry_path = SUBSTRATE_DIR / "registry.jsonl"
    if registry_path.exists():
        with open(registry_path) as f:
            lines = f.readlines()
        print("Step 4: Substrate registry state")
        print(f"  Total entries: {len(lines)}")
        print("  Last 2 entries:\n")
        for line in lines[-2:]:
            entry = json.loads(line)
            print(f"    {json.dumps(entry, indent=6)}\n")

    print("\n=== Phase 2B Complete ===")
    print(f"Remediation queued: {issue_id}")
    print(f"MsgX packet: {msgx['msgx_id']}")
    print("Status: SAFE_MODE (inspection only, no mutations)\n")


if __name__ == "__main__":
    main()
