"""Zen Codex Integration Bridge.

Enables bidirectional communication between NuSyQ ecosystem and Zen Engine.

This bridge allows:
- Claude (this AI) to query Zen Codex for wisdom and rules
- Zen Engine agents (Copilot, Ollama, ChatDev) to interact with ecosystem
- Bidirectional orchestration and learning
- Shared session context across all agents

OmniTag: {
    "purpose": "zen_ecosystem_bridge",
    "tags": ["Python", "ZenEngine", "MultiAgent", "Orchestration"],
    "category": "integration",
    "evolution_stage": "v1.0"
}
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class ZenAgentInteraction:
    """Represents an interaction between ecosystem and Zen agents."""

    timestamp: str
    source_agent: str  # "claude", "ollama", "copilot", "chatdev"
    target_agent: str | None
    interaction_type: str  # "query", "command", "response", "wisdom_share"
    payload: dict[str, Any]
    response: dict[str, Any] | None = None


class ZenCodexBridge:
    """Bridge between NuSyQ ecosystem and Zen Engine.

    Capabilities:
    1. Query Zen Codex from ecosystem agents (including Claude)
    2. Route errors to Zen orchestrator for wisdom-based handling
    3. Enable Zen agents to invoke NuSyQ capabilities
    4. Track bidirectional communication and learning
    5. Coordinate multi-agent workflows across both systems
    """

    def __init__(self, codex_path: Path | str | None = None) -> None:
        """Initialize the Zen Codex Bridge."""
        self.codex_path = Path(codex_path or "zen_engine/codex/zen.json")
        self.codex_loader = None
        self.zen_orchestrator = None
        self.codex_builder = None  # For recursive learning
        self.error_observer = None  # For error capture
        self.interaction_history: list[ZenAgentInteraction] = []
        self.initialized = False

        logger.info("🌉 Initializing Zen Codex Bridge")

    def initialize(self) -> bool:
        """Initialize the bridge (ecosystem activator compatible)."""
        try:
            # Add project root to Python path for zen_engine imports
            import sys
            from pathlib import Path

            project_root = Path(__file__).parent.parent.parent
            if str(project_root) not in sys.path:
                sys.path.insert(0, str(project_root))

            # Import Zen Engine components
            from zen_engine.agents.builder import CodexBuilder
            from zen_engine.agents.codex_loader import CodexLoader
            from zen_engine.agents.error_observer import ErrorObserver
            from zen_engine.agents.orchestrator import ZenOrchestrator

            # Initialize Codex Loader
            self.codex_loader = CodexLoader(codex_path=self.codex_path)
            logger.info(
                f"✅ Zen Codex loaded: {len(self.codex_loader.rules)} rules, {len(self.codex_loader.rules_by_tag)} tags"
            )

            # Initialize Zen Orchestrator
            self.zen_orchestrator = ZenOrchestrator(codex_path=self.codex_path)
            logger.info(
                f"✅ Zen Orchestrator initialized: {len(self.zen_orchestrator.agents)} agents"
            )

            # Initialize CodexBuilder for recursive learning
            self.codex_builder = CodexBuilder(codex_loader=self.codex_loader)
            logger.info("✅ Codex Builder initialized - recursive learning ready")

            # Initialize ErrorObserver for error capture
            self.error_observer = ErrorObserver()
            logger.info("✅ Error Observer initialized - error capture ready")

            self.initialized = True
            logger.info(
                "🌉 Zen Codex Bridge active - bidirectional communication + learning enabled"
            )
            return True

        except Exception as e:
            logger.error(f"❌ Failed to initialize Zen Codex Bridge: {e}")
            return False

    # =============================================================================
    # CLAUDE → ZEN CODEX (Query capabilities)
    # =============================================================================

    def query_rules_by_tag(self, tag: str) -> list[dict[str, Any]]:
        """Query Zen Codex for rules matching a tag.

        Args:
            tag: Tag to search for (e.g., "powershell", "import", "git")

        Returns:
            List of matching rules with lessons and suggestions
        """
        if not self.initialized or not self.codex_loader:
            return []

        rules = self.codex_loader.get_rules_by_tag(tag)

        # Record interaction
        interaction = ZenAgentInteraction(
            timestamp=datetime.now().isoformat(),
            source_agent="claude",
            target_agent="zen_codex",
            interaction_type="query",
            payload={"query_type": "tag", "tag": tag},
            response={"rules_count": len(rules)},
        )
        self.interaction_history.append(interaction)

        return [self._rule_to_dict(rule) for rule in rules]

    def search_rules(self, query: str) -> list[dict[str, Any]]:
        """Search Zen Codex for rules matching a keyword.

        Args:
            query: Search query (e.g., "import error", "git conflict")

        Returns:
            List of matching rules
        """
        if not self.initialized or not self.codex_loader:
            return []

        rules = self.codex_loader.search_rules(query)

        # Record interaction
        interaction = ZenAgentInteraction(
            timestamp=datetime.now().isoformat(),
            source_agent="claude",
            target_agent="zen_codex",
            interaction_type="query",
            payload={"query_type": "search", "query": query},
            response={"rules_count": len(rules)},
        )
        self.interaction_history.append(interaction)

        return [self._rule_to_dict(rule) for rule in rules]

    def get_wisdom_for_error(self, error_type: str, error_message: str) -> dict[str, Any]:
        """Get Zen wisdom for handling a specific error.

        Args:
            error_type: Type of error (e.g., "ImportError", "AttributeError")
            error_message: Error message text

        Returns:
            Wisdom response with matched rules and suggestions
        """
        if not self.initialized or not self.zen_orchestrator:
            return {"matched_rules": [], "suggestions": []}

        # Create error event
        error_event = {
            "type": error_type,
            "message": error_message,
            "timestamp": datetime.now().isoformat(),
        }

        # Capture in Zen orchestrator
        response = self.zen_orchestrator.capture_error(error_event, agent_name="claude")

        # Record interaction
        interaction = ZenAgentInteraction(
            timestamp=datetime.now().isoformat(),
            source_agent="claude",
            target_agent="zen_orchestrator",
            interaction_type="wisdom_share",
            payload=error_event,
            response=response,
        )
        self.interaction_history.append(interaction)

        return response

    # =============================================================================
    # ZEN AGENTS → ECOSYSTEM (Invoke capabilities)
    # =============================================================================

    def zen_agent_query_ecosystem(
        self, agent_name: str, capability: str, parameters: dict[str, Any]
    ) -> dict[str, Any]:
        """Allow Zen agents to query NuSyQ ecosystem capabilities.

        Args:
            agent_name: Name of Zen agent (copilot, ollama, chatdev)
            capability: Capability to invoke (e.g., "analyze_code", "run_quest")
            parameters: Parameters for the capability

        Returns:
            Response from ecosystem
        """
        # Record interaction
        interaction = ZenAgentInteraction(
            timestamp=datetime.now().isoformat(),
            source_agent=f"zen_{agent_name}",
            target_agent="nusyq_ecosystem",
            interaction_type="query",
            payload={"capability": capability, "parameters": parameters},
        )
        self.interaction_history.append(interaction)

        # This would route to the appropriate ecosystem capability
        # For now, return acknowledgment
        response = {
            "success": True,
            "status": "acknowledged",
            "capability": capability,
            "message": f"Zen agent {agent_name} invoked {capability}",
        }

        interaction.response = response
        return response

    # =============================================================================
    # RECURSIVE LEARNING (CLOSES THE LOOP!)
    # =============================================================================

    def learn_from_error(
        self,
        error_type: str,
        error_message: str,
        command: str | None = None,
        shell: str = "unknown",
        auto_save: bool = True,
    ) -> dict[str, Any]:
        """Capture an error and learn from it using Zen's recursive learning system.

        This method enables the system to learn from every error encountered!

        Args:
            error_type: Type of error (e.g., "ImportError", "AttributeError")
            error_message: Full error message
            command: Command that triggered the error
            shell: Shell/environment where error occurred
            auto_save: If True, save learned rules to zen.json

        Returns:
            Dict with learning results and wisdom
        """
        if not self.initialized or not self.error_observer or not self.codex_builder:
            return {
                "success": False,
                "status": "error",
                "message": "Learning components not initialized",
            }

        logger.info(f"🧠 Learning from {error_type}: {error_message[:50]}...")

        # Capture error event
        event = self.error_observer.observe_error(
            error_text=f"{error_type}: {error_message}",
            command=command or "",
            shell=shell,
        )

        if not event:
            return {
                "success": False,
                "status": "error",
                "message": "Failed to capture error event",
            }

        # Learn from this single event (will cluster with similar events if > 3 occurrences)
        learning_result = self.codex_builder.learn_from_events(
            events=[event], auto_save=auto_save, min_confidence=0.75
        )

        # Also get existing wisdom for this error
        wisdom = self.get_wisdom_for_error(error_type, error_message)

        # Record interaction
        interaction = ZenAgentInteraction(
            timestamp=datetime.now().isoformat(),
            source_agent="claude",
            target_agent="zen_learning",
            interaction_type="wisdom_share",
            payload={"error_type": error_type, "auto_save": auto_save},
            response={
                "learned": learning_result,
                "wisdom": wisdom,
            },
        )
        self.interaction_history.append(interaction)

        return {
            "success": True,
            "status": "learned",
            "event_id": event.id,
            "learning_result": learning_result,
            "existing_wisdom": wisdom,
            "message": (
                f"Learned from error. "
                f"{learning_result['rules_saved']} new rules saved, "
                f"{len(wisdom.get('matched_rules', []))} existing rules matched."
            ),
        }

    def learn_from_success(
        self, error_type: str, fix_applied: str, outcome: str = "success"
    ) -> dict[str, Any]:
        """Record successful error resolution to improve rule confidence.

        Args:
            error_type: Type of error that was fixed
            fix_applied: Description of fix that worked
            outcome: Result (success/failure)

        Returns:
            Dict with feedback results
        """
        if not self.initialized:
            return {"success": False, "status": "error", "message": "Bridge not initialized"}

        # This would update success rates in zen.json
        # For now, just record the interaction
        interaction = ZenAgentInteraction(
            timestamp=datetime.now().isoformat(),
            source_agent="claude",
            target_agent="zen_learning",
            interaction_type="wisdom_share",
            payload={
                "type": "success_feedback",
                "error_type": error_type,
                "fix": fix_applied,
                "outcome": outcome,
            },
        )
        self.interaction_history.append(interaction)

        logger.info(f"✅ Recorded success: {error_type} fixed with {fix_applied}")

        return {
            "success": True,
            "status": "recorded",
            "message": f"Success feedback recorded for {error_type}",
        }

    # =============================================================================
    # BIDIRECTIONAL ORCHESTRATION
    # =============================================================================

    def orchestrate_multi_agent_task(
        self, task_description: str, preferred_agents: list[str] | None = None
    ) -> dict[str, Any]:
        """Orchestrate a task across both Zen and ecosystem agents.

        Args:
            task_description: Description of the task
            preferred_agents: List of preferred agents (optional)

        Returns:
            Orchestration plan and execution results
        """
        if not self.initialized:
            return {"success": False, "status": "error", "message": "Bridge not initialized"}

        # Record orchestration request
        interaction = ZenAgentInteraction(
            timestamp=datetime.now().isoformat(),
            source_agent="claude",
            target_agent="multi_agent_orchestration",
            interaction_type="command",
            payload={
                "task": task_description,
                "preferred_agents": preferred_agents or [],
            },
        )
        self.interaction_history.append(interaction)

        # Orchestration logic would go here
        # This is a placeholder showing the capability
        orchestration_plan = {
            "success": True,
            "task": task_description,
            "agents_involved": preferred_agents or ["claude", "zen_codex"],
            "status": "planned",
            "message": "Multi-agent orchestration capability active",
        }

        interaction.response = orchestration_plan
        return orchestration_plan

    # =============================================================================
    # UTILITY METHODS
    # =============================================================================

    def _rule_to_dict(self, rule) -> dict[str, Any]:
        """Convert ZenRule to dictionary."""
        return {
            "id": rule.id,
            "version": rule.version,
            "lesson": rule.lesson,
            "suggestions": rule.suggestions,
            "triggers": rule.triggers,
            "tags": rule.tags,
            "actions": rule.actions,
            "lore": rule.lore,
        }

    def get_stats(self) -> dict[str, Any]:
        """Get bridge statistics."""
        if not self.initialized:
            return {"initialized": False}

        stats = {
            "initialized": True,
            "codex_rules": len(self.codex_loader.rules) if self.codex_loader else 0,
            "codex_tags": (len(self.codex_loader.rules_by_tag) if self.codex_loader else 0),
            "zen_agents": (len(self.zen_orchestrator.agents) if self.zen_orchestrator else 0),
            "interactions_count": len(self.interaction_history),
            "interactions_by_type": self._count_interactions_by_type(),
        }

        if self.codex_loader:
            stats.update(self.codex_loader.stats())

        return stats

    def _count_interactions_by_type(self) -> dict[str, int]:
        """Count interactions by type."""
        counts: dict[str, int] = {}
        for interaction in self.interaction_history:
            counts[interaction.interaction_type] = counts.get(interaction.interaction_type, 0) + 1
        return counts

    def get_interaction_history(
        self, limit: int = 10, agent_filter: str | None = None
    ) -> list[dict[str, Any]]:
        """Get recent interaction history.

        Args:
            limit: Maximum number of interactions to return
            agent_filter: Filter by source agent (optional)

        Returns:
            List of recent interactions
        """
        interactions = self.interaction_history

        if agent_filter:
            interactions = [i for i in interactions if i.source_agent == agent_filter]

        # Return most recent first
        interactions = list(reversed(interactions[-limit:]))

        return [
            {
                "timestamp": i.timestamp,
                "source_agent": i.source_agent,
                "target_agent": i.target_agent,
                "interaction_type": i.interaction_type,
                "payload": i.payload,
                "response": i.response,
            }
            for i in interactions
        ]

    def demonstrate_capabilities(self) -> dict[str, Any]:
        """Demonstrate bidirectional communication capabilities.

        This shows:
        1. Claude querying Zen Codex
        2. Zen agents invoking ecosystem
        3. Multi-agent orchestration
        """
        if not self.initialized:
            return {"error": "Bridge not initialized"}

        demo_results = {}

        # 1. Claude → Zen Codex
        import_rules = self.query_rules_by_tag("import")
        demo_results["claude_queries_zen"] = {
            "query": "Rules with 'import' tag",
            "rules_found": len(import_rules),
            "example_rule": import_rules[0]["id"] if import_rules else None,
        }

        # 2. Zen Agent → Ecosystem
        zen_query = self.zen_agent_query_ecosystem(
            agent_name="ollama",
            capability="analyze_code",
            parameters={"file_path": "src/main.py"},
        )
        demo_results["zen_queries_ecosystem"] = zen_query

        # 3. Multi-agent orchestration
        orchestration = self.orchestrate_multi_agent_task(
            task_description="Fix import errors and run tests",
            preferred_agents=["claude", "ollama", "zen_codex"],
        )
        demo_results["multi_agent_orchestration"] = orchestration

        # 4. Interaction stats
        demo_results["interaction_stats"] = self.get_stats()

        return demo_results


# Convenience function for ecosystem activator
def create_zen_bridge() -> ZenCodexBridge:
    """Create and initialize Zen Codex Bridge."""
    bridge = ZenCodexBridge()
    bridge.initialize()
    return bridge


if __name__ == "__main__":
    # Demo the bridge
    logger.info("🌉 ZEN CODEX BRIDGE DEMONSTRATION\n")

    bridge = create_zen_bridge()

    if bridge.initialized:
        logger.info("✅ Bridge initialized successfully\n")

        # Show capabilities
        demo = bridge.demonstrate_capabilities()

        logger.info("📊 Demonstration Results:")
        logger.info("\n1. Claude → Zen Codex:")
        logger.info(f"   {demo['claude_queries_zen']}")

        logger.info("\n2. Zen Agent → Ecosystem:")
        logger.info(f"   {demo['zen_queries_ecosystem']}")

        logger.info("\n3. Multi-Agent Orchestration:")
        logger.info(f"   {demo['multi_agent_orchestration']}")

        logger.info("\n4. Bridge Statistics:")
        stats = demo["interaction_stats"]
        logger.info(f"   Codex Rules: {stats['codex_rules']}")
        logger.info(f"   Zen Agents: {stats['zen_agents']}")
        logger.info(f"   Total Interactions: {stats['interactions_count']}")
        logger.info(f"   By Type: {stats['interactions_by_type']}")
    else:
        logger.error("❌ Bridge initialization failed")
