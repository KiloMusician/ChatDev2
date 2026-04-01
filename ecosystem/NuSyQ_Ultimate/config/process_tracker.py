"""
ΞNuSyQ Process/Task Tracker - INTELLIGENT Monitoring (Not Arbitrary Timeouts)

Philosophy:
    "Don't kill processes just because they're slow.
     Track behavior, investigate anomalies, let humans decide."

Why This Exists:
    User insight: "Timeout should be intelligent, not just arbitrary based on
    how long something is taking. If something takes longer than expected,
    INVESTIGATE to see if working as intended (downloading deepseek vs stuck)."

What This Replaces:
    ❌ Arbitrary timeouts that kill slow but legitimate operations
    ✅ Behavioral monitoring that tracks WHAT process is doing, not just HOW LONG

Use Cases:
    - Downloading large models (30+ minutes) - KEEP RUNNING, show progress
    - Ollama hung on malformed prompt - ALERT, offer to kill
    - ChatDev generating huge project - KEEP RUNNING, show estimate
    - Network request stuck - INVESTIGATE, check connectivity

Author: AI Code Agent (responding to user's critical insight)
Date: 2025-10-07
"""

import psutil
import subprocess
import time
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, Callable
from dataclasses import dataclass, asdict
from enum import Enum


class ProcessState(Enum):
    """Process behavioral states (not just 'running' vs 'stopped')"""

    STARTING = "starting"  # Just launched
    DOWNLOADING = "downloading"  # Network activity, growing files
    PROCESSING = "processing"  # High CPU, active work
    WAITING = "waiting"  # Low CPU, I/O bound
    STUCK = "stuck"  # No activity at all
    COMPLETING = "completing"  # Finishing up
    FINISHED = "finished"  # Completed successfully
    FAILED = "failed"  # Error/crash
    INVESTIGATING = "investigating"  # Anomaly detected, needs human review


@dataclass
class ProcessSnapshot:
    """Behavioral snapshot of a process at a point in time"""

    timestamp: datetime
    pid: int
    cpu_percent: float
    memory_mb: float
    network_bytes_sent: int
    network_bytes_recv: int
    io_read_bytes: int
    io_write_bytes: int
    state: ProcessState
    notes: str


@dataclass
class ProcessContext:
    """Context about what process should be doing"""

    name: str
    command: str
    purpose: str  # e.g., "Downloading deepseek-coder-33b"
    expected_duration_sec: Optional[int]  # Rough estimate, not hard limit
    expected_behavior: str  # e.g., "high network, growing file"
    investigation_triggers: Dict[str, Any]  # When to investigate


class ProcessTracker:
    """
    Monitor processes WITHOUT killing them arbitrarily.
    Track behavior, investigate anomalies, provide visibility.
    """

    def __init__(self):
        self.tracked_processes: Dict[int, list] = {}  # pid -> [snapshots]
        self.logs_dir = Path("Logs/process_tracker")
        self.logs_dir.mkdir(parents=True, exist_ok=True)

        # Investigation thresholds (triggers, not limits)
        self.investigation_config = {
            "stuck_duration_sec": 300,  # 5min no activity = investigate
            "duration_multiplier": 3.0,  # 3x expected = investigate
            "memory_threshold_mb": 8192,  # 8GB RAM = investigate
            "cpu_idle_threshold": 1.0,  # <1% CPU for 5min = maybe stuck
        }

    def track(
        self,
        process: subprocess.Popen,
        context: ProcessContext,
        monitor_interval_sec: float = 2.0,
        callback: Optional[Callable] = None,
    ) -> Dict[str, Any]:
        """
        Monitor a process WITHOUT killing it.

        Args:
            process: subprocess.Popen instance to track
            context: What the process should be doing
            monitor_interval_sec: How often to check behavior
            callback: Optional function to call with updates

        Returns:
            Final status dict with full execution history
        """
        pid = process.pid
        self.tracked_processes[pid] = []

        start_time = time.time()

        print(f"\n🔍 Tracking Process: {context.name}")
        print(f"   PID: {pid}")
        print(f"   Purpose: {context.purpose}")
        print(f"   Expected: {context.expected_behavior}")
        if context.expected_duration_sec:
            print(
                f"   Estimated Duration: {context.expected_duration_sec}s (~{context.expected_duration_sec / 60:.1f}min)"
            )
        print("   ⚠️  NOTE: Will NOT kill process, only investigate anomalies\n")

        try:
            psutil_process = psutil.Process(pid)

            while process.poll() is None:  # While process is running
                time.sleep(monitor_interval_sec)

                # Capture behavioral snapshot
                snapshot = self._capture_snapshot(psutil_process)
                self.tracked_processes[pid].append(snapshot)

                # Analyze behavior (don't kill, just investigate)
                investigation = self._should_investigate(
                    snapshots=self.tracked_processes[pid],
                    context=context,
                    start_time=start_time,
                )

                if investigation:
                    print(f"\n⚠️  INVESTIGATION TRIGGERED: {investigation['reason']}")
                    print(f"   Current State: {snapshot.state.value}")
                    print(f"   Duration: {time.time() - start_time:.1f}s")
                    print(f"   CPU: {snapshot.cpu_percent:.1f}%")
                    print(f"   Memory: {snapshot.memory_mb:.1f}MB")
                    print(f"   Suggestion: {investigation['suggestion']}")
                    print("   Action: CONTINUING (not killing)\n")

                    # Call user callback if provided
                    if callback:
                        callback(snapshot, investigation)

                    # Mark as investigating but KEEP RUNNING
                    snapshot.state = ProcessState.INVESTIGATING

                # Show periodic progress
                elapsed = time.time() - start_time
                if int(elapsed) % 30 == 0:  # Every 30 seconds
                    self._show_progress(snapshot, elapsed, context)

            # Process finished
            returncode = process.returncode
            elapsed_total = time.time() - start_time

            final_status = {
                "pid": pid,
                "name": context.name,
                "purpose": context.purpose,
                "returncode": returncode,
                "duration_sec": elapsed_total,
                "snapshots_count": len(self.tracked_processes[pid]),
                "state": (
                    ProcessState.FINISHED if returncode == 0 else ProcessState.FAILED
                ).value,
                "expected_duration": context.expected_duration_sec,
                "actual_vs_expected": f"{elapsed_total / context.expected_duration_sec:.1f}x"
                if context.expected_duration_sec
                else "N/A",
            }

            # Save tracking log
            self._save_tracking_log(pid, context, final_status)

            print(f"\n✓ Process Completed: {context.name}")
            print(f"   Return Code: {returncode}")
            print(f"   Duration: {elapsed_total:.1f}s (~{elapsed_total / 60:.1f}min)")
            if context.expected_duration_sec:
                print(
                    f"   Expected: {context.expected_duration_sec}s (~{context.expected_duration_sec / 60:.1f}min)"
                )
                print(f"   Variance: {final_status['actual_vs_expected']}")

            return final_status

        except psutil.NoSuchProcess:
            return {
                "error": "Process disappeared",
                "pid": pid,
                "state": ProcessState.FAILED.value,
            }

    def _capture_snapshot(self, psutil_process: psutil.Process) -> ProcessSnapshot:
        """Capture current behavioral state of process"""
        try:
            cpu = psutil_process.cpu_percent(interval=0.1)
            mem = psutil_process.memory_info().rss / (1024 * 1024)  # MB

            # Network I/O (if available)
            try:
                net_io = psutil_process.io_counters()
                net_sent = net_io.write_bytes  # Approximate
                net_recv = net_io.read_bytes
            except (AttributeError, psutil.AccessDenied):
                net_sent = 0
                net_recv = 0

            # Disk I/O
            try:
                io = psutil_process.io_counters()
                io_read = io.read_bytes
                io_write = io.write_bytes
            except (AttributeError, psutil.AccessDenied):
                io_read = 0
                io_write = 0

            # Infer state from behavior
            state = self._infer_state(cpu, mem, net_sent, io_write)

            return ProcessSnapshot(
                timestamp=datetime.now(),
                pid=psutil_process.pid,
                cpu_percent=cpu,
                memory_mb=mem,
                network_bytes_sent=net_sent,
                network_bytes_recv=net_recv,
                io_read_bytes=io_read,
                io_write_bytes=io_write,
                state=state,
                notes="",
            )

        except psutil.NoSuchProcess:
            return ProcessSnapshot(
                timestamp=datetime.now(),
                pid=psutil_process.pid,
                cpu_percent=0,
                memory_mb=0,
                network_bytes_sent=0,
                network_bytes_recv=0,
                io_read_bytes=0,
                io_write_bytes=0,
                state=ProcessState.FAILED,
                notes="Process disappeared",
            )

    def _infer_state(self, cpu: float, mem: float, net: int, io: int) -> ProcessState:
        """Infer what process is doing based on metrics"""
        if cpu > 50:
            return ProcessState.PROCESSING
        elif net > 1024 * 1024:  # 1MB+ network
            return ProcessState.DOWNLOADING
        elif io > 1024 * 1024:  # 1MB+ disk I/O
            return ProcessState.PROCESSING
        elif cpu < 1:
            return ProcessState.WAITING
        else:
            return ProcessState.PROCESSING

    def _should_investigate(
        self, snapshots: list, context: ProcessContext, start_time: float
    ) -> Optional[Dict[str, str]]:
        """
        Determine if process behavior warrants investigation.
        NOTE: This does NOT kill the process, just alerts.
        """
        if len(snapshots) < 3:
            return None  # Need more data

        latest = snapshots[-1]
        elapsed = time.time() - start_time

        # Check 1: Taking much longer than expected
        if context.expected_duration_sec:
            if (
                elapsed
                > context.expected_duration_sec
                * self.investigation_config["duration_multiplier"]
            ):
                return {
                    "reason": f"Duration {elapsed / context.expected_duration_sec:.1f}x expected ({elapsed:.0f}s vs {context.expected_duration_sec}s)",
                    "suggestion": "Check if downloading large file or stuck. Let it continue if showing progress.",
                }

        # Check 2: No CPU activity for extended period (potential stuck)
        recent_snapshots = snapshots[-10:]  # Last 10 snapshots
        avg_cpu = sum(s.cpu_percent for s in recent_snapshots) / len(recent_snapshots)
        if avg_cpu < self.investigation_config["cpu_idle_threshold"]:
            if elapsed > self.investigation_config["stuck_duration_sec"]:
                return {
                    "reason": f"Low CPU activity ({avg_cpu:.1f}%) for {elapsed:.0f}s",
                    "suggestion": "Might be stuck or waiting. Check process logs/output.",
                }

        # Check 3: Excessive memory usage
        if latest.memory_mb > self.investigation_config["memory_threshold_mb"]:
            return {
                "reason": f"High memory usage ({latest.memory_mb:.0f}MB)",
                "suggestion": "Check if memory leak or legitimate large operation.",
            }

        return None

    def _show_progress(
        self, snapshot: ProcessSnapshot, elapsed: float, context: ProcessContext
    ):
        """Show periodic progress update"""
        print(
            f"⏱  Progress: {elapsed:.0f}s | "
            f"State: {snapshot.state.value} | "
            f"CPU: {snapshot.cpu_percent:.1f}% | "
            f"MEM: {snapshot.memory_mb:.0f}MB"
        )

    def _save_tracking_log(
        self, pid: int, context: ProcessContext, final_status: Dict[str, Any]
    ):
        """Save tracking history for future learning"""
        log_file = (
            self.logs_dir
            / f"process_{pid}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )

        log_data = {
            "context": asdict(context),
            "final_status": final_status,
            "snapshots": [
                {
                    "timestamp": s.timestamp.isoformat(),
                    "cpu_percent": s.cpu_percent,
                    "memory_mb": s.memory_mb,
                    "state": s.state.value,
                }
                for s in self.tracked_processes[pid]
            ],
        }

        with open(log_file, "w", encoding="utf-8") as f:
            json.dump(log_data, f, indent=2)

        print(f"   Tracking log saved: {log_file.name}")


# Example usage
if __name__ == "__main__":
    print("=== ΞNuSyQ Process Tracker Demo ===\n")

    tracker = ProcessTracker()

    # Example 1: Simulate downloading large model
    print("Example 1: Tracking long-running download (simulated)")
    context = ProcessContext(
        name="Download deepseek-coder-33b",
        command="ollama pull deepseek-coder:33b",
        purpose="Downloading 18GB model file",
        expected_duration_sec=1800,  # 30min estimate
        expected_behavior="High network activity, low CPU",
        investigation_triggers={},
    )

    # In real usage:
    # process = subprocess.Popen(["ollama", "pull", "deepseek-coder:33b"])
    # result = tracker.track(process, context)

    print("\nKey Difference from Timeouts:")
    print("  ❌ Timeout: Kill after 30min regardless of progress")
    print(
        "  ✅ Tracker: Monitor behavior, investigate if stuck, but KEEP RUNNING if making progress"
    )
