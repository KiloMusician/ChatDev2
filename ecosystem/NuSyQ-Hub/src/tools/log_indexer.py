"""log_indexer.py.

Purpose:
- Utility to locate and return the most recent machine-readable summary
    artifacts produced by tools such as `src/tools/maze_solver.py`.

Who/What/Where/When/Why/How:
- Who: Agents and human operators who need to find recent scan results.
- What: Searches the `logs/` directory for `maze_summary_*.json` and
    returns a stable, sorted list of file paths.
- Where: Typically run from the repository root; safe to import from
    orchestration code to discover recent summaries.
- When: Use during ingestion pipelines, scheduled jobs, or interactive
    agent fetch operations.
- Why: Downstream agents should prefer these deterministic JSON artifacts
    over parsing raw logs for structured data.
- How: Call `latest_maze_summaries()` to get N most recent summary files.

Integration tips:
- Pair with `src/tools/log_indexer.latest_maze_summaries()` from an
    ingestion workflow. Prefer a small `limit` (e.g., 3) when polling.
- If retention or archival is needed, move older summaries to `logs/storage/`
    and update the ingestion policy accordingly.

"""

from __future__ import annotations

from pathlib import Path


def latest_maze_summaries(log_dir: Path | None = None, limit: int = 3) -> list[Path]:
    if log_dir is None:
        log_dir = Path.cwd() / "logs"
    if not log_dir.exists():
        return []
    files = sorted(
        log_dir.glob("maze_summary_*.json"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    return files[:limit]


if __name__ == "__main__":
    for _p in latest_maze_summaries():
        pass
