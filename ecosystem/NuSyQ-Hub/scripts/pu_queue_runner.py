"""PU Queue Runner with simulated and real execution modes

- Loads data/unified_pu_queue.json
- For each PU in queued/approved: assign_agents, execute
- Writes status report to state/reports/pu_queue_status.md
- Simulated mode (default): marks complete without real work
- Real mode (--real): uses Quantum Problem Resolver for actual execution
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"

# Ensure both ROOT and SRC are in sys.path for imports
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from automation.unified_pu_queue import PU, UnifiedPUQueue

REPORT_PATH = ROOT / "state" / "reports" / "pu_queue_status.md"
REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)


def _summarize(queue: list[PU]) -> str:
    counts: dict[str, int] = {}
    for pu in queue:
        counts[pu.status] = counts.get(pu.status, 0) + 1
    lines = ["# PU Queue Status", ""]
    lines.append(f"Total: {len(queue)}")
    for status, cnt in sorted(counts.items()):
        lines.append(f"- {status}: {cnt}")
    lines.append("")
    top = queue[:5]
    if top:
        lines.append("## Sample (first 5)")
        for pu in top:
            lines.append(f"- {pu.id} | {pu.type} | {pu.title} | {pu.status}")
    return "\n".join(lines)


async def _execute_pu_real(pu: PU) -> dict:
    """Execute PU using Quantum Problem Resolver for real work."""
    try:
        from src.healing.quantum_problem_resolver import QuantumProblemResolver
    except ImportError as e:
        return {"success": False, "executor": "quantum_problem_resolver", "error": str(e)}

    try:
        resolver = QuantumProblemResolver(root_path=ROOT)

        # Create problem context from PU
        problem_context = {
            "pu_id": pu.id,
            "type": pu.type,
            "title": pu.title,
            "description": pu.description,
            "metadata": pu.metadata,
        }

        # Resolve using quantum methods
        result = await resolver.resolve_quantum_problem_from_context(problem_context)

        return {
            "success": result.get("resolved", False),
            "executor": "quantum_problem_resolver",
            "result": result,
        }
    except (RuntimeError, ValueError, KeyError, TypeError, OSError) as e:
        return {"success": False, "executor": "quantum_problem_resolver", "error": str(e)}


def _process_pu(q: UnifiedPUQueue, pu: PU, real_mode: bool) -> bool:
    """Process a single PU, returning True if processed."""
    if pu.status not in {"queued", "approved"}:
        return False

    # Assign agents if none
    if not pu.assigned_agents:
        assigned = q.assign_agents(pu.id)
        if assigned:
            pu.assigned_agents = assigned

    # Transition to executing
    pu.status = "executing"
    print(f"⚙️  Processing: {pu.id} | {pu.title}")

    # Dual-write PU start event to DuckDB for realtime tracking
    try:
        from datetime import datetime
        from pathlib import Path

        from src.duckdb_integration.dual_write import insert_single_event

        insert_single_event(
            Path("data/state.duckdb"),
            {
                "timestamp": datetime.now().isoformat(),
                "event": "pu_started",
                "details": {
                    "pu_id": pu.id,
                    "title": pu.title,
                    "type": pu.type,
                    "assigned_agents": pu.assigned_agents or [],
                    "real_mode": real_mode,
                },
            },
        )
    except Exception:
        pass  # Graceful degradation if DuckDB unavailable

    if real_mode:
        # Real execution using Quantum Problem Resolver
        # Using asyncio to run the coroutine in the current loop
        result = asyncio.get_event_loop().run_until_complete(_execute_pu_real(pu))
        pu.execution_results = result
        pu.status = "completed" if result.get("success") else "failed"
    else:
        # Simulated fast path
        pu.execution_results = {"note": "simulated completion", "executor": "pu_queue_runner"}
        pu.status = "completed"

    # Dual-write PU completion event to DuckDB
    try:
        from datetime import datetime
        from pathlib import Path

        from src.duckdb_integration.dual_write import insert_single_event

        event_type = "pu_completed" if pu.status == "completed" else "pu_failed"
        insert_single_event(
            Path("data/state.duckdb"),
            {
                "timestamp": datetime.now().isoformat(),
                "event": event_type,
                "details": {
                    "pu_id": pu.id,
                    "title": pu.title,
                    "status": pu.status,
                    "execution_results": pu.execution_results or {},
                    "real_mode": real_mode,
                },
            },
        )
    except Exception:
        pass  # Graceful degradation

    return True


def _persist_queue(q: UnifiedPUQueue) -> None:
    """Persist queue using public method if available, fallback otherwise."""
    save_fn = getattr(q, "save_queue", None) or getattr(q, "_save_queue", None)
    if callable(save_fn):
        save_fn()


def main_async(real_mode: bool = False) -> None:
    """Run PU queue processing in simulated or real mode."""
    q = UnifiedPUQueue()

    mode_label = "REAL" if real_mode else "SIMULATED"
    print(f"\n🔄 PU Queue Runner [{mode_label} MODE]\n")

    processed = 0
    for pu in q.queue:
        if _process_pu(q, pu, real_mode):
            processed += 1

    _persist_queue(q)

    # Write report
    report = _summarize(q.queue)
    REPORT_PATH.write_text(report, encoding="utf-8")
    print(f"\n{report}")
    print(f"\n✅ Processed {processed} PUs in {mode_label} mode")
    print(f"📄 Report: {REPORT_PATH}\n")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="PU Queue Runner - Process queued PUs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  python scripts/pu_queue_runner.py              # Simulated mode (default)
  python scripts/pu_queue_runner.py --real       # Real execution mode
        """,
    )
    parser.add_argument(
        "--real",
        action="store_true",
        help="Use real execution (Quantum Problem Resolver) instead of simulation",
    )
    args = parser.parse_args()

    # Run the (now synchronous) main; dispatch real-mode awaits internally
    main_async(real_mode=args.real)


if __name__ == "__main__":
    main()
