"""🧠 Intelligent Adaptive Timeout Manager with AI Agent Weights.

=================================================================

Provides intelligent, adaptive timeout management for AI agents with:
- Dynamic timeout adjustment based on task complexity
- Service-specific weights (Ollama, ChatDev, etc.)
- Historical performance tracking
- Automatic scaling based on system load
- Graceful degradation under pressure

OmniTag: {
    "purpose": "adaptive_timeout_orchestration",
    "tags": ["timeout", "adaptive", "ai-agents", "performance"],
    "category": "infrastructure",
    "evolution_stage": "production_intelligent"
}
"""

import json
import logging
import os
import time
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class ServiceWeights:
    """Weight configuration for a service."""

    name: str
    base_timeout: int
    complexity_multiplier: float = 1.0
    load_sensitivity: float = 1.0
    min_timeout: int = 10
    max_timeout: int = 3600
    adaptive_enabled: bool = True
    history_window: int = 10
    performance_history: list[float] = field(default_factory=list)

    def calculate_timeout(
        self,
        complexity: float = 1.0,
        system_load: float = 1.0,
        task_priority: str = "normal",
    ) -> int:
        """Calculate adaptive timeout based on conditions.

        Args:
            complexity: Task complexity factor (0.5 = simple, 1.0 = normal, 2.0 = complex)
            system_load: Current system load factor (0.5 = light, 1.0 = normal, 2.0 = heavy)
            task_priority: Priority level (low/normal/high/critical)

        Returns:
            Calculated timeout in seconds
        """
        if not self.adaptive_enabled:
            return self.base_timeout

        # Priority multipliers
        priority_multipliers = {
            "low": 0.7,
            "normal": 1.0,
            "high": 1.5,
            "critical": 2.0,
        }
        priority_mult = priority_multipliers.get(task_priority.lower(), 1.0)

        # Historical performance adjustment
        historical_mult = 1.0
        if self.performance_history:
            avg_completion = sum(self.performance_history) / len(self.performance_history)
            if avg_completion > self.base_timeout * 0.8:
                historical_mult = 1.3  # Tasks taking longer - increase timeout
            elif avg_completion < self.base_timeout * 0.5:
                historical_mult = 0.9  # Tasks completing quickly - can reduce

        # Calculate adaptive timeout
        timeout = int(
            self.base_timeout
            * complexity
            * self.complexity_multiplier
            * (1 + (system_load - 1) * self.load_sensitivity)
            * priority_mult
            * historical_mult
        )

        # Clamp to min/max
        return max(self.min_timeout, min(self.max_timeout, timeout))

    def record_performance(self, duration: float) -> None:
        """Record task completion duration for adaptive learning."""
        self.performance_history.append(duration)
        if len(self.performance_history) > self.history_window:
            self.performance_history.pop(0)


class IntelligentTimeoutManager:
    """Manages adaptive timeouts for all AI agents and services."""

    def __init__(self, config_path: str | Path | None = None) -> None:
        """Initialize timeout manager.

        Args:
            config_path: Optional path to timeout configuration JSON
        """
        self.config_path = Path(config_path) if config_path else Path(".cache/timeout_config.json")
        self.service_weights = self._load_service_weights()
        self.system_load_factor = 1.0
        self.last_load_check = time.time()

    def _load_service_weights(self) -> dict[str, ServiceWeights]:
        """Load service weight configurations."""
        # Default configurations
        defaults = {
            "ollama": ServiceWeights(
                name="ollama",
                base_timeout=int(os.getenv("OLLAMA_MAX_TIMEOUT_SECONDS", "300")),
                complexity_multiplier=1.5,  # LLM generation is complex
                load_sensitivity=0.8,  # Moderately sensitive to load
                min_timeout=30,
                max_timeout=3600,
                adaptive_enabled=os.getenv("OLLAMA_ADAPTIVE_TIMEOUT", "true").lower()
                in ("true", "1", "yes"),
            ),
            "chatdev": ServiceWeights(
                name="chatdev",
                base_timeout=int(os.getenv("CHATDEV_GENERATION_TIMEOUT_SECONDS", "600")),
                complexity_multiplier=2.0,  # Multi-agent coordination is complex
                load_sensitivity=1.2,  # More sensitive to system load
                min_timeout=60,
                max_timeout=7200,  # Can take up to 2 hours for large projects
                adaptive_enabled=os.getenv("CHATDEV_ADAPTIVE_TIMEOUT", "true").lower()
                in ("true", "1", "yes"),
            ),
            "http_general": ServiceWeights(
                name="http_general",
                base_timeout=int(os.getenv("HTTP_TIMEOUT_SECONDS", "10")),
                complexity_multiplier=1.0,
                load_sensitivity=0.5,
                min_timeout=5,
                max_timeout=60,
                adaptive_enabled=True,
            ),
            "subprocess": ServiceWeights(
                name="subprocess",
                base_timeout=int(os.getenv("SUBPROCESS_TIMEOUT_SECONDS", "30")),
                complexity_multiplier=1.0,
                load_sensitivity=0.7,
                min_timeout=5,
                max_timeout=300,
                adaptive_enabled=True,
            ),
            "tool_check": ServiceWeights(
                name="tool_check",
                base_timeout=int(os.getenv("TOOL_CHECK_TIMEOUT_SECONDS", "10")),
                complexity_multiplier=0.5,
                load_sensitivity=0.3,
                min_timeout=5,
                max_timeout=30,
                adaptive_enabled=False,  # Tool checks should be quick
            ),
            "tool_help": ServiceWeights(
                name="tool_help",
                base_timeout=int(os.getenv("TOOL_HELP_TIMEOUT_SECONDS", "10")),
                complexity_multiplier=0.5,
                load_sensitivity=0.3,
                min_timeout=5,
                max_timeout=30,
                adaptive_enabled=False,  # Help output should stay deterministic and fast
            ),
            "analysis": ServiceWeights(
                name="analysis",
                base_timeout=int(os.getenv("ANALYSIS_TOOL_TIMEOUT_SECONDS", "180")),
                complexity_multiplier=1.2,
                load_sensitivity=0.9,
                min_timeout=30,
                max_timeout=600,
                adaptive_enabled=True,
            ),
            "pytest": ServiceWeights(
                name="pytest",
                base_timeout=int(os.getenv("PYTEST_TIMEOUT_SECONDS", "120")),
                complexity_multiplier=1.1,
                load_sensitivity=0.8,
                min_timeout=30,
                max_timeout=1800,
                adaptive_enabled=os.getenv("PYTEST_ADAPTIVE_TIMEOUT", "true").lower()
                in ("true", "1", "yes"),
            ),
            "hygiene": ServiceWeights(
                name="hygiene",
                base_timeout=int(os.getenv("HYGIENE_TIMEOUT_SECONDS", "60")),
                complexity_multiplier=1.0,
                load_sensitivity=0.6,
                min_timeout=30,
                max_timeout=600,
                adaptive_enabled=os.getenv("HYGIENE_ADAPTIVE_TIMEOUT", "true").lower()
                in ("true", "1", "yes"),
            ),
            "simulatedverse": ServiceWeights(
                name="simulatedverse",
                base_timeout=int(os.getenv("SIMULATEDVERSE_RESULT_TIMEOUT_SECONDS", "30")),
                complexity_multiplier=1.0,
                load_sensitivity=0.6,
                min_timeout=10,
                max_timeout=120,
                adaptive_enabled=True,
            ),
        }

        # Load from cache if exists
        if self.config_path.exists():
            try:
                with open(self.config_path, encoding="utf-8") as f:
                    cached = json.load(f)
                    for service, data in cached.items():
                        if service in defaults:
                            # Restore performance history
                            defaults[service].performance_history = data.get(
                                "performance_history", []
                            )
                logger.info(f"✅ Loaded timeout config from {self.config_path}")
            except (OSError, json.JSONDecodeError) as e:
                logger.warning(f"⚠️ Could not load timeout config: {e}")

        return defaults

    def save_config(self) -> None:
        """Save service weights and performance history to cache."""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)

        cache_data = {}
        for name, weights in self.service_weights.items():
            cache_data[name] = {
                "base_timeout": weights.base_timeout,
                "performance_history": weights.performance_history[-weights.history_window :],
                "adaptive_enabled": weights.adaptive_enabled,
            }

        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(cache_data, f, indent=2)
        except OSError as e:
            logger.warning(f"⚠️ Could not save timeout config: {e}")

    def get_timeout(
        self,
        service: str,
        complexity: float = 1.0,
        priority: str = "normal",
        update_load: bool = False,
    ) -> int:
        """Get adaptive timeout for a service.

        Args:
            service: Service name (ollama, chatdev, http_general, etc.)
            complexity: Task complexity factor (0.5-2.0)
            priority: Task priority (low/normal/high/critical)
            update_load: Whether to update system load factor

        Returns:
            Calculated timeout in seconds
        """
        if update_load or (time.time() - self.last_load_check) > 60:
            self._update_system_load()

        weights = self.service_weights.get(service.lower())
        if not weights:
            logger.warning(f"⚠️ Unknown service '{service}', using default timeout")
            return 30

        timeout = weights.calculate_timeout(
            complexity=complexity,
            system_load=self.system_load_factor,
            task_priority=priority,
        )

        logger.debug(
            f"🕐 {service} timeout: {timeout}s "
            f"(base={weights.base_timeout}, complexity={complexity}, "
            f"load={self.system_load_factor:.2f}, priority={priority})"
        )

        return timeout

    def record_completion(self, service: str, duration: float) -> None:
        """Record task completion for adaptive learning.

        Args:
            service: Service name
            duration: Actual completion time in seconds
        """
        weights = self.service_weights.get(service.lower())
        if weights:
            weights.record_performance(duration)
            # Save periodically
            if len(weights.performance_history) % 5 == 0:
                self.save_config()

    def _update_system_load(self) -> None:
        """Update system load factor based on current conditions."""
        try:
            import psutil

            cpu_percent = psutil.cpu_percent(interval=0.1)
            mem_percent = psutil.virtual_memory().percent

            # Calculate load factor (1.0 = normal, >1.0 = high load)
            cpu_factor = cpu_percent / 50.0  # 50% CPU = normal
            mem_factor = mem_percent / 60.0  # 60% memory = normal

            self.system_load_factor = max(0.5, min(2.0, (cpu_factor + mem_factor) / 2))
            self.last_load_check = time.time()

            logger.debug(
                f"📊 System load: CPU={cpu_percent:.1f}%, MEM={mem_percent:.1f}%, factor={self.system_load_factor:.2f}"
            )

        except (ImportError, AttributeError):
            # psutil not available - use default
            self.system_load_factor = 1.0

    def get_all_timeouts(self) -> dict[str, int]:
        """Get current timeouts for all services."""
        return {
            name: weights.calculate_timeout(
                complexity=1.0,
                system_load=self.system_load_factor,
                task_priority="normal",
            )
            for name, weights in self.service_weights.items()
        }

    def adjust_service_weight(
        self,
        service: str,
        base_timeout: int | None = None,
        complexity_multiplier: float | None = None,
        adaptive_enabled: bool | None = None,
    ) -> None:
        """Dynamically adjust service weights.

        Args:
            service: Service name
            base_timeout: New base timeout (optional)
            complexity_multiplier: New complexity multiplier (optional)
            adaptive_enabled: Enable/disable adaptive timeouts (optional)
        """
        weights = self.service_weights.get(service.lower())
        if not weights:
            logger.warning(f"⚠️ Unknown service '{service}'")
            return

        if base_timeout is not None:
            weights.base_timeout = base_timeout
        if complexity_multiplier is not None:
            weights.complexity_multiplier = complexity_multiplier
        if adaptive_enabled is not None:
            weights.adaptive_enabled = adaptive_enabled

        self.save_config()
        logger.info(f"✅ Updated timeout weights for '{service}'")


# Backwards-compat: alternate name expected by some tests
class ServiceTimeoutManager(IntelligentTimeoutManager):
    """Alias for IntelligentTimeoutManager for backwards compatibility."""


# Global timeout manager instance
_timeout_manager: IntelligentTimeoutManager | None = None


def get_intelligent_timeout_manager() -> IntelligentTimeoutManager:
    """Get or create global timeout manager instance."""
    global _timeout_manager
    if _timeout_manager is None:
        _timeout_manager = IntelligentTimeoutManager()
    return _timeout_manager


def get_adaptive_timeout(
    service: str,
    complexity: float = 1.0,
    priority: str = "normal",
) -> int:
    """Get adaptive timeout for a service (convenience function).

    Args:
        service: Service name (ollama, chatdev, etc.)
        complexity: Task complexity (0.5 = simple, 1.0 = normal, 2.0 = complex)
        priority: Priority level (low/normal/high/critical)

    Returns:
        Calculated timeout in seconds
    """
    manager = get_intelligent_timeout_manager()
    return manager.get_timeout(service, complexity=complexity, priority=priority)


def record_service_completion(service: str, duration: float) -> None:
    """Record service task completion (convenience function)."""
    manager = get_intelligent_timeout_manager()
    manager.record_completion(service, duration)


# ----------------------------------------------------------------------------
# Backwards-compatibility adapter
# ----------------------------------------------------------------------------
class TimeoutCalculator:
    """Compatibility wrapper expected by older/new tests.

    Provides a simple calculate() API that delegates to the
    IntelligentTimeoutManager.get_timeout(). This allows tests
    referencing TimeoutCalculator to work without changing
    production code paths.
    """

    def __init__(
        self,
        base_timeout: int = 30,
        default_service: str = "ollama",
        min_timeout: int | None = None,
        max_timeout: int | None = None,
    ) -> None:
        """Initialize TimeoutCalculator with base_timeout, default_service, min_timeout, ...."""
        self._manager = get_intelligent_timeout_manager()
        self._default_service = default_service
        # Expose min/max on the adapter for tests
        self.min_timeout = min_timeout if min_timeout is not None else 5
        self.max_timeout = max_timeout if max_timeout is not None else 7200
        # If the test passes a base_timeout, reflect it in the manager weights
        try:
            if isinstance(base_timeout, (int, float)) and base_timeout > 0:
                self._manager.adjust_service_weight(default_service, base_timeout=int(base_timeout))
            # Apply min/max overrides directly to service weights if provided
            weights = self._manager.service_weights.get(default_service)
            if weights is not None:
                if min_timeout is not None:
                    weights.min_timeout = int(min_timeout)
                if max_timeout is not None:
                    weights.max_timeout = int(max_timeout)
        except Exception:
            # Be resilient in constrained environments
            logger.debug("Suppressed Exception", exc_info=True)

    def calculate(
        self,
        complexity: float = 1.0,
        priority: str = "normal",
        service: str | None = None,
    ) -> int:
        """Calculate timeout for a service.

        Args:
            complexity: Task complexity factor
            priority: Priority level
            service: Optional service override; defaults to instance service

        Returns:
            Timeout in seconds
        """
        svc = service or self._default_service
        return self._manager.get_timeout(svc, complexity=complexity, priority=priority)

    def record(self, service: str, duration: float) -> None:
        """Record completion metrics for adaptive learning."""
        record_service_completion(service, duration)

    def record_performance(self, duration: float) -> None:
        """Back-compat: record performance against the default service."""
        try:
            weights = self._manager.service_weights.get(self._default_service)
            if weights:
                weights.record_performance(duration)
        except Exception:
            logger.debug("Suppressed Exception", exc_info=True)

    # Backwards-compatible API name expected by tests
    def calculate_timeout(
        self,
        complexity: float = 1.0,
        priority: str = "normal",
        service: str | None = None,
    ) -> int:
        return self.calculate(complexity=complexity, priority=priority, service=service)
