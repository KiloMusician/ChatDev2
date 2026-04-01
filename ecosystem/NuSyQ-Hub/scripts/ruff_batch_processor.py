#!/usr/bin/env python3
"""Smarter Ruff Batch Processor - Process files in smaller chunks with timeouts.

Problem: `ruff check src/ --fix` hangs for hours on the full codebase.
Solution: Process files in batches, with timeouts and progress tracking.

Features:
- Batch processing (default 10 files per batch)
- Per-file timeout (default 30 seconds)
- Real-time progress logging
- Skip problematic files and continue
- Resume capability via checkpoint file
- Summary report at the end
"""

import json
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
SRC_DIR = PROJECT_ROOT / "src"
CHECKPOINT_FILE = PROJECT_ROOT / "state" / "ruff_batch_checkpoint.json"
LOG_FILE = PROJECT_ROOT / "logs" / "ruff_batch_processor.log"


class RuffBatchProcessor:
    def __init__(self, batch_size: int = 10, timeout_per_file: int = 30):
        self.batch_size = batch_size
        self.timeout_per_file = timeout_per_file
        self.processed_files: set[str] = set()
        self.failed_files: dict[str, str] = {}
        self.skipped_files: dict[str, str] = {}
        self.timing_stats: list[tuple[str, float]] = []
        self.total_batches = 0
        self.current_batch = 0

        # Setup directories
        CHECKPOINT_FILE.parent.mkdir(parents=True, exist_ok=True)
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

        self._load_checkpoint()
        self._log(f"🚀 Starting Ruff Batch Processor (batch_size={batch_size}, timeout={timeout_per_file}s)")

    def _log(self, message: str) -> None:
        """Log message to both console and file."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        print(log_entry)
        with open(LOG_FILE, "a") as f:
            f.write(log_entry + "\n")

    def _load_checkpoint(self) -> None:
        """Load checkpoint to resume interrupted work."""
        if CHECKPOINT_FILE.exists():
            try:
                with open(CHECKPOINT_FILE) as f:
                    data = json.load(f)
                    self.processed_files = set(data.get("processed_files", []))
                    self.failed_files = data.get("failed_files", {})
                    self.skipped_files = data.get("skipped_files", {})
                    if self.processed_files:
                        self._log(f"✅ Resumed from checkpoint: {len(self.processed_files)} files already processed")
            except Exception as e:
                self._log(f"⚠️  Checkpoint load failed, starting fresh: {e}")

    def _save_checkpoint(self) -> None:
        """Save progress checkpoint."""
        data = {
            "processed_files": list(self.processed_files),
            "failed_files": self.failed_files,
            "skipped_files": self.skipped_files,
            "timestamp": datetime.now().isoformat(),
        }
        try:
            with open(CHECKPOINT_FILE, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            self._log(f"⚠️  Checkpoint save failed: {e}")

    def _get_all_python_files(self) -> list[Path]:
        """Get all Python files in src/ directory."""
        if not SRC_DIR.exists():
            self._log(f"❌ Source directory not found: {SRC_DIR}")
            return []

        python_files = sorted([f for f in SRC_DIR.rglob("*.py") if f.is_file()])
        self._log(f"📁 Found {len(python_files)} Python files in {SRC_DIR}")
        return python_files

    def _process_single_file(self, file_path: Path) -> tuple[bool, str]:
        """Process single file with timeout."""
        try:
            # Run ruff check with fixes on single file
            result = subprocess.run(
                ["ruff", "check", str(file_path), "--fix"],
                capture_output=True,
                text=True,
                timeout=self.timeout_per_file,
            )

            if result.returncode == 0:
                return True, "Fixed"
            else:
                # ruff returns non-zero if it found issues (even if fixed), that's OK
                return True, "Checked"
        except subprocess.TimeoutExpired:
            return False, f"Timeout after {self.timeout_per_file}s"
        except FileNotFoundError:
            return False, "ruff not installed"
        except Exception as e:
            return False, str(e)

    def _process_batch(self, batch: list[Path]) -> None:
        """Process a batch of files."""
        self.current_batch += 1
        self._log(f"\n📦 Processing batch {self.current_batch}/{self.total_batches} ({len(batch)} files)")

        for i, file_path in enumerate(batch, 1):
            file_key = str(file_path.relative_to(PROJECT_ROOT))

            # Skip already processed
            if file_key in self.processed_files:
                continue

            # Run ruff on single file
            start_time = time.time()
            success, status = self._process_single_file(file_path)
            elapsed = time.time() - start_time

            self.timing_stats.append((file_key, elapsed))

            if success:
                self.processed_files.add(file_key)
                progress = f"({i}/{len(batch)})"
                self._log(f"  ✅ {file_key} {progress} [{elapsed:.2f}s]")
            else:
                self.failed_files[file_key] = status
                self._log(f"  ⚠️  {file_key} - {status}")

            # Save checkpoint after each file
            self._save_checkpoint()

    def run(self) -> None:
        """Run the batch processor."""
        all_files = self._get_all_python_files()

        if not all_files:
            self._log("❌ No Python files found")
            return

        # Filter to unprocessed files
        pending_files = [f for f in all_files if str(f.relative_to(PROJECT_ROOT)) not in self.processed_files]

        if not pending_files:
            self._log("✅ All files already processed!")
            self._print_summary()
            return

        self._log(f"⏳ {len(pending_files)} files remaining to process")

        # Calculate batches
        self.total_batches = (len(pending_files) + self.batch_size - 1) // self.batch_size

        # Process in batches
        for i in range(0, len(pending_files), self.batch_size):
            batch = pending_files[i : i + self.batch_size]
            self._process_batch(batch)

            # Show progress
            remaining = len(pending_files) - (i + self.batch_size)
            if remaining > 0:
                self._log(f"\n⏱️  {remaining} files remaining...")

        self._log("\n" + "=" * 60)
        self._log("🎯 Batch processing complete!")
        self._print_summary()

    def _print_summary(self) -> None:
        """Print final summary."""
        self._log("\n📊 SUMMARY")
        self._log(f"  ✅ Processed: {len(self.processed_files)}")
        self._log(f"  ⚠️  Failed: {len(self.failed_files)}")
        self._log(f"  ⏭️  Skipped: {len(self.skipped_files)}")

        if self.timing_stats:
            times = [t for _, t in self.timing_stats]
            avg_time = sum(times) / len(times)
            max_time = max(times)
            self._log("\n⏰ TIMING")
            self._log(f"  Average: {avg_time:.2f}s per file")
            self._log(f"  Max: {max_time:.2f}s")

        if self.failed_files:
            self._log("\n❌ Failed files:")
            for file_path, reason in list(self.failed_files.items())[:10]:  # Show first 10
                self._log(f"  - {file_path}: {reason}")
            if len(self.failed_files) > 10:
                self._log(f"  ... and {len(self.failed_files) - 10} more")

        self._log(f"\n📝 Full log: {LOG_FILE}")


def main():
    """Main entry point."""
    # Parse arguments
    batch_size = 10
    timeout = 30

    if len(sys.argv) > 1:
        try:
            batch_size = int(sys.argv[1])
        except ValueError:
            pass

    if len(sys.argv) > 2:
        try:
            timeout = int(sys.argv[2])
        except ValueError:
            pass

    processor = RuffBatchProcessor(batch_size=batch_size, timeout_per_file=timeout)
    processor.run()


if __name__ == "__main__":
    main()
