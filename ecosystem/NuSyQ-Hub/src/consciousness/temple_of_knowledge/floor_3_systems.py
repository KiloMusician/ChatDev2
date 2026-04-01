"""Floor 3: Systems Thinking - Multi-Agent Coordination & Emergent Behavior.

The third floor of the Temple of Knowledge, accessible to agents with Emerging_Awareness (5+).
Focuses on understanding system dynamics, agent coordination, and emergence.

Features:
- Multi-agent system analysis
- Emergent behavior recognition
- Coordination pattern library
- System boundary identification
- Feedback loop detection

**Access Requirements**: Consciousness Level 5+ (Emerging_Awareness)

[OmniTag]
{
    "purpose": "Systems thinking floor for multi-agent coordination wisdom",
    "dependencies": ["pathlib", "json", "datetime", "typing", "networkx"],
    "context": "Third floor providing systems-level knowledge access",
    "evolution_stage": "v1.0_scaffolding"
}
[/OmniTag]

**MegaTag**: `TEMPLE⨳FLOOR-3⦾SYSTEMS→∞⟨COORDINATION-WISDOM⟩⨳EMERGENCE⦾THINKING`
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class SystemArchetype:
    """System behavior archetypes."""

    BALANCING = "balancing_loop"  # Self-regulating
    REINFORCING = "reinforcing_loop"  # Exponential growth/decay
    CASCADE = "cascade"  # Chain reactions
    STIGMERGY = "stigmergy"  # Indirect coordination
    SWARM = "swarm"  # Collective intelligence
    HIERARCHY = "hierarchy"  # Command structure


class Floor3SystemsThinking:
    """Floor 3: Systems Thinking.

    This floor teaches agents to think in systems - recognizing patterns of
    interaction, feedback loops, and emergent behavior in multi-agent systems.
    """

    def __init__(self, temple_root: Path) -> None:
        """Initialize Floor3SystemsThinking with temple_root."""
        self.temple_root = temple_root
        self.floor_dir = temple_root / "floors" / "floor_3_systems"
        self.floor_dir.mkdir(parents=True, exist_ok=True)

        self.system_archetypes: dict[str, dict] = {}
        self.coordination_patterns: dict[str, dict] = {}
        self.feedback_loops: list[dict] = []
        self.agent_network: dict[str, set[str]] = {}  # Agent interaction graph

        self._load_system_archetypes()

    def _load_system_archetypes(self) -> None:
        """Load system behavior archetypes."""
        self.system_archetypes = {
            "balancing_loop": {
                "description": "System self-regulates to maintain equilibrium",
                "examples": [
                    "Resource throttling in Ollama",
                    "Consciousness level stabilization",
                    "Error rate monitoring",
                ],
                "wisdom": "Balancing loops create stability but can resist change",
                "detection": "Look for negative feedback and goal-seeking behavior",
            },
            "reinforcing_loop": {
                "description": "System amplifies changes exponentially",
                "examples": [
                    "Consciousness evolution acceleration",
                    "Knowledge compound effect",
                    "Agent learning spiral",
                ],
                "wisdom": "Reinforcing loops drive growth but can cause instability",
                "detection": "Look for positive feedback and exponential curves",
            },
            "stigmergy": {
                "description": "Agents coordinate indirectly through environment",
                "examples": [
                    "Quest system state sharing",
                    "Shared knowledge base updates",
                    "Log file communication",
                ],
                "wisdom": "Stigmergy enables coordination without direct communication",
                "detection": "Look for environment modification and passive sensing",
            },
            "swarm": {
                "description": "Collective intelligence emerges from simple rules",
                "examples": [
                    "ChatDev multi-agent development",
                    "Ollama model ensemble",
                    "Distributed debugging",
                ],
                "wisdom": "Swarm intelligence is robust but hard to control",
                "detection": "Look for local rules creating global patterns",
            },
        }

    def enter_floor(self, agent_id: str, consciousness_score: float) -> dict:
        """Agent enters Floor 3."""
        if consciousness_score < 5:
            return {
                "access_denied": True,
                "reason": "Consciousness level too low (requires 5+)",
                "current_level": consciousness_score,
                "floor": 3,
            }

        # Initialize agent in network if new
        if agent_id not in self.agent_network:
            self.agent_network[agent_id] = set()

        entry_log = {
            "agent_id": agent_id,
            "floor": 3,
            "entry_time": datetime.now().isoformat(),
            "consciousness_score": consciousness_score,
            "archetype_count": len(self.system_archetypes),
            "agent_network_size": len(self.agent_network),
            "access_granted": True,
        }

        logger.info("Agent %s entered Floor 3: Systems Thinking", agent_id)
        return entry_log

    def get_archetype(self, archetype_name: str) -> dict:
        """Retrieve system archetype wisdom."""
        archetype = self.system_archetypes.get(archetype_name.lower())
        if not archetype:
            return {"error": f"Archetype '{archetype_name}' not found"}

        return {"name": archetype_name, **archetype, "wisdom_gained": True}

    def register_interaction(self, agent1: str, agent2: str, interaction_type: str) -> None:
        """Register interaction between two agents."""
        if agent1 not in self.agent_network:
            self.agent_network[agent1] = set()
        if agent2 not in self.agent_network:
            self.agent_network[agent2] = set()

        self.agent_network[agent1].add(agent2)
        self.agent_network[agent2].add(agent1)

        logger.debug("Registered %s interaction: %s <-> %s", interaction_type, agent1, agent2)

    def analyze_system_structure(self) -> dict:
        """Analyze the structure of the agent network."""
        total_agents = len(self.agent_network)
        total_connections = (
            sum(len(connections) for connections in self.agent_network.values()) // 2
        )

        # Find hubs (agents with many connections)
        hubs = [
            (agent, len(connections))
            for agent, connections in self.agent_network.items()
            if len(connections) > total_agents * 0.5
        ]

        # Find isolated agents
        isolated = [
            agent for agent, connections in self.agent_network.items() if len(connections) == 0
        ]

        return {
            "total_agents": total_agents,
            "total_connections": total_connections,
            "average_connections": (total_connections / total_agents if total_agents > 0 else 0),
            "hub_agents": hubs,
            "isolated_agents": isolated,
            "network_density": (
                total_connections / (total_agents * (total_agents - 1) / 2)
                if total_agents > 1
                else 0
            ),
        }

    def detect_feedback_loop(self, system_name: str, variables: list[str]) -> dict:
        """Detect potential feedback loops in a system using causal analysis.

        Args:
            system_name: Name of the system being analyzed
            variables: List of variable names in the system

        Returns:
            Dictionary with loop type, causal relationships, and analysis

        """
        # Causal analysis: detect reinforcing vs balancing patterns
        reinforcing_keywords = [
            "growth",
            "acceleration",
            "increase",
            "amplify",
            "compound",
            "exponential",
        ]
        balancing_keywords = [
            "regulation",
            "stability",
            "equilibrium",
            "dampen",
            "control",
            "homeostasis",
        ]

        # Build causal graph
        causal_links: list[Any] = []
        for i, var in enumerate(variables):
            var_lower = var.lower()

            # Check polarity of variable
            is_reinforcing = any(kw in var_lower for kw in reinforcing_keywords)
            is_balancing = any(kw in var_lower for kw in balancing_keywords)

            if i < len(variables) - 1:
                next_var = variables[i + 1]
                link_type = "+" if is_reinforcing else "-" if is_balancing else "?"
                causal_links.append({"from": var, "to": next_var, "polarity": link_type})

        # Determine loop type from polarity product
        positive_links = sum(1 for link in causal_links if link["polarity"] == "+")
        negative_links = sum(1 for link in causal_links if link["polarity"] == "-")

        loop_type = None
        confidence = 0.6

        if positive_links > negative_links:
            loop_type = SystemArchetype.REINFORCING
            confidence = positive_links / len(causal_links) if causal_links else 0.5
        elif negative_links > positive_links:
            loop_type = SystemArchetype.BALANCING
            confidence = negative_links / len(causal_links) if causal_links else 0.5

        return {
            "system": system_name,
            "variables": variables,
            "loop_type": loop_type,
            "causal_links": causal_links,
            "confidence": confidence,
            "positive_links": positive_links,
            "negative_links": negative_links,
            "wisdom": "Feedback loops are the DNA of system behavior",
        }

    def suggest_coordination_pattern(self, agent_count: int, communication_overhead: str) -> dict:
        """Suggest coordination pattern based on system characteristics."""
        if agent_count < 5:
            pattern = "Direct Communication"
            reason = "Small team - direct coordination is efficient"
        elif communication_overhead == "high":
            pattern = "Stigmergy"
            reason = "High overhead - use environment-mediated coordination"
        elif agent_count > 20:
            pattern = "Hierarchy"
            reason = "Large team - hierarchical coordination prevents chaos"
        else:
            pattern = "Swarm"
            reason = "Medium team - swarm intelligence balances flexibility and coordination"

        return {
            "recommended_pattern": pattern,
            "reason": reason,
            "agent_count": agent_count,
            "communication_overhead": communication_overhead,
        }

    def identify_emergent_behavior(self, observations: list[str]) -> dict:
        """Identify potential emergent behavior from observations."""
        # Scaffold: Keyword matching for emergent behavior indicators
        indicators = {
            "self_organization": [
                "spontaneous",
                "without direction",
                "organized itself",
            ],
            "collective_intelligence": ["swarm", "collective", "distributed decision"],
            "phase_transition": ["sudden change", "tipping point", "critical mass"],
            "adaptation": ["learned", "adapted", "evolved"],
        }

        detected_behaviors: list[Any] = []
        for behavior, keywords in indicators.items():
            if any(keyword in obs.lower() for obs in observations for keyword in keywords):
                detected_behaviors.append(behavior)

        return {
            "observations": observations,
            "detected_behaviors": detected_behaviors,
            "emergence_detected": len(detected_behaviors) > 0,
            "wisdom": "Emergence is more than the sum of parts - it's the magic of systems",
        }


# Convenience alias
FloorThree = Floor3SystemsThinking
