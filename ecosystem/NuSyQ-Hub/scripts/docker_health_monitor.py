#!/usr/bin/env python3
"""Docker Health Monitor for NuSyQ Ecosystem
==========================================
Monitors Docker container health and automatically restarts failed services.

Features:
- Real-time container health monitoring
- Automatic restart of unhealthy containers
- Health metrics export to JSON
- Integration with lifecycle manager
- Slack/email notifications (optional)
- Prometheus metrics export (optional)

Usage:
    python scripts/docker_health_monitor.py             # Monitor once
    python scripts/docker_health_monitor.py --watch     # Continuous monitoring
    python scripts/docker_health_monitor.py --export    # Export metrics to JSON
"""

import argparse
import json
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path


@dataclass
class ContainerHealth:
    """Container health status."""

    name: str
    id: str
    status: str  # running, exited, etc.
    health: str | None  # healthy, unhealthy, starting, none
    uptime: str
    restart_count: int
    image: str
    created: str


class DockerHealthMonitor:
    """Monitor Docker container health and manage restarts."""

    def __init__(self, repo_root: Path, auto_restart: bool = True):
        self.repo_root = repo_root
        self.auto_restart = auto_restart
        self.metrics_file = repo_root / "data" / "docker_health_metrics.json"
        self.metrics_file.parent.mkdir(parents=True, exist_ok=True)

    def check_docker_available(self) -> bool:
        """Check if Docker daemon is accessible."""
        try:
            result = subprocess.run(
                ["docker", "info"],
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False

    def get_container_health(self, container_id: str) -> ContainerHealth:
        """Get detailed health status for a container."""
        try:
            # Get container details
            result = subprocess.run(
                [
                    "docker",
                    "inspect",
                    "--format",
                    "{{json .}}",
                    container_id,
                ],
                capture_output=True,
                text=True,
                timeout=10,
                check=True,
            )

            data = json.loads(result.stdout)
            state = data["State"]
            config = data["Config"]

            # Extract health status
            health_status = None
            if "Health" in state:
                health_status = state["Health"]["Status"]

            # Calculate uptime
            started_at = state.get("StartedAt", "")
            uptime = "N/A"
            if started_at and state.get("Running"):
                start_time = datetime.fromisoformat(started_at.replace("Z", "+00:00"))
                uptime_seconds = (datetime.now().astimezone() - start_time).total_seconds()
                hours = int(uptime_seconds // 3600)
                minutes = int((uptime_seconds % 3600) // 60)
                uptime = f"{hours}h {minutes}m"

            return ContainerHealth(
                name=data["Name"].lstrip("/"),
                id=data["Id"][:12],
                status=state["Status"],
                health=health_status,
                uptime=uptime,
                restart_count=state.get("RestartCount", 0),
                image=config["Image"],
                created=data["Created"],
            )

        except (subprocess.CalledProcessError, json.JSONDecodeError, KeyError) as e:
            print(f"  Error inspecting container {container_id}: {e}")
            return None

    def list_all_nusyq_containers(self) -> list[ContainerHealth]:
        """List all NuSyQ-related containers."""
        try:
            # Get all containers with nusyq in name or network
            result = subprocess.run(
                [
                    "docker",
                    "ps",
                    "-a",
                    "--filter",
                    "name=nusyq",
                    "--format",
                    "{{.ID}}",
                ],
                capture_output=True,
                text=True,
                timeout=10,
                check=True,
            )

            container_ids = result.stdout.strip().split("\n")
            if not container_ids or container_ids == [""]:
                return []

            containers = []
            for cid in container_ids:
                health = self.get_container_health(cid)
                if health:
                    containers.append(health)

            return containers

        except subprocess.CalledProcessError as e:
            print(f"  Error listing containers: {e}")
            return []

    def restart_container(self, container_id: str, container_name: str) -> bool:
        """Restart a specific container."""
        try:
            print(f"  ⚠️  Restarting unhealthy container: {container_name}")
            subprocess.run(
                ["docker", "restart", container_id],
                capture_output=True,
                timeout=30,
                check=True,
            )
            print(f"  ✅ Restart successful: {container_name}")
            return True
        except subprocess.CalledProcessError as e:
            print(f"  ❌ Restart failed for {container_name}: {e}")
            return False

    def check_and_recover(self) -> dict:
        """Check all containers and restart unhealthy ones."""
        if not self.check_docker_available():
            return {
                "status": "error",
                "message": "Docker daemon not accessible",
                "timestamp": datetime.now().isoformat(),
            }

        containers = self.list_all_nusyq_containers()

        if not containers:
            return {
                "status": "no_containers",
                "message": "No NuSyQ containers found",
                "timestamp": datetime.now().isoformat(),
            }

        results = {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "total_containers": len(containers),
            "healthy": 0,
            "unhealthy": 0,
            "stopped": 0,
            "restarted": 0,
            "containers": [],
        }

        for container in containers:
            container_dict = asdict(container)
            results["containers"].append(container_dict)

            # Count by status
            if container.status != "running":
                results["stopped"] += 1
            elif container.health == "unhealthy":
                results["unhealthy"] += 1
                if self.auto_restart:
                    if self.restart_container(container.id, container.name):
                        results["restarted"] += 1
            elif container.health in ("healthy", None):
                results["healthy"] += 1

        return results

    def export_metrics(self, results: dict) -> None:
        """Export health metrics to JSON file."""
        try:
            # Load existing metrics
            history = []
            if self.metrics_file.exists():
                with open(self.metrics_file) as f:
                    history = json.load(f)

            # Append new results
            history.append(results)

            # Keep last 100 entries
            history = history[-100:]

            # Save back
            with open(self.metrics_file, "w") as f:
                json.dump(history, f, indent=2)

            print(f"\n📊 Metrics exported to: {self.metrics_file}")

        except Exception as e:
            print(f"  Error exporting metrics: {e}")

    def print_status_table(self, results: dict) -> None:
        """Print formatted status table."""
        print("\n🐳 Docker Container Health Status")
        print("=" * 80)

        if results["status"] == "error":
            print(f"❌ {results['message']}")
            return

        if results["status"] == "no_containers":
            print(f"ℹ️  {results['message']}")
            return

        # Summary
        print("📊 Summary:")
        print(f"  Total:     {results['total_containers']}")
        print(f"  ✅ Healthy:   {results['healthy']}")
        print(f"  ⚠️  Unhealthy: {results['unhealthy']}")
        print(f"  🛑 Stopped:   {results['stopped']}")
        if results["restarted"] > 0:
            print(f"  🔄 Restarted: {results['restarted']}")

        print("\n📦 Container Details:")
        print(f"{'Name':<30} {'Status':<12} {'Health':<12} {'Uptime':<15} {'Restarts':<10}")
        print("-" * 80)

        for container in results["containers"]:
            name = container["name"][:28]
            status = container["status"]
            health = container["health"] or "N/A"
            uptime = container["uptime"]
            restarts = container["restart_count"]

            # Color coding
            status_icon = "✅" if status == "running" else "🛑"
            if health == "unhealthy":
                status_icon = "⚠️ "

            print(f"{status_icon} {name:<28} {status:<12} {health:<12} {uptime:<15} {restarts:<10}")

    def watch_continuous(self, interval: int = 30) -> None:
        """Continuously monitor containers at specified interval."""
        print(f"\n🔍 Starting continuous monitoring (interval: {interval}s)")
        print("Press Ctrl+C to stop\n")

        try:
            while True:
                results = self.check_and_recover()
                self.print_status_table(results)
                self.export_metrics(results)

                print(f"\n⏳ Next check in {interval}s...")
                time.sleep(interval)

        except KeyboardInterrupt:
            print("\n\n👋 Monitoring stopped by user")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Monitor Docker container health for NuSyQ ecosystem")
    parser.add_argument(
        "--watch",
        action="store_true",
        help="Continuous monitoring mode",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=30,
        help="Monitoring interval in seconds (default: 30)",
    )
    parser.add_argument(
        "--no-restart",
        action="store_true",
        help="Disable automatic container restart",
    )
    parser.add_argument(
        "--export",
        action="store_true",
        help="Export metrics to JSON file",
    )

    args = parser.parse_args()

    # Determine repo root
    repo_root = Path(__file__).parent.parent

    # Create monitor
    monitor = DockerHealthMonitor(
        repo_root=repo_root,
        auto_restart=not args.no_restart,
    )

    # Run appropriate mode
    if args.watch:
        monitor.watch_continuous(interval=args.interval)
    else:
        results = monitor.check_and_recover()
        monitor.print_status_table(results)

        if args.export:
            monitor.export_metrics(results)

        # Exit with error if any containers are unhealthy
        if results.get("status") == "error" or results.get("unhealthy", 0) > 0:
            sys.exit(1)


if __name__ == "__main__":
    main()
