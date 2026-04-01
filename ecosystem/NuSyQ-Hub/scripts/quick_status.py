#!/usr/bin/env python3
"""Quick integration status checker - one-command health overview."""

import shutil
import subprocess
import sys
from pathlib import Path


def check(name: str, cmd: list[str], success_msg: str = "OK", shell: bool = False) -> bool:
    """Run a check command and print status."""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
            shell=shell,
        )
        if result.returncode == 0:
            print(f"✅ {name}: {success_msg}")
            return True
        else:
            print(f"❌ {name}: Failed (exit {result.returncode})")
            return False
    except FileNotFoundError:
        print(f"❌ {name}: Not found")
        return False
    except subprocess.TimeoutExpired:
        print(f"❌ {name}: Timed out")
        return False
    except Exception as e:
        print(f"❌ {name}: {str(e)[:60]}")
        return False


def check_vscode() -> bool:
    """Check VS Code availability — handles Windows .cmd wrapper."""
    name = "VS Code"
    # shutil.which finds executables AND .cmd/.bat on Windows via PATHEXT
    code_path = shutil.which("code") or shutil.which("code.cmd")
    if not code_path:
        # Common Windows install path (user-level)
        win_path = Path.home() / "AppData/Local/Programs/Microsoft VS Code/bin/code.cmd"
        if win_path.exists():
            code_path = str(win_path)
    if not code_path:
        print(f"❌ {name}: Not found")
        return False
    # Run with shell=True so .cmd files work on Windows
    return check(name, f'"{code_path}" --version', "Available", shell=True)


def check_mjolnir_probes() -> bool:
    """Quick MJOLNIR agent probe — counts online agents."""
    name = "MJOLNIR Agents"
    try:
        result = subprocess.run(
            [sys.executable, "scripts/nusyq_dispatch.py", "status", "--probes"],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        if result.returncode == 0:
            # Count ONLINE lines
            online = result.stdout.count("ONLINE") + result.stdout.count("online")
            total = (
                result.stdout.count("ONLINE")
                + result.stdout.count("online")
                + result.stdout.count("OFFLINE")
                + result.stdout.count("offline")
            )
            print(f"✅ {name}: {online}/{total or '?'} agents online")
            return True
        else:
            print(f"❌ {name}: probe failed (exit {result.returncode})")
            return False
    except subprocess.TimeoutExpired:
        print(f"⏱️  {name}: Timed out (agents may be slow)")
        return False
    except Exception as e:
        print(f"❌ {name}: {str(e)[:60]}")
        return False


def check_ai_backends() -> bool:
    """Check AI backend availability via the dedicated status tool."""
    name = "AI Backends"
    try:
        result = subprocess.run(
            [sys.executable, "-m", "src.tools.ai_backend_status"],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        output = result.stdout.strip()
        if "OLLAMA_REACHABLE=true" in output:
            print(f"✅ {name}: Ollama reachable")
        elif "LMSTUDIO_REACHABLE=true" in output or "LMSTUDIO_BASE_URL" in output:
            print(f"✅ {name}: LM Studio reachable")
        else:
            # Still report what IS available
            keys = [
                line.split("=")[0]
                for line in output.splitlines()
                if "=true" in line or "PRESENT=true" in line.replace("_PRESENT", "")
            ]
            reachable = [k for k in keys if "REACHABLE" in k or "PRESENT" in k]
            if reachable:
                print(f"⚠️  {name}: {', '.join(reachable)}")
                return True
            print(f"❌ {name}: No AI backends reachable")
            return False
        return True
    except Exception as e:
        print(f"❌ {name}: {str(e)[:60]}")
        return False


def main() -> int:
    """Run quick status checks."""
    print("🔍 NuSyQ Integration Status\n")

    checks_passed = 0
    total_checks = 0

    # Python environment
    total_checks += 1
    py_ver = f"v{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    if check(
        "Python",
        [sys.executable, "--version"],
        py_ver,
    ):
        checks_passed += 1

    # Core imports
    total_checks += 1
    if check(
        "AgentTaskRouter",
        [sys.executable, "-c", "from src.tools.agent_task_router import AgentTaskRouter"],
        "Import OK",
    ):
        checks_passed += 1

    total_checks += 1
    if check(
        "MultiAIOrchestrator",
        [
            sys.executable,
            "-c",
            "from src.orchestration.multi_ai_orchestrator import MultiAIOrchestrator",
        ],
        "Import OK",
    ):
        checks_passed += 1

    # Git
    total_checks += 1
    if check("Git", ["git", "--version"], "Available"):
        checks_passed += 1

    # Ollama CLI (may be available but service offline)
    total_checks += 1
    if check("Ollama CLI", ["ollama", "--version"], "Available"):
        checks_passed += 1

    # VS Code — handles .cmd wrapper on Windows
    total_checks += 1
    if check_vscode():
        checks_passed += 1

    # Tests — use --no-cov to skip coverage threshold in collection check
    total_checks += 1
    pytest_path = Path("tests/test_agent_task_router.py")
    if pytest_path.exists():
        if check(
            "Test Suite",
            [sys.executable, "-m", "pytest", str(pytest_path), "-q", "--co", "--no-cov"],
            "Collectible",
        ):
            checks_passed += 1
    else:
        print(f"❌ Test Suite: {pytest_path} not found")

    # AI backend status
    total_checks += 1
    if check_ai_backends():
        checks_passed += 1

    # Linting gate
    total_checks += 1
    if check(
        "Ruff Gate",
        [sys.executable, "-m", "ruff", "check", "src/tools/agent_task_router.py", "--quiet"],
        "Clean",
    ):
        checks_passed += 1

    # Summary
    print(f"\n📊 Status: {checks_passed}/{total_checks} checks passed")

    if checks_passed == total_checks:
        print("✅ System fully operational!")
        return 0
    elif checks_passed >= total_checks * 0.7:
        print("⚠️  System mostly operational")
        return 0
    else:
        print("❌ System needs attention")
        return 1


if __name__ == "__main__":
    sys.exit(main())
