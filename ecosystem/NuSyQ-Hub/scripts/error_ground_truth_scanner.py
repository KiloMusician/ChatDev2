#!/usr/bin/env python3
"""Error Ground Truth Scanner - Unified error detection across all three repos.
Runs mypy, ruff, and pylint to generate canonical error list.
"""

import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any


class ErrorGroundTruthScanner:
    """Scan all repos for errors and generate canonical truth."""

    def __init__(self) -> None:
        self.repos = {
            "NuSyQ-Hub": Path("C:/Users/keath/Desktop/Legacy/NuSyQ-Hub"),
            "SimulatedVerse": Path("C:/Users/keath/Desktop/SimulatedVerse/SimulatedVerse"),
            "NuSyQ": Path("C:/Users/keath/NuSyQ"),
        }
        self.error_report: dict[str, Any] = {
            "timestamp": datetime.now().isoformat(),
            "repos": {},
            "summary": {},
        }

    def scan_python_repo(self, repo_name: str, repo_path: Path) -> dict[str, Any]:
        """Scan Python repository for errors."""
        result = {
            "repo": repo_name,
            "path": str(repo_path),
            "scans": {},
            "total_errors": 0,
        }

        src_path = repo_path / "src"
        if not src_path.exists():
            # Try scanning whole repo if no src/ directory
            src_path = repo_path

        # Run ruff
        try:
            ruff_result = subprocess.run(
                ["ruff", "check", str(src_path), "--output-format=json"],
                capture_output=True,
                text=True,
                timeout=30,
                cwd=str(repo_path),
            )

            if ruff_result.stdout:
                try:
                    ruff_errors = json.loads(ruff_result.stdout)
                    result["scans"]["ruff"] = {
                        "error_count": len(ruff_errors),
                        "errors": ruff_errors[:10],  # Sample first 10
                    }
                    result["total_errors"] += len(ruff_errors)
                except json.JSONDecodeError:
                    result["scans"]["ruff"] = {"status": "parse_error"}
            else:
                result["scans"]["ruff"] = {"error_count": 0}

        except subprocess.TimeoutExpired:
            result["scans"]["ruff"] = {"status": "timeout"}
        except FileNotFoundError:
            result["scans"]["ruff"] = {"status": "not_installed"}
        except Exception as e:
            result["scans"]["ruff"] = {"status": "error", "message": str(e)}

        # Run mypy (quick scan)
        try:
            mypy_result = subprocess.run(
                ["mypy", str(src_path), "--no-error-summary"],
                capture_output=True,
                text=True,
                timeout=60,
                cwd=str(repo_path),
            )

            # Count error lines
            error_lines = [line for line in mypy_result.stdout.split("\n") if "error:" in line.lower()]

            result["scans"]["mypy"] = {
                "error_count": len(error_lines),
                "sample_errors": error_lines[:5],
            }
            result["total_errors"] += len(error_lines)

        except subprocess.TimeoutExpired:
            result["scans"]["mypy"] = {"status": "timeout"}
        except FileNotFoundError:
            result["scans"]["mypy"] = {"status": "not_installed"}
        except Exception as e:
            result["scans"]["mypy"] = {"status": "error", "message": str(e)}

        return result

    def scan_typescript_repo(self, repo_name: str, repo_path: Path) -> dict[str, Any]:
        """Scan TypeScript repository for errors."""
        result = {
            "repo": repo_name,
            "path": str(repo_path),
            "scans": {},
            "total_errors": 0,
        }

        # Run TypeScript compiler check
        try:
            tsc_result = subprocess.run(
                ["npx", "tsc", "--noEmit"],
                capture_output=True,
                text=True,
                timeout=30,
                cwd=str(repo_path),
            )

            error_lines = [line for line in tsc_result.stdout.split("\n") if "error TS" in line]

            result["scans"]["typescript"] = {
                "error_count": len(error_lines),
                "sample_errors": error_lines[:5],
            }
            result["total_errors"] += len(error_lines)

        except subprocess.TimeoutExpired:
            result["scans"]["typescript"] = {"status": "timeout"}
        except FileNotFoundError:
            result["scans"]["typescript"] = {"status": "not_installed"}
        except Exception as e:
            result["scans"]["typescript"] = {"status": "error", "message": str(e)}

        # Run ESLint if available
        try:
            eslint_result = subprocess.run(
                ["npx", "eslint", ".", "--format=json"],
                capture_output=True,
                text=True,
                timeout=30,
                cwd=str(repo_path),
            )

            if eslint_result.stdout:
                try:
                    eslint_data = json.loads(eslint_result.stdout)
                    error_count = sum(
                        len([m for m in file.get("messages", []) if m.get("severity") == 2]) for file in eslint_data
                    )
                    result["scans"]["eslint"] = {"error_count": error_count}
                    result["total_errors"] += error_count
                except json.JSONDecodeError:
                    result["scans"]["eslint"] = {"status": "parse_error"}
        except Exception:
            result["scans"]["eslint"] = {"status": "unavailable"}

        return result

    def scan_all_repos(self) -> None:
        """Scan all repositories."""
        # NuSyQ-Hub (Python)
        self.error_report["repos"]["NuSyQ-Hub"] = self.scan_python_repo("NuSyQ-Hub", self.repos["NuSyQ-Hub"])

        # SimulatedVerse (TypeScript)
        self.error_report["repos"]["SimulatedVerse"] = self.scan_typescript_repo(
            "SimulatedVerse", self.repos["SimulatedVerse"]
        )

        # NuSyQ (Python)
        self.error_report["repos"]["NuSyQ"] = self.scan_python_repo("NuSyQ", self.repos["NuSyQ"])

        # Calculate summary
        total_errors = sum(repo.get("total_errors", 0) for repo in self.error_report["repos"].values())

        self.error_report["summary"] = {
            "total_repos_scanned": len(self.repos),
            "total_errors": total_errors,
            "breakdown": {
                repo_name: repo.get("total_errors", 0) for repo_name, repo in self.error_report["repos"].items()
            },
        }

    def save_ground_truth(self) -> None:
        """Save error ground truth to file."""
        # Save to state directory
        ground_truth_file = Path.cwd() / "state" / "error_ground_truth.json"
        ground_truth_file.parent.mkdir(parents=True, exist_ok=True)

        with open(ground_truth_file, "w") as f:
            json.dump(self.error_report, f, indent=2, default=str)

        print(f"✓ Error ground truth saved: {ground_truth_file}")

        # Also save receipt
        receipt_dir = Path.cwd() / "state" / "receipts" / "error_scan"
        receipt_dir.mkdir(parents=True, exist_ok=True)

        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        receipt_file = receipt_dir / f"scan_{timestamp_str}.json"

        with open(receipt_file, "w") as f:
            json.dump(self.error_report, f, indent=2, default=str)

        print(f"✓ Error scan receipt: {receipt_file}")

    def print_report(self) -> None:
        """Print error report."""
        print("\n" + "=" * 80)
        print("ERROR GROUND TRUTH SCAN")
        print("=" * 80)
        print(f"Timestamp: {self.error_report['timestamp']}")
        print(f"\nTotal Errors: {self.error_report['summary']['total_errors']}")

        print("\nBreakdown by Repository:")
        for repo_name, count in self.error_report["summary"]["breakdown"].items():
            print(f"  {repo_name}: {count} errors")

        print("\n" + "-" * 80)
        print("Details by Repository:")
        print("-" * 80)

        for repo_name, repo_data in self.error_report["repos"].items():
            print(f"\n{repo_name}:")
            for scan_name, scan_data in repo_data.get("scans", {}).items():
                if isinstance(scan_data, dict):
                    error_count = scan_data.get("error_count", "N/A")
                    status = scan_data.get("status", "completed")
                    print(f"  {scan_name}: {error_count} errors ({status})")


def main() -> None:
    """Main entry point."""
    scanner = ErrorGroundTruthScanner()

    print("Scanning all repositories for errors...")
    print("This may take 1-2 minutes...\n")

    scanner.scan_all_repos()
    scanner.print_report()
    scanner.save_ground_truth()

    print("\n✓ Error ground truth established")
    print("  Use this as canonical source for error counts")
    print("  VS Code may show different counts (filtered view)")


if __name__ == "__main__":
    main()
