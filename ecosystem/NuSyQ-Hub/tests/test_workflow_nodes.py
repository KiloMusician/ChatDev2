"""Tests for src/workflow/nodes.py — NodeType, NodePort, WorkflowNode subclasses."""


# ---------------------------------------------------------------------------
# NodeType enum
# ---------------------------------------------------------------------------


class TestNodeType:
    """Tests for NodeType enum."""

    def test_has_six_values(self):
        from src.workflow.nodes import NodeType
        assert len(list(NodeType)) == 6

    def test_known_types(self):
        from src.workflow.nodes import NodeType
        names = {n.name for n in NodeType}
        assert names == {"TRIGGER", "ACTION", "CONDITION", "TRANSFORM", "OUTPUT", "AI"}

    def test_values_are_strings(self):
        from src.workflow.nodes import NodeType
        for nt in NodeType:
            assert isinstance(nt.value, str)

    def test_trigger_value(self):
        from src.workflow.nodes import NodeType
        assert NodeType.TRIGGER.value == "trigger"

    def test_ai_value(self):
        from src.workflow.nodes import NodeType
        assert NodeType.AI.value == "ai"


# ---------------------------------------------------------------------------
# NodePort dataclass
# ---------------------------------------------------------------------------


class TestNodePort:
    """Tests for NodePort dataclass."""

    def _make(self, **kwargs):
        from src.workflow.nodes import NodePort
        defaults = {"name": "input_data"}
        defaults.update(kwargs)
        return NodePort(**defaults)

    def test_instantiation(self):
        assert self._make() is not None

    def test_name_stored(self):
        port = self._make(name="my_port")
        assert port.name == "my_port"

    def test_default_type_any(self):
        assert self._make().type == "any"

    def test_default_required_true(self):
        assert self._make().required is True

    def test_default_default_none(self):
        assert self._make().default is None

    def test_default_description_empty(self):
        assert self._make().description == ""

    def test_custom_type(self):
        port = self._make(type="string")
        assert port.type == "string"

    def test_not_required(self):
        port = self._make(required=False)
        assert port.required is False

    def test_with_default(self):
        port = self._make(default=42)
        assert port.default == 42

    def test_to_dict_returns_dict(self):
        d = self._make().to_dict()
        assert isinstance(d, dict)

    def test_to_dict_has_keys(self):
        d = self._make().to_dict()
        for key in ("name", "type", "required", "has_default", "description"):
            assert key in d

    def test_to_dict_has_default_false_when_none(self):
        d = self._make(default=None).to_dict()
        assert d["has_default"] is False

    def test_to_dict_has_default_true_when_set(self):
        d = self._make(default=0).to_dict()
        assert d["has_default"] is True


# ---------------------------------------------------------------------------
# TriggerNode
# ---------------------------------------------------------------------------


class TestTriggerNode:
    """Tests for TriggerNode."""

    def _make(self, **kwargs):
        from src.workflow.nodes import TriggerNode, NodeType
        defaults = {"id": "trig-1", "name": "Start", "node_type": NodeType.TRIGGER}
        defaults.update(kwargs)
        return TriggerNode(**defaults)

    def test_instantiation(self):
        assert self._make() is not None

    def test_node_type_is_trigger(self):
        from src.workflow.nodes import NodeType
        node = self._make()
        assert node.node_type == NodeType.TRIGGER

    def test_default_output_port_created(self):
        node = self._make()
        assert len(node.outputs) == 1
        assert node.outputs[0].name == "trigger_data"

    def test_execute_returns_ok(self):
        from src.workflow.nodes import TriggerNode, NodeType
        node = TriggerNode(id="t1", name="T", node_type=NodeType.TRIGGER)
        result = node.execute({"event": "start"})
        assert result.ok is True

    def test_execute_result_contains_trigger_data(self):
        from src.workflow.nodes import TriggerNode, NodeType
        node = TriggerNode(id="t1", name="T", node_type=NodeType.TRIGGER)
        result = node.execute({"msg": "hello"})
        assert "trigger_data" in result.value

    def test_execute_result_contains_triggered_at(self):
        from src.workflow.nodes import TriggerNode, NodeType
        node = TriggerNode(id="t1", name="T", node_type=NodeType.TRIGGER)
        result = node.execute({})
        assert "triggered_at" in result.value

    def test_to_dict_returns_dict(self):
        node = self._make()
        d = node.to_dict()
        assert isinstance(d, dict)
        assert d["type"] == "trigger"


# ---------------------------------------------------------------------------
# ActionNode
# ---------------------------------------------------------------------------


class TestActionNode:
    """Tests for ActionNode."""

    def _make(self, config=None):
        from src.workflow.nodes import ActionNode, NodeType
        return ActionNode(id="a1", name="Act", node_type=NodeType.ACTION, config=config or {})

    def test_instantiation(self):
        assert self._make() is not None

    def test_node_type_is_action(self):
        from src.workflow.nodes import NodeType
        assert self._make().node_type == NodeType.ACTION

    def test_default_noop_action(self):
        node = self._make()
        result = node.execute({"data": "test"})
        assert result.ok is True
        assert result.value["action"] == "noop"

    def test_noop_passes_input_through(self):
        node = self._make()
        result = node.execute({"key": "value"})
        assert result.value["result"] == {"key": "value"}

    def test_log_action(self):
        node = self._make(config={"action": "log"})
        result = node.execute({"message": "Hello"})
        assert result.ok is True
        assert result.value["result"]["logged"] is True
        assert result.value["result"]["message"] == "Hello"

    def test_transform_action(self):
        node = self._make(config={"action": "transform", "mapping": {"output": "input"}})
        result = node.execute({"input": 42})
        assert result.ok is True
        assert result.value["result"] == {"output": 42}

    def test_transform_missing_source_key_skipped(self):
        node = self._make(config={"action": "transform", "mapping": {"out": "nonexistent"}})
        result = node.execute({"other": 1})
        assert result.ok is True
        assert result.value["result"] == {}

    def test_unknown_action_fails(self):
        node = self._make(config={"action": "explode"})
        result = node.execute({})
        assert result.ok is False

    def test_default_inputs_created(self):
        node = self._make()
        assert len(node.inputs) == 1
        assert node.inputs[0].name == "data"

    def test_default_outputs_created(self):
        node = self._make()
        assert len(node.outputs) == 1
        assert node.outputs[0].name == "result"


# ---------------------------------------------------------------------------
# ConditionNode
# ---------------------------------------------------------------------------


class TestConditionNode:
    """Tests for ConditionNode."""

    def _make(self, config=None):
        from src.workflow.nodes import ConditionNode, NodeType
        return ConditionNode(id="c1", name="Cond", node_type=NodeType.CONDITION, config=config or {})

    def test_instantiation(self):
        assert self._make() is not None

    def test_truthy_true_branch(self):
        node = self._make({"condition": "truthy", "field": "value"})
        result = node.execute({"value": "nonempty"})
        assert result.ok is True
        assert "true" in result.value
        assert result.value["condition_result"] is True

    def test_truthy_false_branch(self):
        node = self._make({"condition": "truthy", "field": "value"})
        result = node.execute({"value": ""})
        assert "false" in result.value
        assert result.value["condition_result"] is False

    def test_equals_match(self):
        node = self._make({"condition": "equals", "field": "status", "expected": "ok"})
        result = node.execute({"status": "ok"})
        assert result.value["condition_result"] is True

    def test_equals_mismatch(self):
        node = self._make({"condition": "equals", "field": "status", "expected": "ok"})
        result = node.execute({"status": "fail"})
        assert result.value["condition_result"] is False

    def test_not_equals(self):
        node = self._make({"condition": "not_equals", "field": "x", "expected": 1})
        result = node.execute({"x": 2})
        assert result.value["condition_result"] is True

    def test_greater_than(self):
        node = self._make({"condition": "greater_than", "field": "n", "expected": 5})
        result = node.execute({"n": 10})
        assert result.value["condition_result"] is True

    def test_less_than(self):
        node = self._make({"condition": "less_than", "field": "n", "expected": 5})
        result = node.execute({"n": 2})
        assert result.value["condition_result"] is True

    def test_contains(self):
        node = self._make({"condition": "contains", "field": "text", "expected": "hello"})
        result = node.execute({"text": "say hello world"})
        assert result.value["condition_result"] is True

    def test_exists_present(self):
        node = self._make({"condition": "exists", "field": "key"})
        result = node.execute({"key": None})  # exists but is None — condition is "value is not None"
        assert result.value["condition_result"] is False

    def test_exists_truly_present(self):
        node = self._make({"condition": "exists", "field": "key"})
        result = node.execute({"key": "something"})
        assert result.value["condition_result"] is True

    def test_default_two_outputs(self):
        node = self._make()
        assert len(node.outputs) == 2
        output_names = {p.name for p in node.outputs}
        assert "true" in output_names
        assert "false" in output_names


# ---------------------------------------------------------------------------
# WorkflowNode.validate_inputs and get_input
# ---------------------------------------------------------------------------


class TestWorkflowNodeHelpers:
    """Tests for WorkflowNode.validate_inputs() and get_input()."""

    def _make_action(self, inputs=None):
        from src.workflow.nodes import ActionNode, NodePort, NodeType
        node = ActionNode(id="a1", name="A", node_type=NodeType.ACTION)
        if inputs is not None:
            node.inputs = inputs
        return node

    def test_validate_inputs_all_present_ok(self):
        from src.workflow.nodes import NodePort
        node = self._make_action(inputs=[NodePort(name="x", required=True)])
        result = node.validate_inputs({"x": 1})
        assert result.ok is True

    def test_validate_inputs_missing_required_fails(self):
        from src.workflow.nodes import NodePort
        node = self._make_action(inputs=[NodePort(name="x", required=True)])
        result = node.validate_inputs({})
        assert result.ok is False

    def test_validate_inputs_optional_missing_ok(self):
        from src.workflow.nodes import NodePort
        node = self._make_action(inputs=[NodePort(name="x", required=False)])
        result = node.validate_inputs({})
        assert result.ok is True

    def test_validate_inputs_with_default_ok(self):
        from src.workflow.nodes import NodePort
        node = self._make_action(inputs=[NodePort(name="x", required=True, default=0)])
        result = node.validate_inputs({})
        assert result.ok is True

    def test_get_input_present(self):
        node = self._make_action()
        # ActionNode has default "data" input port with required=False and no default
        val = node.get_input({"data": 42}, "data")
        assert val == 42

    def test_get_input_missing_returns_port_default(self):
        from src.workflow.nodes import NodePort
        node = self._make_action(inputs=[NodePort(name="x", default=99)])
        val = node.get_input({}, "x")
        assert val == 99

    def test_get_input_unknown_port_returns_none(self):
        node = self._make_action()
        val = node.get_input({"other": 1}, "unknown_port")
        assert val is None

    def test_to_dict_has_required_keys(self):
        node = self._make_action()
        d = node.to_dict()
        for key in ("id", "name", "type", "inputs", "outputs", "config", "position"):
            assert key in d
