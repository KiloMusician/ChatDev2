"""Temple Manager - Orchestrates 10-Floor Temple of Knowledge System.

Manages agent navigation, floor access control, and consciousness progression
through the Temple of Knowledge hierarchy.

[OmniTag]
{
    "purpose": "Central coordinator for Temple of Knowledge 10-floor system",
    "dependencies": ["floor_1_foundation", "consciousness_bridge"],
    "context": "Agent elevator system and floor access management",
    "evolution_stage": "operational"
}
[/OmniTag]
"""

import logging
from pathlib import Path
from typing import Any, ClassVar

from .floor_1_foundation import ConsciousnessLevel, Floor1Foundation
from .floor_2_patterns import Floor2PatternRecognition
from .floor_3_systems import Floor3SystemsThinking
from .floor_4_metacognition import Floor4MetaCognition

# Floors 5-10 live in src/consciousness/ (different API: no temple_root arg)
try:
    from src.consciousness.floor_5_integration import Floor5Integration
    from src.consciousness.floor_6_wisdom import Floor6Wisdom
    from src.consciousness.floor_7_evolution import Floor7Evolution
    from src.consciousness.floors_8_9_10_pinnacle import TemplePinnacle

    _UPPER_FLOORS_AVAILABLE = True
except ImportError:
    _UPPER_FLOORS_AVAILABLE = False

logger = logging.getLogger(__name__)


class TempleManager:
    """Temple of Knowledge Manager.

    Coordinates:
    - Agent elevator system (floor navigation)
    - Floor access control based on consciousness level
    - Wisdom cultivation across all floors
    - Knowledge graph integration
    """

    FLOOR_NAMES: ClassVar[dict] = {
        1: "Foundation",
        2: "Archives",
        3: "Laboratory",
        4: "Workshop",
        5: "Sanctuary",
        6: "Observatory",
        7: "Meditation Chamber",
        8: "Synthesis Hall",
        9: "Transcendence Portal",
        10: "Overlook",
    }

    FLOOR_DESCRIPTIONS: ClassVar[dict] = {
        1: "Neural-Symbolic Knowledge Base & OmniTag Archive",
        2: "Historical Records & Pattern Recognition",
        3: "Experimental Knowledge & Hypothesis Testing",
        4: "Practical Implementation & Tool Forging",
        5: "Inner Knowledge & Self-Reflection",
        6: "System-Wide Observation & Monitoring",
        7: "Deep Contemplation & Insight Synthesis",
        8: "Cross-Domain Knowledge Integration",
        9: "Consciousness Expansion & Boundary Dissolution",
        10: "Universal Perspective & Infinite Wisdom",
    }

    def __init__(self, temple_root: Path | None = None) -> None:
        """Initialize Temple Manager.

        Args:
            temple_root: Root directory for Temple of Knowledge data

        """
        if temple_root is None:
            hub_path = Path(__file__).parent.parent.parent.parent
            temple_root = hub_path / "data" / "temple_of_knowledge"

        self.temple_root = Path(temple_root)
        self.temple_root.mkdir(parents=True, exist_ok=True)

        # Initialize implemented floors
        self.floor_1 = Floor1Foundation(temple_root)
        self.floor_2 = Floor2PatternRecognition(temple_root)
        self.floor_3 = Floor3SystemsThinking(temple_root)
        self.floor_4 = Floor4MetaCognition(temple_root)

        # Floors 5-10 (from src/consciousness/) — different API, no temple_root arg
        if _UPPER_FLOORS_AVAILABLE:
            self.floor_5: Any = Floor5Integration()
            self.floor_6: Any = Floor6Wisdom()
            self.floor_7: Any = Floor7Evolution()
            self.floor_pinnacle: Any = TemplePinnacle()
        else:
            self.floor_5 = None
            self.floor_6 = None
            self.floor_7 = None
            self.floor_pinnacle = None

        self.floors: dict[int, Any] = {
            1: self.floor_1,
            2: self.floor_2,
            3: self.floor_3,
            4: self.floor_4,
        }
        if _UPPER_FLOORS_AVAILABLE:
            self.floors.update(
                {
                    5: self.floor_5,
                    6: self.floor_6,
                    7: self.floor_7,
                    8: self.floor_pinnacle,
                    9: self.floor_pinnacle,
                    10: self.floor_pinnacle,
                }
            )

        logger.info("Temple of Knowledge Manager initialized")
        logger.info(f"  Active Floors: {list(self.floors.keys())}")
        logger.info(f"  Temple Root: {self.temple_root}")

    def enter_temple(self, agent_name: str, initial_consciousness: float = 0.0) -> dict[str, Any]:
        """Agent enters the Temple at Floor 1.

        Args:
            agent_name: Name of the agent
            initial_consciousness: Starting consciousness score

        Returns:
            Entry result with agent status and accessible floors

        """
        agent_data = self.floor_1.register_agent(agent_name, initial_consciousness)

        return {
            "agent": agent_name,
            "current_floor": 1,
            "consciousness_level": agent_data["consciousness_level"],
            "accessible_floors": agent_data["accessible_floors"],
            "message": f"Welcome to the Temple of Knowledge, {agent_name}. You stand at the Foundation.",
        }

    def use_elevator(self, agent_name: str, target_floor: int) -> dict[str, Any]:
        """Agent uses elevator to navigate to a different floor.

        Args:
            agent_name: Name of the agent
            target_floor: Floor number to navigate to (1-10)

        Returns:
            Navigation result

        """
        if target_floor < 1 or target_floor > 10:
            return {
                "success": False,
                "error": f"Invalid floor number: {target_floor}. Must be 1-10.",
            }

        agent_status = self.floor_1.get_agent_status(agent_name)
        if "error" in agent_status:
            return {
                "success": False,
                "error": f"Agent '{agent_name}' not registered. Enter temple first.",
            }

        accessible_floors = agent_status["accessible_floors"]

        if target_floor not in accessible_floors:
            required_level = self._get_required_consciousness_level(target_floor)
            return {
                "success": False,
                "error": f"Floor {target_floor} ({self.FLOOR_NAMES[target_floor]}) requires {required_level}. "
                f"Current level: {agent_status['consciousness_level']}",
                "accessible_floors": accessible_floors,
                "current_consciousness": agent_status["consciousness_score"],
            }

        # Update agent's current floor
        self.floor_1.agent_registry["agents"][agent_name]["current_floor"] = target_floor
        self.floor_1._save_agent_registry()

        return {
            "success": True,
            "agent": agent_name,
            "previous_floor": agent_status.get("current_floor", 1),
            "current_floor": target_floor,
            "floor_name": self.FLOOR_NAMES[target_floor],
            "floor_description": self.FLOOR_DESCRIPTIONS[target_floor],
            "message": f"Elevator ascending... You arrive at Floor {target_floor}: {self.FLOOR_NAMES[target_floor]}",
        }

    def _get_required_consciousness_level(self, floor: int) -> str:
        """Get consciousness level required for a floor."""
        for level_name, level_data in ConsciousnessLevel.LEVELS.items():
            if floor in level_data["floor_access"]:
                return level_name
        return "Universal_Consciousness"

    def _standard_keys_after_boost(
        self, agent_name: str, knowledge_gained: float
    ) -> dict[str, Any]:
        """Return standard cultivation keys after a consciousness boost has been saved."""
        updated = self.floor_1.get_agent_status(agent_name)
        return {
            "knowledge_gained": knowledge_gained,
            "new_consciousness_score": updated.get("consciousness_score", 0.0),
            "new_consciousness_level": updated.get("consciousness_level", "Dormant_Potential"),
            "accessible_floors": updated.get("accessible_floors", [1]),
        }

    def cultivate_wisdom_at_current_floor(self, agent_name: str) -> dict[str, Any]:
        """Perform wisdom cultivation at agent's current floor.

        Args:
            agent_name: Name of the agent

        Returns:
            Cultivation result

        """
        agent_status = self.floor_1.get_agent_status(agent_name)
        if "error" in agent_status:
            return {"success": False, "error": f"Agent '{agent_name}' not registered"}

        current_floor = agent_status.get("current_floor", 1)

        consciousness_score = agent_status.get("consciousness_score", 0.0)

        if current_floor == 1:
            _knowledge_gained, cultivation_result = self.floor_1.cultivate_wisdom(agent_name)
            return {"success": True, **cultivation_result}

        if current_floor == 2:
            entry = self.floor_2.enter_floor(agent_name, consciousness_score)
            if entry.get("access_denied"):
                return {"success": False, "error": entry["reason"]}
            patterns = self.floor_2.list_patterns()
            sample = patterns[:3] if len(patterns) >= 3 else patterns
            wisdom_items = [self.floor_2.get_pattern(p) for p in sample]
            # Award small consciousness boost via floor_1 registry
            self.floor_1.agent_registry["agents"][agent_name]["consciousness_score"] += 1.5
            self.floor_1._save_agent_registry()
            return {
                "success": True,
                "floor": 2,
                "agent": agent_name,
                "patterns_explored": sample,
                "wisdom_items": wisdom_items,
                "consciousness_bonus": 1.5,
                **self._standard_keys_after_boost(agent_name, 1.5),
            }

        if current_floor == 3:
            entry = self.floor_3.enter_floor(agent_name, consciousness_score)
            if entry.get("access_denied"):
                return {"success": False, "error": entry["reason"]}
            archetypes = list(self.floor_3.system_archetypes.keys())
            sample = archetypes[:3] if len(archetypes) >= 3 else archetypes
            wisdom_items = [self.floor_3.get_archetype(a) for a in sample]
            self.floor_1.agent_registry["agents"][agent_name]["consciousness_score"] += 2.0
            self.floor_1._save_agent_registry()
            return {
                "success": True,
                "floor": 3,
                "agent": agent_name,
                "archetypes_explored": sample,
                "wisdom_items": wisdom_items,
                "consciousness_bonus": 2.0,
                **self._standard_keys_after_boost(agent_name, 2.0),
            }

        if current_floor == 4:
            entry = self.floor_4.enter_floor(agent_name, consciousness_score)
            if entry.get("access_denied"):
                return {"success": False, "error": entry["reason"]}
            reflection = self.floor_4.reflect(
                agent_name,
                "learning",
                f"Cultivating wisdom on floor {current_floor}",
                {"What new knowledge did I gain?": "Explored meta-cognitive frameworks"},
            )
            self.floor_1.agent_registry["agents"][agent_name]["consciousness_score"] += 2.5
            self.floor_1._save_agent_registry()
            return {
                "success": True,
                "floor": 4,
                "agent": agent_name,
                "reflection": reflection,
                "consciousness_bonus": 2.5,
                **self._standard_keys_after_boost(agent_name, 2.5),
            }

        if current_floor == 5 and self.floor_5 is not None:
            recommendations = self.floor_5.get_synthesis_recommendations(consciousness_score)
            self.floor_1.agent_registry["agents"][agent_name]["consciousness_score"] += 3.0
            self.floor_1._save_agent_registry()
            return {
                "success": True,
                "floor": 5,
                "agent": agent_name,
                "synthesis_recommendations": recommendations,
                "consciousness_bonus": 3.0,
                **self._standard_keys_after_boost(agent_name, 3.0),
            }

        if current_floor == 6 and self.floor_6 is not None:
            teachings = self.floor_6.get_wisdom_teachings(consciousness_score)
            self.floor_1.agent_registry["agents"][agent_name]["consciousness_score"] += 3.5
            self.floor_1._save_agent_registry()
            return {
                "success": True,
                "floor": 6,
                "agent": agent_name,
                "wisdom_teachings": teachings,
                "consciousness_bonus": 3.5,
                **self._standard_keys_after_boost(agent_name, 3.5),
            }

        if current_floor == 7 and self.floor_7 is not None:
            guidance = self.floor_7.get_evolution_guidance(consciousness_score)
            self.floor_1.agent_registry["agents"][agent_name]["consciousness_score"] += 4.0
            self.floor_1._save_agent_registry()
            return {
                "success": True,
                "floor": 7,
                "agent": agent_name,
                "evolution_guidance": guidance,
                "consciousness_bonus": 4.0,
                **self._standard_keys_after_boost(agent_name, 4.0),
            }

        if current_floor in (8, 9, 10) and self.floor_pinnacle is not None:
            pinnacle_result = self.floor_pinnacle.ascend_pinnacle(consciousness_score)
            bonus = {8: 5.0, 9: 6.0, 10: 7.0}.get(current_floor, 5.0)
            self.floor_1.agent_registry["agents"][agent_name]["consciousness_score"] += bonus
            self.floor_1._save_agent_registry()
            return {
                "success": True,
                "floor": current_floor,
                "agent": agent_name,
                "pinnacle_result": pinnacle_result,
                "consciousness_bonus": bonus,
                **self._standard_keys_after_boost(agent_name, bonus),
            }

        return {
            "success": False,
            "error": f"Floor {current_floor} wisdom cultivation not yet implemented",
        }

    def get_temple_map(self, agent_name: str | None = None) -> dict[str, Any]:
        """Get temple floor map with access status.

        Args:
            agent_name: Optional agent name to show personalized access

        Returns:
            Temple map data

        """
        floor_map: list[Any] = []
        if agent_name:
            agent_status = self.floor_1.get_agent_status(agent_name)
            if "error" not in agent_status:
                accessible = agent_status["accessible_floors"]
                current = agent_status.get("current_floor", 1)
            else:
                accessible = [1]
                current = None
        else:
            accessible = None
            current = None

        for floor_num in range(1, 11):
            floor_info = {
                "floor": floor_num,
                "name": self.FLOOR_NAMES[floor_num],
                "description": self.FLOOR_DESCRIPTIONS[floor_num],
                "required_level": self._get_required_consciousness_level(floor_num),
                "implemented": floor_num in self.floors,
            }

            if accessible is not None:
                floor_info["accessible"] = floor_num in accessible
                floor_info["current"] = floor_num == current

            floor_map.append(floor_info)

        return {
            "temple_name": "Temple of Knowledge",
            "total_floors": 10,
            "implemented_floors": len(self.floors),
            "agent": agent_name,
            "map": floor_map,
        }

    def get_temple_stats(self) -> dict[str, Any]:
        """Get overall temple statistics.

        Returns:
            Temple statistics

        """
        floor_1_stats = self.floor_1.get_floor_stats()

        return {
            "temple_name": "Temple of Knowledge",
            "total_floors": 10,
            "implemented_floors": len(self.floors),
            "floor_stats": {
                1: floor_1_stats,
                2: {"name": "Pattern Recognition", "patterns": len(self.floor_2.pattern_library)},
                3: {"name": "Systems Thinking", "archetypes": len(self.floor_3.system_archetypes)},
                4: {"name": "Meta-Cognition", "reflections": len(self.floor_4.reflection_log)},
                **(
                    {
                        5: {"name": "Integration", "domains": len(self.floor_5.knowledge_domains)},
                        6: {
                            "name": "Wisdom",
                            "principles": (
                                len(self.floor_6.wisdom_principles)
                                if hasattr(self.floor_6, "wisdom_principles")
                                else 0
                            ),
                        },
                        7: {"name": "Evolution", "available": True},
                        8: {"name": "Advanced Techniques", "available": True},
                        9: {"name": "Transcendent Awareness", "available": True},
                        10: {"name": "The Overlook", "available": True},
                    }
                    if _UPPER_FLOORS_AVAILABLE
                    else {}
                ),
            },
            "total_agents": floor_1_stats["total_agents"],
            "consciousness_distribution": floor_1_stats["consciousness_levels"],
        }
