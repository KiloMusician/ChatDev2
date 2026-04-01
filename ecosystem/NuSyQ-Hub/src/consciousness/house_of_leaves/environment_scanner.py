from typing import Any


class EnvironmentScanner:
    def __init__(self) -> None:
        """Initialize EnvironmentScanner."""
        self.complexity_metrics: dict[str, Any] = {}

    async def scan_repo(self) -> dict[str, int]:
        # Simulate repo scanning with complexity metrics
        self.complexity_metrics = {"file1.py": 5, "file2.py": 3, "file3.py": 7}
        return self.complexity_metrics
