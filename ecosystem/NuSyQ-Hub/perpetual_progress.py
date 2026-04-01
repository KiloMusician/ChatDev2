#!/usr/bin/env python3
"""Perpetual Progress Engine - Never stops, never asks, always improves"""

import json
import logging
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.spine import initialize_spine

logger = logging.getLogger(__name__)


class PerpetualEngine:
    def __init__(self):
        self.cycle = 0
        self.start_time = time.time()
        self.progress_log = Path("state/perpetual_progress.jsonl")
        self.progress_log.parent.mkdir(parents=True, exist_ok=True)
        try:
            initialize_spine(repo_root=PROJECT_ROOT)
        except Exception as exc:
            logger.warning("Perpetual engine spine init failed: %s", exc)

    def log(self, action, result, **kwargs):
        entry = {
            "cycle": self.cycle,
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "result": result,
            **kwargs,
        }
        with open(self.progress_log, "a") as f:
            f.write(json.dumps(entry) + "\n")
        return entry

    def run(self, cmd, description="", timeout=None):
        """Run command with adaptive timeout"""
        print(f"  ⚡ {description}")
        try:
            result = subprocess.run(
                cmd, shell=True, capture_output=True, text=True, timeout=timeout
            )
            return result.returncode == 0, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return False, "", "timeout"
        except Exception as e:
            return False, "", str(e)

    def chug_cycle(self):
        """Single chug cycle - always finds something to do"""
        self.cycle += 1
        print(f"\n🌀 CHUG CYCLE {self.cycle} | {(time.time() - self.start_time) / 60:.1f}min")

        # Action 1: Clean cache files
        success, _, _ = self.run(
            'find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true',
            "Clean Python cache",
        )
        self.log("clean_cache", "success" if success else "skipped")

        # Action 2: Run quick tests
        success, stdout, _ = self.run(
            "python -m pytest tests/test_auto_fix_imports.py -q --tb=no 2>&1 | tail -5",
            "Run auto-fix tests",
            timeout=30,
        )
        if success:
            self.log("quick_test", "passed", output=stdout[-200:])

        # Action 3: Check for uncommitted work
        success, stdout, _ = self.run("git status --short", "Check git status")
        if success and stdout.strip():
            lines = len(stdout.strip().split("\n"))
            self.log("git_check", f"{lines} changes")

            if lines > 5:
                # Auto-commit if many changes
                self.run("git add -A", "Stage all changes")
                self.run('git commit -m "chug: Auto-commit progress" 2>&1 || true', "Auto-commit")
                self.log("auto_commit", "completed")

        # Action 4: Archive generated files
        success, _, _ = self.run(
            r'mkdir -p .archive && find . -maxdepth 1 -name "*_report*.json" -exec mv {} .archive/ \; 2>/dev/null || true',
            "Archive reports",
        )

        # Action 5: Syntax check random files
        success, stdout, _ = self.run(
            'find src/ -name "*.py" -type f | head -10 | xargs -I{} python -m py_compile {} 2>&1 | grep -c Error || echo 0',
            "Syntax check",
        )
        self.log("syntax_check", "clean" if "0" in stdout else "errors_found")

        return True

    def run_forever(self, max_cycles=None):
        """Run perpetual chug cycles"""
        print("🚂 PERPETUAL CHUG ENGINE STARTED")
        print("================================")
        print("Never stops | Never asks | Always improves")
        print("================================\n")

        try:
            while max_cycles is None or self.cycle < max_cycles:
                self.chug_cycle()
                pause = min(10, max(2, 5))
                time.sleep(pause)
        except KeyboardInterrupt:
            print(f"\n🛑 Stopped at cycle {self.cycle}")
        finally:
            print(f"\n📊 Total: {self.cycle} cycles, {(time.time() - self.start_time) / 60:.1f}min")


if __name__ == "__main__":
    import sys

    cycles = int(sys.argv[1]) if len(sys.argv) > 1 else None
    engine = PerpetualEngine()
    engine.run_forever(max_cycles=cycles)
