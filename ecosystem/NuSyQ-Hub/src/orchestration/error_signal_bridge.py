"""Error → Signal Bridge.

======================

Purpose: When error scanner detects problems, automatically post signals to guild board.

Workflow:
1. Run error_ground_truth_scanner.py → generates state/ground_truth_errors.json
2. Parse error report and group by severity/category
3. For each error group, create a signal with:
   - type: "error"
   - severity: "critical" | "high" | "medium" | "low"
   - message: Descriptive message
   - context: Error details, file paths, line counts
4. Post signal to guild board (async)
5. Log signal_id back to error report for traceability
6. Update metrics

Run via:
    python src/orchestration/error_signal_bridge.py [--mode once|watch|test]

Modes:
    once  - Run error scan + post signals once
    watch - Monitor for new errors every 60s
    test  - Run in test mode (don't modify guild board)
"""

from __future__ import annotations

import asyncio
import json
import logging
import subprocess
import sys
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    from datetime import UTC  # type: ignore[attr-defined]
except ImportError:
    UTC = timezone.utc  # noqa: UP017

# Get workspace root
SCRIPT_DIR = Path(__file__).resolve().parent.parent
ROOT = SCRIPT_DIR.parent


def _freshest_unified_report() -> Path:
    """Return best unified error report artifact (scope/confidence aware)."""
    diagnostics_dir = ROOT / "docs" / "Reports" / "diagnostics"
    latest = diagnostics_dir / "unified_error_report_latest.json"
    candidates = [p for p in diagnostics_dir.glob("unified_error_report_*.json") if p.exists()]
    if latest.exists():
        candidates.append(latest)
    if not candidates:
        return latest

    best_path: Path | None = None
    best_score = float("-inf")
    best_ts: datetime | None = None

    for report_path in candidates:
        try:
            payload = json.loads(report_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(payload, dict):
            continue

        timestamp_raw = payload.get("timestamp")
        if isinstance(timestamp_raw, str) and timestamp_raw.strip():
            normalized = timestamp_raw.replace("Z", "+00:00")
            try:
                ts = datetime.fromisoformat(normalized)
            except ValueError:
                ts = datetime.fromtimestamp(report_path.stat().st_mtime, tz=UTC)
        else:
            try:
                ts = datetime.fromtimestamp(report_path.stat().st_mtime, tz=UTC)
            except OSError:
                continue
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=UTC)

        ground_truth = payload.get("ground_truth")
        gt = ground_truth if isinstance(ground_truth, dict) else {}
        scope = gt.get("scope")
        scope_obj = scope if isinstance(scope, dict) else {}
        targets_raw = scope_obj.get("targets", payload.get("targets", []))
        targets = targets_raw if isinstance(targets_raw, list) else []
        target_count = len(targets)
        scan_mode = str(scope_obj.get("scan_mode", payload.get("scan_mode", ""))).lower()
        partial_scan = bool(scope_obj.get("partial_scan", payload.get("partial_scan", False)))
        confidence = str(gt.get("confidence", "unknown")).lower()
        age_hours = max((datetime.now(UTC) - ts).total_seconds() / 3600.0, 0.0)

        quality = target_count * 100
        quality += 40 if scan_mode == "full" else 10 if scan_mode == "quick" else 0
        quality += 20 if not partial_scan else -10
        quality += (
            15
            if confidence == "high"
            else 8 if confidence == "medium" else 3 if confidence == "low" else 0
        )
        score = float(quality) - (age_hours * 2.0)
        if score > best_score or (score == best_score and (best_ts is None or ts > best_ts)):
            best_score = score
            best_path = report_path
            best_ts = ts

    if best_path:
        return best_path
    try:
        return max(candidates, key=lambda p: p.stat().st_mtime)
    except OSError:
        return latest if latest.exists() else candidates[0]


class ErrorSeverity(Enum):
    """Severity mapping for error categories."""

    CRITICAL = "critical"  # Type errors, import errors, syntax errors
    HIGH = "high"  # Linting issues, security issues
    MEDIUM = "medium"  # Code quality, warnings
    LOW = "low"  # Info, deprecation warnings


@dataclass
class ErrorGroup:
    """Grouped error set."""

    category: str  # "mypy", "ruff", "pylint", etc.
    count: int
    severity: ErrorSeverity
    files_affected: list[str]
    examples: list[str]  # First 3 error messages


@dataclass
class SignalToPost:
    """Signal to post to guild board."""

    signal_type: str = "error"
    severity: str = ""
    message: str = ""
    context: dict[str, Any] | None = None
    timestamp: str = ""
    error_category: str = ""
    error_count: int = 0


def get_error_severity(category: str, error_count: int) -> ErrorSeverity:
    """Map error type + count to severity level."""
    # Map error categories to base severity
    category_severity = {
        "mypy": ErrorSeverity.CRITICAL,  # Type errors are critical
        "import": ErrorSeverity.CRITICAL,
        "syntax": ErrorSeverity.CRITICAL,
        "ruff": ErrorSeverity.HIGH,  # Linting is high priority
        "pylint": ErrorSeverity.MEDIUM,
        "pytest": ErrorSeverity.MEDIUM,
        "coverage": ErrorSeverity.LOW,
    }

    base_severity = category_severity.get(category, ErrorSeverity.MEDIUM)

    # Escalate if error count is high
    if error_count > 100 and base_severity == ErrorSeverity.HIGH:
        base_severity = ErrorSeverity.CRITICAL
    elif error_count > 50 and base_severity == ErrorSeverity.MEDIUM:
        base_severity = ErrorSeverity.HIGH

    return base_severity


def parse_error_report(report_path: Path) -> list[ErrorGroup]:
    """Parse error report JSON and return grouped errors."""
    if not report_path.exists():
        fallback = ROOT / "docs" / "Reports" / "diagnostics" / "unified_error_report_latest.json"
        if fallback.exists():
            report_path = fallback
        else:
            logger.warning(f"Error report not found: {report_path}")
            return []

    try:
        with open(report_path) as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse error report: {e}")
        return []

    groups: dict[str, ErrorGroup] = defaultdict(
        lambda: ErrorGroup(
            category="", count=0, severity=ErrorSeverity.MEDIUM, files_affected=[], examples=[]
        )
    )

    # Format A: ground_truth scanner schema.
    errors_by_type = data.get("errors_by_type", {})
    if isinstance(errors_by_type, dict) and errors_by_type:
        for error_type, error_list in errors_by_type.items():
            if not error_list:
                continue

            category = str(error_type).split("_")[0]  # "mypy_error" -> "mypy"
            severity = get_error_severity(category, len(error_list))
            files = set()
            examples = []

            for error in error_list[:10]:  # First 10 errors as examples
                if isinstance(error, dict):
                    files.add(str(error.get("file", "unknown")))
                    msg = str(error.get("message", ""))
                    if msg and len(examples) < 3:
                        examples.append(msg)
                elif isinstance(error, str):
                    examples.append(error[:100])  # Truncate long messages

            groups[category] = ErrorGroup(
                category=category,
                count=len(error_list),
                severity=severity,
                files_affected=list(files),
                examples=examples,
            )
        return list(groups.values())

    # Format B: unified_error_report_latest schema.
    details = data.get("diagnostic_details", [])
    if isinstance(details, list) and details:
        grouped: dict[str, dict[str, Any]] = defaultdict(
            lambda: {
                "count": 0,
                "files": set(),
                "examples": [],
                "has_error": False,
                "has_warning": False,
            }
        )
        for row in details:
            if not isinstance(row, dict):
                continue
            detail_severity = str(row.get("severity") or "").lower()
            # Bridge actionable diagnostics only; skip info/hint noise.
            if detail_severity not in {"error", "warning"}:
                continue
            category = str(row.get("source") or row.get("error_type") or "unknown").lower()
            bucket = grouped[category]
            bucket["count"] += 1
            file_path = str(row.get("file_path") or row.get("file") or "").strip()
            if file_path:
                bucket["files"].add(file_path)
            message = str(row.get("message") or "").strip()
            if message and len(bucket["examples"]) < 3:
                bucket["examples"].append(message[:120])
            if detail_severity == "error":
                bucket["has_error"] = True
            elif detail_severity == "warning":
                bucket["has_warning"] = True

        for category, bucket in grouped.items():
            base = get_error_severity(category, int(bucket["count"]))
            if bucket["has_error"]:
                severity = base
            elif bucket["has_warning"]:
                severity = ErrorSeverity.MEDIUM
            else:
                severity = ErrorSeverity.LOW
            groups[category] = ErrorGroup(
                category=category,
                count=int(bucket["count"]),
                severity=severity,
                files_affected=sorted(str(path) for path in bucket["files"]),
                examples=list(bucket["examples"]),
            )
        if groups:
            return list(groups.values())

    # Format C fallback: summary-level severities only (details missing/sparse).
    by_repo = data.get("by_repo", {})
    if isinstance(by_repo, dict):
        for repo_name, repo_summary in by_repo.items():
            if not isinstance(repo_summary, dict):
                continue
            by_severity = repo_summary.get("by_severity", {})
            if not isinstance(by_severity, dict):
                continue
            error_count = int(by_severity.get("error", 0) or 0)
            warning_count = int(by_severity.get("warning", 0) or 0)
            total_actionable = error_count + warning_count
            if total_actionable <= 0:
                continue
            category = str(repo_name).lower().replace(" ", "_")
            severity = ErrorSeverity.CRITICAL if error_count > 0 else ErrorSeverity.MEDIUM
            groups[category] = ErrorGroup(
                category=category,
                count=total_actionable,
                severity=severity,
                files_affected=[],
                examples=[
                    f"{error_count} errors, {warning_count} warnings in {repo_name} (summary fallback)"
                ],
            )
        if groups:
            return list(groups.values())

    return []


def errors_to_signals(error_groups: list[ErrorGroup]) -> list[SignalToPost]:
    """Convert error groups to signals for guild board."""
    signals: list[SignalToPost] = []

    for group in error_groups:
        if group.count == 0:
            continue

        # Build message
        message = f"Found {group.count} {group.category} errors"
        if group.files_affected:
            message += f" in {len(group.files_affected)} files"

        # Build context
        context = {
            "error_category": group.category,
            "error_count": group.count,
            "files_affected": group.files_affected,
            "example_errors": group.examples,
            "severity_level": group.severity.value,
        }

        # Create signal
        signal = SignalToPost(
            signal_type="error",
            severity=group.severity.value,
            message=message,
            context=context,
            timestamp=datetime.now().isoformat(),
            error_category=group.category,
            error_count=group.count,
        )

        signals.append(signal)

    return signals


async def post_signals_to_guild_board(
    signals: list[SignalToPost], test_mode: bool = False
) -> dict[str, Any]:
    """Post signals to guild board."""
    try:
        from src.guild.guild_board import GuildBoard
    except ImportError:
        logger.error("Could not import GuildBoard - guild board integration unavailable")
        return {"success": False, "status": "error", "reason": "GuildBoard not available"}

    if test_mode:
        logger.info(f"[TEST MODE] Would post {len(signals)} signals:")
        for signal in signals:
            logger.info(f"  - {signal.message} (severity: {signal.severity})")
        return {"success": True, "status": "test", "signals_posted": len(signals)}

    try:
        board = GuildBoard()
        posted_count = 0

        for signal in signals:
            try:
                await board.add_signal(
                    signal_type=signal.signal_type,
                    severity=signal.severity,
                    message=signal.message,
                    context=signal.context,
                )
                posted_count += 1
                logger.info(f"✅ Posted signal: {signal.message}")
            except Exception as e:
                logger.error(f"Failed to post signal: {e}")

        # Persist board state across GuildBoard API variants.
        if hasattr(board, "save_state"):
            await board.save_state()
        elif hasattr(board, "_save_board"):
            await board._save_board()
        else:
            logger.warning(
                "GuildBoard instance has no save_state/_save_board; relying on add_signal persistence"
            )

        if posted_count == len(signals):
            return {
                "success": True,
                "status": "success",
                "signals_posted": posted_count,
                "signals_total": len(signals),
            }
        if posted_count > 0:
            return {
                "success": False,
                "status": "partial",
                "signals_posted": posted_count,
                "signals_total": len(signals),
            }
        return {
            "success": False,
            "status": "error",
            "signals_posted": posted_count,
            "signals_total": len(signals),
            "reason": "all_signal_posts_failed",
        }
    except Exception as e:
        logger.error(f"Error posting signals: {e}")
        return {
            "success": False,
            "status": "error",
            "reason": str(e),
            "signals_total": len(signals),
        }


async def run_error_scan() -> Path:
    """Run error ground truth scanner."""
    try:
        scanner_script = ROOT / "scripts" / "error_ground_truth_scanner.py"

        if not scanner_script.exists():
            logger.warning(f"Scanner not found: {scanner_script}")
            fallback = _freshest_unified_report()
            return fallback if fallback.exists() else ROOT / "state" / "ground_truth_errors.json"

        logger.info("Running error ground truth scanner...")
        result = subprocess.run(
            [sys.executable, str(scanner_script)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=300,  # 5-minute timeout
        )

        if result.returncode == 0:
            logger.info("✅ Error scan completed")
        else:
            logger.warning(f"Error scan returned code {result.returncode}")
            if result.stderr:
                logger.warning(f"stderr: {result.stderr[:500]}")

        report_path = ROOT / "state" / "ground_truth_errors.json"
        if report_path.exists():
            return report_path
        fallback = _freshest_unified_report()
        return fallback if fallback.exists() else report_path

    except subprocess.TimeoutExpired:
        logger.error("Error scanner timed out after 5 minutes")
        fallback = _freshest_unified_report()
        return fallback if fallback.exists() else ROOT / "state" / "ground_truth_errors.json"
    except Exception as e:
        logger.error(f"Error running scanner: {e}")
        fallback = _freshest_unified_report()
        return fallback if fallback.exists() else ROOT / "state" / "ground_truth_errors.json"


async def bridge_cycle(test_mode: bool = False) -> dict[str, Any]:
    """Run one complete error→signal bridge cycle."""
    logger.info("=" * 80)
    logger.info("ERROR→SIGNAL BRIDGE CYCLE")
    logger.info("=" * 80)

    # 1. Run error scanner
    logger.info("Step 1: Running error scanner...")
    report_path = await run_error_scan()

    return await bridge_from_report(report_path=report_path, test_mode=test_mode)


async def bridge_from_report(report_path: Path, test_mode: bool = False) -> dict[str, Any]:
    """Run error→signal bridge cycle using an existing report artifact."""
    logger.info("Using report artifact: %s", report_path)

    # 2. Parse error report
    logger.info("Step 2: Parsing error report...")
    error_groups = parse_error_report(report_path)
    logger.info(f"Found {len(error_groups)} error groups")
    for group in error_groups:
        logger.info(
            f"  - {group.category}: {group.count} errors (severity: {group.severity.value})"
        )

    # 3. Convert to signals
    logger.info("Step 3: Creating signals...")
    signals = errors_to_signals(error_groups)
    logger.info(f"Created {len(signals)} signals")

    # 4. Post to guild board
    logger.info("Step 4: Posting signals to guild board...")
    result = await post_signals_to_guild_board(signals, test_mode=test_mode)
    logger.info(f"Guild board result: {result}")

    # 5. Return summary
    return {
        "timestamp": datetime.now().isoformat(),
        "report_path": str(report_path),
        "error_groups_found": len(error_groups),
        "signals_created": len(signals),
        "signals_posted": result.get("signals_posted", 0),
        "guild_board_result": result,
    }


async def watch_mode(interval: int = 60) -> None:
    """Run bridge in watch mode - continuously scan for errors."""
    logger.info(f"Starting watch mode (scan every {interval}s)")
    logger.info("Press Ctrl+C to stop")

    try:
        while True:
            cycle_result = await bridge_cycle(test_mode=False)
            signals_posted = cycle_result.get("signals_posted", 0)

            if signals_posted > 0:
                logger.info(f"⚠️  Posted {signals_posted} signals - work available!")
            else:
                logger.info("✅ No new errors detected")

            await asyncio.sleep(interval)

    except KeyboardInterrupt:
        logger.info("Watch mode stopped by user")


async def main() -> int:
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Error→Signal Bridge")
    parser.add_argument(
        "--mode",
        choices=["once", "watch", "test"],
        default="once",
        help="Run mode: once (default), watch (continuous), or test (dry-run)",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=60,
        help="Scan interval for watch mode (seconds)",
    )

    args = parser.parse_args()

    try:
        if args.mode == "test":
            logger.info("Running in TEST MODE - no signals will be posted")
            result = await bridge_cycle(test_mode=True)
            logger.info(json.dumps(result, indent=2))
            return 0

        elif args.mode == "once":
            result = await bridge_cycle(test_mode=False)
            logger.info(json.dumps(result, indent=2))
            return 0

        elif args.mode == "watch":
            await watch_mode(interval=args.interval)
            return 0

    except Exception as e:
        logger.error(f"Fatal error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
