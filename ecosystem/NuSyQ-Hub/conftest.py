# Local pytest helper: run async test coroutines even when pytest-asyncio
# plugin is not installed. This keeps CI/test-runner robust in minimal envs.

import sys
from pathlib import Path

# Ensure workspace root is on sys.path so 'scripts' package is importable
_workspace_root = Path(__file__).parent
if str(_workspace_root) not in sys.path:
    sys.path.insert(0, str(_workspace_root))

import asyncio
import inspect
import logging

logger = logging.getLogger(__name__)


def pytest_pyfunc_call(pyfuncitem):
    """Execute async test functions using asyncio.run when pytest-asyncio isn't present.

    This hook is intentionally small and safe: if the test is a coroutine function,
    we run it to completion in a fresh event loop and return True to short-circuit
    the default pyfunc runner.
    """
    testfunc = pyfuncitem.obj
    if inspect.iscoroutinefunction(testfunc):
        # Build kwargs from the collected fixtures
        kwargs = {arg: pyfuncitem.funcargs[arg] for arg in pyfuncitem._fixtureinfo.argnames}
        # Run the coroutine using asyncio.run to avoid deprecated get_event_loop semantics
        return asyncio.run(testfunc(**kwargs))
    # Not a coroutine — let pytest handle it normally by returning None
    return None


def pytest_configure(config):
    """Register custom pytest markers and configure intelligent timeouts."""
    config.addinivalue_line(
        "markers",
        "ml_heavy: mark test as heavy ML/AI dependent (requires sentence_transformers, sklearn, scipy)",
    )

    # Wire up IntelligentTimeoutManager for adaptive pytest timeouts
    try:
        from src.utils.intelligent_timeout_manager import get_intelligent_timeout_manager

        timeout_mgr = get_intelligent_timeout_manager()
        adaptive_timeout = timeout_mgr.get_timeout("pytest", complexity=1.0, priority="normal")

        # Override pytest timeout with adaptive value
        config.option.timeout = adaptive_timeout
        logger.info(f"🧠 Intelligent timeout configured: {adaptive_timeout}s for pytest")
    except (ImportError, AttributeError) as e:
        logger.warning(f"⚠️ Could not load IntelligentTimeoutManager: {e}")
        # Fallback to pytest.ini default
