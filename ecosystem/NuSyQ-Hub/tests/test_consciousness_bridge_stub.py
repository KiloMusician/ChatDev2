from src.system.dictionary.consciousness_bridge import (
    AICoordinator,
    ConsciousnessCore,
    CopilotEnhancementBridge,
)


def test_consciousness_core_heartbeat():
    core = ConsciousnessCore()
    heartbeat = core.heartbeat()
    assert heartbeat["awareness_level"] == "standby"
    assert "timestamp" in heartbeat


def test_copilot_enhancement_bridge_enhance():
    bridge = CopilotEnhancementBridge()
    original = "optimize this"
    enhanced = bridge.enhance(original)
    assert original in bridge.enhancements
    assert "[enhanced by stub bridge]" in enhanced


def test_ai_coordinator_coordinate():
    coord = AICoordinator()
    result = coord.coordinate("test-task")
    assert result["task"] == "test-task"
    assert result["status"] == "queued"
    assert "timestamp" in result
    assert coord.tasks[-1] == "test-task"
