class EnvironmentScanner:
    def __init__(self):
        self.complexity_metrics = {}
    async def scan_repo(self) -> Dict[str, int]:
        # Simulate repo scanning with complexity metrics
        self.complexity_metrics = {
            "file1.py": 5,
            "file2.py": 3,
            "file3.py": 7
        }
        return self.complexity_metrics