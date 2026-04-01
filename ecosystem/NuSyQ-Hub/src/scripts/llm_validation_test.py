#!/usr/bin/env python3
"""🔬 LLM FUNCTIONALITY VALIDATION TEST.

Following AI Intermediary recommendations to prove infrastructure before expanding.

This is the critical test to validate our 72% functional LLM infrastructure

OmniTag: {
    "purpose": "file_systematically_tagged",
    "tags": ["LLM", "Python", "AI", "Testing"],
    "category": "auto_tagged",
    "evolution_stage": "v1.0"
}
"""

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


def test_ollama_service():
    """Test if Ollama is running and available."""
    try:
        # Test ollama version
        result = subprocess.run(
            ["ollama", "--version"],
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )

        if result.returncode == 0:
            # Test model list
            models_result = subprocess.run(
                ["ollama", "list"],
                check=False,
                capture_output=True,
                text=True,
                timeout=10,
            )

            if models_result.returncode == 0:
                models_output = models_result.stdout.strip()
                return True, models_output
            return False, models_result.stderr
        return False, result.stderr

    except FileNotFoundError:
        return False, "Ollama executable not found"
    except subprocess.TimeoutExpired:
        return False, "Command timeout"
    except (OSError, RuntimeError) as e:
        return False, str(e)


def test_chatdev_integration():
    """Test ChatDev integration components."""
    # Add src to path
    repo_root = Path(__file__).parent
    src_path = repo_root / "src"
    sys.path.insert(0, str(src_path))

    results: dict[str, Any] = {}
    # Test ChatDev launcher import
    try:
        from integration.chatdev_launcher import ChatDevLauncher

        launcher = ChatDevLauncher()
        results["launcher"] = True

        # Test API key setup
        api_setup = launcher.setup_api_key()
        results["api_key"] = api_setup

    except (ImportError, AttributeError):
        results["launcher"] = False

    # Test Ollama integrator
    try:
        from ai.ollama_chatdev_integrator import OllamaChatDevIntegrator

        integrator = OllamaChatDevIntegrator()
        results["integrator"] = True

        # Test model listing (if method exists)
        if hasattr(integrator, "get_ollama_models"):
            models = integrator.get_ollama_models()
            results["models"] = len(models) if models else 0
        else:
            results["models"] = 0

    except (ImportError, AttributeError, RuntimeError):
        results["integrator"] = False

    return results


def test_ai_intermediary() -> bool | None:
    """Test AI Intermediary system."""
    try:
        # Add src to path
        repo_root = Path(__file__).parent
        src_path = repo_root / "src"
        sys.path.insert(0, str(src_path))

        from ai.ai_intermediary import CognitiveParadigm

        # Test basic import and initialization
        # Test cognitive paradigm system
        list(CognitiveParadigm)

        return True

    except (ImportError, AttributeError, ValueError):
        return False


def generate_validation_report():
    """Generate comprehensive validation report."""
    report: dict[str, Any] = {
        "timestamp": datetime.now().isoformat(),
        "test_type": "llm_functionality_validation",
        "purpose": "Validate 72% functional LLM infrastructure following AI Intermediary recommendations",
    }

    # Run all tests
    ollama_status, ollama_details = test_ollama_service()
    chatdev_results = test_chatdev_integration()
    intermediary_status = test_ai_intermediary()

    # Compile results
    report["results"] = {
        "ollama": {
            "available": ollama_status,
            "details": ollama_details,
        },
        "chatdev": chatdev_results,
        "ai_intermediary": {
            "available": intermediary_status,
        },
    }

    # Calculate functionality score
    functionality_checks = [
        ollama_status,
        chatdev_results.get("launcher", False),
        chatdev_results.get("integrator", False),
        intermediary_status,
    ]

    functionality_score = sum(functionality_checks) / len(functionality_checks) * 100
    report["functionality_score"] = round(functionality_score, 1)

    # Generate verdict
    if functionality_score >= 75:
        verdict = "🟢 CONFIRMED GAS - Infrastructure is highly functional"
    elif functionality_score >= 50:
        verdict = "🟡 MIXED RESULTS - Partial functionality confirmed"
    else:
        verdict = "🔴 NEEDS ATTENTION - Major functionality issues detected"

    report["verdict"] = verdict

    # Save report
    report_file = Path(__file__).parent / "LLM_VALIDATION_REPORT.json"
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    return report, report_file


def main() -> None:
    """Main validation process."""
    # Generate comprehensive validation report
    _, _report_file = generate_validation_report()

    # AI Intermediary recommendation - functionality score check
    # Score >= 70 indicates healthy LLM infrastructure


if __name__ == "__main__":
    main()
