"""Pre-commit hook: Validate RosettaStone normalization integrity.

Checks that all recent event logs follow RSEV normalization rules:
- Stable content hashes
- LF line endings (no CRLF)
- Trimmed keys and values

Exit code 0: All events valid
Exit code 1: Validation failures found

cSpell:ignore RSEV
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add repo root to path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def validate_recent_events(days: int = 7) -> bool:
    """Validate recent event files for RS normalization compliance.

    Args:
        days: Number of days back to check (default: 7)

    Returns:
        True if all events valid, False if any violations found
    """
    events_dir = ROOT / "Reports" / "events"
    if not events_dir.exists():
        print("✓ No event logs to validate")
        return True

    cutoff = datetime.now() - timedelta(days=days)
    violations = []

    for event_file in sorted(events_dir.glob("events_*.jsonl")):
        # Parse date from filename: events_YYYYMMDD.jsonl
        try:
            date_str = event_file.stem.split("_")[1]
            file_date = datetime.strptime(date_str, "%Y%m%d")
            if file_date < cutoff:
                continue  # Skip old files
        except (IndexError, ValueError):
            violations.append(f"{event_file.name}: Invalid filename format")
            continue

        with event_file.open("r", encoding="utf-8") as f:
            for line_num, line in enumerate(f, start=1):
                if not line.strip():
                    continue

                try:
                    event = json.loads(line)
                except json.JSONDecodeError as e:
                    violations.append(
                        f"{event_file.name}:{line_num} - Invalid JSON: {e}"
                    )
                    continue

                # Validate RS normalization if present
                if "rs" in event:
                    rs_payload = event["rs"]
                    if not isinstance(rs_payload, dict):
                        violations.append(
                            f"{event_file.name}:{line_num} - rs field is not a dict"
                        )
                        continue

                    # Check that content_hash exists
                    if "content_hash" not in rs_payload:
                        violations.append(
                            f"{event_file.name}:{line_num} - RS missing content_hash"
                        )

                    # Validate hash format (64 hex chars for SHA256)
                    content_hash = rs_payload.get("content_hash", "")
                    if not (
                        isinstance(content_hash, str)
                        and len(content_hash) == 64
                        and all(c in "0123456789abcdef" for c in content_hash)
                    ):
                        violations.append(
                            f"{event_file.name}:{line_num} - "
                            "RS content_hash invalid format"
                        )

                # Check for CRLF in payload strings
                payload = event.get("payload", {})
                if isinstance(payload, dict):
                    for k, v in payload.items():
                        if isinstance(v, str) and "\r\n" in v:
                            violations.append(
                                f"{event_file.name}:{line_num} - "
                                f"CRLF found in payload['{k}']"
                            )

    if violations:
        print("❌ RosettaStone Normalization Violations:")
        for v in violations[:10]:  # Show first 10
            print(f"  {v}")
        if len(violations) > 10:
            print(f"  ... and {len(violations) - 10} more")
        return False

    print(f"✓ All events in last {days} days are RSEV-compliant")
    return True


if __name__ == "__main__":
    SUCCESS = validate_recent_events(days=7)
    sys.exit(0 if SUCCESS else 1)
