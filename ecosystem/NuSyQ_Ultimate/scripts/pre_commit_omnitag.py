"""Pre-commit hook: Validate OmniTag usage in Python files.

Checks that log_event() calls include required fields:
- component (str)
- action (str)
- payload (dict)

Also validates that event schema constants are not modified.

Exit code 0: All usage valid
Exit code 1: Validation failures found

cSpell:ignore omnitag
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import List

# Add repo root to path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def validate_log_event_calls(file_path: Path) -> List[str]:
    """Check log_event() calls for required parameters.

    Args:
        file_path: Python file to analyze

    Returns:
        List of violation messages (empty if valid)
    """
    violations = []
    content = file_path.read_text(encoding="utf-8")

    # Find all log_event(...) calls
    # Simple regex - doesn't handle complex multiline cases
    # Only match log_event calls, not definitions (avoid 'def log_event')
    pattern = r"(?<!def )[^\w]log_event\s*\((.*?)\)"
    matches = re.finditer(pattern, content, re.DOTALL)

    for match in matches:
        # Get the full line containing the match
        start = content.rfind("\n", 0, match.start()) + 1
        end = content.find("\n", match.start())
        if end == -1:
            end = len(content)
        line = content[start:end].strip()
        # Skip if this is a function definition
        if line.startswith("def log_event"):
            continue
        args_text = match.group(1)
        line_num = content[: match.start()].count("\n") + 1

        # Check for required kwargs
        required = ["component=", "action=", "payload="]
        missing = [kw.rstrip("=") for kw in required if kw not in args_text]

        if missing:
            try:
                rel_path = str(file_path.relative_to(ROOT))
            except ValueError:
                rel_path = str(file_path)
            msg = f"{rel_path}:{line_num} - log_event missing: {', '.join(missing)}"
            violations.append(msg)

    return violations


def validate_omnitag_schema_unchanged() -> List[str]:
    """Ensure omnitag.py schema constants are not accidentally modified.

    Returns:
        List of violation messages (empty if unchanged)
    """
    omnitag_path = ROOT / "src" / "telemetry" / "omnitag.py"
    if not omnitag_path.exists():
        return ["src/telemetry/omnitag.py does not exist"]

    content = omnitag_path.read_text(encoding="utf-8")
    violations = []

    # Check for schema version
    if 'SCHEMA_VERSION = "1.0.0"' not in content:
        violations.append("omnitag.py: SCHEMA_VERSION modified or missing")

    # Check for EventRecord dataclass presence
    if "@dataclass" not in content or "class EventRecord:" not in content:
        violations.append("omnitag.py: EventRecord dataclass definition missing")

    return violations


def main(filenames: List[str]) -> int:
    """Run OmniTag validation on provided files.

    Args:
        filenames: List of file paths to check

    Returns:
        0 if all valid, 1 if violations found
    """
    all_violations = []

    # Always check omnitag.py schema integrity
    schema_violations = validate_omnitag_schema_unchanged()
    all_violations.extend(schema_violations)

    # Check log_event usage in staged files
    for filename in filenames:
        file_path = Path(filename)
        if not file_path.exists() or file_path.suffix != ".py":
            continue

        violations = validate_log_event_calls(file_path)
        all_violations.extend(violations)

    if all_violations:
        print("❌ OmniTag Schema/Usage Violations:")
        for v in all_violations:
            print(f"  {v}")
        return 1

    print("✓ OmniTag usage is compliant")
    return 0


if __name__ == "__main__":
    # Pre-commit passes filenames as arguments
    EXIT_CODE = main(sys.argv[1:])
    sys.exit(EXIT_CODE)
