"""Tests for src.healing.repository_health_restorer module."""

import json
import os
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


class TestModuleImports:
    """Test module can be imported."""

    def test_import_module(self):
        from src.healing import repository_health_restorer

        assert repository_health_restorer is not None

    def test_import_class(self):
        from src.healing.repository_health_restorer import RepositoryHealthRestorer

        assert RepositoryHealthRestorer is not None

    def test_import_main(self):
        from src.healing.repository_health_restorer import main

        assert callable(main)

    def test_import_validate_path(self):
        from src.healing.repository_health_restorer import validate_path

        assert callable(validate_path)

    def test_import_find_broken_paths(self):
        from src.healing.repository_health_restorer import find_broken_paths

        assert callable(find_broken_paths)


class TestValidatePath:
    """Test validate_path utility function."""

    def test_validate_path_existing_file(self, tmp_path):
        from src.healing.repository_health_restorer import validate_path

        test_file = tmp_path / "test.txt"
        test_file.write_text("content")
        assert validate_path(test_file) is True

    def test_validate_path_existing_directory(self, tmp_path):
        from src.healing.repository_health_restorer import validate_path

        assert validate_path(tmp_path) is True

    def test_validate_path_nonexistent(self, tmp_path):
        from src.healing.repository_health_restorer import validate_path

        assert validate_path(tmp_path / "nonexistent") is False

    def test_validate_path_none(self):
        from src.healing.repository_health_restorer import validate_path

        assert validate_path(None) is False

    def test_validate_path_empty_string(self):
        from src.healing.repository_health_restorer import validate_path

        assert validate_path("") is False

    def test_validate_path_string_argument(self, tmp_path):
        from src.healing.repository_health_restorer import validate_path

        test_file = tmp_path / "test.txt"
        test_file.write_text("content")
        assert validate_path(str(test_file)) is True


class TestFindBrokenPaths:
    """Test find_broken_paths utility function."""

    def test_find_broken_paths_empty_directory(self, tmp_path):
        from src.healing.repository_health_restorer import find_broken_paths

        result = find_broken_paths(tmp_path)
        assert isinstance(result, list)

    def test_find_broken_paths_valid_python_file(self, tmp_path):
        from src.healing.repository_health_restorer import find_broken_paths

        py_file = tmp_path / "valid.py"
        py_file.write_text("import os\nimport sys\n")
        result = find_broken_paths(tmp_path)
        assert isinstance(result, list)

    def test_find_broken_paths_string_argument(self, tmp_path):
        from src.healing.repository_health_restorer import find_broken_paths

        result = find_broken_paths(str(tmp_path))
        assert isinstance(result, list)


class TestRepositoryHealthRestorerInit:
    """Test RepositoryHealthRestorer initialization."""

    def test_init_default(self):
        from src.healing.repository_health_restorer import RepositoryHealthRestorer

        with patch.dict(os.environ, {}, clear=False):
            restorer = RepositoryHealthRestorer()
            assert hasattr(restorer, "base_path")
            assert hasattr(restorer, "report_path")
            assert hasattr(restorer, "requirements_path")

    def test_init_with_env_var(self, tmp_path):
        from src.healing.repository_health_restorer import RepositoryHealthRestorer

        with patch.dict(os.environ, {"NU_SYQ_HUB_ROOT": str(tmp_path)}):
            restorer = RepositoryHealthRestorer()
            assert restorer.base_path == tmp_path

    def test_paths_are_pathlib_objects(self):
        from src.healing.repository_health_restorer import RepositoryHealthRestorer

        restorer = RepositoryHealthRestorer()
        assert isinstance(restorer.base_path, Path)
        assert isinstance(restorer.report_path, Path)
        assert isinstance(restorer.requirements_path, Path)


class TestLoadBrokenPathsReport:
    """Test load_broken_paths_report method."""

    def test_load_valid_report(self, tmp_path):
        from src.healing.repository_health_restorer import RepositoryHealthRestorer

        report_data = {"import_issues": [], "status": "ok"}
        report_path = tmp_path / "broken_paths_report.json"
        report_path.write_text(json.dumps(report_data))

        with patch.dict(os.environ, {"NU_SYQ_HUB_ROOT": str(tmp_path)}):
            restorer = RepositoryHealthRestorer()
            result = restorer.load_broken_paths_report()
            assert result == report_data

    def test_load_missing_report_raises(self, tmp_path):
        from src.healing.repository_health_restorer import RepositoryHealthRestorer

        with patch.dict(os.environ, {"NU_SYQ_HUB_ROOT": str(tmp_path)}):
            restorer = RepositoryHealthRestorer()
            with pytest.raises(FileNotFoundError):
                restorer.load_broken_paths_report()

    def test_load_invalid_json_raises(self, tmp_path):
        from src.healing.repository_health_restorer import RepositoryHealthRestorer

        report_path = tmp_path / "broken_paths_report.json"
        report_path.write_text("not valid json {{{")

        with patch.dict(os.environ, {"NU_SYQ_HUB_ROOT": str(tmp_path)}):
            restorer = RepositoryHealthRestorer()
            with pytest.raises(json.JSONDecodeError):
                restorer.load_broken_paths_report()


class TestInstallMissingDependencies:
    """Test install_missing_dependencies method."""

    def test_install_success(self, tmp_path):
        from src.healing.repository_health_restorer import RepositoryHealthRestorer

        requirements_path = tmp_path / "requirements.txt"
        requirements_path.write_text("pytest\n")

        with patch.dict(os.environ, {"NU_SYQ_HUB_ROOT": str(tmp_path)}):
            restorer = RepositoryHealthRestorer()
            mock_run = MagicMock()
            with patch("subprocess.run", mock_run):
                result = restorer.install_missing_dependencies()
                assert result is True
                mock_run.assert_called_once()

    def test_install_failure(self, tmp_path):
        from src.healing.repository_health_restorer import RepositoryHealthRestorer

        requirements_path = tmp_path / "requirements.txt"
        requirements_path.write_text("nonexistent-package-xyz\n")

        with patch.dict(os.environ, {"NU_SYQ_HUB_ROOT": str(tmp_path)}):
            restorer = RepositoryHealthRestorer()
            with patch("subprocess.run", side_effect=subprocess.CalledProcessError(1, "pip")):
                result = restorer.install_missing_dependencies()
                assert result is False


class TestCreateMissingModules:
    """Test create_missing_modules method."""

    def test_creates_logging_directory(self, tmp_path):
        from src.healing.repository_health_restorer import RepositoryHealthRestorer

        with patch.dict(os.environ, {"NU_SYQ_HUB_ROOT": str(tmp_path)}):
            restorer = RepositoryHealthRestorer()
            result = restorer.create_missing_modules()
            assert result is True
            assert (tmp_path / "LOGGING").is_dir()

    def test_creates_modular_logging_file(self, tmp_path):
        from src.healing.repository_health_restorer import RepositoryHealthRestorer

        with patch.dict(os.environ, {"NU_SYQ_HUB_ROOT": str(tmp_path)}):
            restorer = RepositoryHealthRestorer()
            restorer.create_missing_modules()
            assert (tmp_path / "LOGGING" / "modular_logging_system.py").exists()

    def test_creates_logging_init(self, tmp_path):
        from src.healing.repository_health_restorer import RepositoryHealthRestorer

        with patch.dict(os.environ, {"NU_SYQ_HUB_ROOT": str(tmp_path)}):
            restorer = RepositoryHealthRestorer()
            restorer.create_missing_modules()
            assert (tmp_path / "LOGGING" / "__init__.py").exists()

    def test_creates_kilo_core_directory(self, tmp_path):
        from src.healing.repository_health_restorer import RepositoryHealthRestorer

        with patch.dict(os.environ, {"NU_SYQ_HUB_ROOT": str(tmp_path)}):
            restorer = RepositoryHealthRestorer()
            restorer.create_missing_modules()
            assert (tmp_path / "KILO_Core").is_dir()

    def test_creates_secrets_file(self, tmp_path):
        from src.healing.repository_health_restorer import RepositoryHealthRestorer

        with patch.dict(os.environ, {"NU_SYQ_HUB_ROOT": str(tmp_path)}):
            restorer = RepositoryHealthRestorer()
            restorer.create_missing_modules()
            assert (tmp_path / "KILO_Core" / "secrets.py").exists()


class TestFixImportPaths:
    """Test fix_import_paths method."""

    def test_fix_empty_report(self, tmp_path):
        from src.healing.repository_health_restorer import RepositoryHealthRestorer

        with patch.dict(os.environ, {"NU_SYQ_HUB_ROOT": str(tmp_path)}):
            restorer = RepositoryHealthRestorer()
            report = {"import_issues": []}
            result = restorer.fix_import_paths(report)
            assert result is True

    def test_fix_report_with_standard_lib_imports(self, tmp_path):
        from src.healing.repository_health_restorer import RepositoryHealthRestorer

        with patch.dict(os.environ, {"NU_SYQ_HUB_ROOT": str(tmp_path)}):
            restorer = RepositoryHealthRestorer()
            report = {
                "import_issues": [
                    {"type": "broken_absolute_import", "file": "some_file.py", "import": "csv"},
                    {"type": "broken_absolute_import", "file": "other.py", "import": "builtins"},
                    {"type": "broken_absolute_import", "file": "test.py", "import": "hashlib"},
                ]
            }
            result = restorer.fix_import_paths(report)
            assert result is True

    def test_fix_skips_nonexistent_files(self, tmp_path):
        from src.healing.repository_health_restorer import RepositoryHealthRestorer

        with patch.dict(os.environ, {"NU_SYQ_HUB_ROOT": str(tmp_path)}):
            restorer = RepositoryHealthRestorer()
            report = {
                "import_issues": [
                    {
                        "type": "broken_absolute_import",
                        "file": "/nonexistent/file.py",
                        "import": "custom_mod",
                    }
                ]
            }
            result = restorer.fix_import_paths(report)
            assert result is True


class TestCreateMissingIntegrationModules:
    """Test create_missing_integration_modules method."""

    def test_creates_ai_directory(self, tmp_path):
        from src.healing.repository_health_restorer import RepositoryHealthRestorer

        with patch.dict(os.environ, {"NU_SYQ_HUB_ROOT": str(tmp_path)}):
            restorer = RepositoryHealthRestorer()
            result = restorer.create_missing_integration_modules()
            assert result is True
            expected_path = (
                tmp_path / "Transcendent_Spine" / "kilo-foolish-transcendent-spine" / "src" / "ai"
            )
            assert expected_path.is_dir()

    def test_creates_ollama_integration_file(self, tmp_path):
        from src.healing.repository_health_restorer import RepositoryHealthRestorer

        with patch.dict(os.environ, {"NU_SYQ_HUB_ROOT": str(tmp_path)}):
            restorer = RepositoryHealthRestorer()
            restorer.create_missing_integration_modules()
            expected_path = (
                tmp_path
                / "Transcendent_Spine"
                / "kilo-foolish-transcendent-spine"
                / "src"
                / "ai"
                / "ollama_integration.py"
            )
            assert expected_path.exists()

    def test_creates_conversation_manager(self, tmp_path):
        from src.healing.repository_health_restorer import RepositoryHealthRestorer

        with patch.dict(os.environ, {"NU_SYQ_HUB_ROOT": str(tmp_path)}):
            restorer = RepositoryHealthRestorer()
            restorer.create_missing_integration_modules()
            expected_path = (
                tmp_path
                / "Transcendent_Spine"
                / "kilo-foolish-transcendent-spine"
                / "src"
                / "ai"
                / "conversation_manager.py"
            )
            assert expected_path.exists()

    def test_creates_ollama_hub(self, tmp_path):
        from src.healing.repository_health_restorer import RepositoryHealthRestorer

        with patch.dict(os.environ, {"NU_SYQ_HUB_ROOT": str(tmp_path)}):
            restorer = RepositoryHealthRestorer()
            restorer.create_missing_integration_modules()
            expected_path = (
                tmp_path
                / "Transcendent_Spine"
                / "kilo-foolish-transcendent-spine"
                / "src"
                / "ai"
                / "ollama_hub.py"
            )
            assert expected_path.exists()


class TestRunHealthRestoration:
    """Test run_health_restoration method."""

    def test_restoration_success(self, tmp_path):
        from src.healing.repository_health_restorer import RepositoryHealthRestorer

        # Setup report file
        report_data = {"import_issues": []}
        report_path = tmp_path / "broken_paths_report.json"
        report_path.write_text(json.dumps(report_data))

        # Setup requirements file
        requirements_path = tmp_path / "requirements.txt"
        requirements_path.write_text("pytest\n")

        with patch.dict(os.environ, {"NU_SYQ_HUB_ROOT": str(tmp_path)}):
            restorer = RepositoryHealthRestorer()
            with patch("subprocess.run"):
                result = restorer.run_health_restoration()
                assert result is True

    def test_restoration_missing_report(self, tmp_path):
        from src.healing.repository_health_restorer import RepositoryHealthRestorer

        with patch.dict(os.environ, {"NU_SYQ_HUB_ROOT": str(tmp_path)}):
            restorer = RepositoryHealthRestorer()
            result = restorer.run_health_restoration()
            assert result is False

    def test_restoration_invalid_json_report(self, tmp_path):
        from src.healing.repository_health_restorer import RepositoryHealthRestorer

        report_path = tmp_path / "broken_paths_report.json"
        report_path.write_text("not json")

        with patch.dict(os.environ, {"NU_SYQ_HUB_ROOT": str(tmp_path)}):
            restorer = RepositoryHealthRestorer()
            result = restorer.run_health_restoration()
            assert result is False


class TestMain:
    """Test main function."""

    def test_main_returns_bool(self, tmp_path):
        from src.healing.repository_health_restorer import main

        # Setup report file
        report_data = {"import_issues": []}
        report_path = tmp_path / "broken_paths_report.json"
        report_path.write_text(json.dumps(report_data))

        requirements_path = tmp_path / "requirements.txt"
        requirements_path.write_text("pytest\n")

        with patch.dict(os.environ, {"NU_SYQ_HUB_ROOT": str(tmp_path)}):
            with patch("subprocess.run"):
                result = main()
                assert isinstance(result, bool)

    def test_main_success_returns_true(self, tmp_path):
        from src.healing.repository_health_restorer import main

        report_data = {"import_issues": []}
        report_path = tmp_path / "broken_paths_report.json"
        report_path.write_text(json.dumps(report_data))

        requirements_path = tmp_path / "requirements.txt"
        requirements_path.write_text("pytest\n")

        with patch.dict(os.environ, {"NU_SYQ_HUB_ROOT": str(tmp_path)}):
            with patch("subprocess.run"):
                result = main()
                assert result is True
