"""Tutorial Engine for CyberTerminal.

Provides structured tutorial objectives with hints, validation, and progression.
Guides players through lessons with story context and educational content.
"""

from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ObjectiveStatus(Enum):
    """Status of a tutorial objective."""

    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class HintLevel(Enum):
    """Hint specificity levels."""

    MINIMAL = 1  # "Try a different approach"
    MODERATE = 2  # "You need to use cd to navigate"
    DETAILED = 3  # "Type: cd /home"


@dataclass
class Hint:
    """A single hint within an objective."""

    level: HintLevel
    text: str
    unlocked_after_attempts: int = 0


@dataclass
class TutorialObjective:
    """A single objective within a tutorial lesson."""

    id: str
    title: str
    description: str
    success_condition: str  # Human-readable success state
    validation_fn: Callable[[dict[str, Any]], bool] | None = None
    commands_used: list[str] = field(default_factory=list)
    expected_output: str | None = None
    hints: list[Hint] = field(default_factory=list)
    story_text: str = ""
    reward_xp: int = 10
    max_attempts: int = 10


@dataclass
class ObjectiveProgress:
    """Progress tracking for an objective."""

    objective_id: str
    status: ObjectiveStatus = ObjectiveStatus.NOT_STARTED
    attempts: int = 0
    hints_used: int = 0
    completion_time: float = 0.0  # seconds
    started_at: float | None = None
    completed_at: float | None = None


class TutorialEngine:
    """Manages tutorials, objectives, and gameplay flow."""

    def __init__(self):
        """Initialize the tutorial engine."""
        self.objectives: dict[str, TutorialObjective] = {}
        self.objective_progress: dict[str, ObjectiveProgress] = {}
        self.current_objective_id: str | None = None
        self.hint_counter: dict[str, int] = {}
        self.total_completion_time: float = 0.0

        self._initialize_tutorial_objectives()

    def _initialize_tutorial_objectives(self) -> None:
        """Initialize all tutorial objectives for Tier 1."""
        obj1 = TutorialObjective(
            id="obj_welcome",
            title="Welcome to the File System",
            description="Use pwd to see your current location in the file system",
            success_condition="You should see the current directory path",
            commands_used=["pwd"],
            hints=[
                Hint(HintLevel.MINIMAL, "Try typing a command to see where you are", 0),
                Hint(
                    HintLevel.MODERATE,
                    "Use the pwd command to print your current working directory",
                    1,
                ),
                Hint(HintLevel.DETAILED, "Type: pwd", 3),
            ],
            story_text=(
                "The neon glow of your terminal awakens. You need to know where you are in the system..."
            ),
            reward_xp=10,
        )

        obj2 = TutorialObjective(
            id="obj_navigate",
            title="Navigate to Home",
            description="Use cd to change to your home directory",
            success_condition="You should be in the /home directory",
            commands_used=["cd"],
            hints=[
                Hint(HintLevel.MINIMAL, "You need to change directory", 0),
                Hint(HintLevel.MODERATE, "Use the cd command followed by a path", 2),
                Hint(HintLevel.DETAILED, "Type: cd /home", 4),
            ],
            story_text=(
                "To begin your infiltration, you need to access your home directory. It's where your files are stored."
            ),
            reward_xp=15,
        )

        obj3 = TutorialObjective(
            id="obj_list",
            title="Explore the Directory",
            description="Use ls to list files in your current directory",
            success_condition="You should see a list of files and folders",
            commands_used=["ls"],
            hints=[
                Hint(HintLevel.MINIMAL, "You need to list the contents of a directory", 0),
                Hint(HintLevel.MODERATE, "Use the ls command", 2),
                Hint(HintLevel.DETAILED, "Type: ls", 4),
            ],
            story_text=(
                "Now that you're in your home, see what files and folders are available to you."
            ),
            reward_xp=15,
        )

        obj4 = TutorialObjective(
            id="obj_read_file",
            title="Read Important Data",
            description="Use cat to read the contents of a file",
            success_condition="You should see the file contents displayed",
            commands_used=["cat"],
            hints=[
                Hint(HintLevel.MINIMAL, "You need to read a file", 0),
                Hint(HintLevel.MODERATE, "Use the cat command followed by a filename", 2),
                Hint(HintLevel.DETAILED, "Try: cat README.txt", 4),
            ],
            story_text=(
                "Inside your home directory is a README file. It contains important intel about the system."
            ),
            reward_xp=15,
        )

        obj5 = TutorialObjective(
            id="obj_create_file",
            title="Create a New File",
            description="Use touch to create an empty file, then mkdir to create a directory",
            success_condition="You should have created both a file and a directory",
            commands_used=["touch", "mkdir"],
            hints=[
                Hint(HintLevel.MINIMAL, "You need to create files and directories", 0),
                Hint(HintLevel.MODERATE, "Use touch for files and mkdir for directories", 2),
                Hint(HintLevel.DETAILED, "Type: touch newfile.txt and mkdir mynewdir", 4),
            ],
            story_text=(
                "Every hacker needs their own workspace. "
                "Create a personal directory and file to establish your presence."
            ),
            reward_xp=20,
        )

        # Register objectives
        for obj in [obj1, obj2, obj3, obj4, obj5]:
            self.objectives[obj.id] = obj

    def add_objective(self, objective: TutorialObjective) -> None:
        """Add a new objective to the tutorial."""
        self.objectives[objective.id] = objective

    def start_objective(self, objective_id: str) -> bool:
        """Start an objective."""
        if objective_id not in self.objectives:
            return False

        self.current_objective_id = objective_id

        if objective_id not in self.objective_progress:
            self.objective_progress[objective_id] = ObjectiveProgress(objective_id)

        progress = self.objective_progress[objective_id]
        progress.status = ObjectiveStatus.IN_PROGRESS
        progress.started_at = self._get_timestamp()
        progress.attempts = 0

        return True

    def validate_objective(self, objective_id: str, context: dict[str, Any]) -> bool:
        """Validate if an objective is completed."""
        objective = self.objectives.get(objective_id)
        if not objective:
            return False

        # Use custom validation function if provided
        if objective.validation_fn:
            return objective.validation_fn(context)

        # Default validation: check if required commands were used
        commands_used = context.get("commands_used", [])
        return all(cmd in commands_used for cmd in objective.commands_used)

    def submit_objective(self, objective_id: str, context: dict[str, Any]) -> bool:
        """Submit an objective for validation."""
        if objective_id not in self.objective_progress:
            return False

        progress = self.objective_progress[objective_id]
        progress.attempts += 1

        objective = self.objectives.get(objective_id)
        if not objective:
            return False

        # Check max attempts
        if progress.attempts > objective.max_attempts:
            progress.status = ObjectiveStatus.FAILED
            return False

        # Validate objective
        if self.validate_objective(objective_id, context):
            progress.status = ObjectiveStatus.COMPLETED
            progress.completed_at = self._get_timestamp()
            if progress.started_at:
                progress.completion_time = progress.completed_at - progress.started_at
            return True

        return False

    def get_hint(self, objective_id: str) -> str | None:
        """Get the next hint for an objective."""
        objective = self.objectives.get(objective_id)
        if not objective:
            return None

        progress = self.objective_progress.get(objective_id)
        if not progress:
            return None

        progress.hints_used += 1
        attempts = progress.attempts

        # Find appropriate hint based on attempts
        for hint in objective.hints:
            if attempts >= hint.unlocked_after_attempts:
                return hint.text

        return "You're on the right track! Keep trying."

    def get_objective(self, objective_id: str) -> TutorialObjective | None:
        """Get objective details."""
        return self.objectives.get(objective_id)

    def get_current_objective(self) -> TutorialObjective | None:
        """Get the current active objective."""
        if self.current_objective_id:
            return self.objectives.get(self.current_objective_id)
        return None

    def get_available_objectives(self, completed: list[str]) -> list[TutorialObjective]:
        """Get objectives not yet completed."""
        return [obj for obj in self.objectives.values() if obj.id not in completed]

    def get_objectives_by_category(self, _category: str) -> list[TutorialObjective]:
        """Get objectives by category tag."""
        # Simplified: return all for now
        return list(self.objectives.values())

    def get_progress(self, objective_id: str) -> ObjectiveProgress | None:
        """Get progress for an objective."""
        return self.objective_progress.get(objective_id)

    def get_overall_progress(self) -> dict[str, Any]:
        """Get overall tutorial progress statistics."""
        total_objectives = len(self.objectives)
        completed = sum(
            1 for p in self.objective_progress.values() if p.status == ObjectiveStatus.COMPLETED
        )

        total_attempts = sum(p.attempts for p in self.objective_progress.values())
        total_time = sum(p.completion_time for p in self.objective_progress.values())

        return {
            "total_objectives": total_objectives,
            "completed_objectives": completed,
            "completion_percentage": (
                (completed / total_objectives * 100) if total_objectives > 0 else 0
            ),
            "total_attempts": total_attempts,
            "total_time_seconds": total_time,
        }

    def reset_objective(self, objective_id: str) -> bool:
        """Reset an objective to initial state."""
        if objective_id in self.objective_progress:
            self.objective_progress[objective_id] = ObjectiveProgress(objective_id)
            return True
        return False

    @staticmethod
    def _get_timestamp() -> float:
        """Get current timestamp for time tracking."""
        import time

        return time.time()

    def get_story_context(self, objective_id: str) -> str | None:
        """Get story context for an objective."""
        objective = self.objectives.get(objective_id)
        if objective:
            return objective.story_text
        return None
