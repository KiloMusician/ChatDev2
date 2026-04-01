#!/usr/bin/env python3
"""Process and report on the quest/PU queue so autonomous loops can keep moving."""

from __future__ import annotations

import argparse
import subprocess
import sys
from collections import Counter
from collections.abc import Iterable
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"

for path in (ROOT, SRC):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from automation.unified_pu_queue import PU, UnifiedPUQueue
from Rosetta_Quest_System.quest_engine import QuestEngine

REPORT_PATH = ROOT / "state" / "reports" / "quest_processor_status.md"
REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)


def _summary_lines(queue: Iterable[PU], limit: int = 5) -> list[str]:
    queue_list = list(queue)
    status_counts = Counter(pu.status for pu in queue_list)
    lines = [
        "# Quest Processor Status",
        "",
        f"- Generated: {datetime.now(UTC).isoformat()}",
        "",
        "## Queue Snapshot",
        f"- Total PUs: {len(queue_list)}",
    ]

    for status, count in sorted(status_counts.items()):
        lines.append(f"- {status}: {count}")

    pending = [pu for pu in queue_list if pu.status in {"queued", "approved"}]
    if pending:
        lines.append("")
        lines.append(f"## Pending PUs (first {limit})")
        for pu in pending[:limit]:
            lines.append(f"- {pu.id} | {pu.priority} | {pu.source_repo} | {pu.type} | {pu.title}")

    return lines


def _write_report(lines: list[str]) -> None:
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _run_pu_runner(mode: str) -> subprocess.CompletedProcess:
    cmd = [sys.executable, str(ROOT / "scripts" / "pu_queue_runner.py")]
    if mode == "real":
        cmd.append("--real")

    return subprocess.run(cmd, check=False, text=True)


def _gather_next_quest(engine: QuestEngine) -> str:
    pending = [q for q in engine.quests.values() if q.status == "pending"]
    if not pending:
        return "No pending quests available at this time."
    pending.sort(key=lambda quest: (len(quest.dependencies), quest.created_at))
    quest = pending[0]
    return f"Suggested quest: {quest.title} (id={quest.id}) | questline={quest.questline} | priority={quest.priority}"


def main() -> int:
    parser = argparse.ArgumentParser(description="Review or advance the quest/PU queue.")
    parser.add_argument(
        "--next-action",
        action="store_true",
        help="Evaluate the queue and run the next high-leverage action (PU runner).",
    )
    parser.add_argument(
        "--mode",
        choices=["simulated", "real"],
        default="simulated",
        help="Runner mode when processing the queue.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=5,
        help="How many queue entries to include in the report.",
    )
    args = parser.parse_args()

    queue_manager = UnifiedPUQueue()
    queue = queue_manager.queue
    lines = _summary_lines(queue, limit=args.limit)
    if args.next_action:
        pending = [pu for pu in queue if pu.status in {"queued", "approved"}]
        if pending:
            print(f"⏳ Running queue runner ({args.mode}) to act on {len(pending)} PUs...")
            result = _run_pu_runner(args.mode)
            print(result.stdout or result.stderr or "")
            queue_manager = UnifiedPUQueue()
            queue = queue_manager.queue
            lines = _summary_lines(queue, limit=args.limit)
            lines.append("")
            lines.append("## Last action")
            lines.append(f"- Command: {' '.join(result.args)}")
            lines.append(f"- Exit: {result.returncode}")
        else:
            engine = QuestEngine()
            suggestion = _gather_next_quest(engine)
            lines.append("")
            lines.append("## Next steps from Quest Engine")
            lines.append(f"- {suggestion}")
            print("⚙️  No queued PUs found; using quest engine suggestion.")

    _write_report(lines)
    print(f"📝 Quest report written to {REPORT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
