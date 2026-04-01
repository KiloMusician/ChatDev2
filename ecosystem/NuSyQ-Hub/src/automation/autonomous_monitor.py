"""Autonomous Monitor - Continuous Repository Watching & Auto-Auditing.

Features:
- File system watcher for repository changes
- Automatic theater audits every N minutes (configurable)
- PU submission to Unified Queue
- Human approval hooks for discovered tasks
- Performance metrics and logging
- **NEW**: Sector-awareness and configuration gap detection
- **NEW**: Integration with ZETA tracker and quest system

[OmniTag]
{
    "purpose": "Autonomous repository monitoring with sector-aware gap detection",
    "dependencies": ["unified_pu_queue", "simulatedverse_async_bridge", "sector_definitions.yaml"],
    "context": "Continuous discovery of configuration gaps and missing components",
    "evolution_stage": "enhanced_v2"
}
[/OmniTag]
"""

import importlib
import json
import logging
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

yaml: Any | None
YAMLError: type[Exception]
try:
    yaml = importlib.import_module("yaml")
    error_cls = getattr(yaml, "YAMLError", Exception)
    YAMLError = (
        error_cls if isinstance(error_cls, type) and issubclass(error_cls, Exception) else Exception
    )
except ImportError:
    yaml = None
    YAMLError = Exception

# Add NuSyQ-Hub src to path
HUB_PATH = Path(__file__).parent.parent.parent
sys.path.insert(0, str(HUB_PATH / "src"))

logger = logging.getLogger(__name__)

try:
    from automation.unified_pu_queue import PU, UnifiedPUQueue
except ImportError:
    logger.info("Error: unified_pu_queue not found")
    UnifiedPUQueue = None
    PU = None

try:
    from integration.simulatedverse_unified_bridge import SimulatedVerseBridge
except ImportError:
    logger.info("Warning: SimulatedVerseBridge not found")
    SimulatedVerseBridge = None

try:
    from healing.quantum_problem_resolver import QuantumProblemResolver
except ImportError:
    logger.info("Warning: QuantumProblemResolver not found")
    QuantumProblemResolver = None

try:
    from utils.repo_path_resolver import get_repo_path
except ImportError:  # pragma: no cover - fallback for standalone runs
    get_repo_path = None


class AutonomousMonitor:
    """Continuously monitor repository and trigger autonomous actions.

    **Enhanced v2.0**: Sector-awareness and configuration gap detection
    """

    def __init__(self, audit_interval: int = 1800, enable_sector_awareness: bool = True) -> None:
        """Initialize monitor.

        Args:
            audit_interval: Seconds between automatic audits (default: 1800 = 30min)
            enable_sector_awareness: Enable sector-based gap detection (default: True)

        """
        self.audit_interval = audit_interval
        self.last_audit = datetime.min
        self.config_file = HUB_PATH / "data" / "autonomous_monitor_config.json"
        self.metrics_file = HUB_PATH / "data" / "autonomous_monitor_metrics.json"

        # Initialize queue and bridge
        self.queue = UnifiedPUQueue() if UnifiedPUQueue else None

        sv_path = self._resolve_simulatedverse_path()
        self.sv_bridge = None
        if SimulatedVerseBridge and sv_path.exists():
            self.sv_bridge = SimulatedVerseBridge(str(sv_path))

        # Load or create config
        self.config = self._load_config()

        # Metrics
        self.metrics: dict[str, Any] = {
            "audits_performed": 0,
            "pus_discovered": 0,
            "pus_approved": 0,
            "pus_executed": 0,
            "errors": 0,
            "gaps_detected": 0,
            "sectors_analyzed": 0,
            "quantum_resolver_runs": 0,
            "quantum_problems_detected": 0,
            "quantum_problems_healed": 0,
            "quantum_pus_created": 0,
            "start_time": datetime.now().isoformat(),
            "last_activity": None,
        }
        self._load_metrics()

        # **NEW**: Sector awareness
        self.enable_sector_awareness = enable_sector_awareness
        self.sectors: dict[str, Any] = {}
        self.sector_gaps: list[dict[str, Any]] = []

        self.enable_quantum_resolver = bool(self.config.get("enable_quantum_resolver", False))
        self.enable_quantum_pu_creation = bool(self.config.get("enable_quantum_pu_creation", False))
        self.quantum_pu_limit = int(self.config.get("quantum_pu_limit", 10))
        self.quantum_resolver = QuantumProblemResolver() if QuantumProblemResolver else None

        if self.enable_sector_awareness:
            self._load_sector_definitions()
            self._initialize_gap_detection()

        logger.info("Autonomous Monitor Initialized (Enhanced v2.0)")
        logger.info("  Audit Interval: %ss (%.1f minutes)", audit_interval, audit_interval / 60)
        logger.info(f"  Queue: {'Available' if self.queue else 'Unavailable'}")
        logger.info(f"  SimulatedVerse: {'Connected' if self.sv_bridge else 'Disconnected'}")
        logger.info(
            f"  Sector Awareness: {'Enabled' if self.enable_sector_awareness else 'Disabled'}",
        )
        if self.enable_sector_awareness:
            logger.info(f"  Sectors Loaded: {len(self.sectors)}")
            logger.info(f"  Configuration Gaps Detected: {len(self.sector_gaps)}")
        logger.info(
            "  Quantum Resolver: %s",
            "Enabled" if self.enable_quantum_resolver and self.quantum_resolver else "Disabled",
        )
        logger.info(
            "  Quantum PU Creation: %s (limit: %s)",
            "Enabled" if self.enable_quantum_pu_creation else "Disabled",
            self.quantum_pu_limit,
        )

    def _resolve_simulatedverse_path(self) -> Path:
        if get_repo_path:
            try:
                return Path(get_repo_path("SIMULATEDVERSE_ROOT"))
            except (OSError, RuntimeError, ValueError, KeyError, TypeError):
                return Path.home() / "Desktop" / "SimulatedVerse" / "SimulatedVerse"
        return Path.home() / "Desktop" / "SimulatedVerse" / "SimulatedVerse"

    def _load_config(self) -> dict[str, Any]:
        """Load monitor configuration."""
        default_config = {
            "enabled": True,
            "auto_approve_low_priority": False,
            "auto_approve_refactor": False,
            "auto_approve_doc": True,
            "max_auto_executions_per_hour": 10,
            "require_human_approval": True,
            "audit_on_startup": True,
            "enable_quantum_resolver": True,
            "enable_quantum_pu_creation": True,
            "quantum_pu_limit": 10,
            "watched_directories": ["src/", "tests/", "scripts/"],
        }

        if self.config_file.exists():
            try:
                with open(self.config_file, encoding="utf-8") as f:
                    loaded = json.load(f)
                    default_config.update(loaded)
            except (OSError, ValueError) as e:
                logger.info(f"Warning: Error loading config: {e}")

        # Save config
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_file, "w", encoding="utf-8") as f:
            json.dump(default_config, f, indent=2)

        return default_config

    def _load_sector_definitions(self) -> None:
        """Load sector definitions from YAML config."""
        sector_file = HUB_PATH / "config" / "sector_definitions.yaml"

        if not sector_file.exists():
            logger.warning(f"Sector definitions not found: {sector_file}")
            return
        if yaml is None:
            logger.warning("PyYAML not available; skipping sector definition loading")
            return

        try:
            with open(sector_file, encoding="utf-8") as f:
                data = yaml.safe_load(f)
                self.sectors = data.get("sectors", {})

            logger.info(f"Loaded {len(self.sectors)} sector definitions")

        except (OSError, ValueError, YAMLError) as e:
            logger.exception(f"Error loading sector definitions: {e}")

    def _initialize_gap_detection(self) -> None:
        """Initialize configuration gap detection system."""
        logger.info("\nInitializing Configuration Gap Detection...")

        # Define expected components per sector
        expected_components = {
            "core_infrastructure": [
                "src/core/",
                "src/setup/",
                "src/quantum/",
                "tests/test_quantum.py",
            ],
            "ai_orchestration": [
                "src/ai/",
                "src/orchestration/",
                "src/automation/",
                "src/orchestration/multi_ai_orchestrator.py",
            ],
            "integration": [
                "src/integration/",
                "src/copilot/",
                "src/integration/consciousness_bridge.py",
                "src/integration/simulatedverse_async_bridge.py",
            ],
            "diagnostic_healing": [
                "src/diagnostics/",
                "src/healing/",
                "src/analysis/",
                "src/healing/quantum_problem_resolver.py",
            ],
            "configuration": [
                "config/",
                "config/sector_definitions.yaml",
                "config/feature_flags.json",
            ],
            "testing": ["tests/", "testing_chamber/", "tests/test_minimal.py"],
            "documentation": ["docs/", "web/", "README.md", "AGENTS.md"],
        }

        # Check for missing components
        self.sector_gaps = []

        for sector_name, components in expected_components.items():
            if sector_name not in self.sectors:
                self.sector_gaps.append(
                    {
                        "type": "missing_sector",
                        "sector": sector_name,
                        "severity": "critical",
                        "description": f"Sector '{sector_name}' not defined in sector_definitions.yaml",
                    },
                )
                continue

            for component in components:
                component_path = HUB_PATH / component

                if not component_path.exists():
                    self.sector_gaps.append(
                        {
                            "type": "missing_component",
                            "sector": sector_name,
                            "component": component,
                            "severity": "high" if "src/" in component else "medium",
                            "description": f"Expected component not found: {component}",
                            "suggested_action": f"Create {component} or update sector definition",
                        },
                    )

        # Update metrics
        self.metrics["gaps_detected"] = len(self.sector_gaps)
        self.metrics["sectors_analyzed"] = len(self.sectors)

        logger.info(
            f"Gap Detection Complete: Found {len(self.sector_gaps)} gaps across {len(self.sectors)} sectors",
        )

    def get_sector_gaps(self) -> list[dict[str, Any]]:
        """Get list of detected configuration gaps."""
        return self.sector_gaps

    def get_sector_health_report(self) -> dict[str, Any]:
        """Generate sector health report."""
        sector_health: dict[str, Any] = {}
        for sector_name, sector_data in self.sectors.items():
            # Count gaps for this sector
            gaps = [g for g in self.sector_gaps if g.get("sector") == sector_name]

            # Check path patterns exist
            path_patterns = sector_data.get("path_patterns", [])
            paths_exist: list[Any] = []
            for pattern in path_patterns:
                # Convert glob pattern to simple directory check
                simple_path = pattern.replace("**", "").strip("/").strip("*")
                if simple_path:
                    check_path = HUB_PATH / simple_path
                    paths_exist.append(check_path.exists())

            sector_health[sector_name] = {
                "criticality": sector_data.get("criticality", "UNKNOWN"),
                "gaps_found": len(gaps),
                "paths_exist_count": sum(paths_exist),
                "paths_total": len(path_patterns),
                "health_score": ((sum(paths_exist) / len(paths_exist) * 100) if paths_exist else 0),
                "primary_agents": sector_data.get("primary_agents", []),
                "gaps": gaps,
            }

        return {
            "total_sectors": len(self.sectors),
            "total_gaps": len(self.sector_gaps),
            "timestamp": datetime.now().isoformat(),
            "sectors": sector_health,
        }

    def save_gap_report(self, output_path: Path | None = None) -> Path:
        """Save gap detection report to file.

        Args:
            output_path: Optional custom output path

        Returns:
            Path to saved report

        """
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = HUB_PATH / "data" / f"sector_gap_report_{timestamp}.json"

        report = self.get_sector_health_report()

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)

        logger.info(f"Gap report saved: {output_path}")
        return output_path

    def _load_metrics(self) -> None:
        """Load metrics from disk."""
        if self.metrics_file.exists():
            try:
                with open(self.metrics_file, encoding="utf-8") as f:
                    loaded = json.load(f)
                    self.metrics.update(loaded)
            except (OSError, ValueError) as e:
                logger.info(f"Warning: Error loading metrics: {e}")

    def _save_metrics(self) -> None:
        """Save metrics to disk."""
        self.metrics["last_activity"] = datetime.now().isoformat()
        try:
            self.metrics_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.metrics_file, "w", encoding="utf-8") as f:
                json.dump(self.metrics, f, indent=2)
        except (OSError, ValueError) as e:
            logger.info(f"Warning: Error saving metrics: {e}")

    def _run_quantum_resolution(self) -> dict[str, Any]:
        """Run Quantum Problem Resolver for locally detectable issues."""
        if not self.enable_quantum_resolver or not self.quantum_resolver:
            return {"status": "skipped", "reason": "resolver disabled or unavailable"}

        try:
            workspace = HUB_PATH
            problems = self.quantum_resolver.detect_problems(workspace)
            result = self.quantum_resolver.heal_problems(problems)

            self.metrics["quantum_resolver_runs"] += 1
            self.metrics["quantum_problems_detected"] += len(problems)
            healed_count = int(result.get("healed", 0))
            self.metrics["quantum_problems_healed"] += healed_count

            created_pus: list[str] = []
            if (
                self.enable_quantum_pu_creation
                and self.queue
                and PU
                and problems
                and self.quantum_pu_limit > 0
            ):
                for problem in problems[: self.quantum_pu_limit]:
                    try:
                        pu = PU(
                            id="",
                            type="BugPU",
                            title=f"Quantum issue: {problem.get('type', 'unknown')}",
                            description=f"Auto-generated from quantum resolver: {problem}",
                            source_repo="nusyq-hub",
                            priority="medium",
                            proof_criteria=["diagnose", "resolve", "verify"],
                            metadata={"quantum_problem": problem},
                            status="queued",
                        )
                        pu_id = self.queue.submit_pu(pu)
                        created_pus.append(pu_id)
                    except (RuntimeError, OSError, ValueError, KeyError) as exc:
                        logger.info(f"Quantum PU creation failed: {exc}")
                        self.metrics["errors"] += 1

                self.metrics["quantum_pus_created"] += len(created_pus)

            self._save_metrics()

            return {
                "status": "completed",
                "detected": len(problems),
                "healed": healed_count,
                "pus_created": created_pus,
            }
        except (OSError, RuntimeError, ValueError, TypeError) as exc:
            self.metrics["errors"] += 1
            self._save_metrics()
            return {"status": "failed", "error": str(exc)}

    def perform_theater_audit(self) -> list[dict[str, Any]]:
        """Perform Culture-Ship theater audit.

        Returns:
            list of discovered PUs

        """
        if not self.sv_bridge:
            logger.info("Warning: SimulatedVerse unavailable for audit")
            return []

        logger.info(f"\n[{datetime.now().strftime('%H:%M:%S')}] Performing theater audit...")

        try:
            # Submit audit request to Culture-Ship
            task_id = self.sv_bridge.submit_task(
                "culture-ship",
                "Perform comprehensive theater audit of NuSyQ-Hub",
                {
                    "repository": "NuSyQ-Hub",
                    "scan_depth": "comprehensive",
                    "generate_pus": True,
                },
            )

            # Wait for result
            result = self.sv_bridge.check_result(task_id, timeout=60)

            if not result:
                logger.info("  Timeout: Culture-Ship did not respond")
                self.metrics["errors"] += 1
                self._save_metrics()
                return []

            # Extract PUs from result
            pus: list[Any] = []
            if "effects" in result and "stateDelta" in result["effects"]:
                state_delta = result["effects"]["stateDelta"]
                pus = state_delta.get("pus", [])

            logger.info(f"  Audit Complete: {len(pus)} PUs discovered")

            self.metrics["audits_performed"] += 1
            self.metrics["pus_discovered"] += len(pus)
            self._save_metrics()

            return pus

        except (RuntimeError, OSError, ValueError, KeyError) as e:
            logger.info(f"  Error during audit: {e}")
            self.metrics["errors"] += 1
            self._save_metrics()
            return []

    def submit_pus_to_queue(self, pus: list[dict[str, Any]]) -> list[str]:
        """Submit discovered PUs to unified queue.

        Args:
            pus: list of PU dictionaries from Culture-Ship

        Returns:
            list of PU IDs that were submitted

        """
        if not self.queue or not PU:
            logger.info("Warning: Unified Queue unavailable")
            return []

        submitted_ids: list[Any] = []
        for pu_data in pus:
            try:
                # Create PU object
                pu = PU(
                    id="",
                    type=pu_data.get("type", "RefactorPU"),
                    title=pu_data.get("title", "Untitled PU"),
                    description=pu_data.get("description", ""),
                    source_repo="nusyq-hub",
                    priority=pu_data.get("priority", "medium"),
                    proof_criteria=pu_data.get("proof_criteria", []),
                    metadata=pu_data.get("metadata", {}),
                    status="queued",
                )

                # Submit to queue
                pu_id = self.queue.submit_pu(pu)
                submitted_ids.append(pu_id)

                # Check if auto-approval applies
                if self._should_auto_approve(pu):
                    logger.info(f"  Auto-approving {pu_id} ({pu.type}, {pu.priority})")
                    self.queue.request_council_vote(pu_id)
                    self.queue.assign_agents(pu_id)
                    self.metrics["pus_approved"] += 1

            except (RuntimeError, OSError, ValueError, KeyError) as e:
                logger.info(f"  Error submitting PU: {e}")
                self.metrics["errors"] += 1

        self._save_metrics()
        return submitted_ids

    def _should_auto_approve(self, pu: "PU") -> bool:
        """Determine if PU should be auto-approved based on config."""
        if not self.config.get("enabled", True):
            return False

        if self.config.get("require_human_approval", True):
            return False

        # Check type-based auto-approval
        if pu.type == "DocPU" and self.config.get("auto_approve_doc", False):
            return True

        if pu.type == "RefactorPU" and self.config.get("auto_approve_refactor", False):
            return True

        # Check priority-based auto-approval
        return bool(pu.priority == "low" and self.config.get("auto_approve_low_priority", False))

    def run_monitor_cycle(self) -> None:
        """Run one monitoring cycle."""
        now = datetime.now()
        time_since_audit = (now - self.last_audit).total_seconds()

        # Check if audit is needed
        if time_since_audit >= self.audit_interval:
            logger.info(f"\n{'=' * 80}")
            logger.info(f"AUTONOMOUS MONITOR CYCLE - {now.strftime('%Y-%m-%d %H:%M:%S')}")
            logger.info(f"{'=' * 80}")

            # Perform audit
            pus = self.perform_theater_audit()

            # Submit to queue
            if pus:
                submitted = self.submit_pus_to_queue(pus)
                logger.info(f"\n  Submitted {len(submitted)} PUs to queue")

            # Quantum resolver pass
            logger.info("\n🌌 Quantum Resolver Pass")
            quantum_results = self._run_quantum_resolution()
            logger.info(
                "  Quantum Resolver: %s (detected: %s, healed: %s)",
                quantum_results.get("status"),
                quantum_results.get("detected", 0),
                quantum_results.get("healed", 0),
            )

            self.last_audit = now

            # Display metrics
            self.display_metrics()

    def display_metrics(self) -> None:
        """Display current metrics."""
        logger.info(f"\n{'=' * 80}")
        logger.info("AUTONOMOUS MONITOR METRICS")
        logger.info(f"{'=' * 80}")
        logger.info(f"  Audits Performed: {self.metrics['audits_performed']}")
        logger.info(f"  PUs Discovered: {self.metrics['pus_discovered']}")
        logger.info(f"  PUs Approved: {self.metrics['pus_approved']}")
        logger.info(f"  PUs Executed: {self.metrics['pus_executed']}")
        logger.info(f"  Errors: {self.metrics['errors']}")
        logger.info(f"  Quantum Resolver Runs: {self.metrics['quantum_resolver_runs']}")
        logger.info(f"  Quantum Problems Detected: {self.metrics['quantum_problems_detected']}")
        logger.info(f"  Quantum Problems Healed: {self.metrics['quantum_problems_healed']}")
        logger.info(f"  Quantum PUs Created: {self.metrics['quantum_pus_created']}")

        start = datetime.fromisoformat(self.metrics["start_time"])
        uptime = (datetime.now() - start).total_seconds()
        logger.info(f"  Uptime: {uptime / 3600:.1f} hours")

        if self.metrics["audits_performed"] > 0:
            avg_pus = self.metrics["pus_discovered"] / self.metrics["audits_performed"]
            logger.info(f"  Avg PUs/Audit: {avg_pus:.1f}")

        logger.info(f"{'=' * 80}\n")

    def run_continuous(self, check_interval: int = 60) -> None:
        """Run monitor continuously.

        Args:
            check_interval: Seconds between checks (default: 60)

        """
        logger.info("\nStarting Continuous Monitoring...")
        logger.info(f"  Check Interval: {check_interval}s")
        logger.info(
            f"  Audit Interval: {self.audit_interval}s ({self.audit_interval / 60:.1f} minutes)",
        )
        logger.info("  Press Ctrl+C to stop\n")

        # Initial audit if configured
        if self.config.get("audit_on_startup", True):
            self.run_monitor_cycle()

        try:
            while True:
                time.sleep(check_interval)
                self.run_monitor_cycle()
        except KeyboardInterrupt:
            logger.info("\n\nMonitor stopped by user")
            self.display_metrics()

    def run_single_audit(self) -> None:
        """Run a single audit cycle (for testing)."""
        logger.info("\nRunning Single Audit Cycle...\n")
        self.run_monitor_cycle()


def main() -> None:
    """Main entry point."""
    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == "start":
            # Start continuous monitoring
            interval = int(sys.argv[2]) if len(sys.argv) > 2 else 1800
            monitor = AutonomousMonitor(audit_interval=interval)
            monitor.run_continuous()

        elif command == "audit":
            # Run single audit
            monitor = AutonomousMonitor()
            monitor.run_single_audit()

        elif command == "metrics":
            # Display metrics only
            monitor = AutonomousMonitor()
            monitor.display_metrics()

        elif command == "config":
            # Show config
            monitor = AutonomousMonitor()
            logger.info("\nCurrent Configuration:")
            logger.info(json.dumps(monitor.config, indent=2))

        else:
            logger.info(f"Unknown command: {command}")
            logger.info("\nAvailable commands:")
            logger.info("  start [interval]  - Start continuous monitoring (default: 1800s)")
            logger.info("  audit             - Run single audit cycle")
            logger.info("  metrics           - Display current metrics")
            logger.info("  config            - Show current configuration")

    else:
        # Default: run single audit
        monitor = AutonomousMonitor()
        monitor.run_single_audit()


if __name__ == "__main__":
    main()
