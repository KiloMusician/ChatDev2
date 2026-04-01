"""Specialization Learning System - Phase 5.3.

Implements intelligent agent-task-temperature matching by learning which agents
excel at specific combinations. Enables cross-agent learning and specialization
tracking for 8% additional token savings through optimal agent selection.

Architecture:
  - Agent Profiling: Track agent performance across task types and temperatures
  - Specialization Detection: Identify which agent-task pairs work best
  - Cross-Agent Learning: Share knowledge across agent fleet
  - Pairing Optimization: Recommend best agent-temperature-task combo
"""

import json
import logging
from collections import defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from statistics import mean

logger = logging.getLogger(__name__)

# Ensure state directory exists
STATE_DIR = Path("state/specialization")
STATE_DIR.mkdir(parents=True, exist_ok=True)
AGENT_PROFILES_FILE = STATE_DIR / "agent_profiles.json"
SPECIALIZATION_HISTORY_FILE = STATE_DIR / "specialization_history.jsonl"
AGENT_PAIRINGS_FILE = STATE_DIR / "optimal_pairings.json"


def _normalize_quality_score(value: float) -> float:
    """Normalize quality scores to the expected 0.0-1.0 range."""
    if value > 1.0:
        value = value / 100.0
    if value < 0.0:
        return 0.0
    if value > 1.0:
        return 1.0
    return value


@dataclass
class AgentSpecialization:
    """Tracks specialization for a specific agent."""

    agent_name: str
    task_type: str
    temperature: float
    success_count: int = 0
    failure_count: int = 0
    avg_quality: float = 0.0
    avg_tokens: int = 0
    avg_latency_ms: float = 0.0
    specialization_score: float = 0.0  # 0-100, higher = more specialized

    @property
    def total_attempts(self) -> int:
        return self.success_count + self.failure_count

    @property
    def success_rate(self) -> float:
        if self.total_attempts == 0:
            return 0.0
        return self.success_count / self.total_attempts

    def update(self, success: bool, quality: float, tokens: int, latency_ms: float):
        """Update specialization stats with new result."""
        quality = _normalize_quality_score(quality)
        if success:
            self.success_count += 1
        else:
            self.failure_count += 1

        # Update rolling averages
        n = self.total_attempts
        self.avg_quality = ((self.avg_quality * (n - 1)) + quality) / n
        self.avg_tokens = int(((self.avg_tokens * (n - 1)) + tokens) / n)
        self.avg_latency_ms = ((self.avg_latency_ms * (n - 1)) + latency_ms) / n

        # Calculate specialization score (0-100)
        # High score = this agent specializes in this task+temp combo
        quality_component = self.avg_quality * 40  # 0-40
        success_component = self.success_rate * 60  # 0-60
        self.specialization_score = quality_component + success_component

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "AgentSpecialization":
        spec = cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})
        spec.avg_quality = _normalize_quality_score(spec.avg_quality)
        quality_component = spec.avg_quality * 40
        success_component = spec.success_rate * 60
        spec.specialization_score = quality_component + success_component
        return spec


@dataclass
class SpecializationRecord:
    """Single specialization learning event."""

    timestamp: str
    agent: str
    task_type: str
    temperature: float
    success: bool
    quality_score: float
    tokens_used: int
    latency_ms: float

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "SpecializationRecord":
        payload = dict(data)
        payload["quality_score"] = _normalize_quality_score(
            float(payload.get("quality_score", 0.0))
        )
        return cls(**payload)


class SpecializationTracker:
    """Tracks specialization experiments and learning history."""

    def __init__(self):
        """Initialize tracker."""
        self.history: list[SpecializationRecord] = []
        self.load_history()

    def record_attempt(self, record: SpecializationRecord):
        """Record agent specialization attempt."""
        self.history.append(record)
        self._persist_record(record)

    def _persist_record(self, record: SpecializationRecord):
        """Append record to JSONL file."""
        with open(SPECIALIZATION_HISTORY_FILE, "a") as f:
            f.write(json.dumps(record.to_dict()) + "\n")

    def load_history(self):
        """Load all historical records from JSONL."""
        if not SPECIALIZATION_HISTORY_FILE.exists():
            return

        with open(SPECIALIZATION_HISTORY_FILE) as f:
            for line in f:
                if line.strip():
                    try:
                        data = json.loads(line)
                        record = SpecializationRecord.from_dict(data)
                        self.history.append(record)
                    except (json.JSONDecodeError, TypeError):
                        logger.debug("Suppressed TypeError/json", exc_info=True)

    def get_records_for_agent(self, agent: str) -> list[SpecializationRecord]:
        """Get all records for specific agent."""
        return [r for r in self.history if r.agent == agent]

    def get_records_for_task(self, task_type: str) -> list[SpecializationRecord]:
        """Get all records for specific task type."""
        return [r for r in self.history if r.task_type == task_type]

    def get_records_for_combo(self, agent: str, task_type: str) -> list[SpecializationRecord]:
        """Get records for specific agent-task combo."""
        return [r for r in self.history if r.agent == agent and r.task_type == task_type]

    def get_best_agents_for_task(self, task_type: str, top_n: int = 3) -> list[tuple[str, float]]:
        """Get top N agents by success rate for task."""
        agent_stats = defaultdict(lambda: {"success": 0, "total": 0})

        for record in self.get_records_for_task(task_type):
            agent_stats[record.agent]["total"] += 1
            if record.success:
                agent_stats[record.agent]["success"] += 1

        # Calculate success rates
        results = [
            (agent, stats["success"] / stats["total"])
            for agent, stats in agent_stats.items()
            if stats["total"] >= 3  # Minimum 3 attempts
        ]

        return sorted(results, key=lambda x: x[1], reverse=True)[:top_n]


class SpecializationLearner:
    """Main system for agent specialization learning."""

    def __init__(self):
        """Initialize specialization system."""
        self.tracker = SpecializationTracker()
        self.profiles: dict[str, dict[str, AgentSpecialization]] = defaultdict(
            dict
        )  # agent -> (task+temp -> spec)
        self.agent_list: list[str] = []  # ordered for deterministic tie-breaking
        self.load_profiles()
        self._rebuild_from_history()

    def _rebuild_from_history(self):
        """Rebuild profiles from loaded history."""
        if self.tracker.history:
            self.profiles = defaultdict(dict)
            self.agent_list = []
        for record in self.tracker.history:
            key = f"{record.task_type}_{record.temperature:.2f}"
            if key not in self.profiles[record.agent]:
                self.profiles[record.agent][key] = AgentSpecialization(
                    agent_name=record.agent,
                    task_type=record.task_type,
                    temperature=record.temperature,
                )

            spec = self.profiles[record.agent][key]
            spec.update(record.success, record.quality_score, record.tokens_used, record.latency_ms)

            if record.agent not in self.agent_list:
                self.agent_list.append(record.agent)

    def load_profiles(self):
        """Load specialization profiles from JSON."""
        if not AGENT_PROFILES_FILE.exists():
            return

        try:
            with open(AGENT_PROFILES_FILE) as f:
                data = json.load(f)
                for agent, specs in data.items():
                    for key, spec_data in specs.items():
                        spec = AgentSpecialization.from_dict(spec_data)
                        self.profiles[agent][key] = spec
                        if agent not in self.agent_list:
                            self.agent_list.append(agent)
        except (json.JSONDecodeError, KeyError):
            logger.debug("Suppressed KeyError/json", exc_info=True)

    def save_profiles(self):
        """Persist profiles to JSON."""
        data = {}
        for agent, specs in self.profiles.items():
            data[agent] = {k: v.to_dict() for k, v in specs.items()}

        with open(AGENT_PROFILES_FILE, "w") as f:
            json.dump(data, f, indent=2)

    def record_attempt(
        self,
        agent: str,
        task_type: str,
        temperature: float,
        success: bool,
        quality_score: float,
        tokens_used: int,
        latency_ms: float,
    ):
        """Record an agent's attempt at task-temp combo."""
        quality_score = _normalize_quality_score(quality_score)
        record = SpecializationRecord(
            timestamp=datetime.now().isoformat(),
            agent=agent,
            task_type=task_type,
            temperature=temperature,
            success=success,
            quality_score=quality_score,
            tokens_used=tokens_used,
            latency_ms=latency_ms,
        )

        # Track in history
        self.tracker.record_attempt(record)

        # Update profiles
        key = f"{task_type}_{temperature:.2f}"
        if key not in self.profiles[agent]:
            self.profiles[agent][key] = AgentSpecialization(
                agent_name=agent,
                task_type=task_type,
                temperature=temperature,
            )

        self.profiles[agent][key].update(success, quality_score, tokens_used, latency_ms)
        if agent not in self.agent_list:
            self.agent_list.append(agent)
        self.save_profiles()

        logger.info(
            f"Agent {agent} specialization: {task_type}@{temperature:.2f} success={success} quality={quality_score:.2f}"
        )

    def get_best_agent_for_task(
        self, task_type: str, temperature: float | None = None
    ) -> str | None:
        """Get best agent for specific task (and temp if provided)."""
        best_agent = None
        best_score = -1

        for agent in self.agent_list:
            key = f"{task_type}_{temperature:.2f}" if temperature else f"{task_type}_*"

            if temperature and key in self.profiles[agent]:
                spec = self.profiles[agent][key]
                if spec.total_attempts >= 3:  # Minimum experience
                    score = spec.specialization_score
                    if score > best_score:
                        best_score = score
                        best_agent = agent
            elif not temperature:
                # Average across all temperatures for this task
                task_specs = [
                    s
                    for k, s in self.profiles[agent].items()
                    if s.task_type == task_type and s.total_attempts >= 2
                ]
                if task_specs:
                    avg_score = mean(s.specialization_score for s in task_specs)
                    if avg_score > best_score:
                        best_score = avg_score
                        best_agent = agent

        return best_agent if best_score >= 20 else None  # Minimum specialization score

    def recommend_agent_temperature_pair(
        self, task_type: str, available_agents: list[str]
    ) -> tuple[str | None, float | None]:
        """Recommend best agent and temperature for task."""
        best_agent = None
        best_temp = None
        best_score = -1

        for agent in available_agents:
            agent_specs = self.profiles.get(agent, {})

            for _key, spec in agent_specs.items():
                if (
                    spec.task_type == task_type
                    and spec.total_attempts >= 3
                    and spec.specialization_score > best_score
                ):
                    best_score = spec.specialization_score
                    best_agent = agent
                    best_temp = spec.temperature

        if best_score >= 30:  # Confidence threshold
            return (best_agent, best_temp)
        return (None, None)

    def get_agent_summary(self, agent: str) -> dict:
        """Get agent's specialization summary."""
        if agent not in self.profiles:
            return {"agent": agent, "specializations": 0, "avg_score": 0.0}

        specs = self.profiles[agent].values()
        task_counts = defaultdict(lambda: {"specs": 0, "score": 0.0})

        for spec in specs:
            if spec.total_attempts >= 2:
                task_counts[spec.task_type]["specs"] += 1
                task_counts[spec.task_type]["score"] += spec.specialization_score

        best_task = max(
            task_counts.items(),
            key=lambda x: x[1]["score"],
            default=("N/A", {"specs": 0, "score": 0.0}),
        )

        return {
            "agent": agent,
            "total_specializations": len([s for s in specs if s.total_attempts >= 2]),
            "avg_specialization_score": mean(s.specialization_score for s in specs) if specs else 0,
            "best_task": best_task[0],
            "best_task_score": (
                best_task[1]["score"] / best_task[1]["specs"] if best_task[1]["specs"] > 0 else 0
            ),
            "tasks_attempted": len({s.task_type for s in specs}),
        }

    def get_team_composition(self) -> dict:
        """Analyze team composition and specialization coverage."""
        coverage = defaultdict(list)  # task_type -> [agents with specializations]

        for agent in self.agent_list:
            summary = self.get_agent_summary(agent)
            if summary["total_specializations"] > 0:
                for key in self.profiles[agent]:
                    task_type = self.profiles[agent][key].task_type
                    if task_type not in coverage:
                        coverage[task_type] = []
                    if agent not in coverage[task_type]:
                        coverage[task_type].append(agent)

        return {
            "agent_count": len(self.agent_list),
            "task_coverage": {task: len(agents) for task, agents in coverage.items()},
            "avg_coverage_per_task": (
                mean(len(agents) for agents in coverage.values()) if coverage else 0
            ),
        }


def demo_specialization_learning():
    """Demo showing specialization learning system."""
    logger.info("\n" + "=" * 60)
    logger.info("SPECIALIZATION LEARNING SYSTEM - DEMO")
    logger.info("=" * 60)

    learner = SpecializationLearner()

    # Test 1: Register agents
    logger.info("\n[TEST 1] Agent Fleet Registration")
    agents = ["gpt4-turbo", "ollama-local", "claude-api", "gemini-pro"]
    logger.info(f"  Registered {len(agents)} agents:")
    for agent in agents:
        logger.info(f"    - {agent}")

    # Test 2: Record learning attempts
    logger.info("\n[TEST 2] Recording Specialization Attempts")

    # GPT4 excels at code
    for i in range(5):
        learner.record_attempt(
            agent="gpt4-turbo",
            task_type="code_generation",
            temperature=0.2,
            success=True,
            quality_score=0.94 + (i * 0.01),
            tokens_used=2500,
            latency_ms=450,
        )

    # Ollama excels at creative with high temp
    for i in range(4):
        learner.record_attempt(
            agent="ollama-local",
            task_type="creative_writing",
            temperature=0.85,
            success=True,
            quality_score=0.88 + (i * 0.02),
            tokens_used=2000,
            latency_ms=300,
        )

    # Claude good at code and creative
    for _i in range(3):
        learner.record_attempt(
            agent="claude-api",
            task_type="code_generation",
            temperature=0.25,
            success=True,
            quality_score=0.92,
            tokens_used=2400,
            latency_ms=420,
        )

    logger.info("  ✓ Recorded 12 specialization attempts")

    # Test 3: Get best agent recommendations
    logger.info("\n[TEST 3] Agent Recommendations")
    best_code = learner.get_best_agent_for_task("code_generation")
    best_creative = learner.get_best_agent_for_task("creative_writing")

    logger.info(f"  Best for code_generation: {best_code}")
    logger.info(f"  Best for creative_writing: {best_creative}")

    # Test 4: Agent-Temperature pairing
    logger.info("\n[TEST 4] Agent-Temperature Pairing")
    agent, temp = learner.recommend_agent_temperature_pair("code_generation", agents)
    if agent:
        logger.info(f"  Recommended: {agent} @ {temp:.2f}°")

    # Test 5: Agent summaries
    logger.info("\n[TEST 5] Agent Specialization Summaries")
    for agent in ["gpt4-turbo", "ollama-local", "claude-api"]:
        summary = learner.get_agent_summary(agent)
        logger.info(f"  {agent}:")
        logger.info(f"    Specializations: {summary['total_specializations']}")
        logger.info(f"    Best at: {summary['best_task']}")
        logger.info(f"    Avg score: {summary['avg_specialization_score']:.0f}/100")

    # Test 6: Team composition
    logger.info("\n[TEST 6] Team Composition Analysis")
    composition = learner.get_team_composition()
    logger.info(f"  Team size: {composition['agent_count']} agents")
    logger.info(f"  Task coverage: {dict(composition['task_coverage'])}")
    logger.info(f"  Avg coverage per task: {composition['avg_coverage_per_task']:.1f} agents")

    logger.info("\n" + "=" * 60)
    logger.info("DEMO COMPLETE")
    logger.info("=" * 60)


if __name__ == "__main__":
    demo_specialization_learning()
