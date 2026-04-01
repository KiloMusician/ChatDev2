"""Advanced EOL Workflows Package.

Sophisticated implementations of reconnaissance, escalation, exploit chains,
and optimization techniques for advanced system exploration and optimization.

Components:
  - orchestrator: Master coordinator with all workflow engines
  - reconnaissance: Parallel intelligence gathering
  - escalation: Progressive capability unlocking
  - exploit_chaining: Context-propagating multi-hop exploitation
  - consensus: Distributed consensus voting

Quick Start:

    from src.advanced_workflows.orchestrator import AdvancedWorkflowOrchestrator

    orchestrator = AdvancedWorkflowOrchestrator()
    results = orchestrator.full_breach_sequence()

CLI:
    python -m src.advanced_workflows.orchestrator --demo
"""

from src.advanced_workflows.orchestrator import (AdvancedWorkflowOrchestrator,
                                                 AgentProbe,
                                                 CapabilityEscalator,
                                                 EnvironmentConstraints,
                                                 EscalationStep,
                                                 ExploitChainer, ExploitHop,
                                                 OptimizationGoal,
                                                 ParallelConsensus,
                                                 ParallelRecognaissance)

__all__ = [
    "AdvancedWorkflowOrchestrator",
    "AgentProbe",
    "CapabilityEscalator",
    "EnvironmentConstraints",
    "EscalationStep",
    "ExploitChainer",
    "ExploitHop",
    "OptimizationGoal",
    "ParallelConsensus",
    "ParallelRecognaissance",
]
