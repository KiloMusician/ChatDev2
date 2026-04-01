#!/usr/bin/env python3
"""Background Process Inventory
Discovers and catalogs all dormant/running systems across the ecosystem.
"""

import json
import subprocess
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass
class ServiceDefinition:
    """Definition of a background service."""

    name: str
    type: str  # python, node, docker, powershell
    entry_point: str
    port: int | None = None
    auto_start: bool = False
    critical: bool = False
    repo: str = "NuSyQ-Hub"
    description: str = ""


# Comprehensive service catalog
KNOWN_SERVICES = [
    # Python Services - NuSyQ-Hub
    ServiceDefinition(
        name="Autonomous Monitor",
        type="python",
        entry_point="scripts/autonomous_monitor.py",
        auto_start=False,
        critical=False,
        description="Meta-agent for continuous system monitoring",
    ),
    ServiceDefinition(
        name="Auto Cycle",
        type="python",
        entry_point="scripts/start_nusyq.py auto_cycle --iterations=0",
        auto_start=False,
        critical=False,
        description="Continuous PU processing and cultivation",
    ),
    ServiceDefinition(
        name="Quest Replay Engine",
        type="python",
        entry_point="src/tools/quest_replay_engine.py",
        auto_start=False,
        critical=False,
        description="Learning from quest patterns",
    ),
    ServiceDefinition(
        name="Metrics Dashboard Builder",
        type="python",
        entry_point="src/tools/cultivation_metrics.py",
        auto_start=False,
        critical=False,
        description="Real-time metrics aggregation",
    ),
    # Node Services - NuSyQ-Hub
    ServiceDefinition(
        name="Modular Window Server",
        type="node",
        entry_point="web/modular-window-server/server.js",
        port=3001,
        auto_start=False,
        critical=False,
        description="Windowing system API",
    ),
    # Docker Services - NuSyQ-Hub
    ServiceDefinition(
        name="Observability Stack",
        type="docker",
        entry_point="dev/observability/docker-compose.observability.yml",
        port=16686,  # Jaeger UI
        auto_start=False,
        critical=False,
        description="OpenTelemetry Collector + Jaeger",
    ),
    ServiceDefinition(
        name="Agent Services",
        type="docker",
        entry_point="deploy/docker-compose.agents.yml",
        auto_start=False,
        critical=False,
        description="Containerized AI agents",
    ),
    # Node Services - SimulatedVerse
    ServiceDefinition(
        name="SimulatedVerse API",
        type="node",
        entry_point="server.js",
        port=5002,
        auto_start=False,
        critical=False,
        repo="SimulatedVerse",
        description="Express API server",
    ),
    ServiceDefinition(
        name="SimulatedVerse React",
        type="node",
        entry_point="npm start",
        port=3000,
        auto_start=False,
        critical=False,
        repo="SimulatedVerse",
        description="React dev server",
    ),
    # PowerShell Services - NuSyQ Root
    ServiceDefinition(
        name="NuSyQ Orchestrator",
        type="powershell",
        entry_point="NuSyQ.Orchestrator.ps1",
        auto_start=False,
        critical=True,
        repo="NuSyQ",
        description="Root orchestration script",
    ),
    ServiceDefinition(
        name="Ecosystem Sentinel",
        type="powershell",
        entry_point="scripts/ecosystem_startup_sentinel.ps1",
        auto_start=True,
        critical=True,
        repo="NuSyQ",
        description="Auto-start Ollama and core services",
    ),
    # AI Services - NuSyQ Root
    ServiceDefinition(
        name="Ollama",
        type="service",
        entry_point="ollama serve",
        port=11434,
        auto_start=True,
        critical=True,
        repo="NuSyQ",
        description="Local LLM inference (37.5GB models)",
    ),
    ServiceDefinition(
        name="ChatDev Agents",
        type="python",
        entry_point="ChatDev/run.py",
        auto_start=False,
        critical=False,
        repo="NuSyQ",
        description="14 AI agent system",
    ),
]


def check_port(port: int) -> bool:
    """Check if a port is in use."""
    try:
        result = subprocess.run(
            f'powershell -Command "Get-NetTCPConnection -LocalPort {port} -ErrorAction SilentlyContinue"',
            shell=True,
            capture_output=True,
            text=True,
            timeout=5,
        )
        return bool(result.stdout.strip())
    except Exception:
        return False


def check_docker_service(compose_file: str) -> dict[str, Any]:
    """Check if a docker-compose service is running."""
    try:
        result = subprocess.run(
            f'docker-compose -f "{compose_file}" ps --services --filter "status=running"',
            shell=True,
            capture_output=True,
            text=True,
            timeout=10,
            cwd=Path(__file__).parents[1],
        )
        services = [s.strip() for s in result.stdout.split("\n") if s.strip()]
        return {"running": len(services) > 0, "services": services}
    except Exception as e:
        return {"running": False, "error": str(e)}


def inventory_services() -> dict[str, Any]:
    """Create comprehensive service inventory."""
    inventory = {
        "generated_at": datetime.now().isoformat(),
        "repos": {"NuSyQ-Hub": {}, "SimulatedVerse": {}, "NuSyQ": {}},
        "total_services": len(KNOWN_SERVICES),
        "running_services": 0,
        "auto_start_services": [s.name for s in KNOWN_SERVICES if s.auto_start],
        "critical_services": [s.name for s in KNOWN_SERVICES if s.critical],
    }

    for service in KNOWN_SERVICES:
        status = {**asdict(service), "running": False, "port_active": None}

        # Check port if applicable
        if service.port:
            status["port_active"] = check_port(service.port)
            if status["port_active"]:
                status["running"] = True
                inventory["running_services"] += 1

        # Check docker if applicable
        if service.type == "docker":
            docker_status = check_docker_service(service.entry_point)
            status["docker_info"] = docker_status
            if docker_status.get("running"):
                status["running"] = True
                inventory["running_services"] += 1

        inventory["repos"][service.repo][service.name] = status

    return inventory


def main():
    """Generate and save service inventory."""
    print("🔍 Background Process Inventory - Scanning...")

    inventory = inventory_services()

    # Save to JSON
    output_path = (
        Path(__file__).parents[1]
        / "state"
        / "reports"
        / f"service_inventory_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(inventory, f, indent=2)

    # Print summary
    print("\n📊 Service Inventory Summary")
    print("=" * 60)
    print(f"Total Services: {inventory['total_services']}")
    print(f"Running Services: {inventory['running_services']}")
    print(f"Auto-start Services: {len(inventory['auto_start_services'])}")
    print(f"Critical Services: {len(inventory['critical_services'])}")

    print("\n🔄 Auto-start Services:")
    for svc in inventory["auto_start_services"]:
        print(f"  - {svc}")

    print("\n⚠️  Critical Services:")
    for svc in inventory["critical_services"]:
        print(f"  - {svc}")

    print(f"\n✅ Inventory saved: {output_path}")

    # Check for orphaned processes
    print("\n🔍 Checking for orphaned processes...")
    try:
        result = subprocess.run(
            'tasklist /FI "IMAGENAME eq python.exe" /FO CSV /NH',
            shell=True,
            capture_output=True,
            text=True,
            timeout=10,
        )
        python_procs = [line for line in result.stdout.split("\n") if line.strip()]
        if len(python_procs) > 3:  # More than a few expected processes
            print(f"  ⚠️  Found {len(python_procs)} Python processes - may have orphans")
        else:
            print(f"  ✅ Process count normal ({len(python_procs)} Python processes)")
    except Exception as e:
        print(f"  ❌ Could not check processes: {e}")


if __name__ == "__main__":
    main()
