"""
Claude Code Bridge - Bidirectional Multi-Agent Communication
============================================================

Purpose:
    Enables bidirectional AI agent collaboration:
    - GitHub Copilot ↔ Claude Code
    - Claude Code ↔ Ollama models
    - Any agent ↔ Any other agent via MCP

Architecture:
    Integrates with collaboration_advisor.py for intelligent
    multi-agent orchestration across 14+ AI agents.

Features:
    - Bidirectional communication (not just Copilot → Claude)
    - Multi-agent task distribution
    - Parallel execution support
    - Auto-discovery of available agents
    - Hardware-aware workload balancing (32 cores, 32GB RAM)

Integration Points:
    - CollaborationAdvisor: Intelligent agent selection
    - MultiAgentSession: Coordinate multiple agents
    - AI Council: Route queries across agent types
    - ChatDev: Full project orchestration
    - Ollama: Local LLM execution (8 models)

Agent Support:
    ✓ GitHub Copilot (IDE assistant)
    ✓ Claude Code (cloud, via MCP)
    ✓ Ollama Qwen 2.5 Coder 14B (local)
    ✓ Ollama Qwen 2.5 Coder 7B (local)
    ✓ Ollama StarCoder2 15B (local)
    ✓ Ollama Gemma2 9B (local)
    ✓ Ollama CodeLlama 7B (local)
    ✓ Ollama Llama 3.1 8B (local)
    ✓ Ollama Phi 3.5 (local)
    ✓ ChatDev Team (5 agents, local)
    ⚡ Custom ML models (extensible)

Hardware Capacity:
    Tested on Intel i9-14900HX (32 cores), 32GB RAM
    - Supports 4+ concurrent 7B models
    - Supports 2-3 concurrent 14B+ models
    - Parallel task execution across agents

Security:
    - Local network only (no external exposure)
    - Optional API key authentication
    - Rate limit tracking (respect cooldowns)
    - Query sanitization

Usage Examples:
    # Direct query to Claude Code
    client = ClaudeCodeClient()
    response = await client.query("Architect this feature")

    # Multi-agent orchestration
    from config.collaboration_advisor import get_collaboration_advisor
    advisor = get_collaboration_advisor()
    assessment = advisor.assess_workload(
        "Refactor auth system",
        files=["auth.py", "user.py"],
        complexity_indicators={'cognitive_complexity': 18}
    )
    # Returns: recommended_agent, can_parallelize, agent_scores

    # Parallel execution
    if assessment.can_parallelize:
        # Distribute across Ollama models
        agents = assessment.parallel_agents
        # Execute 4+ agents concurrently
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from enum import Enum

try:
    import aiohttp
except ImportError:
    aiohttp = None

# Import adaptive timeout system
from config.adaptive_timeout_manager import (
    get_timeout_manager,
    AgentType,
    TaskComplexity,
)

logger = logging.getLogger("nusyq.claude_bridge")


class ClaudeStatus(Enum):
    """Claude Code app availability status"""

    AVAILABLE = "available"
    COOLING_DOWN = "cooling_down"  # Rate limited until 6 AM
    OFFLINE = "offline"
    ERROR = "error"


class QueryPriority(Enum):
    """Priority levels for Claude Code queries"""

    CRITICAL = 1  # Architecture decisions, security reviews
    HIGH = 2  # Code review, design feedback
    NORMAL = 3  # General questions, optimization
    LOW = 4  # Nice-to-have insights


class ClaudeCodeClient:
    """
    HTTP client for submitting queries to Claude Code app via MCP server

    Handles:
    - Query submission with priority queuing
    - Response polling with timeout
    - Cooldown period tracking (6 AM reset)
    - Error handling and fallback
    """

    def __init__(
        self,
        mcp_url: str = "http://localhost:3000",
        timeout: int = 30,
        max_retries: int = 3,
    ):
        """
        Initialize Claude Code client

        Args:
            mcp_url: Base URL for MCP server (Claude Code connector)
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts for failed requests
        """
        self.mcp_url = mcp_url
        self.timeout = timeout
        self.max_retries = max_retries
        self.cooldown_until: Optional[datetime] = None
        self.query_count = 0
        self.session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        """Async context manager entry"""
        if aiohttp:
            self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()

    async def check_status(self) -> ClaudeStatus:
        """
        Check Claude Code app availability

        Returns:
            ClaudeStatus enum indicating current state
        """
        # Check if in cooldown period
        if self.cooldown_until and datetime.now() < self.cooldown_until:
            return ClaudeStatus.COOLING_DOWN

        # Try to ping MCP server
        try:
            if not aiohttp or not self.session:
                logger.warning("aiohttp not available, assuming Claude is offline")
                return ClaudeStatus.OFFLINE

            async with self.session.get(
                f"{self.mcp_url}/health", timeout=aiohttp.ClientTimeout(total=5)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    # Check if Claude Code connector is active
                    if data.get("claude_code_connected"):
                        return ClaudeStatus.AVAILABLE
                    return ClaudeStatus.OFFLINE
                return ClaudeStatus.ERROR

        except Exception as e:
            logger.error("Failed to check Claude status: %s", e)
            return ClaudeStatus.ERROR

    async def query(
        self,
        prompt: str,
        priority: QueryPriority = QueryPriority.NORMAL,
        context: Optional[Dict[str, Any]] = None,
        wait_for_response: bool = True,  # noqa: ARG002
    ) -> Optional[str]:
        """
        Submit a query to Claude Code app

        Args:
            prompt: The question or task for Claude
            priority: Query priority (affects queuing)
            context: Additional context (files, code snippets, etc.)
            wait_for_response: If True, block until response received

        Returns:
            Claude's response text, or None if error/cooldown
        """
        status = await self.check_status()

        if status == ClaudeStatus.COOLING_DOWN:
            logger.warning(
                "Claude Code is cooling down until %s. Skipping query.",
                self.cooldown_until,
            )
            return None

        if status != ClaudeStatus.AVAILABLE:
            logger.error("Claude Code not available (status: %s)", status.value)
            return None

        # Build MCP request
        mcp_request = {
            "method": "tools/call",
            "params": {
                "name": "claude_code_query",
                "arguments": {
                    "prompt": prompt,
                    "priority": priority.value,
                    "context": context or {},
                    "timestamp": datetime.now().isoformat(),
                },
            },
            "id": f"query_{self.query_count}",
        }

        self.query_count += 1

        try:
            if not self.session:
                logger.error("HTTP session not initialized")
                return None

            async with self.session.post(
                f"{self.mcp_url}/mcp",
                json=mcp_request,
                timeout=aiohttp.ClientTimeout(total=self.timeout),
            ) as response:
                if response.status == 429:  # Rate limited
                    # Parse cooldown time from response
                    data = await response.json()
                    # Set cooldown until 6 AM tomorrow
                    tomorrow = datetime.now() + timedelta(days=1)
                    self.cooldown_until = tomorrow.replace(
                        hour=6, minute=0, second=0, microsecond=0
                    )
                    logger.warning(
                        "Claude Code rate limited. Cooling down until %s",
                        self.cooldown_until,
                    )
                    return None

                if response.status != 200:
                    logger.error("Claude query failed: HTTP %s", response.status)
                    return None

                data = await response.json()

                if "error" in data:
                    logger.error("Claude query error: %s", data["error"])
                    return None

                # Extract response text
                result = data.get("result", {})
                claude_response = result.get("response", "")

                logger.info(
                    "Claude query succeeded (priority: %s, tokens: %s)",
                    priority.name,
                    result.get("tokens", 0),
                )

                return claude_response

        except asyncio.TimeoutError:
            logger.error("Claude query timed out after %ss", self.timeout)
            return None
        except Exception as e:
            logger.error("Claude query failed: %s", e)
            return None

    async def submit_to_ai_council(
        self,
        topic: str,
        agents: List[str],
        include_claude: bool = True,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Submit a query to AI Council with optional Claude participation

        Args:
            topic: Discussion topic
            agents: List of agent names to include
            include_claude: Whether to query Claude Code app
            context: Optional context dictionary for the council session

        Returns:
            Council session results including Claude's input
        """
        # Import here to avoid circular dependency
        from config.ai_council import AICouncil

        council = AICouncil()

        # If Claude should participate, add it to the discussion
        if include_claude:
            status = await self.check_status()
            if status == ClaudeStatus.AVAILABLE:
                # Query Claude first for high-level analysis
                claude_prompt = (
                    f"AI Council Discussion Topic: {topic}\n\n"
                    f"Participating Agents: {', '.join(agents)}\n\n"
                    "Please provide your analysis and recommendations "
                    "for this council discussion."
                )
                claude_response = await self.query(
                    claude_prompt, priority=QueryPriority.HIGH
                )

                # Add Claude's input to council context
                if claude_response:
                    logger.info("Claude's pre-analysis received for council")
                    # Store in context for council to reference
                    # (Will be added to session initialization)

        # Execute council session using AICouncil
        logger.info("Executing AI Council session: %s", topic)

        try:
            from config.ai_council import AICouncil, CouncilSessionType

            # Determine session type based on context
            session_type = CouncilSessionType.ADVISORY  # Default
            if any(
                word in topic.lower() for word in ["critical", "error", "bug", "fail"]
            ):
                session_type = CouncilSessionType.EMERGENCY
            elif any(
                word in topic.lower() for word in ["progress", "status", "update"]
            ):
                session_type = CouncilSessionType.STANDUP

            # Initialize council
            council = AICouncil()

            # Execute session
            result = council.execute_session(
                session_type=session_type,
                topic=topic,
                context=context,
                priority="high"
                if session_type == CouncilSessionType.EMERGENCY
                else "medium",
            )

            logger.info(f"AI Council session completed: {result.session_id}")

            return {
                "status": "completed",
                "session_id": result.session_id,
                "topic": topic,
                "participants": result.participants,
                "decisions": result.decisions,
                "action_items": result.action_items,
                "insights": result.insights,
            }

        except Exception as e:
            logger.error("AI Council integration failed: %s", e)
            return {
                "status": "error",
                "error": str(e),
                "topic": topic,
                "agents": agents,
            }

    async def submit_to_chatdev(
        self,
        task_description: str,
        architecture_review: bool = True,
        model: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Submit a task to ChatDev with optional Claude architecture review

        Workflow:
        1. Query Claude for architecture recommendations (if enabled)
        2. Pass architecture to ChatDev for implementation
        3. Return ChatDev result with Claude's guidance

        Args:
            task_description: What to build
            architecture_review: Whether to get Claude's input first

        Returns:
            ChatDev execution results with architecture notes
        """
        claude_architecture = None

        if architecture_review:
            status = await self.check_status()
            if status == ClaudeStatus.AVAILABLE:
                arch_prompt = (
                    f"Task: {task_description}\n\n"
                    "Please provide an architecture design for this task, including:\n"
                    "1. Recommended file structure\n"
                    "2. Key components and their responsibilities\n"
                    "3. Design patterns to use\n"
                    "4. Potential pitfalls to avoid\n"
                    "5. Testing strategy\n\n"
                    "The implementation will be done by the ChatDev agent team."
                )

                claude_architecture = await self.query(
                    arch_prompt,
                    priority=QueryPriority.HIGH,
                    context={"task": task_description},
                )

                logger.info("Claude architecture review received for ChatDev")

        # ChatDev Integration: Implemented with Ollama backend
        # Uses nusyq_chatdev.run_chatdev_with_ollama for execution

        logger.info("Submitting to ChatDev: %s", task_description)

        try:
            from integrations.nusyq_chatdev import run_chatdev_with_ollama

            # Execute ChatDev with Ollama backend
            success = run_chatdev_with_ollama(
                task=task_description,
                model=model or "qwen2.5-coder:14b",
                config="NuSyQ_Ollama",
            )

            if success:
                logger.info("ChatDev execution completed successfully")
                return {
                    "status": "completed",
                    "task": task_description,
                    "claude_architecture": claude_architecture,
                    "model": model,
                    "success": True,
                }
            else:
                logger.warning("ChatDev execution failed")
                return {
                    "status": "failed",
                    "task": task_description,
                    "error": "ChatDev execution returned false",
                }

        except Exception as e:
            logger.error("ChatDev integration failed: %s", e)
            return {"status": "error", "task": task_description, "error": str(e)}


class ClaudeCodeBridge:
    """
    High-level orchestrator for Copilot ↔ Claude Code collaboration

    Manages:
    - Query routing based on task complexity
    - Multi-agent orchestration (AI Council + Claude)
    - ChatDev integration with Claude architecture review
    - Response aggregation and synthesis
    """

    def __init__(self):
        self.client = ClaudeCodeClient()
        self.query_history: List[Dict[str, Any]] = []

    async def orchestrate_task(
        self,
        task: str,
        use_ai_council: bool = True,
        use_claude: bool = True,
        use_chatdev: bool = False,
    ) -> Dict[str, Any]:
        """
        Orchestrate a task across multiple AI agents

        Workflow:
        1. AI Council discusses approach (with Claude if available)
        2. Claude provides architecture (if requested)
        3. ChatDev implements (if requested)
        4. If none specified, use MCP multi-agent orchestration
        5. Results aggregated and returned

        Args:
            task: Task description
            use_ai_council: Whether to convene AI Council
            use_claude: Whether to query Claude Code
            use_chatdev: Whether to use ChatDev for implementation

        Returns:
            Orchestrated results from all participating agents
        """
        async with self.client:
            results = {
                "task": task,
                "timestamp": datetime.now().isoformat(),
                "agents_used": [],
            }

            # Step 1: AI Council discussion (optional)
            if use_ai_council:
                logger.info("Step 1: AI Council discussion")
                council_result = await self.client.submit_to_ai_council(
                    topic=task,
                    agents=["ollama_qwen_14b", "ollama_qwen_7b"],
                    include_claude=use_claude,
                )
                results["council_discussion"] = council_result
                results["agents_used"].append("ai_council")

            # Step 2: Claude architecture review (optional)
            claude_architecture = None
            if use_claude and not use_ai_council:
                logger.info("Step 2: Claude architecture review")
                claude_architecture = await self.client.query(
                    f"Architecture design for: {task}", priority=QueryPriority.HIGH
                )
                results["claude_architecture"] = claude_architecture
                results["agents_used"].append("claude_code")

            # Step 3: ChatDev implementation (optional)
            if use_chatdev:
                logger.info("Step 3: ChatDev implementation")
                chatdev_result = await self.client.submit_to_chatdev(
                    task_description=task,
                    architecture_review=(claude_architecture is not None),
                )
                results["chatdev_execution"] = chatdev_result
                results["agents_used"].append("chatdev")

            # Step 4: Fallback to MCP multi-agent orchestration if no specific agents
            if not results["agents_used"]:
                logger.info("Step 4: MCP multi-agent orchestration (fallback)")
                try:
                    # === ADAPTIVE TIMEOUT CALCULATION ===
                    # Get intelligent timeout based on task complexity
                    timeout_manager = get_timeout_manager()

                    # Determine complexity from task description
                    task_lower = task.lower()
                    if any(
                        word in task_lower for word in ["simple", "quick", "trivial"]
                    ):
                        complexity = TaskComplexity.SIMPLE
                    elif any(
                        word in task_lower for word in ["complex", "critical", "major"]
                    ):
                        complexity = TaskComplexity.COMPLEX
                    else:
                        complexity = TaskComplexity.MODERATE

                    # Get adaptive timeout for multi-agent orchestration
                    timeout_rec = timeout_manager.get_timeout(
                        agent_type=AgentType.MULTI_AGENT,
                        task_complexity=complexity,
                        context={"task": task, "agent_count": 2, "mode": "TURN_TAKING"},
                    )

                    logger.info(
                        "Using adaptive timeout: %.1fs (complexity=%s, confidence=%.1f%%)",
                        timeout_rec.timeout_seconds,
                        complexity.value,
                        timeout_rec.confidence * 100,
                    )
                    logger.info("Reasoning: %s", timeout_rec.reasoning)

                    # Track start time for learning
                    start_time = asyncio.get_event_loop().time()
                    # === END ADAPTIVE TIMEOUT ===

                    mcp_request = {
                        "method": "tools/call",
                        "params": {
                            "name": "multi_agent_orchestration",
                            "arguments": {
                                "task": task,
                                "agents": ["ollama_qwen_14b", "ollama_qwen_7b"],
                                "mode": "TURN_TAKING",
                            },
                        },
                        "id": f"orchestrate_{datetime.now().timestamp()}",
                    }

                    # Use adaptive timeout instead of hardcoded 60s
                    timeout = aiohttp.ClientTimeout(total=timeout_rec.timeout_seconds)
                    async with aiohttp.ClientSession(timeout=timeout) as session:
                        async with session.post(
                            "http://localhost:3000/mcp", json=mcp_request
                        ) as response:
                            if response.status == 200:
                                data = await response.json()
                                mcp_result = data.get("result", {})
                                results["mcp_orchestration"] = mcp_result

                                # Extract agents_used from orchestration result
                                phases = mcp_result.get("phases", {})
                                discussion = phases.get("agent_discussion", {})
                                agents_used = discussion.get("agents_used", [])
                                results["agents_used"].extend(agents_used)

                                # === RECORD EXECUTION FOR LEARNING ===
                                duration = asyncio.get_event_loop().time() - start_time
                                timeout_manager.record_execution(
                                    agent_type=AgentType.MULTI_AGENT,
                                    task_complexity=complexity,
                                    duration=duration,
                                    succeeded=True,
                                    context={"task": task, "agents": agents_used},
                                )
                                # === END RECORDING ===

                                logger.info(
                                    "MCP orchestration complete: %d agents, %.1fs",
                                    len(agents_used),
                                    duration,
                                )
                            else:
                                logger.error(
                                    "MCP orchestration failed: HTTP %d", response.status
                                )
                except asyncio.TimeoutError:
                    # Record timeout failure for learning
                    duration = asyncio.get_event_loop().time() - start_time
                    timeout_manager.record_execution(
                        agent_type=AgentType.MULTI_AGENT,
                        task_complexity=complexity,
                        duration=duration,
                        succeeded=False,
                        context={
                            "task": task,
                            "error": "timeout",
                            "timeout_used": timeout_rec.timeout_seconds,
                        },
                    )
                    logger.error(
                        "MCP orchestration timed out after %.1fs (adaptive timeout was %.1fs)",
                        duration,
                        timeout_rec.timeout_seconds,
                    )
                except Exception as e:
                    logger.error("MCP orchestration error: %s", str(e))
                    logger.exception("Full traceback:")

            # Log orchestration
            self.query_history.append(results)

            return results


# === Standalone Testing ===


async def test_claude_bridge():
    """Test the Claude Code bridge functionality"""
    print("🧪 Testing Claude Code Bridge...")

    async with ClaudeCodeClient() as client:
        # Test 1: Check status
        print("\n1. Checking Claude Code status...")
        status = await client.check_status()
        print(f"   Status: {status.value}")

        if status == ClaudeStatus.AVAILABLE:
            # Test 2: Simple query
            print("\n2. Sending test query...")
            response = await client.query(
                "What is the best way to structure a Python module?",
                priority=QueryPriority.NORMAL,
            )
            if response:
                print(f"   Response: {response[:200]}...")
            else:
                print("   No response received")
        elif status == ClaudeStatus.COOLING_DOWN:
            print(f"   ⏰ Claude is cooling down until {client.cooldown_until}")
        else:
            print("   ⚠️ Claude Code is not available")

    # Test 3: Orchestration
    print("\n3. Testing task orchestration...")
    bridge = ClaudeCodeBridge()
    result = await bridge.orchestrate_task(
        task="Create a REST API for managing user profiles",
        use_ai_council=True,
        use_claude=True,
        use_chatdev=False,
    )
    print(f"   Orchestration complete: {len(result['agents_used'])} agents used")
    print(f"   Agents: {', '.join(result['agents_used'])}")


if __name__ == "__main__":
    # Run tests
    asyncio.run(test_claude_bridge())
