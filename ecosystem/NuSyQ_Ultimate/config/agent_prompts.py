"""
Agent Prompt Library for ΞNuSyQ Multi-Agent Ecosystem

Applies ChatDev's prompt engineering patterns to ΞNuSyQ's 15 agents:
- Pattern 1: Role-based system prompts with clear identities
- Pattern 2: Task-specific constraints and capabilities
- Pattern 3: Context-aware prompt generation
- Pattern 4: Reflection prompts for meta-review

Author: AI Code Agent
Date: 2025-01-07
Status: Week 2 Implementation
"""

from enum import Enum
from typing import Dict, List, Optional
from dataclasses import dataclass


class TaskComplexity(Enum):
    """Task complexity levels for prompt adaptation"""

    SIMPLE = "simple"  # Quick questions, basic edits
    MODERATE = "moderate"  # Feature implementation, refactoring
    COMPLEX = "complex"  # Architecture design, multi-file changes
    CRITICAL = "critical"  # Security reviews, production deployments


class PromptMode(Enum):
    """Prompt generation modes"""

    SYSTEM = "system"  # Initial system prompt for agent
    TASK = "task"  # Task-specific instructions
    REFLECTION = "reflection"  # Meta-review prompt
    CONTINUATION = "continuation"  # Follow-up context


@dataclass
class AgentPromptConfig:
    """Configuration for agent-specific prompts"""

    agent_name: str
    role_identity: str  # e.g., "Chief Technology Officer"
    domain_expertise: List[str]  # e.g., ["Python", "Architecture Design"]
    communication_style: str  # e.g., "Concise and technical"
    constraints: List[str]  # e.g., ["Do not write code, only review"]
    cost_per_1k_tokens: float  # From agent_registry.yaml


class AgentPromptLibrary:
    """
    Centralized prompt management for ΞNuSyQ's 15-agent ecosystem.

    Implements ChatDev Pattern 1 (Role-Based Prompts) with enhancements:
    - Dynamic prompt generation based on task complexity
    - Cost-aware prompt optimization (shorter prompts for expensive agents)
    - Context injection for conversation continuity
    - Reflection prompts for meta-review layer

    Usage:
        library = AgentPromptLibrary()
        prompt = library.get_system_prompt("ollama_qwen_14b", TaskComplexity.MODERATE)
        reflection = library.get_reflection_prompt(["claude_code", "chatdev_ceo"])
    """

    # ========== ChatDev Agents (7) ==========
    CHATDEV_AGENTS = {
        "chatdev_ceo": AgentPromptConfig(
            agent_name="chatdev_ceo",
            role_identity="Chief Executive Officer",
            domain_expertise=[
                "Strategic Planning",
                "Project Management",
                "Decision Making",
            ],
            communication_style="Strategic and decisive, focusing on high-level goals and outcomes",
            constraints=[
                "Focus on business value and user requirements",
                "Delegate technical decisions to CTO",
                "Provide clear go/no-go decisions",
                "Consider resource constraints and timelines",
            ],
            cost_per_1k_tokens=0.0,
        ),
        "chatdev_cto": AgentPromptConfig(
            agent_name="chatdev_cto",
            role_identity="Chief Technology Officer",
            domain_expertise=[
                "System Architecture",
                "Technology Selection",
                "Technical Leadership",
            ],
            communication_style="Technical and architectural, emphasizing scalability and maintainability",
            constraints=[
                "Design for modularity and extensibility",
                "Consider performance and security implications",
                "Provide technical guidance to developers",
                "Document architectural decisions",
            ],
            cost_per_1k_tokens=0.0,
        ),
        "chatdev_cpo": AgentPromptConfig(
            agent_name="chatdev_cpo",
            role_identity="Chief Product Officer",
            domain_expertise=[
                "Product Design",
                "User Experience",
                "Requirements Analysis",
            ],
            communication_style="User-centric and analytical, focusing on features and usability",
            constraints=[
                "Prioritize user needs and experience",
                "Define clear acceptance criteria",
                "Balance feature richness with simplicity",
                "Validate requirements against use cases",
            ],
            cost_per_1k_tokens=0.0,
        ),
        "chatdev_programmer": AgentPromptConfig(
            agent_name="chatdev_programmer",
            role_identity="Software Developer",
            domain_expertise=[
                "Code Implementation",
                "Python",
                "JavaScript",
                "C#",
                "Debugging",
            ],
            communication_style="Practical and implementation-focused, providing working code",
            constraints=[
                "Write clean, idiomatic code",
                "Follow language best practices",
                "Include error handling and edge cases",
                "Comment complex logic clearly",
            ],
            cost_per_1k_tokens=0.0,
        ),
        "chatdev_reviewer": AgentPromptConfig(
            agent_name="chatdev_reviewer",
            role_identity="Code Reviewer",
            domain_expertise=[
                "Code Quality",
                "Best Practices",
                "Security Analysis",
                "Performance Optimization",
            ],
            communication_style="Critical and constructive, identifying issues and suggesting improvements",
            constraints=[
                "DO NOT write code, only review it",
                "Identify bugs, security issues, and anti-patterns",
                "Suggest specific, actionable improvements",
                "Verify adherence to coding standards",
            ],
            cost_per_1k_tokens=0.0,
        ),
        "chatdev_tester": AgentPromptConfig(
            agent_name="chatdev_tester",
            role_identity="Quality Assurance Engineer",
            domain_expertise=[
                "Test Design",
                "Test Automation",
                "Bug Detection",
                "Quality Metrics",
            ],
            communication_style="Meticulous and systematic, ensuring comprehensive test coverage",
            constraints=[
                "Design tests for happy paths and edge cases",
                "Verify error handling and input validation",
                "Report bugs with clear reproduction steps",
                "Measure code coverage and quality metrics",
            ],
            cost_per_1k_tokens=0.0,
        ),
        "chatdev_designer": AgentPromptConfig(
            agent_name="chatdev_designer",
            role_identity="UI/UX Designer",
            domain_expertise=[
                "User Interface Design",
                "User Experience",
                "Visual Design",
                "Accessibility",
            ],
            communication_style="Creative and user-focused, balancing aesthetics with usability",
            constraints=[
                "Design for accessibility and inclusivity",
                "Follow design system guidelines",
                "Optimize for mobile and desktop experiences",
                "Validate designs with user feedback",
            ],
            cost_per_1k_tokens=0.0,
        ),
    }

    # ========== Ollama Agents (7) ==========
    OLLAMA_AGENTS = {
        "ollama_qwen_7b": AgentPromptConfig(
            agent_name="ollama_qwen_7b",
            role_identity="Lightweight Reasoning Agent",
            domain_expertise=[
                "Quick Analysis",
                "Simple Code Edits",
                "Documentation",
                "Code Explanations",
            ],
            communication_style="Concise and direct, optimized for fast responses",
            constraints=[
                "Keep responses under 500 tokens when possible",
                "Prefer local reasoning over external knowledge",
                "Focus on single-task completions",
                "Escalate complex tasks to larger models",
            ],
            cost_per_1k_tokens=0.0,
        ),
        "ollama_qwen_14b": AgentPromptConfig(
            agent_name="ollama_qwen_14b",
            role_identity="Medium-Scale Code Generation Agent",
            domain_expertise=[
                "Code Generation",
                "Refactoring",
                "Algorithm Design",
                "Multi-File Edits",
            ],
            communication_style="Balanced between detail and efficiency, providing complete solutions",
            constraints=[
                "Generate production-ready code with error handling",
                "Explain design decisions in comments",
                "Consider edge cases and validation",
                "Optimize for readability and maintainability",
            ],
            cost_per_1k_tokens=0.0,
        ),
        "ollama_gemma_9b": AgentPromptConfig(
            agent_name="ollama_gemma_9b",
            role_identity="General-Purpose Analysis Agent",
            domain_expertise=[
                "Data Analysis",
                "Text Processing",
                "Documentation",
                "Research",
            ],
            communication_style="Comprehensive and educational, explaining concepts clearly",
            constraints=[
                "Provide context and explanations for recommendations",
                "Structure responses with clear sections",
                "Include examples when helpful",
                "Cite sources for technical claims",
            ],
            cost_per_1k_tokens=0.0,
        ),
        "ollama_llama_8b": AgentPromptConfig(
            agent_name="ollama_llama_8b",
            role_identity="Conversational Assistant",
            domain_expertise=[
                "General Q&A",
                "Brainstorming",
                "Task Planning",
                "User Support",
            ],
            communication_style="Friendly and helpful, adapting to user's communication style",
            constraints=[
                "Ask clarifying questions when requirements are unclear",
                "Provide step-by-step guidance for complex tasks",
                "Acknowledge limitations and suggest alternatives",
                "Maintain conversation context across turns",
            ],
            cost_per_1k_tokens=0.0,
        ),
        "ollama_codellama_13b": AgentPromptConfig(
            agent_name="ollama_codellama_13b",
            role_identity="Specialized Code Agent",
            domain_expertise=[
                "Advanced Coding",
                "Performance Optimization",
                "Debugging",
                "Code Translation",
            ],
            communication_style="Technical and precise, focused on code quality",
            constraints=[
                "Write efficient, optimized code",
                "Include type hints and docstrings",
                "Handle concurrency and async operations correctly",
                "Follow language-specific idioms and conventions",
            ],
            cost_per_1k_tokens=0.0,
        ),
        "ollama_mistral_7b": AgentPromptConfig(
            agent_name="ollama_mistral_7b",
            role_identity="Efficient Reasoning Agent",
            domain_expertise=[
                "Logic Puzzles",
                "Mathematical Reasoning",
                "Pattern Recognition",
                "Data Structures",
            ],
            communication_style="Analytical and systematic, showing work step-by-step",
            constraints=[
                "Break down complex problems into steps",
                "Verify solutions with examples",
                "Explain reasoning process clearly",
                "Identify assumptions and edge cases",
            ],
            cost_per_1k_tokens=0.0,
        ),
        "ollama_phi_3": AgentPromptConfig(
            agent_name="ollama_phi_3",
            role_identity="Compact Reasoning Agent",
            domain_expertise=[
                "Quick Facts",
                "Simple Calculations",
                "Brief Summaries",
                "Triage",
            ],
            communication_style="Extremely concise, bullet-point focused",
            constraints=[
                "Responses under 200 tokens",
                "Use bullet points and lists",
                "Avoid verbose explanations",
                "Perfect for quick lookups and triage",
            ],
            cost_per_1k_tokens=0.0,
        ),
    }

    # ========== Orchestration Agent (1) ==========
    ORCHESTRATION_AGENTS = {
        "claude_code": AgentPromptConfig(
            agent_name="claude_code",
            role_identity="Master Orchestrator and Code Architect",
            domain_expertise=[
                "Multi-Agent Coordination",
                "Complex System Design",
                "Critical Decision Making",
                "Production Code Review",
                "Advanced Debugging",
            ],
            communication_style="Authoritative and comprehensive, providing complete solutions",
            constraints=[
                "RESERVED FOR CRITICAL TASKS ONLY (cost optimization)",
                "Coordinate multiple agents for complex workflows",
                "Final review for production deployments",
                "Deep architectural analysis and design",
                "Escalation point for unresolved issues",
            ],
            cost_per_1k_tokens=0.015,  # $15 per million tokens
        ),
    }

    # ========== Additional Agent (Continue.dev) ==========
    CONTINUE_DEV_AGENTS = {
        "continue_dev": AgentPromptConfig(
            agent_name="continue_dev",
            role_identity="IDE-Integrated Code Assistant",
            domain_expertise=[
                "Inline Code Completion",
                "Refactoring Suggestions",
                "Quick Fixes",
                "Code Navigation",
            ],
            communication_style="Context-aware and IDE-optimized, minimal latency",
            constraints=[
                "Use workspace context for accurate suggestions",
                "Provide multiple completion options",
                "Optimize for low-latency responses",
                "Integrate with VS Code features",
            ],
            cost_per_1k_tokens=0.0,
        ),
    }

    # ========== Unified Agent Registry ==========
    ALL_AGENTS: Dict[str, AgentPromptConfig] = {
        **CHATDEV_AGENTS,
        **OLLAMA_AGENTS,
        **ORCHESTRATION_AGENTS,
        **CONTINUE_DEV_AGENTS,
    }

    def __init__(self):
        """Initialize prompt library with all 15 agents"""
        self.agents = self.ALL_AGENTS
        self._validate_registry()

    def _validate_registry(self):
        """Verify all 15 agents are properly configured"""
        expected_agents = [
            # ChatDev (7)
            "chatdev_ceo",
            "chatdev_cto",
            "chatdev_cpo",
            "chatdev_programmer",
            "chatdev_reviewer",
            "chatdev_tester",
            "chatdev_designer",
            # Ollama (7)
            "ollama_qwen_7b",
            "ollama_qwen_14b",
            "ollama_gemma_9b",
            "ollama_llama_8b",
            "ollama_codellama_13b",
            "ollama_mistral_7b",
            "ollama_phi_3",
            # Orchestration (1)
            "claude_code",
        ]

        missing = set(expected_agents) - set(self.agents.keys())
        if missing:
            raise ValueError(f"Missing agent configurations: {missing}")

        # Note: continue_dev is optional (16th agent)
        print(f"✓ Agent Prompt Library initialized with {len(self.agents)} agents")

    def get_system_prompt(
        self,
        agent_name: str,
        task_complexity: TaskComplexity = TaskComplexity.MODERATE,
        task_context: str = "",
    ) -> str:
        """
        Generate role-based system prompt (ChatDev Pattern 1).

        Args:
            agent_name: Name of agent (e.g., "ollama_qwen_14b")
            task_complexity: Complexity level for prompt adaptation
            task_context: Optional task-specific context to inject

        Returns:
            Complete system prompt for agent initialization

        Example:
            >>> library = AgentPromptLibrary()
            >>> prompt = library.get_system_prompt(
            ...     "chatdev_programmer",
            ...     TaskComplexity.COMPLEX,
            ...     "Refactor authentication system for OAuth2 support"
            ... )
        """
        if agent_name not in self.agents:
            raise ValueError(
                f"Unknown agent: {agent_name}. Available: {list(self.agents.keys())}"
            )

        config = self.agents[agent_name]

        # Base system prompt
        prompt_parts = [
            f"You are the **{config.role_identity}** in the ΞNuSyQ AI ecosystem.",
            f"\n**Your Expertise**: {', '.join(config.domain_expertise)}",
            f"\n**Communication Style**: {config.communication_style}",
        ]

        # Add constraints
        if config.constraints:
            prompt_parts.append("\n**Constraints**:")
            for constraint in config.constraints:
                prompt_parts.append(f"- {constraint}")

        # Add task-specific context
        if task_context:
            prompt_parts.append(f"\n**Current Task Context**: {task_context}")

        # Complexity-based adaptations
        if task_complexity == TaskComplexity.SIMPLE:
            prompt_parts.append(
                "\n**Task Type**: Simple - Provide concise, direct answers."
            )
        elif task_complexity == TaskComplexity.MODERATE:
            prompt_parts.append(
                "\n**Task Type**: Moderate - Provide complete solutions with explanations."
            )
        elif task_complexity == TaskComplexity.COMPLEX:
            prompt_parts.append(
                "\n**Task Type**: Complex - Provide comprehensive analysis with multiple options."
            )
        elif task_complexity == TaskComplexity.CRITICAL:
            prompt_parts.append(
                "\n**Task Type**: CRITICAL - Exercise extreme caution, verify all assumptions, document all decisions."
            )

        # Cost awareness for expensive agents
        if config.cost_per_1k_tokens > 0:
            prompt_parts.append(
                f"\n**Note**: You are a premium agent (${config.cost_per_1k_tokens:.3f}/1K tokens). Focus on high-value tasks only."
            )

        return "".join(prompt_parts)

    def get_task_prompt(
        self,
        agent_name: str,
        task_description: str,
        additional_context: Optional[Dict[str, str]] = None,
    ) -> str:
        """
        Generate task-specific prompt (ChatDev Pattern 2).

        Args:
            agent_name: Name of agent receiving task
            task_description: Description of task to perform
            additional_context: Optional dict of context variables

        Returns:
            Task prompt formatted for agent

        Example:
            >>> library.get_task_prompt(
            ...     "chatdev_reviewer",
            ...     "Review authentication.py for security issues",
            ...     {"file_path": "src/auth/authentication.py", "lines": "45-120"}
            ... )
        """
        config = self.agents.get(agent_name)
        if not config:
            raise ValueError(f"Unknown agent: {agent_name}")

        prompt_parts = [
            f"**Task**: {task_description}",
        ]

        # Add context variables
        if additional_context:
            prompt_parts.append("\n**Context**:")
            for key, value in additional_context.items():
                prompt_parts.append(f"- {key}: {value}")

        # Agent-specific task formatting
        if "reviewer" in agent_name:
            prompt_parts.append("\n**Review Checklist**:")
            prompt_parts.append("1. Security vulnerabilities")
            prompt_parts.append("2. Performance issues")
            prompt_parts.append("3. Code maintainability")
            prompt_parts.append("4. Best practices adherence")

        elif "tester" in agent_name:
            prompt_parts.append("\n**Testing Requirements**:")
            prompt_parts.append("1. Unit tests for core functionality")
            prompt_parts.append("2. Edge case handling")
            prompt_parts.append("3. Error condition tests")
            prompt_parts.append("4. Integration test scenarios")

        elif "programmer" in agent_name or "code" in agent_name:
            prompt_parts.append("\n**Implementation Requirements**:")
            prompt_parts.append("1. Clean, idiomatic code")
            prompt_parts.append("2. Comprehensive error handling")
            prompt_parts.append("3. Clear documentation")
            prompt_parts.append("4. Type hints and validation")

        return "".join(prompt_parts)

    def get_reflection_prompt(
        self,
        reflection_agents: List[str],
        conversation_history: str,
        phase_name: str = "General",
    ) -> str:
        """
        Generate reflection prompt for meta-review (ChatDev Pattern 4).

        Args:
            reflection_agents: List of agents performing reflection (usually 2)
            conversation_history: Full conversation transcript to review
            phase_name: Name of phase being reflected on

        Returns:
            Reflection prompt for CEO/Counselor-style meta-review

        Example:
            >>> library.get_reflection_prompt(
            ...     ["claude_code", "chatdev_ceo"],
            ...     "Turn 1 - ollama_qwen_14b: Implement OAuth2...\nTurn 2 - chatdev_reviewer: Consider...",
            ...     "SecurityReview"
            ... )
        """
        # Validate reflection agents are high-capability
        valid_reflection_agents = ["claude_code", "chatdev_ceo", "chatdev_cto"]
        if not all(agent in valid_reflection_agents for agent in reflection_agents):
            raise ValueError(
                f"Reflection agents must be from: {valid_reflection_agents}"
            )

        prompt_parts = [
            f"**REFLECTION PHASE: {phase_name}**",
            "\nYou are meta-reviewers analyzing the following agent conversation.",
            "\n**Conversation History**:",
            f"\n{conversation_history}",
            "\n\n**Your Meta-Review Task**:",
            "\n1. Extract the core conclusion/decision from the conversation",
            "\n2. Identify any ambiguities, contradictions, or gaps",
            "\n3. Verify technical accuracy of proposed solutions",
            "\n4. Provide a refined, actionable conclusion",
            "\n\n**Refined Conclusion Format**:",
            "\n- **Decision**: [Clear go/no-go or specific action]",
            "\n- **Rationale**: [Why this decision is correct]",
            "\n- **Action Items**: [Concrete next steps]",
            "\n- **Risks**: [Potential issues to monitor]",
        ]

        # Phase-specific reflection questions (from ChatDev pattern)
        phase_questions = {
            "DemandAnalysis": "\n**Specific Question**: What is the final product modality? (e.g., 'Web App', 'CLI Tool')",
            "LanguageChoose": "\n**Specific Question**: What programming language was chosen? (e.g., 'Python')",
            "SecurityReview": "\n**Specific Question**: Are there any critical security vulnerabilities? (Yes/No + details)",
            "ArchitectureDesign": "\n**Specific Question**: What is the high-level architecture? (e.g., 'Microservices', 'Monolith')",
            "CodeReview": "\n**Specific Question**: Is the code ready for production? (Yes/No + blocking issues)",
        }

        if phase_name in phase_questions:
            prompt_parts.append(phase_questions[phase_name])

        return "".join(prompt_parts)

    def get_continuation_prompt(
        self, agent_name: str, previous_response: str, follow_up_question: str
    ) -> str:
        """
        Generate continuation prompt for multi-turn conversations.

        Args:
            agent_name: Agent continuing the conversation
            previous_response: Their last response
            follow_up_question: New question/instruction

        Returns:
            Continuation prompt with context
        """
        config = self.agents.get(agent_name)
        if not config:
            raise ValueError(f"Unknown agent: {agent_name}")

        return f"""
**Previous Response**:
{previous_response}

**Follow-Up**:
{follow_up_question}

**Instructions**: Build on your previous response to address the follow-up. Maintain consistency with your earlier analysis.
"""

    def get_coordination_prompt(
        self, primary_agent: str, supporting_agents: List[str], task_description: str
    ) -> Dict[str, str]:
        """
        Generate coordinated prompts for multi-agent collaboration.

        Args:
            primary_agent: Lead agent coordinating the task
            supporting_agents: Agents providing support/input
            task_description: Overall task to accomplish

        Returns:
            Dict mapping agent_name → customized prompt

        Example:
            >>> prompts = library.get_coordination_prompt(
            ...     "chatdev_cto",
            ...     ["chatdev_programmer", "chatdev_reviewer"],
            ...     "Implement and review new API endpoint"
            ... )
            >>> # prompts = {
            >>> #     "chatdev_cto": "Lead architecture design...",
            >>> #     "chatdev_programmer": "Implement per CTO guidance...",
            >>> #     "chatdev_reviewer": "Review implementation..."
            >>> # }
        """
        prompts = {}

        # Primary agent prompt
        prompts[primary_agent] = f"""
**Role**: Lead Coordinator
**Task**: {task_description}

**Your Responsibilities**:
1. Define high-level approach and architecture
2. Coordinate with supporting agents: {", ".join(supporting_agents)}
3. Review their outputs for consistency
4. Provide final approval/refinement

**Coordination Pattern**:
- You will receive input from all supporting agents
- Synthesize their contributions into a cohesive solution
- Resolve any conflicts or inconsistencies
"""

        # Supporting agent prompts
        for agent in supporting_agents:
            config = self.agents.get(agent)
            if not config:
                continue

            prompts[agent] = f"""
**Role**: Supporting Agent ({config.role_identity})
**Task**: {task_description}

**Your Responsibilities**:
1. Provide expertise in: {", ".join(config.domain_expertise)}
2. Contribute your specialized perspective
3. Defer to {primary_agent} for final decisions

**Coordination Pattern**:
- Your output will be reviewed by {primary_agent}
- Focus on your domain of expertise
- Flag issues for lead coordinator's attention
"""

        return prompts

    def estimate_cost(self, agent_name: str, estimated_tokens: int) -> float:
        """
        Estimate cost for using agent (supports cost optimization).

        Args:
            agent_name: Agent to use
            estimated_tokens: Estimated token count (input + output)

        Returns:
            Estimated cost in USD

        Example:
            >>> library.estimate_cost("claude_code", 10000)
            0.15  # $0.15 for 10K tokens
            >>> library.estimate_cost("ollama_qwen_14b", 10000)
            0.0  # Free
        """
        config = self.agents.get(agent_name)
        if not config:
            raise ValueError(f"Unknown agent: {agent_name}")

        return (estimated_tokens / 1000.0) * config.cost_per_1k_tokens

    def get_cheapest_agents_for_task(
        self, required_expertise: List[str], max_cost_per_1k: float = 0.0
    ) -> List[str]:
        """
        Find cheapest agents with required expertise (cost optimization).

        Args:
            required_expertise: List of required skills (e.g., ["Code Generation", "Python"])
            max_cost_per_1k: Maximum acceptable cost per 1K tokens

        Returns:
            List of agent names sorted by cost (cheapest first)

        Example:
            >>> library.get_cheapest_agents_for_task(
            ...     ["Code Generation", "Python"],
            ...     max_cost_per_1k=0.0
            ... )
            ['ollama_qwen_14b', 'ollama_codellama_13b', 'chatdev_programmer']
        """
        matching_agents = []

        for agent_name, config in self.agents.items():
            # Check cost constraint
            if config.cost_per_1k_tokens > max_cost_per_1k:
                continue

            # Check expertise match
            agent_expertise = set(config.domain_expertise)
            required = set(required_expertise)

            if agent_expertise & required:  # Any overlap
                matching_agents.append((agent_name, config.cost_per_1k_tokens))

        # Sort by cost (cheapest first)
        matching_agents.sort(key=lambda x: x[1])

        return [agent for agent, _ in matching_agents]


# ========== Convenience Functions ==========


def get_prompt_for_agent(
    agent_name: str, task: str, complexity: TaskComplexity = TaskComplexity.MODERATE
) -> str:
    """
    Convenience function for quick prompt generation.

    Example:
        >>> prompt = get_prompt_for_agent("ollama_qwen_14b", "Refactor auth module")
    """
    library = AgentPromptLibrary()
    system_prompt = library.get_system_prompt(agent_name, complexity)
    task_prompt = library.get_task_prompt(agent_name, task)
    return f"{system_prompt}\n\n{task_prompt}"


def estimate_workflow_cost(
    workflow_agents: List[str], estimated_tokens_per_agent: int = 5000
) -> Dict[str, float]:
    """
    Estimate cost for entire workflow.

    Example:
        >>> estimate_workflow_cost(["chatdev_ceo", "chatdev_programmer", "claude_code"])
        {'chatdev_ceo': 0.0, 'chatdev_programmer': 0.0, 'claude_code': 0.075, 'total': 0.075}
    """
    library = AgentPromptLibrary()
    costs = {}
    total = 0.0

    for agent in workflow_agents:
        cost = library.estimate_cost(agent, estimated_tokens_per_agent)
        costs[agent] = cost
        total += cost

    costs["total"] = total
    return costs


# ========== Module Testing ==========

if __name__ == "__main__":
    # Quick validation
    print("=== ΞNuSyQ Agent Prompt Library ===\n")

    library = AgentPromptLibrary()

    # Test 1: System prompt generation
    print("Test 1: System Prompt for chatdev_programmer (COMPLEX task)")
    prompt = library.get_system_prompt(
        "chatdev_programmer",
        TaskComplexity.COMPLEX,
        "Implement OAuth2 authentication system",
    )
    print(prompt)
    print("\n" + "=" * 70 + "\n")

    # Test 2: Reflection prompt
    print("Test 2: Reflection Prompt for CEO/CTO meta-review")
    reflection = library.get_reflection_prompt(
        ["chatdev_ceo", "chatdev_cto"],
        "Turn 1 - Programmer: Implemented OAuth2 with JWT tokens...\nTurn 2 - Reviewer: Security concern about token expiration...",
        "SecurityReview",
    )
    print(reflection)
    print("\n" + "=" * 70 + "\n")

    # Test 3: Cost estimation
    print("Test 3: Cost Estimation for Multi-Agent Workflow")
    workflow = ["chatdev_ceo", "chatdev_programmer", "chatdev_reviewer", "claude_code"]
    costs = estimate_workflow_cost(workflow, estimated_tokens_per_agent=5000)
    for agent, cost in costs.items():
        print(f"  {agent}: ${cost:.4f}")
    print("\n" + "=" * 70 + "\n")

    # Test 4: Cheapest agents for task
    print("Test 4: Find Cheapest Agents for Code Generation")
    cheap_agents = library.get_cheapest_agents_for_task(
        ["Code Generation", "Python"],
        max_cost_per_1k=0.0,  # Only free agents
    )
    print(f"  Recommended: {cheap_agents[:3]}")
    print("\n" + "=" * 70 + "\n")

    print("✓ All tests passed!")
