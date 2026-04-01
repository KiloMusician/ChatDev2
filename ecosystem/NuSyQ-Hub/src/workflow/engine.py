"""Workflow Engine - Executes node-based workflows.

Provides workflow execution, loading, and management with:
- Topological sorting for execution order
- Event logging for audit trails
- Integration with QuestExecutor for safe execution

OmniTag: [workflow, engine, execution, automation]
MegaTag: WORKFLOW⨳ENGINE⦾EXECUTION→∞
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from src.core.result import Fail, Ok, Result
from src.workflow.nodes import NODE_TYPES, NodeType, WorkflowNode

logger = logging.getLogger(__name__)


@dataclass
class WorkflowEdge:
    """Connection between two workflow nodes.

    Attributes:
        from_node: Source node ID
        from_port: Source output port name
        to_node: Target node ID
        to_port: Target input port name
    """

    from_node: str
    from_port: str = "output"
    to_node: str = ""
    to_port: str = "input"

    def to_dict(self) -> dict:
        return {
            "from_node": self.from_node,
            "from_port": self.from_port,
            "to_node": self.to_node,
            "to_port": self.to_port,
        }


@dataclass
class Workflow:
    """A complete workflow definition.

    Workflows are directed graphs of nodes connected by edges.
    Execution follows topological order from triggers to outputs.

    Attributes:
        id: Unique workflow identifier
        name: Human-readable name
        description: Workflow description
        nodes: List of workflow nodes
        edges: Connections between nodes
        metadata: Additional workflow metadata
        enabled: Whether workflow is active
    """

    id: str
    name: str
    description: str = ""
    nodes: list[WorkflowNode] = field(default_factory=list)
    edges: list[WorkflowEdge] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
    enabled: bool = True
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def add_node(self, node: WorkflowNode) -> None:
        """Add a node to the workflow."""
        self.nodes.append(node)
        self.updated_at = datetime.now().isoformat()

    def add_edge(
        self, from_node: str, to_node: str, from_port: str = "output", to_port: str = "input"
    ) -> None:
        """Add an edge connecting two nodes."""
        edge = WorkflowEdge(
            from_node=from_node, from_port=from_port, to_node=to_node, to_port=to_port
        )
        self.edges.append(edge)
        self.updated_at = datetime.now().isoformat()

    def get_node(self, node_id: str) -> WorkflowNode | None:
        """Get a node by ID."""
        for node in self.nodes:
            if node.id == node_id:
                return node
        return None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "nodes": [n.to_dict() for n in self.nodes],
            "edges": [e.to_dict() for e in self.edges],
            "metadata": self.metadata,
            "enabled": self.enabled,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


@dataclass
class WorkflowExecution:
    """Tracks the execution of a workflow.

    Attributes:
        workflow_id: ID of the workflow being executed
        execution_id: Unique execution identifier
        status: Current execution status
        started_at: Execution start time
        completed_at: Execution completion time
        results: Results from each node
        errors: Any errors encountered
    """

    workflow_id: str
    execution_id: str
    status: str = "pending"  # pending, running, completed, failed
    started_at: str | None = None
    completed_at: str | None = None
    results: dict = field(default_factory=dict)
    errors: list = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "workflow_id": self.workflow_id,
            "execution_id": self.execution_id,
            "status": self.status,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "results": self.results,
            "errors": self.errors,
        }


class WorkflowEngine:
    """Executes workflows by traversing node graphs.

    The engine manages workflow lifecycle:
    - Loading/saving workflow definitions
    - Registering custom node types
    - Executing workflows with proper ordering
    - Tracking execution history

    Example:
        engine = WorkflowEngine()

        # Register custom node type
        engine.register_node_type("my_node", MyCustomNode)

        # Execute workflow
        result = engine.execute_workflow("my_workflow", {"input": "data"})
    """

    _instance: Optional["WorkflowEngine"] = None
    _initialized: bool = False

    def __new__(cls, workflows_dir: Path | None = None):
        """Singleton pattern for global engine access."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, workflows_dir: Path | None = None):
        """Initialize the workflow engine.

        Args:
            workflows_dir: Directory for workflow definitions
        """
        if self._initialized:
            return

        self.workflows_dir = workflows_dir or Path("config/workflows")
        self.workflows_dir.mkdir(parents=True, exist_ok=True)
        self.executions_file = self.workflows_dir / "_executions.jsonl"

        self._workflows: dict[str, Workflow] = {}
        self._node_registry: dict[str, type[WorkflowNode]] = NODE_TYPES.copy()
        self._executions: list[WorkflowExecution] = self._load_executions()

        self._initialized = True
        logger.info(f"WorkflowEngine initialized with {len(self._node_registry)} node types")

    def _load_executions(self) -> list[WorkflowExecution]:
        """Load persisted executions from disk."""
        if not self.executions_file.exists():
            return []

        executions: list[WorkflowExecution] = []
        for raw_line in self.executions_file.read_text(encoding="utf-8").splitlines():
            if not raw_line.strip():
                continue
            try:
                payload = json.loads(raw_line)
                executions.append(WorkflowExecution(**payload))
            except (json.JSONDecodeError, TypeError, ValueError):
                continue
        return executions

    def _persist_execution(self, execution: WorkflowExecution) -> None:
        """Persist a single execution record as JSONL."""
        try:
            payload = execution.to_dict()
            payload["results"] = self._sanitize_for_json(payload.get("results"))
            payload["errors"] = self._sanitize_for_json(payload.get("errors"))
            with self.executions_file.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(payload, default=str) + "\n")
        except OSError as exc:
            logger.warning(f"Failed to persist workflow execution: {exc}")

    def _sanitize_for_json(self, value: object, seen: set[int] | None = None) -> object:
        """Convert values to a JSON-safe representation and break cycles."""
        if seen is None:
            seen = set()

        value_id = id(value)
        if isinstance(value, (dict, list, tuple, set)):
            if value_id in seen:
                return "<circular>"
            seen.add(value_id)

        if isinstance(value, dict):
            return {str(key): self._sanitize_for_json(val, seen) for key, val in value.items()}
        if isinstance(value, (list, tuple, set)):
            return [self._sanitize_for_json(item, seen) for item in value]
        if isinstance(value, (str, int, float, bool)) or value is None:
            return value
        return str(value)

    def register_node_type(self, name: str, node_class: type) -> None:
        """Register a custom node type.

        Args:
            name: Node type identifier
            node_class: Node class (must inherit from WorkflowNode)
        """
        self._node_registry[name] = node_class
        logger.info(f"Registered workflow node type: {name}")

    def create_workflow(self, id: str, name: str, description: str = "") -> Workflow:
        """Create a new workflow.

        Args:
            id: Unique workflow identifier
            name: Human-readable name
            description: Workflow description

        Returns:
            New Workflow instance
        """
        workflow = Workflow(id=id, name=name, description=description)
        self._workflows[id] = workflow
        return workflow

    def save_workflow(self, workflow: Workflow) -> Result[bool]:
        """Save workflow to disk.

        Args:
            workflow: Workflow to save

        Returns:
            Result[bool]: Ok(True) on success
        """
        try:
            path = self.workflows_dir / f"{workflow.id}.json"
            data = workflow.to_dict()
            path.write_text(json.dumps(data, indent=2))

            self._workflows[workflow.id] = workflow
            logger.info(f"Saved workflow: {workflow.id}")
            return Ok(True)

        except Exception as e:
            return Fail(str(e), code="SAVE_ERROR")

    def load_workflow(self, workflow_id: str) -> Result[Workflow]:
        """Load a workflow from disk.

        Args:
            workflow_id: Workflow identifier

        Returns:
            Result[Workflow]: Loaded workflow or error
        """
        # Check cache first
        if workflow_id in self._workflows:
            return Ok(self._workflows[workflow_id])

        path = self.workflows_dir / f"{workflow_id}.json"
        if not path.exists():
            return Fail(f"Workflow not found: {workflow_id}", code="NOT_FOUND")

        try:
            data = json.loads(path.read_text())

            # Create workflow
            workflow = Workflow(
                id=data["id"],
                name=data["name"],
                description=data.get("description", ""),
                metadata=data.get("metadata", {}),
                enabled=data.get("enabled", True),
                created_at=data.get("created_at", datetime.now().isoformat()),
                updated_at=data.get("updated_at", datetime.now().isoformat()),
            )

            # Load nodes
            for node_data in data.get("nodes", []):
                node_type = node_data.get("type", "action")
                if node_type in self._node_registry:
                    node_class = self._node_registry[node_type]
                    # Create node with basic fields
                    node = node_class(
                        id=node_data["id"],
                        name=node_data["name"],
                        node_type=(
                            NodeType(node_type)
                            if node_type in [e.value for e in NodeType]
                            else NodeType.ACTION
                        ),
                        config=node_data.get("config", {}),
                    )
                    workflow.add_node(node)

            # Load edges
            for edge_data in data.get("edges", []):
                workflow.edges.append(WorkflowEdge(**edge_data))

            self._workflows[workflow_id] = workflow
            return Ok(workflow)

        except Exception as e:
            return Fail(str(e), code="LOAD_ERROR")

    def list_workflows(self) -> list[dict]:
        """List all available workflows.

        Returns:
            List of workflow summaries
        """
        workflows = []

        # From cache
        for wf in self._workflows.values():
            workflows.append(
                {
                    "id": wf.id,
                    "name": wf.name,
                    "description": wf.description,
                    "enabled": wf.enabled,
                    "node_count": len(wf.nodes),
                }
            )

        # From disk (not yet loaded)
        for path in self.workflows_dir.glob("*.json"):
            wf_id = path.stem
            if wf_id not in self._workflows:
                try:
                    data = json.loads(path.read_text())
                    workflows.append(
                        {
                            "id": data["id"],
                            "name": data["name"],
                            "description": data.get("description", ""),
                            "enabled": data.get("enabled", True),
                            "node_count": len(data.get("nodes", [])),
                        }
                    )
                except Exception:
                    logger.debug("Suppressed Exception", exc_info=True)

        return workflows

    def execute_workflow(self, workflow_id: str, initial_data: dict | None = None) -> Result[dict]:
        """Execute a workflow from start to finish.

        Args:
            workflow_id: Workflow to execute
            initial_data: Initial input data

        Returns:
            Result[dict]: Execution results or error
        """
        # Load workflow
        if workflow_id not in self._workflows:
            result = self.load_workflow(workflow_id)
            if not result.success:
                return result

        workflow = self._workflows[workflow_id]

        if not workflow.enabled:
            return Fail("Workflow is disabled", code="DISABLED")

        # Create execution record
        import uuid

        execution = WorkflowExecution(
            workflow_id=workflow_id,
            execution_id=str(uuid.uuid4())[:8],
            status="running",
            started_at=datetime.now().isoformat(),
        )
        self._executions.append(execution)

        try:
            # Log start event
            self._log_event(
                workflow_id, "workflow_started", {"execution_id": execution.execution_id}
            )

            execution_data = initial_data or {}
            results: dict[str, Any] = {"nodes_executed": [], "outputs": {}}

            # Build execution order
            execution_order = self._topological_sort(workflow)

            if not execution_order:
                return Fail("No nodes to execute", code="EMPTY_WORKFLOW")

            # Execute nodes in order
            for node in execution_order:
                self._log_event(workflow_id, f"node_started:{node.id}", {"node_name": node.name})

                # Validate inputs
                validation = node.validate_inputs(execution_data)
                if not validation.success:
                    execution.status = "failed"
                    execution.completed_at = datetime.now().isoformat()
                    execution.errors.append({"node": node.id, "error": validation.error})
                    self._persist_execution(execution)
                    return Fail(
                        f"Node {node.id} validation failed: {validation.error}",
                        code="VALIDATION_FAILED",
                    )

                # Execute node
                result = node.execute(execution_data)
                if not result.success:
                    execution.status = "failed"
                    execution.completed_at = datetime.now().isoformat()
                    execution.errors.append({"node": node.id, "error": result.error})
                    self._persist_execution(execution)
                    return Fail(f"Node {node.id} failed: {result.error}", code="NODE_FAILED")

                # Merge outputs into execution data
                if result.data:
                    execution_data.update(result.data)
                    execution.results[node.id] = result.data

                results["nodes_executed"].append(node.id)
                results["outputs"][node.id] = result.data

                self._log_event(workflow_id, f"node_completed:{node.id}", {"success": True})

            # Complete execution
            execution.status = "completed"
            execution.completed_at = datetime.now().isoformat()
            self._persist_execution(execution)

            self._log_event(
                workflow_id,
                "workflow_completed",
                {
                    "execution_id": execution.execution_id,
                    "nodes_executed": len(results["nodes_executed"]),
                },
            )

            return Ok(results)

        except Exception as e:
            execution.status = "failed"
            execution.errors.append({"error": str(e)})
            execution.completed_at = datetime.now().isoformat()
            self._persist_execution(execution)

            self._log_event(workflow_id, "workflow_failed", {"error": str(e)})

            return Fail(str(e), code="EXECUTION_ERROR")

    def _topological_sort(self, workflow: Workflow) -> list[WorkflowNode]:
        """Sort nodes in execution order based on edges.

        Uses Kahn's algorithm for topological sorting.

        Args:
            workflow: Workflow to sort

        Returns:
            List of nodes in execution order
        """
        if not workflow.nodes:
            return []

        # Build adjacency list and in-degree count
        node_map = {n.id: n for n in workflow.nodes}
        in_degree = {n.id: 0 for n in workflow.nodes}
        adjacency: dict[str, list[str]] = {n.id: [] for n in workflow.nodes}

        for edge in workflow.edges:
            if edge.from_node in adjacency and edge.to_node in in_degree:
                adjacency[edge.from_node].append(edge.to_node)
                in_degree[edge.to_node] += 1

        # Start with nodes that have no incoming edges (triggers)
        queue = [nid for nid, deg in in_degree.items() if deg == 0]
        sorted_nodes = []

        while queue:
            node_id = queue.pop(0)
            if node_id in node_map:
                sorted_nodes.append(node_map[node_id])

            for neighbor in adjacency.get(node_id, []):
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        # If we couldn't sort all nodes, there's a cycle
        if len(sorted_nodes) != len(workflow.nodes):
            logger.warning("Workflow may contain cycles, using partial order")

        return sorted_nodes

    def _log_event(self, workflow_id: str, action: str, data: dict) -> None:
        """Log workflow event to event log.

        Args:
            workflow_id: Workflow identifier
            action: Event action name
            data: Event data
        """
        try:
            from src.nusyq_spine.eventlog import append_event

            append_event(
                {
                    "trace_id": f"wf_{workflow_id}",
                    "actor": "workflow_engine",
                    "action": action,
                    "inputs_hash": "",
                    "outputs_hash": "",
                    "status": "success",
                    **data,
                }
            )
        except ImportError:
            # Event logging not available
            pass

    def get_execution_history(self, workflow_id: str | None = None, limit: int = 10) -> list[dict]:
        """Get workflow execution history.

        Args:
            workflow_id: Optional filter by workflow
            limit: Maximum number of results

        Returns:
            List of execution records
        """
        executions = self._executions

        if workflow_id:
            executions = [e for e in executions if e.workflow_id == workflow_id]

        # Return most recent first
        executions = sorted(executions, key=lambda e: e.started_at or "", reverse=True)

        return [e.to_dict() for e in executions[:limit]]


# Convenience function for global engine access
def get_workflow_engine() -> WorkflowEngine:
    """Get the global workflow engine instance."""
    return WorkflowEngine()
