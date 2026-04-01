"""
Collaboration Advisor - Intelligent Workload Distribution
=========================================================

Purpose:
    Helps GitHub Copilot decide when to suggest handing off work to
    Claude Code to maximize productivity and avoid rate limits.

    Uses subtle hints and user preferences, not hard-coded rules.

Philosophy:
    - Monitor, don't dictate
    - Suggest, don't force
    - Learn from patterns
    - User stays in control
"""

from typing import Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import yaml


class AgentType(Enum):
    """All supported agent types - extensible for future agents"""

    COPILOT = "github_copilot"
    CLAUDE_CODE = "claude_code"
    OLLAMA_QWEN = "ollama_qwen2.5-coder"
    OLLAMA_GEMMA = "ollama_gemma2"
    OLLAMA_STARCODER = "ollama_starcoder2"
    OLLAMA_CODELLAMA = "ollama_codellama"
    OLLAMA_PHI = "ollama_phi3.5"
    OLLAMA_LLAMA = "ollama_llama3.1"
    CUSTOM_ML = "custom_ml_model"
    CHATDEV_TEAM = "chatdev_agents"
    QUANTUM_RESOLVER = "quantum_problem_resolver"


class HandoffReason(Enum):
    """Why a handoff/delegation might be beneficial"""

    TOKEN_BUDGET = "approaching_token_limit"
    COMPLEXITY = "high_cognitive_complexity"
    MULTI_FILE = "many_files_to_edit"
    ARCHITECTURAL = "architectural_decision_needed"
    USER_REQUEST = "user_requested_specific_agent"
    TIME_EFFICIENCY = "another_agent_would_be_faster"
    RATE_LIMIT = "rate_limit_approaching"
    SPECIALIZATION = "task_requires_specialized_model"
    PARALLEL_WORK = "can_distribute_across_agents"


class AgentCapability(Enum):
    """What each agent type is good at"""

    INVESTIGATION = "investigation_and_analysis"
    SMALL_EDITS = "focused_bug_fixes"
    LARGE_REFACTOR = "multi_file_refactoring"
    ARCHITECTURE = "architectural_decisions"
    TESTING = "test_execution_and_validation"
    REPORTING = "documentation_and_reports"
    CODE_GENERATION = "code_generation"
    SPECIALIZED_DOMAIN = "domain_specific_expertise"
    PARALLEL_PROCESSING = "parallel_task_execution"
    QUANTUM_OPTIMIZATION = "quantum_algorithm_optimization"


@dataclass
class AgentScore:
    """Scoring for an agent's suitability for a task"""

    agent_type: AgentType
    confidence: float  # 0.0 to 1.0
    capabilities_match: List[AgentCapability]
    estimated_time: float  # seconds
    estimated_tokens: int
    pros: List[str] = field(default_factory=list)
    cons: List[str] = field(default_factory=list)


@dataclass
class WorkloadAssessment:
    """Assessment of current task complexity - multi-agent aware"""

    files_affected: int
    estimated_complexity: int
    token_cost_estimate: int
    requires_deep_context: bool
    architectural_impact: str  # "none", "low", "medium", "high"

    # Multi-agent scoring
    current_agent: AgentType
    current_agent_confidence: float  # 0.0 to 1.0

    # All agents ranked by suitability
    agent_scores: List[AgentScore] = field(default_factory=list)

    # Best recommendation
    recommended_agent: Optional[AgentType] = None
    should_handoff: bool = False
    handoff_reasons: List[HandoffReason] = field(default_factory=list)

    # Parallel work opportunities
    can_parallelize: bool = False
    parallel_agents: List[AgentType] = field(default_factory=list)

    suggestion: Optional[str] = None


class CollaborationAdvisor:
    """
    Multi-Agent Workload Orchestrator
    ==================================

    Monitors task complexity and suggests optimal agent distribution
    across ALL available agents (Copilot, Claude, Ollama models, etc.)

    Philosophy:
    - NOT a hard-coded enforcer - just provides suggestions
    - Supports bidirectional communication (agents can request help)
    - Learns from patterns and outcomes
    - User stays in control
    - Extensible for new agent types
    """

    def __init__(
        self,
        config_path: str = ".ai-context/collaboration-config.yaml",
        current_agent: AgentType = AgentType.COPILOT,
    ):
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self.current_agent = current_agent
        self.token_usage = 0
        self.session_history: List[Dict] = []

        # Agent registry - dynamically discover available agents
        self.available_agents = self._discover_available_agents()

    def _load_config(self) -> Dict:
        """Load collaboration configuration"""
        if not self.config_path.exists():
            return self._default_config()

        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f)
        except Exception as e:
            print(f"⚠️ Could not load collaboration config: {e}")
            return self._default_config()

    def _default_config(self) -> Dict:
        """Fallback configuration with multi-agent support"""
        return {
            "collaboration": {
                "enabled": True,
                "mode": "multi_agent_orchestration",
                "token_management": {
                    "copilot_max_per_session": 150000,
                    "claude_code_threshold": 100000,
                },
            },
            "agents": {
                AgentType.COPILOT.value: {
                    "strengths": ["investigation", "small_edits", "testing"],
                    "max_concurrent": 1,
                    "cost": "free",
                },
                AgentType.CLAUDE_CODE.value: {
                    "strengths": ["large_refactor", "architecture"],
                    "max_concurrent": 1,
                    "cost": "metered",
                },
                AgentType.OLLAMA_QWEN.value: {
                    "strengths": ["code_generation", "specialized_coding"],
                    "max_concurrent": 4,  # Can run 4 in parallel
                    "cost": "free_local",
                },
            },
        }

    def _discover_available_agents(self) -> Dict[AgentType, Dict]:
        """Dynamically discover which agents are available"""
        available = {}

        # Copilot is always available (that's me!)
        available[AgentType.COPILOT] = {
            "status": "active",
            "capabilities": ["investigation", "small_edits", "testing"],
            "max_concurrent": 1,
        }

        # Check if Claude Code bridge is available
        bridge_path = Path("config/claude_code_bridge.py")
        if bridge_path.exists():
            available[AgentType.CLAUDE_CODE] = {
                "status": "available_via_mcp",
                "capabilities": ["large_refactor", "architecture"],
                "max_concurrent": 1,
            }

        # Check which Ollama models are available
        try:
            import subprocess

            result = subprocess.run(
                ["ollama", "list"], capture_output=True, text=True, timeout=5
            )

            if result.returncode == 0:
                # Parse ollama list output
                lines = result.stdout.strip().split("\n")[1:]  # Skip header
                for line in lines:
                    if "qwen2.5-coder" in line:
                        available[AgentType.OLLAMA_QWEN] = {
                            "status": "available_local",
                            "capabilities": ["code_generation"],
                            "max_concurrent": 4,
                        }
                    elif "gemma2" in line:
                        available[AgentType.OLLAMA_GEMMA] = {
                            "status": "available_local",
                            "capabilities": ["general_reasoning"],
                            "max_concurrent": 4,
                        }
                    elif "starcoder2" in line:
                        available[AgentType.OLLAMA_STARCODER] = {
                            "status": "available_local",
                            "capabilities": ["code_generation"],
                            "max_concurrent": 3,
                        }
                    elif "codellama" in line:
                        available[AgentType.OLLAMA_CODELLAMA] = {
                            "status": "available_local",
                            "capabilities": ["code_generation"],
                            "max_concurrent": 4,
                        }
        except (OSError, subprocess.CalledProcessError, AttributeError):
            pass  # Ollama not available

        # Check ChatDev
        chatdev_path = Path("ChatDev/main.py")
        if chatdev_path.exists():
            available[AgentType.CHATDEV_TEAM] = {
                "status": "available_local",
                "capabilities": ["complex_projects", "team_simulation"],
                "max_concurrent": 1,
            }

        return available

    def update_token_usage(self, tokens_used: int) -> None:
        """Track token consumption"""
        self.token_usage = tokens_used

    def assess_workload(
        self,
        task_description: str,
        files_to_modify: List[str],
        complexity_indicators: Optional[Dict] = None,
        requesting_agent: Optional[AgentType] = None,
    ) -> WorkloadAssessment:
        """
        Multi-agent workload analysis - recommend best agent(s) for task

        Works BIDIRECTIONALLY:
        - Copilot can ask "Should I hand this to Claude/Ollama?"
        - Claude can ask "Should I delegate investigation to Copilot?"
        - Any agent can ask "Can we parallelize this?"

        Args:
            task_description: What needs to be done
            files_to_modify: List of file paths
            complexity_indicators: Optional metrics
            requesting_agent: Which agent is asking (defaults to current)

        Returns:
            WorkloadAssessment with multi-agent recommendations
        """
        requesting_agent = requesting_agent or self.current_agent
        files_count = len(files_to_modify)
        indicators = complexity_indicators or {}
        complexity = indicators.get("cognitive_complexity", 0)

        # Estimate token cost
        token_estimate = self._estimate_token_cost(
            files_count, complexity, task_description
        )

        # Check handoff reasons
        reasons = []

        # Token budget check
        if (
            self.token_usage + token_estimate
            > self.config["collaboration"]["token_management"]["claude_code_threshold"]
        ):
            reasons.append(HandoffReason.TOKEN_BUDGET)

        # Complexity check
        if complexity > 15:
            reasons.append(HandoffReason.COMPLEXITY)

        # Multi-file check
        if files_count > 5:
            reasons.append(HandoffReason.MULTI_FILE)

        # Architectural keywords
        architectural_keywords = ["architect", "design", "refactor", "restructure"]
        if any(kw in task_description.lower() for kw in architectural_keywords):
            reasons.append(HandoffReason.ARCHITECTURAL)

        # Multi-agent assessment
        requires_deep_context = complexity > 10 or files_count > 3
        architectural_impact = self._assess_architectural_impact(
            task_description, files_count
        )

        # Score ALL available agents
        agent_scores = self._score_all_agents(
            task_description,
            files_count,
            complexity,
            token_estimate,
            requires_deep_context,
            architectural_impact,
        )

        # Sort by confidence
        agent_scores.sort(key=lambda x: x.confidence, reverse=True)

        # Current agent's score
        current_score = next(
            (s for s in agent_scores if s.agent_type == requesting_agent), None
        )
        current_confidence = current_score.confidence if current_score else 0.5

        # Best alternative agent
        best_alternative = agent_scores[0] if agent_scores else None
        recommended_agent = (
            best_alternative.agent_type
            if best_alternative
            and best_alternative.confidence > current_confidence + 0.1
            else requesting_agent
        )

        should_handoff = recommended_agent != requesting_agent

        # Check parallelization opportunities
        can_parallelize = self._can_parallelize_task(task_description, files_count)
        parallel_agents = self._suggest_parallel_agents(
            task_description, can_parallelize
        )

        # Generate suggestion
        suggestion = (
            self._generate_multi_agent_suggestion(
                requesting_agent,
                recommended_agent,
                agent_scores[:3],  # Top 3 agents
                reasons,
                can_parallelize,
                parallel_agents,
            )
            if should_handoff or can_parallelize
            else None
        )

        return WorkloadAssessment(
            files_affected=files_count,
            estimated_complexity=complexity,
            token_cost_estimate=token_estimate,
            requires_deep_context=requires_deep_context,
            architectural_impact=architectural_impact,
            current_agent=requesting_agent,
            current_agent_confidence=current_confidence,
            agent_scores=agent_scores,
            recommended_agent=recommended_agent,
            should_handoff=should_handoff,
            handoff_reasons=reasons,
            can_parallelize=can_parallelize,
            parallel_agents=parallel_agents,
            suggestion=suggestion,
        )

    def _estimate_token_cost(
        self, files_count: int, complexity: int, description: str
    ) -> int:
        """Estimate tokens needed for this task"""
        # Base cost
        base = 5000

        # Per file cost
        file_cost = files_count * 3000

        # Complexity multiplier
        complexity_multiplier = 1 + (complexity / 15)

        # Description length
        desc_cost = len(description.split()) * 50

        return int((base + file_cost + desc_cost) * complexity_multiplier)

    def _assess_architectural_impact(self, description: str, files_count: int) -> str:
        """Determine if this affects architecture"""
        high_impact_words = [
            "architecture",
            "design pattern",
            "restructure",
            "redesign",
        ]
        medium_impact_words = ["refactor", "reorganize", "consolidate"]

        desc_lower = description.lower()

        if any(word in desc_lower for word in high_impact_words) or files_count > 10:
            return "high"
        elif any(word in desc_lower for word in medium_impact_words) or files_count > 5:
            return "medium"
        elif files_count > 2:
            return "low"
        else:
            return "none"

    def _calculate_confidence(
        self,
        files_count: int,
        complexity: int,
        token_estimate: int,
        requires_deep_context: bool,
    ) -> float:
        """Calculate Copilot's confidence in handling this alone"""
        confidence = 1.0

        # File count penalty
        if files_count > 5:
            confidence -= 0.3
        elif files_count > 3:
            confidence -= 0.15

        # Complexity penalty
        if complexity > 15:
            confidence -= 0.4
        elif complexity > 10:
            confidence -= 0.2

        # Token budget penalty
        remaining_tokens = 150000 - self.token_usage
        if token_estimate > remaining_tokens * 0.8:
            confidence -= 0.3
        elif token_estimate > remaining_tokens * 0.5:
            confidence -= 0.15

        # Deep context penalty
        if requires_deep_context:
            confidence -= 0.2

        return max(0.0, min(1.0, confidence))

    def _score_all_agents(
        self,
        task_desc: str,
        files: int,
        complexity: int,
        tokens: int,
        deep_context: bool,
        arch_impact: str,
    ) -> List[AgentScore]:
        """Score every available agent for this task"""
        scores = []

        for agent_type, info in self.available_agents.items():
            confidence = self._calculate_agent_confidence(
                agent_type, task_desc, files, complexity, tokens
            )

            score = AgentScore(
                agent_type=agent_type,
                confidence=confidence,
                capabilities_match=info.get("capabilities", []),
                estimated_time=self._estimate_time(agent_type, complexity),
                estimated_tokens=tokens
                if agent_type in [AgentType.COPILOT, AgentType.CLAUDE_CODE]
                else 0,
                pros=self._get_agent_pros(agent_type, task_desc),
                cons=self._get_agent_cons(agent_type, task_desc),
            )
            scores.append(score)

        return scores

    def _calculate_agent_confidence(
        self, agent: AgentType, task_desc: str, files: int, complexity: int, tokens: int
    ) -> float:
        """Calculate confidence score for specific agent"""
        confidence = 0.5  # Base

        # Copilot strengths
        if agent == AgentType.COPILOT:
            if files <= 3:
                confidence += 0.2
            if complexity <= 10:
                confidence += 0.2
            if "investigate" in task_desc.lower():
                confidence += 0.3

        # Claude Code strengths
        elif agent == AgentType.CLAUDE_CODE:
            if files > 5:
                confidence += 0.2
            if complexity > 15:
                confidence += 0.2
            if any(w in task_desc.lower() for w in ["refactor", "architect"]):
                confidence += 0.3

        # Ollama coding models
        elif agent in [AgentType.OLLAMA_QWEN, AgentType.OLLAMA_STARCODER]:
            if "generate" in task_desc.lower():
                confidence += 0.3
            if files <= 2:
                confidence += 0.2

        return min(1.0, max(0.0, confidence))

    def _can_parallelize_task(self, task_desc: str, files: int) -> bool:
        """Check if task can be split across multiple agents"""
        parallel_keywords = ["multiple", "each", "all files", "batch"]
        return any(kw in task_desc.lower() for kw in parallel_keywords)

    def _suggest_parallel_agents(
        self, task_desc: str, can_parallel: bool
    ) -> List[AgentType]:
        """Suggest which agents could work in parallel"""
        if not can_parallel:
            return []

        # Use local Ollama models for parallel processing
        return [
            agent
            for agent in self.available_agents.keys()
            if agent.value.startswith("ollama_")
        ]

    def _estimate_time(self, agent: AgentType, complexity: int) -> float:
        """Estimate task duration in seconds"""
        base_times = {
            AgentType.COPILOT: 30,
            AgentType.CLAUDE_CODE: 60,
            AgentType.OLLAMA_QWEN: 45,
        }
        base = base_times.get(agent, 60)
        return base * (1 + complexity / 10)

    def _get_agent_pros(self, agent: AgentType, task: str) -> List[str]:
        """Get advantages of using this agent"""
        pros_map = {
            AgentType.COPILOT: ["Fast", "Integrated", "No rate limits"],
            AgentType.CLAUDE_CODE: ["Deep analysis", "Large context"],
            AgentType.OLLAMA_QWEN: ["Local", "Free", "Parallel capable"],
        }
        return pros_map.get(agent, [])

    def _get_agent_cons(self, agent: AgentType, task: str) -> List[str]:
        """Get disadvantages of using this agent"""
        cons_map = {
            AgentType.COPILOT: ["Limited context", "Not for large refactor"],
            AgentType.CLAUDE_CODE: ["Rate limits", "Cooldowns"],
            AgentType.OLLAMA_QWEN: ["Slower", "Less context awareness"],
        }
        return cons_map.get(agent, [])

    def _generate_multi_agent_suggestion(
        self,
        current: AgentType,
        recommended: AgentType,
        top_agents: List[AgentScore],
        reasons: List[HandoffReason],
        can_parallel: bool,
        parallel_agents: List[AgentType],
    ) -> str:
        """Generate suggestion for multi-agent scenario"""

        if can_parallel and parallel_agents:
            agent_names = ", ".join([a.value for a in parallel_agents[:3]])
            return f"""
💡 Parallelization Opportunity: This task could be split across multiple agents.

Available for parallel work: {agent_names}
Hardware capacity: 32 cores, 32GB RAM - can easily handle 4+ agents

Would you like me to orchestrate parallel execution?
"""

        if current == recommended:
            return ""  # No handoff needed

        rec_name = recommended.value.replace("_", " ").title()
        curr_name = current.value.replace("_", " ").title()

        top_choice = top_agents[0]

        return f"""
💡 Agent Recommendation: {rec_name} might be better suited for this task.

Current ({curr_name}): {top_choice.confidence:.0%} confidence
Recommended ({rec_name}): Confidence {top_choice.confidence:.0%}

Reasons: {", ".join([r.value for r in reasons])}

Options:
1. Hand off to {rec_name} (recommended)
2. Continue with {curr_name}
3. Use parallel execution with multiple agents
"""

    def should_suggest_handoff(self) -> bool:
        """Simple check: should we suggest handoff right now?"""
        threshold = self.config["collaboration"]["token_management"][
            "claude_code_threshold"
        ]
        return self.token_usage >= threshold

    def record_task_outcome(
        self,
        task_type: str,
        agent_used: str,
        success: bool,
        tokens_used: int,
        duration_seconds: float,
    ) -> None:
        """Record task outcome for learning"""
        self.session_history.append(
            {
                "task_type": task_type,
                "agent": agent_used,
                "success": success,
                "tokens": tokens_used,
                "duration": duration_seconds,
                "timestamp": Path(".").stat().st_mtime,  # Simple timestamp
            }
        )

    def get_learned_patterns(self) -> Dict:
        """Analyze session history for patterns"""
        if not self.session_history:
            return {}

        # Simple analysis
        copilot_tasks = [t for t in self.session_history if t["agent"] == "copilot"]
        claude_tasks = [t for t in self.session_history if t["agent"] == "claude"]

        return {
            "copilot_success_rate": sum(1 for t in copilot_tasks if t["success"])
            / len(copilot_tasks)
            if copilot_tasks
            else 0,
            "claude_success_rate": sum(1 for t in claude_tasks if t["success"])
            / len(claude_tasks)
            if claude_tasks
            else 0,
            "avg_copilot_tokens": sum(t["tokens"] for t in copilot_tasks)
            / len(copilot_tasks)
            if copilot_tasks
            else 0,
            "avg_claude_tokens": sum(t["tokens"] for t in claude_tasks)
            / len(claude_tasks)
            if claude_tasks
            else 0,
        }


# Singleton instance for easy import
_advisor_instance = None


def get_collaboration_advisor() -> CollaborationAdvisor:
    """Get or create the collaboration advisor singleton"""
    global _advisor_instance
    if _advisor_instance is None:
        _advisor_instance = CollaborationAdvisor()
    return _advisor_instance


# Example usage
if __name__ == "__main__":
    advisor = get_collaboration_advisor()

    print("=== Multi-Agent Collaboration System ===\n")
    print(f"Available agents: {len(advisor.available_agents)}")
    for agent_type, info in advisor.available_agents.items():
        print(f"  - {agent_type.value}: {info['status']}")

    # Test scenario
    print("\n=== Testing Task Assessment ===\n")
    assessment = advisor.assess_workload(
        task_description="Refactor agent router - reduce complexity",
        files_to_modify=[
            "config/agent_router.py",
            "config/agent_registry.py",
            "tests/test_agent_router.py",
        ],
        complexity_indicators={"cognitive_complexity": 17},
    )

    print(f"Files: {assessment.files_affected}")
    print(f"Complexity: {assessment.estimated_complexity}")
    print(f"Current agent: {assessment.current_agent.value}")
    recommended_agent = (
        assessment.recommended_agent.value if assessment.recommended_agent else "n/a"
    )
    print(f"Recommended: {recommended_agent}")
    print(f"Should handoff: {assessment.should_handoff}")
    print(f"Can parallelize: {assessment.can_parallelize}")

    print("\nTop 3 Agents:")
    for i, score in enumerate(assessment.agent_scores[:3], 1):
        print(f"{i}. {score.agent_type.value}: {score.confidence:.0%} confidence")

    if assessment.suggestion:
        print(f"\n{assessment.suggestion}")
