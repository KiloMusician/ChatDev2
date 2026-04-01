#!/usr/bin/env python3
"""Autonomous Monitoring Loop
Continuously monitors system state and takes action without asking permission.
This is the meta-agent that demonstrates autonomous operation.

This script orchestrates existing NuSyQ-Hub pipelines instead of duplicating
logic. Placeholder steps remain, but they now invoke real systems and produce
traceable artifacts.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.automation.unified_pu_queue import PU, UnifiedPUQueue
from src.tools.cultivation_metrics import CultivationMetrics
from src.tools.quest_replay_engine import QuestReplayEngine
from src.utils.safe_subprocess import SafeSubprocessExecutor

try:
    from src.automation.autonomous_monitor import AutonomousMonitor as CanonicalMonitor
except Exception:  # pragma: no cover - optional dependency for this wrapper
    CanonicalMonitor = None

logger = logging.getLogger(__name__)


@dataclass
class MonitorConfig:
    """Configuration for autonomous monitoring wrapper."""

    interval: int = 300
    max_pus: int = 2
    sleep_s: int = 1
    auto_cycle_timeout_s: int = 240
    auto_cycle_mode: str = "on-pending"
    run_vantage_sweep: bool = True
    vantage_timeout_s: int = 180
    greenfield_generate_every: int = 0
    real_pus: bool = False
    run_gap_audit: bool = True
    save_gap_report: bool = False
    run_quest_replay: bool = True
    run_metrics: bool = True
    run_zen_expand: bool = False
    trace: bool = True
    trace_dir: Path = Path("state/reports")
    strict_subprocess: bool = False


class AutonomousMonitor:
    """Meta-agent that monitors and acts autonomously."""

    def __init__(self, config: MonitorConfig) -> None:
        self.config = config
        self.root = Path(__file__).resolve().parents[1]
        self.pu_queue = UnifiedPUQueue()
        self.replay_engine = QuestReplayEngine(repo_root=self.root)
        self.metrics = CultivationMetrics(repo_root=self.root)
        self.executor = SafeSubprocessExecutor(auto_fix=True, strict_mode=self.config.strict_subprocess)
        self.monitoring = True
        self.cycle_index = 0
        self.trace_entries: list[dict[str, Any]] = []

    def _tail(self, text: str | None, limit: int = 20) -> list[str]:
        if not text:
            return []
        return text.splitlines()[-limit:]

    def _record_trace(self, step: str, payload: dict[str, Any]) -> None:
        if not self.config.trace:
            return
        self.trace_entries.append(
            {
                "step": step,
                "timestamp": datetime.now(UTC).isoformat(),
                "payload": payload,
            }
        )

    def _write_trace(self) -> Path | None:
        if not self.config.trace:
            return None
        self.config.trace_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        trace_path = self.config.trace_dir / f"autonomous_monitor_trace_{stamp}.json"
        trace_path.write_text(
            json.dumps(
                {
                    "generated_at": datetime.now(UTC).isoformat(),
                    "steps": self.trace_entries,
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        try:
            keep_count = max(1, int(os.getenv("NUSYQ_AUTONOMOUS_TRACE_HISTORY_KEEP", "20") or 20))
        except ValueError:
            keep_count = 20
        traces = sorted(
            self.config.trace_dir.glob("autonomous_monitor_trace_*.json"),
            key=lambda p: p.stat().st_mtime if p.exists() else 0.0,
            reverse=True,
        )
        for stale in traces[keep_count:]:
            try:
                stale.unlink()
            except OSError:
                continue
        return trace_path

    def _run_command(self, label: str, command: list[str], timeout: int = 900) -> dict[str, Any]:
        result = self.executor.run(
            command,
            cwd=self.root,
            timeout=timeout,
            capture_output=True,
            text=True,
        )
        payload = {
            "label": label,
            "command": command,
            "return_code": result.returncode,
            "stdout_tail": self._tail(result.stdout),
            "stderr_tail": self._tail(result.stderr),
        }
        self._record_trace(label, payload)
        return payload

    def _seed_queue_from_gaps(self, max_seed: int) -> int:
        """Seed actionable PUs from canonical sector-gap analysis when queue is idle."""
        if not CanonicalMonitor or max_seed <= 0:
            return 0

        try:
            monitor = CanonicalMonitor(audit_interval=self.config.interval)
            gaps = monitor.get_sector_gaps()
        except Exception as exc:  # pragma: no cover - defensive wrapper
            self._record_trace("seed_gaps", {"status": "failed", "error": str(exc)})
            return 0

        # Dedupe against the full queue (including completed history) to avoid
        # repeatedly re-seeding identical gap tasks and inflating queue bloat.
        existing_titles = {pu.title for pu in self.pu_queue.queue}
        created = 0

        for gap in gaps:
            if created >= max_seed:
                break

            sector = gap.get("sector", "unknown")
            component = gap.get("component") or gap.get("type", "gap")
            title = f"Close sector gap: {sector} / {component}"
            if title in existing_titles:
                continue

            severity = str(gap.get("severity", "medium")).lower()
            priority = "high" if severity in {"critical", "high"} else "medium"
            pu_type = "BugFixPU" if severity in {"critical", "high"} else "RefactorPU"

            pu = PU(
                id="",
                type=pu_type,
                title=title,
                description=gap.get("description", "Autonomous gap remediation task"),
                source_repo="nusyq-hub",
                priority=priority,
                proof_criteria=["diagnose", "resolve", "verify"],
                metadata={"gap": gap, "seeded_by": "autonomous_monitor"},
                status="queued",
            )
            pu_id = self.pu_queue.submit_pu(pu)
            self.pu_queue.request_council_vote(pu_id)
            self.pu_queue.assign_agents(pu_id)
            existing_titles.add(title)
            created += 1

        self._record_trace("seed_gaps", {"status": "ok", "created": created})
        return created

    async def check_pu_queue(self) -> dict[str, Any]:
        """Check PU queue and auto-process if needed."""
        actionable_statuses = {"queued", "approved", "delegated"}
        pending_pus = [pu for pu in self.pu_queue.queue if pu.status in actionable_statuses]

        payload = {
            "pending": len(pending_pus),
            "total": len(self.pu_queue.queue),
            "auto_cycle_ran": False,
        }

        if self.config.auto_cycle_mode == "always":
            payload["auto_cycle_ran"] = True
            payload["auto_cycle"] = self._run_auto_cycle()
            # Placeholder enhanced: auto-cycle now does real PU processing.
            return payload

        if not pending_pus and self.config.auto_cycle_mode == "on-pending":
            seeded = self._seed_queue_from_gaps(max_seed=max(1, self.config.max_pus))
            payload["seeded_from_gaps"] = seeded
            # Reload queue after seeding because submit_pu mutates persisted state.
            self.pu_queue.queue = self.pu_queue._load_queue()
            pending_pus = [pu for pu in self.pu_queue.queue if pu.status in actionable_statuses]
            payload["pending"] = len(pending_pus)
            payload["total"] = len(self.pu_queue.queue)

        if pending_pus and self.config.auto_cycle_mode == "on-pending":
            payload["auto_cycle_ran"] = True
            payload["auto_cycle"] = self._run_auto_cycle()
            # Placeholder enhanced: queued PUs flow through auto-cycle now.
            return payload

        self._record_trace("pu_queue_check", payload)
        return payload

    async def analyze_quest_patterns(self, skip: bool) -> dict[str, Any]:
        """Analyze quest log for learning opportunities."""
        if skip or not self.config.run_quest_replay:
            payload = {"status": "skipped"}
            self._record_trace("quest_replay", payload)
            return payload

        # Placeholder enhanced: pattern extraction now runs QuestReplayEngine.
        replay_report = await self.replay_engine.replay_recent_quests(limit=5)
        work_queue_report = await self.replay_engine.analyze_work_queue_history()
        payload = {
            "replay": replay_report,
            "work_queue": work_queue_report,
        }
        self._record_trace("quest_replay", payload)
        return payload

    async def monitor_metrics(self, skip: bool) -> dict[str, Any]:
        """Monitor cultivation metrics for anomalies."""
        if skip or not self.config.run_metrics:
            payload = {"status": "skipped"}
            self._record_trace("metrics", payload)
            return payload

        # Placeholder enhanced: rebuild dashboard to capture current metrics.
        dashboard_path = await self.metrics.build_dashboard()
        payload = {"status": "rebuilt", "dashboard": str(dashboard_path)}
        self._record_trace("metrics", payload)
        return payload

    def auto_expand_zen_codex(self) -> dict[str, Any]:
        """Scan for new error patterns and auto-add to Zen Codex."""
        if not self.config.run_zen_expand:
            payload = {"status": "skipped"}
            self._record_trace("zen_expand", payload)
            return payload

        # Placeholder enhanced: invoke expansion script for consistent learning.
        result = self._run_command(
            "zen_expand",
            ["python", "scripts/expand_zen_codex_from_errors.py"],
            timeout=600,
        )
        return result

    def run_gap_audit(self) -> dict[str, Any]:
        """Run sector-aware gap audit using canonical Autonomous Monitor."""
        if not self.config.run_gap_audit:
            payload = {"status": "skipped"}
            self._record_trace("gap_audit", payload)
            return payload

        if not CanonicalMonitor:
            payload = {"status": "unavailable", "reason": "canonical_monitor_missing"}
            self._record_trace("gap_audit", payload)
            return payload

        monitor = CanonicalMonitor(audit_interval=self.config.interval)
        report = monitor.get_sector_health_report()
        payload = {
            "status": "ok",
            "sectors": report.get("total_sectors", 0),
            "gaps": report.get("total_gaps", 0),
        }
        if self.config.save_gap_report:
            report_path = monitor.save_gap_report()
            payload["report_path"] = str(report_path)
        self._record_trace("gap_audit", payload)
        return payload

    def _run_auto_cycle(self) -> dict[str, Any]:
        cmd = [
            "python",
            "scripts/start_nusyq.py",
            "auto_cycle",
            "--iterations=1",
            f"--max-pus={self.config.max_pus}",
            f"--sleep={self.config.sleep_s}",
        ]
        if self.config.real_pus:
            cmd.append("--real-pus")
        return self._run_command("auto_cycle", cmd, timeout=self.config.auto_cycle_timeout_s)

    def _latest_generated_project(self) -> Path | None:
        generated_root = self.root / "projects" / "generated"
        if not generated_root.exists():
            return None
        candidates = [p for p in generated_root.iterdir() if p.is_dir()]
        if not candidates:
            return None
        return max(candidates, key=lambda p: p.stat().st_mtime)

    def _run_three_vantage_sweep(self) -> dict[str, Any]:
        """Run top-to-bottom sweep across three development vantages."""
        if not self.config.run_vantage_sweep:
            payload = {"status": "skipped"}
            self._record_trace("vantage_sweep", payload)
            return payload

        timeout = self.config.vantage_timeout_s
        report: dict[str, Any] = {"status": "ok", "steps": {}}

        # Vantage 1: System self-improvement / integrity hardening.
        report["steps"]["system"] = self._run_command(
            "vantage_system_doctor",
            [
                "python",
                "nq",
                "factory",
                "doctor",
                "--strict-hooks",
                "--workspace-integrity",
                "--json",
            ],
            timeout=timeout,
        )

        # Vantage 2: Evolve existing generated/testing-chamber project.
        existing_project = self._latest_generated_project()
        if existing_project:
            report["steps"]["existing_project"] = self._run_command(
                "vantage_existing_project_fix_dry_run",
                ["python", "nq", "fix", str(existing_project), "--dry-run"],
                timeout=timeout,
            )
        else:
            report["steps"]["existing_project"] = {
                "label": "vantage_existing_project_fix_dry_run",
                "status": "skipped",
                "reason": "no generated projects found",
            }

        # Vantage 3: Greenfield/new-project factory readiness (and optional smoke generation).
        report["steps"]["greenfield_health"] = self._run_command(
            "vantage_greenfield_health",
            ["python", "nq", "factory", "health", "--json"],
            timeout=timeout,
        )

        if (
            self.config.greenfield_generate_every > 0
            and self.cycle_index > 0
            and self.cycle_index % self.config.greenfield_generate_every == 0
        ):
            stamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
            smoke_name = f"VantageSmoke_{stamp}"
            report["steps"]["greenfield_generate"] = self._run_command(
                "vantage_greenfield_generate",
                [
                    "python",
                    "nq",
                    "factory",
                    "generate",
                    smoke_name,
                    "--template=default_cli",
                    "--provider=ollama",
                ],
                timeout=max(timeout, 300),
            )

        self._record_trace("vantage_sweep", report)
        return report

    async def run_cycle(self) -> dict[str, Any]:
        """Run one monitoring cycle."""
        # Keep each trace artifact scoped to one monitor cycle.
        self.trace_entries = []
        self.cycle_index += 1
        cycle_ts = datetime.now(UTC).isoformat()
        print("\n" + "=" * 60, flush=True)
        print(f"Autonomous Monitor Cycle - {cycle_ts}", flush=True)
        print("=" * 60 + "\n", flush=True)
        logger.info("Starting monitor cycle %s at %s", self.cycle_index, cycle_ts)

        pu_result = await self.check_pu_queue()
        auto_cycle_ran = bool(pu_result.get("auto_cycle_ran"))

        gap_result = self.run_gap_audit()
        quest_result = await self.analyze_quest_patterns(skip=auto_cycle_ran)
        metrics_result = await self.monitor_metrics(skip=auto_cycle_ran)
        zen_result = self.auto_expand_zen_codex()
        vantage_result = self._run_three_vantage_sweep()

        trace_path = self._write_trace()

        summary = {
            "pu_queue": pu_result,
            "gap_audit": gap_result,
            "quest_replay": quest_result,
            "metrics": metrics_result,
            "zen_expand": zen_result,
            "vantage_sweep": vantage_result,
            "trace_path": str(trace_path) if trace_path else None,
        }
        logger.info(
            "Cycle %s complete | pending=%s total=%s auto_cycle=%s trace=%s",
            self.cycle_index,
            pu_result.get("pending"),
            pu_result.get("total"),
            pu_result.get("auto_cycle_ran"),
            summary["trace_path"],
        )
        return summary

    async def run_continuous(self) -> None:
        """Run continuously with specified interval (seconds)."""
        print("Autonomous Monitor starting...", flush=True)
        print(f"Monitoring interval: {self.config.interval}s", flush=True)
        print(f"Auto-cycle mode: {self.config.auto_cycle_mode}", flush=True)
        print("", flush=True)

        while self.monitoring:
            try:
                await self.run_cycle()
                print(f"Sleeping for {self.config.interval}s...\n", flush=True)
                await asyncio.sleep(self.config.interval)
            except KeyboardInterrupt:
                print("\nInterrupted - shutting down gracefully...", flush=True)
                self.monitoring = False
            except Exception as exc:
                print(f"Error in monitoring cycle: {exc}", flush=True)
                logger.exception("Monitor cycle failed: %s", exc)
                await asyncio.sleep(self.config.interval)


def _parse_args() -> MonitorConfig:
    parser = argparse.ArgumentParser(description="Autonomous monitor orchestrator")
    parser.add_argument("mode", nargs="?", choices=["once", "continuous"], default="once")
    parser.add_argument("--interval", type=int, default=300, help="Seconds between cycles")
    parser.add_argument("--max-pus", type=int, default=2, help="Max PUs per auto_cycle")
    parser.add_argument("--sleep", type=int, default=1, help="Sleep seconds inside auto_cycle")
    parser.add_argument(
        "--auto-cycle-timeout",
        type=int,
        default=240,
        help="Timeout (seconds) for each auto_cycle subprocess run (default: 240)",
    )
    parser.add_argument("--real-pus", action="store_true", help="Use real PU execution")
    parser.add_argument(
        "--auto-cycle",
        choices=["on-pending", "always", "off"],
        default="on-pending",
        help="When to invoke auto_cycle",
    )
    parser.add_argument(
        "--gap-audit",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Run sector-aware gap audit",
    )
    parser.add_argument(
        "--save-gap-report",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Persist gap audit report to data/",
    )
    parser.add_argument(
        "--quest-replay",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Run quest replay engine",
    )
    parser.add_argument(
        "--metrics",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Rebuild cultivation metrics dashboard",
    )
    parser.add_argument(
        "--zen-expand",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Run Zen Codex expansion script",
    )
    parser.add_argument(
        "--trace",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Write trace artifact to state/reports",
    )
    parser.add_argument(
        "--trace-dir",
        default="state/reports",
        help="Directory for trace artifacts",
    )
    parser.add_argument(
        "--strict-subprocess",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Fail when Zen validation blocks commands",
    )
    parser.add_argument(
        "--vantage-sweep",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Run three-vantage sweep (system/existing-project/greenfield) each cycle",
    )
    parser.add_argument(
        "--vantage-timeout",
        type=int,
        default=180,
        help="Timeout (seconds) for each vantage sweep command (default: 180)",
    )
    parser.add_argument(
        "--greenfield-generate-every",
        type=int,
        default=0,
        help="If >0, run greenfield smoke generation every N cycles (default: disabled)",
    )

    args = parser.parse_args()
    return MonitorConfig(
        interval=args.interval,
        max_pus=args.max_pus,
        sleep_s=args.sleep,
        auto_cycle_timeout_s=args.auto_cycle_timeout,
        auto_cycle_mode=args.auto_cycle,
        run_vantage_sweep=args.vantage_sweep,
        vantage_timeout_s=args.vantage_timeout,
        greenfield_generate_every=max(0, args.greenfield_generate_every),
        real_pus=args.real_pus,
        run_gap_audit=args.gap_audit,
        save_gap_report=args.save_gap_report,
        run_quest_replay=args.quest_replay,
        run_metrics=args.metrics,
        run_zen_expand=args.zen_expand,
        trace=args.trace,
        trace_dir=Path(args.trace_dir),
        strict_subprocess=args.strict_subprocess,
    )


async def main() -> None:
    """Entry point for autonomous monitor."""
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    config = _parse_args()
    monitor = AutonomousMonitor(config)

    if config.interval < 1:
        raise SystemExit("interval must be >= 1 second")

    if config.trace and not config.trace_dir.is_dir():
        config.trace_dir.mkdir(parents=True, exist_ok=True)

    if config.trace:
        print(f"Trace artifacts: {config.trace_dir}")

    if "continuous" in sys.argv:
        await monitor.run_continuous()
    else:
        await monitor.run_cycle()


if __name__ == "__main__":
    asyncio.run(main())
