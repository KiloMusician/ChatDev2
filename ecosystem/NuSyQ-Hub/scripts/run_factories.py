#!/usr/bin/env python3
"""Phase 2: Factory Function Integration - CLI Gateway

Rehabilitates 4 orphaned factory functions by providing CLI access:
1. get_integrator() (ai/ollama_chatdev_integrator.py)
2. get_orchestrator() (ai/claude_copilot_orchestrator.py)
3. create_quantum_resolver() (archive quantum v4.2.0)
4. create_server() (docs/Core/context_server.py)

Usage:
    python scripts/run_factories.py --factory=integrator --health
    python scripts/run_factories.py --factory=orchestrator --start
    python scripts/run_factories.py --factory=quantum --problem-type=COMPLEX
    python scripts/run_factories.py --factory=context_server --port=8888
"""

import argparse
import sys
from pathlib import Path

# Add src to path for imports
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))


def run_integrator_factory(args: argparse.Namespace) -> int:
    """Run Ollama/ChatDev integrator factory."""
    # Import from top-level ai/ directory (orphaned location)
    import sys

    ai_path = PROJECT_ROOT / "ai"
    if str(ai_path) not in sys.path:
        sys.path.insert(0, str(ai_path))

    from ollama_chatdev_integrator import get_integrator

    print("🏭 Creating OllamaChatDevIntegrator...")
    integrator = get_integrator()

    if args.health:
        print("\n📊 Health Check:")
        print(f"  Available: {integrator.is_available()}")
        status = integrator.ping()
        print(f"  Status: {status}")
        return 0 if status.get("available") else 1

    print(f"✅ Integrator created: {integrator}")
    print(f"   Available: {integrator.is_available()}")
    return 0


def run_orchestrator_factory(args: argparse.Namespace) -> int:
    """Run Claude/Copilot orchestrator factory."""
    # Import from top-level ai/ directory (orphaned location)
    import sys

    ai_path = PROJECT_ROOT / "ai"
    if str(ai_path) not in sys.path:
        sys.path.insert(0, str(ai_path))

    from claude_copilot_orchestrator import get_orchestrator

    print("🏭 Creating ClaudeCopilotOrchestrator...")
    orchestrator = get_orchestrator()

    if args.start:
        print("\n🚀 Starting orchestrator...")
        success = orchestrator.start()
        print(f"   Started: {success}")

    print(f"\n📊 Status: {orchestrator.status()}")
    return 0


def run_quantum_factory(args: argparse.Namespace) -> int:
    """Run quantum problem resolver factory (archived v4.2.0)."""
    sys.path.insert(0, str(PROJECT_ROOT / "archive" / "quantum_problem_resolver_evolution"))
    from quantum_problem_resolver_v4 import create_quantum_resolver

    print("🏭 Creating QuantumProblemResolver...")
    print(f"   Problem Type: {args.problem_type or 'SIMPLE'}")
    print(f"   Repo Path: {args.repo_path or 'current directory'}")

    resolver = create_quantum_resolver(repo_path=args.repo_path, problem_type=args.problem_type)

    print(f"\n✅ Resolver created: {resolver}")
    print(f"   Mode: {resolver.mode}")
    print(f"   Root Path: {resolver.root_path}")

    if args.demo:
        print("\n🎭 Running demo resolution...")
        # Could add demo problem here
        print("   (Demo mode - would resolve sample problem)")

    return 0


def run_context_server_factory(args: argparse.Namespace) -> int:
    """Run context server factory."""
    # Use docs version (orphaned symbol) rather than src version
    sys.path.insert(0, str(PROJECT_ROOT / "docs" / "Core"))
    from context_server import create_server

    port = args.port or 0  # 0 = auto-assign
    print(f"🏭 Creating ReusableTCPServer on port {port or 'auto'}...")

    server = create_server(port=port)

    print(f"\n✅ Server created: {server}")
    print(f"   Address: {server.server_address}")
    print(f"   Port: {server.server_address[1]}")
    print(f"   Handler: {server.RequestHandlerClass.__name__}")

    if args.serve:
        print("\n🚀 Starting server (Ctrl+C to stop)...")
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("\n\n🛑 Server stopped")
        finally:
            server.shutdown()
            server.server_close()

    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Factory function gateway - rehabilitate orphaned factories",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Health check Ollama/ChatDev integrator
  python run_factories.py --factory=integrator --health

  # Start Claude/Copilot orchestrator
  python run_factories.py --factory=orchestrator --start

  # Create quantum resolver for complex problems
  python run_factories.py --factory=quantum --problem-type=COMPLEX

  # Launch context server on port 8888
  python run_factories.py --factory=context_server --port=8888 --serve
        """,
    )

    parser.add_argument(
        "--factory",
        choices=["integrator", "orchestrator", "quantum", "context_server"],
        required=True,
        help="Which factory to run",
    )

    # Integrator options
    parser.add_argument("--health", action="store_true", help="Run health check (integrator)")

    # Orchestrator options
    parser.add_argument("--start", action="store_true", help="Start orchestrator")

    # Quantum resolver options
    parser.add_argument(
        "--problem-type",
        choices=["SIMPLE", "COMPLEX", "QUANTUM", "OPTIMIZATION"],
        help="Problem type for quantum resolver",
    )
    parser.add_argument("--repo-path", help="Repository path for quantum resolver")
    parser.add_argument("--demo", action="store_true", help="Run demo resolution")

    # Context server options
    parser.add_argument("--port", type=int, help="Port for context server (0=auto)")
    parser.add_argument("--serve", action="store_true", help="Start serving (blocks)")

    args = parser.parse_args()

    print("=" * 70)
    print("🏭 Factory Function Gateway - Phase 2 Rehabilitation")
    print("=" * 70)

    factory_handlers = {
        "integrator": run_integrator_factory,
        "orchestrator": run_orchestrator_factory,
        "quantum": run_quantum_factory,
        "context_server": run_context_server_factory,
    }

    handler = factory_handlers[args.factory]
    return handler(args)


if __name__ == "__main__":
    sys.exit(main())
