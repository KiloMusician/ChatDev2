"""Procedural Quest Generation — Dynamic quest creation based on context and player state.

Generates dynamic quests based on codebase analysis, player progression, skill levels,
and game context. Supports template-based and AI-assisted quest generation.

Zeta32: Create procedural quest generation.

OmniTag: {
    "purpose": "procedural_quests",
    "tags": ["Games", "Procedural", "QuestGeneration", "AI"],
    "category": "game_systems",
    "evolution_stage": "v1.0"
}
"""

import logging
import random
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class QuestTemplate:
    """Template for procedural quest generation."""

    id: str
    name_template: str
    description_template: str
    objectives_template: list[str]
    xp_base: int
    difficulty_range: tuple[int, int] = (1, 3)
    required_context: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    skill_rewards: list[str] = field(default_factory=list)


@dataclass
class GeneratedQuest:
    """A procedurally generated quest instance."""

    id: str
    name: str
    description: str
    objectives: list[str]
    xp_reward: int
    difficulty: int
    generated_at: str
    context: dict[str, Any]
    template_id: str
    tags: list[str] = field(default_factory=list)
    skill_rewards: list[str] = field(default_factory=list)
    expires_at: str | None = None


# Quest template library
QUEST_TEMPLATES: dict[str, QuestTemplate] = {
    # Code analysis templates
    "analyze_file": QuestTemplate(
        id="analyze_file",
        name_template="Analyze {target_file}",
        description_template=(
            "Perform a detailed analysis of {target_file} and identify improvement opportunities."
        ),
        objectives_template=[
            "Review the structure of {target_file}",
            "Identify {issue_count} potential improvements",
            "Document findings in the quest log",
        ],
        xp_base=50,
        difficulty_range=(1, 2),
        required_context=["target_file"],
        tags=["analysis", "code_review"],
        skill_rewards=["code_analysis"],
    ),
    "fix_errors": QuestTemplate(
        id="fix_errors",
        name_template="Fix {error_count} Errors in {module}",
        description_template="Resolve {error_count} detected errors in the {module} module.",
        objectives_template=[
            "Run diagnostic scan on {module}",
            "Fix each identified error",
            "Verify fixes with tests",
        ],
        xp_base=75,
        difficulty_range=(2, 4),
        required_context=["module", "error_count"],
        tags=["debugging", "error_fixing"],
        skill_rewards=["error_handling", "debugging"],
    ),
    "add_tests": QuestTemplate(
        id="add_tests",
        name_template="Add Tests for {target}",
        description_template=(
            "Improve test coverage for {target} by adding comprehensive unit tests."
        ),
        objectives_template=[
            "Identify untested code paths in {target}",
            "Write {test_count} new test cases",
            "Achieve {coverage}% coverage",
        ],
        xp_base=100,
        difficulty_range=(2, 3),
        required_context=["target"],
        tags=["testing", "quality"],
        skill_rewards=["testing", "code_quality"],
    ),
    # Refactoring templates
    "refactor_module": QuestTemplate(
        id="refactor_module",
        name_template="Refactor {module_name}",
        description_template="Improve the code quality and maintainability of {module_name}.",
        objectives_template=[
            "Analyze current structure of {module_name}",
            "Identify refactoring opportunities",
            "Apply {refactor_count} improvements",
            "Ensure all tests pass",
        ],
        xp_base=150,
        difficulty_range=(3, 5),
        required_context=["module_name"],
        tags=["refactoring", "code_quality"],
        skill_rewards=["refactoring", "architecture"],
    ),
    # Documentation templates
    "document_api": QuestTemplate(
        id="document_api",
        name_template="Document {api_name} API",
        description_template="Create comprehensive documentation for the {api_name} API.",
        objectives_template=[
            "List all endpoints/functions in {api_name}",
            "Write docstrings for {doc_count} functions",
            "Create usage examples",
        ],
        xp_base=75,
        difficulty_range=(1, 2),
        required_context=["api_name"],
        tags=["documentation", "api"],
        skill_rewards=["documentation"],
    ),
    # Exploration templates
    "explore_directory": QuestTemplate(
        id="explore_directory",
        name_template="Explore {directory}",
        description_template="Map and understand the contents of {directory}.",
        objectives_template=[
            "List all files in {directory}",
            "Identify key modules",
            "Create a summary map",
        ],
        xp_base=30,
        difficulty_range=(1, 1),
        required_context=["directory"],
        tags=["exploration", "mapping"],
        skill_rewards=["navigation"],
    ),
    # Security templates
    "security_audit": QuestTemplate(
        id="security_audit",
        name_template="Security Audit: {target}",
        description_template="Perform a security review of {target} to identify vulnerabilities.",
        objectives_template=[
            "Scan {target} for security issues",
            "Check for common vulnerabilities",
            "Document findings",
            "Propose remediation steps",
        ],
        xp_base=200,
        difficulty_range=(3, 5),
        required_context=["target"],
        tags=["security", "audit"],
        skill_rewards=["security", "audit"],
    ),
    # Performance templates
    "optimize_performance": QuestTemplate(
        id="optimize_performance",
        name_template="Optimize {component}",
        description_template=(
            "Improve the performance of {component} through profiling and optimization."
        ),
        objectives_template=[
            "Profile {component} execution",
            "Identify {bottleneck_count} bottlenecks",
            "Apply optimizations",
            "Measure improvement",
        ],
        xp_base=175,
        difficulty_range=(3, 4),
        required_context=["component"],
        tags=["performance", "optimization"],
        skill_rewards=["performance", "profiling"],
    ),
    # Daily challenge templates
    "daily_commit": QuestTemplate(
        id="daily_commit",
        name_template="Daily Code Contribution",
        description_template="Make at least one meaningful code contribution today.",
        objectives_template=[
            "Write or improve code",
            "Create a clean commit",
            "Push changes",
        ],
        xp_base=25,
        difficulty_range=(1, 1),
        required_context=[],
        tags=["daily", "contribution"],
        skill_rewards=["consistency"],
    ),
    "code_review": QuestTemplate(
        id="code_review",
        name_template="Review Recent Changes",
        description_template="Review and provide feedback on recent code changes.",
        objectives_template=[
            "Review the last {change_count} commits",
            "Identify improvements",
            "Leave constructive feedback",
        ],
        xp_base=40,
        difficulty_range=(1, 2),
        required_context=[],
        tags=["review", "collaboration"],
        skill_rewards=["code_review"],
    ),
}


class ProceduralQuestGenerator:
    """Generates quests procedurally based on context and player state."""

    def __init__(self, seed: int | None = None):
        """Initialize the quest generator.

        Args:
            seed: Random seed for reproducible generation.
        """
        self.rng = random.Random(seed)
        self._generated_count = 0

    def generate(
        self,
        template_id: str,
        context: dict[str, Any],
        difficulty_override: int | None = None,
    ) -> GeneratedQuest | None:
        """Generate a quest from a template.

        Args:
            template_id: ID of the template to use.
            context: Context variables for template substitution.
            difficulty_override: Override the template's difficulty range.

        Returns:
            Generated quest or None if template invalid.
        """
        template = QUEST_TEMPLATES.get(template_id)
        if not template:
            logger.warning(f"Unknown quest template: {template_id}")
            return None

        # Check required context
        missing = [c for c in template.required_context if c not in context]
        if missing:
            logger.warning(f"Missing required context for {template_id}: {missing}")
            # Fill in defaults
            for m in missing:
                context[m] = f"<{m}>"

        # Fill in optional context with defaults
        context.setdefault("issue_count", self.rng.randint(2, 5))
        context.setdefault("test_count", self.rng.randint(3, 8))
        context.setdefault("coverage", self.rng.randint(70, 90))
        context.setdefault("refactor_count", self.rng.randint(2, 4))
        context.setdefault("doc_count", self.rng.randint(3, 10))
        context.setdefault("bottleneck_count", self.rng.randint(1, 3))
        context.setdefault("change_count", self.rng.randint(3, 7))

        # Determine difficulty
        if difficulty_override is not None:
            difficulty = difficulty_override
        else:
            difficulty = self.rng.randint(*template.difficulty_range)

        # Calculate XP with difficulty scaling
        xp_reward = int(template.xp_base * (1 + (difficulty - 1) * 0.25))

        # Generate quest ID
        self._generated_count += 1
        timestamp = datetime.now(UTC).strftime("%Y%m%d%H%M%S")
        quest_id = f"proc_{template_id}_{self._generated_count}_{timestamp}"

        # Substitute templates
        name = template.name_template.format(**context)
        description = template.description_template.format(**context)
        objectives = [obj.format(**context) for obj in template.objectives_template]

        quest = GeneratedQuest(
            id=quest_id,
            name=name,
            description=description,
            objectives=objectives,
            xp_reward=xp_reward,
            difficulty=difficulty,
            generated_at=datetime.now(UTC).isoformat(),
            context=context,
            template_id=template_id,
            tags=template.tags.copy(),
            skill_rewards=template.skill_rewards.copy(),
        )

        logger.info(f"Generated quest: {quest.name} (difficulty: {difficulty}, XP: {xp_reward})")
        return quest

    def generate_daily_quests(self, player_level: int = 1) -> list[GeneratedQuest]:
        """Generate a set of daily quests based on player level.

        Args:
            player_level: Player's current level.

        Returns:
            List of generated daily quests.
        """
        quests = []

        # Always include daily commit
        if quest := self.generate("daily_commit", {}):
            quests.append(quest)

        # Add code review for level 2+
        if player_level >= 2 and (quest := self.generate("code_review", {})):
            quests.append(quest)

        # Add exploration quest
        directories = ["src/games", "src/tools", "src/orchestration", "scripts"]
        if quest := self.generate("explore_directory", {"directory": self.rng.choice(directories)}):
            quests.append(quest)

        return quests

    def generate_from_errors(self, errors: list[dict[str, Any]]) -> list[GeneratedQuest]:
        """Generate quests based on detected errors.

        Args:
            errors: List of error dictionaries with 'file' and 'count' keys.

        Returns:
            List of generated fix quests.
        """
        quests = []
        for error in errors[:5]:  # Limit to top 5
            file_path = error.get("file", "unknown")
            count = error.get("count", 1)
            module = Path(file_path).stem

            if quest := self.generate("fix_errors", {"module": module, "error_count": count}):
                quests.append(quest)

        return quests

    def generate_from_coverage(
        self,
        uncovered_files: list[str],
        target_coverage: int = 80,
    ) -> list[GeneratedQuest]:
        """Generate test quests for uncovered files.

        Args:
            uncovered_files: List of files with low coverage.
            target_coverage: Target coverage percentage.

        Returns:
            List of generated test quests.
        """
        quests = []
        for file_path in uncovered_files[:3]:  # Limit to top 3
            target = Path(file_path).stem

            if quest := self.generate("add_tests", {"target": target, "coverage": target_coverage}):
                quests.append(quest)

        return quests


# Module-level instance
_generator: ProceduralQuestGenerator | None = None


def get_generator(seed: int | None = None) -> ProceduralQuestGenerator:
    """Get or create the global quest generator."""
    global _generator
    if _generator is None:
        _generator = ProceduralQuestGenerator(seed)
    return _generator


# Convenience functions
def generate_quest(
    template_id: str, context: dict[str, Any] | None = None
) -> GeneratedQuest | None:
    """Generate a single quest."""
    return get_generator().generate(template_id, context or {})


def generate_daily() -> list[GeneratedQuest]:
    """Generate daily quests."""
    return get_generator().generate_daily_quests()


def generate_from_errors(errors: list[dict[str, Any]]) -> list[GeneratedQuest]:
    """Generate quests from errors."""
    return get_generator().generate_from_errors(errors)


logger.info("Procedural quest generation system loaded")
