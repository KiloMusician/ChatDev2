"""Enhanced Task Scheduler - Phase 3 Value-Based Task Prioritization.

This scheduler replaces FIFO queue processing with intelligent task selection:
- Value-based ranking (impact, urgency, dependencies)
- Diversity quotas (prevent lint-heavy batches)
- Learning from past execution results
- Integration with autonomy dashboard metrics

OmniTag: [orchestration, task_scheduling, value_optimization, phase3]
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class TaskCategory(Enum):
    """Task type categories for diversity tracking."""

    FEATURE = "feature"  # New functionality
    BUGFIX = "bugfix"  # Error corrections
    REFACTOR = "refactor"  # Code improvement
    TEST = "test"  # Test additions
    LINT = "lint"  # Code style fixes
    DOCS = "docs"  # Documentation
    SECURITY = "security"  # Security improvements
    PERFORMANCE = "performance"  # Optimization
    DEPENDENCY = "dependency"  # Library updates
    UNKNOWN = "unknown"  # Unclassified


class PriorityTier(Enum):
    """Priority tiers for task execution."""

    CRITICAL = 4  # Must execute immediately
    HIGH = 3  # Should execute soon
    MEDIUM = 2  # Normal priority
    LOW = 1  # Can be deferred
    DEFERRED = 0  # Postponed indefinitely


@dataclass
class TaskMetrics:
    """Metrics for task value calculation."""

    # Impact scoring (0.0-1.0)
    code_quality_impact: float = 0.5  # How much it improves code quality
    user_value: float = 0.5  # Value to end users
    technical_debt_reduction: float = 0.5  # Reduces technical debt?
    security_impact: float = 0.0  # Security implications

    # Complexity scoring (0.0-1.0)
    estimated_effort: float = 0.5  # Time/complexity estimate
    risk_score: float = 0.3  # From Phase 1A risk scorer
    dependency_count: int = 0  # How many tasks depend on this

    # Historical data
    similar_task_success_rate: float = 0.8  # Success rate of similar tasks
    average_completion_time: float | None = None  # Minutes

    # Temporal factors
    age_days: float = 0.0  # How long in queue
    deadline: datetime | None = None  # If time-sensitive


@dataclass
class TaskValue:
    """Calculated value score for task prioritization."""

    task_id: int
    category: TaskCategory
    priority_tier: PriorityTier

    # Component scores (0.0-1.0)
    impact_score: float = 0.0
    urgency_score: float = 0.0
    feasibility_score: float = 0.0
    diversity_score: float = 0.0

    # Final weighted score
    final_score: float = 0.0

    # Metadata
    calculated_at: datetime = field(default_factory=datetime.now)
    reason: str = ""  # Why this score?


class DiversityQuota:
    """Enforce diversity in task selection to prevent monotonous batches."""

    def __init__(
        self,
        max_consecutive_same_category: int = 3,
        min_category_variety_per_batch: int = 2,
        batch_size: int = 10,
    ):
        """Initialize DiversityQuota with max_consecutive_same_category, min_category_variety_per_batch, batch_size."""
        self.max_consecutive_same = max_consecutive_same_category
        self.min_variety = min_category_variety_per_batch
        self.batch_size = batch_size

        # Tracking
        self.recent_categories: list[TaskCategory] = []
        self.batch_categories: set[TaskCategory] = set()
        self.consecutive_count = 0
        self.last_category: TaskCategory | None = None

    def can_select(self, category: TaskCategory) -> bool:
        """Check if selecting this category violates diversity rules."""
        # Always allow SECURITY regardless of diversity
        if category == TaskCategory.SECURITY:
            return True

        # Check consecutive limit
        if category == self.last_category and self.consecutive_count >= self.max_consecutive_same:
            return False

        # Force variety if we've processed a batch
        if (
            len(self.recent_categories) >= self.batch_size
            and len(self.batch_categories) < self.min_variety
        ):
            # Need more variety - prioritize different categories
            return category not in self.recent_categories[-self.batch_size :]

        return True

    def record_selection(self, category: TaskCategory):
        """Record task selection for diversity tracking."""
        self.recent_categories.append(category)
        self.batch_categories.add(category)

        if category == self.last_category:
            self.consecutive_count += 1
        else:
            self.consecutive_count = 1
            self.last_category = category

        # Reset batch tracking
        if len(self.recent_categories) > self.batch_size:
            self.recent_categories = self.recent_categories[-self.batch_size :]

        if len(self.recent_categories) % self.batch_size == 0:
            self.batch_categories.clear()

    def get_diversity_boost(self, category: TaskCategory) -> float:
        """Calculate diversity boost for underrepresented categories."""
        if not self.recent_categories:
            return 0.0

        recent_batch = self.recent_categories[-self.batch_size :]
        category_count = recent_batch.count(category)

        # Boost underrepresented categories
        if category_count == 0:
            return 0.3  # Strong boost for new categories
        elif category_count == 1:
            return 0.1  # Mild boost
        else:
            return -0.1 * (category_count - 1)  # Penalize overrepresentation


class EnhancedTaskScheduler:
    """Phase 3 enhanced task scheduler with value-based prioritization."""

    def __init__(
        self,
        orchestrator: Any,  # BackgroundTaskOrchestrator reference
        enable_diversity: bool = True,
        learning_enabled: bool = True,
    ):
        """Initialize EnhancedTaskScheduler with orchestrator, # BackgroundTaskOrchestrator reference enable_diversity, learning_enabled."""
        self.orchestrator = orchestrator
        self.enable_diversity = enable_diversity
        self.learning_enabled = learning_enabled

        # Components
        self.diversity_quota = DiversityQuota() if enable_diversity else None

        # Weights for value calculation (sum to 1.0)
        self.weights = {
            "impact": 0.35,
            "urgency": 0.25,
            "feasibility": 0.25,
            "diversity": 0.15,
        }

        # Historical tracking for learning
        self.execution_history: list[dict[str, Any]] = []
        self.category_success_rates: dict[TaskCategory, float] = {}

    def categorize_task(self, task: Any) -> TaskCategory:
        """Infer task category from description/metadata."""
        # Check explicit metadata category first (most reliable signal)
        metadata = getattr(task, "metadata", None)
        if isinstance(metadata, dict):
            meta_cat = metadata.get("category", "").upper()
            _meta_map = {
                "SECURITY": TaskCategory.SECURITY,
                "LINT": TaskCategory.LINT,
                "BUGFIX": TaskCategory.BUGFIX,
                "FEATURE": TaskCategory.FEATURE,
                "REFACTOR": TaskCategory.REFACTOR,
                "TEST": TaskCategory.TEST,
                "DOCS": TaskCategory.DOCS,
                "PERFORMANCE": TaskCategory.PERFORMANCE,
                "DEPENDENCY": TaskCategory.DEPENDENCY,
            }
            if meta_cat in _meta_map:
                return _meta_map[meta_cat]

        # BackgroundTask uses 'prompt', other task types might use 'description'
        description = (getattr(task, "prompt", getattr(task, "description", ""))).lower() or ""

        # Keyword-based categorization — specific terms before generic "fix"
        if any(kw in description for kw in ["security", "vulnerability", "cve"]):
            return TaskCategory.SECURITY
        elif any(kw in description for kw in ["lint", "format", "style", "ruff", "black"]):
            return TaskCategory.LINT
        elif any(kw in description for kw in ["fix", "bug", "error", "issue"]):
            return TaskCategory.BUGFIX
        elif any(kw in description for kw in ["refactor", "improve", "optimize"]):
            return TaskCategory.REFACTOR
        elif any(kw in description for kw in ["test", "coverage", "unittest"]):
            return TaskCategory.TEST
        elif any(kw in description for kw in ["doc", "readme", "comment"]):
            return TaskCategory.DOCS
        elif any(kw in description for kw in ["performance", "speed"]):
            return TaskCategory.PERFORMANCE
        elif any(kw in description for kw in ["dependency", "upgrade", "update"]):
            return TaskCategory.DEPENDENCY
        elif any(kw in description for kw in ["add", "feature", "implement", "create"]):
            return TaskCategory.FEATURE
        else:
            return TaskCategory.UNKNOWN

    def calculate_impact_score(self, task: Any, metrics: TaskMetrics) -> float:
        """Calculate task impact (0.0-1.0)."""
        del task
        # Weighted average of impact components
        impact = (
            metrics.code_quality_impact * 0.3
            + metrics.user_value * 0.3
            + metrics.technical_debt_reduction * 0.2
            + metrics.security_impact * 0.2  # Security is important
        )

        # Boost for dependency dependencies (unblocks others)
        if metrics.dependency_count > 0:
            impact += min(0.2, metrics.dependency_count * 0.05)

        return min(1.0, impact)

    def calculate_urgency_score(self, task: Any, metrics: TaskMetrics) -> float:
        """Calculate task urgency (0.0-1.0)."""
        urgency = 0.0

        # Age-based urgency (tasks get more urgent over time)
        if metrics.age_days > 0:
            # Linear increase: 0.1 per week, caps at 0.5
            urgency += min(0.5, (metrics.age_days / 7.0) * 0.1)

        # Deadline urgency
        if metrics.deadline:
            time_remaining = (metrics.deadline - datetime.now(UTC)).total_seconds()
            if time_remaining < 0:
                urgency += 0.5  # Overdue!
            elif time_remaining < 86400:  # < 1 day
                urgency += 0.3
            elif time_remaining < 604800:  # < 1 week
                urgency += 0.2

        # Security tasks are always urgent
        if metrics.security_impact > 0.5:
            urgency += 0.4

        # Factor in task priority field (BackgroundTask.priority)
        task_priority = getattr(task, "priority", None)
        if task_priority is not None and hasattr(task_priority, "value"):
            pval = task_priority.value
            if pval >= 10:  # CRITICAL
                urgency += 0.5
            elif pval >= 8:  # HIGH
                urgency += 0.3
            elif pval <= 2:  # LOW
                urgency -= 0.1

        return min(1.0, urgency)

    def calculate_feasibility_score(self, task: Any, metrics: TaskMetrics) -> float:
        """Calculate task feasibility (0.0-1.0)."""
        del task
        feasibility = 1.0  # Start optimistic

        # Penalize high risk
        feasibility -= metrics.risk_score * 0.3

        # Penalize high effort
        feasibility -= metrics.estimated_effort * 0.2

        # Reward historical success
        feasibility += (metrics.similar_task_success_rate - 0.5) * 0.3

        return max(0.0, min(1.0, feasibility))

    def calculate_task_value(self, task: Any, metrics: TaskMetrics | None = None) -> TaskValue:
        """Calculate comprehensive task value score."""
        # Default metrics if not provided
        if metrics is None:
            metrics = TaskMetrics(
                age_days=(
                    (datetime.now(UTC) - task.created_at).days if hasattr(task, "created_at") else 0
                )
            )

        category = self.categorize_task(task)

        # Calculate component scores
        impact = self.calculate_impact_score(task, metrics)
        urgency = self.calculate_urgency_score(task, metrics)
        feasibility = self.calculate_feasibility_score(task, metrics)

        # Diversity boost
        diversity = 0.5  # Neutral
        if self.diversity_quota:
            diversity += self.diversity_quota.get_diversity_boost(category)
            diversity = max(0.0, min(1.0, diversity))

        # Weighted final score
        final_score = (
            impact * self.weights["impact"]
            + urgency * self.weights["urgency"]
            + feasibility * self.weights["feasibility"]
            + diversity * self.weights["diversity"]
        )

        # Determine priority tier
        if final_score >= 0.8 or metrics.security_impact > 0.7:
            tier = PriorityTier.CRITICAL
        elif final_score >= 0.6:
            tier = PriorityTier.HIGH
        elif final_score >= 0.4:
            tier = PriorityTier.MEDIUM
        elif final_score >= 0.2:
            tier = PriorityTier.LOW
        else:
            tier = PriorityTier.DEFERRED

        # Build reason string
        reason = f"Impact:{impact:.2f} Urgency:{urgency:.2f} Feasibility:{feasibility:.2f} Diversity:{diversity:.2f}"

        return TaskValue(
            task_id=task.id if hasattr(task, "id") else 0,
            category=category,
            priority_tier=tier,
            impact_score=impact,
            urgency_score=urgency,
            feasibility_score=feasibility,
            diversity_score=diversity,
            final_score=final_score,
            reason=reason,
        )

    def select_next_batch(
        self, available_tasks: list[Any], batch_size: int = 10
    ) -> list[tuple[Any, TaskValue]]:
        """Select next batch of tasks to execute using value-based ranking."""
        if not available_tasks:
            logger.info("No tasks available for scheduling")
            return []

        # Calculate values for all tasks
        task_values: list[tuple[Any, TaskValue]] = []
        for task in available_tasks:
            try:
                value = self.calculate_task_value(task)
                task_values.append((task, value))
            except Exception as e:
                logger.error(f"Error calculating value for task {task}: {e}")
                continue

        # Sort by final score (descending)
        task_values.sort(key=lambda x: x[1].final_score, reverse=True)

        # Apply diversity filtering
        selected: list[tuple[Any, TaskValue]] = []
        for task, value in task_values:
            if len(selected) >= batch_size:
                break

            # Check diversity quota
            if self.diversity_quota and not self.diversity_quota.can_select(value.category):
                logger.debug(
                    f"Skipping task {value.task_id} ({value.category.value}) due to diversity quota"
                )
                continue

            selected.append((task, value))

            # Record selection
            if self.diversity_quota:
                self.diversity_quota.record_selection(value.category)

        logger.info(
            f"Selected {len(selected)} tasks from {len(available_tasks)} available. "
            f"Categories: {[v.category.value for _, v in selected]}"
        )

        try:
            from src.system.agent_awareness import emit as _emit

            _cats = ",".join(v.category.value for _, v in selected[:5])
            _emit(
                "tasks",
                f"Scheduler: selected={len(selected)}/{len(available_tasks)} categories=[{_cats}]",
                level="INFO",
                source="enhanced_task_scheduler",
            )
        except Exception:
            pass

        return selected

    def record_execution_result(
        self, task: Any, value: TaskValue, success: bool, duration_seconds: float
    ):
        """Record task execution result for learning."""
        del task
        if not self.learning_enabled:
            return

        result = {
            "task_id": value.task_id,
            "category": value.category.value,
            "predicted_score": value.final_score,
            "success": success,
            "duration": duration_seconds,
            "timestamp": datetime.now(UTC).isoformat(),
        }

        self.execution_history.append(result)

        # Update category success rates
        category_results = [
            r for r in self.execution_history if r["category"] == value.category.value
        ]
        if category_results:
            success_count = sum(1 for r in category_results if r["success"])
            self.category_success_rates[value.category] = success_count / len(category_results)

        logger.debug(
            f"Recorded execution: {value.category.value} Success={success} Duration={duration_seconds:.1f}s"
        )

    def get_scheduler_stats(self) -> dict[str, Any]:
        """Get scheduler statistics for dashboard."""
        return {
            "total_executions": len(self.execution_history),
            "category_success_rates": {
                cat.value: rate for cat, rate in self.category_success_rates.items()
            },
            "recent_categories": [
                cat.value
                for cat in (
                    self.diversity_quota.recent_categories[-10:] if self.diversity_quota else []
                )
            ],
            "diversity_enabled": self.enable_diversity,
            "learning_enabled": self.learning_enabled,
            "weights": self.weights,
        }


# Integration hook for BackgroundTaskOrchestrator
async def integrate_enhanced_scheduler(orchestrator: Any) -> EnhancedTaskScheduler:
    """Wire enhanced scheduler into existing orchestrator."""
    scheduler = EnhancedTaskScheduler(orchestrator, enable_diversity=True, learning_enabled=True)

    logger.info("✅ Enhanced Task Scheduler integrated (Phase 3)")
    logger.info("   - Value-based ranking: ENABLED")
    logger.info("   - Diversity quotas: ENABLED")
    logger.info("   - Learning: ENABLED")

    return scheduler
