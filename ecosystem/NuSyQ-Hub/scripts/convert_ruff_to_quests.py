#!/usr/bin/env python3
"""Convert Ruff Errors to Actionable Quests

Takes the ruff_errors.json file and converts it into Processing Units
that can be executed by the autonomous quest system.
"""

import json
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path


def load_ruff_errors() -> list[dict]:
    """Load ruff errors from JSON file."""
    ruff_file = Path("data/diagnostics/ruff_errors.json")
    if not ruff_file.exists():
        print("❌ No ruff errors found. Run: python -m ruff check src/ --output-format=json")
        return []

    with open(ruff_file, encoding="utf-8") as f:
        return json.load(f)


def categorize_errors(errors: list[dict]) -> dict:
    """Categorize errors by type and severity."""
    by_code = defaultdict(list)

    for error in errors:
        code = error.get("code", "unknown")
        by_code[code].append(error)

    return dict(by_code)


def create_quest_from_error_group(code: str, errors: list[dict]) -> dict:
    """Create a quest from a group of similar errors."""
    # Categorize by file
    by_file = defaultdict(list)
    for error in errors:
        filename = error.get("filename", "unknown")
        by_file[filename].append(error)

    # Determine priority based on error code
    priority_map = {
        "E999": "critical",  # Syntax errors
        "F": "high",  # Flake8 errors (undefined names, etc.)
        "E4": "high",  # Import errors
        "E7": "high",  # Statement errors
        "C901": "medium",  # Complexity
        "E501": "low",  # Line too long
        "W": "low",  # Warnings
    }

    priority = "medium"
    for prefix, pri in priority_map.items():
        if code.startswith(prefix):
            priority = pri
            break

    # Determine quest type
    quest_type = "RefactorPU"
    if code.startswith("F"):
        quest_type = "BugFixPU"
    elif code.startswith("E4"):
        quest_type = "BugFixPU"

    # Get example message
    example_msg = errors[0].get("message", "Fix error")

    return {
        "id": f"ruff_{code}_{int(datetime.now().timestamp())}",
        "title": f"Fix Ruff {code}: {example_msg} ({len(errors)} occurrences)",
        "description": f"Resolve {len(errors)} instances of {code} across {len(by_file)} files",
        "type": quest_type,
        "priority": priority,
        "source_repo": "NuSyQ-Hub",
        "created_at": datetime.now().isoformat(),
        "status": "queued",
        "metadata": {
            "diagnostic_source": "ruff",
            "code": code,
            "files_affected": list(by_file.keys())[:20],  # Limit to 20 files
            "total_occurrences": len(errors),
            "example_error": {
                "file": errors[0].get("filename", ""),
                "line": errors[0].get("location", {}).get("row", 0),
                "message": example_msg,
            },
        },
        "proof_criteria": [
            f"All {code} errors resolved",
            "Ruff check passes for affected files",
            "No new errors introduced",
        ],
        "assigned_agents": [],
    }


def submit_to_queue(pus: list[dict]) -> dict:
    """Submit PUs to unified queue."""
    queue_file = Path("data") / "unified_pu_queue.json"

    # Load existing queue
    if queue_file.exists():
        with open(queue_file, encoding="utf-8") as f:
            existing_queue = json.load(f)
            if isinstance(existing_queue, list):
                queue_list = existing_queue
            else:
                queue_list = existing_queue.get("queue", [])
    else:
        queue_list = []

    # Add new PUs (avoid duplicates)
    existing_ids = {pu.get("id") for pu in queue_list}
    new_pus = [pu for pu in pus if pu.get("id") not in existing_ids]

    queue_list.extend(new_pus)

    # Save
    queue_file.parent.mkdir(parents=True, exist_ok=True)
    with open(queue_file, "w", encoding="utf-8") as f:
        json.dump(queue_list, f, indent=2)

    return {
        "total_submitted": len(new_pus),
        "duplicates_skipped": len(pus) - len(new_pus),
        "queue_size": len(queue_list),
    }


def main():
    """Main execution."""
    print("=" * 80)
    print("🔄 RUFF ERROR → QUEST PIPELINE")
    print("=" * 80)
    print()

    # Load errors
    print("📊 Loading ruff errors...")
    errors = load_ruff_errors()

    if not errors:
        print("❌ No errors to process")
        return 1

    print(f"  ✅ Loaded {len(errors)} ruff errors")
    print()

    # Categorize
    print("📑 Categorizing by error code...")
    categorized = categorize_errors(errors)
    print(f"  ✅ Found {len(categorized)} unique error types")
    print()

    # Create quests
    print("🎯 Creating Processing Units...")
    pus = []
    for code, code_errors in categorized.items():
        pu = create_quest_from_error_group(code, code_errors)
        pus.append(pu)

    print(f"  ✅ Created {len(pus)} PUs")
    print()

    # Submit to queue
    print("📤 Submitting to unified PU queue...")
    result = submit_to_queue(pus)
    print(f"  ✅ Submitted {result['total_submitted']} new PUs")
    print(f"  Info: Skipped {result['duplicates_skipped']} duplicates")
    print(f"  📊 Total queue size: {result['queue_size']}")
    print()

    # Show summary
    print("=" * 80)
    print("📋 QUEST SUMMARY BY PRIORITY")
    print("=" * 80)

    by_priority = defaultdict(list)
    for pu in pus:
        by_priority[pu["priority"]].append(pu)

    for priority in ["critical", "high", "medium", "low"]:
        if priority in by_priority:
            print(f"\n🔥 {priority.upper()} Priority ({len(by_priority[priority])} quests):")
            for pu in sorted(
                by_priority[priority],
                key=lambda x: x["metadata"]["total_occurrences"],
                reverse=True,
            )[:5]:
                count = pu["metadata"]["total_occurrences"]
                code = pu["metadata"]["code"]
                print(f"  • {code}: {count} occurrences")

            if len(by_priority[priority]) > 5:
                print(f"  ... and {len(by_priority[priority]) - 5} more")

    print()
    print("=" * 80)
    print("✅ PIPELINE COMPLETE")
    print("=" * 80)
    print()
    print("🎯 Next Steps:")
    print("  1. Run quest generator:")
    print("     python src/automation/autonomous_quest_generator.py")
    print()
    print("  2. Or run auto-fixes for simple errors:")
    print("     python -m ruff check src/ --fix")
    print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
