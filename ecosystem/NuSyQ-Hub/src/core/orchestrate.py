"""Simple Orchestration Facade for NuSyQ-Hub.

This provides a clean, unified interface to all the system's capabilities.
Instead of importing from 5+ different modules, just use:

    from src.core.orchestrate import nusyq

    # Quick actions
    nusyq.analyze("path/to/file.py")
    nusyq.search("authentication")
    nusyq.quest.add("Fix the login bug")
    nusyq.council.propose("Should we refactor auth?")
    nusyq.background.dispatch("Analyze this codebase")

This is the 10X developer experience.
"""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import Any, Protocol, cast

from .eol_facade_integration import EOLFacade
from .imports import (get_ai_council, get_background_orchestrator,
                      get_quest_engine, get_smart_search)
from .result import Fail, Ok, Result

logger = logging.getLogger(__name__)

JsonDict = dict[str, Any]


class SearchEngineProtocol(Protocol):
    """Minimal smart-search contract used by this facade."""

    def search_keyword(self, query: str) -> list[JsonDict]: ...
    def find_files(self, pattern: str) -> list[str]: ...
    def search_by_function(self, name: str) -> list[JsonDict]: ...
    def search_by_class(self, name: str) -> list[JsonDict]: ...
    def get_index_health(self) -> JsonDict: ...
    def get_index_stats(self) -> JsonDict: ...


class QuestRecordProtocol(Protocol):
    """Quest record shape needed by quest facade methods."""

    status: str

    def to_dict(self) -> JsonDict: ...


class QuestEngineProtocol(Protocol):
    """Quest engine contract used by quest facade."""

    quests: dict[str, QuestRecordProtocol]
    questlines: dict[str, Any]

    def add_quest(
        self,
        title: str,
        description: str = "",
        questline: str = "General",
        priority: str = "normal",
    ) -> str: ...
    def complete_quest(self, quest_id: str) -> None: ...


class DecisionStatusProtocol(Protocol):
    """Decision status enum-like wrapper."""

    value: str


class DecisionRecordProtocol(Protocol):
    """Decision record shape used by council facade."""

    status: DecisionStatusProtocol | str


class CouncilDecisionProtocol(Protocol):
    """Decision creation response shape."""

    decision_id: str


class AICouncilProtocol(Protocol):
    """AI council contract used by council facade."""

    def create_decision(
        self,
        *,
        decision_id: str,
        topic: str,
        description: str,
        proposed_by: str,
    ) -> CouncilDecisionProtocol: ...
    def cast_vote(
        self,
        *,
        decision_id: str,
        voter: str,
        vote: str,
        confidence: float,
    ) -> None: ...
    def list_decisions(self) -> list[DecisionRecordProtocol]: ...


class TaskPriorityProtocol(Protocol):
    """Task priority enum-like wrapper."""

    value: int


class BackgroundTaskProtocol(Protocol):
    """Background task shape used by background facade."""

    task_id: str
    priority: TaskPriorityProtocol
    status: Any

    def to_dict(self) -> JsonDict: ...


class BackgroundOrchestratorProtocol(Protocol):
    """Background orchestrator contract used by facade."""

    def submit_task(
        self,
        *,
        prompt: str,
        target: Any,
        task_type: str,
        priority: Any,
        requesting_agent: str,
    ) -> BackgroundTaskProtocol: ...
    def get_task(self, task_id: str) -> BackgroundTaskProtocol | None: ...
    def get_orchestrator_status(self) -> JsonDict: ...
    def list_tasks(self, status: Any = None) -> list[BackgroundTaskProtocol]: ...
    async def execute_task(self, task: BackgroundTaskProtocol) -> BackgroundTaskProtocol: ...


class FactoryResultProtocol(Protocol):
    """Factory create() result shape used for serialization."""

    name: str
    type: str
    version: str
    output_path: Path
    ai_provider: str | None
    model_used: str | None
    token_cost: float | int | None
    chatdev_warehouse_path: Path | None


class ProjectFactoryProtocol(Protocol):
    """ProjectFactory contract used by factory facade."""

    output_root: Path

    def _list_templates(self) -> list[str]: ...
    def run_health_check(self, include_packaging: bool = True) -> JsonDict: ...
    def inspect_reference_games(self, paths: list[str] | None = None) -> JsonDict: ...
    def run_doctor(
        self,
        strict_hooks: bool = False,
        include_examples: bool = True,
        include_health: bool = True,
        recent_limit: int = 25,
    ) -> JsonDict: ...
    def run_doctor_fix(
        self,
        strict_hooks: bool = False,
        include_examples: bool = True,
        include_health: bool = True,
        recent_limit: int = 25,
    ) -> JsonDict: ...
    def run_autopilot(
        self,
        fix: bool = False,
        strict_hooks: bool = False,
        include_examples: bool = True,
        recent_limit: int = 25,
        example_paths: list[str] | None = None,
    ) -> JsonDict: ...
    def create(
        self,
        *,
        name: str,
        template: str = "default_game",
        version: str = "1.0.0",
        description: str = "",
        ai_provider: str | None = None,
        auto_register: bool = True,
    ) -> FactoryResultProtocol: ...


class SearchFacade:
    """Facade for SmartSearch operations.

    Provides a simplified interface to the SmartSearch system, handling
    lazy initialization and error wrapping with Result types.

    Attributes:
        _parent: Reference to the parent NuSyQOrchestrator instance.
        _instance: Lazily initialized SmartSearch instance.

    Example:
        >>> facade = SearchFacade(orchestrator)
        >>> result = facade.find("authentication")
        >>> if result.ok:
        ...     print(f"Found {len(result.value)} results")
    """

    def __init__(self, parent: NuSyQOrchestrator):
        """Initialize the SearchFacade.

        Args:
            parent: The parent NuSyQOrchestrator instance that owns this facade.
        """
        self._parent = parent
        self._instance: SearchEngineProtocol | None = None

    def _get_instance(self) -> SearchEngineProtocol | None:
        if self._instance is None:
            smart_search_cls = get_smart_search()
            if smart_search_cls:
                self._instance = cast(SearchEngineProtocol, smart_search_cls())
        return self._instance

    def find(self, query: str, limit: int = 10) -> Result[list[dict]]:
        """Search for files and code matching the given query.

        Performs a keyword search across the indexed codebase and returns
        matching results up to the specified limit.

        Args:
            query: The search query string to match against files and code.
            limit: Maximum number of results to return. Defaults to 10.

        Returns:
            Result containing a list of matching result dictionaries on success,
            or a Fail result with error details on failure.

        Example:
            >>> result = facade.find("login handler", limit=5)
            >>> if result.ok:
            ...     for item in result.value:
            ...         print(item['path'])
        """
        ss = self._get_instance()
        if not ss:
            return Fail("SmartSearch not available", code="UNAVAILABLE")

        try:
            # Use search_keyword for general searches
            results = ss.search_keyword(query)
            # Limit results
            if isinstance(results, list):
                results = results[:limit]
            return Ok(
                results, message=f"Found {len(results) if isinstance(results, list) else 0} results"
            )
        except Exception as e:
            return Fail(str(e), code="SEARCH_ERROR")

    def find_files(self, pattern: str) -> Result[list[str]]:
        """Find files matching the given pattern.

        Searches the indexed file system for files matching the specified
        glob or regex pattern.

        Args:
            pattern: A glob or regex pattern to match file paths against.
                Examples: "*.py", "test_*.py", "src/**/models.py"

        Returns:
            Result containing a list of matching file paths on success,
            or a Fail result with error details on failure.

        Example:
            >>> result = facade.find_files("**/*.py")
            >>> if result.ok:
            ...     print(f"Found {len(result.value)} Python files")
        """
        ss = self._get_instance()
        if not ss:
            return Fail("SmartSearch not available", code="UNAVAILABLE")

        try:
            results = ss.find_files(pattern)
            return Ok(results, message=f"Found {len(results)} files")
        except Exception as e:
            return Fail(str(e), code="SEARCH_ERROR")

    def find_function(self, name: str) -> Result[list[dict]]:
        """Find function definitions by name.

        Searches the indexed codebase for function definitions matching
        the specified name.

        Args:
            name: The function name to search for. Can be a partial match
                depending on the underlying search implementation.

        Returns:
            Result containing a list of dictionaries with function details
            (location, signature, etc.) on success, or a Fail result on failure.

        Example:
            >>> result = facade.find_function("authenticate_user")
            >>> if result.ok:
            ...     for func in result.value:
            ...         print(f"{func['name']} in {func['file']}")
        """
        ss = self._get_instance()
        if not ss:
            return Fail("SmartSearch not available", code="UNAVAILABLE")

        try:
            results = ss.search_by_function(name)
            return Ok(results)
        except Exception as e:
            return Fail(str(e), code="SEARCH_ERROR")

    def find_class(self, name: str) -> Result[list[dict]]:
        """Find class definitions by name.

        Searches the indexed codebase for class definitions matching
        the specified name.

        Args:
            name: The class name to search for. Can be a partial match
                depending on the underlying search implementation.

        Returns:
            Result containing a list of dictionaries with class details
            (location, methods, etc.) on success, or a Fail result on failure.

        Example:
            >>> result = facade.find_class("UserAuthentication")
            >>> if result.ok:
            ...     for cls in result.value:
            ...         print(f"{cls['name']} defined in {cls['file']}")
        """
        ss = self._get_instance()
        if not ss:
            return Fail("SmartSearch not available", code="UNAVAILABLE")

        try:
            results = ss.search_by_class(name)
            return Ok(results)
        except Exception as e:
            return Fail(str(e), code="SEARCH_ERROR")

    def health(self) -> Result[dict]:
        """Get the health status of the search index.

        Checks the current state of the search index including whether
        it is properly initialized and accessible.

        Returns:
            Result containing a dictionary with health status information
            on success, or a Fail result on failure.

        Example:
            >>> result = facade.health()
            >>> if result.ok:
            ...     print(f"Index status: {result.value['status']}")
        """
        ss = self._get_instance()
        if not ss:
            return Fail("SmartSearch not available", code="UNAVAILABLE")

        try:
            status = ss.get_index_health()
            return Ok(status)
        except Exception as e:
            return Fail(str(e), code="HEALTH_ERROR")

    def stats(self) -> Result[dict]:
        """Get statistics about the search index.

        Retrieves metrics about the current search index including
        document count, index size, and other relevant statistics.

        Returns:
            Result containing a dictionary with index statistics on success,
            or a Fail result on failure.

        Example:
            >>> result = facade.stats()
            >>> if result.ok:
            ...     print(f"Indexed files: {result.value['file_count']}")
        """
        ss = self._get_instance()
        if not ss:
            return Fail("SmartSearch not available", code="UNAVAILABLE")

        try:
            stats = ss.get_index_stats()
            return Ok(stats)
        except Exception as e:
            return Fail(str(e), code="STATS_ERROR")


class QuestFacade:
    """Facade for Quest Engine operations.

    Provides a simplified interface to the Quest Engine system for managing
    tasks and quests within the NuSyQ ecosystem.

    Attributes:
        _parent: Reference to the parent NuSyQOrchestrator instance.
        _instance: Lazily initialized QuestEngine instance.

    Example:
        >>> facade = QuestFacade(orchestrator)
        >>> result = facade.add("Fix login bug", priority="high")
        >>> if result.ok:
        ...     print(f"Created quest: {result.value}")
    """

    def __init__(self, parent: NuSyQOrchestrator):
        """Initialize the QuestFacade.

        Args:
            parent: The parent NuSyQOrchestrator instance that owns this facade.
        """
        self._parent = parent
        self._instance: QuestEngineProtocol | None = None

    def _get_instance(self) -> QuestEngineProtocol | None:
        if self._instance is None:
            quest_engine_cls = get_quest_engine()
            if quest_engine_cls:
                self._instance = cast(QuestEngineProtocol, quest_engine_cls())
        return self._instance

    def add(
        self,
        title: str,
        description: str = "",
        questline: str = "General",
        priority: str = "normal",
    ) -> Result[str]:
        """Add a new quest to the quest system.

        Creates a new quest with the specified parameters and adds it
        to the active quest pool.

        Args:
            title: The title/name of the quest. Should be descriptive
                and actionable.
            description: Optional detailed description of what the quest
                entails. Defaults to empty string.
            questline: The questline category this quest belongs to.
                Defaults to "General".
            priority: Quest priority level. One of "low", "normal", "high",
                or "critical". Defaults to "normal".

        Returns:
            Result containing the quest ID string on success,
            or a Fail result with error details on failure.

        Example:
            >>> result = facade.add(
            ...     title="Fix authentication bug",
            ...     description="Users cannot log in with special characters",
            ...     questline="Security",
            ...     priority="high"
            ... )
            >>> if result.ok:
            ...     print(f"Quest created with ID: {result.value}")
        """
        qe = self._get_instance()
        if not qe:
            return Fail("QuestEngine not available", code="UNAVAILABLE")

        try:
            quest_id = qe.add_quest(
                title=title,
                description=description,
                questline=questline,
                priority=priority,
            )
            return Ok(quest_id, message=f"Quest created: {quest_id}")
        except Exception as e:
            return Fail(str(e), code="QUEST_ERROR")

    def complete(self, quest_id: str) -> Result[bool]:
        """Mark a quest as complete.

        Updates the status of the specified quest to completed and
        records the completion time.

        Args:
            quest_id: The unique identifier of the quest to complete.

        Returns:
            Result containing True on success, or a Fail result with
            error details if the quest was not found or could not be completed.

        Example:
            >>> result = facade.complete("quest_abc123")
            >>> if result.ok:
            ...     print("Quest completed successfully!")
        """
        qe = self._get_instance()
        if not qe:
            return Fail("QuestEngine not available", code="UNAVAILABLE")

        try:
            qe.complete_quest(quest_id)
            return Ok(True, message=f"Quest {quest_id} completed")
        except Exception as e:
            return Fail(str(e), code="QUEST_ERROR")

    def list(self, status: str | None = None) -> Result[list]:
        """List all quests, optionally filtered by status.

        Retrieves all quests from the quest engine, with optional filtering
        by quest status.

        Args:
            status: Optional status filter. Common values include "pending",
                "in_progress", "completed". If None, returns all quests.

        Returns:
            Result containing a list of quest dictionaries on success,
            or a Fail result with error details on failure.

        Example:
            >>> result = facade.list(status="pending")
            >>> if result.ok:
            ...     for quest in result.value:
            ...         print(f"{quest['title']}: {quest['status']}")
        """
        qe = self._get_instance()
        if not qe:
            return Fail("QuestEngine not available", code="UNAVAILABLE")

        try:
            quests = list(qe.quests.values())
            if status:
                quests = [q for q in quests if q.status == status]
            return Ok([q.to_dict() for q in quests])
        except Exception as e:
            return Fail(str(e), code="QUEST_ERROR")

    def status(self) -> Result[dict]:
        """Get the current status of the quest engine.

        Returns aggregate statistics about quests including total count,
        completed count, and pending count.

        Returns:
            Result containing a dictionary with quest statistics on success:
                - total: Total number of quests
                - completed: Number of completed quests
                - pending: Number of pending quests
                - questlines: Number of active questlines
            Or a Fail result with error details on failure.

        Example:
            >>> result = facade.status()
            >>> if result.ok:
            ...     stats = result.value
            ...     print(f"Quests: {stats['completed']}/{stats['total']} done")
        """
        qe = self._get_instance()
        if not qe:
            return Fail("QuestEngine not available", code="UNAVAILABLE")

        try:
            total = len(qe.quests)
            completed = sum(1 for q in qe.quests.values() if q.status == "completed")
            pending = sum(1 for q in qe.quests.values() if q.status == "pending")
            return Ok(
                {
                    "total": total,
                    "completed": completed,
                    "pending": pending,
                    "questlines": len(qe.questlines),
                }
            )
        except Exception as e:
            return Fail(str(e), code="QUEST_ERROR")


class CouncilFacade:
    """Facade for AI Council voting operations.

    Provides a simplified interface to the AI Council system for proposing
    decisions and casting votes in a multi-agent consensus mechanism.

    Attributes:
        _parent: Reference to the parent NuSyQOrchestrator instance.
        _instance: Lazily initialized AICouncil instance.

    Example:
        >>> facade = CouncilFacade(orchestrator)
        >>> result = facade.propose("Should we refactor the auth module?")
        >>> if result.ok:
        ...     print(f"Decision proposed: {result.value}")
    """

    def __init__(self, parent: NuSyQOrchestrator):
        """Initialize the CouncilFacade.

        Args:
            parent: The parent NuSyQOrchestrator instance that owns this facade.
        """
        self._parent = parent
        self._instance: AICouncilProtocol | None = None

    def _get_instance(self) -> AICouncilProtocol | None:
        if self._instance is None:
            ai_council_cls = get_ai_council()
            if ai_council_cls:
                self._instance = cast(AICouncilProtocol, ai_council_cls())
        return self._instance

    def propose(
        self, topic: str, description: str = "", proposer: str = "orchestrator"
    ) -> Result[str]:
        """Propose a decision to the AI Council for voting.

        Creates a new decision proposal that council members can vote on.
        The decision will remain open for voting until resolved.

        Args:
            topic: The main topic or question to be decided. Should be
                phrased as a clear decision point.
            description: Optional detailed description providing context
                for the decision. Defaults to empty string.
            proposer: Identifier of the agent proposing the decision.
                Defaults to "orchestrator".

        Returns:
            Result containing the decision ID string on success,
            or a Fail result with error details on failure.

        Example:
            >>> result = facade.propose(
            ...     topic="Should we migrate to PostgreSQL?",
            ...     description="Current SQLite causing performance issues",
            ...     proposer="data_agent"
            ... )
            >>> if result.ok:
            ...     print(f"Decision ID: {result.value}")
        """
        council = self._get_instance()
        if not council:
            return Fail("AICouncil not available", code="UNAVAILABLE")

        try:
            import uuid

            decision_id = str(uuid.uuid4())[:8]
            # create_decision expects: decision_id, topic, description, proposed_by
            decision = council.create_decision(
                decision_id=decision_id,
                topic=topic,
                description=description or topic,
                proposed_by=proposer,
            )
            # Return the decision_id from the created decision
            result_id = decision.decision_id if hasattr(decision, "decision_id") else decision_id
            return Ok(result_id, message=f"Decision proposed: {result_id}")
        except Exception as e:
            return Fail(str(e), code="COUNCIL_ERROR")

    def vote(
        self, decision_id: str, vote: str, voter: str = "orchestrator", confidence: float = 0.8
    ) -> Result[bool]:
        """Cast a vote on a council decision.

        Records a vote from a council member on an existing decision.
        Votes are weighted by the confidence level.

        Args:
            decision_id: The unique identifier of the decision to vote on.
            vote: The vote value. Typically "approve", "reject", or "abstain".
            voter: Identifier of the agent casting the vote.
                Defaults to "orchestrator".
            confidence: Confidence level of the vote, from 0.0 to 1.0.
                Higher values give more weight to the vote. Defaults to 0.8.

        Returns:
            Result containing True on success, or a Fail result with
            error details if the vote could not be cast.

        Example:
            >>> result = facade.vote(
            ...     decision_id="dec_xyz789",
            ...     vote="approve",
            ...     voter="security_agent",
            ...     confidence=0.95
            ... )
            >>> if result.ok:
            ...     print("Vote recorded successfully")
        """
        council = self._get_instance()
        if not council:
            return Fail("AICouncil not available", code="UNAVAILABLE")

        try:
            council.cast_vote(
                decision_id=decision_id,
                voter=voter,
                vote=vote,
                confidence=confidence,
            )
            return Ok(True, message=f"Vote cast on {decision_id}")
        except Exception as e:
            return Fail(str(e), code="COUNCIL_ERROR")

    def status(self) -> Result[dict]:
        """Get the current status of the AI Council.

        Returns aggregate statistics about council decisions including
        total decisions, approved count, and pending count.

        Returns:
            Result containing a dictionary with council statistics on success:
                - total_decisions: Total number of decisions
                - approved: Number of approved decisions
                - pending: Number of pending decisions
            Or a Fail result with error details on failure.

        Example:
            >>> result = facade.status()
            >>> if result.ok:
            ...     stats = result.value
            ...     print(f"Pending decisions: {stats['pending']}")
        """
        council = self._get_instance()
        if not council:
            return Fail("AICouncil not available", code="UNAVAILABLE")

        try:
            decisions = council.list_decisions()
            # Handle both enum and string status
            approved = 0
            pending = 0
            for d in decisions:
                status_val = d.status.value if hasattr(d.status, "value") else str(d.status)
                if status_val == "approved":
                    approved += 1
                elif status_val == "pending":
                    pending += 1
            return Ok(
                {
                    "total_decisions": len(decisions),
                    "approved": approved,
                    "pending": pending,
                }
            )
        except Exception as e:
            return Fail(str(e), code="COUNCIL_ERROR")


class BackgroundFacade:
    """Facade for Background Task Orchestrator operations.

    Provides a simplified interface to dispatch and manage background
    tasks to local LLMs for code analysis and other AI-powered operations.

    Attributes:
        _parent: Reference to the parent NuSyQOrchestrator instance.
        _instance: Lazily initialized BackgroundOrchestrator instance.

    Example:
        >>> facade = BackgroundFacade(orchestrator)
        >>> result = facade.dispatch("Analyze this codebase for security issues")
        >>> if result.ok:
        ...     print(f"Task dispatched: {result.value}")
    """

    def __init__(self, parent: NuSyQOrchestrator):
        """Initialize the BackgroundFacade.

        Args:
            parent: The parent NuSyQOrchestrator instance that owns this facade.
        """
        self._parent = parent
        self._instance: BackgroundOrchestratorProtocol | None = None

    def _get_instance(self) -> BackgroundOrchestratorProtocol | None:
        if self._instance is None:
            background_orchestrator_cls = get_background_orchestrator()
            if background_orchestrator_cls:
                self._instance = cast(BackgroundOrchestratorProtocol, background_orchestrator_cls())
        return self._instance

    def dispatch(
        self,
        prompt: str,
        task_type: str = "code_analysis",
        target: str = "auto",
        priority: str = "normal",
    ) -> Result[str]:
        """Dispatch a task to local LLMs for background processing.

        Submits a task to the background orchestrator which routes it
        to the appropriate local LLM based on the task type and target.

        Args:
            prompt: The prompt or instruction for the LLM to process.
            task_type: The type of task being dispatched. Common types include
                "code_analysis", "code_review", "documentation", "refactoring".
                Defaults to "code_analysis".
            target: The target LLM to use. Can be "auto" for automatic selection,
                or a specific target identifier. Defaults to "auto".
            priority: Task priority level. One of "low", "normal", "high",
                or "critical". Defaults to "normal".

        Returns:
            Result containing the task ID string on success,
            or a Fail result with error details on failure.

        Example:
            >>> result = facade.dispatch(
            ...     prompt="Review the authentication module for security issues",
            ...     task_type="code_review",
            ...     priority="high"
            ... )
            >>> if result.ok:
            ...     print(f"Task submitted with ID: {result.value}")
        """
        bg = self._get_instance()
        if not bg:
            return Fail("BackgroundOrchestrator not available", code="UNAVAILABLE")

        try:
            # Import the enums
            from src.orchestration.background_task_orchestrator import (
                TaskPriority, TaskTarget)

            target_enum = TaskTarget(target) if target != "auto" else TaskTarget.AUTO
            priority_map = {
                "low": TaskPriority.LOW,
                "normal": TaskPriority.NORMAL,
                "high": TaskPriority.HIGH,
                "critical": TaskPriority.CRITICAL,
            }
            priority_enum = priority_map.get(priority.lower(), TaskPriority.NORMAL)

            # Submit task (synchronous method - returns BackgroundTask directly)
            task = bg.submit_task(
                prompt=prompt,
                target=target_enum,
                task_type=task_type,
                priority=priority_enum,
                requesting_agent="orchestrator",
            )
            # Extract task_id from the returned BackgroundTask object
            task_id = task.task_id if hasattr(task, "task_id") else str(task)
            return Ok(task_id, message=f"Task dispatched: {task_id}")
        except Exception as e:
            return Fail(str(e), code="DISPATCH_ERROR")

    def status(self, task_id: str | None = None) -> Result[dict]:
        """Get the status of background tasks.

        Retrieves either the status of a specific task or overall
        orchestrator status if no task ID is provided.

        Args:
            task_id: Optional task ID to get status for. If None,
                returns overall orchestrator status.

        Returns:
            Result containing a dictionary with status information on success:
                - For specific task: task details including status, result, etc.
                - For orchestrator: queue sizes, active tasks, etc.
            Or a Fail result with error details on failure.

        Example:
            >>> # Get specific task status
            >>> result = facade.status(task_id="task_abc123")
            >>> if result.ok:
            ...     print(f"Task status: {result.value['status']}")
            >>>
            >>> # Get overall status
            >>> result = facade.status()
            >>> if result.ok:
            ...     print(f"Active tasks: {result.value['active_count']}")
        """
        bg = self._get_instance()
        if not bg:
            return Fail("BackgroundOrchestrator not available", code="UNAVAILABLE")

        try:
            if task_id:
                task = bg.get_task(task_id)
                if task:
                    return Ok(task.to_dict())
                return Fail(f"Task {task_id} not found", code="NOT_FOUND")

            # Use get_orchestrator_status method
            status = bg.get_orchestrator_status()
            return Ok(status)
        except Exception as e:
            return Fail(str(e), code="STATUS_ERROR")

    def list_tasks(self, status_filter: str | None = None) -> Result[list]:
        """List all background tasks with optional filtering.

        Retrieves all tasks from the background orchestrator, optionally
        filtered by task status.

        Args:
            status_filter: Optional status filter. Common values include
                "queued", "running", "completed", "failed". If None,
                returns all tasks.

        Returns:
            Result containing a list of task dictionaries on success,
            or a Fail result with error details on failure.

        Example:
            >>> result = facade.list_tasks(status_filter="running")
            >>> if result.ok:
            ...     for task in result.value:
            ...         print(f"{task['id']}: {task['prompt'][:50]}...")
        """
        bg = self._get_instance()
        if not bg:
            return Fail("BackgroundOrchestrator not available", code="UNAVAILABLE")

        try:
            from src.orchestration.background_task_orchestrator import \
                TaskStatus

            # Convert string to enum if provided
            task_status = TaskStatus(status_filter) if status_filter else None
            tasks = bg.list_tasks(status=task_status)
            return Ok([t.to_dict() for t in tasks])
        except Exception as e:
            return Fail(str(e), code="LIST_ERROR")

    def process_one(self, task_id: str | None = None) -> Result[dict]:
        """Process a single queued task (or the next one in queue).

        Executes either a specific task by ID or the next queued task.
        The task is processed synchronously and the result is returned.

        Args:
            task_id: Optional task ID to process. If None, processes
                the next task in the queue by priority.

        Returns:
            Result containing the processed task dictionary on success,
            or a Fail result with error details on failure.

        Example:
            >>> result = facade.process_one()
            >>> if result.ok:
            ...     print(f"Processed: {result.value['task_id']}")
        """
        bg = self._get_instance()
        if not bg:
            return Fail("BackgroundOrchestrator not available", code="UNAVAILABLE")

        try:
            from src.orchestration.background_task_orchestrator import \
                TaskStatus

            # Get the task to process
            if task_id:
                task = bg.get_task(task_id)
                if not task:
                    return Fail(f"Task {task_id} not found", code="NOT_FOUND")
            else:
                # Get next queued task by priority
                queued_tasks = bg.list_tasks(status=TaskStatus.QUEUED)
                if not queued_tasks:
                    return Ok({"message": "No queued tasks to process"})
                # Sort by priority (higher = more urgent)
                queued_tasks.sort(key=lambda t: t.priority.value, reverse=True)
                task = queued_tasks[0]

            # Execute the task
            result_task = asyncio.run(bg.execute_task(task))
            return Ok(result_task.to_dict(), message=f"Task {task.task_id} processed")
        except Exception as e:
            return Fail(str(e), code="PROCESS_ERROR")

    def process_batch(self, limit: int = 5) -> Result[dict]:
        """Process multiple queued tasks in batch.

        Executes up to `limit` queued tasks sequentially,
        prioritizing by task priority level.

        Args:
            limit: Maximum number of tasks to process. Defaults to 5.

        Returns:
            Result containing a summary dictionary on success:
                - processed: Number of tasks processed
                - succeeded: Number of successful tasks
                - failed: Number of failed tasks
                - results: List of task result dictionaries
            Or a Fail result with error details on failure.

        Example:
            >>> result = facade.process_batch(limit=10)
            >>> if result.ok:
            ...     print(f"Processed {result.value['processed']} tasks")
        """
        bg = self._get_instance()
        if not bg:
            return Fail("BackgroundOrchestrator not available", code="UNAVAILABLE")

        try:
            from src.orchestration.background_task_orchestrator import \
                TaskStatus

            queued_tasks = bg.list_tasks(status=TaskStatus.QUEUED)
            if not queued_tasks:
                return Ok({"processed": 0, "message": "No queued tasks"})

            # Sort by priority and take up to limit
            queued_tasks.sort(key=lambda t: t.priority.value, reverse=True)
            to_process = queued_tasks[:limit]

            results = []
            succeeded = 0
            failed = 0

            for task in to_process:
                try:
                    result_task = asyncio.run(bg.execute_task(task))
                    results.append(result_task.to_dict())
                    if result_task.status == TaskStatus.COMPLETED:
                        succeeded += 1
                    else:
                        failed += 1
                except Exception as e:
                    failed += 1
                    results.append({"task_id": task.task_id, "error": str(e)})

            return Ok(
                {
                    "processed": len(to_process),
                    "succeeded": succeeded,
                    "failed": failed,
                    "results": results,
                }
            )
        except Exception as e:
            return Fail(str(e), code="BATCH_ERROR")


class FactoryFacade:
    """Facade for factory orchestration and diagnostics.

    Provides agent-friendly access to the project factory so orchestration flows
    can create projects, run smoke probes, and inspect reference game packages.
    """

    def __init__(self, parent: NuSyQOrchestrator):
        self._parent = parent
        self._instance: ProjectFactoryProtocol | None = None

    def _get_instance(self) -> ProjectFactoryProtocol | None:
        if self._instance is None:
            try:
                from src.factories import ProjectFactory
            except ImportError:
                ProjectFactory = None
            if ProjectFactory:
                self._instance = cast(ProjectFactoryProtocol, ProjectFactory())
        return self._instance

    def status(self) -> Result[dict]:
        """Return quick availability and template metadata for the factory."""
        factory = self._get_instance()
        if not factory:
            return Fail("ProjectFactory not available", code="UNAVAILABLE")

        try:
            templates = factory._list_templates()
            return Ok(
                {
                    "available": True,
                    "template_count": len(templates),
                    "templates": templates,
                    "output_root": str(factory.output_root),
                }
            )
        except Exception as e:
            return Fail(str(e), code="FACTORY_STATUS_ERROR")

    def health(self, include_packaging: bool = True) -> Result[dict]:
        """Run factory health probes (fallback/bootstrap/packaging)."""
        factory = self._get_instance()
        if not factory:
            return Fail("ProjectFactory not available", code="UNAVAILABLE")

        try:
            return Ok(factory.run_health_check(include_packaging=include_packaging))
        except Exception as e:
            return Fail(str(e), code="FACTORY_HEALTH_ERROR")

    def inspect_examples(self, paths: list[str] | None = None) -> Result[dict]:
        """Inspect reference game installations to extract runtime/packaging signals."""
        factory = self._get_instance()
        if not factory:
            return Fail("ProjectFactory not available", code="UNAVAILABLE")

        try:
            return Ok(factory.inspect_reference_games(paths=paths))
        except Exception as e:
            return Fail(str(e), code="FACTORY_INSPECT_ERROR")

    def doctor(
        self,
        strict_hooks: bool = False,
        include_examples: bool = True,
        include_health: bool = True,
        recent_limit: int = 25,
    ) -> Result[dict]:
        """Run fail-fast factory diagnostics across health and generation quality."""
        factory = self._get_instance()
        if not factory:
            return Fail("ProjectFactory not available", code="UNAVAILABLE")

        try:
            return Ok(
                factory.run_doctor(
                    strict_hooks=strict_hooks,
                    include_examples=include_examples,
                    include_health=include_health,
                    recent_limit=recent_limit,
                )
            )
        except Exception as e:
            return Fail(str(e), code="FACTORY_DOCTOR_ERROR")

    def doctor_fix(
        self,
        strict_hooks: bool = False,
        include_examples: bool = True,
        include_health: bool = True,
        recent_limit: int = 25,
    ) -> Result[dict]:
        """Run doctor and apply safe remediation actions."""
        factory = self._get_instance()
        if not factory:
            return Fail("ProjectFactory not available", code="UNAVAILABLE")

        try:
            return Ok(
                factory.run_doctor_fix(
                    strict_hooks=strict_hooks,
                    include_examples=include_examples,
                    include_health=include_health,
                    recent_limit=recent_limit,
                )
            )
        except Exception as e:
            return Fail(str(e), code="FACTORY_DOCTOR_FIX_ERROR")

    def autopilot(
        self,
        fix: bool = False,
        strict_hooks: bool = False,
        include_examples: bool = True,
        recent_limit: int = 25,
        example_paths: list[str] | None = None,
    ) -> Result[dict]:
        """Run doctor + example inspection + patch plan loop."""
        factory = self._get_instance()
        if not factory:
            return Fail("ProjectFactory not available", code="UNAVAILABLE")

        try:
            return Ok(
                factory.run_autopilot(
                    fix=fix,
                    strict_hooks=strict_hooks,
                    include_examples=include_examples,
                    recent_limit=recent_limit,
                    example_paths=example_paths,
                )
            )
        except Exception as e:
            return Fail(str(e), code="FACTORY_AUTOPILOT_ERROR")

    def create(
        self,
        name: str,
        template: str = "default_game",
        version: str = "1.0.0",
        description: str = "",
        ai_provider: str | None = None,
        auto_register: bool = True,
    ) -> Result[dict]:
        """Create a project through the unified factory facade."""
        factory = self._get_instance()
        if not factory:
            return Fail("ProjectFactory not available", code="UNAVAILABLE")

        try:
            result = factory.create(
                name=name,
                template=template,
                version=version,
                description=description,
                ai_provider=ai_provider,
                auto_register=auto_register,
            )
            return Ok(
                {
                    "name": result.name,
                    "type": result.type,
                    "version": result.version,
                    "output_path": str(result.output_path),
                    "ai_provider": result.ai_provider,
                    "model_used": result.model_used,
                    "token_cost": result.token_cost,
                    "chatdev_warehouse_path": (
                        str(result.chatdev_warehouse_path)
                        if result.chatdev_warehouse_path
                        else None
                    ),
                }
            )
        except Exception as e:
            return Fail(str(e), code="FACTORY_CREATE_ERROR")


class NuSyQOrchestrator:
    """Unified orchestrator for all NuSyQ systems.

    Provides a single entry point to access all NuSyQ subsystems including
    search, quests, AI council, and background task processing. Uses lazy
    initialization to only load components when accessed.

    Attributes:
        search: Facade for SmartSearch operations.
        quest: Facade for Quest Engine operations.
        council: Facade for AI Council operations.
        background: Facade for Background Task Orchestrator operations.
        factory: Facade for project factory orchestration and diagnostics.

    Example:
        >>> from src.core.orchestrate import nusyq
        >>>
        >>> # Search for code
        >>> result = nusyq.search.find("authentication")
        >>>
        >>> # Create a quest
        >>> result = nusyq.quest.add("Fix login bug")
        >>>
        >>> # Propose to the council
        >>> result = nusyq.council.propose("Refactor auth system?")
        >>>
        >>> # Dispatch a background task
        >>> result = nusyq.background.dispatch("Analyze codebase")
        >>>
        >>> # Quick analysis shortcut
        >>> nusyq.analyze("src/auth/login.py")
    """

    def __init__(self) -> None:
        """Initialize the NuSyQOrchestrator.

        Creates a new orchestrator instance with lazy-loaded facades
        for each subsystem. Facades are only instantiated when first accessed.
        """
        self._search: SearchFacade | None = None
        self._quest: QuestFacade | None = None
        self._council: CouncilFacade | None = None
        self._background: BackgroundFacade | None = None
        self._factory: FactoryFacade | None = None
        self._eol: EOLFacade | None = None

    @property
    def search(self) -> SearchFacade:
        """Access the search operations facade.

        Returns:
            SearchFacade: Facade providing access to SmartSearch operations
                including file search, code search, and index management.

        Example:
            >>> result = nusyq.search.find("login handler")
            >>> result = nusyq.search.find_files("**/*.py")
        """
        if self._search is None:
            self._search = SearchFacade(self)
        return self._search

    @property
    def quest(self) -> QuestFacade:
        """Access the quest operations facade.

        Returns:
            QuestFacade: Facade providing access to Quest Engine operations
                including adding, completing, and listing quests.

        Example:
            >>> result = nusyq.quest.add("Fix the bug")
            >>> result = nusyq.quest.list(status="pending")
        """
        if self._quest is None:
            self._quest = QuestFacade(self)
        return self._quest

    @property
    def council(self) -> CouncilFacade:
        """Access the AI council operations facade.

        Returns:
            CouncilFacade: Facade providing access to AI Council operations
                including proposing decisions and casting votes.

        Example:
            >>> result = nusyq.council.propose("Should we refactor?")
            >>> result = nusyq.council.vote("dec_123", "approve")
        """
        if self._council is None:
            self._council = CouncilFacade(self)
        return self._council

    @property
    def background(self) -> BackgroundFacade:
        """Access the background task operations facade.

        Returns:
            BackgroundFacade: Facade providing access to Background Task
                Orchestrator operations including task dispatch and monitoring.

        Example:
            >>> result = nusyq.background.dispatch("Analyze code")
            >>> result = nusyq.background.status("task_123")
        """
        if self._background is None:
            self._background = BackgroundFacade(self)
        return self._background

    @property
    def factory(self) -> FactoryFacade:
        """Access the project factory facade.

        Returns:
            FactoryFacade: Facade for create/health/inspection operations.
        """
        if self._factory is None:
            self._factory = FactoryFacade(self)
        return self._factory

    @property
    def eol(self) -> EOLFacade:
        """Access the Epistemic-Operational Lattice facade.

        Returns the EOL orchestrator for sense → propose → act workflows.
        Provides access to the complete decision cycle with world state
        sensing, action proposal, policy evaluation, and execution tracing.

        Returns:
            EOLFacade: Facade providing EOL decision cycle operations.

        Example:
            >>> from src.core.orchestrate import nusyq
            >>>
            >>> # Run complete cycle
            >>> result = nusyq.eol.full_cycle("Analyze errors", auto_execute=False)
            >>> if result.ok:
            ...     print(f"Actions: {len(result.value['actions'])}")
            >>>
            >>> # Manual phases
            >>> world = nusyq.eol.sense()
            >>> actions = nusyq.eol.propose(world, "Fix bugs")
            >>> receipt = nusyq.eol.act(actions[0], world)
        """
        if self._eol is None:
            self._eol = EOLFacade(self)
        return self._eol

    def analyze(self, path: str, analysis_type: str = "code_analysis") -> Result[str]:
        """Quick analyze a file or directory.

        Convenience method that dispatches an analysis task to the background
        orchestrator for the specified path.

        Args:
            path: Path to the file or directory to analyze.
            analysis_type: Type of analysis to perform. Defaults to "code_analysis".
                Other options include "security_audit", "performance", etc.

        Returns:
            Result containing the task ID string on success,
            or a Fail result with error details on failure.

        Example:
            >>> result = nusyq.analyze("src/auth/login.py")
            >>> if result.ok:
            ...     print(f"Analysis task: {result.value}")
        """
        return self.background.dispatch(
            prompt=f"Analyze the code at: {path}",
            task_type=analysis_type,
        )

    def status(self) -> Result[dict]:
        """Get the overall system status.

        Retrieves status information from all subsystems and aggregates
        them into a single status report.

        Returns:
            Result containing a dictionary with status from each subsystem:
                - search: SmartSearch health status
                - quest: Quest Engine status
                - council: AI Council status
                - background: Background Orchestrator status

        Example:
            >>> result = nusyq.status()
            >>> if result.ok:
            ...     for system, status in result.value.items():
            ...         print(f"{system}: {status}")
        """
        return Ok(
            {
                "search": self.search.health().to_dict(),
                "quest": self.quest.status().to_dict(),
                "council": self.council.status().to_dict(),
                "background": self.background.status().to_dict(),
                "factory": self.factory.status().to_dict(),
            }
        )


# Global singleton instance
nusyq = NuSyQOrchestrator()

# Convenience exports
__all__ = ["NuSyQOrchestrator", "nusyq"]
