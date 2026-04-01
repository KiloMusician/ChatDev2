"""Workflow Node System - Base classes for workflow nodes.

Provides the foundation for n8n-style workflow nodes that can:
- Receive input data from previous nodes
- Process/transform data
- Output results to connected nodes
- Integrate with NuSyQ systems (Quest, Background, Search)

OmniTag: [workflow, nodes, processing, automation]
MegaTag: WORKFLOW⨳NODES⦾PROCESSING→∞
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from src.core.result import Fail, Ok, Result

logger = logging.getLogger(__name__)


class NodeType(Enum):
    """Types of workflow nodes."""

    TRIGGER = "trigger"  # Starts workflow execution
    ACTION = "action"  # Performs an operation
    CONDITION = "condition"  # Branches based on condition
    TRANSFORM = "transform"  # Transforms data
    OUTPUT = "output"  # Outputs/exports results
    AI = "ai"  # AI-powered node (uses LLM)


@dataclass
class NodePort:
    """Input/output port for workflow nodes.

    Ports define the data interface for connecting nodes.
    Each port has a name, type, and optional default value.

    Attributes:
        name: Port identifier
        type: Data type ("any", "string", "number", "object", "array", "boolean")
        required: Whether this port must be connected
        default: Default value if not connected
        description: Human-readable description
    """

    name: str
    type: str = "any"
    required: bool = True
    default: Any = None
    description: str = ""

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "type": self.type,
            "required": self.required,
            "has_default": self.default is not None,
            "description": self.description,
        }


@dataclass
class WorkflowNode(ABC):
    """Base class for all workflow nodes.

    Workflow nodes are the building blocks of automation pipelines.
    Each node receives input, performs processing, and produces output.

    Subclasses must implement the execute() method.

    Example:
        class LogNode(WorkflowNode):
            def execute(self, input_data: dict) -> Result[dict]:
                message = input_data.get("message", "No message")
                logger.info(f"LogNode: {message}")
                return Ok({"logged": True, "message": message})
    """

    id: str
    name: str
    node_type: NodeType
    inputs: list[NodePort] = field(default_factory=list)
    outputs: list[NodePort] = field(default_factory=list)
    config: dict = field(default_factory=dict)
    position: tuple[int, int] = field(default=(0, 0))  # For visual editor

    @abstractmethod
    def execute(self, input_data: dict) -> Result[dict]:
        """Execute the node with the given input.

        Args:
            input_data: Data from connected input nodes

        Returns:
            Result[dict]: Output data for connected nodes
        """
        pass

    def validate_inputs(self, input_data: dict) -> Result[bool]:
        """Validate that required inputs are present.

        Args:
            input_data: Input data dictionary

        Returns:
            Result[bool]: Ok(True) if valid, Fail with missing inputs
        """
        missing = []
        for port in self.inputs:
            if port.required and port.name not in input_data and port.default is None:
                missing.append(port.name)

        if missing:
            return Fail(f"Missing required inputs: {', '.join(missing)}", code="MISSING_INPUTS")
        return Ok(True)

    def get_input(self, input_data: dict, port_name: str) -> Any:
        """Get input value with default fallback.

        Args:
            input_data: Input data dictionary
            port_name: Name of the input port

        Returns:
            Input value or default
        """
        if port_name in input_data:
            return input_data[port_name]

        # Find port and return default
        for port in self.inputs:
            if port.name == port_name:
                return port.default

        return None

    def to_dict(self) -> dict:
        """Serialize node to dictionary.

        Returns:
            Node configuration dictionary
        """
        return {
            "id": self.id,
            "name": self.name,
            "type": self.node_type.value,
            "inputs": [p.to_dict() for p in self.inputs],
            "outputs": [p.to_dict() for p in self.outputs],
            "config": self.config,
            "position": self.position,
        }


# ============================================================================
# Built-in Node Types
# ============================================================================


@dataclass
class TriggerNode(WorkflowNode):
    """Trigger node that starts workflow execution.

    Trigger nodes are the entry points for workflows. They can be
    manual (user-triggered) or automated (webhook, schedule, etc.).
    """

    def __post_init__(self):
        """Implement __post_init__."""
        self.node_type = NodeType.TRIGGER
        if not self.outputs:
            self.outputs = [NodePort(name="trigger_data", type="object")]

    def execute(self, input_data: dict) -> Result[dict]:
        """Pass through trigger data to connected nodes."""
        return Ok(
            {
                "trigger_data": input_data,
                "triggered_at": __import__("datetime").datetime.now().isoformat(),
            }
        )


@dataclass
class ActionNode(WorkflowNode):
    """Action node that performs an operation.

    Action nodes execute commands, call APIs, or interact with
    external systems. The specific action is defined in config.
    """

    def __post_init__(self):
        """Implement __post_init__."""
        self.node_type = NodeType.ACTION
        if not self.inputs:
            self.inputs = [NodePort(name="data", type="any", required=False)]
        if not self.outputs:
            self.outputs = [NodePort(name="result", type="any")]

    def execute(self, input_data: dict) -> Result[dict]:
        """Execute the configured action.

        Override this method in subclasses for specific actions.
        """
        action = self.config.get("action", "noop")

        if action == "noop":
            return Ok({"result": input_data, "action": "noop"})

        elif action == "log":
            message = input_data.get("message", str(input_data))
            logger.info(f"ActionNode[{self.name}]: {message}")
            return Ok({"result": {"logged": True, "message": message}})

        elif action == "transform":
            # Simple key mapping
            mapping = self.config.get("mapping", {})
            result = {}
            for target_key, source_key in mapping.items():
                if source_key in input_data:
                    result[target_key] = input_data[source_key]
            return Ok({"result": result})

        else:
            return Fail(f"Unknown action: {action}", code="UNKNOWN_ACTION")


@dataclass
class ConditionNode(WorkflowNode):
    """Condition node that branches workflow based on a condition.

    Evaluates a condition and outputs to either 'true' or 'false'
    output port for branching workflow logic.
    """

    def __post_init__(self):
        """Implement __post_init__."""
        self.node_type = NodeType.CONDITION
        if not self.inputs:
            self.inputs = [NodePort(name="value", type="any")]
        if not self.outputs:
            self.outputs = [
                NodePort(name="true", type="any"),
                NodePort(name="false", type="any"),
            ]

    def execute(self, input_data: dict) -> Result[dict]:
        """Evaluate condition and route to appropriate output."""
        condition = self.config.get("condition", "truthy")
        field = self.config.get("field", "value")
        expected = self.config.get("expected", None)

        value = input_data.get(field)

        if condition == "truthy":
            result = bool(value)
        elif condition == "equals":
            result = value == expected
        elif condition == "not_equals":
            result = value != expected
        elif condition == "greater_than":
            result = value > expected if value is not None else False
        elif condition == "less_than":
            result = value < expected if value is not None else False
        elif condition == "contains":
            result = expected in value if value else False
        elif condition == "exists":
            result = value is not None
        else:
            result = bool(value)

        # Output to appropriate branch
        output_key = "true" if result else "false"
        return Ok(
            {
                output_key: input_data,
                "condition_result": result,
                "evaluated_field": field,
            }
        )


@dataclass
class TransformNode(WorkflowNode):
    """Transform node that modifies data.

    Applies transformations to input data such as mapping,
    filtering, or restructuring.
    """

    def __post_init__(self):
        """Implement __post_init__."""
        self.node_type = NodeType.TRANSFORM
        if not self.inputs:
            self.inputs = [NodePort(name="data", type="any")]
        if not self.outputs:
            self.outputs = [NodePort(name="transformed", type="any")]

    def execute(self, input_data: dict) -> Result[dict]:
        """Apply transformation to input data."""
        transform_type = self.config.get("transform", "passthrough")
        data = input_data.get("data", input_data)

        if transform_type == "passthrough":
            return Ok({"transformed": data})

        elif transform_type == "pick":
            # Pick specific keys
            keys = self.config.get("keys", [])
            result = {k: data.get(k) for k in keys if k in data} if isinstance(data, dict) else data
            return Ok({"transformed": result})

        elif transform_type == "omit":
            # Omit specific keys
            keys = self.config.get("keys", [])
            result = (
                {k: v for k, v in data.items() if k not in keys} if isinstance(data, dict) else data
            )
            return Ok({"transformed": result})

        elif transform_type == "flatten":
            # Flatten nested dict
            result = self._flatten_dict(data) if isinstance(data, dict) else data
            return Ok({"transformed": result})

        else:
            return Ok({"transformed": data})

    def _flatten_dict(self, d: dict, parent_key: str = "", sep: str = ".") -> dict:
        """Flatten a nested dictionary."""
        items: list[tuple[str, Any]] = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(self._flatten_dict(v, new_key, sep).items())
            else:
                items.append((new_key, v))
        return dict(items)


@dataclass
class OutputNode(WorkflowNode):
    """Output node that exports workflow results.

    Collects and formats the final output of a workflow.
    """

    def __post_init__(self):
        """Implement __post_init__."""
        self.node_type = NodeType.OUTPUT
        if not self.inputs:
            # Output nodes should gracefully consume full execution context when
            # a dedicated "data" field is not present.
            self.inputs = [NodePort(name="data", type="any", required=False)]

    def execute(self, input_data: dict) -> Result[dict]:
        """Collect and format output."""
        output_format = self.config.get("format", "raw")
        data = input_data.get("data", input_data)

        if output_format == "raw":
            return Ok({"output": data})

        elif output_format == "json":
            import json

            return Ok({"output": json.dumps(data, default=str)})

        elif output_format == "summary":
            if isinstance(data, dict):
                summary = {k: type(v).__name__ for k, v in data.items()}
            else:
                summary = {"type": type(data).__name__, "value": str(data)[:100]}
            return Ok({"output": summary})

        return Ok({"output": data})


@dataclass
class AINode(WorkflowNode):
    """AI-powered node that uses LLM for processing.

    Integrates with BackgroundTaskOrchestrator for AI operations.
    """

    def __post_init__(self):
        """Implement __post_init__."""
        self.node_type = NodeType.AI
        if not self.inputs:
            self.inputs = [
                NodePort(name="prompt", type="string"),
                NodePort(name="context", type="any", required=False),
            ]
        if not self.outputs:
            self.outputs = [NodePort(name="response", type="string")]

    def execute(self, input_data: dict) -> Result[dict]:
        """Execute AI operation via BackgroundTaskOrchestrator."""
        prompt = input_data.get("prompt", "")
        context = input_data.get("context", {})

        if not prompt:
            return Fail("No prompt provided", code="MISSING_PROMPT")

        try:
            from src.core import nusyq

            # Dispatch to background orchestrator
            task_type = self.config.get("task_type", "code_analysis")
            full_prompt = f"{prompt}\n\nContext: {context}" if context else prompt

            result = nusyq.background.dispatch(
                prompt=full_prompt,
                task_type=task_type,
                priority=self.config.get("priority", "normal"),
            )

            if result.success:
                return Ok(
                    {
                        "response": f"Task dispatched: {result.data}",
                        "task_id": result.data,
                        "status": "queued",
                    }
                )
            else:
                return Fail(result.error, code="AI_DISPATCH_FAILED")

        except Exception as e:
            return Fail(str(e), code="AI_ERROR")


# Node type registry for dynamic instantiation
NODE_TYPES = {
    "trigger": TriggerNode,
    "action": ActionNode,
    "condition": ConditionNode,
    "transform": TransformNode,
    "output": OutputNode,
    "ai": AINode,
}
