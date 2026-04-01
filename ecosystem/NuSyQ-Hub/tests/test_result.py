"""Tests for src/core/result.py - Unified Result Type.

Coverage targets:
- Result dataclass creation
- _OkDescriptor (class access + instance access)
- Result.ok() class method (via descriptor)
- Result.fail() class method
- Result.to_dict() serialization
- Result.__bool__() boolean context
- Result.unwrap() get data or raise
- Result.unwrap_or() get data or default
- Result.value property
- Ok and Fail convenience aliases
"""

import pytest
from datetime import datetime

from src.core.result import Result, Ok, Fail


class TestResultCreation:
    """Tests for creating Result instances."""

    def test_success_result_defaults(self):
        """Create success result with defaults."""
        result = Result(success=True)

        assert result.success is True
        assert result.data is None
        assert result.error is None
        assert result.code is None
        assert result.message is None
        assert isinstance(result.timestamp, datetime)
        assert result.meta == {}

    def test_success_result_with_data(self):
        """Create success result with data."""
        result = Result(success=True, data={"id": 123, "name": "test"})

        assert result.success is True
        assert result.data == {"id": 123, "name": "test"}

    def test_failure_result_with_error(self):
        """Create failure result with error details."""
        result = Result(
            success=False,
            error="Connection failed",
            code="CONN_ERR",
            message="Unable to connect",
        )

        assert result.success is False
        assert result.error == "Connection failed"
        assert result.code == "CONN_ERR"
        assert result.message == "Unable to connect"

    def test_result_with_meta(self):
        """Create result with metadata."""
        result = Result(success=True, meta={"source": "test", "retry_count": 3})

        assert result.meta == {"source": "test", "retry_count": 3}


class TestResultOkDescriptor:
    """Tests for _OkDescriptor supporting Result.ok() and result.ok."""

    def test_class_access_ok_no_args(self):
        """Result.ok() with no arguments creates success result."""
        result = Result.ok()

        assert result.success is True
        assert result.data is None
        assert result.message is None

    def test_class_access_ok_with_data(self):
        """Result.ok(data=...) creates success result with data."""
        result = Result.ok(data={"key": "value"})

        assert result.success is True
        assert result.data == {"key": "value"}

    def test_class_access_ok_with_message(self):
        """Result.ok(message=...) creates success result with message."""
        result = Result.ok(data=[1, 2, 3], message="Items retrieved")

        assert result.success is True
        assert result.data == [1, 2, 3]
        assert result.message == "Items retrieved"

    def test_class_access_ok_with_meta_kwargs(self):
        """Result.ok(**meta) passes kwargs as metadata."""
        result = Result.ok(data="test", source="api", version=2)

        assert result.success is True
        assert result.data == "test"
        assert result.meta == {"source": "api", "version": 2}

    def test_instance_access_ok_is_bool(self):
        """result.ok on instance returns boolean success."""
        success_result = Result(success=True, data="data")
        failure_result = Result(success=False, error="err")

        assert success_result.ok is True
        assert failure_result.ok is False


class TestResultFail:
    """Tests for Result.fail() class method."""

    def test_fail_basic(self):
        """Result.fail() creates failure result."""
        result = Result.fail("Something went wrong")

        assert result.success is False
        assert result.error == "Something went wrong"
        assert result.code is None
        assert result.data is None

    def test_fail_with_code(self):
        """Result.fail() with error code."""
        result = Result.fail("Not found", code="NOT_FOUND")

        assert result.success is False
        assert result.error == "Not found"
        assert result.code == "NOT_FOUND"

    def test_fail_with_data(self):
        """Result.fail() can include partial data."""
        result = Result.fail("Partial failure", data={"processed": 50, "failed": 10})

        assert result.success is False
        assert result.data == {"processed": 50, "failed": 10}

    def test_fail_with_meta_kwargs(self):
        """Result.fail() passes kwargs as metadata."""
        result = Result.fail("Error", retryable=True, attempts=3)

        assert result.success is False
        assert result.meta == {"retryable": True, "attempts": 3}


class TestResultToDict:
    """Tests for Result.to_dict() serialization."""

    def test_to_dict_success_minimal(self):
        """to_dict for minimal success result."""
        result = Result(success=True)
        d = result.to_dict()

        assert d["success"] is True
        assert "timestamp" in d
        # These should not be present when None/empty
        assert "data" not in d
        assert "error" not in d
        assert "code" not in d
        assert "message" not in d
        assert "meta" not in d

    def test_to_dict_success_full(self):
        """to_dict for success result with all fields."""
        result = Result(
            success=True,
            data={"id": 1},
            message="Created",
            meta={"version": "1.0"},
        )
        d = result.to_dict()

        assert d["success"] is True
        assert d["data"] == {"id": 1}
        assert d["message"] == "Created"
        assert d["meta"] == {"version": "1.0"}

    def test_to_dict_failure(self):
        """to_dict for failure result."""
        result = Result(
            success=False,
            error="Failed to process",
            code="PROC_ERR",
        )
        d = result.to_dict()

        assert d["success"] is False
        assert d["error"] == "Failed to process"
        assert d["code"] == "PROC_ERR"

    def test_to_dict_timestamp_iso_format(self):
        """to_dict formats timestamp as ISO string."""
        result = Result(success=True)
        d = result.to_dict()

        # Should be valid ISO format
        parsed = datetime.fromisoformat(d["timestamp"])
        assert isinstance(parsed, datetime)


class TestResultBool:
    """Tests for Result.__bool__() boolean context."""

    def test_bool_success_is_true(self):
        """Success result is truthy."""
        result = Result(success=True)

        assert bool(result) is True
        assert result  # Direct boolean context

    def test_bool_failure_is_false(self):
        """Failure result is falsy."""
        result = Result(success=False, error="err")

        assert bool(result) is False
        assert not result  # Direct boolean context

    def test_if_statement_with_result(self):
        """Result works in if statements."""
        success = Result.ok(data="test")
        failure = Result.fail("error")

        if success:
            passed_success = True
        else:
            passed_success = False

        if failure:
            passed_failure = True
        else:
            passed_failure = False

        assert passed_success is True
        assert passed_failure is False


class TestResultUnwrap:
    """Tests for Result.unwrap() method."""

    def test_unwrap_success_returns_data(self):
        """unwrap() returns data for success result."""
        result = Result.ok(data={"value": 42})

        assert result.unwrap() == {"value": 42}

    def test_unwrap_success_none_data(self):
        """unwrap() returns None for success with no data."""
        result = Result.ok()

        assert result.unwrap() is None

    def test_unwrap_failure_raises(self):
        """unwrap() raises ValueError for failure result."""
        result = Result.fail("Connection refused", code="CONN_ERR")

        with pytest.raises(ValueError) as exc_info:
            result.unwrap()

        assert "Connection refused" in str(exc_info.value)
        assert "CONN_ERR" in str(exc_info.value)


class TestResultUnwrapOr:
    """Tests for Result.unwrap_or() method."""

    def test_unwrap_or_success_returns_data(self):
        """unwrap_or() returns data for success result."""
        result = Result.ok(data="actual_value")

        assert result.unwrap_or("default") == "actual_value"

    def test_unwrap_or_failure_returns_default(self):
        """unwrap_or() returns default for failure result."""
        result = Result.fail("error")

        assert result.unwrap_or("default") == "default"

    def test_unwrap_or_with_none_data(self):
        """unwrap_or() returns None for success with None data."""
        result = Result.ok()  # data is None

        # This should return None (the actual data), not the default
        # Actually per the implementation, it returns self.data if success
        assert result.unwrap_or("default") is None

    def test_unwrap_or_various_types(self):
        """unwrap_or() works with various default types."""
        failure = Result.fail("err")

        assert failure.unwrap_or(0) == 0
        assert failure.unwrap_or([]) == []
        assert failure.unwrap_or({}) == {}


class TestResultValueProperty:
    """Tests for Result.value property."""

    def test_value_returns_data(self):
        """Value property returns data."""
        result = Result.ok(data={"key": "value"})

        assert result.value == {"key": "value"}

    def test_value_none_when_no_data(self):
        """Value property returns None when no data."""
        result = Result(success=True)

        assert result.value is None

    def test_value_available_on_failure(self):
        """Value property works on failure (may have partial data)."""
        result = Result.fail("error", data={"partial": True})

        assert result.value == {"partial": True}


class TestConvenienceAliases:
    """Tests for Ok and Fail convenience aliases."""

    def test_ok_alias(self):
        """Ok alias works like Result.ok()."""
        result = Ok(data="test", message="success")

        assert result.success is True
        assert result.data == "test"
        assert result.message == "success"

    def test_fail_alias(self):
        """Fail alias works like Result.fail()."""
        result = Fail("error message", code="ERR_CODE")

        assert result.success is False
        assert result.error == "error message"
        assert result.code == "ERR_CODE"


class TestResultGenericTyping:
    """Tests for Result generic type behavior."""

    def test_string_data(self):
        """Result with string data."""
        result: Result[str] = Result.ok(data="hello")
        assert result.data == "hello"

    def test_list_data(self):
        """Result with list data."""
        result: Result[list] = Result.ok(data=[1, 2, 3])
        assert result.data == [1, 2, 3]

    def test_dict_data(self):
        """Result with dict data."""
        result: Result[dict] = Result.ok(data={"a": 1})
        assert result.data == {"a": 1}

    def test_complex_nested_data(self):
        """Result with complex nested data."""
        complex_data = {
            "users": [
                {"id": 1, "name": "Alice"},
                {"id": 2, "name": "Bob"},
            ],
            "total": 2,
        }
        result = Result.ok(data=complex_data)
        assert result.data["users"][0]["name"] == "Alice"
