"""Tests for src/utils/safe_subprocess.py - Safe subprocess execution.

Tests SafeSubprocessExecutor with Zen Engine validation wrapping.
"""

import subprocess
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from src.utils.safe_subprocess import SafeSubprocessExecutor, SecurityError

# =============================================================================
# Test SafeSubprocessExecutor Initialization
# =============================================================================


class TestSafeSubprocessExecutorInit:
    """Tests for SafeSubprocessExecutor initialization."""

    def test_default_auto_fix_enabled(self) -> None:
        """Default auto_fix is True."""
        executor = SafeSubprocessExecutor()
        assert executor.auto_fix is True

    def test_default_strict_mode_disabled(self) -> None:
        """Default strict_mode is False."""
        executor = SafeSubprocessExecutor()
        assert executor.strict_mode is False

    def test_auto_fix_can_be_disabled(self) -> None:
        """auto_fix can be disabled."""
        executor = SafeSubprocessExecutor(auto_fix=False)
        assert executor.auto_fix is False

    def test_strict_mode_can_be_enabled(self) -> None:
        """strict_mode can be enabled."""
        executor = SafeSubprocessExecutor(strict_mode=True)
        assert executor.strict_mode is True

    def test_validation_enabled_depends_on_zen(self) -> None:
        """validation_enabled depends on Zen availability."""
        executor = SafeSubprocessExecutor()
        # Zen might or might not be available; check attribute exists
        assert hasattr(executor, "validation_enabled")

    def test_zen_available_attribute_exists(self) -> None:
        """zen_available attribute exists."""
        executor = SafeSubprocessExecutor()
        assert hasattr(executor, "zen_available")


# =============================================================================
# Test run() method
# =============================================================================


class TestRun:
    """Tests for run() method."""

    def test_run_with_list_command(self) -> None:
        """Run with list command executes successfully."""
        executor = SafeSubprocessExecutor()
        executor.validation_enabled = False  # Disable for simple test
        # Use python -c for cross-platform compatibility (echo is shell builtin on Windows)
        result = executor.run(["python", "-c", "print('hello')"], capture_output=True, text=True)
        assert result.returncode == 0

    def test_run_with_string_command(self) -> None:
        """Run with string command executes successfully."""
        executor = SafeSubprocessExecutor()
        executor.validation_enabled = False
        result = executor.run("echo hello", shell=True, capture_output=True, text=True)
        assert result.returncode == 0

    def test_run_captures_output(self) -> None:
        """Run captures stdout when requested."""
        executor = SafeSubprocessExecutor()
        executor.validation_enabled = False
        result = executor.run(["python", "-c", "print('test')"], capture_output=True, text=True)
        assert "test" in result.stdout

    def test_run_with_check_raises_on_error(self) -> None:
        """Run with check=True raises on non-zero exit."""
        executor = SafeSubprocessExecutor()
        executor.validation_enabled = False
        with pytest.raises(subprocess.CalledProcessError):
            executor.run("exit 1", shell=True, check=True)

    def test_run_with_timeout(self) -> None:
        """Run respects timeout parameter."""
        executor = SafeSubprocessExecutor()
        executor.validation_enabled = False
        result = executor.run(["python", "-c", "print('quick')"], timeout=5, capture_output=True)
        assert result.returncode == 0

    def test_run_with_cwd(self, tmp_path: Any) -> None:
        """Run respects cwd parameter."""
        executor = SafeSubprocessExecutor()
        executor.validation_enabled = False
        result = executor.run(
            ["python", "-c", "import os; print(os.getcwd())"],
            capture_output=True,
            text=True,
            cwd=tmp_path,
        )
        assert str(tmp_path) in result.stdout or tmp_path.name in result.stdout

    def test_run_with_env(self) -> None:
        """Run respects env parameter."""
        executor = SafeSubprocessExecutor()
        executor.validation_enabled = False
        import os

        env = os.environ.copy()
        env["TEST_VAR"] = "test_value"
        result = executor.run(
            ["python", "-c", "import os; print(os.environ.get('TEST_VAR', ''))"],
            capture_output=True,
            text=True,
            env=env,
        )
        assert "test_value" in result.stdout


# =============================================================================
# Test Zen Engine Validation
# =============================================================================


class TestZenValidation:
    """Tests for Zen Engine validation integration."""

    def test_run_with_zen_validation(self) -> None:
        """Run calls Zen validation when available."""
        executor = SafeSubprocessExecutor()

        # Mock Zen wrapper
        mock_zen = MagicMock()
        mock_validation = MagicMock()
        mock_validation.warnings = []
        mock_validation.blocked = False
        mock_validation.modified_command = None
        mock_zen.validate_command.return_value = mock_validation

        executor.zen = mock_zen
        executor.zen_available = True
        executor.validation_enabled = True

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            executor.run(["echo", "hello"])
            mock_zen.validate_command.assert_called_once()

    def test_run_logs_warnings(self) -> None:
        """Run logs Zen validation warnings."""
        executor = SafeSubprocessExecutor()

        mock_zen = MagicMock()
        mock_validation = MagicMock()
        mock_validation.warnings = ["Warning 1"]
        mock_validation.blocked = False
        mock_validation.modified_command = None
        mock_zen.validate_command.return_value = mock_validation

        executor.zen = mock_zen
        executor.zen_available = True
        executor.validation_enabled = True

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            executor.run(["echo", "test"])
            # Should not raise

    def test_run_blocked_in_strict_mode(self) -> None:
        """Run raises SecurityError when blocked in strict mode."""
        executor = SafeSubprocessExecutor(strict_mode=True)

        mock_zen = MagicMock()
        mock_validation = MagicMock()
        mock_validation.warnings = []
        mock_validation.blocked = True
        mock_validation.modified_command = None
        mock_zen.validate_command.return_value = mock_validation

        executor.zen = mock_zen
        executor.zen_available = True
        executor.validation_enabled = True

        with pytest.raises(SecurityError):
            executor.run(["rm", "-rf", "/"])

    def test_run_blocked_proceeds_in_non_strict_mode(self) -> None:
        """Run proceeds when blocked in non-strict mode."""
        executor = SafeSubprocessExecutor(strict_mode=False)

        mock_zen = MagicMock()
        mock_validation = MagicMock()
        mock_validation.warnings = []
        mock_validation.blocked = True
        mock_validation.modified_command = None
        mock_zen.validate_command.return_value = mock_validation

        executor.zen = mock_zen
        executor.zen_available = True
        executor.validation_enabled = True

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            # Should not raise
            executor.run(["echo", "hello"])
            mock_run.assert_called_once()

    def test_run_auto_fix_applied(self) -> None:
        """Run applies Zen auto-fix when enabled."""
        executor = SafeSubprocessExecutor(auto_fix=True)

        mock_zen = MagicMock()
        mock_validation = MagicMock()
        mock_validation.warnings = []
        mock_validation.blocked = False
        mock_validation.modified_command = "echo fixed"
        mock_zen.validate_command.return_value = mock_validation

        executor.zen = mock_zen
        executor.zen_available = True
        executor.validation_enabled = True

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            executor.run(["echo", "original"])
            # Should use modified command
            call_args = mock_run.call_args
            assert "fixed" in str(call_args)


# =============================================================================
# Test Popen() method
# =============================================================================


class TestPopen:
    """Tests for Popen() method."""

    def test_popen_returns_popen_object(self) -> None:
        """Popen returns a Popen object."""
        executor = SafeSubprocessExecutor()
        executor.validation_enabled = False
        # Use python -c for cross-platform (echo is shell builtin on Windows)
        proc = executor.Popen(["python", "-c", "print('hello')"], stdout=subprocess.PIPE)
        assert isinstance(proc, subprocess.Popen)
        proc.wait()

    def test_popen_with_shell(self) -> None:
        """Popen with shell=True works."""
        executor = SafeSubprocessExecutor()
        executor.validation_enabled = False
        proc = executor.Popen("echo hello", shell=True, stdout=subprocess.PIPE)
        output, _ = proc.communicate()
        assert b"hello" in output

    def test_popen_blocked_in_strict_mode(self) -> None:
        """Popen raises SecurityError when blocked in strict mode."""
        executor = SafeSubprocessExecutor(strict_mode=True)

        mock_zen = MagicMock()
        mock_validation = MagicMock()
        mock_validation.blocked = True
        mock_validation.modified_command = None
        mock_zen.validate_command.return_value = mock_validation

        executor.zen = mock_zen
        executor.zen_available = True
        executor.validation_enabled = True

        with pytest.raises(SecurityError):
            executor.Popen(["rm", "-rf", "/"])

    def test_popen_with_cwd(self, tmp_path: Any) -> None:
        """Popen respects cwd parameter."""
        executor = SafeSubprocessExecutor()
        executor.validation_enabled = False
        proc = executor.Popen(
            ["python", "-c", "import os; print(os.getcwd())"],
            stdout=subprocess.PIPE,
            cwd=tmp_path,
        )
        output, _ = proc.communicate()
        assert tmp_path.name.encode() in output


# =============================================================================
# Test check_output() method
# =============================================================================


class TestCheckOutput:
    """Tests for check_output() method."""

    def test_check_output_returns_bytes(self) -> None:
        """check_output returns bytes."""
        executor = SafeSubprocessExecutor()
        executor.validation_enabled = False
        output = executor.check_output(["python", "-c", "print('test')"])
        assert isinstance(output, bytes)
        assert b"test" in output

    def test_check_output_with_shell(self) -> None:
        """check_output works with shell=True."""
        executor = SafeSubprocessExecutor()
        executor.validation_enabled = False
        output = executor.check_output("echo shell_test", shell=True)
        assert b"shell_test" in output

    def test_check_output_raises_on_error(self) -> None:
        """check_output raises on non-zero exit."""
        executor = SafeSubprocessExecutor()
        executor.validation_enabled = False
        with pytest.raises(subprocess.CalledProcessError):
            executor.check_output("exit 1", shell=True)

    def test_check_output_ignores_text_kwarg(self) -> None:
        """check_output ignores text keyword argument."""
        executor = SafeSubprocessExecutor()
        executor.validation_enabled = False
        # Should not raise even if text=True passed
        output = executor.check_output(["python", "-c", "print('test')"], text=True)
        assert isinstance(output, bytes)


# =============================================================================
# Test SecurityError
# =============================================================================


class TestSecurityError:
    """Tests for SecurityError exception."""

    def test_security_error_is_exception(self) -> None:
        """SecurityError is an Exception."""
        assert issubclass(SecurityError, Exception)

    def test_security_error_with_message(self) -> None:
        """SecurityError accepts message."""
        error = SecurityError("Test message")
        assert str(error) == "Test message"


# =============================================================================
# Test Edge Cases
# =============================================================================


class TestEdgeCases:
    """Tests for edge cases."""

    def test_validation_continues_on_zen_error(self) -> None:
        """Validation continues when Zen raises error."""
        executor = SafeSubprocessExecutor()

        mock_zen = MagicMock()
        mock_zen.validate_command.side_effect = ValueError("Zen error")

        executor.zen = mock_zen
        executor.zen_available = True
        executor.validation_enabled = True

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            # Should not raise
            executor.run(["echo", "hello"])
            mock_run.assert_called_once()

    def test_validation_disabled_when_zen_unavailable(self) -> None:
        """Validation disabled when Zen not available."""
        with patch.dict("sys.modules", {"src.integration.zen_engine_wrapper": None}):
            executor = SafeSubprocessExecutor()
            # Should set zen_available to False
            assert executor.zen is None or executor.zen_available is False

    def test_run_with_all_parameters(self, tmp_path: Any) -> None:
        """Run works with all parameters set."""
        executor = SafeSubprocessExecutor()
        executor.validation_enabled = False
        import os

        result = executor.run(
            ["python", "-c", "print('full')"],
            shell=False,
            check=True,
            timeout=5,
            capture_output=True,
            text=True,
            cwd=tmp_path,
            env=os.environ.copy(),
        )
        assert "full" in result.stdout

    def test_popen_validation_error_continues(self) -> None:
        """Popen continues when validation raises error."""
        executor = SafeSubprocessExecutor()

        mock_zen = MagicMock()
        mock_zen.validate_command.side_effect = TypeError("Error")

        executor.zen = mock_zen
        executor.zen_available = True
        executor.validation_enabled = True

        with patch("subprocess.Popen") as mock_popen:
            mock_popen.return_value = MagicMock()
            executor.Popen(["echo", "test"])
            mock_popen.assert_called_once()

    def test_timeout_expired_reraises(self) -> None:
        """TimeoutExpired is re-raised."""
        executor = SafeSubprocessExecutor()
        executor.validation_enabled = False
        with pytest.raises(subprocess.TimeoutExpired):
            executor.run(
                ["python", "-c", "import time; time.sleep(10)"],
                timeout=0.1,
            )
