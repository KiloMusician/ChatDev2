"""Unified Result Type for consistent API responses across NuSyQ-Hub.

This eliminates the chaos of:
- Some methods returning dict
- Some returning bool
- Some returning None
- Some returning custom objects

Now everything returns Result[T] which is clear and predictable.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Generic, TypeVar

T = TypeVar("T")


class _OkDescriptor:
    """Descriptor supporting both `Result.ok(...)` and `result.ok`."""

    def __get__(self, obj, owner):
        if obj is None:
            # Class access: behave like the success constructor.
            def _ok(data=None, message: str | None = None, **meta):
                return owner(success=True, data=data, message=message, meta=meta)

            return _ok
        # Instance access: bool-like success alias.
        return obj.success


@dataclass
class Result(Generic[T]):
    """Unified result type for all NuSyQ operations.

    Usage:
        # Success case
        return Result.ok(data={"task_id": "123"}, message="Task created")

        # Failure case
        return Result.fail("Connection refused", code="CONN_ERROR")

        # Checking results
        if result.success:
            print(result.data)
        else:
            print(result.error)
    """

    success: bool
    data: T | None = None
    error: str | None = None
    code: str | None = None  # Error code for programmatic handling
    message: str | None = None  # Human-readable message
    timestamp: datetime = field(default_factory=datetime.now)
    meta: dict[str, Any] = field(default_factory=dict)

    ok = _OkDescriptor()

    @classmethod
    def fail(cls, error: str, code: str | None = None, data: T | None = None, **meta) -> Result[T]:
        """Create a failed result."""
        return cls(success=False, error=error, code=code, data=data, meta=meta)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = {
            "success": self.success,
            "timestamp": self.timestamp.isoformat(),
        }
        if self.data is not None:
            result["data"] = self.data
        if self.error:
            result["error"] = self.error
        if self.code:
            result["code"] = self.code
        if self.message:
            result["message"] = self.message
        if self.meta:
            result["meta"] = self.meta
        return result

    def __bool__(self) -> bool:
        """Allow using Result in boolean context."""
        return self.success

    def unwrap(self) -> T | None:
        """Get data or raise if failed."""
        if not self.success:
            raise ValueError(f"Result failed: {self.error} (code: {self.code})")
        return self.data

    def unwrap_or(self, default: T) -> T | None:
        """Get data or return default if failed."""
        return self.data if self.success else default

    @property
    def value(self) -> T | None:
        return self.data


# Convenience aliases
Ok = Result.ok
Fail = Result.fail
