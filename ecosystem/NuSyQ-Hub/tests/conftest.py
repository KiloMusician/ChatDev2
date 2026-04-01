"""
SAFE CAPTURE CONFTEST
Ensures pytest capture works without FileNotFoundError
Includes Phase 3 mock infrastructure fixtures
"""

import sys
from pathlib import Path

# Ensure workspace root is on sys.path so 'scripts' package is importable
_workspace_root = Path(__file__).parent.parent
if str(_workspace_root) not in sys.path:
    sys.path.insert(0, str(_workspace_root))

# Preload modules before test files can stub them via sys.modules.setdefault.
# conftest.py is processed first, so importing real modules here ensures setdefault
# in test files finds them already registered and leaves them unchanged.
#
# - test_cyber_terminal.py stubs src.Rosetta_Quest_System.quest_manager
# - test_architecture_watcher.py stubs watchdog.events and watchdog.observers
try:
    import src.Rosetta_Quest_System.quest_manager as _qm_preload
except Exception:
    pass
try:
    import watchdog.events as _wd_events_preload
    import watchdog.observers as _wd_obs_preload
except Exception:
    pass

import json
import os
import platform
import tempfile
from collections.abc import Generator
from typing import TYPE_CHECKING, Any

import pytest


@pytest.fixture(autouse=True)
def _ensure_scripts_path():
    """Ensure scripts package is importable from workspace root (autouse)."""
    import sys

    workspace_str = str(_workspace_root)
    # Ensure path is at front
    if sys.path[0] != workspace_str:
        if workspace_str in sys.path:
            sys.path.remove(workspace_str)
        sys.path.insert(0, workspace_str)
    # Clear any stale module cache entries
    for mod_name in list(sys.modules.keys()):
        if mod_name == "scripts" or mod_name.startswith("scripts."):
            del sys.modules[mod_name]
    yield


if TYPE_CHECKING:
    from src.consciousness.floor_5_integration import Floor5Integration, IntegrationPattern

# Suppress pytest_benchmark plugin to prevent logger conflicts
# This prevents "logger.py:39: PytestBenchmarkWarning" and exit code 5 issues
pytest_plugins = []

# Phase 3: Import mock Ollama fixtures
from tests.fixtures.mock_ollama import (
    mock_ollama_client,
    mock_ollama_server_process,
    mock_ollama_url,
    monkeypatch_session,
    use_mock_ollama_globally,
)
from tests.fixtures.mock_ollama import (
    pytest_addoption as mock_pytest_addoption,
)
from tests.fixtures.mock_ollama import (
    pytest_collection_modifyitems as mock_pytest_collection_modifyitems,
)
from tests.fixtures.mock_ollama import (
    pytest_configure as mock_pytest_configure,
)

# Re-export for test discovery
__all__ = [
    "mock_ollama_client",
    "mock_ollama_server_process",
    "mock_ollama_url",
    "monkeypatch_session",
    "use_mock_ollama_globally",
]


@pytest.hookimpl(tryfirst=True)
def pytest_addoption(parser):
    """Add CLI options including Phase 3 --offline flag."""
    # Call mock infrastructure option adder
    mock_pytest_addoption(parser)


@pytest.hookimpl(tryfirst=True)
def pytest_configure(config):
    """Configure pytest with safe defaults + Phase 3 offline mode."""
    # Original safe capture configuration

    # Ensure we have a stable temp directory for capture
    if not hasattr(config, "workerinput"):
        # Not in pytest-xdist worker
        # Use per-process capture roots to avoid cross-process temp-file collisions.
        temp_dir = Path(tempfile.gettempdir()) / f"pytest_capture_{os.getpid()}"
        temp_dir.mkdir(exist_ok=True, parents=True)

        # Set environment variable for pytest's internal use
        os.environ["PYTEST_DEBUG_TEMPROOT"] = str(temp_dir)

    # Disable problematic plugins if needed
    if config.pluginmanager.has_plugin("pytest-instafail"):
        config.option.tbstyle = "short"  # Use shorter tracebacks

    # Use robust timeout signaling on non-Windows runtimes to avoid silent hangs.
    if platform.system() != "Windows":
        try:
            config.option.timeout_method = "signal"
        except Exception:
            pass

    print("🔧 pytest configured with safe capture")

    # Phase 3: Configure mock infrastructure
    mock_pytest_configure(config)


@pytest.hookimpl(tryfirst=True)
def pytest_collection_modifyitems(config, items):
    """Modify test collection for offline mode (Phase 3)."""
    mock_pytest_collection_modifyitems(config, items)


@pytest.hookimpl(tryfirst=True)
def pytest_sessionstart(session):
    """Initialize session with safe capture"""
    # Ensure temp directories exist
    for attr in ["_tmpdir", "_tmp_path_factory"]:
        if hasattr(session.config, attr):
            try:
                temp_obj = getattr(session.config, attr)
                if hasattr(temp_obj, "ensure_temp"):
                    temp_obj.ensure_temp()
            except (AttributeError, OSError):
                pass


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_protocol(item, nextitem):
    """Wrap test protocol to ensure capture cleanup happens in right order"""
    try:
        yield
    finally:
        # Ensure any temp files are properly cleaned
        if hasattr(item, "_capture"):
            try:
                item._capture.close()
            except Exception:
                pass


# Safe teardown fixture
@pytest.fixture(scope="function", autouse=True)
def safe_capture_teardown(request):
    """Ensure capture is properly torn down after each test"""
    yield
    # Clean up any lingering capture artifacts
    if hasattr(request.node, "_capture"):
        try:
            request.node._capture.close()
        except Exception:
            pass


@pytest.fixture(autouse=True)
def _isolate_rate_limit_guard(monkeypatch: pytest.MonkeyPatch) -> Generator[None, None, None]:
    """Redirect the RateLimitGuard singleton to a temp file for every test.

    Prevents cross-test and cross-run pollution from state/agent_rate_limits.json.
    Each test gets a fresh, empty rate-limit state.

    Uses tempfile.mkdtemp() (outside pytest's tmp_path) so filesystem-scanner
    tests that receive tmp_path do not see the rate-limit file.
    """
    import shutil
    import tempfile

    import src.utils.rate_limit_guard as _rlg_mod
    from src.utils.rate_limit_guard import RateLimitGuard

    rlg_dir = Path(tempfile.mkdtemp(prefix="rlg_iso_"))
    try:
        clean_file = rlg_dir / "rate_limits.json"
        clean_file.write_text("{}", encoding="utf-8")
        new_guard = RateLimitGuard(state_file=clean_file)
        monkeypatch.setattr(_rlg_mod, "_guard", new_guard)
        yield
    finally:
        shutil.rmtree(rlg_dir, ignore_errors=True)


@pytest.fixture
def floor5() -> "Floor5Integration":
    """Provide a reusable Floor5 integration instance for tests."""
    from src.consciousness.floor_5_integration import Floor5Integration

    return Floor5Integration()


@pytest.fixture
def cross_domain_pattern() -> "IntegrationPattern":
    """Reusable integration pattern for cross-domain scenarios."""
    from src.consciousness.floor_5_integration import IntegrationPattern

    return IntegrationPattern.CROSS_DOMAIN


# ---------------------------------------------------------------------------
# Core fixtures needed by integration/E2E suites
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def isolated_workspace(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Create an isolated workspace layout used by e2e/integration tests."""

    workspace = tmp_path_factory.mktemp("workspace")
    for subdir in ("src", "tests", "config", "data"):
        (workspace / subdir).mkdir(exist_ok=True)
    return workspace


@pytest.fixture
def temp_config_file(tmp_path: Path) -> Generator[Path, None, None]:
    """Provide a temporary config file with minimal service settings."""

    config = tmp_path / "test_secrets.json"
    config.write_text(
        json.dumps(
            {
                "OLLAMA_HOST": "http://localhost:11434",
                "OLLAMA_PORT": "11434",
                "CHATDEV_PATH": str(tmp_path / "ChatDev"),
            }
        ),
        encoding="utf-8",
    )
    yield config
    if config.exists():
        config.unlink()


@pytest.fixture
def mock_chatdev_config(tmp_path: Path) -> dict[str, Any]:
    """Mock ChatDev configuration stub for orchestrator tests."""

    chatdev_dir = tmp_path / "ChatDev"
    chatdev_dir.mkdir(exist_ok=True)
    return {"path": str(chatdev_dir), "enabled": False, "models": ["qwen2.5-coder"]}


@pytest.fixture
def sample_quest_data() -> dict[str, Any]:
    """Sample quest data fixture for quest system tests."""

    return {
        "quest_id": "test_quest_001",
        "title": "Test Quest",
        "description": "A test quest for validation",
        "priority": "high",
        "status": "pending",
        "created_at": "2025-12-18T00:00:00Z",
    }


@pytest.fixture
def mock_ollama_server():
    """Mock Ollama server for testing (prevents network calls)."""
    from unittest.mock import AsyncMock, MagicMock

    server = MagicMock()
    server.endpoint = "http://localhost:11434"
    server.generate = AsyncMock(return_value={"response": "Test response"})
    server.available = True
    server.models = ["qwen2.5-coder:14b", "deepseek-coder-v2"]
    return server


@pytest.fixture
def mock_chatdev():
    """Mock ChatDev multi-agent team for testing (prevents subprocess hangs)."""
    from unittest.mock import AsyncMock, MagicMock

    chatdev = MagicMock()
    chatdev.spawn_project = AsyncMock(
        return_value={
            "status": "success",
            "project_id": "test_project_123",
            "path": "/tmp/test_project",
            "model": "qwen2.5-coder:7b",
        }
    )
    chatdev.available = True
    chatdev.path = "/mock/ChatDev"
    return chatdev


@pytest.fixture
def mock_ollama_response() -> dict[str, Any]:
    """Mock Ollama API response for testing."""
    return {
        "model": "qwen2.5-coder:14b",
        "response": "This is a test response from Ollama",
        "context": [1, 2, 3],
        "done": True,
    }


@pytest.fixture
def results() -> object:
    """Provide a lightweight TestResult-like object for CLI tests that expect a 'results' parameter."""

    class _Results:
        def __init__(self) -> None:
            self.passed = 0
            self.failed = 0
            self.errors: list[str] = []

        def test(self, name: str, condition: bool, message: str = "") -> None:
            if condition:
                self.passed += 1
            else:
                self.failed += 1
                msg = f"  ✗ {name}"
                if message:
                    msg += f": {message}"
                self.errors.append(msg)

        def summary(self) -> bool:
            return self.failed == 0

    return _Results()
