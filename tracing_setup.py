"""
Tracing setup for ChatDev - Simple no-op implementation
When OpenTelemetry is not available, this provides stub methods
"""

from contextlib import contextmanager
from typing import Any, Optional, Dict


def initialize_tracing(service_name: str = "chatdev") -> Any:
    """Initialize tracing (no-op if OTEL not available)"""
    return NoOpTracer()


def instrument_requests() -> None:
    """Instrument requests library (no-op)"""
    pass


def instrument_flask(app: Any) -> None:
    """Instrument Flask app (no-op)"""
    pass


@contextmanager
def start_span(name: str, attributes: Optional[Dict[str, Any]] = None):
    """Start a tracing span (no-op context manager)"""
    try:
        yield
    finally:
        pass


class NoOpTracer:
    """No-op tracer when OpenTelemetry is not installed"""
    
    def start_span(self, name: str, attributes: Optional[Dict[str, Any]] = None):
        """Start a span (no-op)"""
        return start_span(name, attributes)
    
    def add_event(self, name: str, attributes: Optional[Dict[str, Any]] = None) -> None:
        """Add event to span (no-op)"""
        pass
    
    def set_attribute(self, key: str, value: Any) -> None:
        """Set span attribute (no-op)"""
        pass
