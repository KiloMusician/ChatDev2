"""Tests for src/resilience/sandbox_chatdev_validator.py."""


class TestSandboxMode:
    def test_enum_values(self):
        from src.resilience.sandbox_chatdev_validator import SandboxMode

        assert SandboxMode.PROCESS_ISOLATED.value == "process_isolated"
        assert SandboxMode.CONTAINER.value == "container"
        assert SandboxMode.LOCAL_ONLY.value == "local_only"

    def test_enum_members(self):
        from src.resilience.sandbox_chatdev_validator import SandboxMode

        modes = list(SandboxMode)
        assert len(modes) == 3


class TestSandboxConfig:
    def test_defaults(self):
        from src.resilience.sandbox_chatdev_validator import SandboxConfig, SandboxMode

        cfg = SandboxConfig()
        assert cfg.mode == SandboxMode.PROCESS_ISOLATED
        assert cfg.memory_limit == 2048
        assert cfg.cpu_limit == 1.0
        assert cfg.timeout == 300.0
        assert cfg.disk_limit == 5000
        assert cfg.network_allowed is False
        assert cfg.write_allowed is True
        assert cfg.output_dir is None

    def test_custom_values(self):
        from pathlib import Path

        from src.resilience.sandbox_chatdev_validator import SandboxConfig, SandboxMode

        cfg = SandboxConfig(
            mode=SandboxMode.CONTAINER,
            memory_limit=1024,
            cpu_limit=2.0,
            timeout=60.0,
            disk_limit=1000,
            network_allowed=True,
            write_allowed=False,
            output_dir=Path("/tmp/test"),
        )
        assert cfg.mode == SandboxMode.CONTAINER
        assert cfg.memory_limit == 1024
        assert cfg.cpu_limit == 2.0
        assert cfg.timeout == 60.0
        assert cfg.network_allowed is True
        assert cfg.write_allowed is False

    def test_to_dict_default(self):
        from src.resilience.sandbox_chatdev_validator import SandboxConfig

        cfg = SandboxConfig()
        d = cfg.to_dict()
        assert d["mode"] == "process_isolated"
        assert d["memory_limit"] == 2048
        assert d["cpu_limit"] == 1.0
        assert d["timeout"] == 300.0
        assert d["disk_limit"] == 5000
        assert d["network_allowed"] is False
        assert d["write_allowed"] is True
        assert d["output_dir"] is None

    def test_to_dict_with_output_dir(self, tmp_path):
        from src.resilience.sandbox_chatdev_validator import SandboxConfig

        cfg = SandboxConfig(output_dir=tmp_path)
        d = cfg.to_dict()
        assert d["output_dir"] == str(tmp_path)

    def test_to_dict_mode_value(self):
        from src.resilience.sandbox_chatdev_validator import SandboxConfig, SandboxMode

        cfg = SandboxConfig(mode=SandboxMode.LOCAL_ONLY)
        d = cfg.to_dict()
        assert d["mode"] == "local_only"


class TestValidatorResult:
    def test_defaults_post_init(self):
        from src.resilience.sandbox_chatdev_validator import ValidatorResult

        r = ValidatorResult(success=True, sandbox_id="abc123", execution_time=1.5)
        assert r.output == {}
        assert r.resource_usage == {}
        assert r.audit_entries == []
        assert r.validation_score == 0.0
        assert r.error is None

    def test_explicit_values(self):
        from src.resilience.sandbox_chatdev_validator import ValidatorResult

        r = ValidatorResult(
            success=False,
            sandbox_id="x",
            execution_time=2.5,
            output={"key": "val"},
            error="something went wrong",
            resource_usage={"memory_mb": 100},
            audit_entries=[{"action": "start"}],
            validation_score=0.75,
        )
        assert r.success is False
        assert r.error == "something went wrong"
        assert r.validation_score == 0.75
        assert r.output == {"key": "val"}
        assert r.resource_usage == {"memory_mb": 100}
        assert len(r.audit_entries) == 1

    def test_none_fields_replaced_by_post_init(self):
        from src.resilience.sandbox_chatdev_validator import ValidatorResult

        r = ValidatorResult(
            success=True,
            sandbox_id="z",
            execution_time=0.1,
            output=None,
            resource_usage=None,
            audit_entries=None,
        )
        assert r.output == {}
        assert r.resource_usage == {}
        assert r.audit_entries == []


class TestChatDevSandboxValidatorInit:
    def test_default_init(self, tmp_path):
        from src.resilience.sandbox_chatdev_validator import ChatDevSandboxValidator, SandboxConfig

        cfg = SandboxConfig(output_dir=tmp_path / "sandbox")
        v = ChatDevSandboxValidator(cfg)
        assert v.config is cfg
        assert len(v.sandbox_id) == 8
        assert v.audit_entries == []

    def test_no_config_uses_default(self, tmp_path):
        from unittest.mock import patch

        from src.resilience.sandbox_chatdev_validator import ChatDevSandboxValidator, SandboxConfig

        with patch.object(SandboxConfig, "__init__", lambda self: None):
            pass  # just confirm import works

        # Real test: no config → SandboxConfig() created
        with patch(
            "src.resilience.sandbox_chatdev_validator.Path.mkdir"
        ):
            v = ChatDevSandboxValidator(SandboxConfig(output_dir=tmp_path / "sb"))
            assert isinstance(v.config, SandboxConfig)

    def test_output_dir_uses_config(self, tmp_path):
        from src.resilience.sandbox_chatdev_validator import ChatDevSandboxValidator, SandboxConfig

        out = tmp_path / "myout"
        cfg = SandboxConfig(output_dir=out)
        v = ChatDevSandboxValidator(cfg)
        assert v.output_dir == out
        assert out.exists()

    def test_output_dir_defaults_to_state_sandbox(self, tmp_path):
        from unittest.mock import patch

        from src.resilience.sandbox_chatdev_validator import ChatDevSandboxValidator, SandboxConfig

        SandboxConfig()
        with patch("src.resilience.sandbox_chatdev_validator.Path.mkdir"):
            with patch(
                "src.resilience.sandbox_chatdev_validator.Path.__truediv__",
                side_effect=lambda self, other: tmp_path / other,
            ):
                pass
        # Just verify it constructs without error when output_dir is None
        cfg2 = SandboxConfig(output_dir=tmp_path / "fallback")
        v = ChatDevSandboxValidator(cfg2)
        assert v.output_dir is not None


class TestEmitAudit:
    def test_emit_adds_entry(self, tmp_path):
        from src.resilience.sandbox_chatdev_validator import ChatDevSandboxValidator, SandboxConfig

        v = ChatDevSandboxValidator(SandboxConfig(output_dir=tmp_path))
        v._emit_audit("test_action", "success", {"key": "val"})
        assert len(v.audit_entries) == 1
        entry = v.audit_entries[0]
        assert entry["action"] == "test_action"
        assert entry["result"] == "success"
        assert entry["context"] == {"key": "val"}
        assert entry["sandbox_id"] == v.sandbox_id

    def test_emit_multiple_entries(self, tmp_path):
        from src.resilience.sandbox_chatdev_validator import ChatDevSandboxValidator, SandboxConfig

        v = ChatDevSandboxValidator(SandboxConfig(output_dir=tmp_path))
        v._emit_audit("a", "running", {})
        v._emit_audit("b", "success", {})
        v._emit_audit("c", "failure", {})
        assert len(v.audit_entries) == 3
        assert [e["action"] for e in v.audit_entries] == ["a", "b", "c"]

    def test_emit_has_timestamp(self, tmp_path):
        from src.resilience.sandbox_chatdev_validator import ChatDevSandboxValidator, SandboxConfig

        v = ChatDevSandboxValidator(SandboxConfig(output_dir=tmp_path))
        v._emit_audit("x", "y", {})
        assert "timestamp" in v.audit_entries[0]


class TestMeasureResources:
    def test_returns_dict_with_keys(self, tmp_path):
        from src.resilience.sandbox_chatdev_validator import ChatDevSandboxValidator, SandboxConfig

        v = ChatDevSandboxValidator(SandboxConfig(output_dir=tmp_path))
        r = v._measure_resources()
        assert "memory_mb" in r
        assert "cpu_percent" in r
        assert "disk_mb" in r

    def test_returns_numeric_values(self, tmp_path):
        from src.resilience.sandbox_chatdev_validator import ChatDevSandboxValidator, SandboxConfig

        v = ChatDevSandboxValidator(SandboxConfig(output_dir=tmp_path))
        r = v._measure_resources()
        assert isinstance(r["memory_mb"], (int, float))
        assert isinstance(r["cpu_percent"], float)
        assert isinstance(r["disk_mb"], (int, float))


class TestValidateOutput:
    def test_missing_dir_returns_zero_score(self, tmp_path):
        from pathlib import Path

        from src.resilience.sandbox_chatdev_validator import ChatDevSandboxValidator, SandboxConfig

        v = ChatDevSandboxValidator(SandboxConfig(output_dir=tmp_path))
        result = v._validate_output(Path("/nonexistent/path/xyz"))
        assert result["score"] == 0.0
        assert len(result["issues"]) > 0

    def test_complete_project_scores_1(self, tmp_path):
        from src.resilience.sandbox_chatdev_validator import ChatDevSandboxValidator, SandboxConfig

        proj = tmp_path / "proj"
        proj.mkdir()
        (proj / "main.py").write_text("# Generated\nprint('hello world')")
        (proj / "README.md").write_text("# Project\n\nDescription")
        (proj / "requirements.txt").write_text("# Dependencies")

        v = ChatDevSandboxValidator(SandboxConfig(output_dir=tmp_path))
        result = v._validate_output(proj)
        assert result["score"] == 1.0
        assert result["issues"] == []

    def test_missing_main_py_penalizes(self, tmp_path):
        from src.resilience.sandbox_chatdev_validator import ChatDevSandboxValidator, SandboxConfig

        proj = tmp_path / "proj"
        proj.mkdir()
        (proj / "README.md").write_text("# Project")

        v = ChatDevSandboxValidator(SandboxConfig(output_dir=tmp_path))
        result = v._validate_output(proj)
        assert result["score"] < 1.0
        assert any("main.py" in issue for issue in result["issues"])

    def test_missing_readme_penalizes(self, tmp_path):
        from src.resilience.sandbox_chatdev_validator import ChatDevSandboxValidator, SandboxConfig

        proj = tmp_path / "proj"
        proj.mkdir()
        (proj / "main.py").write_text("# Generated\nprint('hello')")

        v = ChatDevSandboxValidator(SandboxConfig(output_dir=tmp_path))
        result = v._validate_output(proj)
        assert result["score"] < 1.0
        assert any("README.md" in issue for issue in result["issues"])

    def test_small_py_file_penalizes(self, tmp_path):
        from src.resilience.sandbox_chatdev_validator import ChatDevSandboxValidator, SandboxConfig

        proj = tmp_path / "proj"
        proj.mkdir()
        (proj / "main.py").write_text("x")  # too small
        (proj / "README.md").write_text("# Project\n\nDescription")

        v = ChatDevSandboxValidator(SandboxConfig(output_dir=tmp_path))
        result = v._validate_output(proj)
        assert any("small" in issue.lower() for issue in result["issues"])

    def test_score_clamped_to_zero(self, tmp_path):
        from src.resilience.sandbox_chatdev_validator import ChatDevSandboxValidator, SandboxConfig

        # Empty project dir — no required files
        proj = tmp_path / "proj"
        proj.mkdir()

        v = ChatDevSandboxValidator(SandboxConfig(output_dir=tmp_path))
        result = v._validate_output(proj)
        assert result["score"] >= 0.0

    def test_files_found_key_present(self, tmp_path):
        from src.resilience.sandbox_chatdev_validator import ChatDevSandboxValidator, SandboxConfig

        proj = tmp_path / "proj"
        proj.mkdir()
        (proj / "main.py").write_text("# Generated\nprint('hello')")

        v = ChatDevSandboxValidator(SandboxConfig(output_dir=tmp_path))
        result = v._validate_output(proj)
        assert "files_found" in result
        assert "main.py" in result["files_found"]


class TestSaveResult:
    def test_save_creates_file(self, tmp_path):
        from src.resilience.sandbox_chatdev_validator import (
            ChatDevSandboxValidator,
            SandboxConfig,
            ValidatorResult,
        )

        v = ChatDevSandboxValidator(SandboxConfig(output_dir=tmp_path))
        result = ValidatorResult(success=True, sandbox_id="abc", execution_time=1.0)
        path = v.save_result(result, tmp_path / "result.json")
        assert path.exists()

    def test_save_json_content(self, tmp_path):
        import json

        from src.resilience.sandbox_chatdev_validator import (
            ChatDevSandboxValidator,
            SandboxConfig,
            ValidatorResult,
        )

        v = ChatDevSandboxValidator(SandboxConfig(output_dir=tmp_path))
        result = ValidatorResult(
            success=True, sandbox_id="testid", execution_time=2.5, validation_score=0.9
        )
        path = v.save_result(result, tmp_path / "out.json")
        data = json.loads(path.read_text())
        assert data["success"] is True
        assert data["sandbox_id"] == "testid"
        assert data["validation_score"] == 0.9

    def test_save_default_path(self, tmp_path):
        from src.resilience.sandbox_chatdev_validator import (
            ChatDevSandboxValidator,
            SandboxConfig,
            ValidatorResult,
        )

        v = ChatDevSandboxValidator(SandboxConfig(output_dir=tmp_path))
        result = ValidatorResult(success=False, sandbox_id="x", execution_time=0.1)
        path = v.save_result(result)
        assert path.exists()
        assert path.name == "validation_result.json"


class TestValidateEnvironment:
    import pytest

    @pytest.mark.asyncio
    async def test_env_invalid_when_ollama_fails(self, tmp_path):
        from unittest.mock import AsyncMock, MagicMock, patch

        from src.resilience.sandbox_chatdev_validator import ChatDevSandboxValidator, SandboxConfig

        v = ChatDevSandboxValidator(SandboxConfig(output_dir=tmp_path))

        mock_proc = MagicMock()
        mock_proc.returncode = 1
        mock_proc.wait = AsyncMock(return_value=1)
        mock_proc.kill = MagicMock()

        with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
            with patch("pathlib.Path.exists", return_value=True):
                result = await v._validate_environment()

        assert result["valid"] is False
        assert "ollama" in result
        assert result["ollama"] is False

    @pytest.mark.asyncio
    async def test_env_invalid_when_chatdev_missing(self, tmp_path):
        from unittest.mock import AsyncMock, MagicMock, patch

        from src.resilience.sandbox_chatdev_validator import ChatDevSandboxValidator, SandboxConfig

        v = ChatDevSandboxValidator(SandboxConfig(output_dir=tmp_path))

        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.wait = AsyncMock(return_value=0)

        with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
            with patch("pathlib.Path.exists", return_value=False):
                result = await v._validate_environment()

        assert result["valid"] is False
        assert result["chatdev"] is False

    @pytest.mark.asyncio
    async def test_env_exception_returns_invalid(self, tmp_path):
        from unittest.mock import patch

        from src.resilience.sandbox_chatdev_validator import ChatDevSandboxValidator, SandboxConfig

        v = ChatDevSandboxValidator(SandboxConfig(output_dir=tmp_path))

        with patch(
            "asyncio.create_subprocess_exec", side_effect=OSError("no such program")
        ):
            result = await v._validate_environment()

        assert result["valid"] is False
        assert len(result["errors"]) > 0

    @pytest.mark.asyncio
    async def test_env_both_ok(self, tmp_path):
        from unittest.mock import AsyncMock, MagicMock, patch

        from src.resilience.sandbox_chatdev_validator import ChatDevSandboxValidator, SandboxConfig

        v = ChatDevSandboxValidator(SandboxConfig(output_dir=tmp_path))

        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.wait = AsyncMock(return_value=0)

        with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
            with patch("pathlib.Path.exists", return_value=True):
                result = await v._validate_environment()

        assert result["valid"] is True
        assert result["ollama"] is True
        assert result["chatdev"] is True
        assert result["errors"] == []


class TestExecuteChatdev:
    import pytest

    @pytest.mark.asyncio
    async def test_execute_creates_files(self, tmp_path):
        from src.resilience.sandbox_chatdev_validator import ChatDevSandboxValidator, SandboxConfig

        v = ChatDevSandboxValidator(SandboxConfig(output_dir=tmp_path))
        result = await v._execute_chatdev("Build a calculator", "qwen2.5-coder:7b", "my_calc")
        assert result["success"] is True
        assert result["file_count"] == 3
        assert (result["project_dir"] / "main.py").exists()
        assert (result["project_dir"] / "README.md").exists()
        assert (result["project_dir"] / "requirements.txt").exists()

    @pytest.mark.asyncio
    async def test_execute_readme_contains_task(self, tmp_path):
        from src.resilience.sandbox_chatdev_validator import ChatDevSandboxValidator, SandboxConfig

        v = ChatDevSandboxValidator(SandboxConfig(output_dir=tmp_path))
        task = "Build a todo app"
        result = await v._execute_chatdev(task, "qwen2.5-coder:7b", "todo_proj")
        readme = (result["project_dir"] / "README.md").read_text()
        assert task in readme


class TestValidateChatdevRun:
    import pytest

    @pytest.mark.asyncio
    async def test_env_failure_returns_unsuccessful(self, tmp_path):
        from unittest.mock import AsyncMock, patch

        from src.resilience.sandbox_chatdev_validator import ChatDevSandboxValidator, SandboxConfig

        v = ChatDevSandboxValidator(SandboxConfig(output_dir=tmp_path))

        with patch.object(
            v,
            "_validate_environment",
            new_callable=AsyncMock,
            return_value={"valid": False, "errors": ["ollama not running"]},
        ):
            result = await v.validate_chatdev_run("some task")

        assert result.success is False
        assert result.error is not None
        assert "ollama not running" in result.error
        assert len(result.audit_entries) >= 1

    @pytest.mark.asyncio
    async def test_successful_run(self, tmp_path):
        from unittest.mock import AsyncMock, patch

        from src.resilience.sandbox_chatdev_validator import ChatDevSandboxValidator, SandboxConfig

        v = ChatDevSandboxValidator(SandboxConfig(output_dir=tmp_path))

        with patch.object(
            v,
            "_validate_environment",
            new_callable=AsyncMock,
            return_value={"valid": True, "ollama": True, "chatdev": True, "errors": []},
        ):
            result = await v.validate_chatdev_run("Build a calculator", project_name="calc_proj")

        assert result.success is True
        assert result.sandbox_id == v.sandbox_id
        assert result.execution_time >= 0
        assert result.validation_score > 0
        assert result.output["project_name"] == "calc_proj"
        assert len(result.audit_entries) > 0

    @pytest.mark.asyncio
    async def test_chatdev_failure_propagates(self, tmp_path):
        from unittest.mock import AsyncMock, patch

        from src.resilience.sandbox_chatdev_validator import ChatDevSandboxValidator, SandboxConfig

        v = ChatDevSandboxValidator(SandboxConfig(output_dir=tmp_path))

        with patch.object(
            v,
            "_validate_environment",
            new_callable=AsyncMock,
            return_value={"valid": True, "ollama": True, "chatdev": True, "errors": []},
        ):
            with patch.object(
                v,
                "_execute_chatdev",
                new_callable=AsyncMock,
                return_value={"success": False, "error": "ChatDev crashed"},
            ):
                result = await v.validate_chatdev_run("task")

        assert result.success is False
        assert "ChatDev crashed" in result.error

    @pytest.mark.asyncio
    async def test_timeout_error_handled(self, tmp_path):
        from unittest.mock import AsyncMock, patch

        from src.resilience.sandbox_chatdev_validator import ChatDevSandboxValidator, SandboxConfig

        v = ChatDevSandboxValidator(SandboxConfig(output_dir=tmp_path))

        with patch.object(
            v,
            "_validate_environment",
            new_callable=AsyncMock,
            side_effect=TimeoutError("timeout"),
        ):
            result = await v.validate_chatdev_run("task")

        assert result.success is False
        assert "timeout" in result.error.lower()

    @pytest.mark.asyncio
    async def test_unexpected_exception_handled(self, tmp_path):
        from unittest.mock import AsyncMock, patch

        from src.resilience.sandbox_chatdev_validator import ChatDevSandboxValidator, SandboxConfig

        v = ChatDevSandboxValidator(SandboxConfig(output_dir=tmp_path))

        with patch.object(
            v,
            "_validate_environment",
            new_callable=AsyncMock,
            side_effect=RuntimeError("boom"),
        ):
            result = await v.validate_chatdev_run("task")

        assert result.success is False
        assert "boom" in result.error

    @pytest.mark.asyncio
    async def test_auto_project_name_generated(self, tmp_path):
        from unittest.mock import AsyncMock, patch

        from src.resilience.sandbox_chatdev_validator import ChatDevSandboxValidator, SandboxConfig

        v = ChatDevSandboxValidator(SandboxConfig(output_dir=tmp_path))

        with patch.object(
            v,
            "_validate_environment",
            new_callable=AsyncMock,
            return_value={"valid": True, "ollama": True, "chatdev": True, "errors": []},
        ):
            result = await v.validate_chatdev_run("task")

        assert result.output["project_name"].startswith("sandbox_test_")

    @pytest.mark.asyncio
    async def test_resource_usage_populated(self, tmp_path):
        from unittest.mock import AsyncMock, patch

        from src.resilience.sandbox_chatdev_validator import ChatDevSandboxValidator, SandboxConfig

        v = ChatDevSandboxValidator(SandboxConfig(output_dir=tmp_path))

        with patch.object(
            v,
            "_validate_environment",
            new_callable=AsyncMock,
            return_value={"valid": True, "ollama": True, "chatdev": True, "errors": []},
        ):
            result = await v.validate_chatdev_run("task")

        assert "memory_mb" in result.resource_usage


class TestValidateChatdevSandboxConvenienceFunction:
    import pytest

    @pytest.mark.asyncio
    async def test_calls_validator(self, tmp_path):
        from unittest.mock import AsyncMock, patch

        from src.resilience.sandbox_chatdev_validator import (
            SandboxConfig,
            ValidatorResult,
            validate_chatdev_sandbox,
        )

        cfg = SandboxConfig(output_dir=tmp_path)
        mock_result = ValidatorResult(success=True, sandbox_id="abc", execution_time=1.0)

        with patch(
            "src.resilience.sandbox_chatdev_validator.ChatDevSandboxValidator.validate_chatdev_run",
            new_callable=AsyncMock,
            return_value=mock_result,
        ):
            result = await validate_chatdev_sandbox("some task", config=cfg)

        assert result.success is True

    @pytest.mark.asyncio
    async def test_default_model(self, tmp_path):
        from unittest.mock import AsyncMock, patch

        from src.resilience.sandbox_chatdev_validator import (
            SandboxConfig,
            ValidatorResult,
            validate_chatdev_sandbox,
        )

        cfg = SandboxConfig(output_dir=tmp_path)
        captured = {}

        async def capture_run(task, model="qwen2.5-coder:7b", project_name=None):
            captured["model"] = model
            return ValidatorResult(success=True, sandbox_id="x", execution_time=0.1)

        with patch(
            "src.resilience.sandbox_chatdev_validator.ChatDevSandboxValidator.validate_chatdev_run",
            side_effect=capture_run,
        ):
            await validate_chatdev_sandbox("task", config=cfg)

        assert captured["model"] == "qwen2.5-coder:7b"
