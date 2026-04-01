"""Tests for src/utils/error_handling.py - Error handling decorator with retries."""

import pytest
from src.utils.error_handling import error_stats, with_error_handling


class TestWithErrorHandlingSync:
    """Tests for sync function error handling."""

    def setup_method(self):
        """Clear error stats before each test."""
        error_stats.clear()

    def test_successful_sync_function(self):
        """Test decorator with successful sync function."""

        @with_error_handling()
        def success_func():
            return {"result": "ok"}

        result = success_func()
        assert result == {"result": "ok"}

    def test_sync_function_returns_default_on_failure(self):
        """Test sync function returns default response on failure."""

        @with_error_handling()
        def fail_func():
            raise ValueError("test error")

        result = fail_func()
        assert result["success"] is False
        assert "error" in result
        assert "test error" in result["error"]

    def test_sync_function_retries_before_failing(self):
        """Test sync function retries specified number of times."""
        attempts = []

        @with_error_handling(retries=2)
        def count_attempts():
            attempts.append(1)
            raise RuntimeError("fail")

        result = count_attempts()
        # Should have tried 3 times (initial + 2 retries)
        assert len(attempts) == 3
        assert result["success"] is False

    def test_sync_function_succeeds_on_retry(self):
        """Test sync function succeeds on retry attempt."""
        attempts = []

        @with_error_handling(retries=3)
        def eventually_succeeds():
            attempts.append(1)
            if len(attempts) < 3:
                raise RuntimeError("not yet")
            return {"worked": True}

        result = eventually_succeeds()
        assert result == {"worked": True}
        assert len(attempts) == 3

    def test_custom_default_response(self):
        """Test custom default response on failure."""

        @with_error_handling(default_response={"status": "error", "code": 500})
        def fail_with_custom():
            raise Exception("boom")

        result = fail_with_custom()
        assert result["status"] == "error"
        assert result["code"] == 500
        assert "error" in result
        assert "boom" in result["error"]

    def test_error_stats_tracking(self):
        """Test error statistics are tracked."""

        @with_error_handling(retries=0)
        def tracked_error():
            raise ValueError("tracked")

        tracked_error()
        assert "tracked_error" in error_stats
        assert error_stats["tracked_error"] == 1

        tracked_error()
        assert error_stats["tracked_error"] == 2

    def test_preserves_function_name(self):
        """Test decorator preserves wrapped function name."""

        @with_error_handling()
        def my_named_func():
            return True

        assert my_named_func.__name__ == "my_named_func"

    def test_zero_retries(self):
        """Test with zero retries (fails immediately)."""

        @with_error_handling(retries=0)
        def no_retry():
            raise RuntimeError("no retry")

        result = no_retry()
        assert result["success"] is False


class TestWithErrorHandlingAsync:
    """Tests for async function error handling."""

    def setup_method(self):
        """Clear error stats before each test."""
        error_stats.clear()

    @pytest.mark.asyncio
    async def test_successful_async_function(self):
        """Test decorator with successful async function."""

        @with_error_handling()
        async def async_success():
            return {"async": "ok"}

        result = await async_success()
        assert result == {"async": "ok"}

    @pytest.mark.asyncio
    async def test_async_function_returns_default_on_failure(self):
        """Test async function returns default on failure."""

        @with_error_handling()
        async def async_fail():
            raise ValueError("async error")

        result = await async_fail()
        assert result["success"] is False
        assert "async error" in result["error"]

    @pytest.mark.asyncio
    async def test_async_function_retries(self):
        """Test async function retries before failing."""
        attempts = []

        @with_error_handling(retries=2)
        async def async_count():
            attempts.append(1)
            raise RuntimeError("async fail")

        result = await async_count()
        assert len(attempts) == 3
        assert result["success"] is False

    @pytest.mark.asyncio
    async def test_async_succeeds_on_retry(self):
        """Test async function succeeds on retry."""
        attempts = []

        @with_error_handling(retries=2)
        async def async_eventually():
            attempts.append(1)
            if len(attempts) < 2:
                raise RuntimeError("not yet")
            return {"async_worked": True}

        result = await async_eventually()
        assert result == {"async_worked": True}

    @pytest.mark.asyncio
    async def test_async_error_stats(self):
        """Test async error stats tracking."""

        @with_error_handling(retries=0)
        async def async_tracked():
            raise ValueError("tracked async")

        await async_tracked()
        assert "async_tracked" in error_stats
        assert error_stats["async_tracked"] == 1

    @pytest.mark.asyncio
    async def test_async_preserves_name(self):
        """Test async decorator preserves function name."""

        @with_error_handling()
        async def my_async_func():
            return True

        assert my_async_func.__name__ == "my_async_func"


class TestDecoratorDetection:
    """Test decorator correctly detects sync vs async functions."""

    def test_sync_function_detection(self):
        """Test sync function is wrapped with sync wrapper."""

        @with_error_handling()
        def sync_func():
            return "sync"

        # Should be callable without await
        result = sync_func()
        assert result == "sync"

    @pytest.mark.asyncio
    async def test_async_function_detection(self):
        """Test async function is wrapped with async wrapper."""

        @with_error_handling()
        async def async_func():
            return "async"

        # Should require await
        result = await async_func()
        assert result == "async"


class TestErrorStatsModule:
    """Test module-level error_stats dict."""

    def setup_method(self):
        """Clear error stats before each test."""
        error_stats.clear()

    def test_error_stats_starts_empty(self):
        """Test error_stats dict starts empty after clear."""
        assert len(error_stats) == 0

    def test_multiple_functions_tracked(self):
        """Test multiple function errors are tracked separately."""

        @with_error_handling(retries=0)
        def func_a():
            raise ValueError("a")

        @with_error_handling(retries=0)
        def func_b():
            raise ValueError("b")

        func_a()
        func_b()
        func_a()

        assert error_stats["func_a"] == 2
        assert error_stats["func_b"] == 1


class TestEdgeCases:
    """Edge case tests."""

    def setup_method(self):
        """Clear error stats before each test."""
        error_stats.clear()

    def test_function_with_args(self):
        """Test decorated function with arguments."""

        @with_error_handling()
        def add(a, b):
            return a + b

        assert add(2, 3) == 5

    def test_function_with_kwargs(self):
        """Test decorated function with keyword arguments."""

        @with_error_handling()
        def greet(name="World"):
            return f"Hello, {name}!"

        assert greet(name="Test") == "Hello, Test!"

    def test_function_returning_none(self):
        """Test decorated function can return None."""

        @with_error_handling()
        def returns_none():
            return None

        result = returns_none()
        assert result is None

    def test_exception_type_preserved_in_message(self):
        """Test exception message is preserved."""

        @with_error_handling(retries=0)
        def specific_error():
            raise TypeError("type error message")

        result = specific_error()
        assert "type error message" in result["error"]

    @pytest.mark.asyncio
    async def test_async_with_args(self):
        """Test async decorated function with arguments."""

        @with_error_handling()
        async def async_add(a, b):
            return a + b

        result = await async_add(5, 7)
        assert result == 12

    def test_nested_decorators(self):
        """Test with_error_handling can be nested with other decorators."""

        def log_call(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)

            return wrapper

        import functools

        @with_error_handling()
        @log_call
        def nested_func():
            return "nested"

        result = nested_func()
        assert result == "nested"

    def test_error_during_retries_all_different(self):
        """Test different errors during retries - last error is captured."""
        attempts = []

        @with_error_handling(retries=2)
        def different_errors():
            attempts.append(1)
            if len(attempts) == 1:
                raise ValueError("first error")
            elif len(attempts) == 2:
                raise TypeError("second error")
            else:
                raise RuntimeError("third error")

        result = different_errors()
        assert "third error" in result["error"]
