"""
Tests for AIIntermediary — cognitive event creation, routing, module registration,
security layer, tagging, and emergent behavior detection.
All Ollama/network calls are mocked.
"""

import asyncio
import pytest
from unittest.mock import MagicMock, AsyncMock, patch


# ── Patch fixture ─────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def patch_heavy_deps():
    """Prevent KILOOllamaHub and conversation_manager from hitting the network."""
    fake_hub = MagicMock()
    fake_hub.initialize = AsyncMock()
    fake_hub.intelligent_chat = AsyncMock(return_value="mocked response")

    fake_convo = MagicMock()
    fake_convo.add_message = MagicMock()
    fake_convo.get_history = MagicMock(return_value=[])

    with patch("src.ai.ai_intermediary.KILOOllamaHub", return_value=fake_hub), \
         patch("src.ai.ai_intermediary.conversation_manager", fake_convo):
        yield fake_hub, fake_convo


@pytest.fixture
def intermediary():
    from src.ai.ai_intermediary import AIIntermediary
    ai = AIIntermediary.__new__(AIIntermediary)
    ai.ollama_hub = MagicMock()
    ai.ollama_hub.initialize = AsyncMock()
    ai.ollama_hub.intelligent_chat = AsyncMock(return_value="test response")
    ai.translator = MagicMock()
    ai.feedback_engine = MagicMock()
    ai.memory_core = MagicMock()
    ai.memory_core.store_context = AsyncMock()
    ai.memory_core.retrieve_context = AsyncMock(return_value=[])
    ai.event_bus = asyncio.Queue()
    ai.registered_modules = {}
    ai.security_layer = MagicMock()
    ai.security_layer.validate_input = AsyncMock(return_value=True)
    ai.security_layer.authenticate = AsyncMock(return_value=True)
    ai.logger = MagicMock()
    ai.meta_learning_enabled = True
    ai.emergent_behavior_detection = True
    ai.protocol_evolution_enabled = True
    return ai


@pytest.fixture
def cognitive_event():
    from src.ai.ai_intermediary import CognitiveEvent, CognitiveParadigm
    return CognitiveEvent(
        source="test",
        paradigm=CognitiveParadigm.NATURAL_LANGUAGE,
        payload="hello world",
        context={"conversation_id": "test-123"},
    )


# ── CognitiveParadigm enum ────────────────────────────────────────────────────

def test_cognitive_paradigm_values():
    from src.ai.ai_intermediary import CognitiveParadigm
    assert CognitiveParadigm.NATURAL_LANGUAGE.value == "natural_language"
    assert CognitiveParadigm.SYMBOLIC_LOGIC.value == "symbolic_logic"
    assert CognitiveParadigm.QUANTUM_NOTATION.value == "quantum_notation"


# ── CognitiveEvent dataclass ──────────────────────────────────────────────────

def test_cognitive_event_defaults():
    from src.ai.ai_intermediary import CognitiveEvent, CognitiveParadigm
    event = CognitiveEvent(
        source="user",
        paradigm=CognitiveParadigm.NATURAL_LANGUAGE,
        payload="test",
        context={},
    )
    assert event.source == "user"
    assert event.recursion_depth == 0
    assert isinstance(event.tags, list)
    assert isinstance(event.meta_index, dict)


def test_cognitive_event_tags_are_independent():
    """Each event should get its own tags list, not share a reference."""
    from src.ai.ai_intermediary import CognitiveEvent, CognitiveParadigm
    e1 = CognitiveEvent(source="a", paradigm=CognitiveParadigm.NATURAL_LANGUAGE, payload="x", context={})
    e2 = CognitiveEvent(source="b", paradigm=CognitiveParadigm.NATURAL_LANGUAGE, payload="y", context={})
    e1.tags.append("unique")
    assert "unique" not in e2.tags


# ── receive() ────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_receive_creates_cognitive_event(intermediary):
    from src.ai.ai_intermediary import CognitiveParadigm
    event = await intermediary.receive(
        input_data="hello",
        context={"conversation_id": "c1"},
        source="user",
        paradigm=CognitiveParadigm.NATURAL_LANGUAGE,
    )
    assert event.source == "user"
    assert event.payload == "hello"
    assert "input" in event.tags


@pytest.mark.asyncio
async def test_receive_stores_to_memory(intermediary):
    from src.ai.ai_intermediary import CognitiveParadigm
    await intermediary.receive("data", context={"conversation_id": "c1"}, source="agent")
    intermediary.memory_core.store_context.assert_awaited_once()


@pytest.mark.asyncio
async def test_receive_raises_on_security_failure(intermediary):
    from src.ai.ai_intermediary import CognitiveParadigm, SecurityError
    intermediary.security_layer.validate_input = AsyncMock(return_value=False)
    with pytest.raises(SecurityError):
        await intermediary.receive("bad input", context={}, source="unknown")


@pytest.mark.asyncio
async def test_receive_adds_to_event_bus(intermediary):
    from src.ai.ai_intermediary import CognitiveParadigm
    assert intermediary.event_bus.empty()
    await intermediary.receive("msg", context={"conversation_id": "c2"}, source="user")
    assert not intermediary.event_bus.empty()


# ── register_module() ─────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_register_module_stores_entry(intermediary):
    from src.ai.ai_intermediary import CognitiveParadigm
    fake_module = MagicMock()
    await intermediary.register_module("test_mod", fake_module, CognitiveParadigm.SYMBOLIC_LOGIC)
    assert "test_mod" in intermediary.registered_modules
    assert intermediary.registered_modules["test_mod"]["paradigm"] == CognitiveParadigm.SYMBOLIC_LOGIC


@pytest.mark.asyncio
async def test_register_module_analyzes_capabilities(intermediary):
    from src.ai.ai_intermediary import CognitiveParadigm
    fake_module = MagicMock()
    fake_module.process = AsyncMock(return_value="ok")
    await intermediary.register_module("mod_with_process", fake_module, CognitiveParadigm.NATURAL_LANGUAGE)
    caps = intermediary.registered_modules["mod_with_process"]["capabilities"]
    assert "process" in caps["methods"]


# ── route() ──────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_route_raises_for_unregistered_module(intermediary, cognitive_event):
    from src.ai.ai_intermediary import ModuleNotFoundError
    with pytest.raises(ModuleNotFoundError):
        await intermediary.route("nonexistent", cognitive_event)


@pytest.mark.asyncio
async def test_route_translates_and_executes(intermediary, cognitive_event):
    from src.ai.ai_intermediary import CognitiveParadigm
    fake_module = MagicMock()
    fake_module.process = AsyncMock(return_value="executed result")
    await intermediary.register_module("target", fake_module, CognitiveParadigm.SYMBOLIC_LOGIC)

    intermediary.translator.translate = AsyncMock(return_value="translated payload")

    result_event = await intermediary.route("target", cognitive_event)
    assert "routed" in result_event.tags
    assert "target:target" in result_event.tags


@pytest.mark.asyncio
async def test_route_marks_error_tag_on_exception(intermediary, cognitive_event):
    from src.ai.ai_intermediary import CognitiveParadigm
    broken_module = MagicMock()
    broken_module.process = AsyncMock(side_effect=RuntimeError("boom"))
    await intermediary.register_module("broken", broken_module, CognitiveParadigm.NATURAL_LANGUAGE)
    intermediary.translator.translate = AsyncMock(return_value=cognitive_event.payload)

    result_event = await intermediary.route("broken", cognitive_event)
    assert "error" in result_event.tags


# ── tag() ─────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_tag_appends_symbol(intermediary, cognitive_event):
    await intermediary.tag(cognitive_event, "important")
    assert "important" in cognitive_event.tags


@pytest.mark.asyncio
async def test_tag_records_timestamp_in_meta(intermediary, cognitive_event):
    await intermediary.tag(cognitive_event, "flagged")
    assert "tag_flagged" in cognitive_event.meta_index


# ── authenticate() ────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_authenticate_delegates_to_security_layer(intermediary):
    result = await intermediary.authenticate("agent_001", "read")
    intermediary.security_layer.authenticate.assert_awaited_once_with("agent_001", "read")
    assert result is True


# ── emergent behavior detection ───────────────────────────────────────────────

@pytest.mark.asyncio
async def test_emergent_recursion_tag_added_at_depth_6(intermediary, cognitive_event):
    cognitive_event.recursion_depth = 6
    await intermediary._detect_emergent_behavior(cognitive_event)
    assert "emergent_recursion" in cognitive_event.tags


@pytest.mark.asyncio
async def test_emergent_complexity_tag_added_at_11_tags(intermediary, cognitive_event):
    cognitive_event.tags = [f"tag_{i}" for i in range(11)]
    await intermediary._detect_emergent_behavior(cognitive_event)
    assert "emergent_complexity" in cognitive_event.tags


@pytest.mark.asyncio
async def test_no_emergent_tags_for_normal_event(intermediary, cognitive_event):
    cognitive_event.recursion_depth = 2
    cognitive_event.tags = ["input"]
    await intermediary._detect_emergent_behavior(cognitive_event)
    assert "emergent_recursion" not in cognitive_event.tags
    assert "emergent_complexity" not in cognitive_event.tags


# ── process_with_ollama() ─────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_process_with_ollama_returns_response_event(intermediary, cognitive_event):
    from src.ai.ai_intermediary import CognitiveParadigm
    result = await intermediary.process_with_ollama(cognitive_event)
    assert result.source == "ollama"
    assert "ollama_processed" in result.tags
    assert result.payload == "test response"


@pytest.mark.asyncio
async def test_process_with_ollama_translates_non_natural_language(intermediary, cognitive_event):
    from src.ai.ai_intermediary import CognitiveParadigm
    cognitive_event.paradigm = CognitiveParadigm.SYMBOLIC_LOGIC
    intermediary.translator.translate = AsyncMock(return_value="translated nl text")
    await intermediary.process_with_ollama(cognitive_event)
    intermediary.translator.translate.assert_awaited_once()
