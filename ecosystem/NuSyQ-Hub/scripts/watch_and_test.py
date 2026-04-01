#!/usr/bin/env python3
"""Watch Python files and auto-run tests on changes.

Usage:
    python scripts/watch_and_test.py              # Watch src/ and tests/
    python scripts/watch_and_test.py --fast       # Run only fast tests (no slow marker)
"""

import subprocess
import sys
import time
from pathlib import Path

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer


class TestRunner(FileSystemEventHandler):
    """Run tests when Python files change."""

    def __init__(self, fast_mode: bool = False):
        self.fast_mode = fast_mode
        self.last_run: float = 0
        self.debounce_seconds = 3

    def on_modified(self, event):
        """Handle file modification events."""
        if event.is_directory or not event.src_path.endswith(".py"):
            return

        now = time.time()
        if (now - self.last_run) < self.debounce_seconds:
            return

        if "__pycache__" in event.src_path or event.src_path.endswith(".pyc"):
            return

        print(f"\n🔔 File changed: {Path(event.src_path).name}")
        self.run_tests()
        self.last_run = now

    def run_tests(self):
        """Run pytest with appropriate flags."""
        cmd = ["pytest", "-xvs", "--tb=short"]

        if self.fast_mode:
            cmd.extend(["-m", "not slow"])

        print("\n" + "=" * 60)
        print(f"⚡ Running: {' '.join(cmd)}")
        print("=" * 60 + "\n")

        try:
            result = subprocess.run(cmd, cwd=Path(__file__).parent.parent, check=False)

            if result.returncode == 0:
                print("\n✅ All tests passed")
            else:
                print(f"\n❌ Tests failed (exit code: {result.returncode})")

        except KeyboardInterrupt:
            print("\n⚠️  Test run interrupted")


def watch(fast_mode: bool = False):
    """Watch src/ and tests/ directories for changes."""
    repo_root = Path(__file__).parent.parent
    watch_dirs = [repo_root / "src", repo_root / "tests"]

    print("👁️  Auto-test watcher started")
    print("📂 Watching: src/, tests/")
    print(f"⚡ Fast mode: {fast_mode} {'(skips slow tests)' if fast_mode else ''}")
    print("⏱️  Debounce: 3 seconds")
    print("📝 Press Ctrl+C to stop\n")

    event_handler = TestRunner(fast_mode=fast_mode)
    observer = Observer()

    for watch_dir in watch_dirs:
        if watch_dir.exists():
            observer.schedule(event_handler, str(watch_dir), recursive=True)
            print(f"  ✅ Watching {watch_dir.name}/")

    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\n👋 Stopping file watcher")
        observer.stop()

    observer.join()


if __name__ == "__main__":
    ARGS = sys.argv[1:]
    FAST_MODE = "--fast" in ARGS

    watch(FAST_MODE)
