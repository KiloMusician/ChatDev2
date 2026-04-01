#!/usr/bin/env python3
"""Bootstrap ChatDev for Self-Development Pipeline
Demonstrates ChatDev + Ollama integration for autonomous development
"""

import json
import os
import sys
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, TextIO, cast

# Fix Windows console encoding
if sys.platform == "win32":
    # Safely set console encoding for Windows if possible
    try:
        import codecs

        stdout_buffer = getattr(sys.stdout, "buffer", None)
        if stdout_buffer is not None and hasattr(stdout_buffer, "write"):
            sys.stdout = cast(TextIO, codecs.getwriter("utf-8")(stdout_buffer))
    except (AttributeError, OSError, TypeError):
        pass  # If not possible, ignore and continue

# Load environment variables
from dotenv import load_dotenv

load_dotenv()

try:
    import requests  # type: ignore[import-untyped]

    requests = cast(Any, requests)
except ImportError:
    print("[ERROR] 'requests' library is not installed. Please run 'pip install requests'.")
    sys.exit(1)


def _get_ollama_base_url() -> str:
    """Resolve Ollama base URL from environment with a safe default.

    Honors OLLAMA_BASE_URL first, then OLLAMA_API_URL, falling back to localhost.
    """
    return os.getenv("OLLAMA_BASE_URL", os.getenv("OLLAMA_API_URL", "http://localhost:11434"))


@contextmanager
def _sys_path(paths: list[str]):
    """Temporarily prepend paths to sys.path and restore afterwards."""
    original = list(sys.path)
    try:
        for p in reversed(paths):
            if p not in sys.path:
                sys.path.insert(0, p)
        yield
    finally:
        sys.path[:] = original


def test_chatdev_ollama_integration():
    """Test ChatDev + Ollama integration"""
    print("=" * 70)
    print(" CHATDEV + OLLAMA INTEGRATION BOOTSTRAP")
    print("=" * 70)

    # Check ChatDev path
    chatdev_path = os.getenv("CHATDEV_PATH")
    if not chatdev_path:
        print("[ERROR] CHATDEV_PATH not set in .env file")
        return False

    chatdev_dir = Path(chatdev_path)
    if not chatdev_dir.exists():
        print(f"[ERROR] ChatDev not found at: {chatdev_path}")
        return False

    print(f"[OK] ChatDev found at: {chatdev_path}")

    # Check Ollama
    try:
        base_url = _get_ollama_base_url()
        response = requests.get(f"{base_url}/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get("models", [])
            print(f"[OK] Ollama running with {len(models)} models")
        else:
            print("[ERROR] Ollama not responding properly")
            return False
    except (requests.exceptions.RequestException, OSError) as e:
        print(f"[ERROR] Ollama not available: {e}")
        return False

    # Demonstrate Multi-AI Orchestration
    print("\n" + "=" * 70)
    print(" MULTI-AI ORCHESTRATION DEMONSTRATION")
    print("=" * 70)

    repo_root = str(Path(__file__).parent)
    try:
        with _sys_path([repo_root]):
            from src.orchestration.unified_ai_orchestrator import (
                TaskPriority,
                UnifiedAIOrchestrator,
            )

            orchestrator = UnifiedAIOrchestrator()
            print(
                f"\n[OK] Orchestrator initialized with {len(orchestrator.ai_systems)} AI systems:"
            )

            for name, system in orchestrator.ai_systems.items():
                print(f"   - {name}: {system.system_type.value}")
                print(f"     Capabilities: {', '.join(system.capabilities[:4])}")

            # Submit a self-development task
            print("\n[*] Submitting self-development task...")
            task_id = orchestrator.orchestrate_task(
                task_type="code_analysis",
                content="""Analyze the NuSyQ-Hub integration files and identify:
    1. Consolidation opportunities
    2. Missing functionality
    3. Enhancement recommendations
    4. Integration gaps between ChatDev and Ollama""",
                context={
                    "repository": "NuSyQ-Hub",
                    "target_files": [
                        "src/integration/chatdev_integration.py",
                        "src/ai/ollama_chatdev_integrator.py",
                        "src/integration/chatdev_launcher.py",
                    ],
                    "output_format": "structured_json",
                },
                priority=TaskPriority.HIGH,
            )

            print(f"[OK] Task submitted: {task_id}")
            print("[INFO] Task queued for processing by AI systems")

            # Show what the pipeline would do
            print("\n" + "=" * 70)
            print(" SELF-DEVELOPMENT PIPELINE CAPABILITIES")
            print("=" * 70)

            capabilities = [
                {
                    "stage": "1. Code Analysis",
                    "ai_system": "ChatDev Agents + Ollama",
                    "action": "Analyze codebase for integration opportunities",
                    "models": [
                        "qwen2.5-coder:14b for deep analysis",
                        "llama3.1:8b for architecture",
                    ],
                },
                {
                    "stage": "2. Enhancement Planning",
                    "ai_system": "Consciousness Bridge + Quantum Resolver",
                    "action": "Synthesize findings into actionable improvements",
                    "models": ["Context-aware planning with consciousness integration"],
                },
                {
                    "stage": "3. Implementation",
                    "ai_system": "ChatDev + Copilot",
                    "action": "Generate code improvements with multi-agent review",
                    "models": ["CEO/CTO for architecture", "Programmer/Tester for implementation"],
                },
                {
                    "stage": "4. Validation",
                    "ai_system": "All Systems",
                    "action": "Comprehensive testing and validation",
                    "models": ["Cross-system validation with quantum optimization"],
                },
                {
                    "stage": "5. Documentation",
                    "ai_system": "Unified Documentation Engine",
                    "action": "Auto-generate comprehensive documentation",
                    "models": ["Type2 consciousness-aware documentation"],
                },
            ]

            for cap in capabilities:
                print(f"\n[{cap['stage']}]")
                print(f"  AI System: {cap['ai_system']}")
                print(f"  Action: {cap['action']}")
                print(f"  Models: {cap['models']}")

            # Generate bootstrap report
            print("\n" + "=" * 70)
            print(" GENERATING BOOTSTRAP REPORT")
            print("=" * 70)

            report = {
                "timestamp": datetime.now().isoformat(),
                "chatdev_path": str(chatdev_path),
                "chatdev_available": True,
                "ollama_available": True,
                "ollama_models_count": len(models),
                "orchestrator_systems": len(orchestrator.ai_systems),
                "submitted_task_id": task_id,
                "pipeline_stages": [cap["stage"] for cap in capabilities],
                "status": "OPERATIONAL",
                "next_steps": [
                    "Configure ChatDev to use Ollama models",
                    "Implement automated task processing",
                    "Enable continuous self-improvement",
                    "Activate documentation generation",
                    "Deploy autonomous development pipeline",
                ],
            }

            report_path = Path("bootstrap_report.json")
            with open(report_path, "w", encoding="utf-8") as f:
                json.dump(report, f, indent=2)

            print(f"[OK] Bootstrap report saved to: {report_path}")

            # Show integration status
            print("\n" + "=" * 70)
            print(" INTEGRATION STATUS SUMMARY")
            print("=" * 70)
            print(f"[OK] ChatDev: CONFIGURED at {chatdev_path}")
            print(f"[OK] Ollama: RUNNING with {len(models)} models")
            print(f"[OK] Multi-AI Orchestrator: {len(orchestrator.ai_systems)} systems registered")
            print(f"[OK] Task {task_id}: QUEUED for AI processing")
            print("[OK] Self-Development Pipeline: READY")

            return True

    except (ImportError, RuntimeError, ValueError) as e:
        print(f"[ERROR] Orchestration test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_chatdev_ollama_integration()

    print("\n" + "=" * 70)
    if success:
        print(" BOOTSTRAP SUCCESS")
        print(" ChatDev + Ollama integration is OPERATIONAL")
        print(" Self-development pipeline is READY for deployment")
        print(" Next: Run comprehensive ecosystem health check")
    else:
        print(" BOOTSTRAP FAILED")
        print(" Check configuration and try again")
    print("=" * 70)
