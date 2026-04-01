#!/usr/bin/env python3
"""Expand Zen Codex with new rules based on recent error patterns.

This script analyzes recent error reports and adds new Zen Codex rules
to capture common patterns and their solutions.
"""

import json
import sys
from datetime import datetime
from pathlib import Path

# Add repo root to path
REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT))


def load_zen_codex(path: Path) -> dict:
    """Load the Zen Codex JSON file."""
    with open(path) as f:
        return json.load(f)


def save_zen_codex(path: Path, data: dict) -> None:
    """Save the Zen Codex JSON file."""
    # Backup first
    backup_path = path.with_suffix(".json.backup")
    if path.exists():
        import shutil

        shutil.copy(path, backup_path)
        print(f"✅ Backup saved: {backup_path}")

    with open(path, "w") as f:
        json.dump(data, f, indent=2)
    print(f"✅ Zen Codex saved: {path}")


def create_fstring_placeholder_rule() -> dict:
    """Create rule for F541: f-string without placeholders."""
    return {
        "id": "fstring_without_placeholders",
        "version": 1,
        "triggers": {
            "errors": ["f-string without any placeholders", "ruff-F541"],
            "code_patterns": ["f['\\\"].*['\\\"]"],
        },
        "contexts": {
            "languages": ["python"],
            "tools": ["ruff", "flake8"],
            "repos": ["NuSyQ-Hub", "SimulatedVerse", "NuSyQ"],
        },
        "lesson": {
            "short": "Unnecessary f-string without placeholders wastes performance",
            "long": "F-strings have overhead for interpolation. If no placeholders are used, use a regular string instead. This is a common mistake when refactoring code or converting print statements.",
            "level": "beginner",
            "related_rules": [],
        },
        "suggestions": [
            {
                "strategy": "convert_to_regular_string",
                "description": "Remove f-prefix from string literal",
                "example": 'f"Hello world" -> "Hello world"',
                "when_to_use": "Always when no curly-brace placeholders present",
                "success_rate": 1.0,
            },
            {
                "strategy": "add_placeholder_if_intended",
                "description": "Add missing variable interpolation",
                "example": 'f"Error: description" -> f"Error: {var}"',
                "when_to_use": "When variable interpolation was intended",
                "success_rate": 0.95,
            },
        ],
        "actions": {
            "severity": "info",
            "auto_fix": True,
            "fix_strategy": "remove_f_prefix",
            "notify_agent": False,
            "learn_from_success": True,
        },
        "tags": ["python", "ruff", "f-string", "optimization", "beginner"],
        "lore": {
            "glyph": "ΦΣΤΡ",
            "story": "The Unnecessary Incantation - when magic words are spoken without power",
            "moral": "Invoke only the spells you need",
            "culture_ship_wisdom": "Efficiency is elegance",
        },
        "meta": {
            "hit_count": 3,
            "success_rate": 1.0,
            "first_seen": "2025-12-25",
            "last_seen": "2025-12-25",
            "affected_agents": ["claude", "copilot"],
            "repo_frequency": {"NuSyQ-Hub": 2, "SimulatedVerse": 0, "NuSyQ": 1},
        },
    }


def create_unused_import_rule() -> dict:
    """Create rule for F401: unused imports."""
    return {
        "id": "unused_imports",
        "version": 1,
        "triggers": {
            "errors": ["imported but unused", "ruff-F401", "F401 "],
            "code_patterns": [r"^import ", r"^from .* import "],
        },
        "contexts": {
            "languages": ["python"],
            "tools": ["ruff", "flake8", "pylint"],
            "repos": ["NuSyQ-Hub", "SimulatedVerse", "NuSyQ"],
        },
        "lesson": {
            "short": "Unused imports clutter code and slow startup time",
            "long": "Unused imports increase file size, slow module loading, and confuse readers about dependencies. They often result from refactoring or copy-paste. Modern IDEs and linters can auto-remove them.",
            "level": "beginner",
            "related_rules": [],
        },
        "suggestions": [
            {
                "strategy": "remove_unused_import",
                "description": "Delete the unused import statement",
                "example": "from typing import Dict, List  # Remove if unused",
                "when_to_use": "When import is truly not used anywhere",
                "success_rate": 0.98,
            },
            {
                "strategy": "check_for_type_annotations",
                "description": "Verify if import used in type annotations",
                "example": "def func(x: List[str]) -> Dict:  # List, Dict are used!",
                "when_to_use": "When false positive suspected in type hints",
                "success_rate": 0.85,
            },
            {
                "strategy": "move_to_type_checking_block",
                "description": "Move to TYPE_CHECKING block for type-only imports",
                "example": "if TYPE_CHECKING:\\n    from typing import Dict",
                "when_to_use": "When import only needed for type checking",
                "success_rate": 0.92,
            },
        ],
        "actions": {
            "severity": "info",
            "auto_fix": True,
            "fix_strategy": "remove_import_line",
            "notify_agent": False,
            "learn_from_success": True,
        },
        "tags": ["python", "ruff", "imports", "cleanup", "beginner"],
        "lore": {
            "glyph": "ΔΚΛΜ",
            "story": "The Unused Tools - carrying burdens never wielded",
            "moral": "Travel light, bring only what serves",
            "culture_ship_wisdom": "A Ship's cargo reflects its purpose",
        },
        "meta": {
            "hit_count": 1,
            "success_rate": 0.98,
            "first_seen": "2025-12-25",
            "last_seen": "2025-12-25",
            "affected_agents": ["claude", "copilot"],
            "repo_frequency": {"NuSyQ-Hub": 1, "SimulatedVerse": 0, "NuSyQ": 0},
        },
    }


def create_duplicate_kwarg_rule() -> dict:
    """Create rule for duplicate keyword arguments."""
    return {
        "id": "duplicate_keyword_argument",
        "version": 1,
        "triggers": {
            "errors": [
                "Duplicate keyword argument",
                "duplicate keyword argument",
                "keyword argument repeated",
            ],
            "code_patterns": [r".*\(.*=.*,.*=.*\)"],
        },
        "contexts": {
            "languages": ["python"],
            "tools": ["ruff", "mypy", "pylint"],
            "repos": ["NuSyQ-Hub", "SimulatedVerse", "NuSyQ"],
        },
        "lesson": {
            "short": "Duplicate keyword arguments cause SyntaxError in Python",
            "long": "Python functions cannot accept the same keyword argument twice. This typically happens during refactoring, copy-paste errors, or when manually resolving merge conflicts. The second value would silently override the first if allowed, which is confusing.",
            "level": "beginner",
            "related_rules": [],
        },
        "suggestions": [
            {
                "strategy": "remove_duplicate",
                "description": "Remove one of the duplicate keyword arguments",
                "example": "func(check=True, check=False) -> func(check=True)",
                "when_to_use": "When one argument is clearly redundant",
                "success_rate": 0.95,
            },
            {
                "strategy": "merge_values",
                "description": "Combine values if both are needed",
                "example": "func(tags=['a'], tags=['b']) -> func(tags=['a', 'b'])",
                "when_to_use": "When both values should be combined",
                "success_rate": 0.85,
            },
            {
                "strategy": "check_merge_conflict",
                "description": "Look for git merge conflict markers",
                "example": "Search for <<<<<<< HEAD in file",
                "when_to_use": "When duplicate appeared after merge",
                "success_rate": 0.90,
            },
        ],
        "actions": {
            "severity": "error",
            "auto_fix": False,
            "fix_strategy": "manual_review_required",
            "notify_agent": True,
            "learn_from_success": True,
        },
        "tags": ["python", "syntax", "refactoring", "merge-conflict", "beginner"],
        "lore": {
            "glyph": "ΨΩΞΘ",
            "story": "The Echo Chamber - when the same truth is spoken twice",
            "moral": "Say what needs saying, but say it once",
            "culture_ship_wisdom": "Redundancy in data, not in signal",
        },
        "meta": {
            "hit_count": 2,
            "success_rate": 0.95,
            "first_seen": "2025-12-25",
            "last_seen": "2025-12-25",
            "affected_agents": ["claude", "copilot"],
            "repo_frequency": {"NuSyQ-Hub": 2, "SimulatedVerse": 0, "NuSyQ": 0},
        },
    }


def main():
    """Main function to expand Zen Codex."""
    codex_path = REPO_ROOT / "zen_engine" / "codex" / "zen.json"

    if not codex_path.exists():
        print(f"❌ Zen Codex not found: {codex_path}")
        return 1

    print("📚 Expanding Zen Codex from Recent Errors")
    print("=" * 50)

    # Load current codex
    codex = load_zen_codex(codex_path)
    print(f"✅ Loaded Zen Codex v{codex['version']}")
    print(f"   Current rules: {len(codex['rules'])}")

    # Create new rules
    new_rules = [
        create_fstring_placeholder_rule(),
        create_unused_import_rule(),
        create_duplicate_kwarg_rule(),
    ]

    # Check for duplicates
    existing_ids = {rule["id"] for rule in codex["rules"]}
    rules_to_add = []

    for rule in new_rules:
        if rule["id"] in existing_ids:
            print(f"⚠️  Rule '{rule['id']}' already exists, skipping")
        else:
            rules_to_add.append(rule)
            print(f"✅ New rule: {rule['id']}")

    if not rules_to_add:
        print("\n℩  No new rules to add")
        return 0

    # Add new rules
    codex["rules"].extend(rules_to_add)

    # Update metadata
    codex["meta"]["last_updated"] = datetime.now().strftime("%Y-%m-%d")
    codex["meta"]["total_rules"] = len(codex["rules"])

    # Save
    save_zen_codex(codex_path, codex)

    print("\n🎉 Zen Codex expanded!")
    print(f"   Total rules: {len(codex['rules'])}")
    print(f"   New rules added: {len(rules_to_add)}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
