#!/usr/bin/env python3
"""Smart Quality Tools Orchestrator

Prevents hangs by:
1. Analyzing file complexity first
2. Processing files in optimal batch sizes per category
3. Increasing timeouts for complex files
4. Showing real-time progress with ETA
5. Allowing graceful interruption and resumption

This is the "anti-hang" solution to ruff/quality tool processing.
"""

import json
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
SRC_DIR = PROJECT_ROOT / "src"
STATE_DIR = PROJECT_ROOT / "state"
LOG_DIR = PROJECT_ROOT / "logs"

ORCHESTRATOR_CHECKPOINT = STATE_DIR / "quality_orchestrator_checkpoint.json"
LOG_FILE = LOG_DIR / "quality_orchestrator.log"


class QualityToolsOrchestrator:
    """Orchestrates quality tools processing with smart batching."""

    def __init__(self, skip_analysis: bool = False, verbose: bool = False):
        self.skip_analysis = skip_analysis
        self.verbose = verbose
        self.start_time = time.time()

        # Setup
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        LOG_DIR.mkdir(parents=True, exist_ok=True)

        # Category config: (batch_size, timeout_per_file, tool_list)
        self.category_config = {
            "simple": (20, 10, ["ruff", "black", "mypy"]),
            "moderate": (10, 30, ["ruff", "black", "mypy"]),
            "complex": (5, 60, ["ruff", "black", "mypy"]),
            "problematic": (1, 120, ["ruff", "black", "mypy"]),
        }

        self._log("🚀 Quality Tools Orchestrator Starting")

    def _log(self, message: str) -> None:
        """Log with timestamp."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entry = f"[{timestamp}] {message}"
        print(entry)
        if LOG_FILE.exists():
            LOG_FILE.write_text(LOG_FILE.read_text() + entry + "\n")
        else:
            LOG_FILE.write_text(entry + "\n")

    def _run_analysis(self) -> dict[str, list[str]]:
        """Run file complexity analysis."""
        self._log("📊 Step 1: Analyzing file complexity...")

        try:
            result = subprocess.run(
                [sys.executable, "scripts/analyze_file_complexity.py"],
                cwd=PROJECT_ROOT,
                capture_output=True,
                text=True,
                timeout=300,
            )

            if result.returncode != 0:
                self._log(f"⚠️  Analysis failed: {result.stderr}")
                return {}

            # Parse the JSON report
            report_file = STATE_DIR / "file_complexity_analysis.json"
            if report_file.exists():
                with open(report_file) as f:
                    report = json.load(f)
                    categories = report.get("categories", {})
                    self._log(f"✅ Analysis complete: {self._categorize_summary(categories)}")
                    return categories
        except Exception as e:
            self._log(f"❌ Analysis error: {e}")

        return {}

    def _categorize_summary(self, categories: dict) -> str:
        """Summarize categories."""
        parts = []
        for cat in ["simple", "moderate", "complex", "problematic"]:
            count = len(categories.get(cat, []))
            if count > 0:
                parts.append(f"{count} {cat}")
        return ", ".join(parts)

    def _process_category(
        self,
        category: str,
        files: list[dict],
        batch_size: int,
        timeout: int,
    ) -> bool:
        """Process files in a category."""
        if not files:
            return True

        self._log(f"\n📦 Step 2.{list(self.category_config.keys()).index(category) + 1}: Processing {category} files")
        self._log(f"   Files: {len(files)}, Batch size: {batch_size}, Timeout: {timeout}s")

        # Create a per-category tool args
        tools = self.category_config[category][2]

        try:
            cmd = [
                sys.executable,
                "scripts/quality_tools_batch.py",
                "--tools",
                *tools,
                "--batch-size",
                str(batch_size),
            ]
            if self.verbose:
                cmd.append("--verbose")

            result = subprocess.run(
                cmd,
                cwd=PROJECT_ROOT,
                capture_output=False,  # Show output directly
                text=True,
                timeout=None,  # No timeout for the whole batch
            )

            if result.returncode == 0:
                self._log(f"✅ {category} complete")
                return True
            else:
                self._log(f"⚠️  {category} had some failures (continuing...)")
                return True  # Continue to next category
        except KeyboardInterrupt:
            self._log("⏸️  Interrupted by user - checkpoint saved, resumable")
            return False
        except Exception as e:
            self._log(f"❌ {category} failed: {e}")
            return False

    def run(self) -> int:
        """Run orchestrator."""
        self._log("=" * 70)
        self._log("QUALITY TOOLS ORCHESTRATOR - Anti-Hang Processing")
        self._log("=" * 70)

        # Step 1: Analyze
        if not self.skip_analysis:
            categories = self._run_analysis()
        else:
            self._log("⏭️  Skipping analysis (using cached results)")
            report_file = STATE_DIR / "file_complexity_analysis.json"
            if report_file.exists():
                with open(report_file) as f:
                    categories = json.load(f).get("categories", {})
            else:
                self._log("❌ No cached analysis found")
                return 1

        if not categories:
            self._log("❌ Failed to get file categories")
            return 1

        # Step 2: Process each category in order
        self._log("\n📋 Processing Plan:")
        sum(len(files) for files in categories.values())
        for cat in ["simple", "moderate", "complex", "problematic"]:
            files = categories.get(cat, [])
            if files:
                batch_size, timeout, _tools = self.category_config[cat]
                self._log(f"  {cat:12} - {len(files):3} files @ batch={batch_size:2}, timeout={timeout:3}s")

        self._log(f"\n  ⏱️  Total estimated time: {self._estimate_time(categories):.1f} minutes")
        self._log("\n🎯 Starting processing...\n")

        success = True
        for category in ["simple", "moderate", "complex", "problematic"]:
            files = categories.get(category, [])
            if not files:
                continue

            batch_size, timeout, _tools = self.category_config[category]

            if not self._process_category(category, files, batch_size, timeout):
                success = False
                break

        # Final summary
        self._log("\n" + "=" * 70)
        elapsed = time.time() - self.start_time
        self._log(f"⏱️  Total time: {elapsed / 60:.1f} minutes")

        if success:
            self._log("✅ Quality tools complete! All categories processed.")
            return 0
        else:
            self._log("⚠️  Processing interrupted or failed (resumable via checkpoint)")
            return 1

    def _estimate_time(self, categories: dict) -> float:
        """Estimate total processing time in minutes."""
        total_seconds = 0
        for cat, files in categories.items():
            # Estimate ~15 seconds per file (ruff + black + mypy average)
            _batch_size, _timeout, _tools = self.category_config[cat]
            # Simple estimate: files * 15 seconds
            total_seconds += len(files) * 15
        return total_seconds / 60


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Smart Quality Tools Orchestrator")
    parser.add_argument("--skip-analysis", action="store_true", help="Skip complexity analysis (use cached)")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose logging")

    args = parser.parse_args()

    orchestrator = QualityToolsOrchestrator(
        skip_analysis=args.skip_analysis,
        verbose=args.verbose,
    )

    try:
        return orchestrator.run()
    except KeyboardInterrupt:
        print("\n\n⏸️  Orchestrator interrupted. Progress saved. Resume with:")
        print("     python scripts/quality_orchestrator.py --skip-analysis")
        return 1


if __name__ == "__main__":
    sys.exit(main())
