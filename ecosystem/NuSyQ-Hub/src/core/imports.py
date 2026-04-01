"""Unified import system for NuSyQ-Hub.

Eliminates the chaos of:
    try:
        from src.something import Thing
    except ImportError:
        try:
            from something import Thing
        except ImportError:
            Thing = None

Now use:
    Thing = safe_import("src.something", "Thing")
    # or
    Thing = safe_import("src.something", "Thing", fallback=MockThing)
"""

import importlib
import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, TypeVar, cast

logger = logging.getLogger(__name__)

T = TypeVar("T")

# Global registry of import attempts for debugging
_import_registry: dict[str, "ImportResult"] = {}


@dataclass
class ImportResult:
    """Track the result of an import attempt.

    Records the outcome and metadata of a single import attempt,
    used for debugging and diagnostics.

    Attributes:
        module_path: The full module path that was attempted to import.
        attribute: The specific attribute that was requested from the module.
        success: True if the import succeeded, False otherwise.
        error: Error message if the import failed, None if successful.
        timestamp: When the import attempt occurred.
        fallback_used: True if a fallback value was used instead of the import.

    Example:
        >>> result = ImportResult(
        ...     module_path="src.search.smart_search",
        ...     attribute="SmartSearch",
        ...     success=True
        ... )
    """

    module_path: str
    attribute: str
    success: bool
    error: str | None = None
    timestamp: datetime = field(default_factory=datetime.now)
    fallback_used: bool = False


def safe_import(
    module_path: str,
    attribute: str,
    fallback: T | None = None,
    alternatives: list[str] | None = None,
    required: bool = False,
    log_level: int = logging.DEBUG,
) -> T | None:
    """Safely import a module attribute with fallback support.

    Args:
        module_path: Full module path (e.g., "src.search.smart_search")
        attribute: Attribute to import (e.g., "SmartSearch")
        fallback: Value to return if import fails (default: None)
        alternatives: Alternative module paths to try
        required: If True, raise ImportError on failure
        log_level: Logging level for failures

    Returns:
        The imported attribute or fallback value

    Examples:
        SmartSearch = safe_import("src.search.smart_search", "SmartSearch")

        QuestEngine = safe_import(
            "src.Rosetta_Quest_System.quest_engine",
            "QuestEngine",
            alternatives=["Rosetta_Quest_System.quest_engine"]
        )
    """
    paths_to_try = [module_path] + (alternatives or [])

    for path in paths_to_try:
        try:
            module = importlib.import_module(path)
            result = getattr(module, attribute)

            # Register successful import
            _import_registry[f"{path}.{attribute}"] = ImportResult(
                module_path=path, attribute=attribute, success=True
            )

            return cast(T, result)

        except ImportError as e:
            _import_registry[f"{path}.{attribute}"] = ImportResult(
                module_path=path, attribute=attribute, success=False, error=str(e)
            )
            continue

        except AttributeError as e:
            _import_registry[f"{path}.{attribute}"] = ImportResult(
                module_path=path,
                attribute=attribute,
                success=False,
                error=f"Attribute not found: {e}",
            )
            continue

    # All attempts failed
    if required:
        raise ImportError(f"Could not import {attribute} from any of: {paths_to_try}")

    if fallback is not None:
        key = f"{module_path}.{attribute}"
        if key in _import_registry:
            _import_registry[key].fallback_used = True
        logger.log(log_level, f"Using fallback for {module_path}.{attribute}")

    return fallback


def lazy_import(
    module_path: str, attribute: str, alternatives: list[str] | None = None
) -> Callable[[], Any]:
    """Create a lazy importer that only loads when called.

    Returns a callable that defers the actual import until first invocation.
    Useful for breaking circular imports or deferring heavy module loads
    until they are actually needed.

    Args:
        module_path: Full module path (e.g., "src.search.smart_search").
        attribute: Attribute to import from the module (e.g., "SmartSearch").
        alternatives: Optional list of alternative module paths to try
            if the primary path fails.

    Returns:
        A callable that returns the imported attribute when called.
        The result is cached after the first call.

    Example:
        >>> get_SmartSearch = lazy_import("src.search.smart_search", "SmartSearch")
        >>> # The module is not loaded yet
        >>> SmartSearch = get_SmartSearch()  # Now it loads
        >>> search = SmartSearch()
    """
    _cached: dict[str, Any] = {}

    def _lazy_loader():
        if "value" not in _cached:
            _cached["value"] = safe_import(module_path, attribute, alternatives=alternatives)
        return _cached["value"]

    return _lazy_loader


def import_status() -> dict[str, Any]:
    """Get the status of all import attempts for debugging.

    Provides a summary of all imports attempted through safe_import,
    including success/failure counts and detailed per-import information.

    Returns:
        Dictionary containing:
            - total_attempts: Total number of import attempts
            - successful: Count of successful imports
            - failed: Count of failed imports
            - using_fallbacks: Count of imports using fallback values
            - details: Dict mapping import keys to their status info

    Example:
        >>> status = import_status()
        >>> print(f"Successful imports: {status['successful']}")
        >>> for key, info in status['details'].items():
        ...     if not info['success']:
        ...         print(f"Failed: {key} - {info['error']}")
    """
    successful = [k for k, v in _import_registry.items() if v.success]
    failed = [k for k, v in _import_registry.items() if not v.success]
    fallbacks = [k for k, v in _import_registry.items() if v.fallback_used]

    return {
        "total_attempts": len(_import_registry),
        "successful": len(successful),
        "failed": len(failed),
        "using_fallbacks": len(fallbacks),
        "details": {
            k: {"success": v.success, "error": v.error, "fallback": v.fallback_used}
            for k, v in _import_registry.items()
        },
    }


def clear_import_registry():
    """Clear the import registry.

    Removes all recorded import attempts from the global registry.
    Primarily useful for testing to ensure a clean state between tests.

    Example:
        >>> clear_import_registry()
        >>> status = import_status()
        >>> assert status['total_attempts'] == 0
    """
    _import_registry.clear()


# Pre-configured importers for common NuSyQ components
def get_smart_search():
    """Get the SmartSearch class.

    Attempts to import the SmartSearch class from its known locations,
    returning None if not available.

    Returns:
        The SmartSearch class if available, None otherwise.

    Example:
        >>> SmartSearch = get_smart_search()
        >>> if SmartSearch:
        ...     search = SmartSearch()
        ...     results = search.find("query")
    """
    return safe_import(
        "src.search.smart_search", "SmartSearch", alternatives=["search.smart_search"]
    )


def get_quest_engine():
    """Get the QuestEngine class.

    Attempts to import the QuestEngine class from its known locations,
    returning None if not available.

    Returns:
        The QuestEngine class if available, None otherwise.

    Example:
        >>> QuestEngine = get_quest_engine()
        >>> if QuestEngine:
        ...     engine = QuestEngine()
        ...     engine.add_quest("Fix the bug")
    """
    return safe_import(
        "src.Rosetta_Quest_System.quest_engine",
        "QuestEngine",
        alternatives=["Rosetta_Quest_System.quest_engine"],
    )


def get_ai_council():
    """Get the AICouncilVoting class.

    Attempts to import the AICouncilVoting class from its known locations,
    returning None if not available.

    Returns:
        The AICouncilVoting class if available, None otherwise.

    Example:
        >>> AICouncil = get_ai_council()
        >>> if AICouncil:
        ...     council = AICouncil()
        ...     decision_id = council.create_decision("Refactor?")
    """
    return safe_import(
        "src.orchestration.ai_council_voting",
        "AICouncilVoting",
        alternatives=["orchestration.ai_council_voting"],
    )


def get_background_orchestrator():
    """Get the BackgroundTaskOrchestrator class.

    Attempts to import the BackgroundTaskOrchestrator class from its
    known locations, returning None if not available.

    Returns:
        The BackgroundTaskOrchestrator class if available, None otherwise.

    Example:
        >>> Orchestrator = get_background_orchestrator()
        >>> if Orchestrator:
        ...     bg = Orchestrator()
        ...     task_id = await bg.submit_task("Analyze code")
    """
    return safe_import(
        "src.orchestration.background_task_orchestrator",
        "BackgroundTaskOrchestrator",
        alternatives=["orchestration.background_task_orchestrator"],
    )


def get_ai_intermediary():
    """Get the AIIntermediary class.

    Attempts to import the AIIntermediary class from its known locations,
    returning None if not available.

    Returns:
        The AIIntermediary class if available, None otherwise.

    Example:
        >>> AIIntermediary = get_ai_intermediary()
        >>> if AIIntermediary:
        ...     intermediary = AIIntermediary()
        ...     response = intermediary.process("query")
    """
    return safe_import(
        "src.ai.ai_intermediary", "AIIntermediary", alternatives=["ai.ai_intermediary"]
    )


def get_chatdev_router():
    """Get the ChatDevAutonomousRouter class.

    Attempts to import the ChatDevAutonomousRouter class from its
    known locations, returning None if not available.

    Returns:
        The ChatDevAutonomousRouter class if available, None otherwise.

    Example:
        >>> Router = get_chatdev_router()
        >>> if Router:
        ...     router = Router()
        ...     result = router.route_request("Build a web app")
    """
    return safe_import(
        "src.orchestration.chatdev_autonomous_router",
        "ChatDevAutonomousRouter",
        alternatives=["orchestration.chatdev_autonomous_router"],
    )


def get_connector_registry():
    """Get the ConnectorRegistry class.

    Attempts to import the ConnectorRegistry from known connector module paths.

    Returns:
        The ConnectorRegistry class if available, None otherwise.
    """
    return safe_import(
        "src.connectors.registry",
        "ConnectorRegistry",
        alternatives=["connectors.registry"],
    )


def get_workflow_engine():
    """Get the WorkflowEngine class.

    Attempts to import the WorkflowEngine class from known workflow module paths.

    Returns:
        The WorkflowEngine class if available, None otherwise.
    """
    return safe_import(
        "src.workflow.engine",
        "WorkflowEngine",
        alternatives=["workflow.engine"],
    )


def get_test_loop():
    """Get the TestLoop class.

    Attempts to import the TestLoop class from known automation module paths.

    Returns:
        The TestLoop class if available, None otherwise.
    """
    return safe_import(
        "src.automation.test_loop",
        "TestLoop",
        alternatives=["automation.test_loop"],
    )


def get_zero_token_bridge():
    """Get the ZeroTokenBridge class.

    Attempts to import the ZeroTokenBridge class from known integration paths.

    Returns:
        The ZeroTokenBridge class if available, None otherwise.
    """
    return safe_import(
        "src.integration.zero_token_bridge",
        "ZeroTokenBridge",
        alternatives=["integration.zero_token_bridge"],
    )


def get_sns_converter():
    """Get the convert_to_sns function.

    Attempts to import SNS-Core converter function from known utility paths.

    Returns:
        The convert_to_sns callable if available, None otherwise.
    """
    return safe_import(
        "src.utils.sns_core_helper",
        "convert_to_sns",
        alternatives=["utils.sns_core_helper"],
    )
