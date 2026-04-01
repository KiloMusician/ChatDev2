"""NuSyQ-Hub Workflow Engine - n8n-style node-based workflows.

Provides a visual workflow system for automating tasks with:
- Node-based execution graphs
- Trigger, action, condition, transform, and output nodes
- Integration with QuestExecutor for safe execution
- Event logging for audit trails

OmniTag: [workflow, automation, nodes, pipeline]
MegaTag: WORKFLOW⨳ENGINE⦾AUTOMATION→∞

Usage:
    from src.workflow import WorkflowEngine, Workflow
    from src.workflow.nodes import ActionNode, ConditionNode

    engine = WorkflowEngine()
    engine.register_node_type("action", ActionNode)

    result = engine.execute_workflow("my_workflow", {"input": "data"})
"""

from src.workflow.engine import Workflow, WorkflowEngine, get_workflow_engine
from src.workflow.nodes import NodePort, NodeType, WorkflowNode

__all__ = [
    "NodePort",
    "NodeType",
    "Workflow",
    "WorkflowEngine",
    "WorkflowNode",
    "get_workflow_engine",
]
