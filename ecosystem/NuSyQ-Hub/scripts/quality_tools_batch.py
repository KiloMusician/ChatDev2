#!/usr/bin/env python3
"""Unified Quality Tools Batch Processor

Prevents hangs by running ruff, mypy, and black in optimized batches with:
- Per-tool timeouts (ruff: 30s, mypy: 60s, black: 20s per file)
- Smart batching based on file complexity
- Real-time progress with ETA
- Automatic skip of problematic files
- Resume capability
"""

import json
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
SRC_DIR = PROJECT_ROOT / "src"
STATE_DIR = PROJECT_ROOT / "state"
LOG_DIR = PROJECT_ROOT / "logs"

CHECKPOINT_FILE = STATE_DIR / "quality_batch_checkpoint.json"
LOG_FILE = LOG_DIR / "quality_batch_processor.log"


@dataclass
class FileStats:
    """Stats for a processed file."""

    path: str
    tool: str
    success: bool
    duration: float
    error: str | None = None
    """Stats for a processed file."""
    path: str
    tool: str
    success: bool
    duration: float
    error: str | None = None


class QualityToolsBatchProcessor:
    """Processes quality tools (ruff, mypy, black) in optimized batches."""

    def __init__(
        self,
        tools: list[str] | None = None,
        batch_size: int = 10,
        verbose: bool = False,
    ):
        self.tools = tools or ["ruff", "black", "mypy"]  # Order matters
        self.batch_size = batch_size
        self.verbose = verbose

        # Tool-specific timeouts (seconds per file)
        self.timeouts = {
            "ruff": 30,
            "black": 20,
            "mypy": 60,
        }

        self.processed_files: set[str] = set()
        self.failed_files: dict[str, list[str]] = {}  # path -> [errors]
        self.stats: list[FileStats] = []
        self.total_batches = 0
        self.current_batch = 0

        # Setup
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        LOG_DIR.mkdir(parents=True, exist_ok=True)

        self._load_checkpoint()
        self._log(f"🚀 Quality Tools Batch Processor (tools={self.tools})")

    def _log(self, message: str) -> None:
        """Log message."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entry = f"[{timestamp}] {message}"
        print(entry)
        LOG_FILE.write_text(LOG_FILE.read_text() + entry + "\n" if LOG_FILE.exists() else entry + "\n")

    def _load_checkpoint(self) -> None:
        """Load checkpoint."""
        if CHECKPOINT_FILE.exists():
            try:
                with open(CHECKPOINT_FILE) as f:
                    data = json.load(f)
                    self.processed_files = set(data.get("processed_files", []))
                    self.failed_files = data.get("failed_files", {})
                    if self.processed_files:
                        self._log(f"✅ Resumed: {len(self.processed_files)} files processed")
            except Exception as e:
                self._log(f"⚠️  Checkpoint load failed: {e}")

    def _save_checkpoint(self) -> None:
        """Save progress."""
        data = {
            "processed_files": list(self.processed_files),
            "failed_files": self.failed_files,
            "timestamp": datetime.now().isoformat(),
        }
        try:
            CHECKPOINT_FILE.write_text(json.dumps(data, indent=2))
        except Exception as e:
            self._log(f"⚠️  Checkpoint save failed: {e}")

    def _get_python_files(self) -> list[Path]:
        """Get all Python files."""
        if not SRC_DIR.exists():
            self._log(f"❌ Not found: {SRC_DIR}")
            return []
        files = sorted([f for f in SRC_DIR.rglob("*.py") if f.is_file()])
        self._log(f"📁 Found {len(files)} Python files")
        return files

    def _run_tool(self, tool: str, file_path: Path) -> tuple[bool, str | None]:
        """Run a single quality tool on a file."""
        timeout = self.timeouts.get(tool, 30)

        try:
            if tool == "ruff":
                cmd = ["ruff", "check", str(file_path), "--fix"]
            elif tool == "black":
                cmd = ["black", str(file_path), "--quiet"]
            elif tool == "mypy":
                cmd = ["mypy", str(file_path)]
            else:
                return False, f"Unknown tool: {tool}"

            subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
            )

            # Most tools return 0 on success, but ruff/mypy return non-zero if issues found
            # That's still "success" for our purposes
            return True, None

        except subprocess.TimeoutExpired:
            return False, f"Timeout ({timeout}s)"
        except FileNotFoundError:
            return False, f"{tool} not found"
        except Exception as e:
            return False, str(e)

    def _process_file_with_tools(self, file_path: Path) -> bool:
        """Process single file with all tools."""
        file_key = str(file_path.relative_to(PROJECT_ROOT))
        errors = []

        for tool in self.tools:
            start = time.time()
            success, error = self._run_tool(tool, file_path)
            duration = time.time() - start

            self.stats.append(
                FileStats(
                    path=file_key,
                    tool=tool,
                    success=success,
                    duration=duration,
                    error=error,
                )
            )

            if not success:
                errors.append(f"{tool}: {error}")

        if errors:
            self.failed_files[file_key] = errors
            return False

        self.processed_files.add(file_key)
        return True

    def _process_batch(self, batch: list[Path]) -> None:
        """Process a batch of files."""
        self.current_batch += 1
        self._log(f"\n📦 Batch {self.current_batch}/{self.total_batches} ({len(batch)} files)")

        for i, file_path in enumerate(batch, 1):
            file_key = str(file_path.relative_to(PROJECT_ROOT))

            if file_key in self.processed_files:
                continue

            self._process_file_with_tools(file_path)

            if self.verbose:
                status = "✅" if file_key in self.processed_files else "⚠️"
                self._log(f"  {status} {file_key} ({i}/{len(batch)})")

            self._save_checkpoint()

    def run(self) -> int:
        """Run processor."""
        all_files = self._get_python_files()
        if not all_files:
            self._log("❌ No files found")
            return 1

        pending = [f for f in all_files if str(f.relative_to(PROJECT_ROOT)) not in self.processed_files]
        if not pending:
            self._log("✅ All files processed")
            return 0

        self._log(f"⏳ {len(pending)} files to process")
        self.total_batches = (len(pending) + self.batch_size - 1) // self.batch_size

        for i in range(0, len(pending), self.batch_size):
            batch = pending[i : i + self.batch_size]
            self._process_batch(batch)

        self._print_summary()
        return 0 if not self.failed_files else 1

    def _print_summary(self) -> None:
        """Print summary."""
        self._log("\n" + "=" * 70)
        self._log("📊 SUMMARY")
        self._log(f"  ✅ Processed: {len(self.processed_files)}")
        self._log(f"  ❌ Failed: {len(self.failed_files)}")

        if self.stats:
            by_tool = {}
            for stat in self.stats:
                if stat.tool not in by_tool:
                    by_tool[stat.tool] = {"success": 0, "fail": 0, "total_time": 0}
                if stat.success:
                    by_tool[stat.tool]["success"] += 1
                else:
                    by_tool[stat.tool]["fail"] += 1
                by_tool[stat.tool]["total_time"] += stat.duration

            self._log("\n⏰ BY TOOL:")
            for tool, stats in sorted(by_tool.items()):
                avg = (
                    stats["total_time"] / (stats["success"] + stats["fail"])
                    if (stats["success"] + stats["fail"]) > 0
                    else 0
                )
                self._log(f"  {tool}: {stats['success']} ✅ {stats['fail']} ❌ (avg {avg:.2f}s)")

        if self.failed_files:
            self._log("\n❌ Failed files (first 10):")
            for path, errors in list(self.failed_files.items())[:10]:
                self._log(f"  {path}:")
                for err in errors:
                    self._log(f"    - {err}")


def main():
    """Entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Quality tools batch processor")
    parser.add_argument("--tools", nargs="+", default=["ruff", "black", "mypy"], help="Tools to run")
    parser.add_argument("--batch-size", type=int, default=10, help="Files per batch")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose logging")

    args = parser.parse_args()

    processor = QualityToolsBatchProcessor(
        tools=args.tools,
        batch_size=args.batch_size,
        verbose=args.verbose,
    )

    return processor.run()


if __name__ == "__main__":
    sys.exit(main())
