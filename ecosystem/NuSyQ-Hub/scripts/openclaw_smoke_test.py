#!/usr/bin/env python3
"""Smoke Test - OpenClaw Gateway Bridge Integration.

Validates:
1. Gateway bridge imports successfully
2. Configuration can be loaded from secrets.json
3. Orchestrator integration is wired correctly
4. Main.py CLI flags and help runtime are healthy
5. Integrations module exports OpenClaw bridge symbols

Run with:
  python scripts/openclaw_smoke_test.py
  python scripts/openclaw_smoke_test.py --json
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

# Add repo root to path
REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))


def _iso_timestamp() -> str:
    return datetime.now(UTC).isoformat()


def _file_mtime_iso(path: Path) -> str:
    try:
        return datetime.fromtimestamp(path.stat().st_mtime, tz=UTC).isoformat()
    except OSError:
        return ""


def _make_result(name: str, passed: bool, details: dict[str, Any]) -> dict[str, Any]:
    return {"name": name, "passed": passed, "details": details}


def test_gateway_bridge_import() -> dict[str, Any]:
    """Test that OpenClaw gateway bridge imports successfully."""
    try:
        from src.integrations.openclaw_gateway_bridge import (
            OPENCLAW_DEFAULT_GATEWAY_URL,
            OPENCLAW_DEFAULT_TIMEOUT_SECONDS,
            OpenClawGatewayBridge,
            get_openclaw_gateway_bridge,
        )

        details = {
            "bridge_class": OpenClawGatewayBridge.__name__,
            "factory": get_openclaw_gateway_bridge.__name__,
            "default_gateway_url": OPENCLAW_DEFAULT_GATEWAY_URL,
            "default_timeout_seconds": OPENCLAW_DEFAULT_TIMEOUT_SECONDS,
        }
        return _make_result("Gateway Bridge Import", True, details)
    except Exception as exc:
        return _make_result("Gateway Bridge Import", False, {"error": str(exc)})


def test_config_loading() -> dict[str, Any]:
    """Test that secrets.json has OpenClaw configuration."""
    config_path = REPO_ROOT / "config" / "secrets.json"
    if not config_path.exists():
        return _make_result(
            "Configuration Loading",
            False,
            {"error": f"Config file not found: {config_path}"},
        )

    try:
        config = json.loads(config_path.read_text(encoding="utf-8"))
        openclaw_config = config.get("openclaw", {}) if isinstance(config, dict) else {}
        if not isinstance(openclaw_config, dict):
            return _make_result(
                "Configuration Loading",
                False,
                {"error": "OpenClaw configuration block malformed"},
            )
        gateway_url = openclaw_config.get("gateway_url")
        timeout_seconds = openclaw_config.get("timeout_seconds")
        enabled = bool(openclaw_config.get("enabled", False))
        channels = openclaw_config.get("channels", {})
        details = {
            "gateway_url": gateway_url,
            "timeout_seconds": timeout_seconds,
            "enabled": enabled,
            "channels_count": len(channels) if isinstance(channels, dict) else 0,
            "config_file": str(config_path),
            "config_mtime": _file_mtime_iso(config_path),
        }
        if gateway_url and timeout_seconds is not None:
            return _make_result("Configuration Loading", True, details)
        return _make_result(
            "Configuration Loading",
            False,
            {"error": "Missing gateway_url or timeout_seconds in openclaw config", **details},
        )
    except Exception as exc:
        return _make_result("Configuration Loading", False, {"error": str(exc)})


def test_orchestrator_integration() -> dict[str, Any]:
    """Test that orchestrator imports work."""
    try:
        from src.orchestration.unified_ai_orchestrator import (
            UnifiedAIOrchestrator,
        )
        from src.tools.agent_task_router import AgentTaskRouter

        return _make_result(
            "Orchestrator Integration",
            True,
            {
                "orchestrator": UnifiedAIOrchestrator.__name__,
                "router": AgentTaskRouter.__name__,
            },
        )
    except Exception as exc:
        return _make_result("Orchestrator Integration", False, {"error": str(exc)})


def test_main_cli_flags(help_timeout_s: float, max_help_runtime_s: float) -> dict[str, Any]:
    """Test that main.py has OpenClaw flags and responsive help."""
    started = time.perf_counter()
    try:
        result = subprocess.run(
            [sys.executable, "src/main.py", "--help"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=max(1.0, help_timeout_s),
            check=False,
        )
        elapsed = round(time.perf_counter() - started, 3)
        stdout = result.stdout or ""
        has_enabled = "--openclaw-enabled" in stdout
        has_gateway = "--openclaw-gateway" in stdout
        fast_enough = max_help_runtime_s <= 0 or elapsed <= max_help_runtime_s
        passed = result.returncode == 0 and has_enabled and has_gateway and fast_enough
        details: dict[str, Any] = {
            "help_elapsed_s": elapsed,
            "help_timeout_s": help_timeout_s,
            "max_help_runtime_s": max_help_runtime_s,
            "has_openclaw_enabled_flag": has_enabled,
            "has_openclaw_gateway_flag": has_gateway,
            "return_code": result.returncode,
        }
        if not passed:
            details["stderr_tail"] = "\n".join((result.stderr or "").splitlines()[-5:])
            if not fast_enough:
                details["error"] = f"Help runtime {elapsed}s exceeded max threshold {max_help_runtime_s}s"
        return _make_result("Main CLI Flags", passed, details)
    except subprocess.TimeoutExpired as exc:
        elapsed = round(time.perf_counter() - started, 3)
        return _make_result(
            "Main CLI Flags",
            False,
            {
                "error": f"Help command timed out after {help_timeout_s}s: {exc}",
                "help_elapsed_s": elapsed,
                "help_timeout_s": help_timeout_s,
            },
        )
    except Exception as exc:
        return _make_result("Main CLI Flags", False, {"error": str(exc)})


def test_integrations_module() -> dict[str, Any]:
    """Test that integrations module exports are available."""
    try:
        from src.integrations import (
            OpenClawGatewayBridge,
            get_openclaw_gateway_bridge,
        )

        return _make_result(
            "Integrations Module",
            True,
            {
                "bridge_export": OpenClawGatewayBridge.__name__,
                "factory_export": get_openclaw_gateway_bridge.__name__,
            },
        )
    except Exception as exc:
        return _make_result("Integrations Module", False, {"error": str(exc)})


def run_smoke(help_timeout_s: float, max_help_runtime_s: float) -> dict[str, Any]:
    """Run smoke checks and return structured report."""
    checks = [
        test_gateway_bridge_import(),
        test_config_loading(),
        test_orchestrator_integration(),
        test_main_cli_flags(help_timeout_s=help_timeout_s, max_help_runtime_s=max_help_runtime_s),
        test_integrations_module(),
    ]
    passed = sum(1 for check in checks if check["passed"])
    total = len(checks)
    report_dir = REPO_ROOT / "state" / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = report_dir / f"openclaw_smoke_{stamp}.json"
    latest_path = report_dir / "openclaw_smoke_latest.json"
    payload: dict[str, Any] = {
        "action": "openclaw_smoke",
        "status": "ok" if passed == total else "failed",
        "generated_at": _iso_timestamp(),
        "summary": {
            "passed": passed,
            "total": total,
            "pass_rate": round(passed / total, 4) if total else 0.0,
        },
        "checks": checks,
        "report_file": str(report_path),
        "latest_report_file": str(latest_path),
    }
    report_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    latest_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return payload


def _render_human_summary(payload: dict[str, Any]) -> None:
    print("\n" + "=" * 70)
    print("🔌 OpenClaw Gateway Bridge Integration Smoke Test")
    print("=" * 70 + "\n")
    for check in payload.get("checks", []):
        if not isinstance(check, dict):
            continue
        status = "✅ PASS" if check.get("passed") else "❌ FAIL"
        print(f"  {status}: {check.get('name')}")
        details = check.get("details", {})
        if isinstance(details, dict) and details.get("error"):
            print(f"      error: {details['error']}")

    summary = payload.get("summary", {})
    print("\n" + "=" * 70)
    print("📊 Summary")
    print("=" * 70)
    print(f"  Passed: {summary.get('passed', 0)}/{summary.get('total', 0)}")
    print(f"  Report: {payload.get('latest_report_file')}")
    if payload.get("status") == "ok":
        print("\n✅ All smoke tests passed! OpenClaw integration is healthy.")
    else:
        print("\n❌ One or more smoke tests failed. Check report for details.")


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run OpenClaw smoke checks.")
    parser.add_argument("--json", action="store_true", help="Emit JSON report payload")
    parser.add_argument(
        "--help-timeout-s",
        type=float,
        default=float(os.getenv("NUSYQ_OPENCLAW_HELP_TIMEOUT_S", "10")),
        help="Timeout (seconds) for src/main.py --help check",
    )
    parser.add_argument(
        "--max-help-runtime-s",
        type=float,
        default=float(os.getenv("NUSYQ_OPENCLAW_HELP_MAX_RUNTIME_S", "0")),
        help="Optional max runtime threshold for src/main.py --help (0 disables threshold)",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv or sys.argv[1:])
    payload = run_smoke(
        help_timeout_s=args.help_timeout_s,
        max_help_runtime_s=args.max_help_runtime_s,
    )
    if args.json:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        _render_human_summary(payload)
    return 0 if payload.get("status") == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
