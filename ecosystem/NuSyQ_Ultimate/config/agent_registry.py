"""
ΞNuSyQ Agent Registry - YAML Loader and Agent Manager

Loads agent_registry.yaml and provides programmatic access to agent metadata.

Version: 1.0.0
Date: 2025-10-07
Author: AI Code Agent (fixing missing implementation)
"""

import yaml
import math
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass


@dataclass
class AgentInfo:
    """Information about a single agent"""

    name: str
    type: str
    provider: str
    model: str
    capabilities: List[str]
    cost_per_1k_tokens: Dict[str, float]
    context_window: int
    availability: str
    reliability: str
    strengths: List[str]
    weaknesses: List[str]
    use_cases: List[str]

    def __post_init__(self):
        """Handle different cost structures"""
        # Normalize cost structure
        if isinstance(self.cost_per_1k_tokens, (int, float)):
            # Single value means same for input/output (e.g., 0.0 for Ollama)
            cost_value = float(self.cost_per_1k_tokens)
            self.cost_per_1k_tokens = {"input": cost_value, "output": cost_value}
        elif isinstance(self.cost_per_1k_tokens, dict):
            # Already in correct format
            pass
        else:
            # Default to free
            self.cost_per_1k_tokens = {"input": 0.0, "output": 0.0}


class AgentRegistry:
    """
    Central registry of all ΞNuSyQ agents loaded from agent_registry.yaml.

    Usage:
        registry = AgentRegistry()
        agent = registry.get_agent("ollama_qwen_14b")
        print(agent.capabilities)

        # Find agents by capability
        coders = registry.find_by_capability("code_generation")

        # Get all free agents
        free_agents = registry.get_free_agents()
    """

    def __init__(self, registry_path: Optional[Path] = None):
        """
        Load agent registry from YAML.

        Args:
            registry_path: Path to agent_registry.yaml
                          (default: config/agent_registry.yaml)
        """
        if registry_path is None:
            registry_path = Path(__file__).parent / "agent_registry.yaml"

        self.registry_path = Path(registry_path)
        self.agents: Dict[str, AgentInfo] = {}
        self.routing_preferences: Dict[str, str] = {}
        self.coordination_patterns: Dict[str, Dict[str, Any]] = {}

        self._load_registry()

    def _load_registry(self):
        """Load and parse agent_registry.yaml"""
        if not self.registry_path.exists():
            raise FileNotFoundError(f"Agent registry not found: {self.registry_path}")

        with open(self.registry_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        # Load agents
        agents_data = data.get("agents", {})
        for agent_name, agent_config in agents_data.items():
            self.agents[agent_name] = AgentInfo(
                name=agent_name,
                type=agent_config.get("type", "unknown"),
                provider=agent_config.get("provider", "unknown"),
                model=agent_config.get("model", "unknown"),
                capabilities=agent_config.get("capabilities", []),
                cost_per_1k_tokens=agent_config.get("cost_per_1k_tokens", 0.0),
                context_window=agent_config.get("context_window", 0),
                availability=agent_config.get("availability", "unknown"),
                reliability=agent_config.get("reliability", "unknown"),
                strengths=agent_config.get("strengths", []),
                weaknesses=agent_config.get("weaknesses", []),
                use_cases=agent_config.get("use_cases", []),
            )

        # Load routing preferences
        self.routing_preferences = data.get("routing_preferences", {})

        # Load coordination patterns
        self.coordination_patterns = data.get("coordination_patterns", {})

    def get_agent(self, agent_name: str) -> Optional[AgentInfo]:
        """Get agent by name"""
        return self.agents.get(agent_name)

    def get_all_agents(self) -> List[AgentInfo]:
        """Get list of all agents"""
        return list(self.agents.values())

    def find_by_capability(self, capability: str) -> List[AgentInfo]:
        """Find all agents with a specific capability"""
        return [
            agent for agent in self.agents.values() if capability in agent.capabilities
        ]

    def find_by_type(self, agent_type: str) -> List[AgentInfo]:
        """Find all agents of a specific type"""
        return [agent for agent in self.agents.values() if agent.type == agent_type]

    def get_free_agents(self) -> List[AgentInfo]:
        """Get all agents with zero cost"""
        return [
            agent
            for agent in self.agents.values()
            if (
                math.isclose(agent.cost_per_1k_tokens["input"], 0.0)
                and math.isclose(agent.cost_per_1k_tokens["output"], 0.0)
            )
        ]

    def get_paid_agents(self) -> List[AgentInfo]:
        """Get all agents with non-zero cost"""
        return [
            agent
            for agent in self.agents.values()
            if (
                agent.cost_per_1k_tokens["input"] > 0.0
                or agent.cost_per_1k_tokens["output"] > 0.0
            )
        ]

    def get_ollama_agents(self) -> List[AgentInfo]:
        """Get all Ollama agents"""
        return self.find_by_type("ollama")

    def get_chatdev_agents(self) -> List[AgentInfo]:
        """Get all ChatDev agents"""
        return self.find_by_type("chatdev")

    def get_routing_preference(self, task_type: str) -> Optional[str]:
        """Get routing preference for a task type"""
        return self.routing_preferences.get(task_type)

    def get_coordination_pattern(self, pattern_name: str) -> Optional[Dict[str, Any]]:
        """Get coordination pattern by name"""
        return self.coordination_patterns.get(pattern_name)

    def agent_exists(self, agent_name: str) -> bool:
        """Check if agent exists in registry"""
        return agent_name in self.agents

    def __len__(self) -> int:
        """Number of agents in registry"""
        return len(self.agents)

    def __repr__(self) -> str:
        return f"AgentRegistry({len(self.agents)} agents)"


# Convenience function for quick access
def load_agent_registry(registry_path: Optional[Path] = None) -> AgentRegistry:
    """Load agent registry (convenience function)"""
    return AgentRegistry(registry_path)


if __name__ == "__main__":
    # Test the registry loader
    print("=" * 70)
    print(" ΞNuSyQ Agent Registry Loader Test")
    print("=" * 70)

    try:
        registry = AgentRegistry()
        print(f"\n✓ Registry loaded: {len(registry)} agents")

        print("\n📊 Agent Breakdown:")
        print(f"  Free agents: {len(registry.get_free_agents())}")
        print(f"  Paid agents: {len(registry.get_paid_agents())}")
        print(f"  Ollama agents: {len(registry.get_ollama_agents())}")
        print(f"  ChatDev agents: {len(registry.get_chatdev_agents())}")

        print("\n🤖 All Agents:")
        for agent in registry.get_all_agents():
            cost = agent.cost_per_1k_tokens
            is_free = math.isclose(cost["input"], 0.0) and math.isclose(
                cost["output"], 0.0
            )
            if is_free:
                cost_str = "FREE"
            else:
                cost_str = f"IN: ${cost['input']:.3f} / OUT: ${cost['output']:.3f}"
            print(f"  - {agent.name} ({agent.type}): {cost_str}")

        print("\n🔍 Agents with 'code_generation' capability:")
        coders = registry.find_by_capability("code_generation")
        for agent in coders:
            print(f"  - {agent.name}")

        print("\n✓ Agent registry working correctly!")

    except (FileNotFoundError, yaml.YAMLError) as e:
        print(f"\n❌ Error loading registry: {e}")
        import traceback

        traceback.print_exc()
