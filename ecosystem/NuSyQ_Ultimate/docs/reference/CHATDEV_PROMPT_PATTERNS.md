# ChatDev Prompt Engineering Patterns - Extracted for ΞNuSyQ Integration

**Date**: 2025-01-07
**Source**: ChatDev/camel/prompts/* and ChatDev/chatdev/*
**Purpose**: Document reusable prompt engineering patterns from ChatDev for adaptation to ΞNuSyQ's 15-agent ecosystem

---

## Executive Summary

ChatDev implements a sophisticated multi-agent conversation framework with **4 core prompt engineering patterns**:

1. **Role-Based System Prompts**: Each agent has a distinct personality/expertise defined by RoleType
2. **Task Decomposition Templates**: Complex tasks broken into agent-sized workflow phases
3. **Multi-Agent Communication Protocol**: Structured turn-taking with context passing and seminar conclusions
4. **Incremental Refinement via Reflection**: CEO/Counselor meta-layer reviews conversations and extracts conclusions

These patterns enable ChatDev's 7 agents (CEO, CTO, CPO, Programmer, Reviewer, Tester, Designer) to collaborate on full software development cycles. We will adapt these for ΞNuSyQ's broader ecosystem (15 agents across Ollama, ChatDev, Claude, Continue.dev).

---

## Pattern 1: Role-Based System Prompts

### Implementation in ChatDev

**File**: `camel/prompts/prompt_templates.py`

```python
class PromptTemplateGenerator:
    def get_system_prompt(task_type: TaskType, role_type: RoleType) -> TextPrompt:
        """
        Generate role-specific system prompt based on task type and role type.
        Returns "You are a helpful assistant" if no specific template found.
        """
        # Maps TaskType (AI_SOCIETY, CODE, CHATDEV) + RoleType (USER, ASSISTANT) → TextPrompt
```

**Key Characteristics**:
- Each agent receives a **system prompt** defining:
  - Role identity (e.g., "Chief Technology Officer", "Code Reviewer")
  - Domain expertise (e.g., "expert in Python backend development")
  - Communication style (e.g., "concise and technical", "comprehensive and educational")
  - Constraints (e.g., "do not write code, only review it")

**File**: `chatdev/phase.py` - Role prompt usage

```python
# Each Phase initialized with role-specific prompts
self.assistant_role_prompt = role_prompts[assistant_role_name]  # e.g., "Chief Technology Officer"
self.user_role_prompt = role_prompts[user_role_name]            # e.g., "Programmer"

# RolePlaying session receives both prompts
role_play_session = RolePlaying(
    assistant_role_name=assistant_role_name,
    user_role_name=user_role_name,
    assistant_role_prompt=assistant_role_prompt,  # System prompt for receiving agent
    user_role_prompt=user_role_prompt,            # System prompt for initiating agent
    task_prompt=task_prompt,                      # Current task context
    task_type=task_type,
    background_prompt=chat_env.config.background_prompt  # Global project context
)
```

### Adaptation for ΞNuSyQ

**Implementation**: Create `config/agent_prompts.py` with `AgentPromptLibrary` class

```python
# Proposed structure
class AgentPromptLibrary:
    """Centralized prompt management for 15-agent ΞNuSyQ ecosystem"""

    SYSTEM_PROMPTS = {
        # ChatDev agents (7)
        "chatdev_ceo": "You are the Chief Executive Officer...",
        "chatdev_cto": "You are the Chief Technology Officer...",
        # ... (5 more ChatDev agents)

        # Ollama agents (7)
        "ollama_qwen_7b": "You are a lightweight reasoning agent...",
        "ollama_qwen_14b": "You are a medium-scale code generation agent...",
        "ollama_gemma_9b": "You are a general-purpose analysis agent...",
        # ... (4 more Ollama agents)

        # Orchestration agent (1)
        "claude_code": "You are the master orchestrator coordinating 14 specialized agents..."
    }

    TASK_CONSTRAINTS = {
        # Per-agent constraints
        "chatdev_reviewer": ["Do not write code", "Focus on quality analysis", "Suggest specific improvements"],
        "ollama_qwen_7b": ["Keep responses concise", "Prefer local reasoning over web search"],
        # ...
    }

    def get_system_prompt(self, agent_name: str, task_context: str = "") -> str:
        """Generate role-specific system prompt with optional task context"""
        base_prompt = self.SYSTEM_PROMPTS.get(agent_name, "You are a helpful assistant.")
        constraints = " ".join(self.TASK_CONSTRAINTS.get(agent_name, []))

        if task_context:
            return f"{base_prompt}\n\nCurrent Task Context: {task_context}\n\nConstraints: {constraints}"
        return f"{base_prompt}\n\nConstraints: {constraints}"
```

**Benefits for ΞNuSyQ**:
- **Consistency**: All 15 agents have well-defined roles preventing overlap
- **Specialization**: Each agent optimized for specific capabilities (from agent_registry.yaml)
- **Cost Optimization**: Constraints prevent over-capable agents from simple tasks (e.g., Claude reserved for critical work)

---

## Pattern 2: Task Decomposition Templates

### Implementation in ChatDev

**File**: `camel/prompts/task_prompt_template.py`

```python
TaskPromptTemplateDict: Dict[TaskType, TextPromptDict]
# Maps high-level TaskType to structured prompt dictionaries

# Example TaskTypes:
# - AI_SOCIETY: General multi-agent collaboration
# - CODE: Software development workflow
# - MISALIGNMENT: Detecting agent disagreements
# - etc.
```

**File**: `chatdev/composed_phase.py` - Multi-phase workflows

```python
class ComposedPhase:
    """
    Decomposes complex tasks into sequential SimplePhases.
    Each cycle executes multiple phases in order.
    """
    def __init__(self, phase_name, cycle_num, composition, config_phase):
        self.composition = composition  # List of SimplePhase configs
        self.cycle_num = cycle_num      # How many times to loop through phases

        # Example composition:
        # [
        #   {"phase": "DemandAnalysis", "max_turn_step": 3, "need_reflect": True},
        #   {"phase": "LanguageChoose", "max_turn_step": 2, "need_reflect": False},
        #   {"phase": "Coding", "max_turn_step": 5, "need_reflect": True}
        # ]
```

**Workflow Phases in ChatDev**:
1. **DemandAnalysis**: CEO ↔ CPO analyze user requirements
2. **LanguageChoose**: CEO ↔ CTO select programming language
3. **Coding**: CTO ↔ Programmer implement features
4. **CodeReview**: CTO ↔ Reviewer check code quality
5. **Testing**: Programmer ↔ Tester write/run tests
6. **EnvironmentDoc**: Generate requirements.txt

### Adaptation for ΞNuSyQ

**Implementation**: Extend `config/agent_router.py` with `WorkflowDecomposer`

```python
class WorkflowDecomposer:
    """
    Break complex ΞNuSyQ tasks into agent-executable phases.
    Uses agent_registry.yaml capabilities to route each phase.
    """

    WORKFLOW_TEMPLATES = {
        "full_software_project": [
            {"phase": "requirements_analysis", "agents": ["chatdev_ceo", "ollama_gemma_9b"], "turns": 3},
            {"phase": "architecture_design", "agents": ["chatdev_cto", "ollama_qwen_14b"], "turns": 5},
            {"phase": "implementation", "agents": ["chatdev_programmer", "ollama_qwen_14b"], "turns": 10},
            {"phase": "code_review", "agents": ["chatdev_reviewer", "ollama_qwen_7b"], "turns": 3},
            {"phase": "testing", "agents": ["chatdev_tester", "ollama_gemma_9b"], "turns": 5},
            {"phase": "documentation", "agents": ["ollama_gemma_9b"], "turns": 2}
        ],

        "code_refactoring": [
            {"phase": "code_analysis", "agents": ["chatdev_cto", "ollama_qwen_14b"], "turns": 2},
            {"phase": "refactor_plan", "agents": ["chatdev_programmer", "claude_code"], "turns": 3},
            {"phase": "implementation", "agents": ["chatdev_programmer"], "turns": 5},
            {"phase": "validation", "agents": ["chatdev_reviewer", "chatdev_tester"], "turns": 2}
        ],

        "neural_network_training": [  # For LONG-TERM goal
            {"phase": "data_preparation", "agents": ["ollama_qwen_14b"], "turns": 3},
            {"phase": "architecture_design", "agents": ["chatdev_cto", "claude_code"], "turns": 5},
            {"phase": "training_loop", "agents": ["ollama_qwen_14b"], "turns": 10},
            {"phase": "evaluation", "agents": ["ollama_gemma_9b"], "turns": 3}
        ]
    }

    def decompose_task(self, task_description: str, task_type: TaskType) -> List[PhaseConfig]:
        """
        Analyze task_description and return list of phases with assigned agents.
        Uses agent_router to select optimal agents per phase.
        """
        template = self.WORKFLOW_TEMPLATES.get(task_type, self._generate_custom_workflow(task_description))
        return [self._configure_phase(phase) for phase in template]
```

**Benefits for ΞNuSyQ**:
- **Scalability**: New workflow templates easily added for expanding capabilities
- **Flexibility**: Dynamic phase generation for tasks not matching templates
- **Traceability**: Each phase logged with participating agents and turn limits

---

## Pattern 3: Multi-Agent Communication Protocol

### Implementation in ChatDev

**File**: `chatdev/phase.py` - `chatting()` method (lines 48-176)

```python
def chatting(self, chat_env, task_prompt, assistant_role_name, user_role_name,
             phase_prompt, chat_turn_limit=10) -> str:
    """
    Core multi-agent conversation protocol:
    1. Initialize RolePlaying session with two agents
    2. Loop up to chat_turn_limit turns:
       a) User agent sends message → Assistant agent responds
       b) Assistant agent sends message → User agent responds
    3. Extract "seminar conclusion" (consensus decision) from conversation
    4. Optionally trigger self-reflection for refinement
    """

    # Init conversation
    role_play_session = RolePlaying(
        assistant_role_name=assistant_role_name,
        user_role_name=user_role_name,
        assistant_role_prompt=assistant_role_prompt,
        user_role_prompt=user_role_prompt,
        task_prompt=task_prompt,  # Shared context
        background_prompt=chat_env.config.background_prompt  # Global project state
    )

    _, input_user_msg = role_play_session.init_chat(None, placeholders, phase_prompt)
    seminar_conclusion = None

    # Turn-taking conversation
    for i in range(chat_turn_limit):
        assistant_response, user_response = role_play_session.step(input_user_msg)

        # Check for <INFO> marker indicating conclusion reached
        if role_play_session.assistant_agent.info:
            seminar_conclusion = assistant_response.msg.content
            break
        if role_play_session.user_agent.info:
            seminar_conclusion = user_response.msg.content
            break

        # Check for termination signals
        if assistant_response.terminated or user_response.terminated:
            break

        # Continue conversation
        input_user_msg = user_response.msg

    # Extract conclusion (removes <INFO> marker)
    seminar_conclusion = seminar_conclusion.split("<INFO>")[-1]
    return seminar_conclusion
```

**Key Protocol Features**:
1. **Turn-Taking**: Agents alternate sending messages (user → assistant → user → ...)
2. **Shared Context**: All agents receive `task_prompt` + `background_prompt` + `phase_prompt`
3. **Conclusion Markers**: Agents use `<INFO>` tags to signal consensus reached
4. **Termination Conditions**:
   - Explicit conclusion marker found
   - Agent signals termination (e.g., "I have no further questions")
   - Turn limit reached
5. **Context Passing**: Each message builds on previous conversation history

### Adaptation for ΞNuSyQ

**Implementation**: Create `config/multi_agent_session.py`

```python
class MultiAgentSession:
    """
    Manages conversations between 2+ ΞNuSyQ agents.
    Supports both ChatDev-style turn-taking and parallel consensus voting.
    """

    def __init__(self, agents: List[str], task_prompt: str,
                 coordination_pattern: CoordinationPattern):
        self.agents = agents
        self.task_prompt = task_prompt
        self.pattern = coordination_pattern  # From agent_router.py
        self.conversation_history = []
        self.consensus_threshold = 0.7  # 70% agreement for parallel consensus

    def execute_turn_taking(self, max_turns: int = 10) -> str:
        """
        ChatDev-style sequential conversation.
        Best for: design discussions, code reviews, planning
        """
        current_agent_idx = 0
        conclusion = None

        for turn in range(max_turns):
            current_agent = self.agents[current_agent_idx]

            # Build context from conversation history
            context = self._build_context(current_agent)

            # Send to agent API (Ollama/ChatDev/Claude)
            response = self._send_to_agent(current_agent, context)

            # Log conversation
            self.conversation_history.append({
                "turn": turn,
                "agent": current_agent,
                "message": response
            })

            # Check for conclusion marker
            if "<CONCLUSION>" in response:
                conclusion = response.split("<CONCLUSION>")[-1]
                break

            # Rotate to next agent
            current_agent_idx = (current_agent_idx + 1) % len(self.agents)

        return conclusion or self._extract_consensus()

    def execute_parallel_consensus(self) -> str:
        """
        All agents respond simultaneously, extract majority consensus.
        Best for: critical decisions, security reviews, complex analysis
        """
        responses = []

        # Query all agents in parallel
        for agent in self.agents:
            context = self._build_context(agent)
            response = self._send_to_agent(agent, context)
            responses.append({"agent": agent, "response": response})

        # Extract consensus
        consensus = self._vote_consensus(responses)
        return consensus

    def _build_context(self, current_agent: str) -> str:
        """Build conversation history + task prompt for current agent"""
        history = "\n".join([
            f"{msg['agent']}: {msg['message']}"
            for msg in self.conversation_history
        ])

        agent_prompt = AgentPromptLibrary().get_system_prompt(current_agent)

        return f"{agent_prompt}\n\nTask: {self.task_prompt}\n\nConversation History:\n{history}\n\nYour response:"

    def _send_to_agent(self, agent_name: str, context: str) -> str:
        """Route message to appropriate API (Ollama/ChatDev/Claude)"""
        agent_config = AgentRegistry().get_agent(agent_name)

        if agent_config.provider == "ollama":
            return self._call_ollama(agent_config.model, context)
        elif agent_config.provider == "chatdev":
            return self._call_chatdev(agent_name, context)
        elif agent_config.provider == "claude":
            return self._call_claude(context)
        else:
            raise ValueError(f"Unknown provider: {agent_config.provider}")
```

**Benefits for ΞNuSyQ**:
- **Flexible Coordination**: Supports both sequential (ChatDev-style) and parallel (voting) patterns
- **Provider Agnostic**: Works with Ollama, ChatDev, Claude, Continue.dev APIs
- **Cost Optimized**: Uses coordination_pattern from agent_router.py to minimize expensive calls

---

## Pattern 4: Incremental Refinement via Reflection

### Implementation in ChatDev

**File**: `chatdev/phase.py` - `self_reflection()` method (lines 176-229)

```python
def self_reflection(self, task_prompt: str, role_play_session: RolePlaying,
                    phase_name: str, chat_env: ChatEnv) -> str:
    """
    Meta-layer conversation between CEO and Counselor to review and refine
    conclusions from the main agent conversation.

    Process:
    1. Extract all messages from main conversation
    2. CEO and Counselor discuss these messages
    3. Extract refined conclusion based on phase-specific question
    """

    # Gather conversation history
    messages = role_play_session.assistant_agent.stored_messages
    messages = [f"{msg.role_name}: {msg.content}" for msg in messages]
    messages = "\n\n".join(messages)

    # Phase-specific reflection questions
    if "recruiting" in phase_name:
        question = "Answer their final conclusion (Yes or No) without other words"
    elif phase_name == "DemandAnalysis":
        question = "Answer their final product modality, e.g., 'PowerPoint'"
    elif phase_name == "LanguageChoose":
        question = "Conclude the programming language in format: '*' (e.g., 'Python')"
    elif phase_name == "EnvironmentDoc":
        question = "Write a requirements.txt file based on codes above"

    # Reflection prompt template
    reflection_prompt = f"Here is a conversation: {messages}\n\n{question}"

    # CEO ↔ Counselor meta-conversation (1 turn only)
    reflected_content = self.chatting(
        chat_env=chat_env,
        task_prompt=task_prompt,
        assistant_role_name="Chief Executive Officer",
        user_role_name="Counselor",
        phase_prompt=reflection_prompt,
        phase_name="Reflection",
        assistant_role_prompt=self.ceo_prompt,
        user_role_prompt=self.counselor_prompt,
        need_reflect=False,  # No recursive reflection
        chat_turn_limit=1     # Single exchange only
    )

    return reflected_content
```

**When Reflection Triggers** (from `chatting()` method):
```python
# Reflection triggered when:
# 1. need_reflect=True flag set
# 2. No conclusion marker found in conversation
# 3. Special phases like "recruiting" need forced Yes/No answer

if need_reflect:
    if seminar_conclusion in [None, ""]:
        seminar_conclusion = "<INFO> " + self.self_reflection(...)
```

### Adaptation for ΞNuSyQ

**Implementation**: Add reflection layer to `config/multi_agent_session.py`

```python
class MultiAgentSession:
    # ... (previous methods)

    def execute_with_reflection(self, max_turns: int = 10,
                                reflection_agents: List[str] = None) -> str:
        """
        Run main conversation, then meta-review by reflection agents.

        Args:
            max_turns: Max conversation turns for main session
            reflection_agents: Agents for meta-review (default: claude_code + chatdev_ceo)

        Returns:
            Refined conclusion after reflection
        """
        # Default reflection agents (high-capability orchestrators)
        if reflection_agents is None:
            reflection_agents = ["claude_code", "chatdev_ceo"]

        # Phase 1: Main conversation
        initial_conclusion = self.execute_turn_taking(max_turns)

        # Check if conclusion is clear
        if self._is_conclusive(initial_conclusion):
            return initial_conclusion  # No reflection needed

        # Phase 2: Reflection meta-conversation
        reflection_session = MultiAgentSession(
            agents=reflection_agents,
            task_prompt=self._build_reflection_prompt(initial_conclusion),
            coordination_pattern=CoordinationPattern.SIMPLE  # Short refinement only
        )

        refined_conclusion = reflection_session.execute_turn_taking(max_turns=2)

        # Log both conclusions for audit trail
        self._log_reflection(initial_conclusion, refined_conclusion)

        return refined_conclusion

    def _build_reflection_prompt(self, initial_conclusion: str) -> str:
        """Generate reflection prompt from conversation history"""
        history = "\n".join([
            f"Turn {msg['turn']} - {msg['agent']}: {msg['message']}"
            for msg in self.conversation_history
        ])

        return f"""
        Review the following agent conversation and extract a clear, actionable conclusion.

        Conversation History:
        {history}

        Initial Conclusion Reached:
        {initial_conclusion}

        Your task:
        1. Identify any ambiguities or contradictions
        2. Extract the core decision/deliverable
        3. Format conclusion as clear action items

        Refined Conclusion:
        """

    def _is_conclusive(self, conclusion: str) -> bool:
        """Check if conclusion is clear enough to skip reflection"""
        # Heuristics:
        # - Contains action verbs (implement, create, refactor)
        # - Specifies deliverables (files, code blocks, documentation)
        # - No contradictory statements

        if not conclusion or len(conclusion) < 20:
            return False

        action_verbs = ["implement", "create", "refactor", "delete", "update", "fix"]
        has_action = any(verb in conclusion.lower() for verb in action_verbs)

        contradiction_markers = ["but", "however", "unclear", "uncertain"]
        has_contradiction = any(marker in conclusion.lower() for marker in contradiction_markers)

        return has_action and not has_contradiction
```

**Reflection Agent Selection for ΞNuSyQ**:
- **Default Pair**: `claude_code` (orchestrator) + `chatdev_ceo` (strategic leader)
- **Technical Refinement**: `chatdev_cto` + `ollama_qwen_14b` (deep code analysis)
- **Critical Decisions**: `claude_code` + 2 Ollama agents (voting consensus)

**Benefits for ΞNuSyQ**:
- **Quality Assurance**: High-capability agents review work of specialized agents
- **Cost Efficient**: Reflection only triggered when needed (ambiguous conclusions)
- **Audit Trail**: All reflections logged for debugging and improvement

---

## Integration Roadmap for ΞNuSyQ

### Week 2 Tasks (Current)
1. ✅ **Document Patterns**: CHATDEV_PROMPT_PATTERNS.md (this file)
2. ⏳ **Create Prompt Library**: `config/agent_prompts.py`
   - Implement `AgentPromptLibrary` with 15 agent system prompts
   - Add task-specific constraints from agent_registry.yaml capabilities
3. ⏳ **Extend Agent Router**: Add `WorkflowDecomposer` to `agent_router.py`
   - Define workflow templates (full_project, refactoring, neural_training)
   - Integrate with existing `route_task()` method
4. ⏳ **Create Multi-Agent Session**: `config/multi_agent_session.py`
   - Implement turn-taking protocol (ChatDev-style)
   - Implement parallel consensus (voting)
   - Add reflection layer with configurable agents

### Week 3-4 Tasks (SHORT-TERM)
5. **Test Integration**: Add tests to `tests/integration/test_full_workflow.py`
   - Test turn-taking with 2 Ollama agents
   - Test parallel consensus with 3+ agents
   - Test reflection refinement
   - Test workflow decomposition for sample project
6. **ChatDev Bridge**: Update `nusyq_chatdev.py` to use new patterns
   - Replace direct ChatDev calls with `MultiAgentSession`
   - Use `WorkflowDecomposer` for complex tasks
   - Log all conversations to Reports/

### MEDIUM-TERM Enhancement (Month 2-3)
7. **Adaptive Prompts**: Extend `AgentPromptLibrary` with:
   - Dynamic prompt generation based on task complexity
   - Learning from past conversation success rates
   - A/B testing different prompt formulations
8. **Conversation Analytics**: Track:
   - Average turns to conclusion per task type
   - Reflection trigger rate
   - Cost per conversation (Ollama free, Claude paid)
   - Agent pair synergies (which combinations work best)

---

## Appendix: ChatDev Files Analyzed

| File | Purpose | Key Patterns Extracted |
|------|---------|------------------------|
| `camel/prompts/base.py` | TextPrompt wrapper class | String subclass with key_words property, format() override |
| `camel/prompts/prompt_templates.py` | Role-based prompt generation | get_system_prompt(task_type, role_type) → TextPrompt |
| `camel/prompts/task_prompt_template.py` | Task-specific templates | TaskPromptTemplateDict mapping TaskType → prompts |
| `chatdev/phase.py` | Single-phase conversation | chatting() method with turn-taking, reflection, conclusion extraction |
| `chatdev/composed_phase.py` | Multi-phase workflows | ComposedPhase loops through SimplePhases with cycle control |

---

## Conclusion

ChatDev's prompt engineering patterns provide battle-tested foundations for multi-agent collaboration:

1. **Role-Based Prompts**: Clear agent identities prevent overlap and confusion
2. **Task Decomposition**: Complex projects broken into manageable phases
3. **Communication Protocol**: Turn-taking + shared context ensures coherent conversations
4. **Reflection Layer**: Meta-review catches ambiguities and refines conclusions

**Next Steps for Week 2**:
- Implement `config/agent_prompts.py` with 15 agent system prompts
- Extend `agent_router.py` with `WorkflowDecomposer` class
- Create `config/multi_agent_session.py` for conversation management
- Test integration with sample workflows

**Expected Outcomes**:
- Reduce Claude API costs by 80% (Ollama-first routing)
- Improve task completion quality (reflection layer)
- Scale to 15+ agents without coordination chaos
- Foundation for LONG-TERM neural network integration

---

**Document Status**: ✅ COMPLETE - Ready for implementation
**Author**: AI Code Agent (Week 2 extraction)
**Review Required**: User approval before implementing agent_prompts.py
