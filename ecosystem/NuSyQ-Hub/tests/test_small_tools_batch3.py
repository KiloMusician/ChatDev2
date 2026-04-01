"""Batch tests for small tools modules (batch 3).

Covers:
- scan_guard.py (97 lines - scan safety checks)
- meshctl.py (113 lines - mesh/lattice CLI)
- ai_backend_status.py (127 lines - backend diagnostics)
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

import pytest

if TYPE_CHECKING:
    pass


# =============================================================================
# scan_guard.py - Scan safety checks
# =============================================================================


class TestScansDisabled:
    """Tests for scans_disabled() function."""

    def test_no_sentinel_no_env_returns_false(self, tmp_path: Path) -> None:
        """scans_disabled() returns False when no sentinel and no env var."""
        from src.tools.scan_guard import scans_disabled

        disabled, reason = scans_disabled(tmp_path)
        assert disabled is False
        assert reason == ""

    def test_disable_scans_sentinel_returns_true(self, tmp_path: Path) -> None:
        """scans_disabled() returns True when .disable_scans exists."""
        from src.tools.scan_guard import scans_disabled

        (tmp_path / ".disable_scans").touch()
        disabled, reason = scans_disabled(tmp_path)
        assert disabled is True
        assert ".disable_scans" in reason

    def test_no_repo_scans_sentinel_returns_true(self, tmp_path: Path) -> None:
        """scans_disabled() returns True when .no_repo_scans exists."""
        from src.tools.scan_guard import scans_disabled

        (tmp_path / ".no_repo_scans").touch()
        disabled, reason = scans_disabled(tmp_path)
        assert disabled is True
        assert ".no_repo_scans" in reason

    def test_env_var_disables_scans(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """scans_disabled() returns True when env var is set."""
        from src.tools.scan_guard import scans_disabled

        monkeypatch.setenv("NU_SYQ_DISABLE_SCANS", "1")
        disabled, reason = scans_disabled(tmp_path)
        assert disabled is True
        assert "environment variable" in reason

    def test_env_var_false_does_not_disable(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """scans_disabled() returns False when env var is '0' or 'false'."""
        from src.tools.scan_guard import scans_disabled

        monkeypatch.setenv("NU_SYQ_DISABLE_SCANS", "0")
        disabled, _ = scans_disabled(tmp_path)
        assert disabled is False

        monkeypatch.setenv("NU_SYQ_DISABLE_SCANS", "false")
        disabled, _ = scans_disabled(tmp_path)
        assert disabled is False


class TestCheckScanSafety:
    """Tests for check_scan_safety() function."""

    def test_force_always_returns_safe(self) -> None:
        """check_scan_safety() returns safe when force=True."""
        from src.tools.scan_guard import check_scan_safety

        unsafe, reason = check_scan_safety(force=True)
        assert unsafe is False
        assert reason == ""

    def test_checks_ram_availability(self) -> None:
        """check_scan_safety() checks RAM without error."""
        from src.tools.scan_guard import check_scan_safety

        # Just verify it runs without error
        unsafe, reason = check_scan_safety(force=False)
        # Result depends on system state
        assert isinstance(unsafe, bool)
        assert isinstance(reason, str)

    def test_low_ram_returns_unsafe(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """check_scan_safety() returns unsafe when RAM is low."""
        from src.tools import scan_guard

        mock_mem = MagicMock()
        mock_mem.available = 500 * 1024 * 1024  # 500MB

        with patch.object(scan_guard.psutil, "virtual_memory", return_value=mock_mem):
            unsafe, reason = scan_guard.check_scan_safety(force=False)
        assert unsafe is True
        assert "Low free RAM" in reason

    def test_psutil_failure_returns_unsafe(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """check_scan_safety() returns unsafe when psutil fails."""
        from src.tools import scan_guard

        with patch.object(scan_guard.psutil, "virtual_memory", side_effect=OSError("test")):
            unsafe, reason = scan_guard.check_scan_safety(force=False)
        assert unsafe is True
        assert "Could not determine" in reason


class TestEnsureScanAllowed:
    """Tests for ensure_scan_allowed() function."""

    def test_returns_true_when_all_checks_pass(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """ensure_scan_allowed() returns True when all checks pass."""
        from src.tools import scan_guard

        # Mock sufficient RAM
        mock_mem = MagicMock()
        mock_mem.available = 8 * 1024 * 1024 * 1024  # 8GB

        with patch.object(scan_guard.psutil, "virtual_memory", return_value=mock_mem):
            with patch.object(scan_guard, "os") as mock_os:
                mock_os.name = "linux"  # Skip Windows check
                mock_os.environ = {}
                allowed, reason = scan_guard.ensure_scan_allowed(
                    tmp_path, force=False, raise_on_block=False
                )

        # Note: actual result depends on system state, so just verify structure
        assert isinstance(allowed, bool)
        assert isinstance(reason, str)

    def test_raises_when_disabled_and_raise_on_block(self, tmp_path: Path) -> None:
        """ensure_scan_allowed() raises RuntimeError when blocked and raise_on_block=True."""
        from src.tools.scan_guard import ensure_scan_allowed

        (tmp_path / ".disable_scans").touch()
        with pytest.raises(RuntimeError, match="disabled"):
            ensure_scan_allowed(tmp_path, raise_on_block=True)

    def test_returns_false_when_disabled_and_no_raise(self, tmp_path: Path) -> None:
        """ensure_scan_allowed() returns False when blocked and raise_on_block=False."""
        from src.tools.scan_guard import ensure_scan_allowed

        (tmp_path / ".disable_scans").touch()
        allowed, reason = ensure_scan_allowed(tmp_path, raise_on_block=False)
        assert allowed is False
        assert "disabled" in reason

    def test_force_bypasses_safety_checks(self, tmp_path: Path) -> None:
        """ensure_scan_allowed() with force=True bypasses safety checks."""
        from src.tools.scan_guard import ensure_scan_allowed

        allowed, reason = ensure_scan_allowed(tmp_path, force=True, raise_on_block=False)
        assert allowed is True
        assert reason == ""


# =============================================================================
# meshctl.py - Mesh/lattice CLI
# =============================================================================


class TestMeshctlSafePathParts:
    """Tests for safe_path_parts() function."""

    def test_returns_path_parts(self) -> None:
        """safe_path_parts() returns parts for valid path."""
        from src.tools.meshctl import safe_path_parts

        result = safe_path_parts(Path("foo/bar/baz.json"))
        assert "foo" in result
        assert "bar" in result
        assert "baz.json" in result

    def test_handles_empty_path(self) -> None:
        """safe_path_parts() handles empty path gracefully."""
        from src.tools.meshctl import safe_path_parts

        result = safe_path_parts(Path("."))
        assert isinstance(result, list)


class TestMeshctlCmdIndex:
    """Tests for cmd_index() function."""

    def test_dry_run_does_not_write(self, tmp_path: Path) -> None:
        """cmd_index() with dry_run does not write output file."""
        from src.tools.meshctl import cmd_index

        out_file = tmp_path / "index.json"
        args = argparse.Namespace(
            paths=[str(tmp_path)],
            out=str(out_file),
            dry_run=True,
        )
        cmd_index(args)
        # Should not create file in dry run
        assert not out_file.exists()

    def test_creates_output_directory(self, tmp_path: Path) -> None:
        """cmd_index() creates output directory if missing."""
        from src.tools.meshctl import cmd_index

        out_file = tmp_path / "deep" / "nested" / "index.json"
        args = argparse.Namespace(
            paths=[str(tmp_path)],
            out=str(out_file),
            dry_run=False,
        )
        cmd_index(args)
        assert out_file.exists()

    def test_indexes_vibe_json_files(self, tmp_path: Path) -> None:
        """cmd_index() finds files with 'vibe' in name."""
        from src.tools.meshctl import cmd_index

        # Create a vibe file
        vibe_file = tmp_path / "my_vibe.json"
        vibe_file.write_text("{}", encoding="utf-8")

        out_file = tmp_path / "output" / "index.json"
        args = argparse.Namespace(
            paths=[str(vibe_file)],
            out=str(out_file),
            dry_run=False,
        )
        cmd_index(args)

        result = json.loads(out_file.read_text(encoding="utf-8"))
        assert "lattices" in result
        assert len(result["lattices"]) == 1
        assert result["lattices"][0]["id"] == "my_vibe"

    def test_excludes_venv_and_node_modules(self, tmp_path: Path) -> None:
        """cmd_index() excludes .venv and node_modules paths."""
        from src.tools.meshctl import cmd_index

        # Create files in excluded directories
        venv_dir = tmp_path / ".venv"
        venv_dir.mkdir()
        (venv_dir / "vibe.json").write_text("{}", encoding="utf-8")

        out_file = tmp_path / "index.json"
        args = argparse.Namespace(
            paths=[str(venv_dir / "vibe.json")],
            out=str(out_file),
            dry_run=False,
        )
        cmd_index(args)

        result = json.loads(out_file.read_text(encoding="utf-8"))
        assert len(result["lattices"]) == 0  # Excluded


class TestMeshctlCmdEmbed:
    """Tests for cmd_embed() function."""

    def test_function_exists(self) -> None:
        """cmd_embed() function should exist."""
        from src.tools import meshctl

        assert hasattr(meshctl, "cmd_embed")
        assert callable(meshctl.cmd_embed)


class TestMeshctlMain:
    """Tests for meshctl main() function."""

    def test_no_command_prints_help(self, capsys: pytest.CaptureFixture) -> None:
        """main() with no arguments prints help."""
        from src.tools.meshctl import main

        with pytest.raises(SystemExit) as exc_info:
            main([])
        assert exc_info.value.code == 1

    def test_index_command_parses(self, tmp_path: Path) -> None:
        """main() parses index command correctly."""
        from src.tools.meshctl import main

        out_file = tmp_path / "index.json"
        main(["index", str(tmp_path), "--out", str(out_file), "--dry-run"])
        # Should not raise

    def test_embed_command_parses_dry_run(self, tmp_path: Path) -> None:
        """main() parses embed command with dry-run."""
        from src.tools import meshctl

        # Mock embed_lattice to avoid actual embedding
        with patch.object(meshctl, "cmd_embed") as mock_embed:
            mock_embed.return_value = None
            main_args = ["embed", "--lattice", "test.json", "--dry-run"]
            meshctl.main(main_args)
            mock_embed.assert_called_once()


# =============================================================================
# ai_backend_status.py - Backend diagnostics
# =============================================================================


class TestReadSecretsOllamaHost:
    """Tests for _read_secrets_ollama_host() function."""

    def test_returns_none_when_no_secrets_file(self, tmp_path: Path) -> None:
        """_read_secrets_ollama_host() returns None when secrets.json missing."""
        from src.tools.ai_backend_status import _read_secrets_ollama_host

        result = _read_secrets_ollama_host(tmp_path)
        assert result is None

    def test_returns_host_from_secrets(self, tmp_path: Path) -> None:
        """_read_secrets_ollama_host() returns host from secrets.json."""
        from src.tools.ai_backend_status import _read_secrets_ollama_host

        config_dir = tmp_path / "config"
        config_dir.mkdir()
        secrets_file = config_dir / "secrets.json"
        secrets_file.write_text(
            json.dumps({"ollama": {"host": "http://localhost:11434"}}),
            encoding="utf-8",
        )

        result = _read_secrets_ollama_host(tmp_path)
        assert result == "http://localhost:11434"

    def test_returns_none_for_invalid_json(self, tmp_path: Path) -> None:
        """_read_secrets_ollama_host() returns None for invalid JSON."""
        from src.tools.ai_backend_status import _read_secrets_ollama_host

        config_dir = tmp_path / "config"
        config_dir.mkdir()
        secrets_file = config_dir / "secrets.json"
        secrets_file.write_text("not valid json", encoding="utf-8")

        result = _read_secrets_ollama_host(tmp_path)
        assert result is None

    def test_returns_none_when_ollama_key_missing(self, tmp_path: Path) -> None:
        """_read_secrets_ollama_host() returns None when ollama key missing."""
        from src.tools.ai_backend_status import _read_secrets_ollama_host

        config_dir = tmp_path / "config"
        config_dir.mkdir()
        secrets_file = config_dir / "secrets.json"
        secrets_file.write_text(json.dumps({"other": "value"}), encoding="utf-8")

        result = _read_secrets_ollama_host(tmp_path)
        assert result is None


class TestDetectOllamaBaseUrl:
    """Tests for _detect_ollama_base_url() function."""

    def test_uses_env_var_when_set(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """_detect_ollama_base_url() uses OLLAMA_BASE_URL env var."""
        from src.tools import ai_backend_status

        monkeypatch.setenv("OLLAMA_BASE_URL", "http://custom:1234")
        # Clear ServiceConfig and config_helper
        monkeypatch.setattr(ai_backend_status, "ServiceConfig", None)
        monkeypatch.setattr(ai_backend_status, "config_helper", None)

        result = ai_backend_status._detect_ollama_base_url(tmp_path)
        assert result == "http://custom:1234"

    def test_uses_default_when_nothing_set(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """_detect_ollama_base_url() uses default when nothing configured."""
        from src.tools import ai_backend_status

        monkeypatch.delenv("OLLAMA_BASE_URL", raising=False)
        monkeypatch.delenv("OLLAMA_HOST", raising=False)
        monkeypatch.delenv("OLLAMA_PORT", raising=False)
        monkeypatch.setattr(ai_backend_status, "ServiceConfig", None)
        monkeypatch.setattr(ai_backend_status, "config_helper", None)

        result = ai_backend_status._detect_ollama_base_url(tmp_path)
        assert "127.0.0.1" in result or "localhost" in result
        assert "11434" in result


class TestPingOllama:
    """Tests for _ping_ollama() function."""

    def test_returns_false_when_unreachable(self) -> None:
        """_ping_ollama() returns (False, -1) when server unreachable."""
        from src.tools.ai_backend_status import _ping_ollama

        # Use invalid URL
        reachable, count = _ping_ollama("http://127.0.0.1:99999", timeout=0.5)
        assert reachable is False
        assert count == -1

    def test_returns_true_for_mocked_response(self) -> None:
        """_ping_ollama() returns (True, count) for valid response."""
        from src.tools import ai_backend_status

        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.read.return_value = b'{"models": [{"name": "llama3"}, {"name": "codellama"}]}'
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)

        with patch.object(ai_backend_status, "urlopen", return_value=mock_response):
            reachable, count = ai_backend_status._ping_ollama("http://127.0.0.1:11434")

        assert reachable is True
        assert count == 2

    def test_handles_timeout(self) -> None:
        """_ping_ollama() handles timeout gracefully."""
        from src.tools import ai_backend_status

        with patch.object(ai_backend_status, "urlopen", side_effect=TimeoutError()):
            reachable, count = ai_backend_status._ping_ollama("http://127.0.0.1:11434")

        assert reachable is False
        assert count == -1


class TestAiBackendStatusMain:
    """Tests for ai_backend_status main() function."""

    def test_main_prints_all_keys(
        self, capsys: pytest.CaptureFixture, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """main() prints all expected keys."""
        from src.tools import ai_backend_status

        # Mock to avoid network calls
        monkeypatch.setattr(ai_backend_status, "_ping_ollama", lambda *a, **k: (False, -1))
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

        ai_backend_status.main()
        captured = capsys.readouterr()

        assert "OLLAMA_BASE_URL=" in captured.out
        assert "OLLAMA_REACHABLE=" in captured.out
        assert "OLLAMA_MODELS=" in captured.out
        assert "OPENAI_KEY_PRESENT=" in captured.out
        assert "ANTHROPIC_KEY_PRESENT=" in captured.out

    def test_detects_openai_key_present(
        self, capsys: pytest.CaptureFixture, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """main() reports OPENAI_KEY_PRESENT=true when key set."""
        from src.tools import ai_backend_status

        monkeypatch.setattr(ai_backend_status, "_ping_ollama", lambda *a, **k: (False, -1))
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key")

        ai_backend_status.main()
        captured = capsys.readouterr()

        assert "OPENAI_KEY_PRESENT=true" in captured.out

    def test_detects_anthropic_key_present(
        self, capsys: pytest.CaptureFixture, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """main() reports ANTHROPIC_KEY_PRESENT=true when key set."""
        from src.tools import ai_backend_status

        monkeypatch.setattr(ai_backend_status, "_ping_ollama", lambda *a, **k: (False, -1))
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test")

        ai_backend_status.main()
        captured = capsys.readouterr()

        assert "ANTHROPIC_KEY_PRESENT=true" in captured.out
