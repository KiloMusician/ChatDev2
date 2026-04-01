"""Tests for src/services/ollama_service_manager.py

This module tests the Ollama Service Manager which handles WSL/native
Ollama lifecycle management.

Coverage Target: 70%+
"""

from unittest.mock import MagicMock, patch

import pytest

# =============================================================================
# Module Import Tests
# =============================================================================


class TestModuleImports:
    """Test module-level imports."""

    def test_import_ollama_environment(self):
        """Test OllamaEnvironment enum can be imported."""
        from src.services.ollama_service_manager import OllamaEnvironment

        assert OllamaEnvironment.NATIVE_WINDOWS == "native_windows"
        assert OllamaEnvironment.WSL == "wsl"
        assert OllamaEnvironment.DOCKER == "docker"
        assert OllamaEnvironment.UNAVAILABLE == "unavailable"

    def test_import_ollama_status(self):
        """Test OllamaStatus dataclass can be imported."""
        from src.services.ollama_service_manager import OllamaStatus

        assert OllamaStatus is not None

    def test_import_ollama_service_manager(self):
        """Test OllamaServiceManager class can be imported."""
        from src.services.ollama_service_manager import OllamaServiceManager

        assert OllamaServiceManager is not None

    def test_import_ensure_ollama(self):
        """Test ensure_ollama convenience function can be imported."""
        from src.services.ollama_service_manager import ensure_ollama

        assert ensure_ollama is not None

    def test_import_get_ollama_status(self):
        """Test get_ollama_status convenience function can be imported."""
        from src.services.ollama_service_manager import get_ollama_status

        assert get_ollama_status is not None


# =============================================================================
# OllamaStatus Tests
# =============================================================================


class TestOllamaStatus:
    """Test OllamaStatus dataclass."""

    def test_create_healthy_status(self):
        """Test creating a healthy status."""
        from src.services.ollama_service_manager import OllamaEnvironment, OllamaStatus

        status = OllamaStatus(
            healthy=True,
            environment=OllamaEnvironment.NATIVE_WINDOWS,
            models_available=5,
            latency_ms=42.5,
        )

        assert status.healthy is True
        assert status.environment == OllamaEnvironment.NATIVE_WINDOWS
        assert status.models_available == 5
        assert status.latency_ms == 42.5

    def test_create_unhealthy_status(self):
        """Test creating an unhealthy status with error."""
        from src.services.ollama_service_manager import OllamaEnvironment, OllamaStatus

        status = OllamaStatus(
            healthy=False,
            environment=OllamaEnvironment.UNAVAILABLE,
            error="Connection refused",
            wsl_relay_stale=True,
        )

        assert status.healthy is False
        assert status.error == "Connection refused"
        assert status.wsl_relay_stale is True

    def test_to_dict(self):
        """Test OllamaStatus.to_dict() method."""
        from src.services.ollama_service_manager import OllamaEnvironment, OllamaStatus

        status = OllamaStatus(
            healthy=True,
            environment=OllamaEnvironment.WSL,
            models_available=3,
            latency_ms=15.678,
            detail="Test detail",
        )

        d = status.to_dict()

        assert d["healthy"] is True
        assert d["environment"] == "wsl"
        assert d["models_available"] == 3
        assert d["latency_ms"] == 15.7  # Rounded to 1 decimal
        assert d["detail"] == "Test detail"

    def test_to_dict_none_latency(self):
        """Test to_dict with None latency."""
        from src.services.ollama_service_manager import OllamaEnvironment, OllamaStatus

        status = OllamaStatus(
            healthy=False,
            environment=OllamaEnvironment.UNAVAILABLE,
            latency_ms=None,
        )

        d = status.to_dict()
        assert d["latency_ms"] is None


# =============================================================================
# OllamaServiceManager Init Tests
# =============================================================================


class TestOllamaServiceManagerInit:
    """Test OllamaServiceManager initialization."""

    def test_init_default(self):
        """Test default initialization."""
        from src.services.ollama_service_manager import OllamaServiceManager

        with patch.object(OllamaServiceManager, "ensure_running") as mock_ensure:
            mgr = OllamaServiceManager(auto_start=False)

            mock_ensure.assert_not_called()
            assert mgr._environment is None
            assert mgr._last_status is None

    def test_init_with_auto_start(self):
        """Test initialization with auto_start=True."""
        from src.services.ollama_service_manager import OllamaServiceManager

        with patch.object(OllamaServiceManager, "ensure_running") as mock_ensure:
            mock_ensure.return_value = True
            OllamaServiceManager(auto_start=True)

            mock_ensure.assert_called_once()

    def test_base_url_property(self):
        """Test base_url property."""
        from src.services.ollama_service_manager import OllamaServiceManager

        mgr = OllamaServiceManager(auto_start=False)

        assert mgr.base_url == "http://127.0.0.1:11434"


# =============================================================================
# Environment Detection Tests
# =============================================================================


class TestDetectEnvironment:
    """Test environment detection."""

    def test_detect_native_windows_in_path(self):
        """Test detecting native Windows Ollama in PATH."""
        from src.services.ollama_service_manager import OllamaEnvironment, OllamaServiceManager

        with (
            patch("shutil.which", return_value="C:\\Program Files\\Ollama\\ollama.exe"),
            patch.object(OllamaServiceManager, "_is_wsl_runtime", return_value=False),
        ):
            mgr = OllamaServiceManager(auto_start=False)
            env = mgr.detect_environment()

            assert env == OllamaEnvironment.NATIVE_WINDOWS

    def test_detect_wsl(self):
        """Test detecting Ollama in WSL."""
        from src.services.ollama_service_manager import OllamaEnvironment, OllamaServiceManager

        with (
            patch("shutil.which", return_value=None),
            patch("pathlib.Path.exists", return_value=False),
            patch("sys.platform", "win32"),
            patch("subprocess.run") as mock_run,
        ):
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="/usr/bin/ollama\n",
            )

            mgr = OllamaServiceManager(auto_start=False)
            mgr._environment = None  # Reset cached value
            env = mgr.detect_environment()

            assert env == OllamaEnvironment.WSL

    def test_detect_wsl_from_local_runtime_path(self):
        """A WSL runtime with ollama on PATH must not be mislabeled as native Windows."""
        from src.services.ollama_service_manager import OllamaEnvironment, OllamaServiceManager

        with (
            patch("shutil.which", return_value="/usr/local/bin/ollama"),
            patch.object(OllamaServiceManager, "_is_wsl_runtime", return_value=True),
        ):
            mgr = OllamaServiceManager(auto_start=False)
            env = mgr.detect_environment()

            assert env == OllamaEnvironment.WSL

    def test_detect_docker(self):
        """Test detecting Ollama in Docker."""
        from src.services.ollama_service_manager import OllamaEnvironment, OllamaServiceManager

        with (
            patch("shutil.which", return_value=None),
            patch("pathlib.Path.exists", return_value=False),
            patch("sys.platform", "linux"),
            patch("subprocess.run") as mock_run,
        ):
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="ollama\n",
            )

            mgr = OllamaServiceManager(auto_start=False)
            mgr._environment = None
            env = mgr.detect_environment()

            assert env == OllamaEnvironment.DOCKER

    def test_detect_unavailable(self):
        """Test detecting Ollama as unavailable."""
        from src.services.ollama_service_manager import OllamaEnvironment, OllamaServiceManager

        with (
            patch("shutil.which", return_value=None),
            patch("pathlib.Path.exists", return_value=False),
            patch("sys.platform", "linux"),
            patch("subprocess.run") as mock_run,
        ):
            mock_run.return_value = MagicMock(returncode=1, stdout="")

            mgr = OllamaServiceManager(auto_start=False)
            mgr._environment = None
            env = mgr.detect_environment()

            assert env == OllamaEnvironment.UNAVAILABLE

    def test_cached_environment(self):
        """Test that environment is cached after first detection."""
        from src.services.ollama_service_manager import OllamaEnvironment, OllamaServiceManager

        with (
            patch("shutil.which", return_value="ollama.exe"),
            patch.object(OllamaServiceManager, "_is_wsl_runtime", return_value=False),
        ):
            mgr = OllamaServiceManager(auto_start=False)

            # First call
            env1 = mgr.detect_environment()

            # Change the mock (wouldn't matter if cached)
            with patch("shutil.which", return_value=None):
                env2 = mgr.detect_environment()

            assert env1 == env2 == OllamaEnvironment.NATIVE_WINDOWS


# =============================================================================
# Health Check Tests
# =============================================================================


class TestCheckHealth:
    """Test health check functionality."""

    def test_healthy_response(self):
        """Test handling healthy Ollama response."""
        from src.services.ollama_service_manager import OllamaServiceManager

        mock_response = MagicMock()
        mock_response.read.return_value = b'{"models": [{"name": "llama2"}, {"name": "codellama"}]}'
        mock_response.__enter__ = lambda s: mock_response
        mock_response.__exit__ = MagicMock(return_value=False)

        with (
            patch("shutil.which", return_value="ollama.exe"),
            patch("urllib.request.urlopen", return_value=mock_response),
        ):
            mgr = OllamaServiceManager(auto_start=False)
            status = mgr.check_health()

            assert status.healthy is True
            assert status.models_available == 2

    def test_unhealthy_connection_refused(self):
        """Test handling connection refused."""
        from src.services.ollama_service_manager import OllamaServiceManager

        with (
            patch("shutil.which", return_value="ollama.exe"),
            patch(
                "urllib.request.urlopen", side_effect=ConnectionRefusedError("Connection refused")
            ),
            patch.object(OllamaServiceManager, "_check_wsl_relay_stale", return_value=False),
        ):
            mgr = OllamaServiceManager(auto_start=False)
            status = mgr.check_health()

            assert status.healthy is False
            assert "Connection refused" in status.error

    def test_unhealthy_with_stale_wsl_relay(self):
        """Test handling unhealthy with stale WSL relay."""
        from src.services.ollama_service_manager import OllamaServiceManager

        with (
            patch("shutil.which", return_value=None),
            patch("pathlib.Path.exists", return_value=False),
            patch("sys.platform", "win32"),
            patch("subprocess.run") as mock_run,
            patch("urllib.request.urlopen", side_effect=Exception("WinError 10053")),
            patch.object(OllamaServiceManager, "_check_wsl_relay_stale", return_value=True),
        ):
            # WSL detection
            mock_run.return_value = MagicMock(returncode=0, stdout="/usr/bin/ollama\n")

            mgr = OllamaServiceManager(auto_start=False)
            mgr._environment = None
            status = mgr.check_health()

            assert status.healthy is False
            assert status.wsl_relay_stale is True
            assert "WSL relay stale" in status.detail

    def test_is_healthy_shortcut(self):
        """Test is_healthy() convenience method."""
        from src.services.ollama_service_manager import (
            OllamaEnvironment,
            OllamaServiceManager,
            OllamaStatus,
        )

        with patch.object(OllamaServiceManager, "check_health") as mock_check:
            mock_check.return_value = OllamaStatus(
                healthy=True,
                environment=OllamaEnvironment.NATIVE_WINDOWS,
            )

            mgr = OllamaServiceManager(auto_start=False)
            result = mgr.is_healthy()

            assert result is True


# =============================================================================
# Start Methods Tests
# =============================================================================


class TestStartMethods:
    """Test Ollama start methods."""

    def test_start_native_windows_success(self):
        """Test starting native Windows Ollama."""
        from src.services.ollama_service_manager import OllamaServiceManager

        with (
            patch("shutil.which", return_value="C:\\ollama\\ollama.exe"),
            patch("subprocess.Popen") as mock_popen,
        ):
            mgr = OllamaServiceManager(auto_start=False)
            result = mgr._start_native_windows()

            assert result is True
            mock_popen.assert_called_once()

    def test_start_native_windows_not_found(self):
        """Test starting native Windows when not found."""
        from src.services.ollama_service_manager import OllamaServiceManager

        with (
            patch("shutil.which", return_value=None),
            patch("pathlib.Path.exists", return_value=False),
        ):
            mgr = OllamaServiceManager(auto_start=False)
            result = mgr._start_native_windows()

            assert result is False

    def test_start_wsl_success(self):
        """Test starting Ollama in WSL."""
        from src.services.ollama_service_manager import OllamaServiceManager

        with (
            patch.object(OllamaServiceManager, "_is_wsl_runtime", return_value=True),
            patch.object(
                OllamaServiceManager, "_managed_ollama_home", return_value="/tmp/nusyq-ollama-home"
            ),
            patch("subprocess.Popen") as mock_popen,
        ):
            mgr = OllamaServiceManager(auto_start=False)
            result = mgr._start_wsl(restart_wsl=False)

            assert result is True
            mock_popen.assert_called_once()
            command = mock_popen.call_args.args[0]
            assert command[:2] == ["bash", "-lc"]
            assert "OLLAMA_HOME=/tmp/nusyq-ollama-home" in command[2]
            assert "HOME=/tmp/nusyq-ollama-home" in command[2]
            assert mock_popen.call_args.kwargs["env"]["OLLAMA_HOME"] == "/tmp/nusyq-ollama-home"

    def test_start_wsl_with_restart(self):
        """Test starting WSL with restart (clearing stale relay)."""
        from src.services.ollama_service_manager import OllamaServiceManager

        with (
            patch.object(OllamaServiceManager, "_is_wsl_runtime", return_value=False),
            patch("subprocess.run") as mock_run,
            patch("subprocess.Popen"),
            patch("time.sleep"),
        ):
            mock_run.return_value = MagicMock(returncode=0)

            mgr = OllamaServiceManager(auto_start=False)
            result = mgr._start_wsl(restart_wsl=True)

            assert result is True
            # Should have called wsl --shutdown
            shutdown_call = [c for c in mock_run.call_args_list if "shutdown" in str(c)]
            assert len(shutdown_call) >= 1

    def test_start_docker_success(self):
        """Test starting Ollama Docker container."""
        from src.services.ollama_service_manager import OllamaServiceManager

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)

            mgr = OllamaServiceManager(auto_start=False)
            result = mgr._start_docker()

            assert result is True

    def test_start_docker_failure(self):
        """Test starting Docker failure."""
        from src.services.ollama_service_manager import OllamaServiceManager

        with patch("subprocess.run", side_effect=Exception("Docker not found")):
            mgr = OllamaServiceManager(auto_start=False)
            result = mgr._start_docker()

            assert result is False


# =============================================================================
# Start Orchestration Tests
# =============================================================================


class TestStartOrchestration:
    """Test the main start() orchestration."""

    def test_start_already_healthy(self):
        """Test start() when already healthy."""
        from src.services.ollama_service_manager import (
            OllamaEnvironment,
            OllamaServiceManager,
            OllamaStatus,
        )

        with (
            patch("shutil.which", return_value="ollama.exe"),
            patch.object(OllamaServiceManager, "check_health") as mock_check,
        ):
            mock_check.return_value = OllamaStatus(
                healthy=True,
                environment=OllamaEnvironment.NATIVE_WINDOWS,
            )

            mgr = OllamaServiceManager(auto_start=False)
            result = mgr.start()

            assert result is True

    def test_start_unavailable_environment(self):
        """Test start() when Ollama is unavailable."""
        from src.services.ollama_service_manager import OllamaEnvironment, OllamaServiceManager

        with patch.object(
            OllamaServiceManager, "detect_environment", return_value=OllamaEnvironment.UNAVAILABLE
        ):
            mgr = OllamaServiceManager(auto_start=False)
            result = mgr.start()

            assert result is False

    def test_start_native_with_wait(self):
        """Test start() for native Windows with health wait."""
        from src.services.ollama_service_manager import (
            OllamaEnvironment,
            OllamaServiceManager,
            OllamaStatus,
        )

        check_call_count = [0]

        def mock_check(*args, **kwargs):
            check_call_count[0] += 1
            if check_call_count[0] == 1:
                return OllamaStatus(healthy=False, environment=OllamaEnvironment.NATIVE_WINDOWS)
            return OllamaStatus(healthy=True, environment=OllamaEnvironment.NATIVE_WINDOWS)

        with (
            patch.object(
                OllamaServiceManager,
                "detect_environment",
                return_value=OllamaEnvironment.NATIVE_WINDOWS,
            ),
            patch.object(OllamaServiceManager, "check_health", side_effect=mock_check),
            patch.object(OllamaServiceManager, "_start_native_windows", return_value=True),
            patch("time.sleep"),
        ):
            mgr = OllamaServiceManager(auto_start=False)
            result = mgr.start()

            assert result is True


# =============================================================================
# Ensure Running Tests
# =============================================================================


class TestEnsureRunning:
    """Test ensure_running() auto-recovery."""

    def test_ensure_running_already_healthy(self):
        """Test ensure_running when already healthy."""
        from src.services.ollama_service_manager import (
            OllamaEnvironment,
            OllamaServiceManager,
            OllamaStatus,
        )

        with patch.object(OllamaServiceManager, "check_health") as mock_check:
            mock_check.return_value = OllamaStatus(
                healthy=True,
                environment=OllamaEnvironment.NATIVE_WINDOWS,
            )

            mgr = OllamaServiceManager(auto_start=False)
            result = mgr.ensure_running()

            assert result is True

    def test_ensure_running_starts_when_unhealthy(self):
        """Test ensure_running starts Ollama when unhealthy."""
        from src.services.ollama_service_manager import (
            OllamaEnvironment,
            OllamaServiceManager,
            OllamaStatus,
        )

        with (
            patch.object(OllamaServiceManager, "check_health") as mock_check,
            patch.object(OllamaServiceManager, "start") as mock_start,
        ):
            mock_check.return_value = OllamaStatus(
                healthy=False,
                environment=OllamaEnvironment.NATIVE_WINDOWS,
                detail="Connection refused",
            )
            mock_start.return_value = True

            mgr = OllamaServiceManager(auto_start=False)
            result = mgr.ensure_running()

            mock_start.assert_called_once()
            assert result is True


class TestWaitForHealth:
    """Regression tests for _wait_for_health()."""

    def test_wait_for_health_accepts_force_probe_keyword(self):
        from src.services.ollama_service_manager import (
            OllamaEnvironment,
            OllamaServiceManager,
            OllamaStatus,
        )

        calls: list[dict[str, object]] = []

        def fake_check_health(*args, **kwargs):
            calls.append(dict(kwargs))
            return OllamaStatus(healthy=True, environment=OllamaEnvironment.NATIVE_WINDOWS)

        with patch.object(OllamaServiceManager, "check_health", side_effect=fake_check_health), patch(
            "time.sleep"
        ):
            mgr = OllamaServiceManager(auto_start=False)
            assert mgr._wait_for_health() is True

        assert calls and calls[0].get("force_probe") is True


# =============================================================================
# Restart Tests
# =============================================================================


class TestRestart:
    """Test restart() functionality."""

    def test_restart_wsl_forces_restart(self):
        """Test restart() forces WSL restart."""
        from src.services.ollama_service_manager import OllamaEnvironment, OllamaServiceManager

        with (
            patch.object(
                OllamaServiceManager, "detect_environment", return_value=OllamaEnvironment.WSL
            ),
            patch.object(OllamaServiceManager, "start") as mock_start,
        ):
            mock_start.return_value = True

            mgr = OllamaServiceManager(auto_start=False)
            mgr.restart()

            mock_start.assert_called_once_with(force_wsl_restart=True)

    def test_restart_native_no_force(self):
        """Test restart() for native doesn't force WSL restart."""
        from src.services.ollama_service_manager import OllamaEnvironment, OllamaServiceManager

        with (
            patch.object(
                OllamaServiceManager,
                "detect_environment",
                return_value=OllamaEnvironment.NATIVE_WINDOWS,
            ),
            patch.object(OllamaServiceManager, "start") as mock_start,
        ):
            mock_start.return_value = True

            mgr = OllamaServiceManager(auto_start=False)
            mgr.restart()

            mock_start.assert_called_once_with()


# =============================================================================
# Convenience Function Tests
# =============================================================================


class TestConvenienceFunctions:
    """Test module-level convenience functions."""

    def test_ensure_ollama(self):
        """Test ensure_ollama() function."""
        from src.services.ollama_service_manager import ensure_ollama

        with patch("src.services.ollama_service_manager.OllamaServiceManager") as mock_class:
            mock_instance = MagicMock()
            mock_instance.ensure_running.return_value = True
            mock_class.return_value = mock_instance

            result = ensure_ollama()

            assert result is True
            mock_instance.ensure_running.assert_called_once()

    def test_get_ollama_status(self):
        """Test get_ollama_status() function."""
        from src.services.ollama_service_manager import (
            OllamaEnvironment,
            OllamaStatus,
            get_ollama_status,
        )

        with patch("src.services.ollama_service_manager.OllamaServiceManager") as mock_class:
            mock_status = OllamaStatus(
                healthy=True,
                environment=OllamaEnvironment.NATIVE_WINDOWS,
                models_available=5,
            )
            mock_instance = MagicMock()
            mock_instance.check_health.return_value = mock_status
            mock_class.return_value = mock_instance

            result = get_ollama_status()

            assert result.healthy is True
            assert result.models_available == 5


# =============================================================================
# WSL Relay Stale Detection Tests
# =============================================================================


class TestWslRelayStaleDetection:
    """Test WSL relay stale detection."""

    def test_check_wsl_relay_stale_not_windows(self):
        """Test _check_wsl_relay_stale returns False on non-Windows."""
        from src.services.ollama_service_manager import OllamaServiceManager

        with patch("sys.platform", "linux"):
            mgr = OllamaServiceManager(auto_start=False)
            result = mgr._check_wsl_relay_stale()

            assert result is False

    def test_check_wsl_relay_stale_no_listener(self):
        """Test _check_wsl_relay_stale when no listener on port."""
        from src.services.ollama_service_manager import OllamaServiceManager

        with patch("sys.platform", "win32"), patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                stdout="No listening ports",
                returncode=0,
            )

            mgr = OllamaServiceManager(auto_start=False)
            result = mgr._check_wsl_relay_stale()

            assert result is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
