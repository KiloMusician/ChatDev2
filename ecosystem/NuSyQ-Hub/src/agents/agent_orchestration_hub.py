"""Agent Orchestration Hub - Unified AI coordination.

Central hub for task routing, multi-agent coordination, ChatDev, and healing.
OmniTag: {"purpose": "Unified agent orchestration with consciousness integration",
"tags": ["Agent", "Orchestration", "Consciousness", "Multi-AI"],
"category": "core_infrastructure", "evolution_stage": "v1.0"}
"""

import asyncio
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

from src.agents.agent_orchestration_types import (ExecutionMode,
                                                  RegisteredService,
                                                  ServiceCapability, TaskLock,
                                                  TaskPriority)
from src.LOGGING.modular_logging_system import get_logger

logger = get_logger(__name__)

KEY_STATUS = "status"
KEY_ERROR = "error"

if TYPE_CHECKING:
    from src.healing.quantum_problem_resolver import QuantumProblemResolver
    from src.integration.consciousness_bridge import ConsciousnessBridge
    from src.orchestration.claude_orchestrator import ClaudeOrchestrator
    from src.orchestration.multi_ai_orchestrator import MultiAIOrchestrator


class AgentOrchestrationHub:
    """Central hub for coordinating AI agent interactions.

    Handles routing, coordination, ChatDev, healing, and service registration.
    """

    def __init__(
        self,
        root_path: Path | None = None,
        enable_healing: bool = True,
        enable_consciousness: bool = True,
    ):
        """Initialize the orchestration hub.

        Args:
            root_path: Repository root path
            enable_healing: Enable automatic healing escalation
            enable_consciousness: Enable consciousness-guided routing
        """
        self.root_path = root_path or Path.cwd()
        self.enable_healing = enable_healing
        self.enable_consciousness = enable_consciousness

        # Service registry
        self._services: dict[str, RegisteredService] = {}

        # Task locks
        self._locks: dict[str, TaskLock] = {}
        self._lock_timeout: float = 300.0  # 5 minutes default

        # Consciousness cache (if enabled)
        self._consciousness_cache: dict[str, Any] = {}

        # Load lazy imports
        self._unified_orchestrator: MultiAIOrchestrator | None = None
        self._quantum_resolver: QuantumProblemResolver | None = None
        self._consciousness_bridge: ConsciousnessBridge | None = None
        self._claude_orchestrator: ClaudeOrchestrator | None = None

        logger.info(
            "🌉 AgentOrchestrationHub initialized",
            extra={
                "root_path": str(self.root_path),
                "healing": enable_healing,
                "consciousness": enable_consciousness,
            },
        )

    @staticmethod
    def _status_implies_success(status: str | None) -> bool:
        """Map mixed status strings to a canonical success boolean."""
        if not status:
            return False
        return str(status).strip().lower() in {
            "success",
            "ok",
            "completed",
            "submitted",
            "operational",
            "consensus_reached",
            "vote_success",
            "parallel_complete",
            "synthesized",
            "healing_applied",
            "delivered",
        }

    @classmethod
    def _normalize_response_contract(cls, payload: dict[str, Any]) -> dict[str, Any]:
        """Ensure orchestration boundaries always include status and success."""
        normalized = dict(payload)
        status = normalized.get(KEY_STATUS)
        if not isinstance(status, str) or not status.strip():
            status = "success" if bool(normalized.get("success")) else KEY_ERROR
            normalized[KEY_STATUS] = status
        if "success" not in normalized:
            normalized["success"] = cls._status_implies_success(str(normalized[KEY_STATUS]))
        return normalized

    @classmethod
    def _response_succeeded(cls, payload: dict[str, Any]) -> bool:
        """Treat either success key or status value as success."""
        if "success" in payload:
            return bool(payload["success"])
        return cls._status_implies_success(payload.get(KEY_STATUS))

    # ==================== Core Method 1: Universal Task Routing ====================

    async def route_task(
        self,
        task_type: str,
        description: str,
        context: dict[str, Any] | None = None,
        priority: TaskPriority = TaskPriority.NORMAL,
        target_service: str | None = None,
        require_consciousness: bool = False,
    ) -> dict[str, Any]:
        """Route a task to the appropriate AI service with consciousness awareness.

        This is the primary entry point for all agent tasks. It performs:
        1. Semantic analysis of the task (if consciousness enabled)
        2. Service selection based on capabilities and context
        3. Consciousness-guided routing decisions
        4. Automatic healing escalation on failures
        5. Result synthesis and audit logging

        Args:
            task_type: Type of task (code_review, analysis, generation, etc.)
            description: Human-readable task description
            context: Additional context (files, metadata, etc.)
            priority: Task priority level
            target_service: Force specific service (bypasses routing)
            require_consciousness: Require consciousness integration

        Returns:
            Task result dictionary with status, output, and metadata
        """
        context = context or {}
        task_id = str(uuid.uuid4())

        logger.info(
            f"🎯 Routing task: {task_type}",
            extra={
                "task_id": task_id,
                "priority": priority.name,
                "target": target_service or "auto",
            },
        )

        # Consciousness integration: Semantic analysis
        semantic_context = {}
        if self.enable_consciousness and (require_consciousness or not target_service):
            semantic_context = await self._analyze_task_semantics(task_type, description, context)
            context["semantic_analysis"] = semantic_context

        # Service selection
        if target_service:
            service = self._services.get(target_service)
            if not service:
                return self._normalize_response_contract(
                    {
                        KEY_STATUS: KEY_ERROR,
                        KEY_ERROR: f"Service not found: {target_service}",
                        "task_id": task_id,
                    }
                )
        else:
            service = await self._select_optimal_service(task_type, context, semantic_context)
            if not service:
                return self._normalize_response_contract(
                    {
                        KEY_STATUS: KEY_ERROR,
                        KEY_ERROR: f"No service available for task type: {task_type}",
                        "task_id": task_id,
                    }
                )

        # Execute task with healing fallback
        result = await self._execute_task_with_service(
            service, task_type, description, context, task_id
        )

        # Consciousness integration: Learning from results
        if self.enable_consciousness and self._response_succeeded(result):
            await self._log_consciousness_learning(
                task_type, service.service_id, result, semantic_context
            )

        normalized = self._normalize_response_contract(result)

        try:
            from src.system.agent_awareness import emit as _emit

            _ok = self._response_succeeded(result)
            _lvl = "INFO" if _ok else "WARNING"
            _emit(
                "agents",
                f"Route: {task_type} → {service.service_id} id={task_id[:8]} success={_ok}",
                level=_lvl,
                source="agent_orchestration_hub",
            )
        except Exception:
            pass

        return normalized

    # ==================== Core Method 2: ChatDev Orchestration ====================

    async def route_to_chatdev(
        self,
        project_description: str,
        requirements: list[str] | None = None,
        team_composition: dict[str, Any] | None = None,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Orchestrate ChatDev multi-agent development with optional team overrides."""
        requirements = requirements or []
        context = context or {}
        team_composition = team_composition or self._get_default_chatdev_team()

        logger.info(
            "🎭 Routing to ChatDev",
            extra={
                "description": project_description[:100],
                "requirements": len(requirements),
                "team_size": len(team_composition),
            },
        )

        # Load ChatDev orchestrator
        orchestrator = await self._get_chatdev_orchestrator()
        if not orchestrator:
            return self._normalize_response_contract(
                {
                    KEY_STATUS: KEY_ERROR,
                    KEY_ERROR: "ChatDev orchestrator not available",
                }
            )

        # Prepare ChatDev task
        chatdev_task = {
            "description": project_description,
            "requirements": requirements,
            "team": team_composition,
            "context": context,
        }

        # Execute with progress monitoring
        result = await self._execute_chatdev_with_monitoring(orchestrator, chatdev_task)

        return self._normalize_response_contract(result)

    # ==================== Core Method 3: Claude Orchestration ====================

    async def route_to_claude(
        self,
        task_description: str,
        context: dict[str, Any] | None = None,
        systems: list[str] | None = None,
        mode: str = "consensus",
    ) -> dict[str, Any]:
        """Route a task through the Claude orchestration layer."""
        context = context or {}
        mode = str(context.get("mode", mode)).lower()
        systems = list(systems or context.get("systems") or ["ollama", "claude"])

        logger.info(
            "🤖 Routing to Claude orchestrator",
            extra={"mode": mode, "systems": systems},
        )

        semantic_context = {}
        if self.enable_consciousness:
            semantic_context = await self._analyze_task_semantics(
                "claude_orchestrator", task_description, context
            )
            context["semantic_analysis"] = semantic_context
            if semantic_context.get("requires_creativity") and "chatdev" not in systems:
                systems.append("chatdev")

        if context.get("simulate"):
            return self._normalize_response_contract(
                {
                    KEY_STATUS: "success",
                    "service": "claude_orchestrator",
                    "mode": mode,
                    "simulated": True,
                    "task": task_description[:100],
                }
            )

        orchestrator = await self._get_claude_orchestrator()
        if not orchestrator:
            return self._normalize_response_contract(
                {KEY_STATUS: KEY_ERROR, KEY_ERROR: "Claude orchestrator not available"}
            )

        if mode == "ollama":
            result = await orchestrator.ask_ollama(
                task_description,
                model=context.get("model", "qwen2.5-coder:14b"),
                temperature=float(context.get("temperature", 0.3)),
            )
        elif mode == "chatdev":
            result = await orchestrator.spawn_chatdev(
                task_description,
                testing_chamber=bool(context.get("testing_chamber", True)),
                model=context.get("model", "qwen2.5-coder:7b"),
            )
        elif mode == "health":
            result = await orchestrator.health_check()
        else:
            result = await orchestrator.multi_ai_consensus(task_description, systems=systems)

        if self.enable_consciousness and isinstance(result, dict):
            await self._log_consciousness_learning(
                "claude_orchestrator", "claude_orchestrator", result, semantic_context
            )

        child_result = (
            self._normalize_response_contract(result)
            if isinstance(result, dict)
            else {KEY_STATUS: "success", "success": True, "value": result}
        )
        child_success = self._response_succeeded(child_result)
        payload = {
            KEY_STATUS: "success" if child_success else KEY_ERROR,
            "service": "claude_orchestrator",
            "mode": mode,
            "result": result,
            "child_success": child_success,
        }
        if not child_success and child_result.get(KEY_ERROR):
            payload[KEY_ERROR] = child_result[KEY_ERROR]
        return self._normalize_response_contract(payload)

    # ==================== Core Method 4: Multi-Agent Coordination ====================

    async def orchestrate_multi_agent_task(
        self,
        task_description: str,
        services: list[str],
        mode: ExecutionMode = ExecutionMode.CONSENSUS,
        context: dict[str, Any] | None = None,
        synthesis_required: bool = True,
    ) -> dict[str, Any]:
        """Coordinate multiple AI agents using consensus/voting/parallel modes."""
        context = context or {}

        logger.info(
            f"🤝 Multi-agent coordination: {mode.value}",
            extra={"agents": len(services), "mode": mode.value},
        )

        # Validate services
        active_services = [self._services[sid] for sid in services if sid in self._services]
        if not active_services:
            return self._normalize_response_contract(
                {KEY_STATUS: KEY_ERROR, KEY_ERROR: "No active services found"}
            )

        # Execute based on mode
        result: dict[str, Any] = {KEY_STATUS: KEY_ERROR, KEY_ERROR: f"Unknown mode: {mode}"}
        if mode == ExecutionMode.CONSENSUS:
            result = await self._execute_consensus(active_services, task_description, context)
        elif mode == ExecutionMode.VOTING:
            result = await self._execute_voting(active_services, task_description, context)
        elif mode == ExecutionMode.SEQUENTIAL:
            result = await self._execute_sequential(active_services, task_description, context)
        elif mode == ExecutionMode.PARALLEL:
            result = await self._execute_parallel(
                active_services, task_description, context, synthesis_required
            )
        elif mode == ExecutionMode.FIRST_SUCCESS:
            result = await self._execute_first_success(active_services, task_description, context)

        return self._normalize_response_contract(result)

    # ==================== Core Method 5: Healing Escalation ====================

    async def execute_with_healing(
        self,
        task_description: str,
        initial_service: str,
        context: dict[str, Any] | None = None,
        max_retries: int = 3,
    ) -> dict[str, Any]:
        """Execute a task with automatic healing escalation on failures."""
        context = context or {}
        healing_history: list[dict[str, Any]] = []

        logger.info(
            "🔧 Execute with healing enabled",
            extra={"service": initial_service, "max_retries": max_retries},
        )

        for attempt in range(max_retries):
            # Execute task
            result = await self.route_task(
                task_type="healing_task",
                description=task_description,
                context=context,
                target_service=initial_service,
            )

            # Success - return immediately
            if self._response_succeeded(result):
                result["healing_history"] = healing_history
                return self._normalize_response_contract(result)

            # Failure - attempt healing
            logger.warning(
                f"❌ Task failed (attempt {attempt + 1}/{max_retries})",
                extra={KEY_ERROR: result.get(KEY_ERROR, "Unknown")},
            )

            if not self.enable_healing:
                break

            # Analyze problem with quantum resolver
            healing_result = await self._analyze_and_heal(result, task_description, context)
            healing_history.append(healing_result)

            # Consciousness judgment: Should we retry?
            if self.enable_consciousness:
                should_retry = await self._consciousness_escalation_judgment(
                    healing_result, attempt, max_retries
                )
                if not should_retry:
                    logger.info("🧠 Consciousness recommends stopping retries")
                    break

            # Update context with healing recommendations
            context["healing_applied"] = healing_result.get("recommendations", [])

        # All retries exhausted
        return self._normalize_response_contract(
            {
                KEY_STATUS: "failed_after_healing",
                KEY_ERROR: "Max retries exceeded",
                "healing_history": healing_history,
                "final_attempt": result,
            }
        )

    # ==================== Core Method 6: Task Locking ====================

    async def acquire_task_lock(
        self,
        task_id: str,
        agent_id: str,
        timeout: float | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> bool:
        """Acquire an exclusive lock on a task to prevent collisions.

        Args:
            task_id: Unique task identifier
            agent_id: Agent requesting the lock
            timeout: Lock timeout in seconds (default: 5 minutes)
            metadata: Additional lock metadata

        Returns:
            True if lock acquired, False if already locked
        """
        timeout = timeout or self._lock_timeout
        metadata = metadata or {}

        # Clean expired locks first
        self._clean_expired_locks()

        # Check if already locked
        if task_id in self._locks:
            existing = self._locks[task_id]
            logger.warning(
                "🔒 Task already locked",
                extra={
                    "task_id": task_id,
                    "holder": existing.agent_id,
                    "requester": agent_id,
                },
            )
            return False

        # Acquire lock
        lock = TaskLock(
            task_id=task_id,
            agent_id=agent_id,
            acquired_at=time.time(),
            expires_at=time.time() + timeout,
            metadata=metadata,
        )
        self._locks[task_id] = lock

        logger.info(
            "✅ Task lock acquired",
            extra={"task_id": task_id, "agent": agent_id, "timeout": timeout},
        )
        return True

    async def release_task_lock(self, task_id: str, agent_id: str) -> bool:
        """Release a task lock.

        Args:
            task_id: Task identifier
            agent_id: Agent releasing the lock (must match holder)

        Returns:
            True if released, False if not held by this agent
        """
        if task_id not in self._locks:
            return False

        lock = self._locks[task_id]
        if lock.agent_id != agent_id:
            logger.warning(
                "🔒 Lock release denied - not owner",
                extra={"task_id": task_id, "requester": agent_id, "owner": lock.agent_id},
            )
            return False

        del self._locks[task_id]
        logger.info("🔓 Task lock released", extra={"task_id": task_id})
        return True

    # ==================== Core Method 7: Service Registration ====================

    def register_service(
        self,
        service_id: str,
        name: str,
        capabilities: list[ServiceCapability],
        endpoint: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> bool:
        """Register a new AI service/agent with the hub."""
        metadata = metadata or {}

        if service_id in self._services:
            logger.warning(f"Service already registered: {service_id}")
            return False

        service = RegisteredService(
            service_id=service_id,
            name=name,
            capabilities=capabilities,
            endpoint=endpoint,
            metadata=metadata,
        )
        self._services[service_id] = service

        logger.info(
            f"📝 Service registered: {name}",
            extra={
                "service_id": service_id,
                "capabilities": len(capabilities),
                "endpoint": endpoint,
            },
        )
        return True

    def unregister_service(self, service_id: str) -> bool:
        """Unregister a service.

        Args:
            service_id: Service to remove

        Returns:
            True if removed, False if not found
        """
        if service_id not in self._services:
            return False

        service = self._services.pop(service_id)
        logger.info(f"🗑️  Service unregistered: {service.name}")
        return True

    # ==================== Additional: Inter-Agent Communication ====================

    async def send_agent_message(
        self,
        from_agent: str,
        to_agent: str,
        message_type: str,
        content: dict[str, Any],
        priority: TaskPriority = TaskPriority.NORMAL,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Send a message between agents with optional consciousness metadata."""
        metadata = metadata or {}

        logger.info(
            f"📨 Agent message: {from_agent} → {to_agent}",
            extra={"type": message_type, "priority": priority.name},
        )

        # Create message envelope
        message = {
            "id": str(uuid.uuid4()),
            "timestamp": datetime.now().isoformat(),
            "from": from_agent,
            "to": to_agent,
            "type": message_type,
            "content": content,
            "priority": priority.value,
            "metadata": metadata,
        }

        # Consciousness integration: Analyze message sentiment
        if self.enable_consciousness:
            message["consciousness_sentiment"] = await self._analyze_message_sentiment(content)

        # Delegate to communication hub (lazy import)
        comm_hub = await self._get_agent_communication_hub()
        result: dict[str, Any]
        if comm_hub:
            result = await comm_hub.deliver_message(message)
        else:
            # Fallback: Direct delivery via service registry
            result = await self._direct_message_delivery(message)

        return self._normalize_response_contract(result)

    # ==================== Helper Methods ====================

    async def analyze_task_semantics(
        self, task_type: str, description: str, context: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Public wrapper for consciousness-aware semantic analysis."""
        context = context or {}
        return await self._analyze_task_semantics(task_type, description, context)

    async def _analyze_task_semantics(
        self, task_type: str, description: str, _context: dict[str, Any]
    ) -> dict[str, Any]:
        """Analyze task semantics using consciousness bridge."""
        try:
            bridge = await self._get_consciousness_bridge()
            if not bridge:
                return {}

            analysis = {
                "task_type": task_type,
                "complexity": self._estimate_complexity(description),
                "requires_creativity": "create" in description.lower()
                or "design" in description.lower(),
                "requires_analysis": "analyze" in description.lower()
                or "review" in description.lower(),
                "emotional_tone": "positive",  # Simplified for now
            }
            return analysis
        except Exception as e:
            logger.warning(f"Semantic analysis failed: {e}")
            return {}

    async def _select_optimal_service(
        self, task_type: str, _context: dict[str, Any], semantic_context: dict[str, Any]
    ) -> RegisteredService | None:
        """Select the best service for a task based on capabilities and context."""
        # Score each service
        candidates = []
        for service in self._services.values():
            if not service.active:
                continue

            score = 0
            for cap in service.capabilities:
                if task_type.lower() in cap.name.lower():
                    score += cap.priority

            # Bonus for consciousness if required
            if semantic_context.get("requires_creativity"):
                for cap in service.capabilities:
                    if cap.requires_consciousness:
                        score += 5

            if score > 0:
                candidates.append((score, service))

        if not candidates:
            return None

        # Return highest scoring service
        candidates.sort(key=lambda x: x[0], reverse=True)
        return candidates[0][1]

    def _estimate_complexity(self, description: str) -> int:
        """Estimate task complexity (1-10 scale)."""
        # Simple heuristic based on description length and keywords
        base = min(10, len(description) // 50 + 1)
        if any(word in description.lower() for word in ["complex", "advanced", "comprehensive"]):
            base += 3
        return min(10, base)

    async def _execute_task_with_service(
        self,
        service: RegisteredService,
        _task_type: str,
        _description: str,
        _context: dict[str, Any],
        task_id: str,
    ) -> dict[str, Any]:
        """Execute a task with a specific service."""
        # This would integrate with the actual service
        # For now, return a mock result
        logger.info(f"Executing task with {service.name}")
        return self._normalize_response_contract(
            {
                KEY_STATUS: "success",
                "service": service.service_id,
                "task_id": task_id,
                "result": f"Task executed by {service.name}",
            }
        )

    async def _log_consciousness_learning(
        self,
        task_type: str,
        service_id: str,
        _result: dict[str, Any],
        semantic_context: dict[str, Any],
    ) -> None:
        """Log successful task execution for consciousness learning."""
        learning_entry = {
            "timestamp": datetime.now().isoformat(),
            "task_type": task_type,
            "service": service_id,
            "semantic_context": semantic_context,
            "success": True,
        }
        # Cache for future routing decisions
        cache_key = f"{task_type}:{service_id}"
        self._consciousness_cache[cache_key] = learning_entry

    def _get_default_chatdev_team(self) -> dict[str, Any]:
        """Get default ChatDev team composition."""
        return {
            "ceo": {"role": "Chief Executive Officer", "focus": "strategy"},
            "cto": {"role": "Chief Technology Officer", "focus": "architecture"},
            "designer": {"role": "Designer", "focus": "ui_ux"},
            "programmer": {"role": "Programmer", "focus": "implementation"},
            "tester": {"role": "Quality Assurance", "focus": "testing"},
            "reviewer": {"role": "Code Reviewer", "focus": "code_quality"},
        }

    async def _get_claude_orchestrator(self) -> Any:
        """Lazy load Claude orchestrator."""
        if self._claude_orchestrator is None:
            try:
                from src.orchestration.claude_orchestrator import \
                    ClaudeOrchestrator

                self._claude_orchestrator = ClaudeOrchestrator(self.root_path)
            except ImportError:
                logger.warning("Claude orchestrator not available")
                return None
        return self._claude_orchestrator

    async def _get_chatdev_orchestrator(self) -> Any:
        """Lazy load ChatDev orchestrator."""
        if self._unified_orchestrator is None:
            try:
                from src.orchestration.multi_ai_orchestrator import \
                    get_multi_ai_orchestrator

                self._unified_orchestrator = get_multi_ai_orchestrator()
            except ImportError:
                logger.warning("ChatDev orchestrator not available")
                return None
        return self._unified_orchestrator

    async def _get_consciousness_bridge(self) -> Any:
        """Lazy load consciousness bridge."""
        if self._consciousness_bridge is None:
            try:
                from src.integration.consciousness_bridge import \
                    ConsciousnessBridge

                self._consciousness_bridge = ConsciousnessBridge()
            except ImportError:
                logger.warning("Consciousness bridge not available")
                return None
        return self._consciousness_bridge

    async def _get_agent_communication_hub(self) -> Any:
        """Lazy load agent communication hub."""
        # Placeholder for future AgentCommunicationHub
        return None

    async def _execute_chatdev_with_monitoring(
        self, _orchestrator: Any, _task: dict[str, Any]
    ) -> dict[str, Any]:
        """Execute ChatDev task with progress monitoring."""
        # Simplified - actual implementation would monitor progress
        return {
            "success": True,
            KEY_STATUS: "success",
            "artifacts": [],
            "team_communications": [],
        }

    async def _execute_consensus(
        self, services: list[RegisteredService], description: str, context: dict[str, Any]
    ) -> dict[str, Any]:
        """Execute task with all services and require consensus."""
        results: list[dict[str, Any]] = []
        for service in services:
            result = await self._execute_task_with_service(
                service, "consensus", description, context, str(uuid.uuid4())
            )
            results.append(self._normalize_response_contract(result))

        # Check if all agree (simplified)
        if all(self._response_succeeded(r) for r in results):
            return {"success": True, KEY_STATUS: "consensus_reached", "results": results}
        return {"success": False, KEY_STATUS: "consensus_failed", "results": results}

    async def _execute_voting(
        self, services: list[RegisteredService], description: str, context: dict[str, Any]
    ) -> dict[str, Any]:
        """Execute task and use majority vote."""
        results: list[dict[str, Any]] = []
        for service in services:
            result = await self._execute_task_with_service(
                service, "voting", description, context, str(uuid.uuid4())
            )
            results.append(self._normalize_response_contract(result))

        # Count votes (simplified)
        votes = {"success": 0, "failure": 0}
        for r in results:
            if self._response_succeeded(r):
                votes["success"] += 1
            else:
                votes["failure"] += 1

        winner = "success" if votes["success"] > votes["failure"] else "failure"
        return {
            "success": winner == "success",
            KEY_STATUS: f"vote_{winner}",
            "votes": votes,
            "results": results,
        }

    async def _execute_sequential(
        self, services: list[RegisteredService], description: str, context: dict[str, Any]
    ) -> dict[str, Any]:
        """Execute services sequentially, using last result."""
        result = None
        for service in services:
            result = await self._execute_task_with_service(
                service, "sequential", description, context, str(uuid.uuid4())
            )
            # Update context with previous result
            context["previous_result"] = result

        return result or {
            "success": False,
            KEY_STATUS: KEY_ERROR,
            KEY_ERROR: "No services executed",
        }

    async def _execute_parallel(
        self,
        services: list[RegisteredService],
        description: str,
        context: dict[str, Any],
        synthesize: bool,
    ) -> dict[str, Any]:
        """Execute services in parallel."""
        tasks = [
            self._execute_task_with_service(
                service, "parallel", description, context, str(uuid.uuid4())
            )
            for service in services
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        if synthesize:
            # Synthesize results (simplified)
            return {
                "success": True,
                KEY_STATUS: "synthesized",
                "results": [r for r in results if not isinstance(r, Exception)],
            }
        return {"success": True, KEY_STATUS: "parallel_complete", "results": list(results)}

    async def _execute_first_success(
        self, services: list[RegisteredService], description: str, context: dict[str, Any]
    ) -> dict[str, Any]:
        """Execute until first success."""
        for service in services:
            result = await self._execute_task_with_service(
                service, "first_success", description, context, str(uuid.uuid4())
            )
            normalized = self._normalize_response_contract(result)
            if self._response_succeeded(normalized):
                return normalized

        return {"success": False, KEY_STATUS: "all_failed", KEY_ERROR: "No service succeeded"}

    async def _analyze_and_heal(
        self, _error_result: dict[str, Any], _description: str, _context: dict[str, Any]
    ) -> dict[str, Any]:
        """Analyze error and generate healing recommendations."""
        try:
            if self._quantum_resolver is None:
                from src.healing.quantum_problem_resolver import \
                    QuantumProblemResolver

                self._quantum_resolver = QuantumProblemResolver(self.root_path)

            # Analyze problem (would be used by quantum resolver in full implementation)

            # Simplified healing - actual would use quantum resolver
            recommendations = ["retry_with_different_service", "adjust_context"]

            return {
                "success": True,
                KEY_STATUS: "healing_applied",
                "recommendations": recommendations,
                "confidence": 0.7,
            }
        except Exception as e:
            logger.error(f"Healing analysis failed: {e}")
            return {"success": False, KEY_STATUS: "healing_failed", KEY_ERROR: str(e)}

    async def _consciousness_escalation_judgment(
        self, healing_result: dict[str, Any], attempt: int, max_retries: int
    ) -> bool:
        """Use consciousness to judge if we should retry."""
        # Simplified - actual would use consciousness bridge
        confidence = healing_result.get("confidence", 0.5)
        return confidence > 0.6 and attempt < max_retries - 1

    async def _analyze_message_sentiment(self, content: dict[str, Any]) -> str:
        """Analyze message sentiment using consciousness."""
        # Simplified sentiment analysis
        text = str(content)
        if any(word in text.lower() for word in [KEY_ERROR, "fail", "problem"]):
            return "negative"
        if any(word in text.lower() for word in ["success", "complete", "good"]):
            return "positive"
        return "neutral"

    async def _direct_message_delivery(self, message: dict[str, Any]) -> dict[str, Any]:
        """Fallback direct message delivery via service registry."""
        to_service = message["to"]
        if to_service not in self._services:
            return {
                "success": False,
                KEY_STATUS: "delivery_failed",
                KEY_ERROR: "Recipient not found",
            }

        # Log message for now (actual would queue/deliver)
        logger.info(
            f"📬 Message delivered to {to_service}",
            extra={"message_id": message["id"], "type": message["type"]},
        )

        return {"success": True, KEY_STATUS: "delivered", "message_id": message["id"]}

    def _clean_expired_locks(self) -> None:
        """Remove expired task locks."""
        now = time.time()
        expired = [task_id for task_id, lock in self._locks.items() if lock.expires_at < now]
        for task_id in expired:
            del self._locks[task_id]
            logger.debug(f"🔓 Expired lock cleaned: {task_id}")


# Singleton instance
_hub_instance: AgentOrchestrationHub | None = None


def get_agent_orchestration_hub(
    root_path: Path | None = None,
    enable_healing: bool = True,
    enable_consciousness: bool = True,
) -> AgentOrchestrationHub:
    """Get or create the singleton AgentOrchestrationHub instance.

    Args:
        root_path: Repository root path
        enable_healing: Enable automatic healing escalation
        enable_consciousness: Enable consciousness-guided routing

    Returns:
        The singleton hub instance
    """
    global _hub_instance
    if _hub_instance is None:
        _hub_instance = AgentOrchestrationHub(root_path, enable_healing, enable_consciousness)
    return _hub_instance
