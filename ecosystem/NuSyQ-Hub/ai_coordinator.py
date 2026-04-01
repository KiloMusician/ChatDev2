from typing import Any


class AICoordinator:
    """Minimal AI Coordinator shim to satisfy test expectations.

    Behavior:
    - providers stored in dict: name -> capabilities
    - register_provider(name, capabilities): stores provider
    - route_task(task): task is a tuple (type, content, priority)
      selects a provider that matches the task type and has the highest
      numeric 'priority' in its capabilities. If none match, raises.
    """

    def __init__(self):
        self.providers: dict[str, dict[str, Any]] = {}

    def register_provider(self, name: str, capabilities: dict[str, Any]):
        self.providers[name] = capabilities

    def route_task(self, task: tuple[str, Any, int]) -> tuple[str, tuple[str, Any, int]]:
        task_type, content, priority = task
        # Find providers that match by 'type'
        candidates = [(n, c) for n, c in self.providers.items() if c.get("type") == task_type]
        if not candidates:
            raise Exception("No provider available for the given task type.")

        # Select candidate with highest provider-configured priority (numeric)
        candidates.sort(key=lambda nc: int(nc[1].get("priority", 0)), reverse=True)
        chosen_name = candidates[0][0]
        return chosen_name, task
