#!/usr/bin/env python3
"""Unified cross-repository health checker.
Checks NuSyQ-Hub, SimulatedVerse, and NuSyQ in single command.
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

# Import our SimulatedVerse client
try:
    from src.integration.simulated_verse_client import SimulatedVerseClient
except ImportError:
    try:
        from integration.simulated_verse_client import SimulatedVerseClient
    except ImportError:
        SimulatedVerseClient = None


class UnifiedHealthChecker:
    """Check health across all three repositories."""

    def __init__(self) -> None:
        self.repos = {
            "NuSyQ-Hub": Path("C:/Users/keath/Desktop/Legacy/NuSyQ-Hub"),
            "SimulatedVerse": Path("C:/Users/keath/Desktop/SimulatedVerse/SimulatedVerse"),
            "NuSyQ": Path("C:/Users/keath/NuSyQ"),
        }
        self.health_report: dict[str, Any] = {}

    def check_hub_health(self) -> dict[str, Any]:
        """Check NuSyQ-Hub health."""
        hub_path = self.repos["NuSyQ-Hub"]

        health = {
            "repo": "NuSyQ-Hub",
            "path": str(hub_path),
            "exists": hub_path.exists(),
            "status": "unknown",
        }

        if not hub_path.exists():
            health["status"] = "missing"
            return health

        # Check for key indicators
        src_dir = hub_path / "src"
        scripts_dir = hub_path / "scripts"
        receipts_dir = hub_path / "state" / "receipts"

        health["components"] = {
            "src_directory": src_dir.exists(),
            "scripts_directory": scripts_dir.exists(),
            "receipts_system": receipts_dir.exists(),
        }

        # Check latest health receipt
        if receipts_dir.exists():
            diag_receipts = list((receipts_dir / "diagnostics").glob("health_*.json"))
            if diag_receipts:
                latest = max(diag_receipts, key=lambda f: f.stat().st_mtime)
                try:
                    with open(latest) as f:
                        data = json.load(f)
                        health["last_health_check"] = data.get("timestamp")
                        health["overall_health_score"] = data.get("overall_health_score")
                        health["health_grade"] = data.get("health_grade")
                except Exception:
                    pass

        health["status"] = "operational" if all(health["components"].values()) else "degraded"
        return health

    def check_simverse_health(self) -> dict[str, Any]:
        """Check SimulatedVerse health."""
        simverse_path = self.repos["SimulatedVerse"]

        health = {
            "repo": "SimulatedVerse",
            "path": str(simverse_path),
            "exists": simverse_path.exists(),
            "status": "unknown",
        }

        if not simverse_path.exists():
            health["status"] = "missing"
            return health

        # Check for key files
        package_json = simverse_path / "package.json"
        server_dir = simverse_path / "server"
        test_dir = simverse_path / "test"

        health["components"] = {
            "package_json": package_json.exists(),
            "server_directory": server_dir.exists(),
            "test_directory": test_dir.exists(),
        }

        # Try to query Culture Ship API if client available
        if SimulatedVerseClient:
            client = SimulatedVerseClient()
            api_health = client.get_health()
            health["api_status"] = api_health.get("status")

            if api_health.get("status") == "operational":
                health["api_response"] = api_health.get("response")
                health["consciousness_level"] = api_health.get("response", {}).get("consciousness_level")
        else:
            health["api_status"] = "client_unavailable"

        health["status"] = "operational" if all(health["components"].values()) else "degraded"
        return health

    def check_nusyq_health(self) -> dict[str, Any]:
        """Check NuSyQ root health."""
        nusyq_path = self.repos["NuSyQ"]

        health = {
            "repo": "NuSyQ",
            "path": str(nusyq_path),
            "exists": nusyq_path.exists(),
            "status": "unknown",
        }

        if not nusyq_path.exists():
            health["status"] = "missing"
            return health

        # Check for key components
        chatdev_dir = nusyq_path / "ChatDev"
        knowledge_base = nusyq_path / "knowledge-base.yaml"
        manifest = nusyq_path / "nusyq.manifest.yaml"

        health["components"] = {
            "chatdev": chatdev_dir.exists(),
            "knowledge_base": knowledge_base.exists(),
            "manifest": manifest.exists(),
        }

        # Check Ollama (if receipt exists)
        ollama_receipts = list((nusyq_path / "state" / "receipts" / "ollama").glob("models_*.json"))
        if ollama_receipts:
            latest = max(ollama_receipts, key=lambda f: f.stat().st_mtime)
            try:
                with open(latest) as f:
                    data = json.load(f)
                    health["ollama_status"] = data.get("status")
                    health["ollama_models"] = len(data.get("models", []))
            except Exception:
                pass

        health["status"] = "operational" if all(health["components"].values()) else "degraded"
        return health

    def run_unified_check(self) -> dict[str, Any]:
        """Run unified health check across all repos."""
        report = {
            "timestamp": datetime.now().isoformat(),
            "type": "unified_health_check",
            "repos": {},
            "summary": {},
        }

        # Check each repo
        report["repos"]["NuSyQ-Hub"] = self.check_hub_health()
        report["repos"]["SimulatedVerse"] = self.check_simverse_health()
        report["repos"]["NuSyQ"] = self.check_nusyq_health()

        # Generate summary
        operational = sum(1 for r in report["repos"].values() if r["status"] == "operational")
        degraded = sum(1 for r in report["repos"].values() if r["status"] == "degraded")
        missing = sum(1 for r in report["repos"].values() if r["status"] == "missing")

        report["summary"] = {
            "total_repos": len(self.repos),
            "operational": operational,
            "degraded": degraded,
            "missing": missing,
            "overall_status": "healthy" if operational == 3 else "needs_attention",
        }

        return report

    def save_report(self, report: dict[str, Any]) -> None:
        """Save unified health report."""
        receipt_dir = Path.cwd() / "state" / "receipts" / "unified"
        receipt_dir.mkdir(parents=True, exist_ok=True)

        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        receipt_file = receipt_dir / f"health_{timestamp_str}.json"

        with open(receipt_file, "w") as f:
            json.dump(report, f, indent=2, default=str)

        print(f"✓ Unified health receipt: {receipt_file}")

    def print_report(self, report: dict[str, Any]) -> None:
        """Print unified health report."""
        print("\n" + "=" * 80)
        print("UNIFIED CROSS-REPOSITORY HEALTH CHECK")
        print("=" * 80)
        print(f"Timestamp: {report['timestamp']}")
        print(f"\nOverall Status: {report['summary']['overall_status'].upper()}")
        print(f"  Operational: {report['summary']['operational']}/3")
        print(f"  Degraded: {report['summary']['degraded']}/3")
        print(f"  Missing: {report['summary']['missing']}/3")

        print("\n" + "-" * 80)
        print("Repository Details:")
        print("-" * 80)

        for repo_name, health in report["repos"].items():
            status_icon = {
                "operational": "✓",
                "degraded": "⚠",
                "missing": "❌",
                "unknown": "?",
            }.get(health["status"], "?")

            print(f"\n{status_icon} {repo_name} — {health['status'].upper()}")
            print(f"  Path: {health['path']}")

            if "components" in health:
                print("  Components:")
                for comp, status in health["components"].items():
                    comp_icon = "✓" if status else "❌"
                    print(f"    {comp_icon} {comp}")

            if "overall_health_score" in health:
                print(f"  Health Score: {health['overall_health_score']:.1f}% (Grade {health['health_grade']})")

            if "api_status" in health:
                api_icon = "✓" if health["api_status"] == "operational" else "❌"
                print(f"  API: {api_icon} {health['api_status']}")
                if health.get("consciousness_level"):
                    print(f"  Consciousness: {health['consciousness_level']}")

            if "ollama_status" in health:
                print(f"  Ollama: {health['ollama_status']} ({health.get('ollama_models', 0)} models)")


def main() -> None:
    """Main entry point."""
    checker = UnifiedHealthChecker()
    report = checker.run_unified_check()
    checker.print_report(report)
    checker.save_report(report)

    # Exit code based on health
    if report["summary"]["overall_status"] == "healthy":
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
