"""
ΞNuSyQ Agent Router - Multi-Agent Orchestration
===============================================

Intelligent routing of tasks to optimal AI agents based on:
- Task complexity and scope
- Agent capabilities and specialization
- Hardware capacity (32 cores, 32GB RAM)
- Token budgets and rate limits
- Bidirectional agent collaboration

Supports: Copilot, Claude Code, Ollama (8 models), ChatDev, Custom ML

Version: 2.0.0 - Multi-Agent Edition
Date: 2025-10-07
"""

import io
import logging
import sys
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml  # type: ignore[import-untyped]

# Import ship memory (optional)

try:
    from scripts.ship_memory import ShipMemory

    SHIP_MEMORY_ENABLED = True
except ImportError:
    SHIP_MEMORY_ENABLED = False

# UTF-8 Windows fix — skip when running under pytest to avoid closing capture buffers
if sys.platform == "win32" and "pytest" not in sys.modules:
    if hasattr(sys.stdout, "buffer"):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    if hasattr(sys.stderr, "buffer"):
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

logger = logging.getLogger(__name__)


class TaskComplexity(Enum):
    """Task complexity levels"""

    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"
    CRITICAL = "critical"


class TaskType(Enum):
    """Common task types"""

    DOCSTRING = "docstring"
    CODE_GENERATION = "code_generation"
    REFACTORING = "refactoring"
    BUG_FIX = "bug_fix"
    ARCHITECTURE = "architecture"
    SECURITY_AUDIT = "security_audit"
    DOCUMENTATION = "documentation"
    TEST_GENERATION = "test_generation"
    CODE_REVIEW = "code_review"
    FULL_FEATURE = "full_feature"
    CODEBASE_SEARCH = "codebase_search"


@dataclass
class Task:
    """Task definition for routing"""

    description: str
    task_type: TaskType
    complexity: TaskComplexity
    files_affected: int = 1
    requires_reasoning: bool = False
    requires_security: bool = False
    prefer_free: bool = True


@dataclass
class Agent:
    """Agent definition from registry"""

    name: str
    type: str
    provider: str
    model: Optional[str]
    capabilities: List[str]
    cost_per_1k_tokens: Any  # Can be float or dict with input/output
    availability: str
    reliability: str
    strengths: List[str]
    weaknesses: List[str]
    context_window: int = 32768


@dataclass
class RoutingDecision:
    """Routing decision with rationale"""

    agent: Agent
    rationale: str
    estimated_cost: float
    alternatives: List[Agent]
    coordination_pattern: str


class AgentRouter:
    """
    Routes tasks to optimal agents based on:
    - Task complexity and type
    - Agent capabilities
    - Cost optimization (prefer free Ollama)
    - Availability and reliability

    Implements CLASSIFY phase from Adaptive Workflow Protocol
    """

    def __init__(self, registry_path: Optional[Path] = None):
        """
        Initialize router with agent registry

        Args:
            registry_path: Path to agent_registry.yaml
        """
        if registry_path is None:
            registry_path = Path(__file__).resolve().parent / "agent_registry.yaml"

        self.registry_path = registry_path
        self.base_path = Path(__file__).resolve().parent.parent
        self.agents: Dict[str, Agent] = {}
        self.routing_preferences: Dict[str, str] = {}
        self.coordination_patterns: Dict[str, Dict] = {}

        # Knowledge base for learning
        self.knowledge_base_path = self.base_path / "knowledge-base.yaml"
        self.routing_history: List[Dict[str, Any]] = []

        # Initialize Ship Memory if available
        self.ship_memory: Optional["ShipMemory"] = None
        if SHIP_MEMORY_ENABLED:
            memory_file = self.base_path / "State" / "ship_memory.json"
            memory_file.parent.mkdir(exist_ok=True)
            self.ship_memory = ShipMemory(memory_file)

        self._load_registry()

    def _load_registry(self):
        """Load agent registry from YAML"""
        try:
            with open(self.registry_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)

            # Load agents
            agents_data = data.get("agents", {})
            for name, config in agents_data.items():
                self.agents[name] = Agent(
                    name=name,
                    type=config.get("type", "unknown"),
                    provider=config.get("provider", "unknown"),
                    model=config.get("model"),
                    capabilities=config.get("capabilities", []),
                    cost_per_1k_tokens=config.get("cost_per_1k_tokens", 0.0),
                    availability=config.get("availability", "unknown"),
                    reliability=config.get("reliability", "unknown"),
                    strengths=config.get("strengths", []),
                    weaknesses=config.get("weaknesses", []),
                    context_window=config.get("context_window", 32768),
                )

            # Load routing preferences
            self.routing_preferences = data.get("routing_preferences", {})

            # Load coordination patterns
            self.coordination_patterns = data.get("coordination_patterns", {})

            logger.info("Loaded %d agents from registry", len(self.agents))

        except FileNotFoundError:
            logger.error("Agent registry not found: %s", self.registry_path)
            raise
        except yaml.YAMLError as e:
            logger.error("Error parsing agent registry YAML: %s", e)
            raise

    def _get_agent_cost(self, agent: Agent) -> float:
        """Get numeric cost for agent (handle dict or float)"""
        cost = agent.cost_per_1k_tokens
        if isinstance(cost, dict):
            # Return average of input/output
            return (cost.get("input", 0) + cost.get("output", 0)) / 2.0
        return float(cost) if cost else 0.0

    def _is_free_agent(self, agent: Agent) -> bool:
        """Check if agent is free (cost ~ 0)"""
        return self._get_agent_cost(agent) < 0.001  # Effectively zero

    def route_task(self, task: Task) -> RoutingDecision:
        """
        Route task to optimal agent

        Args:
            task: Task definition with type and complexity

        Returns:
            RoutingDecision with selected agent and rationale
        """
        # Step 1: Find capable agents
        capable_agents = self._find_capable_agents(task)

        if not capable_agents:
            # Fallback to orchestrator (Claude Code) - guaranteed to exist
            agent = self.agents.get("claude_code")
            if not agent:
                raise ValueError("Orchestrator agent 'claude_code' not found")
            return RoutingDecision(
                agent=agent,
                rationale="No specialized agent found, using orchestrator",
                estimated_cost=0.05,
                alternatives=[],
                coordination_pattern="orchestrator_fallback",
            )

        # Step 2: Check routing preferences
        preferred_agent = self._check_preferences(task)

        # Step 3: Optimize selection (cost vs quality)
        selected_agent, alternatives = self._optimize_selection(
            capable_agents, preferred_agent, task
        )

        # Step 4: Determine coordination pattern
        pattern = self._get_coordination_pattern(task, selected_agent)

        # Step 5: Estimate cost
        estimated_cost = self._estimate_cost(task, selected_agent)

        # Step 6: Generate rationale
        rationale = self._generate_rationale(task, selected_agent, pattern)

        return RoutingDecision(
            agent=selected_agent,
            rationale=rationale,
            estimated_cost=estimated_cost,
            alternatives=alternatives,
            coordination_pattern=pattern,
        )

    def _find_capable_agents(self, task: Task) -> List[Agent]:
        """Find agents capable of handling this task"""
        capable = []

        # Map task type to required capabilities
        capability_map = {
            TaskType.DOCSTRING: [
                "code_generation",
                "docstring_creation",
            ],
            TaskType.CODE_GENERATION: [
                "code_generation",
                "complex_code_generation",
            ],
            TaskType.REFACTORING: [
                "refactoring",
                "advanced_refactoring",
            ],
            TaskType.BUG_FIX: [
                "bug_fixing",
                "code_generation",
            ],
            TaskType.ARCHITECTURE: [
                "architecture_design",
                "system_design",
            ],
            TaskType.SECURITY_AUDIT: [
                "security_audit",
                "code_review",
            ],
            TaskType.DOCUMENTATION: [
                "documentation",
                "general_assistance",
            ],
            TaskType.TEST_GENERATION: [
                "test_generation",
            ],
            TaskType.CODE_REVIEW: [
                "code_review",
                "quality_assessment",
            ],
            TaskType.FULL_FEATURE: [
                "task_delegation",
                "feature_development",
            ],
            TaskType.CODEBASE_SEARCH: [
                "codebase_search",
                "semantic_navigation",
            ],
        }

        required_capabilities = capability_map.get(task.task_type, [])

        for agent in self.agents.values():
            # Orchestrator can handle anything OR has required capability
            if agent.type == "orchestrator" or any(
                cap in agent.capabilities for cap in required_capabilities
            ):
                capable.append(agent)

        return capable

    def _check_preferences(self, task: Task) -> Optional[str]:
        """Check routing preferences for this task type"""
        # Build preference key from task type and complexity
        key_map = {
            (TaskType.DOCSTRING, TaskComplexity.SIMPLE): "simple_docstring",
            (TaskType.CODE_GENERATION, TaskComplexity.COMPLEX): "complex_code",
            (TaskType.ARCHITECTURE, TaskComplexity.CRITICAL): ("architecture_decision"),
            (TaskType.SECURITY_AUDIT, TaskComplexity.CRITICAL): ("security_audit"),
            (TaskType.FULL_FEATURE, TaskComplexity.COMPLEX): "full_feature",
            (TaskType.REFACTORING, TaskComplexity.MODERATE): "refactoring",
            (TaskType.BUG_FIX, TaskComplexity.SIMPLE): "bug_fix_simple",
            (TaskType.BUG_FIX, TaskComplexity.COMPLEX): "bug_fix_complex",
            (TaskType.DOCUMENTATION, TaskComplexity.SIMPLE): "documentation",
            (TaskType.TEST_GENERATION, TaskComplexity.MODERATE): ("test_generation"),
            (TaskType.CODE_REVIEW, TaskComplexity.MODERATE): "code_review",
            (TaskType.CODEBASE_SEARCH, TaskComplexity.SIMPLE): ("codebase_search"),
        }

        key = key_map.get((task.task_type, task.complexity))
        if key:
            return self.routing_preferences.get(key)

        return None

    def _select_preferred_agent(
        self, capable_agents: List[Agent], preferred_agent: str
    ) -> Tuple[Optional[Agent], List[Agent]]:
        """Select preferred agent if available"""
        if preferred_agent == "multi_model_consensus":
            consensus_agents = [
                a
                for a in capable_agents
                if a.name
                in [
                    "ollama_qwen_14b",
                    "ollama_gemma_9b",
                    "claude_code",
                ]
            ]
            if consensus_agents:
                return consensus_agents[0], consensus_agents[1:]
        else:
            for agent in capable_agents:
                if agent.name == preferred_agent:
                    alternatives = [a for a in capable_agents if a != agent]
                    return agent, alternatives[:2]
        return None, []

    def _select_free_agent(
        self, capable_agents: List[Agent]
    ) -> Tuple[Optional[Agent], List[Agent]]:
        """Select best free agent if available"""
        free_agents = [a for a in capable_agents if self._is_free_agent(a)]
        if not free_agents:
            return None, []

        free_agents.sort(
            key=lambda a: (
                a.reliability == "high",
                len(a.capabilities),
                -len(a.weaknesses),
            ),
            reverse=True,
        )
        return free_agents[0], free_agents[1:3]

    def _select_best_agent(self, capable_agents: List[Agent]) -> Tuple[Agent, List[Agent]]:
        """Select best agent by reliability and capabilities"""
        capable_agents.sort(
            key=lambda a: (
                a.reliability == "high",
                len(a.capabilities),
                -self._get_agent_cost(a),
            ),
            reverse=True,
        )
        return capable_agents[0], capable_agents[1:3]

    def _optimize_selection(
        self, capable_agents: List[Agent], preferred_agent: Optional[str], task: Task
    ) -> Tuple[Agent, List[Agent]]:
        """
        Optimize agent selection based on cost and quality

        Returns:
            (selected_agent, alternative_agents)
        """
        # Try preferred agent first
        if preferred_agent:
            agent, alternatives = self._select_preferred_agent(capable_agents, preferred_agent)
            if agent:
                return agent, alternatives

        # Try free agents if requested
        if task.prefer_free:
            agent, alternatives = self._select_free_agent(capable_agents)
            if agent:
                return agent, alternatives

        # Fall back to best overall agent
        return self._select_best_agent(capable_agents)

    def _get_coordination_pattern(self, task: Task, agent: Agent) -> str:
        """Determine coordination pattern for this task"""
        # Critical tasks use multi-model consensus
        if task.complexity == TaskComplexity.CRITICAL:
            return "critical_decision"

        # Full projects use ChatDev
        if task.task_type == TaskType.FULL_FEATURE:
            return "full_project"

        # Interactive development
        if agent.name == "continue_dev":
            return "interactive_dev"

        # Complex tasks use review loop
        if task.complexity == TaskComplexity.COMPLEX:
            return "complex_task"

        # Simple tasks are direct
        return "simple_task"

    def _estimate_cost(self, task: Task, agent: Agent) -> float:
        """
        Estimate cost in USD for this task

        Rough estimation based on:
        - Agent cost per 1k tokens
        - Task complexity (affects token count)
        """
        # Estimate tokens based on complexity
        token_estimates = {
            TaskComplexity.SIMPLE: 500,
            TaskComplexity.MODERATE: 2000,
            TaskComplexity.COMPLEX: 5000,
            TaskComplexity.CRITICAL: 10000,
        }

        estimated_tokens = token_estimates.get(task.complexity, 1000)

        # Handle cost as float or dict (input/output)
        cost_per_1k = agent.cost_per_1k_tokens
        if isinstance(cost_per_1k, dict):
            # Average of input and output for estimation
            input_cost = cost_per_1k.get("input", 0)
            output_cost = cost_per_1k.get("output", 0)
            cost_per_1k = (input_cost + output_cost) / 2.0

        cost = (estimated_tokens / 1000.0) * cost_per_1k

        return round(cost, 4)

    def _generate_rationale(self, task: Task, agent: Agent, pattern: str) -> str:
        """Generate human-readable rationale for routing decision"""
        reasons = []

        # Agent selection reason
        if self._is_free_agent(agent):
            reasons.append(f"✓ Using free local agent ({agent.name})")
        else:
            reasons.append(f"Using {agent.name} (${agent.cost_per_1k_tokens}/1k tokens)")

        # Capability match
        if task.task_type.value in " ".join(agent.capabilities):
            reasons.append(f"✓ Specialized for {task.task_type.value}")

        # Complexity match
        if task.complexity == TaskComplexity.CRITICAL and "consensus" in pattern:
            reasons.append("✓ Multi-model consensus for critical decision")

        # Reliability
        if agent.reliability == "high":
            reasons.append("✓ High reliability")

        return " | ".join(reasons)

    def get_agent_by_name(self, name: str) -> Optional[Agent]:
        """Get agent by name"""
        return self.agents.get(name)

    def list_agents(self, filter_type: Optional[str] = None) -> List[Agent]:
        """
        List all agents, optionally filtered by type

        Args:
            filter_type: Optional agent type filter
                (e.g., "executor", "orchestrator")

        Returns:
            List of matching agents
        """
        if filter_type:
            return [a for a in self.agents.values() if a.type == filter_type]
        return list(self.agents.values())

    def get_cost_report(self) -> Dict[str, Any]:
        """Generate cost analysis report"""
        free_agents = [a for a in self.agents.values() if self._is_free_agent(a)]
        paid_agents = [a for a in self.agents.values() if not self._is_free_agent(a)]

        return {
            "total_agents": len(self.agents),
            "free_agents": len(free_agents),
            "paid_agents": len(paid_agents),
            "free_agent_names": [a.name for a in free_agents],
            "paid_agent_names": [a.name for a in paid_agents],
            "estimated_monthly_savings": 880.0,  # From registry
        }

    def record_task_completion(
        self,
        agent_name: str,
        task_type: str,
        success: bool,
        duration: float,
        task_description: Optional[str] = None,
    ):
        """
        Record task completion in Ship Memory and knowledge base

        Args:
            agent_name: Name of agent that handled the task
            task_type: Type of task (e.g., 'code_generation')
            success: Whether task completed successfully
            duration: Task duration in seconds
            task_description: Optional task description for learning
        """
        # Record in Ship Memory (existing functionality)
        if self.ship_memory:
            session_data = {
                "timestamp": datetime.now().isoformat(),
                "agent": agent_name,
                "task_type": task_type,
                "success": success,
                "duration": duration,
            }
            self.ship_memory.record_session(session_data)

        # Record in routing history for knowledge base learning
        routing_entry = {
            "timestamp": datetime.now().isoformat(),
            "agent": agent_name,
            "task_type": task_type,
            "success": success,
            "duration": duration,
            "task_description": task_description,
        }
        self.routing_history.append(routing_entry)

        # Update knowledge base every 10 successful completions
        if success and len(self.routing_history) % 10 == 0:
            self._update_knowledge_base()

    def _update_knowledge_base(self):
        """Update knowledge base with learned routing patterns"""
        try:
            # Load existing knowledge base
            if self.knowledge_base_path.exists():
                with open(self.knowledge_base_path, "r", encoding="utf-8") as f:
                    kb_data = yaml.safe_load(f) or {}
            else:
                kb_data = {"meta": {}, "sessions": []}

            # Create routing learnings entry
            now = datetime.now()

            routing_session = {
                "id": f"routing-learnings-{now.strftime('%Y%m%d')}",
                "date": now.strftime("%Y-%m-%d"),
                "type": "routing-optimization",
                "description": "Learned routing patterns from successful task completions",
                "learnings": self._analyze_routing_history(),
            }

            # Append to sessions
            sessions = kb_data.get("sessions", [])

            # Remove old routing-learnings entry for today
            sessions = [
                s
                for s in sessions
                if not (
                    s.get("id", "").startswith("routing-learnings")
                    and s.get("date") == now.strftime("%Y-%m-%d")
                )
            ]

            sessions.append(routing_session)
            kb_data["sessions"] = sessions

            # Update metadata
            kb_data["meta"]["last_updated"] = now.strftime("%Y-%m-%d")

            # Write back to knowledge base
            with open(self.knowledge_base_path, "w", encoding="utf-8") as f:
                yaml.safe_dump(kb_data, f, default_flow_style=False, allow_unicode=True)

            logger.info(
                "Updated knowledge base with %d routing learnings",
                len(routing_session["learnings"]),
            )

        except (yaml.YAMLError, OSError, IOError) as e:
            logger.warning("Failed to update knowledge base: %s", e)

    def _analyze_routing_history(self) -> List[Dict[str, Any]]:
        """Analyze routing history for patterns"""
        learnings = []

        # Group by task type
        task_types: Dict[str, List[Dict]] = {}
        for entry in self.routing_history:
            if entry["success"]:  # Only learn from successes
                task_type = entry["task_type"]
                if task_type not in task_types:
                    task_types[task_type] = []
                task_types[task_type].append(entry)

        # Analyze each task type
        for task_type, entries in task_types.items():
            # Find best performing agent
            agent_performance: Dict[str, Dict] = {}
            for entry in entries:
                agent = entry["agent"]
                if agent not in agent_performance:
                    agent_performance[agent] = {"count": 0, "total_duration": 0.0}
                agent_performance[agent]["count"] += 1
                agent_performance[agent]["total_duration"] += entry["duration"]

            # Calculate averages and find best
            best_agent = None
            best_avg = float("inf")
            for agent, perf in agent_performance.items():
                avg_duration = perf["total_duration"] / perf["count"]
                if avg_duration < best_avg:
                    best_avg = avg_duration
                    best_agent = agent

            if best_agent:
                learnings.append(
                    {
                        "task_type": task_type,
                        "recommended_agent": best_agent,
                        "avg_duration": round(best_avg, 2),
                        "sample_size": (agent_performance[best_agent]["count"]),
                    }
                )

        return learnings

    def get_agent_performance(self, agent_name: str) -> Dict[str, Any]:
        """Get performance metrics for an agent from Ship Memory"""
        if not self.ship_memory:
            return {}

        sessions = self.ship_memory.memory.get("sessions", [])
        agent_sessions = [s for s in sessions if s.get("agent") == agent_name]

        if not agent_sessions:
            return {"tasks_completed": 0, "success_rate": 0.0}

        total = len(agent_sessions)
        successful = sum(1 for s in agent_sessions if s.get("success"))
        avg_duration = sum(s.get("duration", 0) for s in agent_sessions) / total

        return {
            "tasks_completed": total,
            "tasks_successful": successful,
            "success_rate": successful / total if total > 0 else 0.0,
            "average_duration": avg_duration,
        }


# === Example Usage ===

if __name__ == "__main__":
    # Initialize router
    router = AgentRouter()

    print("=" * 70)
    print("ΞNuSyQ Agent Router - Demonstration")
    print("=" * 70)
    print()

    # Test Case 1: Simple docstring
    task1 = Task(
        description="Add docstring to validate_config function",
        task_type=TaskType.DOCSTRING,
        complexity=TaskComplexity.SIMPLE,
        files_affected=1,
    )

    decision1 = router.route_task(task1)
    print(f"📋 Task 1: {task1.description}")
    print(f"   Agent: {decision1.agent.name}")
    print(f"   Cost: ${decision1.estimated_cost}")
    print(f"   Rationale: {decision1.rationale}")
    print(f"   Pattern: {decision1.coordination_pattern}")
    print()

    # Test Case 2: Security audit
    task2 = Task(
        description="Audit authentication system for SQL injection",
        task_type=TaskType.SECURITY_AUDIT,
        complexity=TaskComplexity.CRITICAL,
        requires_security=True,
        prefer_free=True,
    )

    decision2 = router.route_task(task2)
    print(f"🔒 Task 2: {task2.description}")
    print(f"   Agent: {decision2.agent.name}")
    print(f"   Cost: ${decision2.estimated_cost}")
    print(f"   Rationale: {decision2.rationale}")
    print(f"   Pattern: {decision2.coordination_pattern}")
    print()

    # Test Case 3: Full feature
    task3 = Task(
        description="Create JWT authentication system with FastAPI",
        task_type=TaskType.FULL_FEATURE,
        complexity=TaskComplexity.COMPLEX,
        files_affected=5,
    )

    decision3 = router.route_task(task3)
    print(f"🚀 Task 3: {task3.description}")
    print(f"   Agent: {decision3.agent.name}")
    print(f"   Cost: ${decision3.estimated_cost}")
    print(f"   Rationale: {decision3.rationale}")
    print(f"   Pattern: {decision3.coordination_pattern}")
    print()

    # Cost report
    print("=" * 70)
    print("💰 Cost Analysis Report")
    print("=" * 70)
    cost_report = router.get_cost_report()
    print(f"Total agents: {cost_report['total_agents']}")
    print(f"Free agents: {cost_report['free_agents']}")
    print(f"Paid agents: {cost_report['paid_agents']}")
    print(f"Estimated monthly savings (using Ollama): ${cost_report['estimated_monthly_savings']}")
    print()

    print("✅ Agent Router operational and ready for integration")
