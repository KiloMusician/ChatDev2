#!/usr/bin/env python3
"""
Test Intelligence Terminal - Sophisticated Test Orchestration & Deduplication

A modular, guild-integrated test execution system with:
- Smart deduplication (prevent spam from repeated runs)
- Test result caching with TTL
- Multi-agent coordination via guild board
- Rich terminal output with metasynthesis
- Test classification and intelligent routing
- Performance tracking and optimization suggestions
- Cross-repo test coordination
- Failure pattern detection
"""

from __future__ import annotations

import contextlib
import hashlib
import json
import subprocess
import sys
import time
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

# Add parent to path for imports
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    from src.output.metasynthesis_output_system import (
        MetasynthesisOutputSystem, OutputTier)
except ImportError:
    MetasynthesisOutputSystem = None
    OutputTier = None


# ============================================================================
# Data Models
# ============================================================================


@dataclass
class TestRun:
    """A single test execution record."""

    run_id: str
    timestamp: datetime
    test_pattern: str  # e.g., "tests/", "tests/test_*.py", specific test
    pytest_args: list[str]
    exit_code: int
    duration_seconds: float
    passed: int
    failed: int
    skipped: int
    errors: int
    output: str
    fingerprint: str  # Hash of test pattern + args for dedup
    agent_id: str | None = None
    quest_id: str | None = None
    cache_hit: bool = False


@dataclass
class TestCache:
    """Test result cache with TTL."""

    fingerprint: str
    result: TestRun
    expires_at: datetime
    hit_count: int = 0


@dataclass
class TestTerminalConfig:
    """Configuration for Test Intelligence Terminal."""

    cache_ttl_seconds: int = 300  # 5 minutes default
    max_cache_size: int = 100
    enable_deduplication: bool = True
    enable_guild_integration: bool = True
    enable_metasynthesis_output: bool = True
    spam_threshold: int = 3  # Max identical runs in window
    spam_window_seconds: int = 60  # Time window for spam detection
    output_tier: OutputTier = OutputTier.EVOLVED
    test_timeout_seconds: int = 300  # 5 minutes max per test run
    failure_pattern_threshold: int = 3  # Detect patterns after N failures


# ============================================================================
# Test Intelligence Terminal
# ============================================================================


class TestIntelligenceTerminal:
    """
    Sophisticated test orchestration with deduplication, caching, and guild integration.

    Features:
    - Smart deduplication: Prevents spam from repeated identical test runs
    - Result caching: Reuses recent test results (configurable TTL)
    - Multi-agent coordination: Shares test results via guild board
    - Rich output: Beautiful terminal display with metasynthesis
    - Pattern detection: Identifies recurring failures
    - Performance tracking: Monitors test execution times
    - Cross-repo awareness: Coordinates tests across ecosystem
    """

    def __init__(self, config: TestTerminalConfig | None = None) -> None:
        self.config = config or TestTerminalConfig()
        self.console = Console()

        # State directories
        self.state_dir = PROJECT_ROOT / "state" / "testing"
        self.cache_file = self.state_dir / "test_cache.json"
        self.history_file = self.state_dir / "test_history.jsonl"
        self.dedup_file = self.state_dir / "dedup_tracking.json"

        # Ensure directories exist
        self.state_dir.mkdir(parents=True, exist_ok=True)

        # Runtime state
        self.cache: dict[str, TestCache] = {}
        self.run_history: list[TestRun] = []
        self.dedup_tracker: dict[str, list[datetime]] = defaultdict(list)
        self.failure_patterns: dict[str, int] = defaultdict(int)

        # Load persistent state
        self._load_cache()
        self._load_dedup_tracker()
        self._load_history()

    # ========================================================================
    # Core Test Execution
    # ========================================================================

    def run_tests(
        self,
        test_pattern: str = "tests/",
        pytest_args: list[str] | None = None,
        agent_id: str | None = None,
        quest_id: str | None = None,
        force_run: bool = False,
    ) -> TestRun:
        """
        Execute tests with intelligent deduplication and caching.

        Args:
            test_pattern: Test path or pattern (e.g., "tests/", "tests/test_*.py")
            pytest_args: Additional pytest arguments
            agent_id: Agent requesting the test run
            quest_id: Associated guild quest ID
            force_run: Skip cache and deduplication checks

        Returns:
            TestRun object with results
        """
        pytest_args = pytest_args or []
        run_id = f"test_run_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"

        # Generate fingerprint for deduplication
        fingerprint = self._generate_fingerprint(test_pattern, pytest_args)

        # Check for spam
        if not force_run and self.config.enable_deduplication:
            spam_check = self._check_spam(fingerprint)
            if spam_check["is_spam"]:
                self.console.print(
                    Panel(
                        f"[yellow]⚠️ SPAM DETECTED[/yellow]\n\n"
                        f"This test pattern has been run {spam_check['run_count']} times "
                        f"in the last {self.config.spam_window_seconds}s.\n\n"
                        f"[dim]Fingerprint:[/dim] {fingerprint[:16]}...\n"
                        f"[dim]Last run:[/dim] {spam_check['last_run'].strftime('%H:%M:%S')}\n\n"
                        f"💡 Use force_run=True to override",
                        title="🛡️ Deduplication Guard",
                        border_style="yellow",
                    )
                )
                # Return cached result if available
                if fingerprint in self.cache:
                    cached = self.cache[fingerprint]
                    cached.hit_count += 1
                    self.console.print(
                        f"[green]✅ Returning cached result from {cached.result.timestamp.strftime('%H:%M:%S')}[/green]"
                    )
                    return cached.result

        # Check cache
        if not force_run and fingerprint in self.cache:
            cached = self.cache[fingerprint]
            if datetime.now() < cached.expires_at:
                self.console.print(
                    Panel(
                        f"[cyan]💾 CACHE HIT[/cyan]\n\n"
                        f"Fresh test results available (age: {(datetime.now() - cached.result.timestamp).seconds}s)\n\n"
                        f"[dim]Hit count:[/dim] {cached.hit_count}\n"
                        f"[dim]Expires in:[/dim] {(cached.expires_at - datetime.now()).seconds}s\n\n"
                        f"💡 Use force_run=True to re-run tests",
                        title="🎯 Test Cache",
                        border_style="cyan",
                    )
                )
                cached.hit_count += 1
                cached.result.cache_hit = True
                self._save_cache()
                return cached.result

        # Execute tests
        self.console.print(
            Panel(
                f"[bold cyan]Running Tests[/bold cyan]\n\n"
                f"[dim]Pattern:[/dim] {test_pattern}\n"
                f"[dim]Args:[/dim] {' '.join(pytest_args) if pytest_args else 'none'}\n"
                f"[dim]Agent:[/dim] {agent_id or 'unknown'}\n"
                f"[dim]Quest:[/dim] {quest_id or 'none'}\n"
                f"[dim]Fingerprint:[/dim] {fingerprint[:16]}...",
                title="🧪 Test Execution",
                border_style="blue",
            )
        )

        # Build pytest command
        cmd = [sys.executable, "-m", "pytest", test_pattern]
        cmd.extend(pytest_args)
        cmd.extend(["--tb=short", "-v"])

        # Execute with progress indicator
        start_time = time.monotonic()
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console,
        ) as progress:
            progress.add_task("Running pytest...", total=None)

            try:
                result = subprocess.run(
                    cmd,
                    cwd=str(PROJECT_ROOT),
                    capture_output=True,
                    text=True,
                    timeout=self.config.test_timeout_seconds,
                )
                exit_code = result.returncode
                output = result.stdout + "\n" + result.stderr
            except subprocess.TimeoutExpired as e:
                exit_code = 1
                output = f"TIMEOUT after {self.config.test_timeout_seconds}s\n{e.stdout or ''}\n{e.stderr or ''}"
            except Exception as e:
                exit_code = 1
                output = f"ERROR: {type(e).__name__}: {e}"

        duration = time.monotonic() - start_time

        # Parse pytest output for counts
        stats = self._parse_pytest_output(output)

        # Create test run record
        test_run = TestRun(
            run_id=run_id,
            timestamp=datetime.now(),
            test_pattern=test_pattern,
            pytest_args=pytest_args,
            exit_code=exit_code,
            duration_seconds=duration,
            passed=stats["passed"],
            failed=stats["failed"],
            skipped=stats["skipped"],
            errors=stats["errors"],
            output=output,
            fingerprint=fingerprint,
            agent_id=agent_id,
            quest_id=quest_id,
        )

        # Update cache
        if self.config.enable_deduplication:
            self.cache[fingerprint] = TestCache(
                fingerprint=fingerprint,
                result=test_run,
                expires_at=datetime.now() + timedelta(seconds=self.config.cache_ttl_seconds),
                hit_count=0,
            )
            self._save_cache()

        # Update dedup tracker
        self.dedup_tracker[fingerprint].append(datetime.now())
        self._clean_old_dedup_entries()
        self._save_dedup_tracker()

        # Add to history
        self.run_history.append(test_run)
        self._save_history_entry(test_run)

        # Track failure patterns
        if test_run.failed > 0:
            self.failure_patterns[fingerprint] += 1

        # Display results
        self._display_results(test_run)

        # Guild integration
        if self.config.enable_guild_integration and quest_id:
            self._post_to_guild(test_run)

        return test_run

    # ========================================================================
    # Deduplication & Caching
    # ========================================================================

    def _generate_fingerprint(self, test_pattern: str, pytest_args: list[str]) -> str:
        """Generate unique fingerprint for test run configuration."""
        content = f"{test_pattern}:{':'.join(sorted(pytest_args))}"
        return hashlib.sha256(content.encode()).hexdigest()

    def _check_spam(self, fingerprint: str) -> dict[str, Any]:
        """Check if test run would be considered spam."""
        now = datetime.now()
        window_start = now - timedelta(seconds=self.config.spam_window_seconds)

        # Get recent runs with this fingerprint
        recent_runs = [ts for ts in self.dedup_tracker.get(fingerprint, []) if ts > window_start]

        is_spam = len(recent_runs) >= self.config.spam_threshold

        return {
            "is_spam": is_spam,
            "run_count": len(recent_runs),
            "last_run": recent_runs[-1] if recent_runs else None,
            "threshold": self.config.spam_threshold,
        }

    def _clean_old_dedup_entries(self) -> None:
        """Remove dedup tracker entries outside the window."""
        now = datetime.now()
        window_start = now - timedelta(seconds=self.config.spam_window_seconds)

        for fingerprint in list(self.dedup_tracker.keys()):
            self.dedup_tracker[fingerprint] = [
                ts for ts in self.dedup_tracker[fingerprint] if ts > window_start
            ]
            if not self.dedup_tracker[fingerprint]:
                del self.dedup_tracker[fingerprint]

    # ========================================================================
    # Output Parsing & Display
    # ========================================================================

    def _parse_pytest_output(self, output: str) -> dict[str, int]:
        """Parse pytest output for test counts."""
        stats = {"passed": 0, "failed": 0, "skipped": 0, "errors": 0}

        # Look for pytest summary line
        # Example: "= 10 failed, 465 passed, 3 skipped in 45.67s ="
        for line in output.splitlines():
            if " passed" in line or " failed" in line:
                if " passed" in line:
                    with contextlib.suppress(ValueError, IndexError):
                        stats["passed"] = int(line.split("passed")[0].strip().split()[-1])
                if " failed" in line:
                    with contextlib.suppress(ValueError, IndexError):
                        stats["failed"] = int(line.split("failed")[0].strip().split()[-1])
                if " skipped" in line:
                    with contextlib.suppress(ValueError, IndexError):
                        stats["skipped"] = int(line.split("skipped")[0].strip().split()[-1])
                if " error" in line.lower():
                    with contextlib.suppress(ValueError, IndexError):
                        stats["errors"] = int(line.split("error")[0].strip().split()[-1])

        return stats

    def _display_results(self, test_run: TestRun) -> None:
        """Display test results with rich formatting."""
        # Summary table
        table = Table(title="Test Results Summary", show_header=True)
        table.add_column("Metric", style="cyan")
        table.add_column("Value", justify="right")

        table.add_row("Run ID", test_run.run_id)
        table.add_row("Pattern", test_run.test_pattern)
        table.add_row("Duration", f"{test_run.duration_seconds:.2f}s")
        table.add_row("✅ Passed", str(test_run.passed), style="green")
        table.add_row("❌ Failed", str(test_run.failed), style="red" if test_run.failed > 0 else "")
        table.add_row("⏭️ Skipped", str(test_run.skipped), style="yellow")
        table.add_row("⚠️ Errors", str(test_run.errors), style="red" if test_run.errors > 0 else "")
        table.add_row("Exit Code", str(test_run.exit_code))

        if test_run.cache_hit:
            table.add_row("Source", "💾 Cache", style="cyan")

        self.console.print("\n", table)

        # Outcome banner
        if test_run.exit_code == 0:
            self.console.print(
                Panel(
                    f"[bold green]✅ ALL TESTS PASSED[/bold green]\n\n"
                    f"{test_run.passed} tests passed in {test_run.duration_seconds:.2f}s",
                    border_style="green",
                )
            )
        else:
            self.console.print(
                Panel(
                    f"[bold red]❌ TESTS FAILED[/bold red]\n\n"
                    f"{test_run.failed} failed, {test_run.passed} passed\n\n"
                    f"💡 Check output above for details",
                    border_style="red",
                )
            )

        # Failure pattern detection
        if test_run.fingerprint in self.failure_patterns:
            pattern_count = self.failure_patterns[test_run.fingerprint]
            if pattern_count >= self.config.failure_pattern_threshold:
                self.console.print(
                    Panel(
                        f"[yellow]⚠️ PATTERN DETECTED[/yellow]\n\n"
                        f"This test configuration has failed {pattern_count} times.\n\n"
                        f"💡 Consider creating a guild quest to investigate",
                        border_style="yellow",
                    )
                )

    # ========================================================================
    # Guild Board Integration
    # ========================================================================

    def _post_to_guild(self, test_run: TestRun) -> None:
        """Post test results to guild board."""
        try:
            # Import guild board
            from src.guild.guild_board import GuildBoard

            board = GuildBoard()

            # Create message
            status_emoji = "✅" if test_run.exit_code == 0 else "❌"
            message = (
                f"{status_emoji} Test run completed\n"
                f"Pattern: {test_run.test_pattern}\n"
                f"Passed: {test_run.passed}, Failed: {test_run.failed}\n"
                f"Duration: {test_run.duration_seconds:.2f}s"
            )

            # Post to board
            board.post(
                agent_id=test_run.agent_id or "test_terminal",
                quest_id=test_run.quest_id or "",
                message=message,
                post_type="test_result",
                artifacts=[str(self.history_file)],
            )

            self.console.print("[dim]📋 Posted to guild board[/dim]")

        except Exception as e:
            self.console.print(f"[dim yellow]⚠️ Guild post failed: {e}[/dim yellow]")

    # ========================================================================
    # Analytics & Insights
    # ========================================================================

    def get_statistics(self) -> dict[str, Any]:
        """Get test execution statistics."""
        total_runs = len(self.run_history)
        if total_runs == 0:
            return {"total_runs": 0, "message": "No test runs recorded"}

        passed_runs = sum(1 for r in self.run_history if r.exit_code == 0)
        cache_hits = sum(c.hit_count for c in self.cache.values())
        avg_duration = sum(r.duration_seconds for r in self.run_history) / total_runs

        return {
            "total_runs": total_runs,
            "passed_runs": passed_runs,
            "failed_runs": total_runs - passed_runs,
            "success_rate": passed_runs / total_runs,
            "cache_hits": cache_hits,
            "cache_size": len(self.cache),
            "avg_duration_seconds": avg_duration,
            "failure_patterns": len(self.failure_patterns),
            "active_dedup_fingerprints": len(self.dedup_tracker),
        }

    def print_statistics(self) -> None:
        """Display test statistics."""
        stats = self.get_statistics()

        if stats.get("total_runs", 0) == 0:
            self.console.print("[yellow]No test runs recorded yet[/yellow]")
            return

        table = Table(title="Test Intelligence Statistics", show_header=True)
        table.add_column("Metric", style="cyan")
        table.add_column("Value", justify="right")

        table.add_row("Total Runs", str(stats["total_runs"]))
        table.add_row("Passed Runs", str(stats["passed_runs"]), style="green")
        table.add_row(
            "Failed Runs",
            str(stats["failed_runs"]),
            style="red" if stats["failed_runs"] > 0 else "",
        )
        table.add_row("Success Rate", f"{stats['success_rate']:.1%}")
        table.add_row("Cache Hits", str(stats["cache_hits"]), style="cyan")
        table.add_row("Cache Size", str(stats["cache_size"]))
        table.add_row("Avg Duration", f"{stats['avg_duration_seconds']:.2f}s")
        table.add_row(
            "Failure Patterns",
            str(stats["failure_patterns"]),
            style="yellow" if stats["failure_patterns"] > 0 else "",
        )

        self.console.print("\n", table)

    # ========================================================================
    # Persistence
    # ========================================================================

    def _load_cache(self) -> None:
        """Load test cache from disk."""
        if not self.cache_file.exists():
            return

        try:
            with open(self.cache_file) as f:
                data = json.load(f)

            for fp, cache_data in data.items():
                # Reconstruct TestRun
                run_data = cache_data["result"]
                run_data["timestamp"] = datetime.fromisoformat(run_data["timestamp"])

                test_run = TestRun(**run_data)

                # Reconstruct TestCache
                self.cache[fp] = TestCache(
                    fingerprint=fp,
                    result=test_run,
                    expires_at=datetime.fromisoformat(cache_data["expires_at"]),
                    hit_count=cache_data["hit_count"],
                )

            # Clean expired entries
            now = datetime.now()
            self.cache = {fp: cache for fp, cache in self.cache.items() if cache.expires_at > now}

        except Exception as e:
            self.console.print(f"[dim yellow]⚠️ Cache load failed: {e}[/dim yellow]")

    def _save_cache(self) -> None:
        """Save test cache to disk."""
        try:
            data = {}
            for fp, cache in self.cache.items():
                run_dict = {
                    "run_id": cache.result.run_id,
                    "timestamp": cache.result.timestamp.isoformat(),
                    "test_pattern": cache.result.test_pattern,
                    "pytest_args": cache.result.pytest_args,
                    "exit_code": cache.result.exit_code,
                    "duration_seconds": cache.result.duration_seconds,
                    "passed": cache.result.passed,
                    "failed": cache.result.failed,
                    "skipped": cache.result.skipped,
                    "errors": cache.result.errors,
                    "output": cache.result.output[:1000],  # Truncate for storage
                    "fingerprint": cache.result.fingerprint,
                    "agent_id": cache.result.agent_id,
                    "quest_id": cache.result.quest_id,
                    "cache_hit": cache.result.cache_hit,
                }

                data[fp] = {
                    "result": run_dict,
                    "expires_at": cache.expires_at.isoformat(),
                    "hit_count": cache.hit_count,
                }

            with open(self.cache_file, "w") as f:
                json.dump(data, f, indent=2)

        except Exception as e:
            self.console.print(f"[dim yellow]⚠️ Cache save failed: {e}[/dim yellow]")

    def _load_dedup_tracker(self) -> None:
        """Load deduplication tracker from disk."""
        if not self.dedup_file.exists():
            return

        try:
            with open(self.dedup_file) as f:
                data = json.load(f)

            for fp, timestamps in data.items():
                self.dedup_tracker[fp] = [datetime.fromisoformat(ts) for ts in timestamps]

            self._clean_old_dedup_entries()

        except Exception as e:
            self.console.print(f"[dim yellow]⚠️ Dedup load failed: {e}[/dim yellow]")

    def _save_dedup_tracker(self) -> None:
        """Save deduplication tracker to disk."""
        try:
            data = {
                fp: [ts.isoformat() for ts in timestamps]
                for fp, timestamps in self.dedup_tracker.items()
            }

            with open(self.dedup_file, "w") as f:
                json.dump(data, f, indent=2)

        except Exception as e:
            self.console.print(f"[dim yellow]⚠️ Dedup save failed: {e}[/dim yellow]")

    def _load_history(self) -> None:
        """Load test history from JSONL file."""
        if not self.history_file.exists():
            return

        try:
            with open(self.history_file) as f:
                for line in f:
                    if not line.strip():
                        continue

                    data = json.loads(line)
                    data["timestamp"] = datetime.fromisoformat(data["timestamp"])
                    self.run_history.append(TestRun(**data))

            # Keep only last 100 entries in memory
            self.run_history = self.run_history[-100:]

        except Exception as e:
            self.console.print(f"[dim yellow]⚠️ History load failed: {e}[/dim yellow]")

    def _save_history_entry(self, test_run: TestRun) -> None:
        """Append test run to history file (JSONL format)."""
        try:
            entry = {
                "run_id": test_run.run_id,
                "timestamp": test_run.timestamp.isoformat(),
                "test_pattern": test_run.test_pattern,
                "pytest_args": test_run.pytest_args,
                "exit_code": test_run.exit_code,
                "duration_seconds": test_run.duration_seconds,
                "passed": test_run.passed,
                "failed": test_run.failed,
                "skipped": test_run.skipped,
                "errors": test_run.errors,
                "output": test_run.output[:500],  # Truncate for storage
                "fingerprint": test_run.fingerprint,
                "agent_id": test_run.agent_id,
                "quest_id": test_run.quest_id,
                "cache_hit": test_run.cache_hit,
            }

            with open(self.history_file, "a") as f:
                f.write(json.dumps(entry) + "\n")

        except Exception as e:
            self.console.print(f"[dim yellow]⚠️ History save failed: {e}[/dim yellow]")


# ============================================================================
# CLI Interface
# ============================================================================


def main():
    """CLI interface for Test Intelligence Terminal."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Test Intelligence Terminal - Smart Test Orchestration"
    )
    parser.add_argument(
        "test_pattern",
        nargs="?",
        default="tests/",
        help="Test path or pattern (default: tests/)",
    )
    parser.add_argument("--agent", help="Agent ID running the tests", default="test_terminal")
    parser.add_argument("--quest", help="Associated guild quest ID")
    parser.add_argument("--force", action="store_true", help="Force run, skip cache and dedup")
    parser.add_argument("--stats", action="store_true", help="Show statistics")
    parser.add_argument("--cache-ttl", type=int, default=300, help="Cache TTL in seconds")
    parser.add_argument("--no-dedup", action="store_true", help="Disable deduplication")
    parser.add_argument("--no-guild", action="store_true", help="Disable guild integration")

    # Additional pytest args
    parser.add_argument("pytest_args", nargs="*", help="Additional pytest arguments")

    args = parser.parse_args()

    # Create config
    config = TestTerminalConfig(
        cache_ttl_seconds=args.cache_ttl,
        enable_deduplication=not args.no_dedup,
        enable_guild_integration=not args.no_guild,
    )

    # Create terminal
    terminal = TestIntelligenceTerminal(config)

    # Show stats if requested
    if args.stats:
        terminal.print_statistics()
        return 0

    # Run tests
    test_run = terminal.run_tests(
        test_pattern=args.test_pattern,
        pytest_args=args.pytest_args,
        agent_id=args.agent,
        quest_id=args.quest,
        force_run=args.force,
    )

    return test_run.exit_code


if __name__ == "__main__":
    sys.exit(main())
