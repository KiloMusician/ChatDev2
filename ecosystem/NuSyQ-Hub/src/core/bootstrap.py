"""Unified Bootstrap System for NuSyQ-Hub.

Eliminates the chaos of scattered initialization across files.
One-shot system initialization with clear status reporting.
"""

import logging
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from .imports import import_status

logger = logging.getLogger(__name__)


@dataclass
class SystemComponent:
    """Represents a bootable system component.

    Tracks the state and initialization details of a single component
    in the bootstrap system.

    Attributes:
        name: Unique identifier for this component.
        init_fn: Callable that returns an initialized component instance.
        instance: The initialized component instance, or None if not yet booted.
        status: Current status of the component. One of:
            - "pending": Not yet initialized
            - "ready": Successfully initialized
            - "failed": Initialization failed
            - "disabled": Explicitly disabled, won't be initialized
        error: Error message if status is "failed", None otherwise.
        boot_time_ms: Time taken to initialize this component in milliseconds.
        required: If True, the entire system boot fails if this component fails.

    Example:
        >>> component = SystemComponent(
        ...     name="SmartSearch",
        ...     init_fn=lambda: SmartSearch(),
        ...     required=True
        ... )
    """

    name: str
    init_fn: Callable[[], Any]
    instance: Any = None
    status: str = "pending"  # pending, ready, failed, disabled
    error: str | None = None
    boot_time_ms: float = 0.0
    required: bool = False  # If True, system won't start without it


@dataclass
class BootResult:
    """Result of a system bootstrap operation.

    Contains the outcome and statistics of the bootstrap process,
    including which components succeeded and which failed.

    Attributes:
        success: True if all required components initialized successfully.
        systems_ready: Count of components that initialized successfully.
        systems_failed: Count of components that failed to initialize.
        systems_disabled: Count of components that were disabled.
        total_boot_time_ms: Total time for the boot process in milliseconds.
        components: Dictionary mapping component names to their SystemComponent objects.
        errors: List of error messages from failed components.

    Example:
        >>> result = bootstrap.boot()
        >>> if result.success:
        ...     print(f"Boot completed in {result.total_boot_time_ms}ms")
        ... else:
        ...     for error in result.errors:
        ...         print(f"Error: {error}")
    """

    success: bool
    systems_ready: int
    systems_failed: int
    systems_disabled: int
    total_boot_time_ms: float
    components: dict[str, SystemComponent]
    errors: list[str] = field(default_factory=list)


class SystemBootstrap:
    """Unified system initialization for NuSyQ-Hub.

    Manages the registration and initialization of system components,
    providing ordered startup with error handling and status reporting.

    Attributes:
        name: Name of this bootstrap instance, used in logging.
        components: Dictionary of registered components.

    Example:
        >>> bootstrap = SystemBootstrap()
        >>> bootstrap.register("SmartSearch", lambda: SmartSearch())
        >>> bootstrap.register("QuestEngine", lambda: QuestEngine(), required=True)
        >>>
        >>> result = bootstrap.boot()
        >>> if result.success:
        ...     smart_search = bootstrap.get("SmartSearch")
        ...     print("System ready!")
    """

    def __init__(self, name: str = "NuSyQ-Hub"):
        """Initialize a new SystemBootstrap instance.

        Args:
            name: Display name for this bootstrap instance, used in
                logging and status output. Defaults to "NuSyQ-Hub".
        """
        self.name = name
        self.components: dict[str, SystemComponent] = {}
        self._booted = False
        self._boot_result: BootResult | None = None

    def register(
        self, name: str, init_fn: Callable[[], Any], required: bool = False, enabled: bool = True
    ) -> "SystemBootstrap":
        """Register a component for initialization.

        Adds a component to the bootstrap registry. Components will be
        initialized in registration order when boot() is called.

        Args:
            name: Unique identifier for the component. Used to retrieve
                the component later via get().
            init_fn: A callable that takes no arguments and returns the
                initialized component instance. Called during boot().
            required: If True, the entire boot process is considered failed
                if this component fails to initialize. Defaults to False.
            enabled: If False, the component will be marked as "disabled"
                and skipped during boot. Defaults to True.

        Returns:
            Self reference for method chaining.

        Example:
            >>> bootstrap.register(
            ...     "Database",
            ...     lambda: Database(connection_string),
            ...     required=True
            ... ).register(
            ...     "Cache",
            ...     lambda: Cache(),
            ...     required=False
            ... )
        """
        self.components[name] = SystemComponent(
            name=name,
            init_fn=init_fn,
            required=required,
            status="disabled" if not enabled else "pending",
        )
        return self

    def boot(self, _parallel: bool = False) -> BootResult:
        """Initialize all registered components.

        Iterates through all registered components and calls their
        initialization functions, tracking success/failure and timing.

        Args:
            parallel: If True, initialize components in parallel using
                threading. This is experimental and may cause issues
                with components that have initialization order dependencies.
                Defaults to False.

        Returns:
            BootResult containing the outcome of the boot process including
            counts of ready, failed, and disabled components, as well as
            any error messages.

        Example:
            >>> result = bootstrap.boot()
            >>> if result.success:
            ...     print(f"Booted {result.systems_ready} systems")
            ... else:
            ...     print(f"Boot failed: {result.errors}")
        """
        start_time = time.perf_counter()
        errors = []

        logger.info(f"🚀 Booting {self.name}...")

        for name, component in self.components.items():
            if component.status == "disabled":
                logger.info(f"  ⏸️  {name}: disabled")
                continue

            comp_start = time.perf_counter()

            try:
                component.instance = component.init_fn()
                component.status = "ready"
                component.boot_time_ms = (time.perf_counter() - comp_start) * 1000
                logger.info(f"  ✅ {name}: ready ({component.boot_time_ms:.1f}ms)")

            except Exception as e:
                component.status = "failed"
                component.error = str(e)
                component.boot_time_ms = (time.perf_counter() - comp_start) * 1000
                errors.append(f"{name}: {e}")
                logger.warning(f"  ❌ {name}: {e}")

                if component.required:
                    logger.error(f"Required component {name} failed to initialize")

        total_time = (time.perf_counter() - start_time) * 1000

        ready = sum(1 for c in self.components.values() if c.status == "ready")
        failed = sum(1 for c in self.components.values() if c.status == "failed")
        disabled = sum(1 for c in self.components.values() if c.status == "disabled")

        # Check if any required components failed
        required_failed = any(c.status == "failed" and c.required for c in self.components.values())

        self._boot_result = BootResult(
            success=not required_failed,
            systems_ready=ready,
            systems_failed=failed,
            systems_disabled=disabled,
            total_boot_time_ms=total_time,
            components=self.components,
            errors=errors,
        )

        self._booted = True

        status = "✅ READY" if self._boot_result.success else "❌ FAILED"
        logger.info(f"🏁 {self.name} boot complete: {status}")
        logger.info(f"   {ready} ready, {failed} failed, {disabled} disabled ({total_time:.1f}ms)")

        return self._boot_result

    def get(self, name: str) -> Any:
        """Get an initialized component instance by name.

        Retrieves the instance of a previously booted component.
        Returns None if the component doesn't exist, hasn't been booted,
        or failed to initialize.

        Args:
            name: The unique identifier of the component to retrieve.

        Returns:
            The initialized component instance, or None if not available.

        Example:
            >>> result = bootstrap.boot()
            >>> if result.success:
            ...     search = bootstrap.get("SmartSearch")
            ...     search.find("query")
        """
        if name not in self.components:
            return None
        component = self.components[name]
        if component.status != "ready":
            return None
        return component.instance

    def is_ready(self, name: str) -> bool:
        """Check if a component is ready and available.

        Args:
            name: The unique identifier of the component to check.

        Returns:
            True if the component exists and has status "ready",
            False otherwise.

        Example:
            >>> if bootstrap.is_ready("SmartSearch"):
            ...     search = bootstrap.get("SmartSearch")
            ...     search.find("query")
        """
        return name in self.components and self.components[name].status == "ready"

    def status(self) -> dict[str, Any]:
        """Get the current boot status as a dictionary.

        Returns comprehensive status information including boot state,
        component statuses, and import registry status.

        Returns:
            Dictionary containing:
                - booted: Whether boot() has been called
                - components: Dict of component names to their status info
                - imports: Import registry status from the imports module

        Example:
            >>> status = bootstrap.status()
            >>> print(f"Booted: {status['booted']}")
            >>> for name, info in status['components'].items():
            ...     print(f"{name}: {info['status']}")
        """
        return {
            "booted": self._booted,
            "components": {
                name: {"status": c.status, "error": c.error, "boot_time_ms": c.boot_time_ms}
                for name, c in self.components.items()
            },
            "imports": import_status(),
        }

    def status_string(self) -> str:
        """Get a human-readable formatted status string.

        Creates a multi-line string representation of the current
        bootstrap status, suitable for display to users.

        Returns:
            A formatted string with status icons and component information.

        Example:
            >>> print(bootstrap.status_string())
            === NuSyQ-Hub Status ===
              [check] SmartSearch: ready
              [x] Database: failed
                  Error: Connection refused
        """
        lines = [f"=== {self.name} Status ==="]
        for name, c in self.components.items():
            icon = {"ready": "✅", "failed": "❌", "disabled": "⏸️", "pending": "⏳"}.get(
                c.status, "?"
            )
            lines.append(f"  {icon} {name}: {c.status}")
            if c.error:
                lines.append(f"      Error: {c.error}")
        return "\n".join(lines)


# Global default bootstrap instance
_default_bootstrap: SystemBootstrap | None = None


def get_bootstrap() -> SystemBootstrap:
    """Get the default global bootstrap instance.

    Returns the singleton SystemBootstrap instance, creating it if
    it doesn't exist. Use this to access the shared bootstrap
    instance across the application.

    Returns:
        The global SystemBootstrap instance.

    Example:
        >>> bootstrap = get_bootstrap()
        >>> bootstrap.register("MyComponent", lambda: MyComponent())
        >>> bootstrap.boot()
    """
    global _default_bootstrap
    if _default_bootstrap is None:
        _default_bootstrap = SystemBootstrap()
    return _default_bootstrap


def quick_boot() -> BootResult:
    """Quick boot with all standard NuSyQ components.

    Convenience function that registers and boots all standard NuSyQ
    components (SmartSearch, QuestEngine, AICouncil, BackgroundOrchestrator)
    in a single call.

    Components are only registered if their classes are available
    (i.e., can be imported successfully).

    Returns:
        BootResult containing the outcome of the boot process.

    Example:
        >>> from src.core.bootstrap import quick_boot
        >>>
        >>> result = quick_boot()
        >>> if result.success:
        ...     print("System ready!")
        ...     print(f"Booted {result.systems_ready} components")
        ... else:
        ...     print(f"Boot failed with {len(result.errors)} errors")
    """
    from .imports import (get_ai_council, get_background_orchestrator,
                          get_quest_engine, get_smart_search)

    bootstrap = get_bootstrap()

    # Register standard components
    SmartSearch = get_smart_search()
    if SmartSearch:
        bootstrap.register("SmartSearch", lambda: SmartSearch())

    QuestEngine = get_quest_engine()
    if QuestEngine:
        bootstrap.register("QuestEngine", lambda: QuestEngine())

    AICouncil = get_ai_council()
    if AICouncil:
        bootstrap.register("AICouncil", lambda: AICouncil())

    BackgroundOrchestrator = get_background_orchestrator()
    if BackgroundOrchestrator:
        bootstrap.register("BackgroundOrchestrator", lambda: BackgroundOrchestrator())

    return bootstrap.boot()
