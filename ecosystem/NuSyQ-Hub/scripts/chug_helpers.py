#!/usr/bin/env python
"""Helper functions for the Perpetual Chug workflow."""

import json
import re
import subprocess
import sys
import time
from pathlib import Path


def run_chug_cycle():
    """Run one cycle of the perpetual chug workflow."""
    print("🚂 CHUG CYCLE START")
    print("=" * 60)

    signals = harvest_all_signals()
    if signals:
        print("🔍 Harvested signals:")
        summary = []
        lint_errors = signals.get("lint_errors")
        if lint_errors is not None:
            summary.append(f"lint_errors={lint_errors}")
        lifecycle_age = signals.get("lifecycle_age_minutes")
        if lifecycle_age is not None:
            summary.append(f"lifecycle_age={lifecycle_age:.1f}m")
        missing = signals.get("missing_critical", [])
        if missing:
            summary.append(f"missing_services={','.join(missing)}")
        if summary:
            print("   " + " | ".join(summary))

    steps = [
        ("Lint check", ["python", "-m", "ruff", "check", "--exit-zero"], 60),
        ("Type check", ["python", "-m", "mypy", "src/", "--no-error-summary"], 360),
        (
            "Test auto-fix imports",
            [
                "python",
                "scripts/run_clean_coverage.py",
                "tests/test_auto_fix_imports.py",
                "--cov=scripts",
                "--cov-fail-under=0",
                "-q",
            ],
            60,
        ),
        ("Core hygiene (fast)", ["python", "scripts/start_nusyq.py", "hygiene", "--fast"], 60),
    ]

    results = []
    for name, cmd, timeout in steps:
        print(f"\n🔧 {name}...")
        print(f"   Command: {' '.join(cmd)}")
        print(f"   Timeout: {timeout}s")

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
            )

            if result.returncode == 0:
                print("   ✅ Success")
                results.append((name, True, result.stdout.strip()))
            else:
                print(f"   ❌ Failed (exit: {result.returncode})")
                if result.stderr:
                    print(f"   Error: {result.stderr.strip()}")
                results.append((name, False, result.stderr.strip()))

        except subprocess.TimeoutExpired:
            print("   ⏰ Timeout")
            results.append((name, False, "Timeout"))
        except Exception as e:
            print(f"   💥 Exception: {e}")
            results.append((name, False, str(e)))

    print("\n" + "=" * 60)
    print("📊 CHUG CYCLE REPORT")
    print("=" * 60)

    success_count = sum(1 for _, success, _ in results if success)
    total_count = len(results)

    print(f"Success: {success_count}/{total_count}")

    for name, success, detail in results:
        status = "✅" if success else "❌"
        print(f"  {status} {name}")
        if not success and detail:
            print(f"     Detail: {detail}")

    if success_count == total_count:
        print("\n🎯 All systems go! Ready for next action.")
        suggestions = [
            "Run full test suite: python scripts/run_clean_coverage.py tests/ --cov=src,scripts",
            "Check coverage: python -m pytest --cov=src,scripts --cov-report=html",
            "Run specific module tests: python scripts/run_clean_coverage.py tests/test_orchestration.py",
        ]
        print("\nSuggested next actions:")
        for i, suggestion in enumerate(suggestions, 1):
            print(f"  {i}. {suggestion}")
    else:
        print("\n🔧 Needs attention. Recommended fixes:")
        for name, success, _ in results:
            if not success:
                if "Lint" in name:
                    print("  - Run: python -m ruff check --fix")
                elif "Type check" in name:
                    print("  - Run: python -m mypy src/ --ignore-missing-imports")
                elif "Test" in name:
                    print("  - Run: python scripts/fix_file_encoding.py --scan")
                elif "hygiene" in name:
                    print("  - Check scripts/start_nusyq.py for issues")

    next_actions = generate_next_actions(results, signals)
    if next_actions:
        print("\n🌱 Signal-driven next actions:")
        for i, action in enumerate(next_actions, 1):
            print(f"  {i}. {action}")

    return success_count == total_count


def harvest_current_state_signals() -> dict[str, object]:
    current_state = Path("state/reports/current_state.md")
    if not current_state.exists():
        return {}
    signal: dict[str, object] = {}
    try:
        text = current_state.read_text(encoding="utf-8")
        lint_match = re.search(r"Lint errors:\s*`(\d+)`", text)
        if lint_match:
            signal["lint_errors"] = int(lint_match.group(1))
        if "Active services:" in text:
            services_match = re.search(r"Active services:\s*`?(\d+)`?", text)
            if services_match:
                signal["active_services"] = int(services_match.group(1))
    except Exception:
        pass
    stat = current_state.stat()
    signal["current_state_age_minutes"] = (time.time() - stat.st_mtime) / 60.0
    return signal


def harvest_lifecycle_signals() -> dict[str, object]:
    lifecycle_path = Path("state/reports/lifecycle_catalog_latest.json")
    if not lifecycle_path.exists():
        return {}
    try:
        data = json.loads(lifecycle_path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    signals: dict[str, object] = {}
    services = data.get("services", [])
    missing = data.get("critical_services_missing") or []
    alerts = data.get("alerts_triggered") or []
    signals["missing_critical"] = missing
    signals["alerts_triggered"] = alerts
    stat = lifecycle_path.stat()
    signals["lifecycle_age_minutes"] = (time.time() - stat.st_mtime) / 60.0
    signals["active_services_count"] = sum(1 for svc in services if svc.get("active"))
    return signals


def harvest_all_signals() -> dict[str, object]:
    signals = {}
    signals.update(harvest_current_state_signals())
    signals.update(harvest_lifecycle_signals())
    return signals


def generate_next_actions(results: list[tuple[str, bool, str]], signals: dict[str, object]) -> list[str]:
    actions: list[str] = []
    failed_steps = [name for name, success, _ in results if not success]
    lint_errors = signals.get("lint_errors", 0)
    missing = signals.get("missing_critical", [])
    alerts = signals.get("alerts_triggered", [])

    if failed_steps:
        actions.append(f"Fix failing step(s): {', '.join(failed_steps)} (check logs above).")
    if lint_errors and lint_errors > 0:
        actions.append("Refresh diagnostics: python scripts/start_nusyq.py error_report --quick")
    if missing:
        actions.append(
            "Inspect lifecycle catalog: "
            + ", ".join(missing)
            + " may be down (state/reports/lifecycle_catalog_latest.json)."
        )
    if alerts:
        actions.append("Review alerts triggered: " + ", ".join(alerts))
    if not actions:
        actions.append("Keep momentum: python scripts/chug_helpers.py --cycle")
    return actions


def main():
    """Main entry point for chug helper."""
    import argparse

    parser = argparse.ArgumentParser(description="Perpetual Chug Helper")
    parser.add_argument("--cycle", action="store_true", help="Run one chug cycle")
    parser.add_argument("--clean-cov", nargs="+", help="Run clean coverage on test paths")
    parser.add_argument("--fix-encoding", nargs="*", help="Fix encoding issues in files")
    parser.add_argument("--scan", action="store_true", help="Scan for encoding issues")

    args = parser.parse_args()

    if args.cycle:
        success = run_chug_cycle()
        sys.exit(0 if success else 1)
    elif args.clean_cov:
        from scripts.run_clean_coverage import main as cov_main

        cov_main()
    elif args.fix_encoding is not None:
        from scripts.fix_file_encoding import main as fix_main

        fix_main()
    elif args.scan:
        from scripts.fix_file_encoding import scan_for_encoding_issues

        issues = scan_for_encoding_issues()
        if issues:
            print(f"Found {len(issues)} encoding issues")
            sys.exit(1)
        else:
            print("No encoding issues found")
            sys.exit(0)
    else:
        success = run_chug_cycle()
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
