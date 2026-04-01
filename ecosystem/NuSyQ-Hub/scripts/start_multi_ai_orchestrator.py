"""Start the Unified AI Orchestrator service.
[ROUTE AGENTS] 🤖

Legacy launcher that spins up the unified AI orchestration stack and dumps a
status snapshot for diagnostics.
"""

import json
import time
from pathlib import Path

try:
    from src.orchestration.unified_ai_orchestrator import UnifiedAIOrchestrator
except ImportError:
    import sys

    sys.path.insert(0, str(Path(__file__).parent.parent))
    from src.orchestration.unified_ai_orchestrator import UnifiedAIOrchestrator


def create_orchestrator():
    """Legacy wrapper for compatibility"""
    return UnifiedAIOrchestrator()


def main():
    orchestrator = create_orchestrator()
    # Orchestrator is initialized and ready after creation - no start() method needed

    # Give it a moment to initialize threads
    time.sleep(2)

    status = orchestrator.get_system_status()
    print(json.dumps(status, indent=2, default=str))

    # Export orchestration state
    out = Path("data/orchestration_state.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    # Use export_state method
    orchestrator.export_state(out)
    print(f"Wrote orchestration state: {out}")

    # Keep running - orchestrator stays alive as long as process runs
    print("Multi-AI Orchestrator running... (Press Ctrl+C to stop)")
    try:
        while True:
            time.sleep(60)
            # Refresh state periodically
            orchestrator.export_state(out)
    except KeyboardInterrupt:
        print("\nStopping orchestrator...")
        # No explicit stop needed - process exit handles cleanup


if __name__ == "__main__":
    main()
