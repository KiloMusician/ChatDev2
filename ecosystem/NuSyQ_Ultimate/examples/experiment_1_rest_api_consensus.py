"""
Experiment 1: REST API Multi-Model Consensus
============================================

Run multi-model consensus on REST API generation with 3 models
"""

import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent))

from consensus_orchestrator import ConsensusOrchestrator


def main():
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║  Experiment 1: REST API Multi-Model Consensus               ║")
    print("╚══════════════════════════════════════════════════════════════╝\n")

    # Use 3 coding-focused models
    models = [
        "qwen2.5-coder:14b",  # 9GB - Primary coding specialist
        "codellama:7b",  # 3.8GB - Meta's coding model
        "qwen2.5-coder:7b",  # 4.7GB - Lighter qwen variant
    ]

    task = """Create a Python REST API with the following requirements:
- JWT authentication
- User registration endpoint (/api/register)
- Login endpoint (/api/login)
- Protected resource endpoint (/api/protected)
- Use Flask or FastAPI
- Include basic error handling
- Keep it simple and production-ready

Provide complete working code."""

    print("🎯 Task: REST API with JWT Auth")
    print(f"🤖 Models: {len(models)} coding specialists")
    print("📊 Metrics: Syntax, Semantics, Security, Quality\n")

    orchestrator = ConsensusOrchestrator(models)
    result = orchestrator.run_consensus(task, voting="simple", max_tokens=1000)

    # Additional analysis
    print("\n╔══════════════════════════════════════════════════════════════╗")
    print("║  EXPERIMENT ANALYSIS                                         ║")
    print("╚══════════════════════════════════════════════════════════════╝\n")

    successful = [r for r in result.responses if r.success]

    # Framework detection
    print("🔍 Framework Selection:")
    for r in successful:
        if "flask" in r.response.lower():
            framework = "Flask"
        elif "fastapi" in r.response.lower():
            framework = "FastAPI"
        else:
            framework = "Unknown"
        print(f"  [{r.model}]: {framework}")

    # JWT implementation check
    print("\n🔒 JWT Implementation:")
    for r in successful:
        has_jwt = "jwt" in r.response.lower() or "pyjwt" in r.response.lower()
        print(f"  [{r.model}]: {'✅ Included' if has_jwt else '❌ Missing'}")

    # Code quality indicators
    print("\n✨ Code Quality Indicators:")
    for r in successful:
        has_error_handling = (
            "try" in r.response.lower() or "except" in r.response.lower()
        )
        has_validation = (
            "validate" in r.response.lower() or "check" in r.response.lower()
        )
        has_docs = '"""' in r.response or "'''" in r.response

        print(f"  [{r.model}]:")
        print(f"    Error Handling: {'✅' if has_error_handling else '❌'}")
        print(f"    Validation: {'✅' if has_validation else '❌'}")
        print(f"    Documentation: {'✅' if has_docs else '❌'}")

    print("\n" + "=" * 60)
    print(f"🏆 Consensus Quality: {result.agreement_rate * 100:.1f}% agreement")
    print(f"⏱️  Efficiency: {result.total_duration_sec:.1f}s total")
    print("=" * 60 + "\n")

    return result


if __name__ == "__main__":
    result = main()
