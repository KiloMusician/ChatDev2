"""
reflect.py — Daily reflection + planning agent.

Queries memory for the last 24 hours, uses the LLM to summarize:
  - Accomplishments, mistakes, patterns
  - Prioritized plan for tomorrow
  - Auto-adds tasks to the queue

Usage:
    python reflect.py                  # full reflection
    python reflect.py --quiet          # just the summary
    python reflect.py --hours 48       # 48-hour window
    python reflect.py --from-todo      # parse todo.md unchecked items → memory tasks
"""
from __future__ import annotations

import json
import sys
import time
from datetime import datetime
from pathlib import Path

from memory import Memory, get_memory
from llm_client import LLMClient, Prompts


REFLECTION_DIR = Path("reports/reflections")
REFLECTION_DIR.mkdir(parents=True, exist_ok=True)

REFLECTION_PROMPT = """\
You are analyzing a developer's activity log for the past {hours} hours in the Terminal Depths project.

## Activity Summary
- Total interactions: {interactions}
- Success rate: {success_rate}%
- New errors: {errors_new}
- Unresolved errors: {errors_unresolved}
- Pending tasks: {pending_tasks}
- LLM cache entries: {cache_entries}
- Generated content pieces: {generated_content}

## Recent Errors (sample)
{error_sample}

## Recent Interactions (sample)
{interaction_sample}

## Recent Learnings
{learning_sample}

---
Provide a structured reflection in this exact format:

ACCOMPLISHMENTS:
- (list 3-5 things that went well or were built)

MISTAKES:
- (list 2-3 errors, failures, or inefficiencies observed)

PATTERNS:
- (list 1-3 patterns you notice in the data)

PRIORITIES_TOMORROW:
1. (highest priority actionable task, be specific)
2. (second priority)
3. (third priority)
4. (fourth priority)
5. (fifth priority)

INSIGHT:
(One key learning to remember going forward, 1 sentence.)
"""


def _sample_str(items: list[dict], fields: list[str], limit: int = 5) -> str:
    lines = []
    for item in items[:limit]:
        parts = [str(item.get(f, ""))[:60] for f in fields]
        lines.append("  " + " | ".join(parts))
    return "\n".join(lines) if lines else "  (none)"


def run_reflection(hours: int = 24, quiet: bool = False, llm: LLMClient | None = None) -> dict:
    mem = get_memory()
    llm = llm or LLMClient()

    stats = mem.get_stats(hours=hours)
    errors = mem.get_recent_errors(limit=5, unresolved_only=False)
    interactions = mem.get_recent_interactions(hours=hours)[:10]
    learnings = mem.get_learnings(limit=5)

    prompt = REFLECTION_PROMPT.format(
        hours=hours,
        interactions=stats["interactions"],
        success_rate=stats["success_rate_pct"],
        errors_new=stats["errors_new"],
        errors_unresolved=stats["errors_unresolved"],
        pending_tasks=stats["pending_tasks"],
        cache_entries=stats["cache_entries"],
        generated_content=stats["generated_content"],
        error_sample=_sample_str(errors, ["error_type", "message", "context"]),
        interaction_sample=_sample_str(interactions, ["type", "input", "success"]),
        learning_sample=_sample_str(learnings, ["insight"]),
    )

    if not quiet:
        print(f"\n[reflect] Querying LLM for {hours}h reflection…")

    reflection_text = llm.generate(
        prompt,
        max_tokens=600,
        temperature=0.4,
        system="You are a precise development analyst. Follow the format exactly.",
    )

    # ── Parse priorities and auto-add tasks ──────────────────────────────────
    tasks_added = []
    in_priorities = False
    for line in reflection_text.splitlines():
        stripped = line.strip()
        if stripped.startswith("PRIORITIES_TOMORROW"):
            in_priorities = True
            continue
        if in_priorities and stripped and stripped[0].isdigit() and stripped[1] in ".):":
            desc = stripped[2:].strip().lstrip(" ")
            if desc and not desc.startswith("("):
                pri = 10 - int(stripped[0])
                tid = mem.add_task(desc, priority=pri, category="reflection")
                tasks_added.append((tid, desc))
        if in_priorities and stripped.startswith("INSIGHT"):
            in_priorities = False

    # ── Extract and store the insight ────────────────────────────────────────
    insight = ""
    for line in reflection_text.splitlines():
        if line.strip().startswith("INSIGHT:"):
            insight = line.split("INSIGHT:", 1)[-1].strip()
            if not insight:
                continue
            mem.add_learning(insight, tags=["reflection", "auto"], source="reflect.py")
            break

    # ── Log the reflection interaction ───────────────────────────────────────
    mem.log_interaction(
        "reflection",
        f"period={hours}h",
        reflection_text[:500],
        success=True,
    )

    # ── Save to file ─────────────────────────────────────────────────────────
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = REFLECTION_DIR / f"reflection_{ts}.md"
    out_path.write_text(
        f"# Reflection — {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
        f"**Period:** last {hours} hours  \n"
        f"**Stats:** {json.dumps(stats, indent=2)}\n\n"
        f"---\n\n"
        + reflection_text
        + f"\n\n---\n_Tasks added to queue: {len(tasks_added)}_\n"
    )

    result = {
        "reflection": reflection_text,
        "tasks_added": len(tasks_added),
        "insight": insight,
        "stats": stats,
        "saved": str(out_path),
    }

    if not quiet:
        print(f"\n{'='*60}")
        print(reflection_text)
        print(f"\n[reflect] Tasks auto-queued: {len(tasks_added)}")
        for tid, desc in tasks_added:
            print(f"  [{tid}] {desc[:60]}")
        print(f"[reflect] Saved: {out_path}")

    return result


_TODO_PATH = Path("todo.md")
_UNCHECKED_RE = __import__("re").compile(r"^[-*]\s+\[ \]\s+(.+)", __import__("re").MULTILINE)


def _parse_todo_tasks() -> list[str]:
    """Extract unchecked items from todo.md."""
    if not _TODO_PATH.exists():
        return []
    content = _TODO_PATH.read_text()
    return [m.strip() for m in _UNCHECKED_RE.findall(content)]


def sync_todo_to_memory(quiet: bool = False) -> list[tuple[int, str]]:
    """Parse todo.md unchecked items and add them as memory tasks.

    Returns list of (task_id, description) for newly created tasks.
    Skips descriptions already present as pending tasks (by keyword match).
    """
    mem = get_memory()
    items = _parse_todo_tasks()
    if not items:
        if not quiet:
            print("[reflect] No unchecked items found in todo.md")
        return []

    existing = {t["description"].strip().lower() for t in mem.get_pending_tasks()}
    added: list[tuple[int, str]] = []

    for item in items:
        key = item.lower()
        if any(key[:40] in e or e[:40] in key for e in existing):
            if not quiet:
                print(f"[reflect] SKIP (already in queue): {item[:60]}")
            continue
        category = "todo"
        for kw, cat in [
            ("lore", "lore"), ("challenge", "challenge"), ("code", "code"),
            ("doc", "doc"), ("test", "test"), ("fix", "bug"), ("agent", "agent"),
            ("refactor", "refactor"), ("game", "game"), ("script", "script"),
        ]:
            if kw in key:
                category = cat
                break

        tid = mem.add_task(item, priority=3, category=category, source="todo.md")
        added.append((tid, item))
        existing.add(key)
        if not quiet:
            print(f"[reflect] QUEUED [{tid}] {item[:70]}")

    return added


if __name__ == "__main__":
    hours = 24
    quiet = "--quiet" in sys.argv
    from_todo = "--from-todo" in sys.argv

    for i, arg in enumerate(sys.argv):
        if arg == "--hours" and i + 1 < len(sys.argv):
            hours = int(sys.argv[i + 1])

    if from_todo:
        added = sync_todo_to_memory(quiet=quiet)
        if not quiet:
            print(f"\n[reflect] Synced {len(added)} task(s) from todo.md to memory queue.")
    else:
        run_reflection(hours=hours, quiet=quiet)
