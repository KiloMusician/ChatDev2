"""Action module: AI-driven analyze/review/debug/generate commands."""

from __future__ import annotations

import asyncio
import sys
from collections.abc import Callable
from datetime import datetime
from pathlib import Path

from scripts.nusyq_actions.shared import emit_action_receipt


def _parse_routing_flags(args: list[str], default_system: str) -> tuple[str, str | None]:
    """Parse shared routing flags for AI actions."""
    target_system = default_system
    failover_chain: str | None = None
    for arg in args:
        if arg.startswith("--system="):
            target_system = arg.split("=", 1)[1]
        elif arg.startswith("--failover-chain="):
            value = arg.split("=", 1)[1].strip()
            failover_chain = value or None
    return target_system, failover_chain


def handle_review(args: list[str], paths, run_ai_task: Callable) -> int:
    """Review a file using AI code review."""
    if len(args) < 2:
        print("[ERROR] Missing file path argument")
        print(
            "\nUsage: python start_nusyq.py review <file_path> "
            "[--system=ollama|chatdev|copilot|auto] [--failover-chain=codex,ollama]"
        )
        print("\nExamples:")
        print("  python start_nusyq.py review src/main.py")
        print("  python start_nusyq.py review scripts/start_nusyq.py --system=auto")
        print("  python start_nusyq.py review src/main.py --system=chatdev --failover-chain=codex,ollama")
        emit_action_receipt(
            "review",
            exit_code=1,
            metadata={"error": "missing_file_path", "argv": args},
        )
        return 1

    file_path = args[1]
    target_system, failover_chain = _parse_routing_flags(args[2:], default_system="ollama")

    rc = run_ai_task(
        paths.nusyq_hub,
        "review",
        file_path,
        target_system,
        failover_chain_override=failover_chain,
    )
    emit_action_receipt(
        "review",
        exit_code=rc,
        metadata={"file_path": file_path, "system": target_system},
    )
    return rc


def handle_analyze(args: list[str], paths, run_ai_task: Callable) -> int:
    """Analyze a file or entire system using AI."""
    # Check if we should run full system analysis (no file specified)
    file_path = args[1] if len(args) >= 2 else None

    # If no file specified, run system-wide analysis
    if not file_path or file_path.startswith("--"):
        print("📊 Running full system analysis...")

        if str(paths.nusyq_hub) not in sys.path:
            sys.path.insert(0, str(paths.nusyq_hub))

        try:
            from src.tools.agent_task_router import AgentTaskRouter

            router = AgentTaskRouter(repo_root=paths.nusyq_hub)
            result = asyncio.run(router.analyze_system())

            if result["status"] == "success":
                summary = result["summary"]
                print("\n✅ Analysis complete:")
                print(f"   Working files: {summary['working_files']}")
                print(f"   Broken files: {summary['broken_files']}")
                print(f"   Enhancement candidates: {summary['enhancement_candidates']}")
                print(f"\nReport saved: {result['report_path']}")
                emit_action_receipt(
                    "analyze",
                    exit_code=0,
                    metadata={"mode": "system", "report_path": result.get("report_path")},
                )
                return 0
            else:
                print(f"\n❌ Analysis failed: {result.get('error', 'Unknown error')}")
                emit_action_receipt(
                    "analyze",
                    exit_code=1,
                    metadata={"mode": "system", "error": result.get("error")},
                )
                return 1

        except Exception as exc:
            print(f"[ERROR] Analysis failed: {exc}")
            import traceback

            traceback.print_exc()
            emit_action_receipt(
                "analyze",
                exit_code=1,
                metadata={"mode": "system", "error": str(exc)},
            )
            return 1

    # Otherwise, route specific file to AI system
    target_system, failover_chain = _parse_routing_flags(args[2:], default_system="ollama")

    resolved_path = Path(file_path)
    if not resolved_path.is_absolute():
        resolved_path = paths.nusyq_hub / resolved_path
    if not resolved_path.exists():
        print(f"[ERROR] File not found: {resolved_path}")
        emit_action_receipt(
            "analyze",
            exit_code=1,
            metadata={"mode": "file", "error": "file_not_found", "file_path": str(resolved_path)},
        )
        return 1

    rc = run_ai_task(
        paths.nusyq_hub,
        "analyze",
        str(resolved_path),
        target_system,
        failover_chain_override=failover_chain,
    )
    emit_action_receipt(
        "analyze",
        exit_code=rc,
        metadata={"mode": "file", "file_path": str(resolved_path), "system": target_system},
    )
    return rc


def handle_debug(args: list[str], paths, run_ai_task: Callable) -> int:
    """Debug an error using Quantum Error Bridge or AI systems."""
    if len(args) < 2:
        print("[ERROR] Missing error description")
        print("\nUsage: python start_nusyq.py debug <error_description> [--system=quantum|ai]")
        print("\nExamples:")
        print("  python start_nusyq.py debug \"ImportError: cannot import name 'foo'\"")
        print('  python start_nusyq.py debug "Tests failing in test_ml_modules.py"')
        print('  python start_nusyq.py debug "TypeError in quantum module" --system=quantum')
        emit_action_receipt(
            "debug",
            exit_code=1,
            metadata={"error": "missing_description", "argv": args},
        )
        return 1

    target_system = "quantum_error_bridge"  # Default to Quantum Error Bridge
    failover_chain: str | None = None
    description_parts: list[str] = []
    auto_fix = True  # Default to auto-fix enabled

    for arg in args[1:]:
        if arg.startswith("--system="):
            target_system = arg.split("=", 1)[1]
        elif arg.startswith("--failover-chain="):
            value = arg.split("=", 1)[1].strip()
            failover_chain = value or None
        elif arg == "--no-auto-fix":
            auto_fix = False
        else:
            description_parts.append(arg)

    error_desc = " ".join(description_parts).strip()

    # Use Quantum Error Bridge for quantum-enhanced error handling
    if target_system == "quantum_error_bridge" or target_system == "quantum":
        print(f"🌌 Activating Quantum Error Bridge for: {error_desc}")
        print(f"   Auto-fix: {'enabled' if auto_fix else 'disabled'}")

        try:
            from src.integration.quantum_error_bridge import QuantumErrorBridge

            bridge = QuantumErrorBridge(root_path=paths.nusyq_hub)

            # Create a generic error context from description
            context = {
                "description": error_desc,
                "source": "debug_command",
                "timestamp": datetime.now().isoformat(),
            }

            # Create a simple error representation
            error = RuntimeError(error_desc)

            # Use asyncio to run the async handle_error method
            result = asyncio.run(bridge.handle_error(error, context, auto_fix=auto_fix))

            # Display results
            print("\n✨ Quantum Resolution Results:")
            print(f"   Quantum State: {result.get('quantum_state', 'unknown')}")
            print(f"   Resolution Attempted: {result.get('resolution_attempted', False)}")
            print(f"   Auto-fixed: {result.get('auto_fixed', False)}")
            print(f"   PU Created: {result.get('pu_created', False)}")

            if result.get("actions"):
                print("\n   Actions Taken:")
                for action in result["actions"]:
                    print(f"     - {action}")

            if result.get("pu_id"):
                print(f"\n   📝 PU Created: {result['pu_id']}")
                print("      Run: python start_nusyq.py queue")

            rc = 0 if result.get("auto_fixed") else 1
            emit_action_receipt(
                "debug",
                exit_code=rc,
                metadata={
                    "mode": "quantum_error_bridge",
                    "auto_fixed": bool(result.get("auto_fixed")),
                    "pu_created": bool(result.get("pu_created")),
                },
            )
            return rc

        except Exception as e:
            print(f"[ERROR] Quantum Error Bridge failed: {e}")
            print("Falling back to legacy AI task routing...")
            rc = run_ai_task(
                paths.nusyq_hub,
                "debug",
                error_desc,
                "quantum_resolver",
                failover_chain_override=failover_chain,
            )
            emit_action_receipt(
                "debug",
                exit_code=rc,
                metadata={"mode": "fallback", "system": "quantum_resolver"},
            )
            return rc
    else:
        # Legacy path for other systems
        rc = run_ai_task(
            paths.nusyq_hub,
            "debug",
            error_desc,
            target_system,
            failover_chain_override=failover_chain,
        )
        emit_action_receipt(
            "debug",
            exit_code=rc,
            metadata={"mode": "legacy", "system": target_system},
        )
        return rc


def handle_generate(args: list[str], paths, run_ai_task: Callable) -> int:
    """Generate a new project using ChatDev or other AI systems."""
    if len(args) < 2:
        print("[ERROR] Missing project description")
        print(
            "\nUsage: python start_nusyq.py generate <description> "
            "[--system=chatdev|copilot|auto] [--failover-chain=codex,ollama]"
        )
        print("\nExamples:")
        print('  python start_nusyq.py generate "Create a REST API with JWT authentication"')
        print('  python start_nusyq.py generate "Build a simple calculator CLI tool"')
        print('  python start_nusyq.py generate "Make a snake game with PyGame"')
        emit_action_receipt(
            "generate",
            exit_code=1,
            metadata={"error": "missing_description", "argv": args},
        )
        return 1

    target_system = "chatdev"
    failover_chain: str | None = None
    description_parts: list[str] = []

    for arg in args[1:]:
        if arg.startswith("--system="):
            target_system = arg.split("=", 1)[1]
        elif arg.startswith("--failover-chain="):
            value = arg.split("=", 1)[1].strip()
            failover_chain = value or None
        else:
            description_parts.append(arg)

    description = " ".join(description_parts).strip()

    print(f"🤖 Generating project with {target_system.upper()}...")
    print(f"Description: {description}")

    rc = run_ai_task(
        paths.nusyq_hub,
        "generate",
        description,
        target_system,
        failover_chain_override=failover_chain,
    )
    emit_action_receipt(
        "generate",
        exit_code=rc,
        metadata={"description": description, "system": target_system},
    )
    return rc


def handle_ollama(args: list[str], paths) -> int:
    """Manage Ollama service (status, start, restart, ensure).

    Usage:
        python start_nusyq.py ollama status   # Check Ollama health
        python start_nusyq.py ollama start    # Start Ollama (WSL-aware)
        python start_nusyq.py ollama restart  # Force restart (clears WSL relay)
        python start_nusyq.py ollama ensure   # Ensure running (auto-recovery)
    """
    if str(paths.nusyq_hub) not in sys.path:
        sys.path.insert(0, str(paths.nusyq_hub))

    action = args[1] if len(args) >= 2 else "status"
    json_output = "--json" in args

    try:
        from src.services.ollama_service_manager import OllamaServiceManager
    except ImportError as e:
        print(f"❌ OllamaServiceManager not available: {e}")
        emit_action_receipt(
            "ollama",
            exit_code=1,
            metadata={"error": "import_failed", "action": action},
        )
        return 1

    mgr = OllamaServiceManager()

    if action == "status":
        status = mgr.check_health()
        if json_output:
            import json

            print(json.dumps(status.to_dict(), indent=2))
        else:
            emoji = "✅" if status.healthy else "❌"
            print("\n🦙 Ollama Status")
            print("=" * 40)
            print(f"{emoji} Environment: {status.environment.value}")
            print(f"   Healthy: {status.healthy}")
            if status.models_available:
                print(f"   Models loaded: {status.models_available}")
            if status.latency_ms:
                print(f"   Latency: {status.latency_ms:.0f}ms")
            if status.error:
                print(f"   Error: {status.error}")
            if status.wsl_relay_stale:
                print("   ⚠️  WSL relay stale — recommend: ollama restart")
        emit_action_receipt(
            "ollama",
            exit_code=0 if status.healthy else 1,
            metadata=status.to_dict(),
        )
        return 0 if status.healthy else 1

    elif action == "start":
        print("🦙 Starting Ollama...")
        success = mgr.start()
        if success:
            print("✅ Ollama started successfully")
        else:
            print("❌ Failed to start Ollama")
        emit_action_receipt(
            "ollama",
            exit_code=0 if success else 1,
            metadata={"action": "start", "success": success},
        )
        return 0 if success else 1

    elif action == "restart":
        print("🦙 Restarting Ollama (clearing stale connections)...")
        success = mgr.restart()
        if success:
            print("✅ Ollama restarted successfully")
        else:
            print("❌ Failed to restart Ollama")
        emit_action_receipt(
            "ollama",
            exit_code=0 if success else 1,
            metadata={"action": "restart", "success": success},
        )
        return 0 if success else 1

    elif action == "ensure":
        print("🦙 Ensuring Ollama is running...")
        success = mgr.ensure_running()
        if success:
            print("✅ Ollama is running")
        else:
            print("❌ Could not ensure Ollama is running")
        emit_action_receipt(
            "ollama",
            exit_code=0 if success else 1,
            metadata={"action": "ensure", "success": success},
        )
        return 0 if success else 1

    else:
        print(f"❌ Unknown action: {action}")
        print("\nUsage: python start_nusyq.py ollama [status|start|restart|ensure]")
        emit_action_receipt(
            "ollama",
            exit_code=1,
            metadata={"error": "unknown_action", "action": action},
        )
        return 1
