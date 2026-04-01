"""Lightweight validation wrapper using existing health commands."""

from __future__ import annotations

import subprocess


def run_command(cmd: str, description: str) -> tuple[bool, str]:
    print(f"\n🔧 {description}")
    print(f"   Command: {cmd}")
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )
    except subprocess.TimeoutExpired:
        print("   ⏰ Timeout")
        return False, "Timeout"
    except subprocess.SubprocessError as exc:  # pragma: no cover - defensive
        print(f"   💥 Exception: {exc}")
        return False, str(exc)

    ok = result.returncode == 0
    if ok:
        print("   ✅ Success")
    else:
        print(f"   ❌ Failed (exit code: {result.returncode})")

    if result.stdout:
        print("   stdout (tail):")
        print("   " + "\n   ".join(result.stdout.strip().splitlines()[-8:]))
    if result.stderr:
        print("   stderr (tail):")
        print("   " + "\n   ".join(result.stderr.strip().splitlines()[-8:]))

    return ok, result.stdout + result.stderr


def main() -> int:
    print("🚀 Validating NuSyQ-Hub fixes (lean wrapper)")
    print("=" * 60)

    all_ok = True

    steps = [
        (
            "python -m ruff check --exit-zero",
            "Ruff lint (non-blocking)",
        ),
        (
            "python scripts/run_targeted_tests.py tests/test_auto_fix_imports.py --cov-fail-under=0",
            "Auto-fix import tests with coverage (threshold 0 for dev speed)",
        ),
        (
            "pytest --collect-only -q",
            "Pytest collection sanity check",
        ),
        (
            "git status --short",
            "Git status snapshot",
        ),
    ]

    for cmd, desc in steps:
        ok, _ = run_command(cmd, desc)
        all_ok = all_ok and ok

    print("\n" + "=" * 60)
    print("📊 VALIDATION SUMMARY")
    print("=" * 60)
    if all_ok:
        print("✅ All checks passed")
        print("Next: consider full suite: python -m pytest tests -q")
    else:
        print("❌ Some checks failed. See output above.")
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
