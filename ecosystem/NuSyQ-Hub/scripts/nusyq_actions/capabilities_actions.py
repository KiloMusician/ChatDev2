"""Action module: Capability discovery and inventory."""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime
from typing import TYPE_CHECKING

from scripts.nusyq_actions.shared import emit_action_receipt

if TYPE_CHECKING:
    from scripts.start_nusyq import RepoPaths


SEARCH_ALIASES: dict[str, tuple[str, ...]] = {
    "memory": (
        "meta_learning",
        "continual_learning",
        "knowledge_graph",
        "embeddings",
        "quest",
        "history",
        "context",
        "intermediary",
    ),
    "neural": (
        "model",
        "embedding",
        "graph_learning",
        "meta_learning",
        "ai",
        "llm",
    ),
    "council": (
        "consensus",
        "vote",
        "delegate",
        "parallel",
        "orchestrator",
        "mjolnir",
    ),
}


def _expand_search_terms(search_term: str) -> set[str]:
    terms = {search_term.lower()}
    for alias, expansions in SEARCH_ALIASES.items():
        expanded = {alias, *expansions}
        if search_term.lower() in expanded:
            terms.update(expanded)
    return {term for term in terms if term}


def _iter_inventory_nodes(node: object, breadcrumbs: tuple[str, ...] = ()) -> list[dict[str, str]]:
    matches: list[dict[str, str]] = []
    if isinstance(node, dict):
        if breadcrumbs and any(
            key in node for key in ("description", "path", "type", "name", "command", "status", "summary")
        ):
            label = str(node.get("name") or breadcrumbs[-1])
            snippet = " ".join(
                str(node.get(key, "")) for key in ("description", "summary", "type", "path", "command", "status")
            ).strip()
            matches.append(
                {
                    "label": label,
                    "category": breadcrumbs[0],
                    "path": str(node.get("path", "")),
                    "snippet": snippet,
                }
            )
        for key, value in node.items():
            if isinstance(value, (dict, list)):
                matches.extend(_iter_inventory_nodes(value, (*breadcrumbs, str(key))))
    elif isinstance(node, list):
        for index, value in enumerate(node):
            if isinstance(value, (dict, list)):
                matches.extend(_iter_inventory_nodes(value, (*breadcrumbs, str(index))))
    return matches


def handle_capabilities(paths: RepoPaths, args: list[str] | None = None) -> int:
    """Enhanced capability discovery system using SystemCapabilityInventory.

    Usage:
        python start_nusyq.py capabilities [--search TERM] [--category TYPE] [--refresh]
    """
    print("🧠 NuSyQ Comprehensive Capability Discovery")
    print("=" * 70)

    # Parse arguments
    search_term = None
    category_filter = None
    refresh = False

    if args:
        i = 0
        while i < len(args):
            if args[i] == "--search" and i + 1 < len(args):
                search_term = args[i + 1].lower()
                i += 2
            elif args[i] == "--category" and i + 1 < len(args):
                category_filter = args[i + 1].lower()
                i += 2
            elif args[i] == "--refresh":
                refresh = True
                i += 1
            else:
                i += 1

    # Check if inventory exists
    inventory_path = paths.nusyq_hub / "data" / "system_capability_inventory.json"

    if not inventory_path.exists() or refresh:
        print("📊 Scanning repository for capabilities...")
        print("   (This may take a moment on first run)\n")

        # Run the capability inventory scanner
        result = subprocess.run(
            [sys.executable, "-m", "src.system.capability_inventory"],
            cwd=paths.nusyq_hub,
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            print("⚠️  Warning: Capability scan had issues")
            print(f"   {result.stderr[:200]}")

    # Load the inventory
    if not inventory_path.exists():
        print("❌ Capability inventory not found. Run with --refresh to generate.")
        emit_action_receipt(
            "capabilities",
            exit_code=1,
            metadata={"error": "inventory_not_found"},
        )
        return 1

    with open(inventory_path) as f:
        inventory = json.load(f)

    total_caps = inventory.get("total_capabilities", 0)
    stats = inventory.get("system_stats", {})
    quick_commands = inventory.get("quick_commands", {})

    print("📊 System Snapshot")
    print(f"   Total Capabilities: {total_caps}")
    print(f"   Quick Commands: {len(quick_commands)}")
    print(f"   Actions: {stats.get('total_actions', 0)}")
    print(f"   Passive Systems: {stats.get('total_passives', 0)}")
    print(f"   Active Quests: {stats.get('active_quests', 0)}")
    print()

    # Filter commands based on search/category
    filtered_commands = quick_commands

    semantic_matches: list[dict[str, str]] = []

    if search_term:
        search_terms = _expand_search_terms(search_term)
        filtered_commands = {
            name: info
            for name, info in quick_commands.items()
            if any(
                term
                in " ".join(
                    (
                        name.lower(),
                        info.get("description", "").lower(),
                        info.get("command", "").lower(),
                        info.get("category", "").lower(),
                    )
                )
                for term in search_terms
            )
        }
        semantic_matches = [
            item
            for item in _iter_inventory_nodes(inventory.get("capabilities", {}))
            if any(
                term
                in " ".join(
                    (
                        item.get("label", "").lower(),
                        item.get("category", "").lower(),
                        item.get("path", "").lower(),
                        item.get("snippet", "").lower(),
                    )
                )
                for term in search_terms
            )
        ]
        print(
            f"🔍 Search results for '{search_term}': "
            f"{len(filtered_commands)} quick commands, {len(semantic_matches)} capability matches\n"
        )
        if len(search_terms) > 1:
            print(f"   Expanded terms: {', '.join(sorted(search_terms))}\n")

    if category_filter:
        filtered_commands = {
            name: info
            for name, info in filtered_commands.items()
            if info.get("category", "").lower() == category_filter
        }
        print(f"📁 Filtered by category '{category_filter}': {len(filtered_commands)} matches\n")

    # Display commands in categories
    categories = {}
    for name, info in filtered_commands.items():
        cat = info.get("category", "other")
        if cat not in categories:
            categories[cat] = []
        categories[cat].append((name, info))

    # Show top categories
    for cat in sorted(categories.keys()):
        items = categories[cat]
        print(f"\n## {cat.upper()} ({len(items)} commands)")

        # Show first 5 items in each category
        for name, info in sorted(items[:5]):
            desc = info.get("description", "No description")
            # Truncate long descriptions
            if len(desc) > 80:
                desc = desc[:77] + "..."
            print(f"  • {name}")
            print(f"    {desc}")
            if "command" in info:
                print(f"    💻 {info['command']}")

        if len(items) > 5:
            print(f"  ... and {len(items) - 5} more")

    if semantic_matches:
        print("\n## INVENTORY MATCHES")
        for item in semantic_matches[:10]:
            snippet = item.get("snippet", "")
            if len(snippet) > 100:
                snippet = snippet[:97] + "..."
            print(f"  • {item['label']} [{item['category']}]")
            if item.get("path"):
                print(f"    📍 {item['path']}")
            if snippet:
                print(f"    {snippet}")
        if len(semantic_matches) > 10:
            print(f"  ... and {len(semantic_matches) - 10} more inventory matches")

    # Generate comprehensive markdown documentation
    doc_path = paths.nusyq_hub / "docs" / "CAPABILITY_DIRECTORY.md"
    doc_path.parent.mkdir(parents=True, exist_ok=True)

    with open(doc_path, "w", encoding="utf-8") as f:
        f.write("# NuSyQ System Capability Directory\n\n")
        f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"**Total Capabilities:** {total_caps}\n\n")
        f.write(f"This directory catalogs all {total_caps} discovered capabilities across the NuSyQ ecosystem.\n\n")

        f.write("## Quick Reference\n\n")
        f.write("```bash\n")
        f.write("# Search for capabilities\n")
        f.write("python scripts/start_nusyq.py capabilities --search TERM\n\n")
        f.write("# Filter by category\n")
        f.write("python scripts/start_nusyq.py capabilities --category monitoring\n\n")
        f.write("# Refresh inventory\n")
        f.write("python scripts/start_nusyq.py capabilities --refresh\n")
        f.write("```\n\n")

        f.write("## Categories\n\n")
        for cat in sorted(categories.keys()):
            items = categories[cat]
            f.write(f"### {cat.upper()} ({len(items)} capabilities)\n\n")

            for name, info in sorted(items):
                desc = info.get("description", "No description")
                # Clean up description for markdown
                if len(desc) > 200:
                    desc = desc[:197] + "..."

                f.write(f"#### `{name}`\n\n")
                f.write(f"{desc}\n\n")

                if "command" in info:
                    f.write(f"**Command:** `{info['command']}`\n\n")

                if "path" in info:
                    f.write(f"**Location:** `{info.get('path')}`\n\n")

        f.write("\n## AI Backends\n\n")
        f.write("- 🦖 **Ollama**: Local LLMs (qwen2.5-coder, deepseek-coder-v2, starcoder2)\n")
        f.write("- 👥 **ChatDev**: Multi-agent team (CEO, CTO, Programmer, Tester, Reviewer)\n")
        f.write("- 🧠 **Consciousness Bridge**: Semantic awareness + OmniTag protocol\n")
        f.write("- ⚛️ **Quantum Problem Resolver**: Multi-modal self-healing\n\n")

    print(f"\n📄 Documentation written to: {doc_path.relative_to(paths.nusyq_hub)}")
    print("\n✅ Capability discovery complete")
    emit_action_receipt(
        "capabilities",
        exit_code=0,
        metadata={
            "total_capabilities": total_caps,
            "refresh": refresh,
            "search_term": search_term,
            "category": category_filter,
            "doc_path": str(doc_path),
        },
    )
    return 0
