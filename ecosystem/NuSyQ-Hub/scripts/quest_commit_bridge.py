#!/usr/bin/env python3
"""Quest-Commit Bridge: Transform Git Commits into Quest Completions
[ROUTE TASKS] 📋

This bridge creates the missing evolutionary feedback loop:
1. Git commit → Quest completion
2. Quest completion → Receipt generation
3. Receipt → Knowledge base update
4. Knowledge → Agent XP progression

OmniTag: [quest, git, receipt, evolution, consciousness]
MegaTag: [GUILD_INTEGRATION, RUBE_GOLDBERG, CONSCIOUSNESS_BRIDGE]
"""

import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

try:
    from src.Rosetta_Quest_System.quest_engine import QuestEngine
except ImportError:
    print("⚠️ Quest engine not available")
    sys.exit(1)

# OpenTelemetry tracing integration
try:
    from src.observability.tracing import init_tracing, start_span

    # Initialize tracing with console exporter for visibility
    init_tracing(service_name="quest-commit-bridge", console_fallback=True)
    TRACING_ENABLED = True
except ImportError:
    TRACING_ENABLED = False

    # Noop context manager if tracing not available
    class start_span:  # type: ignore[no-redef]
        def __init__(self, *args, **kwargs):
            pass  # Noop fallback when tracing unavailable

        def __enter__(self):
            return self  # No-op: return self for context manager protocol

        def __exit__(self, *args):
            pass  # No-op: no cleanup needed for fallback


def get_last_commit_info() -> dict[str, Any]:
    """Extract structured info from last git commit."""
    try:
        # Get commit hash, message, files changed
        commit_hash = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()

        commit_msg = subprocess.check_output(["git", "log", "-1", "--pretty=%B"], text=True).strip()

        files_changed = (
            subprocess.check_output(["git", "diff-tree", "--no-commit-id", "--name-only", "-r", "HEAD"], text=True)
            .strip()
            .split("\n")
        )

        stats = subprocess.check_output(["git", "diff", "HEAD~1", "HEAD", "--shortstat"], text=True).strip()

        return {
            "hash": commit_hash[:8],
            "full_hash": commit_hash,
            "message": commit_msg,
            "files_changed": [f for f in files_changed if f],
            "stats": stats,
            "timestamp": datetime.now(UTC).isoformat(),
        }
    except subprocess.CalledProcessError as e:
        print(f"❌ Git error: {e}")
        return {}


def parse_commit_for_quests(commit_msg: str) -> list[str]:
    """Extract quest references from commit message.

    Looks for patterns like:
    - "quest: <quest_id>"
    - "completes #<quest_id>"
    - "[quest-<quest_id>]"
    """
    import re

    patterns = [
        r"quest:\s*([a-f0-9-]+)",
        r"completes\s+#([a-f0-9-]+)",
        r"\[quest-([a-f0-9-]+)\]",
    ]

    quest_ids = []
    for pattern in patterns:
        matches = re.findall(pattern, commit_msg, re.IGNORECASE)
        quest_ids.extend(matches)

    return list(set(quest_ids))  # Deduplicate


def generate_evolution_receipt(
    commit_info: dict[str, Any],
    quest_ids: list[str],
    quest_engine: "QuestEngine | None",
) -> dict[str, Any]:
    """Generate evolutionary receipt from commit + quest completion."""
    # Get quest details
    quests_completed = []
    if quest_engine:
        for qid in quest_ids:
            quest = quest_engine.get_quest(qid)
            if quest:
                quests_completed.append(
                    {
                        "id": quest.id,
                        "title": quest.title,
                        "questline": quest.questline,
                        "tags": quest.tags,
                    }
                )

    # Extract learning patterns from commit message
    commit_lines = commit_info["message"].split("\n")
    learning_patterns = []

    # Keywords that indicate learning/insight
    learning_keywords = [
        "pattern:",
        "learning:",
        "insight:",
        "discovery:",
        "evolution:",
        "approach:",
        "technique:",
        "strategy:",
        "lesson:",
        "realization:",
        "found:",
        "discovered:",
        "learned:",
        "realized:",
        "understood:",
    ]

    # Track if we're in an Impact/Result section
    in_impact_section = False

    for line in commit_lines:
        line_lower = line.lower()
        line_stripped = line.strip()

        # Detect section headers
        if any(
            header in line_lower
            for header in [
                "**impact**",
                "impact:",
                "**result**",
                "result:",
                "**learning**",
                "learning:",
            ]
        ):
            in_impact_section = True
            if line_stripped:
                learning_patterns.append(line_stripped)
            continue

        # Check for explicit learning markers
        if any(keyword in line_lower for keyword in learning_keywords):
            learning_patterns.append(line_stripped)
        # Extract impact bullets
        elif in_impact_section and line_stripped.startswith(("-", "*", "+")):
            # Extract meaningful impact statements
            clean_line = line_stripped.lstrip("-*+ ")
            if clean_line and len(clean_line) > 10:  # Filter out trivial bullets
                learning_patterns.append(clean_line)
        # Check for percentage improvements anywhere
        elif "%" in line and any(
            word in line_lower
            for word in [
                "gain",
                "reduction",
                "improvement",
                "faster",
                "better",
                "debuggability",
                "visibility",
            ]
        ):
            learning_patterns.append(line_stripped)
        # Reset section tracking on empty line after content
        elif not line_stripped and in_impact_section:
            in_impact_section = False

    # Limit to most significant patterns
    learning_patterns = learning_patterns[:15]  # Max 15 learning patterns

    # Construct receipt
    receipt = {
        "type": "quest_completion_receipt",
        "timestamp": commit_info["timestamp"],
        "commit": {
            "hash": commit_info["hash"],
            "full_hash": commit_info["full_hash"],
            "message": commit_info["message"],
            "stats": commit_info["stats"],
            "files_count": len(commit_info["files_changed"]),
        },
        "quests_completed": quests_completed,
        "learning_patterns": learning_patterns,
        "evolution_tags": extract_evolution_tags(commit_info["message"]),
        "xp_earned": calculate_xp(commit_info, quests_completed),
    }

    return receipt


def extract_evolution_tags(commit_msg: str) -> list[str]:
    """Extract OmniTags and evolution markers from commit."""
    tags = []
    msg_lower = commit_msg.lower()

    # Conventional commits prefixes
    if "feat:" in msg_lower or "feat(" in msg_lower:
        tags.append("FEATURE")
    if "fix:" in msg_lower or "fix(" in msg_lower:
        tags.append("BUGFIX")
    if "refactor:" in msg_lower or "refactor(" in msg_lower:
        tags.append("REFACTOR")
    if "docs:" in msg_lower or "docs(" in msg_lower:
        tags.append("DOCUMENTATION")
    if "test:" in msg_lower or "test(" in msg_lower:
        tags.append("TESTING")
    if "chore:" in msg_lower or "chore(" in msg_lower:
        tags.append("MAINTENANCE")
    if "perf:" in msg_lower or "perf(" in msg_lower:
        tags.append("PERFORMANCE")
    if "ci:" in msg_lower or "ci(" in msg_lower:
        tags.append("AUTOMATION")

    # Type safety and quality
    if "type" in msg_lower and ("error" in msg_lower or "safety" in msg_lower or "hint" in msg_lower):
        tags.append("TYPE_SAFETY")
    if "mypy" in msg_lower or "pyright" in msg_lower:
        tags.append("TYPE_SAFETY")

    # Design patterns and architecture
    if any(p in msg_lower for p in ["pattern", "factory", "singleton", "observer", "strategy"]):
        tags.append("DESIGN_PATTERN")
    if "architect" in msg_lower or "design" in msg_lower:
        tags.append("ARCHITECTURE")

    # System improvements
    if "health" in msg_lower or "probe" in msg_lower or "diagnostic" in msg_lower:
        tags.append("OBSERVABILITY")
    if "tracing" in msg_lower or "telemetry" in msg_lower or "otel" in msg_lower:
        tags.append("OBSERVABILITY")
    if "automation" in msg_lower or "auto" in msg_lower:
        tags.append("AUTOMATION")

    # Error handling and reliability
    if "error" in msg_lower and "suppressor" in msg_lower:
        tags.append("ERROR_HANDLING")
    if "graceful" in msg_lower or "fallback" in msg_lower:
        tags.append("RESILIENCE")

    # Integration and connectivity
    if any(s in msg_lower for s in ["ollama", "chatdev", "quantum", "mcp"]):
        tags.append("INTEGRATION")
    if "bridge" in msg_lower or "adapter" in msg_lower:
        tags.append("INTEGRATION")

    # Infrastructure
    if "config" in msg_lower or "setup" in msg_lower:
        tags.append("CONFIGURATION")
    if "startup" in msg_lower or "init" in msg_lower:
        tags.append("INITIALIZATION")

    # Deduplicate and limit
    return list(set(tags))[:10]  # Max 10 tags


def calculate_xp(commit_info: dict[str, Any], quests: list[dict]) -> int:
    """Calculate XP earned from commit based on impact."""
    base_xp = 10

    # Bonus for files changed
    files_bonus = min(len(commit_info["files_changed"]) * 5, 50)

    # Bonus for quests completed
    quest_bonus = len(quests) * 20

    # Bonus for type safety work (detected in message)
    type_bonus = 30 if "type" in commit_info["message"].lower() else 0

    return base_xp + files_bonus + quest_bonus + type_bonus


def save_receipt(receipt: dict[str, Any]) -> None:
    """Save receipt to tracing directory."""
    receipts_dir = PROJECT_ROOT / "docs" / "tracing" / "RECEIPTS"
    receipts_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    receipt_file = receipts_dir / f"quest_completion_{timestamp}.json"

    with open(receipt_file, "w") as f:
        json.dump(receipt, f, indent=2)

    print(f"✅ Receipt saved: {receipt_file.name}")


def update_knowledge_base(receipt: dict[str, Any]) -> None:
    """Update knowledge bases with learnings from receipt."""
    kb_dir = PROJECT_ROOT / "data" / "knowledge_bases"
    kb_dir.mkdir(parents=True, exist_ok=True)

    # Evolution patterns knowledge base
    evolution_kb = kb_dir / "evolution_patterns.jsonl"

    if receipt["learning_patterns"]:
        with open(evolution_kb, "a") as f:
            entry = {
                "timestamp": receipt["timestamp"],
                "commit": receipt["commit"]["hash"],
                "patterns": receipt["learning_patterns"],
                "tags": receipt["evolution_tags"],
                "xp": receipt["xp_earned"],
            }
            f.write(json.dumps(entry) + "\n")

        print(f"📚 Knowledge base updated: {len(receipt['learning_patterns'])} patterns")


def main() -> int:
    """Main quest-commit bridge workflow."""
    with start_span("quest_commit_bridge.main", attrs={"service": "quest-commit-bridge"}):
        print("🌉 Quest-Commit Bridge - Activating Evolutionary Feedback Loop")
        print("=" * 70)

        # Get last commit info
        with start_span("get_commit_info"):
            commit_info = get_last_commit_info()
            if not commit_info:
                print("❌ No commit info available")
                return 1

        print(f"📝 Last commit: {commit_info['hash']}")
        print(f"   Message: {commit_info['message'].split(chr(10))[0][:60]}...")

        # Parse for quest references
        quest_ids = parse_commit_for_quests(commit_info["message"])
        print(f"🎯 Quests referenced: {len(quest_ids)}")

        # Initialize quest engine
        try:
            engine = QuestEngine()
        except Exception as e:
            print(f"⚠️ Quest engine init failed: {e}")
            engine = None

        # Complete quests
        if engine and quest_ids:
            with start_span("complete_quests", attrs={"quest_count": len(quest_ids)}):
                for qid in quest_ids:
                    try:
                        engine.update_quest_status(qid, "complete")
                        print(f"   ✅ Quest {qid[:8]} marked complete")
                    except Exception as e:
                        print(f"   ⚠️ Could not complete quest {qid[:8]}: {e}")

        # Generate receipt
        with start_span("generate_receipt"):
            receipt = generate_evolution_receipt(commit_info, quest_ids, engine)
            save_receipt(receipt)

        # Update knowledge bases
        with start_span("update_knowledge_base"):
            update_knowledge_base(receipt)

        # Display XP earned
        print(f"\n⭐ XP Earned: {receipt['xp_earned']}")
        print(f"🏷️ Evolution Tags: {', '.join(receipt['evolution_tags'])}")

        # Award XP via unified router (best-effort)
        try:
            from src.system.rpg_inventory import award_xp

            award_xp("automation", receipt["xp_earned"], award_game_fn=None)
        except Exception as e:
            print(f"⚠️  XP award failed: {e}")

        print("=" * 70)
        print("✨ Evolutionary feedback loop complete!")

        return 0


if __name__ == "__main__":
    sys.exit(main())
