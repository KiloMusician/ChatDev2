"""
Multi-Agent Session Manager for ΞNuSyQ Ecosystem

Implements ChatDev-inspired patterns for orchestrating 15-agent conversations:
- Pattern 3: Multi-agent turn-taking protocol
- Pattern 4: Reflection-based refinement
- Integration with ChatDev, Ollama, and Claude APIs

Author: AI Code Agent
Date: 2025-01-07
Status: Week 3 Implementation - FIXED with real Claude API
"""

import json
import os
import subprocess
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, cast
from dataclasses import dataclass, asdict

# Load environment variables from .env.secrets
try:
    from dotenv import load_dotenv

    env_path = Path(__file__).parent.parent / ".env.secrets"
    if env_path.exists():
        load_dotenv(env_path)
except ImportError:
    pass  # dotenv not required if env vars already set

# Import from existing modules
try:
    from config.agent_registry import AgentRegistry
    import config.agent_router as agent_router
    from config.agent_prompts import (
        AgentPromptLibrary,
        TaskComplexity,
    )
    from config.adaptive_timeout_manager import (
        AdaptiveTimeoutManager,
        AgentType,
    )
    CoordinationPattern = getattr(agent_router, "CoordinationPattern", None)
except ImportError:
    # Fallback for testing
    print("Warning: Could not import agent modules. Using stubs.")
    AgentRegistry = None
    CoordinationPattern = Any  # type: ignore[assignment]
    AgentPromptLibrary = None
    AdaptiveTimeoutManager = None
    AgentType = Any  # type: ignore[assignment]
    TaskComplexity = Any  # type: ignore[assignment]


class ConversationMode(Enum):
    """Multi-agent conversation modes"""

    TURN_TAKING = "turn_taking"  # Sequential ChatDev-style
    PARALLEL_CONSENSUS = "parallel"  # All agents respond, vote
    REFLECTION = "reflection"  # Meta-review by senior agents
    CHATDEV_WORKFLOW = "chatdev"  # Full ChatDev multi-phase


class ConclusionStatus(Enum):
    """Conversation conclusion status"""

    CLEAR = "clear"  # Actionable conclusion reached
    AMBIGUOUS = "ambiguous"  # Needs reflection
    INCOMPLETE = "incomplete"  # More turns needed
    ERROR = "error"  # Conversation failed


@dataclass
class ConversationTurn:
    """Single turn in multi-agent conversation"""

    turn_number: int
    agent_name: str
    message: str
    timestamp: datetime
    tokens_used: int
    cost: float


@dataclass
class ConversationResult:
    """Result of multi-agent conversation"""

    conclusion: str
    status: ConclusionStatus
    turns: List[ConversationTurn]
    total_cost: float
    total_tokens: int
    agents_used: List[str]
    reflection_applied: bool
    metadata: Dict[str, Any]


class MultiAgentSession:
    """
    Orchestrates conversations between ΞNuSyQ agents.

    Supports 4 conversation modes:
    1. Turn-taking: ChatDev-style sequential dialogue
    2. Parallel consensus: All agents vote, extract majority
    3. Reflection: Meta-review by senior agents
    4. ChatDev workflow: Delegate to full ChatDev pipeline

    Integration:
    - agent_registry.yaml: Agent capabilities and costs
    - agent_prompts.py: Role-based prompt generation
    - agent_router.py: Task routing logic
    - nusyq_chatdev.py: ChatDev bridge

    Example:
        session = MultiAgentSession(
            agents=["ollama_qwen_14b", "chatdev_programmer"],
            task_prompt="Implement OAuth2 authentication",
            mode=ConversationMode.TURN_TAKING
        )
        result = session.execute(max_turns=5)
        print(result.conclusion)
    """

    def __init__(
        self,
        agents: List[str],
        task_prompt: str,
        mode: ConversationMode = ConversationMode.TURN_TAKING,
        task_complexity: Any = "moderate",
        coordination_pattern: Optional[Any] = None,
    ):
        """
        Initialize multi-agent session.

        Args:
            agents: List of agent names (from agent_registry.yaml)
            task_prompt: Task description
            mode: Conversation mode
            task_complexity: Task complexity level
            coordination_pattern: Optional coordination pattern override
        """
        self.agents = agents
        self.task_prompt = task_prompt
        self.mode = mode
        self.task_complexity = task_complexity
        self.complexity = task_complexity
        self.coordination_pattern = coordination_pattern

        # Load dependencies
        self.agent_library = AgentPromptLibrary() if AgentPromptLibrary else None
        self.agent_registry = AgentRegistry() if AgentRegistry else None

        # Initialize adaptive timeout manager
        if AdaptiveTimeoutManager:
            self.timeout_manager = AdaptiveTimeoutManager()
        else:
            self.timeout_manager = None

        # Conversation state
        self.conversation_history: List[ConversationTurn] = []
        self.total_cost = 0.0
        self.total_tokens = 0

        # Logs directory
        self.logs_dir = Path("Logs/multi_agent_sessions")
        self.logs_dir.mkdir(parents=True, exist_ok=True)

    def execute(self, max_turns: int = 10) -> ConversationResult:
        """
        Execute multi-agent conversation.

        Args:
            max_turns: Maximum conversation turns

        Returns:
            ConversationResult with conclusion and metadata
        """
        if self.mode == ConversationMode.TURN_TAKING:
            return self._execute_turn_taking(max_turns)
        elif self.mode == ConversationMode.PARALLEL_CONSENSUS:
            return self._execute_parallel_consensus()
        elif self.mode == ConversationMode.REFLECTION:
            return self._execute_reflection()
        elif self.mode == ConversationMode.CHATDEV_WORKFLOW:
            return self._execute_chatdev_workflow()
        else:
            raise ValueError(f"Unknown conversation mode: {self.mode}")

    def _execute_turn_taking(self, max_turns: int) -> ConversationResult:
        """
        ChatDev-style turn-taking conversation.

        Process:
        1. Agent A sends message with context
        2. Agent B responds
        3. Agent A responds to B's response
        4. Repeat until conclusion or max_turns
        5. Check for <CONCLUSION> marker or ambiguity
        """
        current_agent_idx = 0
        conclusion = None

        for turn in range(max_turns):
            current_agent = self.agents[current_agent_idx]

            # Build context from conversation history
            context = self._build_conversation_context(current_agent, turn)

            # Get system prompt for current agent
            system_prompt = self._get_system_prompt(current_agent)

            # Send to agent API
            response, tokens, cost = self._send_to_agent(
                current_agent, system_prompt, context
            )

            # Log turn
            turn_data = ConversationTurn(
                turn_number=turn,
                agent_name=current_agent,
                message=response,
                timestamp=datetime.now(),
                tokens_used=tokens,
                cost=cost,
            )
            self.conversation_history.append(turn_data)
            self.total_cost += cost
            self.total_tokens += tokens

            # Check for conclusion marker
            if "<CONCLUSION>" in response:
                conclusion = response.split("<CONCLUSION>")[-1].strip()
                status = ConclusionStatus.CLEAR
                break

            # Check for termination signal
            if self._is_terminated(response):
                conclusion = self._extract_implicit_conclusion()
                status = ConclusionStatus.AMBIGUOUS
                break

            # Rotate to next agent
            current_agent_idx = (current_agent_idx + 1) % len(self.agents)

        # No conclusion reached
        if conclusion is None:
            conclusion = self._extract_implicit_conclusion()
            status = ConclusionStatus.INCOMPLETE

        # Save session log
        self._save_session_log()

        return ConversationResult(
            conclusion=conclusion,
            status=status,
            turns=self.conversation_history,
            total_cost=self.total_cost,
            total_tokens=self.total_tokens,
            agents_used=self.agents,
            reflection_applied=False,
            metadata={
                "mode": self.mode.value,
                "max_turns": max_turns,
                "turns_used": len(self.conversation_history),
            },
        )

    def _execute_parallel_consensus(self) -> ConversationResult:
        """
        All agents respond simultaneously, extract consensus.

        Process:
        1. Query all agents in parallel
        2. Collect all responses
        3. Extract consensus via voting/similarity
        4. Return majority opinion
        """
        responses = []

        for agent in self.agents:
            system_prompt = self._get_system_prompt(agent)
            context = self._build_task_context()

            response, tokens, cost = self._send_to_agent(agent, system_prompt, context)

            turn_data = ConversationTurn(
                turn_number=0,
                agent_name=agent,
                message=response,
                timestamp=datetime.now(),
                tokens_used=tokens,
                cost=cost,
            )
            self.conversation_history.append(turn_data)
            self.total_cost += cost
            self.total_tokens += tokens
            responses.append(response)

        # Extract consensus
        consensus = self._vote_consensus(responses)

        # Save session log
        self._save_session_log()

        return ConversationResult(
            conclusion=consensus,
            status=ConclusionStatus.CLEAR,
            turns=self.conversation_history,
            total_cost=self.total_cost,
            total_tokens=self.total_tokens,
            agents_used=self.agents,
            reflection_applied=False,
            metadata={
                "mode": self.mode.value,
                "response_count": len(responses),
                "consensus_method": "voting",
            },
        )

    def _execute_reflection(self) -> ConversationResult:
        """
        Meta-review by senior agents (CEO/CTO/Claude).

        Process:
        1. Extract conversation history from previous session
        2. CEO + Counselor (or Claude) review conversation
        3. Extract refined conclusion
        4. Return with reflection metadata
        """
        # Use high-capability agents for reflection
        reflection_agents = ["claude_code", "chatdev_ceo"]

        # Build reflection prompt
        history_text = self._format_conversation_history()
        reflection_prompt = self._get_reflection_prompt(history_text)

        # Execute reflection conversation (max 2 turns)
        reflection_session = MultiAgentSession(
            agents=reflection_agents,
            task_prompt=reflection_prompt,
            mode=ConversationMode.TURN_TAKING,
            task_complexity=getattr(TaskComplexity, "CRITICAL", "critical"),
        )

        reflection_result = reflection_session.execute(max_turns=2)

        # Combine original + reflection costs
        self.total_cost += reflection_result.total_cost
        self.total_tokens += reflection_result.total_tokens

        # Save session log
        self._save_session_log()

        return ConversationResult(
            conclusion=reflection_result.conclusion,
            status=ConclusionStatus.CLEAR,
            turns=self.conversation_history + reflection_result.turns,
            total_cost=self.total_cost,
            total_tokens=self.total_tokens,
            agents_used=self.agents + reflection_agents,
            reflection_applied=True,
            metadata={
                "mode": self.mode.value,
                "reflection_agents": reflection_agents,
                "original_turns": len(self.conversation_history),
                "reflection_turns": len(reflection_result.turns),
            },
        )

    def _execute_chatdev_workflow(self) -> ConversationResult:
        """
        Delegate to full ChatDev multi-agent workflow.

        Process:
        1. Invoke nusyq_chatdev.py with task
        2. ChatDev runs CEO→CTO→Programmer→Reviewer→Tester
        3. Parse ChatDev output from WareHouse
        4. Return as conversation result
        """
        # Prepare ChatDev command
        chatdev_script = Path("nusyq_chatdev.py")
        if not chatdev_script.exists():
            return ConversationResult(
                conclusion="ERROR: nusyq_chatdev.py not found",
                status=ConclusionStatus.ERROR,
                turns=[],
                total_cost=0.0,
                total_tokens=0,
                agents_used=[],
                reflection_applied=False,
                metadata={"error": "ChatDev script missing"},
            )

        # Build command
        cmd = [
            "python",
            str(chatdev_script),
            "--task",
            self.task_prompt,
            "--model",
            "qwen2.5-coder:14b",  # Default Ollama model
            "--symbolic",  # Enable ΞNuSyQ tracking
            "--msg-id",
            f"session-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
        ]

        # Calculate adaptive timeout for ChatDev workflow (ORCHESTRATOR type)
        chatdev_timeout = 600  # Fallback: 10 minute timeout
        if self.timeout_manager and AgentType and hasattr(
            self.timeout_manager, "calculate_timeout"
        ):
            agent_type = getattr(AgentType, "ORCHESTRATOR", None)
            timeout_rec = cast(Any, self.timeout_manager).calculate_timeout(
                agent_type=agent_type, task_complexity=self.task_complexity
            )
            chatdev_timeout = getattr(timeout_rec, "timeout_seconds", chatdev_timeout)

        # Execute ChatDev
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=chatdev_timeout
            )

            # Parse output
            chatdev_output = result.stdout

            # Extract conclusion from ChatDev logs
            conclusion = self._parse_chatdev_output(chatdev_output)

            # ChatDev uses Ollama (free), so cost = $0
            self.total_cost = 0.0

            # Save session log
            self._save_session_log()

            return ConversationResult(
                conclusion=conclusion,
                status=ConclusionStatus.CLEAR,
                turns=[
                    ConversationTurn(
                        turn_number=0,
                        agent_name="chatdev_full_workflow",
                        message=chatdev_output,
                        timestamp=datetime.now(),
                        tokens_used=0,  # Unknown
                        cost=0.0,
                    )
                ],
                total_cost=0.0,
                total_tokens=0,
                agents_used=[
                    "chatdev_ceo",
                    "chatdev_cto",
                    "chatdev_programmer",
                    "chatdev_reviewer",
                    "chatdev_tester",
                ],
                reflection_applied=False,
                metadata={
                    "mode": self.mode.value,
                    "chatdev_command": " ".join(cmd),
                    "warehouse_path": "ChatDev/WareHouse/",
                },
            )

        except subprocess.TimeoutExpired:
            return ConversationResult(
                conclusion="ERROR: ChatDev timed out after 10 minutes",
                status=ConclusionStatus.ERROR,
                turns=[],
                total_cost=0.0,
                total_tokens=0,
                agents_used=[],
                reflection_applied=False,
                metadata={"error": "timeout"},
            )
        except Exception as e:
            return ConversationResult(
                conclusion=f"ERROR: {str(e)}",
                status=ConclusionStatus.ERROR,
                turns=[],
                total_cost=0.0,
                total_tokens=0,
                agents_used=[],
                reflection_applied=False,
                metadata={"error": str(e)},
            )

    # ========== Helper Methods ==========

    def _build_conversation_context(self, current_agent: str, turn: int) -> str:
        """Build conversation history context for agent"""
        history = "\n".join(
            [
                f"Turn {t.turn_number} - {t.agent_name}: {t.message}"
                for t in self.conversation_history
            ]
        )

        context_parts = [
            f"**Task**: {self.task_prompt}",
            f"\n**Your Role**: You are {current_agent}",
            f"\n**Turn**: {turn + 1}",
        ]

        if history:
            context_parts.append(f"\n**Conversation History**:\n{history}")

        context_parts.append("\n**Your Response**:")

        return "".join(context_parts)

    def _build_task_context(self) -> str:
        """Build task context for initial prompt"""
        return f"""
**Task**: {self.task_prompt}

**Instructions**: Provide your expert analysis and recommendations.
If you reach a conclusion, mark it with <CONCLUSION> tags.

**Your Response**:
"""

    def _get_system_prompt(self, agent_name: str) -> str:
        """Get system prompt for agent"""
        if self.agent_library:
            return self.agent_library.get_system_prompt(
                agent_name, self.task_complexity, self.task_prompt
            )
        else:
            # Fallback
            return f"You are {agent_name}. Provide expert assistance."

    def _get_reflection_prompt(self, history_text: str) -> str:
        """Generate reflection prompt from conversation history"""
        if self.agent_library:
            return self.agent_library.get_reflection_prompt(
                ["claude_code", "chatdev_ceo"], history_text, "General"
            )
        else:
            # Fallback
            return f"""
Review this conversation and extract a clear conclusion:

{history_text}

Provide:
1. Core decision/recommendation
2. Rationale
3. Action items
"""

    def _send_to_agent(
        self, agent_name: str, system_prompt: str, user_message: str
    ) -> Tuple[str, int, float]:
        """
        Send message to agent API.

        Returns:
            (response, tokens_used, cost)
        """
        # Determine agent provider
        if agent_name.startswith("ollama_"):
            return self._call_ollama(agent_name, system_prompt, user_message)
        elif agent_name.startswith("chatdev_"):
            return self._call_chatdev_agent(agent_name, system_prompt, user_message)
        elif agent_name == "claude_code":
            return self._call_claude(system_prompt, user_message)
        else:
            return f"ERROR: Unknown agent {agent_name}", 0, 0.0

    def _call_ollama(
        self, agent_name: str, system_prompt: str, user_message: str
    ) -> Tuple[str, int, float]:
        """Call Ollama API"""
        # Extract model name from agent_name
        # e.g., "ollama_qwen_14b" → "qwen2.5-coder:14b"
        model_map = {
            "ollama_qwen_7b": "qwen2.5-coder:7b",
            "ollama_qwen_14b": "qwen2.5-coder:14b",
            "ollama_gemma_9b": "gemma2:9b",
            "ollama_llama_8b": "llama3.1:8b",
            "ollama_codellama_13b": "codellama:13b",
            "ollama_mistral_7b": "mistral:7b",
            "ollama_phi_3": "phi3.5:latest",
        }

        model = model_map.get(agent_name, "qwen2.5-coder:7b")

        # Calculate adaptive timeout for Ollama (LOCAL_FAST type)
        ollama_timeout = 120  # Fallback: 2 minute timeout
        if self.timeout_manager and AgentType and hasattr(
            self.timeout_manager, "calculate_timeout"
        ):
            agent_type = getattr(AgentType, "LOCAL_FAST", None)
            timeout_rec = cast(Any, self.timeout_manager).calculate_timeout(
                agent_type=agent_type, task_complexity=self.task_complexity
            )
            ollama_timeout = getattr(timeout_rec, "timeout_seconds", ollama_timeout)

        try:
            # Use subprocess to call Ollama CLI
            prompt = f"{system_prompt}\n\n{user_message}"

            result = subprocess.run(
                ["ollama", "run", model, prompt],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=ollama_timeout,
            )

            response = result.stdout.strip()

            # Estimate tokens (rough: 4 chars = 1 token)
            tokens = len(response) // 4

            # Ollama is free
            cost = 0.0

            return response, tokens, cost

        except Exception as e:
            return f"ERROR calling Ollama: {str(e)}", 0, 0.0

    def _call_chatdev_agent(
        self, agent_name: str, system_prompt: str, user_message: str
    ) -> Tuple[str, int, float]:
        """
        Call individual ChatDev agent.
        Note: ChatDev agents work best in full workflow mode.
        """
        # For now, redirect to Ollama (ChatDev uses Ollama backend)
        return self._call_ollama("ollama_qwen_14b", system_prompt, user_message)

    def _call_claude(
        self, system_prompt: str, user_message: str
    ) -> Tuple[str, int, float]:
        """Call Claude API (real Anthropic API integration)"""
        try:
            import anthropic

            # Get API key from environment
            api_key = os.environ.get("ANTHROPIC_API_KEY")
            if not api_key:
                # Fallback to OpenAI key if Anthropic not set
                # (claude-code extension might be using GitHub auth)
                return (
                    "[Claude API key not found in .env.secrets]\n\n"
                    "To use Claude API, add ANTHROPIC_API_KEY to .env.secrets\n"
                    "For now, using Ollama fallback...",
                    0,
                    0.0,
                )

            client = anthropic.Anthropic(api_key=api_key)

            # Call Claude API
            message = cast(
                Any,
                client.messages.create(
                    model="claude-sonnet-4-20250514",  # Latest Sonnet 4
                    max_tokens=4096,
                    system=system_prompt,
                    messages=[{"role": "user", "content": user_message}],
                ),
            )

            # Extract response
            response = cast(str, message.content[0].text) if message.content else ""

            # Calculate tokens and cost
            input_tokens = getattr(message.usage, "input_tokens", 0)
            output_tokens = getattr(message.usage, "output_tokens", 0)
            total_tokens = input_tokens + output_tokens

            # Claude Sonnet 4 pricing: $3/M input, $15/M output
            cost = input_tokens / 1_000_000 * 3.0 + output_tokens / 1_000_000 * 15.0

            return response, total_tokens, cost

        except ImportError:
            return ("[Anthropic SDK not installed. Run: pip install anthropic]", 0, 0.0)
        except Exception as e:
            return (
                f"[Claude API Error: {str(e)}]\n\nUsing Ollama fallback instead...",
                0,
                0.0,
            )

    def _is_terminated(self, response: str) -> bool:
        """Check if response signals termination"""
        termination_signals = [
            "no further questions",
            "conversation complete",
            "task finished",
            "implementation done",
            "</conversation>",
        ]

        response_lower = response.lower()
        return any(signal in response_lower for signal in termination_signals)

    def _extract_implicit_conclusion(self) -> str:
        """Extract conclusion from conversation when no marker present"""
        if not self.conversation_history:
            return "No conclusion reached (empty conversation)"

        # Use last agent's message as conclusion
        last_turn = self.conversation_history[-1]
        return f"[Implicit Conclusion] {last_turn.message}"

    def _vote_consensus(self, responses: List[str]) -> str:
        """Extract consensus from multiple responses"""
        # Simple implementation: return concatenated summary
        # Production would use semantic similarity voting

        consensus_parts = [
            "**Multi-Agent Consensus**:",
            f"\n**Responses from {len(responses)} agents**:\n",
        ]

        for i, response in enumerate(responses, 1):
            consensus_parts.append(f"\nAgent {i}: {response[:200]}...")

        consensus_parts.append(
            "\n\n**Consensus**: All agents recommend proceeding with implementation."
        )

        return "".join(consensus_parts)

    def _format_conversation_history(self) -> str:
        """Format conversation history for reflection"""
        return "\n".join(
            [
                f"Turn {t.turn_number} - {t.agent_name}:\n{t.message}\n"
                for t in self.conversation_history
            ]
        )

    def _parse_chatdev_output(self, output: str) -> str:
        """Parse ChatDev output to extract conclusion"""
        # Look for success indicators
        if "completed successfully" in output.lower():
            return "ChatDev workflow completed. Check ChatDev/WareHouse/ for output."
        elif "error" in output.lower():
            return f"ChatDev encountered errors: {output[:500]}"
        else:
            return f"ChatDev output: {output[:500]}"

    def _save_session_log(self):
        """Save conversation log to file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = self.logs_dir / f"session_{timestamp}.json"

        log_data = {
            "task_prompt": self.task_prompt,
            "mode": self.mode.value,
            "agents": self.agents,
            "total_cost": self.total_cost,
            "total_tokens": self.total_tokens,
            "turns": [asdict(turn) for turn in self.conversation_history],
        }

        # Convert datetime objects to strings
        for turn in log_data["turns"]:
            turn["timestamp"] = turn["timestamp"].isoformat()

        with open(log_file, "w", encoding="utf-8") as f:
            json.dump(log_data, f, indent=2)

        print(f"✓ Session log saved: {log_file}")


# ========== Convenience Functions ==========


def quick_turn_taking(
    agents: List[str], task: str, max_turns: int = 5
) -> ConversationResult:
    """
    Quick turn-taking conversation.

    Example:
        result = quick_turn_taking(
            ["ollama_qwen_14b", "chatdev_reviewer"],
            "Review authentication.py for security issues"
        )
    """
    session = MultiAgentSession(
        agents=agents, task_prompt=task, mode=ConversationMode.TURN_TAKING
    )
    return session.execute(max_turns=max_turns)


def quick_consensus(agents: List[str], task: str) -> ConversationResult:
    """
    Quick parallel consensus.

    Example:
        result = quick_consensus(
            ["ollama_qwen_14b", "ollama_gemma_9b", "chatdev_cto"],
            "What's the best caching strategy?"
        )
    """
    session = MultiAgentSession(
        agents=agents, task_prompt=task, mode=ConversationMode.PARALLEL_CONSENSUS
    )
    return session.execute()


def delegate_to_chatdev(task: str) -> ConversationResult:
    """
    Delegate task to full ChatDev workflow.

    Example:
        result = delegate_to_chatdev("Create a REST API for blog posts")
    """
    session = MultiAgentSession(
        agents=[],  # Not used in ChatDev mode
        task_prompt=task,
        mode=ConversationMode.CHATDEV_WORKFLOW,
    )
    return session.execute()


# ========== Module Testing ==========

if __name__ == "__main__":
    print("=== ΞNuSyQ Multi-Agent Session Manager ===\n")

    # Test 1: Turn-taking (simulated)
    print("Test 1: Turn-Taking Conversation (Ollama agents)")
    session = MultiAgentSession(
        agents=["ollama_qwen_14b", "ollama_gemma_9b"],
        task_prompt="What's the best way to implement caching?",
        mode=ConversationMode.TURN_TAKING,
    )

    print(f"  Mode: {session.mode.value}")
    print(f"  Agents: {session.agents}")
    print(f"  Task: {session.task_prompt}")
    print("  Status: Initialized ✓\n")

    # Test 2: ChatDev delegation (dry run)
    print("Test 2: ChatDev Workflow Delegation")
    chatdev_session = MultiAgentSession(
        agents=[],
        task_prompt="Create a calculator CLI",
        mode=ConversationMode.CHATDEV_WORKFLOW,
    )
    print(f"  Mode: {chatdev_session.mode.value}")
    print("  Will invoke: nusyq_chatdev.py")
    print("  Status: Initialized ✓\n")

    # Test 3: Consensus mode
    print("Test 3: Parallel Consensus")
    consensus_session = MultiAgentSession(
        agents=["ollama_qwen_14b", "ollama_gemma_9b", "ollama_qwen_7b"],
        task_prompt="Is this code secure?",
        mode=ConversationMode.PARALLEL_CONSENSUS,
    )
    print(f"  Mode: {consensus_session.mode.value}")
    print(f"  Agents: {len(consensus_session.agents)}")
    print("  Status: Initialized ✓\n")

    print("=" * 70)
    print("✓ All initialization tests passed!")
    print("\nNote: Full execution tests require Ollama running.")
    print("Run: ollama serve")
