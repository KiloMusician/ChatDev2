"""Tests for src/utils/constants.py — enums, constants, and utility methods."""


class TestAIModel:
    """Tests for AIModel enum."""

    def test_has_openai_models(self):
        from src.utils.constants import AIModel
        assert AIModel.GPT_4 is not None
        assert AIModel.GPT_4O is not None
        assert AIModel.GPT_3_5_TURBO is not None

    def test_has_ollama_models(self):
        from src.utils.constants import AIModel
        assert AIModel.LLAMA2 is not None
        assert AIModel.CODELLAMA is not None
        assert AIModel.MISTRAL is not None

    def test_has_claude_models(self):
        from src.utils.constants import AIModel
        assert AIModel.CLAUDE_3_HAIKU is not None
        assert AIModel.CLAUDE_3_SONNET is not None
        assert AIModel.CLAUDE_3_OPUS is not None

    def test_values_are_strings(self):
        from src.utils.constants import AIModel
        for model in AIModel:
            assert isinstance(model.value, str)

    def test_get_openai_models_returns_list(self):
        from src.utils.constants import AIModel
        result = AIModel.get_openai_models()
        assert isinstance(result, list)
        assert len(result) >= 3

    def test_get_ollama_models_returns_list(self):
        from src.utils.constants import AIModel
        result = AIModel.get_ollama_models()
        assert isinstance(result, list)
        assert len(result) >= 3

    def test_get_claude_models_returns_list(self):
        from src.utils.constants import AIModel
        result = AIModel.get_claude_models()
        assert isinstance(result, list)
        assert len(result) >= 3

    def test_get_openai_models_strings(self):
        from src.utils.constants import AIModel
        for m in AIModel.get_openai_models():
            assert isinstance(m, str)

    def test_openai_not_in_ollama_list(self):
        from src.utils.constants import AIModel
        ollama = set(AIModel.get_ollama_models())
        for gpt in AIModel.get_openai_models():
            assert gpt not in ollama


class TestTaskStatus:
    """Tests for TaskStatus enum."""

    def test_has_seven_values(self):
        from src.utils.constants import TaskStatus
        assert len(list(TaskStatus)) == 7

    def test_terminal_statuses(self):
        from src.utils.constants import TaskStatus
        assert TaskStatus.COMPLETED.is_terminal() is True
        assert TaskStatus.FAILED.is_terminal() is True
        assert TaskStatus.CANCELLED.is_terminal() is True
        assert TaskStatus.TIMEOUT.is_terminal() is True

    def test_non_terminal_statuses(self):
        from src.utils.constants import TaskStatus
        assert TaskStatus.PENDING.is_terminal() is False
        assert TaskStatus.IN_PROGRESS.is_terminal() is False
        assert TaskStatus.RETRYING.is_terminal() is False

    def test_active_statuses(self):
        from src.utils.constants import TaskStatus
        assert TaskStatus.PENDING.is_active() is True
        assert TaskStatus.IN_PROGRESS.is_active() is True
        assert TaskStatus.RETRYING.is_active() is True

    def test_completed_not_active(self):
        from src.utils.constants import TaskStatus
        assert TaskStatus.COMPLETED.is_active() is False

    def test_values_are_strings(self):
        from src.utils.constants import TaskStatus
        for status in TaskStatus:
            assert isinstance(status.value, str)


class TestLogLevel:
    """Tests for LogLevel IntEnum."""

    def test_debug_is_10(self):
        from src.utils.constants import LogLevel
        assert LogLevel.DEBUG == 10

    def test_info_is_20(self):
        from src.utils.constants import LogLevel
        assert LogLevel.INFO == 20

    def test_warning_is_30(self):
        from src.utils.constants import LogLevel
        assert LogLevel.WARNING == 30

    def test_error_is_40(self):
        from src.utils.constants import LogLevel
        assert LogLevel.ERROR == 40

    def test_critical_is_50(self):
        from src.utils.constants import LogLevel
        assert LogLevel.CRITICAL == 50

    def test_ordering(self):
        from src.utils.constants import LogLevel
        assert LogLevel.DEBUG < LogLevel.INFO < LogLevel.WARNING < LogLevel.ERROR < LogLevel.CRITICAL


class TestRepositoryType:
    """Tests for RepositoryType enum."""

    def test_has_five_types(self):
        from src.utils.constants import RepositoryType
        assert len(list(RepositoryType)) == 5

    def test_nusyq_hub_present(self):
        from src.utils.constants import RepositoryType
        assert RepositoryType.NUSYQ_HUB.value == "nusyq_hub"

    def test_values_are_strings(self):
        from src.utils.constants import RepositoryType
        for rt in RepositoryType:
            assert isinstance(rt.value, str)


class TestFileExtension:
    """Tests for FileExtension enum."""

    def test_python_extension(self):
        from src.utils.constants import FileExtension
        assert FileExtension.PYTHON.value == ".py"

    def test_json_extension(self):
        from src.utils.constants import FileExtension
        assert FileExtension.JSON.value == ".json"

    def test_markdown_extension(self):
        from src.utils.constants import FileExtension
        assert FileExtension.MARKDOWN.value == ".md"

    def test_all_start_with_dot(self):
        from src.utils.constants import FileExtension
        for ext in FileExtension:
            assert ext.value.startswith(".")


class TestSystemPriority:
    """Tests for SystemPriority IntEnum."""

    def test_critical_highest(self):
        from src.utils.constants import SystemPriority
        assert SystemPriority.CRITICAL == 100

    def test_background_lowest(self):
        from src.utils.constants import SystemPriority
        assert SystemPriority.BACKGROUND == 10

    def test_ordering(self):
        from src.utils.constants import SystemPriority
        assert SystemPriority.BACKGROUND < SystemPriority.LOW < SystemPriority.MEDIUM < SystemPriority.HIGH < SystemPriority.CRITICAL


class TestShutdownPhase:
    """Tests for ShutdownPhase enum."""

    def test_has_five_phases(self):
        from src.utils.constants import ShutdownPhase
        assert len(list(ShutdownPhase)) == 5

    def test_running_value(self):
        from src.utils.constants import ShutdownPhase
        assert ShutdownPhase.RUNNING.value == "running"

    def test_stopped_value(self):
        from src.utils.constants import ShutdownPhase
        assert ShutdownPhase.STOPPED.value == "stopped"


class TestModuleType:
    """Tests for ModuleType enum."""

    def test_has_many_types(self):
        from src.utils.constants import ModuleType
        assert len(list(ModuleType)) >= 10

    def test_core_value(self):
        from src.utils.constants import ModuleType
        assert ModuleType.CORE.value == "core"

    def test_all_values_are_strings(self):
        from src.utils.constants import ModuleType
        for mt in ModuleType:
            assert isinstance(mt.value, str)


class TestConfigKey:
    """Tests for ConfigKey enum."""

    def test_openai_key_present(self):
        from src.utils.constants import ConfigKey
        assert ConfigKey.OPENAI_API_KEY.value == "OPENAI_API_KEY"

    def test_ollama_keys_present(self):
        from src.utils.constants import ConfigKey
        assert ConfigKey.OLLAMA_HOST is not None
        assert ConfigKey.OLLAMA_PORT is not None

    def test_all_values_are_strings(self):
        from src.utils.constants import ConfigKey
        for ck in ConfigKey:
            assert isinstance(ck.value, str)


class TestErrorCode:
    """Tests for ErrorCode IntEnum."""

    def test_success_is_zero(self):
        from src.utils.constants import ErrorCode
        assert ErrorCode.SUCCESS == 0

    def test_general_error_is_one(self):
        from src.utils.constants import ErrorCode
        assert ErrorCode.GENERAL_ERROR == 1

    def test_has_many_codes(self):
        from src.utils.constants import ErrorCode
        assert len(list(ErrorCode)) >= 10

    def test_success_less_than_errors(self):
        from src.utils.constants import ErrorCode
        assert ErrorCode.SUCCESS < ErrorCode.GENERAL_ERROR < ErrorCode.INVALID_INPUT


class TestAPIEndpoint:
    """Tests for APIEndpoint enum."""

    def test_openai_base_is_string(self):
        from src.utils.constants import APIEndpoint
        assert isinstance(APIEndpoint.OPENAI_BASE.value, str)
        assert "openai.com" in APIEndpoint.OPENAI_BASE.value

    def test_anthropic_base_present(self):
        from src.utils.constants import APIEndpoint
        assert "anthropic.com" in APIEndpoint.ANTHROPIC_BASE.value

    def test_get_ollama_generate_contains_generate(self):
        from src.utils.constants import APIEndpoint
        url = APIEndpoint.get_ollama_generate()
        assert "generate" in url

    def test_get_ollama_chat_contains_chat(self):
        from src.utils.constants import APIEndpoint
        url = APIEndpoint.get_ollama_chat()
        assert "chat" in url

    def test_get_ollama_models_contains_tags(self):
        from src.utils.constants import APIEndpoint
        url = APIEndpoint.get_ollama_models()
        assert "tags" in url


class TestOllamaDefault:
    """Tests for OLLAMA_DEFAULT module constant."""

    def test_ollama_default_is_string(self):
        from src.utils.constants import OLLAMA_DEFAULT
        assert isinstance(OLLAMA_DEFAULT, str)

    def test_ollama_default_not_empty(self):
        from src.utils.constants import OLLAMA_DEFAULT
        assert len(OLLAMA_DEFAULT) > 0
