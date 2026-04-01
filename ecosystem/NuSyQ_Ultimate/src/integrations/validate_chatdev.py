#!/usr/bin/env python3
"""
Validate ChatDev installation and generate operational checklist.
"""

import json
import os
from datetime import datetime
from pathlib import Path

NUSYQ_ROOT_PATH = Path(os.getenv("NUSYQ_ROOT_PATH", "/mnt/c/Users/keath/NuSyQ"))
NUSYQ_HUB_ROOT = Path(os.getenv("NUSYQ_HUB_ROOT", "/mnt/c/Users/keath/Desktop/Legacy/NuSyQ-Hub"))


def validate_chatdev() -> dict:
    """Validate ChatDev installation and structure."""
    report = {
        "timestamp": datetime.now().isoformat(),
        "valid": False,
        "chatdev_path": None,
        "checks": {},
        "issues": [],
        "recommendations": [],
    }

    env_nusyq = NUSYQ_ROOT_PATH
    env_hub = NUSYQ_HUB_ROOT

    # Check for ChatDev in multiple locations
    possible_paths = [
        Path.cwd() / "ChatDev",  # Current directory
        env_nusyq / "ChatDev",  # Under NuSyQ root
        env_hub.parent.parent / "NuSyQ" / "ChatDev",  # relative to Hub parent
    ]

    chatdev_path = None
    for path in possible_paths:
        if path.exists() and (path / "run.py").exists():
            chatdev_path = path.resolve()
            break

    if not chatdev_path:
        report["issues"].append("ChatDev directory not found in expected locations")
        report["recommendations"].append(
            "Ensure NuSyQ/ChatDev is installed. See https://github.com/OpenBMB/ChatDev"
        )
        return report

    report["chatdev_path"] = str(chatdev_path)

    # Check required structure
    required_items = {
        "run.py": "Main ChatDev runner",
        "WareHouse": "Project output directory",
        "camel": "CAMEL framework module",
        "config": "Configuration directory",
    }

    for item, description in required_items.items():
        item_path = chatdev_path / item
        exists = item_path.exists()
        report["checks"][item] = {
            "exists": exists,
            "description": description,
            "path": str(item_path) if exists else None,
        }

    # Check for critical files
    critical_files = {
        "run.py": "ChatDev main runner script",
        "WareHouse/README.md": "Project readme template",
        "camel/__init__.py": "CAMEL module init",
    }

    for file_path, _description in critical_files.items():
        full_path = chatdev_path / file_path
        if not full_path.exists():
            report["issues"].append(f"Missing critical file: {file_path}")

    # Determine if valid
    all_required_exist = all(v["exists"] for v in report["checks"].values() if v["description"])
    report["valid"] = all_required_exist and len(report["issues"]) == 0

    if report["valid"]:
        report["recommendations"].append(f"✓ ChatDev is properly installed at {chatdev_path}")
        report["recommendations"].append("Ready for multi-agent software development")

    return report


def save_chatdev_validation(report: dict) -> None:
    """Save validation report."""
    # For Hub context
    hub_path = Path.cwd() if "NuSyQ-Hub" in str(Path.cwd()) else Path.cwd()
    if "NuSyQ-Hub" not in str(hub_path):
        # Assume we're in NuSyQ, save to receipts there
        pass

    receipt_dir = Path.cwd() / "state" / "receipts" / "chatdev"
    receipt_dir.mkdir(parents=True, exist_ok=True)

    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    receipt_file = receipt_dir / f"validation_{timestamp_str}.json"

    with open(receipt_file, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, default=str)

    print(f"✓ ChatDev validation saved: {receipt_file}")


def print_validation(report: dict) -> None:
    """Print validation report."""
    print("\n" + "=" * 80)
    print("CHATDEV VALIDATION & OPERATIONAL CHECKLIST")
    print("=" * 80)

    if report["valid"]:
        print("✓ ChatDev Installation: VALID")
        print(f"  Path: {report['chatdev_path']}")
    else:
        print("❌ ChatDev Installation: INVALID")
        if report["chatdev_path"]:
            print(f"  Path: {report['chatdev_path']}")

    print("\nStructure Checks:")
    for item, check in report["checks"].items():
        status = "✓" if check["exists"] else "❌"
        print(f"  {status} {item}: {check['description']}")

    if report["issues"]:
        print("\nIssues Found:")
        for issue in report["issues"]:
            print(f"  • {issue}")

    print("\nRecommendations:")
    for rec in report["recommendations"]:
        print(f"  • {rec}")

    print("\nOperational Checklist:")
    if report["valid"]:
        print("  ✓ ChatDev is ready for use")
        print("  1. To create new project: python run.py --task 'Your task description'")
        print("  2. Projects will be created in WareHouse/")
        print("  3. Outputs: [ProjectName_TIMESTAMP]/")
        print("  4. See: https://github.com/OpenBMB/ChatDev for full documentation")
    else:
        print("  ❌ ChatDev needs to be installed before use")


if __name__ == "__main__":
    validation_report = validate_chatdev()
    print_validation(validation_report)
    save_chatdev_validation(validation_report)
