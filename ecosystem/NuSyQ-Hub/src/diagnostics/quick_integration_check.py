#!/usr/bin/env python3
"""🔍 KILO-FOOLISH Integration Status Quick Check.

Direct file-based analysis of system integration status.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any

# Centralized service configuration using factory pattern
from src.utils.config_factory import get_service_config

try:
    from src.utils.config_helper import get_ollama_host
except (ImportError, ModuleNotFoundError):
    get_ollama_host = None  # type: ignore[assignment]


def quick_system_check():
    """Quick system integration check with file output."""
    repo_root = Path.cwd()
    results: dict[str, Any] = {
        "timestamp": datetime.now().isoformat(),
        "system_check": "KILO-FOOLISH Integration Status",
        "checks": {},
    }

    # 1. Check Ollama
    try:
        import requests

        config = get_service_config()
        ollama_url = (
            (get_ollama_host() if callable(get_ollama_host) else None)
            or (
                config._config.get_ollama_url()  # type: ignore[union-attr]
                if config and hasattr(config._config, "get_ollama_url")
                else None
            )
            or os.getenv("OLLAMA_BASE_URL")
            or f"{os.getenv('OLLAMA_HOST', 'http://127.0.0.1')}:{os.getenv('OLLAMA_PORT', '11435')}"
        )
        response = requests.get(f"{ollama_url}/api/tags", timeout=5)
        if response.status_code == 200:
            data = response.json()
            models = data.get("models", [])
            results["checks"]["ollama"] = {
                "status": "RUNNING",
                "models_count": len(models),
                "models": [m["name"] for m in models[:3]],  # First 3 models
            }
        else:
            results["checks"]["ollama"] = {
                "status": "API_ERROR",
                "code": response.status_code,
            }
    except ImportError:
        results["checks"]["ollama"] = {"status": "REQUESTS_MISSING"}
    except Exception as e:
        results["checks"]["ollama"] = {"status": "NOT_RUNNING", "error": str(e)}

    # 2. Check ChatDev files
    chatdev_files = [
        "src/integration/chatdev_llm_adapter.py",
        "src/integration/chatdev_launcher.py",
        "src/ai/ollama_chatdev_integrator.py",
    ]

    results["checks"]["chatdev_files"] = {}
    for file_path in chatdev_files:
        path = repo_root / file_path
        if path.exists():
            size_kb = round(path.stat().st_size / 1024, 1)
            results["checks"]["chatdev_files"][file_path] = {
                "exists": True,
                "size_kb": size_kb,
            }
        else:
            results["checks"]["chatdev_files"][file_path] = {"exists": False}

    # 3. Check Copilot files
    copilot_files = [
        ".copilot/copilot_enhancement_bridge.py",
        ".github/instructions/COPILOT_INSTRUCTIONS_CONFIG.instructions.md",
        ".github/instructions/NuSyQ-Hub_INSTRUCTIONS.instructions.md",
    ]

    results["checks"]["copilot_files"] = {}
    for file_path in copilot_files:
        path = repo_root / file_path
        if path.exists():
            size_kb = round(path.stat().st_size / 1024, 1)
            results["checks"]["copilot_files"][file_path] = {
                "exists": True,
                "size_kb": size_kb,
            }
        else:
            results["checks"]["copilot_files"][file_path] = {"exists": False}

    # 4. Test imports
    results["checks"]["python_imports"] = {}
    test_modules = ["requests", "psutil", "pathlib", "json"]

    for module in test_modules:
        try:
            __import__(module)
            results["checks"]["python_imports"][module] = {"available": True}
        except ImportError:
            results["checks"]["python_imports"][module] = {"available": False}

    # 5. Directory structure check
    important_dirs = [
        "src/core",
        "src/ai",
        "src/integration",
        "src/consciousness",
        "logs/storage",
    ]
    results["checks"]["directories"] = {}

    for dir_path in important_dirs:
        path = repo_root / dir_path
        if path.exists():
            py_files = len(list(path.glob("*.py")))
            results["checks"]["directories"][dir_path] = {
                "exists": True,
                "python_files": py_files,
            }
        else:
            results["checks"]["directories"][dir_path] = {"exists": False}

    # Save results
    output_path = repo_root / "data" / "logs" / "quick_integration_check.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    # Create summary report
    summary_lines = [
        "# 🔍 KILO-FOOLISH Integration Status Summary",
        f"**Generated:** {results['timestamp']}",
        "",
        "## 🦙 Ollama Status",
        f"**Status:** {results['checks']['ollama']['status']}",
    ]

    if results["checks"]["ollama"]["status"] == "RUNNING":
        summary_lines.extend(
            [
                f"**Models:** {results['checks']['ollama']['models_count']}",
                f"**Available:** {', '.join(results['checks']['ollama']['models'])}",
            ]
        )

    summary_lines.extend(
        [
            "",
            "## 🤖 ChatDev Integration Files",
        ]
    )

    for file_path, info in results["checks"]["chatdev_files"].items():
        status = "✅" if info["exists"] else "❌"
        size_info = f" ({info['size_kb']} KB)" if info["exists"] else ""
        summary_lines.append(f"- {status} `{file_path}`{size_info}")

    summary_lines.extend(
        [
            "",
            "## 🤖 Copilot Enhancement Files",
        ]
    )

    for file_path, info in results["checks"]["copilot_files"].items():
        status = "✅" if info["exists"] else "❌"
        size_info = f" ({info['size_kb']} KB)" if info["exists"] else ""
        summary_lines.append(f"- {status} `{file_path}`{size_info}")

    summary_lines.extend(
        [
            "",
            "## 🐍 Python Dependencies",
        ]
    )

    for module, info in results["checks"]["python_imports"].items():
        status = "✅" if info["available"] else "❌"
        summary_lines.append(f"- {status} {module}")

    summary_lines.extend(
        [
            "",
            "## 📁 Directory Structure",
        ]
    )

    for dir_path, info in results["checks"]["directories"].items():
        status = "✅" if info["exists"] else "❌"
        file_info = f" ({info['python_files']} .py files)" if info["exists"] else ""
        summary_lines.append(f"- {status} `{dir_path}`{file_info}")

    # Calculate health score
    total_checks = 0
    passed_checks = 0

    # Ollama check
    total_checks += 1
    if results["checks"]["ollama"]["status"] == "RUNNING":
        passed_checks += 1

    # File checks
    for category in ["chatdev_files", "copilot_files"]:
        for file_info in results["checks"][category].values():
            total_checks += 1
            if file_info["exists"]:
                passed_checks += 1

    # Import checks
    for import_info in results["checks"]["python_imports"].values():
        total_checks += 1
        if import_info["available"]:
            passed_checks += 1

    # Directory checks
    for dir_info in results["checks"]["directories"].values():
        total_checks += 1
        if dir_info["exists"]:
            passed_checks += 1

    health_score = round((passed_checks / total_checks) * 100)

    if health_score >= 80:
        health_status = "🟢 EXCELLENT"
    elif health_score >= 60:
        health_status = "🟡 GOOD"
    elif health_score >= 40:
        health_status = "🟠 FAIR"
    else:
        health_status = "🔴 NEEDS ATTENTION"

    summary_lines.extend(
        [
            "",
            f"## 🎯 Overall Health: {health_status} ({health_score}/100)",
            f"**Passed:** {passed_checks}/{total_checks} checks",
            "",
            "---",
            f"*Report saved to: `{output_path}`*",
        ]
    )

    # Save summary
    summary_path = repo_root / "docs" / "reports" / "integration_status_summary.md"
    summary_path.parent.mkdir(parents=True, exist_ok=True)

    with open(summary_path, "w", encoding="utf-8") as f:
        f.write("\n".join(summary_lines))

    return results


if __name__ == "__main__":
    quick_system_check()
