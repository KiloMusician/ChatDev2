#!/usr/bin/env python3
"""NuSyQ Development Automation - Watch and Auto-Test
Monitors source files and runs tests automatically on changes.
"""

import json
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

# Metasynthesis Output System integration
try:
    from src.output.metasynthesis_output_system import (
        ExecutionContext,
        MetasynthesisOutputSystem,
        OperationReceipt,
        OutputTier,
        Signal,
        SignalSeverity,
    )
except Exception:
    MetasynthesisOutputSystem = None  # type: ignore
    OutputTier = None  # type: ignore
    ExecutionContext = None  # type: ignore
    Signal = None  # type: ignore
    SignalSeverity = None  # type: ignore
    OperationReceipt = None  # type: ignore

# Terminal routing
try:
    from src.output.terminal_router import Channel, emit_route
except ImportError:

    def emit_route(*_args, **_kwargs):  # type: ignore
        return None

    class Channel:  # type: ignore
        AGENTS = "AGENTS"


try:
    from watchdog.events import FileSystemEventHandler
    from watchdog.observers import Observer
except ImportError:
    print("❌ watchdog not installed. Installing...")
    subprocess.run([sys.executable, "-m", "pip", "install", "watchdog"], check=True)
    from watchdog.events import FileSystemEventHandler
    from watchdog.observers import Observer


class TestRunner(FileSystemEventHandler):
    """Automatically run tests when files change."""

    def __init__(self, root_path: Path):
        self.root_path = root_path
        self.last_run: float = 0.0
        self.debounce_seconds = 2

    def should_trigger(self, event) -> bool:
        """Check if event should trigger test run."""
        if event.is_directory:
            return False

        path = Path(event.src_path)

        # Only trigger on Python files
        if path.suffix != ".py":
            return False

        # Skip certain directories
        skip_dirs = {".venv", "__pycache__", ".pytest_cache", ".mypy_cache", "node_modules"}
        if any(skip in path.parts for skip in skip_dirs):
            return False

        # Debounce
        current_time = time.time()
        if current_time - self.last_run < self.debounce_seconds:
            return False

        return True

    def run_tests(self, changed_file: Path):
        """Run relevant tests for changed file."""
        self.last_run = time.time()
        timestamp = datetime.now().strftime("%H:%M:%S")

        print("\n" + ("=" * 80))
        print(f"🔄 [{timestamp}] File changed: {changed_file.name}")
        print(("=" * 80) + "\n")

        # Determine test file
        if "test_" in changed_file.name:
            test_file = changed_file
        else:
            # Try to find corresponding test
            test_name = f"test_{changed_file.stem}.py"
            test_file = self.root_path / "tests" / test_name
            if not test_file.exists():
                test_file = None

        if test_file and test_file.exists():
            print(f"🧪 Running tests: {test_file.name}\n")
            subprocess.run(
                [sys.executable, "-m", "pytest", str(test_file), "-v", "--tb=short"],
                cwd=self.root_path,
                check=False,
            )
        else:
            print("🧪 Running quick test suite\n")
            subprocess.run(
                [sys.executable, "-m", "pytest", "tests/", "-q", "-x"],
                cwd=self.root_path,
                check=False,
            )

        print("\n" + ("=" * 80))
        print("✅ Test run complete - watching for changes...")
        print(("=" * 80) + "\n")

    def on_modified(self, event):
        """Handle file modification."""
        if self.should_trigger(event):
            self.run_tests(Path(event.src_path))


def main():
    """Start development watcher."""
    root = Path(__file__).parent.parent
    # Route to Agents terminal
    emit_route(Channel.AGENTS, "NuSyQ Development Watcher")

    print(
        f"""
╔════════════════════════════════════════════════════════════════════════════════╗
║                                                                                ║
║          🤖 NuSyQ Development Watcher - Auto-Test Mode                        ║
║                                                                                ║
╚════════════════════════════════════════════════════════════════════════════════╝

📁 Watching: {root}
🧪 Auto-running tests on file changes
⏱️  Debounce: 2 seconds

Press Ctrl+C to stop...
"""
    )

    # Emit startup receipt
    try:
        if MetasynthesisOutputSystem is not None and ExecutionContext is not None and OperationReceipt is not None:
            run_id = f"dev_watcher_start_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            system = MetasynthesisOutputSystem(tier=OutputTier.CONSCIOUS)
            context = ExecutionContext(
                run_id=run_id,
                agent_id="dev_watcher",
                branch="unknown",
                python_version=sys.version.split(" ")[0],
                venv_active=(sys.prefix != sys.base_prefix),
                timestamp=datetime.now().isoformat(),
                cwd=str(root),
            )

            signals = [
                Signal(
                    severity=SignalSeverity.INFO,
                    category="[WATCH]",
                    message="Watcher started (src, tests)",
                    confidence=0.9,
                )
            ]
            receipt = OperationReceipt(
                context=context,
                title="Dev Watcher Start",
                signals=signals,
                artifacts=[],
                outcome="✅ Success",
                next_actions=["Edit files to trigger tests"],
                guild_implications={"flow": "interactive"},
            )

            state_dir = root / "state" / "receipts"
            state_dir.mkdir(parents=True, exist_ok=True)
            out_path = state_dir / f"{run_id}.json"
            with out_path.open("w", encoding="utf-8") as f:
                json.dump(system.render_machine_footer(receipt), f, indent=2)
    except (RuntimeError, OSError):
        pass

    event_handler = TestRunner(root)
    observer = Observer()
    observer.schedule(event_handler, str(root / "src"), recursive=True)
    observer.schedule(event_handler, str(root / "tests"), recursive=True)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\n🛑 Stopping watcher...")
        observer.stop()

    observer.join()
    print("✅ Watcher stopped")


if __name__ == "__main__":
    main()
