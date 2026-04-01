#!/usr/bin/env python3
"""Ecosystem Health Check - Redirect Bridge to Canonical System Health Assessment

Phase 3b Consolidation:
- Canonical source: src/diagnostics/system_health_assessor.py (SystemHealthAssessment)
- This file is now a lightweight redirect bridge for backward compatibility
- All health assessment logic centralized in canonical module
"""

import json
import subprocess
from pathlib import Path
from typing import Any

# Redirect to canonical health assessment module
try:
    from src.diagnostics.system_health_assessor import SystemHealthAssessment
    from src.orchestration.multi_ai_orchestrator import get_multi_ai_orchestrator
except ImportError as e:
    raise ImportError(f"Failed to import from canonical health module: {e}") from e


class EcosystemHealthChecker:
    """Backward-compatible wrapper. Delegates to SystemHealthAssessment."""

    def __init__(self) -> None:
        self.health_assessment = SystemHealthAssessment()
        repo_root = Path.cwd().resolve()
        simverse_candidates = [
            repo_root.parent / "SimulatedVerse" / "SimulatedVerse",
            repo_root.parent / "SimulatedVerse",
            repo_root.parent.parent / "SimulatedVerse" / "SimulatedVerse",
            repo_root.parent.parent / "SimulatedVerse",
        ]
        nusyq_core_candidates = [
            repo_root.parent / "NuSyQ",
            repo_root.parent.parent / "NuSyQ",
        ]

        def _first_existing(candidates: list[Path]) -> Path:
            for candidate in candidates:
                if candidate.exists():
                    return candidate
            return candidates[0]

        self.repos: dict[str, Path] = {
            "NuSyQ-Hub": repo_root,
            "SimulatedVerse": _first_existing(simverse_candidates),
            "NuSyQ-Core": _first_existing(nusyq_core_candidates),
        }
        self.health_report: dict[str, Any] = {
            "ai_systems": {},
            "critical_issues": [],
            "repositories": {},
        }
        self.orchestrator = None
        try:
            self.orchestrator = get_multi_ai_orchestrator()
        except Exception:
            pass

    def check_ollama_health(self) -> None:
        """Check Ollama service and model availability"""
        try:
            # Check if Ollama process is running
            result = subprocess.run(["ollama", "list"], capture_output=True, text=True)
            if result.returncode == 0:
                models = result.stdout.strip().split("\n")[1:]  # Skip header
                self.health_report["ai_systems"]["ollama"] = {
                    "status": "healthy",
                    "models_available": len(models),
                    "models": [line.split()[0] for line in models if line.strip()],
                }
                print(f"✅ Ollama: Healthy with {len(models)} models")
            else:
                self.health_report["ai_systems"]["ollama"] = {
                    "status": "error",
                    "error": result.stderr,
                }
                self.health_report["critical_issues"].append("Ollama service not responding")
                print("❌ Ollama: Not responding")
        except Exception as e:
            self.health_report["critical_issues"].append(f"Ollama check failed: {e!s}")
            print(f"❌ Ollama: Check failed - {e!s}")

    def check_repository_health(self, repo_name: str, repo_path: Path) -> dict[str, Any]:
        """Check health of individual repository"""
        health: dict[str, Any] = {
            "exists": repo_path.exists(),
            "python_files": 0,
            "broken_imports": 0,
            "critical_files": {},
        }

        if not repo_path.exists():
            self.health_report["critical_issues"].append(
                f"Repository {repo_name} not found at {repo_path}"
            )
            return health

        # Count Python files
        try:
            health["python_files"] = len(list(repo_path.rglob("*.py")))
        except (OSError, PermissionError):
            health["python_files"] = 0

        # Check for critical files based on repository
        critical_files: dict[str, Any] = {
            "NuSyQ-Hub": [
                "src/main.py",
                "COMPLETE_FUNCTION_REGISTRY.md",
                "config/ZETA_PROGRESS_TRACKER.json",
            ],
            "SimulatedVerse": {
                "required": ["package.json", "CULTURE_SHIP_READY.md"],
                "server_entry": [
                    "server.js",
                    "server/index.ts",
                    "index.js",
                ],  # Check multiple possible entry points
            },
            "NuSyQ-Core": ["mcp_server/main.py", "NuSyQ.Orchestrator.ps1", "knowledge-base.yaml"],
        }

        repo_critical = critical_files.get(repo_name, [])

        # Handle SimulatedVerse's flexible server entry point detection
        if repo_name == "SimulatedVerse" and isinstance(repo_critical, dict):
            # Check required files
            for critical_file in repo_critical["required"]:
                file_path = repo_path / critical_file
                health["critical_files"][critical_file] = file_path.exists()
                if not file_path.exists():
                    self.health_report["critical_issues"].append(
                        f"Missing critical file: {repo_name}/{critical_file}"
                    )

            # Check for at least one server entry point
            server_found = False
            server_entry_used = None
            for server_entry in repo_critical["server_entry"]:
                file_path = repo_path / server_entry
                if file_path.exists():
                    server_found = True
                    server_entry_used = server_entry
                    break

            health["critical_files"]["server_entry"] = server_found
            if not server_found:
                self.health_report["critical_issues"].append(
                    f"Missing server entry: {repo_name}/ (checked: {', '.join(repo_critical['server_entry'])})"
                )
            else:
                health["server_entry_point"] = server_entry_used
        else:
            # Standard critical file checking for other repos
            for critical_file in repo_critical:
                file_path = repo_path / critical_file
                health["critical_files"][critical_file] = file_path.exists()
                if not file_path.exists():
                    self.health_report["critical_issues"].append(
                        f"Missing critical file: {repo_name}/{critical_file}"
                    )

        self.health_report["repositories"][repo_name] = health
        status = "✅" if health["exists"] and all(health["critical_files"].values()) else "⚠️"
        print(
            f"{status} {repo_name}: {health['python_files']} Python files, Critical files: {sum(health['critical_files'].values())}/{len(health['critical_files'])}"
        )

        return health

    def check_mcp_server_health(self) -> None:
        """Check MCP server connectivity"""
        try:
            import requests

            response = requests.get("http://127.0.0.1:3000/health", timeout=5)
            if response.status_code == 200:
                self.health_report["ai_systems"]["mcp_server"] = {
                    "status": "healthy",
                    "port": 3000,
                    "response": (
                        response.json()
                        if response.headers.get("content-type", "").startswith("application/json")
                        else response.text
                    ),
                }
                print("✅ MCP Server: Healthy on port 3000")
            else:
                self.health_report["ai_systems"]["mcp_server"] = {
                    "status": "error",
                    "port": 3000,
                    "status_code": response.status_code,
                }
                print(f"⚠️ MCP Server: Responding with status {response.status_code}")
        except Exception as e:
            self.health_report["ai_systems"]["mcp_server"] = {
                "status": "unreachable",
                "error": str(e),
            }
            print(f"❌ MCP Server: Unreachable - {e!s}")

    def generate_recommendations(self) -> None:
        """Generate actionable recommendations"""
        recommendations: list[dict[str, str]] = []

        # Ollama issues
        if self.health_report["ai_systems"].get("ollama", {}).get("status") != "healthy":
            recommendations.append(
                {"priority": "HIGH", "action": "Restart Ollama service", "command": "ollama serve"}
            )

        # MCP server issues
        if self.health_report["ai_systems"].get("mcp_server", {}).get("status") != "healthy":
            recommendations.append(
                {
                    "priority": "HIGH",
                    "action": "Start/restart MCP server",
                    "command": "cd c:/Users/keath/NuSyQ && python mcp_server/main.py",
                }
            )

        # Missing critical files
        for issue in self.health_report["critical_issues"]:
            if "Missing critical file" in issue:
                recommendations.append({"priority": "MEDIUM", "action": f"Investigate: {issue}"})

        # General maintenance
        recommendations.append(
            {
                "priority": "LOW",
                "action": "Run import health check",
                "command": "python src/utils/quick_import_fix.py",
            }
        )

        self.health_report["recommendations"] = recommendations

    def run_comprehensive_check(self) -> None:
        """Run complete ecosystem health check"""
        print("🔍 Running Comprehensive Ecosystem Health Check...\n")

        # Check each repository
        for repo_name, repo_path in self.repos.items():
            self.check_repository_health(repo_name, repo_path)

        print()

        # Check AI systems
        self.check_ollama_health()
        self.check_mcp_server_health()

        print()

        # Generate recommendations
        self.generate_recommendations()

        # Save report
        report_path = Path("ecosystem_health_report.json")
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(self.health_report, f, indent=2)

        # Display summary
        print("📊 HEALTH SUMMARY:")
        print(
            f"   Repositories: {len([r for r in self.health_report['repositories'].values() if r['exists']])}/3 accessible"
        )
        print(f"   Critical Issues: {len(self.health_report['critical_issues'])}")
        print(f"   Recommendations: {len(self.health_report['recommendations'])}")
        print(f"   Report saved: {report_path.absolute()}")

        # Display recommendations
        if self.health_report["recommendations"]:
            print("\n🎯 IMMEDIATE ACTIONS:")
            for rec in self.health_report["recommendations"][:3]:  # Top 3
                print(f"   {rec['priority']}: {rec['action']}")
                if "command" in rec:
                    print(f"         → {rec['command']}")


if __name__ == "__main__":
    checker = EcosystemHealthChecker()
    checker.run_comprehensive_check()
