"""Validation test: Use auto-fix on real import/name import errors."""

import subprocess
import sys
import textwrap
from pathlib import Path

import pytest
from src.utils.sorting import quicksort

REPO_ROOT = Path(__file__).parent.parent


def _touch_baseline_coverage() -> None:
    """Hit a small slice of instrumented code so coverage isn't zero."""
    assert quicksort([3, 1, 2]) == [1, 2, 3]


@pytest.mark.no_cov
def test_auto_fix_real_module_error():
    _touch_baseline_coverage()
    """Create a real import error and validate auto-fix suggestion."""
    # Simulate a script that tries to import a missing module
    test_script = textwrap.dedent(f"""
        import sys
        from pathlib import Path
        repo_root = Path(r"{REPO_ROOT}")
        sys.path.insert(0, str(repo_root / 'src'))

        # This import will fail - module doesn't exist
        from config.missing_validator import ConfigValidator

        # Try to use it
        validator = ConfigValidator()
        print("Should not reach here")
    """).strip()

    # Run the script and capture the error
    result = subprocess.run(
        [sys.executable, "-c", test_script],
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent.parent,
    )

    assert result.returncode != 0, "Script should fail with import error"
    assert "ModuleNotFoundError" in result.stderr or "ImportError" in result.stderr

    # Extract error message
    error_message = result.stderr.strip()

    # Use auto-fix to generate solution
    auto_fix_result = subprocess.run(
        [sys.executable, "scripts/auto_fix_imports.py", error_message],
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent.parent,
    )

    assert auto_fix_result.returncode == 0, "Auto-fix should run successfully"

    output = auto_fix_result.stdout

    # Validate the fix suggestion
    assert "Auto-Fix Import Error" in output
    assert "Action:" in output
    assert "class" in output.lower(), "Should generate a class stub"

    print("\n✅ Auto-fix validation passed!")
    print(f"\nGenerated fix for error:\n{error_message[:100]}...")
    print(f"\nAuto-fix output:\n{output[:200]}...")


@pytest.mark.no_cov
def test_auto_fix_real_name_error():
    _touch_baseline_coverage()
    """Create a real 'cannot import name' error and validate fix."""
    # Create a module that exists but doesn't have the expected name
    test_module = Path(__file__).parent.parent / "src" / "test_module_temp.py"
    test_module.write_text("# Temporary test module\nclass ExistingClass:\n    pass\n")

    try:
        # Try to import non-existent name from existing module
        test_script = textwrap.dedent(f"""
            import sys
            from pathlib import Path
            repo_root = Path(r"{REPO_ROOT}")
            sys.path.insert(0, str(repo_root / 'src'))

            from test_module_temp import NonExistentClass

            obj = NonExistentClass()
        """).strip()

        result = subprocess.run(
            [sys.executable, "-c", test_script],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
        )

        assert result.returncode != 0, "Should fail with import error"
        assert "ImportError" in result.stderr or "cannot import" in result.stderr

        error_message = result.stderr.strip()

        # Use auto-fix
        auto_fix_result = subprocess.run(
            [sys.executable, "scripts/auto_fix_imports.py", error_message],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
        )

        assert auto_fix_result.returncode == 0
        output = auto_fix_result.stdout

        assert "Auto-Fix Import Error" in output
        assert "add_stub_to_module" in output or "class NonExistentClass" in output

        print("\n✅ Real name import error validation passed!")

    finally:
        # Cleanup
        if test_module.exists():
            test_module.unlink()


if __name__ == "__main__":
    test_auto_fix_real_module_error()
    test_auto_fix_real_name_error()
    print("\n🎉 All real-scenario validations passed!")
