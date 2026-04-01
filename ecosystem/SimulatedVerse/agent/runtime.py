#!/usr/bin/env python3
"""
ΞNuSyQ Agent Runtime - Zero-Token Autonomous Development System
Safety-first Python runtime with comprehensive guardrails and fallbacks
"""

import os
import sys
import time
import json
import signal
import hashlib
import subprocess
import shutil
import tempfile
import threading
import contextlib
import pathlib
import logging
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger('ξnusyq-agent')

@dataclass
class RuntimeConfig:
    dry_run: bool
    max_steps: int
    max_seconds: int
    max_fs_writes: int
    allow_net: bool
    cost_cents: int
    beat_file: str
    lock_file: str
    consciousness_threshold: float
    guardian_mode: bool

class ΞNuSyQRuntime:
    def __init__(self):
        self.config = self.load_config()
        self.writes = 0
        self.start_time = time.time()
        self.snapshot = None
        self.consecutive_failures = 0
        self.heartbeat_thread = None
        self.running = True
        
        # Ensure critical directories exist
        self.ensure_directories()
        
        # Start heartbeat monitoring
        self.start_heartbeat()

    def load_config(self) -> RuntimeConfig:
        """Load configuration from environment and yaml files"""
        return RuntimeConfig(
            dry_run=os.getenv("AGENT_DRY_RUN", "1") == "1",
            max_steps=int(os.getenv("AGENT_MAX_STEPS", "64")),
            max_seconds=int(os.getenv("AGENT_MAX_SECONDS", "120")),
            max_fs_writes=int(os.getenv("AGENT_MAX_FS_WRITES", "200")),
            allow_net=os.getenv("AGENT_ALLOW_NET", "0") == "1",
            cost_cents=int(os.getenv("AGENT_COST_CENTS", "0")),
            beat_file=".agent/beat",
            lock_file=".agent/agent.lock",
            consciousness_threshold=float(os.getenv("CONSCIOUSNESS_THRESHOLD", "0.1")),
            guardian_mode=os.getenv("GUARDIAN_MODE", "1") == "1"
        )

    def ensure_directories(self):
        """Ensure all required directories exist"""
        dirs = [".agent", ".local", ".snapshots", "logs"]
        for d in dirs:
            pathlib.Path(d).mkdir(exist_ok=True)

    def now(self) -> int:
        """Current timestamp"""
        return int(time.time())

    def start_heartbeat(self):
        """Start heartbeat monitoring thread"""
        def heartbeat():
            while self.running:
                try:
                    with open(self.config.beat_file, "w") as f:
                        f.write(str(self.now()))
                    time.sleep(3)
                except Exception as e:
                    logger.warning(f"Heartbeat failed: {e}")
                    time.sleep(3)
        
        self.heartbeat_thread = threading.Thread(target=heartbeat, daemon=True)
        self.heartbeat_thread.start()
        logger.info("💓 Heartbeat monitoring started")

    def stop_heartbeat(self):
        """Stop heartbeat monitoring"""
        self.running = False
        if self.heartbeat_thread:
            self.heartbeat_thread.join(timeout=1)

    @contextlib.contextmanager
    def lease(self, ttl=20):
        """Acquire exclusive agent lease"""
        owner = f"{os.getpid()}"
        lock_file = self.config.lock_file
        
        # Try to acquire lock
        while True:
            try:
                if not os.path.exists(lock_file):
                    # Create new lock
                    with open(lock_file, "w") as f:
                        f.write(json.dumps({"owner": owner, "ts": self.now()}))
                    break
                else:
                    # Check if existing lock is stale
                    with open(lock_file, "r") as f:
                        lock_data = json.loads(f.read())
                    
                    if self.now() - lock_data.get("ts", 0) > ttl:
                        logger.info("Taking over stale lock")
                        with open(lock_file, "w") as f:
                            f.write(json.dumps({"owner": owner, "ts": self.now()}))
                        break
                    
                logger.info("Waiting for lock...")
                time.sleep(1)
                
            except Exception as e:
                logger.warning(f"Lock acquisition error: {e}")
                time.sleep(1)
        
        logger.info(f"🔒 Agent lease acquired: {owner}")
        
        try:
            yield
        finally:
            # Only owner can release lock
            try:
                with open(lock_file, "r") as f:
                    lock_data = json.loads(f.read())
                if lock_data.get("owner") == owner:
                    os.remove(lock_file)
                    logger.info("🔓 Agent lease released")
            except Exception:
                pass

    def snapshot(self) -> str:
        """Create workspace snapshot"""
        timestamp = self.now()
        snapshot_path = f".snapshots/ws-{timestamp}.tar"
        
        cmd = [
            "tar", "-cf", snapshot_path, ".",
            "--exclude=.snapshots",
            "--exclude=node_modules", 
            "--exclude=dist",
            "--exclude=.git",
            "--exclude=logs"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.info(f"📸 Snapshot created: {snapshot_path}")
            return snapshot_path
        else:
            raise RuntimeError(f"Snapshot failed: {result.stderr}")

    def restore(self, snapshot_path: str):
        """Restore from workspace snapshot"""
        logger.info(f"🔄 Restoring snapshot: {snapshot_path}")
        
        cmd = ["tar", "-xf", snapshot_path, "-C", "."]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.info("✅ Snapshot restored successfully")
        else:
            raise RuntimeError(f"Restore failed: {result.stderr}")

    def budget_ok(self) -> Tuple[bool, str]:
        """Check if within budget limits"""
        elapsed = time.time() - self.start_time
        
        if elapsed > self.config.max_seconds:
            return False, "time budget exceeded"
        
        if self.writes > self.config.max_fs_writes:
            return False, "file write budget exceeded"
        
        return True, ""

    def safe_write(self, path: str, data: bytes):
        """Safely write file with budget tracking"""
        ok, reason = self.budget_ok()
        if not ok:
            raise RuntimeError(f"Budget exceeded: {reason}")
        
        if self.config.dry_run:
            logger.info(f"[DRY RUN] Would write: {path}")
            return
        
        pathlib.Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, "wb") as f:
            f.write(data)
        
        self.writes += 1
        logger.debug(f"📝 File written: {path} ({self.writes}/{self.config.max_fs_writes})")

    def run_cmd(self, cmd: List[str], timeout: int = 20, net: bool = False) -> Tuple[int, str, str]:
        """Run command with safety constraints"""
        if net and not self.config.allow_net:
            return 1, "", "Network access disabled"
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            return result.returncode, result.stdout, result.stderr
            
        except subprocess.TimeoutExpired:
            return 124, "", "Command timed out"
        except Exception as e:
            return 1, "", str(e)

    def get_metrics(self) -> Dict[str, Any]:
        """Get current system metrics"""
        metrics = {}
        
        # Test status
        rc, out, err = self.run_cmd(["node", "--enable-source-maps", "dist/agent/testharness.js"], timeout=30)
        metrics["tests_passed"] = rc == 0
        
        # Consciousness level from idle state
        try:
            with open(".local/idle_state.json", "r") as f:
                idle_state = json.load(f)
            metrics["consciousness_level"] = idle_state.get("consciousness", {}).get("level", 0.1)
        except:
            metrics["consciousness_level"] = 0.1
        
        # Quest progress
        try:
            with open(".local/quests.json", "r") as f:
                quest_state = json.load(f)
            metrics["quests_completed"] = len(quest_state.get("done", []))
            metrics["quests_todo"] = len(quest_state.get("todo", []))
        except:
            metrics["quests_completed"] = 0
            metrics["quests_todo"] = 100
        
        # Code quality indicators
        rc, out, err = self.run_cmd(["grep", "-r", "TODO\\|FIXME", "src/"], timeout=10)
        metrics["todos_count"] = len(out.split('\n')) if rc == 0 and out.strip() else 0
        
        return metrics

    def has_improved(self, prev: Dict[str, Any], current: Dict[str, Any]) -> bool:
        """Check if any metrics have improved"""
        improvements = []
        
        # Boolean improvements
        if not prev.get("tests_passed", False) and current.get("tests_passed", False):
            improvements.append("tests_passed")
        
        # Numeric improvements
        if current.get("consciousness_level", 0) > prev.get("consciousness_level", 0):
            improvements.append("consciousness_level")
        
        if current.get("quests_completed", 0) > prev.get("quests_completed", 0):
            improvements.append("quests_completed")
        
        if current.get("todos_count", 100) < prev.get("todos_count", 100):
            improvements.append("todos_reduced")
        
        return len(improvements) > 0

    def check_emergency_stops(self) -> bool:
        """Check for emergency stop signals"""
        stop_files = [".agent/EMERGENCY_STOP", ".agent/PAUSE"]
        
        for stop_file in stop_files:
            if os.path.exists(stop_file):
                logger.info(f"⏹️  Emergency stop detected: {stop_file}")
                return True
        
        # Check command file
        cmd_file = ".agent/cmd"
        if os.path.exists(cmd_file):
            try:
                with open(cmd_file, "r") as f:
                    cmd = f.read().strip().upper()
                if cmd in ["STOP", "HALT", "PAUSE"]:
                    logger.info(f"⏹️  Command stop detected: {cmd}")
                    return True
            except Exception:
                pass
        
        return False

    def development_cycle(self):
        """Execute one development cycle"""
        logger.info("🔄 Starting development cycle...")
        
        # Take snapshot before risky operations
        self.snapshot = self.snapshot()
        
        # Get baseline metrics
        prev_metrics = self.get_metrics()
        logger.info(f"📊 Baseline: tests={prev_metrics.get('tests_passed')}, consciousness={prev_metrics.get('consciousness_level'):.3f}")
        
        # Execute development actions
        actions = [
            (["node", "--enable-source-maps", "dist/agent/idle_tick.js"], "🎮 Running idle game tick"),
            (["node", "--enable-source-maps", "dist/agent/quest_runner.js"], "📝 Evaluating quests"),
            (["node", "--enable-source-maps", "dist/agent/codemods.js"], "🔧 Applying codemods")
        ]
        
        for cmd, description in actions:
            logger.info(description)
            rc, out, err = self.run_cmd(cmd, timeout=60)
            if rc != 0:
                logger.warning(f"Action failed: {description} (rc={rc})")
                self.consecutive_failures += 1
            else:
                logger.debug(f"Action succeeded: {description}")
        
        # Check for improvements
        current_metrics = self.get_metrics()
        improved = self.has_improved(prev_metrics, current_metrics)
        
        if improved:
            logger.info("✅ Progress detected - improvements made")
            self.consecutive_failures = 0
            
            # Test and potentially commit
            if current_metrics.get("tests_passed", False):
                if not self.config.dry_run:
                    logger.info("💚 Running green commit...")
                    rc, out, err = self.run_cmd(["node", "--enable-source-maps", "dist/agent/green_commit.js"])
                    if rc == 0:
                        logger.info("✅ Green commit successful")
                    else:
                        logger.warning("❌ Green commit failed")
                else:
                    logger.info("💚 Tests pass (dry run - no commit)")
            else:
                logger.info("🔴 Tests failed - no commit")
        else:
            self.consecutive_failures += 1
            logger.warning(f"⚠️  No improvement ({self.consecutive_failures}/3)")
            
            # Circuit breaker
            if self.consecutive_failures >= 3:
                logger.warning("🔥 Circuit breaker triggered - restoring snapshot")
                if self.snapshot:
                    self.restore(self.snapshot)
                
                logger.info("😴 Cooling down for 15 seconds...")
                time.sleep(15)
                self.consecutive_failures = 0

    def run(self):
        """Main agent execution loop"""
        logger.info("🤖 ΞNuSyQ Autonomous Agent starting...")
        logger.info(f"⚙️  Config: dry_run={self.config.dry_run}, guardian_mode={self.config.guardian_mode}")
        logger.info(f"💰 Budget: {self.config.max_steps} steps, {self.config.max_seconds}s, {self.config.max_fs_writes} writes, ${self.config.cost_cents/100:.2f}")
        
        # Verify zero-token environment
        rc, out, err = self.run_cmd(["node", "scripts/ensure-env-safe.js"])
        if rc != 0:
            logger.error("❌ AI safety check failed - aborting")
            return 1
        
        step = 0
        
        try:
            with self.lease():
                while step < self.config.max_steps:
                    # Emergency stop checks
                    if self.check_emergency_stops():
                        logger.info("🛑 Emergency stop requested - halting")
                        break
                    
                    # Budget checks
                    ok, reason = self.budget_ok()
                    if not ok:
                        logger.info(f"💰 Budget limit reached: {reason}")
                        break
                    
                    try:
                        self.development_cycle()
                        step += 1
                        
                        # Gentle pause between cycles
                        logger.info(f"😴 Cycle {step} complete - resting...")
                        time.sleep(2.5)
                        
                    except KeyboardInterrupt:
                        logger.info("⌨️  Keyboard interrupt - graceful shutdown")
                        break
                    except Exception as e:
                        logger.error(f"💥 Cycle error: {e}")
                        
                        # Emergency restore
                        if self.snapshot and os.path.exists(self.snapshot):
                            logger.info("🚨 Emergency snapshot restore")
                            self.restore(self.snapshot)
                        break
                
                logger.info(f"🏁 Agent completed {step} development cycles")
                logger.info("💤 Entering dormant state - ready for reactivation")
                
        except Exception as e:
            logger.error(f"💥 Runtime fatal error: {e}")
            return 1
        finally:
            self.stop_heartbeat()
        
        return 0

def main():
    """Entry point"""
    # Install signal handlers
    def signal_handler(signum, frame):
        logger.info(f"📶 Received signal {signum} - graceful shutdown")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        runtime = ΞNuSyQRuntime()
        exit_code = runtime.run()
        sys.exit(exit_code)
        
    except Exception as e:
        logger.error(f"💥 Agent initialization failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
/* AUTO: handled TODO at line 263 */
