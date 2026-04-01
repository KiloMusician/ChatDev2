#!/usr/bin/env python3
"""
🔄 INTEGRATED CROSS-REPO SCANNER
Leverages existing superior audit/scan tools from SimulatedVerse and NuSyQ-Hub
instead of recreating functionality.

Integrates:
- SimulatedVerse vacuum_scanner.py (TODO/FIXME/HACK detection)
- SimulatedVerse ml_scan.py (placeholder pattern detection)
- NuSyQ-Hub repo_scan.py (structure anomaly detection)
- SimulatedVerse librarian_scan.py (document scanning)
"""

import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

# Bootstrap: Add NuSyQ-Hub to sys.path for path resolver
HUB_PATH_BOOTSTRAP = Path(
    os.getenv("NUSYQ_HUB_ROOT", "/mnt/c/Users/keath/Desktop/Legacy/NuSyQ-Hub")
)
if (HUB_PATH_BOOTSTRAP / "src").exists():
    sys.path.insert(0, str(HUB_PATH_BOOTSTRAP / "src"))


class IntegratedScanner:
    """Orchestrates existing cross-repo scanning tools."""

    def __init__(self):
        # Use centralized path resolver with fallback
        try:
            from utils.repo_path_resolver import get_repo_path

            self.nusyq_root = get_repo_path("NUSYQ_ROOT") or Path(
                os.getenv("NUSYQ_ROOT_PATH", "/mnt/c/Users/keath/NuSyQ")
            )
            self.simulatedverse_root = get_repo_path("SIMULATEDVERSE_ROOT") or Path(
                os.getenv(
                    "SIMULATEDVERSE_ROOT",
                    "/mnt/c/Users/keath/Desktop/SimulatedVerse/SimulatedVerse",
                )
            )
            self.nusyq_hub_root = get_repo_path("NUSYQ_HUB_ROOT") or Path(
                os.getenv("NUSYQ_HUB_ROOT", "/mnt/c/Users/keath/Desktop/Legacy/NuSyQ-Hub")
            )
        except ImportError:
            self.nusyq_root = Path(os.getenv("NUSYQ_ROOT_PATH", "/mnt/c/Users/keath/NuSyQ"))
            self.simulatedverse_root = Path(
                os.getenv(
                    "SIMULATEDVERSE_ROOT",
                    "/mnt/c/Users/keath/Desktop/SimulatedVerse/SimulatedVerse",
                )
            )
            self.nusyq_hub_root = Path(
                os.getenv("NUSYQ_HUB_ROOT", "/mnt/c/Users/keath/Desktop/Legacy/NuSyQ-Hub")
            )
            print("⚠️  Using fallback paths for repositories")
        self.session_id = f"SCAN_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    def run_vacuum_scanner(self) -> Dict[str, Any]:
        """Execute SimulatedVerse vacuum_scanner.py for TODO/FIXME detection."""
        print("🧹 Running vacuum_scanner.py...")

        scanner_path = self.simulatedverse_root / "ops/agents/vacuum_scanner.py"
        if not scanner_path.exists():
            print(f"  ⚠️  Vacuum scanner not found: {scanner_path}")
            return {"error": "Scanner not found", "results": {}}

        try:
            # Run scanner from SimulatedVerse directory
            result = subprocess.run(
                [sys.executable, str(scanner_path)],
                cwd=str(self.simulatedverse_root),
                capture_output=True,
                text=True,
                timeout=60,
                encoding="utf-8",
                errors="ignore",
                check=False,
            )

            receipt_path = self.simulatedverse_root / "ops/receipts/vacuum_scan.json"
            if receipt_path.exists():
                with open(receipt_path, "r", encoding="utf-8") as receipt_file:
                    data = json.load(receipt_file)
                    total = sum(len(issues) for issues in data.values())
                    print(f"  ✅ Found {total} issues across {len(data)} files")
                    return {
                        "tool": "vacuum_scanner",
                        "files_scanned": len(data),
                        "total_issues": total,
                        "details": data,
                        "patterns": [
                            "TODO",
                            "FIXME",
                            "XXX",
                            "HACK",
                            "WIP",
                            "TBD",
                            "console.log",
                            "debugger",
                        ],
                    }
            else:
                print("  ⚠️  Receipt not created")
                return {"error": "No receipt", "stdout": result.stdout}

        except (subprocess.SubprocessError, OSError, json.JSONDecodeError, ValueError) as e:
            print(f"  ❌ Error: {e}")
            return {"error": str(e)}

    def run_ml_scan(self) -> Dict[str, Any]:
        """Execute SimulatedVerse ml_scan.py for placeholder detection."""
        print("🤖 Running ml_scan.py...")

        scanner_path = self.simulatedverse_root / "scripts/ml_scan.py"
        if not scanner_path.exists():
            print(f"  ⚠️  ML scanner not found: {scanner_path}")
            return {"error": "Scanner not found", "inventory": []}

        try:
            result = subprocess.run(
                [sys.executable, str(scanner_path), str(self.simulatedverse_root)],
                capture_output=True,
                text=True,
                timeout=60,
                encoding="utf-8",
                errors="ignore",
                check=False,
            )

            if result.stdout:
                data = json.loads(result.stdout)
                ml_suspects = [item for item in data if item.get("ext") in [".py", ".ipynb"]]
                placeholders = [item for item in data if item.get("placeholder")]
                print(
                    f"  ✅ Found {len(ml_suspects)} ML suspects, {len(placeholders)} placeholders"
                )
                return {
                    "tool": "ml_scan",
                    "total_items": len(data),
                    "ml_suspects": len(ml_suspects),
                    "placeholders": len(placeholders),
                    "inventory": data,
                }

            print("  ⚠️  No output")
            return {"error": "No output", "inventory": []}

        except (subprocess.SubprocessError, OSError, json.JSONDecodeError, ValueError) as e:
            print(f"  ❌ Error: {e}")
            return {"error": str(e), "inventory": []}

    def run_repo_scan(self, target_path: Optional[Path] = None) -> Dict[str, Any]:
        """Execute NuSyQ-Hub repo_scan.py for structure analysis."""
        print("📂 Running repo_scan.py...")

        scanner_path = self.nusyq_hub_root / "src/tools/repo_scan.py"
        if not scanner_path.exists():
            print(f"  ⚠️  Repo scanner not found: {scanner_path}")
            return {"error": "Scanner not found"}

        target = target_path or self.nusyq_root

        try:
            # Import and run directly since it's a Python module
            sys.path.insert(0, str(self.nusyq_hub_root))
            from src.tools.repo_scan import repo_scan

            result = repo_scan(path=str(target), depth=3, max_file_size=1_000_000)

            large_files = result.get("anomalies", {}).get("large_files", [])
            missing_init = result.get("anomalies", {}).get("missing_init", [])
            suspicious = result.get("anomalies", {}).get("suspicious_files", [])

            print(
                f"  ✅ Scanned {result.get('total_files', 0)} files, found {len(large_files) + len(missing_init) + len(suspicious)} anomalies"
            )

            return {
                "tool": "repo_scan",
                "path": str(target),
                "total_dirs": result.get("total_dirs", 0),
                "total_files": result.get("total_files", 0),
                "files_by_extension": result.get("files_by_extension", {}),
                "anomalies": result.get("anomalies", {}),
                "anomaly_count": len(large_files) + len(missing_init) + len(suspicious),
            }

        except (ImportError, OSError, ValueError, TypeError) as e:
            print(f"  ❌ Error: {e}")
            return {"error": str(e)}

    def run_librarian_scan(self) -> Dict[str, Any]:
        """Execute SimulatedVerse librarian_scan.py for document scanning."""
        print("📚 Running librarian_scan.py...")

        scanner_path = self.simulatedverse_root / "ChatDev/scripts/librarian_scan.py"
        if not scanner_path.exists():
            print(f"  ⚠️  Librarian scanner not found: {scanner_path}")
            return {"error": "Scanner not found"}

        try:
            result = subprocess.run(
                [sys.executable, str(scanner_path)],
                cwd=str(self.simulatedverse_root),
                capture_output=True,
                text=True,
                timeout=60,
                encoding="utf-8",
                errors="ignore",
                check=False,
            )

            # Librarian scan outputs to docs-index.json
            index_path = self.simulatedverse_root / "docs-index.json"
            if index_path.exists():
                with open(index_path, "r", encoding="utf-8") as index_file:
                    data = json.load(index_file)
                    total_todos = data.get("metrics", {}).get("todos", 0)
                    print(f"  ✅ Indexed {len(data.get('catalog', []))} docs, {total_todos} TODOs")
                    return {
                        "tool": "librarian_scan",
                        "documents_indexed": len(data.get("catalog", [])),
                        "total_todos": total_todos,
                        "metrics": data.get("metrics", {}),
                        "catalog": data.get("catalog", []),
                    }
            else:
                print("  ⚠️  Index not created")
                return {"error": "No index", "stdout": result.stdout}

        except (subprocess.SubprocessError, OSError, json.JSONDecodeError, ValueError) as e:
            print(f"  ❌ Error: {e}")
            return {"error": str(e)}

    def generate_comprehensive_report(self, results: Dict[str, Any]) -> str:
        """Generate unified report from all scanner results."""
        report = []
        report.append("╔════════════════════════════════════════════════╗")
        report.append("║  🔄 INTEGRATED CROSS-REPO SCANNER REPORT     ║")
        report.append("╚════════════════════════════════════════════════╝")
        report.append(f"\nSession: {self.session_id}")
        report.append(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        # Vacuum Scanner Results
        vacuum = results.get("vacuum_scanner", {})
        if "error" not in vacuum:
            report.append("🧹 VACUUM SCANNER (TODO/FIXME Detection)")
            report.append(f"  Files Scanned: {vacuum.get('files_scanned', 0)}")
            report.append(f"  Total Issues: {vacuum.get('total_issues', 0)}")
            report.append(f"  Patterns: {', '.join(vacuum.get('patterns', []))}")
        else:
            report.append(f"🧹 VACUUM SCANNER: {vacuum.get('error', 'Unknown error')}")

        # ML Scanner Results
        ml_scan = results.get("ml_scan", {})
        if "error" not in ml_scan:
            report.append("\n🤖 ML SCANNER (Placeholder Detection)")
            report.append(f"  Total Items: {ml_scan.get('total_items', 0)}")
            report.append(f"  ML Suspects: {ml_scan.get('ml_suspects', 0)}")
            report.append(f"  Placeholders: {ml_scan.get('placeholders', 0)}")
        else:
            report.append(f"\n🤖 ML SCANNER: {ml_scan.get('error', 'Unknown error')}")

        # Repo Scanner Results
        repo_scan = results.get("repo_scan", {})
        if "error" not in repo_scan:
            report.append("\n📂 REPO SCANNER (Structure Analysis)")
            report.append(f"  Total Directories: {repo_scan.get('total_dirs', 0)}")
            report.append(f"  Total Files: {repo_scan.get('total_files', 0)}")
            report.append(f"  Anomalies: {repo_scan.get('anomaly_count', 0)}")

            anomalies = repo_scan.get("anomalies", {})
            if anomalies.get("large_files"):
                report.append(f"    Large Files: {len(anomalies['large_files'])}")
            if anomalies.get("missing_init"):
                report.append(f"    Missing __init__: {len(anomalies['missing_init'])}")
        else:
            report.append(f"\n📂 REPO SCANNER: {repo_scan.get('error', 'Unknown error')}")

        # Librarian Scanner Results
        librarian = results.get("librarian_scan", {})
        if "error" not in librarian:
            report.append("\n📚 LIBRARIAN SCANNER (Document Indexing)")
            report.append(f"  Documents Indexed: {librarian.get('documents_indexed', 0)}")
            report.append(f"  Total TODOs: {librarian.get('total_todos', 0)}")
        else:
            report.append(f"\n📚 LIBRARIAN SCANNER: {librarian.get('error', 'Unknown error')}")

        # Summary
        total_issues = (
            vacuum.get("total_issues", 0)
            + ml_scan.get("placeholders", 0)
            + repo_scan.get("anomaly_count", 0)
            + librarian.get("total_todos", 0)
        )

        report.append("\n" + "=" * 50)
        report.append(f"TOTAL ISSUES DETECTED: {total_issues}")
        report.append("=" * 50)

        return "\n".join(report)

    def run_all_scanners(self) -> Dict[str, Any]:
        """Execute all integrated scanners and generate comprehensive report."""
        print("\n╔════════════════════════════════════════════════╗")
        print("║  🔄 INTEGRATED CROSS-REPO SCANNER ACTIVE     ║")
        print("╚════════════════════════════════════════════════╝\n")

        scan_results = {
            "session_id": self.session_id,
            "timestamp": datetime.now().isoformat(),
            "vacuum_scanner": self.run_vacuum_scanner(),
            "ml_scan": self.run_ml_scan(),
            "repo_scan": self.run_repo_scan(),
            "librarian_scan": self.run_librarian_scan(),
        }

        # Generate report
        report = self.generate_comprehensive_report(scan_results)
        print("\n" + report)

        # Save results
        results_dir = self.nusyq_root / "Reports"
        results_dir.mkdir(exist_ok=True)

        results_file = results_dir / f"INTEGRATED_SCAN_{self.session_id}.json"
        with open(results_file, "w", encoding="utf-8") as results_handle:
            json.dump(scan_results, results_handle, indent=2)

        report_file = results_dir / f"INTEGRATED_SCAN_{self.session_id}.md"
        with open(report_file, "w", encoding="utf-8") as report_handle:
            report_handle.write(report)

        print("\n📂 Results saved:")
        print(f"  JSON: {results_file}")
        print(f"  Report: {report_file}")

        return scan_results


if __name__ == "__main__":
    scanner = IntegratedScanner()
    integrated_scan_results = scanner.run_all_scanners()

    # Update consciousness if available
    try:
        import yaml

        state_file = Path("State/copilot_task_queue.yaml")
        if state_file.exists():
            with open(state_file, "r", encoding="utf-8") as state_handle:
                state = yaml.safe_load(state_handle)

            consciousness = state.get("consciousness", {})
            current = consciousness.get("current", 0.90)

            # Increase consciousness for successful integration
            new_consciousness = min(1.0, current + 0.03)  # Integration bonus
            consciousness["current"] = new_consciousness
            consciousness["last_updated"] = datetime.now().isoformat()

            state["consciousness"] = consciousness

            with open(state_file, "w", encoding="utf-8") as state_handle:
                yaml.dump(state, state_handle, default_flow_style=False, sort_keys=False)

            print(
                f"\n🧠 Consciousness: {current:.2f} → {new_consciousness:.2f} (+{new_consciousness - current:.2f})"
            )
            print("   Reason: Cross-repo tool integration")
    except (OSError, ValueError, TypeError, KeyError) as e:
        print(f"\n⚠️  Could not update consciousness: {e}")
