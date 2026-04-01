"""Skill Tree System — Rosetta Stone progression tied to hacking mechanics.

Defines progression tiers, unlockable skills, and XP requirements inspired by
BitBurner and mapped to existing Rosetta Stone progression stages.

OmniTag: {
    "purpose": "progression_system",
    "tags": ["Skill-Tree", "Progression", "RPG", "Games"],
    "category": "gameplay",
    "evolution_stage": "prototype"
}
"""

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class RosettaTier(Enum):
    """Rosetta Stone progression tiers mapped to game mechanics."""

    TIER_1_SURVIVAL = 1  # Basic scanning and repair
    TIER_2_AUTOMATION = 2  # Script writing and background jobs
    TIER_3_AI_INTEGRATION = 3  # AI co-pilots and advanced analysis
    TIER_4_DEFENSE = 4  # Security hardening and trace evasion
    TIER_5_SYNTHESIS = 5  # Consciousness bridge and multi-agent control


@dataclass
class UnlockableSkill:
    """A skill that becomes available at a certain tier."""

    id: str
    name: str
    description: str
    tier_required: RosettaTier
    xp_cost: int
    subsequent_xp_per_level: int = 100  # XP per level after first unlock
    category: str = "general"  # hacking, scripting, defense, etc.
    related_commands: list[str] = field(default_factory=list)
    prerequisites: list[str] = field(default_factory=list)  # Other skill IDs


@dataclass
class SkillTreeState:
    """Player's current progression through the skill tree."""

    tier: RosettaTier = RosettaTier.TIER_1_SURVIVAL
    total_xp: int = 0
    unlocked_skills: dict[str, int] = field(default_factory=dict)  # skill_id -> level
    available_points: int = 0


class SkillTree:
    """Manages skill progression and unlocking."""

    def __init__(self):
        """Initialize skill tree with all available skills."""
        self.skills = self._initialize_skills()
        self.state = SkillTreeState()
        self.tier_xp_thresholds = {
            RosettaTier.TIER_1_SURVIVAL: 0,
            RosettaTier.TIER_2_AUTOMATION: 500,
            RosettaTier.TIER_3_AI_INTEGRATION: 2000,
            RosettaTier.TIER_4_DEFENSE: 5000,
            RosettaTier.TIER_5_SYNTHESIS: 10000,
        }
        logger.info("SkillTree initialized")

    def _initialize_skills(self) -> dict[str, UnlockableSkill]:
        """Initialize all available skills."""
        skills = {
            # Tier 1: Survival
            "basic_scan": UnlockableSkill(
                id="basic_scan",
                name="Basic Scan",
                description="Scan components to discover open ports and services.",
                tier_required=RosettaTier.TIER_1_SURVIVAL,
                xp_cost=0,
                category="hacking",
                related_commands=["scan", "nmap"],
            ),
            "ssh_crack": UnlockableSkill(
                id="ssh_crack",
                name="SSH Crack",
                description="Execute SSH brute-force attacks.",
                tier_required=RosettaTier.TIER_1_SURVIVAL,
                xp_cost=100,
                category="hacking",
                related_commands=["exploit", "ssh_crack"],
            ),
            "component_heal": UnlockableSkill(
                id="component_heal",
                name="Component Heal",
                description="Repair failing components and restore health.",
                tier_required=RosettaTier.TIER_1_SURVIVAL,
                xp_cost=50,
                category="maintenance",
                related_commands=["heal", "patch"],
            ),
            # Tier 2: Automation
            "script_writing": UnlockableSkill(
                id="script_writing",
                name="Script Writing",
                description="Write and deploy autonomous scripts for background work.",
                tier_required=RosettaTier.TIER_2_AUTOMATION,
                xp_cost=200,
                category="scripting",
                related_commands=["run_script", "background_job"],
                prerequisites=["basic_scan"],
            ),
            "resource_optimization": UnlockableSkill(
                id="resource_optimization",
                name="Resource Optimization",
                description="Optimize memory and CPU usage of running programs.",
                tier_required=RosettaTier.TIER_2_AUTOMATION,
                xp_cost=150,
                category="optimization",
                related_commands=["optimize", "memory_management"],
            ),
            "multi_threading": UnlockableSkill(
                id="multi_threading",
                name="Multi-Threading",
                description="Run multiple scripts concurrently with improved coordination.",
                tier_required=RosettaTier.TIER_2_AUTOMATION,
                xp_cost=250,
                category="scripting",
                related_commands=["parallel_execution"],
                prerequisites=["script_writing"],
            ),
            # Tier 3: AI Integration
            "ai_copilot": UnlockableSkill(
                id="ai_copilot",
                name="AI Co-Pilot",
                description="Request AI-generated code and exploit suggestions.",
                tier_required=RosettaTier.TIER_3_AI_INTEGRATION,
                xp_cost=300,
                category="ai",
                related_commands=["generate_code", "suggest_exploit"],
                prerequisites=["script_writing"],
            ),
            "consciousness_bridge": UnlockableSkill(
                id="consciousness_bridge",
                name="Consciousness Bridge",
                description="Access consciousness integration for semantic awareness.",
                tier_required=RosettaTier.TIER_3_AI_INTEGRATION,
                xp_cost=400,
                category="ai",
                related_commands=["consciousness_query", "semantic_analyze"],
            ),
            "smart_search_plus": UnlockableSkill(
                id="smart_search_plus",
                name="Smart Search+",
                description="Enhanced fl1ght.exe search with AI relevance ranking.",
                tier_required=RosettaTier.TIER_3_AI_INTEGRATION,
                xp_cost=250,
                category="ai",
                related_commands=["fl1ght_plus"],
                prerequisites=["basic_scan"],
            ),
            # Tier 4: Defense
            "trace_evasion": UnlockableSkill(
                id="trace_evasion",
                name="Trace Evasion",
                description="Evade or disrupt active traces/alarms.",
                tier_required=RosettaTier.TIER_4_DEFENSE,
                xp_cost=350,
                category="defense",
                related_commands=["evade", "suppress_trace"],
                prerequisites=["basic_scan"],
            ),
            "firewall_bypass": UnlockableSkill(
                id="firewall_bypass",
                name="Firewall Bypass",
                description="Bypass security firewalls and access restrictions.",
                tier_required=RosettaTier.TIER_4_DEFENSE,
                xp_cost=400,
                category="defense",
                related_commands=["bypass_firewall"],
            ),
            "security_hardening": UnlockableSkill(
                id="security_hardening",
                name="Security Hardening",
                description="Patch vulnerabilities and strengthen component security.",
                tier_required=RosettaTier.TIER_4_DEFENSE,
                xp_cost=300,
                category="defense",
                related_commands=["hardening", "patch_all"],
                prerequisites=["component_heal"],
            ),
            # Tier 5: Synthesis
            "multi_faction_control": UnlockableSkill(
                id="multi_faction_control",
                name="Multi-Faction Control",
                description="Coordinate activities across multiple AI factions.",
                tier_required=RosettaTier.TIER_5_SYNTHESIS,
                xp_cost=500,
                category="orchestration",
                related_commands=["faction_control", "orchestrate"],
                prerequisites=["consciousness_bridge"],
            ),
            "emergent_strategy": UnlockableSkill(
                id="emergent_strategy",
                name="Emergent Strategy",
                description="Unlock emergent behaviors and adaptive strategies.",
                tier_required=RosettaTier.TIER_5_SYNTHESIS,
                xp_cost=600,
                category="orchestration",
                related_commands=["emerge_strategy"],
                prerequisites=["ai_copilot", "consciousness_bridge"],
            ),
        }
        return skills

    def add_xp(self, amount: int) -> None:
        """Add XP to player's total and check for tier advancement."""
        self.state.total_xp += amount
        logger.info(f"Added {amount} XP, total: {self.state.total_xp}")

        # Check for tier advancement
        for tier, threshold in sorted(
            self.tier_xp_thresholds.items(), key=lambda x: x[1], reverse=True
        ):
            if self.state.total_xp >= threshold and tier.value > self.state.tier.value:
                self.state.tier = tier
                logger.info(f"Advanced to tier: {tier.name}")

    def unlock_skill(self, skill_id: str) -> bool:
        """Attempt to unlock a skill. Returns True if successful."""
        if skill_id not in self.skills:
            logger.warning(f"Skill not found: {skill_id}")
            return False

        skill = self.skills[skill_id]

        # Check prerequisites
        for prereq in skill.prerequisites:
            if prereq not in self.state.unlocked_skills:
                logger.warning(f"Prerequisite skill not unlocked: {prereq}")
                return False

        # Check tier requirement
        if skill.tier_required.value > self.state.tier.value:
            logger.warning(f"Insufficient tier to unlock {skill_id}")
            return False

        # Check XP requirement
        if skill_id not in self.state.unlocked_skills and self.state.total_xp < skill.xp_cost:
            logger.warning(
                f"Insufficient XP to unlock {skill_id}: {self.state.total_xp} < {skill.xp_cost}"
            )
            return False

        # Unlock or level up
        current_level = self.state.unlocked_skills.get(skill_id, 0)
        self.state.unlocked_skills[skill_id] = current_level + 1
        logger.info(f"Unlocked {skill_id} (level {current_level + 1})")
        return True

    def is_skill_available(self, skill_id: str) -> bool:
        """Check if a skill is currently available to use."""
        return skill_id in self.state.unlocked_skills

    def get_available_skills(self) -> dict[str, UnlockableSkill]:
        """Get all skills available for current tier."""
        return {
            skill_id: skill
            for skill_id, skill in self.skills.items()
            if skill.tier_required.value <= self.state.tier.value
        }

    def get_next_milestone(self) -> dict[str, Any]:
        """Get information about next tier/skill unlock."""
        # Next tier
        current_tier_xp = self.tier_xp_thresholds[self.state.tier]
        next_tiers = [
            (tier, xp) for tier, xp in self.tier_xp_thresholds.items() if xp > current_tier_xp
        ]

        if next_tiers:
            next_tier, xp_needed = min(next_tiers, key=lambda x: x[1])
            xp_to_next = xp_needed - self.state.total_xp
        else:
            next_tier = None
            xp_to_next = None

        # Next available skill
        available = self.get_available_skills()
        next_skills = [
            (skill_id, skill)
            for skill_id, skill in available.items()
            if skill_id not in self.state.unlocked_skills
        ]

        return {
            "current_tier": self.state.tier.name,
            "next_tier": next_tier.name if next_tier else None,
            "xp_to_next_tier": xp_to_next,
            "next_available_skills": [(s[0], s[1].name) for s in next_skills[:3]],
            "unlocked_count": len(self.state.unlocked_skills),
        }

    def get_state(self) -> dict[str, Any]:
        """Get current skill tree state."""
        return {
            "tier": self.state.tier.name,
            "total_xp": self.state.total_xp,
            "unlocked_skills": {
                skill_id: self.skills[skill_id].name for skill_id in self.state.unlocked_skills
            },
            "next_milestone": self.get_next_milestone(),
        }


# Global instance
_skill_tree: SkillTree | None = None


def get_skill_tree() -> SkillTree:
    """Get or create global SkillTree instance."""
    global _skill_tree
    if _skill_tree is None:
        _skill_tree = SkillTree()
    return _skill_tree
