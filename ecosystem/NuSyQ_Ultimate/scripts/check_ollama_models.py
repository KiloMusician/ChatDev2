#!/usr/bin/env python3
"""
Check Ollama models availability and save report.
"""

import json
import subprocess
from datetime import datetime
from pathlib import Path


def check_ollama_models() -> dict:
    """Check available Ollama models."""
    report = {
        "timestamp": datetime.now().isoformat(),
        "ollama_running": False,
        "models": [],
        "status": "unknown",
        "error": None,
    }

    try:
        # Try to list models
        result = subprocess.run(
            ["ollama", "list"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )

        if result.returncode == 0:
            report["ollama_running"] = True
            report["status"] = "operational"

            # Parse output
            lines = result.stdout.strip().split("\n")[1:]  # Skip header
            for line in lines:
                if line.strip():
                    parts = line.split()
                    if len(parts) >= 2:
                        report["models"].append(
                            {
                                "name": parts[0],
                                "size": parts[1] if len(parts) > 1 else "unknown",
                            }
                        )
        else:
            report["error"] = result.stderr
            report["status"] = "error"

    except FileNotFoundError:
        report["error"] = "Ollama not installed or not in PATH"
        report["status"] = "not_installed"
    except subprocess.TimeoutExpired:
        report["error"] = "Ollama server not responding (timeout)"
        report["status"] = "timeout"
    except (OSError, ValueError, TypeError) as e:
        report["error"] = str(e)
        report["status"] = "error"

    return report


def save_ollama_report(report: dict) -> None:
    """Save Ollama status report to receipts."""
    receipt_dir = Path.cwd() / "state" / "receipts" / "ollama"
    receipt_dir.mkdir(parents=True, exist_ok=True)

    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    receipt_file = receipt_dir / f"models_{timestamp_str}.json"

    with open(receipt_file, "w") as f:
        json.dump(report, f, indent=2, default=str)

    print(f"✓ Ollama report saved: {receipt_file}")


def print_ollama_status(report: dict) -> None:
    """Print Ollama status in human-readable format."""
    print("\n" + "=" * 80)
    print("OLLAMA MODELS STATUS")
    print("=" * 80)
    print(f"Status: {report['status'].upper()}")
    print(f"Timestamp: {report['timestamp']}")

    if report["ollama_running"]:
        print(f"\nAvailable Models ({len(report['models'])}):")
        for model in report["models"]:
            print(f"  • {model['name']} ({model['size']})")
    else:
        print(f"\n❌ Error: {report['error']}")
        print("\nTroubleshooting:")
        print("  1. Ensure Ollama is installed: https://ollama.ai")
        print("  2. Start Ollama service: ollama serve")
        print("  3. For this project, run: C:\\Users\\keath\\NuSyQ\\NuSyQ.Orchestrator.ps1")


if __name__ == "__main__":
    report = check_ollama_models()
    print_ollama_status(report)
    save_ollama_report(report)
