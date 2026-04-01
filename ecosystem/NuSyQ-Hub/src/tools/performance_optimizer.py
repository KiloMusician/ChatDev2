"""Performance optimization utilities for subprocess handling and encoding robustness.

OmniTag: {
    "purpose": "Performance optimization for subprocess handling and terminal encoding",
    "dependencies": ["subprocess", "encoding", "logging"],
    "context": "Addresses PowerShell cp1252 encoding issues and subprocess performance",
    "evolution_stage": "v1.0"
}

MegaTag: {
    "type": "PerformanceOptimizer",
    "integration_points": ["subprocess_handling", "encoding_safety", "terminal_output"],
    "related_tags": ["PerformanceTools", "SubprocessUtils", "EncodingHelpers"]
}

RSHTS: ΞΨΩ∞⟨PERFORMANCE-OPTIMIZATION⟩→ΦΣΣ⟨SUBPROCESS-ENCODING⟩
"""

from __future__ import annotations

import logging
import os
import subprocess
import sys
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pathlib import Path

logger = logging.getLogger(__name__)


class EncodingSafeOutputHandler:
    """Handle terminal output safely across different encoding environments.

    Specifically addresses Windows PowerShell cp1252 encoding issues that cause
    UnicodeEncodeError when printing Unicode characters like box-drawing symbols.
    """

    def __init__(self) -> None:
        """Initialize EncodingSafeOutputHandler."""
        # Use getattr to safely handle binary streams (e.g. _io.BufferedWriter) that
        # lack an .encoding attribute — can happen when pytest redirects sys.stdout
        # during a full test suite run.
        self.terminal_encoding = getattr(sys.stdout, "encoding", None) or "utf-8"
        self.is_windows_powershell = os.name == "nt" and self.terminal_encoding.lower().startswith(
            "cp"
        )

    def safe_print(self, text: str = "") -> None:
        """Print text safely, handling encoding issues."""
        try:
            print(text, flush=True)
        except UnicodeEncodeError:
            if self.is_windows_powershell:
                # PowerShell cp1252 fallback
                safe_text = text.encode(self.terminal_encoding, errors="replace").decode(
                    self.terminal_encoding, errors="replace"
                )
            else:
                # General UTF-8 fallback
                safe_text = text.encode("utf-8", errors="replace").decode("utf-8")
            print(safe_text, flush=True)

    def format_progress(self, current: int, total: int, prefix: str = "Progress") -> str:
        """Format progress safely without Unicode box-drawing characters."""
        if self.is_windows_powershell:
            # ASCII-safe progress format
            percentage = (current / total) * 100 if total > 0 else 0
            return f"{prefix}: {current}/{total} ({percentage:.1f}%)"
        # Unicode-enabled progress format
        percentage = (current / total) * 100 if total > 0 else 0
        bar_length = 20
        filled = int(bar_length * current / total) if total > 0 else 0
        bar = "█" * filled + "░" * (bar_length - filled)
        return f"{prefix}: {bar} {current}/{total} ({percentage:.1f}%)"


class SubprocessOptimizer:
    """Optimize subprocess execution for performance and reliability.

    Implements patterns from KILO-FOOLISH guidance for:
    - Efficient subprocess management
    - Proper encoding handling
    - Interrupt forwarding
    - Performance monitoring
    """

    def __init__(self, encoding_handler: EncodingSafeOutputHandler | None = None) -> None:
        """Initialize SubprocessOptimizer with encoding_handler."""
        self.encoding_handler = encoding_handler or EncodingSafeOutputHandler()
        self.process_count = 0
        self.performance_metrics: dict[int, Any] = {}

    def run_with_progress(
        self,
        cmd: list[str],
        cwd: Path | None = None,
        show_progress: bool = True,
        timeout: int | None = None,
    ) -> subprocess.CompletedProcess:
        """Run subprocess with progress monitoring and encoding safety.

        Args:
            cmd: Command and arguments to run
            cwd: Working directory
            show_progress: Whether to show progress indicators
            timeout: Timeout in seconds

        Returns:
            CompletedProcess result

        """
        import time

        start_time = time.time()

        if show_progress:
            self.encoding_handler.safe_print(f"Starting: {' '.join(cmd)}")

        try:
            # Optimized subprocess creation with proper encoding
            creationflags = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)

            result = subprocess.run(
                cmd,
                check=False,
                cwd=str(cwd) if cwd else None,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=timeout,
                creationflags=creationflags,
            )

            elapsed = time.time() - start_time
            self.process_count += 1
            self.performance_metrics[self.process_count] = {
                "cmd": " ".join(cmd),
                "elapsed": elapsed,
                "returncode": result.returncode,
                "stdout_length": len(result.stdout) if result.stdout else 0,
                "stderr_length": len(result.stderr) if result.stderr else 0,
            }

            if show_progress:
                status = (
                    "✅ Success"
                    if result.returncode == 0
                    else f"❌ Failed (code {result.returncode})"
                )
                self.encoding_handler.safe_print(f"{status} in {elapsed:.2f}s")

            return result

        except subprocess.TimeoutExpired:
            if show_progress:
                self.encoding_handler.safe_print(f"⏰ Timeout after {timeout}s")
            raise
        except Exception as e:
            if show_progress:
                self.encoding_handler.safe_print(f"❌ Error: {e}")
            raise

    def get_performance_summary(self) -> dict[str, Any]:
        """Get performance metrics summary."""
        if not self.performance_metrics:
            return {"message": "No processes executed yet"}

        total_time = sum(m["elapsed"] for m in self.performance_metrics.values())
        avg_time = total_time / len(self.performance_metrics)
        success_count = sum(1 for m in self.performance_metrics.values() if m["returncode"] == 0)

        return {
            "total_processes": self.process_count,
            "total_time": round(total_time, 2),
            "average_time": round(avg_time, 2),
            "success_rate": round(success_count / self.process_count * 100, 1),
            "fastest": min(self.performance_metrics.values(), key=lambda x: x["elapsed"]),
            "slowest": max(self.performance_metrics.values(), key=lambda x: x["elapsed"]),
        }


def optimize_for_large_repositories(max_files: int = 1000, max_depth: int = 8) -> dict[str, Any]:
    """Provide optimization recommendations for large repository scanning.

    Based on KILO-FOOLISH performance guidance patterns.
    """
    return {
        "recommended_max_depth": max_depth,
        "recommended_max_files": max_files,
        "skip_directories": [
            ".git",
            "venv",
            "node_modules",
            ".venv",
            "dist",
            "build",
            "__pycache__",
            ".pytest_cache",
            ".tox",
            "coverage",
            ".mypy_cache",
            ".ruff_cache",
        ],
        "batch_size": 100,
        "progress_interval": 50,
        "encoding_safety": "always_use_utf8_with_replace_fallback",
        "subprocess_optimization": "use_process_groups_for_interrupt_handling",
    }


# Example usage for integration testing
if __name__ == "__main__":
    # Demonstrate encoding-safe output
    handler = EncodingSafeOutputHandler()
    handler.safe_print("Testing encoding safety with Unicode: │ ┌ ┐ └ ┘")
    handler.safe_print(handler.format_progress(75, 100, "Scan"))

    # Demonstrate subprocess optimization
    optimizer = SubprocessOptimizer(handler)

    # Test with a simple command
    try:
        result = optimizer.run_with_progress(["python", "--version"])
        handler.safe_print(f"Command output: {result.stdout.strip()}")

        # Show performance summary
        summary = optimizer.get_performance_summary()
        handler.safe_print(f"Performance summary: {summary}")

    except Exception as e:
        handler.safe_print(f"Test failed: {e}")
