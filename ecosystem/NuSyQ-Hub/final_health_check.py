#!/usr/bin/env python3
"""Final Ecosystem Health Check"""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import requests

# Fix Windows console encoding
if sys.platform == "win32":
    reconfigure = getattr(sys.stdout, "reconfigure", None)
    if callable(reconfigure):
        reconfigure(encoding="utf-8")


def check_health():
    """Comprehensive health check"""
    print("=" * 70)
    print(" NUSYQ-HUB ECOSYSTEM HEALTH CHECK")
    print(" " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("=" * 70)

    health_report: dict[str, Any] = {"timestamp": datetime.now().isoformat(), "components": {}}

    # 1. Check Ollama
    print("\n[*] Checking Ollama...")
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get("models", [])
            health_report["components"]["ollama"] = {
                "status": "OPERATIONAL",
                "models_count": len(models),
                "models": [m["name"] for m in models],
            }
            print(f"[OK] Ollama: OPERATIONAL with {len(models)} models")
        else:
            health_report["components"]["ollama"] = {
                "status": "ERROR",
                "code": response.status_code,
            }
            print(f"[ERROR] Ollama responded with status {response.status_code}")
    except Exception as e:
        health_report["components"]["ollama"] = {"status": "UNAVAILABLE", "error": str(e)}
        print(f"[ERROR] Ollama unavailable: {e}")

    # 2. Check ChatDev
    print("\n[*] Checking ChatDev...")

    # Use centralized path resolver with fallback
    try:
        sys.path.insert(0, str(Path(__file__).parent / "src"))
        from utils.repo_path_resolver import get_repo_path

        # ChatDev is typically in same parent as NuSyQ-Hub
        hub_root = get_repo_path("NUSYQ_HUB_ROOT")
        chatdev_path = hub_root.parent / "ChatDev_CORE" / "ChatDev-main"
    except ImportError:
        chatdev_path = Path("C:/Users/keath/Desktop/Legacy/ChatDev_CORE/ChatDev-main")
        print("⚠️  Using fallback path for ChatDev")

    if chatdev_path.exists():
        health_report["components"]["chatdev"] = {
            "status": "CONFIGURED",
            "path": str(chatdev_path),
            "exists": True,
        }
        print(f"[OK] ChatDev: CONFIGURED at {chatdev_path}")
    else:
        health_report["components"]["chatdev"] = {
            "status": "NOT_FOUND",
            "path": str(chatdev_path),
            "exists": False,
        }
        print(f"[ERROR] ChatDev not found at {chatdev_path}")

    # 3. Check Multi-AI Orchestrator
    print("\n[*] Checking Multi-AI Orchestrator...")
    try:
        sys.path.insert(0, str(Path(__file__).parent))
        from src.orchestration.unified_ai_orchestrator import MultiAIOrchestrator

        orchestrator = MultiAIOrchestrator()
        systems_count = len(orchestrator.ai_systems)
        systems_list = list(orchestrator.ai_systems.keys())

        health_report["components"]["multi_ai_orchestrator"] = {
            "status": "OPERATIONAL",
            "systems_count": systems_count,
            "systems": systems_list,
        }
        print(f"[OK] Multi-AI Orchestrator: OPERATIONAL with {systems_count} systems")
        print(f"     Registered: {', '.join(systems_list)}")
    except Exception as e:
        health_report["components"]["multi_ai_orchestrator"] = {"status": "ERROR", "error": str(e)}
        print(f"[ERROR] Multi-AI Orchestrator: {e}")

    # 4. Check Repository Structure
    print("\n[*] Checking Repository Structure...")
    repo_root = Path(__file__).parent
    critical_dirs = ["src", "config", "docs"]
    dirs_status = {}

    for dir_name in critical_dirs:
        dir_path = repo_root / dir_name
        dirs_status[dir_name] = dir_path.exists()

    health_report["components"]["repository"] = {
        "status": "OK" if all(dirs_status.values()) else "INCOMPLETE",
        "critical_directories": dirs_status,
    }

    for dir_name, exists in dirs_status.items():
        status = "OK" if exists else "MISSING"
        print(f"[{status}] Directory '{dir_name}': {'exists' if exists else 'missing'}")

    # 5. Check Bootstrap Report
    print("\n[*] Checking Bootstrap Report...")
    bootstrap_report = repo_root / "bootstrap_report.json"
    if bootstrap_report.exists():
        with open(bootstrap_report) as f:
            bootstrap_data = json.load(f)

        health_report["components"]["bootstrap"] = {
            "status": "COMPLETE",
            "report_exists": True,
            "task_id": bootstrap_data.get("submitted_task_id"),
        }
        print("[OK] Bootstrap Report: EXISTS")
        print(f"     Task ID: {bootstrap_data.get('submitted_task_id')}")
    else:
        health_report["components"]["bootstrap"] = {"status": "NOT_FOUND", "report_exists": False}
        print("[WARN] Bootstrap Report: NOT FOUND")

    # Calculate Overall Health
    print("\n" + "=" * 70)
    print(" HEALTH SUMMARY")
    print("=" * 70)

    component_statuses = [
        comp.get("status", "UNKNOWN") for comp in health_report["components"].values()
    ]

    operational_count = sum(
        1
        for status in component_statuses
        if status in ["OPERATIONAL", "CONFIGURED", "COMPLETE", "OK"]
    )
    total_count = len(component_statuses)
    health_score = (operational_count / total_count) * 100 if total_count > 0 else 0

    health_report["overall"] = {
        "health_score": health_score,
        "operational_components": operational_count,
        "total_components": total_count,
        "status": (
            "OPERATIONAL"
            if health_score >= 80
            else "DEGRADED" if health_score >= 50 else "CRITICAL"
        ),
    }

    print(f"\nHealth Score: {health_score:.1f}%")
    print(f"Operational Components: {operational_count}/{total_count}")
    print(f"Overall Status: {health_report['overall']['status']}")

    # Save health report
    report_path = repo_root / "final_health_report.json"
    with open(report_path, "w") as f:
        json.dump(health_report, f, indent=2)

    print(f"\n[OK] Health report saved to: {report_path}")

    return health_report


if __name__ == "__main__":
    report = check_health()

    print("\n" + "=" * 70)
    if report["overall"]["health_score"] >= 80:
        print(" ECOSYSTEM HEALTH: EXCELLENT")
        print(" All critical systems operational")
    elif report["overall"]["health_score"] >= 50:
        print(" ECOSYSTEM HEALTH: GOOD")
        print(" Most systems operational, some attention needed")
    else:
        print(" ECOSYSTEM HEALTH: NEEDS ATTENTION")
        print(" Several systems require configuration")
    print("=" * 70)
