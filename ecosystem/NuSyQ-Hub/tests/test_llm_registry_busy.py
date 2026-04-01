from src.ai.ai_coordinator import LLMRegistry, TaskRequest, TaskType


class DummyProvider:
    def __init__(self):
        self._busy = False

    async def process_task(self, request: TaskRequest):
        return None

    def is_available(self) -> bool:
        return True

    def get_capabilities(self):
        return [TaskType.CONVERSATION]

    def estimate_cost(self, request: TaskRequest) -> float:
        return 0.0

    def is_busy(self) -> bool:
        return self._busy


def test_llm_registry_busy_flags():
    reg = LLMRegistry()
    p = DummyProvider()
    reg.register("dummy", p)

    # initially not busy
    assert not reg.is_busy("dummy")

    reg.set_busy("dummy", True)
    assert reg.is_busy("dummy")

    # available_nonbusy should not include dummy when busy
    assert "dummy" not in reg.available_nonbusy()

    reg.set_busy("dummy", False)
    assert not reg.is_busy("dummy")
    assert "dummy" in reg.available()
