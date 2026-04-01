"""
Thin wrapper to invoke the src/tools/search_omnitags utility when imported
from the scripts namespace (used by integration tests).
"""

from pathlib import Path
from typing import Any, List

from src.tools.search_omnitags import main, search_omnitags

__all__ = ["main", "search_omnitags"]


def search_omnitags_wrapper(root: Path, **filters: Any) -> List[Any]:
    """Compatibility wrapper for tests expecting search_omnitags callable."""
    return search_omnitags(root, **filters)


if __name__ == "__main__":
    main()
