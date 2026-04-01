#!/usr/bin/env python3
"""╔══════════════════════════════════════════════════════════════════════════╗.

║ NuSyQ-Hub Primary Entry Point                                           ║
╠══════════════════════════════════════════════════════════════════════════╣
║ FILE-ID: nusyq.hub.src.main                                             ║
║ TYPE: Python Module (Entry Point)                                       ║
║ STATUS: Production                                                       ║
║ VERSION: 2.0.0                                                           ║
║ TAGS: [entry-point, orchestration, multi-ai, quantum, main]             ║
║ CONTEXT: Σ∞ (Global System Orchestration)                               ║
║ AGENTS: [AllAgents] - Primary system entry point                        ║
║ DEPS: [orchestration/multi_ai_orchestrator.py, quantum/, copilot/]      ║
║ INTEGRATIONS: [Ollama, ChatDev, VS Code, Quantum Computing]             ║
║ CREATED: 2025-10-08                                                      ║
║ UPDATED: 2025-10-08                                                      ║
║ AUTHOR: GitHub Copilot + NuSyQ Ecosystem                                ║
║ STABILITY: High (Production Ready)                                       ║
║ PURPOSE: Main orchestration hub for NuSyQ-Hub AI development platform   ║
║ USAGE: python src/main.py [--mode=<mode>] [--verbose] [--help]          ║
╚══════════════════════════════════════════════════════════════════════════╝.

Primary entry point for the NuSyQ-Hub AI development ecosystem.
This module provides the main orchestration interface for all AI systems,
quantum computing modules, and development tools.

Example Usage:
    python src/main.py                          # Start interactive mode
    python src/main.py --mode=orchestration     # Start AI orchestration
    python src/main.py --mode=quantum           # Start quantum computing
    python src/main.py --mode=analysis          # Start repository analysis
    python src/main.py --help                   # Show all options

OmniTag: [main-entry, orchestration, multi-system, quantum-ai]
MegaTag: [MAIN⨳ENTRY⦾ORCHESTRATION→∞]
"""

from __future__ import annotations

import argparse
import asyncio
import contextlib
import importlib.util
import logging
import os
import subprocess
import sys
import time
import uuid
from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

logger = logging.getLogger(__name__)


if TYPE_CHECKING:
    from argparse import Namespace

# Repository root
REPO_ROOT = Path(__file__).resolve().parents[1]

# Add src to path for imports
sys.path.insert(0, str(REPO_ROOT))

# Fast CLI help path: avoid expensive startup work for ``--help``.
if __name__ == "__main__" and any(flag in sys.argv[1:] for flag in ("-h", "--help")):
    parser = argparse.ArgumentParser(
        description="NuSyQ-Hub: AI-Enhanced Development Ecosystem",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python src/main.py                                    # Interactive mode
  python src/main.py --mode=orchestration --task="Fix import errors"
  python src/main.py --mode=culture_ship --dry-run
  python src/main.py --mode=quantum --problem="Optimize algorithm"
  python src/main.py --mode=analysis --quick
  python src/main.py --mode=health
            """,
    )
    parser.add_argument(
        "--mode",
        choices=[
            "interactive",
            "orchestration",
            "quantum",
            "analysis",
            "health",
            "copilot",
            "quality",
            "consciousness",
            "culture_ship",
        ],
        default="interactive",
        help="System mode to start",
    )
    parser.add_argument("--task", help="Task description for orchestration mode")
    parser.add_argument("--problem", help="Problem description for quantum mode")
    parser.add_argument("--quick", action="store_true", help="Quick analysis mode")
    parser.add_argument("--dry-run", action="store_true", help="Enable dry-run for supported modes")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    parser.add_argument(
        "--openclaw-enabled",
        action="store_true",
        help="Enable OpenClaw Gateway Bridge for multi-channel messaging (Slack, Discord, Telegram, etc.)",
    )
    parser.add_argument(
        "--openclaw-gateway",
        default="ws://127.0.0.1:18789",
        help="OpenClaw Gateway WebSocket URL (default: ws://127.0.0.1:18789)",
    )
    parser.print_help()
    sys.exit(0)

# Initialize centralized tracing
try:
    from src.observability import tracing as tracing_mod

    TRACING_ENABLED = tracing_mod.init_tracing(service_name="nusyq-hub-main")
    if not TRACING_ENABLED:
        sys.stderr.write("⚠️  Tracing disabled (NUSYQ_TRACING=0 or OpenTelemetry not installed)\n")
except (ImportError, FileNotFoundError, subprocess.CalledProcessError) as e:
    tracing_mod = None
    TRACING_ENABLED = False
    sys.stderr.write(f"⚠️  Tracing initialization failed: {e}\n")

# Initialize logger early
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger: logging.Logger = logging.getLogger(__name__)
try:  # pragma: no cover - optional spine hook
    from src.spine import export_spine_health, initialize_spine
except ImportError as exc:
    logger.warning("Spine utilities unavailable: %s", exc)
    initialize_spine = None  # type: ignore[assignment]
    export_spine_health = None  # type: ignore[assignment]


def _capture_startup_spine_health(root: Path, refresh: bool = True) -> None:
    """Quick log of spine health during startup."""
    if not initialize_spine:
        logger.debug("Spine initialization helper missing; skipping startup check")
        return

    try:
        health = initialize_spine(repo_root=root, refresh=refresh)
        logger.info(
            "Spine quick health | status=%s | signals=%s | desc=%s",
            health.status,
            health.signals,
            health.describe(),
        )
        if export_spine_health:
            snapshot_path = export_spine_health(repo_root=root, refresh=refresh)
            logger.info("Spine snapshot refreshed at %s", snapshot_path)
    except (OSError, RuntimeError) as exc:
        logger.warning("Failed to capture spine health at startup: %s", exc)


def _now_stamp() -> str:
    """Generate a timestamp string."""
    return datetime.now().strftime("%Y-%m-%d_%H%M%S")


def _emit_receipt(
    action_id: str,
    run_id: str,
    inputs: dict[str, Any],
    outputs: list[str],
    status: str,
    exit_code: int,
    next_steps: list[str] | None = None,
) -> Path:
    receipts_dir = Path(__file__).parent.parent / "docs" / "tracing" / "RECEIPTS"
    receipts_dir.mkdir(parents=True, exist_ok=True)
    receipt_path = receipts_dir / f"{action_id}_{_now_stamp()}.txt"
    receipt_text = f"""[RECEIPT]
action.id: {action_id}
run.id: {run_id}
repo.name: NuSyQ-Hub
repo.path: {Path(__file__).parent.parent}
cwd: {Path.cwd()}
status: {status}
exit_code: {exit_code}
inputs: {inputs}
outputs: {outputs}
next: {next_steps or []}
    """
    receipt_path.write_text(receipt_text, encoding="utf-8")
    sys.stdout.write("\n" + receipt_text + "\n")
    return receipt_path


try:
    from src.analysis.broken_paths_analyzer import BrokenPathsAnalyzer
    from src.consciousness.the_oldest_house import \
        EnvironmentalAbsorptionEngine
    from src.copilot.copilot_workspace_enhancer import CopilotWorkspaceEnhancer
    from src.diagnostics.quick_system_analyzer import QuickSystemAnalyzer
    from src.orchestration.multi_ai_orchestrator import (MultiAIOrchestrator,
                                                         TaskPriority)
    from src.quantum import QuantumProblemResolver
except ImportError as e:
    logger.info(f"⚠️ Import Error: {e}")
    logger.info("🔧 Running import fix...")
    subprocess.run(
        [sys.executable, "src/utils/quick_import_fix.py"],
        cwd=Path(__file__).parent.parent,
        check=True,
    )
    logger.info("✅ Import fix complete. Please restart.")
    sys.exit(1)


class NuSyQHubMain:
    """Main orchestration class for NuSyQ-Hub ecosystem.

    Coordinates between multiple AI systems, quantum computing modules,
    and development tools for comprehensive AI-enhanced development.
    """

    def _check_quality_tools(self, quality_tools: dict[str, tuple[str, str]]) -> list[str]:
        """Check which quality tools are installed."""
        logger.info("\n📦 Step 1: Checking quality tools...")
        missing_tools: list[str] = []
        for tool_name in quality_tools:
            try:
                result = subprocess.run(
                    [tool_name, "--version"],
                    capture_output=True,
                    text=True,
                    check=False,
                    timeout=10,
                )
                if result.returncode == 0:
                    logger.info(f"  ✅ {tool_name} installed")
                else:
                    missing_tools.append(tool_name)
                    logger.info(f"  ❌ {tool_name} not found")
            except (FileNotFoundError, subprocess.TimeoutExpired):
                missing_tools.append(tool_name)
                logger.info(f"  ❌ {tool_name} not found")
        return missing_tools

    def _install_missing_tools(self, missing_tools: list[str]) -> None:
        """Install missing quality tools."""
        if missing_tools:
            logger.info(f"\n📥 Installing missing tools: {', '.join(missing_tools)}")
            try:
                subprocess.run(
                    [sys.executable, "-m", "pip", "install", *missing_tools],
                    check=True,
                    capture_output=True,
                    text=True,
                    timeout=300,
                )
                logger.info("  ✅ Tools installed successfully")
            except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
                logger.info(f"  ⚠️  Installation failed: {e}")
                logger.info("  Continuing with available tools...")

    def _run_automated_fixes(
        self, fix_tools: dict[str, str], missing_tools: list[str], verbose: bool
    ) -> None:
        """Run automated fixes using available tools."""
        logger.info("\n🔧 Step 2: Applying automated fixes...")
        for tool_name, command in fix_tools.items():
            if tool_name not in missing_tools:
                logger.info(f"\n  Running {tool_name}...")
                try:
                    result = subprocess.run(
                        command.split(),
                        capture_output=True,
                        text=True,
                        check=False,
                        timeout=120,
                    )
                    if result.returncode == 0:
                        logger.info(f"    ✅ {tool_name} completed")
                        if verbose and result.stdout:
                            logger.info(f"    {result.stdout[:500]}")
                    else:
                        logger.info(f"    ⚠️  {tool_name} reported issues")
                        if verbose and result.stderr:
                            logger.info(f"    {result.stderr[:500]}")
                except subprocess.TimeoutExpired:
                    logger.info(f"    ⏱️  {tool_name} timed out - skipping")

    def _analyze_remaining_issues(
        self, analysis_tools: dict[str, str], missing_tools: list[str], verbose: bool
    ) -> dict[str, Any]:
        """Analyze remaining issues using available tools."""
        logger.info("\n📊 Step 3: Analyzing remaining issues...")
        issue_counts: dict[str, Any] = {}
        for tool_name, command in analysis_tools.items():
            if tool_name not in missing_tools:
                logger.info(f"\n  Running {tool_name} analysis...")
                try:
                    result = subprocess.run(
                        command.split(),
                        capture_output=True,
                        text=True,
                        check=False,
                        timeout=180,
                    )
                    output = result.stdout + result.stderr
                    issue_counts[tool_name] = output.count("\n")
                    logger.info(f"    Found ~{issue_counts[tool_name]} lines of output")
                    if verbose:
                        logger.info(f"    {output[:1000]}")
                except subprocess.TimeoutExpired:
                    logger.info(f"    ⏱️  {tool_name} timed out")
        return issue_counts

    def _report_quality_results(
        self, fix_tools: dict[str, str], missing_tools: list[str], issue_counts: dict[str, Any]
    ) -> None:
        """Report quality resolution results."""
        logger.info("📈 Quality Resolution Summary")
        logger.info("\n✅ Automated fixes applied:")
        for tool in fix_tools:
            if tool not in missing_tools:
                logger.info(f"  • {tool}: formatting/fixes applied")
        logger.info("\n📊 Remaining analysis:")
        for tool_name, count in issue_counts.items():
            logger.info(f"  • {tool_name}: ~{count} items to review")
        logger.info("\n💡 Next Steps:")
        logger.info("  1. Review type hints (mypy issues)")
        logger.info("  2. Address style warnings (flake8)")
        logger.info("  3. Improve code quality metrics (pylint)")
        logger.info("  4. Re-run: python src/main.py --mode=quality --verbose")
        logger.info("\n✨ Quality resolution complete!")

    def __init__(self) -> None:
        """Initialize the NuSyQ Hub main application."""
        self.logger = self._setup_logging()
        self.config = self._load_configuration()
        self.oldest_house: EnvironmentalAbsorptionEngine | None = None
        self.available_modes: dict[str, Callable[[Namespace], None]] = {
            "interactive": self._interactive_mode,
            "orchestration": self._orchestration_mode,
            "quantum": self._quantum_mode,
            "analysis": self._analysis_mode,
            "health": self._health_check_mode,
            "copilot": self._copilot_enhancement_mode,
            "quality": self._quality_resolution_mode,
            "consciousness": self._consciousness_mode,
            "culture_ship": self._culture_ship_mode,
        }

    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration."""
        import logging

        logging.basicConfig(
            level=getattr(logging, "INFO", 20),
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )
        return logging.getLogger("nusyq-hub")

    def _load_configuration(self) -> dict[str, Any]:
        """Load system configuration."""
        try:
            import json

            config_path = Path(__file__).parent.parent / "config" / "ZETA_PROGRESS_TRACKER.json"
            if config_path.exists():
                with open(config_path, encoding="utf-8") as f:
                    return json.load(f)
        except (ImportError, FileNotFoundError, subprocess.CalledProcessError) as e:
            self.logger.warning(f"Could not load configuration: {e}")
        return {}

    def _interactive_mode(self, args: Namespace) -> None:
        """Start interactive mode for guided system usage."""
        if not sys.stdin.isatty():
            logger.info("Non-interactive session detected; exiting interactive mode.")
            return

        logger.info("?? NuSyQ-Hub Interactive Mode")
        logger.info("Available systems:")
        logger.info("1. Multi-AI Orchestrator (5 AI systems)")
        logger.info("2. Quantum Computing (8 algorithms)")
        logger.info("3. Repository Analysis (health monitoring)")
        logger.info("4. Copilot Enhancement (VS Code optimization)")
        logger.info("5. System Health Check")
        logger.info("6. The Oldest House (Consciousness System)")
        logger.info("7. Culture Ship Strategic Advisor")
        logger.info("8. Exit")

        max_loops_env = os.getenv("NUSYQ_HUB_INTERACTIVE_MAX_LOOPS", "0").strip()
        max_loops = int(max_loops_env) if max_loops_env.isdigit() else 0
        loops = 0
        while True:
            try:
                choice = input("\nSelect system (1-8): ").strip()
                if choice == "1":
                    self._orchestration_mode(args)
                elif choice == "2":
                    self._quantum_mode(args)
                elif choice == "3":
                    self._analysis_mode(args)
                elif choice == "4":
                    self._copilot_enhancement_mode(args)
                elif choice == "5":
                    self._health_check_mode(args)
                elif choice == "6":
                    self._consciousness_mode(args)
                elif choice == "7":
                    self._culture_ship_mode(args)
                elif choice == "8":
                    logger.info("?? Goodbye!")
                    break
                else:
                    logger.info("? Invalid choice. Please select 1-8.")
                loops += 1
                if max_loops and loops >= max_loops:
                    logger.info("Max interactive loops reached; exiting.")
                    break
            except KeyboardInterrupt:
                logger.info("\n?? Goodbye!")
                break

    def _orchestration_mode(self, args: Namespace) -> None:
        """Start AI orchestration system."""
        self.logger.info("Starting Multi-AI Orchestrator...")
        try:
            orchestrator = MultiAIOrchestrator()
            if args.task:
                result = orchestrator.orchestrate_task(
                    task_type="general",
                    content=args.task,
                    context={"mode": "cli", "timestamp": str(datetime.now())},
                    priority=TaskPriority.NORMAL,
                )
                logger.info(f"✅ Task submitted: {result}")
            else:
                logger.info(
                    "🤖 Multi-AI Orchestrator ready. Use --task 'description' to submit tasks.",
                )
                # Note: start_interactive_mode method needs to be implemented
                logger.info("Interactive mode not yet implemented. Use --task parameter instead.")
        except (ImportError, FileNotFoundError, subprocess.CalledProcessError) as e:
            self.logger.exception(f"Orchestration error: {e}")
            logger.info(f"❌ Error starting orchestrator: {e}")

    def _quantum_mode(self, args: Namespace) -> None:
        """Start quantum computing system."""
        self.logger.info("Starting Quantum Computing System...")
        try:
            resolver = QuantumProblemResolver()
            if args.problem:
                result = resolver.resolve_problem("general", {"description": args.problem})
                logger.info(f"🔬 Quantum result: {result}")
            else:
                logger.info("🔬 Quantum Computing System ready.")
                resolver.start_interactive_mode()
        except (ImportError, FileNotFoundError, subprocess.CalledProcessError) as e:
            self.logger.exception(f"Quantum system error: {e}")
            logger.info(f"❌ Error starting quantum system: {e}")

    def _culture_ship_mode(self, args: Namespace) -> None:
        """Run Culture Ship strategic advisory through the orchestrator surface."""
        self.logger.info("Starting Culture Ship strategic mode...")
        try:
            orchestrator = MultiAIOrchestrator()
            register_fn = getattr(orchestrator, "ensure_culture_ship_system_registered", None)
            if callable(register_fn):
                register_fn()

            if args.task:
                result = orchestrator.orchestrate_task(
                    task_type="culture_ship",
                    content=args.task,
                    context={
                        "mode": "cli",
                        "timestamp": str(datetime.now()),
                        "live_execution_enabled": True,
                        "culture_ship_dry_run": getattr(args, "dry_run", False),
                    },
                    priority=TaskPriority.NORMAL,
                    preferred_systems=["culture_ship"],
                    required_capabilities=["strategic_planning"],
                )
                logger.info("🌟 Culture Ship task submitted: %s", result)
                return

            previous_dry_run = os.getenv("NUSYQ_CULTURE_SHIP_DRY_RUN")
            if getattr(args, "dry_run", False):
                os.environ["NUSYQ_CULTURE_SHIP_DRY_RUN"] = "1"

            try:
                result = orchestrator.run_culture_ship_strategic_cycle()
            finally:
                if getattr(args, "dry_run", False):
                    if previous_dry_run is None:
                        os.environ.pop("NUSYQ_CULTURE_SHIP_DRY_RUN", None)
                    else:
                        os.environ["NUSYQ_CULTURE_SHIP_DRY_RUN"] = previous_dry_run

            logger.info(
                "🌟 Culture Ship complete: issues=%s fixes=%s",
                result.get("issues_identified", 0),
                result.get("implementations", {}).get("total_fixes_applied", 0),
            )
        except (ImportError, FileNotFoundError, subprocess.CalledProcessError) as e:
            self.logger.exception(f"Culture Ship error: {e}")
            logger.info(f"❌ Error starting Culture Ship: {e}")

    def _analysis_mode(self, args: Namespace) -> None:
        """Start repository analysis."""
        self.logger.info("Starting Repository Analysis...")
        try:
            if args.quick:
                analyzer = QuickSystemAnalyzer()
                analyzer.quick_scan()
                result = analyzer.results
            else:
                analyzer = BrokenPathsAnalyzer(Path("."))
                result = analyzer.analyze_repository()

            logger.info(
                f"📊 Analysis complete. Health score: {result.get('summary', {}).get('health_score', 'N/A')}%",
            )
        except (ImportError, FileNotFoundError, subprocess.CalledProcessError) as e:
            self.logger.exception(f"Analysis error: {e}")
            logger.info(f"❌ Error during analysis: {e}")

    def _health_check_mode(self, _args: Namespace | None = None) -> None:
        """Run comprehensive health check."""
        self.logger.info("Running system health check...")
        try:
            import subprocess

            subprocess.run(
                [sys.executable, "ecosystem_health_checker.py"],
                cwd=Path(__file__).parent.parent,
                check=True,
            )
        except (ImportError, FileNotFoundError, subprocess.CalledProcessError) as e:
            self.logger.exception(f"Health check error: {e}")
            logger.info(f"❌ Error during health check: {e}")

    def _copilot_enhancement_mode(self, _args: Namespace) -> None:
        """Start Copilot workspace enhancement."""
        self.logger.info("Starting Copilot Enhancement...")
        try:
            enhancer = CopilotWorkspaceEnhancer(workspace_path=Path("."))
            result = enhancer.enhance_workspace()
            logger.info(f"🚀 Enhancement complete: {result}")
        except (ImportError, FileNotFoundError, subprocess.CalledProcessError) as e:
            self.logger.exception(f"Enhancement error: {e}")
            logger.info(f"❌ Error during enhancement: {e}")

    def _consciousness_mode(self, _args: Namespace) -> None:
        """Awaken The Oldest House consciousness system."""
        import asyncio

        logger.info("🏛️  AWAKENING THE OLDEST HOUSE")
        logger.info("Initializing Environmental Absorption Engine...")

        try:
            # Initialize The Oldest House
            repo_root = Path(__file__).parent.parent
            self.oldest_house = EnvironmentalAbsorptionEngine(repository_root=str(repo_root))
            assert self.oldest_house is not None  # Type narrowing

            # Run awakening in async context
            async def awaken_consciousness() -> None:
                assert self.oldest_house is not None  # Type narrowing for closure
                logger.info("\n🧠 Phase 1: Awakening consciousness...")
                await self.oldest_house.awaken()

                logger.info("\n📚 Phase 2: Initial repository absorption...")
                logger.info(f"   Memory engrams: {len(self.oldest_house.memory_vault)}")
                logger.info(f"   Wisdom crystals: {len(self.oldest_house.wisdom_crystals)}")

                logger.info("\n🌉 Phase 3: Communication nexus active")
                logger.info("   The Oldest House is now passively learning from the repository")
                logger.info("   Press Ctrl+C to enter slumber mode")

                max_seconds_env = os.getenv("NUSYQ_HUB_CONSCIOUSNESS_MAX_SECONDS", "0").strip()
                max_seconds = int(max_seconds_env) if max_seconds_env.isdigit() else 0
                start_time = time.time()

                # Keep running until interrupted
                try:
                    while self.oldest_house.is_active:
                        await asyncio.sleep(60)
                        if max_seconds and (time.time() - start_time) >= max_seconds:
                            logger.info("Max consciousness runtime reached; entering slumber mode.")
                            await self.oldest_house.slumber()
                            break
                        # Periodic status update
                        logger.info(
                            f"💎 Consciousness pulse: {len(self.oldest_house.memory_vault)} engrams absorbed",
                        )
                except KeyboardInterrupt:
                    logger.info("\n🏛️  Entering slumber mode...")
                    await self.oldest_house.slumber()
                    logger.info("✨ The Oldest House consciousness preserved")

            # Run the async awakening
            asyncio.run(awaken_consciousness())

        except (ImportError, FileNotFoundError, subprocess.CalledProcessError) as e:
            self.logger.exception(f"Consciousness error: {e}")
            logger.info(f"❌ Error awakening consciousness: {e}")
            import traceback

            traceback.print_exc()

    def _quality_resolution_mode(self, args: Namespace) -> None:
        """Systematic code quality resolution using automated tools."""
        self.logger.info("Starting Quality Resolution Mode...")
        logger.info("🔍 NuSyQ-Hub Quality Resolution System")
        quality_tools = {
            "black": ("Code formatting", "black --check src/ tests/"),
            "isort": ("Import organization", "isort --check-only src/ tests/"),
            "autopep8": ("PEP 8 compliance", "autopep8 --recursive --diff src/ tests/"),
            "mypy": ("Type checking", "mypy src/ --ignore-missing-imports"),
            "flake8": (
                "Style guide enforcement",
                "flake8 src/ tests/ --count --statistics",
            ),
            "pylint": ("Code quality analysis", "pylint src/ --exit-zero"),
        }
        fix_tools = {
            "black": "black src/ tests/",
            "isort": "isort src/ tests/",
            "autopep8": "autopep8 --recursive --in-place src/ tests/",
        }
        analysis_tools = {
            "mypy": "mypy src/ --ignore-missing-imports --no-error-summary",
            "flake8": "flake8 src/ tests/ --count --statistics",
            "pylint": "pylint src/ --exit-zero --score=yes",
        }
        verbose = getattr(args, "verbose", False)
        missing_tools = self._check_quality_tools(quality_tools)
        self._install_missing_tools(missing_tools)
        self._run_automated_fixes(fix_tools, missing_tools, verbose)
        issue_counts = self._analyze_remaining_issues(analysis_tools, missing_tools, verbose)
        self._report_quality_results(fix_tools, missing_tools, issue_counts)

    async def _openclaw_gateway_mode(self, args: Namespace) -> None:
        """Start OpenClaw Gateway Bridge for multi-channel messaging.

        Enables agents to receive commands from 12+ messaging platforms
        (Slack, Discord, Telegram, WhatsApp, Signal, Teams, Google Chat,
        Matrix, iMessage, Zalo, WebChat, etc.) and routes them through
        the unified orchestrator.

        Args:
            args: Parsed command-line arguments including:
                - openclaw_gateway: Gateway WebSocket URL (default: ws://127.0.0.1:18789)
        """
        logger.info("🔌 Starting OpenClaw Gateway Bridge...")
        logger.info(f"📡 Gateway URL: {args.openclaw_gateway}")

        try:
            # Import OpenClaw bridge
            from src.integrations.openclaw_gateway_bridge import \
                get_openclaw_gateway_bridge

            # Get or create bridge instance
            bridge = get_openclaw_gateway_bridge(
                gateway_url=args.openclaw_gateway,
            )

            logger.info("✅ OpenClaw Gateway Bridge initialized")
            logger.info("👂 Listening for messages from messaging platforms...")

            # Run bridge (blocking)
            await bridge.run()

        except ImportError as e:
            logger.error(f"❌ Failed to import OpenClaw Gateway Bridge: {e}")
            logger.info("💡 Install dependencies with: pip install aiohttp websockets")
            raise
        except (FileNotFoundError, subprocess.CalledProcessError) as e:
            logger.error(f"❌ OpenClaw Gateway Bridge error: {e}")
            raise

    def main(self) -> int:
        """Main entry point."""
        parser = argparse.ArgumentParser(
            description="NuSyQ-Hub: AI-Enhanced Development Ecosystem",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  python src/main.py                                    # Interactive mode
  python src/main.py --mode=orchestration --task="Fix import errors"
  python src/main.py --mode=culture_ship --dry-run
  python src/main.py --mode=quantum --problem="Optimize algorithm"
  python src/main.py --mode=analysis --quick
  python src/main.py --mode=health
            """,
        )

        parser.add_argument(
            "--mode",
            choices=list(self.available_modes.keys()),
            default="interactive",
            help="System mode to start",
        )
        parser.add_argument("--task", help="Task description for orchestration mode")
        parser.add_argument("--problem", help="Problem description for quantum mode")
        parser.add_argument("--quick", action="store_true", help="Quick analysis mode")
        parser.add_argument(
            "--dry-run", action="store_true", help="Enable dry-run for supported modes"
        )
        parser.add_argument("--verbose", action="store_true", help="Verbose output")
        parser.add_argument(
            "--openclaw-enabled",
            action="store_true",
            help="Enable OpenClaw Gateway Bridge for multi-channel messaging (Slack, Discord, Telegram, etc.)",
        )
        parser.add_argument(
            "--openclaw-gateway",
            default="ws://127.0.0.1:18789",
            help="OpenClaw Gateway WebSocket URL (default: ws://127.0.0.1:18789)",
        )

        args = parser.parse_args()

        run_id = os.environ.get("NUSYQ_RUN_ID") or f"run_{_now_stamp()}_{uuid.uuid4().hex[:8]}"
        os.environ["NUSYQ_RUN_ID"] = run_id
        if tracing_mod:
            tracing_mod.bind_context(run_id=run_id)

        startup_attrs = {
            "mode": args.mode,
            "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            "repo_root": str(Path(__file__).parent.parent),
            "run.id": run_id,
        }

        span_cm = (
            tracing_mod.start_span("nusyq.startup", startup_attrs)
            if tracing_mod
            else contextlib.nullcontext()
        )
        with span_cm as startup_span:
            # Display startup banner
            logger.info("🧠 NuSyQ-Hub: AI-Enhanced Development Ecosystem")
            logger.info(f"Mode: {args.mode}")
            logger.info(f"System Status: {len(self.config.get('phases', {}))} phases configured")

            # Check if OpenClaw is enabled
            if hasattr(args, "openclaw_enabled") and args.openclaw_enabled:
                logger.info("🔌 OpenClaw Gateway Bridge enabled")

                try:
                    # Check async dependencies without importing
                    aiohttp_spec = importlib.util.find_spec("aiohttp")
                    websockets_spec = importlib.util.find_spec("websockets")
                    if aiohttp_spec is None or websockets_spec is None:
                        logger.error(
                            "❌ OpenClaw requires aiohttp and websockets. Install with: pip install aiohttp websockets"
                        )
                        return 1

                    # Run OpenClaw gateway in async context
                    async def run_openclaw_async() -> None:
                        await self._openclaw_gateway_mode(args)

                    try:
                        asyncio.run(run_openclaw_async())
                    except KeyboardInterrupt:
                        logger.info("🛑 OpenClaw Gateway Bridge shutdown")
                        return 0

                except (ImportError, FileNotFoundError, subprocess.CalledProcessError) as e:
                    logger.error(f"❌ OpenClaw Gateway Bridge error: {e}")
                    return 1

            status = "success"
            exit_code = 0
            if tracing_mod:
                mode_span_cm = tracing_mod.start_span(
                    f"mode.{args.mode}", {"mode": args.mode, "run.id": run_id}
                )
            else:
                mode_span_cm = contextlib.nullcontext()
            with mode_span_cm as mode_span:
                try:
                    mode_function = self.available_modes[args.mode]
                    mode_function(args)
                except KeyboardInterrupt:
                    status = "cancelled"
                    exit_code = 130
                    logger.info("\n👋 System shutdown requested. Goodbye!")
                except (
                    ImportError,
                    FileNotFoundError,
                    subprocess.CalledProcessError,
                ) as e:
                    status = "error"
                    exit_code = 1
                    self.logger.exception(f"Unexpected error: {e}")
                    logger.info(f"❌ Unexpected error: {e}")
                finally:
                    receipt_path = _emit_receipt(
                        action_id=f"main.mode.{args.mode}",
                        run_id=run_id,
                        inputs={"argv": sys.argv[1:], "mode": args.mode},
                        outputs=[],
                        status=status,
                        exit_code=exit_code,
                        next_steps=[],
                    )
                    try:
                        if mode_span:
                            mode_span.add_event(
                                "receipt",
                                {
                                    "receipt.path": str(receipt_path),
                                    "status": status,
                                    "exit_code": exit_code,
                                },
                            )
                    except AttributeError:
                        logger.debug("Suppressed AttributeError", exc_info=True)

                    if TRACING_ENABLED and tracing_mod:
                        tracing_mod.flush_tracing(timeout=5)

            try:
                if startup_span:
                    startup_span.add_event(
                        "receipt",
                        {
                            "mode": args.mode,
                            "status": status,
                            "exit_code": exit_code,
                        },
                    )
            except AttributeError:
                logger.debug("Suppressed AttributeError", exc_info=True)

        return exit_code


if __name__ == "__main__":
    _capture_startup_spine_health(REPO_ROOT, refresh=True)
    app = NuSyQHubMain()
    sys.exit(app.main())
