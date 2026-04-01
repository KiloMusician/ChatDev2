import asyncio
import functools
import logging
from collections.abc import Callable
from typing import Any

# Setup logging
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)

# Error statistics tracking
error_stats: dict[str, int] = {}


def with_error_handling(
    retries: int = 3,
    default_response: dict[str, Any] | None = None,
) -> Callable[[Callable[..., Any]], Callable[..., dict[str, Any] | Any]]:
    if default_response is None:
        default_response = {"success": False}

    def decorator(func: Callable[..., Any]) -> Callable[..., dict[str, Any] | Any]:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            for attempt in range(retries + 1):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    if attempt < retries:
                        continue
                    logger.exception(
                        "Function '%s' failed after %s attempts: %s",
                        func.__name__,
                        retries,
                        e,
                    )
                    error_stats[func.__name__] = error_stats.get(func.__name__, 0) + 1
                    return {**default_response, "error": str(e)}
            return None

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            for attempt in range(retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt < retries:
                        continue
                    logger.exception(
                        "Function '%s' failed after %s attempts: %s",
                        func.__name__,
                        retries,
                        e,
                    )
                    error_stats[func.__name__] = error_stats.get(func.__name__, 0) + 1
                    return {**default_response, "error": str(e)}
            return None

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


# Example usage:


@with_error_handling(retries=2)
def divide_numbers(a: int, b: int) -> float:
    """Divide two numbers, handling errors gracefully.

    Examples:
    >>> divide_numbers(10, 5)
    2.0
    >>> divide_numbers(10, 0)
    {'success': False, 'error': 'division by zero'}

    """
    return a / b


async def async_divide_numbers(a: int, b: int) -> float:
    """Async version of divide_numbers."""
    return await asyncio.to_thread(divide_numbers, a, b)


# Testing the decorators
if __name__ == "__main__":
    result = divide_numbers(10, 0)

    async def main() -> None:
        await async_divide_numbers(10, 0)

    asyncio.run(main())
