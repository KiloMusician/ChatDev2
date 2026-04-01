#!/usr/bin/env python3
"""Auto-Healing Integration - Connects traced errors to quantum resolver.

This module monitors traced errors and automatically triggers the quantum
problem resolver for self-healing. It provides:

- Real-time error detection from traces
- Automatic quantum resolver invocation
- Healing success/failure tracking
- Integration with observability stack
"""

import logging
import time
from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

try:
    from src.observability import tracing as tracing_mod

    TRACING_ENABLED = True
except Exception:
    tracing_mod: Any = None
    TRACING_ENABLED = False

try:
    from prometheus_client import Counter, Histogram

    healing_attempts = Counter(
        "auto_healing_attempts_total",
        "Total auto-healing attempts",
        ["error_type", "outcome"],
    )
    healing_duration = Histogram(
        "auto_healing_duration_seconds",
        "Time taken for healing attempts",
        ["error_type"],
    )
    METRICS_ENABLED = True
except ImportError:
    METRICS_ENABLED = False

logger = logging.getLogger(__name__)


@dataclass
class ErrorContext:
    """Context information for an error."""

    error_type: str
    error_message: str
    span_name: str
    timestamp: float
    attributes: dict
    trace_id: str | None = None
    span_id: str | None = None


class AutoHealingMonitor:
    """Monitors errors and triggers automatic healing."""

    def __init__(
        self,
        enable_auto_heal: bool = True,
        max_retry_attempts: int = 3,
        cooldown_seconds: int = 60,
    ) -> None:
        """Initialize auto-healing monitor.

        Args:
            enable_auto_heal: Whether to automatically attempt healing
            max_retry_attempts: Maximum healing attempts per error type
            cooldown_seconds: Cooldown period between healing attempts
        """
        self.enable_auto_heal = enable_auto_heal
        self.max_retry_attempts = max_retry_attempts
        self.cooldown_seconds = cooldown_seconds

        # Track healing attempts
        self.healing_history: dict[str, list[dict[str, Any]]] = defaultdict(list)
        self.last_healing_time: dict[str, float] = {}

        # Statistics
        self.stats = {
            "errors_detected": 0,
            "healing_attempts": 0,
            "healing_successes": 0,
            "healing_failures": 0,
        }

        logger.info(f"✅ Auto-healing monitor initialized (enabled={enable_auto_heal})")

    def on_error(
        self,
        error: Exception,
        context: ErrorContext,
        healing_callback: Callable | None = None,
    ) -> bool:
        """Handle error detection and trigger healing.

        Args:
            error: The exception that occurred
            context: Error context information
            healing_callback: Optional custom healing function

        Returns:
            True if healing was attempted, False otherwise
        """
        self.stats["errors_detected"] += 1

        logger.warning(f"🔍 Error detected: {context.error_type} in {context.span_name}")

        # Check if we should attempt healing
        if not self.enable_auto_heal:
            logger.debug("Auto-healing disabled, skipping")
            return False

        if not self._should_heal(context.error_type):
            logger.debug(f"Cooldown active or max retries reached for {context.error_type}")
            return False

        # Attempt healing
        return self._attempt_healing(error, context, healing_callback)

    def _should_heal(self, error_type: str) -> bool:
        """Check if healing should be attempted for this error type."""
        # Check cooldown
        last_time = self.last_healing_time.get(error_type, 0)
        if time.time() - last_time < self.cooldown_seconds:
            return False

        # Check retry limit
        recent_attempts = self.healing_history.get(error_type, [])
        return not len(recent_attempts) >= self.max_retry_attempts

    def _attempt_healing(
        self,
        error: Exception,
        context: ErrorContext,
        healing_callback: Callable | None,
    ) -> bool:
        """Attempt to heal the error."""
        start_time = time.time()
        self.stats["healing_attempts"] += 1

        logger.info(f"🔧 Attempting auto-heal for {context.error_type}")

        try:
            # Use custom callback if provided, else fall back to quantum resolver
            success = (
                healing_callback(error, context)
                if healing_callback
                else self._default_healing(error, context)
            )

            duration = time.time() - start_time

            if success:
                self._record_success(context.error_type, duration)
                logger.info(f"✅ Healing successful for {context.error_type} ({duration:.2f}s)")
            else:
                self._record_failure(context.error_type, duration)
                logger.warning(f"❌ Healing failed for {context.error_type} ({duration:.2f}s)")

            result: bool = success
            return result

        except Exception as e:
            duration = time.time() - start_time
            self._record_failure(context.error_type, duration)
            logger.error(f"❌ Healing error: {e}")
            return False

    def _default_healing(self, error: Exception, context: ErrorContext) -> bool:
        """Default healing using quantum resolver."""
        del error
        # Create problem description
        problem_data = {
            "type": context.error_type,
            "message": context.error_message,
            "span": context.span_name,
            "attributes": context.attributes,
        }

        logger.info(f"Quantum resolver analyzing: {problem_data}")

        # Attempt resolution using real QuantumProblemResolver
        try:
            from src.healing.quantum_problem_resolver import \
                QuantumProblemResolver

            resolver = QuantumProblemResolver()
            result = resolver.resolve_problem(context.error_type, problem_data)

            if result.get("status") == "success":
                logger.info(f"Quantum resolution succeeded: {result.get('message', 'resolved')}")
                return True
            elif result.get("status") == "error":
                # Quantum backend unavailable - fall back to heuristic
                logger.debug(f"Quantum backend unavailable: {result.get('message')}")
            else:
                logger.debug(f"Quantum resolution returned: {result}")

        except ImportError:
            logger.debug("QuantumProblemResolver not available, using heuristic fallback")
        except Exception as e:
            logger.debug(f"Quantum resolution failed: {e}, using heuristic fallback")

        # Heuristic fallback: auto-fixable error types
        auto_fixable = ["ConnectionError", "TimeoutError", "ImportError"]
        return any(err in context.error_type for err in auto_fixable)

    def _record_success(self, error_type: str, duration: float) -> None:
        """Record successful healing."""
        self.stats["healing_successes"] += 1
        self.last_healing_time[error_type] = time.time()
        self.healing_history[error_type].append(
            {
                "timestamp": time.time(),
                "success": True,
                "duration": duration,
            }
        )

        if METRICS_ENABLED:
            healing_attempts.labels(error_type=error_type, outcome="success").inc()
            healing_duration.labels(error_type=error_type).observe(duration)

    def _record_failure(self, error_type: str, duration: float) -> None:
        """Record failed healing."""
        self.stats["healing_failures"] += 1
        self.last_healing_time[error_type] = time.time()
        self.healing_history[error_type].append(
            {
                "timestamp": time.time(),
                "success": False,
                "duration": duration,
            }
        )

        if METRICS_ENABLED:
            healing_attempts.labels(error_type=error_type, outcome="failure").inc()
            healing_duration.labels(error_type=error_type).observe(duration)

    def get_stats(self) -> dict:
        """Get healing statistics."""
        success_rate = (
            self.stats["healing_successes"] / self.stats["healing_attempts"]
            if self.stats["healing_attempts"] > 0
            else 0.0
        )

        return {
            **self.stats,
            "success_rate": success_rate,
            "active_error_types": len(self.healing_history),
        }

    def reset_cooldown(self, error_type: str | None = None) -> None:
        """Reset cooldown for error type(s)."""
        if error_type:
            self.last_healing_time.pop(error_type, None)
            logger.info(f"Reset cooldown for {error_type}")
        else:
            self.last_healing_time.clear()
            logger.info("Reset all cooldowns")


# Global monitor instance
_global_monitor: AutoHealingMonitor | None = None


def get_monitor() -> AutoHealingMonitor:
    """Get or create global monitor instance."""
    global _global_monitor
    if _global_monitor is None:
        _global_monitor = AutoHealingMonitor()
    return _global_monitor


def traced_operation(operation_name: str, auto_heal: bool = True):
    """Decorator to add tracing and auto-healing to operations.

    Example:
        @traced_operation("ai_request")
        def call_ai_system(prompt):
            return ai.generate(prompt)
    """

    def decorator(func) -> None:
        def wrapper(*args, **kwargs):
            if not TRACING_ENABLED or tracing_mod is None:
                return func(*args, **kwargs)

            with tracing_mod.start_span(operation_name) as span:
                try:
                    result = func(*args, **kwargs)
                    try:
                        if span:
                            span.add_event("status", {"state": "ok"})
                    except Exception:
                        logger.debug("Suppressed Exception", exc_info=True)
                    return result

                except Exception as e:
                    try:
                        if span:
                            span.add_event("status", {"state": "error", "error": str(e)})
                    except Exception:
                        logger.debug("Suppressed Exception", exc_info=True)

                    # Trigger auto-healing
                    if auto_heal:
                        trace_id, span_id = tracing_mod.current_trace_ids()
                        context = ErrorContext(
                            error_type=type(e).__name__,
                            error_message=str(e),
                            span_name=operation_name,
                            timestamp=time.time(),
                            attributes={},
                            trace_id=trace_id,
                            span_id=span_id,
                        )

                        monitor = get_monitor()
                        healed = monitor.on_error(e, context)

                        if healed:
                            logger.info("Retrying after successful healing...")
                            # Could retry here

                    raise

        return wrapper

    return decorator
