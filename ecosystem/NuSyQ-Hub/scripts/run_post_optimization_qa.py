#!/usr/bin/env python3
"""Post-Optimization Quality Assurance Runner
==========================================

Runs all quality checks and applies improvements from October 22, 2025 optimization session.

Usage:
    python scripts/run_post_optimization_qa.py [--auto-fix] [--verbose]

Options:
    --auto-fix    Automatically apply Black formatting
    --verbose     Show detailed output
"""

import argparse
import subprocess
import sys
from pathlib import Path

# ANSI colors for terminal output
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BLUE = "\033[94m"
RESET = "\033[0m"


def run_command(cmd: list[str], description: str, verbose: bool = False) -> tuple[bool, str]:
    """Run a command and return success status and output"""
    print(f"{BLUE}▶{RESET} {description}...")

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
        )

        if verbose or result.returncode != 0:
            print(result.stdout)
            if result.stderr:
                print(result.stderr)

        if result.returncode == 0:
            print(f"{GREEN}✓{RESET} {description} - PASSED\n")
            return True, result.stdout
        else:
            print(f"{RED}✗{RESET} {description} - FAILED (exit code {result.returncode})\n")
            return False, result.stdout

    except Exception as e:
        print(f"{RED}✗{RESET} {description} - ERROR: {e}\n")
        return False, str(e)


def main():
    parser = argparse.ArgumentParser(description="Run post-optimization QA checks")
    parser.add_argument("--auto-fix", action="store_true", help="Apply Black formatting automatically")
    parser.add_argument("--verbose", action="store_true", help="Show detailed output")
    args = parser.parse_args()

    print(f"\n{BLUE}{'=' * 70}{RESET}")
    print(f"{BLUE}  NuSyQ-Hub Post-Optimization Quality Assurance{RESET}")
    print(f"{BLUE}  Session: October 22, 2025 - Performance Enhancements{RESET}")
    print(f"{BLUE}{'=' * 70}{RESET}\n")

    results = {}

    # 1. Syntax validation
    print(f"{YELLOW}[1/6]{RESET} Syntax Validation")
    success, _ = run_command(
        [
            sys.executable,
            "-m",
            "py_compile",
            "src/game_development/zeta21_game_pipeline.py",
        ],
        "Validate fixed syntax error (zeta21_game_pipeline.py)",
        args.verbose,
    )
    results["syntax"] = success

    # 2. Black formatting check
    print(f"{YELLOW}[2/6]{RESET} Code Formatting")
    if args.auto_fix:
        success, _ = run_command(
            [sys.executable, "-m", "black", "src", "tests", "scripts"],
            "Apply Black formatting to all files",
            args.verbose,
        )
        results["formatting"] = success
    else:
        success, _output = run_command(
            [sys.executable, "-m", "black", "--check", "src", "tests", "scripts"],
            "Check Black formatting compliance",
            args.verbose,
        )
        results["formatting"] = success
        if not success:
            print(f"{YELLOW}i{RESET}  Run with --auto-fix to apply formatting automatically\n")

    # 3. Import validation
    print(f"{YELLOW}[3/6]{RESET} Import Validation")
    success, _ = run_command(
        [
            sys.executable,
            "-c",
            "from src.orchestration.unified_ai_orchestrator import MultiAIOrchestrator; print('OK')",
        ],
        "Validate orchestrator imports",
        args.verbose,
    )
    results["imports"] = success

    # 4. Configuration validation
    print(f"{YELLOW}[4/6]{RESET} Configuration Validation")
    success, _ = run_command(
        [
            sys.executable,
            "-c",
            """
import json
from pathlib import Path

# Check ChatDev model config
config_path = Path('config/chatdev_ollama_models.json')
assert config_path.exists(), 'ChatDev config missing'

with open(config_path, encoding='utf-8') as f:
    config = json.load(f)
    assert 'agent_assignments' in config
    assert 'consensus_pools' in config
    assert 'high_quality' in config['consensus_pools']
    print('ChatDev config valid')

# Check secrets are redacted
secrets_path = Path('config/secrets.json')
with open(secrets_path, encoding='utf-8') as f:
    secrets = json.load(f)
    # List of keys that are config values, not secrets
    non_secret_keys = ['host', 'debug', 'log_level', 'organization', 'project']

    for key, value in secrets.items():
        if isinstance(value, dict):
            for k, v in value.items():
                if isinstance(v, str) and v and k not in non_secret_keys:
                    assert 'REDACTED' in v or v == 'org-your-org-here' or v == 'proj_your-project-here', f'Unredacted secret: {key}.{k}'
    print('Secrets properly redacted')
""",
        ],
        "Validate configurations (ChatDev models, secrets)",
        args.verbose,
    )
    results["config"] = success

    # 5. Orchestrator smoke test
    print(f"{YELLOW}[5/6]{RESET} Orchestrator Smoke Test")
    success, _output = run_command(
        [
            sys.executable,
            "-c",
            """
import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))

from src.orchestration.unified_ai_orchestrator import MultiAIOrchestrator
import os

# Set low worker count for test
os.environ['ORCH_MAX_WORKERS'] = '2'

orch = UnifiedAIOrchestrator()
assert len(orch.ai_systems) >= 5, 'Not enough AI systems registered'
print(f'Orchestrator initialized with {len(orch.ai_systems)} AI systems')
print(f'Thread pool workers: {orch.executor._max_workers}')
assert orch.executor._max_workers == 2, 'ORCH_MAX_WORKERS not applied'
print('Orchestrator smoke test PASSED')
""",
        ],
        "Initialize orchestrator and verify optimizations",
        args.verbose,
    )
    results["orchestrator"] = success

    # 6. Real-time monitor smoke test
    print(f"{YELLOW}[6/6]{RESET} Real-Time Monitor Smoke Test")
    success, _ = run_command(
        [
            sys.executable,
            "-c",
            """
from src.real_time_context_monitor import RealTimeContextMonitor

monitor = RealTimeContextMonitor()
assert hasattr(monitor, 'exclude_patterns'), 'Missing exclude_patterns'
assert '__pycache__' in monitor.exclude_patterns, '__pycache__ not excluded'
assert '.git' in monitor.exclude_patterns, '.git not excluded'
print(f'Real-time monitor initialized with {len(monitor.exclude_patterns)} exclusion patterns')
print('Monitor smoke test PASSED')
""",
        ],
        "Verify real-time monitor event filtering",
        args.verbose,
    )
    results["monitor"] = success

    # Summary
    print(f"\n{BLUE}{'=' * 70}{RESET}")
    print(f"{BLUE}  Quality Assurance Summary{RESET}")
    print(f"{BLUE}{'=' * 70}{RESET}\n")

    passed = sum(results.values())
    total = len(results)

    for check, success in results.items():
        status = f"{GREEN}✓ PASS{RESET}" if success else f"{RED}✗ FAIL{RESET}"
        print(f"  {check.ljust(20)}: {status}")

    print(f"\n{BLUE}{'=' * 70}{RESET}")
    print(f"  {passed}/{total} checks passed")

    if passed == total:
        print(f"{GREEN}  🎉 All quality checks PASSED!{RESET}")
        print(f"{BLUE}{'=' * 70}{RESET}\n")
        return 0
    else:
        print(f"{YELLOW}  ⚠️  Some checks failed. Review output above.{RESET}")
        print(f"{BLUE}{'=' * 70}{RESET}\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
