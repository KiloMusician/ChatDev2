#!/usr/bin/env python3
"""🔍 KILO-FOOLISH System Integration Status Checker.

Comprehensive analysis of Ollama, ChatDev, and Copilot integration status.

OmniTag: {
    "purpose": "system_integration_analysis",
    "type": "diagnostic_tool",
    "evolution_stage": "v4.0_comprehensive"
}
MegaTag: {
    "scope": "system_health_check",
    "integration_points": ["ollama", "chatdev", "copilot", "consciousness"],
    "quantum_context": "system_awareness_validation"
}
RSHTS: ΞΨΩ∞⟨SYSTEM_ANALYSIS⟩→ΦΣΣ⟨STATUS⟩
"""

import json
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, cast

import requests

logger = logging.getLogger(__name__)

_ServiceConfig: Any = None
_get_ollama_host: Any = None

try:
    from src.config.service_config import ServiceConfig

    _ServiceConfig = ServiceConfig
except (ImportError, ModuleNotFoundError):
    pass

try:
    from src.utils.config_helper import get_ollama_host

    _get_ollama_host = get_ollama_host
except (ImportError, ModuleNotFoundError):
    pass

try:
    import psutil

    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False


class KILOSystemStatusChecker:
    """Comprehensive system status checker for KILO-FOOLISH integrations."""

    def __init__(self) -> None:
        """Initialize KILOSystemStatusChecker."""
        self.repo_root = Path.cwd()
        self.status_report = {
            "timestamp": datetime.now().isoformat(),
            "ollama_status": {},
            "chatdev_status": {},
            "copilot_status": {},
            "integration_status": {},
            "process_status": {},
            "health_score": 0,
        }

    def check_ollama_status(self) -> dict[str, Any]:
        """Check Ollama service and model status."""
        ollama_status: dict[str, Any] = {
            "service_running": False,
            "api_responsive": False,
            "models_available": [],
            "models_count": 0,
            "total_size_gb": 0,
            "response_time": None,
            "errors": [],
        }

        try:
            # Test API connectivity
            start_time = time.time()
            host_result = _get_ollama_host() if callable(_get_ollama_host) else None
            config_result = _ServiceConfig.get_ollama_url() if _ServiceConfig is not None else None
            env_result = os.getenv("OLLAMA_BASE_URL")
            fallback_result = f"{os.getenv('OLLAMA_HOST', 'http://127.0.0.1')}:{os.getenv('OLLAMA_PORT', '11435')}"
            ollama_url = host_result or config_result or env_result or fallback_result
            response = requests.get(f"{ollama_url}/api/tags", timeout=10)
            response_time = time.time() - start_time

            if response.status_code == 200:
                ollama_status["service_running"] = True
                ollama_status["api_responsive"] = True
                ollama_status["response_time"] = response_time

                data = response.json()
                models = data.get("models", [])
                ollama_status["models_count"] = len(models)

                for model in models:
                    model_info = {
                        "name": model["name"],
                        "size_gb": round(model.get("size", 0) / (1024**3), 2),
                        "modified": model.get("modified_at", ""),
                        "digest": (
                            model.get("digest", "")[:12] + "..." if model.get("digest") else ""
                        ),
                    }
                    ollama_status["models_available"].append(model_info)
                    ollama_status["total_size_gb"] += model_info["size_gb"]

                ollama_status["total_size_gb"] = round(ollama_status["total_size_gb"], 2)

            else:
                ollama_status["errors"].append(f"API returned status {response.status_code}")

        except requests.exceptions.ConnectionError:
            ollama_status["errors"].append("Connection refused - service not running")
        except (requests.RequestException, ValueError, KeyError) as e:
            ollama_status["errors"].append(str(e))

        return ollama_status

    def check_chatdev_status(self) -> dict[str, Any]:
        """Check ChatDev integration status."""
        chatdev_status: dict[str, Any] = {
            "integration_files_present": {},
            "chatdev_installed": False,
            "launcher_functional": False,
            "adapter_available": False,
            "ollama_integration": False,
            "warehouse_projects": 0,
            "errors": [],
        }

        # Check key integration files
        integration_files = {
            "chatdev_llm_adapter": "src/integration/chatdev_llm_adapter.py",
            "chatdev_launcher": "src/integration/chatdev_launcher.py",
            "ollama_chatdev_integrator": "src/ai/ollama_chatdev_integrator.py",
            "update_chatdev_ollama": "src/integration/Update-ChatDev-to-use-Ollama.py",
            "chatdev_testing_chamber": "src/orchestration/chatdev_testing_chamber.py",
        }

        for name, file_path in integration_files.items():
            path = self.repo_root / file_path
            if path.exists():
                size_kb = round(path.stat().st_size / 1024, 1)
                chatdev_status["integration_files_present"][name] = {
                    "exists": True,
                    "size_kb": size_kb,
                    "path": str(path),
                }
            else:
                chatdev_status["integration_files_present"][name] = {
                    "exists": False,
                    "path": str(path),
                }

        # Test Python imports
        try:
            sys.path.insert(0, str(self.repo_root / "src"))

            # Test launcher import
            try:
                from integration.chatdev_launcher import ChatDevLauncher

                chatdev_status["launcher_functional"] = True
                # Mark that we've verified the launcher can be imported
                assert ChatDevLauncher is not None
            except (ImportError, AssertionError) as e:
                chatdev_status["errors"].append(f"Launcher import failed: {e}")

            # Test adapter import
            try:
                from integration.chatdev_llm_adapter import ChatDevLLMAdapter

                chatdev_status["adapter_available"] = True
                # Mark that we've verified the adapter can be imported
                assert ChatDevLLMAdapter is not None
            except (ImportError, AssertionError) as e:
                chatdev_status["errors"].append(f"Adapter import failed: {e}")

            # Test Ollama integrator
            try:
                from ai.ollama_chatdev_integrator import \
                    EnhancedOllamaChatDevIntegrator

                chatdev_status["ollama_integration"] = True
                # Mark that we've verified the integrator can be imported
                assert EnhancedOllamaChatDevIntegrator is not None
            except (ImportError, AssertionError) as e:
                chatdev_status["errors"].append(f"Ollama integrator import failed: {e}")

        except (ImportError, AttributeError, ValueError) as e:
            chatdev_status["errors"].append(f"Import test failed: {e}")

        # Check for ChatDev projects
        try:
            warehouse_paths = [
                self.repo_root / "ChatDev" / "WareHouse",
                self.repo_root / "WareHouse",
                self.repo_root / "chatdev" / "WareHouse",
            ]

            for warehouse_path in warehouse_paths:
                if warehouse_path.exists():
                    projects = list(warehouse_path.glob("*"))
                    chatdev_status["warehouse_projects"] = len(projects)
                    break

        except (OSError, ValueError) as e:
            chatdev_status["errors"].append(f"Warehouse check failed: {e}")

        return chatdev_status

    def check_copilot_status(self) -> dict[str, Any]:
        """Check Copilot enhancements and integrations."""
        copilot_status: dict[str, Any] = {
            "enhancement_bridge_present": False,
            "context_files_present": {},
            "documentation_status": {},
            "integration_functional": False,
            "errors": [],
        }

        # Check key Copilot files
        copilot_files = {
            "enhancement_bridge": ".copilot/copilot_enhancement_bridge.py",
            "context_md": ".copilot/context.md",
            "instructions_config": ".github/instructions/COPILOT_INSTRUCTIONS_CONFIG.instructions.md",
            "hub_instructions": ".github/instructions/NuSyQ-Hub_INSTRUCTIONS.instructions.md",
            "file_preservation": ".github/instructions/FILE_PRESERVATION_MANDATE.instructions.md",
        }

        for name, file_path in copilot_files.items():
            path = self.repo_root / file_path
            if path.exists():
                size_kb = round(path.stat().st_size / 1024, 1)
                copilot_status["context_files_present"][name] = {
                    "exists": True,
                    "size_kb": size_kb,
                    "last_modified": datetime.fromtimestamp(path.stat().st_mtime).isoformat(),
                }

                if name == "enhancement_bridge":
                    copilot_status["enhancement_bridge_present"] = True
            else:
                copilot_status["context_files_present"][name] = {"exists": False}

        # Check documentation status
        docs_dirs = ["docs", "docs/reports", "docs/archive"]
        for docs_dir in docs_dirs:
            path = self.repo_root / docs_dir
            if path.exists():
                file_count = len(list(path.glob("*.md")))
                copilot_status["documentation_status"][docs_dir] = file_count

        return copilot_status

    def check_process_status(self) -> dict[str, Any]:
        """Check running processes related to our systems."""
        process_status: dict[str, Any] = {
            "vscode_processes": 0,
            "powershell_sessions": 0,
            "python_processes": 0,
            "ollama_processes": 0,
            "system_load": {},
            "errors": [],
        }

        if not PSUTIL_AVAILABLE:
            process_status["errors"].append("psutil not available - limited process info")
            return process_status

        try:
            # Scan processes
            for proc in psutil.process_iter(["pid", "name", "cmdline"]):
                try:
                    proc_info = proc.info
                    proc_name = proc_info["name"].lower()
                    cmdline = " ".join(proc_info["cmdline"] or []).lower()

                    if "code" in proc_name or "vscode" in proc_name:
                        process_status["vscode_processes"] += 1
                    elif "powershell" in proc_name or "pwsh" in proc_name:
                        process_status["powershell_sessions"] += 1
                    elif "python" in proc_name:
                        if self.repo_root.name.lower() in cmdline:
                            process_status["python_processes"] += 1
                    elif "ollama" in proc_name or "ollama" in cmdline:
                        process_status["ollama_processes"] += 1

                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

            # System metrics
            process_status["system_load"] = {
                "cpu_percent": psutil.cpu_percent(interval=1),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_usage_percent": (
                    psutil.disk_usage("/").percent
                    if os.name != "nt"
                    else psutil.disk_usage("C:\\").percent
                ),
            }

        except (OSError, ValueError, RuntimeError) as e:
            process_status["errors"].append(str(e))

        return process_status

    def calculate_health_score(self) -> int:
        """Calculate overall system health score (0-100)."""
        score = 0

        ollama_status = cast(dict[str, Any], self.status_report["ollama_status"])
        chatdev_status = cast(dict[str, Any], self.status_report["chatdev_status"])
        copilot_status = cast(dict[str, Any], self.status_report["copilot_status"])
        process_status = cast(dict[str, Any], self.status_report["process_status"])

        # Ollama (30 points)
        if ollama_status["service_running"]:
            score += 15
        if ollama_status["models_count"] > 0:
            score += 15

        # ChatDev (40 points)
        functional_files = sum(
            1 for f in chatdev_status["integration_files_present"].values() if f["exists"]
        )
        score += min(20, functional_files * 4)  # Up to 20 points for files

        if chatdev_status["launcher_functional"]:
            score += 10
        if chatdev_status["adapter_available"]:
            score += 10

        # Copilot (20 points)
        if copilot_status["enhancement_bridge_present"]:
            score += 10
        context_files = sum(
            1 for f in copilot_status["context_files_present"].values() if f["exists"]
        )
        score += min(10, context_files * 2)

        # Process health (10 points)
        if process_status["vscode_processes"] > 0:
            score += 5
        if len(process_status["errors"]) == 0:
            score += 5

        return min(100, score)

    def generate_status_report(self) -> str:
        """Generate comprehensive status report."""
        health_score = self.calculate_health_score()

        if health_score >= 80:
            health_status = "🟢 EXCELLENT"
        elif health_score >= 60:
            health_status = "🟡 GOOD"
        elif health_score >= 40:
            health_status = "🟠 FAIR"
        else:
            health_status = "🔴 NEEDS ATTENTION"

        ollama_status = cast(dict[str, Any], self.status_report["ollama_status"])
        chatdev_status = cast(dict[str, Any], self.status_report["chatdev_status"])
        copilot_status = cast(dict[str, Any], self.status_report["copilot_status"])
        process_status = cast(dict[str, Any], self.status_report["process_status"])

        report = f"""
# 🔍 KILO-FOOLISH System Integration Status Report

**Generated:** {self.status_report["timestamp"]}
**Overall Health:** {health_status} ({health_score}/100)

---

## 🦙 Ollama LLM Status

**Service Status:** {"🟢 RUNNING" if ollama_status["service_running"] else "🔴 NOT RUNNING"}
**API Responsive:** {"✅ Yes" if ollama_status["api_responsive"] else "❌ No"}
**Available Models:** {ollama_status["models_count"]}
**Total Size:** {ollama_status["total_size_gb"]} GB

"""

        if ollama_status["models_available"]:
            report += "### Available Models:\n"
            for model in ollama_status["models_available"]:
                report += f"- **{model['name']}** ({model['size_gb']} GB)\n"

        if ollama_status["errors"]:
            report += "\n### Ollama Issues:\n"
            for error in ollama_status["errors"]:
                report += f"- ❌ {error}\n"

        report += f"""

---

## 🤖 ChatDev Integration Status

**Integration Files Present:** {sum(1 for f in chatdev_status["integration_files_present"].values() if f["exists"])}/5
**Launcher Functional:** {"✅ Yes" if chatdev_status["launcher_functional"] else "❌ No"}
**Adapter Available:** {"✅ Yes" if chatdev_status["adapter_available"] else "❌ No"}
**Ollama Integration:** {"✅ Yes" if chatdev_status["ollama_integration"] else "❌ No"}
**Warehouse Projects:** {chatdev_status["warehouse_projects"]}

### Integration Files Status:
"""

        for name, info in chatdev_status["integration_files_present"].items():
            status_icon = "✅" if info["exists"] else "❌"
            size_info = f" ({info['size_kb']} KB)" if info["exists"] else ""
            report += f"- {status_icon} **{name}**{size_info}\n"

        if chatdev_status["errors"]:
            report += "\n### ChatDev Issues:\n"
            for error in chatdev_status["errors"]:
                report += f"- ❌ {error}\n"

        report += f"""

---

## 🤖 Copilot Enhancement Status

**Enhancement Bridge:** {"✅ Present" if copilot_status["enhancement_bridge_present"] else "❌ Missing"}
**Context Files:** {sum(1 for f in copilot_status["context_files_present"].values() if f["exists"])}/5

### Context Files Status:
"""

        for name, info in copilot_status["context_files_present"].items():
            if info["exists"]:
                report += f"- ✅ **{name}** ({info['size_kb']} KB)\n"
            else:
                report += f"- ❌ **{name}** (missing)\n"

        report += """

### Documentation Status:
"""
        for docs_dir, count in copilot_status["documentation_status"].items():
            report += f"- 📚 **{docs_dir}**: {count} files\n"

        report += f"""

---

## ⚙️ System Process Status

**VS Code Processes:** {process_status["vscode_processes"]}
**PowerShell Sessions:** {process_status["powershell_sessions"]}
**Python Processes:** {process_status["python_processes"]}
**Ollama Processes:** {process_status["ollama_processes"]}

"""

        if process_status["system_load"]:
            load = process_status["system_load"]
            report += f"""### System Resources:
- **CPU Usage:** {load["cpu_percent"]:.1f}%
- **Memory Usage:** {load["memory_percent"]:.1f}%
- **Disk Usage:** {load["disk_usage_percent"]:.1f}%

"""

        # Recommendations
        report += """---

## 🎯 Recommendations

"""

        if not ollama_status["service_running"]:
            report += "### 🦙 Ollama Setup:\n"
            report += "1. Start Ollama service: `ollama serve`\n"
            report += "2. Install recommended models:\n"
            report += "   - `ollama pull phi:2.7b` (fast, small model)\n"
            report += "   - `ollama pull mistral:7b-instruct` (balanced model)\n"
            report += "   - `ollama pull codellama:7b-instruct` (code-focused)\n\n"

        if not chatdev_status["launcher_functional"]:
            report += "### 🤖 ChatDev Setup:\n"
            report += "1. Install ChatDev: `pip install chatdev`\n"
            report += "2. Configure API keys in secrets\n"
            report += "3. Test integration: `python src/integration/chatdev_launcher.py`\n\n"

        if health_score >= 80:
            report += "### ✅ System Status: EXCELLENT\n"
            report += "Your KILO-FOOLISH system is fully operational! All integrations are functional.\n\n"
            report += "**Ready for:**\n"
            report += "- ChatDev multi-agent development sessions\n"
            report += "- Ollama-powered local AI assistance\n"
            report += "- Enhanced Copilot workflows\n"

        report += """

---

*Generated by KILO-FOOLISH System Status Checker v4.0*
"""

        return report

    def run_comprehensive_check(self) -> dict[str, Any]:
        """Run comprehensive system check."""
        # Run all checks
        self.status_report["ollama_status"] = self.check_ollama_status()

        self.status_report["chatdev_status"] = self.check_chatdev_status()

        self.status_report["copilot_status"] = self.check_copilot_status()

        self.status_report["process_status"] = self.check_process_status()

        # Calculate health score
        self.status_report["health_score"] = self.calculate_health_score()

        # Generate and save report
        report_text = self.generate_status_report()
        report_path = self.repo_root / "docs" / "reports" / "system_integration_status.md"
        report_path.parent.mkdir(parents=True, exist_ok=True)

        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report_text)

        # Save JSON data
        json_path = self.repo_root / "data" / "logs" / "system_status.json"
        json_path.parent.mkdir(parents=True, exist_ok=True)

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(self.status_report, f, indent=2, default=str)

        return self.status_report


def main():
    """Main entry point."""
    checker = KILOSystemStatusChecker()
    status = checker.run_comprehensive_check()

    ollama_ok = bool(status["ollama_status"]["service_running"])
    chatdev_ok = bool(status["chatdev_status"]["launcher_functional"])
    copilot_ok = bool(status["copilot_status"]["enhancement_bridge_present"])
    health_score = int(status.get("health_score", 0) or 0)

    logger.info("\n📋 System Integration Quick Summary")
    logger.error(
        f"   {'✅' if ollama_ok else '❌'} Ollama Service: {'running' if ollama_ok else 'offline'}"
    )
    logger.error(
        f"   {'✅' if chatdev_ok else '❌'} ChatDev Launcher: {'functional' if chatdev_ok else 'unavailable'}"
    )
    logger.error(
        f"   {'✅' if copilot_ok else '❌'} Copilot Bridge: {'present' if copilot_ok else 'missing'}"
    )
    logger.warning(f"   {'✅' if health_score >= 80 else '⚠️'} Health Score: {health_score}/100")
    logger.info("   📄 Report: docs/reports/system_integration_status.md")
    logger.info("   🧾 JSON: data/logs/system_status.json")

    return status


if __name__ == "__main__":
    main()
