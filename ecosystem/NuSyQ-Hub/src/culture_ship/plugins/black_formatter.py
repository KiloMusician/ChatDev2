import subprocess
from typing import Any


class BlackFormatterPlugin:
    """Black code formatter plugin."""

    def __init__(self) -> None:
        """Initialize BlackFormatterPlugin."""
        self.name = "black_formatter"
        self.description = "Format Python source files using black"

    def analyze(self, targets: list[str], dry_run: bool = False) -> dict[str, Any]:
        """Check formatting with black --check."""
        cmd = ["python", "-m", "black", "--check", *targets]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=False)

            # Parse black output to count files that would be reformatted
            # Black prints to stdout in newer versions; stderr in some older versions
            output = result.stdout or result.stderr or ""
            lines = output.splitlines()
            reformat_count = sum(1 for line in lines if "would reformat" in line)

            return {
                "plugin": self.name,
                "would_reformat": reformat_count,
                "needs_formatting": reformat_count > 0,
                "dry_run": dry_run,
                "targets": targets,
            }
        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            return {"plugin": self.name, "error": str(e), "would_reformat": 0, "targets": targets}

    def fix(self, analysis: dict[str, Any], dry_run: bool = False) -> dict[str, Any]:
        """Apply black formatting."""
        if dry_run or not analysis.get("needs_formatting", False):
            return {"plugin": self.name, "formatted_files": 0, "success": True}

        targets = analysis.get("targets", []) or []
        if not targets:
            return {"plugin": self.name, "formatted_files": 0, "success": True}

        cmd = ["python", "-m", "black", *targets]
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)

        # Count formatted files from output
        output = result.stdout or result.stderr or ""
        lines = output.splitlines()
        formatted = sum(1 for line in lines if "reformatted" in line)

        return {
            "plugin": self.name,
            "formatted_files": formatted,
            "success": result.returncode == 0,
        }
